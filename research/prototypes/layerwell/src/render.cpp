#include "layerwell/core.hpp"
#include "layerwell/launch_control_3.hpp"

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
#include <vector>

namespace {

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
        const auto bounded = std::clamp(sample, -1.0f, 1.0f);
        const auto pcm = static_cast<std::int16_t>(std::clamp(
            static_cast<int>(std::lround(bounded * 32767.0f)), -32767, 32767));
        writeU16(stream, static_cast<std::uint16_t>(pcm));
    }
    return static_cast<bool>(stream);
}

bool writeEventStateTrace(
    const std::filesystem::path& path,
    const layerwell::Snapshot& snapshot,
    const std::vector<AbsoluteEvent>& schedule,
    bool callback_edge_timing) {
    std::ofstream stream(path);
    if (!stream) return false;
    stream
        << "{\n"
        << "  \"schema\": \"layerwell-event-state-trace-v1\",\n"
        << "  \"timing_model\": \""
        << (callback_edge_timing ? "callback-edge-comparator" : "sample-exact")
        << "\",\n"
        << "  \"timeline_convention\": \"event-before-sample; start-inclusive; stop-exclusive\",\n"
        << "  \"events\": [\n";
    for (std::size_t index = 0U; index < schedule.size(); ++index) {
        const auto& scheduled = schedule[index];
        const char* kind = "capture-press";
        if (scheduled.event.kind == layerwell::EventKind::source_next) {
            kind = "source-next";
        } else if (scheduled.event.kind == layerwell::EventKind::select_layer) {
            kind = "select-layer-2";
        }
        stream << "    {\"frame\": " << scheduled.frame
               << ", \"sequence\": " << scheduled.event.ingress_sequence
               << ", \"kind\": \"" << kind << "\"}"
               << (index + 1U == schedule.size() ? "\n" : ",\n");
    }
    stream << "  ],\n";
    if (callback_edge_timing) {
        stream << "  \"capture_boundaries\": null,\n";
    } else {
        stream << "  \"capture_boundaries\": {\"first_start\": 0, \"first_commit\": 48000, "
                  "\"second_arm\": 72000, \"second_start\": 96000, \"second_commit\": 144000},\n";
    }
    stream
        << "  \"final\": {\n"
        << "    \"absolute_frame\": " << snapshot.absolute_frame << ",\n"
        << "    \"accepted_sequence\": " << snapshot.accepted_sequence << ",\n"
        << "    \"loop_length_frames\": " << snapshot.loop_length_frames << ",\n"
        << "    \"phase_frames\": " << snapshot.phase_frames << ",\n"
        << "    \"selected_source\": \"" << layerwell::sourceName(snapshot.selected_source) << "\",\n"
        << "    \"selected_layer\": " << static_cast<unsigned>(snapshot.selected_layer) << ",\n"
        << "    \"capture_state\": \"" << layerwell::captureStateName(snapshot.capture_state) << "\",\n"
        << "    \"layers\": [\n";
    for (std::size_t layer = 0U; layer < snapshot.layers.size(); ++layer) {
        const auto& state = snapshot.layers[layer];
        stream << "      {\"index\": " << layer
               << ", \"occupied\": " << (state.occupied ? "true" : "false")
               << ", \"muted\": " << (state.muted ? "true" : "false")
               << ", \"store_owner\": " << static_cast<unsigned>(state.store_owner)
               << "}" << (layer + 1U == snapshot.layers.size() ? "\n" : ",\n");
    }
    stream
        << "    ],\n"
        << "    \"source_processed_frames\": ["
        << snapshot.source_processed_frames[0] << ", "
        << snapshot.source_processed_frames[1] << "]\n"
        << "  }\n"
        << "}\n";
    return static_cast<bool>(stream);
}

bool writeControllerTrace(
    const std::filesystem::path& path,
    const layerwell::Snapshot& snapshot) {
    layerwell::LaunchControl3Adapter adapter;
    const auto connection = adapter.connectionMessages(snapshot);
    const auto overlay = adapter.parameterOverlayMessages("CAPTURE", "IDLE");
    const auto shutdown = adapter.shutdownMessages();
    if (connection.dropped != 0U || overlay.dropped != 0U || shutdown.dropped != 0U) {
        return false;
    }

    std::ofstream stream(path);
    if (!stream) return false;
    stream << "{\n"
           << "  \"schema\": \"layerwell-lc3-protocol-trace-v1\",\n"
           << "  \"physical_device_observed\": false,\n"
           << "  \"connection\": [\n";
    for (std::size_t index = 0U; index < connection.count; ++index) {
        stream << "    [";
        const auto& message = connection.messages[index];
        for (std::size_t byte = 0U; byte < message.size; ++byte) {
            if (byte != 0U) stream << ", ";
            stream << static_cast<unsigned>(message.bytes[byte]);
        }
        stream << "]" << (index + 1U == connection.count ? "\n" : ",\n");
    }
    stream << "  ],\n  \"overlay\": [\n";
    for (std::size_t index = 0U; index < overlay.count; ++index) {
        stream << "    [";
        const auto& message = overlay.messages[index];
        for (std::size_t byte = 0U; byte < message.size; ++byte) {
            if (byte != 0U) stream << ", ";
            stream << static_cast<unsigned>(message.bytes[byte]);
        }
        stream << "]" << (index + 1U == overlay.count ? "\n" : ",\n");
    }
    stream << "  ],\n  \"shutdown\": [[";
    for (std::size_t byte = 0U; byte < shutdown.messages[0].size; ++byte) {
        if (byte != 0U) stream << ", ";
        stream << static_cast<unsigned>(shutdown.messages[0].bytes[byte]);
    }
    stream << "]]\n}\n";
    return static_cast<bool>(stream);
}

