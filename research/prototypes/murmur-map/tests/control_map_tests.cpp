#include "schuss/murmur_map/control_map.hpp"

#include <cmath>
#include <cstdint>
#include <iostream>
#include <string_view>

namespace mm = schuss::murmur_map;

namespace {
int failures = 0;
void expect(bool condition, std::string_view message) {
    if (!condition) { std::cerr << "FAIL: " << message << '\n'; ++failures; }
}
std::int32_t halfUp(std::uint8_t value, std::int32_t span, std::int32_t offset = 0) {
    return offset + static_cast<std::int32_t>((static_cast<std::int64_t>(value) * span + 63) / 127);
}
}

int main() {
    expect(mm::launchControlMidiChannel() == 16U, "LC3 uses channel 16");
    expect(mm::encoderDescriptors().size() == 16U, "regular LC3 has 16 encoders");
    expect(mm::buttonDescriptors().size() == 8U, "regular LC3 has eight buttons");
    expect(mm::controlMapSha256() == "b4bfd6692895f35dadf78ac3acf478552b074cbbe9972b8315a3d1158f9a9b15",
        "control map fingerprint exposed");
    expect(mm::controllerTopologySha256() == "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b",
        "controller topology fingerprint exposed");

    for (std::uint8_t cc = 20U; cc <= 35U; ++cc) {
        expect(mm::encoderDescriptor(cc) != nullptr, "every encoder CC assigned");
        for (unsigned value = 0U; value <= 127U; ++value) {
            const auto mapping = mm::mapMidiCc(16U, cc, static_cast<std::uint8_t>(value));
            expect(mapping.status == mm::MappingStatus::accepted_continuous,
                "every 7-bit encoder value accepted");
            std::int32_t expected = 0;
            switch (cc) {
                case 20: expected = halfUp(value, 210000, 30000); break;
                case 21: expected = static_cast<std::int32_t>(std::lround(250.0 * std::pow(32.0, value / 127.0))); break;
                case 22: case 24: case 25: case 26: case 27:
                case 29: case 30: case 31: expected = halfUp(value, 32767); break;
                case 23: expected = halfUp(value, 30, 2); break;
                case 28: expected = halfUp(value, 48, -24); break;
                case 32: expected = static_cast<std::int32_t>(std::lround(40.0 * std::pow(100.0, value / 127.0))); break;
                case 33: expected = halfUp(value, 54000, -60000); break;
                case 34: expected = halfUp(value, 65534, -32767); break;
                case 35: expected = halfUp(value, 60, 24); break;
                default: break;
            }
            expect(mapping.mapped_value == expected, "encoder uses frozen transform");
        }
    }
    for (std::uint8_t cc = 40U; cc <= 47U; ++cc) {
        expect(mm::buttonDescriptor(cc) != nullptr, "every button CC assigned");
        expect(mm::mapMidiCc(16U, cc, 127U).status == mm::MappingStatus::accepted_action_press,
            "button press accepted");
        expect(mm::mapMidiCc(16U, cc, 0U).status == mm::MappingStatus::accepted_action_release,
            "button release accepted");
        expect(mm::mapMidiCc(16U, cc, 64U).status == mm::MappingStatus::invalid_value,
            "intermediate button value rejected");
    }
    for (unsigned channel = 1U; channel <= 16U; ++channel) {
        if (channel == 16U) continue;
        expect(mm::mapMidiCc(static_cast<std::uint8_t>(channel), 20U, 127U).status
                == mm::MappingStatus::ignored_channel,
            "wrong MIDI channel ignored");
    }
    expect(mm::mapMidiCc(16U, 19U, 127U).status == mm::MappingStatus::unknown_controller,
        "unknown CC remains distinct");
    expect(mm::mapMidiCc(16U, 20U, 128U).status == mm::MappingStatus::invalid_value,
        "out-of-range MIDI value rejected");

    auto state = mm::defaultControllerState();
    const auto accepted_before = state.controls;
    expect(mm::applyMapping(state, mm::mapMidiCc(16U, 40U, 127U)).handled,
        "waypoint selection handled");
    expect(mm::applyMapping(state, mm::mapMidiCc(16U, 44U, 127U)).handled,
        "lane selection handled");
    const auto edit = mm::applyMapping(state, mm::mapMidiCc(16U, 30U, 127U));
    expect(edit.draft_changed && !edit.controls_changed, "draft encoder is not accepted sound state");
    expect(mm::sameControls(state.controls, accepted_before), "draft edit preserves accepted controls");
    const auto capture = mm::applyMapping(state, mm::mapMidiCc(16U, 47U, 127U));
    expect(capture.captured && capture.controls_changed, "capture publishes complete draft");
    expect(!mm::sameControls(state.controls, accepted_before), "capture changes accepted controls");
    expect(!mm::applyMapping(state, mm::mapMidiCc(16U, 47U, 0U)).controls_changed,
        "capture release does not apply twice");
    expect(mm::validControls(state.controls), "mapped state remains valid");

    static_cast<void>(mm::applyMapping(state, mm::mapMidiCc(16U, 29U, 0U)));
    const auto discards = state.editor.draft_discard_count;
    static_cast<void>(mm::applyMapping(state, mm::mapMidiCc(16U, 41U, 127U)));
    expect(state.editor.draft_discard_count == discards + 1U,
        "selection change explicitly discards dirty draft");

    if (failures != 0) { std::cerr << failures << " control-map test(s) failed\n"; return 1; }
    std::cout << "Murmur Map Launch Control 3 tests passed\n";
    return 0;
}
