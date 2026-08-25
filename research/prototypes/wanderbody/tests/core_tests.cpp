#include "wanderbody/core.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <numeric>
#include <string>
#include <vector>

namespace wb = wanderbody;

namespace {

int failures = 0;

#define CHECK(condition) \
    do { \
        if (!(condition)) { \
            std::cerr << __FILE__ << ':' << __LINE__ \
                      << " check failed: " #condition "\n"; \
            ++failures; \
        } \
    } while (false)

struct Render final {
    std::vector<float> left{};
    std::vector<float> right{};
    std::vector<wb::DecisionEvent> decisions{};
    wb::Snapshot snapshot{};
};

[[nodiscard]] bool sameTuple(
    const wb::DecisionTuple& left,
    const wb::DecisionTuple& right) {
    return left.position == right.position
        && left.duration_seconds == right.duration_seconds
        && left.rate == right.rate
        && left.gain == right.gain
        && left.pan == right.pan
        && left.body_frequency_hz == right.body_frequency_hz
        && left.direction == right.direction;
}

[[nodiscard]] Render render(
    const wb::Controls& controls,
    std::uint32_t block,
    std::uint64_t frames,
    wb::MotionMode motion = wb::MotionMode::hover,
    wb::GenerationMode generation = wb::GenerationMode::correlated) {
    wb::Core core{};
    CHECK(core.prepare(48000.0, wb::kMaximumBlockFrames));
    core.setGenerationMode(generation);
    auto current = controls;
    current.motion = motion;
    wb::ActionSequences actions{};
    Render result{};
    result.left.reserve(static_cast<std::size_t>(frames));
    result.right.reserve(static_cast<std::size_t>(frames));
    std::vector<float> input_left(block);
    std::vector<float> input_right(block);
    std::vector<float> output_left(block);
    std::vector<float> output_right(block);
    std::uint64_t cursor{};
    while (cursor < frames) {
        const auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            block,
            frames - cursor));
        for (std::uint32_t index = 0U; index < count; ++index) {
            const auto frame = cursor + index;
            const double time = static_cast<double>(frame) / 48000.0;
            const double impulse = frame % 24000U == 0U ? 0.7 : 0.0;
            const double sample = 0.22 * std::sin(2.0 * 3.141592653589793 * 110.0 * time)
                + 0.11 * std::sin(2.0 * 3.141592653589793 * 173.0 * time)
                + impulse;
            input_left[index] = static_cast<float>(sample);
            input_right[index] = static_cast<float>(sample * 0.91);
        }
        const auto report = core.process(
            current,
            actions,
            input_left.data(),
            input_right.data(),
            output_left.data(),
            output_right.data(),
            count);
        CHECK(report.diagnostic == wb::DiagnosticCode::none);
        result.left.insert(result.left.end(), output_left.begin(), output_left.begin() + count);
        result.right.insert(result.right.end(), output_right.begin(), output_right.begin() + count);
        for (std::size_t index = 0U; index < report.decision_count; ++index) {
            result.decisions.push_back(report.decisions[index]);
        }
        cursor += count;
    }
    result.snapshot = core.snapshot();
    return result;
}

[[nodiscard]] Render renderAtRate(
    double sample_rate,
    std::uint32_t block,
    std::uint64_t frames) {
    wb::Core core{};
    CHECK(core.prepare(sample_rate, wb::kMaximumBlockFrames));
    auto controls = wb::defaultControls();
    controls.internal = 0.10;
    controls.motion = wb::MotionMode::drunk;
    controls.wander = 0.61;
    wb::ActionSequences actions{};
    Render result{};
    result.left.reserve(static_cast<std::size_t>(frames));
    result.right.reserve(static_cast<std::size_t>(frames));
    std::vector<float> input(block);
    std::vector<float> left(block);
    std::vector<float> right(block);
    std::uint64_t cursor{};
    while (cursor < frames) {
        const auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            block,
            frames - cursor));
        for (std::uint32_t index = 0U; index < count; ++index) {
            const auto absolute = cursor + index;
            const double time = static_cast<double>(absolute) / sample_rate;
            input[index] = static_cast<float>(
                0.24 * std::sin(2.0 * 3.141592653589793 * 137.0 * time));
        }
        const auto report = core.process(
            controls,
            actions,
            input.data(),
            input.data(),
            left.data(),
            right.data(),
            count);
        CHECK(report.diagnostic == wb::DiagnosticCode::none);
        result.left.insert(result.left.end(), left.begin(), left.begin() + count);
        result.right.insert(result.right.end(), right.begin(), right.begin() + count);
        result.decisions.insert(
            result.decisions.end(),
            report.decisions.begin(),
            report.decisions.begin() + static_cast<std::ptrdiff_t>(report.decision_count));
        cursor += count;
    }
    result.snapshot = core.snapshot();
    return result;
}

