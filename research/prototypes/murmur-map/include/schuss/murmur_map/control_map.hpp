#pragma once

#include "schuss/murmur_map/core.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace schuss::murmur_map {

enum class ControlId : std::uint8_t {
    tempo,
    travel,
    memory,
    length,
    roam,
    home,
    radius,
    density,
    draft_interval,
    draft_activity,
    draft_timbre,
    draft_color,
    draft_decay,
    draft_level,
    draft_pan,
    root,
    select_waypoint_a,
    select_waypoint_b,
    select_waypoint_c,
    select_waypoint_d,
    select_anchor,
    select_thread,
    select_spark,
    capture_replace,
    unassigned,
};

enum class ControlKind : std::uint8_t {
    continuous,
    action,
};

enum class MappingStatus : std::uint8_t {
    accepted_continuous,
    accepted_action_press,
    accepted_action_release,
    ignored_channel,
    unknown_controller,
    invalid_value,
};

struct EncoderDescriptor final {
    ControlId id;
    std::uint8_t cc;
    std::string_view label;
    std::string_view semantic_key;
    std::int32_t minimum;
    std::int32_t maximum;
};

struct ButtonDescriptor final {
    ControlId id;
    std::uint8_t cc;
    std::string_view label;
    std::string_view semantic_key;
};

struct MappingResult final {
    MappingStatus status{MappingStatus::unknown_controller};
    ControlId id{ControlId::unassigned};
    std::int32_t mapped_value{};
    std::uint8_t midi_value{};

    [[nodiscard]] constexpr bool accepted() const noexcept {
        return status == MappingStatus::accepted_continuous
            || status == MappingStatus::accepted_action_press
            || status == MappingStatus::accepted_action_release;
    }

    [[nodiscard]] constexpr bool dispatchesSemantic() const noexcept {
        return status == MappingStatus::accepted_continuous
            || status == MappingStatus::accepted_action_press;
    }
};

struct EditorState final {
    std::uint8_t selected_waypoint{};
    Lane selected_lane{Lane::anchor};
    std::uint16_t draft_x_u15{};
    std::uint16_t draft_y_u15{};
    LaneState draft_lane{};
    bool dirty{};
    std::uint64_t draft_discard_count{};
    std::uint64_t capture_count{};
    std::uint64_t empty_capture_count{};
    std::uint64_t rejected_capture_count{};
};

struct ControllerState final {
    Controls controls{};
    EditorState editor{};
};

struct ApplyResult final {
    bool handled{};
    bool controls_changed{};
    bool draft_changed{};
    bool captured{};
};

[[nodiscard]] ControllerState defaultControllerState() noexcept;
[[nodiscard]] const std::array<EncoderDescriptor, 16>& encoderDescriptors() noexcept;
[[nodiscard]] const std::array<ButtonDescriptor, 8>& buttonDescriptors() noexcept;
[[nodiscard]] const EncoderDescriptor* encoderDescriptor(std::uint8_t cc) noexcept;
[[nodiscard]] const ButtonDescriptor* buttonDescriptor(std::uint8_t cc) noexcept;
[[nodiscard]] std::uint8_t launchControlMidiChannel() noexcept;
[[nodiscard]] std::string_view controlMapSha256() noexcept;
[[nodiscard]] std::string_view controllerTopologySha256() noexcept;
[[nodiscard]] MappingResult mapMidiCc(
    std::uint8_t one_based_channel,
    std::uint8_t cc,
    std::uint8_t value) noexcept;
[[nodiscard]] ApplyResult applyMapping(
    ControllerState& state,
    const MappingResult& mapping) noexcept;
[[nodiscard]] ApplyResult selectWaypoint(
    ControllerState& state,
    std::uint8_t waypoint_index) noexcept;
[[nodiscard]] ApplyResult selectLane(
    ControllerState& state,
    Lane lane) noexcept;
[[nodiscard]] ApplyResult setDraftPosition(
    ControllerState& state,
    std::uint16_t x_u15,
    std::uint16_t y_u15) noexcept;
[[nodiscard]] ApplyResult captureDraft(ControllerState& state) noexcept;
void reloadDraft(ControllerState& state) noexcept;

}  // namespace schuss::murmur_map
