#include "schuss/pamplist/vst3_model.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <set>
#include <string>

namespace pam = schuss::pamplist;

namespace {

[[noreturn]] void fail(const std::string& message) {
    std::cerr << "pamplist_vst3_model_tests: " << message << '\n';
    std::exit(1);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

void expectNear(float actual, float expected, float tolerance, const std::string& message) {
    if (!std::isfinite(actual) || std::abs(actual - expected) > tolerance) {
        fail(message + " actual=" + std::to_string(actual)
            + " expected=" + std::to_string(expected));
    }
}

void testStableDescriptorContract() {
    static_assert(pam::kVst3MusicalParameterCount == 178U);
    static_assert(pam::kVst3ParameterCount == 179U);
    static_assert(pam::kVst3RunParameterIndex == 178U);
    const auto& descriptors = pam::vst3ParameterDescriptors();
    expect(descriptors.size() == pam::kVst3ParameterCount,
        "parameter count drift");

    std::set<std::string> ids;
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        const auto& descriptor = descriptors[index];
        expect(!descriptor.id.empty() && !descriptor.name.empty(),
            "empty parameter identity at " + std::to_string(index));
        expect(ids.insert(descriptor.id).second,
            "duplicate parameter ID " + descriptor.id);
        expect(std::isfinite(descriptor.minimum)
                && std::isfinite(descriptor.maximum)
                && descriptor.minimum < descriptor.maximum,
            "invalid parameter domain " + descriptor.id);
        expect(descriptor.default_physical >= descriptor.minimum
                && descriptor.default_physical <= descriptor.maximum,
            "default outside parameter domain " + descriptor.id);
        expect(descriptor.step_count == 0U || descriptor.step_count >= 2U,
            "invalid parameter step count " + descriptor.id);
        expect(pam::vst3ParameterIndexForId(descriptor.id) == index,
            "ID lookup mismatch " + descriptor.id);
    }

    expect(descriptors[0].id == "pamp.tempo", "Tempo ID/order drift");
    expect(descriptors[1].id == "pamp.lane1.rate"
            && descriptors[14].id == "pamp.lane7.phase",
        "timeline ID/order drift");
    expect(descriptors[15].id == "pamp.lane1.shape"
            && descriptors[56].id == "pamp.lane7.depth",
        "decision ID/order drift");
    expect(descriptors[57].id == "pamp.lane1.motion.trigger"
            && descriptors[112].id == "pamp.lane7.motion.level",
        "Motion ID/order drift");
    expect(descriptors[113].id == "pamp.lane1.voice.model"
            && descriptors[168].id == "pamp.lane7.voice.level",
        "Voice ID/order drift");
    expect(descriptors[169].id == "pamp.global.drive"
            && descriptors[176].id == "pamp.global.duck"
            && descriptors[177].id == "pamp.master"
            && descriptors[178].id == "pamp.run",
        "Global/Run ID order drift");

    constexpr std::uint64_t expected_fingerprint =
        UINT64_C(14882405573471441702);
    const auto actual = pam::vst3ParameterContractFingerprint();
    expect(actual == expected_fingerprint,
        "parameter contract fingerprint drift actual=" + std::to_string(actual));
}

void testDefaultProgramMatchesSource() {
    const auto source = pam::defaultControls();
    const auto program = pam::defaultVst3ProgramState();
    expect(pam::validVst3ProgramState(program), "default program is invalid");
    expect(program.seed == pam::kDefaultSeed && program.selected_page == 0U
            && program.lane_control_mode == pam::LaneControlMode::voice,
        "default private state drift");
    const auto reconstructed = pam::vst3ControlsFromProgram(program);
    expect(pam::sameControls(source, reconstructed),
        "default program does not reconstruct exact source Controls");
    expect(reconstructed.effect_clear_generation == 0U,
        "default program emitted Clear");
}

void testEveryParameterRoundTrips() {
    const auto& descriptors = pam::vst3ParameterDescriptors();
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        for (const float requested : {0.0F, 0.137F, 0.5F, 0.863F, 1.0F}) {
            auto controls = pam::defaultControls();
            expect(pam::vst3ApplyNormalizedParameter(controls, index, requested),
                "parameter application failed " + descriptors[index].id);
            controls = pam::sanitizeControls(controls);
            const auto accepted = pam::vst3ReadNormalizedParameter(controls, index);
            const auto physical = pam::vst3DenormalizeParameter(
                descriptors[index], requested);
            const auto expected = pam::vst3NormalizePhysical(
                descriptors[index], physical);
            expectNear(accepted, expected, 2.0e-6F,
                "parameter round-trip mismatch " + descriptors[index].id);
        }
    }

    auto controls = pam::defaultControls();
    expect(!pam::vst3ApplyNormalizedParameter(
            controls, pam::kVst3ParameterCount, 0.5F),
        "out-of-range parameter index accepted");
    expect(!pam::vst3ApplyNormalizedParameter(
            controls, 0U, std::numeric_limits<float>::quiet_NaN()),
        "non-finite normalized parameter accepted");
}

