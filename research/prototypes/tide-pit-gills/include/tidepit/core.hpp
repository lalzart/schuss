#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>

namespace tidepit {

inline constexpr double kReferenceSampleRate = 48000.0;
inline constexpr std::uint32_t kReferenceQuantumFrames = 16;
inline constexpr std::uint32_t kMaximumBlockFrames = 512;
inline constexpr std::size_t kMaximumSemanticEvents = 128;
inline constexpr std::size_t kSourceArenaBytes = 251408;
inline constexpr std::size_t kSourceArenaAllocations = 5;

enum class SourceMode : std::uint8_t { reed, rnd, fold };
enum class ScaleMode : std::uint8_t { maj5, min5, dorian, harm };
enum class EffectMode : std::uint8_t { clean, filter, drive };
enum class WaveTarget : std::uint8_t { pitch, body, grain, all };

// Continuous actions carry a normalized value, except set_root, whose event
// value is an actual MIDI note in the inclusive range 36..72. Discrete actions
// ignore value and enter the exact source gesture synthesizer.
enum class SemanticAction : std::uint8_t {
    set_stage_1,
    set_stage_2,
    set_stage_3,
    set_stage_4,
    set_rate,
    set_memory,
    set_material,
    set_position,
    set_fx_a,
    set_fx_b,
    set_root,
    source_next,
    mutate,
    lock_toggle,
    effect_next,
    capture_toggle,
    scale_next,
    target_next,
};

struct SemanticEvent {
    std::uint32_t sample_offset{};
    std::uint64_t ingress_sequence{};
    SemanticAction action{SemanticAction::set_stage_1};
    double value{};
};

struct Controls {
    std::array<float, 4> stages{{0.20f, 0.50f, 0.80f, 0.30f}};
    float rate{0.55f};
    float memory{0.78f};
    float material{0.50f};
    float position{0.31f};
    float fx_a{0.60f};
    float fx_b{0.35f};
    std::int32_t root_note{60};
};

struct Diagnostics {
    std::uint64_t processed_frames{};
    std::uint64_t processed_quanta{};
    std::uint64_t semantic_events_accepted{};
    std::uint64_t semantic_events_dropped{};
    std::uint64_t invalid_events{};
    std::uint64_t non_finite_controls{};
    std::uint64_t unsupported_process_calls{};
    std::uint64_t prepare_failures{};
    std::uint64_t manual_mutations{};
    std::uint64_t gesture_queue_overflows{};
    std::uint32_t pending_events{};
    std::uint32_t arena_allocations{};
    std::uint32_t arena_bytes{};
    bool arena_alignment_valid{};
};

struct Snapshot {
    Controls controls{};
    std::array<std::array<float, 2>, 3> effect_parameters{{
        {{0.50f, 0.50f}},
        {{0.65f, 0.25f}},
        {{0.50f, 0.25f}},
    }};
    std::array<std::int8_t, 4> mutation{{0, 0, 0, 0}};
    std::array<std::array<char, 22>, 4> display_lines{};
    float effective_fx_a{0.50f};
    float effective_fx_b{0.50f};
    float effect_crossfade{1.0f};
    std::uint64_t absolute_sample{};
    std::int32_t record_write_head{};
    std::uint8_t stage{};
    std::uint8_t sympathetic_division{2};
    SourceMode source{SourceMode::reed};
    ScaleMode scale{ScaleMode::maj5};
    EffectMode effect{EffectMode::clean};
    WaveTarget target{WaveTarget::pitch};
    bool locked{};
    bool captured{};
    bool fx_a_pickup_active{true};
    bool fx_b_pickup_active{true};
    bool granular_available{};
    bool prepared{};
};

struct ProcessReport {
    std::size_t events_accepted{};
    std::size_t events_dropped{};
};

class Core final {
public:
    Core();
    ~Core();

    Core(const Core&) = delete;
    Core& operator=(const Core&) = delete;
    Core(Core&&) noexcept;
    Core& operator=(Core&&) noexcept;

    // Preparation is deliberately source-exact: only 48 kHz and maximum
    // callback sizes that are non-zero multiples of 16 up to 512 are accepted.
    bool prepare(
        double sample_rate,
        std::uint32_t maximum_block_frames = kMaximumBlockFrames
    ) noexcept;

    // Events are block-relative. They are ordered by quantized absolute sample
    // then ingress_sequence; ceil-to-16 quantization means an event already on
    // a source boundary affects that quantum before source processing. Events
    // landing on the block end remain in the fixed queue for the next call.
    ProcessReport processQ27(
        std::int32_t* output_left,
        std::int32_t* output_right,
        std::uint32_t frames,
        const SemanticEvent* events = nullptr,
        std::size_t event_count = 0
    ) noexcept;

    // Adapter convenience for continuous controls only. set_root maps a
    // normalized value to MIDI 36..72. This method is not a physical-controller
    // observation and must not race processQ27 on the same Core instance.
    bool setControlNormalized(SemanticAction action, double normalized) noexcept;

    [[nodiscard]] Snapshot snapshot() const noexcept;
    [[nodiscard]] Diagnostics diagnostics() const noexcept;
    [[nodiscard]] bool isPrepared() const noexcept;
    [[nodiscard]] double sampleRate() const noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

[[nodiscard]] const std::array<std::int8_t, 6>& scaleIntervals(ScaleMode scale) noexcept;
[[nodiscard]] const char* sourceName(SourceMode source) noexcept;
[[nodiscard]] const char* scaleName(ScaleMode scale) noexcept;
[[nodiscard]] const char* effectName(EffectMode effect) noexcept;
[[nodiscard]] const char* targetName(WaveTarget target) noexcept;

}  // namespace tidepit
