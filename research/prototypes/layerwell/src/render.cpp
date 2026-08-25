#include "layerwell/core.hpp"
#include "layerwell/launch_control_3.hpp"

#include "schuss/pamplist/ui_model.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace pam = schuss::pamplist;

struct AbsoluteEvent final {
    std::uint64_t frame{};
    layerwell::Event event{};
};

void writeU16(std::ofstream& stream, std::uint16_t value) {
    const std::array<char, 2> bytes{{
        static_cast<char>(value & 0xffU),
        static_cast<char>((value >> 8U) & 0xffU),
    }};
    stream.write(bytes.data(), bytes.size());
}

void writeU32(std::ofstream& stream, std::uint32_t value) {
    const std::array<char, 4> bytes{{
        static_cast<char>(value & 0xffU),
        static_cast<char>((value >> 8U) & 0xffU),
        static_cast<char>((value >> 16U) & 0xffU),
        static_cast<char>((value >> 24U) & 0xffU),
    }};
    stream.write(bytes.data(), bytes.size());
}

std::string jsonEscape(std::string_view value) {
    std::string result;
    result.reserve(value.size());
    for (const auto character : value) {
        switch (character) {
            case '\\': result += "\\\\"; break;
            case '"': result += "\\\""; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\t': result += "\\t"; break;
            default:
                if (static_cast<unsigned char>(character) >= 32U) {
                    result += character;
                }
                break;
        }
    }
    return result;
}

std::string displayLine(const std::array<char, 22>& line) {
    std::size_t size = 0U;
    while (size < 21U && line[size] != '\0') ++size;
    return std::string(line.data(), size);
}

const char* eventName(layerwell::EventKind kind) noexcept {
    switch (kind) {
        case layerwell::EventKind::capture_press: return "capture-press";
        case layerwell::EventKind::set_trim_start: return "trim-start";
        case layerwell::EventKind::set_trim_end: return "trim-end";
        case layerwell::EventKind::source_next: return "source-next";
        case layerwell::EventKind::select_layer: return "select-layer";
        default: return "other";
    }
}

bool writeWav(
    const std::filesystem::path& path,
    const std::vector<float>& interleaved) {
    if ((interleaved.size() & 1U) != 0U) return false;
    std::ofstream stream(path, std::ios::binary);
    if (!stream) return false;
    const auto frame_count = static_cast<std::uint32_t>(interleaved.size() / 2U);
    const auto data_bytes = frame_count * 2U * sizeof(std::int16_t);
    stream.write("RIFF", 4);
    writeU32(stream, 36U + data_bytes);
    stream.write("WAVE", 4);
    stream.write("fmt ", 4);
    writeU32(stream, 16U);
    writeU16(stream, 1U);
    writeU16(stream, 2U);
    writeU32(stream, 48000U);
    writeU32(stream, 48000U * 2U * sizeof(std::int16_t));
    writeU16(stream, 2U * sizeof(std::int16_t));
    writeU16(stream, 16U);
    stream.write("data", 4);
    writeU32(stream, data_bytes);
    for (const auto sample : interleaved) {
        const auto bounded = std::clamp(sample, -1.0F, 1.0F);
        const auto pcm = static_cast<std::int16_t>(std::clamp(
            static_cast<int>(std::lround(bounded * 32767.0F)), -32767, 32767));
        writeU16(stream, static_cast<std::uint16_t>(pcm));
    }
    return static_cast<bool>(stream);
}

