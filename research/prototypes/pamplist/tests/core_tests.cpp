#include "schuss/pamplist/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace pam = schuss::pamplist;

namespace {

[[noreturn]] void fail(const std::string& message) {
    std::cerr << "pamplist_core_tests: " << message << '\n';
    std::exit(1);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

struct Rendered final {
    std::vector<std::int32_t> main;
    std::vector<std::int32_t> auxiliary;
    std::vector<pam::QuantumEvent> events;
    pam::Snapshot snapshot{};
};

Rendered render(
    const pam::Controls& controls,
    std::size_t frames,
    std::size_t block) {
    pam::Core core;
    Rendered result{};
    result.main.resize(frames);
    result.auxiliary.resize(frames);
    std::size_t cursor = 0U;
    while (cursor < frames) {
        const auto count = std::min(block, frames - cursor);
        pam::ProcessReport report{};
        expect(core.process(
            controls,
            result.main.data() + cursor,
            result.auxiliary.data() + cursor,
            count,
            &report), "supported process rejected");
        for (std::size_t event = 0; event < report.event_count; ++event) {
            result.events.push_back(report.events[event]);
        }
        cursor += count;
    }
    result.snapshot = core.snapshot();
    return result;
}

bool sameEvent(const pam::QuantumEvent& left, const pam::QuantumEvent& right) {
    return left.absolute_frame == right.absolute_frame
        && left.boundary_mask == right.boundary_mask
        && left.accepted_mask == right.accepted_mask
        && left.trigger_lane_mask == right.trigger_lane_mask
        && left.started_lane_mask == right.started_lane_mask
        && left.effect_cleared == right.effect_cleared
        && left.effect_clear_generation == right.effect_clear_generation
        && left.resolved_engines == right.resolved_engines
        && left.steps == right.steps
        && left.addresses == right.addresses;
}

bool sameVoice(
    const pam::VoiceControls& left,
    const pam::VoiceControls& right) {
    return left.engine == right.engine
        && left.note == right.note
        && left.harmonics == right.harmonics
        && left.timbre == right.timbre
        && left.morph == right.morph
        && left.decay == right.decay
        && left.lpg_colour == right.lpg_colour
        && left.level == right.level;
}

bool allZero(const std::vector<std::int32_t>& values) {
    return std::all_of(values.begin(), values.end(), [](std::int32_t value) {
        return value == 0;
    });
}

double normalizedStereoRmsDifference(
    const Rendered& left,
    const Rendered& right) {
    expect(left.main.size() == right.main.size()
            && left.auxiliary.size() == right.auxiliary.size()
            && left.main.size() == left.auxiliary.size(),
        "RMS difference input sizes disagree");
    long double energy = 0.0L;
    for (std::size_t frame = 0; frame < left.main.size(); ++frame) {
        const auto main = static_cast<long double>(left.main[frame])
            - static_cast<long double>(right.main[frame]);
        const auto auxiliary = static_cast<long double>(left.auxiliary[frame])
            - static_cast<long double>(right.auxiliary[frame]);
        energy += main * main + auxiliary * auxiliary;
    }
    const auto denominator = 2.0L
        * static_cast<long double>(left.main.size())
        * 134217728.0L * 134217728.0L;
    return std::sqrt(static_cast<double>(energy / denominator));
}

std::vector<std::uint64_t> laneTriggerFrames(
    const Rendered& rendered,
    std::size_t lane) {
    std::vector<std::uint64_t> result;
    for (const auto& event : rendered.events) {
        if ((event.trigger_lane_mask & (1U << lane)) != 0U) {
            result.push_back(event.absolute_frame);
        }
    }
    return result;
}

pam::Controls sevenVoiceControls() {
    auto controls = pam::defaultControls();
    const std::array<pam::Shape, pam::kLaneCount> shapes{{
        pam::Shape::pulse,
        pam::Shape::triangle,
        pam::Shape::sine,
        pam::Shape::ramp,
        pam::Shape::exponential_decay,
        pam::Shape::sample_hold,
        pam::Shape::smooth_random,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> rates{{
        8U, 10U, 6U, 11U, 4U, 12U, 2U,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> models{{
        0U, 3U, 6U, 9U, 12U, 15U, 21U,
    }};
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        controls.lanes[lane].shape = shapes[lane];
        controls.lanes[lane].rate_index = rates[lane];
        controls.lanes[lane].phase_u7 = static_cast<std::uint8_t>(lane * 13U);
        controls.lanes[lane].hits = static_cast<std::uint8_t>(5U + lane);
        controls.lanes[lane].rotation = static_cast<std::uint8_t>(lane * 2U);
        controls.lanes[lane].probability = 1.0F;
        controls.lanes[lane].amplitude = 0.75F;
        controls.lanes[lane].routes.fill(0.0F);
        controls.lanes[lane].routes[
            static_cast<std::size_t>(pam::Destination::trigger)] = 1.0F;
        if (lane != 0U) {
            controls.lanes[lane].routes[lane] = lane == 2U ? -0.25F : 0.25F;
        }
        controls.voices[lane].engine = models[lane];
        controls.voices[lane].note = 36.0F + static_cast<float>(lane * 4U);
        controls.voices[lane].level = 0.07F;
    }
    return controls;
}

void testCardinalityRatesAndEuclidean() {
    expect(pam::kLaneCount == 7U, "voice cardinality is not seven");
    expect(pam::kPageCount == 8U && pam::kGlobalPageIndex == 7U,
        "seven-lane/eight-page contract drift");
    const std::array<pam::Rational, pam::kRateCount> expected{{
        {1U, 16U}, {1U, 12U}, {1U, 8U}, {1U, 6U},
        {1U, 4U}, {1U, 3U}, {1U, 2U}, {3U, 4U},
        {1U, 1U}, {4U, 3U}, {3U, 2U}, {2U, 1U},
        {3U, 1U}, {4U, 1U}, {8U, 1U}, {16U, 1U},
    }};
    for (std::size_t index = 0; index < expected.size(); ++index) {
        expect(pam::rateTable()[index].numerator == expected[index].numerator
            && pam::rateTable()[index].denominator == expected[index].denominator,
            "rate table drift");
    }
    for (std::uint8_t hits = 0U; hits <= 16U; ++hits) {
        for (std::uint8_t rotation = 0U; rotation < 16U; ++rotation) {
            unsigned int count = 0U;
            for (std::uint8_t step = 0U; step < 16U; ++step) {
                count += pam::euclideanHit(step, hits, rotation) ? 1U : 0U;
            }
            expect(count == hits, "Euclidean hit count mismatch");
        }
    }
}

void testShapesAndRandom() {
    for (std::uint8_t shape = 0U; shape < 8U; ++shape) {
        for (const auto phase : {0U, UINT32_C(0x40000000),
                                 UINT32_C(0x80000000), UINT32_MAX}) {
            const auto value = pam::shapeValue(
                static_cast<pam::Shape>(shape), phase, 0.25, 0.75);
            expect(std::isfinite(value) && value >= 0.0F && value <= 1.0F,
                "shape output out of range");
        }
    }
    expect(pam::shapeValue(pam::Shape::gate, 0U, 0.0, 0.0) == 1.0F,
        "gate start mismatch");
    expect(pam::addressedRandomWord(1U, 2U, 3U, 4U)
        == pam::addressedRandomWord(1U, 2U, 3U, 4U),
        "addressed random repeat mismatch");
    std::size_t accepted = 0U;
    for (std::uint64_t address = 0U; address < 65536U; ++address) {
        if (pam::addressedRandomUnit(pam::kDefaultSeed, 0U, address, 17U) < 0.5) {
            ++accepted;
        }
    }
    expect(std::abs(static_cast<double>(accepted) / 65536.0 - 0.5) < 0.01,
        "addressed random bounded mean failed");
}

void testSanitization() {
    auto controls = pam::defaultControls();
    controls.tempo_milli_bpm = 1U;
    controls.voices[0].engine = 200U;
    controls.voices[3].note = std::numeric_limits<float>::quiet_NaN();
    controls.voices[4].harmonics = 2.0F;
    controls.selected_page = 200U;
    controls.lane_control_mode = static_cast<pam::LaneControlMode>(200U);
    controls.cohesion.drive = std::numeric_limits<float>::infinity();
    controls.cohesion.cohere = -1.0F;
    controls.cohesion.root_note = 100.0F;
    controls.cohesion.tail = std::numeric_limits<float>::quiet_NaN();
    controls.lanes[0].rate_index = 200U;
    controls.lanes[0].shape = static_cast<pam::Shape>(200U);
    controls.lanes[0].probability = -1.0F;
    controls.lanes[0].routes[0] = std::numeric_limits<float>::infinity();
    pam::SanitizeCounts counts{};
    const auto sanitized = pam::sanitizeControls(controls, &counts);
    expect(sanitized.tempo_milli_bpm == 120000U, "tempo fallback mismatch");
    expect(sanitized.voices[0].engine == 23U, "model clamp mismatch");
    expect(sanitized.voices[3].note == 48.0F, "note fallback mismatch");
    expect(sanitized.voices[4].harmonics == 1.0F, "unit clamp mismatch");
    expect(sanitized.selected_page == pam::kGlobalPageIndex,
        "selected page clamp mismatch");
    expect(sanitized.lane_control_mode == pam::LaneControlMode::voice,
        "lane control mode fallback mismatch");
    expect(sanitized.cohesion.drive == 0.0F
        && sanitized.cohesion.cohere == 0.0F
        && sanitized.cohesion.root_note == 84.0F
        && sanitized.cohesion.tail == 0.5F,
        "cohesion sanitization mismatch");
    expect(sanitized.lanes[0].rate_index == 8U, "rate fallback mismatch");
    expect(sanitized.lanes[0].shape == pam::Shape::pulse,
        "shape fallback mismatch");
    expect(sanitized.lanes[0].probability == 0.0F,
        "probability clamp mismatch");
    expect(sanitized.lanes[0].routes[0] == 0.0F,
        "route fallback mismatch");
    expect(counts.invalid >= 6U && counts.clamped >= 5U,
        "sanitization diagnostics incomplete");

    for (const auto requested : {
            -1.0F, 0.0F, 1.0F / 127.0F, 0.01F, 0.5F, 1.0F, 2.0F}) {
        auto trigger_controls = pam::defaultControls();
        trigger_controls.lanes[0].routes[0] = requested;
        const auto trigger = pam::sanitizeControls(trigger_controls);
        expect(trigger.lanes[0].routes[0]
                == (requested > (1.0F / 127.0F) ? 1.0F : 0.0F),
            "legacy Trigger value did not sanitize to exact Off/On");
    }
}

void testPartitionIdentity() {
    auto controls = sevenVoiceControls();
    controls.cohesion.drive = 0.35F;
    controls.cohesion.cohere = 0.72F;
    controls.cohesion.spread = 0.45F;
    controls.cohesion.tail = 0.65F;
    controls.cohesion.damping = 0.4F;
    controls.cohesion.width = 0.7F;
    controls.cohesion.duck = 0.3F;
    const auto reference = render(controls, 32768U, 1U);
    expect(!allZero(reference.main), "seven-voice cohesion render is silent");
    for (const auto block : {16U, 64U, 128U, 257U, 512U}) {
        const auto candidate = render(controls, 32768U, block);
        expect(candidate.main == reference.main, "main PCM partition mismatch");
        expect(candidate.auxiliary == reference.auxiliary,
            "auxiliary PCM partition mismatch");
        expect(candidate.events.size() == reference.events.size(),
            "event count partition mismatch");
        for (std::size_t event = 0; event < reference.events.size(); ++event) {
            expect(sameEvent(candidate.events[event], reference.events[event]),
                "event partition mismatch");
        }
        expect(candidate.snapshot.absolute_frame == reference.snapshot.absolute_frame
            && candidate.snapshot.master_phase_q32
                == reference.snapshot.master_phase_q32
            && candidate.snapshot.lane_phase_q32
                == reference.snapshot.lane_phase_q32
            && candidate.snapshot.lane_remainders
                == reference.snapshot.lane_remainders
            && candidate.snapshot.resolved_engines
                == reference.snapshot.resolved_engines
            && candidate.snapshot.source_random_states
                == reference.snapshot.source_random_states
            && candidate.snapshot.cohesion.mode_real
                == reference.snapshot.cohesion.mode_real
            && candidate.snapshot.cohesion.mode_imaginary
                == reference.snapshot.cohesion.mode_imaginary
            && candidate.snapshot.lane_output_energy
                == reference.snapshot.lane_output_energy
            && candidate.snapshot.cohesion.dry_difference_energy
                == reference.snapshot.cohesion.dry_difference_energy,
            "snapshot partition mismatch");
    }
}

void expectSilence(pam::Controls controls, const std::string& label) {
    controls.cohesion.cohere = 1.0F;
    const auto rendered = render(controls, 8192U, 257U);
    expect(allZero(rendered.main), label + " main not silent");
    expect(allZero(rendered.auxiliary), label + " auxiliary not silent");
    expect(std::all_of(
        rendered.snapshot.cohesion.mode_real.begin(),
        rendered.snapshot.cohesion.mode_real.end(),
        [](float value) { return value == 0.0F; }),
        label + " modal state not zero");
}

void testSilenceAndUnsupported() {
    auto stopped = pam::defaultControls();
    stopped.running = false;
    expectSilence(stopped, "stopped");
    auto zero_hit = pam::defaultControls();
    zero_hit.lanes[0].hits = 0U;
    expectSilence(zero_hit, "zero-hit");
    auto zero_amplitude = pam::defaultControls();
    zero_amplitude.lanes[0].amplitude = 0.0F;
    expectSilence(zero_amplitude, "zero-amplitude");
    auto zero_route = pam::defaultControls();
    zero_route.lanes[0].routes.fill(0.0F);
    expectSilence(zero_route, "zero-route");

    pam::Core core;
    std::array<std::int32_t, 513U> main{};
    std::array<std::int32_t, 513U> auxiliary{};
    main.fill(1);
    auxiliary.fill(1);
    expect(!core.process(pam::defaultControls(), main.data(), auxiliary.data(),
        main.size()), "unsupported block accepted");
    expect(core.snapshot().absolute_frame == 0U,
        "unsupported block advanced transport");
    expect(std::all_of(main.begin(), main.end(),
        [](std::int32_t value) { return value == 0; }),
        "unsupported block not cleared");
}

void testTriggerEnableSemantics() {
    auto off = pam::defaultControls();
    off.lanes[0].routes[0] = 0.0F;
    const auto rendered_off = render(off, 8192U, 128U);
    expect(allZero(rendered_off.main) && allZero(rendered_off.auxiliary)
        && rendered_off.snapshot.diagnostics.trigger_count == 0U
        && rendered_off.snapshot.accepted.lanes[0].routes[0] == 0.0F,
        "Trigger Off was not exact fresh-reset silence");

    auto negative = off;
    negative.lanes[0].routes[0] = -1.0F;
    const auto rendered_negative = render(negative, 8192U, 128U);
    expect(rendered_negative.main == rendered_off.main
        && rendered_negative.auxiliary == rendered_off.auxiliary
        && rendered_negative.snapshot.accepted.lanes[0].routes[0] == 0.0F,
        "legacy negative Trigger did not normalize to Off");

    auto on = off;
    on.lanes[0].routes[0] = 1.0F;
    const auto rendered_on = render(on, 8192U, 128U);
    expect(!allZero(rendered_on.main) && !allZero(rendered_on.auxiliary)
        && rendered_on.snapshot.diagnostics.trigger_count > 0U
        && rendered_on.snapshot.accepted.lanes[0].routes[0] == 1.0F,
        "Trigger On did not create activity");

    auto legacy_positive = off;
    legacy_positive.lanes[0].routes[0] = 0.5F;
    const auto rendered_legacy = render(legacy_positive, 8192U, 128U);
    expect(rendered_legacy.main == rendered_on.main
        && rendered_legacy.auxiliary == rendered_on.auxiliary
        && rendered_legacy.snapshot.accepted.lanes[0].routes[0] == 1.0F,
        "legacy positive Trigger did not normalize to exact On parity");
}

void testAllModels() {
    const std::array<const char*, 24U> expected_names{{
        "Virtual Analog VCF", "Phase Distortion", "6-Op FM A", "6-Op FM B",
        "6-Op FM C", "Wave Terrain", "String Machine", "Chiptune",
        "Virtual Analog", "Waveshaping", "2-Op FM", "Granular Formant",
        "Harmonic / Additive", "Wavetable", "Chord", "Speech", "Swarm",
        "Noise", "Particle", "String", "Modal Resonator", "Bass Drum",
        "Snare Drum", "Hi-Hat",
    }};
    for (std::uint8_t model = 0U; model < 24U; ++model) {
        auto controls = pam::defaultControls();
        controls.voices[0].engine = model;
        controls.lanes[0].rate_index = 13U;
        controls.lanes[0].hits = 16U;
        const auto rendered = render(controls, 8192U, 128U);
        const auto valid = [](std::int32_t value) {
            return value >= pam::kQ27Minimum && value <= pam::kQ27Maximum;
        };
        expect(std::all_of(rendered.main.begin(), rendered.main.end(), valid)
            && std::all_of(
                rendered.auxiliary.begin(), rendered.auxiliary.end(), valid),
            "model output out of range");
        expect(!allZero(rendered.main) && !allZero(rendered.auxiliary),
            "model output silent");
        expect(std::string{pam::modelName(model)} == expected_names[model],
            "model source-order name drifted");
    }
    expect(std::string{pam::modelName(24U)} == "Unknown",
        "invalid model name fallback mismatch");
}

void testReset() {
    auto controls = sevenVoiceControls();
    controls.cohesion.cohere = 0.75F;
    controls.cohesion.tail = 0.9F;
    pam::Core core;
    std::array<std::int32_t, 512U> first_main{};
    std::array<std::int32_t, 512U> first_aux{};
    std::array<std::int32_t, 512U> reset_main{};
    std::array<std::int32_t, 512U> reset_aux{};
    expect(core.process(controls, first_main.data(), first_aux.data(), 512U),
        "first reset fixture process failed");
    core.reset();
    expect(core.process(controls, reset_main.data(), reset_aux.data(), 512U),
        "second reset fixture process failed");
    expect(first_main == reset_main && first_aux == reset_aux,
        "reset did not reproduce fresh bytes");
}

void testLaneOutputTelemetry() {
    auto controls = pam::defaultControls();
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        controls.lanes[lane].routes.fill(0.0F);
        controls.voices[lane].level = 0.0F;
    }
    constexpr std::size_t active_lane = 3U;
    controls.lanes[active_lane].rate_index = 15U;
    controls.lanes[active_lane].hits = 16U;
    controls.lanes[active_lane].amplitude = 1.0F;
    controls.lanes[active_lane].routes[
        static_cast<std::size_t>(pam::Destination::trigger)] = 1.0F;
    controls.voices[active_lane].level = 0.3F;

    pam::Core core;
    std::array<std::int32_t, 512U> main{};
    std::array<std::int32_t, 512U> auxiliary{};
    for (std::size_t block = 0; block < 8U; ++block) {
        expect(core.process(
            controls, main.data(), auxiliary.data(), main.size()),
            "telemetry first process failed");
    }
    const auto first = core.snapshot();
    expect(first.lane_output_energy[active_lane] > 0.0
            && std::isfinite(first.lane_output_energy[active_lane]),
        "active lane did not publish finite output energy: energy="
            + std::to_string(first.lane_output_energy[active_lane])
            + " triggers=" + std::to_string(
                first.diagnostics.lane_trigger_count[active_lane])
            + " started=" + std::to_string(
                (first.started_lane_mask >> active_lane) & 1U));
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        if (lane == active_lane) continue;
        expect(first.lane_output_energy[lane] == 0.0,
            "silent lane published output energy");
    }

    expect(core.process(controls, main.data(), auxiliary.data(), main.size()),
        "telemetry second process failed");
    const auto second = core.snapshot();
    expect(second.lane_output_energy[active_lane]
            > first.lane_output_energy[active_lane],
        "active lane output energy was not monotone");
    core.reset();
    const auto reset = core.snapshot();
    expect(reset.absolute_frame == 0U
            && std::all_of(reset.lane_output_energy.begin(),
                reset.lane_output_energy.end(),
                [](double value) { return value == 0.0; }),
        "Core reset did not clear lane output telemetry");
}

void testVoiceControlAndModelIsolation() {
    auto controls = pam::defaultControls();
    controls.lanes[1] = controls.lanes[0];
    controls.voices[0].engine = 8U;
    controls.voices[1].engine = 20U;
    controls.voices[1].note = 67.0F;
    controls.voices[1].level = 0.2F;

    pam::Core core;
    std::array<std::int32_t, 16U> main{};
    std::array<std::int32_t, 16U> auxiliary{};
    expect(core.process(controls, main.data(), auxiliary.data(), main.size()),
        "voice-isolation baseline process failed");
    const auto before = core.snapshot();
    controls.voices[0].engine = 21U;
    controls.voices[0].note = 31.0F;
    controls.voices[0].harmonics = 0.9F;
    expect(core.process(controls, main.data(), auxiliary.data(), main.size()),
        "voice-isolation edited process failed");
    const auto after = core.snapshot();
    for (std::size_t lane = 1; lane < pam::kLaneCount; ++lane) {
        expect(sameVoice(before.accepted.voices[lane], after.accepted.voices[lane]),
            "target voice edit changed a non-target voice");
    }
    expect(after.accepted.voices[0].engine == 21U
        && after.accepted.voices[1].engine == 20U,
        "base models were not independently accepted");

    controls.lanes[0].shape = pam::Shape::gate;
    controls.lanes[0].hits = 16U;
    controls.lanes[0].amplitude = 1.0F;
    controls.lanes[0].routes[
        static_cast<std::size_t>(pam::Destination::model)] = 0.5F;
    controls.lanes[1].routes[
        static_cast<std::size_t>(pam::Destination::model)] = 0.0F;
    expect(core.process(controls, main.data(), auxiliary.data(), main.size()),
        "model-locality process failed");
    const auto model = core.snapshot();
    expect(model.resolved_engines[0] != model.accepted.voices[0].engine,
        "lane-local MODEL SWEEP did not move its resolved model");
    expect(model.resolved_engines[1] == 20U,
        "lane-local MODEL SWEEP changed another lane's model");
}

void testSequencerControlResponse() {
    auto base = pam::defaultControls();
    base.master_gain = 0.35F;
    base.voices[0].engine = 8U;
    base.voices[0].level = 0.3F;
    base.lanes[0].rate_index = 8U;
    base.lanes[0].hits = 5U;
    base.lanes[0].shape = pam::Shape::pulse;
    base.lanes[0].amplitude = 1.0F;
    base.lanes[0].routes.fill(0.0F);
    base.lanes[0].routes[static_cast<std::size_t>(pam::Destination::trigger)] =
        1.0F;

    auto phase_shifted = base;
    phase_shifted.lanes[0].phase_u7 = 64U;
    const auto phase_zero_render = render(base, 96000U, 257U);
    const auto phase_shifted_render = render(phase_shifted, 96000U, 257U);
    expect(laneTriggerFrames(phase_zero_render, 0U)
            != laneTriggerFrames(phase_shifted_render, 0U),
        "Phase did not move eligible trigger frames");
    expect(phase_zero_render.snapshot.accepted.lanes[0].hits == 5U
            && phase_shifted_render.snapshot.accepted.lanes[0].hits == 5U
            && phase_zero_render.snapshot.accepted.lanes[0].rate_index == 8U
            && phase_shifted_render.snapshot.accepted.lanes[0].rate_index == 8U,
        "Phase changed hit count or rate state");

    auto rotated = base;
    rotated.lanes[0].rotation = 3U;
    const auto rotated_render = render(rotated, 96000U, 257U);
    const auto base_triggers = laneTriggerFrames(phase_zero_render, 0U);
    const auto rotated_triggers = laneTriggerFrames(rotated_render, 0U);
    expect(base_triggers.size() == 5U && rotated_triggers.size() == 5U
            && base_triggers != rotated_triggers,
        "Rotate did not move a 5-of-16 pattern with cardinality preserved");

    auto triangle_trigger_only = base;
    triangle_trigger_only.lanes[0].shape = pam::Shape::triangle;
    const auto triangle_trigger_render = render(
        triangle_trigger_only, 96000U, 257U);
    expect(triangle_trigger_render.main == phase_zero_render.main
            && triangle_trigger_render.auxiliary
                == phase_zero_render.auxiliary
            && laneTriggerFrames(triangle_trigger_render, 0U)
                == base_triggers,
        "Shape changed a trigger-only lane despite having no continuous route");

    auto pulse_routed = base;
    pulse_routed.lanes[0].routes[
        static_cast<std::size_t>(pam::Destination::pitch)] = 0.8F;
    auto triangle_routed = pulse_routed;
    triangle_routed.lanes[0].shape = pam::Shape::triangle;
    const auto pulse_routed_render = render(pulse_routed, 96000U, 257U);
    const auto triangle_routed_render = render(
        triangle_routed, 96000U, 257U);
    expect(laneTriggerFrames(pulse_routed_render, 0U)
            == laneTriggerFrames(triangle_routed_render, 0U)
            && normalizedStereoRmsDifference(
                pulse_routed_render, triangle_routed_render) > 5.0e-4,
        "Shape did not alter a routed continuous Motion destination");
}

void testStochasticSourceIsolation() {
    constexpr std::uint32_t seed = UINT32_C(0x13579bdf);
    pam::MacroVoice reference(seed);
    pam::MacroVoice interleaved(seed);
    pam::MacroVoice interferer(UINT32_C(0x2468ace1));
    pam::MacroVoiceControls target{};
    target.engine = 17U;
    pam::MacroVoiceControls other = target;
    other.engine = 18U;
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> reference_main{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> reference_aux{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> candidate_main{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> candidate_aux{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> discard_main{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> discard_aux{};
    for (std::size_t quantum = 0; quantum < 256U; ++quantum) {
        target.trigger = quantum == 0U || quantum % 17U == 0U;
        other.trigger = quantum == 0U || quantum % 7U == 0U;
        reference.process(target, reference_main, reference_aux);
        interferer.process(other, discard_main, discard_aux);
        interleaved.process(target, candidate_main, candidate_aux);
        expect(reference_main == candidate_main
            && reference_aux == candidate_aux
            && reference.randomState() == interleaved.randomState(),
            "interleaved stochastic source changed reference state/output");
    }
}

void testExactDryAndActiveCohesion() {
    auto dry_controls = sevenVoiceControls();
    dry_controls.cohesion.drive = 0.0F;
    dry_controls.cohesion.cohere = 0.0F;
    auto driven_bypass = dry_controls;
    driven_bypass.cohesion.drive = 1.0F;
    driven_bypass.cohesion.root_note = 84.0F;
    driven_bypass.cohesion.spread = 1.0F;
    driven_bypass.cohesion.tail = 1.0F;
    driven_bypass.cohesion.width = 1.0F;
    const auto dry = render(dry_controls, 65536U, 257U);
    const auto bypass = render(driven_bypass, 65536U, 257U);
    expect(dry.main == bypass.main && dry.auxiliary == bypass.auxiliary,
        "Drive or modal controls leaked through Cohere zero");

    auto active_controls = dry_controls;
    active_controls.cohesion.drive = 0.35F;
    active_controls.cohesion.cohere = 0.72F;
    active_controls.cohesion.spread = 0.45F;
    active_controls.cohesion.tail = 0.65F;
    active_controls.cohesion.damping = 0.4F;
    active_controls.cohesion.width = 0.7F;
    active_controls.cohesion.duck = 0.3F;
    const auto active = render(active_controls, 65536U, 257U);
    expect(active.main != dry.main || active.auxiliary != dry.auxiliary,
        "nonzero Cohere is observationally inactive");
    expect(active.snapshot.cohesion.dry_difference_energy > 0.0,
        "Cohere difference energy is not positive");
    for (std::size_t mode = 0; mode < pam::kCohesionModeCount; ++mode) {
        expect(active.snapshot.cohesion.mode_frequencies_hz[mode] > 0.0F
            && active.snapshot.cohesion.mode_frequencies_hz[mode] < 21600.0F,
            "modal frequency escaped guard");
        expect(active.snapshot.cohesion.mode_poles[mode] > 0.0F
            && active.snapshot.cohesion.mode_poles[mode] < 1.0F,
            "modal pole is not strictly stable");
        expect(std::isfinite(active.snapshot.cohesion.mode_real[mode])
            && std::isfinite(active.snapshot.cohesion.mode_imaginary[mode]),
            "modal state is non-finite");
    }
    expect(active.snapshot.diagnostics.effect_recovery_count == 0U,
        "nominal cohesion render recovered invalid state");
}

void testIndividualGlobalResponse() {
    auto baseline = sevenVoiceControls();
    baseline.cohesion.drive = 0.35F;
    baseline.cohesion.cohere = 0.8F;
    baseline.cohesion.root_note = 48.0F;
    baseline.cohesion.spread = 0.45F;
    baseline.cohesion.tail = 0.65F;
    baseline.cohesion.damping = 0.4F;
    baseline.cohesion.width = 0.7F;
    baseline.cohesion.duck = 0.3F;

    const auto expect_response = [&baseline](
            const std::string& label,
            const auto& set_low,
            const auto& set_high) {
        auto low = baseline;
        auto high = baseline;
        set_low(low.cohesion);
        set_high(high.cohesion);
        const auto low_render = render(low, 65536U, 257U);
        const auto high_render = render(high, 65536U, 257U);
        const auto difference = normalizedStereoRmsDifference(
            low_render, high_render);
        expect(difference >= 5.0e-4,
            label + " response below frozen RMS threshold: "
                + std::to_string(difference));
        expect(low_render.snapshot.diagnostics.effect_recovery_count == 0U
                && high_render.snapshot.diagnostics.effect_recovery_count == 0U
                && low_render.snapshot.diagnostics.saturated_sample_count == 0U
                && high_render.snapshot.diagnostics.saturated_sample_count == 0U,
            label + " response produced nominal recovery or saturation");
    };

    expect_response("Drive",
        [](pam::CohesionControls& value) { value.drive = 0.0F; },
        [](pam::CohesionControls& value) { value.drive = 1.0F; });
    expect_response("Root",
        [](pam::CohesionControls& value) { value.root_note = 24.0F; },
        [](pam::CohesionControls& value) { value.root_note = 84.0F; });
    expect_response("Spread",
        [](pam::CohesionControls& value) { value.spread = 0.0F; },
        [](pam::CohesionControls& value) { value.spread = 1.0F; });
    expect_response("Tail",
        [](pam::CohesionControls& value) { value.tail = 0.0F; },
        [](pam::CohesionControls& value) { value.tail = 1.0F; });
    expect_response("Damping",
        [](pam::CohesionControls& value) { value.damping = 0.0F; },
        [](pam::CohesionControls& value) { value.damping = 1.0F; });
    expect_response("Width",
        [](pam::CohesionControls& value) { value.width = 0.0F; },
        [](pam::CohesionControls& value) { value.width = 1.0F; });
    expect_response("Duck",
        [](pam::CohesionControls& value) { value.duck = 0.0F; },
        [](pam::CohesionControls& value) { value.duck = 1.0F; });
}

void testEffectOnlyClear() {
    auto controls = sevenVoiceControls();
    controls.cohesion.drive = 0.25F;
    controls.cohesion.cohere = 0.8F;
    controls.cohesion.tail = 0.8F;
    pam::Core candidate;
    pam::Core reference;
    std::array<std::int32_t, 512U> candidate_main{};
    std::array<std::int32_t, 512U> candidate_aux{};
    std::array<std::int32_t, 512U> reference_main{};
    std::array<std::int32_t, 512U> reference_aux{};
    for (std::size_t frame = 0; frame < 32768U; frame += 512U) {
        expect(candidate.process(controls, candidate_main.data(), candidate_aux.data(),
            candidate_main.size()), "clear candidate excitation failed");
        expect(reference.process(controls, reference_main.data(), reference_aux.data(),
            reference_main.size()), "clear reference excitation failed");
    }
    for (auto& voice : controls.voices) voice.level = 0.0F;
    bool tail_nonzero = false;
    std::int32_t tail_peak = 0;
    for (std::size_t frame = 0; frame < 8192U; frame += 512U) {
        expect(candidate.process(controls, candidate_main.data(), candidate_aux.data(),
            candidate_main.size()), "clear candidate tail failed");
        expect(reference.process(controls, reference_main.data(), reference_aux.data(),
            reference_main.size()), "clear reference tail failed");
        tail_nonzero = tail_nonzero
            || std::any_of(candidate_main.begin(), candidate_main.end(),
                [](std::int32_t value) { return value != 0; })
            || std::any_of(candidate_aux.begin(), candidate_aux.end(),
                [](std::int32_t value) { return value != 0; });
        for (const auto value : candidate_main) {
            tail_peak = std::max<std::int32_t>(tail_peak,
                static_cast<std::int32_t>(std::abs(
                    static_cast<std::int64_t>(value))));
        }
        for (const auto value : candidate_aux) {
            tail_peak = std::max<std::int32_t>(tail_peak,
                static_cast<std::int32_t>(std::abs(
                    static_cast<std::int64_t>(value))));
        }
    }
    expect(tail_nonzero, "shared body produced no tail before Clear");
    expect(static_cast<double>(tail_peak) / 134217728.0 >= 5.0e-4,
        "shared body tail remained below the frozen Clear threshold");

    ++controls.effect_clear_generation;
    pam::ProcessReport clear_report{};
    expect(candidate.process(controls, candidate_main.data(), candidate_aux.data(),
        16U, &clear_report), "Clear quantum failed");
    auto reference_controls = controls;
    --reference_controls.effect_clear_generation;
    expect(reference.process(
        reference_controls, reference_main.data(), reference_aux.data(), 16U),
        "no-clear reference quantum failed");
    expect(std::all_of(candidate_main.begin(), candidate_main.begin() + 16,
            [](std::int32_t value) { return value == 0; })
        && std::all_of(candidate_aux.begin(), candidate_aux.begin() + 16,
            [](std::int32_t value) { return value == 0; }),
        "Clear left audible effect history");
    expect(std::any_of(reference_main.begin(), reference_main.begin() + 16,
            [](std::int32_t value) { return value != 0; })
        || std::any_of(reference_aux.begin(), reference_aux.begin() + 16,
            [](std::int32_t value) { return value != 0; }),
        "no-clear reference unexpectedly lost its tail");
    const auto cleared = candidate.snapshot();
    const auto continued = reference.snapshot();
    expect(cleared.diagnostics.effect_clear_count == 1U
        && cleared.cohesion.applied_clear_generation
            == controls.effect_clear_generation,
        "Clear generation was not applied exactly once");
    expect(clear_report.event_count > 0U
        && clear_report.events[0].effect_cleared,
        "Clear provenance event was not retained");
    expect(std::all_of(cleared.cohesion.mode_real.begin(),
            cleared.cohesion.mode_real.end(),
            [](float value) { return value == 0.0F; })
        && std::all_of(cleared.cohesion.mode_imaginary.begin(),
            cleared.cohesion.mode_imaginary.end(),
            [](float value) { return value == 0.0F; })
        && cleared.cohesion.duck_envelope == 0.0F,
        "Clear did not zero every effect state");
    auto comparable_controls = cleared.accepted;
    comparable_controls.effect_clear_generation =
        continued.accepted.effect_clear_generation;
    expect(pam::sameControls(comparable_controls, continued.accepted)
        && cleared.lane_phase_q32 == continued.lane_phase_q32
        && cleared.lane_remainders == continued.lane_remainders
        && cleared.lane_steps == continued.lane_steps
        && cleared.lane_addresses == continued.lane_addresses
        && cleared.source_random_states == continued.source_random_states
        && cleared.diagnostics.lane_trigger_count
            == continued.diagnostics.lane_trigger_count,
        "Clear changed lane, voice, scheduler, or source state");

    pam::Core combined_change;
    auto combined_controls = pam::defaultControls();
    std::array<std::int32_t, 16U> combined_main{};
    std::array<std::int32_t, 16U> combined_aux{};
    expect(combined_change.process(combined_controls, combined_main.data(),
        combined_aux.data(), combined_main.size()),
        "combined-change baseline failed");
    ++combined_controls.seed;
    ++combined_controls.effect_clear_generation;
    pam::ProcessReport combined_report{};
    expect(combined_change.process(combined_controls, combined_main.data(),
        combined_aux.data(), combined_main.size(), &combined_report),
        "combined seed and Clear quantum failed");
    const auto combined_snapshot = combined_change.snapshot();
    expect(combined_snapshot.diagnostics.effect_clear_count == 1U
        && combined_snapshot.cohesion.applied_clear_generation
            == combined_controls.effect_clear_generation
        && combined_report.event_count > 0U
        && combined_report.events[0].effect_cleared,
        "simultaneous seed and Clear change lost Clear provenance");
}

}  // namespace

int main() {
    testCardinalityRatesAndEuclidean();
    testShapesAndRandom();
    testSanitization();
    testPartitionIdentity();
    testSilenceAndUnsupported();
    testTriggerEnableSemantics();
    testAllModels();
    testReset();
    testLaneOutputTelemetry();
    testVoiceControlAndModelIsolation();
    testSequencerControlResponse();
    testStochasticSourceIsolation();
    testExactDryAndActiveCohesion();
    testIndividualGlobalResponse();
    testEffectOnlyClear();
    std::cout << "pamplist_core_tests: pass\n";
    return 0;
}
