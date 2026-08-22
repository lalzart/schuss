#include "wirefall/core.hpp"

#include "schuss/instrument_lab/renderer_artifacts.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace fs = std::filesystem;

struct ScheduledEvent {
    std::uint64_t sample{};
    wirefall::Event event{};
};

struct Condition {
    std::string id;
    std::string mechanism;
    std::uint64_t duration_frames{};
    std::vector<ScheduledEvent> events;
};

struct RenderedCondition {
    std::vector<float> left;
    std::vector<float> right;
    std::vector<wirefall::LedgerEvent> ledger;
    wirefall::Diagnostics diagnostics{};
    std::string normalized_state_sha256;
    std::string full_state_sha256;
    double rms{};
    double abs_peak{};
    std::array<double, 2> dc_mean{};
};

struct Options {
    fs::path fixture;
    fs::path output_directory;
    std::uint32_t block_frames{64};
    std::uint32_t oversample_factor{4};
    bool parallel_gain_supplied{};
    float parallel_gain{1.0f};
    bool parallel_target_supplied{};
    double parallel_target_rms{};
    std::string output_prefix;
};

std::vector<std::string> split(std::string_view text, char separator) {
    std::vector<std::string> values;
    std::size_t start = 0;
    while (start <= text.size()) {
        const auto end = text.find(separator, start);
        values.emplace_back(text.substr(start, end == std::string_view::npos ? text.size() - start : end - start));
        if (end == std::string_view::npos) break;
        start = end + 1U;
    }
    return values;
}

std::uint64_t parseUnsigned(const std::string& text, const char* field) {
    std::size_t consumed = 0;
    const auto value = std::stoull(text, &consumed, 10);
    if (consumed != text.size()) throw std::runtime_error(std::string("invalid ") + field + ": " + text);
    return value;
}

double parseDouble(const std::string& text, const char* field) {
    std::size_t consumed = 0;
    const auto value = std::stod(text, &consumed);
    if (consumed != text.size() || !std::isfinite(value)) {
        throw std::runtime_error(std::string("invalid ") + field + ": " + text);
    }
    return value;
}

wirefall::ControlId parseControl(const std::string& name) {
    if (name == "TENSION") return wirefall::ControlId::tension;
    if (name == "CUT") return wirefall::ControlId::cut;
    if (name == "SHADOW") return wirefall::ControlId::shadow;
    if (name == "ROOT") return wirefall::ControlId::root;
    if (name == "BITE") return wirefall::ControlId::bite;
    if (name == "HOLES") return wirefall::ControlId::holes;
    if (name == "EDGE") return wirefall::ControlId::edge;
    if (name == "UNDER") return wirefall::ControlId::under;
    if (name == "SWING") return wirefall::ControlId::swing;
    if (name == "SPACE") return wirefall::ControlId::space;
    if (name == "TEMPO") return wirefall::ControlId::tempo;
    throw std::runtime_error("unknown fixture control: " + name);
}

double parseControlValue(wirefall::ControlId control, const std::string& text) {
    if (control == wirefall::ControlId::cut) {
        static constexpr std::array<std::string_view, 9> values{{
            "OPEN", "x0.5", "x1", "x1.5", "x2", "x3", "x4", "x6", "x8",
        }};
        const auto found = std::find(values.begin(), values.end(), text);
        if (found == values.end()) throw std::runtime_error("invalid CUT fixture value: " + text);
        return static_cast<double>(std::distance(values.begin(), found));
    }
    if (control == wirefall::ControlId::under) {
        static constexpr std::array<std::string_view, 5> values{{"1/4", "1/3", "1/2", "2/3", "3/4"}};
        const auto found = std::find(values.begin(), values.end(), text);
        if (found == values.end()) throw std::runtime_error("invalid UNDER fixture value: " + text);
        return static_cast<double>(std::distance(values.begin(), found));
    }
    return parseDouble(text, "control value");
}

