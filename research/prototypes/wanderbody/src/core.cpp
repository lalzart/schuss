#include "wanderbody/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <new>
#include <utility>
#include <vector>

namespace wanderbody {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kTwoPi = 2.0 * kPi;
constexpr std::uint32_t kInvalidReleaseFrames = 64U;
constexpr std::uint32_t kCoefficientQuantum = 16U;
constexpr double kMinimumSampleRate = 8000.0;
constexpr double kMaximumSampleRate = 192000.0;
constexpr std::uint8_t kNoHistoryIndex = 255U;

[[nodiscard]] bool unitValue(double value) noexcept {
    return std::isfinite(value) && value >= 0.0 && value <= 1.0;
}

[[nodiscard]] bool validMotion(MotionMode mode) noexcept {
    return mode == MotionMode::hover || mode == MotionMode::drunk;
}

[[nodiscard]] bool validRecurrence(RecurrenceMode mode) noexcept {
    return mode == RecurrenceMode::fresh
        || mode == RecurrenceMode::locked
        || mode == RecurrenceMode::shuffled
        || mode == RecurrenceMode::mutated;
}

[[nodiscard]] bool validGenerationMode(GenerationMode mode) noexcept {
    return mode == GenerationMode::correlated
        || mode == GenerationMode::independent_uniform;
}

[[nodiscard]] double clampUnit(double value) noexcept {
    return std::clamp(value, 0.0, 1.0);
}

[[nodiscard]] double equalPowerLeft(double pan) noexcept {
    return std::cos(kPi * (std::clamp(pan, -1.0, 1.0) + 1.0) * 0.25);
}

[[nodiscard]] double equalPowerRight(double pan) noexcept {
    return std::sin(kPi * (std::clamp(pan, -1.0, 1.0) + 1.0) * 0.25);
}

[[nodiscard]] double reflectBounded(
    double value,
    double minimum,
    double maximum) noexcept {
    if (!(std::isfinite(value) && std::isfinite(minimum) && std::isfinite(maximum))
        || maximum <= minimum) {
        return std::clamp(minimum, 0.0, 1.0);
    }
    for (std::size_t iteration = 0U; iteration < 4U; ++iteration) {
        if (value < minimum) {
            value = minimum + (minimum - value);
        } else if (value > maximum) {
            value = maximum - (value - maximum);
        } else {
            return value;
        }
    }
    return std::clamp(value, minimum, maximum);
}

struct Pcg32 final {
    std::uint64_t state{};
    std::uint64_t increment{1U};

    void seed(std::uint64_t initial_state, std::uint64_t stream) noexcept {
        state = 0U;
        increment = (stream << 1U) | 1U;
        static_cast<void>(next());
        state += initial_state;
        static_cast<void>(next());
    }

    [[nodiscard]] std::uint32_t next() noexcept {
        const auto old = state;
        state = old * 6364136223846793005ULL + increment;
        const auto shifted = static_cast<std::uint32_t>(
            ((old >> 18U) ^ old) >> 27U);
        const auto rotation = static_cast<std::uint32_t>(old >> 59U);
        return (shifted >> rotation)
            | (shifted << ((0U - rotation) & 31U));
    }

    [[nodiscard]] double unit() noexcept {
        return static_cast<double>(next()) / 4294967296.0;
    }

