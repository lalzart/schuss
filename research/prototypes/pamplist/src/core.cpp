#include "schuss/pamplist/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
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
constexpr double kQ27Scale = 134217728.0;
constexpr double kMaximumModalFrequencyHz = 21599.0;
constexpr double kDenormalThreshold = 1.0e-20;
constexpr double kSmootherSnapThreshold = 1.0e-7;

constexpr std::array<double, kCohesionModeCount> kHarmonicRatios{{
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0,
}};
constexpr std::array<double, kCohesionModeCount> kInharmonicRatios{{
    1.0, 1.41421356, 1.932, 2.756, 3.561, 4.781,
}};
constexpr std::array<double, kCohesionModeCount> kBasePans{{
    -1.0, 0.55, -0.35, 0.85, -0.7, 0.25,
}};

constexpr std::array<const char*, 24U> kEngineNames{{
    "Virtual Analog VCF",
    "Phase Distortion",
    "6-Op FM A",
    "6-Op FM B",
    "6-Op FM C",
    "Wave Terrain",
    "String Machine",
    "Chiptune",
    "Virtual Analog",
    "Waveshaping",
    "2-Op FM",
    "Granular Formant",
    "Harmonic / Additive",
    "Wavetable",
    "Chord",
    "Speech",
    "Swarm",
    "Noise",
    "Particle",
    "String",
    "Modal Resonator",
    "Bass Drum",
    "Snare Drum",
    "Hi-Hat",
}};

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

[[nodiscard]] bool sameVoice(
    const VoiceControls& left,
    const VoiceControls& right) noexcept {
    return left.engine == right.engine
        && left.note == right.note
        && left.harmonics == right.harmonics
        && left.timbre == right.timbre
        && left.morph == right.morph
        && left.decay == right.decay
        && left.lpg_colour == right.lpg_colour
        && left.level == right.level;
}

[[nodiscard]] bool sameCohesion(
    const CohesionControls& left,
    const CohesionControls& right) noexcept {
    return left.drive == right.drive
        && left.cohere == right.cohere
        && left.root_note == right.root_note
        && left.spread == right.spread
        && left.tail == right.tail
        && left.damping == right.damping
        && left.width == right.width
        && left.duck == right.duck;
}

[[nodiscard]] std::uint32_t laneVoiceSeed(
    std::uint32_t seed,
    std::size_t lane) noexcept {
    auto value = seed
        ^ (UINT32_C(0x9e3779b9) * static_cast<std::uint32_t>(lane + 1U));
    value ^= value >> 16U;
    value *= UINT32_C(0x7feb352d);
    value ^= value >> 15U;
    value *= UINT32_C(0x846ca68b);
    value ^= value >> 16U;
    return value == 0U ? static_cast<std::uint32_t>(lane + 1U) : value;
}

[[nodiscard]] std::int64_t scaleContributionQ27(
    std::int32_t sample,
    float level) noexcept {
    return static_cast<std::int64_t>(std::llround(
        static_cast<double>(sample) * static_cast<double>(level)));
}

[[nodiscard]] std::int32_t saturateMixQ27(
    std::int64_t sum,
    double gain,
    Diagnostics& diagnostics) noexcept {
    const auto scaled = static_cast<std::int64_t>(std::llround(
        static_cast<double>(sum) * gain));
    if (scaled > kQ27Maximum || scaled < kQ27Minimum) {
        ++diagnostics.saturated_sample_count;
    }
    return static_cast<std::int32_t>(
        std::clamp<std::int64_t>(scaled, kQ27Minimum, kQ27Maximum));
}

