#include "cinderwheel/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <utility>

namespace cinderwheel {
namespace {

constexpr double kPi = 3.14159265358979323846264338327950288;
constexpr std::size_t kMaximumGrainSamples = 48000;
constexpr std::size_t kDiffusionLeftSamples = 1493;
constexpr std::size_t kDiffusionRightSamples = 1877;
constexpr std::uint32_t kParameterRampMs = 20;

double clampNormalized(double value) noexcept {
    return std::clamp(value, 0.0, 1.0);
}

double midiToFrequency(double midi_note) noexcept {
    return 440.0 * std::pow(2.0, (midi_note - 69.0) / 12.0);
}

float softFold(float value) noexcept {
    value = std::fmod(value + 3.0f, 4.0f);
    if (value < 0.0f) value += 4.0f;
    return value < 2.0f ? value - 1.0f : 3.0f - value;
}

float denormalZero(float value) noexcept {
    return std::abs(value) < 1.0e-20f ? 0.0f : value;
}

std::uint32_t xorshift32(std::uint32_t& state) noexcept {
    state ^= state << 13U;
    state ^= state >> 17U;
    state ^= state << 5U;
    return state;
}

float signedNoise(std::uint32_t& state) noexcept {
    const auto bits = xorshift32(state) >> 8U;
    return static_cast<float>(bits) * (2.0f / 16777215.0f) - 1.0f;
}

template <typename Enum>
Enum nextEnum(Enum value, std::uint8_t count) noexcept {
    return static_cast<Enum>((static_cast<std::uint8_t>(value) + 1U) % count);
}

}  // namespace

struct Core::Impl {
    struct Smoothed {
        double current{};
        double target{};
        double step{};
        std::uint32_t remaining{};

        void reset(double value) noexcept {
            current = value;
            target = value;
            step = 0.0;
            remaining = 0;
        }

        void set(double value, std::uint32_t samples) noexcept {
            target = value;
            if (samples == 0) {
                reset(value);
                return;
            }
            remaining = samples;
            step = (target - current) / static_cast<double>(remaining);
        }

        double next() noexcept {
            if (remaining > 0) {
                current += step;
                --remaining;
                if (remaining == 0) current = target;
            }
            return current;
        }
    };

    struct Resonator {
        float real{};
        float imaginary{};
        float cosine{1.0f};
        float sine{};
        float decay{0.999f};
        float input_gain{0.02f};
        double frequency_hz{};

        void clear() noexcept {
            real = 0.0f;
            imaginary = 0.0f;
        }

        void configure(double frequency, double decay_seconds, double sample_rate, float gain) noexcept {
            const double safe_frequency = std::clamp(frequency, 0.5, sample_rate * 0.45);
            frequency_hz = safe_frequency;
            const double angle = 2.0 * kPi * safe_frequency / sample_rate;
            cosine = static_cast<float>(std::cos(angle));
            sine = static_cast<float>(std::sin(angle));
            decay = static_cast<float>(std::exp(-1.0 / std::max(1.0, decay_seconds * sample_rate)));
            // Keep the driven response bounded as decay changes. Without the
            // pole-distance term, a resonant input is amplified by roughly
            // 1 / (1 - decay) and spends most of the render in the ceiling.
            input_gain = gain * (1.0f - decay);
        }

        void strike(float amount) noexcept {
            real += amount;
        }

        float process(float input, bool& cleared) noexcept {
            real += input * input_gain;
            const float rotated_real = (real * cosine - imaginary * sine) * decay;
            const float rotated_imaginary = (real * sine + imaginary * cosine) * decay;
            real = denormalZero(rotated_real);
            imaginary = denormalZero(rotated_imaginary);
            if (!std::isfinite(real) || !std::isfinite(imaginary)) {
                clear();
                cleared = true;
                return 0.0f;
            }
            return real;
        }
    };

    struct ButtonState {
        bool down{};
        bool hold_fired{};
        std::uint64_t pressed_at_sample{};
    };

    bool prepared{};
    double sample_rate{kReferenceSampleRate};
    std::uint32_t maximum_block_frames{kMaximumBlockFrames};
    std::uint32_t ramp_samples{960};
    Diagnostics diagnostics{};

    std::array<Smoothed, 4> stage_values{};
    Smoothed rate{};
    Smoothed memory{};
    Smoothed body{};
    Smoothed position{};
    std::array<std::array<Smoothed, 2>, 3> fx_parameters{};
    Smoothed fx_mode_crossfade{};
    Smoothed wake{};
    Smoothed structure{};
    Smoothed ember{};
    Smoothed output_gate{};
    std::array<std::array<bool, 2>, 3> fx_pickup_armed{};
    std::array<std::array<std::int16_t, 2>, 3> fx_pickup_previous{{{{-1, -1}}, {{-1, -1}}, {{-1, -1}}}};

    std::array<float, 4> mutation_offsets{};
    std::uint32_t random_state{0x43494e44U};
    double oscillator_phase{};
    double cycle_phase{};
    std::uint8_t current_stage{};
    std::uint32_t transition_index{};
    std::uint32_t pulse_counter{};
    std::uint8_t allocation_position{};
    std::uint64_t absolute_sample{};
    std::uint64_t last_ingress_sequence{};
    double parent_frequency_hz{130.81278265};
    double undertow_frequency_hz{};

