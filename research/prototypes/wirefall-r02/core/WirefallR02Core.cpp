#include "WirefallR02Core.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace wirefall::r02 {
namespace {

constexpr double kPi = 3.14159265358979323846264338327950288;

constexpr std::size_t indexOf(ControlId id) noexcept {
    return static_cast<std::size_t>(id);
}

double raisedCosine(double unit) noexcept {
    const double bounded = std::clamp(unit, 0.0, 1.0);
    return 0.5 - 0.5 * std::cos(kPi * bounded);
}

double finiteOrZero(double value) noexcept {
    return std::isfinite(value) ? value : 0.0;
}

}  // namespace

void Core::Smoothed::configure(double milliseconds, double sample_rate) noexcept {
    coefficient = std::exp(-1.0 / (std::max(milliseconds, 0.001) * 0.001 * sample_rate));
}

void Core::Smoothed::reset(double value) noexcept {
    current = value;
    target = value;
}

double Core::Smoothed::next() noexcept {
    current = target + (current - target) * coefficient;
    if (std::abs(current - target) < 1.0e-12) current = target;
    if (!std::isfinite(current)) current = target;
    return current;
}

void Core::DcBlocker::clear() noexcept {
    previous_input = 0.0;
    previous_output = 0.0;
}

double Core::DcBlocker::process(double input, double coefficient) noexcept {
    const double output = input - previous_input + coefficient * previous_output;
    previous_input = input;
    previous_output = std::abs(output) < 1.0e-24 ? 0.0 : output;
    return previous_output;
}

Core::Core() noexcept {
    for (auto& value : smoothed_) value.configure(12.0, kExperimentSampleRate);
    initialize();
}

bool Core::prepare(double sample_rate, std::uint32_t maximum_block_frames) noexcept {
    if (!std::isfinite(sample_rate) || sample_rate < 44100.0 || sample_rate > 96000.0
        || maximum_block_frames == 0 || maximum_block_frames > kMaximumBlockFrames) {
        prepared_ = false;
        return false;
    }
    sample_rate_ = sample_rate;
    maximum_block_frames_ = maximum_block_frames;
    delay_left_frames_ = static_cast<std::size_t>(std::llround(0.023 * sample_rate_));
    delay_right_frames_ = static_cast<std::size_t>(std::llround(0.031 * sample_rate_));
    tick_length_ = static_cast<std::uint32_t>(std::llround(0.008 * sample_rate_));
    if (delay_left_frames_ == 0 || delay_right_frames_ == 0
        || delay_left_frames_ > delay_left_.size() || delay_right_frames_ > delay_right_.size()
        || tick_length_ < 2) {
        prepared_ = false;
        return false;
    }
    for (auto& value : smoothed_) value.configure(12.0, sample_rate_);
    smoothed_[indexOf(ControlId::break_depth)].configure(5.0, sample_rate_);
    smoothed_[indexOf(ControlId::tick)].configure(5.0, sample_rate_);
    smoothed_[indexOf(ControlId::root)].configure(12.0, sample_rate_);
    smoothed_[indexOf(ControlId::edge)].configure(8.0, sample_rate_);
    smoothed_[indexOf(ControlId::width)].configure(8.0, sample_rate_);
    smoothed_[indexOf(ControlId::output)].configure(8.0, sample_rate_);
    prepared_ = true;
    initialize();
    return true;
}

void Core::initialize() noexcept {
    absolute_frame_ = 0;
    resetDefaults(true);
}

void Core::resetDefaults(bool clear_diagnostics) noexcept {
    if (clear_diagnostics) diagnostics_ = {};
    for (const auto& item : kControlDescriptors) {
        const auto index = indexOf(item.id);
        accepted_[index] = item.default_value;
        smoothed_[index].reset(item.default_value);
    }
    energy_automation_ = {};
    force_open_ = false;
    transition_ = TransitionState::running;
    transition_elapsed_ = 0;
    transition_total_ = 0;
    transition_start_ = 1.0f;
    transition_target_ = 1.0f;
    transition_gain_ = 1.0f;
    non_finite_frames_ = {};
    non_finite_count_ = 0;
    clearSignalState();
}

