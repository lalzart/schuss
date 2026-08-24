#include "layerwell/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace {

int failures = 0;

void expect(bool condition, const std::string& message) {
    if (condition) return;
    std::cerr << "FAIL: " << message << '\n';
    ++failures;
}

struct AbsoluteEvent final {
    std::uint64_t frame{};
    layerwell::Event event{};
};

std::vector<float> renderTimeline(std::uint32_t block_frames) {
    layerwell::Core core;
    expect(core.prepare(layerwell::kSampleRate, layerwell::kMaximumBlockFrames),
        "partition core prepares");

    std::vector<AbsoluteEvent> schedule{
        {0U, {0U, 1U, layerwell::EventKind::capture_press, 0U, 0.0}},
        {48000U, {0U, 2U, layerwell::EventKind::capture_press, 0U, 0.0}},
        {48000U, {0U, 3U, layerwell::EventKind::source_next, 0U, 0.0}},
        {72000U, {0U, 4U, layerwell::EventKind::select_layer, 1U, 0.0}},
        {72000U, {0U, 5U, layerwell::EventKind::capture_press, 0U, 0.0}},
    };
    constexpr std::uint64_t total_frames = 144000U;
    std::vector<float> output(total_frames * 2U);
    std::array<float, layerwell::kMaximumBlockFrames> left{};
    std::array<float, layerwell::kMaximumBlockFrames> right{};
    std::size_t next_event = 0U;

    for (std::uint64_t origin = 0U; origin < total_frames;) {
        const auto frames = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            block_frames, total_frames - origin));
        std::array<layerwell::Event, 8> events{};
        std::size_t count = 0U;
        const auto end = origin + frames;
        while (next_event < schedule.size() && schedule[next_event].frame <= end) {
            auto event = schedule[next_event].event;
            event.sample_offset = static_cast<std::uint32_t>(
                schedule[next_event].frame - origin);
            events[count++] = event;
            ++next_event;
        }
        const auto report = core.process(
            left.data(), right.data(), frames, events.data(), count);
        expect(report.events_dropped == 0U, "partition render drops no event");
        for (std::uint32_t frame = 0U; frame < frames; ++frame) {
            output[(origin + frame) * 2U] = left[frame];
            output[(origin + frame) * 2U + 1U] = right[frame];
        }
        origin += frames;
    }

    const auto snapshot = core.snapshot();
    expect(snapshot.loop_length_frames == 48000U, "partition loop length is exact");
    expect(snapshot.layers[0].occupied && snapshot.layers[1].occupied,
        "partition render commits two layers");
    expect(snapshot.capture_state == layerwell::CaptureState::idle,
        "partition render finishes idle");
    return output;
}

void testPrepareAndInvalidShape() {
    layerwell::Core core;
    expect(!core.prepare(44100.0, 128U), "44.1 kHz fails closed");
    expect(!core.prepare(48000.0, 127U), "non-quantized maximum block fails closed");
    expect(core.prepare(48000.0, 512U), "exact prepare succeeds");
    expect(core.snapshot().diagnostics.sample_storage_bytes == 49152000U,
        "sample storage byte contract is exact");

    std::array<float, 32> left{};
    std::array<float, 32> right{};
    const auto before = core.snapshot();
    core.process(left.data(), right.data(), 15U);
    const auto after = core.snapshot();
    expect(std::all_of(left.begin(), left.begin() + 15,
        [](float value) { return value == 0.0f; }),
        "unsupported block emits silence");
    expect(after.absolute_frame == before.absolute_frame,
        "unsupported block does not advance transport");
    expect(after.source_processed_frames == before.source_processed_frames,
        "unsupported block does not advance a source");
}

