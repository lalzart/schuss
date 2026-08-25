#pragma once

#include "schuss/pamplist/activity_model.hpp"
#include "schuss/pamplist/core.hpp"
#include "tidepit/core.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string_view>

namespace layerwell {

inline constexpr double kSampleRate = 48000.0;
inline constexpr std::uint32_t kSourceQuantumFrames = 16U;
inline constexpr std::uint32_t kMaximumBlockFrames = 512U;
inline constexpr std::uint32_t kMinimumLoopFrames = 24000U;
inline constexpr std::uint32_t kMaximumLoopFrames = 1536000U;
inline constexpr std::size_t kLayerCount = 3U;
inline constexpr std::size_t kStoreCount = 4U;
inline constexpr std::size_t kMaximumEvents = 128U;
inline constexpr std::size_t kSampleStorageBytes =
    kStoreCount * 2U * kMaximumLoopFrames * sizeof(float);
inline constexpr std::uint32_t kSeamFrames = 128U;
inline constexpr std::uint32_t kDeterministicSeed = 0x4C415952U;
inline constexpr std::size_t kTideScopeSamples = 256U;
inline constexpr std::size_t kPamplistImpactHistorySamples = 64U;
inline constexpr std::int32_t kTrimFineStepFrames = 48;
inline constexpr std::int32_t kTrimCoarseStepFrames = 480;

enum class SourceId : std::uint8_t {
    tide_pit = 0,
    pamplist = 1,
};

enum class CaptureState : std::uint8_t {
    idle = 0,
    waiting_boundary = 1,
    recording = 2,
};

enum class SurfaceMode : std::uint8_t {
    mixer = 0,
    control = 1,
};

enum class EventKind : std::uint8_t {
    source_previous,
    source_next,
    select_source,
    layer_previous,
    layer_next,
    select_layer,
    source_encoder_relative,
    source_encoder_absolute,
    source_surface_value,
    source_button,
    source_toggle_run,
    source_set_context,
    source_clear_effect,
    adjust_layer_pan,
    adjust_layer_level,
    adjust_monitor_level,
    adjust_master_level,
    adjust_trim_start,
    adjust_trim_end,
    set_layer_pan,
    set_layer_level,
    set_monitor_level,
    set_master_level,
    set_trim_start,
    set_trim_end,
    reset_trim,
    toggle_layer_mute,
    capture_press,
    toggle_monitor,
    clear_selected_layer,
    set_surface_mode,
    panic,
};

// Relative controls carry a raw 7-bit value with pivot 64. Absolute continuous
// controls carry their declared normalized or signed value. `index` is zero
// based. Events are block-relative and apply before the addressed sample.
struct Event final {
    std::uint32_t sample_offset{};
    std::uint64_t ingress_sequence{};
    EventKind kind{EventKind::capture_press};
    std::uint8_t index{};
    double value{};
};

struct LayerSnapshot final {
    float level{0.45f};
    float pan{};
    std::uint32_t recorded_length_frames{};
    std::uint32_t playback_offset_frames{};
    std::uint8_t store_owner{};
    bool occupied{};
    bool muted{};
};

struct TideScopeSnapshot final {
    std::array<float, kTideScopeSamples> left{};
    std::array<float, kTideScopeSamples> right{};
    std::uint64_t generation{};
    std::uint16_t sample_count{};
    float peak_left{};
    float peak_right{};
};

struct PamplistImpactHistorySnapshot final {
    std::array<schuss::pamplist::ActivitySample, kPamplistImpactHistorySamples>
        samples{};
    std::uint64_t generation{};
    std::uint8_t sample_count{};
};

struct SourcePanelSnapshot final {
    tidepit::Snapshot tide_pit{};
    schuss::pamplist::Snapshot pamplist{};
    TideScopeSnapshot tide_scope{};
    PamplistImpactHistorySnapshot pamplist_impact{};
};

struct Diagnostics final {
    std::uint64_t processed_frames{};
    std::uint64_t accepted_events{};
    std::uint64_t dropped_events{};
    std::uint64_t rejected_events{};
    std::uint64_t source_events_quantized{};
    std::uint64_t source_process_failures{};
    std::uint64_t non_finite_source_samples{};
    std::uint64_t non_finite_mix_samples{};
    std::uint64_t limited_samples{};
    std::uint64_t capture_starts{};
    std::uint64_t capture_arms{};
    std::uint64_t capture_commits{};
    std::uint64_t capture_cancels{};
    std::uint64_t capture_aborts{};
    std::uint64_t short_capture_rejections{};
    std::uint64_t unsupported_process_calls{};
    std::uint64_t prepare_failures{};
    std::uint64_t panic_count{};
    std::uint64_t cleared_layers{};
    std::uint64_t trim_accepts{};
    std::uint64_t trim_resets{};
    std::uint64_t trim_rejections{};
    std::uint64_t trim_locked_rejections{};
    std::uint64_t trim_non_finite_rejections{};
    std::uint64_t playback_invariant_faults{};
    std::uint64_t snapshot_sequence{};
    std::uint64_t sample_storage_bytes{};
};

struct Snapshot final {
    std::array<LayerSnapshot, kLayerCount> layers{};
    std::array<std::uint8_t, 16> source_encoder_values{};
    std::array<bool, 16> source_encoder_assigned{};
    std::array<std::string_view, 16> source_encoder_labels{};
    std::array<std::string_view, 16> source_encoder_tooltips{};
    std::array<bool, 8> source_button_assigned{};
    std::array<bool, 8> source_button_active{};
    std::array<std::string_view, 8> source_button_labels{};
    std::array<std::uint64_t, 2> source_processed_frames{};
    SourcePanelSnapshot source_panel{};
    Diagnostics diagnostics{};
    std::uint64_t absolute_frame{};
    std::uint64_t accepted_sequence{};
    std::uint32_t loop_length_frames{};
    std::uint32_t phase_frames{};
    std::uint32_t capture_write_head{};
    std::uint32_t trim_start_frames{};
    std::uint32_t trim_end_frames{};
    std::uint32_t trim_extent_frames{};
    float monitor_level{0.35f};
    float master_level{0.55f};
    SourceId selected_source{SourceId::tide_pit};
    SourceId capture_source{SourceId::tide_pit};
    CaptureState capture_state{CaptureState::idle};
    SurfaceMode surface_mode{SurfaceMode::mixer};
    std::uint8_t selected_layer{};
    std::uint8_t capture_layer{};
    std::uint8_t occupied_layer_count{};
    bool monitor_enabled{true};
    bool trim_available{};
    bool prepared{};
};

struct ProcessReport final {
    std::size_t events_accepted{};
    std::size_t events_dropped{};
    std::size_t events_rejected{};
    bool capture_aborted{};
    bool source_failed{};
};

class Core final {
public:
    Core();
    ~Core();

