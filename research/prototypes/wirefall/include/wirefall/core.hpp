#pragma once

#include "wirefall/control_descriptor.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>

namespace wirefall {

inline constexpr double kSampleRate = 48000.0;
inline constexpr std::uint32_t kMaximumBlockFrames = 512;
inline constexpr std::size_t kMaximumEventsPerBlock = 128;
inline constexpr float kOutputCeiling = 0.8912f;
inline constexpr std::uint32_t kWireOversampleFactor = 4;
inline constexpr std::uint32_t kReferenceOversampleFactor = 8;
inline constexpr std::size_t kFrozenFirTaps = 63;
inline constexpr std::size_t kReferenceFirTaps = 127;
inline constexpr std::size_t kMaximumDelaySamples = 4272;

enum class ControlId : std::uint8_t {
    tension,
    cut,
    shadow,
    root,
    bite,
    holes,
    edge,
    under,
    swing,
    space,
    tempo,
};

enum class ActionId : std::uint8_t {
    void_on,
    void_off,
    open_on,
    open_off,
    flip,
    flip_cancel,
    downbeat,
    panic,
    panic_release,
    tap_tempo,
    reset,
    unsupported,
};

enum class EventKind : std::uint8_t {
    set_control,
    linear_control,
    action,
};

enum class SchedulerMode : std::uint8_t {
    error_accumulator,
    phase_locked_square,
};

enum class ShadowMode : std::uint8_t {
    complementary,
    continuous_parallel,
};

struct Configuration {
    SchedulerMode scheduler_mode{SchedulerMode::error_accumulator};
    ShadowMode shadow_mode{ShadowMode::complementary};
    std::uint32_t wire_oversample_factor{kWireOversampleFactor};
    float parallel_shadow_gain{1.0f};
};

struct Event {
    std::uint32_t sample_offset{};
    std::uint64_t ingress_sequence{};
    EventKind kind{EventKind::set_control};
    ControlId control{ControlId::tension};
    ActionId action{ActionId::unsupported};
    double value{};
    double end_value{};
    std::uint64_t duration_frames{};
};

enum class LedgerKind : std::uint8_t {
    accepted_control,
    accepted_action,
    beat_boundary,
    rhythm_commit,
    opportunity,
    containment,
    reset_boundary,
    panic_boundary,
};

struct LedgerEvent {
    std::uint64_t sample_index{};
    std::uint64_t ingress_sequence{};
    LedgerKind kind{LedgerKind::accepted_control};
    ControlId control{ControlId::tension};
    ActionId action{ActionId::unsupported};
    double value{};
    std::uint32_t active_rate_index{};
    std::uint32_t active_holes{};
    std::int32_t scheduler_error{};
    std::uint32_t effective_edge_frames{};
    bool cut{};
};

struct Diagnostics {
    std::uint64_t processed_frames{};
    std::uint64_t accepted_events{};
    std::uint64_t dropped_events{};
    std::uint64_t invalid_events{};
    std::uint64_t unsupported_actions{};
    std::uint64_t beat_boundaries{};
    std::uint64_t rhythm_commits{};
    std::uint64_t opportunity_boundaries{};
    std::uint64_t cut_boundaries{};
    std::uint64_t non_finite_targets{};
    std::uint64_t non_finite_containments{};
    std::uint64_t output_non_finite_clears{};
    std::uint64_t scheduler_repairs{};
    std::uint64_t reset_count{};
    std::uint64_t panic_count{};
    std::uint64_t rejected_during_reset{};
    std::uint64_t ledger_overflows{};
    std::uint64_t unsupported_process_calls{};
};

struct StateSnapshot {
    std::uint64_t absolute_sample{};
    double tension{};
    double shadow{};
    double root{};
    double bite{};
    double edge{};
    double swing{};
    double space{};
    double tempo_bpm{};
    double wire_frequency_hz{};
    double shadow_frequency_hz{};
    double beat_phase{};
    double complement_coordinate{};
    double effective_complement_coordinate{};
    double wire_phase{};
    std::array<double, 2> shadow_phases{};
    std::uint32_t active_rate_index{};
    std::uint32_t pending_rate_index{};
    std::uint32_t active_holes{};
    std::uint32_t pending_holes{};
    std::uint32_t under_index{};
    std::int32_t scheduler_error{};
    std::uint64_t opportunity_index{};
    std::size_t fir_write_index{};
    std::array<std::size_t, 4> delay_write_indices{};
    bool rate_pending{};
    bool holes_pending{};
    bool cut{};
    bool flipped{};
    bool void_active{};
    bool open_active{};
    bool reset_active{};
    bool panic_ramping{};
    bool panic_latched{};
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
    Core(Core&&) = delete;
    Core& operator=(Core&&) = delete;

