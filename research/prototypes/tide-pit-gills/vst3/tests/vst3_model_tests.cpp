#include "tidepit/vst3_model.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>

namespace {

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error(message);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

void testIdentityDomainsAndDefaults() {
    const auto& descriptors = tidepit::vst3ParameterDescriptors();
    expect(descriptors.size() == tidepit::kVst3ParameterCount,
        "parameter count drift");
    constexpr std::array<std::string_view, tidepit::kVst3ParameterCount> ids{{
        "tide.stage1", "tide.stage2", "tide.stage3", "tide.stage4",
        "tide.rate", "tide.memory", "tide.material", "tide.position",
        "tide.fx-a", "tide.fx-b", "tide.root", "tide.source",
        "tide.lock", "tide.effect", "tide.target", "tide.scale",
    }};
    std::set<std::string> unique;
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        expect(descriptors[index].id == ids[index], "parameter ID/order drift");
        expect(unique.insert(std::string{descriptors[index].id}).second,
            "duplicate parameter ID");
        expect(descriptors[index].maximum > descriptors[index].minimum,
            "invalid parameter domain");
        expect(tidepit::vst3ParameterIndexForId(ids[index]) == index,
            "ID lookup drift");
    }
    expect(!tidepit::vst3ParameterIndexForId("tide.unknown").has_value(),
        "unknown ID resolved");

    const auto program = tidepit::defaultVst3ProgramState();
    expect(tidepit::validVst3ProgramState(program), "default program invalid");
    const auto controls = tidepit::vst3ControlsFromProgram(program);
    const auto expected = tidepit::Controls{};
    expect(controls.stages == expected.stages
            && controls.rate == expected.rate
            && controls.memory == expected.memory
            && controls.material == expected.material
            && controls.position == expected.position
            && controls.fx_a == expected.fx_a
            && controls.fx_b == expected.fx_b
            && controls.root_note == expected.root_note,
        "default program does not equal Core defaults");
    const auto modes = tidepit::vst3DiscreteFromProgram(program);
    expect(modes.source == tidepit::SourceMode::reed
            && !modes.locked
            && modes.effect == tidepit::EffectMode::clean
            && modes.target == tidepit::WaveTarget::pitch
            && modes.scale == tidepit::ScaleMode::maj5,
        "default persistent mode state drift");
}

void testQuantizationAndFormatting() {
    const auto& descriptors = tidepit::vst3ParameterDescriptors();
    for (const auto& descriptor : descriptors) {
        const auto normalized_default = tidepit::vst3DefaultNormalized(descriptor);
        const auto physical_default = tidepit::vst3DenormalizeParameter(
            descriptor, normalized_default);
        expect(physical_default == descriptor.default_physical,
            "default physical round-trip drift for " + std::string{descriptor.id});
        expect(!tidepit::vst3FormatParameter(
                descriptor, normalized_default).empty(),
            "empty parameter presentation");
        if (descriptor.step_count > 1U) {
            for (std::uint32_t step = 0; step < descriptor.step_count; ++step) {
                const auto normalized = static_cast<float>(step)
                    / static_cast<float>(descriptor.step_count - 1U);
                const auto physical = tidepit::vst3DenormalizeParameter(
                    descriptor, normalized);
                const auto round_trip = tidepit::vst3NormalizePhysical(
                    descriptor, physical);
                expect(std::abs(round_trip - normalized) < 1.0e-6F,
                    "discrete quantization round-trip drift");
            }
        } else {
            for (const float normalized : {0.0F, 0.001F, 0.25F, 0.5F, 0.999F, 1.0F}) {
                const auto physical = tidepit::vst3DenormalizeParameter(
                    descriptor, normalized);
                expect(tidepit::vst3NormalizePhysical(descriptor, physical)
                        == normalized,
                    "continuous normalization round-trip drift");
            }
        }
    }
    expect(tidepit::vst3FormatParameter(
            descriptors[tidepit::kVst3SourceIndex], 0.5F) == "RND",
        "source label drift");
    expect(tidepit::vst3FormatParameter(
            descriptors[tidepit::kVst3EffectIndex], 1.0F) == "DRIVE",
        "effect label drift");
    expect(tidepit::vst3FormatParameter(
            descriptors[tidepit::kVst3ScaleIndex], 1.0F) == "HARM",
        "scale label drift");
}

