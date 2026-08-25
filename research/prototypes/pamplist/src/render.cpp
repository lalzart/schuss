#include "schuss/pamplist/activity_model.hpp"
#include "schuss/pamplist/control_map.hpp"
#include "schuss/pamplist/core.hpp"
#include "schuss/pamplist/ui_model.hpp"

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
    "a923b9665a6024d986a5ae8ac094aa9d41cd634de03c45c8ca954630ea43e917";
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
    std::uint64_t modulation_clamp_count{};
    std::uint64_t saturated_sample_count{};
    std::uint64_t non_finite_source_count{};
    std::uint64_t effect_clear_count{};
    std::uint64_t effect_recovery_count{};
    double maximum_mode_state_absolute{};
    double maximum_duck_envelope{};
    double dry_difference_energy{};
    float maximum_mode_frequency_hz{};
    float maximum_mode_pole{};
    std::uint8_t started_lane_mask{};
};

struct Rendered final {
    std::vector<std::int32_t> main_q27;
    std::vector<std::int32_t> auxiliary_q27;
    std::vector<RecordedEvent> events;
    std::vector<PartSnapshot> snapshots;
    std::vector<PartMetrics> parts;
    bool rng_interleave_equal{true};
    std::uint32_t rng_reference_final_state{};
    std::uint32_t rng_candidate_final_state{};
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

[[nodiscard]] bool sameVoice(
    const pam::VoiceControls& left,
    const pam::VoiceControls& right) noexcept {
    return left.engine == right.engine
        && left.note == right.note
        && left.harmonics == right.harmonics
        && left.timbre == right.timbre
        && left.morph == right.morph
        && left.decay == right.decay
        && left.lpg_colour == right.lpg_colour
        && left.level == right.level;
}

[[nodiscard]] bool sameLane(
    const pam::LaneControls& left,
    const pam::LaneControls& right) noexcept {
    return left.rate_index == right.rate_index
        && left.phase_u7 == right.phase_u7
        && left.shape == right.shape
        && left.hits == right.hits
        && left.rotation == right.rotation
        && left.probability == right.probability
        && left.repeat == right.repeat
        && left.amplitude == right.amplitude
        && left.routes == right.routes;
}

[[nodiscard]] bool sameCohesion(
    const pam::CohesionControls& left,
    const pam::CohesionControls& right) noexcept {
    return left.drive == right.drive
        && left.cohere == right.cohere
        && left.root_note == right.root_note
        && left.spread == right.spread
        && left.tail == right.tail
        && left.damping == right.damping
        && left.width == right.width
        && left.duck == right.duck;
}

[[nodiscard]] pam::Controls clearedControls() {
    auto controls = pam::defaultControls();
    for (auto& lane : controls.lanes) {
        lane.amplitude = 0.0F;
        lane.routes.fill(0.0F);
    }
    return controls;
}

void activateLane(
    pam::Controls& controls,
    std::size_t lane,
    std::uint8_t engine,
    float level,
    std::uint8_t rate,
    std::uint8_t phase,
    pam::Shape shape,
    std::uint8_t hits,
    std::uint8_t rotation,
    float note) {
    auto& lane_controls = controls.lanes[lane];
    lane_controls.rate_index = rate;
    lane_controls.phase_u7 = phase;
    lane_controls.shape = shape;
    lane_controls.hits = hits;
    lane_controls.rotation = rotation;
    lane_controls.probability = 1.0F;
    lane_controls.amplitude = 1.0F;
    lane_controls.routes.fill(0.0F);
    lane_controls.routes[static_cast<std::size_t>(pam::Destination::trigger)] = 1.0F;
    auto& voice = controls.voices[lane];
    voice.engine = engine;
    voice.note = note;
    voice.level = level;
}

[[nodiscard]] pam::Controls baseControls() {
    auto controls = clearedControls();
    controls.master_gain = 0.5F;
    activateLane(
        controls, 0U, 8U, 0.3F, 8U, 0U,
        pam::Shape::pulse, 4U, 0U, 48.0F);
    return controls;
}

[[nodiscard]] pam::Controls sevenVoiceControls() {
    auto controls = clearedControls();
    controls.master_gain = 0.35F;
    const std::array<std::uint8_t, pam::kLaneCount> engines{{
        0U, 3U, 6U, 9U, 12U, 15U, 21U,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> rates{{
        8U, 10U, 6U, 11U, 4U, 12U, 2U,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> phases{{
        0U, 17U, 31U, 47U, 63U, 79U, 97U,
    }};
    const std::array<pam::Shape, pam::kLaneCount> shapes{{
        pam::Shape::pulse,
        pam::Shape::triangle,
        pam::Shape::sine,
        pam::Shape::ramp,
        pam::Shape::exponential_decay,
        pam::Shape::sample_hold,
        pam::Shape::smooth_random,
    }};
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        activateLane(
            controls,
            lane,
            engines[lane],
            0.07F,
            rates[lane],
            phases[lane],
            shapes[lane],
            16U,
            static_cast<std::uint8_t>(lane * 2U),
            32.0F + static_cast<float>(lane * 6U));
        controls.voices[lane].harmonics = 0.15F + 0.1F * static_cast<float>(lane);
        controls.voices[lane].timbre = 0.8F - 0.08F * static_cast<float>(lane);
        controls.voices[lane].morph = 0.1F + 0.1F * static_cast<float>(lane);
        if (lane != 0U) {
            controls.lanes[lane].routes[lane] = lane == 2U ? -0.2F : 0.2F;
        }
    }
    return controls;
}

[[nodiscard]] pam::Controls cohesionControls(float cohere) {
    auto controls = sevenVoiceControls();
    controls.cohesion.drive = cohere == 0.0F ? 1.0F : 0.35F;
    controls.cohesion.cohere = cohere;
    controls.cohesion.root_note = 48.0F;
    controls.cohesion.spread = 0.45F;
    controls.cohesion.tail = 0.65F;
    controls.cohesion.damping = 0.40F;
    controls.cohesion.width = 0.70F;
    controls.cohesion.duck = 0.30F;
    return controls;
}

[[nodiscard]] pam::Controls sequenceControls() {
    auto controls = clearedControls();
    controls.master_gain = 0.65F;
    activateLane(
        controls, 0U, 8U, 0.3F, 8U, 0U,
        pam::Shape::pulse, 5U, 0U, 48.0F);
    return controls;
}

[[nodiscard]] pam::Controls globalResponseControls() {
    auto controls = clearedControls();
    const std::array<pam::Shape, pam::kLaneCount> shapes{{
        pam::Shape::pulse,
        pam::Shape::triangle,
        pam::Shape::sine,
        pam::Shape::ramp,
        pam::Shape::exponential_decay,
        pam::Shape::sample_hold,
        pam::Shape::smooth_random,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> rates{{
        8U, 10U, 6U, 11U, 4U, 12U, 2U,
    }};
    const std::array<std::uint8_t, pam::kLaneCount> models{{
        0U, 3U, 6U, 9U, 12U, 15U, 21U,
    }};
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        activateLane(
            controls,
            lane,
            models[lane],
            0.07F,
            rates[lane],
            static_cast<std::uint8_t>(lane * 13U),
            shapes[lane],
            static_cast<std::uint8_t>(5U + lane),
            static_cast<std::uint8_t>(lane * 2U),
            36.0F + static_cast<float>(lane * 4U));
        if (lane != 0U) {
            controls.lanes[lane].routes[lane] = lane == 2U ? -0.25F : 0.25F;
        }
    }
    controls.cohesion.drive = 0.35F;
    controls.cohesion.cohere = 0.8F;
    controls.cohesion.root_note = 48.0F;
    controls.cohesion.spread = 0.45F;
    controls.cohesion.tail = 0.65F;
    controls.cohesion.damping = 0.4F;
    controls.cohesion.width = 0.7F;
    controls.cohesion.duck = 0.3F;
    return controls;
}

void appendCorePart(
    Rendered& rendered,
    const std::string& part,
    pam::Core& core,
    const pam::Controls& controls,
    std::size_t frame_count,
    std::size_t block_frames) {
    const auto frame_offset = rendered.main_q27.size();
    const auto core_frame_start = core.snapshot().absolute_frame;
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
            event.absolute_frame += frame_offset - core_frame_start;
            rendered.events.push_back({part, event});
        }
        cursor += count;
    }
    const auto snapshot = core.snapshot();
    rendered.snapshots.push_back({part, snapshot});
    PartMetrics metrics{};
    metrics.part = part;
    metrics.frame_count = frame_count;
    metrics.trigger_count = snapshot.diagnostics.trigger_count;
    metrics.modulation_clamp_count =
        snapshot.diagnostics.modulation_clamp_count;
    metrics.saturated_sample_count =
        snapshot.diagnostics.saturated_sample_count;
    metrics.non_finite_source_count =
        snapshot.diagnostics.non_finite_source_count;
    metrics.effect_clear_count = snapshot.diagnostics.effect_clear_count;
    metrics.effect_recovery_count = snapshot.diagnostics.effect_recovery_count;
    metrics.maximum_mode_state_absolute =
        snapshot.cohesion.maximum_mode_state_absolute;
    metrics.maximum_duck_envelope =
        snapshot.cohesion.maximum_duck_envelope;
    metrics.dry_difference_energy =
        snapshot.cohesion.dry_difference_energy;
    for (std::size_t mode = 0; mode < pam::kCohesionModeCount; ++mode) {
        metrics.maximum_mode_frequency_hz = std::max(
            metrics.maximum_mode_frequency_hz,
            snapshot.cohesion.mode_frequencies_hz[mode]);
        metrics.maximum_mode_pole = std::max(
            metrics.maximum_mode_pole,
            snapshot.cohesion.mode_poles[mode]);
    }
    metrics.started_lane_mask = snapshot.started_lane_mask;
    for (std::size_t frame = start; frame < start + frame_count; ++frame) {
        const auto main_absolute = static_cast<std::int32_t>(std::abs(
            static_cast<std::int64_t>(rendered.main_q27[frame])));
        const auto auxiliary_absolute = static_cast<std::int32_t>(std::abs(
            static_cast<std::int64_t>(rendered.auxiliary_q27[frame])));
        metrics.peak_main_q27 = std::max(metrics.peak_main_q27, main_absolute);
        metrics.peak_auxiliary_q27 = std::max(
            metrics.peak_auxiliary_q27, auxiliary_absolute);
        metrics.nonzero_main += rendered.main_q27[frame] != 0 ? 1U : 0U;
        metrics.nonzero_auxiliary +=
            rendered.auxiliary_q27[frame] != 0 ? 1U : 0U;
    }
    rendered.parts.push_back(metrics);
}

void appendPart(
    Rendered& rendered,
    const std::string& part,
    const pam::Controls& controls,
    std::size_t frame_count,
    std::size_t block_frames) {
    pam::Core core;
    appendCorePart(
        rendered, part, core, controls, frame_count, block_frames);
}

void verifyRngIsolation(Rendered& rendered) {
    constexpr std::uint32_t seed = UINT32_C(0x13579bdf);
    pam::MacroVoice reference(seed);
    pam::MacroVoice candidate(seed);
    pam::MacroVoice interferer(UINT32_C(0x2468ace1));
    pam::MacroVoiceControls target{};
    target.engine = 17U;
    pam::MacroVoiceControls other = target;
    other.engine = 18U;
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> reference_main{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> reference_aux{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> candidate_main{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> candidate_aux{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> discard_main{};
    std::array<std::int32_t, pam::kMacroVoiceQuantumFrames> discard_aux{};
    for (std::size_t quantum = 0; quantum < 256U; ++quantum) {
        target.trigger = quantum == 0U || quantum % 17U == 0U;
        other.trigger = quantum == 0U || quantum % 7U == 0U;
        reference.process(target, reference_main, reference_aux);
        interferer.process(other, discard_main, discard_aux);
        candidate.process(target, candidate_main, candidate_aux);
        rendered.rng_interleave_equal = rendered.rng_interleave_equal
            && reference_main == candidate_main
            && reference_aux == candidate_aux
            && reference.randomState() == candidate.randomState();
    }
    rendered.rng_reference_final_state = reference.randomState();
    rendered.rng_candidate_final_state = candidate.randomState();
}

void appendSweep(Rendered& rendered, std::size_t block_frames) {
    pam::Core core;
    auto controls = sevenVoiceControls();
    controls.master_gain = 0.2F;
    for (auto& voice : controls.voices) voice.level = 0.025F;
    for (std::size_t step = 0; step < 64U; ++step) {
        const auto high = (step & 1U) != 0U;
        controls.cohesion.drive = high ? 1.0F : 0.0F;
        controls.cohesion.cohere = high ? 1.0F : 0.0F;
        controls.cohesion.root_note = high ? 84.0F : 24.0F;
        controls.cohesion.spread = high ? 1.0F : 0.0F;
        controls.cohesion.tail = high ? 1.0F : 0.0F;
        controls.cohesion.damping = high ? 1.0F : 0.0F;
        controls.cohesion.width = high ? 1.0F : 0.0F;
        controls.cohesion.duck = high ? 1.0F : 0.0F;
        appendCorePart(
            rendered,
            "sweep-" + std::to_string(step),
            core,
            controls,
            16U,
            std::min<std::size_t>(16U, block_frames));
    }
    appendCorePart(
        rendered,
        "sweep-settle",
        core,
        controls,
        131072U - 64U * 16U,
        block_frames);
}

[[nodiscard]] Rendered renderCondition(
    const std::string& condition,
    std::size_t block_frames) {
    Rendered rendered{};
    if (condition == "PAMP_R06_DRY_CMP") {
        auto controls = sevenVoiceControls();
        controls.cohesion.drive = 1.0F;
        controls.cohesion.cohere = 0.0F;
        controls.lane_control_mode = pam::LaneControlMode::voice;
        appendPart(rendered, "revision-05-dry-seven", controls, 131072U,
            block_frames);
    } else if (condition == "PAMP_R06_SEQUENCE") {
        const auto base = sequenceControls();
        appendPart(rendered, "phase-0", base, 96000U, block_frames);
        auto phase = base;
        phase.lanes[0].phase_u7 = 64U;
        appendPart(rendered, "phase-64", phase, 96000U, block_frames);
        auto rotated = base;
        rotated.lanes[0].rotation = 3U;
        appendPart(rendered, "rotate-3", rotated, 96000U, block_frames);
        auto trigger_triangle = base;
        trigger_triangle.lanes[0].shape = pam::Shape::triangle;
        appendPart(rendered, "trigger-only-triangle", trigger_triangle,
            96000U, block_frames);
        const std::array<std::pair<const char*, pam::Shape>, 7U> shapes{{
            {"routed-pulse", pam::Shape::pulse},
            {"routed-triangle", pam::Shape::triangle},
            {"routed-sine", pam::Shape::sine},
            {"routed-ramp", pam::Shape::ramp},
            {"routed-decay", pam::Shape::exponential_decay},
            {"routed-hold", pam::Shape::sample_hold},
            {"routed-smooth", pam::Shape::smooth_random},
        }};
        for (const auto& [part, shape] : shapes) {
            auto routed = base;
            routed.lanes[0].shape = shape;
            routed.lanes[0].routes[
                static_cast<std::size_t>(pam::Destination::pitch)] = 0.8F;
            appendPart(rendered, part, routed, 96000U, block_frames);
        }
    } else if (condition == "PAMP_R06_GLOBAL") {
        const auto baseline = globalResponseControls();
        const auto append_pair = [&rendered, &baseline, block_frames](
                const std::string& name,
                const auto& set_low,
                const auto& set_high) {
            auto low = baseline;
            auto high = baseline;
            set_low(low.cohesion);
            set_high(high.cohesion);
            appendPart(rendered, name + "-low", low, 65536U, block_frames);
            appendPart(rendered, name + "-high", high, 65536U, block_frames);
        };
        append_pair("drive",
            [](pam::CohesionControls& value) { value.drive = 0.0F; },
            [](pam::CohesionControls& value) { value.drive = 1.0F; });
        append_pair("root",
            [](pam::CohesionControls& value) { value.root_note = 24.0F; },
            [](pam::CohesionControls& value) { value.root_note = 84.0F; });
        append_pair("spread",
            [](pam::CohesionControls& value) { value.spread = 0.0F; },
            [](pam::CohesionControls& value) { value.spread = 1.0F; });
        append_pair("tail",
            [](pam::CohesionControls& value) { value.tail = 0.0F; },
            [](pam::CohesionControls& value) { value.tail = 1.0F; });
        append_pair("damping",
            [](pam::CohesionControls& value) { value.damping = 0.0F; },
            [](pam::CohesionControls& value) { value.damping = 1.0F; });
        append_pair("width",
            [](pam::CohesionControls& value) { value.width = 0.0F; },
            [](pam::CohesionControls& value) { value.width = 1.0F; });
        append_pair("duck",
            [](pam::CohesionControls& value) { value.duck = 0.0F; },
            [](pam::CohesionControls& value) { value.duck = 1.0F; });

        pam::Core clear_core;
        auto clear = cohesionControls(0.8F);
        clear.cohesion.drive = 0.25F;
        clear.cohesion.tail = 0.8F;
        appendCorePart(rendered, "clear-excitation", clear_core, clear,
            32768U, block_frames);
        for (auto& voice : clear.voices) voice.level = 0.0F;
        appendCorePart(rendered, "tail-before-clear", clear_core, clear,
            8192U, block_frames);
        ++clear.effect_clear_generation;
        appendCorePart(rendered, "after-clear", clear_core, clear,
            8192U, block_frames);

        pam::Core no_clear_core;
        auto no_clear = cohesionControls(0.8F);
        no_clear.cohesion.drive = 0.25F;
        no_clear.cohesion.tail = 0.8F;
        appendCorePart(rendered, "no-clear-excitation", no_clear_core,
            no_clear, 32768U, block_frames);
        for (auto& voice : no_clear.voices) voice.level = 0.0F;
        appendCorePart(rendered, "no-clear-tail", no_clear_core, no_clear,
            8192U, block_frames);
        appendCorePart(rendered, "no-clear-continue", no_clear_core,
            no_clear, 8192U, block_frames);
    } else if (condition == "PAMP_R06_ACTIVITY") {
        pam::Core core;
        auto controls = cohesionControls(0.72F);
        const std::array<std::size_t, 7U> intervals{{
            113U, 257U, 509U, 997U, 241U, 443U, 811U,
        }};
        for (std::size_t sample = 0U;
             sample < pam::kImpactHistoryCapacity + 8U;
             ++sample) {
            std::ostringstream part;
            part << "activity-" << std::setw(3) << std::setfill('0') << sample;
            appendCorePart(rendered, part.str(), core, controls,
                intervals[sample % intervals.size()], block_frames);
        }
        ++controls.effect_clear_generation;
        appendCorePart(rendered, "activity-clear", core, controls, 113U,
            block_frames);
        appendPart(rendered, "unstarted-rebase", clearedControls(), 4096U,
            block_frames);
    } else if (condition == "PAMP_R05_AUDIO_CMP") {
        auto controls = sevenVoiceControls();
        controls.cohesion.drive = 1.0F;
        controls.cohesion.cohere = 0.0F;
        controls.lane_control_mode = pam::LaneControlMode::voice;
        appendPart(rendered, "revision-04-dry-seven", controls, 131072U, block_frames);
    } else if (condition == "PAMP_R05_TRIGGER") {
        for (const auto value : {0, 63, 64, 127}) {
            auto controls = pam::defaultControls();
            controls.lanes[0].rate_index = 13U;
            controls.lanes[0].hits = 16U;
            pam::ControllerAdapter adapter;
            static_cast<void>(adapter.handleCc(controls, 16, 40, 127));
            static_cast<void>(adapter.handleCc(controls, 16, 40, 0));
            static_cast<void>(adapter.handleCc(controls, 16, 20, value));
            appendPart(
                rendered,
                "trigger-cc" + std::to_string(value),
                controls,
                8192U,
                block_frames);
        }
    } else if (condition == "PAMP_R05_SURFACE") {
        auto voice = sevenVoiceControls();
        voice.lane_control_mode = pam::LaneControlMode::voice;
        appendPart(rendered, "surface-voice", voice, 16384U, block_frames);
        auto motion = voice;
        motion.lane_control_mode = pam::LaneControlMode::motion;
        appendPart(rendered, "surface-motion", motion, 16384U, block_frames);
    } else if (condition == "PAMP_R05_GLOBAL") {
        auto lane = cohesionControls(0.72F);
        lane.lane_control_mode = pam::LaneControlMode::motion;
        appendPart(rendered, "lane-motion", lane, 16384U, block_frames);
        auto global = lane;
        global.selected_page = pam::kGlobalPageIndex;
        appendPart(rendered, "global-motion", global, 16384U, block_frames);
    } else if (condition == "PAMP_R04_DRY7") {
        auto controls = sevenVoiceControls();
        controls.cohesion.drive = 1.0F;
        controls.cohesion.cohere = 0.0F;
        appendPart(rendered, "dry-seven", controls, 131072U, block_frames);
    } else if (condition == "PAMP_R04_GLOBAL_ISOLATION") {
        auto controls = baseControls();
        controls.selected_page = pam::kGlobalPageIndex;
        appendPart(
            rendered, "global-map-audio-reference", controls, 16384U, block_frames);
    } else if (condition == "PAMP_R04_COHERE") {
        appendPart(
            rendered,
            "cohesion-active",
            cohesionControls(0.72F),
            131072U,
            block_frames);
    } else if (condition == "PAMP_R04_CLEAR") {
        pam::Core core;
        auto controls = cohesionControls(0.8F);
        controls.cohesion.drive = 0.25F;
        controls.cohesion.tail = 0.8F;
        appendCorePart(
            rendered, "clear-excitation", core, controls, 32768U, block_frames);
        for (auto& voice : controls.voices) voice.level = 0.0F;
        appendCorePart(
            rendered, "tail-before-clear", core, controls, 8192U, block_frames);
        ++controls.effect_clear_generation;
        appendCorePart(
            rendered, "after-clear", core, controls, 8192U, block_frames);
    } else if (condition == "PAMP_R04_SWEEP") {
        appendSweep(rendered, block_frames);
    } else if (condition == "PAMP_R04_24") {
        for (std::uint8_t engine = 0U; engine < 24U; ++engine) {
            auto controls = clearedControls();
            controls.master_gain = 0.5F;
            activateLane(
                controls, 0U, engine, 0.3F, 13U, 0U,
                pam::Shape::pulse, 16U, 0U, 48.0F);
            std::ostringstream part;
            part << "model-" << std::setw(2) << std::setfill('0')
                 << static_cast<unsigned int>(engine) << '-'
                 << pam::modelName(engine);
            appendPart(rendered, part.str(), controls, 8192U, block_frames);
        }
        verifyRngIsolation(rendered);
    } else if (condition == "PAMP_R04_SILENCE") {
        auto stopped = pam::defaultControls();
        stopped.running = false;
        stopped.cohesion.cohere = 1.0F;
        appendPart(rendered, "stopped", stopped, 8192U, block_frames);
        auto zero_hit = pam::defaultControls();
        zero_hit.lanes[0].hits = 0U;
        zero_hit.cohesion.cohere = 1.0F;
        appendPart(rendered, "zero-hit", zero_hit, 8192U, block_frames);
        auto zero_amplitude = pam::defaultControls();
        zero_amplitude.lanes[0].amplitude = 0.0F;
        zero_amplitude.cohesion.cohere = 1.0F;
        appendPart(
            rendered, "zero-amplitude", zero_amplitude, 8192U, block_frames);
        auto zero_route = pam::defaultControls();
        zero_route.lanes[0].routes.fill(0.0F);
        zero_route.cohesion.cohere = 1.0F;
        appendPart(
            rendered, "zero-trigger-route", zero_route, 8192U, block_frames);
    } else if (condition == "PAMP_R04_DRY_CMP") {
        appendPart(
            rendered,
            "cohesion-dry-comparator",
            cohesionControls(0.0F),
            131072U,
            block_frames);
    } else {
        throw std::runtime_error("unknown condition: " + condition);
    }
    return rendered;
}

void writeUnsignedArray(
    std::ostringstream& out,
    const std::array<std::uint8_t, pam::kLaneCount>& values) {
    out << '[';
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index != 0U) out << ',';
        out << static_cast<unsigned int>(values[index]);
    }
    out << ']';
}

void writeEngineNames(
    std::ostringstream& out,
    const std::array<std::uint8_t, pam::kLaneCount>& values) {
    out << '[';
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index != 0U) out << ',';
        out << jsonString(pam::modelName(values[index]));
    }
    out << ']';
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
        out << "{\"accepted_mask\":"
            << static_cast<unsigned int>(event.accepted_mask)
            << ",\"absolute_frame\":" << event.absolute_frame
            << ",\"addresses\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            out << event.addresses[lane];
        }
        out << "],\"boundary_mask\":"
            << static_cast<unsigned int>(event.boundary_mask)
            << ",\"effect_clear_generation\":"
            << event.effect_clear_generation
            << ",\"effect_cleared\":"
            << (event.effect_cleared ? "true" : "false")
            << ",\"part\":" << jsonString(recorded.part)
            << ",\"resolved_model_names\":";
        writeEngineNames(out, event.resolved_engines);
        out << ",\"resolved_models\":";
        writeUnsignedArray(out, event.resolved_engines);
        out << ",\"started_lane_mask\":"
            << static_cast<unsigned int>(event.started_lane_mask)
            << ",\"steps\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            out << event.steps[lane];
        }
        out << "],\"trigger_lane_mask\":"
            << static_cast<unsigned int>(event.trigger_lane_mask) << '}';
    }
    out << "]}\n";
    return out.str();
}

