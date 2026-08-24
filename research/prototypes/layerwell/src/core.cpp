#include "layerwell/core.hpp"

#include "layerwell/source_adapters.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <new>
#include <utility>

namespace layerwell {
namespace {

constexpr double kQ27ToFloat = 1.0 / 134217728.0;
constexpr float kDefaultLayerLevel = 0.45f;
constexpr float kDefaultMonitorLevel = 0.35f;
constexpr float kDefaultMasterLevel = 0.55f;
constexpr double kPi = 3.14159265358979323846264338327950288;

bool sourceQuantized(EventKind kind) noexcept {
    switch (kind) {
        case EventKind::source_previous:
        case EventKind::source_next:
        case EventKind::select_source:
        case EventKind::source_encoder_relative:
        case EventKind::source_button:
            return true;
        default:
            return false;
    }
}

std::uint32_t quantizeSourceOffset(std::uint32_t offset) noexcept {
    return ((offset + kSourceQuantumFrames - 1U) / kSourceQuantumFrames)
        * kSourceQuantumFrames;
}

bool midiByte(double value, std::uint8_t& result) noexcept {
    if (!std::isfinite(value) || value < 0.0 || value > 127.0) return false;
    const auto rounded = std::lround(value);
    if (std::abs(value - static_cast<double>(rounded)) > 0.000001) return false;
    result = static_cast<std::uint8_t>(rounded);
    return true;
}

float boundedOrDefault(
    double value,
    float minimum,
    float maximum,
    float fallback,
    Diagnostics& diagnostics) noexcept {
    if (!std::isfinite(value)) {
        ++diagnostics.non_finite_mix_samples;
        return fallback;
    }
    return static_cast<float>(std::clamp(value,
        static_cast<double>(minimum),
        static_cast<double>(maximum)));
}

float seamGain(std::uint32_t phase, std::uint32_t length) noexcept {
    if (length < 4U || phase >= length) return 0.0f;
    const auto fade = std::min(kSeamFrames, length / 2U);
    if (fade < 2U) return 0.0f;
    const auto denominator = static_cast<float>(fade - 1U);
    if (phase < fade) return static_cast<float>(phase) / denominator;
    if (phase >= length - fade) {
        return static_cast<float>(length - 1U - phase) / denominator;
    }
    return 1.0f;
}

}  // namespace

struct Core::Impl final {
    struct StereoStore final {
        std::unique_ptr<float[]> left{};
        std::unique_ptr<float[]> right{};
    };

    struct OrderedEvent final {
        Event event{};
        std::uint32_t effective_offset{};
    };

    SourceRack sources{};
    std::array<StereoStore, kStoreCount> stores{};
    std::array<LayerSnapshot, kLayerCount> layers{};
    std::array<float, kLayerCount> pan_left{};
    std::array<float, kLayerCount> pan_right{};
    std::array<std::int32_t, kMaximumBlockFrames> source_left_q27{};
    std::array<std::int32_t, kMaximumBlockFrames> source_right_q27{};
    Diagnostics diagnostics{};
    std::uint64_t absolute_frame{};
    std::uint64_t accepted_sequence{};
    std::uint32_t maximum_block_frames{kMaximumBlockFrames};
    std::uint32_t loop_length{};
    std::uint32_t phase{};
    std::uint32_t capture_write_head{};
    std::uint8_t staging_owner{3U};
    std::uint8_t selected_layer{};
    std::uint8_t capture_layer{};
    SourceId selected_source{SourceId::tide_pit};
    SourceId capture_source{SourceId::tide_pit};
    CaptureState capture_state{CaptureState::idle};
    SurfaceMode surface_mode{SurfaceMode::mixer};
    float monitor_level{kDefaultMonitorLevel};
    float master_level{kDefaultMasterLevel};
    bool monitor_enabled{true};
    bool prepared{};
    bool panic_source_silence{};

    bool storageAllocated() const noexcept {
        for (const auto& store : stores) {
            if (store.left == nullptr || store.right == nullptr) return false;
        }
        return true;
    }

    void updatePan(std::size_t layer) noexcept {
        if (layer >= layers.size()) return;
        const auto theta = (static_cast<double>(layers[layer].pan) + 1.0)
            * kPi * 0.25;
        pan_left[layer] = static_cast<float>(std::cos(theta));
        pan_right[layer] = static_cast<float>(std::sin(theta));
    }

