#include "schuss/generative_drum_machine/ui_model.hpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <limits>

namespace schuss::generative_drum_machine {
namespace {

std::uint8_t ccFor(ControlId id) noexcept {
    for (const auto& descriptor : encoderDescriptors()) {
        if (descriptor.id == id) return descriptor.cc;
    }
    return 0U;
}

const VoiceShape* selectedShape(const Controls& controls) noexcept {
    return controls.selected_voice_lane < controls.voice_shapes.size()
        ? &controls.voice_shapes[controls.selected_voice_lane]
        : nullptr;
}

std::int32_t signedPercent(std::uint8_t value) noexcept {
    return value <= 64U
        ? -static_cast<std::int32_t>(64U - value) * 100 / 64
        : static_cast<std::int32_t>(value - 64U) * 100 / 63;
}

}  // namespace

std::uint32_t acceptedValue(ControlId id, const Controls& controls) noexcept {
    switch (id) {
        case ControlId::complexity_kick: return controls.complexity[0];
        case ControlId::complexity_snare: return controls.complexity[1];
        case ControlId::complexity_hat: return controls.complexity[2];
        case ControlId::complexity_percussion_1: return controls.complexity[3];
        case ControlId::complexity_percussion_2: return controls.complexity[4];
        case ControlId::complexity_percussion_3: return controls.complexity[5];
        case ControlId::enthusiasm: return controls.enthusiasm;
        case ControlId::tempo_milli_bpm: return controls.tempo_milli_bpm;
        case ControlId::swing_u15: return controls.swing_u15;
        case ControlId::rhythm_select: return controls.rhythm_preset;
        case ControlId::shape_tune:
            return selectedShape(controls) != nullptr ? selectedShape(controls)->tune_u7 : 64U;
        case ControlId::shape_timbre:
            return selectedShape(controls) != nullptr ? selectedShape(controls)->timbre_u7 : 64U;
        case ControlId::shape_color:
            return selectedShape(controls) != nullptr ? selectedShape(controls)->color_u7 : 64U;
        case ControlId::shape_decay:
            return selectedShape(controls) != nullptr ? selectedShape(controls)->decay_u7 : 64U;
        case ControlId::shape_pitch_env:
            return selectedShape(controls) != nullptr ? selectedShape(controls)->pitch_env_u7 : 64U;
        case ControlId::shape_level:
            return selectedShape(controls) != nullptr ? selectedShape(controls)->level_u7 : 64U;
        case ControlId::fill:
        case ControlId::rhythm_next:
        case ControlId::shape_select_kick:
        case ControlId::shape_select_snare:
        case ControlId::shape_select_hat:
        case ControlId::shape_select_percussion_1:
        case ControlId::shape_select_percussion_2:
        case ControlId::shape_select_percussion_3:
        case ControlId::unassigned: return 0U;
    }
    return 0U;
}

std::uint8_t midiValueForAcceptedState(ControlId id, const Controls& controls) noexcept {
    const auto cc = ccFor(id);
    if (cc == 0U) return 0U;
    const auto target = acceptedValue(id, controls);
    std::uint8_t best = 0U;
    std::uint32_t best_distance = std::numeric_limits<std::uint32_t>::max();
    for (std::uint16_t value = 0U; value <= 127U; ++value) {
        const auto mapping = mapMidiCc(16U, cc, static_cast<std::uint8_t>(value));
        if (mapping.status != MappingStatus::accepted_continuous) continue;
        const auto distance = mapping.mapped_value > target
            ? mapping.mapped_value - target
            : target - mapping.mapped_value;
        if (distance < best_distance) {
            best = static_cast<std::uint8_t>(value);
            best_distance = distance;
        }
    }
    return best;
}

std::string formatAcceptedValue(ControlId id, const Controls& controls) {
    std::array<char, 32> text{};
    const auto value = acceptedValue(id, controls);
    switch (id) {
        case ControlId::tempo_milli_bpm:
            std::snprintf(
                text.data(), text.size(), "%u.%u BPM",
                value / 1000U, (value % 1000U) / 100U);
            break;
        case ControlId::swing_u15:
            std::snprintf(
                text.data(), text.size(), "%u%%",
                (value * 100U + 16383U) / 32767U);
            break;
        case ControlId::complexity_kick:
        case ControlId::complexity_snare:
        case ControlId::complexity_hat:
        case ControlId::complexity_percussion_1:
        case ControlId::complexity_percussion_2:
        case ControlId::complexity_percussion_3:
        case ControlId::enthusiasm:
            std::snprintf(
                text.data(), text.size(), "%u%%",
                (value * 100U + 32767U) / 65535U);
            break;
        case ControlId::shape_tune: {
            const auto offset_q7 = value <= 64U
                ? -static_cast<std::int32_t>(64U - value) * 3072 / 64
                : static_cast<std::int32_t>(value - 64U) * 3072 / 63;
            const auto tenths = offset_q7 * 10 / 128;
            std::snprintf(
                text.data(), text.size(), "%+.1f ST",
                static_cast<double>(tenths) / 10.0);
            break;
        }
        case ControlId::shape_timbre:
        case ControlId::shape_color:
        case ControlId::shape_pitch_env:
            std::snprintf(text.data(), text.size(), "%+d%%", signedPercent(value));
            break;
        case ControlId::shape_decay: {
            const auto factor_milli = value <= 64U
                ? 250U + (750U * value + 32U) / 64U
                : 1000U + (3000U * (value - 64U) + 31U) / 63U;
            std::snprintf(
                text.data(), text.size(), "%u.%02ux",
                factor_milli / 1000U, (factor_milli % 1000U) / 10U);
            break;
        }
        case ControlId::shape_level: {
            const auto percent = value <= 64U
                ? (100U * value + 32U) / 64U
                : 100U + (100U * (value - 64U) + 31U) / 63U;
            std::snprintf(text.data(), text.size(), "%u%%", percent);
            break;
        }
        case ControlId::fill:
            return "TRIGGER";
        case ControlId::rhythm_select:
            return rhythmLabel(controls.rhythm_preset);
        case ControlId::rhythm_next:
            return "NEXT";
        case ControlId::shape_select_kick:
        case ControlId::shape_select_snare:
        case ControlId::shape_select_hat:
        case ControlId::shape_select_percussion_1:
        case ControlId::shape_select_percussion_2:
        case ControlId::shape_select_percussion_3:
            return "SELECT";
        case ControlId::unassigned:
            return "--";
    }
    return text.data();
}

std::string_view modelName(Lane lane) noexcept {
    const auto index = static_cast<std::size_t>(lane);
    if (index >= laneRecipes().size()) return "INVALID";
    switch (laneRecipes()[index].model) {
        case BraidsModel::kick: return "KICK";
        case BraidsModel::snare: return "SNARE";
        case BraidsModel::cymbal: return "CYMBAL";
        case BraidsModel::sine_triangle: return "SINE/TRI";
        case BraidsModel::fm: return "FM";
        case BraidsModel::filtered_noise: return "NOISE";
    }
    return "INVALID";
}

std::string rhythmLabel(std::uint8_t rhythm_preset) {
    const auto info = rhythmPresetInfo(rhythm_preset);
    return std::string{info.name} + "  "
        + std::to_string(info.meter_numerator) + "/"
        + std::to_string(info.note_value_denominator);
}

}  // namespace schuss::generative_drum_machine
