#include "layerwell/source_adapters.hpp"

#include "schuss/pamplist/activity_model.hpp"
#include "schuss/pamplist/control_map.hpp"
#include "schuss/pamplist/ui_model.hpp"
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

namespace pam = schuss::pamplist;

constexpr double kQ27ToFloat = 1.0 / 134217728.0;
constexpr std::uint32_t kPamplistActivityPeriodFrames = 2400U;

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
            return static_cast<std::uint8_t>(((note - 36) * 127 + 18) / 36);
        }
        default:
            return 0U;
    }
}

std::uint8_t surfaceValueToMidi(const pam::SurfaceSlot& slot) noexcept {
    if (!slot.enabled || !std::isfinite(slot.value)
        || !std::isfinite(slot.minimum) || !std::isfinite(slot.maximum)
        || slot.maximum <= slot.minimum) {
        return 0U;
    }
    const auto normalized = std::clamp(
        (slot.value - slot.minimum) / (slot.maximum - slot.minimum), 0.0, 1.0);
    return static_cast<std::uint8_t>(std::clamp(
        static_cast<int>(std::lround(normalized * 127.0)), 0, 127));
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

SourceControlStatus pamStatus(pam::MappingStatus status) noexcept {
    switch (status) {
        case pam::MappingStatus::accepted_continuous:
        case pam::MappingStatus::accepted_press:
            return SourceControlStatus::accepted;
        case pam::MappingStatus::accepted_release:
        case pam::MappingStatus::accepted_hold:
            return SourceControlStatus::accepted_release;
        case pam::MappingStatus::accepted_noop:
            return SourceControlStatus::unassigned;
        default:
            return SourceControlStatus::invalid;
    }
}

constexpr std::array<std::string_view, 8> kPamplistButtonLabels{{
    "LANE 1", "LANE 2", "LANE 3", "LANE 4",
    "LANE 5", "LANE 6", "LANE 7", "GLOBAL / CLEAR",
}};

constexpr std::array<std::string_view, 16> kPamplistFallbackEncoderLabels{{
    "TOP 1", "TOP 2", "TOP 3", "TOP 4", "TOP 5", "TOP 6", "TOP 7", "TOP 8",
    "BOTTOM 1", "BOTTOM 2", "BOTTOM 3", "BOTTOM 4",
    "BOTTOM 5", "BOTTOM 6", "BOTTOM 7", "BOTTOM 8",
}};

}  // namespace

struct SourceRack::Impl final {
    tidepit::Core tide{};
    pam::Core pamplist{};
    pam::Controls pamplist_controls{pam::defaultControls()};
    pam::ControllerAdapter pamplist_controller{};
    pam::ActivityReducer pamplist_activity_reducer{};
    std::array<pam::ActivitySample, kPamplistImpactHistorySamples>
        pamplist_activity_history{};
    std::array<tidepit::SemanticEvent, kMaximumEvents> tide_pending{};
    std::array<float, kTideScopeSamples> tide_scope_left{};
    std::array<float, kTideScopeSamples> tide_scope_right{};
    std::size_t tide_pending_count{};
    std::size_t tide_scope_write{};
    std::size_t tide_scope_count{};
    std::size_t pamplist_activity_write{};
    std::size_t pamplist_activity_count{};
    std::uint64_t tide_scope_generation{};
    std::uint64_t pamplist_activity_generation{};
    std::uint32_t pamplist_activity_frames{};
    double sample_rate{};
    std::uint32_t maximum_block_frames{};
    bool prepared{};

    pam::SurfaceModel pendingPamplistSurface() const noexcept {
        auto snapshot = pamplist.snapshot();
        snapshot.accepted = pamplist_controls;
        return pam::surfaceModel(snapshot);
    }

    void resetPresentation() noexcept {
        tide_scope_left.fill(0.0F);
        tide_scope_right.fill(0.0F);
        pamplist_activity_history.fill(pam::ActivitySample{});
        tide_scope_write = 0U;
        tide_scope_count = 0U;
        pamplist_activity_write = 0U;
        pamplist_activity_count = 0U;
        tide_scope_generation = 0U;
        pamplist_activity_generation = 0U;
        pamplist_activity_frames = 0U;
        pamplist_activity_reducer.reset();
    }

