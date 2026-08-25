#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>

namespace schuss::murmur_map {

constexpr std::uint32_t kSampleRateHz = 48000U;
constexpr std::size_t kMaximumBlockFrames = 512U;
constexpr std::size_t kMaximumWaypoints = 8U;
constexpr std::size_t kDefaultWaypointCount = 4U;
constexpr std::size_t kLaneCount = 3U;
constexpr std::size_t kMaximumRouteMemory = 32U;
constexpr std::size_t kMaximumEventsPerBlock = 64U;
constexpr std::size_t kUiRouteTraceCapacity = 64U;
constexpr std::uint64_t kDefaultSeed = 0x4d55524d41503031ULL;

enum class Lane : std::uint8_t {
    anchor,
    thread,
    spark,
};

enum class Scale : std::uint8_t {
    chromatic,
    major,
    natural_minor,
    dorian,
    mixolydian,
    major_pentatonic,
    minor_pentatonic,
    whole_tone,
    octatonic_half_whole,
};

enum class GenerationMode : std::uint8_t {
    route_memory,
    independent_white_scene,
};

enum class DiagnosticCode : std::uint8_t {
    none,
    invalid_controls,
    invalid_state,
    invalid_buffer,
    oversized_block,
    numeric_fault,
    event_capacity,
};

struct LaneState final {
    std::int16_t interval_semitones{};
    std::uint16_t activity_u15{};
    std::uint16_t timbre_u15{};
    std::uint16_t color_u15{};
    std::uint16_t decay_ms{40U};
    std::int32_t level_milli_db{-60000};
    std::int16_t pan_s15{};
};

struct Waypoint final {
    std::uint32_t id{};
    std::uint16_t x_u15{};
    std::uint16_t y_u15{};
    std::array<LaneState, kLaneCount> lanes{};
};

struct Controls final {
    bool run{true};
    std::uint32_t tempo_milli_bpm{120000U};
    std::uint32_t travel_milli_quarters{500U};
    std::uint16_t memory_u15{};
    std::uint8_t memory_length{16U};
    std::uint16_t roam_u15{};
    std::uint16_t home_u15{};
    std::uint16_t radius_u15{};
    std::uint16_t density_u15{};
    std::uint8_t root_midi_note{48U};
    Scale scale{Scale::minor_pentatonic};
    std::uint8_t waypoint_count{static_cast<std::uint8_t>(kDefaultWaypointCount)};
    std::uint8_t home_index{};
    std::array<Waypoint, kMaximumWaypoints> waypoints{};
};

struct ActionSequences final {
    std::uint64_t reset{};
    std::uint64_t panic{};
    std::uint64_t reseed{};
    std::uint64_t reseed_value{kDefaultSeed};
};

struct RouteTraceEvent final {
    std::uint64_t absolute_frame{};
    std::uint32_t from_id{};
    std::uint32_t to_id{};
    std::uint8_t memory_slot{};
    bool replayed{};
    bool replaced{};
    bool dwell{};
};

struct MusicalEvent final {
    std::uint64_t absolute_frame{};
    Lane lane{Lane::anchor};
    std::uint32_t pitch_waypoint_id{};
    std::uint8_t pitch_midi{};
    std::uint16_t timbre_u15{};
    std::uint16_t color_u15{};
    std::uint16_t decay_ms{};
    std::int32_t level_milli_db{};
    std::int16_t pan_s15{};
};

struct ProcessReport final {
    std::uint64_t absolute_frame_start{};
    std::array<RouteTraceEvent, kMaximumEventsPerBlock> route_events{};
    std::size_t route_event_count{};
    std::array<MusicalEvent, kMaximumEventsPerBlock> musical_events{};
    std::size_t musical_event_count{};
    DiagnosticCode diagnostic{DiagnosticCode::none};
};

struct Snapshot final {
    Controls accepted_controls{};
    std::uint64_t absolute_frame{};
    std::uint16_t route_x_u15{};
    std::uint16_t route_y_u15{};
    std::uint16_t route_progress_u15{};
    std::uint8_t current_index{};
    std::uint8_t destination_index{};
    std::uint8_t memory_head{};
    std::array<std::uint32_t, kMaximumRouteMemory> route_memory{};
    std::array<bool, kMaximumRouteMemory> route_memory_valid{};
    std::array<std::uint32_t, kUiRouteTraceCapacity> route_trace_ids{};
    std::uint8_t route_trace_count{};
    std::array<std::uint16_t, kLaneCount> envelope_u15{};
    std::array<std::uint64_t, kLaneCount> lane_event_counts{};
    std::uint64_t route_transition_count{};
    std::uint64_t dropped_event_count{};
    std::uint64_t repair_count{};
    std::uint64_t clamp_count{};
    std::uint64_t panic_count{};
    std::uint64_t control_epoch{};
    DiagnosticCode latched_fault{DiagnosticCode::none};
};

struct CoreState final {
    std::uint32_t version{1U};
    Controls controls{};
    std::uint64_t seed{kDefaultSeed};
    std::array<std::uint64_t, 4U> random_states{};
    std::array<std::uint64_t, 4U> random_streams{};
    std::array<std::uint32_t, kMaximumRouteMemory> route_memory{};
    std::array<bool, kMaximumRouteMemory> route_memory_valid{};
    std::uint8_t memory_head{};
    std::uint32_t current_id{};
    std::uint32_t destination_id{};
    std::uint8_t edge_memory_slot{};
    bool edge_replayed{};
    bool edge_replaced{};
    std::uint64_t route_elapsed_q32{};
    std::uint64_t route_duration_q32{};
    std::uint64_t musical_time_q32{};
    std::uint64_t tempo_remainder{};
    std::uint64_t next_thread_q32{};
    std::uint64_t next_spark_q32{};
    std::uint64_t next_control_tick_q32{};
    std::uint64_t absolute_frame{};
    bool reseed_pending{};
    std::uint64_t pending_reseed_value{kDefaultSeed};
    std::array<std::uint64_t, kLaneCount> lane_event_counts{};
    std::uint64_t route_transition_count{};
    std::uint64_t dropped_event_count{};
    std::uint64_t repair_count{};
    std::uint64_t control_epoch{};
    GenerationMode generation_mode{GenerationMode::route_memory};
};

[[nodiscard]] Controls defaultControls() noexcept;
[[nodiscard]] bool validControls(const Controls& controls) noexcept;
[[nodiscard]] bool sameControls(const Controls& left, const Controls& right) noexcept;
[[nodiscard]] const char* scaleName(Scale scale) noexcept;
[[nodiscard]] const char* laneName(Lane lane) noexcept;

class Core final {
public:
    explicit Core(std::uint64_t seed = kDefaultSeed);
    ~Core();
    Core(const Core&) = delete;
    Core& operator=(const Core&) = delete;
    Core(Core&&) noexcept;
    Core& operator=(Core&&) noexcept;

    [[nodiscard]] bool process(
        const Controls& controls,
        const ActionSequences& actions,
        float* left,
        float* right,
        std::size_t frame_count,
        ProcessReport* report = nullptr) noexcept;

    [[nodiscard]] Snapshot snapshot() const noexcept;
    [[nodiscard]] CoreState captureState() const noexcept;
    [[nodiscard]] bool recallState(const CoreState& state) noexcept;
    void setGenerationMode(GenerationMode mode) noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}  // namespace schuss::murmur_map
