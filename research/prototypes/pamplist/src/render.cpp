#include "schuss/pamplist/control_map.hpp"
#include "schuss/pamplist/core.hpp"

#include "schuss/instrument_lab/renderer_artifacts.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace pam = schuss::pamplist;
namespace lab = schuss::instrument_lab;
namespace fs = std::filesystem;

namespace {

constexpr std::string_view kProposalSha256 =
    "bf110cd1bfe6b86e032bc993e0baf705d7459182c891d095a9a1a39ce1789af3";
constexpr std::string_view kSourceRevision =
    "08d3e6e1e2b61230308c20a15ded58ffdaf4656c";
constexpr std::string_view kSourceTree =
    "58917f3e2e46a30337cfb6292a3504845b1d5552";

struct RecordedEvent final {
    std::string part;
    pam::QuantumEvent event{};
};

struct PartSnapshot final {
    std::string part;
    pam::Snapshot snapshot{};
};

struct PartMetrics final {
    std::string part;
    std::uint64_t frame_count{};
    std::int32_t peak_main_q27{};
    std::int32_t peak_auxiliary_q27{};
    std::uint64_t nonzero_main{};
    std::uint64_t nonzero_auxiliary{};
    std::uint64_t trigger_count{};
    std::uint64_t matrix_clamp_count{};
};

struct Rendered final {
    std::vector<std::int32_t> main_q27;
    std::vector<std::int32_t> auxiliary_q27;
    std::vector<RecordedEvent> events;
    std::vector<PartSnapshot> snapshots;
    std::vector<PartMetrics> parts;
};

[[nodiscard]] std::string jsonString(std::string_view value) {
    return "\"" + lab::jsonEscape(value) + "\"";
}

void writeText(const fs::path& path, const std::string& content) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) throw std::runtime_error("cannot write " + path.string());
    stream.write(content.data(), static_cast<std::streamsize>(content.size()));
    if (!stream) throw std::runtime_error("failed writing " + path.string());
}

[[nodiscard]] std::vector<std::uint8_t> readBytes(const fs::path& path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("cannot read " + path.string());
    return std::vector<std::uint8_t>(
        std::istreambuf_iterator<char>(stream),
        std::istreambuf_iterator<char>());
}

[[nodiscard]] std::string fileSha256(const fs::path& path) {
    const auto bytes = readBytes(path);
    return lab::sha256(bytes.data(), bytes.size());
}

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

void writeTag(std::ofstream& stream, const char (&tag)[5]) {
    stream.write(tag, 4);
}

void writeWav(
    const fs::path& path,
    const std::vector<std::int32_t>& main_q27,
    const std::vector<std::int32_t>& auxiliary_q27) {
    if (main_q27.size() != auxiliary_q27.size()) {
        throw std::runtime_error("stereo channel length mismatch");
    }
    const auto frame_count = static_cast<std::uint32_t>(main_q27.size());
    const auto data_size = frame_count * 6U;
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) throw std::runtime_error("cannot write " + path.string());
    writeTag(stream, "RIFF");
    writeU32(stream, 36U + data_size);
    writeTag(stream, "WAVE");
    writeTag(stream, "fmt ");
    writeU32(stream, 16U);
    writeU16(stream, 1U);
    writeU16(stream, 2U);
    writeU32(stream, pam::kSampleRateHz);
    writeU32(stream, pam::kSampleRateHz * 6U);
    writeU16(stream, 6U);
    writeU16(stream, 24U);
    writeTag(stream, "data");
    writeU32(stream, data_size);
    for (std::size_t frame = 0; frame < main_q27.size(); ++frame) {
        for (const auto q27 : {main_q27[frame], auxiliary_q27[frame]}) {
            const auto q23 = static_cast<std::int32_t>(std::clamp<std::int64_t>(
                static_cast<std::int64_t>(q27) / 16,
                -8388608,
                8388607));
            const std::array<char, 3> bytes{{
                static_cast<char>(q23 & 0xff),
                static_cast<char>((q23 >> 8) & 0xff),
                static_cast<char>((q23 >> 16) & 0xff),
            }};
            stream.write(bytes.data(), bytes.size());
        }
    }
    if (!stream) throw std::runtime_error("failed writing " + path.string());
}