    [[nodiscard]] double bipolar() noexcept {
        return unit() * 2.0 - 1.0;
    }
};

[[nodiscard]] std::uint64_t splitmix64(std::uint64_t& value) noexcept {
    value += 0x9e3779b97f4a7c15ULL;
    auto mixed = value;
    mixed = (mixed ^ (mixed >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    mixed = (mixed ^ (mixed >> 27U)) * 0x94d049bb133111ebULL;
    return mixed ^ (mixed >> 31U);
}

struct Smoother final {
    double current{};
    double target{};
    double increment{};
    std::uint32_t remaining{};

    void reset(double value) noexcept {
        current = value;
        target = value;
        increment = 0.0;
        remaining = 0U;
    }

    void setTarget(double value, std::uint32_t frames) noexcept {
        if (value == target) return;
        target = value;
        if (frames == 0U) {
            reset(value);
            return;
        }
        increment = (target - current) / static_cast<double>(frames);
        remaining = frames;
    }

    [[nodiscard]] double next() noexcept {
        if (remaining > 0U) {
            current += increment;
            --remaining;
            if (remaining == 0U) current = target;
        }
        return current;
    }
};

struct SmoothedControls final {
    Smoother external{};
    Smoother internal{};
    Smoother anchor{};
    Smoother field{};
    Smoother wander{};
    Smoother mutation{};
    Smoother fragment{};
    Smoother energy{};
    Smoother body{};
    Smoother structure{};
    Smoother brightness{};
    Smoother damping{};
    Smoother position{};
    Smoother dry{};
    Smoother memory{};

    void reset(const Controls& controls) noexcept {
        external.reset(controls.external);
        internal.reset(controls.internal);
        anchor.reset(controls.anchor);
        field.reset(controls.field);
        wander.reset(controls.wander);
        mutation.reset(controls.mutation);
        fragment.reset(controls.fragment);
        energy.reset(controls.energy);
        body.reset(controls.body);
        structure.reset(controls.structure);
        brightness.reset(controls.brightness);
        damping.reset(controls.damping);
        position.reset(controls.position);
        dry.reset(controls.dry);
        memory.reset(controls.memory);
    }

    void setTargets(const Controls& controls, std::uint32_t frames) noexcept {
        external.setTarget(controls.external, frames);
        internal.setTarget(controls.internal, frames);
        anchor.setTarget(controls.anchor, frames);
        field.setTarget(controls.field, frames);
        wander.setTarget(controls.wander, frames);
        mutation.setTarget(controls.mutation, frames);
        fragment.setTarget(controls.fragment, frames);
        energy.setTarget(controls.energy, frames);
        body.setTarget(controls.body, frames);
        structure.setTarget(controls.structure, frames);
        brightness.setTarget(controls.brightness, frames);
        damping.setTarget(controls.damping, frames);
        position.setTarget(controls.position, frames);
        dry.setTarget(controls.dry, frames);
        memory.setTarget(controls.memory, frames);
    }

    void advance() noexcept {
        static_cast<void>(external.next());
        static_cast<void>(internal.next());
        static_cast<void>(anchor.next());
        static_cast<void>(field.next());
        static_cast<void>(wander.next());
        static_cast<void>(mutation.next());
        static_cast<void>(fragment.next());
        static_cast<void>(energy.next());
        static_cast<void>(body.next());
        static_cast<void>(structure.next());
        static_cast<void>(brightness.next());
        static_cast<void>(damping.next());
        static_cast<void>(position.next());
        static_cast<void>(dry.next());
        static_cast<void>(memory.next());
    }
};

struct CaptureStore final {
    std::vector<float> samples{};
    std::uint64_t write_frame{};
    std::uint64_t valid_frames{};
    std::uint64_t epoch{};

    [[nodiscard]] std::size_t capacity() const noexcept {
        return samples.size();
    }

    void invalidate() noexcept {
        write_frame = 0U;
        valid_frames = 0U;
        ++epoch;
    }

    void write(float sample) noexcept {
        if (samples.empty()) return;
        samples[static_cast<std::size_t>(write_frame % samples.size())] = sample;
        ++write_frame;
        valid_frames = std::min<std::uint64_t>(
            valid_frames + 1U,
            static_cast<std::uint64_t>(samples.size()));
    }

    [[nodiscard]] std::uint64_t oldestFrame() const noexcept {
        return write_frame - valid_frames;
    }

    [[nodiscard]] bool read(double frame, float& result) const noexcept {
        if (samples.empty() || valid_frames < 2U || !std::isfinite(frame)
            || frame < 0.0) {
            result = 0.0F;
            return false;
        }
        const double floored = std::floor(frame);
        if (floored < 0.0
            || floored > static_cast<double>(std::numeric_limits<std::uint64_t>::max() - 1U)) {
            result = 0.0F;
            return false;
        }
        const auto first = static_cast<std::uint64_t>(floored);
        const auto second = first + 1U;
        const auto oldest = oldestFrame();
        if (first < oldest || second >= write_frame) {
            result = 0.0F;
            return false;
        }
        const double fraction = frame - floored;
        const auto first_sample = samples[static_cast<std::size_t>(first % samples.size())];
        const auto second_sample = samples[static_cast<std::size_t>(second % samples.size())];
        const double interpolated = static_cast<double>(first_sample)
            + (static_cast<double>(second_sample) - static_cast<double>(first_sample))
                * fraction;
        result = std::isfinite(interpolated)
            ? static_cast<float>(interpolated)
            : 0.0F;
        return std::isfinite(interpolated);
    }

    [[nodiscard]] bool sourceStart(
        double normalized_position,
        std::uint32_t length,
        double rate,
        double& result) const noexcept {
        if (samples.empty() || length < 2U || !std::isfinite(rate)
            || std::abs(rate) < 0.5 || valid_frames < 4U) {
            return false;
        }
        const double extent = static_cast<double>(length - 1U) * std::abs(rate);
        const double oldest = static_cast<double>(oldestFrame());
        const double newest = static_cast<double>(write_frame - 2U);
        double minimum = oldest;
        double maximum = newest - extent;
        if (rate < 0.0) {
            minimum = oldest + extent;
            maximum = newest;
        }
        if (!(maximum > minimum)) return false;
        result = minimum + (maximum - minimum) * clampUnit(normalized_position);
        return std::isfinite(result);
    }

    [[nodiscard]] double normalized(double frame) const noexcept {
        if (valid_frames < 2U || !std::isfinite(frame)) return 0.0;
        const double oldest = static_cast<double>(oldestFrame());
        const double span = static_cast<double>(valid_frames - 1U);
        return clampUnit((frame - oldest) / span);
    }
};

struct Voice final {
    DecisionTuple tuple{};
    double source_position{};
    double pan_left{0.7071067811865476};
    double pan_right{0.7071067811865476};
    float last_left{};
    float last_right{};
    std::uint64_t source_epoch{};
    std::uint64_t birth_ordinal{};
    std::uint32_t length{};
    std::uint32_t age{};
    std::uint32_t release_remaining{};
    bool active{};
    bool invalidating{};

    void clear() noexcept {
        *this = Voice{};
    }

    void start(
        const DecisionTuple& next_tuple,
        double next_source_position,
        std::uint64_t next_epoch,
        std::uint64_t ordinal,
        double sample_rate) noexcept {
        tuple = next_tuple;
        source_position = next_source_position;
        source_epoch = next_epoch;
        birth_ordinal = ordinal;
        length = static_cast<std::uint32_t>(std::clamp<long long>(
            std::llround(tuple.duration_seconds * sample_rate),
            32LL,
            static_cast<long long>(std::numeric_limits<std::uint32_t>::max())));
        age = 0U;
        release_remaining = 0U;
        invalidating = false;
        pan_left = equalPowerLeft(tuple.pan);
        pan_right = equalPowerRight(tuple.pan);
        last_left = 0.0F;
        last_right = 0.0F;
        active = true;
    }

    [[nodiscard]] std::pair<float, float> render(
        const CaptureStore& capture,
        Diagnostics& diagnostics) noexcept {
        if (!active) return {0.0F, 0.0F};
        if (invalidating) {
            const double fade = static_cast<double>(release_remaining)
                / static_cast<double>(kInvalidReleaseFrames);
            const auto left = static_cast<float>(static_cast<double>(last_left) * fade);
            const auto right = static_cast<float>(static_cast<double>(last_right) * fade);
            if (release_remaining > 0U) --release_remaining;
            if (release_remaining == 0U) clear();
            return {left, right};
        }
        if (age >= length || source_epoch != capture.epoch) {
            invalidating = true;
            release_remaining = kInvalidReleaseFrames;
            ++diagnostics.invalid_read_count;
            return render(capture, diagnostics);
        }
        float source{};
        if (!capture.read(source_position, source)) {
            invalidating = true;
            release_remaining = kInvalidReleaseFrames;
            ++diagnostics.invalid_read_count;
            return render(capture, diagnostics);
        }
        const double phase = length > 1U
            ? static_cast<double>(age) / static_cast<double>(length - 1U)
            : 1.0;
        const double window = 0.5 - 0.5 * std::cos(kTwoPi * phase);
        const double mono = static_cast<double>(source) * window * tuple.gain;
        const double left = mono * pan_left;
        const double right = mono * pan_right;
        if (!(std::isfinite(left) && std::isfinite(right))) {
            clear();
            ++diagnostics.voice_repair_count;
            return {0.0F, 0.0F};
        }
        last_left = static_cast<float>(left);
        last_right = static_cast<float>(right);
        source_position += tuple.rate;
        ++age;
        if (age >= length) active = false;
        return {last_left, last_right};
    }
};

struct BodyMode final {
    double left_y1{};
    double left_y2{};
    double right_y1{};
    double right_y2{};
    double a1{};
    double a2{};
    double gain_left{};
    double gain_right{};

    void clear() noexcept {
        left_y1 = 0.0;
        left_y2 = 0.0;
        right_y1 = 0.0;
        right_y2 = 0.0;
    }
};

struct DcBlocker final {
    double x1{};
    double y1{};

    void clear() noexcept {
        x1 = 0.0;
        y1 = 0.0;
    }

    [[nodiscard]] double process(double input) noexcept {
        const double output = input - x1 + 0.995 * y1;
        x1 = input;
        y1 = output;
        return output;
    }
};

}  // namespace

Controls defaultControls() noexcept {
    return Controls{};
}

bool validControls(const Controls& controls) noexcept {
    return unitValue(controls.external)
        && unitValue(controls.internal)
        && unitValue(controls.anchor)
        && unitValue(controls.field)
        && validMotion(controls.motion)
        && unitValue(controls.wander)
        && validRecurrence(controls.recurrence)
        && unitValue(controls.mutation)
        && unitValue(controls.fragment)
        && unitValue(controls.energy)
        && unitValue(controls.body)
        && unitValue(controls.structure)
        && unitValue(controls.brightness)
        && unitValue(controls.damping)
        && unitValue(controls.position)
        && unitValue(controls.dry)
        && unitValue(controls.memory);
}

bool sameControls(const Controls& left, const Controls& right) noexcept {
    return left.external == right.external
        && left.internal == right.internal
        && left.anchor == right.anchor
        && left.field == right.field
        && left.motion == right.motion
        && left.wander == right.wander
        && left.recurrence == right.recurrence
        && left.mutation == right.mutation
        && left.fragment == right.fragment
        && left.energy == right.energy
        && left.body == right.body
        && left.structure == right.structure
        && left.brightness == right.brightness
        && left.damping == right.damping
        && left.position == right.position
        && left.dry == right.dry
        && left.memory == right.memory;
}

bool validDecisionTuple(const DecisionTuple& tuple) noexcept {
    return unitValue(tuple.position)
        && std::isfinite(tuple.duration_seconds)
        && tuple.duration_seconds >= 0.08
        && tuple.duration_seconds <= 0.48
        && std::isfinite(tuple.rate)
        && std::abs(tuple.rate) >= 0.5
        && std::abs(tuple.rate) <= 1.5
        && std::isfinite(tuple.gain)
        && tuple.gain >= 0.0
        && tuple.gain <= 0.42
        && std::isfinite(tuple.pan)
        && tuple.pan >= -1.0
        && tuple.pan <= 1.0
        && std::isfinite(tuple.body_frequency_hz)
        && tuple.body_frequency_hz >= 55.0
        && tuple.body_frequency_hz <= 440.0
        && tuple.direction <= 1U;
}

const char* motionName(MotionMode mode) noexcept {
    switch (mode) {
        case MotionMode::hover: return "Hover";
        case MotionMode::drunk: return "Drunk";
    }
    return "Invalid";
}

const char* recurrenceName(RecurrenceMode mode) noexcept {
    switch (mode) {
        case RecurrenceMode::fresh: return "Fresh";
        case RecurrenceMode::locked: return "Locked";
        case RecurrenceMode::shuffled: return "Shuffled";
        case RecurrenceMode::mutated: return "Mutated";
    }
    return "Invalid";
}

const char* diagnosticName(DiagnosticCode code) noexcept {
    switch (code) {
        case DiagnosticCode::none: return "none";
        case DiagnosticCode::unprepared: return "unprepared";
        case DiagnosticCode::invalid_buffer: return "invalid-buffer";
        case DiagnosticCode::oversized_block: return "oversized-block";
        case DiagnosticCode::invalid_controls: return "invalid-controls";
        case DiagnosticCode::invalid_state: return "invalid-state";
        case DiagnosticCode::numeric_fault: return "numeric-fault";
    }
    return "invalid-diagnostic";
}

struct Core::Impl final {
    explicit Impl(std::uint64_t value) : seed(value) {
        seedRandom();
        resetState(false);
    }

    std::uint64_t seed{kDefaultSeed};
    double sample_rate{};
    std::uint32_t maximum_block_frames{};
    bool prepared{};
    bool controls_initialized{true};

    Controls accepted{defaultControls()};
    SmoothedControls smooth{};
    ActionSequences last_actions{};
    GenerationMode generation_mode{GenerationMode::correlated};
    CaptureStore capture{};
    std::array<Voice, kVoiceCount> voices{};
    std::array<BodyMode, kBodyModeCount> body_modes{};
    DcBlocker dc_left{};
    DcBlocker dc_right{};
    Diagnostics diagnostics{};
    DiagnosticCode latched_fault{DiagnosticCode::none};

    Pcg32 motion_random{};
    Pcg32 recurrence_random{};
    Pcg32 exciter_random{};
    std::array<DecisionTuple, kHistoryCapacity> history{};
    std::array<std::uint8_t, kHistoryCapacity> permutation{};
    std::uint8_t history_count{};
    std::uint8_t history_write{};
    std::uint8_t recurrence_cursor{};
    std::uint8_t permutation_count{};

    double hover_phase{0.5};
    double hover_direction{1.0};
    double drunk_position{0.55};
    double drunk_velocity{};
    double body_frequency{110.0};
    double body_frequency_target{110.0};
    double exciter_phase{};
    double exciter_envelope{};
    std::uint64_t exciter_age{};
    std::uint64_t exciter_countdown{};
    std::uint64_t next_launch_countdown{};
    std::uint64_t absolute_frame{};
    std::uint64_t decision_ordinal{};

    ClearPhase clear_phase{ClearPhase::idle};
    double clear_gain{1.0};
    bool frozen{};

    std::array<float, kScopeCapacity> scope{};
    std::uint64_t next_scope_frame{};

    void seedRandom() noexcept {
        auto source = seed;
        motion_random.seed(splitmix64(source), splitmix64(source));
        recurrence_random.seed(splitmix64(source), splitmix64(source));
        exciter_random.seed(splitmix64(source), splitmix64(source));
    }

    void clearVoicesAndBody() noexcept {
        for (auto& voice : voices) voice.clear();
        for (auto& mode : body_modes) mode.clear();
        dc_left.clear();
        dc_right.clear();
        body_frequency = 110.0;
        body_frequency_target = 110.0;
    }

    void clearHistory() noexcept {
        history = {};
        for (std::size_t index = 0U; index < permutation.size(); ++index) {
            permutation[index] = static_cast<std::uint8_t>(index);
        }
        history_count = 0U;
        history_write = 0U;
        recurrence_cursor = 0U;
        permutation_count = 0U;
    }

    void resetState(bool count_reset) noexcept {
        accepted = defaultControls();
        smooth.reset(accepted);
        last_actions = {};
        generation_mode = GenerationMode::correlated;
        seedRandom();
        capture.invalidate();
        clearVoicesAndBody();
        clearHistory();
        hover_phase = 0.5;
        hover_direction = 1.0;
        drunk_position = accepted.anchor;
        drunk_velocity = 0.0;
        exciter_phase = 0.0;
        exciter_envelope = 0.0;
        exciter_age = 0U;
        exciter_countdown = 0U;
        next_launch_countdown = 0U;
        absolute_frame = 0U;
        decision_ordinal = 0U;
        clear_phase = ClearPhase::idle;
        clear_gain = 1.0;
        frozen = false;
        scope = {};
        next_scope_frame = 0U;
        latched_fault = DiagnosticCode::none;
        const auto storage_bytes = diagnostics.capture_storage_bytes;
        diagnostics = {};
        diagnostics.capture_storage_bytes = storage_bytes;
        if (count_reset) diagnostics.reset_count = 1U;
    }

    [[nodiscard]] std::uint32_t smoothingFrames() const noexcept {
        return static_cast<std::uint32_t>(std::max<long long>(
            1LL,
            std::llround(sample_rate * 0.020)));
    }

    [[nodiscard]] std::uint32_t clearFrames() const noexcept {
        return static_cast<std::uint32_t>(std::max<long long>(
            1LL,
            std::llround(sample_rate * 0.010)));
    }

    [[nodiscard]] std::size_t logicalToPhysical(std::size_t logical) const noexcept {
        if (history_count < kHistoryCapacity) return logical;
        return (static_cast<std::size_t>(history_write) + logical) % kHistoryCapacity;
    }

    void appendHistory(const DecisionTuple& tuple) noexcept {
        history[history_write] = tuple;
        history_write = static_cast<std::uint8_t>((history_write + 1U) % kHistoryCapacity);
        if (history_count < kHistoryCapacity) ++history_count;
        permutation_count = 0U;
    }

    [[nodiscard]] const DecisionTuple& historyAt(std::size_t logical) const noexcept {
        return history[logicalToPhysical(logical % std::max<std::size_t>(1U, history_count))];
    }

    void makePermutation() noexcept {
        permutation_count = history_count;
        for (std::size_t index = 0U; index < history_count; ++index) {
            permutation[index] = static_cast<std::uint8_t>(index);
        }
        if (history_count > 1U) {
            for (std::size_t index = history_count - 1U; index > 0U; --index) {
                const auto selected = static_cast<std::size_t>(
                    recurrence_random.next() % static_cast<std::uint32_t>(index + 1U));
                std::swap(permutation[index], permutation[selected]);
            }
            bool identity = true;
            for (std::size_t index = 0U; index < history_count; ++index) {
                identity = identity && permutation[index] == index;
            }
            if (identity) std::swap(permutation[0], permutation[1]);
        }
        recurrence_cursor = 0U;
    }

    void acceptControls(const Controls& controls) noexcept {
        const auto previous_recurrence = accepted.recurrence;
        accepted = controls;
        if (!controls_initialized) {
            smooth.reset(accepted);
            controls_initialized = true;
        } else {
            smooth.setTargets(accepted, smoothingFrames());
        }
        if (previous_recurrence != accepted.recurrence) {
            recurrence_cursor = 0U;
            if (accepted.recurrence == RecurrenceMode::shuffled) makePermutation();
        }
    }

    void panic() noexcept {
        clearVoicesAndBody();
        exciter_envelope = 0.0;
        exciter_age = 0U;
        next_launch_countdown = 32U;
        ++diagnostics.panic_count;
    }

    void beginClear() noexcept {
        clear_phase = ClearPhase::fading_out;
        if (clear_gain <= 0.0) clear_gain = 1.0;
        ++diagnostics.clear_count;
    }

    void updateClear() noexcept {
        const double increment = 1.0 / static_cast<double>(clearFrames());
        if (clear_phase == ClearPhase::fading_out) {
            clear_gain = std::max(0.0, clear_gain - increment);
            if (clear_gain <= 0.0) {
                capture.invalidate();
                clearVoicesAndBody();
                clearHistory();
                hover_phase = 0.5;
                hover_direction = 1.0;
                drunk_position = smooth.anchor.current;
                drunk_velocity = 0.0;
                next_launch_countdown = 32U;
                clear_phase = ClearPhase::fading_in;
            }
        } else if (clear_phase == ClearPhase::fading_in) {
            clear_gain = std::min(1.0, clear_gain + increment);
            if (clear_gain >= 1.0) clear_phase = ClearPhase::idle;
        }
    }

    [[nodiscard]] double nextInternalSource() noexcept {
        const double energy = clampUnit(smooth.energy.current);
        if (exciter_countdown == 0U) {
            exciter_envelope = 1.0;
            exciter_age = 0U;
            const double seconds = 0.5 + 1.5 * (1.0 - energy);
            exciter_countdown = static_cast<std::uint64_t>(std::max<long long>(
                1LL,
                std::llround(seconds * sample_rate)));
        } else {
            --exciter_countdown;
        }

        const double frequency = 55.0 * std::pow(2.0, 2.0 * clampUnit(smooth.anchor.current));
        exciter_phase += frequency / sample_rate;
        exciter_phase -= std::floor(exciter_phase);
        const double triangle = 1.0 - 4.0 * std::abs(exciter_phase - 0.5);
        const double attack_frames = std::max(1.0, 0.003 * sample_rate);
        const double attack = std::min(1.0, static_cast<double>(exciter_age) / attack_frames);
        const double decay = std::exp(-static_cast<double>(exciter_age) / (0.180 * sample_rate));
        const double noise_decay = std::exp(-static_cast<double>(exciter_age) / (0.008 * sample_rate));
        const double noise = exciter_random.bipolar() * 0.18 * noise_decay;
        const double result = (triangle * 0.27 + noise) * attack * decay * exciter_envelope;
        ++exciter_age;
        if (decay < 1.0e-6) exciter_envelope = 0.0;
        return std::clamp(result, -0.45, 0.45);
    }

    [[nodiscard]] DecisionTuple generateFresh() noexcept {
        DecisionTuple tuple{};
        const double anchor = clampUnit(smooth.anchor.current);
        const double field = 0.01 + 0.47 * clampUnit(smooth.field.current);
        const double minimum = std::max(0.0, anchor - field);
        const double maximum = std::min(1.0, anchor + field);
        const double wander = clampUnit(smooth.wander.current);
        double position = anchor;
        double direction = 1.0;

        if (generation_mode == GenerationMode::independent_uniform) {
            position = minimum + (maximum - minimum) * motion_random.unit();
            direction = motion_random.unit() < 0.5 ? -1.0 : 1.0;
        } else if (accepted.motion == MotionMode::hover) {
            position = anchor + field * wander * (2.0 * hover_phase - 1.0);
            direction = hover_direction;
            hover_phase += (0.12 + 0.20 * wander) * hover_direction;
            if (hover_phase > 1.0) {
                hover_phase = 2.0 - hover_phase;
                hover_direction = -1.0;
            } else if (hover_phase < 0.0) {
                hover_phase = -hover_phase;
                hover_direction = 1.0;
            }
        } else {
            if (wander == 0.0) {
                drunk_velocity = 0.0;
                drunk_position = anchor;
            } else {
                const double acceleration = motion_random.bipolar()
                    * (0.002 + 0.12 * wander);
                drunk_velocity = std::clamp(
                    0.86 * drunk_velocity + 0.14 * acceleration,
                    -0.14,
                    0.14);
                drunk_position = reflectBounded(
                    drunk_position + drunk_velocity,
                    minimum,
                    maximum);
            }
            position = drunk_position;
            direction = drunk_velocity < 0.0 ? -1.0 : 1.0;
        }

        tuple.position = std::clamp(position, minimum, maximum);
        tuple.duration_seconds = 0.08 + 0.40 * clampUnit(smooth.fragment.current);
        const double rate_magnitude = 0.85 + 0.30 * motion_random.unit();
        tuple.direction = direction < 0.0 ? 0U : 1U;
        tuple.rate = tuple.direction == 0U ? -rate_magnitude : rate_magnitude;
        tuple.gain = std::clamp(0.24 + 0.18 * clampUnit(smooth.energy.current), 0.0, 0.42);
        tuple.pan = std::clamp(
            (tuple.position - 0.5) * 1.6 + motion_random.bipolar() * 0.08,
            -1.0,
            1.0);
        tuple.body_frequency_hz = std::clamp(
            55.0 * std::pow(2.0, 2.0 * tuple.position),
            55.0,
            440.0);
        return tuple;
    }

    struct SelectedDecision final {
        DecisionTuple tuple{};
        std::uint8_t history_index{kNoHistoryIndex};
        bool replayed{};
        bool shuffled{};
        bool mutated{};
    };

    [[nodiscard]] SelectedDecision selectDecision() noexcept {
        SelectedDecision selected{};
        if (accepted.recurrence == RecurrenceMode::fresh || history_count == 0U) {
            selected.tuple = generateFresh();
            appendHistory(selected.tuple);
            selected.history_index = static_cast<std::uint8_t>(history_count - 1U);
            return selected;
        }

        if (accepted.recurrence == RecurrenceMode::shuffled
            && permutation_count != history_count) {
            makePermutation();
        }
        std::uint8_t logical_index = static_cast<std::uint8_t>(
            recurrence_cursor % history_count);
        if (accepted.recurrence == RecurrenceMode::shuffled) {
            logical_index = permutation[logical_index];
            selected.shuffled = true;
        }
        selected.tuple = historyAt(logical_index);
        selected.history_index = logical_index;
        selected.replayed = true;
        recurrence_cursor = static_cast<std::uint8_t>(
            (recurrence_cursor + 1U) % history_count);

        if (accepted.recurrence == RecurrenceMode::mutated) {
            const double amount = clampUnit(smooth.mutation.current);
            const double field = 0.01 + 0.47 * clampUnit(smooth.field.current);
            const double position_delta = recurrence_random.bipolar()
                * 0.08 * field * amount;
            const double rate_delta = recurrence_random.bipolar() * 0.08 * amount;
            const double duration_scale = 1.0
                + recurrence_random.bipolar() * 0.08 * amount;
            const double pan_delta = recurrence_random.bipolar() * 0.10 * amount;
            selected.tuple.position = clampUnit(selected.tuple.position + position_delta);
            const double sign = selected.tuple.rate < 0.0 ? -1.0 : 1.0;
            selected.tuple.rate = sign * std::clamp(
                std::abs(selected.tuple.rate) + rate_delta,
                0.5,
                1.5);
            selected.tuple.duration_seconds = std::clamp(
                selected.tuple.duration_seconds * duration_scale,
                0.08,
                0.48);
            selected.tuple.pan = std::clamp(selected.tuple.pan + pan_delta, -1.0, 1.0);
            selected.tuple.body_frequency_hz = std::clamp(
                55.0 * std::pow(2.0, 2.0 * selected.tuple.position),
                55.0,
                440.0);
            selected.mutated = amount > 0.0;
        }
        return selected;
    }

    [[nodiscard]] std::size_t allocateVoice(bool& stolen) noexcept {
        for (std::size_t index = 0U; index < voices.size(); ++index) {
            if (!voices[index].active) {
                stolen = false;
                return index;
            }
        }
        auto oldest = std::size_t{0U};
        for (std::size_t index = 1U; index < voices.size(); ++index) {
            if (voices[index].birth_ordinal < voices[oldest].birth_ordinal) oldest = index;
        }
        stolen = true;
        ++diagnostics.voice_steal_count;
        return oldest;
    }

    [[nodiscard]] bool schedule(DecisionEvent& event) noexcept {
        auto selected = selectDecision();
        if (!validDecisionTuple(selected.tuple)) {
            ++diagnostics.decision_drop_count;
            return false;
        }
        const auto length = static_cast<std::uint32_t>(std::clamp<long long>(
            std::llround(selected.tuple.duration_seconds * sample_rate),
            32LL,
            static_cast<long long>(std::numeric_limits<std::uint32_t>::max())));
        double source_start{};
        if (!capture.sourceStart(
                selected.tuple.position,
                length,
                selected.tuple.rate,
                source_start)) {
            ++diagnostics.decision_drop_count;
            return false;
        }
        bool stolen{};
        const auto voice_index = allocateVoice(stolen);
        ++decision_ordinal;
        voices[voice_index].start(
            selected.tuple,
            source_start,
            capture.epoch,
            decision_ordinal,
            sample_rate);
        body_frequency_target = selected.tuple.body_frequency_hz;

        event.absolute_frame = absolute_frame;
        event.ordinal = decision_ordinal;
        event.source_epoch = capture.epoch;
        event.source_start_frame = static_cast<std::uint64_t>(std::floor(source_start));
        event.tuple = selected.tuple;
        event.motion = accepted.motion;
        event.recurrence = accepted.recurrence;
        event.history_index = selected.history_index;
        event.voice_index = static_cast<std::uint8_t>(voice_index);
        event.replayed = selected.replayed;
        event.shuffled = selected.shuffled;
        event.mutated = selected.mutated;
        event.stolen = stolen;
        ++diagnostics.decision_count;

        const double hop_ratio = 0.72 - 0.32 * clampUnit(smooth.energy.current);
        next_launch_countdown = static_cast<std::uint64_t>(std::max<long long>(
            32LL,
            std::llround(static_cast<double>(length) * hop_ratio)));
        return true;
    }

    void updateBodyCoefficients() noexcept {
        const double frequency_step = 1.0 / static_cast<double>(smoothingFrames());
        body_frequency += (body_frequency_target - body_frequency)
            * std::min(1.0, frequency_step * kCoefficientQuantum);
        const double structure = clampUnit(smooth.structure.current);
        const double brightness = clampUnit(smooth.brightness.current);
        const double damping = clampUnit(smooth.damping.current);
        const double position = clampUnit(smooth.position.current);
        const double decay_seconds = 0.12 * std::pow(40.0, damping);
        const double radius = std::clamp(
            std::exp(-1.0 / (decay_seconds * sample_rate)),
            0.0,
            0.999999);
        for (std::size_t index = 0U; index < body_modes.size(); ++index) {
            const double order = static_cast<double>(index + 1U);
            const double stretch = 1.0 + 0.018 * structure * static_cast<double>(index);
            const double frequency = std::min(
                body_frequency * order * stretch,
                sample_rate * 0.45);
            const double omega = kTwoPi * frequency / sample_rate;
            auto& mode = body_modes[index];
            mode.a1 = 2.0 * radius * std::cos(omega);
            mode.a2 = -(radius * radius);
            const double spectral = 0.25 + 0.75 * std::pow(
                brightness,
                0.5 * static_cast<double>(index) + 1.0);
            const double left_position = std::sin(kPi * order * position);
            const double right_position = std::sin(
                kPi * order * std::fmod(position + 0.07, 1.0));
            const double normalization = 1.0 / std::sqrt(static_cast<double>(kBodyModeCount));
            mode.gain_left = left_position * spectral * normalization;
            mode.gain_right = right_position * spectral * normalization;
        }
    }

    [[nodiscard]] std::pair<double, double> renderBody(double input) noexcept {
        double left{};
        double right{};
        for (auto& mode : body_modes) {
            const double next_left = input * mode.gain_left
                + mode.a1 * mode.left_y1 + mode.a2 * mode.left_y2;
            const double next_right = input * mode.gain_right
                + mode.a1 * mode.right_y1 + mode.a2 * mode.right_y2;
            if (!(std::isfinite(next_left) && std::isfinite(next_right))) {
                mode.clear();
                ++diagnostics.body_repair_count;
                continue;
            }
            mode.left_y2 = mode.left_y1;
            mode.left_y1 = next_left;
            mode.right_y2 = mode.right_y1;
            mode.right_y1 = next_right;
            left += next_left;
            right += next_right;
        }
        return {left * 0.18, right * 0.18};
    }

    void updateScope() noexcept {
        if (sample_rate <= 0.0 || absolute_frame < next_scope_frame) return;
        next_scope_frame = absolute_frame + static_cast<std::uint64_t>(
            std::max<long long>(1LL, std::llround(sample_rate / 20.0)));
        if (capture.valid_frames == 0U || capture.samples.empty()) {
            scope = {};
        } else {
            const auto oldest = capture.oldestFrame();
            const auto span = capture.valid_frames - 1U;
            for (std::size_t index = 0U; index < scope.size(); ++index) {
                const auto offset = span * index / (scope.size() - 1U);
                const auto frame = oldest + offset;
                scope[index] = capture.samples[static_cast<std::size_t>(
                    frame % capture.samples.size())];
            }
        }
        ++diagnostics.snapshot_sequence;
    }

    [[nodiscard]] bool validState(const CoreState& state) const noexcept {
        if (state.version != kStateVersion || !validControls(state.controls)
            || !validGenerationMode(state.generation_mode)
            || state.history_count > kHistoryCapacity
            || state.history_write >= kHistoryCapacity
            || state.permutation_count > state.history_count
            || (state.history_count > 0U && state.recurrence_cursor >= state.history_count)) {
            return false;
        }
        for (std::size_t index = 0U; index < state.random_streams.size(); ++index) {
            if ((state.random_streams[index] & 1U) == 0U) return false;
        }
        const std::size_t tuple_count = state.history_count < kHistoryCapacity
            ? state.history_count
            : kHistoryCapacity;
        for (std::size_t index = 0U; index < tuple_count; ++index) {
            if (!validDecisionTuple(state.history[index])) return false;
        }
        std::array<bool, kHistoryCapacity> seen{};
        for (std::size_t index = 0U; index < state.permutation_count; ++index) {
            if (state.permutation[index] >= state.history_count
                || seen[state.permutation[index]]) {
                return false;
            }
            seen[state.permutation[index]] = true;
        }
        return std::isfinite(state.hover_phase)
            && state.hover_phase >= 0.0 && state.hover_phase <= 1.0
            && std::isfinite(state.hover_direction)
            && std::abs(state.hover_direction) == 1.0
            && std::isfinite(state.drunk_position)
            && state.drunk_position >= 0.0 && state.drunk_position <= 1.0
            && std::isfinite(state.drunk_velocity)
            && std::abs(state.drunk_velocity) <= 0.14;
    }
};

Core::Core(std::uint64_t seed)
    : impl_(std::make_unique<Impl>(seed)) {}

Core::~Core() = default;
Core::Core(Core&&) noexcept = default;
Core& Core::operator=(Core&&) noexcept = default;

bool Core::prepare(double sample_rate, std::uint32_t maximum_block_frames) noexcept {
    if (!(std::isfinite(sample_rate)
          && sample_rate >= kMinimumSampleRate
          && sample_rate <= kMaximumSampleRate)
        || maximum_block_frames == 0U
        || maximum_block_frames > kMaximumBlockFrames) {
        impl_->prepared = false;
        return false;
    }
    const auto capacity = static_cast<std::size_t>(std::ceil(
        sample_rate * kCaptureSeconds));
    try {
        impl_->capture.samples.assign(capacity, 0.0F);
    } catch (const std::bad_alloc&) {
        impl_->capture.samples.clear();
        impl_->prepared = false;
        return false;
    }
    impl_->sample_rate = sample_rate;
    impl_->maximum_block_frames = maximum_block_frames;
    impl_->prepared = true;
    impl_->diagnostics.capture_storage_bytes = capacity * sizeof(float);
    impl_->resetState(false);
    impl_->prepared = true;
    impl_->controls_initialized = false;
    impl_->diagnostics.capture_storage_bytes = capacity * sizeof(float);
    return true;
}

void Core::reset() noexcept {
    const bool was_prepared = impl_->prepared;
    const auto rate = impl_->sample_rate;
    const auto maximum = impl_->maximum_block_frames;
    impl_->resetState(true);
    impl_->prepared = was_prepared;
    impl_->sample_rate = rate;
    impl_->maximum_block_frames = maximum;
    impl_->diagnostics.capture_storage_bytes = impl_->capture.capacity() * sizeof(float);
}

ProcessReport Core::process(
    const Controls& controls,
    const ActionSequences& actions,
    const float* input_left,
    const float* input_right,
    float* output_left,
    float* output_right,
    std::uint32_t frame_count) noexcept {
    ProcessReport report{};
    const auto clear_outputs = [&]() noexcept {
        if (output_left != nullptr) {
            std::fill_n(output_left, frame_count, 0.0F);
        }
        if (output_right != nullptr) {
            std::fill_n(output_right, frame_count, 0.0F);
        }
    };

    if (!impl_->prepared) {
        clear_outputs();
        report.diagnostic = DiagnosticCode::unprepared;
        return report;
    }
    if (output_left == nullptr || output_right == nullptr || frame_count == 0U) {
        clear_outputs();
        report.diagnostic = DiagnosticCode::invalid_buffer;
        return report;
    }
    if (frame_count > impl_->maximum_block_frames) {
        clear_outputs();
        report.diagnostic = DiagnosticCode::oversized_block;
        return report;
    }
    if (!validControls(controls)) {
        clear_outputs();
        ++impl_->diagnostics.rejected_control_count;
        report.diagnostic = DiagnosticCode::invalid_controls;
        return report;
    }

    bool reset_applied = false;
    if (actions.reset > impl_->last_actions.reset) {
        const bool was_prepared = impl_->prepared;
        const auto rate = impl_->sample_rate;
        const auto maximum = impl_->maximum_block_frames;
        impl_->resetState(true);
        impl_->prepared = was_prepared;
        impl_->sample_rate = rate;
        impl_->maximum_block_frames = maximum;
        impl_->last_actions = actions;
        impl_->diagnostics.capture_storage_bytes = impl_->capture.capacity() * sizeof(float);
        reset_applied = true;
    } else {
        if (actions.freeze > impl_->last_actions.freeze) {
            impl_->frozen = !impl_->frozen;
            ++impl_->diagnostics.freeze_count;
        }
        if (actions.clear > impl_->last_actions.clear) impl_->beginClear();
        if (actions.panic > impl_->last_actions.panic) impl_->panic();
        impl_->last_actions = actions;
    }
    if (!reset_applied) impl_->acceptControls(controls);

    for (std::uint32_t frame = 0U; frame < frame_count; ++frame) {
        impl_->smooth.advance();
        impl_->updateClear();

        double external{};
        int input_channels{};
        if (input_left != nullptr) {
            double value = static_cast<double>(input_left[frame]);
            if (!std::isfinite(value)) {
                value = 0.0;
                ++impl_->diagnostics.non_finite_input_count;
            }
            external += std::clamp(value, -2.0, 2.0);
            ++input_channels;
        }
        if (input_right != nullptr) {
            double value = static_cast<double>(input_right[frame]);
            if (!std::isfinite(value)) {
                value = 0.0;
                ++impl_->diagnostics.non_finite_input_count;
            }
            external += std::clamp(value, -2.0, 2.0);
            ++input_channels;
        }
        if (input_channels > 0) external /= static_cast<double>(input_channels);
        const double internal = impl_->nextInternalSource();
        const double external_gain = impl_->smooth.external.current;
        const double internal_gain = impl_->smooth.internal.current;
        const double source_normalization = std::max(1.0, external_gain + internal_gain);
        const double live = std::clamp(
            (external * external_gain + internal * internal_gain) / source_normalization,
            -2.0,
            2.0);
        if (!impl_->frozen) impl_->capture.write(static_cast<float>(live));

        const bool scheduler_enabled = impl_->smooth.memory.current > 0.0
            || impl_->smooth.body.current > 0.0;
        if (scheduler_enabled) {
            if (impl_->next_launch_countdown == 0U) {
                DecisionEvent event{};
                if (impl_->schedule(event)) {
                    if (report.decision_count < report.decisions.size()) {
                        report.decisions[report.decision_count++] = event;
                    } else {
                        ++impl_->diagnostics.decision_drop_count;
                    }
                } else {
                    impl_->next_launch_countdown = 32U;
                }
            } else {
                --impl_->next_launch_countdown;
            }
        }

        double memory_left{};
        double memory_right{};
        for (auto& voice : impl_->voices) {
            const auto rendered = voice.render(impl_->capture, impl_->diagnostics);
            memory_left += rendered.first;
            memory_right += rendered.second;
        }
        memory_left *= 0.5;
        memory_right *= 0.5;
        const double memory_mono = (memory_left + memory_right) * 0.5;

        if ((impl_->absolute_frame % kCoefficientQuantum) == 0U) {
            impl_->updateBodyCoefficients();
        }
        const auto body = impl_->renderBody(memory_mono * 0.20);
        if (impl_->smooth.body.target == 0.0
            && impl_->smooth.body.current < 1.0e-6) {
            for (auto& mode : impl_->body_modes) mode.clear();
        }

        const double dry_gain = impl_->smooth.dry.current;
        const double memory_gain = impl_->smooth.memory.current;
        const double body_gain = impl_->smooth.body.current;
        const double mix_normalization = std::max(
            1.0,
            dry_gain + memory_gain + body_gain);
        const double wet_gate = impl_->clear_gain;
        double left = (live * dry_gain
            + memory_left * memory_gain * wet_gate
            + body.first * body_gain * wet_gate) / mix_normalization;
        double right = (live * dry_gain
            + memory_right * memory_gain * wet_gate
            + body.second * body_gain * wet_gate) / mix_normalization;
        left = impl_->dc_left.process(left);
        right = impl_->dc_right.process(right);
        left = 0.98 * left / (1.0 + std::abs(left));
        right = 0.98 * right / (1.0 + std::abs(right));
        if (!(std::isfinite(left) && std::isfinite(right))) {
            left = 0.0;
            right = 0.0;
            impl_->latched_fault = DiagnosticCode::numeric_fault;
            ++impl_->diagnostics.final_fault_count;
            report.diagnostic = DiagnosticCode::numeric_fault;
        }
        output_left[frame] = static_cast<float>(left);
        output_right[frame] = static_cast<float>(right);

        ++impl_->absolute_frame;
        ++impl_->diagnostics.processed_frames;
        impl_->updateScope();
    }
    return report;
}

Snapshot Core::snapshot() const noexcept {
    Snapshot result{};
    result.accepted_controls = impl_->accepted;
    result.diagnostics = impl_->diagnostics;
    result.capture_scope = impl_->scope;
    result.absolute_frame = impl_->absolute_frame;
    result.capture_write_frame = impl_->capture.write_frame;
    result.capture_valid_frames = impl_->capture.valid_frames;
    result.capture_epoch = impl_->capture.epoch;
    result.capture_capacity_frames = static_cast<std::uint32_t>(impl_->capture.capacity());
    result.history_count = impl_->history_count;
    result.motion = impl_->accepted.motion;
    result.recurrence = impl_->accepted.recurrence;
    result.clear_phase = impl_->clear_phase;
    result.clear_gain = static_cast<float>(impl_->clear_gain);
    result.frozen = impl_->frozen;
    result.prepared = impl_->prepared;
    result.latched_fault = impl_->latched_fault;
    for (std::size_t index = 0U; index < impl_->voices.size(); ++index) {
        if (impl_->voices[index].active) {
            ++result.active_voice_count;
            result.active_head_positions[index] = impl_->capture.normalized(
                impl_->voices[index].source_position);
        }
    }
    return result;
}

CoreState Core::captureState() const noexcept {
    CoreState result{};
    result.version = kStateVersion;
    result.controls = impl_->accepted;
    result.seed = impl_->seed;
    result.random_states = {{
        impl_->motion_random.state,
        impl_->recurrence_random.state,
        impl_->exciter_random.state,
    }};
    result.random_streams = {{
        impl_->motion_random.increment,
        impl_->recurrence_random.increment,
        impl_->exciter_random.increment,
    }};
    result.history = impl_->history;
    result.permutation = impl_->permutation;
    result.absolute_frame = impl_->absolute_frame;
    result.decision_ordinal = impl_->decision_ordinal;
    result.next_launch_countdown = impl_->next_launch_countdown;
    result.hover_phase = impl_->hover_phase;
    result.hover_direction = impl_->hover_direction;
    result.drunk_position = impl_->drunk_position;
    result.drunk_velocity = impl_->drunk_velocity;
    result.history_count = impl_->history_count;
    result.history_write = impl_->history_write;
    result.recurrence_cursor = impl_->recurrence_cursor;
    result.permutation_count = impl_->permutation_count;
    result.frozen = impl_->frozen;
    result.generation_mode = impl_->generation_mode;
    return result;
}

bool Core::recallState(const CoreState& state) noexcept {
    if (!impl_->validState(state)) {
        ++impl_->diagnostics.rejected_state_count;
        impl_->latched_fault = DiagnosticCode::invalid_state;
        return false;
    }
    impl_->accepted = state.controls;
    impl_->smooth.reset(state.controls);
    impl_->seed = state.seed;
    impl_->motion_random.state = state.random_states[0];
    impl_->recurrence_random.state = state.random_states[1];
    impl_->exciter_random.state = state.random_states[2];
    impl_->motion_random.increment = state.random_streams[0];
    impl_->recurrence_random.increment = state.random_streams[1];
    impl_->exciter_random.increment = state.random_streams[2];
    impl_->history = state.history;
    impl_->permutation = state.permutation;
    impl_->absolute_frame = state.absolute_frame;
    impl_->decision_ordinal = state.decision_ordinal;
    impl_->next_launch_countdown = state.next_launch_countdown;
    impl_->hover_phase = state.hover_phase;
    impl_->hover_direction = state.hover_direction;
    impl_->drunk_position = state.drunk_position;
    impl_->drunk_velocity = state.drunk_velocity;
    impl_->history_count = state.history_count;
    impl_->history_write = state.history_write;
    impl_->recurrence_cursor = state.recurrence_cursor;
    impl_->permutation_count = state.permutation_count;
    impl_->frozen = state.frozen;
    impl_->generation_mode = state.generation_mode;
    impl_->capture.invalidate();
    impl_->clearVoicesAndBody();
    impl_->exciter_phase = 0.0;
    impl_->exciter_envelope = 0.0;
    impl_->exciter_age = 0U;
    impl_->clear_phase = ClearPhase::idle;
    impl_->clear_gain = 1.0;
    impl_->scope = {};
    impl_->latched_fault = DiagnosticCode::none;
    ++impl_->diagnostics.snapshot_sequence;
    return true;
}

void Core::setGenerationMode(GenerationMode mode) noexcept {
    if (validGenerationMode(mode)) impl_->generation_mode = mode;
}

GenerationMode Core::generationMode() const noexcept {
    return impl_->generation_mode;
}

double Core::sampleRate() const noexcept {
    return impl_->sample_rate;
}

std::uint32_t Core::maximumBlockFrames() const noexcept {
    return impl_->maximum_block_frames;
}

bool Core::isPrepared() const noexcept {
    return impl_->prepared;
}

}  // namespace wanderbody
