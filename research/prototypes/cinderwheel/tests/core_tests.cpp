#include "cinderwheel/core.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <new>
#include <string>
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

void* operator new[](std::size_t size) {
    return ::operator new(size);
}

void operator delete(void* memory) noexcept {
    std::free(memory);
}

void operator delete[](void* memory) noexcept {
    std::free(memory);
}

void operator delete(void* memory, std::size_t) noexcept {
    std::free(memory);
}

void operator delete[](void* memory, std::size_t) noexcept {
    std::free(memory);
}

namespace {

int failures = 0;

void check(bool condition, const char* expression, const char* file, int line) {
    if (condition) return;
    ++failures;
    std::cerr << file << ':' << line << ": CHECK failed: " << expression << '\n';
}

#define CHECK(expression) check(static_cast<bool>(expression), #expression, __FILE__, __LINE__)

bool close(double left, double right, double tolerance) {
    return std::abs(left - right) <= tolerance;
}

struct ScheduledMidi {
    std::uint64_t sample{};
    std::uint64_t sequence{};
    std::array<std::uint8_t, 3> bytes{};
};

ScheduledMidi cc(std::uint64_t sample, std::uint64_t sequence, std::uint8_t controller, std::uint8_t value, std::uint8_t status = 0xBFU) {
    return {sample, sequence, {status, controller, value}};
}

struct RenderResult {
    std::vector<float> left;
    std::vector<float> right;
    std::vector<cinderwheel::WakeEvent> events;
    std::size_t process_allocations{};
};

RenderResult render(
    cinderwheel::Core& core,
    std::uint64_t frames,
    std::uint32_t block_frames,
    const std::vector<ScheduledMidi>& schedule = {}
) {
    RenderResult result;
    result.left.resize(static_cast<std::size_t>(frames));
    result.right.resize(static_cast<std::size_t>(frames));
    result.events.reserve(static_cast<std::size_t>(frames / 1000U + 32U));
    std::uint64_t rendered = 0;
    std::size_t schedule_index = 0;
    while (rendered < frames) {
        const auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(block_frames, frames - rendered));
        std::array<cinderwheel::MidiEvent, 32> block_midi{};
        std::size_t block_midi_count = 0;
        while (schedule_index < schedule.size() && schedule[schedule_index].sample < rendered + count) {
            CHECK(schedule[schedule_index].sample >= rendered);
            CHECK(block_midi_count < block_midi.size());
            if (block_midi_count < block_midi.size()) {
                const auto& source = schedule[schedule_index];
                block_midi[block_midi_count++] = {
                    static_cast<std::uint32_t>(source.sample - rendered),
                    source.sequence,
                    source.bytes,
                    3,
                };
            }
            ++schedule_index;
        }
        std::array<cinderwheel::WakeEvent, 16> block_events{};
        allocation_probe::count.store(0, std::memory_order_relaxed);
        allocation_probe::tracking.store(true, std::memory_order_release);
        const auto report = core.process(
            result.left.data() + rendered,
            result.right.data() + rendered,
            count,
            block_midi.data(),
            block_midi_count,
            block_events.data(),
            block_events.size()
        );
        allocation_probe::tracking.store(false, std::memory_order_release);
        result.process_allocations += allocation_probe::count.load(std::memory_order_relaxed);
        CHECK(report.events_dropped == 0);
        result.events.insert(result.events.end(), block_events.begin(), block_events.begin() + static_cast<std::ptrdiff_t>(report.events_written));
        rendered += count;
    }
    CHECK(schedule_index == schedule.size());
    return result;
}