[[nodiscard]] pam::Controls clearedControls() {
    auto controls = pam::defaultControls();
    for (auto& lane : controls.lanes) {
        lane.amplitude = 0.0F;
        lane.routes.fill(0.0F);
    }
    return controls;
}

[[nodiscard]] pam::Controls matrixControls() {
    auto controls = clearedControls();
    controls.engine = 8U;
    const std::array<pam::Shape, pam::kLaneCount> shapes{{
        pam::Shape::pulse,
        pam::Shape::triangle,
        pam::Shape::sine,
        pam::Shape::ramp,
        pam::Shape::exponential_decay,
        pam::Shape::sample_hold,
        pam::Shape::smooth_random,
        pam::Shape::gate,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> rates{{
        8U, 10U, 6U, 11U, 4U, 12U, 2U, 13U,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> phases{{
        0U, 17U, 31U, 47U, 63U, 79U, 97U, 113U,
    }};
    const std::array<float, pam::kLaneCount> weights{{
        1.0F, 0.35F, 0.55F, -0.4F, 0.5F, -0.45F, 0.4F, -0.35F,
    }};
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        controls.lanes[lane].rate_index = rates[lane];
        controls.lanes[lane].phase_u7 = phases[lane];
        controls.lanes[lane].shape = shapes[lane];
        controls.lanes[lane].hits = static_cast<std::uint8_t>(5U + lane);
        controls.lanes[lane].rotation = static_cast<std::uint8_t>(lane * 2U);
        controls.lanes[lane].probability = 1.0F;
        controls.lanes[lane].amplitude = 0.8F;
        controls.lanes[lane].routes[lane] = weights[lane];
    }
    return controls;
}

void appendPart(
    Rendered& rendered,
    const std::string& part,
    const pam::Controls& controls,
    std::size_t frame_count,
    std::size_t block_frames) {
    pam::Core core;
    const auto frame_offset = rendered.main_q27.size();
    const auto start = rendered.main_q27.size();
    rendered.main_q27.resize(start + frame_count);
    rendered.auxiliary_q27.resize(start + frame_count);
    std::size_t cursor = 0U;
    while (cursor < frame_count) {
        const auto count = std::min(block_frames, frame_count - cursor);
        pam::ProcessReport report{};
        if (!core.process(
                controls,
                rendered.main_q27.data() + start + cursor,
                rendered.auxiliary_q27.data() + start + cursor,
                count,
                &report)) {
            throw std::runtime_error("Core rejected a frozen renderer block");
        }
        for (std::size_t index = 0; index < report.event_count; ++index) {
            auto event = report.events[index];
            event.absolute_frame += frame_offset;
            rendered.events.push_back({part, event});
        }
        cursor += count;
    }
    rendered.snapshots.push_back({part, core.snapshot()});
    PartMetrics metrics{};
    metrics.part = part;
    metrics.frame_count = frame_count;
    metrics.trigger_count = core.snapshot().diagnostics.trigger_count;
    metrics.matrix_clamp_count = core.snapshot().diagnostics.matrix_clamp_count;
    for (std::size_t frame = start; frame < start + frame_count; ++frame) {
        const auto main_absolute = static_cast<std::int32_t>(std::abs(
            static_cast<std::int64_t>(rendered.main_q27[frame])));
        const auto auxiliary_absolute = static_cast<std::int32_t>(std::abs(
            static_cast<std::int64_t>(rendered.auxiliary_q27[frame])));
        metrics.peak_main_q27 = std::max(metrics.peak_main_q27, main_absolute);
        metrics.peak_auxiliary_q27 = std::max(
            metrics.peak_auxiliary_q27, auxiliary_absolute);
        metrics.nonzero_main += rendered.main_q27[frame] != 0 ? 1U : 0U;
        metrics.nonzero_auxiliary += rendered.auxiliary_q27[frame] != 0 ? 1U : 0U;
    }
    rendered.parts.push_back(metrics);
}

[[nodiscard]] Rendered renderCondition(
    const std::string& condition,
    std::size_t block_frames) {
    Rendered rendered{};
    if (condition == "PAMP_BASE") {
        appendPart(rendered, "base", pam::defaultControls(), 65536U, block_frames);
    } else if (condition == "PAMP_EUCLID") {
        auto controls = clearedControls();
        controls.engine = 8U;
        controls.lanes[0].rate_index = 8U;
        controls.lanes[0].shape = pam::Shape::pulse;
        controls.lanes[0].hits = 5U;
        controls.lanes[0].amplitude = 1.0F;
        controls.lanes[0].routes[0] = 1.0F;
        controls.lanes[1].rate_index = 10U;
        controls.lanes[1].phase_u7 = 31U;
        controls.lanes[1].shape = pam::Shape::triangle;
        controls.lanes[1].hits = 16U;
        controls.lanes[1].amplitude = 1.0F;
        controls.lanes[1].routes[1] = 0.35F;
        controls.lanes[2].rate_index = 7U;
        controls.lanes[2].phase_u7 = 67U;
        controls.lanes[2].shape = pam::Shape::sine;
        controls.lanes[2].hits = 16U;
        controls.lanes[2].amplitude = 1.0F;
        controls.lanes[2].routes[4] = 0.5F;
        appendPart(rendered, "euclid", controls, 65536U, block_frames);
    } else if (condition == "PAMP_LOOP") {
        auto controls = clearedControls();
        controls.engine = 8U;
        controls.lanes[0].rate_index = 13U;
        controls.lanes[0].shape = pam::Shape::pulse;
        controls.lanes[0].hits = 16U;
        controls.lanes[0].probability = 0.5F;
        controls.lanes[0].repeat = 7U;
        controls.lanes[0].amplitude = 1.0F;
        controls.lanes[0].routes[0] = 1.0F;
        appendPart(rendered, "loop-7", controls, 131072U, block_frames);
    } else if (condition == "PAMP_MATRIX") {
        appendPart(rendered, "matrix", matrixControls(), 131072U, block_frames);
    } else if (condition == "PAMP_24") {
        for (std::uint8_t engine = 0U; engine < 24U; ++engine) {
            auto controls = pam::defaultControls();
            controls.engine = engine;
            controls.lanes[0].rate_index = 13U;
            controls.lanes[0].hits = 16U;
            std::ostringstream part;
            part << "engine-" << std::setw(2) << std::setfill('0')
                 << static_cast<unsigned int>(engine);
            appendPart(rendered, part.str(), controls, 8192U, block_frames);
        }
    } else if (condition == "PAMP_SILENCE") {
        auto stopped = pam::defaultControls();
        stopped.running = false;
        appendPart(rendered, "stopped", stopped, 8192U, block_frames);
        auto zero_hit = pam::defaultControls();
        zero_hit.lanes[0].hits = 0U;
        appendPart(rendered, "zero-hit", zero_hit, 8192U, block_frames);
        auto zero_amplitude = pam::defaultControls();
        zero_amplitude.lanes[0].amplitude = 0.0F;
        appendPart(rendered, "zero-amplitude", zero_amplitude, 8192U, block_frames);
        auto zero_route = pam::defaultControls();
        zero_route.lanes[0].routes.fill(0.0F);
        appendPart(rendered, "zero-route", zero_route, 8192U, block_frames);
    } else if (condition == "PAMP_CMP_PHASELESS") {
        auto controls = matrixControls();
        for (auto& lane : controls.lanes) {
            lane.phase_u7 = 0U;
            for (std::size_t destination = 1U;
                 destination < pam::kDestinationCount;
                 ++destination) {
                lane.routes[destination] = 0.0F;
            }
        }
        appendPart(rendered, "phaseless", controls, 131072U, block_frames);
    } else {
        throw std::runtime_error("unknown condition: " + condition);
    }
    return rendered;
}

[[nodiscard]] std::string eventsJson(
    const std::string& condition,
    const std::vector<RecordedEvent>& events) {
    std::ostringstream out;
    out << "{\"condition\":" << jsonString(condition) << ",\"events\":[";
    for (std::size_t index = 0; index < events.size(); ++index) {
        if (index != 0U) out << ',';
        const auto& recorded = events[index];
        const auto& event = recorded.event;
        out << "{\"accepted_mask\":" << static_cast<unsigned int>(event.accepted_mask)
            << ",\"absolute_frame\":" << event.absolute_frame
            << ",\"addresses\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            out << event.addresses[lane];
        }
        out << "],\"boundary_mask\":" << static_cast<unsigned int>(event.boundary_mask)
            << ",\"part\":" << jsonString(recorded.part)
            << ",\"resolved_engine\":" << static_cast<unsigned int>(event.resolved_engine)
            << ",\"steps\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            out << event.steps[lane];
        }
        out << "],\"trigger\":" << (event.trigger ? "true" : "false")
            << ",\"trigger_lane_mask\":"
            << static_cast<unsigned int>(event.trigger_lane_mask) << '}';
    }
    out << "]}\n";
    return out.str();
}

void controlsJson(std::ostringstream& out, const pam::Controls& controls) {
    out << "{\"decay\":" << lab::finiteJsonNumber(controls.decay)
        << ",\"engine\":" << static_cast<unsigned int>(controls.engine)
        << ",\"harmonics\":" << lab::finiteJsonNumber(controls.harmonics)
        << ",\"lanes\":[";
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        if (lane != 0U) out << ',';
        const auto& value = controls.lanes[lane];
        out << "{\"amplitude\":" << lab::finiteJsonNumber(value.amplitude)
            << ",\"hits\":" << static_cast<unsigned int>(value.hits)
            << ",\"phase_u7\":" << static_cast<unsigned int>(value.phase_u7)
            << ",\"probability\":" << lab::finiteJsonNumber(value.probability)
            << ",\"rate_index\":" << static_cast<unsigned int>(value.rate_index)
            << ",\"repeat\":" << static_cast<unsigned int>(value.repeat)
            << ",\"rotation\":" << static_cast<unsigned int>(value.rotation)
            << ",\"routes\":[";
        for (std::size_t destination = 0;
             destination < pam::kDestinationCount;
             ++destination) {
            if (destination != 0U) out << ',';
            out << lab::finiteJsonNumber(value.routes[destination]);
        }
        out << "],\"shape\":" << static_cast<unsigned int>(value.shape) << '}';
    }
    out << "],\"lpg_colour\":" << lab::finiteJsonNumber(controls.lpg_colour)
        << ",\"master_gain\":" << lab::finiteJsonNumber(controls.master_gain)
        << ",\"morph\":" << lab::finiteJsonNumber(controls.morph)
        << ",\"note\":" << lab::finiteJsonNumber(controls.note)
        << ",\"running\":" << (controls.running ? "true" : "false")
        << ",\"seed\":" << controls.seed
        << ",\"selected_lane\":" << static_cast<unsigned int>(controls.selected_lane)
        << ",\"source_level\":" << lab::finiteJsonNumber(controls.source_level)
        << ",\"tempo_milli_bpm\":" << controls.tempo_milli_bpm
        << ",\"timbre\":" << lab::finiteJsonNumber(controls.timbre) << '}';
}

