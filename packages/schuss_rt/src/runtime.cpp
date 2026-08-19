#include "schuss_rt/runtime.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace schuss::rt {
namespace {

constexpr std::int64_t kQ27 = std::int64_t{1} << 27;
static_assert(std::atomic<std::uint32_t>::is_always_lock_free);
static_assert(std::atomic<std::uint64_t>::is_always_lock_free);

std::int32_t clamp_i32(std::int64_t value) noexcept {
    if (value > std::numeric_limits<std::int32_t>::max()) return std::numeric_limits<std::int32_t>::max();
    if (value < std::numeric_limits<std::int32_t>::min()) return std::numeric_limits<std::int32_t>::min();
    return static_cast<std::int32_t>(value);
}

std::int32_t multiply_q27(std::int32_t left, std::int32_t right) noexcept {
    const std::int64_t product = static_cast<std::int64_t>(left) * right;
    const std::int64_t scaled = product >= 0
        ? product / kQ27
        : -((-product + kQ27 - 1) / kQ27);
    return clamp_i32(scaled);
}

std::int32_t phase_to_q27(std::uint32_t phase) noexcept {
    const std::int64_t signed_phase = phase < 0x80000000U
        ? static_cast<std::int64_t>(phase)
        : static_cast<std::int64_t>(phase) - 0x100000000LL;
    if (signed_phase >= 0) return static_cast<std::int32_t>(signed_phase / 16);
    return static_cast<std::int32_t>(-((-signed_phase + 15) / 16));
}

std::uint32_t load_u32(const std::vector<std::uint8_t>& state, std::uint32_t offset) noexcept {
    std::uint32_t value{};
    std::memcpy(&value, state.data() + offset, sizeof(value));
    return value;
}

void store_u32(std::vector<std::uint8_t>& state, std::uint32_t offset, std::uint32_t value) noexcept {
    std::memcpy(state.data() + offset, &value, sizeof(value));
}

std::int32_t load_i32(const std::vector<std::uint8_t>& state, std::uint32_t offset) noexcept {
    std::int32_t value{};
    std::memcpy(&value, state.data() + offset, sizeof(value));
    return value;
}

void store_i32(std::vector<std::uint8_t>& state, std::uint32_t offset, std::int32_t value) noexcept {
    std::memcpy(state.data() + offset, &value, sizeof(value));
}

bool event_less(const Event& left, const Event& right) noexcept {
    if (left.frame_offset != right.frame_offset) return left.frame_offset < right.frame_offset;
    return left.sequence < right.sequence;
}

}  // namespace

Result Runtime::prepare(const PreparedPackage& package) {
    if (package.buffer_count == 0 || package.buffer_frames != kMaximumBlockFrames
        || package.state_bytes == 0 || package.event_capacity == 0) {
        return {ErrorCode::package_shape_invalid, "HOST_PREPARE_PACKAGE_INVALID"};
    }
    package_ = package;
    state_.assign(package.state_bytes, 0);
    buffers_.assign(static_cast<std::size_t>(package.buffer_count) * package.buffer_frames, 0);
    event_ring_.assign(static_cast<std::size_t>(package.event_capacity) + 1U, {});
    callback_events_.clear();
    callback_events_.reserve(package.event_capacity);
    prepared_ = true;
    reset();
    return {};
}

void Runtime::reset() noexcept {
    std::fill(state_.begin(), state_.end(), 0);
    std::fill(buffers_.begin(), buffers_.end(), 0);
    event_write_.store(0, std::memory_order_relaxed);
    event_read_.store(0, std::memory_order_relaxed);
    queue_overflows_.store(0, std::memory_order_relaxed);
    processed_frames_.store(0, std::memory_order_relaxed);
    events_delivered_.store(0, std::memory_order_relaxed);
}

bool Runtime::enqueue(const Event& event) noexcept {
    if (!prepared_ || event_ring_.empty()) return false;
    if (event.frame_offset >= kMaximumBlockFrames) return false;
    if (event.kind == EventKind::parameter_q27) {
        if (event.node_index >= package_.nodes.size()
            || event.parameter_index >= package_.nodes[event.node_index].parameter_count) {
            return false;
        }
    } else if (event.kind == EventKind::midi_message) {
        if (event.midi_size == 0 || event.midi_size > event.midi.size()) return false;
    } else {
        return false;
    }
    const auto write = event_write_.load(std::memory_order_relaxed);
    const auto next = (write + 1U) % static_cast<std::uint32_t>(event_ring_.size());
    if (next == event_read_.load(std::memory_order_acquire)) {
        queue_overflows_.fetch_add(1, std::memory_order_relaxed);
        return false;
    }
    event_ring_[write] = event;
    event_write_.store(next, std::memory_order_release);
    return true;
}

