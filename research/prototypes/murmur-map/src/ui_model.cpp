#include "schuss/murmur_map/ui_model.hpp"

#include <algorithm>
#include <array>
#include <iomanip>
#include <sstream>
#include <string>

namespace schuss::murmur_map {
namespace {

[[nodiscard]] ApplyResult applyExact(
    ControllerState& state,
    ControlId id,
    std::int32_t value) noexcept {
    return applyMapping(
        state,
        MappingResult{MappingStatus::accepted_continuous, id, value, 0U});
}

}  // namespace

ApplyResult applyUiCommand(
    ControllerState& state,
    ActionSequences& actions,
    bool& locked,
    std::uint16_t& prior_memory_u15,
    const UiCommand& command) noexcept {
    switch (command.kind) {
        case UiCommandKind::set_tempo: return applyExact(state, ControlId::tempo, command.value);
        case UiCommandKind::set_travel: return applyExact(state, ControlId::travel, command.value);
        case UiCommandKind::set_memory: {
            const auto result = applyExact(state, ControlId::memory, command.value);
            if (result.controls_changed) {
                locked = command.value == 32767;
                if (!locked) prior_memory_u15 = static_cast<std::uint16_t>(command.value);
            }
            return result;
        }
        case UiCommandKind::set_length: return applyExact(state, ControlId::length, command.value);
        case UiCommandKind::set_roam: return applyExact(state, ControlId::roam, command.value);
        case UiCommandKind::set_home_probability: return applyExact(state, ControlId::home, command.value);
        case UiCommandKind::set_radius: return applyExact(state, ControlId::radius, command.value);
        case UiCommandKind::set_density: return applyExact(state, ControlId::density, command.value);
        case UiCommandKind::set_root: return applyExact(state, ControlId::root, command.value);
        case UiCommandKind::set_scale: {
            if (command.value < 0
                || command.value > static_cast<std::int32_t>(Scale::octatonic_half_whole)) return {};
            const auto scale = static_cast<Scale>(command.value);
            if (state.controls.scale == scale) return ApplyResult{true, false, false, false};
            state.controls.scale = scale;
            return ApplyResult{true, true, false, false};
        }
        case UiCommandKind::set_run: {
            const bool next = command.value != 0;
            if (state.controls.run == next) return ApplyResult{true, false, false, false};
            state.controls.run = next;
            return ApplyResult{true, true, false, false};
        }
        case UiCommandKind::set_lock: {
            const bool next = command.value != 0;
            if (next == locked) return ApplyResult{true, false, false, false};
            if (next) {
                if (state.controls.memory_u15 != 32767U) prior_memory_u15 = state.controls.memory_u15;
                state.controls.memory_u15 = 32767U;
            } else {
                state.controls.memory_u15 = std::min<std::uint16_t>(prior_memory_u15, 32766U);
            }
            locked = next;
            return ApplyResult{true, true, false, false};
        }
        case UiCommandKind::set_home_index: {
            if (command.value < 0 || command.value >= state.controls.waypoint_count) return {};
            const auto next = static_cast<std::uint8_t>(command.value);
            if (state.controls.home_index == next) return ApplyResult{true, false, false, false};
            state.controls.home_index = next;
            return ApplyResult{true, true, false, false};
        }
        case UiCommandKind::select_waypoint:
            if (command.value < 0 || command.value > 255) return {};
            return selectWaypoint(state, static_cast<std::uint8_t>(command.value));
        case UiCommandKind::select_lane:
            if (command.value < 0 || command.value >= static_cast<std::int32_t>(kLaneCount)) return {};
            return selectLane(state, static_cast<Lane>(command.value));
        case UiCommandKind::set_draft_interval: return applyExact(state, ControlId::draft_interval, command.value);
        case UiCommandKind::set_draft_activity: return applyExact(state, ControlId::draft_activity, command.value);
        case UiCommandKind::set_draft_timbre: return applyExact(state, ControlId::draft_timbre, command.value);
        case UiCommandKind::set_draft_color: return applyExact(state, ControlId::draft_color, command.value);
        case UiCommandKind::set_draft_decay: return applyExact(state, ControlId::draft_decay, command.value);
        case UiCommandKind::set_draft_level: return applyExact(state, ControlId::draft_level, command.value);
        case UiCommandKind::set_draft_pan: return applyExact(state, ControlId::draft_pan, command.value);
        case UiCommandKind::set_draft_position:
            if (command.value < 0 || command.value > 32767
                || command.value_2 < 0 || command.value_2 > 32767) return {};
            return setDraftPosition(
                state,
                static_cast<std::uint16_t>(command.value),
                static_cast<std::uint16_t>(command.value_2));
        case UiCommandKind::capture: return captureDraft(state);
        case UiCommandKind::reset:
            state = defaultControllerState();
            locked = false;
            prior_memory_u15 = state.controls.memory_u15;
            ++actions.reset;
            return ApplyResult{true, true, true, false};
        case UiCommandKind::panic:
            ++actions.panic;
            return ApplyResult{true, false, false, false};
        case UiCommandKind::reseed:
            actions.reseed_value = command.sequence == 0U ? kDefaultSeed : command.sequence;
            ++actions.reseed;
            return ApplyResult{true, false, false, false};
    }
    return {};
}

std::string formatGlobalStatus(const Snapshot& snapshot) {
    const auto& controls = snapshot.accepted_controls;
    std::ostringstream stream;
    stream << (controls.run ? "RUN" : "PAUSED")
           << " | " << controls.tempo_milli_bpm / 1000.0 << " BPM"
           << " | memory " << std::fixed << std::setprecision(2)
           << static_cast<double>(controls.memory_u15) / 32767.0
           << " x" << static_cast<unsigned>(controls.memory_length)
           << " | " << scaleName(controls.scale)
           << " root " << static_cast<unsigned>(controls.root_midi_note);
    return stream.str();
}

std::string formatEditorStatus(const EditorState& editor) {
    std::ostringstream stream;
    stream << "Waypoint " << static_cast<char>('A' + editor.selected_waypoint)
           << " / " << laneName(editor.selected_lane)
           << (editor.dirty ? " | DRAFT — CAPTURE TO APPLY" : " | accepted")
           << " | captures " << editor.capture_count
           << " | discarded " << editor.draft_discard_count;
    return stream.str();
}

std::string formatDiagnostics(const PresentationSnapshot& snapshot) {
    std::ostringstream stream;
    stream << "MIDI " << snapshot.midi_receive_count
           << " recv / " << snapshot.midi_ignored_count << " ignored"
           << " | last ch " << static_cast<unsigned>(snapshot.last_midi_channel)
           << " CC" << static_cast<unsigned>(snapshot.last_midi_cc)
           << '=' << static_cast<unsigned>(snapshot.last_midi_value)
           << " | route " << snapshot.core.route_transition_count
           << " | events " << snapshot.core.lane_event_counts[0] << '/'
           << snapshot.core.lane_event_counts[1] << '/'
           << snapshot.core.lane_event_counts[2]
           << " | drop " << snapshot.core.dropped_event_count
           << " | repair " << snapshot.core.repair_count
           << " | clamp " << snapshot.core.clamp_count;
    return stream.str();
}

std::array<std::string, 8> launchControlTopLabels() {
    return {{"TEMPO", "TRAVEL", "MEMORY", "LENGTH", "ROAM", "HOME", "RADIUS", "DENSITY"}};
}

std::array<std::string, 8> launchControlBottomLabels() {
    return {{"INTERVAL", "ACTIVITY", "TIMBRE", "COLOR", "DECAY", "LEVEL", "PAN", "ROOT"}};
}

}  // namespace schuss::murmur_map