void test_prepare_and_defaults() {
    cinderwheel::Core core;
    CHECK(!core.isPrepared());
    CHECK(!core.prepare(std::numeric_limits<double>::quiet_NaN()));
    CHECK(!core.prepare(44100.0));
    CHECK(!core.prepare(96000.0));
    CHECK(!core.prepare(48000.0, 0));
    CHECK(!core.prepare(48000.0, 513));
    CHECK(core.prepare(48000.0));
    const auto state = core.snapshot();
    CHECK(state.root_note == 48);
    CHECK(state.undertow_divisor == 0);
    CHECK(state.pulse_divide == 1);
    CHECK(close(state.rate_hz, 0.8, 1.0e-12));
    CHECK(!state.panic_latched);
    CHECK((state.ledger_energy == std::array<float, 4>{}));

    std::array<float, 513> left{};
    std::array<float, 513> right{};
    left.fill(1.0f);
    right.fill(1.0f);
    core.process(left.data(), right.data(), 513);
    CHECK(core.diagnostics().unsupported_process_calls == 1);
    CHECK(std::all_of(left.begin(), left.end(), [](float value) { return value == 1.0f; }));
}

void test_complete_controller_surface_and_quantizers() {
    constexpr std::array<double, 16> expected_defaults{{
        0.20, 0.70, 0.35, 0.85, 0.533104, 0.65, 0.55, 0.35,
        0.50, 0.25, 0.333333, 0.0, 0.0, 0.0, 0.50, 0.0,
    }};
    for (std::uint8_t controller = 20; controller <= 35; ++controller) {
        const auto* descriptor = cinderwheel::encoderDescriptor(controller);
        CHECK(descriptor != nullptr);
        CHECK(descriptor->cc == controller);
        CHECK(descriptor->id == static_cast<cinderwheel::ControlId>(controller - 20U));
        CHECK(close(descriptor->default_normalized, expected_defaults[controller - 20U], 1.0e-12));
        CHECK(cinderwheel::buttonDescriptor(controller) == nullptr);
    }
    for (std::uint8_t controller = 40; controller <= 47; ++controller) {
        const auto* descriptor = cinderwheel::buttonDescriptor(controller);
        CHECK(descriptor != nullptr);
        CHECK(descriptor->cc == controller);
        CHECK(descriptor->id == static_cast<cinderwheel::ControlId>(
            static_cast<unsigned>(cinderwheel::ControlId::source_scale) + controller - 40U
        ));
        CHECK(descriptor->hold_threshold_ms == (controller == 40 ? 600U : controller == 47 ? 1200U : 0U));
        CHECK(cinderwheel::encoderDescriptor(controller) == nullptr);
    }
    CHECK(cinderwheel::encoderDescriptor(36) == nullptr);
    CHECK(cinderwheel::buttonDescriptor(48) == nullptr);

    for (unsigned raw = 0; raw <= 127U; ++raw) {
        const auto value = static_cast<std::uint8_t>(raw);
        CHECK(close(cinderwheel::normalizedFromMidi(value), raw / 127.0, 1.0e-12));
        CHECK(close(
            cinderwheel::rateHzFromMidi(value),
            0.08 * std::pow(75.0, raw / 127.0),
            1.0e-12
        ));
        CHECK(cinderwheel::rootNoteFromMidi(value)
            == 36 + static_cast<std::int32_t>((raw * 36U + 63U) / 127U));
        CHECK(cinderwheel::undertowDivisorFromMidi(value)
            == (raw == 0 ? 0U : 1U + ((raw - 1U) * 16U) / 127U));
        CHECK(cinderwheel::pulseDivideFromMidi(value)
            == 1U + (raw * 15U + 63U) / 127U);
    }

    cinderwheel::Core core;
    CHECK(core.prepare(48000.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::root, 1.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::undertow, 1.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::pulse_divide, 1.0));
    const auto result = render(core, 16000, 128);
    CHECK(result.process_allocations == 0);
    auto state = core.snapshot();
    CHECK(state.root_note == 72);
    CHECK(state.undertow_divisor == 16);
    CHECK(state.pulse_divide == 16);
    if (!close(state.undertow_frequency_hz * 16.0, state.parent_frequency_hz, 1.0e-9)) {
        std::cerr << "undertow=" << state.undertow_frequency_hz << " parent=" << state.parent_frequency_hz << '\n';
    }
    CHECK(close(state.undertow_frequency_hz * 16.0, state.parent_frequency_hz, 1.0e-9));
    CHECK(std::abs(
        state.undertow_resonator_frequency_hz / state.undertow_frequency_hz - 1.0
    ) < 1.0e-3);

    CHECK(core.setControlNormalized(cinderwheel::ControlId::root, 0.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::undertow, 0.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::pulse_divide, 0.0));
    render(core, 16000, 64);
    state = core.snapshot();
    CHECK(state.root_note == 36);
    CHECK(state.undertow_divisor == 0);
    CHECK(state.undertow_frequency_hz == 0.0);
    CHECK(state.undertow_resonator_frequency_hz == 0.0);
    CHECK(state.pulse_divide == 1);

    CHECK(core.setControlNormalized(cinderwheel::ControlId::root, 0.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::undertow, 1.0));
    for (const auto control : {
            cinderwheel::ControlId::wave_1,
            cinderwheel::ControlId::wave_2,
            cinderwheel::ControlId::wave_3,
            cinderwheel::ControlId::wave_4,
        }) {
        CHECK(core.setControlNormalized(control, 0.0));
    }
    render(core, 16000, 128);
    state = core.snapshot();
    CHECK(state.undertow_frequency_hz < 12.0);
    CHECK(close(state.undertow_resonator_frequency_hz, state.undertow_frequency_hz, 1.0e-9));

    const auto before = core.diagnostics();
    const std::vector<ScheduledMidi> wrong{{cc(0, 1, 20, 100, 0xBEU), cc(1, 2, 40, 64)}};
    render(core, 2, 2, wrong);
    const auto after = core.diagnostics();
    CHECK(after.ignored_midi_messages == before.ignored_midi_messages + 1);
    CHECK(after.malformed_midi_messages == before.malformed_midi_messages + 1);

    cinderwheel::Core overflow;
    CHECK(overflow.prepare(48000.0));
    std::array<cinderwheel::MidiEvent, cinderwheel::kMaximumMidiEventsPerBlock + 1U> messages{};
    for (std::size_t index = 0; index < messages.size(); ++index) {
        messages[index] = {
            0,
            static_cast<std::uint64_t>(index + 1U),
            {0xBFU, 20, static_cast<std::uint8_t>(index % 128U)},
            3,
        };
    }
    std::array<float, 1> overflow_left{};
    std::array<float, 1> overflow_right{};
    overflow.process(
        overflow_left.data(),
        overflow_right.data(),
        1,
        messages.data(),
        messages.size()
    );
    CHECK(overflow.diagnostics().midi_events_dropped == 1);
}

