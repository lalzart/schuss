#include "schuss/generative_drum_machine/ui_model.hpp"

#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

int failures = 0;

void expect(bool condition, std::string_view message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

}  // namespace

int main() {
    using namespace schuss::generative_drum_machine;

    const auto controls = desktopAuditionControls();
    expect(controls.complexity == std::array<std::uint16_t, 6>{{
        42000U, 36000U, 34000U, 30000U, 26000U, 22000U}},
        "desktop preset carries six map-owned lane defaults");
    expect(controls.enthusiasm == 22000U, "desktop enthusiasm default");
    expect(controls.tempo_milli_bpm == 120000U, "desktop tempo default");
    expect(controls.swing_u15 == 4096U, "desktop swing default");
    expect(controls.rhythm_preset == 0U, "desktop rhythm starts at First Light");
    expect(!controls.voice_shaping, "desktop shaping starts inactive");

    for (const auto& descriptor : kLaneUiControls) {
        const auto midi = midiValueForAcceptedState(descriptor.id, controls);
        const auto mapped = mapMidiCc(16U, descriptor.cc, midi);
        expect(mapped.accepted(), "lane presentation MIDI value maps back through authority");
        const auto target = acceptedValue(descriptor.id, controls);
        const auto step = 65535U / 127U + 1U;
        const auto distance = mapped.mapped_value > target
            ? mapped.mapped_value - target
            : target - mapped.mapped_value;
        expect(distance <= step / 2U + 1U, "lane inverse presentation is nearest 7-bit value");
        expect(!formatAcceptedValue(descriptor.id, controls).empty(), "lane value formats");
    }

    for (const auto& descriptor : kGlobalUiControls) {
        const auto midi = midiValueForAcceptedState(descriptor.id, controls);
        const auto mapped = mapMidiCc(16U, descriptor.cc, midi);
        expect(mapped.accepted(), "global presentation MIDI value maps back through authority");
        expect(!formatAcceptedValue(descriptor.id, controls).empty(), "global value formats");
    }

    auto shaped = controls;
    shaped.voice_shaping = true;
    shaped.selected_voice_lane = 2U;
    shaped.voice_shapes[2].tune_u7 = 91U;
    shaped.voice_shapes[2].decay_u7 = 32U;
    for (const auto& descriptor : kShapeUiControls) {
        const auto midi = midiValueForAcceptedState(descriptor.id, shaped);
        expect(midi == acceptedValue(descriptor.id, shaped),
            "shape presentation uses exact U7 accepted state");
        expect(!formatAcceptedValue(descriptor.id, shaped).empty(), "shape value formats");
    }

    expect(formatAcceptedValue(ControlId::tempo_milli_bpm, controls) == "120.0 BPM", "tempo text");
    expect(formatAcceptedValue(ControlId::fill, controls) == "TRIGGER", "fill text");
    expect(formatAcceptedValue(ControlId::unassigned, controls) == "--", "unassigned text");
    expect(modelName(Lane::kick) == "KICK", "kick model label");
    expect(modelName(Lane::snare) == "SNARE", "snare model label");
    expect(modelName(Lane::hat) == "CYMBAL", "hat model label");
    expect(rhythmLabel(0U) == "First Light  4/4", "First Light rhythm label");
    expect(rhythmLabel(1U) == "Three Turn  3/4", "three-four rhythm label");
    expect(formatAcceptedValue(ControlId::shape_timbre, controls) == "+0%",
        "neutral shape is visibly neutral");

    if (failures != 0) {
        std::cerr << failures << " UI-model test(s) failed\n";
        return 1;
    }
    std::cout << "Generative drum-machine UI-model tests passed\n";
    return 0;
}
