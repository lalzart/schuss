#include "schuss/murmur_map/control_map.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace schuss::murmur_map {
namespace {

constexpr std::array<EncoderDescriptor, 16> kEncoders{{
    {ControlId::tempo, 20U, "TEMPO", "tempo_milli_bpm", 30000, 240000},
    {ControlId::travel, 21U, "TRAVEL", "travel_milli_quarters", 250, 8000},
    {ControlId::memory, 22U, "MEMORY", "memory_u15", 0, 32767},
    {ControlId::length, 23U, "LENGTH", "memory_length", 2, 32},
    {ControlId::roam, 24U, "ROAM", "roam_u15", 0, 32767},
    {ControlId::home, 25U, "HOME", "home_u15", 0, 32767},
    {ControlId::radius, 26U, "RADIUS", "radius_u15", 0, 32767},
    {ControlId::density, 27U, "DENSITY", "density_u15", 0, 32767},
    {ControlId::draft_interval, 28U, "INTERVAL", "draft_lane.interval_semitones", -24, 24},
    {ControlId::draft_activity, 29U, "ACTIVITY", "draft_lane.activity_u15", 0, 32767},
    {ControlId::draft_timbre, 30U, "TIMBRE", "draft_lane.timbre_u15", 0, 32767},
    {ControlId::draft_color, 31U, "COLOR", "draft_lane.color_u15", 0, 32767},
    {ControlId::draft_decay, 32U, "DECAY", "draft_lane.decay_ms", 40, 4000},
    {ControlId::draft_level, 33U, "LEVEL", "draft_lane.level_milli_db", -60000, -6000},
    {ControlId::draft_pan, 34U, "PAN", "draft_lane.pan_s15", -32767, 32767},
    {ControlId::root, 35U, "ROOT", "root_midi_note", 24, 84},
}};

constexpr std::array<ButtonDescriptor, 8> kButtons{{
    {ControlId::select_waypoint_a, 40U, "WAYPOINT A", "editor.selected_waypoint=A"},
    {ControlId::select_waypoint_b, 41U, "WAYPOINT B", "editor.selected_waypoint=B"},
    {ControlId::select_waypoint_c, 42U, "WAYPOINT C", "editor.selected_waypoint=C"},
    {ControlId::select_waypoint_d, 43U, "WAYPOINT D", "editor.selected_waypoint=D"},
    {ControlId::select_anchor, 44U, "ANCHOR", "editor.selected_lane=anchor"},
    {ControlId::select_thread, 45U, "THREAD", "editor.selected_lane=thread"},
    {ControlId::select_spark, 46U, "SPARK", "editor.selected_lane=spark"},
    {ControlId::capture_replace, 47U, "CAPTURE", "capture_replace"},
}};

[[nodiscard]] bool validLaneValue(Lane lane) noexcept {
    return static_cast<std::size_t>(lane) < kLaneCount;
}

[[nodiscard]] std::int32_t roundHalfUp(
    std::uint8_t value,
    std::int32_t span,
    std::int32_t offset = 0) noexcept {
    return offset + static_cast<std::int32_t>(
        (static_cast<std::int64_t>(value) * span + 63) / 127);
}

[[nodiscard]] std::int32_t mapEncoder(ControlId id, std::uint8_t value) noexcept {
    switch (id) {
        case ControlId::tempo: return roundHalfUp(value, 210000, 30000);
        case ControlId::travel:
            return static_cast<std::int32_t>(std::lround(
                250.0 * std::pow(32.0, static_cast<double>(value) / 127.0)));
        case ControlId::memory:
        case ControlId::roam:
        case ControlId::home:
        case ControlId::radius:
        case ControlId::density:
        case ControlId::draft_activity:
        case ControlId::draft_timbre:
        case ControlId::draft_color:
            return roundHalfUp(value, 32767);
        case ControlId::length: return roundHalfUp(value, 30, 2);
        case ControlId::draft_interval: return roundHalfUp(value, 48, -24);
        case ControlId::draft_decay:
            return static_cast<std::int32_t>(std::lround(
                40.0 * std::pow(100.0, static_cast<double>(value) / 127.0)));
        case ControlId::draft_level: return roundHalfUp(value, 54000, -60000);
        case ControlId::draft_pan: return roundHalfUp(value, 65534, -32767);
        case ControlId::root: return roundHalfUp(value, 60, 24);
        default: return 0;
    }
}

[[nodiscard]] bool setIfDifferent(std::uint32_t& destination, std::uint32_t value) noexcept {
    if (destination == value) return false;
    destination = value;
    return true;
}

[[nodiscard]] bool setIfDifferent(std::uint16_t& destination, std::uint16_t value) noexcept {
    if (destination == value) return false;
    destination = value;
    return true;
}

[[nodiscard]] bool setIfDifferent(std::uint8_t& destination, std::uint8_t value) noexcept {
    if (destination == value) return false;
    destination = value;
    return true;
}

[[nodiscard]] bool setIfDifferent(std::int16_t& destination, std::int16_t value) noexcept {
    if (destination == value) return false;
    destination = value;
    return true;
}

[[nodiscard]] bool setIfDifferent(std::int32_t& destination, std::int32_t value) noexcept {
    if (destination == value) return false;
    destination = value;
    return true;
}

}  // namespace

