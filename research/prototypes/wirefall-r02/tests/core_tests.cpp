#include "WirefallR02Core.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <new>
#include <vector>

namespace {

bool measure_allocations = false;
std::size_t allocation_count = 0;
int failures = 0;

void expect(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

wirefall::r02::Event setEvent(
    std::uint32_t offset,
    std::uint64_t sequence,
    wirefall::r02::ControlId id,
    double value
) {
    wirefall::r02::Event event{};
    event.sample_offset = offset;
    event.ingress_sequence = sequence;
    event.kind = wirefall::r02::EventKind::set_control;
    event.control = id;
    event.value = value;
    return event;
}

wirefall::r02::Event actionEvent(
    std::uint32_t offset,
    std::uint64_t sequence,
    wirefall::r02::ActionId id
) {
    wirefall::r02::Event event{};
    event.sample_offset = offset;
    event.ingress_sequence = sequence;
    event.kind = wirefall::r02::EventKind::action;
    event.action = id;
    return event;
}

struct Scheduled {
    std::uint64_t frame{};
    wirefall::r02::Event event{};
};

std::vector<float> render(std::uint32_t partition, const std::vector<Scheduled>& schedule) {
    wirefall::r02::Core core;
    expect(core.prepare(48000.0), "partition Core must prepare");
    constexpr std::uint64_t duration = 96000;
    std::vector<float> interleaved(duration * 2U);
    std::array<float, wirefall::r02::kMaximumBlockFrames> left{};
    std::array<float, wirefall::r02::kMaximumBlockFrames> right{};
    std::size_t next_event = 0;
    std::uint64_t position = 0;
    while (position < duration) {
        const auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(partition, duration - position));
        std::array<wirefall::r02::Event, wirefall::r02::kMaximumEventsPerBlock> events{};
        std::size_t event_count = 0;
        while (next_event < schedule.size() && schedule[next_event].frame < position + count) {
            events[event_count] = schedule[next_event].event;
            events[event_count].sample_offset = static_cast<std::uint32_t>(schedule[next_event].frame - position);
            ++event_count;
            ++next_event;
        }
        const auto report = core.process(left.data(), right.data(), count, events.data(), event_count);
        expect(report.dropped_events == 0, "partition render must not drop events");
        for (std::uint32_t frame = 0; frame < count; ++frame) {
            interleaved[(position + frame) * 2U] = left[frame];
            interleaved[(position + frame) * 2U + 1U] = right[frame];
        }
        position += count;
    }
    return interleaved;
}

void testControlContract() {
    using namespace wirefall::r02;
    constexpr std::array<ControlDescriptor, 11> expected{{
        {ControlId::energy, "ENERGY", 0.0, 1.0, 0.32, false},
        {ControlId::break_depth, "BREAK", 0.0, 1.0, 0.0, false},
        {ControlId::pulse, "PULSE", 0.0, 7.0, 0.0, true},
        {ControlId::tick, "TICK", 0.0, 1.0, 0.0, false},
        {ControlId::root, "ROOT", -12.0, 12.0, 0.0, false},
        {ControlId::color, "COLOR", 0.0, 1.0, 0.55, false},
        {ControlId::width, "WIDTH", 0.0, 1.0, 0.35, false},
        {ControlId::edge, "EDGE", 0.0, 1.0, 0.34, false},
        {ControlId::space, "SPACE", 0.0, 1.0, 0.10, false},
        {ControlId::output, "OUTPUT", 0.0, 1.0, 0.82, false},
        {ControlId::tempo, "TEMPO", 40.0, 240.0, 120.0, false},
    }};
    expect(kControlDescriptors.size() == 11, "control descriptor count must remain eleven");
    for (std::size_t index = 0; index < expected.size(); ++index) {
        const auto& actual = kControlDescriptors[index];
        const auto& frozen = expected[index];
        expect(actual.id == frozen.id && actual.name == frozen.name
            && actual.minimum == frozen.minimum && actual.maximum == frozen.maximum
            && actual.default_value == frozen.default_value && actual.stepped == frozen.stepped,
            "exhaustive control descriptor comparison failed");
    }
    expect(kPulseNames[0] == "OFF" && kPulseNames[7] == "x8", "pulse names drifted");
    expect(kPulseRatesPerBeat[1] == 0.5 && kPulseRatesPerBeat[7] == 8.0,
        "pulse rate table drifted");

    Core core;
    expect(!core.prepare(22050.0), "unsupported low sample rate must fail closed");
    expect(!core.prepare(48000.0, 513), "oversized callback contract must fail closed");
    expect(core.prepare(48000.0), "48 kHz Core must prepare");
    const auto defaults = core.snapshot();
    expect(defaults.accepted_controls[0] == 0.32 && defaults.accepted_controls[1] == 0.0,
        "accepted defaults drifted");
    expect(core.setControlValue(ControlId::energy, 2.0), "finite ENERGY must be accepted and clamped");
    expect(core.snapshot().accepted_controls[0] == 1.0, "ENERGY clamp failed");
    expect(core.setControlValue(ControlId::pulse, 5.6), "finite PULSE selector must be accepted");
    expect(core.snapshot().pulse_index == 6, "PULSE selector must resolve to nearest index");
    expect(!core.setControlValue(ControlId::color, std::nan("")), "non-finite control must fail closed");
    expect(core.diagnostics().non_finite_controls == 1, "non-finite control diagnostic drifted");
}

void testFixedCapacityAndAllocation() {
    using namespace wirefall::r02;
    Core core;
    expect(core.prepare(48000.0), "capacity Core must prepare");
    std::array<Event, 129> events{};
    for (std::size_t index = 0; index < events.size(); ++index) {
        events[index] = setEvent(0, index, ControlId::color, 0.5);
    }
    std::array<float, 64> left{};
    std::array<float, 64> right{};
    const auto overflow = core.process(left.data(), right.data(), 64, events.data(), events.size());
    expect(overflow.accepted_events == 128 && overflow.dropped_events == 1,
        "event capacity must accept 128 and reject the remainder");

    allocation_count = 0;
    measure_allocations = true;
    const auto report = core.process(left.data(), right.data(), 64);
    measure_allocations = false;
    expect(report.dropped_events == 0, "ordinary process call must succeed");
    expect(allocation_count == 0, "Core processing must not allocate");
    expect(core.diagnostics().safety_clamps == 0, "ordinary process call must not clamp");
}

void testPartitionEquivalence() {
    using namespace wirefall::r02;
    std::vector<Scheduled> schedule;
    schedule.push_back({0, setEvent(0, 1, ControlId::energy, 0.68)});
    schedule.push_back({0, setEvent(0, 2, ControlId::break_depth, 1.0)});
    schedule.push_back({0, setEvent(0, 3, ControlId::pulse, 5.0)});
    schedule.push_back({24000, setEvent(0, 4, ControlId::tick, 0.85)});
    schedule.push_back({48000, actionEvent(0, 5, ActionId::downbeat)});
    schedule.push_back({72000, setEvent(0, 6, ControlId::pulse, 7.0)});
    const auto one = render(1, schedule);
    const auto sixty_four = render(64, schedule);
    const auto odd = render(257, schedule);
    expect(one.size() == sixty_four.size() && one.size() == odd.size(), "partition sizes must match");
    expect(std::memcmp(one.data(), sixty_four.data(), one.size() * sizeof(float)) == 0,
        "partition 1 and 64 output must be byte-identical");
    expect(std::memcmp(one.data(), odd.data(), one.size() * sizeof(float)) == 0,
        "partition 1 and 257 output must be byte-identical");
}

void testInterruptionAndTransitions() {
    using namespace wirefall::r02;
    Core core;
    expect(core.prepare(48000.0), "interruption Core must prepare");
    expect(core.setControlValue(ControlId::energy, 0.68), "ENERGY setup failed");
    expect(core.setControlValue(ControlId::break_depth, 1.0), "BREAK setup failed");
    expect(core.setControlValue(ControlId::pulse, 2.0), "PULSE setup failed");
    expect(core.setControlValue(ControlId::tick, 0.0), "TICK setup failed");
    std::array<float, 512> left{};
    std::array<float, 512> right{};
    float closed_peak = 0.0f;
    for (int block = 0; block < 100; ++block) {
        core.process(left.data(), right.data(), 512);
        if (block >= 50 && block <= 52) {
            for (std::size_t index = 0; index < left.size(); ++index) {
                closed_peak = std::max({closed_peak, std::abs(left[index]), std::abs(right[index])});
            }
        }
    }
    expect(closed_peak == 0.0f, "full BREAK with TICK zero must reach exact digital silence");

    expect(core.triggerAction(ActionId::panic_press), "Panic press must be accepted");
    core.process(left.data(), right.data(), 480);
    expect(core.snapshot().panic_latched, "Panic must latch after 480 frames at 48 kHz");
    float panic_peak = 0.0f;
    core.process(left.data(), right.data(), 64);
    for (std::size_t index = 0; index < 64; ++index) {
        panic_peak = std::max({panic_peak, std::abs(left[index]), std::abs(right[index])});
    }
    expect(panic_peak == 0.0f, "latched Panic must be exact silence");
    expect(core.triggerAction(ActionId::panic_release), "Panic release must be accepted");
    core.process(left.data(), right.data(), 240);
    expect(core.snapshot().transition == TransitionState::running,
        "Panic release must return to running after 240 frames");

    expect(core.triggerAction(ActionId::reset), "Reset must be accepted");
    core.process(left.data(), right.data(), 120);
    expect(core.triggerAction(ActionId::reset), "second Reset must restart the fade-down");
    core.process(left.data(), right.data(), 360);
    expect(core.snapshot().transition != TransitionState::running,
        "restarted Reset must still be completing at 360 frames after replacement");
    core.process(left.data(), right.data(), 120);
    expect(core.snapshot().transition == TransitionState::running,
        "restarted Reset must complete after replacement down and up ramps");
}

}  // namespace

void* operator new(std::size_t size) {
    if (measure_allocations) ++allocation_count;
    if (void* memory = std::malloc(size)) return memory;
    throw std::bad_alloc();
}

void* operator new[](std::size_t size) {
    if (measure_allocations) ++allocation_count;
    if (void* memory = std::malloc(size)) return memory;
    throw std::bad_alloc();
}

void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

int main() {
    testControlContract();
    testFixedCapacityAndAllocation();
    testPartitionEquivalence();
    testInterruptionAndTransitions();
    if (failures != 0) {
        std::cerr << failures << " Wirefall revision 0.2 assertion(s) failed\n";
        return 1;
    }
    std::cout << "Wirefall revision 0.2 Core tests passed\n";
    return 0;
}
