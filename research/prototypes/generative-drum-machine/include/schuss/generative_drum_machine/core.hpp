#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace schuss::generative_drum_machine {

inline constexpr std::uint32_t kSampleRateHz = 48000;
inline constexpr std::size_t kLogicalLaneCount = 6;
inline constexpr std::size_t kPhysicalVoiceCount = 4;
inline constexpr std::size_t kRhythmPresetCount = 15;
inline constexpr std::size_t kMaximumStreamingBlockFrames = 512;
inline constexpr std::size_t kMaximumStreamingEventsPerBlock = 128;
inline constexpr std::uint32_t kVoiceShapeSlewFrames = 128;

enum class Lane : std::uint8_t {
    kick = 0,
    snare = 1,
    hat = 2,
    percussion_1 = 3,
    percussion_2 = 4,
    percussion_3 = 5,
};

enum class BraidsModel : std::uint8_t {
    kick,
    snare,
    cymbal,
    sine_triangle,
    fm,
    filtered_noise,
};

enum class GeneratorMode : std::uint8_t {
    authored,
    independent_probability_comparator,
    allocator_stress,
};

struct Rational final {
    std::uint32_t numerator{};
    std::uint32_t denominator{1};
};

struct LaneRecipe final {
    BraidsModel model{};
    std::int16_t base_pitch_q7{};
    std::uint16_t timbre_u15{};
    std::uint16_t color_u15{};
    std::int16_t pitch_env_amount_q7{};
    std::int16_t timbre_env_amount_s15{};
    std::int16_t color_env_amount_s15{};
    std::uint32_t amp_decay_multiplier_q31{};
    std::uint32_t transient_decay_multiplier_q31{};
    std::uint16_t gain_q15{};
    std::int16_t pan_s15{};
    std::uint8_t choke_group{};
    std::uint8_t priority{};
};

struct PatternEvent final {
    std::uint8_t bar{};
    Rational position_quarters{};
    Lane lane{};
    std::uint16_t complexity_threshold{};
    std::uint16_t velocity_u15{};
    std::uint8_t articulation{};
    std::uint8_t variation_group{};
    std::uint32_t source_ordinal{};
};

struct VoiceShape final {
    std::uint8_t tune_u7{64};
    std::uint8_t timbre_u7{64};
    std::uint8_t color_u7{64};
    std::uint8_t decay_u7{64};
    std::uint8_t pitch_env_u7{64};
    std::uint8_t level_u7{64};
};

struct Controls final {
    std::array<std::uint16_t, kLogicalLaneCount> complexity{};
    std::uint16_t enthusiasm{};
    std::uint32_t tempo_milli_bpm{120000};
    std::uint16_t swing_u15{};
    std::uint8_t rhythm_preset{};
    std::array<VoiceShape, kLogicalLaneCount> voice_shapes{};
    std::uint8_t selected_voice_lane{};
    bool voice_shaping{};
};

struct RhythmPresetInfo final {
    const char* id{};
    const char* name{};
    const char* family{};
    const char* grouping{};
    const char* source_relationship{};
    std::uint8_t meter_numerator{};
    std::uint8_t note_value_denominator{};
    std::uint8_t phrase_bars{};
    bool authenticity_claim{};
};

struct DrumHit final {
    std::uint64_t absolute_frame{};
    Lane lane{};
    std::uint16_t velocity_u15{};
    std::uint8_t articulation{};
    std::uint32_t source_ordinal{};
    std::uint32_t phrase_index{};
    std::uint8_t variation_group{};
};

enum class AllocationAction : std::uint8_t {
    idle,
    choke,
    tail_reuse,
    steal,
    retrigger,
    drop,
};

struct AllocationDecision final {
    std::uint64_t absolute_frame{};
    std::uint32_t source_ordinal{};
    Lane lane{};
    AllocationAction action{};
    std::int8_t voice_index{-1};
    std::int8_t victim_lane{-1};
};