void test_button_tap_hold_boundaries() {
    cinderwheel::Core tap;
    CHECK(tap.prepare(48000.0));
    render(tap, 20000, 128, {cc(0, 1, 40, 127), cc(100, 2, 40, 0)});
    CHECK(tap.snapshot().source == cinderwheel::SourceMode::rnd);
    CHECK(tap.snapshot().scale == cinderwheel::ScaleMode::minor_pentatonic);

    cinderwheel::Core exact_hold;
    CHECK(exact_hold.prepare(48000.0));
    render(exact_hold, 45000, 128, {cc(0, 1, 40, 127), cc(28800, 2, 40, 0)});
    CHECK(exact_hold.snapshot().source == cinderwheel::SourceMode::reed);
    CHECK(exact_hold.snapshot().scale == cinderwheel::ScaleMode::dorian);

    cinderwheel::Core duplicate;
    CHECK(duplicate.prepare(48000.0));
    render(duplicate, 4, 4, {
        cc(0, 1, 42, 127), cc(1, 2, 42, 127), cc(2, 3, 42, 0), cc(3, 4, 42, 0),
    });
    CHECK(duplicate.diagnostics().duplicate_button_edges == 2);

    cinderwheel::Core reset_boundary;
    CHECK(reset_boundary.prepare(48000.0));
    render(reset_boundary, 58000, 128, {
        cc(0, 1, 47, 127), cc(57599, 2, 47, 0),
    });
    CHECK(reset_boundary.diagnostics().reset_count == 1);
    CHECK(reset_boundary.diagnostics().panic_count == 0);

    cinderwheel::Core panic_boundary;
    CHECK(panic_boundary.prepare(48000.0));
    render(panic_boundary, 58100, 128, {
        cc(0, 1, 47, 127), cc(57600, 2, 47, 0),
    });
    CHECK(panic_boundary.diagnostics().reset_count == 0);
    CHECK(panic_boundary.diagnostics().panic_count == 1);
    CHECK(panic_boundary.snapshot().panic_latched);
}