Condition readCondition(const fs::path& path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("cannot read fixture: " + path.string());
    stream.imbue(std::locale::classic());
    Condition condition;
    std::string line;
    bool in_events = false;
    while (std::getline(stream, line)) {
        if (!line.empty() && line.back() == '\r') throw std::runtime_error("fixture must use LF line endings");
        if (line.empty()) continue;
        if (!in_events) {
            const auto equals = line.find('=');
            if (equals == std::string::npos) throw std::runtime_error("invalid fixture header line");
            const auto key = line.substr(0, equals);
            const auto value = line.substr(equals + 1U);
            if (key == "schema_version" && value != "wirefall-condition-v1") {
                throw std::runtime_error("unsupported fixture schema");
            } else if (key == "id") {
                condition.id = value;
            } else if (key == "mechanism") {
                condition.mechanism = value;
            } else if (key == "duration_frames") {
                condition.duration_frames = parseUnsigned(value, "duration_frames");
            } else if (key == "events") {
                if (value != "sample_index|ingress_sequence|action|control|value|end_sample_index|end_value") {
                    throw std::runtime_error("fixture event columns drifted");
                }
                in_events = true;
            }
            continue;
        }
        const auto fields = split(line, '|');
        if (fields.size() != 7U) throw std::runtime_error("fixture event must have seven fields");
        ScheduledEvent scheduled{};
        scheduled.sample = parseUnsigned(fields[0], "sample_index");
        scheduled.event.ingress_sequence = parseUnsigned(fields[1], "ingress_sequence");
        scheduled.event.control = parseControl(fields[3]);
        if (fields[2] == "set") {
            scheduled.event.kind = wirefall::EventKind::set_control;
            scheduled.event.value = parseControlValue(scheduled.event.control, fields[4]);
        } else if (fields[2] == "linear-ramp") {
            scheduled.event.kind = wirefall::EventKind::linear_control;
            scheduled.event.value = parseControlValue(scheduled.event.control, fields[4]);
            const auto end_sample = parseUnsigned(fields[5], "end_sample_index");
            if (end_sample <= scheduled.sample) throw std::runtime_error("linear ramp must have positive duration");
            scheduled.event.duration_frames = end_sample - scheduled.sample;
            scheduled.event.end_value = parseControlValue(scheduled.event.control, fields[6]);
        } else {
            throw std::runtime_error("unsupported fixture action: " + fields[2]);
        }
        if (scheduled.sample >= condition.duration_frames) throw std::runtime_error("fixture event lies beyond duration");
        condition.events.push_back(scheduled);
    }
    if (!in_events || condition.id.empty() || condition.mechanism.empty() || condition.duration_frames == 0) {
        throw std::runtime_error("fixture is incomplete");
    }
    if (!std::is_sorted(condition.events.begin(), condition.events.end(), [](const auto& left, const auto& right) {
        if (left.sample != right.sample) return left.sample < right.sample;
        return left.event.ingress_sequence < right.event.ingress_sequence;
    })) {
        throw std::runtime_error("fixture events are not canonically ordered");
    }
    return condition;
}

wirefall::Configuration configurationFor(
    const Condition& condition,
    std::uint32_t oversample_factor,
    float parallel_gain
) {
    wirefall::Configuration configuration{};
    configuration.wire_oversample_factor = oversample_factor;
    configuration.parallel_shadow_gain = parallel_gain;
    if (condition.mechanism == "phase-locked-square-comparator") {
        configuration.scheduler_mode = wirefall::SchedulerMode::phase_locked_square;
    } else if (condition.mechanism == "continuous-low-comparator") {
        configuration.shadow_mode = wirefall::ShadowMode::continuous_parallel;
    } else if (condition.mechanism != "approved-wirefall") {
        throw std::runtime_error("unknown condition mechanism: " + condition.mechanism);
    }
    return configuration;
}

