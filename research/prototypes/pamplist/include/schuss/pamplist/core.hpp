#pragma once

#include "schuss/pamplist/macro_voice.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace schuss::pamplist {

inline constexpr std::uint32_t kSampleRateHz = 48000U;
inline constexpr std::size_t kLaneCount = 7U;
inline constexpr std::size_t kPageCount = 8U;
inline constexpr std::uint8_t kGlobalPageIndex = 7U;
inline constexpr std::size_t kCohesionModeCount = 6U;
inline constexpr std::size_t kDestinationCount = 8U;
inline constexpr std::size_t kRateCount = 16U;
inline constexpr std::size_t kMaximumHostBlockFrames = 512U;
inline constexpr std::size_t kMaximumQuantumEventsPerBlock = 32U;
inline constexpr std::uint32_t kDefaultSeed = UINT32_C(0x50414d50);
inline constexpr std::int32_t kQ27Maximum = (INT32_C(1) << 27) - 1;
inline constexpr std::int32_t kQ27Minimum = -(INT32_C(1) << 27);

struct Rational final {
    std::uint32_t numerator{1U};
    std::uint32_t denominator{1U};
};

enum class Shape : std::uint8_t {
    gate = 0,
    pulse = 1,
    triangle = 2,
    sine = 3,
    ramp = 4,
    exponential_decay = 5,
    sample_hold = 6,
    smooth_random = 7,
};

enum class Destination : std::uint8_t {
    trigger = 0,
    pitch = 1,
    model = 2,
    harmonics = 3,
    timbre = 4,
    morph = 5,
    decay = 6,
    level = 7,
};

enum class LaneControlMode : std::uint8_t {
    voice = 0,
    motion = 1,
};

struct LaneControls final {
    std::uint8_t rate_index{8U};
    std::uint8_t phase_u7{};
    Shape shape{Shape::pulse};
    std::uint8_t hits{4U};
    std::uint8_t rotation{};
    float probability{1.0F};
    std::uint8_t repeat{};
    float amplitude{};
    std::array<float, kDestinationCount> routes{};
};

struct VoiceControls final {
    std::uint8_t engine{};
    float note{48.0F};
    float harmonics{0.5F};
    float timbre{0.5F};
    float morph{0.5F};
    float decay{0.5F};
    float lpg_colour{0.5F};
    float level{0.8F};
};

struct CohesionControls final {
    float drive{};
    float cohere{};
    float root_note{48.0F};
    float spread{};
    float tail{0.5F};
    float damping{0.5F};
    float width{0.5F};
    float duck{};
};

struct Controls final {
    bool running{true};
    std::uint32_t tempo_milli_bpm{120000U};
    std::uint32_t seed{kDefaultSeed};
    float master_gain{0.65F};
    std::uint8_t selected_page{};
    LaneControlMode lane_control_mode{LaneControlMode::voice};
    std::uint32_t effect_clear_generation{};
    CohesionControls cohesion{};
    std::array<LaneControls, kLaneCount> lanes{};
    std::array<VoiceControls, kLaneCount> voices{};
};

struct Diagnostics final {
    std::uint64_t invalid_control_count{};
    std::uint64_t clamped_control_count{};
    std::uint64_t non_finite_source_count{};
    std::uint64_t modulation_clamp_count{};
    std::uint64_t trigger_count{};
    std::array<std::uint64_t, kLaneCount> lane_trigger_count{};
    std::uint64_t saturated_sample_count{};
    std::uint64_t effect_clear_count{};
    std::uint64_t effect_recovery_count{};
    std::uint64_t unsupported_process_count{};
    std::uint64_t panic_count{};
};

struct CohesionSnapshot final {
    float smoothed_master_gain{0.65F};
    float smoothed_drive{};
    float smoothed_cohere{};
    float smoothed_root_note{48.0F};
    float smoothed_spread{};
    float smoothed_tail{0.5F};
    float smoothed_damping{0.5F};
    float smoothed_width{0.5F};
    float smoothed_duck{};
    float duck_envelope{};
    std::array<float, kCohesionModeCount> mode_frequencies_hz{};
    std::array<float, kCohesionModeCount> mode_poles{};
    std::array<float, kCohesionModeCount> mode_real{};
    std::array<float, kCohesionModeCount> mode_imaginary{};
    std::uint32_t applied_clear_generation{};
    double maximum_mode_state_absolute{};
    double maximum_duck_envelope{};
    double dry_difference_energy{};
};