void test_defaults_and_prepare() {
    const auto defaults = wb::defaultControls();
    CHECK(wb::validControls(defaults));
    CHECK(wb::sameControls(defaults, wb::Controls{}));
    wb::Core core{};
    CHECK(!core.prepare(7999.0, 128U));
    CHECK(!core.prepare(48000.0, 0U));
    CHECK(!core.prepare(48000.0, wb::kMaximumBlockFrames + 1U));
    for (const double rate : {44100.0, 48000.0, 88200.0, 96000.0}) {
        CHECK(core.prepare(rate, wb::kMaximumBlockFrames));
        CHECK(core.isPrepared());
        CHECK(core.sampleRate() == rate);
        CHECK(core.snapshot().capture_capacity_frames
            == static_cast<std::uint32_t>(std::ceil(rate * wb::kCaptureSeconds)));
    }
}

void test_hover_and_drunk_invariants() {
    auto controls = wb::defaultControls();
    controls.internal = 0.0;
    controls.anchor = 0.50;
    controls.field = 0.35;
    controls.wander = 0.70;
    controls.recurrence = wb::RecurrenceMode::fresh;
    const auto hover = render(controls, 127U, 48000U * 8U, wb::MotionMode::hover);
    CHECK(hover.decisions.size() >= 16U);
    const double hover_field = 0.01 + 0.47 * controls.field;
    for (const auto& event : hover.decisions) {
        CHECK(event.tuple.position >= controls.anchor - hover_field - 1.0e-12);
        CHECK(event.tuple.position <= controls.anchor + hover_field + 1.0e-12);
        CHECK(wb::validDecisionTuple(event.tuple));
    }

    const auto drunk = render(controls, 127U, 48000U * 12U, wb::MotionMode::drunk);
    CHECK(drunk.decisions.size() >= 24U);
    std::vector<double> deltas;
    for (std::size_t index = 1U; index < drunk.decisions.size(); ++index) {
        deltas.push_back(
            drunk.decisions[index].tuple.position
            - drunk.decisions[index - 1U].tuple.position);
    }
    CHECK(deltas.size() >= 2U);
    const double first_mean = std::accumulate(
        deltas.begin(), deltas.end() - 1, 0.0)
        / static_cast<double>(deltas.size() - 1U);
    const double second_mean = std::accumulate(
        deltas.begin() + 1, deltas.end(), 0.0)
        / static_cast<double>(deltas.size() - 1U);
    double covariance{};
    double first_energy{};
    double second_energy{};
    for (std::size_t index = 0U; index + 1U < deltas.size(); ++index) {
        const double first = deltas[index] - first_mean;
        const double second = deltas[index + 1U] - second_mean;
        covariance += first * second;
        first_energy += first * first;
        second_energy += second * second;
    }
    const double correlation = covariance / std::sqrt(first_energy * second_energy);
    CHECK(std::isfinite(correlation));
    CHECK(correlation >= 0.30);

    controls.wander = 0.0;
    const auto still = render(controls, 64U, 48000U * 5U, wb::MotionMode::drunk);
    CHECK(still.decisions.size() >= 8U);
    for (const auto& event : still.decisions) {
        CHECK(event.tuple.position == controls.anchor);
    }
}