void voiceJson(std::ostringstream& out, const pam::VoiceControls& voice) {
    out << "{\"decay\":" << lab::finiteJsonNumber(voice.decay)
        << ",\"model\":" << static_cast<unsigned int>(voice.engine)
        << ",\"model_name\":" << jsonString(pam::modelName(voice.engine))
        << ",\"harmonics\":" << lab::finiteJsonNumber(voice.harmonics)
        << ",\"level\":" << lab::finiteJsonNumber(voice.level)
        << ",\"lpg_colour\":" << lab::finiteJsonNumber(voice.lpg_colour)
        << ",\"morph\":" << lab::finiteJsonNumber(voice.morph)
        << ",\"note\":" << lab::finiteJsonNumber(voice.note)
        << ",\"timbre\":" << lab::finiteJsonNumber(voice.timbre) << '}';
}

void controlsJson(std::ostringstream& out, const pam::Controls& controls) {
    out << "{\"cohesion\":{\"damping\":"
        << lab::finiteJsonNumber(controls.cohesion.damping)
        << ",\"drive\":" << lab::finiteJsonNumber(controls.cohesion.drive)
        << ",\"duck\":" << lab::finiteJsonNumber(controls.cohesion.duck)
        << ",\"cohere\":" << lab::finiteJsonNumber(controls.cohesion.cohere)
        << ",\"root_note\":"
        << lab::finiteJsonNumber(controls.cohesion.root_note)
        << ",\"spread\":" << lab::finiteJsonNumber(controls.cohesion.spread)
        << ",\"tail\":" << lab::finiteJsonNumber(controls.cohesion.tail)
        << ",\"width\":" << lab::finiteJsonNumber(controls.cohesion.width)
        << "},\"effect_clear_generation\":"
        << controls.effect_clear_generation
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
    out << "],\"master_gain\":" << lab::finiteJsonNumber(controls.master_gain)
        << ",\"running\":" << (controls.running ? "true" : "false")
        << ",\"seed\":" << controls.seed
        << ",\"selected_page\":"
        << static_cast<unsigned int>(controls.selected_page)
        << ",\"lane_control_mode\":"
        << static_cast<unsigned int>(controls.lane_control_mode)
        << ",\"tempo_milli_bpm\":" << controls.tempo_milli_bpm
        << ",\"voices\":[";
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        if (lane != 0U) out << ',';
        voiceJson(out, controls.voices[lane]);
    }
    out << "]}";
}