void Core::clearSignalState() noexcept {
    oscillator_phase_ = 0.0;
    pulse_phase_ = 0.0;
    svf_ic1_ = 0.0;
    svf_ic2_ = 0.0;
    svf_g_ = 0.0;
    svf_k_ = 1.0;
    coefficient_countdown_ = 0;
    wire_frequency_hz_ = 82.4069;
    delay_left_.fill(0.0f);
    delay_right_.fill(0.0f);
    delay_left_write_ = 0;
    delay_right_write_ = 0;
    dc_left_.clear();
    dc_right_.clear();
    tick_frame_ = tick_length_;
    pulse_was_active_ = false;
    pulse_onset_pending_ = false;
}

bool Core::applyControl(ControlId id, double value) noexcept {
    const auto raw = static_cast<std::size_t>(id);
    if (raw >= kControlDescriptors.size() || !std::isfinite(value)) {
        ++diagnostics_.invalid_events;
        if (!std::isfinite(value)) ++diagnostics_.non_finite_controls;
        return false;
    }
    const auto& item = descriptor(id);
    double accepted = std::clamp(value, item.minimum, item.maximum);
    if (item.stepped) accepted = std::round(accepted);
    accepted_[raw] = accepted;
    if (id == ControlId::pulse) {
        smoothed_[raw].reset(accepted);
    } else {
        smoothed_[raw].target = accepted;
    }
    if (id == ControlId::energy) energy_automation_.active = false;
    return true;
}

void Core::beginTransition(TransitionState state, float target, std::uint32_t frames) noexcept {
    transition_ = state;
    transition_elapsed_ = 0;
    transition_total_ = frames;
    transition_start_ = transition_gain_;
    transition_target_ = target;
    if (frames == 0) transition_gain_ = target;
}

bool Core::applyAction(ActionId id) noexcept {
    switch (id) {
        case ActionId::open_press:
            force_open_ = true;
            return true;
        case ActionId::open_release:
            force_open_ = false;
            return true;
        case ActionId::tick_preview:
            tick_frame_ = 0;
            return true;
        case ActionId::downbeat:
            pulse_phase_ = 0.0;
            pulse_onset_pending_ = true;
            return true;
        case ActionId::panic_press:
            ++diagnostics_.panic_count;
            beginTransition(TransitionState::panic_down, 0.0f,
                static_cast<std::uint32_t>(std::llround(0.010 * sample_rate_)));
            return true;
        case ActionId::panic_release:
            non_finite_count_ = 0;
            non_finite_frames_ = {};
            beginTransition(TransitionState::panic_up, 1.0f,
                static_cast<std::uint32_t>(std::llround(0.005 * sample_rate_)));
            return true;
        case ActionId::reset:
            ++diagnostics_.reset_count;
            beginTransition(TransitionState::reset_down, 0.0f,
                static_cast<std::uint32_t>(std::llround(0.005 * sample_rate_)));
            return true;
        case ActionId::unsupported:
            ++diagnostics_.unknown_actions;
            return false;
    }
    ++diagnostics_.unknown_actions;
    return false;
}

bool Core::applyEvent(const Event& event) noexcept {
    if (event.kind == EventKind::set_control) return applyControl(event.control, event.value);
    if (event.kind == EventKind::action) return applyAction(event.action);
    if (event.kind == EventKind::linear_control) {
        if (event.control != ControlId::energy || event.duration_frames == 0
            || !std::isfinite(event.value) || !std::isfinite(event.end_value)) {
            ++diagnostics_.invalid_events;
            return false;
        }
        if (!applyControl(event.control, event.value)) return false;
        energy_automation_.active = true;
        energy_automation_.start_frame = absolute_frame_;
        energy_automation_.end_frame = absolute_frame_ + event.duration_frames;
        energy_automation_.start_value = std::clamp(event.value, 0.0, 1.0);
        energy_automation_.end_value = std::clamp(event.end_value, 0.0, 1.0);
        return true;
    }
    ++diagnostics_.invalid_events;
    return false;
}

bool Core::setControlValue(ControlId id, double value) noexcept {
    return applyControl(id, value);
}

