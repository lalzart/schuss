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
        && left.trigger == right.trigger
        && left.resolved_engine == right.resolved_engine
        && left.steps == right.steps
        && left.addresses == right.addresses;
}

void testRatesAndEuclidean() {
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
    expect(pam::shapeValue(pam::Shape::pulse, UINT32_C(0x80000000), 0.0, 0.0)
        == 0.0F, "pulse half-cycle mismatch");
    expect(pam::shapeValue(pam::Shape::sample_hold, 0U, 0.25, 0.75) == 0.25F,
        "sample-hold mismatch");
    expect(pam::addressedRandomWord(1U, 2U, 3U, 4U)
        == pam::addressedRandomWord(1U, 2U, 3U, 4U),
        "addressed random repeat mismatch");
    std::size_t accepted = 0U;
    for (std::uint64_t address = 0U; address < 65536U; ++address) {
        if (pam::addressedRandomUnit(pam::kDefaultSeed, 0U, address, 17U) < 0.5) {
            ++accepted;
        }
    }
    const auto mean = static_cast<double>(accepted) / 65536.0;
    expect(std::abs(mean - 0.5) < 0.01, "addressed random bounded mean failed");
}

void testSanitization() {
    auto controls = pam::defaultControls();
    controls.tempo_milli_bpm = 1U;
    controls.note = std::numeric_limits<float>::quiet_NaN();
    controls.harmonics = 2.0F;
    controls.selected_lane = 200U;
    controls.lanes[0].rate_index = 200U;
    controls.lanes[0].shape = static_cast<pam::Shape>(200U);
    controls.lanes[0].probability = -1.0F;
    controls.lanes[0].routes[0] = std::numeric_limits<float>::infinity();
    pam::SanitizeCounts counts{};
    const auto sanitized = pam::sanitizeControls(controls, &counts);
    expect(sanitized.tempo_milli_bpm == 120000U, "tempo fallback mismatch");
    expect(sanitized.note == 48.0F, "note fallback mismatch");
    expect(sanitized.harmonics == 1.0F, "unit clamp mismatch");
    expect(sanitized.selected_lane == 7U, "selected lane clamp mismatch");
    expect(sanitized.lanes[0].rate_index == 8U, "rate fallback mismatch");
    expect(sanitized.lanes[0].shape == pam::Shape::pulse, "shape fallback mismatch");
    expect(sanitized.lanes[0].probability == 0.0F, "probability clamp mismatch");
    expect(sanitized.lanes[0].routes[0] == 0.0F, "route fallback mismatch");
    expect(counts.invalid >= 4U && counts.clamped >= 3U,
        "sanitization diagnostics incomplete");
}

pam::Controls matrixControls() {
    auto controls = pam::defaultControls();
    const std::array<pam::Shape, pam::kLaneCount> shapes{{
        pam::Shape::pulse,
        pam::Shape::triangle,
        pam::Shape::sine,
        pam::Shape::ramp,
        pam::Shape::exponential_decay,
        pam::Shape::sample_hold,
        pam::Shape::smooth_random,
        pam::Shape::gate,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> rates{{8U, 10U, 6U, 11U, 4U, 12U, 2U, 13U}};
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        controls.lanes[lane].shape = shapes[lane];
        controls.lanes[lane].rate_index = rates[lane];
        controls.lanes[lane].phase_u7 = static_cast<std::uint8_t>(lane * 13U);
        controls.lanes[lane].hits = static_cast<std::uint8_t>(5U + lane);
        controls.lanes[lane].probability = 1.0F;
        controls.lanes[lane].amplitude = 0.75F;
        controls.lanes[lane].routes.fill(0.0F);
        controls.lanes[lane].routes[lane] = lane == 2U ? -0.45F : 0.45F;
    }
    controls.lanes[0].routes[0] = 1.0F;
    return controls;
}

void testPartitionIdentity() {
    const auto controls = matrixControls();
    const auto reference = render(controls, 32768U, 1U);
    expect(std::any_of(reference.main.begin(), reference.main.end(),
        [](std::int32_t value) { return value != 0; }), "matrix main is silent");
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
            && candidate.snapshot.master_phase_q32 == reference.snapshot.master_phase_q32
            && candidate.snapshot.lane_phase_q32 == reference.snapshot.lane_phase_q32
            && candidate.snapshot.lane_remainders == reference.snapshot.lane_remainders
            && candidate.snapshot.diagnostics.trigger_count
                == reference.snapshot.diagnostics.trigger_count,
            "snapshot partition mismatch");
    }
}

void expectSilence(pam::Controls controls, const std::string& label) {
    const auto rendered = render(controls, 8192U, 257U);
    expect(std::all_of(rendered.main.begin(), rendered.main.end(),
        [](std::int32_t value) { return value == 0; }), label + " main not silent");
    expect(std::all_of(rendered.auxiliary.begin(), rendered.auxiliary.end(),
        [](std::int32_t value) { return value == 0; }), label + " auxiliary not silent");
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
    std::array<std::int32_t, 513> main{};
    std::array<std::int32_t, 513> auxiliary{};
    main.fill(1);
    auxiliary.fill(1);
    expect(!core.process(pam::defaultControls(), main.data(), auxiliary.data(),
        main.size()), "unsupported block accepted");
    expect(core.snapshot().absolute_frame == 0U,
        "unsupported block advanced transport");
    expect(std::all_of(main.begin(), main.end(),
        [](std::int32_t value) { return value == 0; }), "unsupported block not cleared");
}

void testAllEngines() {
    for (std::uint8_t engine = 0U; engine < 24U; ++engine) {
        auto controls = pam::defaultControls();
        controls.engine = engine;
        controls.lanes[0].rate_index = 13U;
        controls.lanes[0].hits = 16U;
        const auto rendered = render(controls, 8192U, 128U);
        const auto valid = [](std::int32_t value) {
            return value >= pam::kQ27Minimum && value <= pam::kQ27Maximum;
        };
        expect(std::all_of(rendered.main.begin(), rendered.main.end(), valid),
            "engine main out of range");
        expect(std::all_of(rendered.auxiliary.begin(), rendered.auxiliary.end(), valid),
            "engine auxiliary out of range");
        expect(std::any_of(rendered.main.begin(), rendered.main.end(),
            [](std::int32_t value) { return value != 0; }), "engine main silent");
        expect(std::any_of(rendered.auxiliary.begin(), rendered.auxiliary.end(),
            [](std::int32_t value) { return value != 0; }), "engine auxiliary silent");
    }
}

void testReset() {
    auto controls = matrixControls();
    pam::Core core;
    std::array<std::int32_t, 512> first_main{};
    std::array<std::int32_t, 512> first_aux{};
    std::array<std::int32_t, 512> reset_main{};
    std::array<std::int32_t, 512> reset_aux{};
    expect(core.process(controls, first_main.data(), first_aux.data(), 512U),
        "first reset fixture process failed");
    core.reset();
    expect(core.process(controls, reset_main.data(), reset_aux.data(), 512U),
        "second reset fixture process failed");
    expect(first_main == reset_main && first_aux == reset_aux,
        "reset did not reproduce fresh bytes");
}

}  // namespace

int main() {
    testRatesAndEuclidean();
    testShapesAndRandom();
    testSanitization();
    testPartitionIdentity();
    testSilenceAndUnsupported();
    testAllEngines();
    testReset();
    std::cout << "pamplist_core_tests: pass\n";
    return 0;
}
