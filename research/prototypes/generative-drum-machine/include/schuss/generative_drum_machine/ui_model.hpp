#pragma once

#include "schuss/generative_drum_machine/control_map.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace schuss::generative_drum_machine {

struct UiControlDescriptor final {
    ControlId id;
    std::uint8_t cc;
    std::string_view label;
};

inline constexpr std::array<UiControlDescriptor, kLogicalLaneCount> kLaneUiControls{{
    {ControlId::complexity_kick, 20U, "KICK"},
    {ControlId::complexity_snare, 21U, "SNARE"},
    {ControlId::complexity_hat, 22U, "HAT"},
    {ControlId::complexity_percussion_1, 23U, "PERC 1"},
    {ControlId::complexity_percussion_2, 24U, "PERC 2"},
    {ControlId::complexity_percussion_3, 25U, "PERC 3"},
}};

inline constexpr std::array<UiControlDescriptor, 3> kGlobalUiControls{{
    {ControlId::enthusiasm, 26U, "ENTHUSIASM"},
    {ControlId::tempo_milli_bpm, 27U, "TEMPO"},
    {ControlId::swing_u15, 34U, "SWING"},
}};

inline constexpr std::array<UiControlDescriptor, 6> kShapeUiControls{{
    {ControlId::shape_tune, 28U, "TUNE"},
    {ControlId::shape_timbre, 29U, "TIMBRE"},
    {ControlId::shape_color, 30U, "COLOR"},
    {ControlId::shape_decay, 31U, "DECAY"},
    {ControlId::shape_pitch_env, 32U, "PUNCH"},
    {ControlId::shape_level, 33U, "LEVEL"},
}};

[[nodiscard]] std::uint32_t acceptedValue(
    ControlId id,
    const Controls& controls) noexcept;

[[nodiscard]] std::uint8_t midiValueForAcceptedState(
    ControlId id,
    const Controls& controls) noexcept;

[[nodiscard]] std::string formatAcceptedValue(
    ControlId id,
    const Controls& controls);

[[nodiscard]] std::string_view modelName(Lane lane) noexcept;
[[nodiscard]] std::string rhythmLabel(std::uint8_t rhythm_preset);

}  // namespace schuss::generative_drum_machine