    void clearMusicalState() noexcept {
        for (std::size_t layer = 0U; layer < layers.size(); ++layer) {
            layers[layer] = LayerSnapshot{};
            layers[layer].level = kDefaultLayerLevel;
            layers[layer].store_owner = static_cast<std::uint8_t>(layer);
            updatePan(layer);
        }
        staging_owner = 3U;
        selected_layer = 0U;
        capture_layer = 0U;
        selected_source = SourceId::tide_pit;
        capture_source = SourceId::tide_pit;
        capture_state = CaptureState::idle;
        surface_mode = SurfaceMode::mixer;
        loop_length = 0U;
        phase = 0U;
        capture_write_head = 0U;
        monitor_level = kDefaultMonitorLevel;
        master_level = kDefaultMasterLevel;
        monitor_enabled = true;
        absolute_frame = 0U;
        accepted_sequence = 0U;
        panic_source_silence = false;
        diagnostics = Diagnostics{};
        diagnostics.sample_storage_bytes = kSampleStorageBytes;
    }

    void zeroStorage() noexcept {
        for (auto& store : stores) {
            if (store.left != nullptr) {
                std::fill_n(store.left.get(), kMaximumLoopFrames, 0.0f);
            }
            if (store.right != nullptr) {
                std::fill_n(store.right.get(), kMaximumLoopFrames, 0.0f);
            }
        }
    }

    bool busyCapture() const noexcept {
        return capture_state != CaptureState::idle;
    }

    bool anyOccupied() const noexcept {
        for (const auto& layer : layers) {
            if (layer.occupied) return true;
        }
        return false;
    }

    bool abortCapture(bool cancelled, ProcessReport& report) noexcept {
        if (!busyCapture()) return false;
        capture_state = CaptureState::idle;
        capture_write_head = 0U;
        if (cancelled) {
            ++diagnostics.capture_cancels;
        } else {
            ++diagnostics.capture_aborts;
            report.capture_aborted = true;
        }
        return true;
    }

    bool commitCapture(bool first_capture) noexcept {
        const auto length = first_capture ? capture_write_head : loop_length;
        if (length == 0U || length > kMaximumLoopFrames) return false;
        if (first_capture && length < kMinimumLoopFrames) return false;

        auto& target = layers[capture_layer];
        std::swap(target.store_owner, staging_owner);
        target.occupied = true;
        if (first_capture) {
            loop_length = length;
            phase = 0U;
        }
        capture_state = CaptureState::idle;
        capture_write_head = 0U;
        monitor_enabled = false;
        ++diagnostics.capture_commits;
        return true;
    }

    bool handleCapturePress(ProcessReport& report) noexcept {
        if (capture_state == CaptureState::waiting_boundary) {
            abortCapture(true, report);
            return true;
        }
        if (capture_state == CaptureState::recording) {
            if (loop_length != 0U) {
                abortCapture(true, report);
                return true;
            }
            if (capture_write_head < kMinimumLoopFrames) {
                ++diagnostics.short_capture_rejections;
                abortCapture(false, report);
                return true;
            }
            if (!commitCapture(true)) {
                abortCapture(false, report);
            }
            return true;
        }

        capture_layer = selected_layer;
        capture_source = selected_source;
        capture_write_head = 0U;
        if (loop_length == 0U || phase == 0U) {
            capture_state = CaptureState::recording;
            ++diagnostics.capture_starts;
        } else {
            capture_state = CaptureState::waiting_boundary;
            ++diagnostics.capture_arms;
        }
        return true;
    }

    void beginWaitingCaptureIfDue() noexcept {
        if (capture_state != CaptureState::waiting_boundary
            || loop_length == 0U
            || phase != 0U) {
            return;
        }
        capture_state = CaptureState::recording;
        capture_write_head = 0U;
        ++diagnostics.capture_starts;
    }