void test_same_sample_ordering_and_bloom() {
    cinderwheel::Core ordering;
    CHECK(ordering.prepare(48000.0));
    render(ordering, 4, 4, {
        cc(0, 2, 20, 127),
        cc(0, 1, 21, 0),
        cc(0, 2, 22, 0),
    });
    CHECK(ordering.diagnostics().malformed_midi_messages == 2);

    cinderwheel::Core rapid_cycles;
    CHECK(rapid_cycles.prepare(48000.0));
    render(rapid_cycles, 16000, 128, {
        cc(0, 1, 40, 127), cc(100, 2, 40, 0),
        cc(200, 3, 40, 127), cc(300, 4, 40, 0),
        cc(400, 5, 40, 127), cc(500, 6, 40, 0),
        cc(600, 7, 44, 127), cc(700, 8, 44, 0),
        cc(800, 9, 44, 127), cc(900, 10, 44, 0),
        cc(1000, 11, 45, 127), cc(1100, 12, 45, 0),
        cc(1200, 13, 45, 127), cc(1300, 14, 45, 0),
        cc(1400, 15, 45, 127), cc(1500, 16, 45, 0),
    });
    CHECK(rapid_cycles.snapshot().source == cinderwheel::SourceMode::dust);
    CHECK(rapid_cycles.snapshot().fx_mode == cinderwheel::FxMode::drive);
    CHECK(rapid_cycles.snapshot().wave_target == cinderwheel::WaveTarget::all);

    cinderwheel::Core fx_full_cycle;
    CHECK(fx_full_cycle.prepare(48000.0));
    render(fx_full_cycle, 16000, 128, {
        cc(0, 1, 44, 127), cc(100, 2, 44, 0),
        cc(200, 3, 44, 127), cc(300, 4, 44, 0),
        cc(400, 5, 44, 127), cc(500, 6, 44, 0),
    });
    CHECK(fx_full_cycle.snapshot().fx_mode == cinderwheel::FxMode::clean);
    CHECK(!fx_full_cycle.snapshot().fx_a_pickup_armed);
    CHECK(!fx_full_cycle.snapshot().fx_b_pickup_armed);

    cinderwheel::Core ignored;
    CHECK(ignored.prepare(48000.0));
    const auto ignored_render = render(ignored, 16000, 128, {
        cc(0, 1, 33, 127),
        cc(0, 2, 35, 0),
        cc(100, 99, 36, 64),
        cc(101, 100, 40, 64),
    });
    CHECK(!ignored_render.events.empty());
    CHECK(ignored_render.events.front().ingress_sequence == 2);

    cinderwheel::Core bloom;
    CHECK(bloom.prepare(48000.0));
    const auto before_transition = render(bloom, 14000, 128, {
        cc(0, 1, 33, 127),
        cc(0, 2, 35, 127),
        cc(100, 3, 46, 127),
        cc(101, 4, 46, 0),
    });
    CHECK(before_transition.events.empty());
    CHECK(bloom.snapshot().bloom_armed);
    const auto after_transition = render(bloom, 2000, 64);
    CHECK(!bloom.snapshot().bloom_armed);
    CHECK(std::count_if(after_transition.events.begin(), after_transition.events.end(), [](const auto& event) {
        return event.kind == cinderwheel::WakeEventKind::afterstrike;
    }) == 1);
    CHECK(std::count_if(after_transition.events.begin(), after_transition.events.end(), [](const auto& event) {
        return event.kind == cinderwheel::WakeEventKind::primary;
    }) == 1);
}

