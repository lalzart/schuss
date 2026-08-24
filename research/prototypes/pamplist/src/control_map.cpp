#include "schuss/pamplist/control_map.hpp"

#include <algorithm>

namespace schuss::pamplist {
namespace {

constexpr std::uint8_t kMidiChannel = 16U;

[[nodiscard]] SemanticControl routeSemantic(std::uint8_t index) noexcept {
    return static_cast<SemanticControl>(
        static_cast<std::uint8_t>(SemanticControl::route_trigger) + index);
}

[[nodiscard]] SemanticControl laneSemantic(std::uint8_t index) noexcept {
    return static_cast<SemanticControl>(
        static_cast<std::uint8_t>(SemanticControl::select_lane_1) + index);
}

[[nodiscard]] float signedRoute(std::uint8_t value) noexcept {
    if (value <= 64U) {
        return -static_cast<float>(64U - value) / 64.0F;
    }
    return static_cast<float>(value - 64U) / 63.0F;
}

}  // namespace

bool MappingResult::accepted() const noexcept {
    return status == MappingStatus::accepted_continuous
        || status == MappingStatus::accepted_press
        || status == MappingStatus::accepted_release
        || status == MappingStatus::accepted_hold;
}

bool MappingResult::dispatches() const noexcept {
    return status == MappingStatus::accepted_continuous
        || status == MappingStatus::accepted_press;
}

std::uint8_t launchControlMidiChannel() noexcept { return kMidiChannel; }

std::string_view controlMapSha256() noexcept {
    return "aa8c59a568c16999f72ef362b639c2d3fa24d02ee81ca47e7a7a9f4e2c096263";
}

std::string_view controllerTopologySha256() noexcept {
    return "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b";
}

MappingResult mapMidiCc(
    int one_based_channel,
    int cc,
    int value) noexcept {
    MappingResult result{};
    if (one_based_channel != kMidiChannel) {
        result.status = MappingStatus::ignored_channel;
        return result;
    }
    if (cc < 0 || cc > 127 || value < 0 || value > 127) {
        result.status = MappingStatus::invalid_message;
        return result;
    }
    result.cc = static_cast<std::uint8_t>(cc);
    result.value = static_cast<std::uint8_t>(value);

    if (cc >= 20 && cc <= 27) {
        const auto destination = static_cast<std::uint8_t>(cc - 20);
        result.status = MappingStatus::accepted_continuous;
        result.semantic = routeSemantic(destination);
        result.discrete_value = destination;
        result.continuous_value = signedRoute(result.value);
        return result;
    }
    if (cc >= 28 && cc <= 35) {
        result.status = MappingStatus::accepted_continuous;
        result.semantic = static_cast<SemanticControl>(
            static_cast<std::uint8_t>(SemanticControl::rate)
            + static_cast<std::uint8_t>(cc - 28));
        switch (cc) {
            case 28:
                result.discrete_value = static_cast<std::uint8_t>(value * 16 / 128);
                break;
            case 29:
                result.discrete_value = result.value;
                result.continuous_value = static_cast<float>(value) / 128.0F;
                break;
            case 30:
                result.discrete_value = static_cast<std::uint8_t>(value * 8 / 128);
                break;
            case 31:
                result.discrete_value = static_cast<std::uint8_t>(
                    (value * 16 + 63) / 127);
                break;
            case 32:
                result.discrete_value = static_cast<std::uint8_t>(value * 16 / 128);
                break;
            case 33:
                result.continuous_value = static_cast<float>(value) / 127.0F;
                break;
            case 34:
                result.discrete_value = value == 0
                    ? 0U
                    : static_cast<std::uint8_t>(
                        1 + ((value - 1) * 64) / 127);
                break;
            case 35:
                result.continuous_value = static_cast<float>(value) / 127.0F;
                break;
            default:
                break;
        }
        return result;
    }
    if (cc >= 40 && cc <= 47) {
        const auto lane = static_cast<std::uint8_t>(cc - 40);
        result.semantic = laneSemantic(lane);
        result.lane = lane;
        result.status = value == 0
            ? MappingStatus::accepted_release
            : MappingStatus::accepted_press;
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
    const auto first_route = static_cast<std::uint8_t>(SemanticControl::route_trigger);
    const auto last_route = static_cast<std::uint8_t>(SemanticControl::route_level);
    const auto first_lane = static_cast<std::uint8_t>(SemanticControl::select_lane_1);
    const auto last_lane = static_cast<std::uint8_t>(SemanticControl::select_lane_8);
    if (semantic >= first_lane && semantic <= last_lane) {
        controls.selected_lane = static_cast<std::uint8_t>(semantic - first_lane);
        return true;
    }
    if (controls.selected_lane >= kLaneCount) return false;
    auto& lane = controls.lanes[controls.selected_lane];
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

MappingResult ControllerAdapter::handleCc(
    Controls& controls,
    int one_based_channel,
    int cc,
    int value) noexcept {
    auto mapping = mapMidiCc(one_based_channel, cc, value);
    if (mapping.status == MappingStatus::accepted_press
        && mapping.lane < button_down_.size()) {
        if (button_down_[mapping.lane]) {
            mapping.status = MappingStatus::accepted_hold;
        } else {
            button_down_[mapping.lane] = true;
        }
    } else if (mapping.status == MappingStatus::accepted_release
               && mapping.lane < button_down_.size()) {
        button_down_[mapping.lane] = false;
    }

    if (mapping.accepted()) ++diagnostics_.accepted_message_count;
    if (mapping.status == MappingStatus::ignored_channel) {
        ++diagnostics_.ignored_channel_count;
    } else if (mapping.status == MappingStatus::unknown_cc) {
        ++diagnostics_.unknown_cc_count;
    } else if (mapping.status == MappingStatus::invalid_message) {
        ++diagnostics_.invalid_message_count;
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
