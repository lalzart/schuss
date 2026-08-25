#include "schuss/pamplist/activity_model.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

namespace pam = schuss::pamplist;

namespace {

[[noreturn]] void fail(const std::string& message) {
    std::cerr << "pamplist_activity_model_tests: " << message << '\n';
    std::exit(1);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

void testAcceptedTelemetryReduction() {
    pam::ActivityReducer reducer;
    pam::Snapshot first{};
    first.absolute_frame = 100U;
    const auto initial = reducer.reduce(first);
    expect(initial.frame_count == 0U && initial.trigger_mask == 0U
            && !initial.effect_cleared && !initial.rebased,
        "initial accepted Snapshot was not a quiet baseline");
    const auto duplicate = reducer.reduce(first);
    expect(duplicate.frame_count == 0U && !duplicate.rebased
            && duplicate.trigger_mask == 0U,
        "duplicate accepted Snapshot was mistaken for a reset");

    auto next = first;
    next.absolute_frame = 200U;
    // Stereo mean-square 1e-4 -> RMS 0.01 -> -40 dBFS -> display 0.5.
    next.lane_output_energy[0] = 2.0 * 100.0 * 1.0e-4;
    next.lane_output_energy[1] = 2.0 * 100.0 * 1.0e-8;
    next.diagnostics.lane_trigger_count[0] = 2U;
    next.diagnostics.lane_trigger_count[3] = 1U;
    next.cohesion.dry_difference_energy = 2.0 * 100.0 * 1.0e-6;
    next.diagnostics.effect_clear_count = 1U;
    const auto activity = reducer.reduce(next);
    expect(activity.frame_count == 100U
            && std::abs(activity.lane_levels[0] - 0.5F) < 1.0e-5F
            && activity.lane_levels[1] == 0.0F,
        "logarithmic lane activity reduction mismatch");
    expect(activity.trigger_deltas[0] == 2U
            && activity.trigger_deltas[3] == 1U
            && activity.trigger_mask == ((1U << 0U) | (1U << 3U)),
        "trigger deltas were not retained across the UI poll");
    expect(activity.cohesion_level > 0.0F
            && activity.cohesion_level < 1.0F
            && activity.effect_cleared,
        "cohesion or Clear feedback was not reduced");

    auto reset = next;
    reset.absolute_frame = 16U;
    reset.lane_output_energy.fill(0.0);
    reset.diagnostics.lane_trigger_count.fill(0U);
    reset.cohesion.dry_difference_energy = 0.0;
    reset.diagnostics.effect_clear_count = 0U;
    const auto rebased = reducer.reduce(reset);
    expect(rebased.rebased && rebased.frame_count == 0U
            && rebased.trigger_mask == 0U && !rebased.effect_cleared
            && std::all_of(
                rebased.lane_levels.begin(), rebased.lane_levels.end(),
                [](float value) { return value == 0.0F; }),
        "counter rollback created false visual activity");
}

void testFixedHistoryOrdering() {
    pam::ImpactHistory history;
    for (std::size_t index = 0U;
         index < pam::kImpactHistoryCapacity + 8U;
         ++index) {
        pam::ActivitySample sample{};
        sample.frame_count = index;
        sample.lane_levels[0] = static_cast<float>(index) / 256.0F;
        history.push(sample);
    }
    expect(history.size() == pam::kImpactHistoryCapacity,
        "impact history exceeded fixed capacity");
    expect(history.oldest(0U).frame_count == 8U
            && history.oldest(history.size() - 1U).frame_count
                == pam::kImpactHistoryCapacity + 7U,
        "wrapped impact history lost chronological order");
    expect(history.oldest(history.size()).frame_count == 0U,
        "out-of-range history read did not fail closed");
    history.clear();
    expect(history.size() == 0U, "history clear did not reset fixed state");
}

}  // namespace

int main() {
    testAcceptedTelemetryReduction();
    testFixedHistoryOrdering();
    std::cout << "pamplist_activity_model_tests: pass\n";
    return 0;
}
