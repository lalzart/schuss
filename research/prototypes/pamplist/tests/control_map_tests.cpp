#include "schuss/pamplist/control_map.hpp"

#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>

namespace pam = schuss::pamplist;

namespace {

[[noreturn]] void fail(const std::string& message) {
    std::cerr << "pamplist_control_map_tests: " << message << '\n';
    std::exit(1);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

pam::MappingResult mapped(
    int cc,
    int value,
    const pam::Controls& controls) {
    return pam::mapMidiCc(
        16,
        cc,
        value,
        controls.selected_page,
        controls.lane_control_mode);
}

void testAuthority() {
    expect(pam::launchControlMidiChannel() == 16U, "MIDI channel drift");
    expect(pam::controlMapSha256()
        == "1cdc7010eee169caeaf21026ecf448db5317a130a24423578a17d357d35c07cf",
        "control-map fingerprint drift");
    expect(pam::controllerTopologySha256()
        == "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b",
        "controller topology fingerprint drift");
}

void testChannelsAndUnknown() {
    for (int channel = 1; channel <= 16; ++channel) {
        const auto result = pam::mapMidiCc(
            channel, 20, 64, 0U, pam::LaneControlMode::voice);
        expect(result.status == (channel == 16
                ? pam::MappingStatus::accepted_continuous
                : pam::MappingStatus::ignored_channel),
            "channel filter mismatch");
    }
    expect(pam::mapMidiCc(16, 19, 64, 0U, pam::LaneControlMode::voice).status
        == pam::MappingStatus::unknown_cc, "unknown low CC accepted");
    expect(pam::mapMidiCc(16, 36, 64, 0U, pam::LaneControlMode::voice).status
        == pam::MappingStatus::unknown_cc, "unknown middle CC accepted");
    expect(pam::mapMidiCc(16, 127, 64, 0U, pam::LaneControlMode::voice).status
        == pam::MappingStatus::unknown_cc, "unknown high CC accepted");
    expect(pam::mapMidiCc(16, -1, 64, 0U, pam::LaneControlMode::voice).status
        == pam::MappingStatus::invalid_message, "negative CC accepted");
    expect(pam::mapMidiCc(16, 20, 128, 0U, pam::LaneControlMode::voice).status
        == pam::MappingStatus::invalid_message, "invalid value accepted");
    expect(pam::mapMidiCc(16, 20, 64, 8U, pam::LaneControlMode::voice).status
        == pam::MappingStatus::invalid_message, "invalid page accepted");
    expect(pam::mapMidiCc(16, 20, 64, 0U,
        static_cast<pam::LaneControlMode>(200U)).status
        == pam::MappingStatus::invalid_message, "invalid mode accepted");
}

void testVoiceTopRow() {
    auto controls = pam::defaultControls();
    controls.selected_page = 3U;
    controls.lane_control_mode = pam::LaneControlMode::voice;
    const auto lanes_before = controls.lanes;
    const auto voices_before = controls.voices;

    auto result = mapped(20, 127, controls);
    expect(result.semantic == pam::SemanticControl::voice_model
        && result.discrete_value == 23U
        && pam::applyMapping(controls, result),
        "Voice Model high endpoint mismatch");
    result = mapped(20, 0, controls);
    expect(result.discrete_value == 0U && pam::applyMapping(controls, result),
        "Voice Model low endpoint mismatch");
    result = mapped(21, 0, controls);
    expect(result.semantic == pam::SemanticControl::voice_pitch
        && result.continuous_value == 24.0F
        && pam::applyMapping(controls, result),
        "Voice Pitch low endpoint mismatch");
    result = mapped(21, 127, controls);
    expect(result.continuous_value == 96.0F
        && pam::applyMapping(controls, result),
        "Voice Pitch high endpoint mismatch");
    for (int cc = 22; cc <= 27; ++cc) {
        const auto low = mapped(cc, 0, controls);
        expect(low.continuous_value == 0.0F
            && pam::applyMapping(controls, low),
            "Voice unit low endpoint mismatch");
        const auto high = mapped(cc, 127, controls);
        expect(high.continuous_value == 1.0F
            && pam::applyMapping(controls, high),
            "Voice unit high endpoint mismatch");
    }
    expect(controls.voices[3].engine == 0U
        && controls.voices[3].note == 96.0F
        && controls.voices[3].harmonics == 1.0F
        && controls.voices[3].timbre == 1.0F
        && controls.voices[3].morph == 1.0F
        && controls.voices[3].decay == 1.0F
        && controls.voices[3].lpg_colour == 1.0F
        && controls.voices[3].level == 1.0F,
        "Voice top row did not target the complete selected voice record");
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        expect(controls.lanes[lane].routes == lanes_before[lane].routes,
            "Voice top row changed motion routes");
        if (lane != 3U) {
            expect(controls.voices[lane].engine == voices_before[lane].engine
                && controls.voices[lane].note == voices_before[lane].note
                && controls.voices[lane].level == voices_before[lane].level,
                "Voice top row changed another voice");
        }
    }
}

void testMotionTopRowAndTriggerBoundary() {
    auto controls = pam::defaultControls();
    controls.selected_page = 4U;
    controls.lane_control_mode = pam::LaneControlMode::motion;
    const auto voices_before = controls.voices;

    for (int value = 0; value <= 127; ++value) {
        const auto trigger = mapped(20, value, controls);
        expect(trigger.semantic == pam::SemanticControl::route_trigger
            && trigger.continuous_value == (value < 64 ? 0.0F : 1.0F),
            "Trigger CC boundary is not 0-63 Off and 64-127 On");
        expect(pam::applyMapping(controls, trigger),
            "Trigger mapping did not dispatch");
        expect(controls.lanes[4].routes[0]
                == (value < 64 ? 0.0F : 1.0F),
            "Trigger route did not retain exact binary state");
    }
    for (int cc = 21; cc <= 27; ++cc) {
        auto low = mapped(cc, 0, controls);
        expect(low.continuous_value == -1.0F,
            "Motion low endpoint mismatch");
        expect(pam::applyMapping(controls, low),
            "Motion low endpoint did not dispatch");
        auto center = mapped(cc, 64, controls);
        expect(center.continuous_value == 0.0F,
            "Motion Direct center mismatch");
        expect(pam::applyMapping(controls, center),
            "Motion center did not dispatch");
        auto high = mapped(cc, 127, controls);
        expect(high.continuous_value == 1.0F,
            "Motion high endpoint mismatch");
        expect(pam::applyMapping(controls, high),
            "Motion high endpoint did not dispatch");
    }
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        expect(controls.voices[lane].engine == voices_before[lane].engine
            && controls.voices[lane].note == voices_before[lane].note
            && controls.voices[lane].level == voices_before[lane].level,
            "Motion top row changed a base voice");
    }
}

