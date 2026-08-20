#include "cinderwheel/juce_midi_adapter.hpp"

#include <algorithm>
#include <limits>

namespace cinderwheel {

void JuceMidiAdapter::reset() noexcept {
    ingress_sequence_ = 0;
}

AdaptedMidiBlock JuceMidiAdapter::adapt(
    const juce::MidiBuffer& source,
    std::uint32_t block_frames,
    Core& core
) noexcept {
    std::size_t event_count = 0;
    std::size_t dropped_events = 0;
    const auto maximum_sample_position = block_frames > 0
        ? static_cast<int>(block_frames - 1U)
        : 0;

    for (const auto metadata : source) {
        const auto sequence = ++ingress_sequence_;
        if (event_count == events_.size()) {
            ++dropped_events;
            continue;
        }

        auto& destination = events_[event_count++];
        destination = {};
        destination.sample_offset = static_cast<std::uint32_t>(
            std::clamp(metadata.samplePosition, 0, maximum_sample_position)
        );
        destination.ingress_sequence = sequence;

        const auto byte_count = metadata.numBytes > 0
            ? static_cast<std::size_t>(metadata.numBytes)
            : 0U;
        const auto copied_bytes = std::min(destination.bytes.size(), byte_count);
        if (metadata.data != nullptr) {
            std::copy_n(metadata.data, copied_bytes, destination.bytes.begin());
        }
        destination.size = byte_count <= std::numeric_limits<std::uint8_t>::max()
            ? static_cast<std::uint8_t>(byte_count)
            : 0U;
    }

    core.noteDroppedMidiEvents(dropped_events);
    return {events_.data(), event_count, dropped_events};
}

}  // namespace cinderwheel
