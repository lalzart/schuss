#include "tidepit/core.hpp"

#include "tidepit_port_overlay.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <new>
#include <utility>

namespace tidepit_port_detail {

struct ArenaContext {
    std::byte* data{};
    std::size_t capacity{};
    std::size_t offset{};
    std::size_t allocations{};
    bool failed{};
    bool alignment_valid{true};
};

thread_local ArenaContext* active_arena = nullptr;

}  // namespace tidepit_port_detail

void* sdram_malloc(std::size_t bytes) noexcept {
    auto* const arena = tidepit_port_detail::active_arena;
    if (arena == nullptr || bytes > arena->capacity - arena->offset) {
        if (arena != nullptr) arena->failed = true;
        return nullptr;
    }
    void* const result = arena->data + arena->offset;
    arena->alignment_valid = arena->alignment_valid &&
        reinterpret_cast<std::uintptr_t>(result) % alignof(std::max_align_t) == 0;
    arena->offset += bytes;
    ++arena->allocations;
    return result;
}

namespace tidepit {
namespace {

constexpr std::uint32_t kEffectTapHighBlocks = 76;
constexpr std::uint32_t kEffectCaptureHighBlocks = 1575;
constexpr std::uint32_t kEffectReleaseBlocks = 76;
constexpr std::uint32_t kScaleTapHighBlocks = 9;
constexpr std::uint32_t kTargetHoldHighBlocks = 1508;
constexpr std::uint32_t kEncoderReleaseBlocks = 9;
constexpr std::size_t kMaximumQueuedGestures = 16;

constexpr std::array<std::array<std::int8_t, 6>, 4> kScales{{
    {{0, 2, 4, 7, 9, 12}},
    {{0, 2, 3, 5, 7, 10}},
    {{0, 2, 3, 5, 7, 9}},
    {{0, 3, 5, 7, 10, 12}},
}};

bool isContinuous(SemanticAction action) noexcept {
    return action <= SemanticAction::set_root;
}

bool isValidAction(SemanticAction action) noexcept {
    return action <= SemanticAction::target_next;
}

bool isNormalized(double value) noexcept {
    return std::isfinite(value) && value >= 0.0 && value <= 1.0;
}

std::int32_t normalizedRoot(double normalized) noexcept {
    return 36 + static_cast<std::int32_t>(std::floor(normalized * 36.0 + 0.5));
}

std::int32_t toQ27(float value) noexcept {
    return static_cast<std::int32_t>(value * 134217728.0f);
}

std::uint64_t ceilToQuantum(std::uint64_t sample) noexcept {
    constexpr std::uint64_t mask = kReferenceQuantumFrames - 1U;
    return (sample + mask) & ~mask;
}

template <typename Enum>
Enum boundedEnum(std::uint8_t value, std::uint8_t count) noexcept {
    return static_cast<Enum>(value < count ? value : 0U);
}

struct PulseLane {
    std::uint8_t pending{};
    bool was_high{};

    bool request() noexcept {
        if (pending == std::numeric_limits<std::uint8_t>::max()) return false;
        ++pending;
        return true;
    }

    bool level() noexcept {
        if (was_high || pending == 0) return false;
        --pending;
        return true;
    }

    void advance(bool current) noexcept { was_high = current; }
};

enum class GestureKind : std::uint8_t { effect_tap, capture_hold, scale_tap, target_hold };

struct GestureLane {
    std::array<GestureKind, kMaximumQueuedGestures> queue{};
    std::size_t read{};
    std::size_t count{};
    std::uint32_t high_remaining{};
    std::uint32_t low_remaining{};

    bool active() const noexcept {
        return high_remaining != 0 || low_remaining != 0;
    }

    static std::uint32_t highBlocks(GestureKind kind) noexcept {
        switch (kind) {
            case GestureKind::effect_tap: return kEffectTapHighBlocks;
            case GestureKind::capture_hold: return kEffectCaptureHighBlocks;
            case GestureKind::scale_tap: return kScaleTapHighBlocks;
            case GestureKind::target_hold: return kTargetHoldHighBlocks;
        }
        return 0;
    }

    static std::uint32_t lowBlocks(GestureKind kind) noexcept {
        return kind == GestureKind::effect_tap || kind == GestureKind::capture_hold
            ? kEffectReleaseBlocks
            : kEncoderReleaseBlocks;
    }

