#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>

namespace wanderbody {

inline constexpr std::uint64_t kDefaultSeed = 0x57414E4445523031ULL;
inline constexpr std::size_t kVoiceCount = 4U;
inline constexpr std::size_t kHistoryCapacity = 8U;
inline constexpr std::size_t kBodyModeCount = 6U;
inline constexpr std::size_t kScopeCapacity = 256U;
inline constexpr std::size_t kMaximumDecisionsPerBlock = 8U;
inline constexpr std::uint32_t kStateVersion = 1U;
inline constexpr double kCaptureSeconds = 8.0;
inline constexpr std::uint32_t kMaximumBlockFrames = 2048U;

enum class MotionMode : std::uint8_t {
    hover = 0,
    drunk = 1,
};

enum class RecurrenceMode : std::uint8_t {
    fresh = 0,
    locked = 1,
    shuffled = 2,
    mutated = 3,
};

enum class GenerationMode : std::uint8_t {
    correlated = 0,
    independent_uniform = 1,
};

enum class ClearPhase : std::uint8_t {
    idle = 0,
    fading_out = 1,
    fading_in = 2,
};

enum class DiagnosticCode : std::uint8_t {
    none = 0,
    unprepared,
    invalid_buffer,
    oversized_block,
    invalid_controls,
    invalid_state,
    numeric_fault,
};

struct Controls final {
    double external{0.85};
    double internal{0.25};
    double anchor{0.55};
    double field{0.22};
    MotionMode motion{MotionMode::hover};
    double wander{0.35};
    RecurrenceMode recurrence{RecurrenceMode::fresh};
    double mutation{0.30};
    double fragment{0.38};
    double energy{0.42};
    double body{0.28};
    double structure{0.42};
    double brightness{0.50};
    double damping{0.48};
    double position{0.33};
    double dry{0.55};
    double memory{0.72};
};

struct ActionSequences final {
    std::uint64_t freeze{};
    std::uint64_t clear{};
    std::uint64_t reset{};
    std::uint64_t panic{};
};

struct DecisionTuple final {
    double position{};
    double duration_seconds{0.20};
    double rate{1.0};
    double gain{0.30};
    double pan{};
    double body_frequency_hz{110.0};
    std::uint8_t direction{1U};
};

struct DecisionEvent final {
    std::uint64_t absolute_frame{};
    std::uint64_t ordinal{};
    std::uint64_t source_epoch{};
    std::uint64_t source_start_frame{};
    DecisionTuple tuple{};
    MotionMode motion{MotionMode::hover};
    RecurrenceMode recurrence{RecurrenceMode::fresh};
    std::uint8_t history_index{255U};
    std::uint8_t voice_index{};
    bool replayed{};
    bool shuffled{};
    bool mutated{};
    bool stolen{};
};

struct ProcessReport final {
    std::array<DecisionEvent, kMaximumDecisionsPerBlock> decisions{};
    std::size_t decision_count{};
    DiagnosticCode diagnostic{DiagnosticCode::none};
};

struct Diagnostics final {
    std::uint64_t processed_frames{};
    std::uint64_t decision_count{};
    std::uint64_t voice_steal_count{};
    std::uint64_t decision_drop_count{};
    std::uint64_t invalid_read_count{};
    std::uint64_t non_finite_input_count{};
    std::uint64_t voice_repair_count{};
    std::uint64_t body_repair_count{};
    std::uint64_t final_fault_count{};
    std::uint64_t rejected_control_count{};
    std::uint64_t rejected_state_count{};
    std::uint64_t freeze_count{};
    std::uint64_t clear_count{};
    std::uint64_t reset_count{};
    std::uint64_t panic_count{};
    std::uint64_t snapshot_sequence{};
    std::uint64_t capture_storage_bytes{};
};

struct Snapshot final {
    Controls accepted_controls{};
    Diagnostics diagnostics{};
    std::array<float, kScopeCapacity> capture_scope{};
    std::array<double, kVoiceCount> active_head_positions{};
    std::uint64_t absolute_frame{};
    std::uint64_t capture_write_frame{};
    std::uint64_t capture_valid_frames{};
    std::uint64_t capture_epoch{};
    std::uint32_t capture_capacity_frames{};
    std::uint8_t history_count{};
    std::uint8_t active_voice_count{};
    MotionMode motion{MotionMode::hover};
    RecurrenceMode recurrence{RecurrenceMode::fresh};
    ClearPhase clear_phase{ClearPhase::idle};
    float clear_gain{1.0F};
    bool frozen{};
    bool prepared{};
    DiagnosticCode latched_fault{DiagnosticCode::none};
};

struct CoreState final {
    std::uint32_t version{kStateVersion};
    Controls controls{};
    std::uint64_t seed{kDefaultSeed};
    std::array<std::uint64_t, 3U> random_states{};
    std::array<std::uint64_t, 3U> random_streams{};
    std::array<DecisionTuple, kHistoryCapacity> history{};
    std::array<std::uint8_t, kHistoryCapacity> permutation{};
    std::uint64_t absolute_frame{};
    std::uint64_t decision_ordinal{};
    std::uint64_t next_launch_countdown{};
    double hover_phase{0.5};
    double hover_direction{1.0};
    double drunk_position{0.55};
    double drunk_velocity{};
    std::uint8_t history_count{};
    std::uint8_t history_write{};
    std::uint8_t recurrence_cursor{};
    std::uint8_t permutation_count{};
    bool frozen{};
    GenerationMode generation_mode{GenerationMode::correlated};
};

[[nodiscard]] Controls defaultControls() noexcept;
[[nodiscard]] bool validControls(const Controls& controls) noexcept;
[[nodiscard]] bool sameControls(const Controls& left, const Controls& right) noexcept;
[[nodiscard]] bool validDecisionTuple(const DecisionTuple& tuple) noexcept;
[[nodiscard]] const char* motionName(MotionMode mode) noexcept;
[[nodiscard]] const char* recurrenceName(RecurrenceMode mode) noexcept;
[[nodiscard]] const char* diagnosticName(DiagnosticCode code) noexcept;

class Core final {
public:
    explicit Core(std::uint64_t seed = kDefaultSeed);
    ~Core();

    Core(const Core&) = delete;
    Core& operator=(const Core&) = delete;
    Core(Core&&) noexcept;
    Core& operator=(Core&&) noexcept;

    [[nodiscard]] bool prepare(
        double sample_rate,
        std::uint32_t maximum_block_frames) noexcept;
    void reset() noexcept;

    [[nodiscard]] ProcessReport process(
        const Controls& controls,
        const ActionSequences& actions,
        const float* input_left,
        const float* input_right,
        float* output_left,
        float* output_right,
        std::uint32_t frame_count) noexcept;

    [[nodiscard]] Snapshot snapshot() const noexcept;
    [[nodiscard]] CoreState captureState() const noexcept;
    [[nodiscard]] bool recallState(const CoreState& state) noexcept;

    void setGenerationMode(GenerationMode mode) noexcept;
    [[nodiscard]] GenerationMode generationMode() const noexcept;
    [[nodiscard]] double sampleRate() const noexcept;
    [[nodiscard]] std::uint32_t maximumBlockFrames() const noexcept;
    [[nodiscard]] bool isPrepared() const noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}  // namespace wanderbody
