#include "cinderwheel/ui_model.hpp"
#include "schuss/instrument_lab/ui_projection.hpp"

#include <algorithm>
#include <cmath>

namespace cinderwheel {

namespace {

double clampMidi(double value) noexcept {
    return std::clamp(value, 0.0, 127.0);
}

double valueFor(ControlId id, const StateSnapshot& state) noexcept {
    switch (id) {
        case ControlId::wave_1: return clampMidi(state.stage_values[0] * 127.0);
        case ControlId::wave_2: return clampMidi(state.stage_values[1] * 127.0);
        case ControlId::wave_3: return clampMidi(state.stage_values[2] * 127.0);
        case ControlId::wave_4: return clampMidi(state.stage_values[3] * 127.0);
        case ControlId::rate:
            return clampMidi(127.0 * std::log(std::max(state.rate_hz, 0.08) / 0.08)
                / std::log(75.0));
        case ControlId::memory: return clampMidi(state.memory * 127.0);
        case ControlId::body: return clampMidi(state.body * 127.0);
        case ControlId::position: return clampMidi(state.position * 127.0);
        case ControlId::fx_a: return clampMidi(state.fx_a * 127.0);
        case ControlId::fx_b: return clampMidi(state.fx_b * 127.0);
        case ControlId::root:
            return clampMidi(static_cast<double>(state.root_note - 36) * 127.0 / 36.0);
        case ControlId::undertow:
            return state.undertow_divisor == 0
                ? 0.0
                : clampMidi(1.0 + static_cast<double>(state.undertow_divisor - 1U) * 127.0 / 16.0);
        case ControlId::pulse_divide:
            return clampMidi(static_cast<double>(state.pulse_divide - 1U) * 127.0 / 15.0);
        case ControlId::wake: return clampMidi(state.wake * 127.0);
        case ControlId::structure: return clampMidi(state.structure * 127.0);
        case ControlId::ember: return clampMidi(state.ember * 127.0);
        default: return 0.0;
    }
}

}  // namespace

std::array<double, 16> encoderPresentation(const StateSnapshot& snapshot) noexcept {
    return schuss::instrument_lab::projectControlValues(
        kLaunchControl3Encoders,
        snapshot,
        [](const EncoderDescriptor& descriptor, const StateSnapshot& state) noexcept {
            return valueFor(descriptor.id, state);
        });
}

ButtonPresentation buttonPresentation(
    ControlId id,
    const StateSnapshot& snapshot
) noexcept {
    switch (id) {
        case ControlId::source_scale:
            return {"SOURCE", snapshot.source == SourceMode::reed ? "REED"
                : snapshot.source == SourceMode::rnd ? "RND"
                : snapshot.source == SourceMode::fold ? "FOLD" : "DUST", false};
        case ControlId::mutate: return {"MUTATE", "READY", false};
        case ControlId::lock: return {"LOCK", snapshot.locked ? "ON" : "OFF", snapshot.locked};
        case ControlId::freeze: return {"FREEZE", snapshot.frozen ? "ON" : "OFF", snapshot.frozen};
        case ControlId::fx_mode:
            return {"FX MODE", snapshot.fx_mode == FxMode::clean ? "CLEAN"
                : snapshot.fx_mode == FxMode::filter ? "FILTER" : "DRIVE", false};
        case ControlId::wave_target:
            return {"TARGET", snapshot.wave_target == WaveTarget::pitch ? "PITCH"
                : snapshot.wave_target == WaveTarget::body ? "BODY"
                : snapshot.wave_target == WaveTarget::grain ? "GRAIN" : "ALL", false};
        case ControlId::bloom: return {"BLOOM", snapshot.bloom_armed ? "ARMED" : "OFF", snapshot.bloom_armed};
        case ControlId::reset_panic: return {"RESET", snapshot.panic_latched ? "PANIC" : "READY", snapshot.panic_latched};
        default: return {"CONTROL", "--", false};
    }
}

}  // namespace cinderwheel
