#include "schuss/generative_drum_machine/core.hpp"

#include "preset_data.hpp"

#include "schuss/dsp/mutable_braids_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>

namespace schuss::generative_drum_machine {
namespace {

constexpr std::uint32_t kEnvelopeOneQ31 = 0x7fffffffU;
constexpr std::uint32_t kTailReuseThresholdQ31 = kEnvelopeOneQ31 / 1000U;
constexpr std::uint32_t kEnvelopeSilenceThresholdQ31 = 4096U;
constexpr std::uint32_t kTailBridgeFrames = 48U;
constexpr std::int32_t kQ27Maximum = (1 << 27) - 1;
constexpr std::int32_t kQ27Minimum = -(1 << 27);

[[nodiscard]] std::size_t laneIndex(Lane lane) noexcept {
    return static_cast<std::size_t>(lane);
}

[[nodiscard]] std::uint16_t deterministicWord(
    std::uint32_t seed,
    std::uint32_t cycle,
    std::uint32_t source,
    std::uint32_t control_epoch,
    const char* domain,
    const char* rhythm_fingerprint) noexcept {
    std::uint32_t hash = 2166136261U;
    const auto mix_byte = [&hash](std::uint8_t value) {
        hash ^= value;
        hash *= 16777619U;
    };
    const auto mix_text = [&mix_byte](const char* text) {
        while (*text != '\0') {
            mix_byte(static_cast<std::uint8_t>(*text));
            ++text;
        }
        mix_byte(0xffU);
    };
    const auto mix_u32 = [&mix_byte](std::uint32_t value) {
        for (std::uint32_t shift = 0U; shift < 32U; shift += 8U) {
            mix_byte(static_cast<std::uint8_t>(value >> shift));
        }
    };
    mix_text("schuss.generative-drum-machine.v0");
    mix_text(domain);
    mix_text(rhythm_fingerprint);
    mix_u32(seed);
    mix_u32(cycle);
    mix_u32(control_epoch);
    mix_u32(source);
    hash ^= hash >> 16U;
    hash *= 0x7feb352dU;
    hash ^= hash >> 15U;
    hash *= 0x846ca68bU;
    hash ^= hash >> 16U;
    return static_cast<std::uint16_t>(hash >> 16U);
}

[[nodiscard]] std::uint8_t selectedVariationGroup(
    std::uint16_t enthusiasm,
    std::uint32_t seed,
    std::uint32_t cycle,
    std::uint32_t control_epoch,
    const generated::RhythmPresetDescriptor& rhythm) {
    if (enthusiasm == 0U
        || enthusiasm < rhythm.variation_minimum_enthusiasm[1]) {
        return 0U;
    }
    const auto decision = deterministicWord(
        seed, cycle, 0U, control_epoch, "enthusiasm", rhythm.fingerprint);
    if (decision > enthusiasm) {
        return 0U;
    }
    const bool second_group_eligible = enthusiasm
        >= rhythm.variation_minimum_enthusiasm[2];
    if (!second_group_eligible) {
        return 1U;
    }
    return static_cast<std::uint8_t>(
        1U + (deterministicWord(
            seed, cycle, 1U, control_epoch,
            "variation-group", rhythm.fingerprint) & 1U));
}

[[nodiscard]] const generated::RhythmPresetDescriptor& rhythmDescriptor(
    std::uint8_t index) {
    if (index >= generated::kRhythmPresets.size()) {
        throw std::invalid_argument("rhythm preset index out of range");
    }
    return generated::kRhythmPresets[index];
}

[[nodiscard]] std::int32_t signedShapeOffset(
    std::uint8_t value,
    std::int32_t negative_extent,
    std::int32_t positive_extent) noexcept {
    if (value <= 64U) {
        return -static_cast<std::int32_t>(64U - value) * negative_extent / 64;
    }
    return static_cast<std::int32_t>(value - 64U) * positive_extent / 63;
}

[[nodiscard]] std::uint32_t interpolateShapeU32(
    std::uint8_t value,
    std::uint32_t minimum,
    std::uint32_t neutral,
    std::uint32_t maximum) noexcept {
    if (value <= 64U) {
        return minimum + static_cast<std::uint32_t>(
            (static_cast<std::uint64_t>(neutral - minimum) * value + 32U) / 64U);
    }
    return neutral + static_cast<std::uint32_t>(
        (static_cast<std::uint64_t>(maximum - neutral) * (value - 64U) + 31U) / 63U);
}

[[nodiscard]] dsp::mutable_braids_v1::Model adapterModel(BraidsModel model) {
    switch (model) {
        case BraidsModel::kick:
            return dsp::mutable_braids_v1::Model::kick;
        case BraidsModel::snare:
            return dsp::mutable_braids_v1::Model::snare;
        case BraidsModel::cymbal:
            return dsp::mutable_braids_v1::Model::cymbal;
        case BraidsModel::sine_triangle:
            return dsp::mutable_braids_v1::Model::sine_triangle;
        case BraidsModel::fm:
            return dsp::mutable_braids_v1::Model::fm;
        case BraidsModel::filtered_noise:
            return dsp::mutable_braids_v1::Model::filtered_noise;
    }
    throw std::logic_error("unknown Braids model");
}

[[nodiscard]] std::int32_t clampParameter(std::int64_t value) noexcept {
    return static_cast<std::int32_t>(std::clamp<std::int64_t>(value, 0, 32767));
}

[[nodiscard]] std::uint32_t multiplyQ31(
    std::uint32_t value,
    std::uint32_t multiplier) noexcept {
    const auto product = static_cast<std::uint64_t>(value) * multiplier;
    return static_cast<std::uint32_t>((product + (std::uint64_t{1} << 30U)) >> 31U);
}

[[nodiscard]] bool sameRecipe(
    const LaneRecipe& left,
    const LaneRecipe& right) noexcept {
    return left.model == right.model
        && left.base_pitch_q7 == right.base_pitch_q7
        && left.timbre_u15 == right.timbre_u15
        && left.color_u15 == right.color_u15
        && left.pitch_env_amount_q7 == right.pitch_env_amount_q7
        && left.timbre_env_amount_s15 == right.timbre_env_amount_s15
        && left.color_env_amount_s15 == right.color_env_amount_s15
        && left.amp_decay_multiplier_q31 == right.amp_decay_multiplier_q31
        && left.transient_decay_multiplier_q31 == right.transient_decay_multiplier_q31
        && left.gain_q15 == right.gain_q15
        && left.pan_s15 == right.pan_s15
        && left.choke_group == right.choke_group
        && left.priority == right.priority;
}

template <typename Value>
[[nodiscard]] Value interpolateRecipeValue(
    Value start,
    Value target,
    std::uint32_t elapsed) noexcept {
    const auto start_wide = static_cast<std::int64_t>(start);
    const auto target_wide = static_cast<std::int64_t>(target);
    return static_cast<Value>(
        start_wide
        + (target_wide - start_wide) * elapsed
            / static_cast<std::int64_t>(kVoiceShapeSlewFrames));
}

struct Voice final {
    dsp::mutable_braids_v1::Voice oscillator{};
    bool active{};
    bool assigned{};
    Lane lane{};
    std::uint8_t priority{};
    std::uint8_t choke_group{};
    std::uint64_t onset_frame{};
    std::uint16_t velocity_u15{};
    std::uint32_t amplitude_q31{};
    std::uint32_t transient_q31{};
    std::uint32_t attack_remaining{};
    std::array<std::int16_t, 5> decimator_history{};
    std::int32_t last_left_q27{};
    std::int32_t last_right_q27{};
    std::int32_t bridge_left_q27{};
    std::int32_t bridge_right_q27{};
    std::uint32_t bridge_remaining{};

