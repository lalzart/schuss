#pragma once

#include "schuss/pamplist/core.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace schuss::pamplist {

enum class SemanticControl : std::uint8_t {
    voice_model,
    voice_pitch,
    voice_harmonics,
    voice_timbre,
    voice_morph,
    voice_decay,
    voice_colour,
    voice_level,
    route_trigger,
    route_pitch,
    route_model_sweep,
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
    global_drive,
    global_cohere,
    global_root,
    global_spread,
    global_tail,
    global_damping,
    global_width,
    global_duck,
    global_bpm,
    global_master,
    global_unassigned,
    toggle_lane_mode,
    select_page_1,
    select_page_2,
    select_page_3,
    select_page_4,
    select_page_5,
    select_page_6,
    select_page_7,
    select_global,
    clear_fx,
    none,
};

enum class MappingStatus : std::uint8_t {
    accepted_continuous,
    accepted_press,
    accepted_release,
    accepted_hold,
    accepted_noop,
    ignored_channel,
    unknown_cc,
    invalid_message,
};

struct MappingResult final {
    MappingStatus status{MappingStatus::unknown_cc};
    SemanticControl semantic{SemanticControl::none};
    std::uint8_t cc{};
    std::uint8_t value{};
    std::uint8_t page{};
    std::uint8_t discrete_value{};
    std::uint32_t integer_value{};
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
    std::uint64_t ignored_global_control_count{};
};

[[nodiscard]] std::uint8_t launchControlMidiChannel() noexcept;
[[nodiscard]] std::string_view controlMapSha256() noexcept;
[[nodiscard]] std::string_view controllerTopologySha256() noexcept;
[[nodiscard]] MappingResult mapMidiCc(
    int one_based_channel,
    int cc,
    int value,
    std::uint8_t selected_page,
    LaneControlMode lane_control_mode) noexcept;
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
    std::array<bool, kPageCount> button_down_{};
    ControllerDiagnostics diagnostics_{};
};

}  // namespace schuss::pamplist
