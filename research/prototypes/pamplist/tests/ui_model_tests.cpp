#include "schuss/pamplist/ui_model.hpp"

#include <array>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <set>
#include <string>

namespace pam = schuss::pamplist;

namespace {

[[noreturn]] void fail(const std::string& message) {
    std::cerr << "pamplist_ui_model_tests: " << message << '\n';
    std::exit(1);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

pam::SurfaceModel modelFor(const pam::Controls& controls) {
    pam::Snapshot snapshot{};
    snapshot.accepted = pam::sanitizeControls(controls);
    return pam::surfaceModel(snapshot);
}

void expectCompleteSlots(const pam::SurfaceModel& model) {
    std::set<pam::SurfaceSemantic> semantics;
    for (const auto& slot : model.top) {
        expect(!slot.label.empty() && !slot.tooltip.empty(),
            "top slot lacks semantic help");
        expect(slot.enabled, "lane top slot unexpectedly disabled");
        expect(slot.minimum <= slot.value && slot.value <= slot.maximum,
            "top accepted value outside presentation range");
        semantics.insert(slot.semantic);
    }
    for (const auto& slot : model.bottom) {
        expect(!slot.label.empty() && !slot.tooltip.empty(),
            "bottom slot lacks semantic help");
        expect(slot.enabled, "lane bottom slot unexpectedly disabled");
        expect(slot.minimum <= slot.value && slot.value <= slot.maximum,
            "bottom accepted value outside presentation range");
        semantics.insert(slot.semantic);
    }
    expect(model.top.size() + model.bottom.size() == pam::kSurfaceRotaryCount,
        "surface is not exactly sixteen rotary slots");
    expect(semantics.size() == pam::kSurfaceRotaryCount,
        "lane surface contains a duplicate semantic target");
}

void testVoiceAndMotionDescriptors() {
    static_assert(pam::kSurfaceColumnCount == 8U);
    static_assert(pam::kSurfaceRotaryCount == 16U);
    auto controls = pam::defaultControls();
    controls.selected_page = 2U;
    controls.voices[2].engine = 17U;
    controls.voices[2].note = 61.5F;
    controls.lanes[2].rate_index = 13U;
    controls.lanes[2].hits = 11U;

    const auto voice = modelFor(controls);
    expect(voice.context == pam::SurfaceContext::voice,
        "default lane surface is not Voice");
    expect(pam::surfaceContextName(voice.context) == "VOICE",
        "Voice context name drift");
    expect(voice.top_group.find("VOICE SHAPE") != std::string_view::npos
        && voice.bottom_group.find("SEQUENCER") != std::string_view::npos,
        "Voice grouping is unclear");
    expectCompleteSlots(voice);
    expect(voice.top[0].semantic == pam::SurfaceSemantic::voice_model
        && voice.top[0].value == 17.0
        && voice.top[1].semantic == pam::SurfaceSemantic::voice_pitch
        && voice.top[1].value == 61.5,
        "Voice descriptor does not project accepted lane values");
    expect(voice.bottom[0].semantic == pam::SurfaceSemantic::sequence_rate
        && voice.bottom[0].value == 13.0
        && voice.bottom[3].semantic == pam::SurfaceSemantic::sequence_hits
        && voice.bottom[3].value == 11.0,
        "Sequencer descriptor does not project accepted lane values");

    controls.lane_control_mode = pam::LaneControlMode::motion;
    controls.lanes[2].routes[0] = 1.0F;
    controls.lanes[2].routes[1] = -0.5F;
    const auto motion = modelFor(controls);
    expect(motion.context == pam::SurfaceContext::motion
        && pam::surfaceContextName(motion.context) == "MOTION",
        "accepted Motion context was not projected");
    expect(motion.top_group.find("MOTION") != std::string_view::npos,
        "Motion grouping is unclear");
    expectCompleteSlots(motion);
    expect(motion.top[0].semantic == pam::SurfaceSemantic::motion_trigger
        && motion.top[0].presentation == pam::PresentationKind::trigger_switch
        && motion.top[0].minimum == 0.0
        && motion.top[0].maximum == 1.0
        && motion.top[0].value == 1.0,
        "Trigger is not presented as an Off/On switch");
    expect(motion.top[1].semantic == pam::SurfaceSemantic::motion_pitch
        && motion.top[1].value == -0.5,
        "Motion descriptor does not project signed route values");
    for (std::size_t column = 0; column < pam::kSurfaceColumnCount; ++column) {
        expect(motion.bottom[column].semantic == voice.bottom[column].semantic,
            "Sequencer row changed between Voice and Motion");
    }
}

void testGlobalDescriptor() {
    auto controls = pam::defaultControls();
    controls.selected_page = pam::kGlobalPageIndex;
    controls.tempo_milli_bpm = 137000U;
    controls.master_gain = 0.42F;
    const auto global = modelFor(controls);
    expect(global.context == pam::SurfaceContext::global
        && pam::surfaceContextName(global.context) == "GLOBAL",
        "Global context was not projected");
    expect(global.top_group.find("COHESION") != std::string_view::npos
        && global.bottom_group.find("TRANSPORT") != std::string_view::npos,
        "Global grouping is unclear");
    for (const auto& slot : global.top) {
        expect(slot.enabled && !slot.tooltip.empty(),
            "Global cohesion slot unavailable or unexplained");
    }
    expect(global.bottom[0].enabled && global.bottom[0].value == 137.0
        && global.bottom[1].enabled
        && std::abs(global.bottom[1].value - 0.42) < 1.0e-6,
        "Global BPM/Master projection mismatch");
    for (std::size_t column = 2U; column < pam::kSurfaceColumnCount; ++column) {
        expect(!global.bottom[column].enabled
            && global.bottom[column].presentation
                == pam::PresentationKind::disabled,
            "reserved Global bottom slot is not explicitly disabled");
    }
}

void testApplyAndIsolation() {
    auto controls = pam::defaultControls();
    controls.selected_page = 4U;
    const auto lanes_before = controls.lanes;
    const auto voices_before = controls.voices;
    const std::array<double, 8U> voice_values{{
        23.0, 72.5, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6,
    }};
    for (std::size_t column = 0; column < voice_values.size(); ++column) {
        expect(pam::applySurfaceValue(
            controls, pam::SurfaceRow::top, column, voice_values[column]),
            "Voice surface value was rejected");
    }
    expect(controls.voices[4].engine == 23U
        && controls.voices[4].note == 72.5F
        && controls.voices[4].harmonics == 0.1F
        && controls.voices[4].level == 0.6F,
        "Voice surface values were applied incorrectly");
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        expect(controls.lanes[lane].routes == lanes_before[lane].routes,
            "Voice edit changed a motion route");
        if (lane != 4U) {
            expect(controls.voices[lane].engine == voices_before[lane].engine
                && controls.voices[lane].note == voices_before[lane].note,
                "Voice edit changed another lane");
        }
    }

    controls.lane_control_mode = pam::LaneControlMode::motion;
    const auto edited_voice = controls.voices[4];
    expect(pam::applySurfaceValue(
        controls, pam::SurfaceRow::top, 0U, 0.0),
        "Trigger Off edit rejected");
    expect(controls.lanes[4].routes[0] == 0.0F,
        "Trigger Off did not become exact zero");
    expect(pam::applySurfaceValue(
        controls, pam::SurfaceRow::top, 0U, 1.0),
        "Trigger On edit rejected");
    expect(controls.lanes[4].routes[0] == 1.0F,
        "Trigger On did not become exact one");
    expect(pam::applySurfaceValue(
        controls, pam::SurfaceRow::top, 2U, -0.75),
        "Model Sweep edit rejected");
    expect(controls.lanes[4].routes[2] == -0.75F
        && controls.voices[4].engine == edited_voice.engine
        && controls.voices[4].note == edited_voice.note,
        "Motion edit changed the base voice");

    const std::array<double, 8U> sequence_values{{
        15.0, 127.0, 7.0, 16.0, 15.0, 0.25, 64.0, 0.75,
    }};
    for (std::size_t column = 0; column < sequence_values.size(); ++column) {
        expect(pam::applySurfaceValue(
            controls, pam::SurfaceRow::bottom, column,
            sequence_values[column]),
            "Sequencer surface value was rejected");
    }
    const auto& lane = controls.lanes[4];
    expect(lane.rate_index == 15U && lane.phase_u7 == 127U
        && lane.shape == pam::Shape::smooth_random && lane.hits == 16U
        && lane.rotation == 15U && lane.probability == 0.25F
        && lane.repeat == 64U && lane.amplitude == 0.75F,
        "Sequencer surface application mismatch");

    controls.selected_page = pam::kGlobalPageIndex;
    expect(pam::applySurfaceValue(
        controls, pam::SurfaceRow::top, 1U, 0.8),
        "Global Cohere edit rejected");
    expect(pam::applySurfaceValue(
        controls, pam::SurfaceRow::bottom, 0U, 143.0),
        "Global BPM edit rejected");
    expect(!pam::applySurfaceValue(
        controls, pam::SurfaceRow::bottom, 2U, 1.0),
        "unassigned Global slot dispatched");
    expect(controls.cohesion.cohere == 0.8F
        && controls.tempo_milli_bpm == 143000U,
        "Global surface application mismatch");
    expect(!pam::applySurfaceValue(
        controls, pam::SurfaceRow::top, 8U, 0.0),
        "out-of-range surface column dispatched");
    expect(!pam::applySurfaceValue(
        controls, pam::SurfaceRow::top, 0U, std::nan("")),
        "non-finite surface value dispatched");
}

void testTriggerAppliesIndependentlyToEveryLane() {
    for (std::size_t selected = 0; selected < pam::kLaneCount; ++selected) {
        auto controls = pam::defaultControls();
        controls.selected_page = static_cast<std::uint8_t>(selected);
        controls.lane_control_mode = pam::LaneControlMode::motion;
        const auto lanes_before = controls.lanes;

        expect(pam::applySurfaceValue(
            controls, pam::SurfaceRow::top, 0U, 1.0),
            "Trigger On edit was rejected for a lane");
        expect(controls.lanes[selected].routes[0] == 1.0F,
            "Trigger On did not reach the selected lane");
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane == selected) continue;
            expect(controls.lanes[lane].routes == lanes_before[lane].routes,
                "Trigger edit changed another lane");
        }
        expect(modelFor(controls).top[0].value == 1.0,
            "selected lane Trigger On was not projected");

        expect(pam::applySurfaceValue(
            controls, pam::SurfaceRow::top, 0U, 0.0),
            "Trigger Off edit was rejected for a lane");
        expect(controls.lanes[selected].routes[0] == 0.0F
            && modelFor(controls).top[0].value == 0.0,
            "selected lane Trigger Off was not projected");
    }
}

}  // namespace

int main() {
    testVoiceAndMotionDescriptors();
    testGlobalDescriptor();
    testApplyAndIsolation();
    testTriggerAppliesIndependentlyToEveryLane();
    std::cout << "pamplist_ui_model_tests: pass\n";
    return 0;
}