    void start(GestureKind kind) noexcept {
        high_remaining = highBlocks(kind);
        low_remaining = lowBlocks(kind);
    }

    bool request(GestureKind kind) noexcept {
        if (!active() && count == 0) {
            start(kind);
            return true;
        }
        if (count == queue.size()) return false;
        queue[(read + count) % queue.size()] = kind;
        ++count;
        return true;
    }

    bool level() const noexcept { return high_remaining != 0; }

    void advance() noexcept {
        if (high_remaining != 0) {
            --high_remaining;
            return;
        }
        if (low_remaining != 0) {
            --low_remaining;
            if (low_remaining != 0 || count == 0) return;
            const auto kind = queue[read];
            read = (read + 1U) % queue.size();
            --count;
            start(kind);
        }
    }
};

}  // namespace

struct Core::Impl {
    struct PendingEvent {
        std::uint64_t quantized_sample{};
        std::uint64_t ingress_sequence{};
        SemanticAction action{SemanticAction::set_stage_1};
        double value{};
    };

    alignas(std::max_align_t) std::array<std::byte, kSourceArenaBytes> arena{};
    alignas(Instrument) std::array<std::byte, sizeof(Instrument)> instrument_storage{};
    Instrument* instrument{};
    std::uint32_t lcg_state{0x21U};
    bool prepared{};
    double sample_rate{};
    std::uint32_t maximum_block_frames{kMaximumBlockFrames};
    Controls controls{};
    Diagnostics diagnostics{};
    std::array<PendingEvent, kMaximumSemanticEvents> pending_events{};
    std::size_t pending_event_count{};
    PulseLane source_pulse{};
    PulseLane mutate_pulse{};
    PulseLane lock_pulse{};
    GestureLane effect_gesture{};
    GestureLane encoder_gesture{};

    ~Impl() { destroyInstrument(); }

    void destroyInstrument() noexcept {
        if (instrument == nullptr) return;
        instrument->~Instrument();
        instrument = nullptr;
    }

    void resetOwnedState() noexcept {
        destroyInstrument();
        std::memset(instrument_storage.data(), 0, instrument_storage.size());
        std::memset(arena.data(), 0, arena.size());
        controls = Controls{};
        pending_events = {};
        pending_event_count = 0;
        source_pulse = {};
        mutate_pulse = {};
        lock_pulse = {};
        effect_gesture = {};
        encoder_gesture = {};
        lcg_state = 0x21U;
    }

    bool initializeSource() noexcept {
        tidepit_port_detail::ArenaContext arena_context{
            arena.data(), arena.size(), 0, 0, false, true,
        };
        tidepit_port_detail::active_arena = &arena_context;

        instrument = ::new (static_cast<void*>(instrument_storage.data())) Instrument;
        const auto previous_lcg = stmlib::Random::state();
        stmlib::Random::Seed(0x21U);
        instrument->Init();
        lcg_state = stmlib::Random::state();
        stmlib::Random::Seed(previous_lcg);
        tidepit_port_detail::active_arena = nullptr;

        diagnostics.arena_allocations = static_cast<std::uint32_t>(arena_context.allocations);
        diagnostics.arena_bytes = static_cast<std::uint32_t>(arena_context.offset);
        diagnostics.arena_alignment_valid = arena_context.alignment_valid;
        return !arena_context.failed &&
            arena_context.alignment_valid &&
            arena_context.allocations == kSourceArenaAllocations &&
            arena_context.offset == kSourceArenaBytes &&
            instrument->granular_available() &&
            instrument->waveguide_.available() &&
            instrument->sympathetic_.available() &&
            instrument->reverb_.available();
    }

    bool insertPending(const PendingEvent& event) noexcept {
        if (pending_event_count == pending_events.size()) return false;
        std::size_t position = pending_event_count;
        while (position > 0) {
            const auto& previous = pending_events[position - 1U];
            if (previous.quantized_sample < event.quantized_sample ||
                (previous.quantized_sample == event.quantized_sample &&
                 previous.ingress_sequence <= event.ingress_sequence)) {
                break;
            }
            pending_events[position] = previous;
            --position;
        }
        pending_events[position] = event;
        ++pending_event_count;
        diagnostics.pending_events = static_cast<std::uint32_t>(pending_event_count);
        return true;
    }