template <typename Value, std::size_t Count>
void writeNumericArray(
    std::ostringstream& out,
    const std::array<Value, Count>& values) {
    out << '[';
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index != 0U) out << ',';
        out << values[index];
    }
    out << ']';
}

template <std::size_t Count>
void writeFloatArray(
    std::ostringstream& out,
    const std::array<float, Count>& values) {
    out << '[';
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index != 0U) out << ',';
        out << lab::finiteJsonNumber(values[index]);
    }
    out << ']';
}

template <std::size_t Count>
void writeDoubleArray(
    std::ostringstream& out,
    const std::array<double, Count>& values) {
    out << '[';
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index != 0U) out << ',';
        out << lab::finiteJsonNumber(values[index]);
    }
    out << ']';
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
            << ",\"invalid_control_count\":"
            << value.diagnostics.invalid_control_count
            << ",\"lane_trigger_count\":";
        writeNumericArray(out, value.diagnostics.lane_trigger_count);
        out << ",\"modulation_clamp_count\":"
            << value.diagnostics.modulation_clamp_count
            << ",\"effect_clear_count\":"
            << value.diagnostics.effect_clear_count
            << ",\"effect_recovery_count\":"
            << value.diagnostics.effect_recovery_count
            << ",\"non_finite_source_count\":"
            << value.diagnostics.non_finite_source_count
            << ",\"saturated_sample_count\":"
            << value.diagnostics.saturated_sample_count
            << ",\"trigger_count\":" << value.diagnostics.trigger_count
            << ",\"unsupported_process_count\":"
            << value.diagnostics.unsupported_process_count << '}'
            << ",\"lane_addresses\":";
        writeNumericArray(out, value.lane_addresses);
        out << ",\"lane_output_energy\":";
        writeDoubleArray(out, value.lane_output_energy);
        out << ",\"lane_phase_q32\":";
        writeNumericArray(out, value.lane_phase_q32);
        out << ",\"lane_remainders\":";
        writeNumericArray(out, value.lane_remainders);
        out << ",\"lane_steps\":";
        writeNumericArray(out, value.lane_steps);
        out << ",\"lane_values\":";
        writeFloatArray(out, value.lane_values);
        out << ",\"modulation_values\":[";
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (lane != 0U) out << ',';
            writeFloatArray(out, value.modulation_values[lane]);
        }
        out << ']';
        out << ",\"master_phase_q32\":" << value.master_phase_q32
            << ",\"master_remainder\":" << value.master_remainder
            << ",\"cohesion\":{\"applied_clear_generation\":"
            << value.cohesion.applied_clear_generation
            << ",\"dry_difference_energy\":"
            << lab::finiteJsonNumber(value.cohesion.dry_difference_energy)
            << ",\"duck_envelope\":"
            << lab::finiteJsonNumber(value.cohesion.duck_envelope)
            << ",\"maximum_duck_envelope\":"
            << lab::finiteJsonNumber(value.cohesion.maximum_duck_envelope)
            << ",\"maximum_mode_state_absolute\":"
            << lab::finiteJsonNumber(
                value.cohesion.maximum_mode_state_absolute)
            << ",\"mode_frequencies_hz\":";
        writeFloatArray(out, value.cohesion.mode_frequencies_hz);
        out << ",\"mode_imaginary\":";
        writeFloatArray(out, value.cohesion.mode_imaginary);
        out << ",\"mode_poles\":";
        writeFloatArray(out, value.cohesion.mode_poles);
        out << ",\"mode_real\":";
        writeFloatArray(out, value.cohesion.mode_real);
        out << ",\"smoothed\":{\"cohere\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_cohere)
            << ",\"damping\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_damping)
            << ",\"drive\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_drive)
            << ",\"duck\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_duck)
            << ",\"master_gain\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_master_gain)
            << ",\"root_note\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_root_note)
            << ",\"spread\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_spread)
            << ",\"tail\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_tail)
            << ",\"width\":"
            << lab::finiteJsonNumber(value.cohesion.smoothed_width)
            << "}}"
            << ",\"part\":" << jsonString(recorded.part)
            << ",\"quantum_count\":" << value.quantum_count
            << ",\"rendered_through_frame\":" << value.rendered_through_frame
            << ",\"resolved_model_names\":";
        writeEngineNames(out, value.resolved_engines);
        out << ",\"resolved_models\":";
        writeUnsignedArray(out, value.resolved_engines);
        out << ",\"resolved_levels\":";
        writeFloatArray(out, value.resolved_levels);
        out << ",\"resolved_notes\":";
        writeFloatArray(out, value.resolved_notes);
        out << ",\"source_random_states\":";
        writeNumericArray(out, value.source_random_states);
        out << ",\"started_lane_mask\":"
            << static_cast<unsigned int>(value.started_lane_mask)
            << ",\"trigger_lane_mask\":"
            << static_cast<unsigned int>(value.trigger_lane_mask) << '}';
    }
    out << "]}\n";
    return out.str();
}