    Voice(const Voice&) = delete;
    Voice& operator=(const Voice&) = delete;

    void reconstruct(const LaneRecipe* recipe) {
        oscillator.reset();
        decimator_history.fill(0);
        last_left_q27 = 0;
        last_right_q27 = 0;
        if (recipe != nullptr) {
            oscillator.setModel(adapterModel(recipe->model));
            oscillator.setPitch(recipe->base_pitch_q7);
            oscillator.setParameters(
                static_cast<std::int16_t>(recipe->timbre_u15),
                static_cast<std::int16_t>(recipe->color_u15));
        }
    }

    void hardReset() {
        reconstruct(nullptr);
        active = false;
        assigned = false;
        lane = Lane::kick;
        priority = 0U;
        choke_group = 0U;
        onset_frame = 0U;
        velocity_u15 = 0U;
        amplitude_q31 = 0U;
        transient_q31 = 0U;
        attack_remaining = 0U;
        bridge_left_q27 = 0;
        bridge_right_q27 = 0;
        bridge_remaining = 0U;
    }

    void start(
        Lane incoming_lane,
        const LaneRecipe& recipe,
        const DrumHit& hit,
        bool preserve_core,
        bool make_bridge) {
        const auto previous_left = last_left_q27;
        const auto previous_right = last_right_q27;
        if (!preserve_core) {
            reconstruct(&recipe);
        }
        bridge_left_q27 = make_bridge ? previous_left : 0;
        bridge_right_q27 = make_bridge ? previous_right : 0;
        bridge_remaining = make_bridge ? kTailBridgeFrames : 0U;
        lane = incoming_lane;
        priority = recipe.priority;
        choke_group = recipe.choke_group;
        onset_frame = hit.absolute_frame;
        velocity_u15 = hit.velocity_u15;
        amplitude_q31 = kEnvelopeOneQ31;
        transient_q31 = kEnvelopeOneQ31;
        attack_remaining = kTailBridgeFrames;
        active = true;
        assigned = true;
        oscillator.strike();
    }

    [[nodiscard]] std::pair<std::int32_t, std::int32_t> renderFrame(
        const LaneRecipe& recipe) {
        if (!active && bridge_remaining == 0U) {
            last_left_q27 = 0;
            last_right_q27 = 0;
            return {0, 0};
        }

        std::int64_t left = 0;
        std::int64_t right = 0;
        if (active) {
            const auto pitch = static_cast<std::int64_t>(recipe.base_pitch_q7)
                + ((static_cast<std::int64_t>(recipe.pitch_env_amount_q7)
                    * transient_q31) >> 31U);
            const auto timbre = static_cast<std::int64_t>(recipe.timbre_u15)
                + ((static_cast<std::int64_t>(recipe.timbre_env_amount_s15)
                    * transient_q31) >> 31U);
            const auto color = static_cast<std::int64_t>(recipe.color_u15)
                + ((static_cast<std::int64_t>(recipe.color_env_amount_s15)
                    * transient_q31) >> 31U);
            oscillator.setPitch(static_cast<std::int16_t>(
                std::clamp<std::int64_t>(pitch, 0, 16383)));
            oscillator.setParameters(
                static_cast<std::int16_t>(clampParameter(timbre)),
                static_cast<std::int16_t>(clampParameter(color)));

            std::array<std::uint8_t, 2> sync{{0U, 0U}};
            std::array<std::int16_t, 2> core_samples{{0, 0}};
            oscillator.render(sync.data(), core_samples.data(), core_samples.size());
            for (const auto sample : core_samples) {
                for (std::size_t index = decimator_history.size() - 1U;
                     index > 0U;
                     --index) {
                    decimator_history[index] = decimator_history[index - 1U];
                }
                decimator_history[0] = sample;
            }
            const std::int64_t filtered =
                static_cast<std::int64_t>(decimator_history[0]) * 2048
                + static_cast<std::int64_t>(decimator_history[1]) * 8192
                + static_cast<std::int64_t>(decimator_history[2]) * 12288
                + static_cast<std::int64_t>(decimator_history[3]) * 8192
                + static_cast<std::int64_t>(decimator_history[4]) * 2048;
            std::int64_t mono_q27 = (filtered >> 15U) << 12U;
            mono_q27 = (mono_q27 * amplitude_q31) >> 31U;
            mono_q27 = (mono_q27 * velocity_u15) >> 15U;
            mono_q27 = (mono_q27 * recipe.gain_q15) >> 15U;
            if (attack_remaining > 0U) {
                const auto attack_gain = static_cast<std::int64_t>(
                    (kTailBridgeFrames - attack_remaining) * 32767U
                    / kTailBridgeFrames);
                mono_q27 = (mono_q27 * attack_gain) >> 15U;
                --attack_remaining;
            }
            const std::int32_t left_gain = recipe.pan_s15 > 0
                ? 32767 - recipe.pan_s15
                : 32767;
            const std::int32_t right_gain = recipe.pan_s15 < 0
                ? 32767 + recipe.pan_s15
                : 32767;
            left = (mono_q27 * left_gain) >> 15U;
            right = (mono_q27 * right_gain) >> 15U;

            amplitude_q31 = multiplyQ31(
                amplitude_q31, recipe.amp_decay_multiplier_q31);
            transient_q31 = multiplyQ31(
                transient_q31, recipe.transient_decay_multiplier_q31);
            if (amplitude_q31 <= kEnvelopeSilenceThresholdQ31) {
                amplitude_q31 = 0U;
                transient_q31 = 0U;
                active = false;
            }
        }

        if (bridge_remaining > 0U) {
            left += static_cast<std::int64_t>(bridge_left_q27)
                * bridge_remaining / kTailBridgeFrames;
            right += static_cast<std::int64_t>(bridge_right_q27)
                * bridge_remaining / kTailBridgeFrames;
            --bridge_remaining;
        }
        last_left_q27 = static_cast<std::int32_t>(std::clamp<std::int64_t>(
            left, std::numeric_limits<std::int32_t>::min(),
            std::numeric_limits<std::int32_t>::max()));
        last_right_q27 = static_cast<std::int32_t>(std::clamp<std::int64_t>(
            right, std::numeric_limits<std::int32_t>::min(),
            std::numeric_limits<std::int32_t>::max()));
        return {last_left_q27, last_right_q27};
    }
};

struct Engine final {
    std::array<Voice, kPhysicalVoiceCount> voices{};
    std::array<LaneRecipe, kLogicalLaneCount> recipes{};
    std::array<LaneRecipe, kLogicalLaneCount> recipe_starts{};
    std::array<LaneRecipe, kLogicalLaneCount> recipe_targets{};
    std::array<std::uint32_t, kLogicalLaneCount> recipe_slew_remaining{};
    Metrics metrics{};

