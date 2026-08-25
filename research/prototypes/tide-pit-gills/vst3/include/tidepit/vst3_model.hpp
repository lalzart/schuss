#pragma once

#include "tidepit/core.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace tidepit {

inline constexpr std::size_t kVst3ParameterCount = 16U;
inline constexpr std::size_t kVst3Stage1Index = 0U;
inline constexpr std::size_t kVst3RateIndex = 4U;
inline constexpr std::size_t kVst3MemoryIndex = 5U;
inline constexpr std::size_t kVst3MaterialIndex = 6U;
inline constexpr std::size_t kVst3PositionIndex = 7U;
inline constexpr std::size_t kVst3FxAIndex = 8U;
inline constexpr std::size_t kVst3FxBIndex = 9U;
inline constexpr std::size_t kVst3RootIndex = 10U;
inline constexpr std::size_t kVst3SourceIndex = 11U;
inline constexpr std::size_t kVst3LockIndex = 12U;
inline constexpr std::size_t kVst3EffectIndex = 13U;
inline constexpr std::size_t kVst3TargetIndex = 14U;
inline constexpr std::size_t kVst3ScaleIndex = 15U;
inline constexpr std::uint32_t kVst3StateSchemaVersion = 1U;
inline constexpr std::string_view kVst3StateSchema{
    "schuss-tide-pit-vst3-state-v1"};

enum class Vst3ParameterTarget : std::uint8_t {
    stage,
    rate,
    memory,
    material,
    position,
    fx_a,
    fx_b,
    root,
    source,
    lock,
    effect,
    target,
    scale,
};

enum class Vst3Presentation : std::uint8_t {
    unit_percent,
    midi_note,
    source_mode,
    on_off,
    effect_mode,
    wave_target,
    scale_mode,
};

struct Vst3ParameterDescriptor final {
    std::string_view id;
    std::string_view name;
    std::string_view unit;
    Vst3ParameterTarget target{Vst3ParameterTarget::stage};
    Vst3Presentation presentation{Vst3Presentation::unit_percent};
    std::uint8_t element{};
    float minimum{};
    float maximum{1.0F};
    float default_physical{};
    // Zero means continuous. Otherwise this is the exact number of legal
    // evenly spaced values including both endpoints.
    std::uint32_t step_count{};
};

struct Vst3ProgramState final {
    std::array<float, kVst3ParameterCount> normalized{};
};

struct Vst3DiscreteState final {
    SourceMode source{SourceMode::reed};
    bool locked{};
    EffectMode effect{EffectMode::clean};
    WaveTarget target{WaveTarget::pitch};
    ScaleMode scale{ScaleMode::maj5};
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

[[nodiscard]] Vst3ProgramState defaultVst3ProgramState() noexcept;
[[nodiscard]] Controls vst3ControlsFromProgram(
    const Vst3ProgramState& program) noexcept;
[[nodiscard]] Vst3DiscreteState vst3DiscreteFromProgram(
    const Vst3ProgramState& program) noexcept;
[[nodiscard]] bool validVst3ProgramState(
    const Vst3ProgramState& program) noexcept;

[[nodiscard]] std::optional<std::size_t> vst3ParameterIndexForId(
    std::string_view id) noexcept;
[[nodiscard]] std::optional<std::size_t> vst3ParameterIndexForAction(
    SemanticAction action) noexcept;
[[nodiscard]] bool vst3CycleProgramForAction(
    Vst3ProgramState& program,
    SemanticAction action) noexcept;

// Deterministic allocation-free digest over IDs, ordering, targets, domains,
// defaults, and step counts. Tests freeze the observed value.
[[nodiscard]] std::uint64_t vst3ParameterContractFingerprint() noexcept;

}  // namespace tidepit