    std::int32_t root_note{48};
    std::int32_t pending_root_note{48};
    std::uint8_t undertow_divisor{};
    std::uint8_t pending_undertow_divisor{};
    std::uint8_t pulse_divide{1};
    std::uint8_t pending_pulse_divide{1};
    SourceMode source{SourceMode::reed};
    SourceMode pending_source{SourceMode::reed};
    ScaleMode scale{ScaleMode::minor_pentatonic};
    ScaleMode pending_scale{ScaleMode::minor_pentatonic};
    FxMode fx_mode{FxMode::clean};
    FxMode pending_fx_mode{FxMode::clean};
    FxMode previous_fx_mode{FxMode::clean};
    WaveTarget wave_target{WaveTarget::pitch};
    WaveTarget pending_wave_target{WaveTarget::pitch};
    bool root_pending{};
    bool undertow_pending{};
    bool pulse_pending{};
    bool source_pending{};
    bool scale_pending{};
    bool fx_mode_pending{};
    bool wave_target_pending{};
    bool locked{};
    bool frozen{};
    bool bloom_armed{};
    bool panic_latched{};
    std::uint32_t panic_clear_remaining{};
    std::uint32_t wake_clear_remaining{};

    std::array<ButtonState, 8> button_states{};
    std::array<Resonator, 4> body_modes{};
    Resonator undertow_voice{};
    std::array<Resonator, 4> wake_voices{};
    std::array<float, 4> ledger_energy{};
    std::array<float, 4> ledger_transfers{};
    std::array<std::uint8_t, 4> rotor_positions{};
    std::array<std::uint8_t, 4> refractory{};

    std::array<float, kMaximumGrainSamples> grain_buffer{};
    std::size_t grain_length{48000};
    std::size_t grain_write{};
    std::array<float, kDiffusionLeftSamples> diffusion_left{};
    std::array<float, kDiffusionRightSamples> diffusion_right{};
    std::size_t diffusion_left_index{};
    std::size_t diffusion_right_index{};
    float filter_left{};
    float filter_right{};
    float drive_tone_left{};
    float drive_tone_right{};
    float dc_x_left{};
    float dc_x_right{};
    float dc_y_left{};
    float dc_y_right{};
    float dust_previous{};

    std::uint32_t millisecondsToSamples(std::uint32_t milliseconds) const noexcept {
        return static_cast<std::uint32_t>(std::llround(sample_rate * static_cast<double>(milliseconds) / 1000.0));
    }

    void initializeParameters() noexcept {
        constexpr std::array<double, 4> defaults{{0.20, 0.70, 0.35, 0.85}};
        for (std::size_t index = 0; index < stage_values.size(); ++index) {
            stage_values[index].reset(defaults[index]);
        }
        rate.reset(0.8);
        memory.reset(0.65);
        body.reset(0.55);
        position.reset(0.35);
        for (auto& mode : fx_parameters) {
            mode[0].reset(0.50);
            mode[1].reset(0.25);
        }
        fx_mode_crossfade.reset(1.0);
        wake.reset(0.0);
        structure.reset(0.50);
        ember.reset(0.0);
        output_gate.reset(1.0);
        fx_pickup_armed = {};
        fx_pickup_previous = {{{{-1, -1}}, {{-1, -1}}, {{-1, -1}}}};
        root_note = 48;
        pending_root_note = root_note;
        undertow_divisor = 0;
        pending_undertow_divisor = undertow_divisor;
        pulse_divide = 1;
        pending_pulse_divide = pulse_divide;
        source = SourceMode::reed;
        pending_source = source;
        scale = ScaleMode::minor_pentatonic;
        pending_scale = scale;
        fx_mode = FxMode::clean;
        pending_fx_mode = fx_mode;
        previous_fx_mode = fx_mode;
        wave_target = WaveTarget::pitch;
        pending_wave_target = wave_target;
        locked = false;
        frozen = false;
    }

    void clearWake() noexcept {
        for (auto& voice : wake_voices) voice.clear();
        ledger_energy.fill(0.0f);
        ledger_transfers.fill(0.0f);
        rotor_positions.fill(0);
        refractory.fill(0);
        allocation_position = 0;
        bloom_armed = false;
    }

    void clearAudioState(bool preserve_grain_buffer) noexcept {
        for (auto& voice : body_modes) voice.clear();
        undertow_voice.clear();
        clearWake();
        if (!preserve_grain_buffer) grain_buffer.fill(0.0f);
        diffusion_left.fill(0.0f);
        diffusion_right.fill(0.0f);
        grain_write = 0;
        diffusion_left_index = 0;
        diffusion_right_index = 0;
        filter_left = 0.0f;
        filter_right = 0.0f;
        drive_tone_left = 0.0f;
        drive_tone_right = 0.0f;
        dc_x_left = 0.0f;
        dc_x_right = 0.0f;
        dc_y_left = 0.0f;
        dc_y_right = 0.0f;
        dust_previous = 0.0f;
    }

    void fullReset() noexcept {
        diagnostics = {};
        initializeParameters();
        mutation_offsets.fill(0.0f);
        random_state = 0x43494e44U;
        oscillator_phase = 0.0;
        cycle_phase = 0.0;
        current_stage = 0;
        transition_index = 0;
        pulse_counter = 0;
        absolute_sample = 0;
        last_ingress_sequence = 0;
        root_pending = false;
        undertow_pending = false;
        pulse_pending = false;
        source_pending = false;
        scale_pending = false;
        fx_mode_pending = false;
        previous_fx_mode = fx_mode;
        fx_mode_crossfade.reset(1.0);
        wave_target_pending = false;
        bloom_armed = false;
        panic_latched = false;
        panic_clear_remaining = 0;
        wake_clear_remaining = 0;
        button_states = {};
        clearAudioState(false);
        updateResonatorCoefficients();
    }