bool writeMetrics(
    const std::filesystem::path& path,
    const std::vector<float>& interleaved,
    const layerwell::Snapshot& snapshot,
    bool callback_edge_timing) {
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
           << "  \"schema\": \"layerwell-metrics-v1\",\n"
           << "  \"frames\": " << interleaved.size() / 2U << ",\n"
           << "  \"finite_samples\": " << finite << ",\n"
           << "  \"peak_absolute\": " << peak << ",\n"
           << "  \"rms\": " << static_cast<double>(rms) << ",\n"
           << "  \"dc\": " << static_cast<double>(dc) << ",\n"
           << "  \"limited_samples\": " << snapshot.diagnostics.limited_samples << ",\n"
           << "  \"capture_commits\": " << snapshot.diagnostics.capture_commits << ",\n"
           << "  \"capture_aborts\": " << snapshot.diagnostics.capture_aborts << ",\n"
           << "  \"events_accepted\": " << snapshot.diagnostics.accepted_events << ",\n"
           << "  \"events_dropped\": " << snapshot.diagnostics.dropped_events << ",\n"
           << "  \"sample_storage_bytes\": " << snapshot.diagnostics.sample_storage_bytes << ",\n"
           << "  \"timing_model\": \""
           << (callback_edge_timing ? "callback-edge-comparator" : "sample-exact")
           << "\",\n"
           << "  \"physical_device_observed\": false,\n"
           << "  \"listening_performed\": false\n"
           << "}\n";
    return static_cast<bool>(stream);
}

}  // namespace

int main(int argc, char** argv) {
    std::uint32_t block_frames = 128U;
    std::filesystem::path output_directory;
    bool callback_edge_timing = false;
    for (int index = 1; index < argc; ++index) {
        const std::string argument{argv[index]};
        if (argument == "--block" && index + 1 < argc) {
            block_frames = static_cast<std::uint32_t>(std::stoul(argv[++index]));
        } else if (argument == "--output-dir" && index + 1 < argc) {
            output_directory = argv[++index];
        } else if (argument == "--callback-edge") {
            callback_edge_timing = true;
        } else {
            std::cerr << "usage: layerwell-render --block 16|64|128|512 "
                         "--output-dir PATH [--callback-edge]\n";
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
        {48000U, {0U, 3U, layerwell::EventKind::source_next, 0U, 0.0}},
        {72000U, {0U, 4U, layerwell::EventKind::select_layer, 1U, 0.0}},
        {72000U, {0U, 5U, layerwell::EventKind::capture_press, 0U, 0.0}},
    };
    if (callback_edge_timing) {
        for (auto& scheduled : schedule) {
            scheduled.frame = ((scheduled.frame + block_frames - 1U)
                / block_frames) * block_frames;
        }
    }
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
    if (!callback_edge_timing
        && (snapshot.absolute_frame != total_frames
            || snapshot.loop_length_frames != 48000U
            || snapshot.phase_frames != 0U
            || !snapshot.layers[0].occupied
            || !snapshot.layers[1].occupied
            || snapshot.layers[2].occupied
            || snapshot.capture_state != layerwell::CaptureState::idle)) {
        std::cerr << "final state invariant failed\n";
        return 5;
    }

    const auto ok = writeWav(output_directory / "layerwell.wav", interleaved)
        && writeEventStateTrace(
            output_directory / "event-state-trace.json", snapshot,
            schedule, callback_edge_timing)
        && writeControllerTrace(
            output_directory / "controller-trace.json", snapshot)
        && writeMetrics(
            output_directory / "metrics.json", interleaved, snapshot,
            callback_edge_timing);
    if (!ok) {
        std::cerr << "could not retain render evidence\n";
        return 6;
    }
    std::cout << "Layerwell render complete: frames=" << total_frames
              << " peak bounded block=" << block_frames << '\n';
    return 0;
}