[[nodiscard]] std::string snapshotsJson(
    const std::string& condition,
    const std::vector<PartSnapshot>& snapshots) {
    std::ostringstream out;
    out << "{\"condition\":" << jsonString(condition) << ",\"snapshots\":[";
    for (std::size_t index = 0; index < snapshots.size(); ++index) {
        if (index != 0U) out << ',';
        const auto& recorded = snapshots[index];
        const auto& value = recorded.snapshot;
        out << "{\"absolute_frame\":" << value.absolute_frame
            << ",\"accepted\":";
        controlsJson(out, value.accepted);
        out << ",\"accepted_sequence\":" << value.accepted_sequence
            << ",\"diagnostics\":{\"clamped_control_count\":"
            << value.diagnostics.clamped_control_count
            << ",\"coalesced_trigger_count\":"
            << value.diagnostics.coalesced_trigger_count
            << ",\"invalid_control_count\":"
            << value.diagnostics.invalid_control_count
            << ",\"matrix_clamp_count\":"
            << value.diagnostics.matrix_clamp_count
            << ",\"non_finite_source_count\":"
            << value.diagnostics.non_finite_source_count
            << ",\"saturated_sample_count\":"
            << value.diagnostics.saturated_sample_count
            << ",\"trigger_count\":" << value.diagnostics.trigger_count
            << ",\"unsupported_process_count\":"
            << value.diagnostics.unsupported_process_count << "}"
            << ",\"lane_addresses\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            out << value.lane_addresses[lane];
        }
        out << "],\"lane_phase_q32\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            out << value.lane_phase_q32[lane];
        }
        out << "],\"lane_remainders\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            out << value.lane_remainders[lane];
        }
        out << "],\"master_phase_q32\":" << value.master_phase_q32
            << ",\"master_remainder\":" << value.master_remainder
            << ",\"part\":" << jsonString(recorded.part)
            << ",\"quantum_count\":" << value.quantum_count
            << ",\"rendered_through_frame\":" << value.rendered_through_frame
            << ",\"resolved_engine\":"
            << static_cast<unsigned int>(value.resolved_engine)
            << ",\"resolved_level\":" << lab::finiteJsonNumber(value.resolved_level)
            << ",\"resolved_note\":" << lab::finiteJsonNumber(value.resolved_note)
            << '}';
    }
    out << "]}\n";
    return out.str();
}