void testSequencerBottomRow() {
    for (const auto mode : {
            pam::LaneControlMode::voice,
            pam::LaneControlMode::motion}) {
        auto controls = pam::defaultControls();
        controls.selected_page = 2U;
        controls.lane_control_mode = mode;
        const auto apply = [&controls](int cc, int value) {
            const auto result = mapped(cc, value, controls);
            expect(result.status == pam::MappingStatus::accepted_continuous,
                "lane bottom encoder was not accepted");
            expect(pam::applyMapping(controls, result),
                "lane bottom encoder did not dispatch");
        };
        apply(28, 0);
        expect(controls.lanes[2].rate_index == 0U, "Rate low mismatch");
        apply(28, 127);
        expect(controls.lanes[2].rate_index == 15U, "Rate high mismatch");
        apply(29, 127);
        expect(controls.lanes[2].phase_u7 == 127U, "Phase mismatch");
        apply(30, 127);
        expect(controls.lanes[2].shape == pam::Shape::smooth_random,
            "Shape high mismatch");
        apply(31, 0);
        expect(controls.lanes[2].hits == 0U, "Hits low mismatch");
        apply(31, 127);
        expect(controls.lanes[2].hits == 16U, "Hits high mismatch");
        apply(32, 127);
        expect(controls.lanes[2].rotation == 15U, "Rotation high mismatch");
        apply(33, 0);
        expect(controls.lanes[2].probability == 0.0F,
            "Chance low mismatch");
        apply(33, 127);
        expect(controls.lanes[2].probability == 1.0F,
            "Chance high mismatch");
        apply(34, 0);
        expect(controls.lanes[2].repeat == 0U, "Repeat Free mismatch");
        apply(34, 1);
        expect(controls.lanes[2].repeat == 1U, "Repeat one mismatch");
        apply(34, 127);
        expect(controls.lanes[2].repeat == 64U, "Repeat high mismatch");
        apply(35, 0);
        expect(controls.lanes[2].amplitude == 0.0F, "Depth low mismatch");
        apply(35, 127);
        expect(controls.lanes[2].amplitude == 1.0F, "Depth high mismatch");
        expect(controls.lane_control_mode == mode,
            "bottom row changed Voice/Motion mode");
    }
}