bool writeEventStateTrace(
    const std::filesystem::path& path,
    const layerwell::Snapshot& snapshot,
    const std::vector<AbsoluteEvent>& schedule,
    bool untrimmed) {
    std::ofstream stream(path);
    if (!stream) return false;
    stream << "{\n"
           << "  \"schema\": \"layerwell-event-state-trace-v2\",\n"
           << "  \"condition\": \""
           << (untrimmed ? "LW02_CMP_UNTRIMMED" : "LW02_TRIM") << "\",\n"
           << "  \"timeline_convention\": \"event-before-sample; capture start inclusive and stop exclusive; accepted trim resets phase zero\",\n"
           << "  \"events\": [\n";
    for (std::size_t index = 0U; index < schedule.size(); ++index) {
        const auto& scheduled = schedule[index];
        stream << "    {\"frame\": " << scheduled.frame
               << ", \"sequence\": " << scheduled.event.ingress_sequence
               << ", \"kind\": \"" << eventName(scheduled.event.kind)
               << "\", \"value\": " << scheduled.event.value << "}"
               << (index + 1U == schedule.size() ? "\n" : ",\n");
    }
    stream << "  ],\n"
           << "  \"capture_boundaries\": {\"first_start\": 0, \"first_commit\": 48000, "
           << "\"second_arm\": 72000, \"second_start\": "
           << (untrimmed ? 96000U : 86400U) << ", \"second_commit\": "
           << (untrimmed ? 144000U : 124800U) << "},\n"
           << "  \"final\": {\n"
           << "    \"absolute_frame\": " << snapshot.absolute_frame << ",\n"
           << "    \"accepted_sequence\": " << snapshot.accepted_sequence << ",\n"
           << "    \"loop_length_frames\": " << snapshot.loop_length_frames << ",\n"
           << "    \"phase_frames\": " << snapshot.phase_frames << ",\n"
           << "    \"trim_start_frames\": " << snapshot.trim_start_frames << ",\n"
           << "    \"trim_end_frames\": " << snapshot.trim_end_frames << ",\n"
           << "    \"trim_extent_frames\": " << snapshot.trim_extent_frames << ",\n"
           << "    \"trim_available\": "
           << (snapshot.trim_available ? "true" : "false") << ",\n"
           << "    \"selected_source\": \""
           << layerwell::sourceName(snapshot.selected_source) << "\",\n"
           << "    \"selected_layer\": "
           << static_cast<unsigned>(snapshot.selected_layer) << ",\n"
           << "    \"capture_state\": \""
           << layerwell::captureStateName(snapshot.capture_state) << "\",\n"
           << "    \"layers\": [\n";
    for (std::size_t layer = 0U; layer < snapshot.layers.size(); ++layer) {
        const auto& state = snapshot.layers[layer];
        stream << "      {\"index\": " << layer
               << ", \"occupied\": " << (state.occupied ? "true" : "false")
               << ", \"muted\": " << (state.muted ? "true" : "false")
               << ", \"store_owner\": " << static_cast<unsigned>(state.store_owner)
               << ", \"recorded_length_frames\": " << state.recorded_length_frames
               << ", \"playback_offset_frames\": " << state.playback_offset_frames
               << "}" << (layer + 1U == snapshot.layers.size() ? "\n" : ",\n");
    }
    stream << "    ],\n"
           << "    \"source_processed_frames\": ["
           << snapshot.source_processed_frames[0] << ", "
           << snapshot.source_processed_frames[1] << "]\n"
           << "  }\n"
           << "}\n";
    return static_cast<bool>(stream);
}