[[nodiscard]] std::string activityJson(
    const std::string& condition,
    const std::vector<PartSnapshot>& snapshots) {
    pam::ActivityReducer reducer;
    pam::ImpactHistory history;
    std::vector<std::pair<std::string, pam::ActivitySample>> samples;
    std::size_t maximum_history_size = 0U;
    std::size_t history_size_before_rebase = 0U;
    std::uint64_t oldest_before_rebase = 0U;
    std::uint64_t newest_before_rebase = 0U;
    for (const auto& recorded : snapshots) {
        const auto sample = reducer.reduce(recorded.snapshot);
        samples.emplace_back(recorded.part, sample);
        if (sample.rebased) {
            history_size_before_rebase = history.size();
            if (history.size() != 0U) {
                oldest_before_rebase = history.oldest(0U).frame_count;
                newest_before_rebase = history.oldest(history.size() - 1U).frame_count;
            }
            history.clear();
        }
        if (sample.frame_count != 0U) history.push(sample);
        maximum_history_size = std::max(maximum_history_size, history.size());
    }

    std::ostringstream out;
    out << "{\"condition\":" << jsonString(condition)
        << ",\"history\":{\"capacity\":" << pam::kImpactHistoryCapacity
        << ",\"final_size\":" << history.size()
        << ",\"maximum_size\":" << maximum_history_size
        << ",\"newest_frame_count_before_rebase\":"
        << newest_before_rebase
        << ",\"oldest_frame_count_before_rebase\":"
        << oldest_before_rebase
        << ",\"size_before_rebase\":" << history_size_before_rebase
        << "},\"samples\":[";
    for (std::size_t index = 0; index < samples.size(); ++index) {
        if (index != 0U) out << ',';
        const auto& [part, sample] = samples[index];
        out << "{\"cohesion_level\":"
            << lab::finiteJsonNumber(sample.cohesion_level)
            << ",\"effect_cleared\":"
            << (sample.effect_cleared ? "true" : "false")
            << ",\"frame_count\":" << sample.frame_count
            << ",\"lane_levels\":";
        writeFloatArray(out, sample.lane_levels);
        out << ",\"part\":" << jsonString(part)
            << ",\"rebased\":" << (sample.rebased ? "true" : "false")
            << ",\"trigger_deltas\":";
        writeNumericArray(out, sample.trigger_deltas);
        out << ",\"trigger_mask\":"
            << static_cast<unsigned int>(sample.trigger_mask) << '}';
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
    std::uint64_t saturated_frames = 0U;
    std::uint64_t diagnostic_saturated_samples = 0U;
    std::uint64_t effect_clear_count = 0U;
    std::uint64_t effect_recovery_count = 0U;
    double maximum_mode_state_absolute = 0.0;
    double maximum_duck_envelope = 0.0;
    double dry_difference_energy = 0.0;
    float maximum_mode_frequency_hz = 0.0F;
    float maximum_mode_pole = 0.0F;
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
        saturated_frames += (main == pam::kQ27Maximum || main == pam::kQ27Minimum
            || auxiliary == pam::kQ27Maximum || auxiliary == pam::kQ27Minimum)
            ? 1U : 0U;
    }
    for (const auto& part : rendered.parts) {
        diagnostic_saturated_samples += part.saturated_sample_count;
        effect_clear_count = std::max(
            effect_clear_count, part.effect_clear_count);
        effect_recovery_count += part.effect_recovery_count;
        maximum_mode_state_absolute = std::max(
            maximum_mode_state_absolute, part.maximum_mode_state_absolute);
        maximum_duck_envelope = std::max(
            maximum_duck_envelope, part.maximum_duck_envelope);
        dry_difference_energy = std::max(
            dry_difference_energy, part.dry_difference_energy);
        maximum_mode_frequency_hz = std::max(
            maximum_mode_frequency_hz, part.maximum_mode_frequency_hz);
        maximum_mode_pole = std::max(
            maximum_mode_pole, part.maximum_mode_pole);
    }
    const auto frames = static_cast<long double>(rendered.main_q27.size());
    const auto normalized = static_cast<long double>(UINT32_C(1) << 27);
    std::ostringstream out;
    out << "{\"condition\":" << jsonString(condition)
        << ",\"dc_auxiliary\":"
        << lab::finiteJsonNumber(static_cast<double>(sum_auxiliary / frames / normalized))
        << ",\"dc_main\":"
        << lab::finiteJsonNumber(static_cast<double>(sum_main / frames / normalized))
        << ",\"diagnostic_saturated_sample_count\":"
        << diagnostic_saturated_samples
        << ",\"dry_difference_energy\":"
        << lab::finiteJsonNumber(dry_difference_energy)
        << ",\"effect_clear_count\":" << effect_clear_count
        << ",\"effect_recovery_count\":" << effect_recovery_count
        << ",\"finite_samples_percent\":100"
        << ",\"frame_count\":" << rendered.main_q27.size()
        << ",\"parts\":[";
    for (std::size_t index = 0; index < rendered.parts.size(); ++index) {
        if (index != 0U) out << ',';
        const auto& part = rendered.parts[index];
        out << "{\"frame_count\":" << part.frame_count
            << ",\"dry_difference_energy\":"
            << lab::finiteJsonNumber(part.dry_difference_energy)
            << ",\"effect_clear_count\":" << part.effect_clear_count
            << ",\"effect_recovery_count\":" << part.effect_recovery_count
            << ",\"maximum_duck_envelope\":"
            << lab::finiteJsonNumber(part.maximum_duck_envelope)
            << ",\"maximum_mode_frequency_hz\":"
            << lab::finiteJsonNumber(part.maximum_mode_frequency_hz)
            << ",\"maximum_mode_pole\":"
            << lab::finiteJsonNumber(part.maximum_mode_pole)
            << ",\"maximum_mode_state_absolute\":"
            << lab::finiteJsonNumber(part.maximum_mode_state_absolute)
            << ",\"modulation_clamp_count\":" << part.modulation_clamp_count
            << ",\"non_finite_source_count\":" << part.non_finite_source_count
            << ",\"nonzero_auxiliary\":" << part.nonzero_auxiliary
            << ",\"nonzero_main\":" << part.nonzero_main
            << ",\"part\":" << jsonString(part.part)
            << ",\"peak_auxiliary_q27\":" << part.peak_auxiliary_q27
            << ",\"peak_main_q27\":" << part.peak_main_q27
            << ",\"saturated_sample_count\":" << part.saturated_sample_count
            << ",\"started_lane_mask\":"
            << static_cast<unsigned int>(part.started_lane_mask)
            << ",\"trigger_count\":" << part.trigger_count << '}';
    }
    out << "]"
        << ",\"maximum_duck_envelope\":"
        << lab::finiteJsonNumber(maximum_duck_envelope)
        << ",\"maximum_mode_frequency_hz\":"
        << lab::finiteJsonNumber(maximum_mode_frequency_hz)
        << ",\"maximum_mode_pole\":"
        << lab::finiteJsonNumber(maximum_mode_pole)
        << ",\"maximum_mode_state_absolute\":"
        << lab::finiteJsonNumber(maximum_mode_state_absolute)
        << ",\"peak_auxiliary_q27\":" << peak_auxiliary
        << ",\"peak_main_q27\":" << peak_main
        << ",\"rms_auxiliary\":"
        << lab::finiteJsonNumber(static_cast<double>(
            std::sqrt(square_auxiliary / frames) / normalized))
        << ",\"rms_main\":"
        << lab::finiteJsonNumber(static_cast<double>(
            std::sqrt(square_main / frames) / normalized))
        << ",\"rng_candidate_final_state\":"
        << rendered.rng_candidate_final_state
        << ",\"rng_interleave_equal\":"
        << (rendered.rng_interleave_equal ? "true" : "false")
        << ",\"rng_reference_final_state\":"
        << rendered.rng_reference_final_state
        << ",\"saturated_frame_count\":" << saturated_frames << "}\n";
    return out.str();
}