    void musicalReset() noexcept {
        // A short Reset commits current control positions, then restores only
        // the musical cycle/mutation/Wake reference. The body, effects,
        // diffusion tail, and captured grain buffer continue sounding.
        applyPendingTransitionState();
        mutation_offsets.fill(0.0f);
        random_state = 0x43494e44U;
        cycle_phase = 0.0;
        current_stage = 0;
        transition_index = 0;
        pulse_counter = 0;
        root_pending = false;
        undertow_pending = false;
        pulse_pending = false;
        source_pending = false;
        scale_pending = false;
        fx_mode_pending = false;
        previous_fx_mode = fx_mode;
        fx_mode_crossfade.reset(1.0);
        wave_target_pending = false;
        panic_latched = false;
        panic_clear_remaining = 0;
        wake_clear_remaining = 0;
        output_gate.set(1.0, millisecondsToSamples(10));
        clearWake();
        updateResonatorCoefficients();
        ++diagnostics.reset_count;
    }

    void beginPanic() noexcept {
        if (panic_latched) return;
        panic_latched = true;
        frozen = false;
        panic_clear_remaining = millisecondsToSamples(10);
        output_gate.set(0.0, panic_clear_remaining);
        ++diagnostics.panic_count;
    }

    double stageWave() const noexcept {
        const double four_phase = cycle_phase * 4.0;
        const auto first = static_cast<std::size_t>(std::floor(four_phase)) % 4U;
        const auto second = (first + 1U) % 4U;
        const double local = four_phase - std::floor(four_phase);
        const double smooth = local * local * (3.0 - 2.0 * local);
        const double a = clampNormalized(stage_values[first].current + mutation_offsets[first]);
        const double b = clampNormalized(stage_values[second].current + mutation_offsets[second]);
        return a + (b - a) * smooth;
    }

    double scaleSemitone(double normalized) const noexcept {
        static constexpr std::array<std::array<double, 8>, 4> scales{{
            {{0.0, 3.0, 5.0, 7.0, 10.0, 12.0, 15.0, 17.0}},
            {{0.0, 2.0, 3.0, 5.0, 7.0, 9.0, 10.0, 12.0}},
            {{0.0, 2.0, 3.0, 5.0, 7.0, 8.0, 11.0, 12.0}},
            {{0.0, 7.0, 12.0, 19.0, 24.0, 31.0, 36.0, 43.0}},
        }};
        const double position_in_scale = clampNormalized(normalized) * 7.0;
        const auto low = static_cast<std::size_t>(std::floor(position_in_scale));
        const auto high = std::min<std::size_t>(7U, low + 1U);
        const double fraction = position_in_scale - static_cast<double>(low);
        const auto& selected = scales[static_cast<std::size_t>(scale)];
        return selected[low] + (selected[high] - selected[low]) * fraction;
    }

    void updateResonatorCoefficients() noexcept {
        const double structure_value = clampNormalized(structure.current);
        const double base = std::max(24.0, parent_frequency_hz);
        const std::array<double, 4> body_ratios{{
            1.0,
            1.49 + structure_value * 0.08,
            2.02 + structure_value * 0.18,
            2.91 + structure_value * 0.34,
        }};
        for (std::size_t index = 0; index < body_modes.size(); ++index) {
            const double decay_seconds = 0.20 + body.current * (0.55 + 0.12 * static_cast<double>(index));
            body_modes[index].configure(base * body_ratios[index], decay_seconds, sample_rate, 0.50f);
        }
        undertow_frequency_hz = undertow_divisor == 0
            ? 0.0
            : parent_frequency_hz / static_cast<double>(undertow_divisor);
        undertow_voice.configure(
            undertow_divisor == 0 ? 20.0 : undertow_frequency_hz,
            0.45 + body.current * 0.8,
            sample_rate,
            0.42f
        );
        const std::array<double, 4> wake_ratios{{
            0.75 + structure_value * 0.25,
            1.00 + structure_value * 0.36,
            1.49 + structure_value * 0.43,
            2.01 + structure_value * 0.62,
        }};
        const double wake_decay = 0.12 + ember.current * 1.25;
        for (std::size_t index = 0; index < wake_voices.size(); ++index) {
            wake_voices[index].configure(base * wake_ratios[index], wake_decay, sample_rate, 0.0f);
        }
    }

    void mutateOnce() noexcept {
        const float amount = static_cast<float>(0.10 * (1.0 - clampNormalized(memory.current)));
        for (auto& offset : mutation_offsets) {
            offset = signedNoise(random_state) * amount;
        }
    }

    void applyPendingTransitionState() noexcept {
        if (root_pending) {
            root_note = pending_root_note;
            root_pending = false;
        }
        if (undertow_pending) {
            if (undertow_divisor != pending_undertow_divisor) {
                undertow_divisor = pending_undertow_divisor;
                undertow_voice.clear();
            }
            undertow_pending = false;
        }
        if (pulse_pending) {
            pulse_divide = pending_pulse_divide;
            pulse_pending = false;
        }
        if (source_pending) {
            source = pending_source;
            source_pending = false;
        }
        if (scale_pending) {
            scale = pending_scale;
            scale_pending = false;
        }
        if (fx_mode_pending) {
            if (fx_mode != pending_fx_mode) {
                previous_fx_mode = fx_mode;
                fx_mode = pending_fx_mode;
                const auto new_mode = static_cast<std::size_t>(fx_mode);
                fx_mode_crossfade.reset(0.0);
                fx_mode_crossfade.set(1.0, ramp_samples);
                fx_pickup_armed[new_mode] = {{true, true}};
                fx_pickup_previous[new_mode] = {{-1, -1}};
            }
            fx_mode_pending = false;
        }
        if (wave_target_pending) {
            wave_target = pending_wave_target;
            wave_target_pending = false;
        }
    }