    bool prepare(
        double sample_rate,
        std::uint32_t maximum_block_frames = kMaximumBlockFrames,
        Configuration configuration = {}
    ) noexcept;
    void initialize() noexcept;

    ProcessReport process(
        float* output_left,
        float* output_right,
        std::uint32_t frames,
        const Event* events = nullptr,
        std::size_t event_count = 0,
        LedgerEvent* ledger_output = nullptr,
        std::size_t ledger_capacity = 0
    ) noexcept;

    bool setControlValue(ControlId control, double value) noexcept;
    bool triggerAction(ActionId action) noexcept;

    [[nodiscard]] bool isPrepared() const noexcept { return prepared_; }
    [[nodiscard]] double sampleRate() const noexcept { return sample_rate_; }
    [[nodiscard]] std::uint32_t maximumBlockFrames() const noexcept { return maximum_block_frames_; }
    [[nodiscard]] const Configuration& configuration() const noexcept { return configuration_; }
    [[nodiscard]] Diagnostics diagnostics() const noexcept { return diagnostics_; }
    [[nodiscard]] StateSnapshot snapshot() const noexcept;
    [[nodiscard]] std::string normalizedStateSha256() const;
    [[nodiscard]] std::string fullStateSha256() const;

    [[nodiscard]] static std::string frozenFirByteSha256();
    [[nodiscard]] static constexpr std::size_t stateBytes() noexcept { return sizeof(Core); }

private:
    struct Smoothed {
        float current{};
        float target{};
        float coefficient{};

        void reset(float value) noexcept;
        void configure(float tau_ms, double sample_rate) noexcept;
        float next() noexcept;
    };

    struct RaisedCosineRamp {
        float current{};
        float start{};
        float target{};
        std::uint32_t total{};
        std::uint32_t elapsed{};

        void reset(float value) noexcept;
        void begin(float value, std::uint32_t frames) noexcept;
        float next() noexcept;
        [[nodiscard]] bool active() const noexcept { return elapsed < total; }
    };

    struct VoiceSpace {
        std::array<float, kMaximumDelaySamples> left{};
        std::array<float, kMaximumDelaySamples> right{};
        std::size_t left_write{};
        std::size_t right_write{};
        float wet_recovery{1.0f};

        void clear() noexcept;
    };

    struct DcBlocker {
        float input_previous{};
        float output_previous{};

        void clear() noexcept;
        float process(float input, float coefficient) noexcept;
    };

    struct Automation {
        bool active{};
        std::uint64_t start_sample{};
        std::uint64_t end_sample{};
        float start_value{};
        float end_value{};

        void clear() noexcept;
    };

    bool prepared_{};
    double sample_rate_{kSampleRate};
    std::uint32_t maximum_block_frames_{kMaximumBlockFrames};
    Configuration configuration_{};
    Diagnostics diagnostics_{};

    Smoothed tension_{};
    Smoothed shadow_{};
    Smoothed root_{};
    Smoothed bite_{};
    Smoothed edge_{};
    Smoothed swing_{};
    Smoothed space_{};
    Automation tension_automation_{};

    std::uint32_t active_rate_index_{};
    std::uint32_t pending_rate_index_{};
    std::uint32_t active_holes_{3};
    std::uint32_t pending_holes_{3};
    std::uint32_t under_index_{2};
    bool rate_pending_{};
    bool holes_pending_{};
    double tempo_bpm_{120.0};

