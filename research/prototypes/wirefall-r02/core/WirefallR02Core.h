#pragma once

#include "WirefallR02Controls.h"

#include <array>
#include <cstddef>
#include <cstdint>

namespace wirefall::r02 {

inline constexpr double kExperimentSampleRate = 48000.0;
inline constexpr std::uint32_t kMaximumBlockFrames = 512;
inline constexpr std::size_t kMaximumEventsPerBlock = 128;
inline constexpr float kOutputCeiling = 0.8912f;
inline constexpr std::size_t kMaximumDelayFrames = 3008;
inline constexpr std::uint32_t kTickFramesAt48k = 384;

enum class EventKind : std::uint8_t {
    set_control,
    linear_control,
    action,
};

struct Event {
    std::uint32_t sample_offset{};
    std::uint64_t ingress_sequence{};
    EventKind kind{EventKind::set_control};
    ControlId control{ControlId::energy};
    ActionId action{ActionId::unsupported};
    double value{};
    double end_value{};
    std::uint64_t duration_frames{};
};

enum class LedgerKind : std::uint8_t {
    accepted_control,
    accepted_action,
    pulse_onset,
    reset_boundary,
    panic_boundary,
};

struct LedgerEvent {
    std::uint64_t sample_index{};
    std::uint64_t ingress_sequence{};
    LedgerKind kind{LedgerKind::accepted_control};
    ControlId control{ControlId::energy};
    ActionId action{ActionId::unsupported};
    double value{};
    std::uint8_t pulse_index{};
    double pulse_phase{};
};

struct Diagnostics {
    std::uint64_t processed_frames{};
    std::uint64_t accepted_events{};
    std::uint64_t dropped_events{};
    std::uint64_t invalid_events{};
    std::uint64_t unknown_actions{};
    std::uint64_t ledger_overflows{};
    std::uint64_t pulse_onsets{};
    std::uint64_t reset_count{};
    std::uint64_t panic_count{};
    std::uint64_t non_finite_controls{};
    std::uint64_t non_finite_samples{};
    std::uint64_t safety_clamps{};
    std::uint64_t unsupported_process_calls{};
};

enum class TransitionState : std::uint8_t {
    running,
    reset_down,
    reset_up,
    panic_down,
    panic_latched,
    panic_up,
};

struct Snapshot {
    std::uint64_t absolute_frame{};
    std::array<double, 11> accepted_controls{};
    std::array<double, 11> smoothed_controls{};
    double wire_frequency_hz{};
    double oscillator_phase{};
    double pulse_phase{};
    std::uint32_t tick_frame{};
    std::uint8_t pulse_index{};
    bool open_held{};
    bool panic_latched{};
    TransitionState transition{TransitionState::running};
    float transition_gain{1.0f};
    std::array<std::size_t, 2> delay_write_heads{};
};

struct ProcessReport {
    std::size_t accepted_events{};
    std::size_t dropped_events{};
    std::size_t ledger_events_written{};
    std::size_t ledger_events_dropped{};
};

class Core final {
public:
    Core() noexcept;

    Core(const Core&) = delete;
    Core& operator=(const Core&) = delete;

    bool prepare(double sample_rate, std::uint32_t maximum_block_frames = kMaximumBlockFrames) noexcept;
    void initialize() noexcept;

    ProcessReport process(
        float* output_left,
        float* output_right,
        std::uint32_t frames,
        const Event* events = nullptr,
        std::size_t event_count = 0,
        LedgerEvent* ledger = nullptr,
        std::size_t ledger_capacity = 0
    ) noexcept;

    bool setControlValue(ControlId id, double value) noexcept;
    bool triggerAction(ActionId id) noexcept;

    [[nodiscard]] bool isPrepared() const noexcept { return prepared_; }
    [[nodiscard]] double sampleRate() const noexcept { return sample_rate_; }
    [[nodiscard]] Snapshot snapshot() const noexcept;
    [[nodiscard]] Diagnostics diagnostics() const noexcept { return diagnostics_; }
    [[nodiscard]] static constexpr std::size_t stateBytes() noexcept { return sizeof(Core); }

private:
    struct Smoothed {
        double current{};
        double target{};
        double coefficient{};
        void configure(double milliseconds, double sample_rate) noexcept;
        void reset(double value) noexcept;
        double next() noexcept;
    };

    struct Automation {
        bool active{};
        std::uint64_t start_frame{};
        std::uint64_t end_frame{};
        double start_value{};
        double end_value{};
    };

    struct DcBlocker {
        double previous_input{};
        double previous_output{};
        void clear() noexcept;
        double process(double input, double coefficient) noexcept;
    };

    bool prepared_{};
    double sample_rate_{kExperimentSampleRate};
    std::uint32_t maximum_block_frames_{kMaximumBlockFrames};
    Diagnostics diagnostics_{};
    std::array<double, 11> accepted_{};
    std::array<Smoothed, 11> smoothed_{};
    Automation energy_automation_{};

    double oscillator_phase_{};
    double pulse_phase_{};
    double svf_ic1_{};
    double svf_ic2_{};
    double svf_g_{};
    double svf_k_{};
    std::uint32_t coefficient_countdown_{};
    double wire_frequency_hz_{82.4069};

    std::array<float, kMaximumDelayFrames> delay_left_{};
    std::array<float, kMaximumDelayFrames> delay_right_{};
    std::size_t delay_left_write_{};
    std::size_t delay_right_write_{};
    std::size_t delay_left_frames_{1104};
    std::size_t delay_right_frames_{1488};
    DcBlocker dc_left_{};
    DcBlocker dc_right_{};

    std::uint32_t tick_frame_{kTickFramesAt48k};
    std::uint32_t tick_length_{kTickFramesAt48k};
    bool pulse_was_active_{};
    bool pulse_onset_pending_{};
    bool force_open_{};

    TransitionState transition_{TransitionState::running};
    std::uint32_t transition_elapsed_{};
    std::uint32_t transition_total_{};
    float transition_start_{1.0f};
    float transition_target_{1.0f};
    float transition_gain_{1.0f};

    std::array<std::uint64_t, 3> non_finite_frames_{};
    std::size_t non_finite_count_{};
    std::uint64_t absolute_frame_{};

    void resetDefaults(bool clear_diagnostics) noexcept;
    void clearSignalState() noexcept;
    bool applyControl(ControlId id, double value) noexcept;
    bool applyAction(ActionId id) noexcept;
    bool applyEvent(const Event& event) noexcept;
    void beginTransition(TransitionState state, float target, std::uint32_t frames) noexcept;
    float advanceTransition(LedgerEvent* ledger, std::size_t ledger_capacity, ProcessReport& report) noexcept;
    bool appendLedger(const LedgerEvent& event, LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    void registerNonFinite() noexcept;
    double pulseWindow(double width, double edge, double rate_hz, bool& onset) noexcept;
};

}  // namespace wirefall::r02
