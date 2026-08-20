#pragma once

#include "tidepit/core.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace tidepit {

// Names intentionally mirror Core's SemanticAction names. `unassigned` is a
// surface descriptor state and never becomes a Core event.
enum class ControlId : std::uint8_t {
    set_stage_1,
    set_stage_2,
    set_stage_3,
    set_stage_4,
    set_rate,
    set_memory,
    set_material,
    set_position,
    set_fx_a,
    set_fx_b,
    set_root,
    source_next,
    mutate,
    lock_toggle,
    capture_toggle,
    effect_next,
    target_next,
    scale_next,
    unassigned,
};

enum class ControlKind : std::uint8_t {
    continuous,
    action,
    unassigned,
};

enum class MidiCurve : std::uint8_t {
    linear_normalized,
    root_note_round_half_up,
    none,
};

enum class SourceCurve : std::uint8_t {
    direct_normalized,
    rate_quadratic,
    memory_squared_threshold,
    contextual_material,
    grain_position,
    contextual_fx_a_soft_pickup,
    contextual_fx_b_soft_pickup,
    root_note_36_to_72,
    none,
};

enum class GestureKind : std::uint8_t {
    direct_rising_edge,
    source_effect_button_hold,
    source_effect_button_tap,
    source_encoder_switch_hold,
    source_encoder_switch_tap,
    none,
};

struct EncoderDescriptor {
    ControlId id;
    std::uint8_t cc;
    std::string_view physical_control;
    std::string_view label;
    std::string_view semantic_key;
    ControlKind kind;
    MidiCurve midi_curve;
    SourceCurve source_curve;
    std::string_view timing;
    double default_semantic_value;
    std::uint8_t default_midi_value;
    bool adapter_owned_default;
    bool soft_pickup;
};

struct ButtonDescriptor {
    ControlId id;
    std::uint8_t cc;
    std::string_view physical_control;
    std::string_view label;
    std::string_view semantic_key;
    ControlKind kind;
    GestureKind gesture;
    std::uint8_t press_value;
    std::uint8_t release_value;
};

enum class MappingStatus : std::uint8_t {
    accepted_continuous,
    accepted_action_press,
    accepted_action_release,
    ignored_channel,
    unassigned,
    unknown_controller,
    invalid_value,
};

struct MappingResult {
    MappingStatus status{MappingStatus::unknown_controller};
    ControlId id{ControlId::unassigned};
    double normalized_value{};
    std::int32_t root_note{};
    std::uint8_t midi_value{};

    [[nodiscard]] constexpr bool accepted() const noexcept {
        return status == MappingStatus::accepted_continuous
            || status == MappingStatus::accepted_action_press
            || status == MappingStatus::accepted_action_release;
    }

    [[nodiscard]] constexpr bool dispatchesCoreEvent() const noexcept {
        return status == MappingStatus::accepted_continuous
            || status == MappingStatus::accepted_action_press;
    }
};

[[nodiscard]] const std::array<EncoderDescriptor, 16>& encoderDescriptors() noexcept;
[[nodiscard]] const std::array<ButtonDescriptor, 8>& buttonDescriptors() noexcept;
[[nodiscard]] const EncoderDescriptor* encoderDescriptor(std::uint8_t cc) noexcept;
[[nodiscard]] const ButtonDescriptor* buttonDescriptor(std::uint8_t cc) noexcept;

[[nodiscard]] std::uint8_t launchControlMidiChannel() noexcept;
[[nodiscard]] std::string_view controlMapSha256() noexcept;
[[nodiscard]] std::string_view controllerTopologySha256() noexcept;
[[nodiscard]] Controls adapterOwnedDesktopAuditionPreset() noexcept;

[[nodiscard]] double normalizedFromMidi(std::uint8_t value) noexcept;
[[nodiscard]] std::int32_t rootNoteFromMidi(std::uint8_t value) noexcept;
[[nodiscard]] MappingResult mapMidiCc(
    std::uint8_t one_based_channel,
    std::uint8_t cc,
    std::uint8_t value
) noexcept;

[[nodiscard]] std::optional<SemanticAction> semanticAction(ControlId id) noexcept;

}  // namespace tidepit