    explicit Engine(const Controls& controls)
        : recipes(resolvedLaneRecipes(controls)),
          recipe_starts(recipes),
          recipe_targets(recipes) {}

    void reset(const Controls& controls) {
        for (auto& voice : voices) {
            voice.hardReset();
        }
        recipes = resolvedLaneRecipes(controls);
        recipe_starts = recipes;
        recipe_targets = recipes;
        recipe_slew_remaining.fill(0U);
        metrics = Metrics{};
    }

    void setRecipeTargets(const Controls& controls) {
        const auto next = resolvedLaneRecipes(controls);
        for (std::size_t lane = 0; lane < kLogicalLaneCount; ++lane) {
            if (sameRecipe(next[lane], recipe_targets[lane])) {
                continue;
            }
            recipe_starts[lane] = recipes[lane];
            recipe_targets[lane] = next[lane];
            recipe_slew_remaining[lane] = kVoiceShapeSlewFrames;
        }
    }

    void advanceRecipeSlews() noexcept {
        for (std::size_t lane = 0; lane < kLogicalLaneCount; ++lane) {
            auto& remaining = recipe_slew_remaining[lane];
            if (remaining == 0U) {
                continue;
            }
            const auto elapsed = kVoiceShapeSlewFrames - remaining + 1U;
            const auto& start = recipe_starts[lane];
            const auto& target = recipe_targets[lane];
            auto& current = recipes[lane];
            current = target;
            current.base_pitch_q7 = interpolateRecipeValue(
                start.base_pitch_q7, target.base_pitch_q7, elapsed);
            current.timbre_u15 = interpolateRecipeValue(
                start.timbre_u15, target.timbre_u15, elapsed);
            current.color_u15 = interpolateRecipeValue(
                start.color_u15, target.color_u15, elapsed);
            current.pitch_env_amount_q7 = interpolateRecipeValue(
                start.pitch_env_amount_q7, target.pitch_env_amount_q7, elapsed);
            current.amp_decay_multiplier_q31 = interpolateRecipeValue(
                start.amp_decay_multiplier_q31,
                target.amp_decay_multiplier_q31,
                elapsed);
            current.gain_q15 = interpolateRecipeValue(
                start.gain_q15, target.gain_q15, elapsed);
            --remaining;
            if (remaining == 0U) {
                current = target;
            }
        }
    }

    [[nodiscard]] AllocationDecision allocate(const DrumHit& hit) {
        const auto& incoming = recipes[laneIndex(hit.lane)];
        std::size_t selected = voices.size();
        AllocationAction action = AllocationAction::drop;

        if (incoming.choke_group != 0U) {
            for (std::size_t index = 0; index < voices.size(); ++index) {
                if (voices[index].active
                    && voices[index].choke_group == incoming.choke_group) {
                    selected = index;
                    action = AllocationAction::choke;
                    break;
                }
            }
        }
        if (selected == voices.size()) {
            for (std::size_t index = 0; index < voices.size(); ++index) {
                if (!voices[index].active) {
                    selected = index;
                    action = AllocationAction::idle;
                    break;
                }
            }
        }
        if (selected == voices.size()) {
            for (std::size_t index = 0; index < voices.size(); ++index) {
                if (voices[index].amplitude_q31 > kTailReuseThresholdQ31) {
                    continue;
                }
                if (selected == voices.size()
                    || std::tie(voices[index].amplitude_q31,
                                voices[index].onset_frame, index)
                        < std::tie(voices[selected].amplitude_q31,
                                   voices[selected].onset_frame, selected)) {
                    selected = index;
                    action = AllocationAction::tail_reuse;
                }
            }
        }
        if (selected == voices.size()) {
            for (std::size_t index = 0; index < voices.size(); ++index) {
                if (voices[index].priority > incoming.priority) {
                    continue;
                }
                if (selected == voices.size()
                    || std::tie(voices[index].priority,
                                voices[index].amplitude_q31,
                                voices[index].onset_frame, index)
                        < std::tie(voices[selected].priority,
                                   voices[selected].amplitude_q31,
                                   voices[selected].onset_frame, selected)) {
                    selected = index;
                    action = AllocationAction::steal;
                }
            }
        }

        AllocationDecision decision{};
        decision.absolute_frame = hit.absolute_frame;
        decision.source_ordinal = hit.source_ordinal;
        decision.lane = hit.lane;
        decision.action = action;
        if (selected == voices.size()) {
            ++metrics.dropped_hit_count;
            return decision;
        }

        auto& voice = voices[selected];
        decision.voice_index = static_cast<std::int8_t>(selected);
        decision.victim_lane = voice.assigned
            ? static_cast<std::int8_t>(laneIndex(voice.lane))
            : static_cast<std::int8_t>(-1);
        const bool preserve_core = voice.assigned && voice.lane == hit.lane;
        const bool make_bridge = voice.active;
        if (action == AllocationAction::steal) {
            ++metrics.stolen_voice_count;
        } else if (action == AllocationAction::choke) {
            ++metrics.choked_voice_count;
        }
        voice.start(hit.lane, incoming, hit, preserve_core, make_bridge);
        return decision;
    }