    bool initialize() noexcept {
        prepared = false;
        tide_pending_count = 0U;
        pamplist_controls = pam::defaultControls();
        pamplist_controller.reset();
        resetPresentation();
        if (!tide.prepare(sample_rate, maximum_block_frames)) return false;
        pamplist.reset();
        prepared = true;
        return true;
    }

    SourceControlStatus setTideAbsolute(
        std::size_t slot,
        std::uint8_t value) noexcept {
        const auto mapping = tidepit::mapMidiCc(
            tidepit::launchControlMidiChannel(),
            static_cast<std::uint8_t>(20U + slot), value);
        const auto status = tideStatus(mapping.status);
        if (status != SourceControlStatus::accepted) return status;
        const auto action = tidepit::semanticAction(mapping.id);
        if (!action.has_value()
            || !tide.setControlNormalized(*action, mapping.normalized_value)) {
            return SourceControlStatus::invalid;
        }
        return SourceControlStatus::accepted;
    }

    SourceControlStatus setPamplistAbsolute(
        std::size_t slot,
        std::uint8_t value) noexcept {
        const auto mapping = pam::mapMidiCc(
            pam::launchControlMidiChannel(),
            static_cast<int>(20U + slot),
            value,
            pamplist_controls.selected_page,
            pamplist_controls.lane_control_mode);
        const auto status = pamStatus(mapping.status);
        if (status != SourceControlStatus::accepted) return status;
        return pam::applyMapping(pamplist_controls, mapping)
            ? SourceControlStatus::accepted
            : SourceControlStatus::inactive;
    }

    void pushTideScope(
        const std::int32_t* left,
        const std::int32_t* right,
        std::uint32_t frames) noexcept {
        for (std::uint32_t frame = 0U; frame < frames; ++frame) {
            tide_scope_left[tide_scope_write] = static_cast<float>(
                static_cast<double>(left[frame]) * kQ27ToFloat);
            tide_scope_right[tide_scope_write] = static_cast<float>(
                static_cast<double>(right[frame]) * kQ27ToFloat);
            tide_scope_write = (tide_scope_write + 1U) % kTideScopeSamples;
            tide_scope_count = std::min(tide_scope_count + 1U, kTideScopeSamples);
        }
        ++tide_scope_generation;
    }

    void observePamplistActivity(std::uint32_t frames) noexcept {
        pamplist_activity_frames += frames;
        if (pamplist_activity_frames < kPamplistActivityPeriodFrames) return;
        pamplist_activity_frames %= kPamplistActivityPeriodFrames;
        const auto sample = pamplist_activity_reducer.reduce(pamplist.snapshot());
        pamplist_activity_history[pamplist_activity_write] = sample;
        pamplist_activity_write =
            (pamplist_activity_write + 1U) % kPamplistImpactHistorySamples;
        pamplist_activity_count = std::min(
            pamplist_activity_count + 1U, kPamplistImpactHistorySamples);
        ++pamplist_activity_generation;
    }

    TideScopeSnapshot tideScopeSnapshot() const noexcept {
        TideScopeSnapshot result{};
        result.generation = tide_scope_generation;
        result.sample_count = static_cast<std::uint16_t>(tide_scope_count);
        const auto start = tide_scope_count == kTideScopeSamples
            ? tide_scope_write
            : 0U;
        for (std::size_t index = 0U; index < tide_scope_count; ++index) {
            const auto source = (start + index) % kTideScopeSamples;
            result.left[index] = tide_scope_left[source];
            result.right[index] = tide_scope_right[source];
            result.peak_left = std::max(result.peak_left, std::abs(result.left[index]));
            result.peak_right = std::max(result.peak_right, std::abs(result.right[index]));
        }
        return result;
    }