void testFirstCaptureAndShortRejection() {
    layerwell::Core core;
    expect(core.prepare(), "first-capture core prepares");
    std::array<float, 16> left{};
    std::array<float, 16> right{};
    const layerwell::Event start{0U, 1U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &start, 1U);
    for (std::uint32_t frame = 16U; frame < layerwell::kMinimumLoopFrames; frame += 16U) {
        core.process(left.data(), right.data(), 16U);
    }
    const layerwell::Event stop{0U, 2U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &stop, 1U);
    auto snapshot = core.snapshot();
    expect(snapshot.loop_length_frames == layerwell::kMinimumLoopFrames,
        "minimum first take establishes exact loop");
    expect(snapshot.layers[0].occupied, "first take occupies selected layer");
    expect(!snapshot.monitor_enabled, "commit turns source monitor off");
    expect(snapshot.phase_frames == 16U, "commit sample is playback phase zero");

    expect(core.reset(), "reset succeeds without reallocating");
    core.process(left.data(), right.data(), 16U, &start, 1U);
    constexpr std::uint32_t stop_block_origin = 23984U;
    for (std::uint32_t frame = 16U; frame < stop_block_origin; frame += 16U) {
        core.process(left.data(), right.data(), 16U);
    }
    auto exact_short_stop = stop;
    exact_short_stop.sample_offset = 15U;
    core.process(left.data(), right.data(), 16U, &exact_short_stop, 1U);
    snapshot = core.snapshot();
    expect(snapshot.loop_length_frames == 0U, "short first take establishes no loop");
    expect(!snapshot.layers[0].occupied, "short first take occupies no layer");
    expect(snapshot.diagnostics.short_capture_rejections == 1U,
        "23999-frame short rejection is diagnosed");
}

void testReplacementCancelAndOverflow() {
    layerwell::Core core;
    expect(core.prepare(), "replacement core prepares");
    std::array<float, 16> left{};
    std::array<float, 16> right{};
    const layerwell::Event start{0U, 1U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &start, 1U);
    for (std::uint32_t frame = 16U; frame < layerwell::kMinimumLoopFrames; frame += 16U) {
        core.process(left.data(), right.data(), 16U);
    }
    const layerwell::Event stop{0U, 2U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &stop, 1U);

    std::array<float, 64> before{};
    std::copy_n(core.committedSamples(0U, 0U), before.size(), before.begin());
    const layerwell::Event arm{0U, 3U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &arm, 1U);
    const layerwell::Event cancel{0U, 4U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &cancel, 1U);
    expect(std::memcmp(before.data(), core.committedSamples(0U, 0U),
               before.size() * sizeof(float)) == 0,
        "cancel preserves committed bytes");

    core.process(left.data(), right.data(), 16U, &arm, 1U);
    std::array<layerwell::Event, layerwell::kMaximumEvents + 1U> overflow{};
    for (std::size_t index = 0U; index < overflow.size(); ++index) {
        overflow[index] = {0U, 100U + index,
            layerwell::EventKind::toggle_monitor, 0U, 0.0};
    }
    const auto report = core.process(
        left.data(), right.data(), 16U, overflow.data(), overflow.size());
    expect(report.capture_aborted, "overflow aborts provisional capture");
    expect(report.events_dropped == overflow.size(), "overflow drops whole event batch");
    expect(std::memcmp(before.data(), core.committedSamples(0U, 0U),
               before.size() * sizeof(float)) == 0,
        "overflow preserves committed bytes");
}

void testRecordingCancelAndInvalidShapePreserve() {
    layerwell::Core core;
    expect(core.prepare(), "recording-cancel core prepares");
    std::array<float, 32> left{};
    std::array<float, 32> right{};
    const layerwell::Event start{0U, 1U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &start, 1U);
    for (std::uint32_t frame = 16U; frame < layerwell::kMinimumLoopFrames; frame += 16U) {
        core.process(left.data(), right.data(), 16U);
    }
    const layerwell::Event stop{0U, 2U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &stop, 1U);

    std::array<float, 64> before{};
    std::copy_n(core.committedSamples(0U, 0U), before.size(), before.begin());
    const layerwell::Event arm{0U, 3U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &arm, 1U);
    while (core.snapshot().capture_state == layerwell::CaptureState::waiting_boundary) {
        core.process(left.data(), right.data(), 16U);
    }
    expect(core.snapshot().capture_state == layerwell::CaptureState::recording,
        "replacement reaches recording only at phase zero");
    expect(core.snapshot().capture_write_head == 16U,
        "boundary sample is included in replacement");

    core.process(left.data(), right.data(), 15U);
    expect(core.snapshot().capture_state == layerwell::CaptureState::recording,
        "unsupported shape does not mutate provisional capture state");
    expect(std::memcmp(before.data(), core.committedSamples(0U, 0U),
               before.size() * sizeof(float)) == 0,
        "unsupported shape preserves committed bytes");

    const layerwell::Event cancel{0U, 4U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 16U, &cancel, 1U);
    expect(core.snapshot().capture_state == layerwell::CaptureState::idle,
        "recording capture cancels to idle");
    expect(std::memcmp(before.data(), core.committedSamples(0U, 0U),
               before.size() * sizeof(float)) == 0,
        "recording cancellation preserves committed bytes");
}