void test_recurrence_modes() {
    wb::Core core{};
    CHECK(core.prepare(48000.0, 512U));
    auto controls = wb::defaultControls();
    controls.internal = 0.0;
    controls.motion = wb::MotionMode::drunk;
    controls.wander = 0.60;
    wb::ActionSequences actions{};
    std::vector<float> input(127U, 0.25F);
    std::vector<float> left(127U);
    std::vector<float> right(127U);
    std::vector<wb::DecisionEvent> locked;
    std::uint64_t absolute{};
    const std::uint64_t total = 48000U * 12U;
    while (absolute < total) {
        if (absolute >= 48000U * 5U) controls.recurrence = wb::RecurrenceMode::locked;
        const auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            input.size(), total - absolute));
        const auto report = core.process(
            controls, actions, input.data(), input.data(), left.data(), right.data(), count);
        for (std::size_t index = 0U; index < report.decision_count; ++index) {
            if (report.decisions[index].recurrence == wb::RecurrenceMode::locked) {
                locked.push_back(report.decisions[index]);
            }
        }
        absolute += count;
    }
    CHECK(locked.size() >= wb::kHistoryCapacity * 2U);
    for (std::size_t index = wb::kHistoryCapacity; index < locked.size(); ++index) {
        CHECK(sameTuple(
            locked[index].tuple,
            locked[index % wb::kHistoryCapacity].tuple));
        CHECK(locked[index].replayed);
    }
}

void test_freeze_clear_and_state() {
    wb::Core core{};
    CHECK(core.prepare(48000.0, 256U));
    auto controls = wb::defaultControls();
    controls.internal = 0.0;
    wb::ActionSequences actions{};
    std::vector<float> input(256U, 0.2F);
    std::vector<float> left(256U);
    std::vector<float> right(256U);
    for (int block = 0; block < 300; ++block) {
        static_cast<void>(core.process(
            controls, actions, input.data(), input.data(), left.data(), right.data(), 256U));
    }
    const auto before = core.snapshot();
    ++actions.freeze;
    static_cast<void>(core.process(
        controls, actions, input.data(), input.data(), left.data(), right.data(), 256U));
    const auto frozen_start = core.snapshot();
    for (int block = 0; block < 50; ++block) {
        static_cast<void>(core.process(
            controls, actions, input.data(), input.data(), left.data(), right.data(), 256U));
    }
    const auto frozen_end = core.snapshot();
    CHECK(frozen_start.frozen);
    CHECK(frozen_start.capture_write_frame == frozen_end.capture_write_frame);
    CHECK(frozen_start.capture_write_frame >= before.capture_write_frame);

    ++actions.freeze;
    ++actions.clear;
    for (int block = 0; block < 20; ++block) {
        static_cast<void>(core.process(
            controls, actions, input.data(), input.data(), left.data(), right.data(), 256U));
    }
    const auto cleared = core.snapshot();
    CHECK(!cleared.frozen);
    CHECK(cleared.capture_epoch > before.capture_epoch);
    CHECK(cleared.diagnostics.clear_count == 1U);
    CHECK(cleared.latched_fault == wb::DiagnosticCode::none);

    const auto state = core.captureState();
    wb::Core restored{};
    CHECK(restored.prepare(48000.0, 256U));
    CHECK(restored.recallState(state));
    const auto restored_state = restored.captureState();
    CHECK(wb::sameControls(state.controls, restored_state.controls));
    CHECK(state.history_count == restored_state.history_count);
    CHECK(restored.snapshot().capture_valid_frames == 0U);
    auto invalid = state;
    invalid.version = 999U;
    const auto prior = restored.captureState();
    CHECK(!restored.recallState(invalid));
    const auto after = restored.captureState();
    CHECK(wb::sameControls(prior.controls, after.controls));
    CHECK(prior.decision_ordinal == after.decision_ordinal);

    invalid = state;
    invalid.controls.motion = static_cast<wb::MotionMode>(99U);
    CHECK(!restored.recallState(invalid));
    invalid = state;
    invalid.controls.body = std::numeric_limits<double>::infinity();
    CHECK(!restored.recallState(invalid));
    invalid = state;
    invalid.random_streams[1] &= ~std::uint64_t{1U};
    CHECK(!restored.recallState(invalid));
    invalid = state;
    invalid.hover_phase = std::numeric_limits<double>::quiet_NaN();
    CHECK(!restored.recallState(invalid));
    const auto after_rejections = restored.captureState();
    CHECK(wb::sameControls(prior.controls, after_rejections.controls));
    CHECK(prior.decision_ordinal == after_rejections.decision_ordinal);
}