    PamplistImpactHistorySnapshot pamplistImpactSnapshot() const noexcept {
        PamplistImpactHistorySnapshot result{};
        result.generation = pamplist_activity_generation;
        result.sample_count = static_cast<std::uint8_t>(pamplist_activity_count);
        const auto start = pamplist_activity_count == kPamplistImpactHistorySamples
            ? pamplist_activity_write
            : 0U;
        for (std::size_t index = 0U; index < pamplist_activity_count; ++index) {
            result.samples[index] = pamplist_activity_history[
                (start + index) % kPamplistImpactHistorySamples];
        }
        return result;
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
    std::uint64_t ingress_sequence) noexcept {
    if (!impl_->prepared || slot >= 16U || relative_value > 127U) {
        return SourceControlStatus::invalid;
    }
    std::uint8_t current{};
    if (source == SourceId::tide_pit) {
        current = projection(source).encoder_values[slot];
    } else if (source == SourceId::pamplist) {
        const auto surface = impl_->pendingPamplistSurface();
        current = surfaceValueToMidi(
            slot < 8U ? surface.top[slot] : surface.bottom[slot - 8U]);
    } else {
        return SourceControlStatus::invalid;
    }
    const auto delta = static_cast<int>(relative_value) - 64;
    const auto next = static_cast<std::uint8_t>(std::clamp(
        static_cast<int>(current) + delta, 0, 127));
    return applyAbsoluteEncoder(source, slot, next, ingress_sequence);
}

SourceControlStatus SourceRack::applyAbsoluteEncoder(
    SourceId source,
    std::size_t slot,
    std::uint8_t absolute_value,
    std::uint64_t) noexcept {
    if (!impl_->prepared || slot >= 16U || absolute_value > 127U) {
        return SourceControlStatus::invalid;
    }
    if (source == SourceId::tide_pit) {
        return impl_->setTideAbsolute(slot, absolute_value);
    }
    if (source == SourceId::pamplist) {
        return impl_->setPamplistAbsolute(slot, absolute_value);
    }
    return SourceControlStatus::invalid;
}

SourceControlStatus SourceRack::applySurfaceValue(
    SourceId source,
    std::size_t slot,
    double value,
    std::uint64_t) noexcept {
    if (!impl_->prepared || slot >= 16U || !std::isfinite(value)) {
        return SourceControlStatus::invalid;
    }
    if (source == SourceId::tide_pit) {
        if (value < 0.0 || value > 1.0) return SourceControlStatus::invalid;
        const auto& descriptor = tidepit::encoderDescriptors()[slot];
        if (descriptor.kind == tidepit::ControlKind::unassigned) {
            return SourceControlStatus::unassigned;
        }
        const auto action = tidepit::semanticAction(descriptor.id);
        if (!action.has_value() || !impl_->tide.setControlNormalized(*action, value)) {
            return SourceControlStatus::invalid;
        }
        return SourceControlStatus::accepted;
    }
    if (source == SourceId::pamplist) {
        return pam::applySurfaceValue(
                   impl_->pamplist_controls,
                   slot < 8U ? pam::SurfaceRow::top : pam::SurfaceRow::bottom,
                   slot < 8U ? slot : slot - 8U,
                   value)
            ? SourceControlStatus::accepted
            : SourceControlStatus::inactive;
    }
    return SourceControlStatus::invalid;
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
            static_cast<std::uint8_t>(40U + slot), value);
        const auto status = tideStatus(mapping.status);
        if (status == SourceControlStatus::accepted_release) return status;
        if (status != SourceControlStatus::accepted) return status;
        const auto action = tidepit::semanticAction(mapping.id);
        if (!action.has_value()) return SourceControlStatus::invalid;
        if (impl_->tide_pending_count == impl_->tide_pending.size()) {
            return SourceControlStatus::capacity_exceeded;
        }
        impl_->tide_pending[impl_->tide_pending_count++] = {
            0U, ingress_sequence, *action, 0.0,
        };
        return SourceControlStatus::accepted;
    }
    if (source == SourceId::pamplist) {
        const auto mapping = impl_->pamplist_controller.handleCc(
            impl_->pamplist_controls,
            pam::launchControlMidiChannel(),
            static_cast<int>(40U + slot),
            value);
        return pamStatus(mapping.status);
    }
    return SourceControlStatus::invalid;
}

SourceControlStatus SourceRack::toggleRun(SourceId source) noexcept {
    if (!impl_->prepared || source != SourceId::pamplist) {
        return SourceControlStatus::unassigned;
    }
    impl_->pamplist_controls.running = !impl_->pamplist_controls.running;
    return SourceControlStatus::accepted;
}