[[nodiscard]] std::string metricsJson(
    const std::string& condition,
    const Rendered& rendered) {
    std::int32_t peak_main = 0;
    std::int32_t peak_auxiliary = 0;
    long double sum_main = 0.0;
    long double sum_auxiliary = 0.0;
    long double square_main = 0.0;
    long double square_auxiliary = 0.0;
    std::uint64_t saturated = 0U;
    for (std::size_t frame = 0; frame < rendered.main_q27.size(); ++frame) {
        const auto main = rendered.main_q27[frame];
        const auto auxiliary = rendered.auxiliary_q27[frame];
        peak_main = std::max(peak_main, static_cast<std::int32_t>(
            std::abs(static_cast<std::int64_t>(main))));
        peak_auxiliary = std::max(peak_auxiliary, static_cast<std::int32_t>(
            std::abs(static_cast<std::int64_t>(auxiliary))));
        sum_main += main;
        sum_auxiliary += auxiliary;
        square_main += static_cast<long double>(main) * main;
        square_auxiliary += static_cast<long double>(auxiliary) * auxiliary;
        saturated += (main == pam::kQ27Maximum || main == pam::kQ27Minimum
            || auxiliary == pam::kQ27Maximum || auxiliary == pam::kQ27Minimum)
            ? 1U : 0U;
    }
    const auto frames = static_cast<long double>(rendered.main_q27.size());
    const auto normalized = static_cast<long double>(UINT32_C(1) << 27);
    std::ostringstream out;
    out << "{\"condition\":" << jsonString(condition)
        << ",\"dc_auxiliary\":"
        << lab::finiteJsonNumber(static_cast<double>(sum_auxiliary / frames / normalized))
        << ",\"dc_main\":"
        << lab::finiteJsonNumber(static_cast<double>(sum_main / frames / normalized))
        << ",\"finite_samples_percent\":100"
        << ",\"frame_count\":" << rendered.main_q27.size()
        << ",\"parts\":[";
    for (std::size_t index = 0; index < rendered.parts.size(); ++index) {
        if (index != 0U) out << ',';
        const auto& part = rendered.parts[index];
        out << "{\"frame_count\":" << part.frame_count
            << ",\"matrix_clamp_count\":" << part.matrix_clamp_count
            << ",\"nonzero_auxiliary\":" << part.nonzero_auxiliary
            << ",\"nonzero_main\":" << part.nonzero_main
            << ",\"part\":" << jsonString(part.part)
            << ",\"peak_auxiliary_q27\":" << part.peak_auxiliary_q27
            << ",\"peak_main_q27\":" << part.peak_main_q27
            << ",\"trigger_count\":" << part.trigger_count << '}';
    }
    out << "]"
        << ",\"peak_auxiliary_q27\":" << peak_auxiliary
        << ",\"peak_main_q27\":" << peak_main
        << ",\"rms_auxiliary\":"
        << lab::finiteJsonNumber(static_cast<double>(
            std::sqrt(square_auxiliary / frames) / normalized))
        << ",\"rms_main\":"
        << lab::finiteJsonNumber(static_cast<double>(
            std::sqrt(square_main / frames) / normalized))
        << ",\"saturated_frame_count\":" << saturated << "}\n";
    return out.str();
}

