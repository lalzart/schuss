#include "tidepit/control_map.hpp"

#include <array>
#include <cmath>
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

bool close(double lhs, double rhs) {
    return std::abs(lhs - rhs) <= 1.0e-6;
}

}  // namespace

int main() {
    using namespace tidepit;

    expect(launchControlMidiChannel() == 16, "MIDI channel is 16");
    expect(encoderDescriptors().size() == 16, "16 encoder descriptors");
    expect(buttonDescriptors().size() == 8, "8 button descriptors");
    expect(controlMapSha256().size() == 64, "control-map fingerprint exposed");
    expect(controllerTopologySha256() == "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b", "topology fingerprint exposed");

    const std::array<ControlId, 11> encoder_ids{{
        ControlId::set_stage_1,
        ControlId::set_stage_2,
        ControlId::set_stage_3,
        ControlId::set_stage_4,
        ControlId::set_rate,
        ControlId::set_memory,
        ControlId::set_material,
        ControlId::set_position,
        ControlId::set_fx_a,
        ControlId::set_fx_b,
        ControlId::set_root,
    }};
    for (std::uint8_t cc = 20; cc <= 30; ++cc) {
        const auto* descriptor = encoderDescriptor(cc);
        expect(descriptor != nullptr, "assigned encoder descriptor lookup");
        if (descriptor != nullptr) {
            expect(descriptor->id == encoder_ids[cc - 20], "assigned encoder semantic ID");
            expect(descriptor->adapter_owned_default, "assigned encoder has adapter default");
        }
        for (unsigned value = 0; value <= 127; ++value) {
            const auto mapping = mapMidiCc(16, cc, static_cast<std::uint8_t>(value));
            expect(mapping.status == MappingStatus::accepted_continuous, "encoder value accepted");
            expect(mapping.id == encoder_ids[cc - 20], "encoder mapping semantic ID");
            expect(close(mapping.normalized_value, static_cast<double>(value) / 127.0), "encoder normalized mapping");
            if (cc == 30) {
                const auto expected_root = 36 + static_cast<std::int32_t>((value * 36U + 63U) / 127U);
                expect(mapping.root_note == expected_root, "root round-half-up mapping");
            } else {
                expect(mapping.root_note == 0, "non-root mapping has no root note");
            }
            expect(mapping.dispatchesCoreEvent(), "continuous mapping dispatches a Core event");
        }
    }

    for (std::uint8_t cc = 31; cc <= 35; ++cc) {
        const auto* descriptor = encoderDescriptor(cc);
        expect(descriptor != nullptr, "unassigned encoder descriptor exists");
        expect(descriptor != nullptr && descriptor->label == "UNASSIGNED", "unassigned encoder is visible");
        expect(mapMidiCc(16, cc, 0).status == MappingStatus::unassigned, "unassigned encoder is counted separately");
        expect(mapMidiCc(16, cc, 127).status == MappingStatus::unassigned, "unassigned encoder full range remains unassigned");
    }

    const std::array<ControlId, 7> button_ids{{
        ControlId::source_next,
        ControlId::mutate,
        ControlId::lock_toggle,
        ControlId::capture_toggle,
        ControlId::effect_next,
        ControlId::target_next,
        ControlId::scale_next,
    }};
    for (std::uint8_t cc = 40; cc <= 46; ++cc) {
        const auto* descriptor = buttonDescriptor(cc);
        expect(descriptor != nullptr, "assigned button descriptor lookup");
        if (descriptor != nullptr) {
            expect(descriptor->id == button_ids[cc - 40], "assigned button semantic ID");
            expect(descriptor->press_value == 127 && descriptor->release_value == 0, "button is momentary 127/0");
        }
        const auto press = mapMidiCc(16, cc, 127);
        const auto release = mapMidiCc(16, cc, 0);
        expect(press.status == MappingStatus::accepted_action_press, "button press accepted");
        expect(release.status == MappingStatus::accepted_action_release, "button release accepted");
        expect(press.dispatchesCoreEvent(), "button press dispatches Core event");
        expect(!release.dispatchesCoreEvent(), "button release does not double-dispatch semantic action");
        expect(mapMidiCc(16, cc, 64).status == MappingStatus::invalid_value, "non-momentary button value rejected");
    }

    expect(buttonDescriptor(47) != nullptr, "unassigned button descriptor exists");
    expect(buttonDescriptor(47)->label == "UNASSIGNED", "unassigned button is visible");
    expect(mapMidiCc(16, 47, 127).status == MappingStatus::unassigned, "CC47 is declared unassigned");
    expect(mapMidiCc(16, 39, 127).status == MappingStatus::unknown_controller, "unknown CC distinct from unassigned");
    expect(mapMidiCc(16, 48, 127).status == MappingStatus::unknown_controller, "unknown CC above surface distinct from unassigned");
    expect(mapMidiCc(1, 20, 127).status == MappingStatus::ignored_channel, "wrong channel ignored separately");
    expect(mapMidiCc(16, 20, 128).status == MappingStatus::invalid_value, "invalid encoder value rejected");
    expect(mapMidiCc(16, 40, 128).status == MappingStatus::invalid_value, "invalid button value rejected");

    for (const auto& descriptor : encoderDescriptors()) {
        const auto action = semanticAction(descriptor.id);
        expect(action.has_value() == (descriptor.kind != ControlKind::unassigned), "encoder semantic bridge coverage");
    }
    for (const auto& descriptor : buttonDescriptors()) {
        const auto action = semanticAction(descriptor.id);
        expect(action.has_value() == (descriptor.kind != ControlKind::unassigned), "button semantic bridge coverage");
    }
    expect(!semanticAction(ControlId::unassigned).has_value(), "unassigned never becomes Core action");

    const auto preset = adapterOwnedDesktopAuditionPreset();
    expect(close(preset.stages[0], 0.20), "adapter preset stage 1");
    expect(close(preset.stages[1], 0.50), "adapter preset stage 2");
    expect(close(preset.stages[2], 0.80), "adapter preset stage 3");
    expect(close(preset.stages[3], 0.30), "adapter preset stage 4");
    expect(close(preset.rate, 0.55), "adapter preset rate");
    expect(close(preset.memory, 0.78), "adapter preset memory");
    expect(close(preset.material, 0.50), "adapter preset material");
    expect(close(preset.position, 0.31), "adapter preset position");
    expect(close(preset.fx_a, 0.60), "adapter preset FX-A");
    expect(close(preset.fx_b, 0.35), "adapter preset FX-B");
    expect(preset.root_note == 60, "adapter preset root C4");

    const Controls declared_core_startup{};
    expect(declared_core_startup.stages == preset.stages, "declared Core stages equal map-generated adapter preset");
    expect(declared_core_startup.rate == preset.rate, "declared Core rate equals map-generated adapter preset");
    expect(declared_core_startup.memory == preset.memory, "declared Core memory equals map-generated adapter preset");
    expect(declared_core_startup.material == preset.material, "declared Core material equals map-generated adapter preset");
    expect(declared_core_startup.position == preset.position, "declared Core position equals map-generated adapter preset");
    expect(declared_core_startup.fx_a == preset.fx_a, "declared Core FX-A equals map-generated adapter preset");
    expect(declared_core_startup.fx_b == preset.fx_b, "declared Core FX-B equals map-generated adapter preset");
    expect(declared_core_startup.root_note == preset.root_note, "declared Core root equals map-generated adapter preset");

    Core core;
    expect(core.prepare(kReferenceSampleRate, kReferenceQuantumFrames), "Core prepares for startup parity test");
    const auto runtime_startup = core.snapshot().controls;
    expect(runtime_startup.stages == preset.stages, "runtime Core stages equal map-generated adapter preset");
    expect(runtime_startup.rate == preset.rate, "runtime Core rate equals map-generated adapter preset");
    expect(runtime_startup.memory == preset.memory, "runtime Core memory equals map-generated adapter preset");
    expect(runtime_startup.material == preset.material, "runtime Core material equals map-generated adapter preset");
    expect(runtime_startup.position == preset.position, "runtime Core position equals map-generated adapter preset");
    expect(runtime_startup.fx_a == preset.fx_a, "runtime Core FX-A equals map-generated adapter preset");
    expect(runtime_startup.fx_b == preset.fx_b, "runtime Core FX-B equals map-generated adapter preset");
    expect(runtime_startup.root_note == preset.root_note, "runtime Core root equals map-generated adapter preset");

    if (failures != 0) {
        std::cerr << failures << " control-map test(s) failed\n";
        return 1;
    }
    std::cout << "Tide Pit control-map tests passed\n";
    return 0;
}