void test_clean_fx_a_changes_grain_context() {
    cinderwheel::Core small;
    cinderwheel::Core large;
    CHECK(small.prepare(48000.0));
    CHECK(large.prepare(48000.0));
    CHECK(small.setControlNormalized(cinderwheel::ControlId::fx_a, 0.0));
    CHECK(large.setControlNormalized(cinderwheel::ControlId::fx_a, 1.0));
    const auto small_render = render(small, 96000, 128);
    const auto large_render = render(large, 96000, 128);
    float maximum_difference = 0.0f;
    for (std::size_t index = 0; index < small_render.left.size(); ++index) {
        maximum_difference = std::max(
            maximum_difference,
            std::abs(small_render.left[index] - large_render.left[index])
        );
        maximum_difference = std::max(
            maximum_difference,
            std::abs(small_render.right[index] - large_render.right[index])
        );
    }
    CHECK(maximum_difference > 1.0e-4f);

    cinderwheel::Core stable;
    cinderwheel::Core repeated;
    CHECK(stable.prepare(48000.0));
    CHECK(repeated.prepare(48000.0));
    const auto stable_render = render(stable, 60000, 128, {cc(0, 1, 31, 20)});
    const auto repeated_render = render(repeated, 60000, 128, {
        cc(0, 1, 31, 20),
        cc(20000, 2, 31, 20),
    });
    CHECK(stable_render.left == repeated_render.left);
    CHECK(stable_render.right == repeated_render.right);
}

void test_contextual_fx_soft_pickup() {
    cinderwheel::Core core;
    CHECK(core.prepare(48000.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::fx_a, 0.90));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::fx_b, 0.80));
    render(core, 1200, 128);
    CHECK(close(core.snapshot().fx_a, 0.897638, 1.0e-5));

    render(core, 16000, 128, {cc(0, 1, 44, 127), cc(100, 2, 44, 0)});
    auto state = core.snapshot();
    CHECK(state.fx_mode == cinderwheel::FxMode::filter);
    CHECK(state.fx_a_pickup_armed);
    CHECK(state.fx_b_pickup_armed);
    CHECK(close(state.fx_a, 0.50, 1.0e-9));

    CHECK(core.setControlNormalized(cinderwheel::ControlId::fx_a, 0.0));
    render(core, 1200, 128);
    state = core.snapshot();
    CHECK(state.fx_a_pickup_armed);
    CHECK(close(state.fx_a, 0.50, 1.0e-9));

    CHECK(core.setControlNormalized(cinderwheel::ControlId::fx_a, 0.50));
    render(core, 1200, 128);
    state = core.snapshot();
    CHECK(!state.fx_a_pickup_armed);
    CHECK(close(state.fx_a, 64.0 / 127.0, 1.0e-9));

    CHECK(core.setControlNormalized(cinderwheel::ControlId::fx_a, 0.20));
    render(core, 1200, 128);
    CHECK(close(core.snapshot().fx_a, 25.0 / 127.0, 1.0e-9));

    render(core, 16000, 128, {cc(0, 3, 44, 127), cc(100, 4, 44, 0)});
    CHECK(core.snapshot().fx_mode == cinderwheel::FxMode::drive);
    render(core, 16000, 128, {cc(0, 5, 44, 127), cc(100, 6, 44, 0)});
    state = core.snapshot();
    CHECK(state.fx_mode == cinderwheel::FxMode::clean);
    CHECK(close(state.fx_a, 114.0 / 127.0, 1.0e-9));
    CHECK(close(state.fx_b, 102.0 / 127.0, 1.0e-9));
}

bool sameEvent(const cinderwheel::WakeEvent& left, const cinderwheel::WakeEvent& right) {
    return left.sample_index == right.sample_index
        && left.ingress_sequence == right.ingress_sequence
        && left.transition_index == right.transition_index
        && left.voice == right.voice
        && left.kind == right.kind
        && left.ledger_energy == right.ledger_energy;
}

