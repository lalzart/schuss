#include "tidepit/juce_midi_adapter.hpp"

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

bool sameEvent(const tidepit::SemanticEvent& left, const tidepit::SemanticEvent& right) {
    return left.sample_offset == right.sample_offset
        && left.ingress_sequence == right.ingress_sequence
        && left.action == right.action
        && left.value == right.value;
}

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

bool sameDiagnostics(
    const tidepit::Diagnostics& left,
    const tidepit::Diagnostics& right
) {
    return left.processed_frames == right.processed_frames
        && left.processed_quanta == right.processed_quanta
        && left.semantic_events_accepted == right.semantic_events_accepted
        && left.semantic_events_dropped == right.semantic_events_dropped
        && left.invalid_events == right.invalid_events
        && left.non_finite_controls == right.non_finite_controls
        && left.unsupported_process_calls == right.unsupported_process_calls
        && left.prepare_failures == right.prepare_failures
        && left.manual_mutations == right.manual_mutations
        && left.gesture_queue_overflows == right.gesture_queue_overflows
        && left.pending_events == right.pending_events
        && left.arena_allocations == right.arena_allocations
        && left.arena_bytes == right.arena_bytes
        && left.arena_alignment_valid == right.arena_alignment_valid;
}

struct RenderedQuantum {
    std::array<std::int32_t, tidepit::kReferenceQuantumFrames> left{};
    std::array<std::int32_t, tidepit::kReferenceQuantumFrames> right{};
    tidepit::ProcessReport report{};
};

RenderedQuantum render(
    tidepit::Core& core,
    const tidepit::SemanticEvent* events,
    std::size_t event_count
) {
    RenderedQuantum result;
    result.report = core.processQ27(
        result.left.data(),
        result.right.data(),
        tidepit::kReferenceQuantumFrames,
        events,
        event_count
    );
    return result;
}

void checkCoreParity(
    tidepit::Core& adapted_core,
    tidepit::Core& direct_core,
    const tidepit::SemanticEvent* adapted_events,
    std::size_t adapted_count,
    const tidepit::SemanticEvent* direct_events,
    std::size_t direct_count
) {
    const auto adapted = render(adapted_core, adapted_events, adapted_count);
    const auto direct = render(direct_core, direct_events, direct_count);
    CHECK(adapted.left == direct.left);
    CHECK(adapted.right == direct.right);
    CHECK(adapted.report.events_accepted == direct.report.events_accepted);
    CHECK(adapted.report.events_dropped == direct.report.events_dropped);
    CHECK(sameSnapshot(adapted_core.snapshot(), direct_core.snapshot()));
    CHECK(sameDiagnostics(adapted_core.diagnostics(), direct_core.diagnostics()));
}

void testRawParsingOrderAndDiagnostics() {
    tidepit::JuceMidiAdapter adapter;
    juce::MidiBuffer source;
    source.ensureSize(4096);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 30U, 127U}, 0);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 20U, 64U}, 0);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 40U, 127U}, 5);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 40U, 0U}, 6);
    addRaw(source, std::array<std::uint8_t, 3>{0xbeU, 20U, 64U}, 7);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 31U, 64U}, 8);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 19U, 64U}, 9);
    addRaw(source, std::array<std::uint8_t, 3>{0x9fU, 60U, 100U}, 10);
    addRaw(source, std::array<std::uint8_t, 2>{0xcfU, 7U}, 11);
    addRaw(source, std::array<std::uint8_t, 4>{0xf0U, 1U, 2U, 0xf7U}, 12);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 41U, 64U}, 13);
    addRaw(source, std::array<std::uint8_t, 3>{0xbfU, 21U, 100U}, 200);

    allocation_count.store(0, std::memory_order_release);
    track_allocations.store(true, std::memory_order_release);
    const auto adapted = adapter.adapt(source, 16);
    track_allocations.store(false, std::memory_order_release);
    CHECK(allocation_count.load(std::memory_order_acquire) == 0);
    CHECK(adapted.event_count == 4);
    CHECK(adapted.dropped_events == 0);
    const std::array<tidepit::SemanticEvent, 4> expected{{
        {0, 1, tidepit::SemanticAction::set_root, 72.0},
        {0, 2, tidepit::SemanticAction::set_stage_1, 64.0 / 127.0},
        {5, 3, tidepit::SemanticAction::source_next, 0.0},
        {15, 12, tidepit::SemanticAction::set_stage_2, 100.0 / 127.0},
    }};
    for (std::size_t index = 0; index < expected.size(); ++index) {
        CHECK(sameEvent(adapted.events[index], expected[index]));
    }

    const auto diagnostics = adapter.diagnostics();
    CHECK(diagnostics.raw_messages == 12);
    CHECK(diagnostics.accepted_messages == 5);
    CHECK(diagnostics.semantic_events == 4);
    CHECK(diagnostics.action_releases == 1);
    CHECK(diagnostics.malformed_messages == 3);
    CHECK(diagnostics.ignored_channels == 1);
    CHECK(diagnostics.unassigned_controllers == 1);
    CHECK(diagnostics.unknown_controllers == 1);
    CHECK(diagnostics.invalid_values == 1);
    CHECK(diagnostics.dropped_events == 0);
    CHECK(diagnostics.last_accepted_channel == 16);
    CHECK(diagnostics.last_accepted_cc == 21);
    CHECK(diagnostics.last_accepted_value == 100);
}

