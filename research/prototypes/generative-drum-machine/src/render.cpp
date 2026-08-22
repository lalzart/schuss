#include "schuss/generative_drum_machine/core.hpp"

#include "schuss/instrument_lab/renderer_artifacts.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace fs = std::filesystem;
namespace gdm = schuss::generative_drum_machine;

namespace {

void appendU16(std::vector<std::uint8_t>& bytes, std::uint16_t value) {
    bytes.push_back(static_cast<std::uint8_t>(value & 0xffU));
    bytes.push_back(static_cast<std::uint8_t>((value >> 8U) & 0xffU));
}

void appendU32(std::vector<std::uint8_t>& bytes, std::uint32_t value) {
    for (std::uint32_t shift = 0; shift < 32U; shift += 8U) {
        bytes.push_back(static_cast<std::uint8_t>((value >> shift) & 0xffU));
    }
}

void appendTag(std::vector<std::uint8_t>& bytes, std::string_view tag) {
    bytes.insert(bytes.end(), tag.begin(), tag.end());
}

[[nodiscard]] std::vector<std::uint8_t> makeWav(const gdm::RenderResult& result) {
    if (result.left_q27.size() != result.right_q27.size()) {
        throw std::logic_error("channel length mismatch");
    }
    const auto sample_bytes = result.left_q27.size() * 2U * sizeof(std::int32_t);
    if (sample_bytes > 0xffffffffU - 36U) {
        throw std::length_error("WAV exceeds RIFF32 capacity");
    }
    std::vector<std::uint8_t> bytes;
    bytes.reserve(44U + sample_bytes);
    appendTag(bytes, "RIFF");
    appendU32(bytes, static_cast<std::uint32_t>(36U + sample_bytes));
    appendTag(bytes, "WAVE");
    appendTag(bytes, "fmt ");
    appendU32(bytes, 16U);
    appendU16(bytes, 1U);
    appendU16(bytes, 2U);
    appendU32(bytes, gdm::kSampleRateHz);
    appendU32(bytes, gdm::kSampleRateHz * 2U * sizeof(std::int32_t));
    appendU16(bytes, static_cast<std::uint16_t>(2U * sizeof(std::int32_t)));
    appendU16(bytes, 32U);
    appendTag(bytes, "data");
    appendU32(bytes, static_cast<std::uint32_t>(sample_bytes));
    for (std::size_t frame = 0; frame < result.left_q27.size(); ++frame) {
        appendU32(bytes, static_cast<std::uint32_t>(result.left_q27[frame]));
        appendU32(bytes, static_cast<std::uint32_t>(result.right_q27[frame]));
    }
    return bytes;
}

void writeBytes(const fs::path& path, const std::vector<std::uint8_t>& bytes) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream.write(
            reinterpret_cast<const char*>(bytes.data()),
            static_cast<std::streamsize>(bytes.size()))) {
        throw std::runtime_error("failed to write " + path.string());
    }
}

void writeText(const fs::path& path, const std::string& text) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream.write(text.data(), static_cast<std::streamsize>(text.size()))) {
        throw std::runtime_error("failed to write " + path.string());
    }
}

[[nodiscard]] std::string eventTrace(
    const std::string& condition,
    const gdm::RenderRequest& request,
    const std::vector<gdm::DrumHit>& hits) {
    const auto rhythm = gdm::rhythmPresetInfo(request.controls.rhythm_preset);
    std::string json = "{\"condition\":\""
        + schuss::instrument_lab::jsonEscape(condition)
        + "\",\"events\":[";
    for (std::size_t index = 0; index < hits.size(); ++index) {
        const auto& hit = hits[index];
        if (index != 0U) {
            json += ',';
        }
        json += "{\"articulation\":" + std::to_string(hit.articulation)
            + ",\"frame\":" + std::to_string(hit.absolute_frame)
            + ",\"lane\":\"" + gdm::laneName(hit.lane)
            + "\",\"phrase\":" + std::to_string(hit.phrase_index)
            + ",\"source_ordinal\":" + std::to_string(hit.source_ordinal)
            + ",\"variation_group\":" + std::to_string(hit.variation_group)
            + ",\"velocity_u15\":" + std::to_string(hit.velocity_u15) + '}';
    }
    json += "],\"meter\":\"" + std::to_string(rhythm.meter_numerator)
        + "/" + std::to_string(rhythm.note_value_denominator)
        + "\",\"preset_fingerprint\":\"" + gdm::presetFingerprint()
        + "\",\"rhythm_index\":" + std::to_string(request.controls.rhythm_preset)
        + ",\"rhythm_name\":\"" + schuss::instrument_lab::jsonEscape(rhythm.name)
        + "\",\"schema_version\":\"schuss-drum-hit-trace-prototype-v0\"}\n";
    return json;
}

