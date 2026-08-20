#include "tidepit/core.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <new>
#include <string_view>
#include <thread>
#include <type_traits>
#include <utility>
#include <vector>

namespace allocation_probe {
std::atomic<bool> tracking{false};
std::atomic<std::size_t> count{0};
}  // namespace allocation_probe

void* operator new(std::size_t size) {
    if (allocation_probe::tracking.load(std::memory_order_relaxed)) {
        allocation_probe::count.fetch_add(1, std::memory_order_relaxed);
    }
    if (void* memory = std::malloc(size == 0 ? 1 : size); memory != nullptr) return memory;
    throw std::bad_alloc();
}

void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

namespace {

int failures = 0;

void check(bool condition, const char* expression, const char* file, int line) {
    if (condition) return;
    ++failures;
    std::cerr << file << ':' << line << ": CHECK failed: " << expression << '\n';
}

#define CHECK(expression) check(static_cast<bool>(expression), #expression, __FILE__, __LINE__)

bool close(double left, double right, double tolerance = 1.0e-6) {
    return std::abs(left - right) <= tolerance;
}

struct ScheduledEvent {
    std::uint64_t sample{};
    std::uint64_t sequence{};
    tidepit::SemanticAction action{tidepit::SemanticAction::set_stage_1};
    double value{};
};

struct RenderResult {
    std::vector<std::int32_t> left;
    std::vector<std::int32_t> right;
    tidepit::Snapshot snapshot{};
};

bool sameControls(const tidepit::Controls& left, const tidepit::Controls& right) {
    return left.stages == right.stages
        && left.rate == right.rate
        && left.memory == right.memory
        && left.material == right.material
        && left.position == right.position
        && left.fx_a == right.fx_a
        && left.fx_b == right.fx_b
        && left.root_note == right.root_note;
}

bool sameSnapshot(const tidepit::Snapshot& left, const tidepit::Snapshot& right) {
    return sameControls(left.controls, right.controls)
        && left.effect_parameters == right.effect_parameters
        && left.mutation == right.mutation
        && left.display_lines == right.display_lines
        && left.effective_fx_a == right.effective_fx_a
        && left.effective_fx_b == right.effective_fx_b
        && left.effect_crossfade == right.effect_crossfade
        && left.absolute_sample == right.absolute_sample
        && left.record_write_head == right.record_write_head
        && left.stage == right.stage
        && left.sympathetic_division == right.sympathetic_division
        && left.source == right.source
        && left.scale == right.scale
        && left.effect == right.effect
        && left.target == right.target
        && left.locked == right.locked
        && left.captured == right.captured
        && left.fx_a_pickup_active == right.fx_a_pickup_active
        && left.fx_b_pickup_active == right.fx_b_pickup_active
        && left.granular_available == right.granular_available
        && left.prepared == right.prepared;
}

void processBlocks(
    tidepit::Core& core,
    std::size_t block_count,
    const tidepit::SemanticEvent* first_event = nullptr
) {
    std::array<std::int32_t, tidepit::kReferenceQuantumFrames> left{};
    std::array<std::int32_t, tidepit::kReferenceQuantumFrames> right{};
    for (std::size_t block = 0; block < block_count; ++block) {
        const auto report = core.processQ27(
            left.data(),
            right.data(),
            tidepit::kReferenceQuantumFrames,
            block == 0 ? first_event : nullptr,
            block == 0 && first_event != nullptr ? 1U : 0U
        );
        CHECK(report.events_dropped == 0);
    }
}

void performEffectTap(tidepit::Core& core, std::uint64_t sequence) {
    const tidepit::SemanticEvent event{
        0, sequence, tidepit::SemanticAction::effect_next, 0.0,
    };
    processBlocks(core, 152, &event);
}

RenderResult render(
    tidepit::Core& core,
    std::uint64_t frames,
    std::uint32_t partition,
    const std::vector<ScheduledEvent>& events = {}
) {
    RenderResult result;
    result.left.resize(static_cast<std::size_t>(frames));
    result.right.resize(static_cast<std::size_t>(frames));
    std::uint64_t rendered = 0;
    std::size_t event_index = 0;
    while (rendered < frames) {
        const auto count = static_cast<std::uint32_t>(
            std::min<std::uint64_t>(partition, frames - rendered)
        );
        std::array<tidepit::SemanticEvent, 32> block_events{};
        std::size_t block_event_count = 0;
        while (event_index < events.size() && events[event_index].sample < rendered + count) {
            CHECK(events[event_index].sample >= rendered);
            CHECK(block_event_count < block_events.size());
            if (block_event_count < block_events.size()) {
                const auto& source = events[event_index];
                block_events[block_event_count++] = {
                    static_cast<std::uint32_t>(source.sample - rendered),
                    source.sequence,
                    source.action,
                    source.value,
                };
            }
            ++event_index;
        }
        const auto report = core.processQ27(
            result.left.data() + static_cast<std::ptrdiff_t>(rendered),
            result.right.data() + static_cast<std::ptrdiff_t>(rendered),
            count,
            block_events.data(),
            block_event_count
        );
        CHECK(report.events_dropped == 0);
        rendered += count;
    }
    CHECK(event_index == events.size());
    result.snapshot = core.snapshot();
    return result;
}

void testPrepareDefaultsDisplayAndAllocation() {
    static_assert(std::is_trivially_copyable_v<tidepit::Controls>);
    static_assert(std::is_trivially_copyable_v<tidepit::Diagnostics>);
    static_assert(std::is_trivially_copyable_v<tidepit::Snapshot>);
    static_assert(std::is_trivially_copyable_v<tidepit::SemanticEvent>);

    tidepit::Core invalid;
    CHECK(!invalid.isPrepared());
    CHECK(!invalid.prepare(std::numeric_limits<double>::quiet_NaN()));
    CHECK(!invalid.prepare(44100.0));
    CHECK(!invalid.prepare(96000.0));
    CHECK(!invalid.prepare(48000.0, 0));
    CHECK(!invalid.prepare(48000.0, 17));
    CHECK(!invalid.prepare(48000.0, 513));
    std::array<std::int32_t, 16> invalid_left{};
    std::array<std::int32_t, 16> invalid_right{};
    invalid_left.fill(9);
    invalid_right.fill(9);
    invalid.processQ27(invalid_left.data(), invalid_right.data(), 16);
    CHECK(std::all_of(invalid_left.begin(), invalid_left.end(), [](auto value) { return value == 0; }));
    CHECK(!invalid.isPrepared());
    CHECK(invalid.prepare(48000.0, 16));
    CHECK(invalid.isPrepared());

    tidepit::Core core;
    CHECK(core.prepare(48000.0));
    CHECK(core.isPrepared());
    CHECK(core.sampleRate() == tidepit::kReferenceSampleRate);
    const auto initial = core.snapshot();
    CHECK(initial.prepared);
    CHECK(initial.controls.root_note == 60);
    CHECK(initial.controls.stages == (std::array<float, 4>{{0.20f, 0.50f, 0.80f, 0.30f}}));
    CHECK(initial.source == tidepit::SourceMode::reed);
    CHECK(initial.scale == tidepit::ScaleMode::maj5);
    CHECK(initial.effect == tidepit::EffectMode::clean);
    CHECK(initial.effect_crossfade == 1.0f);
    CHECK(initial.target == tidepit::WaveTarget::pitch);
    CHECK(!initial.locked);
    CHECK(!initial.captured);
    CHECK(initial.stage == 0);
    CHECK(initial.sympathetic_division == 2);
    CHECK(initial.granular_available);
    CHECK(std::string_view(initial.display_lines[0].data()) == "TIDE PIT PIT    C 4  ");
    CHECK(std::string_view(initial.display_lines[1].data()) == "WAVE 0-0-0-0 STEP 1  ");
    CHECK(std::string_view(initial.display_lines[2].data()) == "M74 S49 D49 CLEAN    ");
    CHECK(std::string_view(initial.display_lines[3].data()) == "MAJ5  REED EVOLVE    ");

    const auto prepared_diagnostics = core.diagnostics();
    CHECK(prepared_diagnostics.arena_allocations == tidepit::kSourceArenaAllocations);
    CHECK(prepared_diagnostics.arena_bytes == tidepit::kSourceArenaBytes);
    CHECK(prepared_diagnostics.arena_alignment_valid);

    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    allocation_probe::count.store(0, std::memory_order_relaxed);
    allocation_probe::tracking.store(true, std::memory_order_release);
    for (std::size_t block = 0; block < 64; ++block) {
        core.processQ27(left.data(), right.data(), 16);
    }
    allocation_probe::tracking.store(false, std::memory_order_release);
    CHECK(allocation_probe::count.load(std::memory_order_relaxed) == 0);

    const auto displayed = core.snapshot();
    CHECK(displayed.absolute_sample == 1024);
    CHECK(displayed.record_write_head == 1024);
    CHECK(close(displayed.effective_fx_a, 0.60));
    CHECK(close(displayed.effective_fx_b, 0.35));
    CHECK(std::string_view(displayed.display_lines[1].data()) == "WAVE 1-4-7-2 STEP 1  ");
    CHECK(std::string_view(displayed.display_lines[2].data()) == "M77 S59 D34 CLEAN    ");

    CHECK(core.setControlNormalized(tidepit::SemanticAction::set_root, 1.0));
    CHECK(core.snapshot().controls.root_note == 72);
    CHECK(core.setControlNormalized(tidepit::SemanticAction::set_stage_1, 0.25));
    CHECK(close(core.snapshot().controls.stages[0], 0.25));
    CHECK(!core.setControlNormalized(tidepit::SemanticAction::mutate, 1.0));
}

void testScaleTargetAndHarmPreservation() {
    CHECK(tidepit::scaleIntervals(tidepit::ScaleMode::maj5) ==
          (std::array<std::int8_t, 6>{{0, 2, 4, 7, 9, 12}}));
    CHECK(tidepit::scaleIntervals(tidepit::ScaleMode::min5) ==
          (std::array<std::int8_t, 6>{{0, 2, 3, 5, 7, 10}}));
    CHECK(tidepit::scaleIntervals(tidepit::ScaleMode::dorian) ==
          (std::array<std::int8_t, 6>{{0, 2, 3, 5, 7, 9}}));
    CHECK(tidepit::scaleIntervals(tidepit::ScaleMode::harm) ==
          (std::array<std::int8_t, 6>{{0, 3, 5, 7, 10, 12}}));
    CHECK(std::string_view(tidepit::scaleName(tidepit::ScaleMode::harm)) == "HARM");

    tidepit::Core scale;
    CHECK(scale.prepare(48000.0, 16));
    tidepit::SemanticEvent scale_event{0, 1, tidepit::SemanticAction::scale_next, 0.0};
    processBlocks(scale, 17, &scale_event);
    CHECK(scale.snapshot().scale == tidepit::ScaleMode::maj5);
    processBlocks(scale, 1);
    CHECK(scale.snapshot().scale == tidepit::ScaleMode::min5);
    scale_event.ingress_sequence = 2;
    processBlocks(scale, 18, &scale_event);
    scale_event.ingress_sequence = 3;
    processBlocks(scale, 18, &scale_event);
    CHECK(scale.snapshot().scale == tidepit::ScaleMode::harm);

    tidepit::Core target;
    CHECK(target.prepare(48000.0, 16));
    const tidepit::SemanticEvent target_event{
        0, 1, tidepit::SemanticAction::target_next, 0.0,
    };
    processBlocks(target, 1507, &target_event);
    CHECK(target.snapshot().target == tidepit::WaveTarget::pitch);
    CHECK(target.snapshot().scale == tidepit::ScaleMode::maj5);
    processBlocks(target, 1);
    CHECK(target.snapshot().target == tidepit::WaveTarget::body);
    CHECK(target.snapshot().scale == tidepit::ScaleMode::maj5);
    processBlocks(target, 9);
    scale_event.ingress_sequence = 2;
    processBlocks(target, 18, &scale_event);
    CHECK(target.snapshot().scale == tidepit::ScaleMode::min5);
    CHECK(target.snapshot().target == tidepit::WaveTarget::body);
}

void testMutationAndLock() {
    tidepit::Core core;
    CHECK(core.prepare(48000.0, 16));
    const tidepit::SemanticEvent mutate{
        0, 1, tidepit::SemanticAction::mutate, 0.0,
    };
    processBlocks(core, 1, &mutate);
    const auto manually_mutated = core.snapshot().mutation;
    CHECK(manually_mutated != (std::array<std::int8_t, 4>{{0, 0, 0, 0}}));
    processBlocks(core, 1);

    const tidepit::SemanticEvent lock{
        0, 2, tidepit::SemanticAction::lock_toggle, 0.0,
    };
    processBlocks(core, 1, &lock);
    CHECK(core.snapshot().locked);
    processBlocks(core, 1);
    CHECK(core.setControlNormalized(tidepit::SemanticAction::set_rate, 1.0));
    CHECK(core.setControlNormalized(tidepit::SemanticAction::set_memory, 0.0));
    processBlocks(core, 1200);
    CHECK(core.snapshot().mutation == manually_mutated);

    const tidepit::SemanticEvent unlock{
        0, 3, tidepit::SemanticAction::lock_toggle, 0.0,
    };
    processBlocks(core, 1, &unlock);
    CHECK(!core.snapshot().locked);
    processBlocks(core, 600);
    CHECK(core.snapshot().mutation != manually_mutated);
    CHECK(core.diagnostics().manual_mutations == 1);
}

void testEffectAndCaptureGestureBoundaries() {
    tidepit::Core effect;
    CHECK(effect.prepare(48000.0, 16));
    const tidepit::SemanticEvent effect_event{
        0, 1, tidepit::SemanticAction::effect_next, 0.0,
    };
    processBlocks(effect, 151, &effect_event);
    CHECK(effect.snapshot().effect == tidepit::EffectMode::clean);
    processBlocks(effect, 1);
    CHECK(effect.snapshot().effect == tidepit::EffectMode::filter);
    CHECK(effect.snapshot().effect_crossfade == 16.0f / 1024.0f);
    CHECK(!effect.snapshot().captured);
    processBlocks(effect, 62);
    CHECK(effect.snapshot().effect_crossfade == 1008.0f / 1024.0f);
    processBlocks(effect, 1);
    CHECK(effect.snapshot().effect_crossfade == 1.0f);

    tidepit::Core capture;
    CHECK(capture.prepare(48000.0, 16));
    const tidepit::SemanticEvent capture_event{
        0, 1, tidepit::SemanticAction::capture_toggle, 0.0,
    };
    processBlocks(capture, 1574, &capture_event);
    CHECK(!capture.snapshot().captured);
    processBlocks(capture, 1);
    CHECK(capture.snapshot().captured);
    const auto frozen_head = capture.snapshot().record_write_head;
    processBlocks(capture, 100);
    CHECK(capture.snapshot().record_write_head == frozen_head);
    CHECK(capture.snapshot().effect == tidepit::EffectMode::clean);

    processBlocks(capture, 1, &capture_event);
    processBlocks(capture, 1574);
    CHECK(!capture.snapshot().captured);
    CHECK(capture.snapshot().record_write_head != frozen_head);
    CHECK(capture.snapshot().effect == tidepit::EffectMode::clean);
}

void testContextualEffectPickup() {
    tidepit::Core core;
    CHECK(core.prepare(48000.0, 16));
    processBlocks(core, 1);
    CHECK(close(core.snapshot().effective_fx_a, 0.60));
    CHECK(close(core.snapshot().effective_fx_b, 0.35));

    performEffectTap(core, 1);
    CHECK(core.snapshot().effect == tidepit::EffectMode::filter);
    CHECK(close(core.snapshot().effective_fx_a, 0.60));
    CHECK(close(core.snapshot().effective_fx_b, 0.35));
    const std::array<tidepit::SemanticEvent, 2> high{{
        {0, 2, tidepit::SemanticAction::set_fx_a, 0.90},
        {0, 3, tidepit::SemanticAction::set_fx_b, 0.90},
    }};
    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    core.processQ27(left.data(), right.data(), 16, high.data(), high.size());
    CHECK(close(core.snapshot().effective_fx_a, 0.90));
    CHECK(close(core.snapshot().effective_fx_b, 0.90));

    performEffectTap(core, 4);
    CHECK(core.snapshot().effect == tidepit::EffectMode::drive);
    CHECK(close(core.snapshot().effective_fx_a, 0.90));
    const std::array<tidepit::SemanticEvent, 2> low{{
        {0, 5, tidepit::SemanticAction::set_fx_a, 0.20},
        {0, 6, tidepit::SemanticAction::set_fx_b, 0.20},
    }};
    core.processQ27(left.data(), right.data(), 16, low.data(), low.size());
    CHECK(close(core.snapshot().effective_fx_a, 0.20));

    performEffectTap(core, 7);
    auto state = core.snapshot();
    CHECK(state.effect == tidepit::EffectMode::clean);
    CHECK(close(state.controls.fx_a, 0.20));
    CHECK(close(state.effective_fx_a, 0.60));
    CHECK(close(state.effective_fx_b, 0.35));
    CHECK(!state.fx_a_pickup_active);
    CHECK(!state.fx_b_pickup_active);

    const std::array<tidepit::SemanticEvent, 2> crossed{{
        {0, 8, tidepit::SemanticAction::set_fx_a, 0.59},
        {0, 9, tidepit::SemanticAction::set_fx_b, 0.90},
    }};
    core.processQ27(left.data(), right.data(), 16, crossed.data(), crossed.size());
    state = core.snapshot();
    CHECK(state.fx_a_pickup_active);
    CHECK(state.fx_b_pickup_active);
    CHECK(close(state.effective_fx_a, 0.59));
    CHECK(close(state.effective_fx_b, 0.90));
}

void testPartitionAndQuantization() {
    const std::vector<ScheduledEvent> schedule{
        {1, 1, tidepit::SemanticAction::set_root, 72.0},
        {17, 2, tidepit::SemanticAction::set_stage_1, 0.11},
        {257, 3, tidepit::SemanticAction::source_next, 0.0},
        {513, 4, tidepit::SemanticAction::mutate, 0.0},
        {1025, 5, tidepit::SemanticAction::lock_toggle, 0.0},
        {1537, 6, tidepit::SemanticAction::lock_toggle, 0.0},
        {2049, 7, tidepit::SemanticAction::effect_next, 0.0},
        {8193, 8, tidepit::SemanticAction::set_fx_a, 0.73},
        {12289, 9, tidepit::SemanticAction::scale_next, 0.0},
        {16385, 10, tidepit::SemanticAction::set_position, 0.77},
    };

    std::vector<RenderResult> results;
    for (const auto partition : {16U, 64U, 128U, 512U}) {
        tidepit::Core core;
        CHECK(core.prepare(48000.0, partition));
        results.push_back(render(core, 32768, partition, schedule));
    }
    for (std::size_t index = 1; index < results.size(); ++index) {
        CHECK(results[index].left == results[0].left);
        CHECK(results[index].right == results[0].right);
        CHECK(sameSnapshot(results[index].snapshot, results[0].snapshot));
    }

    tidepit::Core quantized;
    CHECK(quantized.prepare(48000.0, 16));
    const tidepit::SemanticEvent future{
        1, 1, tidepit::SemanticAction::set_root, 72.0,
    };
    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    auto report = quantized.processQ27(left.data(), right.data(), 16, &future, 1);
    CHECK(report.events_accepted == 1);
    CHECK(quantized.snapshot().controls.root_note == 60);
    CHECK(quantized.diagnostics().pending_events == 1);
    quantized.processQ27(left.data(), right.data(), 16);
    CHECK(quantized.snapshot().controls.root_note == 72);
    CHECK(quantized.diagnostics().pending_events == 0);

    tidepit::Core block_end;
    CHECK(block_end.prepare(48000.0, 16));
    const tidepit::SemanticEvent at_block_end{
        16, 1, tidepit::SemanticAction::set_root, 36.0,
    };
    block_end.processQ27(left.data(), right.data(), 16, &at_block_end, 1);
    CHECK(block_end.snapshot().controls.root_note == 60);
    CHECK(block_end.diagnostics().pending_events == 1);
    block_end.processQ27(left.data(), right.data(), 16);
    CHECK(block_end.snapshot().controls.root_note == 36);

    tidepit::Core ordered;
    CHECK(ordered.prepare(48000.0, 16));
    const std::array<tidepit::SemanticEvent, 2> reverse_ingress{{
        {16, 2, tidepit::SemanticAction::set_stage_1, 0.20},
        {16, 1, tidepit::SemanticAction::set_stage_1, 0.80},
    }};
    ordered.processQ27(
        left.data(), right.data(), 16, reverse_ingress.data(), reverse_ingress.size()
    );
    ordered.processQ27(left.data(), right.data(), 16);
    CHECK(close(ordered.snapshot().controls.stages[0], 0.20));
}

void testIndependentInstancesAndAudioThreads() {
    constexpr std::uint64_t frames = 8192;
    tidepit::Core reference;
    CHECK(reference.prepare(48000.0, 128));
    const auto expected = render(reference, frames, 128);

    tidepit::Core interleaved_first;
    tidepit::Core interleaved_second;
    CHECK(interleaved_first.prepare(48000.0, 128));
    CHECK(interleaved_second.prepare(48000.0, 128));
    RenderResult interleaved_first_result;
    RenderResult interleaved_second_result;
    interleaved_first_result.left.resize(frames);
    interleaved_first_result.right.resize(frames);
    interleaved_second_result.left.resize(frames);
    interleaved_second_result.right.resize(frames);
    for (std::uint64_t offset = 0; offset < frames; offset += 128U) {
        interleaved_first.processQ27(
            interleaved_first_result.left.data() + static_cast<std::ptrdiff_t>(offset),
            interleaved_first_result.right.data() + static_cast<std::ptrdiff_t>(offset),
            128
        );
        interleaved_second.processQ27(
            interleaved_second_result.left.data() + static_cast<std::ptrdiff_t>(offset),
            interleaved_second_result.right.data() + static_cast<std::ptrdiff_t>(offset),
            128
        );
    }
    CHECK(interleaved_first_result.left == expected.left);
    CHECK(interleaved_first_result.right == expected.right);
    CHECK(interleaved_second_result.left == expected.left);
    CHECK(interleaved_second_result.right == expected.right);

    tidepit::Core first;
    tidepit::Core second;
    CHECK(first.prepare(48000.0, 128));
    CHECK(second.prepare(48000.0, 128));
    RenderResult first_result;
    RenderResult second_result;
    std::thread first_thread([&] { first_result = render(first, frames, 128); });
    std::thread second_thread([&] { second_result = render(second, frames, 128); });
    first_thread.join();
    second_thread.join();

    CHECK(first_result.left == expected.left);
    CHECK(first_result.right == expected.right);
    CHECK(second_result.left == expected.left);
    CHECK(second_result.right == expected.right);
}

void testInvalidEventsAndCapacity() {
    tidepit::Core core;
    CHECK(core.prepare(48000.0, 16));
    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    left.fill(7);
    right.fill(7);
    core.processQ27(left.data(), right.data(), 8);
    CHECK(std::all_of(left.begin(), left.begin() + 8, [](auto value) { return value == 0; }));
    CHECK(core.diagnostics().unsupported_process_calls == 1);

    const std::array<tidepit::SemanticEvent, 5> invalid{{
        {17, 1, tidepit::SemanticAction::set_rate, 0.5},
        {0, 2, static_cast<tidepit::SemanticAction>(255), 0.0},
        {0, 3, tidepit::SemanticAction::set_memory, 1.1},
        {0, 4, tidepit::SemanticAction::set_root, 35.0},
        {0, 5, tidepit::SemanticAction::set_fx_a,
         std::numeric_limits<double>::quiet_NaN()},
    }};
    const auto invalid_report = core.processQ27(
        left.data(), right.data(), 16, invalid.data(), invalid.size()
    );
    CHECK(invalid_report.events_accepted == 0);
    CHECK(invalid_report.events_dropped == invalid.size());
    CHECK(core.diagnostics().invalid_events >= invalid.size());
    CHECK(core.diagnostics().non_finite_controls >= 1);

    std::array<tidepit::SemanticEvent, tidepit::kMaximumSemanticEvents + 1U> queued{};
    for (std::size_t index = 0; index < queued.size(); ++index) {
        queued[index] = {
            16,
            static_cast<std::uint64_t>(100 + index),
            tidepit::SemanticAction::set_stage_1,
            static_cast<double>(index % 100U) / 100.0,
        };
    }
    const auto capacity_report = core.processQ27(
        left.data(), right.data(), 16, queued.data(), queued.size()
    );
    CHECK(capacity_report.events_accepted == tidepit::kMaximumSemanticEvents);
    CHECK(capacity_report.events_dropped == 1);
    CHECK(core.diagnostics().pending_events == tidepit::kMaximumSemanticEvents);
    core.processQ27(left.data(), right.data(), 16);
    CHECK(core.diagnostics().pending_events == 0);

    const auto null_report = core.processQ27(left.data(), right.data(), 16, nullptr, 1);
    CHECK(null_report.events_dropped == 1);
    CHECK(core.diagnostics().unsupported_process_calls == 2);
    CHECK(!core.setControlNormalized(
        tidepit::SemanticAction::set_rate,
        std::numeric_limits<double>::infinity()
    ));
}

}  // namespace

int main() {
    testPrepareDefaultsDisplayAndAllocation();
    testScaleTargetAndHarmPreservation();
    testMutationAndLock();
    testEffectAndCaptureGestureBoundaries();
    testContextualEffectPickup();
    testPartitionAndQuantization();
    testIndependentInstancesAndAudioThreads();
    testInvalidEventsAndCapacity();
    if (failures != 0) {
        std::cerr << failures << " Tide Pit Core checks failed\n";
        return 1;
    }
    std::cout << "Tide Pit Core checks passed\n";
    return 0;
}