void testControlsModesAndActions() {
    auto program = tidepit::defaultVst3ProgramState();
    const auto& descriptors = tidepit::vst3ParameterDescriptors();
    for (std::size_t index = 0; index < 11U; ++index) {
        const auto physical = index == tidepit::kVst3RootIndex
            ? 72.0F
            : static_cast<float>(index + 1U) / 12.0F;
        program.normalized[index] = tidepit::vst3NormalizePhysical(
            descriptors[index], physical);
    }
    expect(tidepit::validVst3ProgramState(program), "dense program invalid");
    const auto controls = tidepit::vst3ControlsFromProgram(program);
    expect(controls.stages[0] == 1.0F / 12.0F
            && controls.stages[3] == 4.0F / 12.0F
            && controls.rate == 5.0F / 12.0F
            && controls.root_note == 72,
        "dense Controls conversion drift");

    expect(tidepit::vst3CycleProgramForAction(
            program, tidepit::SemanticAction::source_next),
        "source cycle rejected");
    expect(tidepit::vst3CycleProgramForAction(
            program, tidepit::SemanticAction::lock_toggle),
        "lock cycle rejected");
    expect(tidepit::vst3CycleProgramForAction(
            program, tidepit::SemanticAction::effect_next),
        "effect cycle rejected");
    expect(tidepit::vst3CycleProgramForAction(
            program, tidepit::SemanticAction::target_next),
        "target cycle rejected");
    expect(tidepit::vst3CycleProgramForAction(
            program, tidepit::SemanticAction::scale_next),
        "scale cycle rejected");
    const auto modes = tidepit::vst3DiscreteFromProgram(program);
    expect(modes.source == tidepit::SourceMode::rnd
            && modes.locked
            && modes.effect == tidepit::EffectMode::filter
            && modes.target == tidepit::WaveTarget::body
            && modes.scale == tidepit::ScaleMode::min5,
        "mode cycling drift");
    expect(!tidepit::vst3CycleProgramForAction(
            program, tidepit::SemanticAction::mutate),
        "Mutate became persistent state");
    expect(!tidepit::vst3CycleProgramForAction(
            program, tidepit::SemanticAction::capture_toggle),
        "Freeze became persistent state");

    constexpr std::array<tidepit::SemanticAction, 11U> continuous{{
        tidepit::SemanticAction::set_stage_1,
        tidepit::SemanticAction::set_stage_2,
        tidepit::SemanticAction::set_stage_3,
        tidepit::SemanticAction::set_stage_4,
        tidepit::SemanticAction::set_rate,
        tidepit::SemanticAction::set_memory,
        tidepit::SemanticAction::set_material,
        tidepit::SemanticAction::set_position,
        tidepit::SemanticAction::set_fx_a,
        tidepit::SemanticAction::set_fx_b,
        tidepit::SemanticAction::set_root,
    }};
    for (std::size_t index = 0; index < continuous.size(); ++index) {
        expect(tidepit::vst3ParameterIndexForAction(continuous[index]) == index,
            "continuous action/index drift");
    }
    expect(!tidepit::vst3ParameterIndexForAction(
            tidepit::SemanticAction::source_next).has_value(),
        "mode action became continuous parameter");
}

void testInvalidProgramsAndFingerprint() {
    auto invalid = tidepit::defaultVst3ProgramState();
    invalid.normalized[0] = -0.01F;
    expect(!tidepit::validVst3ProgramState(invalid),
        "negative normalized value accepted");
    invalid = tidepit::defaultVst3ProgramState();
    invalid.normalized[0] = std::numeric_limits<float>::quiet_NaN();
    expect(!tidepit::validVst3ProgramState(invalid),
        "non-finite normalized value accepted");
    invalid = tidepit::defaultVst3ProgramState();
    invalid.normalized[tidepit::kVst3SourceIndex] = 0.2F;
    expect(!tidepit::validVst3ProgramState(invalid),
        "off-grid discrete value accepted");

    const auto fingerprint = tidepit::vst3ParameterContractFingerprint();
    constexpr std::uint64_t expected_fingerprint = 14672542899034963389ULL;
    expect(fingerprint == expected_fingerprint,
        "parameter contract fingerprint drift");
    std::cout << "Tide Pit VST3 parameter fingerprint: " << fingerprint << "\n";
}

}  // namespace

int main() {
    try {
        testIdentityDomainsAndDefaults();
        testQuantizationAndFormatting();
        testControlsModesAndActions();
        testInvalidProgramsAndFingerprint();
        std::cout << "Tide Pit VST3 model checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Tide Pit VST3 model failure: " << error.what() << "\n";
        return 1;
    }
}
