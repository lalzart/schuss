#pragma once

#include "schuss/murmur_map/control_map.hpp"

#include <array>
#include <cstdint>
#include <string>

namespace schuss::murmur_map {

enum class UiCommandKind : std::uint8_t {
    set_tempo,
    set_travel,
    set_memory,
    set_length,
    set_roam,
    set_home_probability,
    set_radius,
    set_density,
    set_root,
    set_scale,
    set_run,
    set_lock,
    set_home_index,
    select_waypoint,
    select_lane,
    set_draft_interval,
    set_draft_activity,
    set_draft_timbre,
    set_draft_color,
    set_draft_decay,
    set_draft_level,
    set_draft_pan,
    set_draft_position,
    capture,
    reset,
    panic,
    reseed,
};

struct UiCommand final {
    UiCommandKind kind{UiCommandKind::set_tempo};
    std::int32_t value{};
    std::int32_t value_2{};
    std::uint64_t sequence{};
};

struct PresentationSnapshot final {
    Snapshot core{};
    EditorState editor{};
    std::uint64_t midi_receive_count{};
    std::uint64_t midi_ignored_count{};
    std::uint8_t last_midi_channel{};
    std::uint8_t last_midi_cc{};
    std::uint8_t last_midi_value{};
    MappingStatus last_mapping_status{MappingStatus::unknown_controller};
    std::uint64_t ui_command_drop_count{};
};

[[nodiscard]] ApplyResult applyUiCommand(
    ControllerState& state,
    ActionSequences& actions,
    bool& locked,
    std::uint16_t& prior_memory_u15,
    const UiCommand& command) noexcept;
[[nodiscard]] std::string formatGlobalStatus(const Snapshot& snapshot);
[[nodiscard]] std::string formatEditorStatus(const EditorState& editor);
[[nodiscard]] std::string formatDiagnostics(const PresentationSnapshot& snapshot);
[[nodiscard]] std::array<std::string, 8> launchControlTopLabels();
[[nodiscard]] std::array<std::string, 8> launchControlBottomLabels();

}  // namespace schuss::murmur_map
