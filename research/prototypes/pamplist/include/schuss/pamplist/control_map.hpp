#pragma once

#include "schuss/pamplist/core.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace schuss::pamplist {

enum class SemanticControl : std::uint8_t {
    route_trigger,
    route_pitch,
    route_model,
    route_harmonics,
    route_timbre,
    route_morph,
    route_decay,
    route_level,
    rate,
    phase,
    shape,
    hits,
    rotation,
    probability,
    repeat,
    amplitude,
    select_lane_1,
    select_lane_2,
    select_lane_3,
    select_lane_4,
    select_lane_5,
    select_lane_6,
    select_lane_7,
    select_lane_8,
    none,
};

enum class MappingStatus : std::uint8_t {
    accepted_continuous,
    accepted_press,
    accepted_release,
    accepted_hold,
    ignored_channel,
    unknown_cc,
    invalid_message,
};

struct MappingResult final {
    MappingStatus status{MappingStatus::unknown_cc};
    SemanticControl semantic{SemanticControl::none};
    std::uint8_t cc{};
    std::uint8_t value{};
    std::uint8_t lane{};
    std::uint8_t discrete_value{};
    float continuous_value{};

    [[nodiscard]] bool accepted() const noexcept;
    [[nodiscard]] bool dispatches() const noexcept;
};

struct ControllerDiagnostics final {
    std::uint64_t accepted_message_count{};
    std::uint64_t dispatched_message_count{};
    std::uint64_t ignored_channel_count{};
    std::uint64_t unknown_cc_count{};
    std::uint64_t invalid_message_count{};
};

[[nodiscard]] std::uint8_t launchControlMidiChannel() noexcept;
[[nodiscard]] std::string_view controlMapSha256() noexcept;
[[nodiscard]] std::string_view controllerTopologySha256() noexcept;
[[nodiscard]] MappingResult mapMidiCc(
    int one_based_channel,
    int cc,
    int value) noexcept;
[[nodiscard]] bool applyMapping(
    Controls& controls,
    const MappingResult& mapping) noexcept;

class ControllerAdapter final {
public:
    [[nodiscard]] MappingResult handleCc(
        Controls& controls,
        int one_based_channel,
        int cc,
        int value) noexcept;

    void reset() noexcept;
    [[nodiscard]] const ControllerDiagnostics& diagnostics() const noexcept;

private:
    std::array<bool, kLaneCount> button_down_{};
    ControllerDiagnostics diagnostics_{};
};

}  // namespace schuss::pamplist