ControllerState defaultControllerState() noexcept {
    ControllerState state{};
    state.controls = defaultControls();
    reloadDraft(state);
    return state;
}

const std::array<EncoderDescriptor, 16>& encoderDescriptors() noexcept { return kEncoders; }
const std::array<ButtonDescriptor, 8>& buttonDescriptors() noexcept { return kButtons; }

const EncoderDescriptor* encoderDescriptor(std::uint8_t cc) noexcept {
    const auto found = std::find_if(
        kEncoders.begin(), kEncoders.end(),
        [cc](const EncoderDescriptor& descriptor) { return descriptor.cc == cc; });
    return found == kEncoders.end() ? nullptr : &*found;
}

const ButtonDescriptor* buttonDescriptor(std::uint8_t cc) noexcept {
    const auto found = std::find_if(
        kButtons.begin(), kButtons.end(),
        [cc](const ButtonDescriptor& descriptor) { return descriptor.cc == cc; });
    return found == kButtons.end() ? nullptr : &*found;
}

std::uint8_t launchControlMidiChannel() noexcept { return 16U; }

std::string_view controlMapSha256() noexcept {
    return "b4bfd6692895f35dadf78ac3acf478552b074cbbe9972b8315a3d1158f9a9b15";
}

std::string_view controllerTopologySha256() noexcept {
    return "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b";
}

MappingResult mapMidiCc(
    std::uint8_t one_based_channel,
    std::uint8_t cc,
    std::uint8_t value) noexcept {
    MappingResult result{};
    result.midi_value = value;
    if (one_based_channel != launchControlMidiChannel()) {
        result.status = MappingStatus::ignored_channel;
        return result;
    }
    if (value > 127U) {
        result.status = MappingStatus::invalid_value;
        return result;
    }
    if (const auto* descriptor = encoderDescriptor(cc)) {
        result.id = descriptor->id;
        result.mapped_value = mapEncoder(descriptor->id, value);
        result.status = MappingStatus::accepted_continuous;
        return result;
    }
    if (const auto* descriptor = buttonDescriptor(cc)) {
        result.id = descriptor->id;
        if (value == 127U) {
            result.status = MappingStatus::accepted_action_press;
            result.mapped_value = 1;
        } else if (value == 0U) {
            result.status = MappingStatus::accepted_action_release;
        } else {
            result.status = MappingStatus::invalid_value;
        }
        return result;
    }
    result.status = MappingStatus::unknown_controller;
    return result;
}