[[nodiscard]] std::int32_t saturateFloatQ27(
    double sample,
    double gain,
    Diagnostics& diagnostics) noexcept {
    const auto scaled = sample * kQ27Scale * gain;
    if (scaled > static_cast<double>(kQ27Maximum)) {
        ++diagnostics.saturated_sample_count;
        return kQ27Maximum;
    }
    if (scaled < static_cast<double>(kQ27Minimum)) {
        ++diagnostics.saturated_sample_count;
        return kQ27Minimum;
    }
    return static_cast<std::int32_t>(std::llround(scaled));
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
    result.master_gain = finiteBounded(result.master_gain, 0.0F, 1.0F, 0.65F, local);
    if (result.selected_page >= kPageCount) {
        result.selected_page = kGlobalPageIndex;
        ++local.clamped;
    }
    if (static_cast<std::uint8_t>(result.lane_control_mode)
        > static_cast<std::uint8_t>(LaneControlMode::motion)) {
        result.lane_control_mode = LaneControlMode::voice;
        ++local.invalid;
    }
    result.cohesion.drive = finiteBounded(
        result.cohesion.drive, 0.0F, 1.0F, 0.0F, local);
    result.cohesion.cohere = finiteBounded(
        result.cohesion.cohere, 0.0F, 1.0F, 0.0F, local);
    result.cohesion.root_note = finiteBounded(
        result.cohesion.root_note, 24.0F, 84.0F, 48.0F, local);
    result.cohesion.spread = finiteBounded(
        result.cohesion.spread, 0.0F, 1.0F, 0.0F, local);
    result.cohesion.tail = finiteBounded(
        result.cohesion.tail, 0.0F, 1.0F, 0.5F, local);
    result.cohesion.damping = finiteBounded(
        result.cohesion.damping, 0.0F, 1.0F, 0.5F, local);
    result.cohesion.width = finiteBounded(
        result.cohesion.width, 0.0F, 1.0F, 0.5F, local);
    result.cohesion.duck = finiteBounded(
        result.cohesion.duck, 0.0F, 1.0F, 0.0F, local);
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
        auto& trigger = lane.routes[destinationIndex(Destination::trigger)];
        if (!std::isfinite(trigger)) {
            trigger = 0.0F;
            ++local.invalid;
        } else {
            const auto accepted_trigger = trigger > (1.0F / 127.0F)
                ? 1.0F
                : 0.0F;
            if (accepted_trigger != trigger) ++local.clamped;
            trigger = accepted_trigger;
        }
        for (std::size_t destination = 1U;
             destination < lane.routes.size();
             ++destination) {
            lane.routes[destination] = finiteBounded(
                lane.routes[destination], -1.0F, 1.0F, 0.0F, local);
        }
    }
    for (auto& voice : result.voices) {
        if (voice.engine > 23U) {
            voice.engine = 23U;
            ++local.clamped;
        }
        voice.note = finiteBounded(
            voice.note, 24.0F, 96.0F, 48.0F, local);
        voice.harmonics = finiteBounded(
            voice.harmonics, 0.0F, 1.0F, 0.5F, local);
        voice.timbre = finiteBounded(
            voice.timbre, 0.0F, 1.0F, 0.5F, local);
        voice.morph = finiteBounded(
            voice.morph, 0.0F, 1.0F, 0.5F, local);
        voice.decay = finiteBounded(
            voice.decay, 0.0F, 1.0F, 0.5F, local);
        voice.lpg_colour = finiteBounded(
            voice.lpg_colour, 0.0F, 1.0F, 0.5F, local);
        voice.level = finiteBounded(
            voice.level, 0.0F, 1.0F, 0.8F, local);
    }
    if (counts != nullptr) *counts = local;
    return result;
}

bool sameControls(const Controls& left, const Controls& right) noexcept {
    if (left.running != right.running
        || left.tempo_milli_bpm != right.tempo_milli_bpm
        || left.seed != right.seed
        || left.master_gain != right.master_gain
        || left.selected_page != right.selected_page
        || left.lane_control_mode != right.lane_control_mode
        || left.effect_clear_generation != right.effect_clear_generation
        || !sameCohesion(left.cohesion, right.cohesion)) {
        return false;
    }
    for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
        if (!sameLane(left.lanes[lane], right.lanes[lane])
            || !sameVoice(left.voices[lane], right.voices[lane])) {
            return false;
        }
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
        case Destination::trigger: return "Trigger Enable";
        case Destination::pitch: return "Pitch";
        case Destination::model: return "MODEL SWEEP";
        case Destination::harmonics: return "Harmonics";
        case Destination::timbre: return "Timbre";
        case Destination::morph: return "Morph";
        case Destination::decay: return "Decay";
        case Destination::level: return "Level";
    }
    return "Invalid";
}

