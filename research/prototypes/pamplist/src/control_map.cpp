#include "schuss/pamplist/control_map.hpp"

#include <algorithm>

namespace schuss::pamplist {
namespace {

constexpr std::uint8_t kMidiChannel = 16U;

[[nodiscard]] SemanticControl voiceSemantic(std::uint8_t index) noexcept {
    return static_cast<SemanticControl>(
        static_cast<std::uint8_t>(SemanticControl::voice_model) + index);
}

[[nodiscard]] SemanticControl routeSemantic(std::uint8_t index) noexcept {
    return static_cast<SemanticControl>(
        static_cast<std::uint8_t>(SemanticControl::route_trigger) + index);
}

[[nodiscard]] SemanticControl timingSemantic(std::uint8_t index) noexcept {
    return static_cast<SemanticControl>(
        static_cast<std::uint8_t>(SemanticControl::rate) + index);
}

[[nodiscard]] SemanticControl globalEffectSemantic(std::uint8_t index) noexcept {
    return static_cast<SemanticControl>(
        static_cast<std::uint8_t>(SemanticControl::global_drive) + index);
}

[[nodiscard]] SemanticControl pageSemantic(std::uint8_t index) noexcept {
    return static_cast<SemanticControl>(
        static_cast<std::uint8_t>(SemanticControl::select_page_1) + index);
}

[[nodiscard]] float normalized(std::uint8_t value) noexcept {
    return static_cast<float>(value) / 127.0F;
}

[[nodiscard]] float signedRoute(std::uint8_t value) noexcept {
    return std::clamp(
        static_cast<float>(static_cast<int>(value) - 64) / 63.0F,
        -1.0F,
        1.0F);
}

}  // namespace

bool MappingResult::accepted() const noexcept {
    return status == MappingStatus::accepted_continuous
        || status == MappingStatus::accepted_press
        || status == MappingStatus::accepted_release
        || status == MappingStatus::accepted_hold
        || status == MappingStatus::accepted_noop;
}

bool MappingResult::dispatches() const noexcept {
    return status == MappingStatus::accepted_continuous
        || status == MappingStatus::accepted_press;
}

std::uint8_t launchControlMidiChannel() noexcept { return kMidiChannel; }

std::string_view controlMapSha256() noexcept {
    return "1cdc7010eee169caeaf21026ecf448db5317a130a24423578a17d357d35c07cf";
}

std::string_view controllerTopologySha256() noexcept {
    return "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b";
}

MappingResult mapMidiCc(
    int one_based_channel,
    int cc,
    int value,
    std::uint8_t selected_page,
    LaneControlMode lane_control_mode) noexcept {
    MappingResult result{};
    if (one_based_channel != kMidiChannel) {
        result.status = MappingStatus::ignored_channel;
        return result;
    }
    if (cc < 0 || cc > 127 || value < 0 || value > 127
        || selected_page >= kPageCount
        || static_cast<std::uint8_t>(lane_control_mode)
            > static_cast<std::uint8_t>(LaneControlMode::motion)) {
        result.status = MappingStatus::invalid_message;
        return result;
    }
    result.cc = static_cast<std::uint8_t>(cc);
    result.value = static_cast<std::uint8_t>(value);

    if (cc >= 20 && cc <= 27) {
        const auto index = static_cast<std::uint8_t>(cc - 20);
        result.status = MappingStatus::accepted_continuous;
        result.discrete_value = index;
        if (selected_page < kLaneCount) {
            if (lane_control_mode == LaneControlMode::voice) {
                result.semantic = voiceSemantic(index);
                if (index == 0U) {
                    result.discrete_value = static_cast<std::uint8_t>(
                        (value * 23 + 63) / 127);
                    result.integer_value = result.discrete_value;
                } else if (index == 1U) {
                    result.continuous_value = 24.0F
                        + static_cast<float>(value) * 72.0F / 127.0F;
                } else {
                    result.continuous_value = normalized(result.value);
                }
            } else {
                result.semantic = routeSemantic(index);
                result.continuous_value = index == 0U
                    ? (value >= 64 ? 1.0F : 0.0F)
                    : signedRoute(result.value);
            }
        } else {
            result.semantic = globalEffectSemantic(index);
            if (result.semantic == SemanticControl::global_root) {
                result.discrete_value = static_cast<std::uint8_t>(
                    24 + (value * 60 + 63) / 127);
                result.integer_value = result.discrete_value;
            } else {
                result.continuous_value = normalized(result.value);
            }
        }
        return result;
    }

    if (cc >= 28 && cc <= 35) {
        if (selected_page == kGlobalPageIndex) {
            if (cc == 28) {
                result.status = MappingStatus::accepted_continuous;
                result.semantic = SemanticControl::global_bpm;
                result.integer_value = static_cast<std::uint32_t>(
                    20 + (value * 280 + 63) / 127);
            } else if (cc == 29) {
                result.status = MappingStatus::accepted_continuous;
                result.semantic = SemanticControl::global_master;
                result.continuous_value = normalized(result.value);
            } else {
                result.status = MappingStatus::accepted_noop;
                result.semantic = SemanticControl::global_unassigned;
            }
            return result;
        }

        result.status = MappingStatus::accepted_continuous;
        result.semantic = timingSemantic(static_cast<std::uint8_t>(cc - 28));
        switch (cc) {
            case 28:
                result.discrete_value = static_cast<std::uint8_t>(
                    value * 16 / 128);
                break;
            case 29:
                result.discrete_value = result.value;
                result.continuous_value = static_cast<float>(value) / 128.0F;
                break;
            case 30:
                result.discrete_value = static_cast<std::uint8_t>(
                    value * 8 / 128);
                break;
            case 31:
                result.discrete_value = static_cast<std::uint8_t>(
                    (value * 16 + 63) / 127);
                break;
            case 32:
                result.discrete_value = static_cast<std::uint8_t>(
                    value * 16 / 128);
                break;
            case 33:
                result.continuous_value = normalized(result.value);
                break;
            case 34:
                result.discrete_value = value == 0
                    ? 0U
                    : static_cast<std::uint8_t>(
                        1 + ((value - 1) * 64) / 127);
                break;
            case 35:
                result.continuous_value = normalized(result.value);
                break;
            default:
                break;
        }
        return result;
    }

    if (cc >= 40 && cc <= 47) {
        result.page = static_cast<std::uint8_t>(cc - 40);
        result.status = value == 0
            ? MappingStatus::accepted_release
            : MappingStatus::accepted_press;
        if (cc <= 46) {
            result.semantic = result.page == selected_page
                ? SemanticControl::toggle_lane_mode
                : pageSemantic(result.page);
        } else {
            result.semantic = selected_page == kGlobalPageIndex
                ? SemanticControl::clear_fx
                : SemanticControl::select_global;
        }
        return result;
    }

    result.status = MappingStatus::unknown_cc;
    return result;
}

bool applyMapping(
    Controls& controls,
    const MappingResult& mapping) noexcept {
    if (!mapping.dispatches()) return false;

    const auto semantic = static_cast<std::uint8_t>(mapping.semantic);
    const auto first_voice = static_cast<std::uint8_t>(
        SemanticControl::voice_model);
    const auto last_voice = static_cast<std::uint8_t>(
        SemanticControl::voice_level);
    const auto first_route = static_cast<std::uint8_t>(
        SemanticControl::route_trigger);
    const auto last_route = static_cast<std::uint8_t>(
        SemanticControl::route_level);
    const auto first_page = static_cast<std::uint8_t>(
        SemanticControl::select_page_1);
    const auto last_page = static_cast<std::uint8_t>(
        SemanticControl::select_page_7);
    if (semantic >= first_page && semantic <= last_page) {
        controls.selected_page = static_cast<std::uint8_t>(
            semantic - first_page);
        return true;
    }
    if (mapping.semantic == SemanticControl::select_global) {
        controls.selected_page = kGlobalPageIndex;
        return true;
    }
    if (mapping.semantic == SemanticControl::clear_fx) {
        ++controls.effect_clear_generation;
        return true;
    }
    if (mapping.semantic == SemanticControl::toggle_lane_mode
        && controls.selected_page < kLaneCount) {
        controls.lane_control_mode = controls.lane_control_mode
                == LaneControlMode::voice
            ? LaneControlMode::motion
            : LaneControlMode::voice;
        return true;
    }

    if (controls.selected_page < kLaneCount) {
        auto& lane = controls.lanes[controls.selected_page];
        auto& voice = controls.voices[controls.selected_page];
        if (semantic >= first_voice && semantic <= last_voice) {
            switch (mapping.semantic) {
                case SemanticControl::voice_model:
                    voice.engine = mapping.discrete_value;
                    return true;
                case SemanticControl::voice_pitch:
                    voice.note = mapping.continuous_value;
                    return true;
                case SemanticControl::voice_harmonics:
                    voice.harmonics = mapping.continuous_value;
                    return true;
                case SemanticControl::voice_timbre:
                    voice.timbre = mapping.continuous_value;
                    return true;
                case SemanticControl::voice_morph:
                    voice.morph = mapping.continuous_value;
                    return true;
                case SemanticControl::voice_decay:
                    voice.decay = mapping.continuous_value;
                    return true;
                case SemanticControl::voice_colour:
                    voice.lpg_colour = mapping.continuous_value;
                    return true;
                case SemanticControl::voice_level:
                    voice.level = mapping.continuous_value;
                    return true;
                default:
                    return false;
            }
        }
        if (semantic >= first_route && semantic <= last_route) {
            lane.routes[semantic - first_route] = mapping.continuous_value;
            return true;
        }
        switch (mapping.semantic) {
            case SemanticControl::rate:
                lane.rate_index = mapping.discrete_value;
                return true;
            case SemanticControl::phase:
                lane.phase_u7 = mapping.discrete_value;
                return true;
            case SemanticControl::shape:
                lane.shape = static_cast<Shape>(mapping.discrete_value);
                return true;
            case SemanticControl::hits:
                lane.hits = mapping.discrete_value;
                return true;
            case SemanticControl::rotation:
                lane.rotation = mapping.discrete_value;
                return true;
            case SemanticControl::probability:
                lane.probability = mapping.continuous_value;
                return true;
            case SemanticControl::repeat:
                lane.repeat = mapping.discrete_value;
                return true;
            case SemanticControl::amplitude:
                lane.amplitude = mapping.continuous_value;
                return true;
            default:
                return false;
        }
    }

    if (controls.selected_page != kGlobalPageIndex) return false;
    switch (mapping.semantic) {
        case SemanticControl::global_drive:
            controls.cohesion.drive = mapping.continuous_value;
            return true;
        case SemanticControl::global_cohere:
            controls.cohesion.cohere = mapping.continuous_value;
            return true;
        case SemanticControl::global_root:
            controls.cohesion.root_note = static_cast<float>(
                mapping.discrete_value);
            return true;
        case SemanticControl::global_spread:
            controls.cohesion.spread = mapping.continuous_value;
            return true;
        case SemanticControl::global_tail:
            controls.cohesion.tail = mapping.continuous_value;
            return true;
        case SemanticControl::global_damping:
            controls.cohesion.damping = mapping.continuous_value;
            return true;
        case SemanticControl::global_width:
            controls.cohesion.width = mapping.continuous_value;
            return true;
        case SemanticControl::global_duck:
            controls.cohesion.duck = mapping.continuous_value;
            return true;
        case SemanticControl::global_bpm:
            controls.tempo_milli_bpm = mapping.integer_value * 1000U;
            return true;
        case SemanticControl::global_master:
            controls.master_gain = mapping.continuous_value;
            return true;
        default:
            return false;
    }
}

MappingResult ControllerAdapter::handleCc(
    Controls& controls,
    int one_based_channel,
    int cc,
    int value) noexcept {
    auto mapping = mapMidiCc(
        one_based_channel,
        cc,
        value,
        controls.selected_page,
        controls.lane_control_mode);
    if (mapping.status == MappingStatus::accepted_press
        && mapping.page < button_down_.size()) {
        if (button_down_[mapping.page]) {
            mapping.status = MappingStatus::accepted_hold;
        } else {
            button_down_[mapping.page] = true;
        }
    } else if (mapping.status == MappingStatus::accepted_release
               && mapping.page < button_down_.size()) {
        button_down_[mapping.page] = false;
    }

    if (mapping.accepted()) ++diagnostics_.accepted_message_count;
    if (mapping.status == MappingStatus::ignored_channel) {
        ++diagnostics_.ignored_channel_count;
    } else if (mapping.status == MappingStatus::unknown_cc) {
        ++diagnostics_.unknown_cc_count;
    } else if (mapping.status == MappingStatus::invalid_message) {
        ++diagnostics_.invalid_message_count;
    } else if (mapping.status == MappingStatus::accepted_noop) {
        ++diagnostics_.ignored_global_control_count;
    }
    if (applyMapping(controls, mapping)) {
        ++diagnostics_.dispatched_message_count;
    }
    return mapping;
}

void ControllerAdapter::reset() noexcept {
    button_down_.fill(false);
    diagnostics_ = {};
}

const ControllerDiagnostics& ControllerAdapter::diagnostics() const noexcept {
    return diagnostics_;
}

}  // namespace schuss::pamplist