void test_block_partition_invariance_and_no_process_allocation() {
    const std::vector<ScheduledMidi> schedule{
        cc(0, 1, 32, 0),
        cc(0, 2, 33, 96),
        cc(0, 3, 35, 82),
        cc(100, 4, 40, 127),
        cc(200, 5, 40, 0),
        cc(30000, 6, 46, 127),
        cc(30010, 7, 46, 0),
        cc(50000, 8, 30, 86),
        cc(90000, 9, 34, 105),
    };
    std::array<RenderResult, 3> renders;
    const std::array<std::uint32_t, 3> blocks{{64, 128, 512}};
    for (std::size_t index = 0; index < renders.size(); ++index) {
        cinderwheel::Core core;
        CHECK(core.prepare(48000.0));
        renders[index] = render(core, 192000, blocks[index], schedule);
        CHECK(renders[index].process_allocations == 0);
    }
    for (std::size_t comparison = 1; comparison < renders.size(); ++comparison) {
        CHECK(renders[comparison].left.size() == renders[0].left.size());
        CHECK(renders[comparison].events.size() == renders[0].events.size());
        float maximum_difference = 0.0f;
        for (std::size_t index = 0; index < renders[0].left.size(); ++index) {
            maximum_difference = std::max(maximum_difference, std::abs(renders[0].left[index] - renders[comparison].left[index]));
            maximum_difference = std::max(maximum_difference, std::abs(renders[0].right[index] - renders[comparison].right[index]));
        }
        CHECK(maximum_difference <= 1.0e-7f);
        for (std::size_t index = 0; index < renders[0].events.size(); ++index) {
            CHECK(sameEvent(renders[0].events[index], renders[comparison].events[index]));
        }
    }
}

void test_ember_zero_caps_and_wake_clear() {
    cinderwheel::Core ember_zero;
    CHECK(ember_zero.prepare(48000.0));
    CHECK(ember_zero.setControlNormalized(cinderwheel::ControlId::wake, 1.0));
    CHECK(ember_zero.setControlNormalized(cinderwheel::ControlId::ember, 0.0));
    const auto zero = render(ember_zero, 192000, 128);
    CHECK(std::any_of(zero.events.begin(), zero.events.end(), [](const auto& event) {
        return event.kind == cinderwheel::WakeEventKind::primary;
    }));
    CHECK(!zero.events.empty());
    CHECK(zero.events.front().sample_index == 15001);
    CHECK(std::none_of(zero.events.begin(), zero.events.end(), [](const auto& event) {
        return event.kind == cinderwheel::WakeEventKind::afterstrike;
    }));
    CHECK(ember_zero.diagnostics().afterstrikes == 0);

    cinderwheel::Core dense;
    CHECK(dense.prepare(48000.0));
    CHECK(dense.setControlNormalized(cinderwheel::ControlId::wake, 1.0));
    CHECK(dense.setControlNormalized(cinderwheel::ControlId::ember, 1.0));
    const auto dense_render = render(dense, 480000, 512);
    std::uint32_t current_transition = 0;
    std::uint8_t afterstrikes = 0;
    std::array<std::uint8_t, 4> per_voice{};
    std::array<std::uint32_t, 4> last_afterstrike_transition{};
    for (const auto& event : dense_render.events) {
        if (event.transition_index != current_transition) {
            CHECK(afterstrikes <= 2);
            current_transition = event.transition_index;
            afterstrikes = 0;
            per_voice.fill(0);
        }
        if (event.kind == cinderwheel::WakeEventKind::afterstrike) {
            ++afterstrikes;
            CHECK(++per_voice[event.voice] <= 1);
            if (last_afterstrike_transition[event.voice] != 0) {
                CHECK(event.transition_index - last_afterstrike_transition[event.voice] >= 2);
            }
            last_afterstrike_transition[event.voice] = event.transition_index;
        }
    }
    CHECK(afterstrikes <= 2);
    CHECK(dense.diagnostics().afterstrikes <= dense.diagnostics().stage_transitions * 2U);

    cinderwheel::Core sink_overflow;
    CHECK(sink_overflow.prepare(48000.0));
    CHECK(sink_overflow.setControlNormalized(cinderwheel::ControlId::wake, 1.0));
    CHECK(sink_overflow.setControlNormalized(cinderwheel::ControlId::ember, 1.0));
    std::array<float, 512> overflow_left{};
    std::array<float, 512> overflow_right{};
    std::array<cinderwheel::WakeEvent, 1> one_event{};
    bool observed_sink_drop = false;
    for (int block = 0; block < 70; ++block) {
        const auto report = sink_overflow.process(
            overflow_left.data(),
            overflow_right.data(),
            512,
            nullptr,
            0,
            one_event.data(),
            one_event.size()
        );
        observed_sink_drop = observed_sink_drop || report.events_dropped > 0;
    }
    CHECK(observed_sink_drop);
    CHECK(sink_overflow.diagnostics().event_sink_overflows > 0);

    cinderwheel::Core maximum_rate;
    CHECK(maximum_rate.prepare(48000.0));
    CHECK(maximum_rate.setControlNormalized(cinderwheel::ControlId::rate, 1.0));
    render(maximum_rate, 2000, 128);
    CHECK(maximum_rate.setControlNormalized(cinderwheel::ControlId::wake, 1.0));
    CHECK(maximum_rate.setControlNormalized(cinderwheel::ControlId::ember, 1.0));
    const auto one_second = render(maximum_rate, 48000, 128);
    CHECK(one_second.events.size() <= 72);
    CHECK(maximum_rate.diagnostics().stage_transitions <= 26);

    CHECK(dense.setControlNormalized(cinderwheel::ControlId::wake, 0.0));
    render(dense, 600, 64);
    const auto state = dense.snapshot();
    CHECK((state.ledger_energy == std::array<float, 4>{}));
}