SourceControlStatus SourceRack::setContext(
    SourceId source,
    std::uint8_t context) noexcept {
    if (!impl_->prepared || source != SourceId::pamplist || context > 1U) {
        return SourceControlStatus::unassigned;
    }
    if (impl_->pamplist_controls.selected_page >= pam::kLaneCount) {
        return SourceControlStatus::inactive;
    }
    impl_->pamplist_controls.lane_control_mode = context == 0U
        ? pam::LaneControlMode::voice
        : pam::LaneControlMode::motion;
    return SourceControlStatus::accepted;
}

SourceControlStatus SourceRack::clearEffect(SourceId source) noexcept {
    if (!impl_->prepared || source != SourceId::pamplist) {
        return SourceControlStatus::unassigned;
    }
    ++impl_->pamplist_controls.effect_clear_generation;
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
            left_q27, right_q27, frames,
            impl_->tide_pending.data(), impl_->tide_pending_count);
        impl_->tide_pending_count = 0U;
        if (report.events_dropped != 0U) return false;
        impl_->pushTideScope(left_q27, right_q27, frames);
        return true;
    }
    if (source == SourceId::pamplist) {
        pam::ProcessReport report{};
        const auto ok = impl_->pamplist.process(
            impl_->pamplist_controls,
            left_q27,
            right_q27,
            frames,
            &report);
        if (!ok) return false;
        impl_->pamplist_controls = report.snapshot.accepted;
        impl_->observePamplistActivity(frames);
        return true;
    }
    return false;
}

SourceProjection SourceRack::projection(SourceId source) const noexcept {
    SourceProjection result{};
    if (source == SourceId::tide_pit) {
        const auto snapshot = impl_->tide.snapshot();
        result.panel.tide_pit = snapshot;
        result.panel.tide_scope = impl_->tideScopeSnapshot();
        result.processed_frames = snapshot.absolute_sample;
        const auto& encoders = tidepit::encoderDescriptors();
        for (std::size_t slot = 0U; slot < encoders.size(); ++slot) {
            result.encoder_assigned[slot] =
                encoders[slot].kind != tidepit::ControlKind::unassigned;
            result.encoder_values[slot] = result.encoder_assigned[slot]
                ? tideAcceptedValue(encoders[slot].id, snapshot)
                : 0U;
            result.encoder_labels[slot] = encoders[slot].label;
            result.encoder_tooltips[slot] = encoders[slot].timing;
        }
        const auto& buttons = tidepit::buttonDescriptors();
        for (std::size_t slot = 0U; slot < buttons.size(); ++slot) {
            result.button_assigned[slot] =
                buttons[slot].kind != tidepit::ControlKind::unassigned;
            result.button_labels[slot] = buttons[slot].label;
        }
        result.button_active[2] = snapshot.locked;
        result.button_active[3] = snapshot.captured;
        return result;
    }
    if (source == SourceId::pamplist) {
        const auto snapshot = impl_->pamplist.snapshot();
        const auto surface = pam::surfaceModel(snapshot);
        result.panel.pamplist = snapshot;
        result.panel.pamplist_impact = impl_->pamplistImpactSnapshot();
        result.processed_frames = snapshot.absolute_frame;
        for (std::size_t slot = 0U; slot < 16U; ++slot) {
            const auto& model = slot < 8U
                ? surface.top[slot]
                : surface.bottom[slot - 8U];
            result.encoder_assigned[slot] = model.enabled;
            result.encoder_values[slot] = surfaceValueToMidi(model);
            result.encoder_labels[slot] = model.label;
            result.encoder_tooltips[slot] = model.tooltip;
        }
        for (std::size_t slot = 0U; slot < 8U; ++slot) {
            result.button_assigned[slot] = true;
            result.button_active[slot] = snapshot.accepted.selected_page == slot;
            result.button_labels[slot] = kPamplistButtonLabels[slot];
        }
        return result;
    }
    return result;
}

std::string_view sourceEncoderLabel(SourceId source, std::size_t slot) noexcept {
    if (slot >= 16U) return "INVALID";
    return source == SourceId::tide_pit
        ? tidepit::encoderDescriptors()[slot].label
        : kPamplistFallbackEncoderLabels[slot];
}

std::string_view sourceButtonLabel(SourceId source, std::size_t slot) noexcept {
    if (slot >= 8U) return "INVALID";
    return source == SourceId::tide_pit
        ? tidepit::buttonDescriptors()[slot].label
        : kPamplistButtonLabels[slot];
}

}  // namespace layerwell
