#include "schuss/pamplist/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <new>
#include <utility>

namespace schuss::pamplist {
namespace {

constexpr std::uint64_t kPhaseOneQ32 = UINT64_C(1) << 32U;
constexpr std::uint64_t kTempoDenominator =
    UINT64_C(60000) * static_cast<std::uint64_t>(kSampleRateHz);
constexpr std::uint64_t kProbabilityDomain = UINT64_C(0x50524f424142494c);
constexpr std::uint64_t kShapeDomain = UINT64_C(0x534841504552414e);
constexpr double kTwoToMinus53 = 1.0 / 9007199254740992.0;
constexpr double kTwoPi = 6.283185307179586476925286766559;

constexpr std::array<Rational, kRateCount> kRates{{
    {1U, 16U},
    {1U, 12U},
    {1U, 8U},
    {1U, 6U},
    {1U, 4U},
    {1U, 3U},
    {1U, 2U},
    {3U, 4U},
    {1U, 1U},
    {4U, 3U},
    {3U, 2U},
    {2U, 1U},
    {3U, 1U},
    {4U, 1U},
    {8U, 1U},
    {16U, 1U},
}};

[[nodiscard]] std::size_t destinationIndex(Destination destination) noexcept {
    return static_cast<std::size_t>(destination);
}

[[nodiscard]] float finiteBounded(
    float value,
    float minimum,
    float maximum,
    float fallback,
    SanitizeCounts& counts) noexcept {
    if (!std::isfinite(value)) {
        ++counts.invalid;
        return fallback;
    }
    const auto bounded = std::clamp(value, minimum, maximum);
    if (bounded != value) ++counts.clamped;
    return bounded;
}

[[nodiscard]] bool sameLane(
    const LaneControls& left,
    const LaneControls& right) noexcept {
    return left.rate_index == right.rate_index
        && left.phase_u7 == right.phase_u7
        && left.shape == right.shape
        && left.hits == right.hits
        && left.rotation == right.rotation
        && left.probability == right.probability
        && left.repeat == right.repeat
        && left.amplitude == right.amplitude
        && left.routes == right.routes;
}

[[nodiscard]] std::int32_t scaleAndSaturateQ27(
    std::int32_t sample,
    float gain,
    Diagnostics& diagnostics) noexcept {
    const auto scaled = static_cast<std::int64_t>(std::llround(
        static_cast<double>(sample) * static_cast<double>(gain)));
    if (scaled > kQ27Maximum || scaled < kQ27Minimum) {
        ++diagnostics.saturated_sample_count;
    }
    return static_cast<std::int32_t>(
        std::clamp<std::int64_t>(scaled, kQ27Minimum, kQ27Maximum));
}

}  // namespace

Controls defaultControls() noexcept {
    Controls controls{};
    controls.lanes[0].amplitude = 1.0F;
    controls.lanes[0].routes[destinationIndex(Destination::trigger)] = 1.0F;
    return controls;
}

Controls sanitizeControls(
    const Controls& requested,
    SanitizeCounts* counts) noexcept {
    SanitizeCounts local{};
    Controls result = requested;
    if (result.tempo_milli_bpm < 20000U || result.tempo_milli_bpm > 300000U) {
        result.tempo_milli_bpm = 120000U;
        ++local.invalid;
    }
    if (result.engine > 23U) {
        result.engine = 23U;
        ++local.clamped;
    }
    result.note = finiteBounded(result.note, 24.0F, 96.0F, 48.0F, local);
    result.harmonics = finiteBounded(result.harmonics, 0.0F, 1.0F, 0.5F, local);
    result.timbre = finiteBounded(result.timbre, 0.0F, 1.0F, 0.5F, local);
    result.morph = finiteBounded(result.morph, 0.0F, 1.0F, 0.5F, local);
    result.decay = finiteBounded(result.decay, 0.0F, 1.0F, 0.5F, local);
    result.lpg_colour = finiteBounded(result.lpg_colour, 0.0F, 1.0F, 0.5F, local);
    result.source_level = finiteBounded(result.source_level, 0.0F, 1.0F, 0.8F, local);
    result.master_gain = finiteBounded(result.master_gain, 0.0F, 1.0F, 0.65F, local);
    if (result.selected_lane >= kLaneCount) {
        result.selected_lane = static_cast<std::uint8_t>(kLaneCount - 1U);
        ++local.clamped;
    }
    for (auto& lane : result.lanes) {
        if (lane.rate_index >= kRateCount) {
            lane.rate_index = 8U;
            ++local.invalid;
        }
        if (lane.phase_u7 > 127U) {
            lane.phase_u7 = 127U;
            ++local.clamped;
        }
        if (static_cast<std::uint8_t>(lane.shape)
            > static_cast<std::uint8_t>(Shape::smooth_random)) {
            lane.shape = Shape::pulse;
            ++local.invalid;
        }
        if (lane.hits > 16U) {
            lane.hits = 16U;
            ++local.clamped;
        }
        if (lane.rotation > 15U) {
            lane.rotation = 15U;
            ++local.clamped;
        }
        if (lane.repeat > 64U) {
            lane.repeat = 64U;
            ++local.clamped;
        }
        lane.probability = finiteBounded(
            lane.probability, 0.0F, 1.0F, 1.0F, local);
        lane.amplitude = finiteBounded(
            lane.amplitude, 0.0F, 1.0F, 0.0F, local);
        for (auto& route : lane.routes) {
            route = finiteBounded(route, -1.0F, 1.0F, 0.0F, local);
        }
    }
    if (counts != nullptr) *counts = local;
    return result;
}

bool sameControls(const Controls& left, const Controls& right) noexcept {
    if (left.running != right.running
        || left.tempo_milli_bpm != right.tempo_milli_bpm
        || left.seed != right.seed
        || left.engine != right.engine
        || left.note != right.note
        || left.harmonics != right.harmonics
        || left.timbre != right.timbre
        || left.morph != right.morph
        || left.decay != right.decay
        || left.lpg_colour != right.lpg_colour
        || left.source_level != right.source_level
        || left.master_gain != right.master_gain
        || left.selected_lane != right.selected_lane) {
        return false;
    }
    for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
        if (!sameLane(left.lanes[lane], right.lanes[lane])) return false;
    }
    return true;
}