    Core(const Core&) = delete;
    Core& operator=(const Core&) = delete;
    Core(Core&&) noexcept;
    Core& operator=(Core&&) noexcept;

    // Preparation is intentionally desktop-only and exact: 48 kHz, a nonzero
    // multiple-of-16 maximum block no larger than 512, and 49,152,000 bytes of
    // preallocated sample storage.
    bool prepare(
        double sample_rate = kSampleRate,
        std::uint32_t maximum_block_frames = kMaximumBlockFrames) noexcept;

    // Reset is a stopped-host operation. It zeroes all sample stores and
    // reconstructs both exact source states without reallocating loop storage.
    bool reset() noexcept;

    ProcessReport process(
        float* output_left,
        float* output_right,
        std::uint32_t frames,
        const Event* events = nullptr,
        std::size_t event_count = 0U) noexcept;

    [[nodiscard]] Snapshot snapshot() const noexcept;
    [[nodiscard]] Diagnostics diagnostics() const noexcept;
    [[nodiscard]] bool isPrepared() const noexcept;
    [[nodiscard]] std::uint32_t maximumBlockFrames() const noexcept;

    // Test/evidence seam: hashes and pointer-owner assertions use sample bytes
    // without exposing mutable storage to hosts.
    [[nodiscard]] const float* committedSamples(
        std::size_t layer,
        std::size_t channel) const noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

[[nodiscard]] const char* sourceName(SourceId source) noexcept;
[[nodiscard]] const char* captureStateName(CaptureState state) noexcept;
[[nodiscard]] const char* surfaceModeName(SurfaceMode mode) noexcept;

}  // namespace layerwell
