#pragma once

#include "layerwell/core.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string_view>

namespace layerwell {

enum class SourceControlStatus : std::uint8_t {
    accepted,
    accepted_release,
    unassigned,
    inactive,
    invalid,
    capacity_exceeded,
};

struct SourceProjection final {
    std::array<std::uint8_t, 16> encoder_values{};
    std::array<bool, 16> encoder_assigned{};
    std::array<bool, 8> button_assigned{};
    std::array<bool, 8> button_active{};
    std::uint64_t processed_frames{};
};

// Owns the two exact public source Cores. Layerwell never reaches into source
// internals; every control terminates at the existing public mapping reducer.
class SourceRack final {
public:
    SourceRack();
    ~SourceRack();

    SourceRack(const SourceRack&) = delete;
    SourceRack& operator=(const SourceRack&) = delete;
    SourceRack(SourceRack&&) noexcept;
    SourceRack& operator=(SourceRack&&) noexcept;

    bool prepare(double sample_rate, std::uint32_t maximum_block_frames) noexcept;
    bool reset() noexcept;

    SourceControlStatus applyRelativeEncoder(
        SourceId source,
        std::size_t slot,
        std::uint8_t relative_value,
        std::uint64_t ingress_sequence) noexcept;

    SourceControlStatus applyButton(
        SourceId source,
        std::size_t slot,
        std::uint8_t value,
        std::uint64_t ingress_sequence) noexcept;

    bool render(
        SourceId source,
        std::int32_t* left_q27,
        std::int32_t* right_q27,
        std::uint32_t frames) noexcept;

    [[nodiscard]] SourceProjection projection(SourceId source) const noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

[[nodiscard]] std::string_view sourceEncoderLabel(
    SourceId source,
    std::size_t slot) noexcept;
[[nodiscard]] std::string_view sourceButtonLabel(
    SourceId source,
    std::size_t slot) noexcept;

}  // namespace layerwell