bool writePanelTrace(
    const std::filesystem::path& path,
    const layerwell::Snapshot& tide_snapshot,
    const layerwell::Snapshot& pamplist_snapshot) {
    std::ofstream stream(path);
    if (!stream) return false;
    const auto& tide = tide_snapshot.source_panel.tide_pit;
    const auto& pam_state = pamplist_snapshot.source_panel.pamplist;
    const auto surface = pam::surfaceModel(pam_state);
    stream << std::setprecision(17)
           << "{\n"
           << "  \"schema\": \"layerwell-embedded-panel-trace-v1\",\n"
           << "  \"presentation_authority\": \"accepted Layerwell Snapshot only\",\n"
           << "  \"tide_pit\": {\n"
           << "    \"processed_frames\": " << tide.absolute_sample << ",\n"
           << "    \"source\": \"" << tidepit::sourceName(tide.source) << "\",\n"
           << "    \"scale\": \"" << tidepit::scaleName(tide.scale) << "\",\n"
           << "    \"effect\": \"" << tidepit::effectName(tide.effect) << "\",\n"
           << "    \"target\": \"" << tidepit::targetName(tide.target) << "\",\n"
           << "    \"display_lines\": [";
    for (std::size_t line = 0U; line < tide.display_lines.size(); ++line) {
        if (line != 0U) stream << ", ";
        stream << "\"" << jsonEscape(displayLine(tide.display_lines[line])) << "\"";
    }
    stream << "],\n"
           << "    \"encoder_positions\": 16,\n"
           << "    \"button_positions\": 8,\n"
           << "    \"scope_samples\": "
           << tide_snapshot.source_panel.tide_scope.sample_count << "\n"
           << "  },\n"
           << "  \"pamplist\": {\n"
           << "    \"processed_frames\": " << pam_state.absolute_frame << ",\n"
           << "    \"selected_page\": "
           << static_cast<unsigned>(pam_state.accepted.selected_page) << ",\n"
           << "    \"context\": \""
           << jsonEscape(pam::surfaceContextName(surface.context)) << "\",\n"
           << "    \"running\": "
           << (pam_state.accepted.running ? "true" : "false") << ",\n"
           << "    \"guide\": \"" << jsonEscape(surface.guide) << "\",\n"
           << "    \"controls\": [\n";
    for (std::size_t slot = 0U; slot < 16U; ++slot) {
        const auto& model = slot < 8U
            ? surface.top[slot]
            : surface.bottom[slot - 8U];
        stream << "      {\"slot\": " << slot
               << ", \"label\": \"" << jsonEscape(model.label)
               << "\", \"value\": " << model.value
               << ", \"enabled\": " << (model.enabled ? "true" : "false")
               << "}" << (slot == 15U ? "\n" : ",\n");
    }
    stream << "    ],\n"
           << "    \"page_buttons\": 8,\n"
           << "    \"impact_history_samples\": "
           << static_cast<unsigned>(
                  pamplist_snapshot.source_panel.pamplist_impact.sample_count)
           << "\n"
           << "  }\n"
           << "}\n";
    return static_cast<bool>(stream);
}

bool writeControllerTrace(
    const std::filesystem::path& path,
    const layerwell::Snapshot& snapshot) {
    layerwell::LaunchControl3Adapter adapter;
    const auto connection = adapter.connectionMessages(snapshot);
    const auto overlay = adapter.parameterOverlayMessages("TRIM", "LOCKED");
    const auto shutdown = adapter.shutdownMessages();
    if (connection.dropped != 0U || overlay.dropped != 0U
        || shutdown.dropped != 0U) {
        return false;
    }
    std::ofstream stream(path);
    if (!stream) return false;
    auto writeBatch = [&](const layerwell::MidiBatch& batch) {
        stream << "[\n";
        for (std::size_t index = 0U; index < batch.count; ++index) {
            stream << "    [";
            const auto& message = batch.messages[index];
            for (std::size_t byte = 0U; byte < message.size; ++byte) {
                if (byte != 0U) stream << ", ";
                stream << static_cast<unsigned>(message.bytes[byte]);
            }
            stream << "]" << (index + 1U == batch.count ? "\n" : ",\n");
        }
        stream << "  ]";
    };
    stream << "{\n"
           << "  \"schema\": \"layerwell-lc3-protocol-trace-v2\",\n"
           << "  \"physical_device_observed\": false,\n"
           << "  \"connection\": ";
    writeBatch(connection);
    stream << ",\n  \"overlay\": ";
    writeBatch(overlay);
    stream << ",\n  \"shutdown\": ";
    writeBatch(shutdown);
    stream << "\n}\n";
    return static_cast<bool>(stream);
}