[[nodiscard]] std::string allocatorTrace(
    const std::string& condition,
    const std::vector<gdm::AllocationDecision>& decisions) {
    std::string json = "{\"condition\":\""
        + schuss::instrument_lab::jsonEscape(condition)
        + "\",\"decisions\":[";
    for (std::size_t index = 0; index < decisions.size(); ++index) {
        const auto& decision = decisions[index];
        if (index != 0U) {
            json += ',';
        }
        json += "{\"action\":\"" + std::string{gdm::allocationActionName(decision.action)}
            + "\",\"frame\":" + std::to_string(decision.absolute_frame)
            + ",\"lane\":\"" + gdm::laneName(decision.lane)
            + "\",\"source_ordinal\":" + std::to_string(decision.source_ordinal)
            + ",\"victim_lane\":" + std::to_string(decision.victim_lane)
            + ",\"voice\":" + std::to_string(decision.voice_index) + '}';
    }
    json += "],\"schema_version\":\"schuss-drum-allocator-trace-prototype-v0\"}\n";
    return json;
}

[[nodiscard]] std::string metricsJson(
    const std::string& condition,
    const gdm::Metrics& metrics,
    std::size_t event_count) {
    const std::int64_t left_dc = metrics.frame_count == 0U
        ? 0
        : metrics.sum_left_q27 / static_cast<std::int64_t>(metrics.frame_count);
    const std::int64_t right_dc = metrics.frame_count == 0U
        ? 0
        : metrics.sum_right_q27 / static_cast<std::int64_t>(metrics.frame_count);
    const auto dc_absolute = std::max(
        left_dc < 0 ? -left_dc : left_dc,
        right_dc < 0 ? -right_dc : right_dc);
    return "{\"choked_voice_count\":" + std::to_string(metrics.choked_voice_count)
        + ",\"clipped_sample_count\":" + std::to_string(metrics.clipped_sample_count)
        + ",\"condition\":\"" + schuss::instrument_lab::jsonEscape(condition)
        + "\",\"dc_mean_absolute_q27\":" + std::to_string(dc_absolute)
        + ",\"dropped_hit_count\":" + std::to_string(metrics.dropped_hit_count)
        + ",\"event_count\":" + std::to_string(event_count)
        + ",\"frame_count\":" + std::to_string(metrics.frame_count)
        + ",\"overflow_count\":" + std::to_string(metrics.overflow_count)
        + ",\"peak_absolute_q27\":" + std::to_string(metrics.peak_absolute_q27)
        + ",\"schema_version\":\"schuss-drum-render-metrics-prototype-v0\""
        + ",\"stolen_voice_count\":" + std::to_string(metrics.stolen_voice_count)
        + "}\n";
}