void testThreeLayersAndClearLastLoop() {
    layerwell::Core core;
    expect(core.prepare(), "three-layer core prepares");
    std::array<float, 16> left{};
    std::array<float, 16> right{};
    std::uint64_t sequence = 1U;
    auto processEvent = [&](layerwell::EventKind kind, std::uint8_t index = 0U,
                            double value = 0.0) {
        const layerwell::Event event{0U, sequence++, kind, index, value};
        core.process(left.data(), right.data(), 16U, &event, 1U);
    };

    processEvent(layerwell::EventKind::capture_press);
    for (std::uint32_t frame = 16U; frame < layerwell::kMinimumLoopFrames; frame += 16U) {
        core.process(left.data(), right.data(), 16U);
    }
    processEvent(layerwell::EventKind::capture_press);

    for (std::uint8_t layer = 1U; layer < layerwell::kLayerCount; ++layer) {
        processEvent(layerwell::EventKind::select_layer, layer);
        processEvent(layerwell::EventKind::capture_press);
        std::size_t guard = 0U;
        while ((!core.snapshot().layers[layer].occupied
                || core.snapshot().capture_state != layerwell::CaptureState::idle)
            && guard++ < 4000U) {
            core.process(left.data(), right.data(), 16U);
        }
        expect(core.snapshot().layers[layer].occupied,
            "later capture commits selected layer");
    }

    auto snapshot = core.snapshot();
    expect(snapshot.layers[0].occupied
            && snapshot.layers[1].occupied
            && snapshot.layers[2].occupied,
        "all three committed layers coexist");
    expect(snapshot.layers[0].store_owner != snapshot.layers[1].store_owner
            && snapshot.layers[0].store_owner != snapshot.layers[2].store_owner
            && snapshot.layers[1].store_owner != snapshot.layers[2].store_owner,
        "committed layers retain distinct store owners");

    processEvent(layerwell::EventKind::set_layer_pan, 0U, -1.0);
    processEvent(layerwell::EventKind::set_layer_level, 1U, 0.75);
    processEvent(layerwell::EventKind::toggle_layer_mute, 2U);
    snapshot = core.snapshot();
    expect(snapshot.layers[0].pan == -1.0f
            && snapshot.layers[1].level == 0.75f
            && snapshot.layers[2].muted,
        "level pan and mute remain layer-owned while phase stays shared");

    processEvent(layerwell::EventKind::clear_selected_layer);
    expect(core.snapshot().loop_length_frames == layerwell::kMinimumLoopFrames,
        "clearing one layer preserves the session loop");
    processEvent(layerwell::EventKind::select_layer, 1U);
    processEvent(layerwell::EventKind::clear_selected_layer);
    expect(core.snapshot().loop_length_frames == layerwell::kMinimumLoopFrames,
        "clearing two layers preserves the last loop");
    processEvent(layerwell::EventKind::select_layer, 0U);
    processEvent(layerwell::EventKind::clear_selected_layer);
    snapshot = core.snapshot();
    expect(snapshot.loop_length_frames == 0U && snapshot.phase_frames == 0U,
        "clearing the final committed layer returns to no-loop state");
}

void testPartitionIdentityAndSafety() {
    const auto reference = renderTimeline(16U);
    for (const auto block : {64U, 128U, 512U}) {
        const auto candidate = renderTimeline(block);
        expect(candidate.size() == reference.size(), "partition frame count matches");
        expect(std::memcmp(candidate.data(), reference.data(),
                   reference.size() * sizeof(float)) == 0,
            "PCM is byte exact for block " + std::to_string(block));
        expect(std::all_of(candidate.begin(), candidate.end(), [](float value) {
            return std::isfinite(value) && value >= -1.0f && value <= 1.0f;
        }), "partition output is finite and bounded");
    }
}

}  // namespace

int main() {
    testPrepareAndInvalidShape();
    testFirstCaptureAndShortRejection();
    testReplacementCancelAndOverflow();
    testRecordingCancelAndInvalidShapePreserve();
    testThreeLayersAndClearLastLoop();
    testPartitionIdentityAndSafety();
    if (failures != 0) {
        std::cerr << failures << " Layerwell Core test(s) failed\n";
        return 1;
    }
    std::cout << "Layerwell Core tests passed\n";
    return 0;
}