void testDescriptorExhaustiveDirectParity() {
    tidepit::Core adapted_core;
    tidepit::Core direct_core;
    CHECK(adapted_core.prepare(tidepit::kReferenceSampleRate, 16));
    CHECK(direct_core.prepare(tidepit::kReferenceSampleRate, 16));
    tidepit::JuceMidiAdapter adapter;
    juce::MidiBuffer source;
    source.ensureSize(1024);

    for (const auto& descriptor : tidepit::encoderDescriptors()) {
        if (descriptor.kind == tidepit::ControlKind::unassigned) continue;
        const auto action = tidepit::semanticAction(descriptor.id);
        CHECK(action.has_value());
        for (std::uint16_t midi_value = 0; midi_value < 128U; ++midi_value) {
            source.clear();
            addRaw(
                source,
                std::array<std::uint8_t, 3>{
                    0xbfU,
                    descriptor.cc,
                    static_cast<std::uint8_t>(midi_value),
                },
                0
            );
            const auto adapted = adapter.adapt(source, 16);
            CHECK(adapted.event_count == 1);
            const auto mapping = tidepit::mapMidiCc(
                tidepit::launchControlMidiChannel(),
                descriptor.cc,
                static_cast<std::uint8_t>(midi_value)
            );
            CHECK(mapping.status == tidepit::MappingStatus::accepted_continuous);
            const tidepit::SemanticEvent direct{
                0,
                adapted.events[0].ingress_sequence,
                *action,
                descriptor.id == tidepit::ControlId::set_root
                    ? static_cast<double>(mapping.root_note)
                    : mapping.normalized_value,
            };
            CHECK(sameEvent(adapted.events[0], direct));
            checkCoreParity(
                adapted_core,
                direct_core,
                adapted.events,
                adapted.event_count,
                &direct,
                1
            );
        }
    }

    for (const auto& descriptor : tidepit::buttonDescriptors()) {
        if (descriptor.kind == tidepit::ControlKind::unassigned) continue;
        const auto action = tidepit::semanticAction(descriptor.id);
        CHECK(action.has_value());
        source.clear();
        addRaw(
            source,
            std::array<std::uint8_t, 3>{0xbfU, descriptor.cc, descriptor.press_value},
            0
        );
        const auto press = adapter.adapt(source, 16);
        CHECK(press.event_count == 1);
        const tidepit::SemanticEvent direct{
            0,
            press.events[0].ingress_sequence,
            *action,
            0.0,
        };
        CHECK(sameEvent(press.events[0], direct));
        checkCoreParity(adapted_core, direct_core, press.events, 1, &direct, 1);

        source.clear();
        addRaw(
            source,
            std::array<std::uint8_t, 3>{0xbfU, descriptor.cc, descriptor.release_value},
            0
        );
        const auto release = adapter.adapt(source, 16);
        CHECK(release.event_count == 0);
        checkCoreParity(adapted_core, direct_core, nullptr, 0, nullptr, 0);
    }
}