bool Core::triggerAction(ActionId id) noexcept {
    return applyAction(id);
}

bool Core::appendLedger(
    const LedgerEvent& event,
    LedgerEvent* ledger,
    std::size_t capacity,
    ProcessReport& report
) noexcept {
    if (ledger != nullptr && report.ledger_events_written < capacity) {
        ledger[report.ledger_events_written++] = event;
        return true;
    }
    ++report.ledger_events_dropped;
    ++diagnostics_.ledger_overflows;
    return false;
}

float Core::advanceTransition(
    LedgerEvent* ledger,
    std::size_t ledger_capacity,
    ProcessReport& report
) noexcept {
    if (transition_ == TransitionState::running || transition_ == TransitionState::panic_latched) {
        return transition_gain_;
    }
    if (transition_total_ == 0) {
        transition_gain_ = transition_target_;
    } else {
        ++transition_elapsed_;
        const float unit = std::min(1.0f,
            static_cast<float>(transition_elapsed_) / static_cast<float>(transition_total_));
        transition_gain_ = transition_start_ + (transition_target_ - transition_start_) * unit;
    }
    if (transition_elapsed_ < transition_total_) return transition_gain_;

    if (transition_ == TransitionState::reset_down) {
        clearSignalState();
        for (std::size_t index = 0; index < smoothed_.size(); ++index) {
            smoothed_[index].reset(accepted_[index]);
        }
        energy_automation_ = {};
        appendLedger({absolute_frame_, 0, LedgerKind::reset_boundary}, ledger, ledger_capacity, report);
        beginTransition(TransitionState::reset_up, 1.0f,
            static_cast<std::uint32_t>(std::llround(0.005 * sample_rate_)));
    } else if (transition_ == TransitionState::reset_up || transition_ == TransitionState::panic_up) {
        transition_ = TransitionState::running;
        transition_gain_ = 1.0f;
    } else if (transition_ == TransitionState::panic_down) {
        transition_ = TransitionState::panic_latched;
        transition_gain_ = 0.0f;
        appendLedger({absolute_frame_, 0, LedgerKind::panic_boundary}, ledger, ledger_capacity, report);
    }
    return transition_gain_;
}

void Core::registerNonFinite() noexcept {
    ++diagnostics_.non_finite_samples;
    if (non_finite_count_ < non_finite_frames_.size()) {
        non_finite_frames_[non_finite_count_++] = absolute_frame_;
    } else {
        non_finite_frames_[0] = non_finite_frames_[1];
        non_finite_frames_[1] = non_finite_frames_[2];
        non_finite_frames_[2] = absolute_frame_;
    }
    if (non_finite_count_ == non_finite_frames_.size()
        && non_finite_frames_[2] - non_finite_frames_[0] < static_cast<std::uint64_t>(sample_rate_)) {
        ++diagnostics_.panic_count;
        beginTransition(TransitionState::panic_down, 0.0f,
            static_cast<std::uint32_t>(std::llround(0.010 * sample_rate_)));
    }
}

double Core::pulseWindow(double width, double edge, double rate_hz, bool& onset) noexcept {
    onset = false;
    if (rate_hz <= 0.0 || !std::isfinite(rate_hz)) {
        pulse_was_active_ = false;
        pulse_onset_pending_ = false;
        return 0.0;
    }
    if (!pulse_was_active_ || pulse_onset_pending_) {
        onset = true;
        pulse_onset_pending_ = false;
    }
    pulse_was_active_ = true;
    const double duty = 0.08 + 0.34 * std::clamp(width, 0.0, 1.0);
    const double requested_edge_seconds = (1.5 + 10.5 * edge * edge) * 0.001;
    const double edge_phase = std::min(requested_edge_seconds * rate_hz, 0.45 * duty);
    double pulse = 0.0;
    if (pulse_phase_ < duty) {
        if (edge_phase <= 0.0) {
            pulse = 1.0;
        } else if (pulse_phase_ < edge_phase) {
            pulse = raisedCosine(pulse_phase_ / edge_phase);
        } else if (pulse_phase_ > duty - edge_phase) {
            pulse = raisedCosine((duty - pulse_phase_) / edge_phase);
        } else {
            pulse = 1.0;
        }
    }
    pulse_phase_ += rate_hz / sample_rate_;
    if (pulse_phase_ >= 1.0) {
        pulse_phase_ -= std::floor(pulse_phase_);
        pulse_onset_pending_ = true;
    }
    return std::clamp(pulse, 0.0, 1.0);
}