RenderedCondition renderCondition(
    const Condition& condition,
    std::uint32_t block_frames,
    std::uint32_t oversample_factor,
    float parallel_gain,
    bool retain_artifacts
) {
    auto core = std::make_unique<wirefall::Core>();
    if (!core->prepare(48000.0, wirefall::kMaximumBlockFrames,
        configurationFor(condition, oversample_factor, parallel_gain))) {
        throw std::runtime_error("Core rejected the requested render configuration");
    }
    RenderedCondition result;
    if (retain_artifacts) {
        result.left.resize(static_cast<std::size_t>(condition.duration_frames));
        result.right.resize(static_cast<std::size_t>(condition.duration_frames));
    }
    std::array<float, wirefall::kMaximumBlockFrames> scratch_left{};
    std::array<float, wirefall::kMaximumBlockFrames> scratch_right{};
    std::size_t next_event = 0;
    std::uint64_t position = 0;
    long double sum_squares = 0.0L;
    std::array<long double, 2> sums{{0.0L, 0.0L}};
    while (position < condition.duration_frames) {
        const auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            block_frames, condition.duration_frames - position));
        std::array<wirefall::Event, wirefall::kMaximumEventsPerBlock> block_events{};
        std::size_t event_count = 0;
        while (next_event < condition.events.size()
            && condition.events[next_event].sample < position + count) {
            if (condition.events[next_event].sample < position) {
                throw std::runtime_error("fixture event traversal lost ordering");
            }
            if (event_count >= block_events.size()) throw std::runtime_error("fixture exceeds per-block event capacity");
            block_events[event_count] = condition.events[next_event].event;
            block_events[event_count].sample_offset = static_cast<std::uint32_t>(
                condition.events[next_event].sample - position);
            ++event_count;
            ++next_event;
        }
        std::array<wirefall::LedgerEvent, 256> block_ledger{};
        auto* left = retain_artifacts ? result.left.data() + position : scratch_left.data();
        auto* right = retain_artifacts ? result.right.data() + position : scratch_right.data();
        const auto report = core->process(
            left, right, count,
            block_events.data(), event_count,
            block_ledger.data(), block_ledger.size());
        if (report.dropped_events != 0 || report.ledger_events_dropped != 0) {
            throw std::runtime_error("normal fixture render dropped an event or ledger entry");
        }
        if (retain_artifacts) {
            result.ledger.insert(
                result.ledger.end(), block_ledger.begin(),
                block_ledger.begin() + static_cast<std::ptrdiff_t>(report.ledger_events_written));
        }
        for (std::uint32_t frame = 0; frame < count; ++frame) {
            const double left_value = left[frame];
            const double right_value = right[frame];
            if (!std::isfinite(left_value) || !std::isfinite(right_value)) {
                throw std::runtime_error("Core emitted a non-finite sample");
            }
            result.abs_peak = std::max(result.abs_peak, std::abs(left_value));
            result.abs_peak = std::max(result.abs_peak, std::abs(right_value));
            sum_squares += static_cast<long double>(left_value * left_value + right_value * right_value);
            sums[0] += left_value;
            sums[1] += right_value;
        }
        position += count;
    }
    const auto denominator = static_cast<long double>(condition.duration_frames) * 2.0L;
    result.rms = std::sqrt(static_cast<double>(sum_squares / denominator));
    result.dc_mean = {{
        static_cast<double>(sums[0] / static_cast<long double>(condition.duration_frames)),
        static_cast<double>(sums[1] / static_cast<long double>(condition.duration_frames)),
    }};
    result.diagnostics = core->diagnostics();
    result.normalized_state_sha256 = core->normalizedStateSha256();
    result.full_state_sha256 = core->fullStateSha256();
    return result;
}

void writeU16(std::ostream& stream, std::uint16_t value) {
    const std::array<char, 2> bytes{{
        static_cast<char>(value & 0xffU), static_cast<char>((value >> 8U) & 0xffU),
    }};
    stream.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
}