    [[nodiscard]] std::pair<std::int32_t, std::int32_t> renderFrame() {
        advanceRecipeSlews();
        std::int64_t left = 0;
        std::int64_t right = 0;
        for (auto& voice : voices) {
            if (!voice.assigned) {
                continue;
            }
            const auto sample = voice.renderFrame(
                recipes[laneIndex(voice.lane)]);
            left += sample.first;
            right += sample.second;
        }
        if (left > kQ27Maximum || left < kQ27Minimum
            || right > kQ27Maximum || right < kQ27Minimum) {
            ++metrics.clipped_sample_count;
        }
        const auto left_q27 = static_cast<std::int32_t>(
            std::clamp<std::int64_t>(left, kQ27Minimum, kQ27Maximum));
        const auto right_q27 = static_cast<std::int32_t>(
            std::clamp<std::int64_t>(right, kQ27Minimum, kQ27Maximum));
        metrics.peak_absolute_q27 = std::max(
            metrics.peak_absolute_q27,
            std::max(
                static_cast<std::int32_t>(std::abs(static_cast<std::int64_t>(left_q27))),
                static_cast<std::int32_t>(std::abs(static_cast<std::int64_t>(right_q27)))));
        metrics.sum_left_q27 += left_q27;
        metrics.sum_right_q27 += right_q27;
        ++metrics.frame_count;
        return {left_q27, right_q27};
    }
};

}  // namespace

struct StreamingEngine::Impl final {
    static constexpr std::size_t kMaximumEventsPerRhythm = 256U;
    static constexpr std::uint64_t kQuarterQ32 = std::uint64_t{1} << 32U;
    static constexpr std::uint64_t kTempoPhaseDenominator =
        static_cast<std::uint64_t>(60000U) * kSampleRateHz;

    std::uint32_t seed{};
    Engine engine{Controls{}};
    Controls last_controls{};
    bool initialized{};
    std::uint8_t rhythm_index{};
    std::uint32_t cycle_index{};
    std::uint32_t control_epoch{};
    std::uint64_t cycle_phase_q32{};
    std::uint64_t tempo_phase_remainder{};
    std::uint64_t absolute_frame{};
    std::array<bool, kMaximumEventsPerRhythm> cycle_fired{};
    std::uint64_t last_fill_request_sequence{};
    bool fill_active{};
    std::uint64_t fill_phase_q32{};
    std::array<bool, kMaximumEventsPerRhythm> fill_fired{};

    explicit Impl(std::uint32_t initial_seed)
        : seed(initial_seed) {
        dsp::mutable_braids_v1::seedRandom(seed);
        resetFiredForCycle();
        resetFiredForFill();
    }

    [[nodiscard]] static bool validControls(const Controls& controls) noexcept {
        if (controls.tempo_milli_bpm < 30000U
            || controls.tempo_milli_bpm > 240000U
            || controls.swing_u15 > 32767U
            || controls.rhythm_preset >= kRhythmPresetCount
            || controls.selected_voice_lane >= kLogicalLaneCount) {
            return false;
        }
        for (const auto& shape : controls.voice_shapes) {
            if (shape.tune_u7 > 127U
                || shape.timbre_u7 > 127U
                || shape.color_u7 > 127U
                || shape.decay_u7 > 127U
                || shape.pitch_env_u7 > 127U
                || shape.level_u7 > 127U) {
                return false;
            }
        }
        return true;
    }

    [[nodiscard]] static std::uint64_t rationalQ32(Rational position) noexcept {
        return (static_cast<std::uint64_t>(position.numerator) * kQuarterQ32
                    + position.denominator / 2U)
            / position.denominator;
    }

    [[nodiscard]] static std::uint64_t barLengthQ32(
        const generated::RhythmPresetDescriptor& rhythm) noexcept {
        return static_cast<std::uint64_t>(rhythm.meter_numerator)
            * 4U * kQuarterQ32 / rhythm.note_value_denominator;
    }

    [[nodiscard]] static bool swingEligible(Rational position) noexcept {
        const auto doubled = static_cast<std::uint64_t>(position.numerator) * 2U;
        return doubled % position.denominator == 0U
            && ((doubled / position.denominator) & 1U) != 0U;
    }

    [[nodiscard]] static std::uint64_t swingOffsetQ32(
        Rational position,
        std::uint16_t swing_u15) noexcept {
        if (swing_u15 == 0U || !swingEligible(position)) {
            return 0U;
        }
        return (kQuarterQ32 * swing_u15 + (32767U * 6U) / 2U)
            / (32767U * 6U);
    }

    [[nodiscard]] static std::uint64_t eventPositionQ32(
        const PatternEvent& event,
        const generated::RhythmPresetDescriptor& rhythm,
        std::uint16_t swing_u15,
        bool include_bar) noexcept {
        const auto bar = include_bar
            ? static_cast<std::uint64_t>(event.bar) * barLengthQ32(rhythm)
            : 0U;
        return bar + rationalQ32(event.position_quarters)
            + swingOffsetQ32(event.position_quarters, swing_u15);
    }

    [[nodiscard]] const generated::RhythmPresetDescriptor& rhythm() const noexcept {
        return generated::kRhythmPresets[rhythm_index];
    }

    [[nodiscard]] std::size_t eventCount() const noexcept {
        return static_cast<std::size_t>(rhythm().event_count);
    }

