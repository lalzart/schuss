#include "schuss/generative_drum_machine/core.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace gdm = schuss::generative_drum_machine;

namespace {

int failures = 0;

void check(bool condition, const char* expression, int line) {
    if (!condition) {
        std::cerr << "line " << line << ": check failed: " << expression << '\n';
        ++failures;
    }
}

#define CHECK(expression) check((expression), #expression, __LINE__)

gdm::RenderRequest baseRequest() {
    gdm::RenderRequest request{};
    request.condition_id = "test";
    request.controls.complexity = {{42000U, 36000U, 34000U, 30000U, 26000U, 22000U}};
    return request;
}

using EventIdentity = std::tuple<
    std::uint32_t, std::uint32_t, std::uint8_t, std::uint32_t>;

std::set<EventIdentity> identities(const std::vector<gdm::DrumHit>& hits) {
    std::set<EventIdentity> result;
    for (const auto& hit : hits) {
        result.emplace(
            hit.phrase_index,
            hit.source_ordinal,
            static_cast<std::uint8_t>(hit.lane),
            hit.variation_group);
    }
    return result;
}

void testRationalTimeline() {
    CHECK(gdm::rationalPositionToFrame(0U, 0U, {0U, 1U}, 120000U, 0U) == 0U);
    CHECK(gdm::rationalPositionToFrame(0U, 0U, {1U, 1U}, 120000U, 0U) == 24000U);
    CHECK(gdm::rationalPositionToFrame(0U, 0U, {1U, 3U}, 120000U, 0U) == 8000U);
    CHECK(gdm::rationalPositionToFrame(0U, 0U, {1U, 5U}, 120000U, 0U) == 4800U);
    // A late 4/4 event can still use an exact half-quarter position.
    CHECK(gdm::rationalPositionToFrame(0U, 0U, {7U, 2U}, 120000U, 0U) == 84000U);
    const auto straight = gdm::rationalPositionToFrame(0U, 0U, {1U, 2U}, 120000U, 0U);
    const auto swung = gdm::rationalPositionToFrame(0U, 0U, {1U, 2U}, 120000U, 32767U);
    CHECK(straight == 12000U);
    CHECK(swung == 16000U);
    bool rejected = false;
    try {
        static_cast<void>(
            gdm::rationalPositionToFrame(0U, 0U, {2U, 4U}, 120000U, 0U));
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    CHECK(rejected);
}

void testRhythmBankMeters() {
    const std::array<std::tuple<const char*, std::uint8_t, std::uint8_t, std::uint8_t, std::uint64_t>, 15>
        expected{{
            {"First Light", 4U, 4U, 4U, 384000U},
            {"Three Turn", 3U, 4U, 4U, 288000U},
            {"Rolling Six", 6U, 8U, 4U, 288000U},
            {"Five Across", 5U, 4U, 2U, 240000U},
            {"Samba Enredo Study", 2U, 4U, 4U, 192000U},
            {"Partido Alto Study", 2U, 4U, 4U, 192000U},
            {"Samba de Roda Study", 2U, 4U, 4U, 192000U},
            {"Samba-Reggae Study", 4U, 4U, 4U, 384000U},
            {"Maracatu Pulse Study", 4U, 4U, 4U, 384000U},
            {"Candombe Conversation", 4U, 4U, 2U, 192000U},
            {"Chacarera Cross-Meter", 6U, 8U, 4U, 288000U},
            {"Aksak Five Study", 5U, 8U, 4U, 240000U},
            {"Aksak Seven Study", 7U, 8U, 4U, 336000U},
            {"Aksak Nine Study", 9U, 8U, 4U, 432000U},
            {"Jhaptal Cycle Study", 10U, 8U, 2U, 240000U},
        }};
    std::set<std::string> ids;
    std::set<std::pair<std::uint8_t, std::uint8_t>> meters;
    for (std::uint8_t index = 0U; index < gdm::kRhythmPresetCount; ++index) {
        const auto info = gdm::rhythmPresetInfo(index);
        CHECK(std::string{info.name} == std::get<0>(expected[index]));
        CHECK(info.meter_numerator == std::get<1>(expected[index]));
        CHECK(info.note_value_denominator == std::get<2>(expected[index]));
        CHECK(info.phrase_bars == std::get<3>(expected[index]));
        CHECK(std::string{info.id}.size() > 2U);
        CHECK(std::string{info.family}.size() > 2U);
        CHECK(std::string{info.grouping}.size() > 2U);
        CHECK(std::string{info.source_relationship}.size() > 8U);
        CHECK(!info.authenticity_claim);
        ids.insert(info.id);
        meters.emplace(info.meter_numerator, info.note_value_denominator);
        CHECK(gdm::phraseFrameCount(index, 120000U) == std::get<4>(expected[index]));

        auto request = baseRequest();
        request.phrase_count = 1U;
        request.controls.rhythm_preset = index;
        const auto hits = gdm::generateHits(request);
        CHECK(!hits.empty());
        CHECK(std::all_of(hits.begin(), hits.end(), [&](const gdm::DrumHit& hit) {
            return hit.absolute_frame < gdm::phraseFrameCount(index, 120000U);
        }));
    }
    CHECK(ids.size() == gdm::kRhythmPresetCount);
    CHECK(meters.size() >= 5U);
    CHECK(gdm::rhythmPositionToFrame(1U, 0U, 0U, {1U, 1U}, 120000U, 0U) == 24000U);
    CHECK(gdm::rhythmPositionToFrame(2U, 0U, 0U, {3U, 2U}, 120000U, 0U) == 36000U);
    CHECK(gdm::rhythmPositionToFrame(3U, 0U, 0U, {21U, 5U}, 120000U, 0U) == 100800U);
    bool rejected = false;
    try {
        static_cast<void>(
            gdm::rhythmPositionToFrame(1U, 0U, 0U, {3U, 1U}, 120000U, 0U));
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    CHECK(rejected);
}

void testMonotoneComplexity() {
    auto low = baseRequest();
    low.controls.complexity.fill(12000U);
    low.controls.enthusiasm = 0U;
    auto high = low;
    high.controls.complexity.fill(52000U);
    const auto low_set = identities(gdm::generateHits(low));
    const auto high_set = identities(gdm::generateHits(high));
    CHECK(low_set.size() < high_set.size());
    CHECK(std::includes(
        high_set.begin(), high_set.end(), low_set.begin(), low_set.end()));
}

void testStaticPhraseRepeat() {
    auto request = baseRequest();
    request.controls.enthusiasm = 0U;
    const auto hits = gdm::generateHits(request);
    const auto phrase_frames = gdm::phraseFrameCount(
        request.controls.rhythm_preset, request.controls.tempo_milli_bpm);
    std::array<std::vector<std::tuple<std::uint64_t, std::uint8_t, std::uint32_t>>, 3> normalized;
    for (const auto& hit : hits) {
        normalized.at(hit.phrase_index).emplace_back(
            hit.absolute_frame - hit.phrase_index * phrase_frames,
            static_cast<std::uint8_t>(hit.lane),
            hit.source_ordinal);
    }
    CHECK(normalized[0] == normalized[1]);
    CHECK(normalized[1] == normalized[2]);
    CHECK(std::all_of(hits.begin(), hits.end(), [](const gdm::DrumHit& hit) {
        return hit.variation_group == 0U;
    }));
}

void testEnthusiasmIsPhraseCoherent() {
    auto request = baseRequest();
    request.controls.complexity.fill(65535U);
    request.controls.enthusiasm = 65535U;
    const auto first = gdm::generateHits(request);
    const auto second = gdm::generateHits(request);
    CHECK(first.size() == second.size());
    CHECK(std::equal(first.begin(), first.end(), second.begin(), second.end(),
        [](const gdm::DrumHit& left, const gdm::DrumHit& right) {
            return left.absolute_frame == right.absolute_frame
                && left.lane == right.lane
                && left.source_ordinal == right.source_ordinal
                && left.variation_group == right.variation_group;
        }));
    for (std::uint32_t phrase = 0; phrase < request.phrase_count; ++phrase) {
        std::set<std::uint8_t> groups;
        for (const auto& hit : first) {
            if (hit.phrase_index == phrase && hit.variation_group != 0U) {
                groups.insert(hit.variation_group);
            }
        }
        CHECK(groups.size() <= 1U);
    }
}

void testPhraseIndexOffset() {
    auto request = baseRequest();
    request.phrase_count = 1U;
    request.phrase_index_offset = 17U;
    request.controls.enthusiasm = 65535U;
    const auto hits = gdm::generateHits(request);
    CHECK(!hits.empty());
    CHECK(std::all_of(hits.begin(), hits.end(), [](const gdm::DrumHit& hit) {
        return hit.phrase_index == 17U;
    }));
    CHECK(hits.front().absolute_frame < gdm::phraseFrameCount(
        request.controls.rhythm_preset, request.controls.tempo_milli_bpm));

    auto repeated = request;
    CHECK(identities(gdm::generateHits(request)) == identities(gdm::generateHits(repeated)));
}

void testAllocatorAndOuterBlockInvariance() {
    gdm::RenderRequest small{};
    small.condition_id = "allocator-stress";
    small.mode = gdm::GeneratorMode::allocator_stress;
    small.phrase_count = 1U;
    small.outer_block_frames = 1U;
    auto large = small;
    large.outer_block_frames = 511U;
    const auto first = gdm::render(small);
    const auto second = gdm::render(large);
    CHECK(first.left_q27 == second.left_q27);
    CHECK(first.right_q27 == second.right_q27);
    CHECK(first.allocations.size() == 8U);
    CHECK(first.metrics.dropped_hit_count == 2U);
    CHECK(first.metrics.choked_voice_count == 2U);
    CHECK(first.metrics.overflow_count == 0U);
    CHECK(first.allocations[0].voice_index == 0);
    CHECK(first.allocations[1].voice_index == 1);
    CHECK(first.allocations[2].voice_index == 2);
    CHECK(first.allocations[3].voice_index == 3);
    CHECK(first.allocations[4].action == gdm::AllocationAction::drop);
    CHECK(first.allocations[5].action == gdm::AllocationAction::drop);
    CHECK(first.allocations[6].action == gdm::AllocationAction::choke);
    CHECK(first.allocations[7].action == gdm::AllocationAction::choke);
}

void testPublicRecipeBoundary() {
    const auto& recipes = gdm::laneRecipes();
    CHECK(recipes.size() == gdm::kLogicalLaneCount);
    CHECK(recipes[0].priority > recipes[1].priority);
    CHECK(recipes[1].priority > recipes[2].priority);
    CHECK(recipes[2].choke_group == 1U);
    CHECK(!gdm::presetFingerprint().empty());

    gdm::Controls neutral{};
    const auto neutral_resolved = gdm::resolvedLaneRecipes(neutral);
    CHECK(neutral_resolved[0].base_pitch_q7 == recipes[0].base_pitch_q7);
    CHECK(neutral_resolved[0].timbre_u15 == recipes[0].timbre_u15);
    CHECK(neutral_resolved[0].color_u15 == recipes[0].color_u15);
    CHECK(neutral_resolved[0].amp_decay_multiplier_q31
        == recipes[0].amp_decay_multiplier_q31);
    CHECK(neutral_resolved[0].pitch_env_amount_q7 == recipes[0].pitch_env_amount_q7);
    CHECK(neutral_resolved[0].timbre_env_amount_s15 == recipes[0].timbre_env_amount_s15);
    CHECK(neutral_resolved[0].gain_q15 == recipes[0].gain_q15);

    auto shaped = neutral;
    shaped.voice_shapes[1].tune_u7 = 127U;
    shaped.voice_shapes[1].timbre_u7 = 0U;
    shaped.voice_shapes[1].color_u7 = 127U;
    shaped.voice_shapes[1].decay_u7 = 127U;
    shaped.voice_shapes[1].pitch_env_u7 = 0U;
    shaped.voice_shapes[1].level_u7 = 0U;
    const auto shaped_resolved = gdm::resolvedLaneRecipes(shaped);
    CHECK(shaped_resolved[0].base_pitch_q7 == recipes[0].base_pitch_q7);
    CHECK(shaped_resolved[1].base_pitch_q7 > recipes[1].base_pitch_q7);
    CHECK(shaped_resolved[1].timbre_u15 <= recipes[1].timbre_u15);
    CHECK(shaped_resolved[1].color_u15 >= recipes[1].color_u15);
    CHECK(shaped_resolved[1].amp_decay_multiplier_q31
        > recipes[1].amp_decay_multiplier_q31);
    CHECK(shaped_resolved[1].pitch_env_amount_q7 < recipes[1].pitch_env_amount_q7);
    CHECK(shaped_resolved[1].timbre_env_amount_s15 == recipes[1].timbre_env_amount_s15);
    CHECK(shaped_resolved[1].gain_q15 == 0U);

    auto request = baseRequest();
    request.phrase_count = 1U;
    const auto original = gdm::render(request);
    request.controls.voice_shapes[1].tune_u7 = 127U;
    const auto changed = gdm::render(request);
    CHECK(original.hits.size() == changed.hits.size());
    CHECK(original.allocations.size() == changed.allocations.size());
    CHECK(original.left_q27 != changed.left_q27);
}

std::vector<std::int32_t> renderStreamingTimeline(std::size_t block_frames) {
    gdm::Controls controls{};
    controls.complexity.fill(65535U);
    controls.enthusiasm = 0U;
    controls.tempo_milli_bpm = 240000U;
    controls.rhythm_preset = 12U;
    gdm::StreamingEngine engine{0x53434855U};
    constexpr std::size_t total_frames = 32000U;
    std::vector<std::int32_t> stereo;
    stereo.reserve(total_frames * 2U);
    std::array<std::int32_t, gdm::kMaximumStreamingBlockFrames> left{};
    std::array<std::int32_t, gdm::kMaximumStreamingBlockFrames> right{};
    for (std::size_t cursor = 0U; cursor < total_frames;) {
        const auto count = std::min(block_frames, total_frames - cursor);
        gdm::StreamingProcessReport report{};
        CHECK(engine.process(
            controls, 0U, left.data(), right.data(), count, &report));
        CHECK(report.diagnostic_overflow_count == 0U);
        for (std::size_t frame = 0U; frame < count; ++frame) {
            stereo.push_back(left[frame]);
            stereo.push_back(right[frame]);
        }
        cursor += count;
    }
    return stereo;
}

void testStreamingBlockPartitionAndRealtimeControl() {
    const auto small = renderStreamingTimeline(64U);
    const auto large = renderStreamingTimeline(512U);
    CHECK(small == large);
    CHECK(std::any_of(small.begin(), small.end(), [](std::int32_t sample) {
        return sample != 0;
    }));

    gdm::Controls controls{};
    controls.complexity.fill(65535U);
    controls.tempo_milli_bpm = 240000U;
    controls.rhythm_preset = 0U;
    gdm::StreamingEngine engine{99U};
    std::array<std::int32_t, 512> left{};
    std::array<std::int32_t, 512> right{};
    gdm::StreamingProcessReport report{};
    CHECK(engine.process(controls, 0U, left.data(), right.data(), 137U, &report));
    const auto restart_frame = engine.absoluteFrame();
    controls.rhythm_preset = 12U;
    CHECK(engine.process(controls, 0U, left.data(), right.data(), 64U, &report));
    CHECK(report.hit_count > 0U);
    CHECK(report.hits[0].absolute_frame == restart_frame);
    CHECK(report.hits[0].phrase_index == 0U);

    controls.rhythm_preset = 11U;
    CHECK(engine.process(controls, 1U, left.data(), right.data(), 64U, &report));
    bool observed_fill = false;
    for (std::size_t remaining = 30000U; remaining > 0U && !observed_fill;) {
        const auto count = std::min<std::size_t>(remaining, left.size());
        CHECK(engine.process(controls, 1U, left.data(), right.data(), count, &report));
        for (std::size_t index = 0U; index < report.hit_count; ++index) {
            observed_fill = observed_fill
                || report.hits[index].variation_group == 100U;
        }
        remaining -= count;
    }
    CHECK(observed_fill);
}

std::vector<std::int32_t> renderShapeResponse(bool change_shape) {
    gdm::Controls controls{};
    controls.complexity.fill(65535U);
    controls.tempo_milli_bpm = 240000U;
    gdm::StreamingEngine engine{12345U};
    std::array<std::int32_t, 512> left{};
    std::array<std::int32_t, 512> right{};
    CHECK(engine.process(controls, 0U, left.data(), right.data(), 256U));
    if (change_shape) {
        controls.voice_shapes[0].tune_u7 = 127U;
        controls.voice_shapes[0].decay_u7 = 8U;
        controls.voice_shapes[0].level_u7 = 96U;
    }
    CHECK(engine.process(controls, 0U, left.data(), right.data(), 256U));
    std::vector<std::int32_t> result;
    result.reserve(512U);
    for (std::size_t frame = 0U; frame < 256U; ++frame) {
        result.push_back(left[frame]);
        result.push_back(right[frame]);
    }
    return result;
}

void testStreamingShapesAffectSoundingVoice() {
    const auto shaped = renderShapeResponse(true);
    const auto neutral = renderShapeResponse(false);
    CHECK(shaped != neutral);
    CHECK(std::any_of(shaped.begin(), shaped.begin() + 128U,
        [](std::int32_t sample) { return sample != 0; }));
}

}  // namespace

int main() {
    testRationalTimeline();
    testRhythmBankMeters();
    testMonotoneComplexity();
    testStaticPhraseRepeat();
    testEnthusiasmIsPhraseCoherent();
    testPhraseIndexOffset();
    testAllocatorAndOuterBlockInvariance();
    testPublicRecipeBoundary();
    testStreamingBlockPartitionAndRealtimeControl();
    testStreamingShapesAffectSoundingVoice();
    if (failures != 0) {
        std::cerr << failures << " checks failed\n";
        return 1;
    }
    std::cout << "generative drum machine core tests: passed\n";
    return 0;
}
