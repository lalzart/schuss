#include "layerwell/launch_control_3.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <string_view>

namespace layerwell {
namespace {

constexpr std::uint8_t kCcMode = 30U;
constexpr std::uint8_t kCcShift = 63U;
constexpr std::uint8_t kCcRelativeTop = 69U;
constexpr std::uint8_t kCcRelativeBottom = 72U;
constexpr std::uint8_t kCcTrackRight = 102U;
constexpr std::uint8_t kCcTrackLeft = 103U;
constexpr std::uint8_t kCcPageUp = 106U;
constexpr std::uint8_t kCcPageDown = 107U;
constexpr std::uint8_t kEncoderRelativeFirst = 77U;
constexpr std::uint8_t kEncoderRelativeLast = 92U;
constexpr std::uint8_t kEncoderAbsoluteFirst = 13U;
constexpr std::uint8_t kButtonFirst = 37U;
constexpr std::uint8_t kButtonLast = 44U;
constexpr std::uint8_t kDisplayStationary = 53U;
constexpr std::uint8_t kDisplayOverlay = 54U;

constexpr std::array<std::uint8_t, 9> kEnableDaw{{
    0xF0U, 0x00U, 0x20U, 0x29U, 0x02U, 0x16U, 0x02U, 0x7FU, 0xF7U}};
constexpr std::array<std::uint8_t, 9> kDisableDaw{{
    0xF0U, 0x00U, 0x20U, 0x29U, 0x02U, 0x16U, 0x02U, 0x00U, 0xF7U}};

bool isPress(std::uint8_t value) noexcept { return value == 127U; }
bool isRelease(std::uint8_t value) noexcept { return value == 0U; }

std::uint8_t normalizedMidi(float value) noexcept {
    if (!std::isfinite(value)) return 0U;
    return static_cast<std::uint8_t>(std::clamp(
        static_cast<int>(std::lround(value * 127.0f)), 0, 127));
}

std::uint8_t panMidi(float pan) noexcept {
    if (!std::isfinite(pan)) return 64U;
    return static_cast<std::uint8_t>(std::clamp(
        static_cast<int>(std::lround((pan + 1.0f) * 63.5f)), 0, 127));
}

void pushCc(
    MidiBatch& batch,
    std::uint8_t status,
    std::uint8_t controller,
    std::uint8_t value) noexcept {
    const std::array<std::uint8_t, 3> bytes{{status, controller, value}};
    batch.push(bytes.data(), bytes.size());
}

void pushRgb(
    MidiBatch& batch,
    std::uint8_t control,
    std::uint8_t red,
    std::uint8_t green,
    std::uint8_t blue) noexcept {
    const std::array<std::uint8_t, 13> bytes{{
        0xF0U, 0x00U, 0x20U, 0x29U, 0x02U, 0x16U, 0x01U, 0x53U,
        control,
        static_cast<std::uint8_t>(std::min<unsigned>(red, 127U)),
        static_cast<std::uint8_t>(std::min<unsigned>(green, 127U)),
        static_cast<std::uint8_t>(std::min<unsigned>(blue, 127U)),
        0xF7U,
    }};
    batch.push(bytes.data(), bytes.size());
}

void pushDisplayConfig(
    MidiBatch& batch,
    std::uint8_t target,
    std::uint8_t arrangement) noexcept {
    const std::array<std::uint8_t, 10> bytes{{
        0xF0U, 0x00U, 0x20U, 0x29U, 0x02U, 0x16U, 0x04U,
        target, arrangement, 0xF7U,
    }};
    batch.push(bytes.data(), bytes.size());
}

void pushDisplayText(
    MidiBatch& batch,
    std::uint8_t target,
    std::uint8_t field,
    std::string_view text) noexcept {
    MidiMessage message{};
    constexpr std::array<std::uint8_t, 7> prefix{{
        0xF0U, 0x00U, 0x20U, 0x29U, 0x02U, 0x16U, 0x06U}};
    std::copy(prefix.begin(), prefix.end(), message.bytes.begin());
    message.bytes[7] = target;
    message.bytes[8] = field;
    std::size_t size = 9U;
    for (const auto character : text) {
        if (size + 1U >= message.bytes.size()) break;
        const auto value = static_cast<unsigned char>(character);
        message.bytes[size++] = value >= 32U && value <= 126U
            ? static_cast<std::uint8_t>(value)
            : static_cast<std::uint8_t>('?');
    }
    message.bytes[size++] = 0xF7U;
    batch.push(message.bytes.data(), size);
}

void encoderValuesForSnapshot(
    const Snapshot& snapshot,
    std::array<std::uint8_t, 16>& values,
    std::array<bool, 16>& assigned) noexcept {
    if (snapshot.surface_mode == SurfaceMode::control) {
        values = snapshot.source_encoder_values;
        assigned = snapshot.source_encoder_assigned;
        return;
    }

    values.fill(0U);
    assigned.fill(false);
    for (std::size_t layer = 0U; layer < kLayerCount; ++layer) {
        values[layer] = panMidi(snapshot.layers[layer].pan);
        assigned[layer] = true;
        values[8U + layer] = normalizedMidi(snapshot.layers[layer].level);
        assigned[8U + layer] = true;
    }
    values[3] = normalizedMidi(snapshot.monitor_level);
    assigned[3] = true;
    values[11] = normalizedMidi(snapshot.master_level);
    assigned[11] = true;
}

void addStateSync(MidiBatch& batch, const Snapshot& snapshot) noexcept {
    pushCc(batch, dawFeatureStatus(), kCcMode,
        snapshot.surface_mode == SurfaceMode::mixer ? 1U : 2U);

    std::array<std::uint8_t, 16> values{};
    std::array<bool, 16> assigned{};
    encoderValuesForSnapshot(snapshot, values, assigned);
    for (std::size_t slot = 0U; slot < values.size(); ++slot) {
        const auto control = static_cast<std::uint8_t>(kEncoderAbsoluteFirst + slot);
        pushCc(batch, dawEnableStatus(), control, values[slot]);
        if (assigned[slot]) {
            const bool top = slot < 8U;
            pushRgb(batch, control,
                top ? 10U : 52U,
                top ? 48U : 18U,
                top ? 62U : 58U);
        } else {
            pushRgb(batch, control, 0U, 0U, 0U);
        }
    }

    for (std::size_t slot = 0U; slot < 8U; ++slot) {
        const auto control = static_cast<std::uint8_t>(kButtonFirst + slot);
        if (snapshot.surface_mode == SurfaceMode::control) {
            if (!snapshot.source_button_assigned[slot]) {
                pushRgb(batch, control, 0U, 0U, 0U);
            } else if (snapshot.source_button_active[slot]) {
                pushRgb(batch, control, 20U, 70U, 45U);
            } else {
                pushRgb(batch, control, 8U, 22U, 28U);
            }
            continue;
        }

        if (slot < 3U) {
            const bool selected = snapshot.selected_layer == slot;
            pushRgb(batch, control,
                selected ? 18U : 4U,
                selected ? 62U : 18U,
                selected ? 54U : 20U);
        } else if (slot < 6U) {
            const auto layer = slot - 3U;
            const bool muted = snapshot.layers[layer].muted;
            pushRgb(batch, control,
                muted ? 64U : 12U,
                muted ? 10U : 30U,
                muted ? 8U : 22U);
        } else if (slot == 6U) {
            if (snapshot.capture_state == CaptureState::recording) {
                pushRgb(batch, control, 76U, 4U, 3U);
            } else if (snapshot.capture_state == CaptureState::waiting_boundary) {
                pushRgb(batch, control, 72U, 35U, 2U);
            } else {
                pushRgb(batch, control, 10U, 36U, 18U);
            }
        } else {
            pushRgb(batch, control,
                snapshot.monitor_enabled ? 8U : 3U,
                snapshot.monitor_enabled ? 48U : 8U,
                snapshot.monitor_enabled ? 58U : 10U);
        }
    }

    pushRgb(batch, kCcPageUp, 6U, 24U, 42U);
    pushRgb(batch, kCcPageDown, 6U, 24U, 42U);
    pushRgb(batch, kCcTrackLeft, 10U, 34U, 30U);
    pushRgb(batch, kCcTrackRight, 10U, 34U, 30U);

    pushDisplayConfig(batch, kDisplayStationary, 2U);
    pushDisplayText(batch, kDisplayStationary, 0U, "LAYERWELL");
    pushDisplayText(batch, kDisplayStationary, 1U, sourceName(snapshot.selected_source));
    std::array<char, 40> detail{};
    std::snprintf(detail.data(), detail.size(), "L%u %s %u/%u",
        static_cast<unsigned>(snapshot.selected_layer + 1U),
        captureStateName(snapshot.capture_state),
        snapshot.phase_frames,
        snapshot.loop_length_frames);
    pushDisplayText(batch, kDisplayStationary, 2U, detail.data());
}

}  // namespace

void MidiBatch::clear() noexcept {
    count = 0U;
    dropped = 0U;
}

bool MidiBatch::push(const std::uint8_t* bytes, std::size_t size) noexcept {
    if (bytes == nullptr || size == 0U || size > kMaximumMidiMessageBytes
        || count == messages.size()) {
        ++dropped;
        return false;
    }
    auto& message = messages[count++];
    message = MidiMessage{};
    std::copy_n(bytes, size, message.bytes.begin());
    message.size = static_cast<std::uint8_t>(size);
    return true;
}

void LaunchControl3Adapter::reset() noexcept {
    mode_ = SurfaceMode::mixer;
    shift_held_ = false;
    diagnostics_ = ControllerDiagnostics{};
}

MidiParseResult LaunchControl3Adapter::parse(
    const std::uint8_t* bytes,
    std::size_t size,
    std::uint32_t sample_offset,
    std::uint64_t ingress_sequence) noexcept {
    ++diagnostics_.raw_messages;
    MidiParseResult result{};
    if (bytes == nullptr || size != 3U
        || (bytes[0] & 0xF0U) != 0xB0U
        || bytes[1] > 127U
        || bytes[2] > 127U) {
        ++diagnostics_.invalid_messages;
        return result;
    }

    const auto channel = static_cast<std::uint8_t>((bytes[0] & 0x0FU) + 1U);
    const auto cc = bytes[1];
    const auto value = bytes[2];
    diagnostics_.last_channel = channel;
    diagnostics_.last_cc = cc;
    diagnostics_.last_value = value;

    auto emit = [&](EventKind kind, std::uint8_t index = 0U,
                    double event_value = 0.0) noexcept {
        result.event = {sample_offset, ingress_sequence, kind, index, event_value};
        result.status = MidiParseStatus::accepted_event;
        result.has_event = true;
        ++diagnostics_.accepted_events;
        return result;
    };
    auto stateOnly = [&]() noexcept {
        result.status = MidiParseStatus::accepted_state_only;
        ++diagnostics_.accepted_state_only;
        return result;
    };
    auto release = [&]() noexcept {
        result.status = MidiParseStatus::accepted_release;
        ++diagnostics_.accepted_releases;
        return result;
    };
    auto invalid = [&]() noexcept {
        result.status = MidiParseStatus::invalid_message;
        ++diagnostics_.invalid_messages;
        return result;
    };

    if (channel == 7U) {
        if (cc == kCcShift) {
            if (!isPress(value) && !isRelease(value)) return invalid();
            shift_held_ = isPress(value);
            return stateOnly();
        }
        if (cc == kCcMode) {
            if (value == 1U) mode_ = SurfaceMode::mixer;
            else if (value == 2U) mode_ = SurfaceMode::control;
            else return invalid();
            return emit(EventKind::set_surface_mode,
                mode_ == SurfaceMode::mixer ? 0U : 1U);
        }
        result.status = MidiParseStatus::unknown_controller;
        ++diagnostics_.unknown_controls;
        return result;
    }

    if (channel == 16U) {
        if (cc < kEncoderRelativeFirst || cc > kEncoderRelativeLast) {
            result.status = MidiParseStatus::unknown_controller;
            ++diagnostics_.unknown_controls;
            return result;
        }
        const auto slot = static_cast<std::uint8_t>(cc - kEncoderRelativeFirst);
        if (mode_ == SurfaceMode::control) {
            return emit(EventKind::source_encoder_relative, slot, value);
        }
        if (slot < 3U) return emit(EventKind::adjust_layer_pan, slot, value);
        if (slot == 3U) return emit(EventKind::adjust_monitor_level, 0U, value);
        if (slot >= 8U && slot < 11U) {
            return emit(EventKind::adjust_layer_level,
                static_cast<std::uint8_t>(slot - 8U), value);
        }
        if (slot == 11U) return emit(EventKind::adjust_master_level, 0U, value);
        result.status = MidiParseStatus::unassigned;
        ++diagnostics_.unassigned_controls;
        return result;
    }

    if (channel != 1U) {
        result.status = MidiParseStatus::ignored_channel;
        ++diagnostics_.ignored_channels;
        return result;
    }

    if (cc == kCcPageUp || cc == kCcPageDown
        || cc == kCcTrackLeft || cc == kCcTrackRight) {
        if (isRelease(value)) return release();
        if (!isPress(value)) return invalid();
        if (cc == kCcPageUp) return emit(EventKind::source_previous);
        if (cc == kCcPageDown) return emit(EventKind::source_next);
        if (cc == kCcTrackLeft) return emit(EventKind::layer_previous);
        return emit(EventKind::layer_next);
    }

    if (cc < kButtonFirst || cc > kButtonLast) {
        result.status = MidiParseStatus::unknown_controller;
        ++diagnostics_.unknown_controls;
        return result;
    }
    const auto slot = static_cast<std::uint8_t>(cc - kButtonFirst);
    if (mode_ == SurfaceMode::control) {
        if (!isPress(value) && !isRelease(value)) return invalid();
        return emit(EventKind::source_button, slot, value);
    }
    if (isRelease(value)) return release();
    if (!isPress(value)) return invalid();
    if (slot < 3U) return emit(EventKind::select_layer, slot);
    if (slot < 6U) {
        return emit(EventKind::toggle_layer_mute,
            static_cast<std::uint8_t>(slot - 3U));
    }
    if (slot == 6U) return emit(EventKind::capture_press);
    if (shift_held_) return emit(EventKind::clear_selected_layer);
    return emit(EventKind::toggle_monitor);
}

MidiBatch LaunchControl3Adapter::connectionMessages(const Snapshot& snapshot) noexcept {
    mode_ = snapshot.surface_mode;
    MidiBatch batch{};
    batch.push(kEnableDaw.data(), kEnableDaw.size());
    pushCc(batch, dawFeatureStatus(), kCcRelativeTop, 127U);
    pushCc(batch, dawFeatureStatus(), kCcRelativeBottom, 127U);
    addStateSync(batch, snapshot);
    accountFeedback(batch);
    return batch;
}

MidiBatch LaunchControl3Adapter::stateSyncMessages(const Snapshot& snapshot) noexcept {
    mode_ = snapshot.surface_mode;
    MidiBatch batch{};
    addStateSync(batch, snapshot);
    accountFeedback(batch);
    return batch;
}

MidiBatch LaunchControl3Adapter::parameterOverlayMessages(
    std::string_view name,
    std::string_view value) noexcept {
    MidiBatch batch{};
    pushDisplayConfig(batch, kDisplayOverlay, 1U);
    pushDisplayText(batch, kDisplayOverlay, 0U, name);
    pushDisplayText(batch, kDisplayOverlay, 1U, value);
    accountFeedback(batch);
    return batch;
}

MidiBatch LaunchControl3Adapter::endpointChangeCleanupMessages() noexcept {
    return shutdownMessages();
}

MidiBatch LaunchControl3Adapter::shutdownMessages() noexcept {
    MidiBatch batch{};
    batch.push(kDisableDaw.data(), kDisableDaw.size());
    accountFeedback(batch);
    shift_held_ = false;
    return batch;
}

SurfaceMode LaunchControl3Adapter::mode() const noexcept { return mode_; }
bool LaunchControl3Adapter::shiftHeld() const noexcept { return shift_held_; }

ControllerDiagnostics LaunchControl3Adapter::diagnostics() const noexcept {
    return diagnostics_;
}

void LaunchControl3Adapter::accountFeedback(const MidiBatch& batch) noexcept {
    diagnostics_.feedback_messages += batch.count;
    diagnostics_.feedback_dropped += batch.dropped;
}

}  // namespace layerwell
