#include "schuss/generative_drum_machine/control_map.hpp"

#include "../generated/control_descriptors.hpp"

#include <algorithm>

namespace schuss::generative_drum_machine {
namespace {

std::uint32_t roundHalfUpScale(
    std::uint8_t value,
    std::uint32_t span,
    std::uint32_t offset = 0U) noexcept {
    return offset + (static_cast<std::uint32_t>(value) * span + 63U) / 127U;
}

std::uint32_t mappedValue(const EncoderDescriptor& descriptor, std::uint8_t value) noexcept {
    switch (descriptor.curve) {
        case MappingCurve::u16_full_range:
            return roundHalfUpScale(value, 65535U);
        case MappingCurve::tempo_milli_bpm:
            return roundHalfUpScale(value, 210000U, 30000U);
        case MappingCurve::swing_u15:
            return roundHalfUpScale(value, 32767U);
        case MappingCurve::rhythm_index:
            return roundHalfUpScale(value, kRhythmPresetCount - 1U);
        case MappingCurve::u7_identity:
            return value;
        case MappingCurve::none:
            return 0U;
    }
    return 0U;
}

}  // namespace

const std::array<EncoderDescriptor, 16>& encoderDescriptors() noexcept {
    return generated::kEncoders;
}

const std::array<ButtonDescriptor, 8>& buttonDescriptors() noexcept {
    return generated::kButtons;
}

const EncoderDescriptor* encoderDescriptor(std::uint8_t cc) noexcept {
    const auto match = std::find_if(
        generated::kEncoders.begin(),
        generated::kEncoders.end(),
        [cc](const EncoderDescriptor& descriptor) { return descriptor.cc == cc; });
    return match == generated::kEncoders.end() ? nullptr : &*match;
}

const ButtonDescriptor* buttonDescriptor(std::uint8_t cc) noexcept {
    const auto match = std::find_if(
        generated::kButtons.begin(),
        generated::kButtons.end(),
        [cc](const ButtonDescriptor& descriptor) { return descriptor.cc == cc; });
    return match == generated::kButtons.end() ? nullptr : &*match;
}

std::uint8_t launchControlMidiChannel() noexcept {
    return generated::kMidiChannel;
}

std::string_view controlMapSha256() noexcept {
    return generated::kControlMapSha256;
}

std::string_view controllerTopologySha256() noexcept {
    return generated::kControllerTopologySha256;
}

Controls desktopAuditionControls() noexcept {
    return generated::kDesktopAuditionControls;
}

MappingResult mapMidiCc(
    std::uint8_t one_based_channel,
    std::uint8_t cc,
    std::uint8_t value) noexcept {
    MappingResult result{};
    result.midi_value = value;
    if (one_based_channel != generated::kMidiChannel) {
        result.status = MappingStatus::ignored_channel;
        return result;
    }
    if (value > 127U) {
        result.status = MappingStatus::invalid_value;
        return result;
    }
    if (const auto* encoder = encoderDescriptor(cc)) {
        result.id = encoder->id;
        if (encoder->kind == ControlKind::unassigned) {
            result.status = MappingStatus::unassigned;
            return result;
        }
        result.mapped_value = mappedValue(*encoder, value);
        result.status = MappingStatus::accepted_continuous;
        return result;
    }
    if (const auto* button = buttonDescriptor(cc)) {
        result.id = button->id;
        if (button->kind == ControlKind::unassigned) {
            result.status = MappingStatus::unassigned;
            return result;
        }
        if (value == button->press_value) {
            result.status = MappingStatus::accepted_action_press;
            result.mapped_value = 1U;
        } else if (value == button->release_value) {
            result.status = MappingStatus::accepted_action_release;
        } else {
            result.status = MappingStatus::invalid_value;
        }
        return result;
    }
    result.status = MappingStatus::unknown_controller;
    return result;
}

bool applyMapping(
    Controls& controls,
    bool& fill_queued,
    const MappingResult& mapping) noexcept {
    if (!mapping.dispatchesSemantic()) {
        return false;
    }
    const auto is_continuous = mapping.status == MappingStatus::accepted_continuous;
    switch (mapping.id) {
        case ControlId::complexity_kick:
            if (!is_continuous || mapping.mapped_value > 65535U) return false;
            controls.complexity[0] = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::complexity_snare:
            if (!is_continuous || mapping.mapped_value > 65535U) return false;
            controls.complexity[1] = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::complexity_hat:
            if (!is_continuous || mapping.mapped_value > 65535U) return false;
            controls.complexity[2] = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::complexity_percussion_1:
            if (!is_continuous || mapping.mapped_value > 65535U) return false;
            controls.complexity[3] = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::complexity_percussion_2:
            if (!is_continuous || mapping.mapped_value > 65535U) return false;
            controls.complexity[4] = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::complexity_percussion_3:
            if (!is_continuous || mapping.mapped_value > 65535U) return false;
            controls.complexity[5] = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::enthusiasm:
            if (!is_continuous || mapping.mapped_value > 65535U) return false;
            controls.enthusiasm = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::tempo_milli_bpm:
            if (!is_continuous
                || mapping.mapped_value < 30000U
                || mapping.mapped_value > 240000U) return false;
            controls.tempo_milli_bpm = mapping.mapped_value;
            return true;
        case ControlId::swing_u15:
            if (!is_continuous || mapping.mapped_value > 32767U) return false;
            controls.swing_u15 = static_cast<std::uint16_t>(mapping.mapped_value);
            return true;
        case ControlId::rhythm_select:
            if (!is_continuous || mapping.mapped_value >= kRhythmPresetCount) return false;
            return selectRhythmPreset(
                controls, static_cast<std::uint8_t>(mapping.mapped_value));
        case ControlId::shape_tune:
        case ControlId::shape_timbre:
        case ControlId::shape_color:
        case ControlId::shape_decay:
        case ControlId::shape_pitch_env:
        case ControlId::shape_level: {
            if (!is_continuous
                || mapping.mapped_value > 127U
                || !controls.voice_shaping
                || controls.selected_voice_lane >= kLogicalLaneCount) {
                return false;
            }
            auto& shape = controls.voice_shapes[controls.selected_voice_lane];
            const auto value = static_cast<std::uint8_t>(mapping.mapped_value);
            switch (mapping.id) {
                case ControlId::shape_tune:
                    shape.tune_u7 = value;
                    break;
                case ControlId::shape_timbre:
                    shape.timbre_u7 = value;
                    break;
                case ControlId::shape_color:
                    shape.color_u7 = value;
                    break;
                case ControlId::shape_decay:
                    shape.decay_u7 = value;
                    break;
                case ControlId::shape_pitch_env:
                    shape.pitch_env_u7 = value;
                    break;
                case ControlId::shape_level:
                    shape.level_u7 = value;
                    break;
                default:
                    return false;
            }
            return true;
        }
        case ControlId::fill:
            if (mapping.status != MappingStatus::accepted_action_press
                || mapping.mapped_value != 1U) return false;
            fill_queued = true;
            return true;
        case ControlId::rhythm_next:
            if (mapping.status != MappingStatus::accepted_action_press
                || mapping.mapped_value != 1U) return false;
            return selectRhythmPreset(
                controls,
                static_cast<std::uint8_t>(
                    (controls.rhythm_preset + 1U) % kRhythmPresetCount));
        case ControlId::shape_select_kick:
        case ControlId::shape_select_snare:
        case ControlId::shape_select_hat:
        case ControlId::shape_select_percussion_1:
        case ControlId::shape_select_percussion_2:
        case ControlId::shape_select_percussion_3: {
            if (mapping.status != MappingStatus::accepted_action_press
                || mapping.mapped_value != 1U) return false;
            const auto lane = static_cast<std::uint8_t>(
                static_cast<std::uint8_t>(mapping.id)
                - static_cast<std::uint8_t>(ControlId::shape_select_kick));
            if (lane >= kLogicalLaneCount) return false;
            if (controls.voice_shaping && controls.selected_voice_lane == lane) {
                controls.voice_shaping = false;
            } else {
                controls.selected_voice_lane = lane;
                controls.voice_shaping = true;
            }
            return true;
        }
        case ControlId::unassigned:
            return false;
    }
    return false;
}

bool selectRhythmPreset(
    Controls& controls,
    std::uint8_t rhythm_preset) noexcept {
    if (rhythm_preset >= kRhythmPresetCount
        || controls.rhythm_preset == rhythm_preset) {
        return false;
    }
    controls.rhythm_preset = rhythm_preset;
    return true;
}

}  // namespace schuss::generative_drum_machine