    bool duplicateEvent(const PendingEvent& event) const noexcept {
        for (std::size_t index = 0; index < pending_event_count; ++index) {
            if (pending_events[index].quantized_sample == event.quantized_sample &&
                pending_events[index].ingress_sequence == event.ingress_sequence) {
                return true;
            }
        }
        return false;
    }

    bool validateEventValue(SemanticAction action, double value) noexcept {
        if (!isContinuous(action)) return true;
        if (!std::isfinite(value)) {
            ++diagnostics.non_finite_controls;
            return false;
        }
        if (action == SemanticAction::set_root) return value >= 36.0 && value <= 72.0;
        return value >= 0.0 && value <= 1.0;
    }

    bool setContinuous(SemanticAction action, double value) noexcept {
        if (!validateEventValue(action, value)) return false;
        const auto normalized = static_cast<float>(value);
        switch (action) {
            case SemanticAction::set_stage_1: controls.stages[0] = normalized; return true;
            case SemanticAction::set_stage_2: controls.stages[1] = normalized; return true;
            case SemanticAction::set_stage_3: controls.stages[2] = normalized; return true;
            case SemanticAction::set_stage_4: controls.stages[3] = normalized; return true;
            case SemanticAction::set_rate: controls.rate = normalized; return true;
            case SemanticAction::set_memory: controls.memory = normalized; return true;
            case SemanticAction::set_material: controls.material = normalized; return true;
            case SemanticAction::set_position: controls.position = normalized; return true;
            case SemanticAction::set_fx_a: controls.fx_a = normalized; return true;
            case SemanticAction::set_fx_b: controls.fx_b = normalized; return true;
            case SemanticAction::set_root:
                controls.root_note = static_cast<std::int32_t>(std::floor(value + 0.5));
                return true;
            default: return false;
        }
    }

    void countGestureOverflow(bool accepted) noexcept {
        if (!accepted) ++diagnostics.gesture_queue_overflows;
    }

    void applyEvent(const PendingEvent& event) noexcept {
        if (isContinuous(event.action)) {
            if (!setContinuous(event.action, event.value)) ++diagnostics.invalid_events;
            return;
        }
        switch (event.action) {
            case SemanticAction::source_next:
                countGestureOverflow(source_pulse.request());
                break;
            case SemanticAction::mutate:
                countGestureOverflow(mutate_pulse.request());
                ++diagnostics.manual_mutations;
                break;
            case SemanticAction::lock_toggle:
                countGestureOverflow(lock_pulse.request());
                break;
            case SemanticAction::effect_next:
                countGestureOverflow(effect_gesture.request(GestureKind::effect_tap));
                break;
            case SemanticAction::capture_toggle:
                countGestureOverflow(effect_gesture.request(GestureKind::capture_hold));
                break;
            case SemanticAction::scale_next:
                countGestureOverflow(encoder_gesture.request(GestureKind::scale_tap));
                break;
            case SemanticAction::target_next:
                countGestureOverflow(encoder_gesture.request(GestureKind::target_hold));
                break;
            default:
                ++diagnostics.invalid_events;
                break;
        }
    }

    void applyPendingAt(std::uint64_t quantum_sample) noexcept {
        std::size_t applied = 0;
        while (applied < pending_event_count &&
               pending_events[applied].quantized_sample <= quantum_sample) {
            applyEvent(pending_events[applied]);
            ++applied;
        }
        if (applied != 0) {
            std::move(
                pending_events.begin() + static_cast<std::ptrdiff_t>(applied),
                pending_events.begin() + static_cast<std::ptrdiff_t>(pending_event_count),
                pending_events.begin()
            );
            pending_event_count -= applied;
            diagnostics.pending_events = static_cast<std::uint32_t>(pending_event_count);
        }
    }

