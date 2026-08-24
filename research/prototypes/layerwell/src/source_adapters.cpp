#include "layerwell/source_adapters.hpp"

#include "schuss/generative_drum_machine/control_map.hpp"
#include "schuss/generative_drum_machine/core.hpp"
#include "tidepit/control_map.hpp"
#include "tidepit/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace layerwell {
namespace {

namespace drums = schuss::generative_drum_machine;

std::uint8_t normalizedToMidi(double value) noexcept {
    if (!std::isfinite(value)) return 0U;
    return static_cast<std::uint8_t>(std::clamp(
        static_cast<int>(std::lround(value * 127.0)), 0, 127));
}

std::uint8_t tideAcceptedValue(
    tidepit::ControlId id,
    const tidepit::Snapshot& snapshot) noexcept {
    switch (id) {
        case tidepit::ControlId::set_stage_1:
            return normalizedToMidi(snapshot.controls.stages[0]);
        case tidepit::ControlId::set_stage_2:
            return normalizedToMidi(snapshot.controls.stages[1]);
        case tidepit::ControlId::set_stage_3:
            return normalizedToMidi(snapshot.controls.stages[2]);
        case tidepit::ControlId::set_stage_4:
            return normalizedToMidi(snapshot.controls.stages[3]);
        case tidepit::ControlId::set_rate:
            return normalizedToMidi(snapshot.controls.rate);
        case tidepit::ControlId::set_memory:
            return normalizedToMidi(snapshot.controls.memory);
        case tidepit::ControlId::set_material:
            return normalizedToMidi(snapshot.controls.material);
        case tidepit::ControlId::set_position:
            return normalizedToMidi(snapshot.controls.position);
        case tidepit::ControlId::set_fx_a:
            return normalizedToMidi(snapshot.controls.fx_a);
        case tidepit::ControlId::set_fx_b:
            return normalizedToMidi(snapshot.controls.fx_b);
        case tidepit::ControlId::set_root: {
            const auto note = std::clamp(snapshot.controls.root_note, 36, 72);
            return static_cast<std::uint8_t>(
                ((note - 36) * 127 + 18) / 36);
        }
        default:
            return 0U;
    }
}

std::uint32_t drumAcceptedValue(
    drums::ControlId id,
    const drums::Controls& controls) noexcept {
    switch (id) {
        case drums::ControlId::complexity_kick: return controls.complexity[0];
        case drums::ControlId::complexity_snare: return controls.complexity[1];
        case drums::ControlId::complexity_hat: return controls.complexity[2];
        case drums::ControlId::complexity_percussion_1: return controls.complexity[3];
        case drums::ControlId::complexity_percussion_2: return controls.complexity[4];
        case drums::ControlId::complexity_percussion_3: return controls.complexity[5];
        case drums::ControlId::enthusiasm: return controls.enthusiasm;
        case drums::ControlId::tempo_milli_bpm: return controls.tempo_milli_bpm;
        case drums::ControlId::swing_u15: return controls.swing_u15;
        case drums::ControlId::rhythm_select: return controls.rhythm_preset;
        case drums::ControlId::shape_tune:
        case drums::ControlId::shape_timbre:
        case drums::ControlId::shape_color:
        case drums::ControlId::shape_decay:
        case drums::ControlId::shape_pitch_env:
        case drums::ControlId::shape_level: {
            const auto lane = std::min<std::size_t>(
                controls.selected_voice_lane,
                controls.voice_shapes.size() - 1U);
            const auto& shape = controls.voice_shapes[lane];
            switch (id) {
                case drums::ControlId::shape_tune: return shape.tune_u7;
                case drums::ControlId::shape_timbre: return shape.timbre_u7;
                case drums::ControlId::shape_color: return shape.color_u7;
                case drums::ControlId::shape_decay: return shape.decay_u7;
                case drums::ControlId::shape_pitch_env: return shape.pitch_env_u7;
                case drums::ControlId::shape_level: return shape.level_u7;
                default: return 0U;
            }
        }
        default:
            return 0U;
    }
}

std::uint8_t drumMidiForAccepted(
    const drums::EncoderDescriptor& descriptor,
    const drums::Controls& controls) noexcept {
    const auto target = drumAcceptedValue(descriptor.id, controls);
    std::uint8_t best = 0U;
    auto best_distance = std::numeric_limits<std::uint32_t>::max();
    for (std::uint16_t raw = 0U; raw <= 127U; ++raw) {
        const auto mapping = drums::mapMidiCc(
            drums::launchControlMidiChannel(),
            descriptor.cc,
            static_cast<std::uint8_t>(raw));
        if (mapping.status != drums::MappingStatus::accepted_continuous) continue;
        const auto distance = mapping.mapped_value > target
            ? mapping.mapped_value - target
            : target - mapping.mapped_value;
        if (distance < best_distance) {
            best_distance = distance;
            best = static_cast<std::uint8_t>(raw);
        }
    }
    return best;
}

SourceControlStatus tideStatus(tidepit::MappingStatus status) noexcept {
    switch (status) {
        case tidepit::MappingStatus::accepted_continuous:
        case tidepit::MappingStatus::accepted_action_press:
            return SourceControlStatus::accepted;
        case tidepit::MappingStatus::accepted_action_release:
            return SourceControlStatus::accepted_release;
        case tidepit::MappingStatus::unassigned:
            return SourceControlStatus::unassigned;
        default:
            return SourceControlStatus::invalid;
    }
}

SourceControlStatus drumStatus(drums::MappingStatus status) noexcept {
    switch (status) {
        case drums::MappingStatus::accepted_continuous:
        case drums::MappingStatus::accepted_action_press:
            return SourceControlStatus::accepted;
        case drums::MappingStatus::accepted_action_release:
            return SourceControlStatus::accepted_release;
        case drums::MappingStatus::unassigned:
            return SourceControlStatus::unassigned;
        case drums::MappingStatus::inactive_mode:
            return SourceControlStatus::inactive;
        default:
            return SourceControlStatus::invalid;
    }
}

}  // namespace