    void emitEvent(
        WakeEventKind kind,
        std::uint8_t voice,
        float energy,
        WakeEvent* output,
        std::size_t capacity,
        ProcessReport& report
    ) noexcept {
        WakeEvent event{
            absolute_sample + 1U,
            last_ingress_sequence,
            transition_index,
            voice,
            kind,
            energy,
        };
        if (output == nullptr && capacity == 0) return;
        if (output != nullptr && report.events_written < capacity) {
            output[report.events_written++] = event;
        } else {
            ++report.events_dropped;
            ++diagnostics.event_sink_overflows;
        }
    }

    void onStageTransition(
        WakeEvent* event_output,
        std::size_t event_capacity,
        ProcessReport& report
    ) noexcept {
        ++transition_index;
        ++diagnostics.stage_transitions;
        applyPendingTransitionState();
        updateResonatorCoefficients();
        if (panic_latched) return;

        const float transition_shape = static_cast<float>(0.18 + 0.32 * stageWave());
        for (std::size_t index = 0; index < body_modes.size(); ++index) {
            body_modes[index].strike(transition_shape * static_cast<float>(0.12 / (1.0 + index)));
        }
        if (undertow_divisor != 0) undertow_voice.strike(transition_shape * 0.16f);

        if (current_stage == 0 && !locked) {
            const float renewal = (signedNoise(random_state) + 1.0f) * 0.5f;
            if (renewal > static_cast<float>(clampNormalized(memory.current))) mutateOnce();
        }

        const float ember_value = static_cast<float>(clampNormalized(ember.current));
        const bool bloom = bloom_armed;
        bloom_armed = false;
        if (ember.target <= 0.0 || wake.target <= 0.0 || panic_latched) {
            ledger_energy.fill(0.0f);
            ledger_transfers.fill(0.0f);
            refractory.fill(0);
        } else {
            const float decay = 0.70f + ember_value * 0.24f;
            const float threshold = (1.10f - ember_value * 0.45f)
                * (bloom ? 0.82f : 1.0f);
            const float coupling = std::min(0.72f, ember_value * 0.72f);
            ledger_transfers.fill(0.0f);
            if (bloom) {
                ledger_energy[allocation_position] = std::clamp(
                    ledger_energy[allocation_position] + 0.70f,
                    0.0f,
                    4.0f
                );
            }
            std::uint8_t afterstrike_count = 0;
            bool eligible_beyond_cap = false;
            for (std::uint8_t voice = 0; voice < 4; ++voice) {
                ledger_energy[voice] = std::clamp(ledger_energy[voice] * decay, 0.0f, 4.0f);
                if (refractory[voice] > 0) {
                    --refractory[voice];
                    continue;
                }
                if (ledger_energy[voice] + 1.0e-7f < threshold) continue;
                if (afterstrike_count >= 2) {
                    eligible_beyond_cap = true;
                    continue;
                }
                ledger_energy[voice] -= threshold;
                const float amplitude = (0.16f + ember_value * 0.22f)
                    * static_cast<float>(clampNormalized(wake.current));
                wake_voices[voice].strike(amplitude);
                refractory[voice] = 1;
                const std::uint8_t rotor = rotor_positions[voice] % 3U;
                const std::uint8_t neighbor = static_cast<std::uint8_t>(
                    (voice + (rotor == 0 ? 1 : rotor == 1 ? 2 : 3)) % 4U
                );
                rotor_positions[voice] = static_cast<std::uint8_t>((rotor + 1U) % 3U);
                ledger_transfers[neighbor] += threshold * coupling;
                ++afterstrike_count;
                ++diagnostics.afterstrikes;
                emitEvent(WakeEventKind::afterstrike, voice, ledger_energy[voice], event_output, event_capacity, report);
            }
            if (eligible_beyond_cap) ++diagnostics.event_cap_hits;
            for (std::size_t index = 0; index < ledger_energy.size(); ++index) {
                ledger_energy[index] = std::clamp(ledger_energy[index] + ledger_transfers[index], 0.0f, 4.0f);
            }
        }

        ++pulse_counter;
        const bool accepted_primary = pulse_divide > 0 && pulse_counter % pulse_divide == 0;
        if (accepted_primary && wake.target > 0.0 && !panic_latched) {
            const std::uint8_t voice = allocation_position;
            allocation_position = static_cast<std::uint8_t>((allocation_position + 1U) % 4U);
            const float body_linked_excitation = 0.20f + transition_shape * 0.44f;
            wake_voices[voice].strike(
                body_linked_excitation * static_cast<float>(clampNormalized(wake.current))
            );
            if (ember.target > 0.0) {
                ledger_energy[voice] = std::clamp(
                    ledger_energy[voice]
                        + 0.54f
                        + transition_shape * 0.30f
                        + static_cast<float>(ember.current) * 0.38f,
                    0.0f,
                    4.0f
                );
            }
            ++diagnostics.primary_strikes;
            emitEvent(WakeEventKind::primary, voice, ledger_energy[voice], event_output, event_capacity, report);
        }
    }

    bool acceptFxPickup(std::size_t parameter, std::uint8_t midi_value) noexcept {
        const auto mode = static_cast<std::size_t>(fx_mode);
        if (!fx_pickup_armed[mode][parameter]) return true;
        const auto target = static_cast<std::int16_t>(std::llround(
            std::clamp(fx_parameters[mode][parameter].target, 0.0, 1.0) * 127.0
        ));
        const auto value = static_cast<std::int16_t>(midi_value);
        const auto previous = fx_pickup_previous[mode][parameter];
        const bool within_threshold = std::abs(value - target) <= 2;
        const bool crossed = previous >= 0
            && ((previous < target && value > target) || (previous > target && value < target));
        fx_pickup_previous[mode][parameter] = value;
        if (!within_threshold && !crossed) return false;
        fx_pickup_armed[mode][parameter] = false;
        return true;
    }