const std::array<Rational, kRateCount>& rateTable() noexcept {
    return kRates;
}

const char* shapeName(Shape shape) noexcept {
    switch (shape) {
        case Shape::gate: return "gate";
        case Shape::pulse: return "pulse";
        case Shape::triangle: return "triangle";
        case Shape::sine: return "sine";
        case Shape::ramp: return "ramp";
        case Shape::exponential_decay: return "exponential-decay";
        case Shape::sample_hold: return "sample-hold";
        case Shape::smooth_random: return "smooth-random";
    }
    return "invalid";
}

const char* destinationName(Destination destination) noexcept {
    switch (destination) {
        case Destination::trigger: return "Trigger";
        case Destination::pitch: return "Pitch";
        case Destination::model: return "Model";
        case Destination::harmonics: return "Harmonics";
        case Destination::timbre: return "Timbre";
        case Destination::morph: return "Morph";
        case Destination::decay: return "Decay";
        case Destination::level: return "Level";
    }
    return "Invalid";
}

bool euclideanHit(
    std::uint8_t step,
    std::uint8_t hits,
    std::uint8_t rotation) noexcept {
    const auto bounded_hits = std::min<std::uint8_t>(hits, 16U);
    if (bounded_hits == 0U) return false;
    if (bounded_hits == 16U) return true;
    const auto rotated = static_cast<std::uint8_t>(
        (static_cast<unsigned int>(step & 15U) + (rotation & 15U)) & 15U);
    return (static_cast<unsigned int>(rotated) * bounded_hits) % 16U
        < bounded_hits;
}

std::uint64_t addressedRandomWord(
    std::uint32_t seed,
    std::uint8_t lane,
    std::uint64_t address,
    std::uint64_t domain) noexcept {
    std::uint64_t value = static_cast<std::uint64_t>(seed)
        ^ (static_cast<std::uint64_t>(lane) * UINT64_C(0x9e3779b97f4a7c15))
        ^ (address * UINT64_C(0xbf58476d1ce4e5b9))
        ^ domain;
    value += UINT64_C(0x9e3779b97f4a7c15);
    value = (value ^ (value >> 30U)) * UINT64_C(0xbf58476d1ce4e5b9);
    value = (value ^ (value >> 27U)) * UINT64_C(0x94d049bb133111eb);
    return value ^ (value >> 31U);
}