void writeU32(std::ostream& stream, std::uint32_t value) {
    const std::array<char, 4> bytes{{
        static_cast<char>(value & 0xffU), static_cast<char>((value >> 8U) & 0xffU),
        static_cast<char>((value >> 16U) & 0xffU), static_cast<char>((value >> 24U) & 0xffU),
    }};
    stream.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
}

void writeS24(std::ostream& stream, float value) {
    const double bounded = std::clamp(static_cast<double>(value), -1.0, 1.0);
    const auto quantized = static_cast<std::int32_t>(std::llround(bounded * 8388607.0));
    const auto word = static_cast<std::uint32_t>(quantized);
    const std::array<char, 3> bytes{{
        static_cast<char>(word & 0xffU), static_cast<char>((word >> 8U) & 0xffU),
        static_cast<char>((word >> 16U) & 0xffU),
    }};
    stream.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
}

void writeWav(const fs::path& path, const RenderedCondition& render) {
    if (render.left.size() != render.right.size()) throw std::runtime_error("stereo render length mismatch");
    const auto data_bytes_64 = render.left.size() * 6U;
    if (data_bytes_64 > std::numeric_limits<std::uint32_t>::max() - 36U) {
        throw std::runtime_error("WAV exceeds RIFF size limit");
    }
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) throw std::runtime_error("cannot create WAV: " + path.string());
    stream.write("RIFF", 4);
    writeU32(stream, static_cast<std::uint32_t>(36U + data_bytes_64));
    stream.write("WAVEfmt ", 8);
    writeU32(stream, 16);
    writeU16(stream, 1);
    writeU16(stream, 2);
    writeU32(stream, 48000);
    writeU32(stream, 48000U * 6U);
    writeU16(stream, 6);
    writeU16(stream, 24);
    stream.write("data", 4);
    writeU32(stream, static_cast<std::uint32_t>(data_bytes_64));
    for (std::size_t frame = 0; frame < render.left.size(); ++frame) {
        writeS24(stream, render.left[frame]);
        writeS24(stream, render.right[frame]);
    }
    if (!stream) throw std::runtime_error("failed while writing WAV: " + path.string());
}

void writeLedger(const fs::path& path, const std::vector<wirefall::LedgerEvent>& ledger) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) throw std::runtime_error("cannot create ledger: " + path.string());
    stream.imbue(std::locale::classic());
    stream << "sample_index,ingress_sequence,kind,control,action,value,active_rate_index,active_holes,scheduler_error,effective_edge_frames,cut\n";
    stream << std::setprecision(std::numeric_limits<double>::max_digits10);
    for (const auto& event : ledger) {
        stream << event.sample_index << ',' << event.ingress_sequence << ','
               << wirefall::ledgerKindName(event.kind) << ',' << wirefall::controlName(event.control)
               << ',' << wirefall::actionName(event.action) << ',' << event.value << ','
               << event.active_rate_index << ',' << event.active_holes << ','
               << event.scheduler_error << ',' << event.effective_edge_frames << ','
               << (event.cut ? 1 : 0) << '\n';
    }
    if (!stream) throw std::runtime_error("failed while writing ledger: " + path.string());
}

std::string fileSha256(const fs::path& path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("cannot hash file: " + path.string());
    schuss::instrument_lab::Sha256 hash;
    std::array<std::uint8_t, 65536> buffer{};
    while (stream) {
        stream.read(reinterpret_cast<char*>(buffer.data()), static_cast<std::streamsize>(buffer.size()));
        const auto count = stream.gcount();
        if (count > 0) hash.update(buffer.data(), static_cast<std::size_t>(count));
    }
    return hash.finish();
}