    void setEncoder(const EncoderDescriptor& descriptor, std::uint8_t midi_value) noexcept {
        const double normalized = normalizedFromMidi(midi_value);
        switch (descriptor.id) {
            case ControlId::wave_1:
            case ControlId::wave_2:
            case ControlId::wave_3:
            case ControlId::wave_4: {
                const auto index = static_cast<std::size_t>(descriptor.id) - static_cast<std::size_t>(ControlId::wave_1);
                stage_values[index].set(normalized, ramp_samples);
                mutation_offsets[index] = 0.0f;
                break;
            }
            case ControlId::rate:
                rate.set(rateHzFromMidi(midi_value), ramp_samples);
                break;
            case ControlId::memory:
                memory.set(normalized, ramp_samples);
                break;
            case ControlId::body:
                body.set(normalized, ramp_samples);
                break;
            case ControlId::position:
                position.set(normalized, ramp_samples);
                break;
            case ControlId::fx_a:
                if (!acceptFxPickup(0, midi_value)) break;
                fx_parameters[static_cast<std::size_t>(fx_mode)][0].set(normalized, ramp_samples);
                break;
            case ControlId::fx_b:
                if (!acceptFxPickup(1, midi_value)) break;
                fx_parameters[static_cast<std::size_t>(fx_mode)][1].set(normalized, ramp_samples);
                break;
            case ControlId::root:
                pending_root_note = rootNoteFromMidi(midi_value);
                root_pending = true;
                break;
            case ControlId::undertow:
                pending_undertow_divisor = undertowDivisorFromMidi(midi_value);
                undertow_pending = true;
                break;
            case ControlId::pulse_divide:
                pending_pulse_divide = pulseDivideFromMidi(midi_value);
                pulse_pending = true;
                break;
            case ControlId::wake:
                wake.set(normalized, midi_value == 0 ? millisecondsToSamples(10) : ramp_samples);
                if (midi_value == 0) {
                    wake_clear_remaining = millisecondsToSamples(10);
                    ledger_energy.fill(0.0f);
                    ledger_transfers.fill(0.0f);
                } else {
                    wake_clear_remaining = 0;
                }
                break;
            case ControlId::structure:
                structure.set(normalized, ramp_samples);
                break;
            case ControlId::ember:
                ember.set(normalized, ramp_samples);
                if (midi_value == 0) {
                    ledger_energy.fill(0.0f);
                    ledger_transfers.fill(0.0f);
                    refractory.fill(0);
                }
                break;
            default:
                ++diagnostics.ignored_midi_messages;
                break;
        }
    }

    void handleButtonPress(ControlId control) noexcept {
        switch (control) {
            case ControlId::mutate:
                mutateOnce();
                break;
            case ControlId::bloom:
                bloom_armed = true;
                break;
            default:
                break;
        }
    }

    void handleButtonTap(ControlId control) noexcept {
        switch (control) {
            case ControlId::source_scale:
                pending_source = nextEnum(source_pending ? pending_source : source, 4);
                source_pending = true;
                break;
            case ControlId::lock:
                locked = !locked;
                break;
            case ControlId::freeze:
                frozen = !frozen;
                break;
            case ControlId::fx_mode:
                pending_fx_mode = nextEnum(fx_mode_pending ? pending_fx_mode : fx_mode, 3);
                fx_mode_pending = true;
                break;
            case ControlId::wave_target:
                pending_wave_target = nextEnum(
                    wave_target_pending ? pending_wave_target : wave_target,
                    4
                );
                wave_target_pending = true;
                break;
            case ControlId::reset_panic:
                musicalReset();
                break;
            default:
                break;
        }
    }

    void handleButtonHold(ControlId control) noexcept {
        if (control == ControlId::source_scale) {
            pending_scale = nextEnum(scale_pending ? pending_scale : scale, 4);
            scale_pending = true;
        } else if (control == ControlId::reset_panic) {
            beginPanic();
        }
    }

    bool setButton(const ButtonDescriptor& descriptor, bool pressed) noexcept {
        const std::size_t index = static_cast<std::size_t>(descriptor.cc - 40U);
        auto& state = button_states[index];
        if (pressed) {
            if (state.down) {
                ++diagnostics.duplicate_button_edges;
                return false;
            }
            state.down = true;
            state.hold_fired = false;
            state.pressed_at_sample = absolute_sample;
            handleButtonPress(descriptor.id);
            return true;
        }
        if (!state.down) {
            ++diagnostics.duplicate_button_edges;
            return false;
        }
        if (!state.hold_fired && descriptor.hold_threshold_ms > 0) {
            const std::uint64_t threshold = millisecondsToSamples(descriptor.hold_threshold_ms);
            if (absolute_sample - state.pressed_at_sample >= threshold) {
                state.hold_fired = true;
                handleButtonHold(descriptor.id);
            }
        }
        state.down = false;
        if (!state.hold_fired && descriptor.hold_threshold_ms > 0) {
            handleButtonTap(descriptor.id);
        } else if (!state.hold_fired && descriptor.hold_threshold_ms == 0) {
            handleButtonTap(descriptor.id);
        }
        return true;
    }

    void checkButtonHolds() noexcept {
        for (std::size_t index = 0; index < button_states.size(); ++index) {
            auto& state = button_states[index];
            const auto& descriptor = kLaunchControl3Buttons[index];
            if (!state.down || state.hold_fired || descriptor.hold_threshold_ms == 0) continue;
            const std::uint64_t threshold = millisecondsToSamples(descriptor.hold_threshold_ms);
            if (absolute_sample - state.pressed_at_sample >= threshold) {
                state.hold_fired = true;
                handleButtonHold(descriptor.id);
            }
        }
    }

