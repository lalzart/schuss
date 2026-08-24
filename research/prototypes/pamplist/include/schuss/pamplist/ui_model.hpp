#pragma once

#include "schuss/pamplist/core.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace schuss::pamplist {

inline constexpr std::size_t kSurfaceColumnCount = 8U;
inline constexpr std::size_t kSurfaceRotaryCount = 16U;

enum class SurfaceContext : std::uint8_t {
    voice,
    motion,
    global,
};

enum class SurfaceRow : std::uint8_t {
    top,
    bottom,
};

enum class SurfaceSemantic : std::uint8_t {
    voice_model,
    voice_pitch,
    voice_harmonics,
    voice_timbre,
    voice_morph,
    voice_decay,
    voice_colour,
    voice_level,
    motion_trigger,
    motion_pitch,
    motion_model_sweep,
    motion_harmonics,
    motion_timbre,
    motion_morph,
    motion_decay,
    motion_level,
    sequence_rate,
    sequence_phase,
    sequence_shape,
    sequence_hits,
    sequence_rotation,
    sequence_chance,
    sequence_repeat,
    sequence_depth,
    global_drive,
    global_cohere,
    global_root,
    global_spread,
    global_tail,
    global_damping,
    global_width,
    global_duck,
    global_bpm,
    global_master,
    global_unassigned,
};

enum class PresentationKind : std::uint8_t {
    model,
    note,
    unit_percent,
    signed_percent,
    trigger_switch,
    rate,
    phase,
    shape,
    hits,
    rotation,
    chance,
    repeat,
    depth,
    bpm,
    disabled,
};

struct SurfaceSlot final {
    SurfaceSemantic semantic{SurfaceSemantic::global_unassigned};
    std::string_view label{"-"};
    std::string_view tooltip{};
    PresentationKind presentation{PresentationKind::disabled};
    double minimum{};
    double maximum{1.0};
    double interval{1.0};
    double value{};
    bool enabled{};
};

struct SurfaceModel final {
    SurfaceContext context{SurfaceContext::voice};
    std::string_view top_group{};
    std::string_view bottom_group{};
    std::string_view guide{};
    std::array<SurfaceSlot, kSurfaceColumnCount> top{};
    std::array<SurfaceSlot, kSurfaceColumnCount> bottom{};
};

[[nodiscard]] SurfaceModel surfaceModel(const Snapshot& snapshot) noexcept;
[[nodiscard]] bool applySurfaceValue(
    Controls& controls,
    SurfaceRow row,
    std::size_t column,
    double value) noexcept;
[[nodiscard]] std::string_view surfaceContextName(
    SurfaceContext context) noexcept;

}  // namespace schuss::pamplist