[[nodiscard]] const char* mappingStatusName(pam::MappingStatus status) {
    switch (status) {
        case pam::MappingStatus::accepted_continuous: return "accepted-continuous";
        case pam::MappingStatus::accepted_press: return "accepted-press";
        case pam::MappingStatus::accepted_release: return "accepted-release";
        case pam::MappingStatus::accepted_hold: return "accepted-hold";
        case pam::MappingStatus::ignored_channel: return "ignored-channel";
        case pam::MappingStatus::unknown_cc: return "unknown-cc";
        case pam::MappingStatus::invalid_message: return "invalid-message";
    }
    return "invalid-status";
}

[[nodiscard]] std::string controllerTraceJson() {
    struct Input final { int channel; int cc; int value; };
    std::vector<Input> inputs;
    for (int lane = 0; lane < 8; ++lane) {
        inputs.push_back({16, 40 + lane, 127});
        inputs.push_back({16, 40 + lane, 127});
        inputs.push_back({16, 40 + lane, 0});
    }
    for (int cc = 20; cc <= 35; ++cc) {
        inputs.push_back({16, cc, 0});
        inputs.push_back({16, cc, 64});
        inputs.push_back({16, cc, 127});
    }
    inputs.push_back({1, 20, 64});
    inputs.push_back({16, 39, 64});
    inputs.push_back({16, 20, 128});
    auto controls = pam::defaultControls();
    pam::ControllerAdapter adapter;
    std::ostringstream out;
    out << "{\"control_map_sha256\":" << jsonString(pam::controlMapSha256())
        << ",\"controller_topology_sha256\":"
        << jsonString(pam::controllerTopologySha256()) << ",\"messages\":[";
    for (std::size_t index = 0; index < inputs.size(); ++index) {
        if (index != 0U) out << ',';
        const auto input = inputs[index];
        const auto mapping = adapter.handleCc(
            controls, input.channel, input.cc, input.value);
        out << "{\"accepted_selected_lane\":"
            << static_cast<unsigned int>(controls.selected_lane)
            << ",\"cc\":" << input.cc
            << ",\"channel\":" << input.channel
            << ",\"continuous\":"
            << lab::finiteJsonNumber(mapping.continuous_value)
            << ",\"discrete\":"
            << static_cast<unsigned int>(mapping.discrete_value)
            << ",\"semantic\":"
            << static_cast<unsigned int>(mapping.semantic)
            << ",\"status\":" << jsonString(mappingStatusName(mapping.status))
            << ",\"value\":" << input.value << '}';
    }
    const auto diagnostics = adapter.diagnostics();
    out << "],\"diagnostics\":{\"accepted\":"
        << diagnostics.accepted_message_count
        << ",\"dispatched\":" << diagnostics.dispatched_message_count
        << ",\"ignored_channel\":" << diagnostics.ignored_channel_count
        << ",\"invalid\":" << diagnostics.invalid_message_count
        << ",\"unknown_cc\":" << diagnostics.unknown_cc_count << "}}\n";
    return out.str();
}