    double wire_phase_{};
    std::array<double, 2> shadow_phase_{};
    std::array<std::uint32_t, 2> shadow_ratio_index_{{2, 2}};
    std::uint32_t active_shadow_slot_{};
    RaisedCosineRamp ratio_crossfade_{};
    std::array<float, 2> shadow_lowpass_{};

    float derived_wire_frequency_{110.0f};
    float derived_fold_gain_{1.0f};
    float derived_q_{0.8f};
    float derived_drive_{1.0f};
    float derived_compensation_{1.0f};
    float svf_a1_{1.0f};
    float svf_a2_{};
    float svf_a3_{};
    float svf_k_{1.25f};
    float svf_ic1_{};
    float svf_ic2_{};

    std::array<float, kReferenceFirTaps> fir_coefficients_{};
    std::array<float, kReferenceFirTaps> fir_ring_{};
    std::size_t fir_taps_{kFrozenFirTaps};
    std::size_t fir_write_{};

    VoiceSpace wire_space_{};
    VoiceSpace shadow_space_{};
    DcBlocker dc_left_{};
    DcBlocker dc_right_{};

    double beat_position_samples_{};
    double next_opportunity_sample_{};
    double square_cut_end_sample_{};
    std::uint64_t opportunity_index_{};
    std::int32_t scheduler_error_{};
    bool opportunity_scheduled_{};
    bool square_end_scheduled_{};
    bool cut_{};
    std::uint32_t current_slot_frames_{24000};
    RaisedCosineRamp complement_{};
    RaisedCosineRamp flip_{};
    RaisedCosineRamp void_override_{};
    RaisedCosineRamp open_override_{};
    bool flip_cancel_pending_{};

    enum class TransitionState : std::uint8_t {
        normal,
        reset_down,
        reset_up,
        panic_down,
        panic_latched,
        panic_up,
    };
    TransitionState transition_{TransitionState::normal};
    RaisedCosineRamp output_transition_{};

    std::array<std::uint64_t, 3> containment_samples_{};
    std::size_t containment_count_{};
    std::array<std::uint64_t, 3> tap_intervals_{};
    std::size_t tap_interval_count_{};
    std::uint64_t last_tap_sample_{};
    bool has_last_tap_{};
    std::uint64_t absolute_sample_{};

    void resetDefaults(bool clear_diagnostics) noexcept;
    void clearSignalState() noexcept;
    void deriveWireCoefficients() noexcept;
    bool applyEvent(const Event& event, ProcessReport& report, LedgerEvent* ledger, std::size_t capacity) noexcept;
    bool applyControl(ControlId control, double value, std::uint64_t ingress_sequence, LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    bool applyAction(ActionId action, std::uint64_t ingress_sequence, LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    void writeLedger(const LedgerEvent& event, LedgerEvent* output, std::size_t capacity, ProcessReport& report) noexcept;
    void onBeatBoundary(LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    void onOpportunity(LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    void onSquareEnd(LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    void scheduleNextOpportunity() noexcept;
    void updateAutomation() noexcept;
    void updateTransition(LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    void contain(std::uint64_t ingress_sequence, LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    float processWire() noexcept;
    float processShadow() noexcept;
    std::array<float, 2> processSpace(VoiceSpace& space, float input, float amount) noexcept;
    std::array<float, 2> processOneSample(LedgerEvent* ledger, std::size_t capacity, ProcessReport& report) noexcept;
    [[nodiscard]] double samplesPerBeat() const noexcept;
    [[nodiscard]] double activeRate() const noexcept;
    [[nodiscard]] std::uint32_t effectiveEdgeFrames() const noexcept;
};

static_assert(sizeof(Core) <= 256U * 1024U, "Wirefall Core exceeds the frozen 256 KiB state budget");

[[nodiscard]] const char* controlName(ControlId control) noexcept;
[[nodiscard]] const char* actionName(ActionId action) noexcept;
[[nodiscard]] const char* ledgerKindName(LedgerKind kind) noexcept;

}  // namespace wirefall