struct Snapshot final {
    Controls accepted{};
    Diagnostics diagnostics{};
    std::uint64_t absolute_frame{};
    std::uint64_t rendered_through_frame{};
    std::uint64_t quantum_count{};
    std::uint64_t accepted_sequence{};
    std::uint64_t master_phase_q32{};
    std::uint64_t master_remainder{};
    std::array<std::uint64_t, kLaneCount> lane_phase_q32{};
    std::array<std::uint64_t, kLaneCount> lane_remainders{};
    std::array<std::uint64_t, kLaneCount> lane_steps{};
    std::array<std::uint64_t, kLaneCount> lane_addresses{};
    std::array<float, kLaneCount> lane_values{};
    // Monotone normalized stereo energy for each post-level, pre-cohesion
    // lane contribution. UI clients difference accepted snapshots rather than
    // reading callback buffers or trying to catch one-quantum peaks.
    std::array<double, kLaneCount> lane_output_energy{};
    std::array<std::array<float, kDestinationCount>, kLaneCount>
        modulation_values{};
    std::uint8_t trigger_lane_mask{};
    std::uint8_t started_lane_mask{};
    std::array<std::uint8_t, kLaneCount> resolved_engines{};
    std::array<float, kLaneCount> resolved_notes{};
    std::array<float, kLaneCount> resolved_harmonics{};
    std::array<float, kLaneCount> resolved_timbres{};
    std::array<float, kLaneCount> resolved_morphs{};
    std::array<float, kLaneCount> resolved_decays{};
    std::array<float, kLaneCount> resolved_lpg_colours{};
    std::array<float, kLaneCount> resolved_levels{};
    std::array<std::uint32_t, kLaneCount> source_random_states{};
    CohesionSnapshot cohesion{};
};

struct QuantumEvent final {
    std::uint64_t absolute_frame{};
    std::uint8_t boundary_mask{};
    std::uint8_t accepted_mask{};
    std::uint8_t trigger_lane_mask{};
    std::uint8_t started_lane_mask{};
    bool effect_cleared{};
    std::uint32_t effect_clear_generation{};
    std::array<std::uint8_t, kLaneCount> resolved_engines{};
    std::array<std::uint64_t, kLaneCount> steps{};
    std::array<std::uint64_t, kLaneCount> addresses{};
};

struct ProcessReport final {
    std::uint64_t absolute_frame_start{};
    std::uint64_t absolute_frame_end{};
    std::uint8_t event_count{};
    std::array<QuantumEvent, kMaximumQuantumEventsPerBlock> events{};
    Snapshot snapshot{};
};

struct SanitizeCounts final {
    std::uint64_t invalid{};
    std::uint64_t clamped{};
};

[[nodiscard]] Controls defaultControls() noexcept;
[[nodiscard]] Controls sanitizeControls(
    const Controls& requested,
    SanitizeCounts* counts = nullptr) noexcept;
[[nodiscard]] bool sameControls(const Controls& left, const Controls& right) noexcept;
[[nodiscard]] const std::array<Rational, kRateCount>& rateTable() noexcept;
[[nodiscard]] const char* shapeName(Shape shape) noexcept;
[[nodiscard]] const char* destinationName(Destination destination) noexcept;
[[nodiscard]] const char* engineName(std::uint8_t engine) noexcept;
[[nodiscard]] const char* modelName(std::uint8_t model) noexcept;
[[nodiscard]] bool euclideanHit(
    std::uint8_t step,
    std::uint8_t hits,
    std::uint8_t rotation) noexcept;
[[nodiscard]] std::uint64_t addressedRandomWord(
    std::uint32_t seed,
    std::uint8_t lane,
    std::uint64_t address,
    std::uint64_t domain) noexcept;
[[nodiscard]] double addressedRandomUnit(
    std::uint32_t seed,
    std::uint8_t lane,
    std::uint64_t address,
    std::uint64_t domain) noexcept;
[[nodiscard]] float shapeValue(
    Shape shape,
    std::uint32_t local_phase_q32,
    double random_a,
    double random_b) noexcept;

// Callback-owned fixed-capacity instrument. reset() and panic() are host-only
// lifecycle calls. process() accepts one coherent Controls value and performs
// no allocation, locking, file I/O, JSON, endpoint, or UI work.
class Core final {
public:
    Core();
    ~Core();

    Core(const Core&) = delete;
    Core& operator=(const Core&) = delete;
    Core(Core&&) noexcept;
    Core& operator=(Core&&) noexcept;

    void reset() noexcept;
    void panic() noexcept;

    [[nodiscard]] bool process(
        const Controls& controls,
        std::int32_t* main_q27,
        std::int32_t* auxiliary_q27,
        std::size_t frame_count,
        ProcessReport* report = nullptr) noexcept;

    [[nodiscard]] const Snapshot& snapshot() const noexcept;

private:
    struct Impl;
    Impl* impl_{};
};

}  // namespace schuss::pamplist