void writeOutputs(
    const fs::path& output,
    const std::string& condition,
    const Rendered& rendered) {
    if (fs::exists(output) && !fs::is_empty(output)) {
        throw std::runtime_error("output directory is not empty: " + output.string());
    }
    fs::create_directories(output);
    writeWav(output / "audio.wav", rendered.main_q27, rendered.auxiliary_q27);
    writeText(output / "events.json", eventsJson(condition, rendered.events));
    writeText(output / "snapshots.json", snapshotsJson(condition, rendered.snapshots));
    writeText(output / "metrics.json", metricsJson(condition, rendered));
    writeText(output / "controller-trace.json", controllerTraceJson());

    const std::array<std::string, 5> primary{{
        "audio.wav",
        "controller-trace.json",
        "events.json",
        "metrics.json",
        "snapshots.json",
    }};
    std::ostringstream manifest;
    manifest << "{\"condition\":" << jsonString(condition)
             << ",\"files\":{ ";
    for (std::size_t index = 0; index < primary.size(); ++index) {
        if (index != 0U) manifest << ',';
        manifest << jsonString(primary[index]) << ':'
                 << jsonString(fileSha256(output / primary[index]));
    }
    manifest << "},\"proposal_sha256\":" << jsonString(kProposalSha256)
             << ",\"renderer_revision\":2"
             << ",\"sample_rate_hz\":" << pam::kSampleRateHz
             << ",\"seed\":" << pam::kDefaultSeed
             << ",\"source_revision\":" << jsonString(kSourceRevision)
             << ",\"source_tree\":" << jsonString(kSourceTree) << "}\n";
    writeText(output / "manifest.json", manifest.str());

    const std::array<std::string, 6> all{{
        "audio.wav",
        "controller-trace.json",
        "events.json",
        "manifest.json",
        "metrics.json",
        "snapshots.json",
    }};
    std::ostringstream sums;
    for (const auto& name : all) {
        sums << fileSha256(output / name) << "  " << name << '\n';
    }
    writeText(output / "SHA256SUMS", sums.str());
}