struct Metrics final {
    std::int32_t peak_absolute_q27{};
    std::int64_t sum_left_q27{};
    std::int64_t sum_right_q27{};
    std::uint64_t frame_count{};
    std::uint32_t overflow_count{};
    std::uint32_t clipped_sample_count{};
    std::uint32_t dropped_hit_count{};
    std::uint32_t stolen_voice_count{};
    std::uint32_t choked_voice_count{};
};

struct RenderRequest final {
    std::string condition_id;
    GeneratorMode mode{GeneratorMode::authored};
    Controls controls{};
    std::uint32_t seed{1396918357U};
    std::uint32_t phrase_count{3};
    std::uint32_t phrase_index_offset{};
    std::int32_t fill_phrase{-1};
    std::size_t outer_block_frames{128};
};

struct RenderResult final {
    std::vector<std::int32_t> left_q27;
    std::vector<std::int32_t> right_q27;
    std::vector<DrumHit> hits;
    std::vector<AllocationDecision> allocations;
    Metrics metrics{};
};

struct StreamingProcessReport final {
    std::uint64_t absolute_frame_start{};
    std::uint64_t absolute_frame_end{};
    std::uint32_t cycle_index{};
    std::uint16_t cycle_progress_u15{};
    std::uint16_t hit_count{};
    std::uint16_t allocation_count{};
    std::uint32_t diagnostic_overflow_count{};
    std::array<DrumHit, kMaximumStreamingEventsPerBlock> hits{};
    std::array<AllocationDecision, kMaximumStreamingEventsPerBlock> allocations{};
};

// Callback-owned, fixed-capacity musical scheduler and four-voice synthesis
// pool. Construction/reset happen while playback is stopped. process() accepts
// one coherent public-control snapshot and performs no allocation, locking, I/O,
// JSON, or UI work.
class StreamingEngine final {
public:
    explicit StreamingEngine(std::uint32_t seed = 1396918357U);
    ~StreamingEngine();

    StreamingEngine(const StreamingEngine&) = delete;
    StreamingEngine& operator=(const StreamingEngine&) = delete;
    StreamingEngine(StreamingEngine&&) noexcept;
    StreamingEngine& operator=(StreamingEngine&&) noexcept;

    void reset(std::uint32_t seed = 1396918357U) noexcept;

    [[nodiscard]] bool process(
        const Controls& controls,
        std::uint64_t fill_request_sequence,
        std::int32_t* left_q27,
        std::int32_t* right_q27,
        std::size_t frame_count,
        StreamingProcessReport* report = nullptr) noexcept;

    [[nodiscard]] std::uint64_t absoluteFrame() const noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

[[nodiscard]] std::uint64_t rationalPositionToFrame(
    std::uint32_t phrase_index,
    std::uint8_t bar,
    Rational position_quarters,
    std::uint32_t tempo_milli_bpm,
    std::uint16_t swing_u15);

[[nodiscard]] std::uint64_t rhythmPositionToFrame(
    std::uint8_t rhythm_preset,
    std::uint32_t phrase_index,
    std::uint8_t bar,
    Rational position_quarters,
    std::uint32_t tempo_milli_bpm,
    std::uint16_t swing_u15);

[[nodiscard]] std::uint64_t phraseFrameCount(
    std::uint8_t rhythm_preset,
    std::uint32_t tempo_milli_bpm);

[[nodiscard]] std::vector<DrumHit> generateHits(const RenderRequest& request);
[[nodiscard]] RenderResult render(const RenderRequest& request);

[[nodiscard]] const char* laneName(Lane lane) noexcept;
[[nodiscard]] const char* allocationActionName(AllocationAction action) noexcept;
[[nodiscard]] const std::array<LaneRecipe, kLogicalLaneCount>& laneRecipes() noexcept;
[[nodiscard]] std::array<LaneRecipe, kLogicalLaneCount> resolvedLaneRecipes(
    const Controls& controls);
[[nodiscard]] RhythmPresetInfo rhythmPresetInfo(std::uint8_t index);
[[nodiscard]] bool sameSoundControls(
    const Controls& left,
    const Controls& right) noexcept;
[[nodiscard]] const std::string& presetFingerprint() noexcept;

}  // namespace schuss::generative_drum_machine