void testGlobalControlsAndNoops() {
    auto controls = pam::defaultControls();
    controls.selected_page = pam::kGlobalPageIndex;
    controls.lane_control_mode = pam::LaneControlMode::motion;
    const auto lanes_before = controls.lanes;
    const auto voices_before = controls.voices;
    const auto apply = [&controls](int cc, int value) {
        const auto result = mapped(cc, value, controls);
        expect(result.status == pam::MappingStatus::accepted_continuous,
            "global encoder was not accepted");
        expect(pam::applyMapping(controls, result),
            "global encoder did not dispatch");
    };
    apply(20, 127);
    apply(21, 127);
    apply(22, 0);
    expect(controls.cohesion.root_note == 24.0F, "Root low mismatch");
    apply(22, 127);
    apply(23, 127);
    apply(24, 127);
    apply(25, 127);
    apply(26, 127);
    apply(27, 127);
    apply(28, 0);
    expect(controls.tempo_milli_bpm == 20000U, "BPM low mismatch");
    apply(28, 127);
    apply(29, 127);
    expect(controls.cohesion.drive == 1.0F
        && controls.cohesion.cohere == 1.0F
        && controls.cohesion.root_note == 84.0F
        && controls.cohesion.spread == 1.0F
        && controls.cohesion.tail == 1.0F
        && controls.cohesion.damping == 1.0F
        && controls.cohesion.width == 1.0F
        && controls.cohesion.duck == 1.0F
        && controls.tempo_milli_bpm == 300000U
        && controls.master_gain == 1.0F,
        "global high endpoint mismatch");

    pam::ControllerAdapter adapter;
    const auto before_noops = controls;
    for (int cc = 30; cc <= 35; ++cc) {
        for (int value = 0; value <= 127; ++value) {
            const auto result = adapter.handleCc(controls, 16, cc, value);
            expect(result.status == pam::MappingStatus::accepted_noop,
                "unassigned Global encoder was not a counted no-op");
        }
    }
    expect(pam::sameControls(controls, before_noops),
        "unassigned Global encoder changed controls");
    expect(adapter.diagnostics().ignored_global_control_count == 6U * 128U,
        "ignored Global diagnostic mismatch");
    expect(controls.lane_control_mode == pam::LaneControlMode::motion,
        "Global edits changed retained lane mode");
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        expect(controls.lanes[lane].routes == lanes_before[lane].routes
            && controls.voices[lane].engine == voices_before[lane].engine
            && controls.voices[lane].note == voices_before[lane].note,
            "global mapping changed lane or voice state");
    }
}