struct SourceRack::Impl final {
    tidepit::Core tide{};
    std::unique_ptr<drums::StreamingEngine> drums_engine{};
    drums::Controls drum_controls{drums::desktopAuditionControls()};
    std::array<tidepit::SemanticEvent, kMaximumEvents> tide_pending{};
    std::size_t tide_pending_count{};
    std::uint64_t fill_sequence{};
    double sample_rate{};
    std::uint32_t maximum_block_frames{};
    bool prepared{};

    bool initialize() noexcept {
        prepared = false;
        drums_engine.reset();
        tide_pending_count = 0U;
        fill_sequence = 0U;
        drum_controls = drums::desktopAuditionControls();
        if (!tide.prepare(sample_rate, maximum_block_frames)) {
            return false;
        }
        // Layerwell's parent build privately prefixes Tide Pit's Mutable
        // namespaces because the two exact source closures otherwise export
        // colliding braids/stmlib symbols. Construction remains stopped-host
        // work; neither source bytes nor either public Core contract changes.
        try {
            drums_engine = std::make_unique<drums::StreamingEngine>(
                kDeterministicSeed);
        } catch (...) {
            drums_engine.reset();
            return false;
        }
        prepared = true;
        return true;
    }
};

SourceRack::SourceRack() : impl_(std::make_unique<Impl>()) {}
SourceRack::~SourceRack() = default;
SourceRack::SourceRack(SourceRack&&) noexcept = default;
SourceRack& SourceRack::operator=(SourceRack&&) noexcept = default;

bool SourceRack::prepare(
    double sample_rate,
    std::uint32_t maximum_block_frames) noexcept {
    if (sample_rate != kSampleRate
        || maximum_block_frames == 0U
        || maximum_block_frames > kMaximumBlockFrames
        || maximum_block_frames % kSourceQuantumFrames != 0U) {
        impl_->prepared = false;
        return false;
    }
    impl_->sample_rate = sample_rate;
    impl_->maximum_block_frames = maximum_block_frames;
    return impl_->initialize();
}

bool SourceRack::reset() noexcept {
    return impl_->sample_rate == kSampleRate
        && impl_->maximum_block_frames != 0U
        && impl_->initialize();
}

SourceControlStatus SourceRack::applyRelativeEncoder(
    SourceId source,
    std::size_t slot,
    std::uint8_t relative_value,
    std::uint64_t) noexcept {
    if (!impl_->prepared || slot >= 16U || relative_value > 127U) {
        return SourceControlStatus::invalid;
    }
    const auto current = projection(source).encoder_values[slot];
    const auto delta = static_cast<int>(relative_value) - 64;
    const auto next = static_cast<std::uint8_t>(std::clamp(
        static_cast<int>(current) + delta, 0, 127));

    if (source == SourceId::tide_pit) {
        const auto mapping = tidepit::mapMidiCc(
            tidepit::launchControlMidiChannel(),
            static_cast<std::uint8_t>(20U + slot),
            next);
        const auto status = tideStatus(mapping.status);
        if (status != SourceControlStatus::accepted) return status;
        const auto action = tidepit::semanticAction(mapping.id);
        if (!action.has_value()
            || !impl_->tide.setControlNormalized(*action, mapping.normalized_value)) {
            return SourceControlStatus::invalid;
        }
        return SourceControlStatus::accepted;
    }

    const auto mapping = drums::mapMidiCc(
        drums::launchControlMidiChannel(),
        static_cast<std::uint8_t>(20U + slot),
        next);
    const auto status = drumStatus(mapping.status);
    if (status != SourceControlStatus::accepted) return status;
    bool fill_queued = false;
    if (!drums::applyMapping(impl_->drum_controls, fill_queued, mapping)) {
        return SourceControlStatus::inactive;
    }
    if (fill_queued) ++impl_->fill_sequence;
    return SourceControlStatus::accepted;
}