void test_musical_reset_repeats_ledger() {
    cinderwheel::Core pending;
    CHECK(pending.prepare(48000.0));
    CHECK(pending.setControlNormalized(cinderwheel::ControlId::root, 1.0));
    CHECK(pending.setControlNormalized(cinderwheel::ControlId::undertow, 1.0));
    CHECK(pending.setControlNormalized(cinderwheel::ControlId::pulse_divide, 1.0));
    render(pending, 200, 64, {cc(0, 1, 47, 127), cc(100, 2, 47, 0)});
    CHECK(pending.snapshot().root_note == 72);
    CHECK(pending.snapshot().undertow_divisor == 16);
    CHECK(pending.snapshot().pulse_divide == 16);

    cinderwheel::Core capture;
    CHECK(capture.prepare(48000.0));
    render(capture, 48000, 128);
    render(capture, 200, 64, {cc(0, 1, 43, 127), cc(100, 2, 43, 0)});
    CHECK(capture.snapshot().frozen);
    const auto captured_write_index = capture.snapshot().grain_write_index;
    render(capture, 200, 64, {cc(0, 3, 47, 127), cc(100, 4, 47, 0)});
    CHECK(capture.snapshot().frozen);
    CHECK(capture.snapshot().grain_write_index == captured_write_index);

    cinderwheel::Core core;
    CHECK(core.prepare(48000.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::wake, 0.85));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::ember, 0.90));
    render(core, 32000, 128);

    const auto reset_once_origin = core.snapshot().absolute_sample + 100U;
    render(core, 200, 64, {cc(0, 1, 47, 127), cc(100, 2, 47, 0)});
    const auto first = render(core, 960000, 128);

    const auto reset_twice_origin = core.snapshot().absolute_sample + 100U;
    render(core, 200, 64, {cc(0, 3, 47, 127), cc(100, 4, 47, 0)});
    const auto second = render(core, 960000, 128);
    CHECK(first.events.size() == second.events.size());
    for (std::size_t index = 0; index < first.events.size(); ++index) {
        CHECK(first.events[index].sample_index - reset_once_origin
            == second.events[index].sample_index - reset_twice_origin);
        CHECK(first.events[index].transition_index == second.events[index].transition_index);
        CHECK(first.events[index].voice == second.events[index].voice);
        CHECK(first.events[index].kind == second.events[index].kind);
        CHECK(first.events[index].ledger_energy == second.events[index].ledger_energy);
    }
    CHECK(core.diagnostics().reset_count == 2);
}