[[nodiscard]] const char* mappingStatusName(pam::MappingStatus status) {
    switch (status) {
        case pam::MappingStatus::accepted_continuous: return "accepted-continuous";
        case pam::MappingStatus::accepted_press: return "accepted-press";
        case pam::MappingStatus::accepted_release: return "accepted-release";
        case pam::MappingStatus::accepted_hold: return "accepted-hold";
        case pam::MappingStatus::accepted_noop: return "accepted-noop";
        case pam::MappingStatus::ignored_channel: return "ignored-channel";
        case pam::MappingStatus::unknown_cc: return "unknown-cc";
        case pam::MappingStatus::invalid_message: return "invalid-message";
    }
    return "invalid-status";
}

[[nodiscard]] std::string controllerTraceJson() {
    struct Input final {
        std::string phase;
        int channel;
        int cc;
        int value;
    };
    std::vector<Input> inputs;
    const std::array<int, 4U> representative_values{{0, 63, 64, 127}};
    for (int cc = 20; cc <= 27; ++cc) {
        for (const auto value : representative_values) {
            inputs.push_back({"voice-top", 16, cc, value});
        }
    }
    inputs.push_back({"toggle-motion", 16, 40, 127});
    inputs.push_back({"toggle-motion-hold", 16, 40, 127});
    inputs.push_back({"toggle-motion-release", 16, 40, 0});
    for (int cc = 20; cc <= 27; ++cc) {
        for (const auto value : representative_values) {
            inputs.push_back({"motion-top", 16, cc, value});
        }
    }
    for (int cc = 28; cc <= 35; ++cc) {
        for (const auto value : representative_values) {
            inputs.push_back({"sequencer-motion", 16, cc, value});
        }
    }
    inputs.push_back({"select-lane-2", 16, 41, 127});
    inputs.push_back({"select-lane-2-release", 16, 41, 0});
    inputs.push_back({"toggle-lane-2-voice", 16, 41, 127});
    inputs.push_back({"toggle-lane-2-voice-hold", 16, 41, 127});
    inputs.push_back({"toggle-lane-2-voice-release", 16, 41, 0});
    for (int cc = 28; cc <= 35; ++cc) {
        for (const auto value : representative_values) {
            inputs.push_back({"sequencer-voice", 16, cc, value});
        }
    }
    inputs.push_back({"restore-motion", 16, 41, 127});
    inputs.push_back({"restore-motion-release", 16, 41, 0});
    inputs.push_back({"enter-global", 16, 47, 127});
    inputs.push_back({"enter-global-hold", 16, 47, 127});
    inputs.push_back({"enter-global-release", 16, 47, 0});
    for (int cc = 20; cc <= 35; ++cc) {
        for (const auto value : representative_values) {
            inputs.push_back({"global", 16, cc, value});
        }
    }
    inputs.push_back({"clear-global", 16, 47, 127});
    inputs.push_back({"clear-global-hold", 16, 47, 127});
    inputs.push_back({"clear-global-release", 16, 47, 0});
    inputs.push_back({"return-lane-1", 16, 40, 127});
    inputs.push_back({"return-lane-1-release", 16, 40, 0});
    inputs.push_back({"wrong-channel", 1, 20, 64});
    inputs.push_back({"unknown-cc", 16, 39, 64});
    inputs.push_back({"invalid-value", 16, 20, 128});
    auto controls = pam::defaultControls();
    pam::ControllerAdapter adapter;
    std::ostringstream out;
    out << "{\"control_map_sha256\":" << jsonString(pam::controlMapSha256())
        << ",\"controller_topology_sha256\":"
        << jsonString(pam::controllerTopologySha256()) << ",\"messages\":[";
    for (std::size_t index = 0; index < inputs.size(); ++index) {
        if (index != 0U) out << ',';
        const auto input = inputs[index];
        const auto before = controls;
        const auto mapping = adapter.handleCc(
            controls, input.channel, input.cc, input.value);
        std::uint8_t voice_change_mask = 0U;
        std::uint8_t lane_change_mask = 0U;
        for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
            if (!sameVoice(before.voices[lane], controls.voices[lane])) {
                voice_change_mask = static_cast<std::uint8_t>(
                    voice_change_mask | (1U << lane));
            }
            if (!sameLane(before.lanes[lane], controls.lanes[lane])) {
                lane_change_mask = static_cast<std::uint8_t>(
                    lane_change_mask | (1U << lane));
            }
        }
        out << "{\"accepted_clear_generation\":"
            << controls.effect_clear_generation
            << ",\"accepted_lane_control_mode\":"
            << static_cast<unsigned int>(controls.lane_control_mode)
            << ",\"accepted_selected_page\":"
            << static_cast<unsigned int>(controls.selected_page)
            << ",\"before_clear_generation\":"
            << before.effect_clear_generation
            << ",\"before_lane_control_mode\":"
            << static_cast<unsigned int>(before.lane_control_mode)
            << ",\"before_selected_page\":"
            << static_cast<unsigned int>(before.selected_page)
            << ",\"cc\":" << input.cc
            << ",\"channel\":" << input.channel
            << ",\"cohesion_unchanged\":"
            << (sameCohesion(before.cohesion, controls.cohesion)
                    ? "true" : "false")
            << ",\"continuous\":"
            << lab::finiteJsonNumber(mapping.continuous_value)
            << ",\"discrete\":"
            << static_cast<unsigned int>(mapping.discrete_value)
            << ",\"integer\":" << mapping.integer_value
            << ",\"lane_change_mask\":"
            << static_cast<unsigned int>(lane_change_mask)
            << ",\"page\":" << static_cast<unsigned int>(mapping.page)
            << ",\"phase\":" << jsonString(input.phase)
            << ",\"semantic\":"
            << static_cast<unsigned int>(mapping.semantic)
            << ",\"status\":" << jsonString(mappingStatusName(mapping.status))
            << ",\"surface_context\":"
            << jsonString(pam::surfaceContextName(
                controls.selected_page == pam::kGlobalPageIndex
                    ? pam::SurfaceContext::global
                    : controls.lane_control_mode == pam::LaneControlMode::voice
                        ? pam::SurfaceContext::voice
                        : pam::SurfaceContext::motion))
            << ",\"surface_slot_count\":" << pam::kSurfaceRotaryCount
            << ",\"value\":" << input.value
            << ",\"voice_change_mask\":"
            << static_cast<unsigned int>(voice_change_mask) << '}';
    }
    const auto diagnostics = adapter.diagnostics();
    out << "],\"diagnostics\":{\"accepted\":"
        << diagnostics.accepted_message_count
        << ",\"dispatched\":" << diagnostics.dispatched_message_count
        << ",\"ignored_channel\":" << diagnostics.ignored_channel_count
        << ",\"ignored_global\":"
        << diagnostics.ignored_global_control_count
        << ",\"invalid\":" << diagnostics.invalid_message_count
        << ",\"unknown_cc\":" << diagnostics.unknown_cc_count << "}}\n";
    return out.str();
}