void test_supported_rate_partition_properties() {
    for (const double rate : {44100.0, 88200.0, 96000.0}) {
        const auto frames = static_cast<std::uint64_t>(rate * 0.75);
        const auto small = renderAtRate(rate, 17U, frames);
        const auto irregular = renderAtRate(rate, 511U, frames);
        CHECK(small.left == irregular.left);
        CHECK(small.right == irregular.right);
        CHECK(small.decisions.size() == irregular.decisions.size());
        CHECK(small.snapshot.active_voice_count <= wb::kVoiceCount);
        CHECK(small.snapshot.capture_valid_frames <= small.snapshot.capture_capacity_frames);
        for (std::size_t index = 0U; index < small.decisions.size(); ++index) {
            CHECK(small.decisions[index].absolute_frame
                == irregular.decisions[index].absolute_frame);
            CHECK(sameTuple(small.decisions[index].tuple, irregular.decisions[index].tuple));
        }
    }
}

void test_partition_determinism_and_safety() {
    auto controls = wb::defaultControls();
    controls.internal = 0.15;
    controls.motion = wb::MotionMode::drunk;
    controls.wander = 0.62;
    const auto one = render(controls, 1U, 48000U * 4U, wb::MotionMode::drunk);
    const auto odd = render(controls, 127U, 48000U * 4U, wb::MotionMode::drunk);
    const auto large = render(controls, 1024U, 48000U * 4U, wb::MotionMode::drunk);
    CHECK(one.left == odd.left);
    CHECK(one.right == odd.right);
    CHECK(one.left == large.left);
    CHECK(one.decisions.size() == odd.decisions.size());
    CHECK(one.decisions.size() == large.decisions.size());
    for (std::size_t index = 0U; index < one.decisions.size(); ++index) {
        CHECK(one.decisions[index].absolute_frame == odd.decisions[index].absolute_frame);
        CHECK(one.decisions[index].absolute_frame == large.decisions[index].absolute_frame);
        CHECK(sameTuple(one.decisions[index].tuple, odd.decisions[index].tuple));
        CHECK(sameTuple(one.decisions[index].tuple, large.decisions[index].tuple));
    }
    for (const auto sample : one.left) {
        CHECK(std::isfinite(sample));
        CHECK(std::abs(sample) < 0.98F);
    }

    wb::Core silent_core{};
    CHECK(silent_core.prepare(48000.0, 64U));
    auto silent = wb::defaultControls();
    silent.external = 0.0;
    silent.internal = 0.0;
    silent.dry = 0.0;
    silent.memory = 0.0;
    silent.body = 0.0;
    std::vector<float> zeros(65U);
    std::vector<float> left(65U, 1.0F);
    std::vector<float> right(65U, 1.0F);
    const auto report = silent_core.process(
        silent, {}, zeros.data(), zeros.data(), left.data(), right.data(), 64U);
    CHECK(report.decision_count == 0U);
    CHECK(std::all_of(left.begin(), left.begin() + 64, [](float value) { return value == 0.0F; }));
    CHECK(std::all_of(right.begin(), right.begin() + 64, [](float value) { return value == 0.0F; }));

    auto invalid_controls = silent;
    invalid_controls.anchor = std::numeric_limits<double>::quiet_NaN();
    const auto invalid_report = silent_core.process(
        invalid_controls, {}, zeros.data(), zeros.data(), left.data(), right.data(), 64U);
    CHECK(invalid_report.diagnostic == wb::DiagnosticCode::invalid_controls);
    const auto oversized = silent_core.process(
        silent, {}, zeros.data(), zeros.data(), left.data(), right.data(), 65U);
    CHECK(oversized.diagnostic == wb::DiagnosticCode::oversized_block);
}

}  // namespace

int main() {
    test_defaults_and_prepare();
    test_hover_and_drunk_invariants();
    test_recurrence_modes();
    test_freeze_clear_and_state();
    test_supported_rate_partition_properties();
    test_partition_determinism_and_safety();
    if (failures != 0) {
        std::cerr << failures << " Wanderbody core test(s) failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "Wanderbody core tests passed\n";
    return EXIT_SUCCESS;
}