void writeMetrics(
    const fs::path& path,
    const Condition& condition,
    const RenderedCondition& render,
    const Options& options,
    float selected_parallel_gain,
    const std::string& fixture_hash,
    const std::string& wav_hash,
    const std::string& ledger_hash
) {
    using schuss::instrument_lab::finiteJsonNumber;
    using schuss::instrument_lab::jsonEscape;
    const auto& d = render.diagnostics;
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) throw std::runtime_error("cannot create metrics: " + path.string());
    stream.imbue(std::locale::classic());
    stream << "{\n"
           << "  \"artifact_hashes\": {\"events_csv_sha256\": \"" << ledger_hash
           << "\", \"fixture_sha256\": \"" << fixture_hash
           << "\", \"wav_sha256\": \"" << wav_hash << "\"},\n"
           << "  \"audio\": {\"abs_peak\": " << finiteJsonNumber(render.abs_peak)
           << ", \"channel_dc_mean\": [" << finiteJsonNumber(render.dc_mean[0]) << ", "
           << finiteJsonNumber(render.dc_mean[1]) << "], \"rms\": " << finiteJsonNumber(render.rms) << "},\n"
           << "  \"block_frames\": " << options.block_frames << ",\n"
           << "  \"condition_id\": \"" << jsonEscape(condition.id) << "\",\n"
           << "  \"core\": {\"fir_byte_sha256\": \"" << wirefall::Core::frozenFirByteSha256()
           << "\", \"full_state_sha256\": \"" << render.full_state_sha256
           << "\", \"normalized_state_sha256\": \"" << render.normalized_state_sha256
           << "\", \"state_bytes\": " << wirefall::Core::stateBytes() << "},\n"
           << "  \"diagnostics\": {"
           << "\"accepted_events\": " << d.accepted_events
           << ", \"beat_boundaries\": " << d.beat_boundaries
           << ", \"cut_boundaries\": " << d.cut_boundaries
           << ", \"dropped_events\": " << d.dropped_events
           << ", \"invalid_events\": " << d.invalid_events
           << ", \"ledger_overflows\": " << d.ledger_overflows
           << ", \"non_finite_containments\": " << d.non_finite_containments
           << ", \"non_finite_targets\": " << d.non_finite_targets
           << ", \"opportunity_boundaries\": " << d.opportunity_boundaries
           << ", \"output_non_finite_clears\": " << d.output_non_finite_clears
           << ", \"processed_frames\": " << d.processed_frames
           << ", \"rhythm_commits\": " << d.rhythm_commits << "},\n"
           << "  \"duration_frames\": " << condition.duration_frames << ",\n"
           << "  \"mechanism\": \"" << jsonEscape(condition.mechanism) << "\",\n"
           << "  \"oversample_factor\": " << options.oversample_factor << ",\n"
           << "  \"parallel_shadow_gain\": " << finiteJsonNumber(selected_parallel_gain) << ",\n"
           << "  \"sample_rate_hz\": 48000,\n"
           << "  \"schema_version\": \"wirefall-condition-metrics-v1\",\n"
           << "  \"seed\": 1464422981,\n"
           << "  \"seed_used\": false\n"
           << "}\n";
    if (!stream) throw std::runtime_error("failed while writing metrics: " + path.string());
}

