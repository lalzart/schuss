#pragma once

#include "tidepit/control_map.hpp"
#include "tidepit/core.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace tidepit {

struct ButtonPresentation {
    std::string_view label;
    std::string_view state;
    bool latched_active{};
};

[[nodiscard]] ButtonPresentation buttonPresentation(
    ControlId id,
    const Snapshot& snapshot,
    bool mutate_feedback = false
) noexcept;

inline constexpr std::size_t kScopeFrameSamples = 1024;

struct ScopeFrame {
    std::array<float, kScopeFrameSamples> left{};
    std::array<float, kScopeFrameSamples> right{};
    std::size_t sample_count{};
    std::uint64_t generation{};
    float peak_left{};
    float peak_right{};
};

// Audio-thread-owned fixed-capacity accumulator. A completed frame remains
// valid until the next pushSample call and can be copied into an SPSC mailbox.
class ScopeAccumulator final {
public:
    void reset() noexcept;

    [[nodiscard]] const ScopeFrame* pushSample(float left, float right) noexcept;

private:
    ScopeFrame frame_{};
    std::size_t write_index_{};
    std::uint64_t next_generation_{1};
};

}  // namespace tidepit