const char* engineName(std::uint8_t engine) noexcept {
    return engine < kEngineNames.size() ? kEngineNames[engine] : "Unknown";
}

const char* modelName(std::uint8_t model) noexcept {
    return engineName(model);
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

    struct Smoother final {
        double current{};
        double target{};
        double coefficient{};

        void reset(double value, double seconds) noexcept {
            current = value;
            target = value;
            coefficient = 1.0 - std::exp(
                -1.0 / (seconds * static_cast<double>(kSampleRateHz)));
        }

        void setTarget(double value) noexcept { target = value; }

        [[nodiscard]] double step() noexcept {
            current += (target - current) * coefficient;
            if (std::abs(target - current) <= kSmootherSnapThreshold) {
                current = target;
            }
            return current;
        }
    };

    struct ModeState final {
        double real{};
        double imaginary{};
        double frequency_hz{};
        double pole{};
    };

    struct CohesionState final {
        Smoother master{};
        Smoother drive{};
        Smoother cohere{};
        Smoother root_note{};
        Smoother spread{};
        Smoother tail{};
        Smoother damping{};
        Smoother width{};
        Smoother duck{};
        std::array<ModeState, kCohesionModeCount> modes{};
        double duck_envelope{};
        double maximum_mode_state_absolute{};
        double maximum_duck_envelope{};
        double dry_difference_energy{};
        std::uint32_t applied_clear_generation{};
    };

    Controls accepted{defaultControls()};
    Diagnostics diagnostics{};
    Snapshot public_snapshot{};
    std::array<std::unique_ptr<MacroVoice>, kLaneCount> voices{};
    std::array<LaneState, kLaneCount> lanes{};
    std::uint64_t master_phase_q32{};
    std::uint64_t master_remainder{};
    std::uint64_t absolute_frame{};
    std::uint64_t render_frame{};
    std::uint64_t quantum_count{};
    std::uint64_t accepted_sequence{};
    std::array<std::array<std::int32_t, kMacroVoiceQuantumFrames>, kLaneCount>
        voice_main_quantum{};
    std::array<std::array<std::int32_t, kMacroVoiceQuantumFrames>, kLaneCount>
        voice_auxiliary_quantum{};
    std::array<std::int32_t, kMacroVoiceQuantumFrames> main_quantum{};
    std::array<std::int32_t, kMacroVoiceQuantumFrames> auxiliary_quantum{};
    std::size_t quantum_cursor{kMacroVoiceQuantumFrames};
    bool has_accepted{};
    bool was_running{};
    std::array<bool, kLaneCount> voice_started{};
    CohesionState cohesion{};
    bool effect_cleared_for_quantum{};

    Impl() {
        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            voices[lane] = std::make_unique<MacroVoice>(
                laneVoiceSeed(kDefaultSeed, lane));
        }
        resetEffectRuntimeToAccepted();
        setResolvedToBase();
        refreshSnapshot();
    }

    void setEffectTargets() noexcept {
        cohesion.master.setTarget(accepted.master_gain);
        cohesion.drive.setTarget(accepted.cohesion.drive);
        cohesion.cohere.setTarget(accepted.cohesion.cohere);
        cohesion.root_note.setTarget(accepted.cohesion.root_note);
        cohesion.spread.setTarget(accepted.cohesion.spread);
        cohesion.tail.setTarget(accepted.cohesion.tail);
        cohesion.damping.setTarget(accepted.cohesion.damping);
        cohesion.width.setTarget(accepted.cohesion.width);
        cohesion.duck.setTarget(accepted.cohesion.duck);
    }

    void clearEffectHistory() noexcept {
        for (auto& mode : cohesion.modes) mode = {};
        cohesion.duck_envelope = 0.0;
    }

    void resetEffectRuntimeToAccepted() noexcept {
        cohesion.master.reset(accepted.master_gain, 0.010);
        cohesion.drive.reset(accepted.cohesion.drive, 0.030);
        cohesion.cohere.reset(accepted.cohesion.cohere, 0.010);
        cohesion.root_note.reset(accepted.cohesion.root_note, 0.030);
        cohesion.spread.reset(accepted.cohesion.spread, 0.030);
        cohesion.tail.reset(accepted.cohesion.tail, 0.030);
        cohesion.damping.reset(accepted.cohesion.damping, 0.030);
        cohesion.width.reset(accepted.cohesion.width, 0.030);
        cohesion.duck.reset(accepted.cohesion.duck, 0.030);
        cohesion.applied_clear_generation = accepted.effect_clear_generation;
        clearEffectHistory();
        effect_cleared_for_quantum = false;
    }

    void clearScheduler() noexcept {
        master_phase_q32 = 0U;
        master_remainder = 0U;
        lanes = {};
    }

    void resetTransport(std::uint32_t seed) noexcept {
        clearScheduler();
        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            voices[lane]->reset(laneVoiceSeed(seed, lane));
            voice_main_quantum[lane].fill(0);
            voice_auxiliary_quantum[lane].fill(0);
        }
        main_quantum.fill(0);
        auxiliary_quantum.fill(0);
        quantum_cursor = kMacroVoiceQuantumFrames;
        was_running = false;
        voice_started.fill(false);
        resetEffectRuntimeToAccepted();
        setResolvedToBase();
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
        cohesion = {};
        effect_cleared_for_quantum = false;
        resetTransport(kDefaultSeed);
        refreshSnapshot();
    }

    void setResolvedToBase() noexcept {
        public_snapshot.lane_values.fill(0.0F);
        public_snapshot.modulation_values = {};
        public_snapshot.trigger_lane_mask = 0U;
        public_snapshot.started_lane_mask = 0U;
        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            const auto& voice = accepted.voices[lane];
            public_snapshot.resolved_engines[lane] = voice.engine;
            public_snapshot.resolved_notes[lane] = voice.note;
            public_snapshot.resolved_harmonics[lane] = voice.harmonics;
            public_snapshot.resolved_timbres[lane] = voice.timbre;
            public_snapshot.resolved_morphs[lane] = voice.morph;
            public_snapshot.resolved_decays[lane] = voice.decay;
            public_snapshot.resolved_lpg_colours[lane] = voice.lpg_colour;
            public_snapshot.resolved_levels[lane] = voice.level;
        }
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
            public_snapshot.source_random_states[lane] =
                voices[lane]->randomState();
            if (voice_started[lane]) {
                public_snapshot.started_lane_mask = static_cast<std::uint8_t>(
                    public_snapshot.started_lane_mask | (1U << lane));
            } else {
                public_snapshot.started_lane_mask = static_cast<std::uint8_t>(
                    public_snapshot.started_lane_mask & ~(1U << lane));
            }
        }
        public_snapshot.cohesion.smoothed_master_gain =
            static_cast<float>(cohesion.master.current);
        public_snapshot.cohesion.smoothed_drive =
            static_cast<float>(cohesion.drive.current);
        public_snapshot.cohesion.smoothed_cohere =
            static_cast<float>(cohesion.cohere.current);
        public_snapshot.cohesion.smoothed_root_note =
            static_cast<float>(cohesion.root_note.current);
        public_snapshot.cohesion.smoothed_spread =
            static_cast<float>(cohesion.spread.current);
        public_snapshot.cohesion.smoothed_tail =
            static_cast<float>(cohesion.tail.current);
        public_snapshot.cohesion.smoothed_damping =
            static_cast<float>(cohesion.damping.current);
        public_snapshot.cohesion.smoothed_width =
            static_cast<float>(cohesion.width.current);
        public_snapshot.cohesion.smoothed_duck =
            static_cast<float>(cohesion.duck.current);
        public_snapshot.cohesion.duck_envelope =
            static_cast<float>(cohesion.duck_envelope);
        for (std::size_t mode = 0; mode < kCohesionModeCount; ++mode) {
            public_snapshot.cohesion.mode_frequencies_hz[mode] =
                static_cast<float>(cohesion.modes[mode].frequency_hz);
            public_snapshot.cohesion.mode_poles[mode] =
                static_cast<float>(cohesion.modes[mode].pole);
            public_snapshot.cohesion.mode_real[mode] =
                static_cast<float>(cohesion.modes[mode].real);
            public_snapshot.cohesion.mode_imaginary[mode] =
                static_cast<float>(cohesion.modes[mode].imaginary);
        }
        public_snapshot.cohesion.applied_clear_generation =
            cohesion.applied_clear_generation;
        public_snapshot.cohesion.maximum_mode_state_absolute =
            cohesion.maximum_mode_state_absolute;
        public_snapshot.cohesion.maximum_duck_envelope =
            cohesion.maximum_duck_envelope;
        public_snapshot.cohesion.dry_difference_energy =
            cohesion.dry_difference_energy;
    }

    void accept(const Controls& requested) noexcept {
        SanitizeCounts counts{};
        const auto next = sanitizeControls(requested, &counts);
        diagnostics.invalid_control_count += counts.invalid;
        diagnostics.clamped_control_count += counts.clamped;
        const bool seed_changed = next.seed != accepted.seed;
        const bool clear_changed =
            next.effect_clear_generation != accepted.effect_clear_generation;
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
        setEffectTargets();
        if (seed_changed) {
            resetTransport(accepted.seed);
        }
        if (clear_changed) {
            if (!seed_changed) {
                clearEffectHistory();
            }
            cohesion.applied_clear_generation =
                accepted.effect_clear_generation;
            effect_cleared_for_quantum = true;
            ++diagnostics.effect_clear_count;
        }
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

    [[nodiscard]] bool processCohesionSample(
        std::int64_t main_sum,
        std::int64_t auxiliary_sum,
        double& output_left,
        double& output_right,
        double& master_gain) noexcept {
        master_gain = cohesion.master.step();
        const auto drive = cohesion.drive.step();
        const auto cohere = cohesion.cohere.step();
        const auto root_note = cohesion.root_note.step();
        const auto spread = cohesion.spread.step();
        const auto tail = cohesion.tail.step();
        const auto damping = cohesion.damping.step();
        const auto width = cohesion.width.step();
        const auto duck = cohesion.duck.step();

        const std::array<double, 9U> parameters{{
            master_gain,
            drive,
            cohere,
            root_note,
            spread,
            tail,
            damping,
            width,
            duck,
        }};
        if (!std::all_of(
                parameters.begin(), parameters.end(), [](double value) {
                    return std::isfinite(value);
                })) {
            ++diagnostics.effect_recovery_count;
            clearEffectHistory();
            master_gain = std::isfinite(master_gain)
                ? master_gain
                : static_cast<double>(accepted.master_gain);
            return false;
        }

        const auto dry_left = static_cast<double>(main_sum) / kQ27Scale;
        const auto dry_right = static_cast<double>(auxiliary_sum) / kQ27Scale;
        const auto drive_sample = [drive](double input) noexcept {
            if (drive == 0.0) return input;
            const auto gain = 1.0 + 7.0 * drive;
            const auto denominator = std::tanh(gain);
            return (1.0 - drive) * input
                + drive * std::tanh(gain * input) / denominator;
        };
        const auto driven_left = drive_sample(dry_left);
        const auto driven_right = drive_sample(dry_right);
        const auto mid = 0.5 * (driven_left + driven_right);
        const auto side = 0.5 * (driven_left - driven_right);

        const auto envelope_input = std::max(
            std::abs(dry_left), std::abs(dry_right));
        const auto envelope_seconds = envelope_input > cohesion.duck_envelope
            ? 0.005
            : 0.160;
        const auto envelope_coefficient = 1.0 - std::exp(
            -1.0
            / (envelope_seconds * static_cast<double>(kSampleRateHz)));
        cohesion.duck_envelope +=
            (envelope_input - cohesion.duck_envelope)
            * envelope_coefficient;
        cohesion.maximum_duck_envelope = std::max(
            cohesion.maximum_duck_envelope, cohesion.duck_envelope);

        const auto root_hz = 440.0 * std::pow(
            2.0, (root_note - 69.0) / 12.0);
        const auto base_tail = 0.06 * std::pow(4.0 / 0.06, tail);
        double wet_left = 0.0;
        double wet_right = 0.0;
        double weight_sum = 0.0;
        bool valid = std::isfinite(driven_left)
            && std::isfinite(driven_right)
            && std::isfinite(cohesion.duck_envelope)
            && std::isfinite(root_hz)
            && std::isfinite(base_tail);
        for (std::size_t index = 0;
             valid && index < kCohesionModeCount;
             ++index) {
            const auto ratio = kHarmonicRatios[index]
                + (kInharmonicRatios[index] - kHarmonicRatios[index])
                    * spread;
            const auto frequency = std::min(
                kMaximumModalFrequencyHz, root_hz * ratio);
            const auto mode_tail = base_tail
                / (1.0 + damping * 0.32 * static_cast<double>(index));
            const auto pole = std::exp(
                -1.0
                / (mode_tail * static_cast<double>(kSampleRateHz)));
            const auto weight = std::exp(
                -0.34 * damping * static_cast<double>(index));
            const auto pan = kBasePans[index] * width;
            valid = std::isfinite(frequency)
                && frequency > 0.0
                && frequency < 0.45 * static_cast<double>(kSampleRateHz)
                && std::isfinite(pole)
                && pole > 0.0
                && pole < 1.0
                && std::isfinite(weight)
                && weight > 0.0
                && std::isfinite(pan);
            if (!valid) break;

            auto& mode = cohesion.modes[index];
            const auto excitation = mid + side * pan;
            const auto excited_real = mode.real
                + excitation * weight * (1.0 - pole);
            const auto angle = kTwoPi * frequency
                / static_cast<double>(kSampleRateHz);
            const auto cosine = std::cos(angle);
            const auto sine = std::sin(angle);
            const auto next_real = pole
                * (excited_real * cosine - mode.imaginary * sine);
            const auto next_imaginary = pole
                * (excited_real * sine + mode.imaginary * cosine);
            valid = std::isfinite(next_real) && std::isfinite(next_imaginary);
            if (!valid) break;

            mode.real = std::abs(next_real) < kDenormalThreshold
                ? 0.0
                : next_real;
            mode.imaginary = std::abs(next_imaginary) < kDenormalThreshold
                ? 0.0
                : next_imaginary;
            mode.frequency_hz = frequency;
            mode.pole = pole;
            cohesion.maximum_mode_state_absolute = std::max(
                cohesion.maximum_mode_state_absolute,
                std::max(std::abs(mode.real), std::abs(mode.imaginary)));
            wet_left += mode.real * weight * (1.0 - pan);
            wet_right += mode.real * weight * (1.0 + pan);
            weight_sum += weight;
        }

        valid = valid
            && std::isfinite(weight_sum)
            && weight_sum > 0.0
            && std::isfinite(wet_left)
            && std::isfinite(wet_right);
        if (!valid) {
            ++diagnostics.effect_recovery_count;
            clearEffectHistory();
            return false;
        }

        wet_left /= weight_sum;
        wet_right /= weight_sum;
        const auto duck_gain = 1.0
            / (1.0 + 6.0 * duck * cohesion.duck_envelope);
        const auto effect_left = driven_left + 0.82 * wet_left * duck_gain;
        const auto effect_right = driven_right + 0.82 * wet_right * duck_gain;
        output_left = dry_left + cohere * (effect_left - dry_left);
        output_right = dry_right + cohere * (effect_right - dry_right);
        valid = std::isfinite(output_left)
            && std::isfinite(output_right)
            && std::isfinite(duck_gain);
        if (!valid) {
            ++diagnostics.effect_recovery_count;
            clearEffectHistory();
            return false;
        }
        const auto difference_left = output_left - dry_left;
        const auto difference_right = output_right - dry_right;
        cohesion.dry_difference_energy +=
            difference_left * difference_left
            + difference_right * difference_right;
        return true;
    }

    [[nodiscard]] bool renderQuantum(QuantumEvent& event) noexcept {
        const auto effect_cleared = effect_cleared_for_quantum;
        effect_cleared_for_quantum = false;
        event = {};
        event.absolute_frame = render_frame;
        event.effect_cleared = effect_cleared;
        event.effect_clear_generation = cohesion.applied_clear_generation;
        if (!accepted.running) {
            if (was_running) resetTransport(accepted.seed);
            main_quantum.fill(0);
            auxiliary_quantum.fill(0);
            setResolvedToBase();
            quantum_cursor = 0U;
            render_frame += kMacroVoiceQuantumFrames;
            ++quantum_count;
            refreshSnapshot();
            return effect_cleared;
        }
        was_running = true;

        std::array<float, kLaneCount> lane_values{};
        std::array<std::array<float, kDestinationCount>, kLaneCount>
            modulation{};
        std::uint8_t boundary_mask = 0U;
        std::uint8_t accepted_mask = 0U;
        std::uint8_t trigger_lane_mask = 0U;

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
            for (std::size_t destination = 0;
                 destination < kDestinationCount;
                 ++destination) {
                const auto raw = lane_values[lane_index]
                    * controls.routes[destination];
                const auto bounded = std::clamp(raw, -1.0F, 1.0F);
                if (bounded != raw) ++diagnostics.modulation_clamp_count;
                modulation[lane_index][destination] = bounded;
            }
            if (boundary
                && state.accepted_step
                && controls.amplitude > 0.0F
                && controls.routes[destinationIndex(Destination::trigger)]
                    == 1.0F) {
                trigger_lane_mask = static_cast<std::uint8_t>(
                    trigger_lane_mask | (1U << lane_index));
                ++diagnostics.trigger_count;
                ++diagnostics.lane_trigger_count[lane_index];
            }
        }

        std::array<std::uint8_t, kLaneCount> resolved_engines{};
        std::array<float, kLaneCount> resolved_notes{};
        std::array<float, kLaneCount> resolved_harmonics{};
        std::array<float, kLaneCount> resolved_timbres{};
        std::array<float, kLaneCount> resolved_morphs{};
        std::array<float, kLaneCount> resolved_decays{};
        std::array<float, kLaneCount> resolved_lpg_colours{};
        std::array<float, kLaneCount> resolved_levels{};

        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            const auto& base = accepted.voices[lane];
            const auto& local = modulation[lane];
            const auto model_offset = static_cast<int>(std::lround(
                23.0 * local[destinationIndex(Destination::model)]));
            resolved_engines[lane] = static_cast<std::uint8_t>(std::clamp(
                static_cast<int>(base.engine) + model_offset, 0, 23));
            resolved_notes[lane] = std::clamp(
                base.note
                    + 24.0F * local[destinationIndex(Destination::pitch)],
                24.0F,
                96.0F);
            const auto unit = [&local](float value, Destination destination) {
                return std::clamp(
                    value + local[destinationIndex(destination)], 0.0F, 1.0F);
            };
            resolved_harmonics[lane] = unit(
                base.harmonics, Destination::harmonics);
            resolved_timbres[lane] = unit(base.timbre, Destination::timbre);
            resolved_morphs[lane] = unit(base.morph, Destination::morph);
            resolved_decays[lane] = unit(base.decay, Destination::decay);
            resolved_lpg_colours[lane] = base.lpg_colour;
            resolved_levels[lane] = unit(base.level, Destination::level);

            const bool trigger = (trigger_lane_mask & (1U << lane)) != 0U;
            if (trigger) voice_started[lane] = true;
            if (voice_started[lane]) {
                MacroVoiceControls voice_controls{};
                voice_controls.trigger = trigger;
                voice_controls.engine = resolved_engines[lane];
                voice_controls.note = resolved_notes[lane];
                voice_controls.harmonics = resolved_harmonics[lane];
                voice_controls.timbre = resolved_timbres[lane];
                voice_controls.morph = resolved_morphs[lane];
                voice_controls.decay = resolved_decays[lane];
                voice_controls.lpg_colour = resolved_lpg_colours[lane];
                voice_controls.level = resolved_levels[lane];
                voices[lane]->process(
                    voice_controls,
                    voice_main_quantum[lane],
                    voice_auxiliary_quantum[lane]);
            } else {
                voice_main_quantum[lane].fill(0);
                voice_auxiliary_quantum[lane].fill(0);
            }
        }

        for (std::size_t frame = 0; frame < kMacroVoiceQuantumFrames; ++frame) {
            std::int64_t main_sum = 0;
            std::int64_t auxiliary_sum = 0;
            for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
                main_sum += scaleContributionQ27(
                    voice_main_quantum[lane][frame], resolved_levels[lane]);
                auxiliary_sum += scaleContributionQ27(
                    voice_auxiliary_quantum[lane][frame], resolved_levels[lane]);
            }
            double effect_left = 0.0;
            double effect_right = 0.0;
            double master_gain = accepted.master_gain;
            const auto effect_valid = processCohesionSample(
                main_sum,
                auxiliary_sum,
                effect_left,
                effect_right,
                master_gain);
            if (!effect_valid || cohesion.cohere.current == 0.0) {
                main_quantum[frame] = saturateMixQ27(
                    main_sum, master_gain, diagnostics);
                auxiliary_quantum[frame] = saturateMixQ27(
                    auxiliary_sum, master_gain, diagnostics);
            } else {
                main_quantum[frame] = saturateFloatQ27(
                    effect_left, master_gain, diagnostics);
                auxiliary_quantum[frame] = saturateFloatQ27(
                    effect_right, master_gain, diagnostics);
            }
        }
        quantum_cursor = 0U;

        std::uint8_t started_lane_mask = 0U;
        event.boundary_mask = boundary_mask;
        event.accepted_mask = accepted_mask;
        event.trigger_lane_mask = trigger_lane_mask;
        event.effect_cleared = effect_cleared;
        event.effect_clear_generation = cohesion.applied_clear_generation;
        event.resolved_engines = resolved_engines;
        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            if (voice_started[lane]) {
                started_lane_mask = static_cast<std::uint8_t>(
                    started_lane_mask | (1U << lane));
            }
            event.steps[lane] = lanes[lane].observed_step;
            event.addresses[lane] = lanes[lane].address;
        }
        event.started_lane_mask = started_lane_mask;

        public_snapshot.lane_values = lane_values;
        public_snapshot.modulation_values = modulation;
        public_snapshot.trigger_lane_mask = trigger_lane_mask;
        public_snapshot.started_lane_mask = started_lane_mask;
        public_snapshot.resolved_engines = resolved_engines;
        public_snapshot.resolved_notes = resolved_notes;
        public_snapshot.resolved_harmonics = resolved_harmonics;
        public_snapshot.resolved_timbres = resolved_timbres;
        public_snapshot.resolved_morphs = resolved_morphs;
        public_snapshot.resolved_decays = resolved_decays;
        public_snapshot.resolved_lpg_colours = resolved_lpg_colours;
        public_snapshot.resolved_levels = resolved_levels;

        advanceSchedulers();
        render_frame += kMacroVoiceQuantumFrames;
        ++quantum_count;
        refreshSnapshot();
        return boundary_mask != 0U
            || trigger_lane_mask != 0U
            || effect_cleared;
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