bool writeMetrics(
    const std::filesystem::path& path,
    const std::vector<float>& interleaved,
    const layerwell::Snapshot& snapshot,
    bool untrimmed) {
    double peak = 0.0;
    long double sum = 0.0;
    long double sum_squares = 0.0;
    std::uint64_t finite = 0U;
    for (const auto sample : interleaved) {
        if (std::isfinite(sample)) ++finite;
        peak = std::max(peak, std::abs(static_cast<double>(sample)));
        sum += sample;
        sum_squares += static_cast<long double>(sample) * sample;
    }
    const auto count = static_cast<long double>(interleaved.size());
    const auto dc = count == 0.0L ? 0.0L : sum / count;
    const auto rms = count == 0.0L ? 0.0L : std::sqrt(sum_squares / count);
    std::ofstream stream(path);
    if (!stream) return false;
    stream << std::setprecision(17)
           << "{\n"
           << "  \"schema\": \"layerwell-metrics-v2\",\n"
           << "  \"condition\": \""
           << (untrimmed ? "LW02_CMP_UNTRIMMED" : "LW02_TRIM") << "\",\n"
           << "  \"frames\": " << interleaved.size() / 2U << ",\n"
           << "  \"finite_samples\": " << finite << ",\n"
           << "  \"peak_absolute\": " << peak << ",\n"
           << "  \"rms\": " << static_cast<double>(rms) << ",\n"
           << "  \"dc\": " << static_cast<double>(dc) << ",\n"
           << "  \"limited_samples\": " << snapshot.diagnostics.limited_samples << ",\n"
           << "  \"capture_commits\": " << snapshot.diagnostics.capture_commits << ",\n"
           << "  \"capture_aborts\": " << snapshot.diagnostics.capture_aborts << ",\n"
           << "  \"trim_accepts\": " << snapshot.diagnostics.trim_accepts << ",\n"
           << "  \"trim_rejections\": " << snapshot.diagnostics.trim_rejections << ",\n"
           << "  \"playback_invariant_faults\": "
           << snapshot.diagnostics.playback_invariant_faults << ",\n"
           << "  \"events_accepted\": " << snapshot.diagnostics.accepted_events << ",\n"
           << "  \"events_dropped\": " << snapshot.diagnostics.dropped_events << ",\n"
           << "  \"sample_storage_bytes\": "
           << snapshot.diagnostics.sample_storage_bytes << ",\n"
           << "  \"physical_device_observed\": false,\n"
           << "  \"listening_performed\": false\n"
           << "}\n";
    return static_cast<bool>(stream);
}

}  // namespace

