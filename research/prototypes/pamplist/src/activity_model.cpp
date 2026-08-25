#include "schuss/pamplist/activity_model.hpp"

#include <algorithm>
#include <cmath>

namespace schuss::pamplist {
namespace {

[[nodiscard]] float displayLevel(double energy, std::uint64_t frames) noexcept {
    if (!(energy > 0.0) || frames == 0U || !std::isfinite(energy)) return 0.0F;
    const auto mean_square = energy / (2.0 * static_cast<double>(frames));
    if (!(mean_square > 0.0) || !std::isfinite(mean_square)) return 0.0F;
    const auto rms = std::sqrt(mean_square);
    const auto decibels = 20.0 * std::log10(std::max(rms, 1.0e-4));
    const auto normalized = (decibels + 80.0) / 80.0;
    return static_cast<float>(std::clamp(normalized, 0.0, 1.0));
}

}  // namespace

void ActivityReducer::capture(const Snapshot& snapshot) noexcept {
    previous_frame_ = snapshot.absolute_frame;
    previous_energy_ = snapshot.lane_output_energy;
    previous_triggers_ = snapshot.diagnostics.lane_trigger_count;
    previous_cohesion_energy_ = snapshot.cohesion.dry_difference_energy;
    previous_clear_count_ = snapshot.diagnostics.effect_clear_count;
    initialized_ = true;
}

ActivitySample ActivityReducer::reduce(const Snapshot& snapshot) noexcept {
    ActivitySample result{};
    bool rollback = initialized_ && snapshot.absolute_frame < previous_frame_;
    rollback = rollback
        || (initialized_
            && snapshot.cohesion.dry_difference_energy
                < previous_cohesion_energy_);
    for (std::size_t lane = 0; initialized_ && lane < kLaneCount; ++lane) {
        rollback = rollback
            || snapshot.lane_output_energy[lane] < previous_energy_[lane]
            || snapshot.diagnostics.lane_trigger_count[lane]
                < previous_triggers_[lane];
    }
    rollback = rollback
        || (initialized_
            && snapshot.diagnostics.effect_clear_count
                < previous_clear_count_);

    if (!initialized_ || rollback) {
        result.rebased = initialized_;
        capture(snapshot);
        return result;
    }

    result.frame_count = snapshot.absolute_frame - previous_frame_;
    for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
        const auto energy = std::max(
            0.0, snapshot.lane_output_energy[lane] - previous_energy_[lane]);
        result.lane_levels[lane] = displayLevel(energy, result.frame_count);
        result.trigger_deltas[lane] =
            snapshot.diagnostics.lane_trigger_count[lane]
            - previous_triggers_[lane];
        if (result.trigger_deltas[lane] != 0U) {
            result.trigger_mask = static_cast<std::uint8_t>(
                result.trigger_mask | (1U << lane));
        }
    }
    result.cohesion_level = displayLevel(
        std::max(
            0.0,
            snapshot.cohesion.dry_difference_energy
                - previous_cohesion_energy_),
        result.frame_count);
    result.effect_cleared = snapshot.diagnostics.effect_clear_count
        > previous_clear_count_;
    capture(snapshot);
    return result;
}

void ActivityReducer::reset() noexcept {
    initialized_ = false;
    previous_frame_ = 0U;
    previous_energy_.fill(0.0);
    previous_triggers_.fill(0U);
    previous_cohesion_energy_ = 0.0;
    previous_clear_count_ = 0U;
}

void ImpactHistory::push(const ActivitySample& sample) noexcept {
    samples_[write_index_] = sample;
    write_index_ = (write_index_ + 1U) % samples_.size();
    size_ = std::min(size_ + 1U, samples_.size());
}

void ImpactHistory::clear() noexcept {
    samples_ = {};
    write_index_ = 0U;
    size_ = 0U;
}

std::size_t ImpactHistory::size() const noexcept { return size_; }

ActivitySample ImpactHistory::oldest(std::size_t index) const noexcept {
    if (index >= size_) return {};
    const auto first = size_ == samples_.size() ? write_index_ : 0U;
    return samples_[(first + index) % samples_.size()];
}

}  // namespace schuss::pamplist