std::int32_t Runtime::parameter(const Node& node, std::string_view facet, std::int32_t fallback) const noexcept {
    for (std::uint8_t index = 0; index < node.parameter_count; ++index) {
        if (node.parameters[index].facet_id == facet) return node.parameters[index].value_q;
    }
    return fallback;
}

void Runtime::apply_event(const Event& event) noexcept {
    if (event.kind == EventKind::midi_message) {
        events_delivered_.fetch_add(1, std::memory_order_relaxed);
        return;
    }
    if (event.node_index >= package_.nodes.size()) return;
    Node& node = package_.nodes[event.node_index];
    if (event.parameter_index >= node.parameter_count) return;
    node.parameters[event.parameter_index].value_q = event.value_q;
    events_delivered_.fetch_add(1, std::memory_order_relaxed);
}

void Runtime::process_segment(std::uint32_t begin, std::uint32_t end) noexcept {
    if (begin >= end) return;
    auto buffer = [this](std::uint8_t index) noexcept {
        return buffers_.data() + static_cast<std::size_t>(index) * package_.buffer_frames;
    };

    for (const std::uint8_t scheduled : package_.schedule) {
        Node& node = package_.nodes[scheduled];
        switch (node.role) {
            case Role::saw: {
                auto* output = buffer(node.output_buffers[0]);
                std::uint32_t phase = load_u32(state_, node.state_offset_bytes);
                constexpr std::uint32_t increment = 9842633U;  // 110 Hz at 48 kHz.
                for (std::uint32_t frame = begin; frame < end; ++frame) {
                    output[frame] = phase_to_q27(phase);
                    phase += increment;
                }
                store_u32(state_, node.state_offset_bytes, phase);
                break;
            }
            case Role::pwm: {
                auto* output = buffer(node.output_buffers[0]);
                std::uint32_t phase = load_u32(state_, node.state_offset_bytes);
                constexpr std::uint32_t increment = 19685267U;  // 220 Hz at 48 kHz.
                const std::int32_t width = std::clamp(
                    parameter(node, "component-port-000002", 0),
                    static_cast<std::int32_t>(-kQ27),
                    static_cast<std::int32_t>(kQ27)
                );
                const std::uint32_t threshold = static_cast<std::uint32_t>(
                    (static_cast<std::int64_t>(width) + kQ27) * 16
                );
                for (std::uint32_t frame = begin; frame < end; ++frame) {
                    output[frame] = phase < threshold ? static_cast<std::int32_t>(kQ27) : static_cast<std::int32_t>(-kQ27);
                    phase += increment;
                }
                store_u32(state_, node.state_offset_bytes, phase);
                break;
            }
            case Role::soft: {
                const auto* input = buffer(node.input_buffers[0]);
                auto* output = buffer(node.output_buffers[0]);
                for (std::uint32_t frame = begin; frame < end; ++frame) {
                    const std::int32_t x = std::clamp(input[frame], static_cast<std::int32_t>(-kQ27), static_cast<std::int32_t>(kQ27));
                    const std::int32_t square = multiply_q27(x, x);
                    const std::int32_t cube = multiply_q27(square, x);
                    output[frame] = clamp_i32(static_cast<std::int64_t>(x) - cube / 3);
                }
                break;
            }
            case Role::smooth: {
                auto* output = buffer(node.output_buffers[0]);
                std::int32_t current = load_i32(state_, node.state_offset_bytes);
                const std::int32_t target = parameter(node, "component-port-000001", static_cast<std::int32_t>(kQ27 / 2));
                for (std::uint32_t frame = begin; frame < end; ++frame) {
                    current = clamp_i32(static_cast<std::int64_t>(current) + (static_cast<std::int64_t>(target) - current) / 16);
                    output[frame] = current;
                }
                store_i32(state_, node.state_offset_bytes, current);
                break;
            }
            case Role::crossfade: {
                const auto* a = buffer(node.input_buffers[0]);
                const auto* b = buffer(node.input_buffers[1]);
                auto* output = buffer(node.output_buffers[0]);
                const std::int32_t fade = std::clamp(parameter(node, "component-port-000003", static_cast<std::int32_t>(kQ27 / 2)), 0, static_cast<std::int32_t>(kQ27));
                for (std::uint32_t frame = begin; frame < end; ++frame) {
                    output[frame] = clamp_i32(
                        static_cast<std::int64_t>(multiply_q27(a[frame], static_cast<std::int32_t>(kQ27) - fade))
                        + multiply_q27(b[frame], fade)
                    );
                }
                break;
            }
            case Role::vca: {
                const auto* gain = buffer(node.input_buffers[0]);
                const auto* input = buffer(node.input_buffers[1]);
                auto* output = buffer(node.output_buffers[0]);
                for (std::uint32_t frame = begin; frame < end; ++frame) output[frame] = multiply_q27(input[frame], gain[frame]);
                break;
            }
            case Role::output: {
                const auto* left = buffer(node.input_buffers[0]);
                const auto* right = buffer(node.input_buffers[1]);
                auto* left_output = buffer(node.output_buffers[0]);
                auto* right_output = buffer(node.output_buffers[1]);
                for (std::uint32_t frame = begin; frame < end; ++frame) {
                    left_output[frame] = left[frame];
                    right_output[frame] = right[frame];
                }
                break;
            }
        }
    }
}

