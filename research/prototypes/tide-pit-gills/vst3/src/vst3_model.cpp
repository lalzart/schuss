#include "tidepit/vst3_model.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <sstream>

namespace tidepit {
namespace {

constexpr std::array<Vst3ParameterDescriptor, kVst3ParameterCount> kDescriptors{{
    {"tide.stage1", "Stage 1", "%", Vst3ParameterTarget::stage,
        Vst3Presentation::unit_percent, 0U, 0.0F, 1.0F, 0.20F, 0U},
    {"tide.stage2", "Stage 2", "%", Vst3ParameterTarget::stage,
        Vst3Presentation::unit_percent, 1U, 0.0F, 1.0F, 0.50F, 0U},
    {"tide.stage3", "Stage 3", "%", Vst3ParameterTarget::stage,
        Vst3Presentation::unit_percent, 2U, 0.0F, 1.0F, 0.80F, 0U},
    {"tide.stage4", "Stage 4", "%", Vst3ParameterTarget::stage,
        Vst3Presentation::unit_percent, 3U, 0.0F, 1.0F, 0.30F, 0U},
    {"tide.rate", "Rate", "%", Vst3ParameterTarget::rate,
        Vst3Presentation::unit_percent, 0U, 0.0F, 1.0F, 0.55F, 0U},
    {"tide.memory", "Memory", "%", Vst3ParameterTarget::memory,
        Vst3Presentation::unit_percent, 0U, 0.0F, 1.0F, 0.78F, 0U},
    {"tide.material", "Material", "%", Vst3ParameterTarget::material,
        Vst3Presentation::unit_percent, 0U, 0.0F, 1.0F, 0.50F, 0U},
    {"tide.position", "Position", "%", Vst3ParameterTarget::position,
        Vst3Presentation::unit_percent, 0U, 0.0F, 1.0F, 0.31F, 0U},
    {"tide.fx-a", "FX-A", "%", Vst3ParameterTarget::fx_a,
        Vst3Presentation::unit_percent, 0U, 0.0F, 1.0F, 0.60F, 0U},
    {"tide.fx-b", "FX-B", "%", Vst3ParameterTarget::fx_b,
        Vst3Presentation::unit_percent, 0U, 0.0F, 1.0F, 0.35F, 0U},
    {"tide.root", "Root", "note", Vst3ParameterTarget::root,
        Vst3Presentation::midi_note, 0U, 36.0F, 72.0F, 60.0F, 37U},
    {"tide.source", "Source", "", Vst3ParameterTarget::source,
        Vst3Presentation::source_mode, 0U, 0.0F, 2.0F, 0.0F, 3U},
    {"tide.lock", "Lock", "", Vst3ParameterTarget::lock,
        Vst3Presentation::on_off, 0U, 0.0F, 1.0F, 0.0F, 2U},
    {"tide.effect", "FX Mode", "", Vst3ParameterTarget::effect,
        Vst3Presentation::effect_mode, 0U, 0.0F, 2.0F, 0.0F, 3U},
    {"tide.target", "Target", "", Vst3ParameterTarget::target,
        Vst3Presentation::wave_target, 0U, 0.0F, 3.0F, 0.0F, 4U},
    {"tide.scale", "Scale", "", Vst3ParameterTarget::scale,
        Vst3Presentation::scale_mode, 0U, 0.0F, 3.0F, 0.0F, 4U},
}};

[[nodiscard]] float boundedNormalized(
    const Vst3ParameterDescriptor& descriptor,
    float normalized) noexcept {
    if (!std::isfinite(normalized)) {
        const auto span = descriptor.maximum - descriptor.minimum;
        return span > 0.0F
            ? (descriptor.default_physical - descriptor.minimum) / span
            : 0.0F;
    }
    return std::clamp(normalized, 0.0F, 1.0F);
}

[[nodiscard]] float snapPhysical(
    const Vst3ParameterDescriptor& descriptor,
    float physical) noexcept {
    const auto fallback = descriptor.default_physical;
    auto result = std::clamp(
        std::isfinite(physical) ? physical : fallback,
        descriptor.minimum,
        descriptor.maximum);
    if (descriptor.step_count > 1U) {
        const auto denominator = static_cast<float>(descriptor.step_count - 1U);
        const auto step = (descriptor.maximum - descriptor.minimum) / denominator;
        result = descriptor.minimum
            + std::round((result - descriptor.minimum) / step) * step;
        result = std::clamp(result, descriptor.minimum, descriptor.maximum);
    }
    return result;
}

[[nodiscard]] std::string compactNumber(float value, int precision) {
    std::ostringstream stream;
    stream << std::fixed << std::setprecision(precision) << value;
    auto result = stream.str();
    while (result.size() > 1U && result.back() == '0') result.pop_back();
    if (!result.empty() && result.back() == '.') result.pop_back();
    return result;
}

void fnvByte(std::uint64_t& value, std::uint8_t byte) noexcept {
    value ^= byte;
    value *= UINT64_C(1099511628211);
}

void fnvText(std::uint64_t& value, std::string_view text) noexcept {
    for (const auto character : text) {
        fnvByte(value, static_cast<std::uint8_t>(character));
    }
    fnvByte(value, 0U);
}

template <typename Value>
void fnvScalar(std::uint64_t& hash, const Value& value) noexcept {
    std::array<std::uint8_t, sizeof(Value)> bytes{};
    std::memcpy(bytes.data(), &value, sizeof(Value));
    for (const auto byte : bytes) fnvByte(hash, byte);
}

void setPhysical(
    Vst3ProgramState& program,
    std::size_t index,
    float physical) noexcept {
    program.normalized[index] = vst3NormalizePhysical(kDescriptors[index], physical);
}

[[nodiscard]] int physicalIndex(
    const Vst3ProgramState& program,
    std::size_t index) noexcept {
    return static_cast<int>(std::lround(
        vst3DenormalizeParameter(kDescriptors[index], program.normalized[index])));
}

}  // namespace

const std::array<Vst3ParameterDescriptor, kVst3ParameterCount>&
vst3ParameterDescriptors() noexcept {
    return kDescriptors;
}

float vst3NormalizePhysical(
    const Vst3ParameterDescriptor& descriptor,
    float physical) noexcept {
    const auto span = descriptor.maximum - descriptor.minimum;
    if (!(span > 0.0F)) return 0.0F;
    return std::clamp(
        (snapPhysical(descriptor, physical) - descriptor.minimum) / span,
        0.0F,
        1.0F);
}

float vst3DenormalizeParameter(
    const Vst3ParameterDescriptor& descriptor,
    float normalized) noexcept {
    const auto value = descriptor.minimum
        + boundedNormalized(descriptor, normalized)
            * (descriptor.maximum - descriptor.minimum);
    return snapPhysical(descriptor, value);
}

float vst3DefaultNormalized(
    const Vst3ParameterDescriptor& descriptor) noexcept {
    return vst3NormalizePhysical(descriptor, descriptor.default_physical);
}

std::string vst3FormatParameter(
    const Vst3ParameterDescriptor& descriptor,
    float normalized) {
    const auto physical = vst3DenormalizeParameter(descriptor, normalized);
    const auto index = static_cast<int>(std::lround(physical));
    switch (descriptor.presentation) {
        case Vst3Presentation::unit_percent:
            return compactNumber(physical * 100.0F, 1) + "%";
        case Vst3Presentation::midi_note:
            return std::to_string(index);
        case Vst3Presentation::source_mode:
            return sourceName(static_cast<SourceMode>(std::clamp(index, 0, 2)));
        case Vst3Presentation::on_off:
            return index == 0 ? "OFF" : "ON";
        case Vst3Presentation::effect_mode:
            return effectName(static_cast<EffectMode>(std::clamp(index, 0, 2)));
        case Vst3Presentation::wave_target:
            return targetName(static_cast<WaveTarget>(std::clamp(index, 0, 3)));
        case Vst3Presentation::scale_mode:
            return scaleName(static_cast<ScaleMode>(std::clamp(index, 0, 3)));
    }
    return compactNumber(physical, 3);
}

Vst3ProgramState defaultVst3ProgramState() noexcept {
    Vst3ProgramState result{};
    for (std::size_t index = 0; index < kDescriptors.size(); ++index) {
        result.normalized[index] = vst3DefaultNormalized(kDescriptors[index]);
    }
    return result;
}

Controls vst3ControlsFromProgram(const Vst3ProgramState& program) noexcept {
    auto result = Controls{};
    for (std::size_t stage = 0; stage < 4U; ++stage) {
        result.stages[stage] = vst3DenormalizeParameter(
            kDescriptors[kVst3Stage1Index + stage],
            program.normalized[kVst3Stage1Index + stage]);
    }
    result.rate = vst3DenormalizeParameter(
        kDescriptors[kVst3RateIndex], program.normalized[kVst3RateIndex]);
    result.memory = vst3DenormalizeParameter(
        kDescriptors[kVst3MemoryIndex], program.normalized[kVst3MemoryIndex]);
    result.material = vst3DenormalizeParameter(
        kDescriptors[kVst3MaterialIndex], program.normalized[kVst3MaterialIndex]);
    result.position = vst3DenormalizeParameter(
        kDescriptors[kVst3PositionIndex], program.normalized[kVst3PositionIndex]);
    result.fx_a = vst3DenormalizeParameter(
        kDescriptors[kVst3FxAIndex], program.normalized[kVst3FxAIndex]);
    result.fx_b = vst3DenormalizeParameter(
        kDescriptors[kVst3FxBIndex], program.normalized[kVst3FxBIndex]);
    result.root_note = static_cast<std::int32_t>(std::lround(
        vst3DenormalizeParameter(
            kDescriptors[kVst3RootIndex], program.normalized[kVst3RootIndex])));
    return result;
}

Vst3DiscreteState vst3DiscreteFromProgram(
    const Vst3ProgramState& program) noexcept {
    return {
        static_cast<SourceMode>(std::clamp(
            physicalIndex(program, kVst3SourceIndex), 0, 2)),
        physicalIndex(program, kVst3LockIndex) != 0,
        static_cast<EffectMode>(std::clamp(
            physicalIndex(program, kVst3EffectIndex), 0, 2)),
        static_cast<WaveTarget>(std::clamp(
            physicalIndex(program, kVst3TargetIndex), 0, 3)),
        static_cast<ScaleMode>(std::clamp(
            physicalIndex(program, kVst3ScaleIndex), 0, 3)),
    };
}

bool validVst3ProgramState(const Vst3ProgramState& program) noexcept {
    for (std::size_t index = 0; index < program.normalized.size(); ++index) {
        const auto value = program.normalized[index];
        if (!std::isfinite(value) || value < 0.0F || value > 1.0F) return false;
        if (kDescriptors[index].step_count > 1U) {
            const auto canonical = vst3NormalizePhysical(
                kDescriptors[index],
                vst3DenormalizeParameter(kDescriptors[index], value));
            if (std::abs(canonical - value) > 1.0e-6F) return false;
        }
    }
    return true;
}

std::optional<std::size_t> vst3ParameterIndexForId(
    std::string_view id) noexcept {
    for (std::size_t index = 0; index < kDescriptors.size(); ++index) {
        if (kDescriptors[index].id == id) return index;
    }
    return std::nullopt;
}

std::optional<std::size_t> vst3ParameterIndexForAction(
    SemanticAction action) noexcept {
    switch (action) {
        case SemanticAction::set_stage_1: return 0U;
        case SemanticAction::set_stage_2: return 1U;
        case SemanticAction::set_stage_3: return 2U;
        case SemanticAction::set_stage_4: return 3U;
        case SemanticAction::set_rate: return kVst3RateIndex;
        case SemanticAction::set_memory: return kVst3MemoryIndex;
        case SemanticAction::set_material: return kVst3MaterialIndex;
        case SemanticAction::set_position: return kVst3PositionIndex;
        case SemanticAction::set_fx_a: return kVst3FxAIndex;
        case SemanticAction::set_fx_b: return kVst3FxBIndex;
        case SemanticAction::set_root: return kVst3RootIndex;
        default: return std::nullopt;
    }
}

bool vst3CycleProgramForAction(
    Vst3ProgramState& program,
    SemanticAction action) noexcept {
    switch (action) {
        case SemanticAction::source_next:
            setPhysical(program, kVst3SourceIndex,
                static_cast<float>((physicalIndex(program, kVst3SourceIndex) + 1) % 3));
            return true;
        case SemanticAction::lock_toggle:
            setPhysical(program, kVst3LockIndex,
                physicalIndex(program, kVst3LockIndex) == 0 ? 1.0F : 0.0F);
            return true;
        case SemanticAction::effect_next:
            setPhysical(program, kVst3EffectIndex,
                static_cast<float>((physicalIndex(program, kVst3EffectIndex) + 1) % 3));
            return true;
        case SemanticAction::target_next:
            setPhysical(program, kVst3TargetIndex,
                static_cast<float>((physicalIndex(program, kVst3TargetIndex) + 1) % 4));
            return true;
        case SemanticAction::scale_next:
            setPhysical(program, kVst3ScaleIndex,
                static_cast<float>((physicalIndex(program, kVst3ScaleIndex) + 1) % 4));
            return true;
        default:
            return false;
    }
}

std::uint64_t vst3ParameterContractFingerprint() noexcept {
    auto hash = UINT64_C(1469598103934665603);
    for (const auto& descriptor : kDescriptors) {
        fnvText(hash, descriptor.id);
        fnvText(hash, descriptor.name);
        fnvText(hash, descriptor.unit);
        fnvScalar(hash, descriptor.target);
        fnvScalar(hash, descriptor.presentation);
        fnvScalar(hash, descriptor.element);
        fnvScalar(hash, descriptor.minimum);
        fnvScalar(hash, descriptor.maximum);
        fnvScalar(hash, descriptor.default_physical);
        fnvScalar(hash, descriptor.step_count);
    }
    return hash;
}

}  // namespace tidepit