    bool applyEvent(const Event& event, ProcessReport& report) noexcept {
        auto accept = [&]() noexcept {
            accepted_sequence = std::max(accepted_sequence, event.ingress_sequence);
            ++diagnostics.accepted_events;
            ++report.events_accepted;
            return true;
        };
        auto reject = [&]() noexcept {
            ++diagnostics.rejected_events;
            ++report.events_rejected;
            return false;
        };

        switch (event.kind) {
            case EventKind::source_previous:
            case EventKind::source_next:
            case EventKind::select_source: {
                if (busyCapture()) return reject();
                std::uint8_t index{};
                if (event.kind == EventKind::source_previous) {
                    index = selected_source == SourceId::tide_pit ? 1U : 0U;
                } else if (event.kind == EventKind::source_next) {
                    index = selected_source == SourceId::tide_pit ? 1U : 0U;
                } else {
                    index = event.index;
                }
                if (index > 1U) return reject();
                selected_source = static_cast<SourceId>(index);
                monitor_enabled = true;
                return accept();
            }
            case EventKind::layer_previous:
            case EventKind::layer_next:
            case EventKind::select_layer: {
                if (busyCapture()) return reject();
                std::uint8_t index{};
                if (event.kind == EventKind::layer_previous) {
                    index = static_cast<std::uint8_t>(
                        (selected_layer + kLayerCount - 1U) % kLayerCount);
                } else if (event.kind == EventKind::layer_next) {
                    index = static_cast<std::uint8_t>(
                        (selected_layer + 1U) % kLayerCount);
                } else {
                    index = event.index;
                }
                if (index >= kLayerCount) return reject();
                selected_layer = index;
                return accept();
            }
            case EventKind::source_encoder_relative: {
                std::uint8_t value{};
                if (!midiByte(event.value, value) || event.index >= 16U) return reject();
                const auto status = sources.applyRelativeEncoder(
                    selected_source, event.index, value, event.ingress_sequence);
                if (status != SourceControlStatus::accepted) return reject();
                return accept();
            }
            case EventKind::source_button: {
                std::uint8_t value{};
                if (!midiByte(event.value, value) || event.index >= 8U) return reject();
                const auto status = sources.applyButton(
                    selected_source, event.index, value, event.ingress_sequence);
                if (status != SourceControlStatus::accepted
                    && status != SourceControlStatus::accepted_release) {
                    return reject();
                }
                return accept();
            }
            case EventKind::adjust_layer_pan:
            case EventKind::adjust_layer_level:
            case EventKind::adjust_monitor_level:
            case EventKind::adjust_master_level: {
                std::uint8_t value{};
                if (!midiByte(event.value, value)) return reject();
                const auto delta = static_cast<int>(value) - 64;
                if (event.kind == EventKind::adjust_layer_pan) {
                    if (event.index >= kLayerCount) return reject();
                    layers[event.index].pan = std::clamp(
                        layers[event.index].pan + static_cast<float>(delta) / 64.0f,
                        -1.0f, 1.0f);
                    updatePan(event.index);
                } else if (event.kind == EventKind::adjust_layer_level) {
                    if (event.index >= kLayerCount) return reject();
                    layers[event.index].level = std::clamp(
                        layers[event.index].level + static_cast<float>(delta) / 127.0f,
                        0.0f, 1.0f);
                } else if (event.kind == EventKind::adjust_monitor_level) {
                    monitor_level = std::clamp(
                        monitor_level + static_cast<float>(delta) / 127.0f,
                        0.0f, 1.0f);
                } else {
                    master_level = std::clamp(
                        master_level + static_cast<float>(delta) / 127.0f,
                        0.0f, 1.0f);
                }
                return accept();
            }
            case EventKind::set_layer_pan:
                if (event.index >= kLayerCount) return reject();
                layers[event.index].pan = boundedOrDefault(
                    event.value, -1.0f, 1.0f, 0.0f, diagnostics);
                updatePan(event.index);
                return accept();
            case EventKind::set_layer_level:
                if (event.index >= kLayerCount) return reject();
                layers[event.index].level = boundedOrDefault(
                    event.value, 0.0f, 1.0f, kDefaultLayerLevel, diagnostics);
                return accept();
            case EventKind::set_monitor_level:
                monitor_level = boundedOrDefault(
                    event.value, 0.0f, 1.0f, kDefaultMonitorLevel, diagnostics);
                return accept();
            case EventKind::set_master_level:
                master_level = boundedOrDefault(
                    event.value, 0.0f, 1.0f, kDefaultMasterLevel, diagnostics);
                return accept();
            case EventKind::toggle_layer_mute:
                if (event.index >= kLayerCount) return reject();
                layers[event.index].muted = !layers[event.index].muted;
                return accept();
            case EventKind::capture_press:
                handleCapturePress(report);
                return accept();
            case EventKind::toggle_monitor:
                monitor_enabled = !monitor_enabled;
                return accept();
            case EventKind::clear_selected_layer:
                if (busyCapture()) return reject();
                if (layers[selected_layer].occupied) {
                    layers[selected_layer].occupied = false;
                    ++diagnostics.cleared_layers;
                    if (!anyOccupied()) {
                        loop_length = 0U;
                        phase = 0U;
                    }
                }
                return accept();
            case EventKind::set_surface_mode:
                if (event.index > 1U) return reject();
                surface_mode = static_cast<SurfaceMode>(event.index);
                return accept();
            case EventKind::panic:
                abortCapture(false, report);
                panic_source_silence = true;
                ++diagnostics.panic_count;
                return accept();
        }
        return reject();
    }

