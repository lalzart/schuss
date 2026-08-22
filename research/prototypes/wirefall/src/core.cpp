#include "wirefall/core.hpp"

#include "schuss/instrument_lab/renderer_artifacts.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <limits>
#include <type_traits>

namespace wirefall {
namespace {

constexpr double kPi = 3.14159265358979323846264338327950288;
constexpr std::array<double, 9> kRateTable{{0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0}};
constexpr std::array<double, 5> kShadowRatios{{0.25, 1.0 / 3.0, 0.5, 2.0 / 3.0, 0.75}};
constexpr std::array<std::uint32_t, kFrozenFirTaps> kFrozenFirWords{{
    0x1fbae85dU, 0xb7188f0cU, 0xb82960edU, 0xb890d175U, 0xb816d7d5U,
    0x38f7046aU, 0x39cf93b4U, 0x3a3753faU, 0x3a578cf9U, 0x3a0844f8U,
    0xb9ba77aaU, 0xbade7786U, 0xbb47e36bU, 0xbb7096d2U, 0xbb36a7b2U,
    0x2229e922U, 0x3b8d464dU, 0x3c10512cU, 0x3c3b0556U, 0x3c23c2efU,
    0x3b5ab702U, 0xbc018f6dU, 0xbcaa0f08U, 0xbcf7d55fU, 0xbcfb5157U,
    0xbc8eb55cU, 0x3c370359U, 0x3d5761bbU, 0x3dcd2851U, 0x3e1408d9U,
    0x3e344e48U, 0x3e3ffa51U, 0x3e344e48U, 0x3e1408d9U, 0x3dcd2851U,
    0x3d5761bbU, 0x3c370359U, 0xbc8eb55cU, 0xbcfb5157U, 0xbcf7d55fU,
    0xbcaa0f08U, 0xbc018f6dU, 0x3b5ab702U, 0x3c23c2efU, 0x3c3b0556U,
    0x3c10512cU, 0x3b8d464dU, 0x2229e922U, 0xbb36a7b2U, 0xbb7096d2U,
    0xbb47e36bU, 0xbade7786U, 0xb9ba77aaU, 0x3a0844f8U, 0x3a578cf9U,
    0x3a3753faU, 0x39cf93b4U, 0x38f7046aU, 0xb816d7d5U, 0xb890d175U,
    0xb82960edU, 0xb7188f0cU, 0x1fbae85dU,
}};

float clamp01(double value) noexcept {
    return static_cast<float>(std::clamp(value, 0.0, 1.0));
}

float wordToFloat(std::uint32_t word) noexcept {
    float result{};
    static_assert(sizeof(result) == sizeof(word));
    std::memcpy(&result, &word, sizeof(result));
    return result;
}

double raisedCosine(double unit) noexcept {
    const double bounded = std::clamp(unit, 0.0, 1.0);
    return 0.5 - 0.5 * std::cos(kPi * bounded);
}

float denormalZero(float value) noexcept {
    return std::abs(value) < 1.0e-20f ? 0.0f : value;
}

template <typename T>
void hashPod(schuss::instrument_lab::Sha256& hash, const T& value) noexcept {
    static_assert(std::is_trivially_copyable_v<T>);
    hash.update(reinterpret_cast<const std::uint8_t*>(&value), sizeof(value));
}

void hashBool(schuss::instrument_lab::Sha256& hash, bool value) noexcept {
    const std::uint8_t byte = value ? 1U : 0U;
    hashPod(hash, byte);
}

}  // namespace

void Core::Smoothed::reset(float value) noexcept {
    current = value;
    target = value;
}

void Core::Smoothed::configure(float tau_ms, double sample_rate) noexcept {
    coefficient = static_cast<float>(std::exp(-1.0 / (std::max(0.001, static_cast<double>(tau_ms)) * 0.001 * sample_rate)));
}

float Core::Smoothed::next() noexcept {
    current = coefficient * current + (1.0f - coefficient) * target;
    if (!std::isfinite(current)) current = target;
    return current;
}

void Core::RaisedCosineRamp::reset(float value) noexcept {
    current = value;
    start = value;
    target = value;
    total = 0;
    elapsed = 0;
}

void Core::RaisedCosineRamp::begin(float value, std::uint32_t frames) noexcept {
    start = current;
    target = value;
    total = frames;
    elapsed = 0;
    if (frames == 0) reset(value);
}

float Core::RaisedCosineRamp::next() noexcept {
    if (total == 0 || elapsed >= total) {
        current = target;
        elapsed = total;
        return current;
    }
    const double unit = total > 1U
        ? static_cast<double>(elapsed) / static_cast<double>(total - 1U)
        : 1.0;
    current = static_cast<float>(start + (target - start) * raisedCosine(unit));
    ++elapsed;
    return current;
}

void Core::VoiceSpace::clear() noexcept {
    left.fill(0.0f);
    right.fill(0.0f);
    left_write = 0;
    right_write = 0;
    wet_recovery = 1.0f;
}

void Core::DcBlocker::clear() noexcept {
    input_previous = 0.0f;
    output_previous = 0.0f;
}

float Core::DcBlocker::process(float input, float coefficient) noexcept {
    const float output = input - input_previous + coefficient * output_previous;
    input_previous = input;
    output_previous = denormalZero(output);
    return output_previous;
}

void Core::Automation::clear() noexcept {
    active = false;
    start_sample = 0;
    end_sample = 0;
    start_value = 0.0f;
    end_value = 0.0f;
}

Core::Core() noexcept {
    tension_.configure(25.0f, kSampleRate);
    shadow_.configure(8.0f, kSampleRate);
    root_.configure(15.0f, kSampleRate);
    bite_.configure(10.0f, kSampleRate);
    edge_.configure(10.0f, kSampleRate);
    swing_.configure(10.0f, kSampleRate);
    space_.configure(10.0f, kSampleRate);
    initialize();
}

bool Core::prepare(
    double sample_rate,
    std::uint32_t maximum_block_frames,
    Configuration configuration
) noexcept {
    if (!std::isfinite(sample_rate) || sample_rate != kSampleRate
        || maximum_block_frames == 0 || maximum_block_frames > kMaximumBlockFrames
        || (configuration.wire_oversample_factor != kWireOversampleFactor
            && configuration.wire_oversample_factor != kReferenceOversampleFactor)
        || !std::isfinite(configuration.parallel_shadow_gain)
        || configuration.parallel_shadow_gain < 0.0f) {
        prepared_ = false;
        return false;
    }
    sample_rate_ = sample_rate;
    maximum_block_frames_ = maximum_block_frames;
    configuration_ = configuration;
    tension_.configure(25.0f, sample_rate_);
    shadow_.configure(8.0f, sample_rate_);
    root_.configure(15.0f, sample_rate_);
    bite_.configure(10.0f, sample_rate_);
    edge_.configure(10.0f, sample_rate_);
    swing_.configure(10.0f, sample_rate_);
    space_.configure(10.0f, sample_rate_);

    fir_coefficients_.fill(0.0f);
    if (configuration_.wire_oversample_factor == kWireOversampleFactor) {
        fir_taps_ = kFrozenFirTaps;
        for (std::size_t index = 0; index < kFrozenFirWords.size(); ++index) {
            fir_coefficients_[index] = wordToFloat(kFrozenFirWords[index]);
        }
    } else {
        fir_taps_ = kReferenceFirTaps;
        constexpr std::size_t count = kReferenceFirTaps;
        constexpr double center = static_cast<double>(count - 1U) * 0.5;
        const double normalized_cutoff = 18000.0 / (sample_rate_ * kReferenceOversampleFactor);
        double sum = 0.0;
        for (std::size_t index = 0; index < count; ++index) {
            const double offset = static_cast<double>(index) - center;
            const double argument = 2.0 * normalized_cutoff * offset;
            const double sinc = argument == 0.0
                ? 1.0
                : std::sin(kPi * argument) / (kPi * argument);
            const double window = 0.42
                - 0.5 * std::cos(2.0 * kPi * static_cast<double>(index) / static_cast<double>(count - 1U))
                + 0.08 * std::cos(4.0 * kPi * static_cast<double>(index) / static_cast<double>(count - 1U));
            fir_coefficients_[index] = static_cast<float>(2.0 * normalized_cutoff * sinc * window);
            sum += static_cast<double>(fir_coefficients_[index]);
        }
        for (std::size_t index = 0; index < count; ++index) {
            fir_coefficients_[index] = static_cast<float>(static_cast<double>(fir_coefficients_[index]) / sum);
        }
    }
    prepared_ = true;
    initialize();
    return true;
}

void Core::initialize() noexcept {
    absolute_sample_ = 0;
    diagnostics_ = {};
    resetDefaults(true);
}

void Core::resetDefaults(bool clear_diagnostics) noexcept {
    if (clear_diagnostics) diagnostics_ = {};
    tension_.reset(0.38f);
    shadow_.reset(0.0f);
    root_.reset(0.5f);
    bite_.reset(0.55f);
    edge_.reset(static_cast<float>(std::sqrt((4.0 - 1.5) / 28.5)));
    swing_.reset(0.0f);
    space_.reset(0.12f);
    tension_automation_.clear();
    active_rate_index_ = 0;
    pending_rate_index_ = 0;
    active_holes_ = 3;
    pending_holes_ = 3;
    under_index_ = 2;
    rate_pending_ = false;
    holes_pending_ = false;
    tempo_bpm_ = 120.0;
    shadow_ratio_index_ = {{2, 2}};
    active_shadow_slot_ = 0;
    ratio_crossfade_.reset(0.0f);
    complement_.reset(0.0f);
    flip_.reset(0.0f);
    void_override_.reset(0.0f);
    open_override_.reset(0.0f);
    flip_cancel_pending_ = false;
    transition_ = TransitionState::normal;
    output_transition_.reset(1.0f);
    containment_samples_ = {};
    containment_count_ = 0;
    tap_intervals_ = {};
    tap_interval_count_ = 0;
    last_tap_sample_ = 0;
    has_last_tap_ = false;
    clearSignalState();
    deriveWireCoefficients();
}

void Core::clearSignalState() noexcept {
    wire_phase_ = 0.0;
    shadow_phase_ = {};
    shadow_lowpass_ = {};
    svf_ic1_ = 0.0f;
    svf_ic2_ = 0.0f;
    fir_ring_.fill(0.0f);
    fir_write_ = 0;
    wire_space_.clear();
    shadow_space_.clear();
    dc_left_.clear();
    dc_right_.clear();
    beat_position_samples_ = 0.0;
    next_opportunity_sample_ = 0.0;
    square_cut_end_sample_ = 0.0;
    opportunity_index_ = 0;
    scheduler_error_ = 0;
    opportunity_scheduled_ = false;
    square_end_scheduled_ = false;
    cut_ = false;
    current_slot_frames_ = static_cast<std::uint32_t>(samplesPerBeat());
    complement_.reset(0.0f);
}

double Core::samplesPerBeat() const noexcept {
    return sample_rate_ * 60.0 / std::clamp(tempo_bpm_, 30.0, 240.0);
}

double Core::activeRate() const noexcept {
    return kRateTable[std::min<std::size_t>(active_rate_index_, kRateTable.size() - 1U)];
}

std::uint32_t Core::effectiveEdgeFrames() const noexcept {
    const double requested_ms = 1.5 + 28.5 * static_cast<double>(edge_.current) * static_cast<double>(edge_.current);
    const auto requested = static_cast<std::uint32_t>(std::max(1.0, std::round(requested_ms * 0.001 * sample_rate_)));
    const auto slot_limit = static_cast<std::uint32_t>(std::max(1.0, std::floor(0.45 * current_slot_frames_)));
    return std::min(requested, slot_limit);
}

void Core::deriveWireCoefficients() noexcept {
    const double tension = std::clamp(static_cast<double>(tension_.current), 0.0, 1.0);
    const double root = 55.0 * std::pow(2.0, 2.0 * std::clamp(static_cast<double>(root_.current), 0.0, 1.0));
    const double semitones = 42.0 * std::pow(tension, 1.35);
    const double frequency = std::clamp(root * std::pow(2.0, semitones / 12.0), 40.0, 6000.0);
    const double bite = std::clamp(static_cast<double>(bite_.current), 0.0, 1.0);
    const double q = std::clamp(0.8 + 14.0 * tension * tension * (0.25 + 0.75 * bite), 0.8, 14.8);
    const double filter_frequency = std::clamp(
        std::min(0.42 * sample_rate_, frequency * (1.35 + 1.15 * bite)),
        0.001,
        20160.0
    );
    const double oversampled_rate = sample_rate_ * configuration_.wire_oversample_factor;
    const double g = std::tan(kPi * filter_frequency / oversampled_rate);
    const double k = 1.0 / q;
    const double a1 = 1.0 / (1.0 + g * (g + k));
    const double a2 = g * a1;
    const double a3 = g * a2;
    if (!std::isfinite(frequency) || !std::isfinite(a1) || !std::isfinite(a2) || !std::isfinite(a3)) {
        derived_wire_frequency_ = 110.0f;
        derived_fold_gain_ = 1.0f;
        derived_q_ = 0.8f;
        derived_drive_ = 1.0f;
        derived_compensation_ = 1.0f;
        svf_a1_ = 1.0f;
        svf_a2_ = 0.0f;
        svf_a3_ = 0.0f;
        svf_k_ = 1.25f;
        ++diagnostics_.non_finite_containments;
        return;
    }
    derived_wire_frequency_ = static_cast<float>(frequency);
    derived_fold_gain_ = static_cast<float>(1.0 + 7.0 * tension * tension);
    derived_q_ = static_cast<float>(q);
    derived_drive_ = static_cast<float>(1.0 + 6.0 * tension * tension);
    derived_compensation_ = static_cast<float>(1.0 / std::sqrt(1.0 + 0.9 * tension + 1.1 * tension * tension));
    svf_a1_ = static_cast<float>(a1);
    svf_a2_ = static_cast<float>(a2);
    svf_a3_ = static_cast<float>(a3);
    svf_k_ = static_cast<float>(k);
}

void Core::writeLedger(
    const LedgerEvent& event,
    LedgerEvent* output,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    if (output == nullptr) return;
    if (report.ledger_events_written < capacity) {
        output[report.ledger_events_written++] = event;
    } else {
        ++report.ledger_events_dropped;
        ++diagnostics_.ledger_overflows;
    }
}

bool Core::applyControl(
    ControlId control,
    double value,
    std::uint64_t ingress_sequence,
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    if (!std::isfinite(value)) {
        ++diagnostics_.non_finite_targets;
        return false;
    }
    double accepted = value;
    switch (control) {
        case ControlId::tension: tension_.target = clamp01(value); accepted = tension_.target; break;
        case ControlId::cut:
            pending_rate_index_ = static_cast<std::uint32_t>(std::llround(std::clamp(value, 0.0, 8.0)));
            rate_pending_ = true;
            accepted = pending_rate_index_;
            break;
        case ControlId::shadow: shadow_.target = clamp01(value); accepted = shadow_.target; break;
        case ControlId::root: root_.target = clamp01(value); accepted = root_.target; break;
        case ControlId::bite: bite_.target = clamp01(value); accepted = bite_.target; break;
        case ControlId::holes:
            pending_holes_ = static_cast<std::uint32_t>(std::llround(std::clamp(value, 1.0, 6.0)));
            holes_pending_ = true;
            accepted = pending_holes_;
            break;
        case ControlId::edge: edge_.target = clamp01(value); accepted = edge_.target; break;
        case ControlId::under: {
            const auto selected = static_cast<std::uint32_t>(std::llround(std::clamp(value, 0.0, 4.0)));
            accepted = selected;
            if (selected != under_index_) {
                const auto inactive = 1U - active_shadow_slot_;
                shadow_ratio_index_[inactive] = selected;
                under_index_ = selected;
                ratio_crossfade_.reset(0.0f);
                ratio_crossfade_.begin(1.0f, 960U);
            }
            break;
        }
        case ControlId::swing: swing_.target = clamp01(value); accepted = swing_.target; break;
        case ControlId::space: space_.target = clamp01(value); accepted = space_.target; break;
        case ControlId::tempo: {
            const double old_samples_per_beat = samplesPerBeat();
            const double phase = old_samples_per_beat > 0.0 ? beat_position_samples_ / old_samples_per_beat : 0.0;
            const double old_remaining = opportunity_scheduled_
                ? std::max(0.0, next_opportunity_sample_ - static_cast<double>(absolute_sample_))
                : 0.0;
            tempo_bpm_ = std::clamp(value, 30.0, 240.0);
            const double scale = samplesPerBeat() / old_samples_per_beat;
            beat_position_samples_ = std::clamp(phase, 0.0, 1.0) * samplesPerBeat();
            if (opportunity_scheduled_) next_opportunity_sample_ = static_cast<double>(absolute_sample_) + old_remaining * scale;
            accepted = tempo_bpm_;
            break;
        }
    }
    writeLedger({absolute_sample_, ingress_sequence, LedgerKind::accepted_control, control, ActionId::unsupported, accepted, active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
    return true;
}

bool Core::applyAction(
    ActionId action,
    std::uint64_t ingress_sequence,
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    switch (action) {
        case ActionId::void_on: void_override_.begin(1.0f, 144U); break;
        case ActionId::void_off: void_override_.begin(0.0f, 144U); break;
        case ActionId::open_on: open_override_.begin(1.0f, 144U); break;
        case ActionId::open_off: open_override_.begin(0.0f, 144U); break;
        case ActionId::flip: flip_.begin(flip_.target < 0.5f ? 1.0f : 0.0f, 480U); break;
        case ActionId::flip_cancel: flip_cancel_pending_ = true; break;
        case ActionId::downbeat:
            beat_position_samples_ = samplesPerBeat();
            scheduler_error_ = 0;
            break;
        case ActionId::panic:
            if (transition_ != TransitionState::panic_down && transition_ != TransitionState::panic_latched) {
                transition_ = TransitionState::panic_down;
                output_transition_.begin(0.0f, 480U);
                rate_pending_ = false;
                holes_pending_ = false;
                flip_cancel_pending_ = false;
                ++diagnostics_.panic_count;
            }
            break;
        case ActionId::panic_release:
            if (transition_ == TransitionState::panic_latched) {
                transition_ = TransitionState::panic_up;
                output_transition_.reset(0.0f);
                output_transition_.begin(1.0f, 240U);
            }
            break;
        case ActionId::tap_tempo:
            if (has_last_tap_) {
                const auto interval = absolute_sample_ - last_tap_sample_;
                if (interval >= 12000U && interval <= 96000U) {
                    if (tap_interval_count_ < tap_intervals_.size()) {
                        tap_intervals_[tap_interval_count_++] = interval;
                    } else {
                        tap_intervals_[0] = tap_intervals_[1];
                        tap_intervals_[1] = tap_intervals_[2];
                        tap_intervals_[2] = interval;
                    }
                    if (tap_interval_count_ == tap_intervals_.size()) {
                        auto sorted = tap_intervals_;
                        std::sort(sorted.begin(), sorted.end());
                        const double bpm = 60.0 * sample_rate_ / static_cast<double>(sorted[1]);
                        applyControl(ControlId::tempo, bpm, ingress_sequence, nullptr, 0, report);
                    }
                }
            }
            last_tap_sample_ = absolute_sample_;
            has_last_tap_ = true;
            break;
        case ActionId::reset:
            transition_ = TransitionState::reset_down;
            output_transition_.begin(0.0f, 240U);
            rate_pending_ = false;
            holes_pending_ = false;
            flip_cancel_pending_ = false;
            ++diagnostics_.reset_count;
            break;
        case ActionId::unsupported:
            ++diagnostics_.unsupported_actions;
            return false;
    }
    writeLedger({absolute_sample_, ingress_sequence, LedgerKind::accepted_action, ControlId::tension, action, 0.0, active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
    return true;
}

bool Core::applyEvent(
    const Event& event,
    ProcessReport& report,
    LedgerEvent* ledger,
    std::size_t capacity
) noexcept {
    const bool resetting = transition_ == TransitionState::reset_down || transition_ == TransitionState::reset_up;
    const bool reset_override = event.kind == EventKind::action
        && (event.action == ActionId::panic || event.action == ActionId::reset);
    if (resetting && !reset_override) {
        ++diagnostics_.rejected_during_reset;
        ++diagnostics_.dropped_events;
        ++report.dropped_events;
        return false;
    }
    bool accepted = false;
    if (event.kind == EventKind::action) {
        accepted = applyAction(event.action, event.ingress_sequence, ledger, capacity, report);
    } else if (event.kind == EventKind::linear_control
        && (event.control != ControlId::tension
            || event.duration_frames == 0
            || !std::isfinite(event.value)
            || !std::isfinite(event.end_value))) {
        ++diagnostics_.invalid_events;
    } else {
        accepted = applyControl(event.control, event.value, event.ingress_sequence, ledger, capacity, report);
        if (accepted && event.kind == EventKind::linear_control) {
            tension_automation_.active = true;
            tension_automation_.start_sample = absolute_sample_;
            tension_automation_.end_sample = absolute_sample_ + event.duration_frames;
            tension_automation_.start_value = clamp01(event.value);
            tension_automation_.end_value = clamp01(event.end_value);
        }
    }
    if (accepted) {
        ++diagnostics_.accepted_events;
        ++report.accepted_events;
    } else if (!resetting) {
        ++diagnostics_.dropped_events;
        ++report.dropped_events;
    }
    return accepted;
}

bool Core::setControlValue(ControlId control, double value) noexcept {
    ProcessReport report{};
    return applyControl(control, value, 0, nullptr, 0, report);
}

bool Core::triggerAction(ActionId action) noexcept {
    ProcessReport report{};
    return applyAction(action, 0, nullptr, 0, report);
}

void Core::updateAutomation() noexcept {
    if (!tension_automation_.active) return;
    if (absolute_sample_ >= tension_automation_.end_sample) {
        tension_.target = tension_automation_.end_value;
        tension_automation_.active = false;
        return;
    }
    const double span = static_cast<double>(tension_automation_.end_sample - tension_automation_.start_sample);
    const double elapsed = static_cast<double>(absolute_sample_ - tension_automation_.start_sample);
    const double unit = span > 0.0 ? elapsed / span : 1.0;
    tension_.target = static_cast<float>(tension_automation_.start_value
        + (tension_automation_.end_value - tension_automation_.start_value) * unit);
}

void Core::onBeatBoundary(
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    ++diagnostics_.beat_boundaries;
    writeLedger({absolute_sample_, 0, LedgerKind::beat_boundary, ControlId::tempo, ActionId::unsupported, tempo_bpm_, active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
    bool changed = false;
    if (rate_pending_) {
        changed = pending_rate_index_ != active_rate_index_;
        active_rate_index_ = pending_rate_index_;
        rate_pending_ = false;
    }
    if (holes_pending_) {
        active_holes_ = pending_holes_;
        holes_pending_ = false;
        scheduler_error_ = 0;
        changed = true;
    }
    if (flip_cancel_pending_) {
        flip_.begin(0.0f, 480U);
        flip_cancel_pending_ = false;
        changed = true;
    }
    if (changed) {
        ++diagnostics_.rhythm_commits;
        writeLedger({absolute_sample_, 0, LedgerKind::rhythm_commit, ControlId::cut, ActionId::unsupported, static_cast<double>(active_rate_index_), active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
        if (active_rate_index_ == 0) {
            opportunity_scheduled_ = false;
            square_end_scheduled_ = false;
            cut_ = false;
            complement_.begin(0.0f, effectiveEdgeFrames());
        } else {
            next_opportunity_sample_ = static_cast<double>(absolute_sample_);
            opportunity_scheduled_ = true;
            square_end_scheduled_ = false;
        }
    } else if (active_rate_index_ > 0 && !opportunity_scheduled_) {
        next_opportunity_sample_ = static_cast<double>(absolute_sample_);
        opportunity_scheduled_ = true;
    }
}

void Core::scheduleNextOpportunity() noexcept {
    const double rate = activeRate();
    if (rate <= 0.0) {
        opportunity_scheduled_ = false;
        return;
    }
    const double slot = samplesPerBeat() / rate;
    const double swing = 0.5 + 0.18 * std::clamp(static_cast<double>(swing_.current), 0.0, 1.0);
    const bool first_interval = (opportunity_index_ % 2U) == 1U;
    double interval = first_interval ? 2.0 * swing * slot : 2.0 * (1.0 - swing) * slot;
    interval = std::max(32.0, interval);
    current_slot_frames_ = static_cast<std::uint32_t>(std::max(32.0, std::round(interval)));
    next_opportunity_sample_ += interval;
    opportunity_scheduled_ = true;
}

void Core::onOpportunity(
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    ++diagnostics_.opportunity_boundaries;
    ++opportunity_index_;
    const bool old_cut = cut_;
    if (configuration_.scheduler_mode == SchedulerMode::error_accumulator) {
        scheduler_error_ += static_cast<std::int32_t>(active_holes_);
        cut_ = scheduler_error_ >= 8;
        if (cut_) scheduler_error_ -= 8;
    } else {
        cut_ = true;
        const double slot = samplesPerBeat() / std::max(0.5, activeRate());
        square_cut_end_sample_ = static_cast<double>(absolute_sample_) + 0.375 * slot;
        square_end_scheduled_ = true;
        scheduler_error_ = 0;
    }
    if (cut_ != old_cut) {
        if (cut_) ++diagnostics_.cut_boundaries;
        complement_.begin(cut_ ? 1.0f : 0.0f, effectiveEdgeFrames());
    }
    writeLedger({absolute_sample_, 0, LedgerKind::opportunity, ControlId::cut, ActionId::unsupported, activeRate(), active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
    scheduleNextOpportunity();
}

void Core::onSquareEnd(
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    square_end_scheduled_ = false;
    const bool old_cut = cut_;
    cut_ = false;
    if (old_cut) complement_.begin(0.0f, effectiveEdgeFrames());
    ++diagnostics_.opportunity_boundaries;
    writeLedger({absolute_sample_, 0, LedgerKind::opportunity, ControlId::cut, ActionId::unsupported, activeRate(), active_rate_index_, active_holes_, 0, effectiveEdgeFrames(), false}, ledger, capacity, report);
}

void Core::updateTransition(
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    const bool ramp_was_active = output_transition_.active();
    output_transition_.next();
    if (transition_ == TransitionState::reset_down && !ramp_was_active) {
        const auto saved_sample = absolute_sample_;
        const auto saved_diagnostics = diagnostics_;
        resetDefaults(false);
        absolute_sample_ = saved_sample;
        diagnostics_ = saved_diagnostics;
        transition_ = TransitionState::reset_up;
        output_transition_.reset(0.0f);
        output_transition_.begin(1.0f, 240U);
        output_transition_.next();
        writeLedger({absolute_sample_, 0, LedgerKind::reset_boundary, ControlId::tension, ActionId::reset, 0.0, active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
    } else if (transition_ == TransitionState::reset_up && !ramp_was_active) {
        transition_ = TransitionState::normal;
    } else if (transition_ == TransitionState::panic_down && !ramp_was_active) {
        clearSignalState();
        active_rate_index_ = 0;
        pending_rate_index_ = 0;
        rate_pending_ = false;
        holes_pending_ = false;
        const auto retained_ratio = shadow_ratio_index_[active_shadow_slot_];
        shadow_ratio_index_ = {{retained_ratio, retained_ratio}};
        under_index_ = retained_ratio;
        ratio_crossfade_.reset(0.0f);
        flip_.reset(0.0f);
        void_override_.reset(0.0f);
        open_override_.reset(0.0f);
        flip_cancel_pending_ = false;
        transition_ = TransitionState::panic_latched;
        output_transition_.reset(0.0f);
        writeLedger({absolute_sample_, 0, LedgerKind::panic_boundary, ControlId::tension, ActionId::panic, 0.0, active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
    } else if (transition_ == TransitionState::panic_up && !ramp_was_active) {
        transition_ = TransitionState::normal;
    }
}

void Core::contain(
    std::uint64_t ingress_sequence,
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    ++diagnostics_.non_finite_containments;
    if (containment_count_ < containment_samples_.size()) {
        containment_samples_[containment_count_++] = absolute_sample_;
    } else {
        containment_samples_[0] = containment_samples_[1];
        containment_samples_[1] = containment_samples_[2];
        containment_samples_[2] = absolute_sample_;
    }
    writeLedger({absolute_sample_, ingress_sequence, LedgerKind::containment, ControlId::tension, ActionId::unsupported, 0.0, active_rate_index_, active_holes_, scheduler_error_, effectiveEdgeFrames(), cut_}, ledger, capacity, report);
    if (containment_count_ == containment_samples_.size()
        && containment_samples_[2] - containment_samples_[0] <= 48000U
        && transition_ != TransitionState::panic_down
        && transition_ != TransitionState::panic_latched) {
        applyAction(ActionId::panic, ingress_sequence, ledger, capacity, report);
    }
}

float Core::processWire() noexcept {
    const auto factor = configuration_.wire_oversample_factor;
    const double oversampled_rate = sample_rate_ * factor;
    for (std::uint32_t sub = 0; sub < factor; ++sub) {
        const double source = 0.82 * std::sin(wire_phase_)
            + 0.18 * std::sin(2.0 * wire_phase_ + 0.31);
        wire_phase_ += 2.0 * kPi * static_cast<double>(derived_wire_frequency_) / oversampled_rate;
        if (wire_phase_ >= 2.0 * kPi) wire_phase_ -= 2.0 * kPi;
        const double folded = (2.0 / kPi) * std::asin(std::sin(kPi * static_cast<double>(derived_fold_gain_) * source * 0.5));
        const float input = static_cast<float>(folded);
        const float v3 = input - svf_ic2_;
        const float band = svf_a1_ * svf_ic1_ + svf_a2_ * v3;
        const float low = svf_ic2_ + svf_a2_ * svf_ic1_ + svf_a3_ * v3;
        svf_ic1_ = denormalZero(2.0f * band - svf_ic1_);
        svf_ic2_ = denormalZero(2.0f * low - svf_ic2_);
        const double mixed = 0.68 * folded + 0.32 * static_cast<double>(band) / std::sqrt(static_cast<double>(derived_q_));
        const double driven = static_cast<double>(derived_compensation_)
            * std::tanh(static_cast<double>(derived_drive_) * mixed)
            / std::tanh(static_cast<double>(derived_drive_));
        if (!std::isfinite(driven) || !std::isfinite(svf_ic1_) || !std::isfinite(svf_ic2_)) {
            svf_ic1_ = 0.0f;
            svf_ic2_ = 0.0f;
            fir_ring_.fill(0.0f);
            return std::numeric_limits<float>::quiet_NaN();
        }
        fir_ring_[fir_write_] = static_cast<float>(driven);
        fir_write_ = (fir_write_ + 1U) % fir_taps_;
    }
    float decimated = 0.0f;
    std::size_t read = fir_write_ == 0 ? fir_taps_ - 1U : fir_write_ - 1U;
    for (std::size_t tap = 0; tap < fir_taps_; ++tap) {
        decimated += fir_coefficients_[tap] * fir_ring_[read];
        read = read == 0 ? fir_taps_ - 1U : read - 1U;
    }
    return denormalZero(decimated);
}

float Core::processShadow() noexcept {
    std::array<float, 2> values{};
    for (std::size_t slot = 0; slot < values.size(); ++slot) {
        const double ratio = kShadowRatios[std::min<std::size_t>(shadow_ratio_index_[slot], kShadowRatios.size() - 1U)];
        const double frequency = std::clamp(ratio * static_cast<double>(derived_wire_frequency_), 27.5, 4000.0);
        const double source = 0.82 * std::sin(shadow_phase_[slot]) + 0.18 * std::sin(2.0 * shadow_phase_[slot]);
        shadow_phase_[slot] += 2.0 * kPi * frequency / sample_rate_;
        if (shadow_phase_[slot] >= 2.0 * kPi) shadow_phase_[slot] -= 2.0 * kPi;
        const float coefficient = static_cast<float>(std::exp(-2.0 * kPi * std::min(4.0 * frequency, 6000.0) / sample_rate_));
        shadow_lowpass_[slot] = denormalZero((1.0f - coefficient) * static_cast<float>(source) + coefficient * shadow_lowpass_[slot]);
        values[slot] = std::tanh(1.4f * shadow_lowpass_[slot]);
    }
    if (ratio_crossfade_.active()) {
        const auto old_slot = active_shadow_slot_;
        const auto new_slot = 1U - old_slot;
        const float coordinate = ratio_crossfade_.next();
        const float old_gain = static_cast<float>(std::cos(0.5 * kPi * coordinate));
        const float new_gain = static_cast<float>(std::sin(0.5 * kPi * coordinate));
        const float result = values[old_slot] * old_gain + values[new_slot] * new_gain;
        if (!ratio_crossfade_.active() && coordinate >= 1.0f) {
            active_shadow_slot_ = new_slot;
            ratio_crossfade_.reset(0.0f);
        }
        return result;
    }
    return values[active_shadow_slot_];
}

std::array<float, 2> Core::processSpace(VoiceSpace& state, float input, float amount) noexcept {
    constexpr std::size_t left_delay = 3216;
    constexpr std::size_t right_delay = 4272;
    const float read_left = state.left[state.left_write];
    const float read_right = state.right[state.right_write];
    const float feedback = 0.32f * amount;
    const float wet = 0.28f * amount * state.wet_recovery;
    state.left[state.left_write] = std::tanh(input + feedback * read_right);
    state.right[state.right_write] = std::tanh(input + feedback * read_left);
    state.left_write = (state.left_write + 1U) % left_delay;
    state.right_write = (state.right_write + 1U) % right_delay;
    return {{(1.0f - wet) * input + wet * read_left, (1.0f - wet) * input + wet * read_right}};
}

std::array<float, 2> Core::processOneSample(
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    updateAutomation();
    updateTransition(ledger, capacity, report);

    const double beat_length = samplesPerBeat();
    if (absolute_sample_ == 0 || beat_position_samples_ >= beat_length - 1.0e-9) {
        if (absolute_sample_ != 0) beat_position_samples_ = std::max(0.0, beat_position_samples_ - beat_length);
        onBeatBoundary(ledger, capacity, report);
    }
    if (square_end_scheduled_ && static_cast<double>(absolute_sample_) + 1.0e-9 >= square_cut_end_sample_) {
        onSquareEnd(ledger, capacity, report);
    }
    if (opportunity_scheduled_ && static_cast<double>(absolute_sample_) + 1.0e-9 >= next_opportunity_sample_) {
        onOpportunity(ledger, capacity, report);
    }

    tension_.next();
    shadow_.next();
    root_.next();
    bite_.next();
    edge_.next();
    swing_.next();
    space_.next();
    if ((absolute_sample_ % 16U) == 0U) deriveWireCoefficients();

    if (transition_ == TransitionState::panic_latched) {
        beat_position_samples_ += 1.0;
        return {{0.0f, 0.0f}};
    }

    float wire = processWire();
    float shadow = processShadow();
    if (!std::isfinite(wire) || !std::isfinite(shadow)) {
        wire = 0.0f;
        shadow = 0.0f;
        contain(0, ledger, capacity, report);
    }
    const auto wire_stereo = processSpace(wire_space_, wire, space_.current);
    const auto shadow_stereo = processSpace(shadow_space_, shadow, space_.current);

    const float q = complement_.next();
    const float flip = flip_.next();
    const float open = open_override_.next();
    const float void_amount = void_override_.next();
    const float flipped_coordinate = 1.0f - q;
    float effective_q = q * (1.0f - flip) + flipped_coordinate * flip;
    effective_q *= (1.0f - open);
    effective_q = std::clamp(effective_q, 0.0f, 1.0f);
    const float wire_gain = static_cast<float>(std::cos(0.5 * kPi * effective_q));
    const float shadow_amount = std::clamp(shadow_.current * (1.0f - void_amount), 0.0f, 1.0f);
    const float shadow_gain = configuration_.shadow_mode == ShadowMode::continuous_parallel
        ? std::sqrt(shadow_amount) * configuration_.parallel_shadow_gain
        : std::sqrt(shadow_amount) * static_cast<float>(std::sin(0.5 * kPi * effective_q));
    const float mixed_left = wire_gain * wire_stereo[0] + shadow_gain * shadow_stereo[0];
    const float mixed_right = wire_gain * wire_stereo[1] + shadow_gain * shadow_stereo[1];

    const float dc_coefficient = static_cast<float>(std::exp(-2.0 * kPi * 10.0 / sample_rate_));
    const float dc_left = dc_left_.process(mixed_left, dc_coefficient);
    const float dc_right = dc_right_.process(mixed_right, dc_coefficient);
    float output_left = kOutputCeiling * std::tanh(dc_left / kOutputCeiling);
    float output_right = kOutputCeiling * std::tanh(dc_right / kOutputCeiling);
    if (!std::isfinite(output_left) || !std::isfinite(output_right)) {
        output_left = 0.0f;
        output_right = 0.0f;
        ++diagnostics_.output_non_finite_clears;
        contain(0, ledger, capacity, report);
    }
    output_left *= output_transition_.current;
    output_right *= output_transition_.current;
    beat_position_samples_ += 1.0;
    return {{output_left, output_right}};
}

ProcessReport Core::process(
    float* output_left,
    float* output_right,
    std::uint32_t frames,
    const Event* events,
    std::size_t event_count,
    LedgerEvent* ledger_output,
    std::size_t ledger_capacity
) noexcept {
    ProcessReport report{};
    if (!prepared_ || output_left == nullptr || output_right == nullptr
        || frames == 0 || frames > maximum_block_frames_
        || (event_count > 0 && events == nullptr)) {
        ++diagnostics_.unsupported_process_calls;
        return report;
    }
    const std::size_t accepted_input_count = std::min(event_count, kMaximumEventsPerBlock);
    if (event_count > accepted_input_count) {
        const auto dropped = event_count - accepted_input_count;
        report.dropped_events += dropped;
        diagnostics_.dropped_events += dropped;
    }
    std::size_t event_index = 0;
    for (std::uint32_t frame = 0; frame < frames; ++frame) {
        while (event_index < accepted_input_count && events[event_index].sample_offset < frame) {
            ++diagnostics_.invalid_events;
            ++diagnostics_.dropped_events;
            ++report.dropped_events;
            ++event_index;
        }
        std::uint64_t previous_sequence = 0;
        bool have_sequence = false;
        while (event_index < accepted_input_count && events[event_index].sample_offset == frame) {
            const auto& event = events[event_index++];
            if (have_sequence && event.ingress_sequence <= previous_sequence) {
                ++diagnostics_.invalid_events;
                ++diagnostics_.dropped_events;
                ++report.dropped_events;
                continue;
            }
            previous_sequence = event.ingress_sequence;
            have_sequence = true;
            applyEvent(event, report, ledger_output, ledger_capacity);
        }
        const auto output = processOneSample(ledger_output, ledger_capacity, report);
        output_left[frame] = output[0];
        output_right[frame] = output[1];
        ++absolute_sample_;
        ++diagnostics_.processed_frames;
    }
    while (event_index < accepted_input_count) {
        ++event_index;
        ++diagnostics_.invalid_events;
        ++diagnostics_.dropped_events;
        ++report.dropped_events;
    }
    return report;
}

StateSnapshot Core::snapshot() const noexcept {
    const auto active_slot = std::min<std::size_t>(active_shadow_slot_, 1U);
    const double ratio = kShadowRatios[std::min<std::size_t>(shadow_ratio_index_[active_slot], kShadowRatios.size() - 1U)];
    const float q = complement_.current;
    const float flipped_q = 1.0f - q;
    const float effective_q = std::clamp((q * (1.0f - flip_.current) + flipped_q * flip_.current) * (1.0f - open_override_.current), 0.0f, 1.0f);
    return {
        absolute_sample_, tension_.current, shadow_.current, root_.current, bite_.current,
        edge_.current, swing_.current, space_.current, tempo_bpm_, derived_wire_frequency_,
        ratio * derived_wire_frequency_, beat_position_samples_ / samplesPerBeat(),
        complement_.current, effective_q, wire_phase_, shadow_phase_, active_rate_index_,
        pending_rate_index_, active_holes_, pending_holes_, under_index_, scheduler_error_,
        opportunity_index_, fir_write_,
        {{wire_space_.left_write, wire_space_.right_write, shadow_space_.left_write, shadow_space_.right_write}},
        rate_pending_, holes_pending_, cut_, flip_.current >= 0.5f,
        void_override_.current > 0.0f, open_override_.current > 0.0f,
        transition_ == TransitionState::reset_down || transition_ == TransitionState::reset_up,
        transition_ == TransitionState::panic_down,
        transition_ == TransitionState::panic_latched,
    };
}

std::string Core::normalizedStateSha256() const {
    schuss::instrument_lab::Sha256 hash;
    const auto state = snapshot();
    hashPod(hash, state.tension); hashPod(hash, state.shadow); hashPod(hash, state.root);
    hashPod(hash, state.bite); hashPod(hash, state.edge); hashPod(hash, state.swing);
    hashPod(hash, state.space); hashPod(hash, state.tempo_bpm); hashPod(hash, state.wire_frequency_hz);
    hashPod(hash, state.shadow_frequency_hz); hashPod(hash, state.beat_phase);
    hashPod(hash, state.complement_coordinate); hashPod(hash, state.effective_complement_coordinate);
    hashPod(hash, state.wire_phase);
    for (const auto value : state.shadow_phases) hashPod(hash, value);
    hashPod(hash, state.active_rate_index); hashPod(hash, state.pending_rate_index);
    hashPod(hash, state.active_holes); hashPod(hash, state.pending_holes); hashPod(hash, state.under_index);
    hashPod(hash, state.scheduler_error); hashPod(hash, state.opportunity_index); hashPod(hash, state.fir_write_index);
    for (const auto value : state.delay_write_indices) hashPod(hash, value);
    hashBool(hash, state.rate_pending); hashBool(hash, state.holes_pending); hashBool(hash, state.cut);
    hashBool(hash, state.flipped); hashBool(hash, state.void_active); hashBool(hash, state.open_active);
    hashBool(hash, state.reset_active); hashBool(hash, state.panic_ramping); hashBool(hash, state.panic_latched);
    for (const auto value : fir_ring_) hashPod(hash, value);
    for (const auto value : wire_space_.left) hashPod(hash, value);
    for (const auto value : wire_space_.right) hashPod(hash, value);
    for (const auto value : shadow_space_.left) hashPod(hash, value);
    for (const auto value : shadow_space_.right) hashPod(hash, value);
    hashPod(hash, svf_ic1_); hashPod(hash, svf_ic2_);
    hashPod(hash, dc_left_.input_previous); hashPod(hash, dc_left_.output_previous);
    hashPod(hash, dc_right_.input_previous); hashPod(hash, dc_right_.output_previous);
    return hash.finish();
}

std::string Core::fullStateSha256() const {
    schuss::instrument_lab::Sha256 hash;
    const auto normalized = normalizedStateSha256();
    hash.update(reinterpret_cast<const std::uint8_t*>(normalized.data()), normalized.size());
    hashPod(hash, absolute_sample_);
    hashPod(hash, diagnostics_);
    return hash.finish();
}

std::string Core::frozenFirByteSha256() {
    std::array<std::uint8_t, kFrozenFirTaps * 4U> bytes{};
    for (std::size_t index = 0; index < kFrozenFirWords.size(); ++index) {
        const auto word = kFrozenFirWords[index];
        bytes[index * 4U] = static_cast<std::uint8_t>(word);
        bytes[index * 4U + 1U] = static_cast<std::uint8_t>(word >> 8U);
        bytes[index * 4U + 2U] = static_cast<std::uint8_t>(word >> 16U);
        bytes[index * 4U + 3U] = static_cast<std::uint8_t>(word >> 24U);
    }
    return schuss::instrument_lab::sha256(bytes.data(), bytes.size());
}

const char* controlName(ControlId control) noexcept {
    switch (control) {
        case ControlId::tension: return "TENSION";
        case ControlId::cut: return "CUT";
        case ControlId::shadow: return "SHADOW";
        case ControlId::root: return "ROOT";
        case ControlId::bite: return "BITE";
        case ControlId::holes: return "HOLES";
        case ControlId::edge: return "EDGE";
        case ControlId::under: return "UNDER";
        case ControlId::swing: return "SWING";
        case ControlId::space: return "SPACE";
        case ControlId::tempo: return "TEMPO";
    }
    return "UNKNOWN";
}

const char* actionName(ActionId action) noexcept {
    switch (action) {
        case ActionId::void_on: return "VOID_ON";
        case ActionId::void_off: return "VOID_OFF";
        case ActionId::open_on: return "OPEN_ON";
        case ActionId::open_off: return "OPEN_OFF";
        case ActionId::flip: return "FLIP";
        case ActionId::flip_cancel: return "FLIP_CANCEL";
        case ActionId::downbeat: return "DOWNBEAT";
        case ActionId::panic: return "PANIC";
        case ActionId::panic_release: return "PANIC_RELEASE";
        case ActionId::tap_tempo: return "TAP_TEMPO";
        case ActionId::reset: return "RESET";
        case ActionId::unsupported: return "UNSUPPORTED";
    }
    return "UNSUPPORTED";
}

const char* ledgerKindName(LedgerKind kind) noexcept {
    switch (kind) {
        case LedgerKind::accepted_control: return "accepted_control";
        case LedgerKind::accepted_action: return "accepted_action";
        case LedgerKind::beat_boundary: return "beat_boundary";
        case LedgerKind::rhythm_commit: return "rhythm_commit";
        case LedgerKind::opportunity: return "opportunity";
        case LedgerKind::containment: return "containment";
        case LedgerKind::reset_boundary: return "reset_boundary";
        case LedgerKind::panic_boundary: return "panic_boundary";
    }
    return "unknown";
}

}  // namespace wirefall