[[nodiscard]] gdm::RenderRequest requestFor(
    const std::string& condition,
    std::size_t block_frames) {
    gdm::RenderRequest request{};
    request.condition_id = condition;
    request.outer_block_frames = block_frames;
    if (condition == "authored-static") {
        request.controls.complexity = {{42000U, 36000U, 34000U, 30000U, 26000U, 22000U}};
        request.controls.enthusiasm = 0U;
    } else if (condition == "authored-phrase-variation") {
        request.controls.complexity = {{50000U, 44000U, 48000U, 39000U, 35000U, 32000U}};
        request.controls.enthusiasm = 22000U;
        request.controls.swing_u15 = 4096U;
        request.fill_phrase = 2;
    } else if (condition == "independent-probability-comparator") {
        request.mode = gdm::GeneratorMode::independent_probability_comparator;
        request.controls.complexity = {{42000U, 36000U, 34000U, 30000U, 26000U, 22000U}};
        request.controls.enthusiasm = 22000U;
    } else if (condition == "allocator-stress") {
        request.mode = gdm::GeneratorMode::allocator_stress;
        request.phrase_count = 1U;
    } else if (condition == "three-turn-static") {
        request.controls.rhythm_preset = 1U;
        request.controls.complexity = {{44000U, 38000U, 36000U, 30000U, 28000U, 26000U}};
        request.controls.enthusiasm = 0U;
    } else if (condition == "rolling-six-static") {
        request.controls.rhythm_preset = 2U;
        request.controls.complexity = {{44000U, 38000U, 39000U, 30000U, 28000U, 26000U}};
        request.controls.enthusiasm = 0U;
    } else if (condition == "five-across-shaped") {
        request.controls.rhythm_preset = 3U;
        request.controls.complexity = {{48000U, 43000U, 50000U, 39000U, 36000U, 43000U}};
        request.controls.enthusiasm = 18000U;
        request.controls.voice_shapes[0].tune_u7 = 52U;
        request.controls.voice_shapes[1].decay_u7 = 86U;
        request.controls.voice_shapes[2].color_u7 = 78U;
        request.controls.voice_shapes[3].timbre_u7 = 91U;
        request.controls.voice_shapes[4].pitch_env_u7 = 80U;
        request.controls.voice_shapes[5].level_u7 = 76U;
        request.fill_phrase = 1;
    } else if (condition == "samba-enredo-study") {
        request.controls.rhythm_preset = 4U;
        request.controls.complexity = {{42000U, 40000U, 46000U, 36000U, 34000U, 32000U}};
        request.controls.enthusiasm = 12000U;
        request.controls.tempo_milli_bpm = 104000U;
    } else {
        throw std::invalid_argument("unknown condition: " + condition);
    }
    return request;
}

[[nodiscard]] std::string sha256(const std::vector<std::uint8_t>& bytes) {
    return schuss::instrument_lab::sha256(bytes.data(), bytes.size());
}

[[nodiscard]] std::vector<std::uint8_t> asBytes(const std::string& text) {
    return std::vector<std::uint8_t>(text.begin(), text.end());
}

}  // namespace

int main(int argc, char** argv) {
    try {
        std::string condition;
        fs::path output;
        std::size_t block_frames = 128U;
        for (int index = 1; index < argc; ++index) {
            const std::string argument = argv[index];
            if (argument == "--condition" && index + 1 < argc) {
                condition = argv[++index];
            } else if (argument == "--output" && index + 1 < argc) {
                output = argv[++index];
            } else if (argument == "--block-frames" && index + 1 < argc) {
                block_frames = static_cast<std::size_t>(std::stoul(argv[++index]));
            } else {
                throw std::invalid_argument("unknown or incomplete argument: " + argument);
            }
        }
        if (condition.empty() || output.empty()) {
            throw std::invalid_argument(
                "usage: generative-drum-machine-render --condition ID --output DIR "
                "[--block-frames N]");
        }
        fs::create_directories(output);
        const auto request = requestFor(condition, block_frames);
        const auto result = gdm::render(request);
        const auto event_text = eventTrace(condition, request, result.hits);
        const auto allocator_text = allocatorTrace(condition, result.allocations);
        const auto metrics_text = metricsJson(condition, result.metrics, result.hits.size());
        const auto wav_bytes = makeWav(result);
        const auto event_bytes = asBytes(event_text);
        const auto allocator_bytes = asBytes(allocator_text);
        const auto metrics_bytes = asBytes(metrics_text);
        writeText(output / "event-trace.json", event_text);
        writeText(output / "allocator-trace.json", allocator_text);
        writeText(output / "metrics.json", metrics_text);
        writeBytes(output / "audio.wav", wav_bytes);
        const std::string manifest =
            "{\"artifacts\":{\"allocator-trace.json\":\"" + sha256(allocator_bytes)
            + "\",\"audio.wav\":\"" + sha256(wav_bytes)
            + "\",\"event-trace.json\":\"" + sha256(event_bytes)
            + "\",\"metrics.json\":\"" + sha256(metrics_bytes)
            + "\"},\"condition\":\"" + schuss::instrument_lab::jsonEscape(condition)
            + "\",\"schema_version\":\"schuss-drum-render-manifest-prototype-v0\"}\n";
        writeText(output / "manifest.json", manifest);
        std::cout << condition << ": " << result.hits.size() << " events, "
                  << result.metrics.peak_absolute_q27 << " peak Q27\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "render failed: " << error.what() << '\n';
        return 1;
    }
}
