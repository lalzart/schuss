#include "schuss/generative_drum_machine/control_map.hpp"

#include <array>
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

bool sameState(
    const schuss::generative_drum_machine::Controls& left,
    const schuss::generative_drum_machine::Controls& right) {
    using schuss::generative_drum_machine::sameSoundControls;
    return sameSoundControls(left, right)
        && left.selected_voice_lane == right.selected_voice_lane
        && left.voice_shaping == right.voice_shaping;
}

}  // namespace

int main() {
    using namespace schuss::generative_drum_machine;

    expect(launchControlMidiChannel() == 16, "MIDI channel is 16");
    expect(encoderDescriptors().size() == 16, "regular LC3 has 16 encoder descriptors");
    expect(buttonDescriptors().size() == 8, "regular LC3 has eight button descriptors");
    expect(controlMapSha256().size() == 64, "control-map fingerprint exposed");
    expect(
        controllerTopologySha256()
            == "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b",
        "exact Tide Pit regular LC3 topology fingerprint exposed");

    const std::array<ControlId, 16> encoder_ids{{
        ControlId::complexity_kick,
        ControlId::complexity_snare,
        ControlId::complexity_hat,
        ControlId::complexity_percussion_1,
        ControlId::complexity_percussion_2,
        ControlId::complexity_percussion_3,
        ControlId::enthusiasm,
        ControlId::tempo_milli_bpm,
        ControlId::shape_tune,
        ControlId::shape_timbre,
        ControlId::shape_color,
        ControlId::shape_decay,
        ControlId::shape_pitch_env,
        ControlId::shape_level,
        ControlId::swing_u15,
        ControlId::rhythm_select,
    }};

    for (std::uint8_t cc = 20; cc <= 35; ++cc) {
        const auto* descriptor = encoderDescriptor(cc);
        expect(descriptor != nullptr, "assigned encoder descriptor lookup");
        if (descriptor != nullptr) {
            expect(descriptor->id == encoder_ids[cc - 20], "assigned encoder semantic ID");
            expect(descriptor->kind == ControlKind::continuous, "assigned encoder is continuous");
        }
        for (unsigned value = 0; value <= 127; ++value) {
            const auto mapping = mapMidiCc(16, cc, static_cast<std::uint8_t>(value));
            const auto expected = cc <= 26
                ? (value * 65535U + 63U) / 127U
                : cc == 27
                    ? 30000U + (value * 210000U + 63U) / 127U
                    : cc == 34
                        ? (value * 32767U + 63U) / 127U
                        : cc == 35
                            ? (value * 14U + 63U) / 127U
                            : value;
            expect(mapping.status == MappingStatus::accepted_continuous, "encoder value accepted");
            expect(mapping.id == encoder_ids[cc - 20], "encoder mapped to public semantic ID");
            expect(mapping.mapped_value == expected, "encoder uses its frozen integer map");
            expect(mapping.dispatchesSemantic(), "continuous selector dispatches to reducer");
        }
    }

    const std::array<ControlId, 8> button_ids{{
        ControlId::shape_select_kick,
        ControlId::shape_select_snare,
        ControlId::shape_select_hat,
        ControlId::shape_select_percussion_1,
        ControlId::shape_select_percussion_2,
        ControlId::shape_select_percussion_3,
        ControlId::fill,
        ControlId::rhythm_next,
    }};
    for (std::uint8_t cc = 40; cc <= 47; ++cc) {
        const auto* descriptor = buttonDescriptor(cc);
        expect(descriptor != nullptr, "assigned button descriptor lookup");
        if (descriptor != nullptr) {
            expect(descriptor->id == button_ids[cc - 40], "assigned button semantic ID");
            expect(descriptor->kind == ControlKind::action, "assigned button is action");
        }
        for (unsigned value = 0; value <= 127; ++value) {
            const auto mapping = mapMidiCc(16, cc, static_cast<std::uint8_t>(value));
            if (value == 127) {
                expect(mapping.status == MappingStatus::accepted_action_press, "button press accepted");
                expect(mapping.mapped_value == 1U, "button press has one-shot value");
                expect(mapping.dispatchesSemantic(), "button press dispatches");
            } else if (value == 0) {
                expect(mapping.status == MappingStatus::accepted_action_release, "button release accepted");
                expect(!mapping.dispatchesSemantic(), "button release cannot double-dispatch");
            } else {
                expect(mapping.status == MappingStatus::invalid_value, "intermediate button value fails closed");
            }
        }
    }

    for (unsigned channel : {0U, 1U, 8U, 15U, 17U}) {
        for (unsigned cc = 20; cc <= 47; ++cc) {
            for (unsigned value = 0; value <= 127; ++value) {
                expect(
                    mapMidiCc(
                        static_cast<std::uint8_t>(channel),
                        static_cast<std::uint8_t>(cc),
                        static_cast<std::uint8_t>(value)).status
                        == MappingStatus::ignored_channel,
                    "wrong channel is classified before selector handling");
            }
        }
    }

    for (unsigned cc = 0; cc <= 127; ++cc) {
        const bool known = (cc >= 20 && cc <= 35) || (cc >= 40 && cc <= 47);
        if (!known) {
            for (unsigned value = 0; value <= 127; ++value) {
                expect(
                    mapMidiCc(16, static_cast<std::uint8_t>(cc), static_cast<std::uint8_t>(value)).status
                        == MappingStatus::unknown_controller,
                    "unknown selector remains distinct");
            }
        }
        for (unsigned value = 128; value <= 255; ++value) {
            expect(
                mapMidiCc(16, static_cast<std::uint8_t>(cc), static_cast<std::uint8_t>(value)).status
                    == MappingStatus::invalid_value,
                "out-of-range MIDI value fails closed for every selector");
        }
    }

    Controls initial{};
    initial.complexity = {{101U, 202U, 303U, 404U, 505U, 606U}};
    initial.enthusiasm = 707U;
    initial.tempo_milli_bpm = 120000U;
    initial.swing_u15 = 808U;
    for (std::uint8_t cc = 20; cc <= 27; ++cc) {
        auto actual = initial;
        auto expected = initial;
        bool fill = false;
        const auto mapping = mapMidiCc(16, cc, 93);
        switch (cc) {
            case 20: expected.complexity[0] = static_cast<std::uint16_t>(mapping.mapped_value); break;
            case 21: expected.complexity[1] = static_cast<std::uint16_t>(mapping.mapped_value); break;
            case 22: expected.complexity[2] = static_cast<std::uint16_t>(mapping.mapped_value); break;
            case 23: expected.complexity[3] = static_cast<std::uint16_t>(mapping.mapped_value); break;
            case 24: expected.complexity[4] = static_cast<std::uint16_t>(mapping.mapped_value); break;
            case 25: expected.complexity[5] = static_cast<std::uint16_t>(mapping.mapped_value); break;
            case 26: expected.enthusiasm = static_cast<std::uint16_t>(mapping.mapped_value); break;
            case 27: expected.tempo_milli_bpm = mapping.mapped_value; break;
            default: break;
        }
        expect(applyMapping(actual, fill, mapping), "accepted performance encoder applies");
        expect(sameState(actual, expected), "performance mapping changes only its named field");
        expect(!fill, "continuous mapping cannot queue fill");
    }
    {
        auto actual = initial;
        bool action = false;
        const auto swing = mapMidiCc(16, 34, 93);
        expect(applyMapping(actual, action, swing), "swing encoder applies");
        expect(actual.swing_u15 == swing.mapped_value, "swing changes only accepted swing");
        const auto rhythm = mapMidiCc(16, 35, 93);
        expect(applyMapping(actual, action, rhythm), "direct rhythm encoder applies");
        expect(actual.rhythm_preset == rhythm.mapped_value, "direct rhythm index is accepted");
        expect(actual.rhythm_preset < kRhythmPresetCount, "direct rhythm index stays in bank");
    }

    auto controls = initial;
    bool fill = false;
    expect(!applyMapping(controls, fill, mapMidiCc(16, 28, 127)),
        "shape encoder is a semantic no-op without selected shaping lane");
    expect(sameState(controls, initial), "inactive shape encoder preserves state");

    expect(applyMapping(controls, fill, mapMidiCc(16, 40, 127)), "kick shaping selection applies");
    expect(controls.voice_shaping && controls.selected_voice_lane == 0U,
        "kick shaping selection enters mode");
    const auto focus_only = controls;
    expect(sameSoundControls(initial, focus_only), "focus-only selection does not change sound controls");
    for (std::uint8_t cc = 28; cc <= 33; ++cc) {
        const auto before = controls;
        expect(applyMapping(controls, fill, mapMidiCc(16, cc, 93)), "selected-lane shape applies");
        expect(!sameSoundControls(before, controls), "shape edit changes sound controls");
        expect(controls.voice_shapes[1].tune_u7 == 64U, "shape edit cannot leak to another lane");
    }
    expect(controls.voice_shapes[0].tune_u7 == 93U, "tune stored for selected lane");
    expect(controls.voice_shapes[0].level_u7 == 93U, "level stored for selected lane");

    const auto shaped = controls;
    expect(applyMapping(controls, fill, mapMidiCc(16, 41, 127)), "snare selection applies");
    expect(controls.voice_shaping && controls.selected_voice_lane == 1U,
        "selection moves directly to snare");
    expect(sameSoundControls(shaped, controls), "moving focus does not mutate shape banks");
    expect(applyMapping(controls, fill, mapMidiCc(16, 41, 127)), "selected lane press toggles mode");
    expect(!controls.voice_shaping, "second selected-lane press exits shaping");
    expect(!applyMapping(controls, fill, mapMidiCc(16, 41, 0)), "button release does not toggle twice");

    const auto before_rhythm = controls;
    expect(applyMapping(controls, fill, mapMidiCc(16, 47, 127)), "rhythm advance applies");
    expect(controls.rhythm_preset == 1U, "rhythm advances once");
    expect(!applyMapping(controls, fill, mapMidiCc(16, 47, 0)), "rhythm release does not advance");
    expect(controls.rhythm_preset == 1U, "rhythm release preserves index");
    controls.rhythm_preset = static_cast<std::uint8_t>(kRhythmPresetCount - 1U);
    expect(applyMapping(controls, fill, mapMidiCc(16, 47, 127)), "rhythm wrap applies");
    expect(controls.rhythm_preset == 0U, "rhythm wraps modulo bank size");
    controls = before_rhythm;

    expect(applyMapping(controls, fill, mapMidiCc(16, 46, 127)), "fill press applies");
    expect(fill, "fill press queues one semantic action");
    fill = false;
    expect(!applyMapping(controls, fill, mapMidiCc(16, 46, 0)), "fill release does not apply twice");
    expect(!fill, "fill release preserves token state");
    expect(!applyMapping(controls, fill, mapMidiCc(1, 20, 127)), "wrong channel cannot apply");
    expect(!applyMapping(controls, fill, mapMidiCc(16, 39, 127)), "unknown selector cannot apply");

    const auto before_forged = controls;
    expect(
        !applyMapping(
            controls,
            fill,
            MappingResult{
                MappingStatus::accepted_continuous,
                ControlId::complexity_kick,
                65536U,
                127U}),
        "forged out-of-domain continuous result fails closed");
    expect(sameState(controls, before_forged) && !fill, "forged result preserves public state");

    if (failures != 0) {
        std::cerr << failures << " control-map test(s) failed\n";
        return 1;
    }
    std::cout << "Generative drum-machine LC3 control-map tests passed\n";
    return 0;
}
