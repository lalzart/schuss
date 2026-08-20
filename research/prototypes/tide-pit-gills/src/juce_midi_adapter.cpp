#include "tidepit/juce_midi_adapter.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>

namespace tidepit {

namespace {

constexpr double kQ27ToFloat = 1.0 / 134217728.0;

}  // namespace

void Q27HostBridge::reset() noexcept {
    quantum_read_ = kReferenceQuantumFrames;
    pending_head_ = 0;
    pending_count_ = 0;
    callback_origin_ = 0;
    generated_frames_ = 0;
    dropped_events_ = 0;
}

void Q27HostBridge::process(
    Core& core,
    float* output_left,
    float* output_right,
    std::uint32_t frames,
    const SemanticEvent* events,
    std::size_t event_count
) noexcept {
    if (output_left == nullptr || output_right == nullptr || frames == 0) {
        dropped_events_ += event_count;
        return;
    }
    enqueue(events, event_count);
    for (std::uint32_t frame = 0; frame < frames; ++frame) {
        if (quantum_read_ == kReferenceQuantumFrames) renderNextQuantum(core);
        output_left[frame] = static_cast<float>(
            static_cast<double>(quantum_left_[quantum_read_]) * kQ27ToFloat
        );
        output_right[frame] = static_cast<float>(
            static_cast<double>(quantum_right_[quantum_read_]) * kQ27ToFloat
        );
        ++quantum_read_;
    }
    callback_origin_ += frames;
}

std::uint64_t Q27HostBridge::droppedEvents() const noexcept {
    return dropped_events_;
}

void Q27HostBridge::enqueue(const SemanticEvent* events, std::size_t count) noexcept {
    if (events == nullptr) {
        if (count != 0) dropped_events_ += count;
        return;
    }
    for (std::size_t index = 0; index < count; ++index) {
        if (pending_count_ == pending_.size()) {
            ++dropped_events_;
            continue;
        }
        const auto write = (pending_head_ + pending_count_) % pending_.size();
        pending_[write] = {
            callback_origin_ + events[index].sample_offset,
            events[index].ingress_sequence,
            events[index].action,
            events[index].value,
        };
        ++pending_count_;
    }
}

const Q27HostBridge::PendingEvent& Q27HostBridge::pendingFront() const noexcept {
    return pending_[pending_head_];
}

void Q27HostBridge::popPending() noexcept {
    pending_head_ = (pending_head_ + 1U) % pending_.size();
    --pending_count_;
}

void Q27HostBridge::renderNextQuantum(Core& core) noexcept {
    std::array<SemanticEvent, kMaximumSemanticEvents> quantum_events{};
    std::size_t event_count = 0;
    const auto quantum_end = generated_frames_ + kReferenceQuantumFrames;
    while (pending_count_ != 0 && pendingFront().absolute_sample < quantum_end) {
        const auto event = pendingFront();
        popPending();
        if (event_count == quantum_events.size()) {
            ++dropped_events_;
            continue;
        }
        const auto offset = event.absolute_sample <= generated_frames_
            ? 0U
            : static_cast<std::uint32_t>(event.absolute_sample - generated_frames_);
        quantum_events[event_count++] = {
            offset,
            event.ingress_sequence,
            event.action,
            event.value,
        };
    }
    const auto report = core.processQ27(
        quantum_left_.data(),
        quantum_right_.data(),
        kReferenceQuantumFrames,
        quantum_events.data(),
        event_count
    );
    dropped_events_ += report.events_dropped;
    generated_frames_ += kReferenceQuantumFrames;
    quantum_read_ = 0;
}

void JuceMidiAdapter::reset() noexcept {
    ingress_sequence_.reset();
    events_.clear();
    diagnostics_ = {};
}

AdaptedMidiBlock JuceMidiAdapter::adapt(
    const juce::MidiBuffer& source,
    std::uint32_t block_frames
) noexcept {
    events_.clear();

    for (const auto metadata : source) {
        const auto sequence = ingress_sequence_.next();
        ++diagnostics_.raw_messages;
        if (metadata.data == nullptr || metadata.numBytes != 3) {
            ++diagnostics_.malformed_messages;
            continue;
        }

        const auto status = metadata.data[0];
        const auto controller = metadata.data[1];
        const auto value = metadata.data[2];
        if ((status & 0xf0U) != 0xb0U || controller > 127U || value > 127U) {
            ++diagnostics_.malformed_messages;
            continue;
        }

        const auto channel = static_cast<std::uint8_t>((status & 0x0fU) + 1U);
        const auto mapping = mapMidiCc(channel, controller, value);
        switch (mapping.status) {
            case MappingStatus::ignored_channel:
                ++diagnostics_.ignored_channels;
                continue;
            case MappingStatus::unassigned:
                ++diagnostics_.unassigned_controllers;
                continue;
            case MappingStatus::unknown_controller:
                ++diagnostics_.unknown_controllers;
                continue;
            case MappingStatus::invalid_value:
                ++diagnostics_.invalid_values;
                continue;
            case MappingStatus::accepted_action_release:
                ++diagnostics_.accepted_messages;
                ++diagnostics_.action_releases;
                diagnostics_.last_accepted_channel = channel;
                diagnostics_.last_accepted_cc = controller;
                diagnostics_.last_accepted_value = value;
                continue;
            case MappingStatus::accepted_continuous:
            case MappingStatus::accepted_action_press:
                break;
        }

        ++diagnostics_.accepted_messages;
        diagnostics_.last_accepted_channel = channel;
        diagnostics_.last_accepted_cc = controller;
        diagnostics_.last_accepted_value = value;
        const auto action = semanticAction(mapping.id);
        if (!action.has_value()) {
            ++diagnostics_.invalid_values;
            continue;
        }
        const auto semantic_value = mapping.status == MappingStatus::accepted_action_press
            ? 0.0
            : (mapping.id == ControlId::set_root
                   ? static_cast<double>(mapping.root_note)
                   : mapping.normalized_value);
        const SemanticEvent event{
            schuss::instrument_lab::clampSampleOffset(
                metadata.samplePosition, block_frames),
            sequence,
            *action,
            semantic_value,
        };
        if (!events_.push(event)) {
            ++diagnostics_.dropped_events;
            continue;
        }
        ++diagnostics_.semantic_events;
    }
    return {events_.data(), events_.size(), events_.dropped()};
}

MidiAdapterDiagnostics JuceMidiAdapter::diagnostics() const noexcept {
    return diagnostics_;
}

}  // namespace tidepit