    [[nodiscard]] const PatternEvent& event(std::size_t local_index) const noexcept {
        return generated::kPatternEvents[
            static_cast<std::size_t>(rhythm().event_offset) + local_index];
    }

    void resetFiredForCycle() noexcept {
        cycle_fired.fill(true);
        if (rhythm_index >= generated::kRhythmPresets.size()
            || eventCount() > cycle_fired.size()) {
            return;
        }
        for (std::size_t index = 0U; index < eventCount(); ++index) {
            cycle_fired[index] = event(index).variation_group == 100U;
        }
    }

    void resetFiredForFill() noexcept {
        fill_fired.fill(true);
        if (rhythm_index >= generated::kRhythmPresets.size()
            || eventCount() > fill_fired.size()) {
            return;
        }
        for (std::size_t index = 0U; index < eventCount(); ++index) {
            fill_fired[index] = event(index).variation_group != 100U;
        }
    }

    void markPastEvents(std::uint16_t swing_u15) noexcept {
        for (std::size_t index = 0U; index < eventCount(); ++index) {
            if (!cycle_fired[index]
                && eventPositionQ32(event(index), rhythm(), swing_u15, true)
                    < cycle_phase_q32) {
                cycle_fired[index] = true;
            }
        }
    }

    [[nodiscard]] static bool generatorControlsChanged(
        const Controls& left,
        const Controls& right) noexcept {
        return left.complexity != right.complexity
            || left.enthusiasm != right.enthusiasm
            || left.tempo_milli_bpm != right.tempo_milli_bpm
            || left.swing_u15 != right.swing_u15
            || left.rhythm_preset != right.rhythm_preset;
    }

    [[nodiscard]] bool includeEvent(
        const PatternEvent& candidate,
        const Controls& controls,
        std::uint8_t selected_group) const noexcept {
        const auto lane = laneIndex(candidate.lane);
        if (candidate.variation_group == 0U) {
            return candidate.complexity_threshold <= controls.complexity[lane];
        }
        return candidate.variation_group == selected_group
            && candidate.complexity_threshold <= controls.complexity[lane];
    }

    void restartRhythm(std::uint8_t next_rhythm) noexcept {
        rhythm_index = next_rhythm;
        cycle_index = 0U;
        cycle_phase_q32 = 0U;
        tempo_phase_remainder = 0U;
        fill_active = false;
        fill_phase_q32 = 0U;
        resetFiredForCycle();
        resetFiredForFill();
    }

    void startFill() noexcept {
        fill_active = true;
        fill_phase_q32 = 0U;
        resetFiredForFill();
    }

    void reset(std::uint32_t next_seed) noexcept {
        seed = next_seed;
        Controls defaults{};
        engine.reset(defaults);
        last_controls = defaults;
        initialized = false;
        rhythm_index = 0U;
        cycle_index = 0U;
        control_epoch = 0U;
        cycle_phase_q32 = 0U;
        tempo_phase_remainder = 0U;
        absolute_frame = 0U;
        last_fill_request_sequence = 0U;
        fill_active = false;
        fill_phase_q32 = 0U;
        resetFiredForCycle();
        resetFiredForFill();
        dsp::mutable_braids_v1::seedRandom(seed);
    }

