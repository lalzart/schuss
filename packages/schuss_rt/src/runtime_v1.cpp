#include "schuss_rt/runtime_v1.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace schuss::rt::v1 {
namespace {

constexpr std::int64_t kQ27 = std::int64_t{1} << 27;
static_assert(std::atomic<std::uint32_t>::is_always_lock_free);
static_assert(std::atomic<std::uint64_t>::is_always_lock_free);

std::int32_t clamp_i32(std::int64_t value) noexcept {
    if (value > std::numeric_limits<std::int32_t>::max()) {
        return std::numeric_limits<std::int32_t>::max();
    }
    if (value < std::numeric_limits<std::int32_t>::min()) {
        return std::numeric_limits<std::int32_t>::min();
    }
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

std::uint32_t load_u32(const std::uint8_t* state) noexcept {
    std::uint32_t value{};
    std::memcpy(&value, state, sizeof(value));
    return value;
}

void store_u32(std::uint8_t* state, std::uint32_t value) noexcept {
    std::memcpy(state, &value, sizeof(value));
}

std::int32_t load_i32(const std::uint8_t* state) noexcept {
    std::int32_t value{};
    std::memcpy(&value, state, sizeof(value));
    return value;
}

void store_i32(std::uint8_t* state, std::int32_t value) noexcept {
    std::memcpy(state, &value, sizeof(value));
}

bool event_less(const Event& left, const Event& right) noexcept {
    if (left.frame_offset != right.frame_offset) {
        return left.frame_offset < right.frame_offset;
    }
    return left.sequence < right.sequence;
}

bool prepare_generic(const Node&) noexcept { return true; }

void reset_zero(std::uint8_t* state, std::uint32_t size) noexcept {
    if (size != 0) std::fill_n(state, size, std::uint8_t{0});
}

bool event_parameter(Node& node, const Event& event) noexcept {
    if (event.kind != EventKind::parameter_q27
        || event.parameter_index >= node.parameter_count) {
        return false;
    }
    node.parameters[event.parameter_index].value_q = event.value_q;
    return true;
}

void process_saw(Runtime& runtime, Node& node, std::uint32_t begin, std::uint32_t end) noexcept {
    auto* output = runtime.buffer(node.outputs[0].buffer_index);
    auto* state = runtime.state(node);
    std::uint32_t phase = load_u32(state);
    constexpr std::uint32_t increment = 9842633U;
    for (std::uint32_t frame = begin; frame < end; ++frame) {
        output[frame] = phase_to_q27(phase);
        phase += increment;
    }
    store_u32(state, phase);
}

void process_pwm(Runtime& runtime, Node& node, std::uint32_t begin, std::uint32_t end) noexcept {
    auto* output = runtime.buffer(node.outputs[0].buffer_index);
    auto* state = runtime.state(node);
    std::uint32_t phase = load_u32(state);
    constexpr std::uint32_t increment = 19685267U;
    for (std::uint32_t frame = begin; frame < end; ++frame) {
        const std::int32_t width = std::clamp(
            runtime.input(node, 1, frame),
            static_cast<std::int32_t>(-kQ27),
            static_cast<std::int32_t>(kQ27)
        );
        const auto threshold = static_cast<std::uint32_t>(
            (static_cast<std::int64_t>(width) + kQ27) * 16
        );
        output[frame] = phase < threshold
            ? static_cast<std::int32_t>(kQ27)
            : static_cast<std::int32_t>(-kQ27);
        phase += increment;
    }
    store_u32(state, phase);
}

void process_soft(Runtime& runtime, Node& node, std::uint32_t begin, std::uint32_t end) noexcept {
    auto* output = runtime.buffer(node.outputs[0].buffer_index);
    for (std::uint32_t frame = begin; frame < end; ++frame) {
        const std::int32_t input = std::clamp(
            runtime.input(node, 0, frame),
            static_cast<std::int32_t>(-kQ27),
            static_cast<std::int32_t>(kQ27)
        );
        const std::int32_t square = multiply_q27(input, input);
        const std::int32_t cube = multiply_q27(square, input);
        output[frame] = clamp_i32(static_cast<std::int64_t>(input) - cube / 3);
    }
}

void process_smooth(Runtime& runtime, Node& node, std::uint32_t begin, std::uint32_t end) noexcept {
    auto* output = runtime.buffer(node.outputs[0].buffer_index);
    auto* state = runtime.state(node);
    std::int32_t current = load_i32(state);
    for (std::uint32_t frame = begin; frame < end; ++frame) {
        const std::int32_t target = runtime.input(node, 0, frame);
        current = clamp_i32(
            static_cast<std::int64_t>(current)
            + (static_cast<std::int64_t>(target) - current) / 16
        );
        output[frame] = current;
    }
    store_i32(state, current);
}

void process_crossfade(Runtime& runtime, Node& node, std::uint32_t begin, std::uint32_t end) noexcept {
    auto* output = runtime.buffer(node.outputs[0].buffer_index);
    for (std::uint32_t frame = begin; frame < end; ++frame) {
        const std::int32_t fade = std::clamp(
            runtime.input(node, 2, frame),
            0,
            static_cast<std::int32_t>(kQ27)
        );
        output[frame] = clamp_i32(
            static_cast<std::int64_t>(multiply_q27(
                runtime.input(node, 0, frame),
                static_cast<std::int32_t>(kQ27) - fade
            ))
            + multiply_q27(runtime.input(node, 1, frame), fade)
        );
    }
}

void process_vca(Runtime& runtime, Node& node, std::uint32_t begin, std::uint32_t end) noexcept {
    auto* output = runtime.buffer(node.outputs[0].buffer_index);
    for (std::uint32_t frame = begin; frame < end; ++frame) {
        output[frame] = multiply_q27(
            runtime.input(node, 1, frame), runtime.input(node, 0, frame)
        );
    }
}

void process_output(Runtime&, Node&, std::uint32_t, std::uint32_t) noexcept {}

constexpr PortDescriptor no_port{"", 0};

const std::array<FactoryDescriptor, 7> kFactories{{
    {
        "saw", Role::saw, "schuss-component-contract-000012",
        "sha256:3f399547dbe7a1a76bdcedc1d1d886ccd49d0620fdbca3fbace6aac0a9d2292c",
        "schuss-implementation-000162",
        "sha256:e928bf31a0b4427d6c960d4a0d29b181912aa20635ff244673d784e3f66a413f",
        "schuss.rt.saw-q27-v0",
        {{{"component-port-000001", 21}, no_port, no_port}}, 1,
        {{{"component-port-000002", 27}, no_port}}, 1,
        {{"component-parameter-000001", "", "", ""}}, 1,
        16, 16, prepare_generic, reset_zero, event_parameter, process_saw,
    },
    {
        "pwm", Role::pwm, "schuss-component-contract-000013",
        "sha256:2c4d15d5228dadfbf9c5ecb8734e7207b7157fc8960fb4100b461b59f859daa0",
        "schuss-implementation-000163",
        "sha256:f4a9f8f06aaf286860dc31e3bf4faf1b60b786e925a307a1e3641bc576601df2",
        "schuss.rt.pwm-q27-v0",
        {{{"component-port-000001", 21}, {"component-port-000002", 27}, no_port}}, 2,
        {{{"component-port-000003", 27}, no_port}}, 1,
        {{"component-parameter-000001", "", "", ""}}, 1,
        16, 16, prepare_generic, reset_zero, event_parameter, process_pwm,
    },
    {
        "soft", Role::soft, "schuss-component-contract-000016",
        "sha256:c98e44b172cf256439edfe2f51c15499f29ffe39900d9f8de72c339e346762e2",
        "schuss-implementation-000164",
        "sha256:5444c071225361d2cff4542406fc17d4ecbfd7396884285d1a776f7c51bde7be",
        "schuss.rt.soft-q27-v0",
        {{{"component-port-000001", 27}, no_port, no_port}}, 1,
        {{{"component-port-000002", 27}, no_port}}, 1,
        {{"", "", "", ""}}, 0,
        0, 1, prepare_generic, reset_zero, event_parameter, process_soft,
    },
    {
        "smooth", Role::smooth, "schuss-component-contract-000015",
        "sha256:705b8e11c00d985eb8fd010a2d3fd71cb891f00711ad647b0746cdfb90c6ff81",
        "schuss-implementation-000165",
        "sha256:ba3859246c68f72a9c4c14ad8ccdbbac4273bcccb69f85eb1ffb100ec0db5a83",
        "schuss.rt.smooth-q27-v0",
        {{{"component-port-000001", 27}, no_port, no_port}}, 1,
        {{{"component-port-000002", 27}, no_port}}, 1,
        {{"component-parameter-000001", "", "", ""}}, 1,
        8, 8, prepare_generic, reset_zero, event_parameter, process_smooth,
    },
    {
        "crossfade", Role::crossfade, "schuss-component-contract-000003",
        "sha256:96a29faf58769be5f2ac52de07aa80cae3dcdff28f0f3c158fb1fd12cc234a8d",
        "schuss-implementation-000166",
        "sha256:31c327556140c1dc8fed576ffcaa456d0987921cf274f0b8f04e180a2c7be597",
        "schuss.rt.crossfade-q27-v0",
        {{{"component-port-000001", 27}, {"component-port-000002", 27}, {"component-port-000003", 27}}}, 3,
        {{{"component-port-000004", 27}, no_port}}, 1,
        {{"", "", "", ""}}, 0,
        0, 1, prepare_generic, reset_zero, event_parameter, process_crossfade,
    },
    {
        "vca", Role::vca, "schuss-component-contract-000020",
        "sha256:0cf9737582327560e82feb565fd3092993b750938a9669fc43305b5658ac5490",
        "schuss-implementation-000167",
        "sha256:c05655fe1840bea79d9b6bf03e27231cea440ccde23f2ee7b75e5c5216893c28",
        "schuss.rt.vca-q27-v0",
        {{{"component-port-000001", 27}, {"component-port-000002", 27}, no_port}}, 2,
        {{{"component-port-000003", 27}, no_port}}, 1,
        {{"", "", "", ""}}, 0,
        8, 8, prepare_generic, reset_zero, event_parameter, process_vca,
    },
    {
        "output", Role::output, "schuss-component-contract-000009",
        "sha256:179c1526ed2bd6d9ad1c6fbfc9caa7abc21f479bef50cf93c8599b5817ca8718",
        "schuss-implementation-000168",
        "sha256:6dda7b4532e2e1798c0f1d7bcf67d74846f7e407456ecc3aaba57b24948af33f",
        "schuss.rt.output-q27-v0",
        {{{"component-port-000001", 27}, {"component-port-000002", 27}, no_port}}, 2,
        {{no_port, no_port}}, 0,
        {{"", "", "", ""}}, 0,
        0, 1, prepare_generic, reset_zero, event_parameter, process_output,
    },
}};

}  // namespace

const std::array<FactoryDescriptor, 7>& factory_registry() noexcept {
    return kFactories;
}

const FactoryDescriptor* find_factory(std::string_view factory_id) noexcept {
    const auto found = std::find_if(
        kFactories.begin(), kFactories.end(),
        [factory_id](const FactoryDescriptor& descriptor) {
            return descriptor.factory_id == factory_id;
        }
    );
    return found == kFactories.end() ? nullptr : &*found;
}

Result Runtime::prepare(const PreparedPackage& package) {
    if (package.nodes.size() < 2 || package.nodes.size() > kMaximumNodes
        || package.schedule.size() != package.nodes.size()
        || package.buffer_count == 0 || package.buffer_count > kMaximumBuffers
        || package.buffer_frames != kMaximumBlockFrames
        || package.state_bytes == 0 || package.state_bytes > kMaximumStateBytes
        || package.parameter_count > kMaximumParameters
        || package.event_capacity == 0 || package.event_capacity > kMaximumEvents) {
        return {ErrorCode::package_shape_invalid, "HOST_V1_PREPARE_PACKAGE_INVALID"};
    }
    for (const Node& node : package.nodes) {
        if (node.factory_index >= kFactories.size()
            || !kFactories[node.factory_index].prepare(node)) {
            return {ErrorCode::package_shape_invalid, "HOST_V1_FACTORY_PREPARE_FAILED"};
        }
    }
    package_ = package;
    state_.assign(package.state_bytes, 0);
    buffers_.assign(
        static_cast<std::size_t>(package.buffer_count) * package.buffer_frames, 0
    );
    event_ring_.assign(static_cast<std::size_t>(package.event_capacity) + 1U, {});
    callback_events_.clear();
    callback_events_.reserve(package.event_capacity);
    prepared_ = true;
    reset();
    return {};
}

void Runtime::reset() noexcept {
    std::fill(state_.begin(), state_.end(), std::uint8_t{0});
    std::fill(buffers_.begin(), buffers_.end(), 0);
    for (Node& node : package_.nodes) {
        const auto& descriptor = kFactories[node.factory_index];
        descriptor.reset(state(node), node.state_size_bytes);
    }
    event_write_.store(0, std::memory_order_relaxed);
    event_read_.store(0, std::memory_order_relaxed);
    queue_overflows_.store(0, std::memory_order_relaxed);
    processed_frames_.store(0, std::memory_order_relaxed);
    events_delivered_.store(0, std::memory_order_relaxed);
}

bool Runtime::enqueue(const Event& event) noexcept {
    if (!prepared_ || event_ring_.empty() || event.frame_offset >= kMaximumBlockFrames) {
        return false;
    }
    if (event.kind == EventKind::parameter_q27) {
        if (event.node_index >= package_.nodes.size()
            || event.parameter_index
                >= package_.nodes[event.node_index].parameter_count) {
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

std::int32_t* Runtime::buffer(std::uint8_t index) noexcept {
    return buffers_.data() + static_cast<std::size_t>(index) * package_.buffer_frames;
}

const std::int32_t* Runtime::buffer(std::uint8_t index) const noexcept {
    return buffers_.data() + static_cast<std::size_t>(index) * package_.buffer_frames;
}

std::uint8_t* Runtime::state(const Node& node) noexcept {
    return state_.data() + node.state_offset_bytes;
}

std::int32_t Runtime::input(
    const Node& node, std::size_t input_index, std::uint32_t frame
) const noexcept {
    const Input& input_value = node.inputs[input_index];
    return input_value.source == InputSource::buffer
        ? buffer(input_value.buffer_index)[frame]
        : input_value.value_q;
}

std::int32_t Runtime::parameter(
    const Node& node, std::string_view facet, std::int32_t fallback
) const noexcept {
    for (std::uint8_t index = 0; index < node.parameter_count; ++index) {
        if (node.parameters[index].facet_id == facet) {
            return node.parameters[index].value_q;
        }
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
    const auto& descriptor = kFactories[node.factory_index];
    if (descriptor.event(node, event)) {
        events_delivered_.fetch_add(1, std::memory_order_relaxed);
    }
}

void Runtime::process_segment(std::uint32_t begin, std::uint32_t end) noexcept {
    if (begin >= end) return;
    for (const std::uint8_t scheduled : package_.schedule) {
        Node& node = package_.nodes[scheduled];
        kFactories[node.factory_index].process(*this, node, begin, end);
    }
}

Result Runtime::process(
    std::int32_t* left_q27,
    std::int32_t* right_q27,
    std::uint32_t frames
) noexcept {
    if (!prepared_) return {ErrorCode::not_prepared, "HOST_V1_RUNTIME_NOT_PREPARED"};
    if (frames == 0 || frames > package_.buffer_frames) {
        return {ErrorCode::block_too_large, "HOST_V1_BLOCK_FRAMES_INVALID"};
    }
    if (left_q27 == nullptr || right_q27 == nullptr) {
        return {ErrorCode::package_shape_invalid, "HOST_V1_OUTPUT_POINTER_INVALID"};
    }
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
    std::copy_n(buffer(package_.left_buffer), frames, left_q27);
    std::copy_n(buffer(package_.right_buffer), frames, right_q27);
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

}  // namespace schuss::rt::v1