void testCapacityAndReset() {
    tidepit::JuceMidiAdapter adapter;
    juce::MidiBuffer source;
    source.ensureSize(16384);
    for (std::size_t index = 0; index < tidepit::kMaximumSemanticEvents + 2U; ++index) {
        addRaw(
            source,
            std::array<std::uint8_t, 3>{
                0xbfU,
                20U,
                static_cast<std::uint8_t>(index % 128U),
            },
            0
        );
    }
    const auto full = adapter.adapt(source, 16);
    CHECK(full.event_count == tidepit::kMaximumSemanticEvents);
    CHECK(full.dropped_events == 2);
    CHECK(adapter.diagnostics().accepted_messages == tidepit::kMaximumSemanticEvents + 2U);
    CHECK(adapter.diagnostics().semantic_events == tidepit::kMaximumSemanticEvents);
    CHECK(adapter.diagnostics().dropped_events == 2);

    juce::MidiBuffer next_source;
    addRaw(next_source, std::array<std::uint8_t, 3>{0xbfU, 20U, 64U}, 0);
    const auto next = adapter.adapt(next_source, 16);
    CHECK(next.event_count == 1);
    CHECK(next.events[0].ingress_sequence == tidepit::kMaximumSemanticEvents + 3U);

    adapter.reset();
    const auto restarted = adapter.adapt(next_source, 16);
    CHECK(restarted.event_count == 1);
    CHECK(restarted.events[0].ingress_sequence == 1);
    CHECK(adapter.diagnostics().raw_messages == 1);
}