    void handleMidi(const MidiEvent& event) noexcept {
        if (event.size != 3) {
            ++diagnostics.malformed_midi_messages;
            return;
        }
        const auto status = event.bytes[0];
        const auto controller = event.bytes[1];
        const auto value = event.bytes[2];
        if (status != 0xBFU || controller > 127U || value > 127U) {
            ++diagnostics.ignored_midi_messages;
            return;
        }
        if (const auto* encoder = encoderDescriptor(controller); encoder != nullptr) {
            setEncoder(*encoder, value);
            last_ingress_sequence = event.ingress_sequence;
            return;
        }
        if (const auto* button = buttonDescriptor(controller); button != nullptr) {
            if (value != 0U && value != 127U) {
                ++diagnostics.malformed_midi_messages;
                return;
            }
            if (setButton(*button, value == 127U)) {
                last_ingress_sequence = event.ingress_sequence;
            }
            return;
        }
        ++diagnostics.ignored_midi_messages;
    }

    float sourceSample(double frequency, float noise) noexcept {
        oscillator_phase += frequency / sample_rate;
        oscillator_phase -= std::floor(oscillator_phase);
        const float sine = static_cast<float>(std::sin(2.0 * kPi * oscillator_phase));
        switch (source) {
            case SourceMode::reed:
                return std::tanh(1.7f * (sine + 0.23f * static_cast<float>(std::sin(4.0 * kPi * oscillator_phase))));
            case SourceMode::rnd:
                return 0.66f * sine + 0.34f * noise;
            case SourceMode::fold:
                return softFold(sine * 2.6f);
            case SourceMode::dust: {
                const float high_pass = noise - dust_previous * 0.92f;
                dust_previous = noise;
                return std::tanh(high_pass * 2.4f) * 0.72f;
            }
        }
        return 0.0f;
    }

    std::pair<float, float> grainBed(float body_sample, double wave_value) noexcept {
        if (!frozen) grain_buffer[grain_write] = body_sample;
        const double target_position = clampNormalized(position.current + (
            wave_target == WaveTarget::grain || wave_target == WaveTarget::all
                ? (wave_value - 0.5) * 0.22
                : 0.0
        ));
        const std::size_t base_offset = static_cast<std::size_t>(
            (0.05 + target_position * 0.82) * static_cast<double>(grain_length - 1U)
        );
        const auto& clean_parameters = fx_parameters[static_cast<std::size_t>(FxMode::clean)];
        const double grain_size = 0.08 + clampNormalized(clean_parameters[0].current) * 0.42;
        float left = 0.0f;
        float right = 0.0f;
        for (std::size_t grain = 0; grain < 6; ++grain) {
            const std::size_t spread = static_cast<std::size_t>(
                static_cast<double>(grain * grain_length) * grain_size / 6.0
            );
            const std::size_t modulation = static_cast<std::size_t>((absolute_sample / (131U + grain * 17U)) % 257U);
            const std::size_t offset = (base_offset + spread + modulation) % grain_length;
            const std::size_t read = (grain_write + grain_length - offset) % grain_length;
            const float sample = grain_buffer[read] * (0.18f - static_cast<float>(grain) * 0.012f);
            if ((grain & 1U) == 0) {
                left += sample;
                right += sample * 0.42f;
            } else {
                right += sample;
                left += sample * 0.42f;
            }
        }
        if (!frozen) grain_write = (grain_write + 1U) % grain_length;
        const float depth = static_cast<float>(clampNormalized(clean_parameters[1].current));
        return {left * depth, right * depth};
    }

    std::pair<float, float> diffusion(float left, float right) noexcept {
        const float delayed_left = diffusion_left[diffusion_left_index];
        const float delayed_right = diffusion_right[diffusion_right_index];
        diffusion_left[diffusion_left_index] = denormalZero(left + delayed_right * 0.34f);
        diffusion_right[diffusion_right_index] = denormalZero(right + delayed_left * 0.31f);
        diffusion_left_index = (diffusion_left_index + 1U) % diffusion_left.size();
        diffusion_right_index = (diffusion_right_index + 1U) % diffusion_right.size();
        return {left + delayed_left * 0.22f, right + delayed_right * 0.22f};
    }

    std::pair<float, float> applyFxMode(FxMode mode, float left, float right) noexcept {
        const auto& parameters = fx_parameters[static_cast<std::size_t>(mode)];
        const float a = static_cast<float>(clampNormalized(parameters[0].current));
        const float b = static_cast<float>(clampNormalized(parameters[1].current));
        if (mode == FxMode::filter) {
            const double cutoff = 180.0 * std::pow(80.0, static_cast<double>(a));
            const float alpha = static_cast<float>(1.0 - std::exp(-2.0 * kPi * cutoff / sample_rate));
            filter_left += alpha * (left - filter_left - filter_right * b * 0.05f);
            filter_right += alpha * (right - filter_right - filter_left * b * 0.05f);
            return {filter_left, filter_right};
        }
        if (mode == FxMode::drive) {
            const float tone_alpha = 0.02f + a * 0.36f;
            drive_tone_left += tone_alpha * (left - drive_tone_left);
            drive_tone_right += tone_alpha * (right - drive_tone_right);
            const float gain = 1.0f + b * 13.0f;
            return {std::tanh((left * 0.55f + drive_tone_left * 0.45f) * gain) / std::tanh(gain),
                    std::tanh((right * 0.55f + drive_tone_right * 0.45f) * gain) / std::tanh(gain)};
        }
        return {left, right};
    }