void testButtonEdgesModesAndClear() {
    auto controls = pam::defaultControls();
    pam::ControllerAdapter adapter;

    const auto toggle_motion = adapter.handleCc(controls, 16, 40, 127);
    expect(toggle_motion.status == pam::MappingStatus::accepted_press
        && toggle_motion.semantic == pam::SemanticControl::toggle_lane_mode
        && controls.selected_page == 0U
        && controls.lane_control_mode == pam::LaneControlMode::motion,
        "selected-lane edge did not toggle Motion exactly once");
    const auto hold = adapter.handleCc(controls, 16, 40, 127);
    expect(hold.status == pam::MappingStatus::accepted_hold
        && controls.lane_control_mode == pam::LaneControlMode::motion,
        "duplicate selected-lane press toggled again");
    const auto release = adapter.handleCc(controls, 16, 40, 0);
    expect(release.status == pam::MappingStatus::accepted_release,
        "selected-lane release mismatch");
    const auto toggle_voice = adapter.handleCc(controls, 16, 40, 127);
    expect(toggle_voice.status == pam::MappingStatus::accepted_press
        && controls.lane_control_mode == pam::LaneControlMode::voice,
        "new selected-lane edge did not toggle back to Voice");
    static_cast<void>(adapter.handleCc(controls, 16, 40, 0));

    const auto select_lane = adapter.handleCc(controls, 16, 43, 127);
    expect(select_lane.status == pam::MappingStatus::accepted_press
        && select_lane.semantic == pam::SemanticControl::select_page_4
        && controls.selected_page == 3U
        && controls.lane_control_mode == pam::LaneControlMode::voice,
        "another lane did not select while preserving mode");
    static_cast<void>(adapter.handleCc(controls, 16, 43, 0));
    static_cast<void>(adapter.handleCc(controls, 16, 43, 127));
    expect(controls.selected_page == 3U
        && controls.lane_control_mode == pam::LaneControlMode::motion,
        "selected new lane did not toggle context");
    static_cast<void>(adapter.handleCc(controls, 16, 43, 0));

    const auto enter = adapter.handleCc(controls, 16, 47, 127);
    expect(enter.status == pam::MappingStatus::accepted_press
        && enter.semantic == pam::SemanticControl::select_global
        && controls.selected_page == pam::kGlobalPageIndex
        && controls.lane_control_mode == pam::LaneControlMode::motion
        && controls.effect_clear_generation == 0U,
        "first Global edge did not enter without clearing or preserve mode");
    const auto enter_hold = adapter.handleCc(controls, 16, 47, 127);
    expect(enter_hold.status == pam::MappingStatus::accepted_hold
        && controls.effect_clear_generation == 0U,
        "held Global entry cleared or repeated");
    static_cast<void>(adapter.handleCc(controls, 16, 47, 0));
    const auto clear = adapter.handleCc(controls, 16, 47, 127);
    expect(clear.status == pam::MappingStatus::accepted_press
        && clear.semantic == pam::SemanticControl::clear_fx
        && controls.effect_clear_generation == 1U,
        "second Global edge did not clear once");
    static_cast<void>(adapter.handleCc(controls, 16, 47, 127));
    expect(controls.effect_clear_generation == 1U,
        "held Clear repeated");
}

void testExhaustiveContextualValues() {
    for (const auto mode : {
            pam::LaneControlMode::voice,
            pam::LaneControlMode::motion}) {
        for (std::uint8_t page = 0U; page < pam::kLaneCount; ++page) {
            pam::ControllerAdapter adapter;
            auto controls = pam::defaultControls();
            controls.selected_page = page;
            controls.lane_control_mode = mode;
            for (int cc = 20; cc <= 35; ++cc) {
                for (int value = 0; value <= 127; ++value) {
                    const auto mapping = adapter.handleCc(
                        controls, 16, cc, value);
                    expect(mapping.status
                            == pam::MappingStatus::accepted_continuous,
                        "lane-context encoder value rejected");
                }
            }
            expect(pam::sameControls(controls, pam::sanitizeControls(controls)),
                "lane-context sweep produced invalid controls");
        }
    }

    auto global = pam::defaultControls();
    global.selected_page = pam::kGlobalPageIndex;
    global.lane_control_mode = pam::LaneControlMode::motion;
    pam::ControllerAdapter adapter;
    for (int cc = 20; cc <= 35; ++cc) {
        for (int value = 0; value <= 127; ++value) {
            const auto mapping = adapter.handleCc(global, 16, cc, value);
            expect(mapping.status == (cc <= 29
                    ? pam::MappingStatus::accepted_continuous
                    : pam::MappingStatus::accepted_noop),
                "Global-context encoder status mismatch");
        }
    }
    expect(pam::sameControls(global, pam::sanitizeControls(global)),
        "Global-context sweep produced invalid controls");
}

}  // namespace

int main() {
    testAuthority();
    testChannelsAndUnknown();
    testVoiceTopRow();
    testMotionTopRowAndTriggerBoundary();
    testSequencerBottomRow();
    testGlobalControlsAndNoops();
    testButtonEdgesModesAndClear();
    testExhaustiveContextualValues();
    std::cout << "pamplist_control_map_tests: pass\n";
    return 0;
}