void reloadDraft(ControllerState& state) noexcept {
    if (state.controls.waypoint_count == 0U) return;
    if (state.editor.selected_waypoint >= state.controls.waypoint_count) {
        state.editor.selected_waypoint = 0U;
    }
    if (!validLaneValue(state.editor.selected_lane)) state.editor.selected_lane = Lane::anchor;
    const auto& waypoint = state.controls.waypoints[state.editor.selected_waypoint];
    state.editor.draft_x_u15 = waypoint.x_u15;
    state.editor.draft_y_u15 = waypoint.y_u15;
    state.editor.draft_lane = waypoint.lanes[static_cast<std::size_t>(state.editor.selected_lane)];
    state.editor.dirty = false;
}

ApplyResult selectWaypoint(ControllerState& state, std::uint8_t waypoint_index) noexcept {
    if (waypoint_index >= state.controls.waypoint_count) return {};
    ApplyResult result{true, false, false, false};
    if (waypoint_index == state.editor.selected_waypoint) return result;
    if (state.editor.dirty) ++state.editor.draft_discard_count;
    state.editor.selected_waypoint = waypoint_index;
    reloadDraft(state);
    result.draft_changed = true;
    return result;
}

ApplyResult selectLane(ControllerState& state, Lane lane) noexcept {
    if (!validLaneValue(lane)) return {};
    ApplyResult result{true, false, false, false};
    if (lane == state.editor.selected_lane) return result;
    if (state.editor.dirty) ++state.editor.draft_discard_count;
    state.editor.selected_lane = lane;
    reloadDraft(state);
    result.draft_changed = true;
    return result;
}

ApplyResult setDraftPosition(
    ControllerState& state,
    std::uint16_t x_u15,
    std::uint16_t y_u15) noexcept {
    if (x_u15 > 32767U || y_u15 > 32767U) return {};
    const bool x_changed = setIfDifferent(state.editor.draft_x_u15, x_u15);
    const bool y_changed = setIfDifferent(state.editor.draft_y_u15, y_u15);
    const bool changed = x_changed || y_changed;
    state.editor.dirty = state.editor.dirty || changed;
    return ApplyResult{true, false, changed, false};
}

ApplyResult captureDraft(ControllerState& state) noexcept {
    ApplyResult result{true, false, false, false};
    if (!state.editor.dirty) {
        ++state.editor.empty_capture_count;
        return result;
    }
    if (state.editor.selected_waypoint >= state.controls.waypoint_count
        || !validLaneValue(state.editor.selected_lane)
        || state.editor.draft_x_u15 > 32767U
        || state.editor.draft_y_u15 > 32767U) {
        ++state.editor.rejected_capture_count;
        return result;
    }
    auto next = state.controls;
    auto& waypoint = next.waypoints[state.editor.selected_waypoint];
    waypoint.x_u15 = state.editor.draft_x_u15;
    waypoint.y_u15 = state.editor.draft_y_u15;
    waypoint.lanes[static_cast<std::size_t>(state.editor.selected_lane)] = state.editor.draft_lane;
    if (!validControls(next)) {
        ++state.editor.rejected_capture_count;
        return result;
    }
    state.controls = next;
    state.editor.dirty = false;
    ++state.editor.capture_count;
    result.controls_changed = true;
    result.draft_changed = true;
    result.captured = true;
    return result;
}