void testProgramRoundTripAndValidation() {
    auto program = pam::defaultVst3ProgramState();
    const auto& descriptors = pam::vst3ParameterDescriptors();
    for (std::size_t index = 0; index < program.normalized.size(); ++index) {
        program.normalized[index] = static_cast<float>((index * 37U) % 997U)
            / 996.0F;
    }
    program.seed = UINT32_C(0xf1234567);
    program.selected_page = 6U;
    program.lane_control_mode = pam::LaneControlMode::motion;
    expect(pam::validVst3ProgramState(program), "dense program is invalid");

    const auto controls = pam::vst3ControlsFromProgram(program, 91U);
    expect(controls.seed == program.seed && controls.selected_page == 6U
            && controls.lane_control_mode == pam::LaneControlMode::motion
            && controls.effect_clear_generation == 91U,
        "private program state did not reach Controls");
    const auto accepted = pam::vst3ProgramFromControls(controls);
    for (std::size_t index = 0; index < program.normalized.size(); ++index) {
        const auto expected = pam::vst3NormalizePhysical(
            descriptors[index],
            pam::vst3DenormalizeParameter(descriptors[index], program.normalized[index]));
        expectNear(accepted.normalized[index], expected, 2.0e-6F,
            "program round-trip mismatch " + descriptors[index].id);
    }
    expect(accepted.seed == program.seed && accepted.selected_page == 6U
            && accepted.lane_control_mode == pam::LaneControlMode::motion,
        "program private state round-trip mismatch");

    auto invalid = program;
    invalid.normalized[17] = std::numeric_limits<float>::infinity();
    expect(!pam::validVst3ProgramState(invalid),
        "non-finite program accepted");
    invalid = program;
    invalid.normalized[17] = -0.001F;
    expect(!pam::validVst3ProgramState(invalid),
        "negative normalized program accepted");
    invalid = program;
    invalid.selected_page = 8U;
    expect(!pam::validVst3ProgramState(invalid), "invalid page accepted");
    invalid = program;
    invalid.lane_control_mode = static_cast<pam::LaneControlMode>(9U);
    expect(!pam::validVst3ProgramState(invalid), "invalid mode accepted");
}

void testSurfaceReachesEveryMusicalParameterExactly() {
    std::set<std::size_t> reached;
    auto controls = pam::defaultControls();
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        controls.selected_page = static_cast<std::uint8_t>(lane);
        for (const auto mode : {
                pam::LaneControlMode::voice,
                pam::LaneControlMode::motion}) {
            controls.lane_control_mode = mode;
            for (const auto row : {pam::SurfaceRow::top, pam::SurfaceRow::bottom}) {
                for (std::size_t column = 0; column < pam::kSurfaceColumnCount; ++column) {
                    const auto index = pam::vst3ParameterIndexForSurface(
                        controls, row, column);
                    expect(index.has_value(), "lane surface lacks a parameter");
                    expect(*index < pam::kVst3MusicalParameterCount,
                        "lane surface reached host-only parameter");
                    reached.insert(*index);
                }
            }
        }
    }
    controls.selected_page = pam::kGlobalPageIndex;
    for (std::size_t column = 0; column < pam::kSurfaceColumnCount; ++column) {
        const auto top = pam::vst3ParameterIndexForSurface(
            controls, pam::SurfaceRow::top, column);
        expect(top.has_value(), "Global top surface lacks a parameter");
        reached.insert(*top);
        const auto bottom = pam::vst3ParameterIndexForSurface(
            controls, pam::SurfaceRow::bottom, column);
        if (column < 2U) {
            expect(bottom.has_value(), "Global BPM/Master lacks a parameter");
            reached.insert(*bottom);
        } else {
            expect(!bottom.has_value(), "disabled Global slot reached a parameter");
        }
    }
    expect(reached.size() == pam::kVst3MusicalParameterCount,
        "surface does not reach exactly 178 musical parameters; reached="
            + std::to_string(reached.size()));
    for (std::size_t index = 0; index < pam::kVst3MusicalParameterCount; ++index) {
        expect(reached.count(index) == 1U,
            "unreachable musical parameter " + std::to_string(index));
    }
    expect(reached.count(pam::kVst3RunParameterIndex) == 0U,
        "surface rotary unexpectedly reached Run");
}

void testFormattingIsBoundedAndMeaningful() {
    const auto& descriptors = pam::vst3ParameterDescriptors();
    for (const auto& descriptor : descriptors) {
        for (const float value : {0.0F, 0.5F, 1.0F}) {
            const auto text = pam::vst3FormatParameter(descriptor, value);
            expect(!text.empty() && text.size() < 96U,
                "invalid formatted value " + descriptor.id);
        }
    }
    expect(pam::vst3FormatParameter(descriptors[57], 0.0F) == "Off"
            && pam::vst3FormatParameter(descriptors[57], 1.0F) == "On",
        "Trigger formatting drift");
    expect(pam::vst3FormatParameter(descriptors[58], 0.5F) == "Direct",
        "signed route center formatting drift");
    expect(pam::vst3FormatParameter(descriptors[1], 8.0F / 15.0F).find('/')
            != std::string::npos,
        "rate formatting drift");
}

}  // namespace

int main() {
    testStableDescriptorContract();
    testDefaultProgramMatchesSource();
    testEveryParameterRoundTrips();
    testProgramRoundTripAndValidation();
    testSurfaceReachesEveryMusicalParameterExactly();
    testFormattingIsBoundedAndMeaningful();
    std::cout << "pamplist_vst3_model_tests: PASS\n";
    return 0;
}
