#include "schuss/murmur_map/ui_model.hpp"

#include <iostream>
#include <string>

namespace mm = schuss::murmur_map;

int main() {
    auto state = mm::defaultControllerState();
    mm::ActionSequences actions{};
    bool locked = false;
    auto prior_memory = state.controls.memory_u15;
    auto result = mm::applyUiCommand(
        state, actions, locked, prior_memory,
        {mm::UiCommandKind::set_lock, 1, 0, 1U});
    if (!result.controls_changed || !locked || state.controls.memory_u15 != 32767U) return 1;
    result = mm::applyUiCommand(
        state, actions, locked, prior_memory,
        {mm::UiCommandKind::set_lock, 0, 0, 2U});
    if (!result.controls_changed || locked || state.controls.memory_u15 != prior_memory) return 1;

    static_cast<void>(mm::applyUiCommand(
        state, actions, locked, prior_memory,
        {mm::UiCommandKind::set_draft_timbre, 32767, 0, 3U}));
    if (!state.editor.dirty || state.controls.waypoints[0].lanes[0].timbre_u15 == 32767U) return 1;
    result = mm::applyUiCommand(
        state, actions, locked, prior_memory,
        {mm::UiCommandKind::capture, 0, 0, 4U});
    if (!result.captured || state.controls.waypoints[0].lanes[0].timbre_u15 != 32767U) return 1;

    static_cast<void>(mm::applyUiCommand(
        state, actions, locked, prior_memory,
        {mm::UiCommandKind::panic, 0, 0, 5U}));
    if (actions.panic != 1U) return 1;
    static_cast<void>(mm::applyUiCommand(
        state, actions, locked, prior_memory,
        {mm::UiCommandKind::reseed, 0, 0, 0x1234U}));
    if (actions.reseed != 1U || actions.reseed_value != 0x1234U) return 1;

    mm::Snapshot snapshot{};
    snapshot.accepted_controls = state.controls;
    const auto global = mm::formatGlobalStatus(snapshot);
    const auto editor = mm::formatEditorStatus(state.editor);
    if (global.find("BPM") == std::string::npos
        || editor.find("Waypoint A") == std::string::npos) return 1;
    const auto top = mm::launchControlTopLabels();
    const auto bottom = mm::launchControlBottomLabels();
    if (top.front() != "TEMPO" || top.back() != "DENSITY"
        || bottom.front() != "INTERVAL" || bottom.back() != "ROOT") return 1;
    std::cout << "Murmur Map UI model tests passed\n";
    return 0;
}
