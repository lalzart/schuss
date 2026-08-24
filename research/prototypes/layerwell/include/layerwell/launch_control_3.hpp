#pragma once

#include "layerwell/core.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace layerwell {

inline constexpr std::size_t kMaximumMidiMessageBytes = 64U;
inline constexpr std::size_t kMaximumFeedbackMessages = 96U;

struct MidiMessage final {
    std::array<std::uint8_t, kMaximumMidiMessageBytes> bytes{};
    std::uint8_t size{};
};

struct MidiBatch final {
    std::array<MidiMessage, kMaximumFeedbackMessages> messages{};
    std::size_t count{};
    std::size_t dropped{};

    void clear() noexcept;
    bool push(const std::uint8_t* bytes, std::size_t size) noexcept;
};

enum class MidiParseStatus : std::uint8_t {
    accepted_event,
    accepted_state_only,
    accepted_release,
    ignored_channel,
    unassigned,
    unknown_controller,
    invalid_message,
};

struct MidiParseResult final {
    Event event{};
    MidiParseStatus status{MidiParseStatus::invalid_message};
    bool has_event{};
};

struct ControllerDiagnostics final {
    std::uint64_t raw_messages{};
    std::uint64_t accepted_events{};
    std::uint64_t accepted_state_only{};
    std::uint64_t accepted_releases{};
    std::uint64_t ignored_channels{};
    std::uint64_t unassigned_controls{};
    std::uint64_t unknown_controls{};
    std::uint64_t invalid_messages{};
    std::uint64_t feedback_messages{};
    std::uint64_t feedback_dropped{};
    std::uint8_t last_channel{};
    std::uint8_t last_cc{};
    std::uint8_t last_value{};
};

// Pure regular Launch Control 3 DAW-mode protocol adapter. It owns gesture and
// presentation mode only; endpoint enumeration and I/O remain host concerns.
class LaunchControl3Adapter final {
public:
    void reset() noexcept;

    [[nodiscard]] MidiParseResult parse(
        const std::uint8_t* bytes,
        std::size_t size,
        std::uint32_t sample_offset,
        std::uint64_t ingress_sequence) noexcept;

    [[nodiscard]] MidiBatch connectionMessages(const Snapshot& snapshot) noexcept;
    [[nodiscard]] MidiBatch stateSyncMessages(const Snapshot& snapshot) noexcept;
    [[nodiscard]] MidiBatch parameterOverlayMessages(
        std::string_view name,
        std::string_view value) noexcept;
    [[nodiscard]] MidiBatch endpointChangeCleanupMessages() noexcept;
    [[nodiscard]] MidiBatch shutdownMessages() noexcept;

    [[nodiscard]] SurfaceMode mode() const noexcept;
    [[nodiscard]] bool shiftHeld() const noexcept;
    [[nodiscard]] ControllerDiagnostics diagnostics() const noexcept;

private:
    SurfaceMode mode_{SurfaceMode::mixer};
    bool shift_held_{};
    ControllerDiagnostics diagnostics_{};

    void accountFeedback(const MidiBatch& batch) noexcept;
};

[[nodiscard]] constexpr std::uint8_t dawEnableStatus() noexcept { return 0xBFU; }
[[nodiscard]] constexpr std::uint8_t dawFeatureStatus() noexcept { return 0xB6U; }
[[nodiscard]] constexpr std::uint8_t dawButtonStatus() noexcept { return 0xB0U; }

}  // namespace layerwell
