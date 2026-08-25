#pragma once

#include "schuss/pamplist/core.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace schuss::pamplist {

inline constexpr std::size_t kImpactHistoryCapacity = 192U;

struct ActivitySample final {
    std::array<float, kLaneCount> lane_levels{};
    std::array<std::uint64_t, kLaneCount> trigger_deltas{};
    std::uint8_t trigger_mask{};
    float cohesion_level{};
    bool effect_cleared{};
    bool rebased{};
    std::uint64_t frame_count{};
};

// UI-side reducer for monotone accepted Snapshot telemetry. The reducer owns
// no audio buffers and turns any reset/counter rollback into one bounded zero
// rebase rather than a false full-scale impact.
class ActivityReducer final {
public:
    [[nodiscard]] ActivitySample reduce(const Snapshot& snapshot) noexcept;
    void reset() noexcept;

private:
    void capture(const Snapshot& snapshot) noexcept;

    bool initialized_{};
    std::uint64_t previous_frame_{};
    std::array<double, kLaneCount> previous_energy_{};
    std::array<std::uint64_t, kLaneCount> previous_triggers_{};
    double previous_cohesion_energy_{};
    std::uint64_t previous_clear_count_{};
};

// Fixed UI history with chronological readback. It is intentionally a plain
// instrument-local value rather than shared runtime or DSP state.
class ImpactHistory final {
public:
    void push(const ActivitySample& sample) noexcept;
    void clear() noexcept;
    [[nodiscard]] std::size_t size() const noexcept;
    [[nodiscard]] ActivitySample oldest(std::size_t index) const noexcept;

private:
    std::array<ActivitySample, kImpactHistoryCapacity> samples_{};
    std::size_t write_index_{};
    std::size_t size_{};
};

}  // namespace schuss::pamplist