struct Arguments final {
    std::string condition;
    std::size_t block_frames{};
    fs::path output;
};

[[nodiscard]] Arguments parseArguments(int argc, char** argv) {
    Arguments arguments{};
    for (int index = 1; index < argc; ++index) {
        const std::string token = argv[index];
        if (token == "--condition" && index + 1 < argc) {
            arguments.condition = argv[++index];
        } else if (token == "--block" && index + 1 < argc) {
            arguments.block_frames = static_cast<std::size_t>(std::stoul(argv[++index]));
        } else if (token == "--output" && index + 1 < argc) {
            arguments.output = argv[++index];
        } else {
            throw std::runtime_error("invalid renderer argument: " + token);
        }
    }
    if (arguments.condition.empty() || arguments.output.empty()) {
        throw std::runtime_error("--condition and --output are required");
    }
    if (arguments.block_frames == 0U
        || arguments.block_frames > pam::kMaximumHostBlockFrames) {
        throw std::runtime_error("--block must be in 1 through 512");
    }
    return arguments;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const auto arguments = parseArguments(argc, argv);
        const auto rendered = renderCondition(
            arguments.condition, arguments.block_frames);
        writeOutputs(arguments.output, arguments.condition, rendered);
        std::cout << "pamplist-render: " << arguments.condition
                  << " frames=" << rendered.main_q27.size()
                  << " output=" << arguments.output << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "pamplist-render: " << error.what() << '\n';
        return 1;
    }
}
