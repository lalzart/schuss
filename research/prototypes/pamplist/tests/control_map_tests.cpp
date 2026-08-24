#include "schuss/pamplist/control_map.hpp"

#include <cmath>
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

void testAuthority() {
    expect(pam::launchControlMidiChannel() == 16U, "MIDI channel drift");
    expect(pam::controlMapSha256()
        == "aa8c59a568c16999f72ef362b639c2d3fa24d02ee81ca47e7a7a9f4e2c096263",
        "control-map fingerprint drift");
    expect(pam::controllerTopologySha256()
        == "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b",
        "controller topology fingerprint drift");
}

void testChannelsAndUnknown() {
    for (int channel = 1; channel <= 16; ++channel) {
        const auto result = pam::mapMidiCc(channel, 20, 64);
        expect(result.status == (channel == 16
            ? pam::MappingStatus::accepted_continuous
            : pam::MappingStatus::ignored_channel),
            "channel filter mismatch");
    }
    expect(pam::mapMidiCc(16, 19, 64).status == pam::MappingStatus::unknown_cc,
        "unknown low CC accepted");
    expect(pam::mapMidiCc(16, 36, 64).status == pam::MappingStatus::unknown_cc,
        "unknown middle CC accepted");
    expect(pam::mapMidiCc(16, 127, 64).status == pam::MappingStatus::unknown_cc,
        "unknown high CC accepted");
    expect(pam::mapMidiCc(16, -1, 64).status
        == pam::MappingStatus::invalid_message, "negative CC accepted");
    expect(pam::mapMidiCc(16, 20, 128).status
        == pam::MappingStatus::invalid_message, "invalid value accepted");
}

void testRoutes() {
    auto controls = pam::defaultControls();
    controls.selected_lane = 3U;
    for (int cc = 20; cc <= 27; ++cc) {
        auto low = pam::mapMidiCc(16, cc, 0);
        expect(low.continuous_value == -1.0F, "route low endpoint mismatch");
        expect(pam::applyMapping(controls, low), "route low did not dispatch");
        expect(controls.lanes[3].routes[cc - 20] == -1.0F,
            "route low application mismatch");
        auto center = pam::mapMidiCc(16, cc, 64);
        expect(center.continuous_value == 0.0F, "route center mismatch");
        expect(pam::applyMapping(controls, center), "route center did not dispatch");
        auto high = pam::mapMidiCc(16, cc, 127);
        expect(high.continuous_value == 1.0F, "route high endpoint mismatch");
        expect(pam::applyMapping(controls, high), "route high did not dispatch");
    }
}

void testLaneFields() {
    auto controls = pam::defaultControls();
    controls.selected_lane = 2U;
    const auto apply = [&controls](int cc, int value) {
        const auto result = pam::mapMidiCc(16, cc, value);
        expect(result.status == pam::MappingStatus::accepted_continuous,
            "lane encoder was not accepted");
        expect(pam::applyMapping(controls, result), "lane encoder did not dispatch");
    };
    apply(28, 0);
    expect(controls.lanes[2].rate_index == 0U, "rate low mismatch");
    apply(28, 127);
    expect(controls.lanes[2].rate_index == 15U, "rate high mismatch");
    apply(29, 127);
    expect(controls.lanes[2].phase_u7 == 127U, "phase mismatch");
    apply(30, 127);
    expect(controls.lanes[2].shape == pam::Shape::smooth_random,
        "shape high mismatch");
    apply(31, 0);
    expect(controls.lanes[2].hits == 0U, "hits low mismatch");
    apply(31, 127);
    expect(controls.lanes[2].hits == 16U, "hits high mismatch");
    apply(32, 127);
    expect(controls.lanes[2].rotation == 15U, "rotation high mismatch");
    apply(33, 0);
    expect(controls.lanes[2].probability == 0.0F, "probability low mismatch");
    apply(33, 127);
    expect(controls.lanes[2].probability == 1.0F, "probability high mismatch");
    apply(34, 0);
    expect(controls.lanes[2].repeat == 0U, "repeat free mismatch");
    apply(34, 1);
    expect(controls.lanes[2].repeat == 1U, "repeat one mismatch");
    apply(34, 127);
    expect(controls.lanes[2].repeat == 64U, "repeat high mismatch");
    apply(35, 0);
    expect(controls.lanes[2].amplitude == 0.0F, "amplitude low mismatch");
    apply(35, 127);
    expect(controls.lanes[2].amplitude == 1.0F, "amplitude high mismatch");
}

void testButtonEdgesAndDiagnostics() {
    auto controls = pam::defaultControls();
    pam::ControllerAdapter adapter;
    for (int lane = 0; lane < 8; ++lane) {
        const auto press = adapter.handleCc(controls, 16, 40 + lane, 127);
        expect(press.status == pam::MappingStatus::accepted_press,
            "button press mismatch");
        expect(controls.selected_lane == lane, "button selection mismatch");
        const auto hold = adapter.handleCc(controls, 16, 40 + lane, 127);
        expect(hold.status == pam::MappingStatus::accepted_hold,
            "duplicate press did not become hold");
        const auto release = adapter.handleCc(controls, 16, 40 + lane, 0);
        expect(release.status == pam::MappingStatus::accepted_release,
            "button release mismatch");
        expect(controls.selected_lane == lane, "release changed selection");
    }
    static_cast<void>(adapter.handleCc(controls, 1, 20, 64));
    static_cast<void>(adapter.handleCc(controls, 16, 39, 64));
    static_cast<void>(adapter.handleCc(controls, 16, 20, 200));
    expect(adapter.diagnostics().accepted_message_count == 24U,
        "accepted message count mismatch");
    expect(adapter.diagnostics().dispatched_message_count == 8U,
        "dispatched message count mismatch");
    expect(adapter.diagnostics().ignored_channel_count == 1U,
        "ignored channel count mismatch");
    expect(adapter.diagnostics().unknown_cc_count == 1U,
        "unknown CC count mismatch");
    expect(adapter.diagnostics().invalid_message_count == 1U,
        "invalid message count mismatch");
}

void testExhaustiveValues() {
    auto controls = pam::defaultControls();
    pam::ControllerAdapter adapter;
    for (int cc = 20; cc <= 35; ++cc) {
        for (int value = 0; value <= 127; ++value) {
            const auto mapping = adapter.handleCc(controls, 16, cc, value);
            expect(mapping.status == pam::MappingStatus::accepted_continuous,
                "assigned encoder value rejected");
        }
    }
    const auto sanitized = pam::sanitizeControls(controls);
    expect(pam::sameControls(controls, sanitized),
        "exhaustive controller sweep produced invalid controls");
}

}  // namespace

int main() {
    testAuthority();
    testChannelsAndUnknown();
    testRoutes();
    testLaneFields();
    testButtonEdgesAndDiagnostics();
    testExhaustiveValues();
    std::cout << "pamplist_control_map_tests: pass\n";
    return 0;
}