void test_panic_numeric_safety_and_ceiling() {
    cinderwheel::Core invalid;
    CHECK(invalid.prepare(48000.0));
    CHECK(!invalid.setControlNormalized(cinderwheel::ControlId::rate, std::numeric_limits<double>::infinity()));
    CHECK(invalid.diagnostics().non_finite_clears == 1);

    cinderwheel::Core core;
    CHECK(core.prepare(48000.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::wake, 1.0));
    CHECK(core.setControlNormalized(cinderwheel::ControlId::ember, 1.0));
    const auto panic = render(core, 60200, 128, {
        cc(0, 1, 43, 127),
        cc(100, 2, 43, 0),
        cc(200, 3, 47, 127),
    });
    CHECK(core.snapshot().panic_latched);
    CHECK(!core.snapshot().frozen);
    CHECK(core.diagnostics().panic_count == 1);
    CHECK((core.snapshot().ledger_energy == std::array<float, 4>{}));
    constexpr std::size_t first_silent_sample = 200U + 57600U + 479U;
    CHECK(panic.left[first_silent_sample - 1U] != 0.0f
        || panic.right[first_silent_sample - 1U] != 0.0f);
    CHECK(panic.left[first_silent_sample] == 0.0f);
    CHECK(panic.right[first_silent_sample] == 0.0f);
    for (std::size_t index = panic.left.size() - 256U; index < panic.left.size(); ++index) {
        CHECK(panic.left[index] == 0.0f);
        CHECK(panic.right[index] == 0.0f);
    }

    cinderwheel::Core ceiling;
    CHECK(ceiling.prepare(48000.0));
    CHECK(ceiling.setControlNormalized(cinderwheel::ControlId::body, 1.0));
    CHECK(ceiling.setControlNormalized(cinderwheel::ControlId::wake, 1.0));
    CHECK(ceiling.setControlNormalized(cinderwheel::ControlId::ember, 1.0));
    const auto signal = render(ceiling, 1968000, 512);
    float peak = 0.0f;
    double mean_left = 0.0;
    double mean_right = 0.0;
    const std::size_t mean_start = 48000;
    for (std::size_t index = 0; index < signal.left.size(); ++index) {
        CHECK(std::isfinite(signal.left[index]));
        CHECK(std::isfinite(signal.right[index]));
        peak = std::max(peak, std::abs(signal.left[index]));
        peak = std::max(peak, std::abs(signal.right[index]));
        if (index >= mean_start) {
            mean_left += signal.left[index];
            mean_right += signal.right[index];
        }
    }
    const double denominator = static_cast<double>(signal.left.size() - mean_start);
    mean_left /= denominator;
    mean_right /= denominator;
    if (std::abs(mean_left) >= 1.0e-4 || std::abs(mean_right) >= 1.0e-4) {
        std::cerr << "dc mean left=" << mean_left << " right=" << mean_right << '\n';
    }
    CHECK(peak <= cinderwheel::kOutputCeiling);
    CHECK(std::abs(mean_left) < 1.0e-4);
    CHECK(std::abs(mean_right) < 1.0e-4);
}

}  // namespace

int main() {
    test_prepare_and_defaults();
    test_complete_controller_surface_and_quantizers();
    test_button_tap_hold_boundaries();
    test_same_sample_ordering_and_bloom();
    test_contextual_fx_soft_pickup();
    test_clean_fx_a_changes_grain_context();
    test_block_partition_invariance_and_no_process_allocation();
    test_ember_zero_caps_and_wake_clear();
    test_musical_reset_repeats_ledger();
    test_panic_numeric_safety_and_ceiling();
    if (failures != 0) {
        std::cerr << failures << " Cinderwheel focused checks failed\n";
        return 1;
    }
    std::cout << "Cinderwheel focused checks: PASS\n";
    return 0;
}