    std::pair<float, float> applyFx(float left, float right) noexcept {
        const auto current = applyFxMode(fx_mode, left, right);
        if (fx_mode_crossfade.remaining == 0 || previous_fx_mode == fx_mode) return current;
        const auto previous = applyFxMode(previous_fx_mode, left, right);
        const float mix = static_cast<float>(clampNormalized(fx_mode_crossfade.current));
        return {
            previous.first + (current.first - previous.first) * mix,
            previous.second + (current.second - previous.second) * mix,
        };
    }

    float dcAndCeiling(float input, float& previous_input, float& previous_output) noexcept {
        const float limited = kOutputCeiling * std::tanh(input / kOutputCeiling);
        const float dc = limited - previous_input + 0.990f * previous_output;
        previous_input = limited;
        previous_output = denormalZero(dc);
        return std::clamp(previous_output, -kOutputCeiling, kOutputCeiling);
    }

    void tickControls() noexcept {
        for (auto& stage : stage_values) stage.next();
        rate.next();
        memory.next();
        body.next();
        position.next();
        for (auto& mode : fx_parameters) {
            mode[0].next();
            mode[1].next();
        }
        fx_mode_crossfade.next();
        wake.next();
        structure.next();
        ember.next();
        output_gate.next();
        if (wake_clear_remaining > 0 && --wake_clear_remaining == 0) clearWake();
        if (panic_clear_remaining > 0 && --panic_clear_remaining == 0) clearAudioState(false);
    }