[[nodiscard]] std::string surfaceSlotsJson(
    const std::array<pam::SurfaceSlot, pam::kSurfaceColumnCount>& slots) {
    std::ostringstream out;
    out << '[';
    for (std::size_t column = 0; column < slots.size(); ++column) {
        if (column != 0U) out << ',';
        const auto& slot = slots[column];
        out << "{\"column\":" << column
            << ",\"enabled\":" << (slot.enabled ? "true" : "false")
            << ",\"interval\":" << lab::finiteJsonNumber(slot.interval)
            << ",\"label\":" << jsonString(slot.label)
            << ",\"maximum\":" << lab::finiteJsonNumber(slot.maximum)
            << ",\"minimum\":" << lab::finiteJsonNumber(slot.minimum)
            << ",\"presentation\":"
            << static_cast<unsigned int>(slot.presentation)
            << ",\"semantic\":"
            << static_cast<unsigned int>(slot.semantic)
            << ",\"tooltip\":" << jsonString(slot.tooltip)
            << ",\"value\":" << lab::finiteJsonNumber(slot.value) << '}';
    }
    out << ']';
    return out.str();
}

[[nodiscard]] std::string surfaceJson(const std::string& condition) {
    std::array<pam::Controls, 3U> controls{{
        pam::defaultControls(),
        pam::defaultControls(),
        pam::defaultControls(),
    }};
    controls[1].lane_control_mode = pam::LaneControlMode::motion;
    controls[2].selected_page = pam::kGlobalPageIndex;
    std::ostringstream out;
    out << "{\"condition\":" << jsonString(condition)
        << ",\"contexts\":[";
    for (std::size_t index = 0; index < controls.size(); ++index) {
        if (index != 0U) out << ',';
        pam::Snapshot snapshot{};
        snapshot.accepted = pam::sanitizeControls(controls[index]);
        const auto model = pam::surfaceModel(snapshot);
        out << "{\"bottom_group\":" << jsonString(model.bottom_group)
            << ",\"bottom_slots\":" << surfaceSlotsJson(model.bottom)
            << ",\"context\":" << jsonString(pam::surfaceContextName(model.context))
            << ",\"guide\":" << jsonString(model.guide)
            << ",\"rotary_slot_count\":" << pam::kSurfaceRotaryCount
            << ",\"top_group\":" << jsonString(model.top_group)
            << ",\"top_slots\":" << surfaceSlotsJson(model.top) << '}';
    }
    out << "]}\n";
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
    writeText(output / "activity.json", activityJson(condition, rendered.snapshots));
    writeText(output / "controller-trace.json", controllerTraceJson());
    writeText(output / "surface.json", surfaceJson(condition));

    const std::array<std::string, 7> primary{{
        "activity.json",
        "audio.wav",
        "controller-trace.json",
        "events.json",
        "metrics.json",
        "snapshots.json",
        "surface.json",
    }};
    std::ostringstream manifest;
    manifest << "{\"condition\":" << jsonString(condition)
             << ",\"control_map_sha256\":"
             << jsonString(pam::controlMapSha256())
             << ",\"model_names\":[";
    for (std::uint8_t model = 0U; model < 24U; ++model) {
        if (model != 0U) manifest << ',';
        manifest << jsonString(pam::modelName(model));
    }
    manifest << "],\"files\":{";
    for (std::size_t index = 0; index < primary.size(); ++index) {
        if (index != 0U) manifest << ',';
        manifest << jsonString(primary[index]) << ':'
                 << jsonString(fileSha256(output / primary[index]));
    }
    manifest << "},\"predecessor_audio_sha256\":"
             << jsonString(
                 "a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912")
             << ",\"proposal_sha256\":" << jsonString(kProposalSha256)
             << ",\"renderer_revision\":6"
             << ",\"sample_rate_hz\":" << pam::kSampleRateHz
             << ",\"seed\":" << pam::kDefaultSeed
             << ",\"source_revision\":" << jsonString(kSourceRevision)
             << ",\"source_tree\":" << jsonString(kSourceTree) << "}\n";
    writeText(output / "manifest.json", manifest.str());

    const std::array<std::string, 8> all{{
        "activity.json",
        "audio.wav",
        "controller-trace.json",
        "events.json",
        "manifest.json",
        "metrics.json",
        "snapshots.json",
        "surface.json",
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
            arguments.block_frames = static_cast<std::size_t>(
                std::stoul(argv[++index]));
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