    void recordSourceSample(
        float left,
        float right,
        ProcessReport& report) noexcept {
        if (capture_state != CaptureState::recording) return;
        if (!std::isfinite(left) || !std::isfinite(right)
            || capture_write_head >= kMaximumLoopFrames) {
            abortCapture(false, report);
            return;
        }
        auto& staging = stores[staging_owner];
        staging.left[capture_write_head] = left;
        staging.right[capture_write_head] = right;
        ++capture_write_head;
    }

    void completeCaptureAfterSample(ProcessReport& report) noexcept {
        if (capture_state != CaptureState::recording) return;
        if (loop_length == 0U) {
            if (capture_write_head == kMaximumLoopFrames
                && !commitCapture(true)) {
                abortCapture(false, report);
            }
            return;
        }
        if (capture_write_head == loop_length
            && !commitCapture(false)) {
            abortCapture(false, report);
        }
    }

    float mixChannel(float source, bool right_channel) noexcept {
        double mixed = monitor_enabled
            ? static_cast<double>(monitor_level) * static_cast<double>(source)
            : 0.0;
        if (loop_length != 0U) {
            const auto seam = static_cast<double>(seamGain(phase, loop_length));
            for (std::size_t index = 0U; index < layers.size(); ++index) {
                const auto& layer = layers[index];
                if (!layer.occupied || layer.muted) continue;
                const auto& store = stores[layer.store_owner];
                const auto sample = right_channel
                    ? store.right[phase]
                    : store.left[phase];
                const auto pan = right_channel ? pan_right[index] : pan_left[index];
                mixed += static_cast<double>(sample)
                    * seam
                    * static_cast<double>(layer.level)
                    * static_cast<double>(pan);
            }
        }
        mixed *= static_cast<double>(master_level);
        if (!std::isfinite(mixed)) {
            ++diagnostics.non_finite_mix_samples;
            return 0.0f;
        }
        if (mixed > 1.0) {
            ++diagnostics.limited_samples;
            return 1.0f;
        }
        if (mixed < -1.0) {
            ++diagnostics.limited_samples;
            return -1.0f;
        }
        return static_cast<float>(mixed);
    }

