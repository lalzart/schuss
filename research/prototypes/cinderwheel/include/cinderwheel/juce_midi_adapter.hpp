#pragma once

#include "cinderwheel/core.hpp"

#include <juce_audio_basics/juce_audio_basics.h>

#include <array>
#include <cstddef>
#include <cstdint>

namespace cinderwheel {

struct AdaptedMidiBlock {
    const MidiEvent* events{};
    std::size_t event_count{};
    std::size_t dropped_events{};
};

// Converts one JUCE MIDI block into the Core's bounded, allocation-free event
// representation. The adapter deliberately leaves message interpretation to
// Core so wrong channels, unsupported statuses, and unassigned controls remain
// observable diagnostics rather than disappearing at the host boundary.
class JuceMidiAdapter final {
public:
    void reset() noexcept;

    [[nodiscard]] AdaptedMidiBlock adapt(
        const juce::MidiBuffer& source,
        std::uint32_t block_frames,
        Core& core
    ) noexcept;

private:
    std::array<MidiEvent, kMaximumMidiEventsPerBlock> events_{};
    std::uint64_t ingress_sequence_{};
};

}  // namespace cinderwheel