double addressedRandomUnit(
    std::uint32_t seed,
    std::uint8_t lane,
    std::uint64_t address,
    std::uint64_t domain) noexcept {
    return static_cast<double>(
        addressedRandomWord(seed, lane, address, domain) >> 11U)
        * kTwoToMinus53;
}

float shapeValue(
    Shape shape,
    std::uint32_t local_phase_q32,
    double random_a,
    double random_b) noexcept {
    const auto x = static_cast<double>(local_phase_q32) / 4294967296.0;
    double value = 0.0;
    switch (shape) {
        case Shape::gate:
            value = 1.0;
            break;
        case Shape::pulse:
            value = x < 0.5 ? 1.0 : 0.0;
            break;
        case Shape::triangle:
            value = 1.0 - std::abs(2.0 * x - 1.0);
            break;
        case Shape::sine:
            value = 0.5 - 0.5 * std::cos(kTwoPi * x);
            break;
        case Shape::ramp:
            value = x;
            break;
        case Shape::exponential_decay:
            value = std::exp(-6.0 * x);
            break;
        case Shape::sample_hold:
            value = random_a;
            break;
        case Shape::smooth_random: {
            const auto smooth = x * x * (3.0 - 2.0 * x);
            value = random_a + (random_b - random_a) * smooth;
            break;
        }
    }
    if (!std::isfinite(value)) return 0.0F;
    return static_cast<float>(std::clamp(value, 0.0, 1.0));
}

struct Core::Impl final {
    struct LaneState final {
        std::uint64_t phase_q32{};
        std::uint64_t remainder{};
        std::uint64_t observed_step{};
        std::uint64_t address{};
        bool has_observed_step{};
        bool accepted_step{};
        double random_a{};
        double random_b{};
    };

    Controls accepted{defaultControls()};
    Diagnostics diagnostics{};
    Snapshot public_snapshot{};
    MacroVoice voice{kDefaultSeed};
    std::array<LaneState, kLaneCount> lanes{};
    std::uint64_t master_phase_q32{};
    std::uint64_t master_remainder{};
    std::uint64_t absolute_frame{};
    std::uint64_t render_frame{};
    std::uint64_t quantum_count{};
    std::uint64_t accepted_sequence{};
    std::array<std::int32_t, kMacroVoiceQuantumFrames> main_quantum{};
    std::array<std::int32_t, kMacroVoiceQuantumFrames> auxiliary_quantum{};
    std::size_t quantum_cursor{kMacroVoiceQuantumFrames};
    bool has_accepted{};
    bool was_running{};
    bool voice_started{};

    Impl() { refreshSnapshot(); }

    void clearScheduler() noexcept {
        master_phase_q32 = 0U;
        master_remainder = 0U;
        lanes = {};
    }

    void resetTransport(std::uint32_t seed) noexcept {
        clearScheduler();
        voice.reset(seed);
        main_quantum.fill(0);
        auxiliary_quantum.fill(0);
        quantum_cursor = kMacroVoiceQuantumFrames;
        was_running = false;
        voice_started = false;
    }

    void resetAll() noexcept {
        accepted = defaultControls();
        diagnostics = {};
        public_snapshot = {};
        absolute_frame = 0U;
        render_frame = 0U;
        quantum_count = 0U;
        accepted_sequence = 0U;
        has_accepted = false;
        resetTransport(kDefaultSeed);
        refreshSnapshot();
    }

