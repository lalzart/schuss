#pragma once

#include "tidepit/control_map.hpp"
#include "tidepit/core.hpp"
#include "schuss/instrument_lab/bounded_midi.hpp"
#include "schuss/instrument_lab/host_bridge.hpp"

#include <juce_audio_basics/juce_audio_basics.h>

#include <array>
#include <cstddef>
#include <cstdint>

namespace tidepit {

struct MidiAdapterDiagnostics {
    std::uint64_t raw_messages{};
    std::uint64_t accepted_messages{};
    std::uint64_t semantic_events{};
    std::uint64_t action_releases{};
    std::uint64_t malformed_messages{};
    std::uint64_t ignored_channels{};
    std::uint64_t unassigned_controllers{};
    std::uint64_t unknown_controllers{};
    std::uint64_t invalid_values{};
    std::uint64_t dropped_events{};
    std::int32_t last_accepted_channel{-1};
    std::int32_t last_accepted_cc{-1};
    std::int32_t last_accepted_value{-1};
};

struct AdaptedMidiBlock {
    const SemanticEvent* events{};
    std::size_t event_count{};
    std::size_t dropped_events{};
};

inline constexpr std::size_t kMaximumPendingHostEvents = 512;

// Converts an arbitrary positive host callback length into the source-exact
// 16-frame planar Q27 Core calls. It retains at most one already-rendered
// quantum of output, so a later callback can still deliver an event that
// quantizes to the next not-yet-rendered source boundary. Event arrays must be
// nondecreasing by sample_offset; JuceMidiAdapter provides this precondition
// because juce::MidiBuffer iteration is timestamp ordered.
class Q27HostBridge final {
public:
    [[nodiscard]] static constexpr schuss::instrument_lab::HostProfile
    profile() noexcept {
        return {
            schuss::instrument_lab::SampleRepresentation::q27,
            kReferenceSampleRate,
            0x7fffffffU,
            kReferenceQuantumFrames,
            true,
            true,
        };
    }

    void reset() noexcept;

    void process(
        Core& core,
        float* output_left,
        float* output_right,
        std::uint32_t frames,
        const SemanticEvent* events = nullptr,
        std::size_t event_count = 0
    ) noexcept;

    [[nodiscard]] std::uint64_t droppedEvents() const noexcept;

private:
    struct PendingEvent {
        std::uint64_t absolute_sample{};
        std::uint64_t ingress_sequence{};
        SemanticAction action{SemanticAction::set_stage_1};
        double value{};
    };

    void enqueue(const SemanticEvent* events, std::size_t count) noexcept;
    void renderNextQuantum(Core& core) noexcept;
    [[nodiscard]] const PendingEvent& pendingFront() const noexcept;
    void popPending() noexcept;

    std::array<std::int32_t, kReferenceQuantumFrames> quantum_left_{};
    std::array<std::int32_t, kReferenceQuantumFrames> quantum_right_{};
    std::array<PendingEvent, kMaximumPendingHostEvents> pending_{};
    std::size_t quantum_read_{kReferenceQuantumFrames};
    std::size_t pending_head_{};
    std::size_t pending_count_{};
    std::uint64_t callback_origin_{};
    std::uint64_t generated_frames_{};
    std::uint64_t dropped_events_{};
};

// Converts JUCE raw MIDI into the bounded semantic event contract. The storage
// is owned by this object and is valid until the next adapt call. No allocation,
// sorting, or Core access occurs in adapt; JUCE's timestamp/iteration order is
// retained and equal timestamps are disambiguated by ingress_sequence.
class JuceMidiAdapter final {
public:
    void reset() noexcept;

    [[nodiscard]] AdaptedMidiBlock adapt(
        const juce::MidiBuffer& source,
        std::uint32_t block_frames
    ) noexcept;

    [[nodiscard]] MidiAdapterDiagnostics diagnostics() const noexcept;

private:
    schuss::instrument_lab::FixedEventBuffer<
        SemanticEvent, kMaximumSemanticEvents> events_{};
    schuss::instrument_lab::IngressSequence ingress_sequence_{};
    MidiAdapterDiagnostics diagnostics_{};
};

using ParameterizedQ27HostBridge =
    schuss::instrument_lab::HostBridge<Q27HostBridge>;

}  // namespace tidepit