    void renderSample(float& output_left, float& output_right) noexcept {
        tickControls();
        if (panic_latched && panic_clear_remaining == 0) {
            output_left = 0.0f;
            output_right = 0.0f;
            return;
        }
        const double wave = stageWave();
        const bool pitch_target = wave_target == WaveTarget::pitch || wave_target == WaveTarget::all;
        const double pitch_control = pitch_target ? wave : 0.5;
        parent_frequency_hz = midiToFrequency(static_cast<double>(root_note) + scaleSemitone(pitch_control));
        undertow_frequency_hz = undertow_divisor == 0
            ? 0.0
            : parent_frequency_hz / static_cast<double>(undertow_divisor);
        if ((absolute_sample & 31U) == 0U) updateResonatorCoefficients();

        const float noise = signedNoise(random_state);
        const float source_value = sourceSample(parent_frequency_hz, noise);
        const double body_modulation = wave_target == WaveTarget::body || wave_target == WaveTarget::all
            ? 0.68 + wave * 0.42
            : 0.86;
        bool resonator_cleared = false;
        float body_left = 0.0f;
        float body_right = 0.0f;
        for (std::size_t index = 0; index < body_modes.size(); ++index) {
            const float mode = body_modes[index].process(
                source_value * static_cast<float>(body_modulation), resonator_cleared
            );
            if ((index & 1U) == 0) {
                body_left += mode * 0.34f;
                body_right += mode * 0.15f;
            } else {
                body_right += mode * 0.34f;
                body_left += mode * 0.15f;
            }
        }
        float undertow = 0.0f;
        if (undertow_divisor != 0) {
            undertow = undertow_voice.process(source_value, resonator_cleared) * 0.48f;
        }
        body_left += source_value * 0.11f + undertow * 0.52f;
        body_right += source_value * 0.11f + undertow * 0.48f;

        float wake_left = 0.0f;
        float wake_right = 0.0f;
        for (std::size_t index = 0; index < wake_voices.size(); ++index) {
            const float value = wake_voices[index].process(0.0f, resonator_cleared);
            if ((index & 1U) == 0) {
                wake_left += value * 0.72f;
                wake_right += value * 0.28f;
            } else {
                wake_right += value * 0.72f;
                wake_left += value * 0.28f;
            }
        }
        if (resonator_cleared) ++diagnostics.non_finite_clears;
        const auto grain = grainBed((body_left + body_right) * 0.5f, wave);
        const float wake_gain = static_cast<float>(clampNormalized(wake.current)) * 0.32f;
        const float compensation = 1.0f / (1.0f + wake_gain * 0.42f);
        auto mixed = diffusion(
            (body_left + grain.first + wake_left * wake_gain) * compensation,
            (body_right + grain.second + wake_right * wake_gain) * compensation
        );
        mixed = applyFx(mixed.first, mixed.second);
        const float gate = static_cast<float>(clampNormalized(output_gate.current));
        output_left = dcAndCeiling(mixed.first * gate, dc_x_left, dc_y_left);
        output_right = dcAndCeiling(mixed.second * gate, dc_x_right, dc_y_right);
        if (!std::isfinite(output_left) || !std::isfinite(output_right)) {
            output_left = 0.0f;
            output_right = 0.0f;
            clearAudioState(false);
            ++diagnostics.non_finite_clears;
        }
    }
};

Core::Core() : impl_(std::make_unique<Impl>()) {}
Core::~Core() = default;
Core::Core(Core&&) noexcept = default;
Core& Core::operator=(Core&&) noexcept = default;

bool Core::prepare(double sample_rate, std::uint32_t maximum_block_frames) noexcept {
    if (!std::isfinite(sample_rate) || sample_rate != kReferenceSampleRate
        || maximum_block_frames == 0 || maximum_block_frames > kMaximumBlockFrames) {
        impl_->prepared = false;
        return false;
    }
    impl_->sample_rate = sample_rate;
    impl_->maximum_block_frames = maximum_block_frames;
    impl_->ramp_samples = impl_->millisecondsToSamples(kParameterRampMs);
    impl_->grain_length = std::min<std::size_t>(
        kMaximumGrainSamples,
        static_cast<std::size_t>(std::llround(sample_rate))
    );
    impl_->prepared = true;
    impl_->fullReset();
    return true;
}

void Core::reset() noexcept {
    if (impl_->prepared) impl_->fullReset();
}

ProcessReport Core::process(
    float* output_left,
    float* output_right,
    std::uint32_t frames,
    const MidiEvent* midi_events,
    std::size_t midi_event_count,
    WakeEvent* event_output,
    std::size_t event_capacity
) noexcept {
    ProcessReport report{};
    if (!impl_->prepared || output_left == nullptr || output_right == nullptr
        || frames == 0 || frames > impl_->maximum_block_frames
        || (midi_event_count > 0 && midi_events == nullptr)) {
        ++impl_->diagnostics.unsupported_process_calls;
        return report;
    }

    const std::size_t bounded_midi_count = std::min(
        midi_event_count,
        kMaximumMidiEventsPerBlock
    );
    impl_->diagnostics.midi_events_dropped += midi_event_count - bounded_midi_count;

    std::size_t midi_index = 0;
    std::uint32_t previous_offset = 0;
    std::uint64_t previous_sequence = 0;
    bool have_previous_event = false;
    for (std::uint32_t frame = 0; frame < frames; ++frame) {
        while (midi_index < bounded_midi_count && midi_events[midi_index].sample_offset < frame) {
            ++impl_->diagnostics.malformed_midi_messages;
            ++midi_index;
        }
        while (midi_index < bounded_midi_count && midi_events[midi_index].sample_offset == frame) {
            const auto& event = midi_events[midi_index++];
            const bool ordered = !have_previous_event
                || event.sample_offset > previous_offset
                || (event.sample_offset == previous_offset && event.ingress_sequence > previous_sequence);
            if (!ordered) {
                ++impl_->diagnostics.malformed_midi_messages;
            } else {
                impl_->handleMidi(event);
                previous_offset = event.sample_offset;
                previous_sequence = event.ingress_sequence;
                have_previous_event = true;
            }
        }
        impl_->checkButtonHolds();
        impl_->renderSample(output_left[frame], output_right[frame]);

        impl_->cycle_phase += impl_->rate.current / impl_->sample_rate;
        if (impl_->cycle_phase >= 1.0) impl_->cycle_phase -= std::floor(impl_->cycle_phase);
        const auto new_stage = static_cast<std::uint8_t>(std::floor(impl_->cycle_phase * 4.0)) % 4U;
        if (new_stage != impl_->current_stage) {
            impl_->current_stage = new_stage;
            impl_->onStageTransition(event_output, event_capacity, report);
        }
        ++impl_->absolute_sample;
        ++impl_->diagnostics.processed_frames;
    }
    while (midi_index < bounded_midi_count) {
        ++impl_->diagnostics.malformed_midi_messages;
        ++midi_index;
    }
    return report;
}

bool Core::setControlNormalized(ControlId control, double normalized) noexcept {
    if (!impl_->prepared || !std::isfinite(normalized)) {
        if (impl_->prepared) ++impl_->diagnostics.non_finite_clears;
        return false;
    }
    const auto match = std::find_if(
        kLaunchControl3Encoders.begin(),
        kLaunchControl3Encoders.end(),
        [control](const auto& descriptor) { return descriptor.id == control; }
    );
    if (match == kLaunchControl3Encoders.end()) return false;
    const auto midi_value = static_cast<std::uint8_t>(std::llround(clampNormalized(normalized) * 127.0));
    impl_->setEncoder(*match, midi_value);
    return true;
}

void Core::noteDroppedMidiEvents(std::size_t count) noexcept {
    impl_->diagnostics.midi_events_dropped += count;
}

Diagnostics Core::diagnostics() const noexcept {
    return impl_->diagnostics;
}

StateSnapshot Core::snapshot() const noexcept {
    StateSnapshot result{};
    for (std::size_t index = 0; index < result.stage_values.size(); ++index) {
        result.stage_values[index] = static_cast<float>(
            clampNormalized(impl_->stage_values[index].current + impl_->mutation_offsets[index])
        );
    }
    result.ledger_energy = impl_->ledger_energy;
    result.rotor_positions = impl_->rotor_positions;
    result.absolute_sample = impl_->absolute_sample;
    result.grain_write_index = impl_->grain_write;
    result.stage_transition_index = impl_->transition_index;
    result.pulse_counter = impl_->pulse_counter;
    result.cycle_phase = impl_->cycle_phase;
    result.rate_hz = impl_->rate.current;
    const auto active_fx_mode = static_cast<std::size_t>(impl_->fx_mode);
    result.fx_a = impl_->fx_parameters[active_fx_mode][0].current;
    result.fx_b = impl_->fx_parameters[active_fx_mode][1].current;
    result.parent_frequency_hz = impl_->parent_frequency_hz;
    result.undertow_frequency_hz = impl_->undertow_divisor == 0 ? 0.0 : impl_->undertow_frequency_hz;
    result.undertow_resonator_frequency_hz = impl_->undertow_divisor == 0
        ? 0.0
        : impl_->undertow_voice.frequency_hz;
    result.root_note = impl_->root_note;
    result.undertow_divisor = impl_->undertow_divisor;
    result.pulse_divide = impl_->pulse_divide;
    result.source = impl_->source;
    result.scale = impl_->scale;
    result.fx_mode = impl_->fx_mode;
    result.wave_target = impl_->wave_target;
    result.locked = impl_->locked;
    result.frozen = impl_->frozen;
    result.fx_a_pickup_armed = impl_->fx_pickup_armed[active_fx_mode][0];
    result.fx_b_pickup_armed = impl_->fx_pickup_armed[active_fx_mode][1];
    result.bloom_armed = impl_->bloom_armed;
    result.panic_latched = impl_->panic_latched;
    return result;
}

double Core::sampleRate() const noexcept {
    return impl_->sample_rate;
}

bool Core::isPrepared() const noexcept {
    return impl_->prepared;
}

}  // namespace cinderwheel