void testIrregularHostPartitionParityAndLifecycle() {
    struct AbsoluteEvent {
        std::uint32_t sample;
        std::uint64_t sequence;
        tidepit::SemanticAction action;
        double value;
    };
    const std::array<AbsoluteEvent, 8> schedule{{
        {0, 1, tidepit::SemanticAction::set_stage_1, 0.75},
        {1, 2, tidepit::SemanticAction::source_next, 0.0},
        {15, 3, tidepit::SemanticAction::set_root, 67.0},
        {16, 4, tidepit::SemanticAction::lock_toggle, 0.0},
        {17, 5, tidepit::SemanticAction::set_fx_a, 0.9},
        {31, 6, tidepit::SemanticAction::effect_next, 0.0},
        {32, 7, tidepit::SemanticAction::set_material, 0.12},
        {63, 8, tidepit::SemanticAction::scale_next, 0.0},
    }};
    const std::array<std::uint32_t, 10> partitions{{1, 7, 3, 19, 5, 11, 2, 14, 9, 9}};
    constexpr std::uint32_t total_frames = 80;

    tidepit::Core direct_core;
    tidepit::Core bridged_core;
    CHECK(direct_core.prepare(tidepit::kReferenceSampleRate, total_frames));
    CHECK(bridged_core.prepare(
        tidepit::kReferenceSampleRate,
        tidepit::kReferenceQuantumFrames
    ));
    std::array<tidepit::SemanticEvent, schedule.size()> direct_events{};
    for (std::size_t index = 0; index < schedule.size(); ++index) {
        direct_events[index] = {
            schedule[index].sample,
            schedule[index].sequence,
            schedule[index].action,
            schedule[index].value,
        };
    }
    std::array<std::int32_t, total_frames> direct_left{};
    std::array<std::int32_t, total_frames> direct_right{};
    const auto direct_report = direct_core.processQ27(
        direct_left.data(),
        direct_right.data(),
        total_frames,
        direct_events.data(),
        direct_events.size()
    );
    CHECK(direct_report.events_accepted == direct_events.size());
    CHECK(direct_report.events_dropped == 0);

    tidepit::Q27HostBridge bridge;
    std::array<float, total_frames> bridged_left{};
    std::array<float, total_frames> bridged_right{};
    std::size_t event_index = 0;
    std::uint32_t origin = 0;
    allocation_count.store(0, std::memory_order_release);
    track_allocations.store(true, std::memory_order_release);
    for (const auto frames : partitions) {
        std::array<tidepit::SemanticEvent, schedule.size()> callback_events{};
        std::size_t callback_count = 0;
        while (event_index < schedule.size()
            && schedule[event_index].sample < origin + frames) {
            const auto& event = schedule[event_index++];
            callback_events[callback_count++] = {
                event.sample - origin,
                event.sequence,
                event.action,
                event.value,
            };
        }
        bridge.process(
            bridged_core,
            bridged_left.data() + origin,
            bridged_right.data() + origin,
            frames,
            callback_events.data(),
            callback_count
        );
        origin += frames;
    }
    track_allocations.store(false, std::memory_order_release);
    CHECK(allocation_count.load(std::memory_order_acquire) == 0);
    CHECK(origin == total_frames);
    CHECK(event_index == schedule.size());
    CHECK(bridge.droppedEvents() == 0);
    for (std::size_t frame = 0; frame < total_frames; ++frame) {
        const auto expected_left = static_cast<float>(
            static_cast<double>(direct_left[frame]) / 134217728.0
        );
        const auto expected_right = static_cast<float>(
            static_cast<double>(direct_right[frame]) / 134217728.0
        );
        CHECK(bridged_left[frame] == expected_left);
        CHECK(bridged_right[frame] == expected_right);
    }
    CHECK(sameSnapshot(bridged_core.snapshot(), direct_core.snapshot()));
    CHECK(sameDiagnostics(bridged_core.diagnostics(), direct_core.diagnostics()));

    tidepit::Core restarted_core;
    CHECK(restarted_core.prepare(
        tidepit::kReferenceSampleRate,
        tidepit::kReferenceQuantumFrames
    ));
    bridge.reset();
    std::array<float, tidepit::kReferenceQuantumFrames> restarted_left{};
    std::array<float, tidepit::kReferenceQuantumFrames> restarted_right{};
    const tidepit::SemanticEvent restarted_event{
        0,
        1,
        tidepit::SemanticAction::set_stage_1,
        0.75,
    };
    bridge.process(
        restarted_core,
        restarted_left.data(),
        restarted_right.data(),
        tidepit::kReferenceQuantumFrames,
        &restarted_event,
        1
    );
    CHECK(bridge.droppedEvents() == 0);
    for (std::size_t frame = 0; frame < tidepit::kReferenceQuantumFrames; ++frame) {
        CHECK(restarted_left[frame] == static_cast<float>(
            static_cast<double>(direct_left[frame]) / 134217728.0
        ));
        CHECK(restarted_right[frame] == static_cast<float>(
            static_cast<double>(direct_right[frame]) / 134217728.0
        ));
    }
}

void testHostBridgeCapacityIsBounded() {
    tidepit::Core core;
    CHECK(core.prepare(
        tidepit::kReferenceSampleRate,
        tidepit::kReferenceQuantumFrames
    ));
    tidepit::Q27HostBridge bridge;
    std::array<float, 1> left{};
    std::array<float, 1> right{};
    bridge.process(core, left.data(), right.data(), 1);

    std::array<tidepit::SemanticEvent, tidepit::kMaximumSemanticEvents> events{};
    std::uint64_t sequence = 0;
    for (int callback = 0; callback < 5; ++callback) {
        for (auto& event : events) {
            event = {
                0,
                ++sequence,
                tidepit::SemanticAction::set_stage_1,
                0.5,
            };
        }
        bridge.process(
            core,
            left.data(),
            right.data(),
            1,
            events.data(),
            events.size()
        );
    }
    CHECK(bridge.droppedEvents() == tidepit::kMaximumSemanticEvents);
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
    testRawParsingOrderAndDiagnostics();
    testDescriptorExhaustiveDirectParity();
    testCapacityAndReset();
    testIrregularHostPartitionParityAndLifecycle();
    testHostBridgeCapacityIsBounded();
    if (failures != 0) {
        std::cerr << "Tide Pit JUCE MIDI adapter checks: " << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "Tide Pit JUCE MIDI adapter checks: PASS\n";
    return 0;
}
