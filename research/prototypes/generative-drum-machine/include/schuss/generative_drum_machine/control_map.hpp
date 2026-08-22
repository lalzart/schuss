#pragma once

#include "schuss/generative_drum_machine/core.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace schuss::generative_drum_machine {

enum class ControlId : std::uint8_t {
    complexity_kick,
    complexity_snare,
    complexity_hat,
    complexity_percussion_1,
    complexity_percussion_2,
    complexity_percussion_3,
    enthusiasm,
    tempo_milli_bpm,
    swing_u15,
    rhythm_select,
    shape_tune,
    shape_timbre,
    shape_color,
    shape_decay,
    shape_pitch_env,
    shape_level,
    fill,
    rhythm_next,
    shape_select_kick,
    shape_select_snare,
    shape_select_hat,
    shape_select_percussion_1,
    shape_select_percussion_2,
    shape_select_percussion_3,
    unassigned,
};

enum class ControlKind : std::uint8_t {
    continuous,
    action,
    unassigned,
};

enum class MappingCurve : std::uint8_t {
    u16_full_range,
    tempo_milli_bpm,
    swing_u15,
    rhythm_index,
    u7_identity,
    none,
};

enum class GestureKind : std::uint8_t {
    direct_rising_edge,
    none,
};

struct EncoderDescriptor final {
    ControlId id;
    std::uint8_t cc;
    std::string_view physical_control;
    std::string_view label;
    std::string_view semantic_key;
    ControlKind kind;
    MappingCurve curve;
    std::uint32_t minimum;
    std::uint32_t maximum;
    std::string_view timing;
};

struct ButtonDescriptor final {
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
    inactive_mode,
    unknown_controller,
    invalid_value,
};

struct MappingResult final {
    MappingStatus status{MappingStatus::unknown_controller};
    ControlId id{ControlId::unassigned};
    std::uint32_t mapped_value{};
    std::uint8_t midi_value{};

    [[nodiscard]] constexpr bool accepted() const noexcept {
        return status == MappingStatus::accepted_continuous
            || status == MappingStatus::accepted_action_press
            || status == MappingStatus::accepted_action_release;
    }

    [[nodiscard]] constexpr bool dispatchesSemantic() const noexcept {
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
[[nodiscard]] Controls desktopAuditionControls() noexcept;

[[nodiscard]] MappingResult mapMidiCc(
    std::uint8_t one_based_channel,
    std::uint8_t cc,
    std::uint8_t value) noexcept;

// Applies only already-mapped public semantics. Action releases are accepted
// for accounting but deliberately return false and do not queue a second fill.
[[nodiscard]] bool applyMapping(
    Controls& controls,
    bool& fill_queued,
    const MappingResult& mapping) noexcept;

// UI preset selection and CC41 both terminate at this public-state reducer.
[[nodiscard]] bool selectRhythmPreset(
    Controls& controls,
    std::uint8_t rhythm_preset) noexcept;

}  // namespace schuss::generative_drum_machine
