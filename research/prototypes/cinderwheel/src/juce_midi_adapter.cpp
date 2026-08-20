#include "cinderwheel/juce_midi_adapter.hpp"

namespace cinderwheel {

void JuceMidiAdapter::reset() noexcept {
    ingress_sequence_.reset();
    events_.clear();
}

AdaptedMidiBlock JuceMidiAdapter::adapt(
    const juce::MidiBuffer& source,
    std::uint32_t block_frames,
    Core& core
) noexcept {
    events_.clear();

    for (const auto metadata : source) {
        const auto envelope = schuss::instrument_lab::makeRawMidiEnvelope(
            metadata.data,
            metadata.numBytes,
            metadata.samplePosition,
            block_frames,
            ingress_sequence_.next());
        MidiEvent destination{};
        destination.sample_offset = envelope.sample_offset;
        destination.ingress_sequence = envelope.ingress_sequence;
        destination.bytes = envelope.bytes;
        destination.size = envelope.size;
        static_cast<void>(events_.push(destination));
    }

    core.noteDroppedMidiEvents(events_.dropped());
    return {events_.data(), events_.size(), events_.dropped()};
}

}  // namespace cinderwheel