int main(int argc, char** argv) {
    std::uint32_t block_frames = 128U;
    std::filesystem::path output_directory;
    bool untrimmed = false;
    for (int index = 1; index < argc; ++index) {
        const std::string argument{argv[index]};
        if (argument == "--block" && index + 1 < argc) {
            block_frames = static_cast<std::uint32_t>(std::stoul(argv[++index]));
        } else if (argument == "--output-dir" && index + 1 < argc) {
            output_directory = argv[++index];
        } else if (argument == "--untrimmed") {
            untrimmed = true;
        } else {
            std::cerr << "usage: layerwell-render --block 16|64|128|512 "
                         "--output-dir PATH [--untrimmed]\n";
            return 2;
        }
    }
    if (output_directory.empty()
        || block_frames == 0U
        || block_frames > layerwell::kMaximumBlockFrames
        || block_frames % layerwell::kSourceQuantumFrames != 0U) {
        std::cerr << "invalid render arguments\n";
        return 2;
    }
    std::filesystem::create_directories(output_directory);

    layerwell::Core core;
    if (!core.prepare()) {
        std::cerr << "Layerwell Core preparation failed\n";
        return 3;
    }
    std::vector<AbsoluteEvent> schedule{
        {0U, {0U, 1U, layerwell::EventKind::capture_press, 0U, 0.0}},
        {48000U, {0U, 2U, layerwell::EventKind::capture_press, 0U, 0.0}},
    };
    if (!untrimmed) {
        schedule.push_back(
            {48000U, {0U, 3U, layerwell::EventKind::set_trim_start, 0U, 4800.0}});
        schedule.push_back(
            {48000U, {0U, 4U, layerwell::EventKind::set_trim_end, 0U, 43200.0}});
    }
    schedule.push_back(
        {48000U, {0U, 5U, layerwell::EventKind::source_next, 0U, 0.0}});
    schedule.push_back(
        {72000U, {0U, 6U, layerwell::EventKind::select_layer, 1U, 0.0}});
    schedule.push_back(
        {72000U, {0U, 7U, layerwell::EventKind::capture_press, 0U, 0.0}});

    constexpr std::uint64_t total_frames = 144000U;
    std::vector<float> interleaved(total_frames * 2U);
    std::array<float, layerwell::kMaximumBlockFrames> left{};
    std::array<float, layerwell::kMaximumBlockFrames> right{};
    std::size_t next_event = 0U;
    for (std::uint64_t origin = 0U; origin < total_frames;) {
        const auto frames = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            block_frames, total_frames - origin));
        std::array<layerwell::Event, 8> events{};
        std::size_t event_count = 0U;
        const auto end = origin + frames;
        while (next_event < schedule.size() && schedule[next_event].frame <= end) {
            auto event = schedule[next_event].event;
            event.sample_offset = static_cast<std::uint32_t>(
                schedule[next_event].frame - origin);
            events[event_count++] = event;
            ++next_event;
        }
        const auto report = core.process(
            left.data(), right.data(), frames, events.data(), event_count);
        if (report.events_dropped != 0U
            || report.events_rejected != 0U
            || report.capture_aborted
            || report.source_failed) {
            std::cerr << "render process invariant failed\n";
            return 4;
        }
        for (std::uint32_t frame = 0U; frame < frames; ++frame) {
            interleaved[(origin + frame) * 2U] = left[frame];
            interleaved[(origin + frame) * 2U + 1U] = right[frame];
        }
        origin += frames;
    }

    const auto snapshot = core.snapshot();
    const auto expected_length = untrimmed ? 48000U : 38400U;
    const auto expected_phase = untrimmed ? 0U : 19200U;
    if (snapshot.absolute_frame != total_frames
        || snapshot.loop_length_frames != expected_length
        || snapshot.phase_frames != expected_phase
        || !snapshot.layers[0].occupied
        || !snapshot.layers[1].occupied
        || snapshot.layers[2].occupied
        || snapshot.layers[0].recorded_length_frames != 48000U
        || snapshot.layers[0].playback_offset_frames != (untrimmed ? 0U : 4800U)
        || snapshot.layers[1].recorded_length_frames != expected_length
        || snapshot.layers[1].playback_offset_frames != 0U
        || snapshot.capture_state != layerwell::CaptureState::idle
        || snapshot.trim_available
        || snapshot.diagnostics.playback_invariant_faults != 0U) {
        std::cerr << "final state invariant failed\n";
        return 5;
    }

    const auto ok = writeWav(output_directory / "layerwell.wav", interleaved)
        && writeEventStateTrace(
            output_directory / "event-state-trace.json", snapshot,
            schedule, untrimmed)
        && writePanelTrace(
            output_directory / "panel-trace.json", snapshot, snapshot)
        && writeControllerTrace(
            output_directory / "controller-trace.json", snapshot)
        && writeMetrics(
            output_directory / "metrics.json", interleaved, snapshot, untrimmed);
    if (!ok) {
        std::cerr << "could not retain render evidence\n";
        return 6;
    }
    std::cout << "Layerwell 0.2 render complete: frames=" << total_frames
              << " block=" << block_frames
              << " condition="
              << (untrimmed ? "LW02_CMP_UNTRIMMED" : "LW02_TRIM") << '\n';
    return 0;
}
