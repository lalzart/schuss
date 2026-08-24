#include "layerwell/core.hpp"
#include "layerwell/launch_control_3.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <string>

namespace {

int failures = 0;

void expect(bool condition, const std::string& message) {
    if (condition) return;
    std::cerr << "FAIL: " << message << '\n';
    ++failures;
}

layerwell::MidiParseResult cc(
    layerwell::LaunchControl3Adapter& adapter,
    std::uint8_t status,
    std::uint8_t controller,
    std::uint8_t value,
    std::uint64_t sequence = 1U) {
    const std::array<std::uint8_t, 3> bytes{{status, controller, value}};
    return adapter.parse(bytes.data(), bytes.size(), 0U, sequence);
}

const layerwell::MidiMessage* findCc(
    const layerwell::MidiBatch& batch,
    std::uint8_t status,
    std::uint8_t controller) {
    for (std::size_t index = 0U; index < batch.count; ++index) {
        const auto& message = batch.messages[index];
        if (message.size == 3U
            && message.bytes[0] == status
            && message.bytes[1] == controller) {
            return &message;
        }
    }
    return nullptr;
}

void testInputMap() {
    layerwell::LaunchControl3Adapter adapter;
    auto result = cc(adapter, 0xB0U, 106U, 127U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::source_previous,
        "Page Up selects previous source");
    result = cc(adapter, 0xB0U, 107U, 127U, 2U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::source_next,
        "Page Down selects next source");
    result = cc(adapter, 0xB0U, 103U, 127U, 3U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::layer_previous,
        "Track Left selects previous layer");
    result = cc(adapter, 0xB0U, 102U, 127U, 4U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::layer_next,
        "Track Right selects next layer");

    result = cc(adapter, 0xB6U, 30U, 2U, 5U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::set_surface_mode
            && result.event.index == 1U
            && adapter.mode() == layerwell::SurfaceMode::control,
        "channel-7 mode report selects Control");
    result = cc(adapter, 0xBFU, 77U, 65U, 6U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::source_encoder_relative
            && result.event.index == 0U
            && result.event.value == 65.0,
        "Control top encoder maps to source slot 1");
    result = cc(adapter, 0xB0U, 44U, 127U, 7U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::source_button
            && result.event.index == 7U,
        "Control button 8 maps to source action slot 8");
    result = cc(adapter, 0xB0U, 44U, 0U, 8U);
    expect(result.has_event && result.event.value == 0.0,
        "Control source release remains an explicit source event");

    result = cc(adapter, 0xB6U, 30U, 1U, 9U);
    expect(result.has_event && adapter.mode() == layerwell::SurfaceMode::mixer,
        "mode report selects Mixer");
    result = cc(adapter, 0xBFU, 77U, 63U, 10U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::adjust_layer_pan
            && result.event.index == 0U,
        "Mixer top encoder 1 maps layer 1 pan");
    result = cc(adapter, 0xBFU, 85U, 65U, 11U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::adjust_layer_level
            && result.event.index == 0U,
        "Mixer bottom encoder 1 maps layer 1 level");
    result = cc(adapter, 0xBFU, 92U, 65U, 12U);
    expect(!result.has_event
            && result.status == layerwell::MidiParseStatus::unassigned,
        "unused Mixer encoder remains explicit and dark");
    result = cc(adapter, 0xB0U, 37U, 127U, 13U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::select_layer
            && result.event.index == 0U,
        "Mixer button 1 selects layer 1");
    result = cc(adapter, 0xB0U, 40U, 127U, 14U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::toggle_layer_mute
            && result.event.index == 0U,
        "Mixer button 4 toggles layer 1 mute");
    result = cc(adapter, 0xB0U, 43U, 127U, 15U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::capture_press,
        "Mixer button 7 drives capture");
    result = cc(adapter, 0xB0U, 44U, 127U, 16U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::toggle_monitor,
        "Mixer button 8 toggles monitor without Shift");

    result = cc(adapter, 0xB6U, 63U, 127U, 17U);
    expect(!result.has_event && adapter.shiftHeld(),
        "official channel-7 CC63 Shift press is tracked");
    result = cc(adapter, 0xB0U, 44U, 127U, 18U);
    expect(result.has_event
            && result.event.kind == layerwell::EventKind::clear_selected_layer,
        "Shift plus Mixer button 8 clears selected layer");
    result = cc(adapter, 0xB6U, 63U, 0U, 19U);
    expect(!result.has_event && !adapter.shiftHeld(), "Shift release clears chord state");

    result = cc(adapter, 0xB2U, 77U, 64U, 20U);
    expect(!result.has_event
            && result.status == layerwell::MidiParseStatus::ignored_channel,
        "wrong MIDI channel remains distinct");
    const std::array<std::uint8_t, 2> malformed{{0xB0U, 37U}};
    result = adapter.parse(malformed.data(), malformed.size(), 0U, 21U);
    expect(result.status == layerwell::MidiParseStatus::invalid_message,
        "malformed MIDI is rejected");
}

void testFeedbackAndAcceptedState() {
    layerwell::Core core;
    expect(core.prepare(), "controller feedback Core prepares");
    auto snapshot = core.snapshot();
    layerwell::LaunchControl3Adapter adapter;
    auto connection = adapter.connectionMessages(snapshot);
    expect(connection.dropped == 0U && connection.count > 40U,
        "connection emits bounded complete sync");
    expect(connection.messages[0].size == 9U
            && connection.messages[0].bytes[0] == 0xF0U
            && connection.messages[0].bytes[7] == 0x7FU,
        "connection begins with exact DAW enable SysEx");
    const auto* top_relative = findCc(connection, 0xB6U, 69U);
    const auto* bottom_relative = findCc(connection, 0xB6U, 72U);
    expect(top_relative != nullptr && top_relative->bytes[2] == 127U,
        "connection enables top relative row");
    expect(bottom_relative != nullptr && bottom_relative->bytes[2] == 127U,
        "connection enables bottom relative row");
    expect(findCc(connection, 0xBFU, 13U) != nullptr,
        "accepted encoder position is sent on channel 16");

    auto mode = cc(adapter, 0xB6U, 30U, 2U, 30U);
    std::array<float, 16> left{};
    std::array<float, 16> right{};
    core.process(left.data(), right.data(), 16U, &mode.event, 1U);
    snapshot = core.snapshot();
    const auto accepted_before = snapshot.source_encoder_values[0];
    auto encoder = cc(adapter, 0xBFU, 77U, 65U, 31U);
    auto pre_accept_sync = adapter.stateSyncMessages(snapshot);
    const auto* pre_position = findCc(pre_accept_sync, 0xBFU, 13U);
    expect(pre_position != nullptr && pre_position->bytes[2] == accepted_before,
        "raw encoder input does not change feedback before Core acceptance");
    core.process(left.data(), right.data(), 16U, &encoder.event, 1U);
    const auto accepted_after = core.snapshot();
    auto post_accept_sync = adapter.stateSyncMessages(accepted_after);
    const auto* post_position = findCc(post_accept_sync, 0xBFU, 13U);
    expect(post_position != nullptr
            && post_position->bytes[2] == accepted_before + 1U,
        "feedback follows accepted source state");

    const auto overlay = adapter.parameterOverlayMessages("LEVEL", "45%");
    expect(overlay.count == 3U && overlay.dropped == 0U,
        "parameter overlay is fixed and bounded");
    const auto cleanup = adapter.endpointChangeCleanupMessages();
    expect(cleanup.count == 1U
            && cleanup.messages[0].size == 9U
            && cleanup.messages[0].bytes[7] == 0U,
        "endpoint change emits exact DAW disable cleanup");
    const auto shutdown = adapter.shutdownMessages();
    expect(shutdown.count == 1U && shutdown.messages[0].bytes[7] == 0U,
        "shutdown emits exact DAW disable SysEx");
}

}  // namespace

int main() {
    testInputMap();
    testFeedbackAndAcceptedState();
    if (failures != 0) {
        std::cerr << failures << " controller test(s) failed\n";
        return 1;
    }
    std::cout << "Layerwell controller tests passed\n";
    return 0;
}
