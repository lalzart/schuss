#include "tidepit/control_map.hpp"

#include "../generated/control_descriptors.hpp"

#include <algorithm>

namespace tidepit {

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
        [cc](const EncoderDescriptor& descriptor) { return descriptor.cc == cc; }
    );
    return match == generated::kEncoders.end() ? nullptr : &*match;
}

const ButtonDescriptor* buttonDescriptor(std::uint8_t cc) noexcept {
    const auto match = std::find_if(
        generated::kButtons.begin(),
        generated::kButtons.end(),
        [cc](const ButtonDescriptor& descriptor) { return descriptor.cc == cc; }
    );
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

Controls adapterOwnedDesktopAuditionPreset() noexcept {
    return generated::kAdapterOwnedDesktopAuditionPreset;
}

double normalizedFromMidi(std::uint8_t value) noexcept {
    return static_cast<double>(value) / 127.0;
}

std::int32_t rootNoteFromMidi(std::uint8_t value) noexcept {
    const auto bounded = std::min<unsigned>(value, 127U);
    return 36 + static_cast<std::int32_t>((bounded * 36U + 63U) / 127U);
}

MappingResult mapMidiCc(
    std::uint8_t one_based_channel,
    std::uint8_t cc,
    std::uint8_t value
) noexcept {
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
        result.normalized_value = normalizedFromMidi(value);
        result.root_note = encoder->id == ControlId::set_root
            ? rootNoteFromMidi(value)
            : 0;
        result.status = MappingStatus::accepted_continuous;
        return result;
    }

    if (const auto* button = buttonDescriptor(cc)) {
        result.id = button->id;
        if (button->kind == ControlKind::unassigned) {
            result.status = MappingStatus::unassigned;
            return result;
        }
        result.normalized_value = normalizedFromMidi(value);
        if (value == button->press_value) {
            result.status = MappingStatus::accepted_action_press;
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

std::optional<SemanticAction> semanticAction(ControlId id) noexcept {
    switch (id) {
        case ControlId::set_stage_1: return SemanticAction::set_stage_1;
        case ControlId::set_stage_2: return SemanticAction::set_stage_2;
        case ControlId::set_stage_3: return SemanticAction::set_stage_3;
        case ControlId::set_stage_4: return SemanticAction::set_stage_4;
        case ControlId::set_rate: return SemanticAction::set_rate;
        case ControlId::set_memory: return SemanticAction::set_memory;
        case ControlId::set_material: return SemanticAction::set_material;
        case ControlId::set_position: return SemanticAction::set_position;
        case ControlId::set_fx_a: return SemanticAction::set_fx_a;
        case ControlId::set_fx_b: return SemanticAction::set_fx_b;
        case ControlId::set_root: return SemanticAction::set_root;
        case ControlId::source_next: return SemanticAction::source_next;
        case ControlId::mutate: return SemanticAction::mutate;
        case ControlId::lock_toggle: return SemanticAction::lock_toggle;
        case ControlId::capture_toggle: return SemanticAction::capture_toggle;
        case ControlId::effect_next: return SemanticAction::effect_next;
        case ControlId::target_next: return SemanticAction::target_next;
        case ControlId::scale_next: return SemanticAction::scale_next;
        case ControlId::unassigned: return std::nullopt;
    }
    return std::nullopt;
}

}  // namespace tidepit