Options parseOptions(int argc, char** argv) {
    Options options;
    for (int index = 1; index < argc; ++index) {
        const std::string argument = argv[index];
        const auto take = [&](const char* name) -> std::string {
            if (index + 1 >= argc) throw std::runtime_error(std::string("missing value for ") + name);
            return argv[++index];
        };
        if (argument == "--fixture") options.fixture = take("--fixture");
        else if (argument == "--output-dir") options.output_directory = take("--output-dir");
        else if (argument == "--block-frames") options.block_frames = static_cast<std::uint32_t>(parseUnsigned(take("--block-frames"), "block_frames"));
        else if (argument == "--oversample-factor") options.oversample_factor = static_cast<std::uint32_t>(parseUnsigned(take("--oversample-factor"), "oversample_factor"));
        else if (argument == "--parallel-gain") {
            options.parallel_gain = static_cast<float>(parseDouble(take("--parallel-gain"), "parallel_gain"));
            options.parallel_gain_supplied = true;
        } else if (argument == "--parallel-target-rms") {
            options.parallel_target_rms = parseDouble(take("--parallel-target-rms"), "parallel_target_rms");
            options.parallel_target_supplied = true;
        } else if (argument == "--output-prefix") options.output_prefix = take("--output-prefix");
        else throw std::runtime_error("unknown argument: " + argument);
    }
    if (options.fixture.empty() || options.output_directory.empty()) {
        throw std::runtime_error("usage: wirefall_render --fixture PATH --output-dir PATH [--block-frames N] [--oversample-factor 4|8] [--parallel-gain G|--parallel-target-rms RMS] [--output-prefix STEM]");
    }
    if (options.block_frames == 0 || options.block_frames > wirefall::kMaximumBlockFrames) {
        throw std::runtime_error("block_frames must be in [1,512]");
    }
    if (options.oversample_factor != 4 && options.oversample_factor != 8) {
        throw std::runtime_error("oversample_factor must be 4 or 8");
    }
    if (options.parallel_gain_supplied && options.parallel_target_supplied) {
        throw std::runtime_error("parallel gain and target RMS are mutually exclusive");
    }
    return options;
}

float selectParallelGain(const Condition& condition, const Options& options) {
    if (condition.mechanism != "continuous-low-comparator") {
        if (options.parallel_gain_supplied || options.parallel_target_supplied) {
            throw std::runtime_error("parallel comparator arguments require CMP02");
        }
        return 1.0f;
    }
    if (options.parallel_gain_supplied) return options.parallel_gain;
    if (!options.parallel_target_supplied || options.parallel_target_rms <= 0.0) {
        throw std::runtime_error("CMP02 requires --parallel-target-rms or --parallel-gain");
    }
    double lower = 0.0;
    double upper = 1.5;
    for (int iteration = 0; iteration < 32; ++iteration) {
        const double midpoint = 0.5 * (lower + upper);
        const auto probe = renderCondition(
            condition, options.block_frames, options.oversample_factor,
            static_cast<float>(midpoint), false);
        if (probe.rms < options.parallel_target_rms) lower = midpoint;
        else upper = midpoint;
    }
    return static_cast<float>(lower);
}

int run(int argc, char** argv) {
    const auto options = parseOptions(argc, argv);
    const auto condition = readCondition(options.fixture);
    const float parallel_gain = selectParallelGain(condition, options);
    const auto render = renderCondition(
        condition, options.block_frames, options.oversample_factor,
        parallel_gain, true);
    fs::create_directories(options.output_directory);
    const std::string stem = options.output_prefix.empty() ? condition.id : options.output_prefix;
    const auto wav_path = options.output_directory / (stem + ".wav");
    const auto ledger_path = options.output_directory / (stem + ".events.csv");
    const auto metrics_path = options.output_directory / (stem + ".metrics.json");
    for (const auto& path : {wav_path, ledger_path, metrics_path}) {
        if (fs::exists(path)) throw std::runtime_error("refusing to overwrite artifact: " + path.string());
    }
    writeWav(wav_path, render);
    writeLedger(ledger_path, render.ledger);
    writeMetrics(
        metrics_path, condition, render, options, parallel_gain,
        fileSha256(options.fixture), fileSha256(wav_path), fileSha256(ledger_path));
    std::cout.imbue(std::locale::classic());
    std::cout << "condition=" << condition.id
              << " block_frames=" << options.block_frames
              << " oversample_factor=" << options.oversample_factor
              << " rms=" << std::setprecision(17) << render.rms
              << " parallel_shadow_gain=" << parallel_gain << '\n';
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        return run(argc, argv);
    } catch (const std::exception& error) {
        std::cerr << "Wirefall render failed: " << error.what() << '\n';
        return 2;
    }
}