Result Runtime::process(std::int32_t* left_q27, std::int32_t* right_q27, std::uint32_t frames) noexcept {
    if (!prepared_) return {ErrorCode::not_prepared, "HOST_RUNTIME_NOT_PREPARED"};
    if (frames == 0 || frames > package_.buffer_frames) return {ErrorCode::block_too_large, "HOST_BLOCK_FRAMES_INVALID"};
    if (left_q27 == nullptr || right_q27 == nullptr) return {ErrorCode::package_shape_invalid, "HOST_OUTPUT_POINTER_INVALID"};

    callback_events_.clear();
    auto read = event_read_.load(std::memory_order_relaxed);
    const auto write = event_write_.load(std::memory_order_acquire);
    while (read != write && callback_events_.size() < callback_events_.capacity()) {
        Event event = event_ring_[read];
        if (event.frame_offset >= frames) event.frame_offset = frames - 1U;
        callback_events_.push_back(event);
        read = (read + 1U) % static_cast<std::uint32_t>(event_ring_.size());
    }
    event_read_.store(read, std::memory_order_release);
    std::sort(callback_events_.begin(), callback_events_.end(), event_less);

    std::uint32_t cursor = 0;
    for (const Event& event : callback_events_) {
        process_segment(cursor, event.frame_offset);
        apply_event(event);
        cursor = event.frame_offset;
    }
    process_segment(cursor, frames);

    const auto* left = buffers_.data() + static_cast<std::size_t>(package_.left_buffer) * package_.buffer_frames;
    const auto* right = buffers_.data() + static_cast<std::size_t>(package_.right_buffer) * package_.buffer_frames;
    std::copy_n(left, frames, left_q27);
    std::copy_n(right, frames, right_q27);
    processed_frames_.fetch_add(frames, std::memory_order_relaxed);
    return {};
}

Metrics Runtime::metrics() const noexcept {
    return {
        processed_frames_.load(std::memory_order_relaxed),
        events_delivered_.load(std::memory_order_relaxed),
        queue_overflows_.load(std::memory_order_relaxed),
    };
}

const char* error_name(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::ok: return "ok";
        case ErrorCode::json_invalid: return "json-invalid";
        case ErrorCode::package_schema_unsupported: return "package-schema-unsupported";
        case ErrorCode::runtime_abi_mismatch: return "runtime-abi-mismatch";
        case ErrorCode::numeric_profile_unsupported: return "numeric-profile-unsupported";
        case ErrorCode::package_hash_mismatch: return "package-hash-mismatch";
        case ErrorCode::package_shape_invalid: return "package-shape-invalid";
        case ErrorCode::unknown_node: return "unknown-node";
        case ErrorCode::unknown_factory: return "unknown-factory";
        case ErrorCode::port_contract_invalid: return "port-contract-invalid";
        case ErrorCode::schedule_invalid: return "schedule-invalid";
        case ErrorCode::cycle_detected: return "cycle-detected";
        case ErrorCode::state_plan_invalid: return "state-plan-invalid";
        case ErrorCode::buffer_plan_invalid: return "buffer-plan-invalid";
        case ErrorCode::event_contract_invalid: return "event-contract-invalid";
        case ErrorCode::not_prepared: return "not-prepared";
        case ErrorCode::block_too_large: return "block-too-large";
    }
    return "unknown";
}

}  // namespace schuss::rt