    [[nodiscard]] bool process(
        const Controls& controls,
        std::uint64_t fill_request_sequence,
        std::int32_t* left_q27,
        std::int32_t* right_q27,
        std::size_t frame_count,
        StreamingProcessReport* report) noexcept {
        if (left_q27 == nullptr || right_q27 == nullptr
            || frame_count > kMaximumStreamingBlockFrames
            || !validControls(controls)) {
            if (left_q27 != nullptr && right_q27 != nullptr
                && frame_count <= kMaximumStreamingBlockFrames) {
                std::fill_n(left_q27, frame_count, 0);
                std::fill_n(right_q27, frame_count, 0);
            }
            if (report != nullptr) {
                *report = StreamingProcessReport{};
            }
            return false;
        }

        StreamingProcessReport local_report{};
        local_report.absolute_frame_start = absolute_frame;
        if (!initialized) {
            rhythm_index = controls.rhythm_preset;
            restartRhythm(rhythm_index);
            engine.setRecipeTargets(controls);
            last_controls = controls;
            initialized = true;
        } else {
            if (generatorControlsChanged(last_controls, controls)) {
                ++control_epoch;
            }
            if (controls.rhythm_preset != rhythm_index) {
                restartRhythm(controls.rhythm_preset);
            }
            engine.setRecipeTargets(controls);
            last_controls = controls;
        }
        if (eventCount() > kMaximumEventsPerRhythm) {
            std::fill_n(left_q27, frame_count, 0);
            std::fill_n(right_q27, frame_count, 0);
            local_report.diagnostic_overflow_count = 1U;
            if (report != nullptr) {
                *report = local_report;
            }
            return false;
        }
        markPastEvents(controls.swing_u15);
        if (fill_request_sequence != last_fill_request_sequence) {
            last_fill_request_sequence = fill_request_sequence;
            startFill();
        }

        const auto selected_group = selectedVariationGroup(
            controls.enthusiasm,
            seed,
            cycle_index,
            control_epoch,
            rhythm());
        for (std::size_t frame = 0U; frame < frame_count; ++frame) {
            std::array<const PatternEvent*, kMaximumStreamingEventsPerBlock> due{};
            std::size_t due_count = 0U;
            for (std::size_t index = 0U; index < eventCount(); ++index) {
                if (cycle_fired[index]) {
                    continue;
                }
                const auto& candidate = event(index);
                if (eventPositionQ32(
                        candidate, rhythm(), controls.swing_u15, true)
                    > cycle_phase_q32) {
                    continue;
                }
                cycle_fired[index] = true;
                if (!includeEvent(candidate, controls, selected_group)) {
                    continue;
                }
                if (due_count < due.size()) {
                    due[due_count++] = &candidate;
                } else {
                    ++local_report.diagnostic_overflow_count;
                }
            }
            if (fill_active) {
                for (std::size_t index = 0U; index < eventCount(); ++index) {
                    if (fill_fired[index]) {
                        continue;
                    }
                    const auto& candidate = event(index);
                    if (eventPositionQ32(
                            candidate, rhythm(), controls.swing_u15, false)
                        > fill_phase_q32) {
                        continue;
                    }
                    fill_fired[index] = true;
                    if (due_count < due.size()) {
                        due[due_count++] = &candidate;
                    } else {
                        ++local_report.diagnostic_overflow_count;
                    }
                }
            }
            std::sort(due.begin(), due.begin() + static_cast<std::ptrdiff_t>(due_count),
                [](const PatternEvent* left, const PatternEvent* right) {
                    const auto& left_recipe = generated::kLaneRecipes[laneIndex(left->lane)];
                    const auto& right_recipe = generated::kLaneRecipes[laneIndex(right->lane)];
                    return std::tuple{
                               static_cast<std::uint8_t>(255U - left_recipe.priority),
                               laneIndex(left->lane),
                               left->source_ordinal}
                        < std::tuple{
                               static_cast<std::uint8_t>(255U - right_recipe.priority),
                               laneIndex(right->lane),
                               right->source_ordinal};
                });
            for (std::size_t index = 0U; index < due_count; ++index) {
                const auto& candidate = *due[index];
                const DrumHit hit{
                    absolute_frame,
                    candidate.lane,
                    candidate.velocity_u15,
                    candidate.articulation,
                    candidate.source_ordinal,
                    cycle_index,
                    candidate.variation_group,
                };
                const auto allocation = engine.allocate(hit);
                if (local_report.hit_count < local_report.hits.size()) {
                    local_report.hits[local_report.hit_count++] = hit;
                    local_report.allocations[local_report.allocation_count++] = allocation;
                } else {
                    ++local_report.diagnostic_overflow_count;
                }
            }

            const auto sample = engine.renderFrame();
            left_q27[frame] = sample.first;
            right_q27[frame] = sample.second;
            ++absolute_frame;

            const auto phase_numerator =
                static_cast<std::uint64_t>(controls.tempo_milli_bpm) * kQuarterQ32
                + tempo_phase_remainder;
            const auto phase_increment = phase_numerator / kTempoPhaseDenominator;
            tempo_phase_remainder = phase_numerator % kTempoPhaseDenominator;
            cycle_phase_q32 += phase_increment;
            if (fill_active) {
                fill_phase_q32 += phase_increment;
                if (fill_phase_q32 >= barLengthQ32(rhythm())) {
                    fill_active = false;
                }
            }
            const auto cycle_length = barLengthQ32(rhythm()) * rhythm().phrase_bars;
            if (cycle_phase_q32 >= cycle_length) {
                cycle_phase_q32 -= cycle_length;
                ++cycle_index;
                resetFiredForCycle();
            }
        }
        local_report.absolute_frame_end = absolute_frame;
        local_report.cycle_index = cycle_index;
        const auto cycle_length = barLengthQ32(rhythm()) * rhythm().phrase_bars;
        local_report.cycle_progress_u15 = cycle_length == 0U
            ? 0U
            : static_cast<std::uint16_t>(std::min<std::uint64_t>(
                  32767U,
                  (cycle_phase_q32 * 32767U + cycle_length / 2U)
                      / cycle_length));
        if (report != nullptr) {
            *report = local_report;
        }
        return local_report.diagnostic_overflow_count == 0U;
    }
};

StreamingEngine::StreamingEngine(std::uint32_t seed)
    : impl_(std::make_unique<Impl>(seed)) {}

StreamingEngine::~StreamingEngine() = default;
StreamingEngine::StreamingEngine(StreamingEngine&&) noexcept = default;
StreamingEngine& StreamingEngine::operator=(StreamingEngine&&) noexcept = default;

void StreamingEngine::reset(std::uint32_t seed) noexcept {
    impl_->reset(seed);
}

bool StreamingEngine::process(
    const Controls& controls,
    std::uint64_t fill_request_sequence,
    std::int32_t* left_q27,
    std::int32_t* right_q27,
    std::size_t frame_count,
    StreamingProcessReport* report) noexcept {
    return impl_->process(
        controls,
        fill_request_sequence,
        left_q27,
        right_q27,
        frame_count,
        report);
}

std::uint64_t StreamingEngine::absoluteFrame() const noexcept {
    return impl_->absolute_frame;
}

std::uint64_t rationalPositionToFrame(
    std::uint32_t phrase_index,
    std::uint8_t bar,
    Rational position_quarters,
    std::uint32_t tempo_milli_bpm,
    std::uint16_t swing_u15) {
    return rhythmPositionToFrame(
        0U, phrase_index, bar, position_quarters, tempo_milli_bpm, swing_u15);
}

std::uint64_t rhythmPositionToFrame(
    std::uint8_t rhythm_preset,
    std::uint32_t phrase_index,
    std::uint8_t bar,
    Rational position_quarters,
    std::uint32_t tempo_milli_bpm,
    std::uint16_t swing_u15) {
    const auto& rhythm = rhythmDescriptor(rhythm_preset);
    if (position_quarters.denominator == 0U
        || position_quarters.denominator > 64U
        || std::gcd(position_quarters.numerator, position_quarters.denominator) != 1U
        || bar >= rhythm.phrase_bars
        || tempo_milli_bpm < 30000U
        || tempo_milli_bpm > 240000U
        || swing_u15 > 32767U) {
        throw std::invalid_argument("invalid rational timeline input");
    }
    const std::uint64_t bar_quarter_numerator =
        static_cast<std::uint64_t>(rhythm.meter_numerator) * 4U;
    const std::uint64_t bar_quarter_denominator = rhythm.note_value_denominator;
    if (static_cast<std::uint64_t>(position_quarters.numerator)
            * bar_quarter_denominator
        >= bar_quarter_numerator * position_quarters.denominator) {
        throw std::invalid_argument("rational position falls outside selected meter");
    }
    const std::uint64_t complete_bars =
        static_cast<std::uint64_t>(phrase_index) * rhythm.phrase_bars + bar;
    const std::uint64_t total_denominator =
        bar_quarter_denominator * position_quarters.denominator;
    const std::uint64_t total_numerator =
        complete_bars * bar_quarter_numerator * position_quarters.denominator
        + static_cast<std::uint64_t>(position_quarters.numerator)
            * bar_quarter_denominator;
    const std::uint64_t numerator = static_cast<std::uint64_t>(kSampleRateHz)
        * 60000U * total_numerator;
    const std::uint64_t denominator = static_cast<std::uint64_t>(tempo_milli_bpm)
        * total_denominator;
    std::uint64_t frame = (numerator + denominator / 2U) / denominator;

    const std::uint64_t doubled =
        static_cast<std::uint64_t>(position_quarters.numerator) * 2U;
    if (swing_u15 != 0U
        && doubled % position_quarters.denominator == 0U
        && ((doubled / position_quarters.denominator) & 1U) != 0U) {
        const std::uint64_t swing_numerator =
            static_cast<std::uint64_t>(kSampleRateHz) * 60000U * swing_u15;
        const std::uint64_t swing_denominator =
            static_cast<std::uint64_t>(tempo_milli_bpm) * 32767U * 6U;
        frame += (swing_numerator + swing_denominator / 2U) / swing_denominator;
    }
    return frame;
}

std::uint64_t phraseFrameCount(
    std::uint8_t rhythm_preset,
    std::uint32_t tempo_milli_bpm) {
    const auto& rhythm = rhythmDescriptor(rhythm_preset);
    if (tempo_milli_bpm < 30000U || tempo_milli_bpm > 240000U) {
        throw std::invalid_argument("tempo out of range");
    }
    const std::uint64_t quarter_numerator =
        static_cast<std::uint64_t>(rhythm.phrase_bars)
        * rhythm.meter_numerator * 4U;
    const std::uint64_t numerator = static_cast<std::uint64_t>(kSampleRateHz)
        * 60000U * quarter_numerator;
    const std::uint64_t denominator = static_cast<std::uint64_t>(tempo_milli_bpm)
        * rhythm.note_value_denominator;
    return (numerator + denominator / 2U) / denominator;
}

std::vector<DrumHit> generateHits(const RenderRequest& request) {
    if (request.phrase_count == 0U || request.phrase_count > 1024U) {
        throw std::invalid_argument("phrase count out of range");
    }
    if (request.outer_block_frames == 0U || request.outer_block_frames > 4096U) {
        throw std::invalid_argument("outer block size out of range");
    }
    if (request.controls.selected_voice_lane >= kLogicalLaneCount) {
        throw std::invalid_argument("selected voice lane out of range");
    }
    std::vector<DrumHit> hits;
    if (request.mode == GeneratorMode::allocator_stress) {
        for (std::size_t lane = 0; lane < kLogicalLaneCount; ++lane) {
            hits.push_back(DrumHit{
                0U, static_cast<Lane>(lane), 28000U, 0U,
                static_cast<std::uint32_t>(1000U + lane), 0U, 0U});
        }
        hits.push_back(DrumHit{240U, Lane::hat, 26000U, 1U, 1010U, 0U, 0U});
        hits.push_back(DrumHit{480U, Lane::hat, 26000U, 0U, 1011U, 0U, 0U});
    } else {
        const auto& rhythm = rhythmDescriptor(request.controls.rhythm_preset);
        const auto event_begin = static_cast<std::size_t>(rhythm.event_offset);
        const auto event_end = event_begin + static_cast<std::size_t>(rhythm.event_count);
        if (event_end > generated::kPatternEvents.size()) {
            throw std::logic_error("rhythm event slice out of range");
        }
        for (std::uint32_t local_phrase = 0;
             local_phrase < request.phrase_count;
             ++local_phrase) {
            const auto phrase = request.phrase_index_offset + local_phrase;
            const auto selected_group = selectedVariationGroup(
                request.controls.enthusiasm,
                request.seed,
                phrase,
                0U,
                rhythm);
            for (std::size_t event_index = event_begin;
                 event_index < event_end;
                 ++event_index) {
                const auto& event = generated::kPatternEvents[event_index];
                const auto lane = laneIndex(event.lane);
                bool include = false;
                if (request.mode == GeneratorMode::independent_probability_comparator) {
                    include = event.variation_group == 0U
                        && deterministicWord(
                               request.seed, phrase, event.source_ordinal, 0U,
                               "independent-hit", rhythm.fingerprint)
                            <= request.controls.complexity[lane];
                } else if (event.variation_group == 0U) {
                    include = event.complexity_threshold
                        <= request.controls.complexity[lane];
                } else if (event.variation_group == 100U) {
                    include = request.fill_phrase
                        == static_cast<std::int32_t>(local_phrase);
                } else {
                    include = event.variation_group == selected_group
                        && event.complexity_threshold
                            <= request.controls.complexity[lane];
                }
                if (!include) {
                    continue;
                }
                hits.push_back(DrumHit{
                    rhythmPositionToFrame(
                        request.controls.rhythm_preset,
                        local_phrase, event.bar, event.position_quarters,
                        request.controls.tempo_milli_bpm,
                        request.controls.swing_u15),
                    event.lane,
                    event.velocity_u15,
                    event.articulation,
                    event.source_ordinal,
                    phrase,
                    event.variation_group,
                });
            }
        }
    }
    std::sort(hits.begin(), hits.end(), [](const DrumHit& left, const DrumHit& right) {
        const auto& left_recipe = generated::kLaneRecipes[laneIndex(left.lane)];
        const auto& right_recipe = generated::kLaneRecipes[laneIndex(right.lane)];
        return std::tuple{
                   left.absolute_frame,
                   static_cast<std::uint8_t>(255U - left_recipe.priority),
                   laneIndex(left.lane),
                   left.source_ordinal}
            < std::tuple{
                   right.absolute_frame,
                   static_cast<std::uint8_t>(255U - right_recipe.priority),
                   laneIndex(right.lane),
                   right.source_ordinal};
    });
    return hits;
}

RenderResult render(const RenderRequest& request) {
    RenderResult result{};
    result.hits = generateHits(request);
    dsp::mutable_braids_v1::seedRandom(request.seed);
    Engine engine{request.controls};
    result.allocations.reserve(result.hits.size());
    const std::uint64_t total_frames = request.mode == GeneratorMode::allocator_stress
        ? kSampleRateHz
        : rhythmPositionToFrame(
              request.controls.rhythm_preset,
              request.phrase_count, 0U, Rational{0U, 1U},
              request.controls.tempo_milli_bpm, request.controls.swing_u15)
            + kSampleRateHz;
    if (total_frames > 100000000U) {
        throw std::invalid_argument("render duration out of range");
    }
    result.left_q27.resize(static_cast<std::size_t>(total_frames));
    result.right_q27.resize(static_cast<std::size_t>(total_frames));
    std::size_t event_index = 0U;
    for (std::uint64_t block_start = 0U; block_start < total_frames;
         block_start += request.outer_block_frames) {
        const auto block_end = std::min<std::uint64_t>(
            total_frames, block_start + request.outer_block_frames);
        for (std::uint64_t frame = block_start; frame < block_end; ++frame) {
            while (event_index < result.hits.size()
                   && result.hits[event_index].absolute_frame == frame) {
                result.allocations.push_back(
                    engine.allocate(result.hits[event_index]));
                ++event_index;
            }
            const auto sample = engine.renderFrame();
            result.left_q27[static_cast<std::size_t>(frame)] = sample.first;
            result.right_q27[static_cast<std::size_t>(frame)] = sample.second;
        }
    }
    if (event_index != result.hits.size()) {
        throw std::logic_error("event fell outside rendered timeline");
    }
    result.metrics = engine.metrics;
    return result;
}

const char* laneName(Lane lane) noexcept {
    constexpr std::array<const char*, kLogicalLaneCount> names{{
        "kick", "snare", "hat", "percussion_1", "percussion_2", "percussion_3"}};
    const auto index = laneIndex(lane);
    return index < names.size() ? names[index] : "invalid";
}

const char* allocationActionName(AllocationAction action) noexcept {
    switch (action) {
        case AllocationAction::idle:
            return "idle";
        case AllocationAction::choke:
            return "choke";
        case AllocationAction::tail_reuse:
            return "tail-reuse";
        case AllocationAction::steal:
            return "steal";
        case AllocationAction::retrigger:
            return "retrigger";
        case AllocationAction::drop:
            return "drop";
    }
    return "invalid";
}

const std::array<LaneRecipe, kLogicalLaneCount>& laneRecipes() noexcept {
    return generated::kLaneRecipes;
}

std::array<LaneRecipe, kLogicalLaneCount> resolvedLaneRecipes(
    const Controls& controls) {
    std::array<LaneRecipe, kLogicalLaneCount> recipes = generated::kLaneRecipes;
    for (std::size_t lane = 0; lane < recipes.size(); ++lane) {
        const auto& shape = controls.voice_shapes[lane];
        const std::array<std::uint8_t, 6> values{{
            shape.tune_u7,
            shape.timbre_u7,
            shape.color_u7,
            shape.decay_u7,
            shape.pitch_env_u7,
            shape.level_u7,
        }};
        if (std::any_of(values.begin(), values.end(), [](std::uint8_t value) {
                return value > 127U;
            })) {
            throw std::invalid_argument("voice shape value out of U7 range");
        }
        auto& recipe = recipes[lane];
        const auto& base = generated::kLaneRecipes[lane];
        recipe.base_pitch_q7 = static_cast<std::int16_t>(std::clamp<std::int32_t>(
            static_cast<std::int32_t>(base.base_pitch_q7)
                + signedShapeOffset(shape.tune_u7, 3072, 3072),
            0,
            16383));
        recipe.timbre_u15 = static_cast<std::uint16_t>(std::clamp<std::int32_t>(
            static_cast<std::int32_t>(base.timbre_u15)
                + signedShapeOffset(shape.timbre_u7, 16384, 16383),
            0,
            32767));
        recipe.color_u15 = static_cast<std::uint16_t>(std::clamp<std::int32_t>(
            static_cast<std::int32_t>(base.color_u15)
                + signedShapeOffset(shape.color_u7, 16384, 16383),
            0,
            32767));
        recipe.amp_decay_multiplier_q31 = interpolateShapeU32(
            shape.decay_u7,
            generated::kFastAmpDecayMultipliers[lane],
            base.amp_decay_multiplier_q31,
            generated::kSlowAmpDecayMultipliers[lane]);
        recipe.pitch_env_amount_q7 = static_cast<std::int16_t>(
            std::clamp<std::int32_t>(
                static_cast<std::int32_t>(base.pitch_env_amount_q7)
                    + signedShapeOffset(shape.pitch_env_u7, 2048, 2048),
                -16384,
                16383));
        const auto gain_scale_q15 = interpolateShapeU32(
            shape.level_u7, 0U, 32768U, 65535U);
        recipe.gain_q15 = static_cast<std::uint16_t>(std::clamp<std::uint64_t>(
            (static_cast<std::uint64_t>(base.gain_q15) * gain_scale_q15 + 16384U)
                >> 15U,
            0U,
            32767U));
    }
    return recipes;
}

RhythmPresetInfo rhythmPresetInfo(std::uint8_t index) {
    const auto& rhythm = rhythmDescriptor(index);
    return RhythmPresetInfo{
        rhythm.id,
        rhythm.name,
        rhythm.family,
        rhythm.grouping,
        rhythm.source_relationship,
        rhythm.meter_numerator,
        rhythm.note_value_denominator,
        rhythm.phrase_bars,
        rhythm.authenticity_claim,
    };
}

bool sameSoundControls(const Controls& left, const Controls& right) noexcept {
    if (left.complexity != right.complexity
        || left.enthusiasm != right.enthusiasm
        || left.tempo_milli_bpm != right.tempo_milli_bpm
        || left.swing_u15 != right.swing_u15
        || left.rhythm_preset != right.rhythm_preset) {
        return false;
    }
    for (std::size_t lane = 0; lane < kLogicalLaneCount; ++lane) {
        const auto& a = left.voice_shapes[lane];
        const auto& b = right.voice_shapes[lane];
        if (a.tune_u7 != b.tune_u7
            || a.timbre_u7 != b.timbre_u7
            || a.color_u7 != b.color_u7
            || a.decay_u7 != b.decay_u7
            || a.pitch_env_u7 != b.pitch_env_u7
            || a.level_u7 != b.level_u7) {
            return false;
        }
    }
    return true;
}

const std::string& presetFingerprint() noexcept {
    static const std::string fingerprint{generated::kPresetFingerprint};
    return fingerprint;
}

}  // namespace schuss::generative_drum_machine