ProcessReport Core::process(
    float* output_left,
    float* output_right,
    std::uint32_t frames,
    const Event* events,
    std::size_t event_count,
    LedgerEvent* ledger,
    std::size_t ledger_capacity
) noexcept {
    ProcessReport report{};
    if (!prepared_ || output_left == nullptr || output_right == nullptr || frames == 0
        || frames > maximum_block_frames_ || (event_count > 0 && events == nullptr)) {
        ++diagnostics_.unsupported_process_calls;
        if (output_left != nullptr && output_right != nullptr) {
            for (std::uint32_t frame = 0; frame < frames; ++frame) {
                output_left[frame] = 0.0f;
                output_right[frame] = 0.0f;
            }
        }
        return report;
    }

    const std::size_t bounded_events = std::min(event_count, kMaximumEventsPerBlock);
    report.dropped_events = event_count - bounded_events;
    diagnostics_.dropped_events += report.dropped_events;
    std::size_t next_event = 0;
    std::uint32_t previous_offset = 0;
    std::uint64_t previous_sequence = 0;
    bool has_previous = false;

    for (std::uint32_t frame = 0; frame < frames; ++frame) {
        while (next_event < bounded_events && events[next_event].sample_offset == frame) {
            const auto& event = events[next_event];
            const bool ordered = !has_previous
                || event.sample_offset > previous_offset
                || (event.sample_offset == previous_offset && event.ingress_sequence >= previous_sequence);
            if (!ordered) {
                ++report.dropped_events;
                ++diagnostics_.dropped_events;
                ++diagnostics_.invalid_events;
            } else if (applyEvent(event)) {
                ++report.accepted_events;
                ++diagnostics_.accepted_events;
                LedgerEvent row{};
                row.sample_index = absolute_frame_;
                row.ingress_sequence = event.ingress_sequence;
                row.kind = event.kind == EventKind::action
                    ? LedgerKind::accepted_action : LedgerKind::accepted_control;
                row.control = event.control;
                row.action = event.action;
                row.value = event.value;
                row.pulse_index = static_cast<std::uint8_t>(accepted_[indexOf(ControlId::pulse)]);
                row.pulse_phase = pulse_phase_;
                appendLedger(row, ledger, ledger_capacity, report);
            } else {
                ++report.dropped_events;
                ++diagnostics_.dropped_events;
            }
            previous_offset = event.sample_offset;
            previous_sequence = event.ingress_sequence;
            has_previous = true;
            ++next_event;
        }

        if (energy_automation_.active) {
            if (absolute_frame_ >= energy_automation_.end_frame) {
                accepted_[indexOf(ControlId::energy)] = energy_automation_.end_value;
                smoothed_[indexOf(ControlId::energy)].target = energy_automation_.end_value;
                energy_automation_.active = false;
            } else {
                const double unit = static_cast<double>(absolute_frame_ - energy_automation_.start_frame)
                    / static_cast<double>(energy_automation_.end_frame - energy_automation_.start_frame);
                const double value = energy_automation_.start_value
                    + (energy_automation_.end_value - energy_automation_.start_value) * unit;
                accepted_[indexOf(ControlId::energy)] = value;
                smoothed_[indexOf(ControlId::energy)].target = value;
            }
        }

        std::array<double, 11> control{};
        for (std::size_t index = 0; index < smoothed_.size(); ++index) {
            control[index] = smoothed_[index].next();
        }
        const double energy = control[indexOf(ControlId::energy)];
        const double break_depth = control[indexOf(ControlId::break_depth)];
        const double tick_amount = control[indexOf(ControlId::tick)];
        const double root = control[indexOf(ControlId::root)];
        const double color = control[indexOf(ControlId::color)];
        const double width = control[indexOf(ControlId::width)];
        const double edge = control[indexOf(ControlId::edge)];
        const double space = control[indexOf(ControlId::space)];
        const double output = control[indexOf(ControlId::output)];
        const double tempo = control[indexOf(ControlId::tempo)];
        const auto pulse_index = static_cast<std::size_t>(std::clamp(
            std::llround(accepted_[indexOf(ControlId::pulse)]), 0LL, 7LL));

        const double semitones = 36.0 * std::pow(std::clamp(energy, 0.0, 1.0), 1.15);
        wire_frequency_hz_ = std::clamp(
            82.4069 * std::pow(2.0, (root + semitones) / 12.0), 55.0, 1800.0);
        const auto harmonics = static_cast<std::uint32_t>(std::clamp(
            std::floor(20000.0 / wire_frequency_hz_), 1.0, 24.0));
        const double slope = std::clamp(2.40 - 1.50 * energy - 0.45 * color, 0.55, 2.40);
        double wire = 0.0;
        double norm_power = 0.0;
        for (std::uint32_t harmonic = 1; harmonic <= harmonics; ++harmonic) {
            const double amplitude = std::pow(static_cast<double>(harmonic), -slope);
            wire += amplitude * std::sin(
                static_cast<double>(harmonic) * oscillator_phase_
                + 0.17 * static_cast<double>(harmonic % 4U));
            norm_power += amplitude * amplitude;
        }
        wire /= std::sqrt(std::max(0.5 * norm_power, 1.0e-12));

        const double tracked = 2.0 + 7.0 * energy;
        const auto lower_harmonic = static_cast<std::uint32_t>(std::floor(tracked));
        const auto upper_harmonic = static_cast<std::uint32_t>(std::ceil(tracked));
        const double fraction = tracked - std::floor(tracked);
        double squeal = 0.0;
        if (lower_harmonic >= 1U && lower_harmonic <= harmonics) {
            squeal += std::cos(0.5 * kPi * fraction)
                * std::sin(static_cast<double>(lower_harmonic) * oscillator_phase_ + 0.31);
        }
        if (upper_harmonic >= 1U && upper_harmonic <= harmonics) {
            squeal += std::sin(0.5 * kPi * fraction)
                * std::sin(static_cast<double>(upper_harmonic) * oscillator_phase_ + 0.31);
        }
        const double squeal_mix = std::clamp(0.08 + 0.32 * energy + 0.25 * color, 0.0, 0.65);
        const double source = (1.0 - squeal_mix) * wire + squeal_mix * (1.41421356237 * squeal);

        if (coefficient_countdown_ == 0) {
            const double cutoff = std::min(18000.0,
                wire_frequency_hz_ * (2.0 + 5.0 * energy + 2.0 * color));
            const double q = 1.1 + 5.5 * energy * energy * (0.3 + 0.7 * color);
            const double g = std::tan(kPi * cutoff / sample_rate_);
            if (std::isfinite(g) && g >= 0.0 && std::isfinite(q) && q > 0.0) {
                svf_g_ = g;
                svf_k_ = 1.0 / q;
            }
            coefficient_countdown_ = 16;
        }
        --coefficient_countdown_;
        const double a1 = 1.0 / (1.0 + svf_g_ * (svf_g_ + svf_k_));
        const double v1 = a1 * svf_ic1_ + a1 * svf_g_ * (source - svf_ic2_);
        const double v2 = svf_ic2_ + svf_g_ * v1;
        svf_ic1_ = 2.0 * v1 - svf_ic1_;
        svf_ic2_ = 2.0 * v2 - svf_ic2_;
        const double q = 1.0 / std::max(svf_k_, 1.0e-9);
        const double colored = 0.82 * source + 0.18 * v1 / std::sqrt(q);
        const double energy_gain = 0.16 * std::pow(10.0, 3.0 * energy / 20.0);
        const double dry = energy_gain * colored;
        const double dc_coefficient = std::exp(-2.0 * kPi * 12.0 / sample_rate_);
        const double clean_left = dc_left_.process(dry, dc_coefficient);
        const double clean_right = dc_right_.process(dry, dc_coefficient);

        const double delayed_left = delay_left_[delay_left_write_];
        const double delayed_right = delay_right_[delay_right_write_];
        delay_left_[delay_left_write_] = static_cast<float>(finiteOrZero(
            clean_left + 0.20 * space * delayed_right));
        delay_right_[delay_right_write_] = static_cast<float>(finiteOrZero(
            clean_right + 0.20 * space * delayed_left));
        delay_left_write_ = (delay_left_write_ + 1U) % delay_left_frames_;
        delay_right_write_ = (delay_right_write_ + 1U) % delay_right_frames_;
        const double spaced_left = clean_left + 0.18 * space * delayed_left;
        const double spaced_right = clean_right + 0.18 * space * delayed_right;

        const double rate_hz = kPulseRatesPerBeat[pulse_index] * tempo / 60.0;
        bool onset = false;
        const double pulse = pulseWindow(width, edge, rate_hz, onset);
        if (onset) {
            tick_frame_ = 0;
            ++diagnostics_.pulse_onsets;
            LedgerEvent row{};
            row.sample_index = absolute_frame_;
            row.kind = LedgerKind::pulse_onset;
            row.pulse_index = static_cast<std::uint8_t>(pulse_index);
            row.pulse_phase = pulse_phase_;
            appendLedger(row, ledger, ledger_capacity, report);
        }
        const double main_gain = force_open_ ? 1.0 : 1.0 - break_depth * pulse;
        double tick = 0.0;
        if (tick_frame_ < tick_length_) {
            const double unit = static_cast<double>(tick_frame_)
                / static_cast<double>(tick_length_ - 1U);
            const double window = std::sin(kPi * unit);
            tick = 0.24 * tick_amount * std::sqrt(std::max(0.0, break_depth))
                * std::sin(8.0 * kPi * unit) * window * window;
            ++tick_frame_;
        }

        const float safety_gain = advanceTransition(ledger, ledger_capacity, report);
        double left = output * (main_gain * spaced_left + tick) * safety_gain;
        double right = output * (main_gain * spaced_right + tick) * safety_gain;
        if (!std::isfinite(left) || !std::isfinite(right)) {
            registerNonFinite();
            left = 0.0;
            right = 0.0;
        }
        if (std::abs(left) > kOutputCeiling || std::abs(right) > kOutputCeiling) {
            ++diagnostics_.safety_clamps;
            left = std::clamp(left, -static_cast<double>(kOutputCeiling), static_cast<double>(kOutputCeiling));
            right = std::clamp(right, -static_cast<double>(kOutputCeiling), static_cast<double>(kOutputCeiling));
        }
        output_left[frame] = static_cast<float>(left);
        output_right[frame] = static_cast<float>(right);

        oscillator_phase_ += 2.0 * kPi * wire_frequency_hz_ / sample_rate_;
        if (oscillator_phase_ >= 2.0 * kPi) oscillator_phase_ -= 2.0 * kPi;
        ++absolute_frame_;
        ++diagnostics_.processed_frames;
    }

    while (next_event < bounded_events) {
        ++report.dropped_events;
        ++diagnostics_.dropped_events;
        ++diagnostics_.invalid_events;
        ++next_event;
    }
    return report;
}

Snapshot Core::snapshot() const noexcept {
    Snapshot result{};
    result.absolute_frame = absolute_frame_;
    result.accepted_controls = accepted_;
    for (std::size_t index = 0; index < smoothed_.size(); ++index) {
        result.smoothed_controls[index] = smoothed_[index].current;
    }
    result.wire_frequency_hz = wire_frequency_hz_;
    result.oscillator_phase = oscillator_phase_;
    result.pulse_phase = pulse_phase_;
    result.tick_frame = tick_frame_;
    result.pulse_index = static_cast<std::uint8_t>(accepted_[indexOf(ControlId::pulse)]);
    result.open_held = force_open_;
    result.panic_latched = transition_ == TransitionState::panic_latched;
    result.transition = transition_;
    result.transition_gain = transition_gain_;
    result.delay_write_heads = {delay_left_write_, delay_right_write_};
    return result;
}

}  // namespace wirefall::r02
