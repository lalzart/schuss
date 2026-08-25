#pragma once

#include "schuss/pamplist/core.hpp"
#include "schuss/pamplist/ui_model.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace schuss::pamplist {

inline constexpr std::size_t kVst3MusicalParameterCount = 178U;
inline constexpr std::size_t kVst3ParameterCount = 179U;
inline constexpr std::size_t kVst3RunParameterIndex = 178U;
inline constexpr std::uint32_t kVst3StateSchemaVersion = 1U;
inline constexpr std::string_view kVst3StateSchema{
    "schuss-pamplist-vst3-state-v1"};

enum class Vst3ParameterTarget : std::uint8_t {
    tempo,
    lane_rate,
    lane_phase,
    lane_shape,
    lane_hits,
    lane_rotation,
    lane_probability,
    lane_repeat,
    lane_amplitude,
    lane_route,
    voice_engine,
    voice_note,
    voice_harmonics,
    voice_timbre,
    voice_morph,
    voice_decay,
    voice_colour,
    voice_level,
    cohesion_drive,
    cohesion_cohere,
    cohesion_root,
    cohesion_spread,
    cohesion_tail,
    cohesion_damping,
    cohesion_width,
    cohesion_duck,
    master_gain,
    running,
};

struct Vst3ParameterDescriptor final {
    std::string id;
    std::string name;
    std::string unit;
    Vst3ParameterTarget target{Vst3ParameterTarget::tempo};
    PresentationKind presentation{PresentationKind::unit_percent};
    std::uint8_t lane{};
    std::uint8_t element{};
    float minimum{};
    float maximum{1.0F};
    float default_physical{};
    // Zero means continuous. Otherwise this is the exact number of legal
    // evenly spaced values, including both endpoints.
    std::uint32_t step_count{};
};

struct Vst3ProgramState final {
    std::array<float, kVst3ParameterCount> normalized{};
    std::uint32_t seed{kDefaultSeed};
    std::uint8_t selected_page{};
    LaneControlMode lane_control_mode{LaneControlMode::voice};
};

[[nodiscard]] const std::array<Vst3ParameterDescriptor, kVst3ParameterCount>&
vst3ParameterDescriptors() noexcept;

[[nodiscard]] float vst3NormalizePhysical(
    const Vst3ParameterDescriptor& descriptor,
    float physical) noexcept;
[[nodiscard]] float vst3DenormalizeParameter(
    const Vst3ParameterDescriptor& descriptor,
    float normalized) noexcept;
[[nodiscard]] float vst3DefaultNormalized(
    const Vst3ParameterDescriptor& descriptor) noexcept;
[[nodiscard]] std::string vst3FormatParameter(
    const Vst3ParameterDescriptor& descriptor,
    float normalized);

[[nodiscard]] float vst3ReadNormalizedParameter(
    const Controls& controls,
    std::size_t parameter_index) noexcept;
[[nodiscard]] bool vst3ApplyNormalizedParameter(
    Controls& controls,
    std::size_t parameter_index,
    float normalized) noexcept;

[[nodiscard]] Vst3ProgramState defaultVst3ProgramState() noexcept;
[[nodiscard]] Vst3ProgramState vst3ProgramFromControls(
    const Controls& controls) noexcept;
[[nodiscard]] Controls vst3ControlsFromProgram(
    const Vst3ProgramState& program,
    std::uint32_t effect_clear_generation = 0U) noexcept;
[[nodiscard]] bool validVst3ProgramState(
    const Vst3ProgramState& program) noexcept;

[[nodiscard]] std::optional<std::size_t> vst3ParameterIndexForId(
    std::string_view id) noexcept;
[[nodiscard]] std::optional<std::size_t> vst3ParameterIndexForSurface(
    const Controls& controls,
    SurfaceRow row,
    std::size_t column) noexcept;

// A deterministic, allocation-free digest over IDs, ordering, targets,
// domains, defaults, and step counts. Tests freeze its value so a host-state
// compatibility change cannot happen accidentally.
[[nodiscard]] std::uint64_t vst3ParameterContractFingerprint() noexcept;

}  // namespace schuss::pamplist