ApplyResult applyMapping(ControllerState& state, const MappingResult& mapping) noexcept {
    if (!mapping.dispatchesSemantic()) {
        return ApplyResult{mapping.status == MappingStatus::accepted_action_release, false, false, false};
    }
    if (mapping.status == MappingStatus::accepted_action_press) {
        switch (mapping.id) {
            case ControlId::select_waypoint_a: return selectWaypoint(state, 0U);
            case ControlId::select_waypoint_b: return selectWaypoint(state, 1U);
            case ControlId::select_waypoint_c: return selectWaypoint(state, 2U);
            case ControlId::select_waypoint_d: return selectWaypoint(state, 3U);
            case ControlId::select_anchor: return selectLane(state, Lane::anchor);
            case ControlId::select_thread: return selectLane(state, Lane::thread);
            case ControlId::select_spark: return selectLane(state, Lane::spark);
            case ControlId::capture_replace: return captureDraft(state);
            default: return {};
        }
    }
    ApplyResult result{true, false, false, false};
    bool changed = false;
    switch (mapping.id) {
        case ControlId::tempo:
            if (mapping.mapped_value < 30000 || mapping.mapped_value > 240000) return {};
            changed = setIfDifferent(state.controls.tempo_milli_bpm, static_cast<std::uint32_t>(mapping.mapped_value));
            result.controls_changed = changed;
            break;
        case ControlId::travel:
            if (mapping.mapped_value < 250 || mapping.mapped_value > 8000) return {};
            changed = setIfDifferent(state.controls.travel_milli_quarters, static_cast<std::uint32_t>(mapping.mapped_value));
            result.controls_changed = changed;
            break;
        case ControlId::memory:
        case ControlId::roam:
        case ControlId::home:
        case ControlId::radius:
        case ControlId::density: {
            if (mapping.mapped_value < 0 || mapping.mapped_value > 32767) return {};
            auto* destination = mapping.id == ControlId::memory ? &state.controls.memory_u15
                : mapping.id == ControlId::roam ? &state.controls.roam_u15
                : mapping.id == ControlId::home ? &state.controls.home_u15
                : mapping.id == ControlId::radius ? &state.controls.radius_u15
                : &state.controls.density_u15;
            changed = setIfDifferent(*destination, static_cast<std::uint16_t>(mapping.mapped_value));
            result.controls_changed = changed;
            break;
        }
        case ControlId::length:
            if (mapping.mapped_value < 2 || mapping.mapped_value > 32) return {};
            changed = setIfDifferent(state.controls.memory_length, static_cast<std::uint8_t>(mapping.mapped_value));
            result.controls_changed = changed;
            break;
        case ControlId::root:
            if (mapping.mapped_value < 24 || mapping.mapped_value > 84) return {};
            changed = setIfDifferent(state.controls.root_midi_note, static_cast<std::uint8_t>(mapping.mapped_value));
            result.controls_changed = changed;
            break;
        case ControlId::draft_interval:
            if (mapping.mapped_value < -24 || mapping.mapped_value > 24) return {};
            changed = setIfDifferent(state.editor.draft_lane.interval_semitones, static_cast<std::int16_t>(mapping.mapped_value));
            result.draft_changed = changed;
            break;
        case ControlId::draft_activity:
        case ControlId::draft_timbre:
        case ControlId::draft_color: {
            if (mapping.mapped_value < 0 || mapping.mapped_value > 32767) return {};
            auto* destination = mapping.id == ControlId::draft_activity
                ? &state.editor.draft_lane.activity_u15
                : mapping.id == ControlId::draft_timbre
                    ? &state.editor.draft_lane.timbre_u15
                    : &state.editor.draft_lane.color_u15;
            changed = setIfDifferent(*destination, static_cast<std::uint16_t>(mapping.mapped_value));
            result.draft_changed = changed;
            break;
        }
        case ControlId::draft_decay:
            if (mapping.mapped_value < 40 || mapping.mapped_value > 4000) return {};
            changed = setIfDifferent(state.editor.draft_lane.decay_ms, static_cast<std::uint16_t>(mapping.mapped_value));
            result.draft_changed = changed;
            break;
        case ControlId::draft_level:
            if (mapping.mapped_value < -60000 || mapping.mapped_value > -6000) return {};
            changed = setIfDifferent(state.editor.draft_lane.level_milli_db, mapping.mapped_value);
            result.draft_changed = changed;
            break;
        case ControlId::draft_pan:
            if (mapping.mapped_value < -32767 || mapping.mapped_value > 32767) return {};
            changed = setIfDifferent(state.editor.draft_lane.pan_s15, static_cast<std::int16_t>(mapping.mapped_value));
            result.draft_changed = changed;
            break;
        default: return {};
    }
    state.editor.dirty = state.editor.dirty || result.draft_changed;
    return result;
}

}  // namespace schuss::murmur_map