SourceControlStatus SourceRack::applyButton(
    SourceId source,
    std::size_t slot,
    std::uint8_t value,
    std::uint64_t ingress_sequence) noexcept {
    if (!impl_->prepared || slot >= 8U || value > 127U) {
        return SourceControlStatus::invalid;
    }

    if (source == SourceId::tide_pit) {
        const auto mapping = tidepit::mapMidiCc(
            tidepit::launchControlMidiChannel(),
            static_cast<std::uint8_t>(40U + slot),
            value);
        const auto status = tideStatus(mapping.status);
        if (status != SourceControlStatus::accepted) return status;
        const auto action = tidepit::semanticAction(mapping.id);
        if (!action.has_value()) return SourceControlStatus::invalid;
        if (impl_->tide_pending_count == impl_->tide_pending.size()) {
            return SourceControlStatus::capacity_exceeded;
        }
        impl_->tide_pending[impl_->tide_pending_count++] = {
            0U,
            ingress_sequence,
            *action,
            0.0,
        };
        return SourceControlStatus::accepted;
    }

    const auto mapping = drums::mapMidiCc(
        drums::launchControlMidiChannel(),
        static_cast<std::uint8_t>(40U + slot),
        value);
    const auto status = drumStatus(mapping.status);
    if (status != SourceControlStatus::accepted) return status;
    bool fill_queued = false;
    if (!drums::applyMapping(impl_->drum_controls, fill_queued, mapping)) {
        return SourceControlStatus::invalid;
    }
    if (fill_queued) ++impl_->fill_sequence;
    return SourceControlStatus::accepted;
}

bool SourceRack::render(
    SourceId source,
    std::int32_t* left_q27,
    std::int32_t* right_q27,
    std::uint32_t frames) noexcept {
    if (!impl_->prepared
        || left_q27 == nullptr
        || right_q27 == nullptr
        || frames == 0U
        || frames > impl_->maximum_block_frames
        || frames % kSourceQuantumFrames != 0U) {
        return false;
    }

    if (source == SourceId::tide_pit) {
        const auto report = impl_->tide.processQ27(
            left_q27,
            right_q27,
            frames,
            impl_->tide_pending.data(),
            impl_->tide_pending_count);
        impl_->tide_pending_count = 0U;
        return report.events_dropped == 0U;
    }

    drums::StreamingProcessReport report{};
    if (impl_->drums_engine == nullptr) return false;
    return impl_->drums_engine->process(
        impl_->drum_controls,
        impl_->fill_sequence,
        left_q27,
        right_q27,
        frames,
        &report);
}

SourceProjection SourceRack::projection(SourceId source) const noexcept {
    SourceProjection result{};
    if (source == SourceId::tide_pit) {
        const auto snapshot = impl_->tide.snapshot();
        result.processed_frames = snapshot.absolute_sample;
        const auto& encoders = tidepit::encoderDescriptors();
        for (std::size_t slot = 0U; slot < encoders.size(); ++slot) {
            result.encoder_assigned[slot] =
                encoders[slot].kind != tidepit::ControlKind::unassigned;
            result.encoder_values[slot] = result.encoder_assigned[slot]
                ? tideAcceptedValue(encoders[slot].id, snapshot)
                : 0U;
        }
        const auto& buttons = tidepit::buttonDescriptors();
        for (std::size_t slot = 0U; slot < buttons.size(); ++slot) {
            result.button_assigned[slot] =
                buttons[slot].kind != tidepit::ControlKind::unassigned;
        }
        result.button_active[2] = snapshot.locked;
        result.button_active[3] = snapshot.captured;
        return result;
    }

    result.processed_frames = impl_->drums_engine != nullptr
        ? impl_->drums_engine->absoluteFrame()
        : 0U;
    const auto& encoders = drums::encoderDescriptors();
    for (std::size_t slot = 0U; slot < encoders.size(); ++slot) {
        result.encoder_assigned[slot] =
            encoders[slot].kind != drums::ControlKind::unassigned;
        result.encoder_values[slot] = result.encoder_assigned[slot]
            ? drumMidiForAccepted(encoders[slot], impl_->drum_controls)
            : 0U;
    }
    const auto& buttons = drums::buttonDescriptors();
    for (std::size_t slot = 0U; slot < buttons.size(); ++slot) {
        result.button_assigned[slot] =
            buttons[slot].kind != drums::ControlKind::unassigned;
    }
    if (impl_->drum_controls.voice_shaping
        && impl_->drum_controls.selected_voice_lane < 6U) {
        result.button_active[impl_->drum_controls.selected_voice_lane] = true;
    }
    return result;
}

std::string_view sourceEncoderLabel(SourceId source, std::size_t slot) noexcept {
    if (slot >= 16U) return "INVALID";
    return source == SourceId::tide_pit
        ? tidepit::encoderDescriptors()[slot].label
        : drums::encoderDescriptors()[slot].label;
}

std::string_view sourceButtonLabel(SourceId source, std::size_t slot) noexcept {
    if (slot >= 8U) return "INVALID";
    return source == SourceId::tide_pit
        ? tidepit::buttonDescriptors()[slot].label
        : drums::buttonDescriptors()[slot].label;
}

}  // namespace layerwell