    void refreshSnapshot() noexcept {
        public_snapshot.accepted = accepted;
        public_snapshot.diagnostics = diagnostics;
        public_snapshot.absolute_frame = absolute_frame;
        public_snapshot.rendered_through_frame = render_frame;
        public_snapshot.quantum_count = quantum_count;
        public_snapshot.accepted_sequence = accepted_sequence;
        public_snapshot.master_phase_q32 = master_phase_q32;
        public_snapshot.master_remainder = master_remainder;
        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            public_snapshot.lane_phase_q32[lane] = lanes[lane].phase_q32;
            public_snapshot.lane_remainders[lane] = lanes[lane].remainder;
            public_snapshot.lane_steps[lane] = lanes[lane].observed_step;
            public_snapshot.lane_addresses[lane] = lanes[lane].address;
        }
    }

    void accept(const Controls& requested) noexcept {
        SanitizeCounts counts{};
        const auto next = sanitizeControls(requested, &counts);
        diagnostics.invalid_control_count += counts.invalid;
        diagnostics.clamped_control_count += counts.clamped;
        if (has_accepted) {
            if (next.tempo_milli_bpm != accepted.tempo_milli_bpm) {
                master_remainder = 0U;
                for (auto& lane : lanes) lane.remainder = 0U;
            } else {
                for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
                    if (next.lanes[lane].rate_index
                        != accepted.lanes[lane].rate_index) {
                        lanes[lane].remainder = 0U;
                    }
                }
            }
        }
        if (!has_accepted || !sameControls(next, accepted)) {
            ++accepted_sequence;
        }
        accepted = next;
        has_accepted = true;
    }

    void advanceSchedulers() noexcept {
        const auto master_numerator =
            static_cast<std::uint64_t>(accepted.tempo_milli_bpm)
            * 4U * kPhaseOneQ32;
        for (std::size_t frame = 0; frame < kMacroVoiceQuantumFrames; ++frame) {
            const auto master_total = master_numerator + master_remainder;
            master_phase_q32 += master_total / kTempoDenominator;
            master_remainder = master_total % kTempoDenominator;
            for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
                const auto rate = kRates[accepted.lanes[lane].rate_index];
                const auto numerator = master_numerator * rate.numerator;
                const auto denominator = kTempoDenominator * rate.denominator;
                const auto total = numerator + lanes[lane].remainder;
                lanes[lane].phase_q32 += total / denominator;
                lanes[lane].remainder = total % denominator;
            }
        }
    }

    [[nodiscard]] bool renderQuantum(QuantumEvent& event) noexcept {
        if (!accepted.running) {
            if (was_running) resetTransport(accepted.seed);
            main_quantum.fill(0);
            auxiliary_quantum.fill(0);
            quantum_cursor = 0U;
            render_frame += kMacroVoiceQuantumFrames;
            ++quantum_count;
            refreshSnapshot();
            return false;
        }
        was_running = true;

        std::array<float, kLaneCount> lane_values{};
        std::array<float, kDestinationCount> matrix{};
        std::uint8_t boundary_mask = 0U;
        std::uint8_t accepted_mask = 0U;
        std::uint8_t trigger_lane_mask = 0U;
        std::uint8_t trigger_lanes = 0U;

        event = {};
        event.absolute_frame = render_frame;
        for (std::size_t lane_index = 0; lane_index < kLaneCount; ++lane_index) {
            const auto& controls = accepted.lanes[lane_index];
            auto& state = lanes[lane_index];
            const auto phase_offset =
                static_cast<std::uint64_t>(controls.phase_u7) << 25U;
            const auto effective = state.phase_q32 + phase_offset;
            const auto step = effective >> 32U;
            const auto local_phase = static_cast<std::uint32_t>(effective);
            const bool boundary = !state.has_observed_step
                || state.observed_step != step;
            if (boundary) {
                state.has_observed_step = true;
                state.observed_step = step;
                state.address = controls.repeat == 0U
                    ? step
                    : step % controls.repeat;
                const auto mask_hit = euclideanHit(
                    static_cast<std::uint8_t>(step & 15U),
                    controls.hits,
                    controls.rotation);
                const auto probability_word = addressedRandomUnit(
                    accepted.seed,
                    static_cast<std::uint8_t>(lane_index),
                    state.address,
                    kProbabilityDomain);
                state.accepted_step = mask_hit
                    && (controls.probability >= 1.0F
                        || (controls.probability > 0.0F
                            && probability_word
                                < static_cast<double>(controls.probability)));
                state.random_a = addressedRandomUnit(
                    accepted.seed,
                    static_cast<std::uint8_t>(lane_index),
                    state.address,
                    kShapeDomain);
                const auto next_address = controls.repeat == 0U
                    ? state.address + 1U
                    : (state.address + 1U) % controls.repeat;
                state.random_b = addressedRandomUnit(
                    accepted.seed,
                    static_cast<std::uint8_t>(lane_index),
                    next_address,
                    kShapeDomain);
                boundary_mask = static_cast<std::uint8_t>(
                    boundary_mask | (1U << lane_index));
                if (state.accepted_step) {
                    accepted_mask = static_cast<std::uint8_t>(
                        accepted_mask | (1U << lane_index));
                }
            }
            const auto value = state.accepted_step
                ? shapeValue(
                    controls.shape, local_phase, state.random_a, state.random_b)
                    * controls.amplitude
                : 0.0F;
            lane_values[lane_index] = std::clamp(value, 0.0F, 1.0F);
            if (boundary
                && state.accepted_step
                && controls.amplitude > 0.0F
                && controls.routes[destinationIndex(Destination::trigger)]
                    > (1.0F / 127.0F)) {
                trigger_lane_mask = static_cast<std::uint8_t>(
                    trigger_lane_mask | (1U << lane_index));
                ++trigger_lanes;
            }
        }

        for (std::size_t destination = 0;
             destination < kDestinationCount;
             ++destination) {
            double sum = 0.0;
            for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
                sum += static_cast<double>(lane_values[lane])
                    * accepted.lanes[lane].routes[destination];
            }
            const auto bounded = std::clamp(sum, -1.0, 1.0);
            if (bounded != sum) ++diagnostics.matrix_clamp_count;
            matrix[destination] = static_cast<float>(bounded);
        }

        const bool trigger = trigger_lanes > 0U;
        if (trigger) {
            ++diagnostics.trigger_count;
            diagnostics.coalesced_trigger_count += trigger_lanes - 1U;
        }
        const auto model_offset = static_cast<int>(std::lround(
            23.0 * matrix[destinationIndex(Destination::model)]));
        const auto resolved_engine = static_cast<std::uint8_t>(std::clamp(
            static_cast<int>(accepted.engine) + model_offset, 0, 23));
        const auto resolved_note = std::clamp(
            accepted.note
                + 24.0F * matrix[destinationIndex(Destination::pitch)],
            24.0F,
            96.0F);
        const auto unit = [&matrix](float base, Destination destination) {
            return std::clamp(
                base + matrix[destinationIndex(destination)], 0.0F, 1.0F);
        };
        const auto resolved_harmonics = unit(accepted.harmonics, Destination::harmonics);
        const auto resolved_timbre = unit(accepted.timbre, Destination::timbre);
        const auto resolved_morph = unit(accepted.morph, Destination::morph);
        const auto resolved_decay = unit(accepted.decay, Destination::decay);
        const auto resolved_level = unit(accepted.source_level, Destination::level);

        MacroVoiceControls voice_controls{};
        voice_controls.trigger = trigger;
        voice_controls.engine = resolved_engine;
        voice_controls.note = resolved_note;
        voice_controls.harmonics = resolved_harmonics;
        voice_controls.timbre = resolved_timbre;
        voice_controls.morph = resolved_morph;
        voice_controls.decay = resolved_decay;
        voice_controls.lpg_colour = accepted.lpg_colour;
        voice_controls.level = resolved_level;
        if (trigger) voice_started = true;
        if (voice_started) {
            voice.process(voice_controls, main_quantum, auxiliary_quantum);
        } else {
            main_quantum.fill(0);
            auxiliary_quantum.fill(0);
        }
        const auto output_gain = accepted.master_gain * resolved_level;
        for (std::size_t frame = 0; frame < kMacroVoiceQuantumFrames; ++frame) {
            main_quantum[frame] = scaleAndSaturateQ27(
                main_quantum[frame], output_gain, diagnostics);
            auxiliary_quantum[frame] = scaleAndSaturateQ27(
                auxiliary_quantum[frame], output_gain, diagnostics);
        }
        quantum_cursor = 0U;

        event.boundary_mask = boundary_mask;
        event.accepted_mask = accepted_mask;
        event.trigger_lane_mask = trigger_lane_mask;
        event.trigger = trigger;
        event.resolved_engine = resolved_engine;
        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            event.steps[lane] = lanes[lane].observed_step;
            event.addresses[lane] = lanes[lane].address;
        }

        public_snapshot.lane_values = lane_values;
        public_snapshot.matrix_values = matrix;
        public_snapshot.trigger = trigger;
        public_snapshot.resolved_engine = resolved_engine;
        public_snapshot.resolved_note = resolved_note;
        public_snapshot.resolved_harmonics = resolved_harmonics;
        public_snapshot.resolved_timbre = resolved_timbre;
        public_snapshot.resolved_morph = resolved_morph;
        public_snapshot.resolved_decay = resolved_decay;
        public_snapshot.resolved_level = resolved_level;

        advanceSchedulers();
        render_frame += kMacroVoiceQuantumFrames;
        ++quantum_count;
        refreshSnapshot();
        return boundary_mask != 0U || trigger;
    }

    [[nodiscard]] bool process(
        const Controls& requested,
        std::int32_t* main_q27,
        std::int32_t* auxiliary_q27,
        std::size_t frame_count,
        ProcessReport* report) noexcept {
        if (report != nullptr) {
            *report = {};
            report->absolute_frame_start = absolute_frame;
        }
        if (main_q27 == nullptr
            || auxiliary_q27 == nullptr
            || frame_count == 0U
            || frame_count > kMaximumHostBlockFrames) {
            if (main_q27 != nullptr && auxiliary_q27 != nullptr) {
                std::fill_n(main_q27, frame_count, 0);
                std::fill_n(auxiliary_q27, frame_count, 0);
            }
            ++diagnostics.unsupported_process_count;
            refreshSnapshot();
            if (report != nullptr) {
                report->absolute_frame_end = absolute_frame;
                report->snapshot = public_snapshot;
            }
            return false;
        }

        std::size_t written = 0U;
        std::uint8_t report_events = 0U;
        while (written < frame_count) {
            if (quantum_cursor == kMacroVoiceQuantumFrames) {
                accept(requested);
                QuantumEvent event{};
                const auto retain_event = renderQuantum(event);
                if (retain_event
                    && report != nullptr
                    && report_events < report->events.size()) {
                    report->events[report_events++] = event;
                }
            }
            const auto available = kMacroVoiceQuantumFrames - quantum_cursor;
            const auto copied = std::min(available, frame_count - written);
            std::copy_n(
                main_quantum.data() + quantum_cursor,
                copied,
                main_q27 + written);
            std::copy_n(
                auxiliary_quantum.data() + quantum_cursor,
                copied,
                auxiliary_q27 + written);
            quantum_cursor += copied;
            written += copied;
            absolute_frame += copied;
        }
        refreshSnapshot();
        if (report != nullptr) {
            report->absolute_frame_end = absolute_frame;
            report->event_count = report_events;
            report->snapshot = public_snapshot;
        }
        return true;
    }
};

Core::Core()
    : impl_(new Impl()) {}

Core::~Core() { delete impl_; }

Core::Core(Core&& other) noexcept
    : impl_(std::exchange(other.impl_, nullptr)) {}

Core& Core::operator=(Core&& other) noexcept {
    if (this != &other) {
        delete impl_;
        impl_ = std::exchange(other.impl_, nullptr);
    }
    return *this;
}

void Core::reset() noexcept { impl_->resetAll(); }

void Core::panic() noexcept {
    impl_->accepted.running = false;
    impl_->resetTransport(impl_->accepted.seed);
    ++impl_->diagnostics.panic_count;
    impl_->refreshSnapshot();
}

bool Core::process(
    const Controls& controls,
    std::int32_t* main_q27,
    std::int32_t* auxiliary_q27,
    std::size_t frame_count,
    ProcessReport* report) noexcept {
    return impl_->process(
        controls, main_q27, auxiliary_q27, frame_count, report);
}

const Snapshot& Core::snapshot() const noexcept { return impl_->public_snapshot; }

}  // namespace schuss::pamplist