    void processQuantum(std::int32_t* left, std::int32_t* right) noexcept {
        const bool source_level = source_pulse.level();
        const bool mutate_level = mutate_pulse.level();
        const bool lock_level = lock_pulse.level();
        const bool effect_level = effect_gesture.level();
        const bool encoder_level = encoder_gesture.level();
        const std::int32_t stages[4] = {
            toQ27(controls.stages[0]),
            toQ27(controls.stages[1]),
            toQ27(controls.stages[2]),
            toQ27(controls.stages[3]),
        };

        const auto previous_lcg = stmlib::Random::state();
        stmlib::Random::Seed(lcg_state);
        instrument->Process(
            stages,
            toQ27(controls.rate),
            toQ27(controls.memory),
            toQ27(controls.material),
            toQ27(controls.position),
            toQ27(controls.fx_a),
            toQ27(controls.fx_b),
            source_level,
            mutate_level,
            lock_level,
            effect_level,
            controls.root_note,
            encoder_level,
            left,
            right
        );
        lcg_state = stmlib::Random::state();
        stmlib::Random::Seed(previous_lcg);

        source_pulse.advance(source_level);
        mutate_pulse.advance(mutate_level);
        lock_pulse.advance(lock_level);
        effect_gesture.advance();
        encoder_gesture.advance();
    }
};

Core::Core() : impl_(std::make_unique<Impl>()) {}
Core::~Core() = default;
Core::Core(Core&&) noexcept = default;
Core& Core::operator=(Core&&) noexcept = default;

bool Core::prepare(double sample_rate, std::uint32_t maximum_block_frames) noexcept {
    if (!std::isfinite(sample_rate) || sample_rate != kReferenceSampleRate ||
        maximum_block_frames == 0 || maximum_block_frames > kMaximumBlockFrames ||
        maximum_block_frames % kReferenceQuantumFrames != 0) {
        impl_->prepared = false;
        ++impl_->diagnostics.prepare_failures;
        return false;
    }

    impl_->prepared = false;
    impl_->diagnostics = {};
    impl_->resetOwnedState();
    impl_->sample_rate = sample_rate;
    impl_->maximum_block_frames = maximum_block_frames;
    if (!impl_->initializeSource()) {
        ++impl_->diagnostics.prepare_failures;
        return false;
    }
    impl_->prepared = true;
    return true;
}

ProcessReport Core::processQ27(
    std::int32_t* output_left,
    std::int32_t* output_right,
    std::uint32_t frames,
    const SemanticEvent* events,
    std::size_t event_count
) noexcept {
    ProcessReport report{};
    const bool valid_shape = output_left != nullptr && output_right != nullptr &&
        frames != 0 && frames <= impl_->maximum_block_frames &&
        frames % kReferenceQuantumFrames == 0;
    if (!impl_->prepared || !valid_shape || (event_count != 0 && events == nullptr)) {
        ++impl_->diagnostics.unsupported_process_calls;
        if (output_left != nullptr && output_right != nullptr &&
            frames <= kMaximumBlockFrames) {
            std::fill(output_left, output_left + frames, 0);
            std::fill(output_right, output_right + frames, 0);
        }
        report.events_dropped = event_count;
        impl_->diagnostics.semantic_events_dropped += event_count;
        return report;
    }

    const std::uint64_t block_start = impl_->diagnostics.processed_frames;
    for (std::size_t index = 0; index < event_count; ++index) {
        const auto& source = events[index];
        if (source.sample_offset > frames || !isValidAction(source.action) ||
            !impl_->validateEventValue(source.action, source.value) ||
            block_start > std::numeric_limits<std::uint64_t>::max() - source.sample_offset -
                    (kReferenceQuantumFrames - 1U)) {
            ++impl_->diagnostics.invalid_events;
            ++impl_->diagnostics.semantic_events_dropped;
            ++report.events_dropped;
            continue;
        }
        const Impl::PendingEvent pending{
            ceilToQuantum(block_start + source.sample_offset),
            source.ingress_sequence,
            source.action,
            source.value,
        };
        if (impl_->duplicateEvent(pending) || !impl_->insertPending(pending)) {
            ++impl_->diagnostics.invalid_events;
            ++impl_->diagnostics.semantic_events_dropped;
            ++report.events_dropped;
            continue;
        }
        ++impl_->diagnostics.semantic_events_accepted;
        ++report.events_accepted;
    }

    for (std::uint32_t offset = 0; offset < frames; offset += kReferenceQuantumFrames) {
        impl_->applyPendingAt(block_start + offset);
        impl_->processQuantum(output_left + offset, output_right + offset);
        ++impl_->diagnostics.processed_quanta;
    }
    impl_->diagnostics.processed_frames += frames;
    return report;
}

bool Core::setControlNormalized(SemanticAction action, double normalized) noexcept {
    if (!impl_->prepared || !isContinuous(action) || !isNormalized(normalized)) {
        if (!std::isfinite(normalized)) ++impl_->diagnostics.non_finite_controls;
        ++impl_->diagnostics.invalid_events;
        return false;
    }
    if (action == SemanticAction::set_root) {
        impl_->controls.root_note = normalizedRoot(normalized);
        return true;
    }
    return impl_->setContinuous(action, normalized);
}

Snapshot Core::snapshot() const noexcept {
    Snapshot result{};
    result.controls = impl_->controls;
    result.absolute_sample = impl_->diagnostics.processed_frames;
    result.prepared = impl_->prepared;
    if (impl_->instrument == nullptr) return result;

    const auto& instrument = *impl_->instrument;
    result.stage = instrument.stage();
    result.source = boundedEnum<SourceMode>(port::sourceMode(instrument), 3);
    result.scale = boundedEnum<ScaleMode>(port::scaleMode(instrument), 4);
    result.effect = boundedEnum<EffectMode>(port::effectMode(instrument), 3);
    result.target = boundedEnum<WaveTarget>(port::waveTarget(instrument), 4);
    result.locked = port::locked(instrument);
    result.captured = port::captured(instrument);
    result.sympathetic_division = port::sympatheticDivision(instrument);
    result.record_write_head = port::recordWriteHead(instrument);
    result.granular_available = instrument.granular_available();
    for (std::size_t mode = 0; mode < result.effect_parameters.size(); ++mode) {
        for (std::size_t parameter = 0; parameter < 2; ++parameter) {
            result.effect_parameters[mode][parameter] =
                port::effectParameter(instrument, mode, parameter);
        }
    }
    const auto active_effect = static_cast<std::size_t>(port::effectMode(instrument));
    result.effective_fx_a = result.effect_parameters[active_effect][0];
    result.effective_fx_b = result.effect_parameters[active_effect][1];
    result.effect_crossfade = port::effectCrossfade(instrument);
    result.fx_a_pickup_active = port::effectPickup(instrument, active_effect, 0);
    result.fx_b_pickup_active = port::effectPickup(instrument, active_effect, 1);
    for (std::size_t index = 0; index < result.mutation.size(); ++index) {
        result.mutation[index] = port::mutation(instrument, index);
    }
    for (std::size_t line = 0; line < result.display_lines.size(); ++line) {
        std::memcpy(result.display_lines[line].data(), port::displayLine(instrument, line), 22);
    }
    return result;
}

Diagnostics Core::diagnostics() const noexcept {
    auto result = impl_->diagnostics;
    result.pending_events = static_cast<std::uint32_t>(impl_->pending_event_count);
    return result;
}

bool Core::isPrepared() const noexcept { return impl_->prepared; }
double Core::sampleRate() const noexcept { return impl_->sample_rate; }

const std::array<std::int8_t, 6>& scaleIntervals(ScaleMode scale) noexcept {
    const auto index = static_cast<std::size_t>(scale);
    return kScales[index < kScales.size() ? index : 0];
}

const char* sourceName(SourceMode source) noexcept {
    constexpr std::array<const char*, 3> names{{"REED", "RND", "FOLD"}};
    const auto index = static_cast<std::size_t>(source);
    return names[index < names.size() ? index : 0];
}

const char* scaleName(ScaleMode scale) noexcept {
    constexpr std::array<const char*, 4> names{{"MAJ5", "MIN5", "DOR", "HARM"}};
    const auto index = static_cast<std::size_t>(scale);
    return names[index < names.size() ? index : 0];
}

const char* effectName(EffectMode effect) noexcept {
    constexpr std::array<const char*, 3> names{{"CLEAN", "FILT", "DRIVE"}};
    const auto index = static_cast<std::size_t>(effect);
    return names[index < names.size() ? index : 0];
}

const char* targetName(WaveTarget target) noexcept {
    constexpr std::array<const char*, 4> names{{"PIT", "BODY", "GRAIN", "ALL"}};
    const auto index = static_cast<std::size_t>(target);
    return names[index < names.size() ? index : 0];
}

}  // namespace tidepit
