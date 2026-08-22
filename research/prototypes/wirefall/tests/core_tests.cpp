#include "wirefall/core.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <new>
#include <string>
#include <vector>

namespace {

std::atomic<bool> g_measure_allocations{false};
std::atomic<std::size_t> g_measured_allocations{0};

struct ScheduledEvent {
    std::uint64_t sample{};
    wirefall::Event event{};
};

struct RenderResult {
    std::vector<float> left;
    std::vector<float> right;
    std::vector<wirefall::LedgerEvent> ledger;
    std::string normalized_state;
    std::string full_state;
    wirefall::Diagnostics diagnostics{};
};

int failures = 0;

void expect(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

bool ledgerEqual(const wirefall::LedgerEvent& left, const wirefall::LedgerEvent& right) {
    return left.sample_index == right.sample_index
        && left.ingress_sequence == right.ingress_sequence
        && left.kind == right.kind
        && left.control == right.control
        && left.action == right.action
        && left.value == right.value
        && left.active_rate_index == right.active_rate_index
        && left.active_holes == right.active_holes
        && left.scheduler_error == right.scheduler_error
        && left.effective_edge_frames == right.effective_edge_frames
        && left.cut == right.cut;
}

bool ledgersEqual(
    const std::vector<wirefall::LedgerEvent>& left,
    const std::vector<wirefall::LedgerEvent>& right
) {
    if (left.size() != right.size()) return false;
    for (std::size_t index = 0; index < left.size(); ++index) {
        if (!ledgerEqual(left[index], right[index])) return false;
    }
    return true;
}

RenderResult render(
    wirefall::Core& core,
    std::uint64_t frames,
    std::uint32_t block_frames,
    const std::vector<ScheduledEvent>& schedule = {},
    bool allow_dropped_events = false
) {
    RenderResult result;
    result.left.resize(static_cast<std::size_t>(frames));
    result.right.resize(static_cast<std::size_t>(frames));
    std::size_t next_event = 0;
    std::uint64_t position = 0;
    while (position < frames) {
        const auto count = static_cast<std::uint32_t>(
            std::min<std::uint64_t>(block_frames, frames - position));
        std::array<wirefall::Event, wirefall::kMaximumEventsPerBlock> events{};
        std::size_t event_count = 0;
        while (next_event < schedule.size()
            && schedule[next_event].sample < position + count) {
            if (schedule[next_event].sample >= position
                && event_count < events.size()) {
                events[event_count] = schedule[next_event].event;
                events[event_count].sample_offset = static_cast<std::uint32_t>(
                    schedule[next_event].sample - position);
                ++event_count;
            }
            ++next_event;
        }
        std::array<wirefall::LedgerEvent, 256> ledger{};
        const auto report = core.process(
            result.left.data() + position,
            result.right.data() + position,
            count,
            events.data(),
            event_count,
            ledger.data(),
            ledger.size());
        if (!allow_dropped_events) {
            expect(report.dropped_events == 0, "normal test render must not drop events");
        }
        expect(report.ledger_events_dropped == 0, "normal test render must not overflow its ledger");
        result.ledger.insert(
            result.ledger.end(), ledger.begin(),
            ledger.begin() + static_cast<std::ptrdiff_t>(report.ledger_events_written));
        position += count;
    }
    result.normalized_state = core.normalizedStateSha256();
    result.full_state = core.fullStateSha256();
    result.diagnostics = core.diagnostics();
    return result;
}

wirefall::Event setControl(
    std::uint64_t sequence,
    wirefall::ControlId control,
    double value
) {
    wirefall::Event event{};
    event.ingress_sequence = sequence;
    event.kind = wirefall::EventKind::set_control;
    event.control = control;
    event.value = value;
    return event;
}

wirefall::Event action(std::uint64_t sequence, wirefall::ActionId action_id) {
    wirefall::Event event{};
    event.ingress_sequence = sequence;
    event.kind = wirefall::EventKind::action;
    event.action = action_id;
    return event;
}

void testPreparationAndContract() {
    wirefall::Core core;
    expect(!core.prepare(44100.0), "Core must reject a non-contract sample rate");
    expect(!core.prepare(48000.0, 513), "Core must reject an oversized block");
    wirefall::Configuration invalid{};
    invalid.wire_oversample_factor = 2;
    expect(!core.prepare(48000.0, 512, invalid), "Core must reject an unsupported oversampling factor");
    expect(core.prepare(48000.0), "Core must prepare for the frozen host contract");
    expect(core.sampleRate() == 48000.0, "prepared sample rate must be 48 kHz");
    expect(core.maximumBlockFrames() == 512, "prepared maximum block must be 512 frames");
    expect(wirefall::Core::stateBytes() <= 256U * 1024U, "Core state must fit the 256 KiB budget");
    expect(wirefall::kPublicControlDescriptors.size() == 19, "generated public control descriptor must expose 19 controls/actions");
    expect(
        wirefall::Core::frozenFirByteSha256()
            == "a99f4e674be713a0b0f2405711cff20b6a0676a13f4af63380165c4984e70b1a",
        "compiled 63-tap FIR words must match the frozen byte hash");
    const auto initial = core.snapshot();
    expect(initial.absolute_sample == 0, "initial absolute sample must be zero");
    expect(initial.active_rate_index == 0, "initial CUT rate must be OPEN");
    expect(initial.active_holes == 3, "initial HOLES numerator must be 3");
    expect(std::abs(initial.tension - 0.38) < 1.0e-6, "initial TENSION must be 0.38");
    expect(std::abs(initial.shadow) < 1.0e-9, "initial SHADOW must be zero");
}

void testFiniteClampsAndEventRejection() {
    wirefall::Core core;
    expect(core.prepare(48000.0), "finite-clamp Core must prepare");
    expect(core.setControlValue(wirefall::ControlId::tension, 7.0), "finite TENSION target must be accepted and clamped");
    expect(!core.setControlValue(
        wirefall::ControlId::shadow,
        std::numeric_limits<double>::quiet_NaN()), "non-finite SHADOW target must be rejected");
    const auto diagnostics = core.diagnostics();
    expect(diagnostics.non_finite_targets == 1, "non-finite target counter must increment exactly once");

    std::array<float, 8> left{};
    std::array<float, 8> right{};
    wirefall::Event invalid = setControl(1, wirefall::ControlId::shadow, 0.5);
    invalid.kind = wirefall::EventKind::linear_control;
    invalid.duration_frames = 16;
    invalid.end_value = 1.0;
    std::array<wirefall::LedgerEvent, 16> ledger{};
    const auto report = core.process(left.data(), right.data(), 8, &invalid, 1, ledger.data(), ledger.size());
    expect(report.accepted_events == 0 && report.dropped_events == 1,
        "unsupported linear automation must be rejected before acceptance");
    expect(report.ledger_events_written == 1,
        "rejected automation must not add an accepted-control ledger entry");
}

void testRealtimeAndCapacity() {
    wirefall::Core core;
    expect(core.prepare(48000.0), "realtime Core must prepare");
    std::array<float, 512> left{};
    std::array<float, 512> right{};
    std::array<wirefall::LedgerEvent, 32> ledger{};
    g_measured_allocations = 0;
    g_measure_allocations = true;
    const auto report = core.process(left.data(), right.data(), 512, nullptr, 0, ledger.data(), ledger.size());
    g_measure_allocations = false;
    expect(g_measured_allocations == 0, "audio processing must perform no heap allocation");
    expect(report.dropped_events == 0, "allocation probe process call must not drop events");
    for (std::size_t index = 0; index < left.size(); ++index) {
        expect(std::isfinite(left[index]) && std::isfinite(right[index]), "Core output must remain finite");
        expect(std::abs(left[index]) <= wirefall::kOutputCeiling + 1.0e-6f,
            "Core output must remain below the frozen ceiling");
    }

    wirefall::Core capacity_core;
    expect(capacity_core.prepare(48000.0), "capacity Core must prepare");
    std::array<wirefall::Event, 129> events{};
    for (std::size_t index = 0; index < events.size(); ++index) {
        events[index] = setControl(index + 1U, wirefall::ControlId::tension, 0.25);
    }
    std::array<float, 1> capacity_left{};
    std::array<float, 1> capacity_right{};
    std::array<wirefall::LedgerEvent, 256> capacity_ledger{};
    const auto capacity_report = capacity_core.process(
        capacity_left.data(), capacity_right.data(), 1,
        events.data(), events.size(), capacity_ledger.data(), capacity_ledger.size());
    expect(capacity_report.accepted_events == 128, "event capacity must accept the first 128 events");
    expect(capacity_report.dropped_events == 1, "event capacity must reject event 129 deterministically");
    expect(capacity_core.diagnostics().dropped_events == 1, "capacity rejection must increment the monotonic drop counter");
}

void testPartitionInvariance() {
    std::vector<ScheduledEvent> schedule{
        {0, setControl(1, wirefall::ControlId::tension, 0.72)},
        {0, setControl(2, wirefall::ControlId::shadow, 0.8)},
        {0, setControl(3, wirefall::ControlId::holes, 3)},
        {0, setControl(4, wirefall::ControlId::cut, 4)},
        {24001, setControl(5, wirefall::ControlId::under, 4)},
        {48017, action(6, wirefall::ActionId::flip)},
        {72003, action(7, wirefall::ActionId::flip_cancel)},
    };
    wirefall::Core one;
    wirefall::Core irregular;
    expect(one.prepare(48000.0), "single-frame partition Core must prepare");
    expect(irregular.prepare(48000.0), "irregular partition Core must prepare");
    const auto a = render(one, 120000, 1, schedule);
    const auto b = render(irregular, 120000, 257, schedule);
    expect(a.left == b.left && a.right == b.right,
        "audio must be byte-identical across 1- and 257-frame partitions");
    expect(ledgersEqual(a.ledger, b.ledger),
        "event and scheduler ledgers must be identical across partitions");
    expect(a.full_state == b.full_state,
        "full Core state must be identical across partitions");
}

void testRhythmCommitAndVoidInterior() {
    std::vector<ScheduledEvent> schedule{
        {0, setControl(1, wirefall::ControlId::tension, 0.72)},
        {0, setControl(2, wirefall::ControlId::shadow, 0.0)},
        {0, setControl(3, wirefall::ControlId::holes, 3)},
        {1, setControl(4, wirefall::ControlId::cut, 1)},
    };
    wirefall::Core core;
    expect(core.prepare(48000.0), "void-interior Core must prepare");
    const auto result = render(core, 145000, 512, schedule);
    bool commit_at_beat = false;
    bool cut_at_96000 = false;
    for (const auto& event : result.ledger) {
        if (event.kind == wirefall::LedgerKind::rhythm_commit
            && event.sample_index == 24000 && event.active_rate_index == 1) {
            commit_at_beat = true;
        }
        if (event.kind == wirefall::LedgerKind::opportunity
            && event.sample_index == 120000 && event.cut) {
            cut_at_96000 = true;
        }
    }
    expect(commit_at_beat, "pending CUT must commit at the next beat boundary");
    expect(cut_at_96000, "3/8 scheduler must produce its first cut on the third post-commit opportunity");
    float interior_peak = 0.0f;
    for (std::size_t index = 130000; index < 143000; ++index) {
        interior_peak = std::max(interior_peak, std::abs(result.left[index]));
        interior_peak = std::max(interior_peak, std::abs(result.right[index]));
    }
    expect(interior_peak <= 1.0e-5f, "SHADOW-zero cut interior must be a true void");
}

void testResetAndPanicTiming() {
    wirefall::Core reset_core;
    wirefall::Core reference;
    expect(reset_core.prepare(48000.0), "reset Core must prepare");
    expect(reference.prepare(48000.0), "reset reference Core must prepare");
    const std::vector<ScheduledEvent> disturbed{
        {0, setControl(1, wirefall::ControlId::tension, 0.9)},
        {0, setControl(2, wirefall::ControlId::shadow, 0.8)},
        {128, action(3, wirefall::ActionId::reset)},
        {200, setControl(4, wirefall::ControlId::root, 1.0)},
    };
    const auto reset_result = render(reset_core, 609, 64, disturbed, true);
    const auto reference_result = render(reference, 241, 64);
    expect(reset_result.normalized_state == reference_result.normalized_state,
        "normalized state after the 480-frame Reset must equal fresh post-clear processing");
    expect(reset_result.diagnostics.rejected_during_reset == 1,
        "non-Panic events inside Reset must be rejected and counted");
    expect(reset_result.diagnostics.dropped_events == 1,
        "Reset rejection must increment the monotonic drop counter");
    bool reset_boundary = false;
    for (const auto& event : reset_result.ledger) {
        if (event.kind == wirefall::LedgerKind::reset_boundary && event.sample_index == 368) {
            reset_boundary = true;
        }
    }
    expect(reset_boundary, "Reset clear boundary must occur before frame n+240");
    expect(!reset_core.snapshot().reset_active, "normal output must resume at frame n+480");

    wirefall::Core restarted_reset;
    expect(restarted_reset.prepare(48000.0), "restarted Reset Core must prepare");
    const std::vector<ScheduledEvent> restarted_schedule{
        {10, action(1, wirefall::ActionId::reset)},
        {100, action(2, wirefall::ActionId::reset)},
    };
    const auto restarted_result = render(restarted_reset, 581, 37, restarted_schedule);
    std::size_t restarted_boundaries = 0;
    for (const auto& event : restarted_result.ledger) {
        if (event.kind == wirefall::LedgerKind::reset_boundary) {
            ++restarted_boundaries;
            expect(event.sample_index == 340,
                "a second Reset must restart the down/clear boundary from its event frame");
        }
    }
    expect(restarted_boundaries == 1, "restarted Reset must clear once at the replacement boundary");
    expect(restarted_reset.diagnostics().reset_count == 2,
        "both accepted Reset actions must remain in diagnostics");
    expect(!restarted_reset.snapshot().reset_active,
        "restarted Reset must return to normal at the replacement n+480 boundary");

    wirefall::Core panic_core;
    expect(panic_core.prepare(48000.0), "Panic Core must prepare");
    const std::vector<ScheduledEvent> panic_schedule{
        {10, action(1, wirefall::ActionId::panic)},
    };
    const auto panic_result = render(panic_core, 600, 37, panic_schedule);
    expect(panic_core.snapshot().panic_latched, "Panic must latch after its 480-frame ramp");
    bool panic_boundary = false;
    for (const auto& event : panic_result.ledger) {
        if (event.kind == wirefall::LedgerKind::panic_boundary && event.sample_index == 490) {
            panic_boundary = true;
        }
    }
    expect(panic_boundary, "Panic clear boundary must occur at n+480");
    float latched_peak = 0.0f;
    for (std::size_t index = 490; index < panic_result.left.size(); ++index) {
        latched_peak = std::max(latched_peak, std::abs(panic_result.left[index]));
        latched_peak = std::max(latched_peak, std::abs(panic_result.right[index]));
    }
    expect(latched_peak == 0.0f, "latched Panic must produce exact digital silence");
    expect(panic_core.triggerAction(wirefall::ActionId::panic_release), "Panic release must be accepted while latched");
    const auto release = render(panic_core, 240, 64);
    expect(!panic_core.snapshot().panic_latched && !panic_core.snapshot().panic_ramping,
        "Panic release must leave the Core normal after 240 frames");
    expect(std::isfinite(release.left.back()), "Panic release output must remain finite");
}

}  // namespace

void* operator new(std::size_t size) {
    if (g_measure_allocations) ++g_measured_allocations;
    if (void* memory = std::malloc(size)) return memory;
    throw std::bad_alloc();
}

void* operator new[](std::size_t size) {
    if (g_measure_allocations) ++g_measured_allocations;
    if (void* memory = std::malloc(size)) return memory;
    throw std::bad_alloc();
}

void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

int main() {
    testPreparationAndContract();
    testFiniteClampsAndEventRejection();
    testRealtimeAndCapacity();
    testPartitionInvariance();
    testRhythmCommitAndVoidInterior();
    testResetAndPanicTiming();
    if (failures != 0) {
        std::cerr << failures << " Wirefall Core test assertion(s) failed\n";
        return 1;
    }
    std::cout << "Wirefall Core contract tests passed\n";
    return 0;
}
