#include "cinderwheel/juce_midi_adapter.hpp"

#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <new>

namespace {

std::atomic<bool> track_allocations{false};
std::atomic<std::size_t> allocation_count{0};
int failures = 0;

void check(bool condition, const char* expression, int line) {
    if (condition) return;
    std::cerr << "line " << line << ": CHECK(" << expression << ") failed\n";
    ++failures;
}

#define CHECK(condition) check(static_cast<bool>(condition), #condition, __LINE__)

template <std::size_t Size>
void addRaw(
    juce::MidiBuffer& buffer,
    const std::array<std::uint8_t, Size>& bytes,
    int sample_position
) {
    const juce::MidiMessage message(bytes.data(), static_cast<int>(bytes.size()));
    CHECK(message.getRawDataSize() == static_cast<int>(bytes.size()));
    CHECK(buffer.addEvent(message, sample_position));
}

bool sameMidiEvent(
    const cinderwheel::MidiEvent& left,
    const cinderwheel::MidiEvent& right
) {
    return left.sample_offset == right.sample_offset
        && left.ingress_sequence == right.ingress_sequence
        && left.bytes == right.bytes
        && left.size == right.size;
}

bool sameWakeEvent(
    const cinderwheel::WakeEvent& left,
    const cinderwheel::WakeEvent& right
) {
    return left.sample_index == right.sample_index
        && left.ingress_sequence == right.ingress_sequence
        && left.transition_index == right.transition_index
        && left.voice == right.voice
        && left.kind == right.kind
        && left.ledger_energy == right.ledger_energy;
}

void checkDiagnosticsEqual(
    const cinderwheel::Diagnostics& left,
    const cinderwheel::Diagnostics& right
) {
    CHECK(left.processed_frames == right.processed_frames);
    CHECK(left.stage_transitions == right.stage_transitions);
    CHECK(left.primary_strikes == right.primary_strikes);
    CHECK(left.afterstrikes == right.afterstrikes);
    CHECK(left.event_cap_hits == right.event_cap_hits);
    CHECK(left.event_sink_overflows == right.event_sink_overflows);
    CHECK(left.ignored_midi_messages == right.ignored_midi_messages);
    CHECK(left.malformed_midi_messages == right.malformed_midi_messages);
    CHECK(left.midi_events_dropped == right.midi_events_dropped);
    CHECK(left.duplicate_button_edges == right.duplicate_button_edges);
    CHECK(left.non_finite_clears == right.non_finite_clears);
    CHECK(left.reset_count == right.reset_count);
    CHECK(left.panic_count == right.panic_count);
    CHECK(left.unsupported_process_calls == right.unsupported_process_calls);
}

struct RenderedBlock {
    std::array<float, 128> left{};
    std::array<float, 128> right{};
    std::array<cinderwheel::WakeEvent, 16> events{};
    cinderwheel::ProcessReport report{};
};

RenderedBlock processBlock(
    cinderwheel::Core& core,
    const cinderwheel::MidiEvent* events,
    std::size_t event_count
) {
    RenderedBlock rendered;
    rendered.report = core.process(
        rendered.left.data(),
        rendered.right.data(),
        static_cast<std::uint32_t>(rendered.left.size()),
        events,
        event_count,
        rendered.events.data(),
        rendered.events.size()
    );
    return rendered;
}

void checkRenderedEqual(const RenderedBlock& left, const RenderedBlock& right) {
    CHECK(left.left == right.left);
    CHECK(left.right == right.right);
    CHECK(left.report.events_written == right.report.events_written);
    CHECK(left.report.events_dropped == right.report.events_dropped);
    for (std::size_t index = 0; index < left.report.events_written; ++index) {
        CHECK(sameWakeEvent(left.events[index], right.events[index]));
    }
}

void testOfflineParityAndLifecycle() {
    constexpr std::uint32_t block_frames = 128;
    cinderwheel::Core adapted_core;
    cinderwheel::Core direct_core;
    CHECK(adapted_core.prepare(cinderwheel::kReferenceSampleRate, block_frames));
    CHECK(direct_core.prepare(cinderwheel::kReferenceSampleRate, block_frames));

    cinderwheel::JuceMidiAdapter adapter;
    juce::MidiBuffer source;
    source.ensureSize(1024);
    addRaw(source, std::array<std::uint8_t, 3>{0xBFU, 33U, 127U}, 0);
    addRaw(source, std::array<std::uint8_t, 3>{0xBFU, 35U, 80U}, 0);
    addRaw(source, std::array<std::uint8_t, 3>{0xBFU, 24U, 127U}, 0);
    addRaw(source, std::array<std::uint8_t, 3>{0xBFU, 20U, 100U}, 0);
    addRaw(source, std::array<std::uint8_t, 3>{0xBEU, 20U, 64U}, 4);
    addRaw(source, std::array<std::uint8_t, 3>{0xBFU, 36U, 64U}, 4);
    addRaw(source, std::array<std::uint8_t, 3>{0xBFU, 40U, 64U}, 8);
    addRaw(source, std::array<std::uint8_t, 3>{0x9FU, 60U, 100U}, 9);
    addRaw(source, std::array<std::uint8_t, 2>{0xCFU, 7U}, 10);
    addRaw(source, std::array<std::uint8_t, 4>{0xF0U, 1U, 2U, 0xF7U}, 200);

    const std::array<cinderwheel::MidiEvent, 10> expected{{
        {0, 1, {0xBFU, 33U, 127U}, 3},
        {0, 2, {0xBFU, 35U, 80U}, 3},
        {0, 3, {0xBFU, 24U, 127U}, 3},
        {0, 4, {0xBFU, 20U, 100U}, 3},
        {4, 5, {0xBEU, 20U, 64U}, 3},
        {4, 6, {0xBFU, 36U, 64U}, 3},
        {8, 7, {0xBFU, 40U, 64U}, 3},
        {9, 8, {0x9FU, 60U, 100U}, 3},
        {10, 9, {0xCFU, 7U, 0U}, 2},
        {127, 10, {0xF0U, 1U, 2U}, 4},
    }};

    allocation_count.store(0, std::memory_order_release);
    track_allocations.store(true, std::memory_order_release);
    const auto adapted = adapter.adapt(source, block_frames, adapted_core);
    const auto adapted_render = processBlock(
        adapted_core,
        adapted.events,
        adapted.event_count
    );
    track_allocations.store(false, std::memory_order_release);
    CHECK(allocation_count.load(std::memory_order_acquire) == 0);
    CHECK(adapted.event_count == expected.size());
    CHECK(adapted.dropped_events == 0);
    for (std::size_t index = 0; index < expected.size(); ++index) {
        CHECK(sameMidiEvent(adapted.events[index], expected[index]));
    }

    const auto direct_render = processBlock(direct_core, expected.data(), expected.size());
    checkRenderedEqual(adapted_render, direct_render);

    bool observed_wake_event = false;
    juce::MidiBuffer empty;
    for (int block = 1; block < 64; ++block) {
        const auto empty_adapted = adapter.adapt(empty, block_frames, adapted_core);
        const auto left = processBlock(
            adapted_core,
            empty_adapted.events,
            empty_adapted.event_count
        );
        const auto right = processBlock(direct_core, nullptr, 0);
        checkRenderedEqual(left, right);
        observed_wake_event = observed_wake_event || left.report.events_written > 0;
    }
    CHECK(observed_wake_event);
    checkDiagnosticsEqual(adapted_core.diagnostics(), direct_core.diagnostics());
    CHECK(adapted_core.diagnostics().ignored_midi_messages == 3);
    CHECK(adapted_core.diagnostics().malformed_midi_messages == 3);

    adapted_core.reset();
    direct_core.reset();
    adapter.reset();
    juce::MidiBuffer restarted_source;
    addRaw(restarted_source, std::array<std::uint8_t, 3>{0xBFU, 20U, 127U}, 0);
    const auto restarted = adapter.adapt(restarted_source, block_frames, adapted_core);
    CHECK(restarted.event_count == 1);
    CHECK(restarted.events[0].ingress_sequence == 1);
    const std::array<cinderwheel::MidiEvent, 1> restarted_direct{{
        {0, 1, {0xBFU, 20U, 127U}, 3},
    }};
    checkRenderedEqual(
        processBlock(adapted_core, restarted.events, restarted.event_count),
        processBlock(direct_core, restarted_direct.data(), restarted_direct.size())
    );
    checkDiagnosticsEqual(adapted_core.diagnostics(), direct_core.diagnostics());
}

void testCapacityAndMalformedSizes() {
    cinderwheel::Core overflow_core;
    CHECK(overflow_core.prepare(cinderwheel::kReferenceSampleRate, 1));
    cinderwheel::JuceMidiAdapter overflow_adapter;
    juce::MidiBuffer overflow_source;
    overflow_source.ensureSize(8192);
    for (std::size_t index = 0; index < cinderwheel::kMaximumMidiEventsPerBlock + 2U; ++index) {
        addRaw(
            overflow_source,
            std::array<std::uint8_t, 3>{
                0xBFU,
                20U,
                static_cast<std::uint8_t>(index % 128U),
            },
            0
        );
    }

    const auto overflow = overflow_adapter.adapt(overflow_source, 1, overflow_core);
    CHECK(overflow.event_count == cinderwheel::kMaximumMidiEventsPerBlock);
    CHECK(overflow.dropped_events == 2);
    CHECK(overflow_core.diagnostics().midi_events_dropped == 2);
    std::array<float, 1> left{};
    std::array<float, 1> right{};
    overflow_core.process(
        left.data(),
        right.data(),
        1,
        overflow.events,
        overflow.event_count
    );
    CHECK(overflow_core.diagnostics().midi_events_dropped == 2);

    juce::MidiBuffer next_source;
    addRaw(next_source, std::array<std::uint8_t, 3>{0xBFU, 20U, 64U}, 0);
    const auto next = overflow_adapter.adapt(next_source, 1, overflow_core);
    CHECK(next.event_count == 1);
    CHECK(next.events[0].ingress_sequence == 131);
    overflow_adapter.reset();
    const auto reset = overflow_adapter.adapt(next_source, 1, overflow_core);
    CHECK(reset.events[0].ingress_sequence == 1);

    cinderwheel::Core malformed_core;
    CHECK(malformed_core.prepare(cinderwheel::kReferenceSampleRate, 2));
    cinderwheel::JuceMidiAdapter malformed_adapter;
    juce::MidiBuffer malformed_source;
    addRaw(malformed_source, std::array<std::uint8_t, 2>{0xCFU, 7U}, 0);
    addRaw(malformed_source, std::array<std::uint8_t, 4>{0xF0U, 1U, 2U, 0xF7U}, 1);
    const auto malformed = malformed_adapter.adapt(malformed_source, 2, malformed_core);
    CHECK(malformed.event_count == 2);
    CHECK(malformed.events[0].size == 2);
    CHECK(malformed.events[1].size == 4);
    std::array<float, 2> malformed_left{};
    std::array<float, 2> malformed_right{};
    malformed_core.process(
        malformed_left.data(),
        malformed_right.data(),
        2,
        malformed.events,
        malformed.event_count
    );
    CHECK(malformed_core.diagnostics().malformed_midi_messages == 2);
}

}  // namespace

void* operator new(std::size_t size) {
    if (track_allocations.load(std::memory_order_acquire)) {
        allocation_count.fetch_add(1, std::memory_order_relaxed);
    }
    if (void* memory = std::malloc(size); memory != nullptr) return memory;
    throw std::bad_alloc();
}

void operator delete(void* memory) noexcept {
    std::free(memory);
}

void operator delete(void* memory, std::size_t) noexcept {
    std::free(memory);
}

int main() {
    testOfflineParityAndLifecycle();
    testCapacityAndMalformedSizes();
    if (failures != 0) {
        std::cerr << "Cinderwheel JUCE adapter checks: " << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "Cinderwheel JUCE adapter checks: PASS\n";
    return 0;
}