    void advanceTransport() noexcept {
        if (loop_length == 0U) {
            phase = 0U;
            return;
        }
        ++phase;
        if (phase == loop_length) phase = 0U;
    }
};

Core::Core() : impl_(std::make_unique<Impl>()) {}
Core::~Core() = default;
Core::Core(Core&&) noexcept = default;
Core& Core::operator=(Core&&) noexcept = default;

bool Core::prepare(double sample_rate, std::uint32_t maximum_block_frames) noexcept {
    if (sample_rate != kSampleRate
        || maximum_block_frames == 0U
        || maximum_block_frames > kMaximumBlockFrames
        || maximum_block_frames % kSourceQuantumFrames != 0U) {
        ++impl_->diagnostics.prepare_failures;
        impl_->prepared = false;
        return false;
    }

    std::array<Impl::StereoStore, kStoreCount> fresh{};
    for (auto& store : fresh) {
        store.left.reset(new (std::nothrow) float[kMaximumLoopFrames]);
        store.right.reset(new (std::nothrow) float[kMaximumLoopFrames]);
        if (store.left == nullptr || store.right == nullptr) {
            ++impl_->diagnostics.prepare_failures;
            impl_->prepared = false;
            return false;
        }
        std::fill_n(store.left.get(), kMaximumLoopFrames, 0.0f);
        std::fill_n(store.right.get(), kMaximumLoopFrames, 0.0f);
    }

    if (!impl_->sources.prepare(sample_rate, maximum_block_frames)) {
        ++impl_->diagnostics.prepare_failures;
        impl_->prepared = false;
        return false;
    }
    impl_->stores = std::move(fresh);
    impl_->maximum_block_frames = maximum_block_frames;
    impl_->clearMusicalState();
    impl_->prepared = true;
    return true;
}

bool Core::reset() noexcept {
    if (!impl_->prepared || !impl_->storageAllocated()) return false;
    if (!impl_->sources.reset()) {
        impl_->prepared = false;
        return false;
    }
    impl_->zeroStorage();
    impl_->clearMusicalState();
    impl_->prepared = true;
    return true;
}

ProcessReport Core::process(
    float* output_left,
    float* output_right,
    std::uint32_t frames,
    const Event* events,
    std::size_t event_count) noexcept {
    ProcessReport report{};
    if (output_left == nullptr
        || output_right == nullptr
        || !impl_->prepared
        || !impl_->storageAllocated()
        || frames == 0U
        || frames > impl_->maximum_block_frames
        || frames % kSourceQuantumFrames != 0U) {
        if (output_left != nullptr) std::fill_n(output_left, frames, 0.0f);
        if (output_right != nullptr) std::fill_n(output_right, frames, 0.0f);
        ++impl_->diagnostics.unsupported_process_calls;
        return report;
    }

    std::fill_n(output_left, frames, 0.0f);
    std::fill_n(output_right, frames, 0.0f);
    impl_->panic_source_silence = false;

    std::array<Impl::OrderedEvent, kMaximumEvents> ordered{};
    std::size_t ordered_count = 0U;
    if (event_count > kMaximumEvents || (event_count != 0U && events == nullptr)) {
        report.events_dropped = event_count;
        impl_->diagnostics.dropped_events += event_count;
        impl_->abortCapture(false, report);
    } else {
        for (std::size_t index = 0U; index < event_count; ++index) {
            if (events[index].sample_offset > frames) {
                ++report.events_dropped;
                ++impl_->diagnostics.dropped_events;
                continue;
            }
            auto effective = events[index].sample_offset;
            if (sourceQuantized(events[index].kind)) {
                effective = quantizeSourceOffset(effective);
                if (effective != events[index].sample_offset) {
                    ++impl_->diagnostics.source_events_quantized;
                }
            }
            Impl::OrderedEvent next{events[index], effective};
            auto position = ordered_count;
            while (position > 0U) {
                const auto& previous = ordered[position - 1U];
                if (previous.effective_offset < next.effective_offset
                    || (previous.effective_offset == next.effective_offset
                        && previous.event.ingress_sequence
                            <= next.event.ingress_sequence)) {
                    break;
                }
                ordered[position] = previous;
                --position;
            }
            ordered[position] = next;
            ++ordered_count;
        }
    }

    std::size_t next_event = 0U;
    auto applyAt = [&](std::uint32_t offset) noexcept {
        while (next_event < ordered_count
            && ordered[next_event].effective_offset == offset) {
            impl_->applyEvent(ordered[next_event].event, report);
            ++next_event;
        }
    };

    for (std::uint32_t quantum = 0U;
         quantum < frames;
         quantum += kSourceQuantumFrames) {
        applyAt(quantum);
        const auto source_ok = impl_->sources.render(
            impl_->selected_source,
            impl_->source_left_q27.data() + quantum,
            impl_->source_right_q27.data() + quantum,
            kSourceQuantumFrames);
        if (!source_ok) {
            std::fill_n(
                impl_->source_left_q27.data() + quantum,
                kSourceQuantumFrames,
                0);
            std::fill_n(
                impl_->source_right_q27.data() + quantum,
                kSourceQuantumFrames,
                0);
            ++impl_->diagnostics.source_process_failures;
            report.source_failed = true;
            impl_->abortCapture(false, report);
        }

        for (std::uint32_t local = 0U; local < kSourceQuantumFrames; ++local) {
            const auto frame = quantum + local;
            if (local != 0U) applyAt(frame);
            impl_->beginWaitingCaptureIfDue();

            auto source_left = static_cast<float>(
                static_cast<double>(impl_->source_left_q27[frame]) * kQ27ToFloat);
            auto source_right = static_cast<float>(
                static_cast<double>(impl_->source_right_q27[frame]) * kQ27ToFloat);
            if (!std::isfinite(source_left) || !std::isfinite(source_right)) {
                ++impl_->diagnostics.non_finite_source_samples;
                source_left = 0.0f;
                source_right = 0.0f;
                impl_->abortCapture(false, report);
            }
            if (impl_->panic_source_silence) {
                source_left = 0.0f;
                source_right = 0.0f;
            }

            impl_->recordSourceSample(source_left, source_right, report);
            output_left[frame] = impl_->mixChannel(source_left, false);
            output_right[frame] = impl_->mixChannel(source_right, true);
            impl_->advanceTransport();
            impl_->completeCaptureAfterSample(report);
            ++impl_->absolute_frame;
        }
    }
    applyAt(frames);

    impl_->diagnostics.processed_frames += frames;
    ++impl_->diagnostics.snapshot_sequence;
    return report;
}

Snapshot Core::snapshot() const noexcept {
    Snapshot result{};
    result.layers = impl_->layers;
    result.diagnostics = impl_->diagnostics;
    result.absolute_frame = impl_->absolute_frame;
    result.accepted_sequence = impl_->accepted_sequence;
    result.loop_length_frames = impl_->loop_length;
    result.phase_frames = impl_->phase;
    result.capture_write_head = impl_->capture_write_head;
    result.monitor_level = impl_->monitor_level;
    result.master_level = impl_->master_level;
    result.selected_source = impl_->selected_source;
    result.capture_source = impl_->capture_source;
    result.capture_state = impl_->capture_state;
    result.surface_mode = impl_->surface_mode;
    result.selected_layer = impl_->selected_layer;
    result.capture_layer = impl_->capture_layer;
    result.monitor_enabled = impl_->monitor_enabled;
    result.prepared = impl_->prepared;

    const auto selected = impl_->sources.projection(impl_->selected_source);
    result.source_encoder_values = selected.encoder_values;
    result.source_encoder_assigned = selected.encoder_assigned;
    result.source_button_assigned = selected.button_assigned;
    result.source_button_active = selected.button_active;
    result.source_processed_frames[0] =
        impl_->sources.projection(SourceId::tide_pit).processed_frames;
    result.source_processed_frames[1] =
        impl_->sources.projection(SourceId::generative_drums).processed_frames;
    return result;
}

Diagnostics Core::diagnostics() const noexcept {
    return impl_->diagnostics;
}

bool Core::isPrepared() const noexcept {
    return impl_->prepared;
}

std::uint32_t Core::maximumBlockFrames() const noexcept {
    return impl_->maximum_block_frames;
}

const float* Core::committedSamples(
    std::size_t layer,
    std::size_t channel) const noexcept {
    if (layer >= impl_->layers.size() || channel > 1U || !impl_->storageAllocated()) {
        return nullptr;
    }
    const auto& store = impl_->stores[impl_->layers[layer].store_owner];
    return channel == 0U ? store.left.get() : store.right.get();
}

const char* sourceName(SourceId source) noexcept {
    switch (source) {
        case SourceId::tide_pit: return "TIDE PIT";
        case SourceId::generative_drums: return "GENERATIVE DRUMS";
    }
    return "INVALID";
}

const char* captureStateName(CaptureState state) noexcept {
    switch (state) {
        case CaptureState::idle: return "IDLE";
        case CaptureState::waiting_boundary: return "ARMED";
        case CaptureState::recording: return "RECORDING";
    }
    return "INVALID";
}

const char* surfaceModeName(SurfaceMode mode) noexcept {
    switch (mode) {
        case SurfaceMode::mixer: return "MIXER";
        case SurfaceMode::control: return "CONTROL";
    }
    return "INVALID";
}

}  // namespace layerwell
