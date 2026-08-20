#include "cinderwheel/core.hpp"
#include "schuss/instrument_lab/renderer_artifacts.hpp"

#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_core/juce_core.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

constexpr std::uint32_t kSampleRate = 48000;
constexpr std::uint32_t kCycles = 32;
constexpr double kCyclesPerSecond = 0.8;
constexpr std::uint64_t kFramesPerCycle = 60000;
constexpr std::uint64_t kTotalFrames = kCycles * kFramesPerCycle;
constexpr std::uint8_t kChannel16ControlChange = 0xBFU;
constexpr double kMaximumAbsoluteDcMean = 1.0e-4;

struct Options {
    juce::File output_directory;
    std::uint32_t block_frames{128};
};

struct ScheduledCc {
    std::uint64_t sample{};
    std::uint64_t sequence{};
    std::uint8_t controller{};
    std::uint8_t value{};
};

struct Condition {
    std::string stem;
    std::string description;
    std::uint8_t undertow{};
    std::uint8_t pulse_divide{};
    std::uint8_t wake{};
    std::uint8_t ember{};
    bool bloom{};
    bool corroded{};
};

struct RenderMetrics {
    double peak{};
    double dc_mean_left{};
    double dc_mean_right{};
    double rms{};
    bool finite{true};
    std::uint64_t audio_fingerprint{14695981039346656037ULL};
};

struct RenderResult {
    Condition condition;
    std::vector<ScheduledCc> schedule;
    std::vector<cinderwheel::WakeEvent> ledger;
    RenderMetrics metrics;
    cinderwheel::Diagnostics diagnostics;
    cinderwheel::StateSnapshot final_state;
    std::string wav_name;
    std::string ledger_name;
    std::int64_t wav_bytes{};
    std::int64_t ledger_bytes{};
};

using schuss::instrument_lab::jsonEscape;

std::string jsonNumber(double value) {
    return schuss::instrument_lab::finiteJsonNumber(value);
}

std::string hex64(std::uint64_t value) {
    std::ostringstream stream;
    stream.imbue(std::locale::classic());
    stream << std::hex << std::setfill('0') << std::setw(16) << value;
    return stream.str();
}

std::optional<std::uint32_t> parseBlock(std::string_view text) {
    if (text == "64") return 64U;
    if (text == "128") return 128U;
    if (text == "512") return 512U;
    return std::nullopt;
}

void printUsage(std::ostream& stream, const char* executable) {
    stream << "Usage: " << executable
           << " --output-dir PATH [--block 64|128|512]\n";
}

Options parseOptions(int argc, char** argv) {
    std::optional<juce::File> output_directory;
    std::uint32_t block_frames = 128;
    for (int index = 1; index < argc; ++index) {
        const std::string_view argument(argv[index]);
        if (argument == "--help" || argument == "-h") {
            printUsage(std::cout, argv[0]);
            std::exit(0);
        }
        if (argument == "--output-dir") {
            if (++index >= argc) throw std::runtime_error("--output-dir requires a path");
            output_directory = juce::File(juce::String::fromUTF8(argv[index]));
            continue;
        }
        if (argument == "--block") {
            if (++index >= argc) throw std::runtime_error("--block requires 64, 128, or 512");
            const auto parsed = parseBlock(argv[index]);
            if (!parsed.has_value()) throw std::runtime_error("--block must be 64, 128, or 512");
            block_frames = *parsed;
            continue;
        }
        throw std::runtime_error("unknown argument: " + std::string(argument));
    }
    if (!output_directory.has_value()) throw std::runtime_error("--output-dir is required");
    return {*output_directory, block_frames};
}

void addCc(
    std::vector<ScheduledCc>& schedule,
    std::uint64_t sample,
    std::uint8_t controller,
    std::uint8_t value
) {
    schedule.push_back({sample, 0, controller, value});
}

void addTap(
    std::vector<ScheduledCc>& schedule,
    std::uint64_t sample,
    std::uint8_t controller
) {
    addCc(schedule, sample, controller, 127);
    addCc(schedule, sample + 100U, controller, 0);
}

std::vector<ScheduledCc> makeSchedule(const Condition& condition) {
    std::vector<ScheduledCc> schedule;
    schedule.reserve(48);

    // The four experiment controls arrive before the first rendered sample.
    addCc(schedule, 0, 31, condition.undertow);
    addCc(schedule, 0, 32, condition.pulse_divide);
    addCc(schedule, 0, 33, condition.wake);
    addCc(schedule, 0, 35, condition.ember);

    // Three separated source gestures select DUST only in the corroded render.
    // The clean schedule uses accepted BODY messages in the same event slots so
    // both ledgers observe identical ingress sequence numbers at every strike.
    for (const std::uint64_t sample : {1000ULL, 16000ULL, 31000ULL}) {
        if (condition.corroded) {
            addTap(schedule, sample, 40);
        } else {
            addCc(schedule, sample, 26, 70);
            addCc(schedule, sample + 100U, 26, 70);
        }
    }

    // Set the CLEAN grain controls before any mode change. Their retained
    // values remain independent from later FILTER/DRIVE contexts.
    addCc(schedule, 60000, 28, condition.corroded ? 112 : 64);
    addCc(schedule, 60000, 29, condition.corroded ? 112 : 32);

    // Corrosion first enters the FILTER context, then changes to DRIVE halfway
    // through the gesture. Clean counterparts keep identical event timing.
    if (condition.corroded) {
        addTap(schedule, 61000, 44);
    } else {
        addCc(schedule, 61000, 27, 44);
        addCc(schedule, 61100, 27, 44);
    }

    const std::array<std::uint8_t, 5> context_controllers{{25, 26, 27, 28, 29}};
    const std::array<std::uint8_t, 5> clean_context{{83, 70, 44, 64, 32}};
    const std::array<std::uint8_t, 5> corroded_context{{83, 112, 101, 112, 112}};
    const auto& initial_context = condition.corroded ? corroded_context : clean_context;
    // Cross the remembered FX-A/B defaults after the mode transition so the
    // corroded gesture exercises the same soft-pickup path as a controller.
    addCc(schedule, 75500, 28, 64);
    addCc(schedule, 75500, 29, 32);
    for (std::size_t index = 0; index < context_controllers.size(); ++index) {
        addCc(schedule, 76000, context_controllers[index], initial_context[index]);
    }

    for (const std::uint64_t cycle : {6ULL, 14ULL, 22ULL, 30ULL}) {
        addTap(schedule, cycle * kFramesPerCycle + 500U, 41);
    }

    addCc(schedule, 8U * kFramesPerCycle, 34, 32);
    addCc(schedule, 16U * kFramesPerCycle, 34, 104);
    addCc(schedule, 24U * kFramesPerCycle, 34, 64);

    if (condition.corroded) {
        addTap(schedule, 16U * kFramesPerCycle + 1000U, 44);
    } else {
        addCc(schedule, 16U * kFramesPerCycle + 1000U, 27, 44);
        addCc(schedule, 16U * kFramesPerCycle + 1100U, 27, 44);
    }
    addCc(schedule, 16U * kFramesPerCycle + 15500U, 28, 64);
    addCc(schedule, 16U * kFramesPerCycle + 15500U, 29, 32);
    addCc(schedule, 16U * kFramesPerCycle + 16000U, 28, condition.corroded ? 108 : 64);
    addCc(schedule, 16U * kFramesPerCycle + 16000U, 29, condition.corroded ? 118 : 32);

    if (condition.bloom) {
        for (const std::uint64_t cycle : {18ULL, 19ULL, 20ULL, 21ULL}) {
            addTap(schedule, cycle * kFramesPerCycle + 1000U, 46);
        }
    }

    std::stable_sort(
        schedule.begin(),
        schedule.end(),
        [](const auto& left, const auto& right) { return left.sample < right.sample; }
    );
    for (std::size_t index = 0; index < schedule.size(); ++index) {
        schedule[index].sequence = static_cast<std::uint64_t>(index + 1U);
    }
    return schedule;
}

std::array<Condition, 6> conditions() {
    return {{
        {"01-baseline", "four-stage body/grain surrogate; Undertow off; Wake zero", 0, 0, 0, 0, false, false},
        {"02-undertow-f3", "Undertow f/3; Wake zero", 20, 0, 0, 0, false, false},
        {"03-primary-wake-ember-zero", "primary Wake strikes; Ember zero", 0, 0, 96, 0, false, false},
        {"04-rotor-medium-clean", "Pulse Divide 3; rotor routing; medium Ember", 0, 17, 96, 72, false, false},
        {"05-rotor-high-bloom", "Pulse Divide 3; high Ember; four-cycle Bloom gesture", 0, 17, 96, 112, true, false},
        {"06-rotor-medium-corroded", "medium rotor counterpart with DUST, filter, grain amount, and drive context", 0, 17, 96, 72, false, true},
    }};
}

bool sameWakeEvent(
    const cinderwheel::WakeEvent& left,
    const cinderwheel::WakeEvent& right
) {
    return left.sample_index == right.sample_index
        && left.ingress_sequence == right.ingress_sequence
        && left.transition_index == right.transition_index
        && left.voice == right.voice
        && left.kind == right.kind
        && left.ledger_energy == right.ledger_energy;
}

void fingerprintFloat(std::uint64_t& fingerprint, float value) {
    static_assert(sizeof(float) == sizeof(std::uint32_t));
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    constexpr std::uint64_t prime = 1099511628211ULL;
    for (unsigned shift = 0; shift < 32U; shift += 8U) {
        fingerprint ^= static_cast<std::uint8_t>((bits >> shift) & 0xffU);
        fingerprint *= prime;
    }
}

void updateMetrics(
    RenderMetrics& metrics,
    const float* left,
    const float* right,
    std::uint32_t frames,
    std::uint64_t origin,
    double& dc_sum_left,
    double& dc_sum_right,
    double& square_sum,
    std::uint64_t& dc_frames
) {
    for (std::uint32_t frame = 0; frame < frames; ++frame) {
        const float left_sample = left[frame];
        const float right_sample = right[frame];
        metrics.finite = metrics.finite
            && std::isfinite(left_sample)
            && std::isfinite(right_sample);
        metrics.peak = std::max(metrics.peak, static_cast<double>(std::abs(left_sample)));
        metrics.peak = std::max(metrics.peak, static_cast<double>(std::abs(right_sample)));
        square_sum += static_cast<double>(left_sample) * static_cast<double>(left_sample);
        square_sum += static_cast<double>(right_sample) * static_cast<double>(right_sample);
        if (origin + frame >= kSampleRate) {
            dc_sum_left += left_sample;
            dc_sum_right += right_sample;
            ++dc_frames;
        }
        fingerprintFloat(metrics.audio_fingerprint, left_sample);
        fingerprintFloat(metrics.audio_fingerprint, right_sample);
    }
}

RenderResult renderCondition(
    const juce::File& output_directory,
    const Condition& condition,
    std::uint32_t block_frames
) {
    RenderResult result;
    result.condition = condition;
    result.schedule = makeSchedule(condition);
    result.ledger.reserve(384);
    result.wav_name = condition.stem + ".wav";
    result.ledger_name = condition.stem + ".ledger.csv";

    const auto wav_file = output_directory.getChildFile(result.wav_name);
    const auto ledger_file = output_directory.getChildFile(result.ledger_name);
    std::unique_ptr<juce::OutputStream> wav_stream = wav_file.createOutputStream();
    if (wav_stream == nullptr) throw std::runtime_error("cannot create " + result.wav_name);
    juce::WavAudioFormat wav_format;
    const auto writer_options = juce::AudioFormatWriterOptions()
        .withSampleRate(static_cast<double>(kSampleRate))
        .withNumChannels(2)
        .withBitsPerSample(24);
    auto writer = wav_format.createWriterFor(wav_stream, writer_options);
    if (writer == nullptr) throw std::runtime_error("cannot create WAV writer for " + result.wav_name);

    std::ofstream ledger_stream(ledger_file.getFullPathName().toStdString(), std::ios::binary);
    ledger_stream.imbue(std::locale::classic());
    if (!ledger_stream) throw std::runtime_error("cannot create " + result.ledger_name);
    ledger_stream << "sample_index,ingress_sequence,transition_index,voice,kind,ledger_energy\n";
    ledger_stream << std::setprecision(std::numeric_limits<float>::max_digits10);

    cinderwheel::Core core;
    if (!core.prepare(kSampleRate, cinderwheel::kMaximumBlockFrames)) {
        throw std::runtime_error("Core rejected the fixed render configuration");
    }

    juce::AudioBuffer<float> audio(2, static_cast<int>(block_frames));
    std::size_t schedule_index = 0;
    std::uint64_t origin = 0;
    double dc_sum_left = 0.0;
    double dc_sum_right = 0.0;
    double square_sum = 0.0;
    std::uint64_t dc_frames = 0;
    while (origin < kTotalFrames) {
        const auto frames = static_cast<std::uint32_t>(
            std::min<std::uint64_t>(block_frames, kTotalFrames - origin)
        );
        std::array<cinderwheel::MidiEvent, 32> midi{};
        std::size_t midi_count = 0;
        while (schedule_index < result.schedule.size()
            && result.schedule[schedule_index].sample < origin + frames) {
            if (result.schedule[schedule_index].sample < origin || midi_count == midi.size()) {
                throw std::runtime_error("render schedule capacity/order failure");
            }
            const auto& source = result.schedule[schedule_index++];
            midi[midi_count++] = {
                static_cast<std::uint32_t>(source.sample - origin),
                source.sequence,
                {kChannel16ControlChange, source.controller, source.value},
                3,
            };
        }

        std::array<cinderwheel::WakeEvent, 16> block_events{};
        const auto report = core.process(
            audio.getWritePointer(0),
            audio.getWritePointer(1),
            frames,
            midi.data(),
            midi_count,
            block_events.data(),
            block_events.size()
        );
        if (report.events_dropped != 0) throw std::runtime_error("renderer event sink overflow");
        for (std::size_t index = 0; index < report.events_written; ++index) {
            const auto& event = block_events[index];
            result.ledger.push_back(event);
            ledger_stream << event.sample_index << ','
                          << event.ingress_sequence << ','
                          << event.transition_index << ','
                          << static_cast<unsigned>(event.voice) << ','
                          << (event.kind == cinderwheel::WakeEventKind::primary
                                  ? "primary"
                                  : "afterstrike")
                          << ',' << event.ledger_energy << '\n';
        }
        if (!writer->writeFromAudioSampleBuffer(audio, 0, static_cast<int>(frames))) {
            throw std::runtime_error("WAV write failed for " + result.wav_name);
        }
        updateMetrics(
            result.metrics,
            audio.getReadPointer(0),
            audio.getReadPointer(1),
            frames,
            origin,
            dc_sum_left,
            dc_sum_right,
            square_sum,
            dc_frames
        );
        origin += frames;
    }
    if (schedule_index != result.schedule.size()) {
        throw std::runtime_error("render ended before the schedule");
    }
    writer.reset();
    ledger_stream.close();
    if (!ledger_stream) throw std::runtime_error("ledger write failed for " + result.ledger_name);

    result.metrics.dc_mean_left = dc_frames == 0
        ? 0.0
        : dc_sum_left / static_cast<double>(dc_frames);
    result.metrics.dc_mean_right = dc_frames == 0
        ? 0.0
        : dc_sum_right / static_cast<double>(dc_frames);
    result.metrics.rms = std::sqrt(square_sum / static_cast<double>(kTotalFrames * 2U));
    result.diagnostics = core.diagnostics();
    result.final_state = core.snapshot();
    result.wav_bytes = wav_file.getSize();
    result.ledger_bytes = ledger_file.getSize();
    return result;
}

bool filesEqual(const juce::File& left, const juce::File& right) {
    return left.getSize() == right.getSize()
        && left.loadFileAsString() == right.loadFileAsString();
}

void writeDiagnosticsJson(std::ostream& stream, const cinderwheel::Diagnostics& value) {
    stream << "{\n"
           << "        \"afterstrikes\": " << value.afterstrikes << ",\n"
           << "        \"duplicate_button_edges\": " << value.duplicate_button_edges << ",\n"
           << "        \"event_cap_hits\": " << value.event_cap_hits << ",\n"
           << "        \"event_sink_overflows\": " << value.event_sink_overflows << ",\n"
           << "        \"ignored_midi_messages\": " << value.ignored_midi_messages << ",\n"
           << "        \"malformed_midi_messages\": " << value.malformed_midi_messages << ",\n"
           << "        \"midi_events_dropped\": " << value.midi_events_dropped << ",\n"
           << "        \"non_finite_clears\": " << value.non_finite_clears << ",\n"
           << "        \"panic_count\": " << value.panic_count << ",\n"
           << "        \"primary_strikes\": " << value.primary_strikes << ",\n"
           << "        \"processed_frames\": " << value.processed_frames << ",\n"
           << "        \"reset_count\": " << value.reset_count << ",\n"
           << "        \"stage_transitions\": " << value.stage_transitions << ",\n"
           << "        \"unsupported_process_calls\": " << value.unsupported_process_calls << "\n"
           << "      }";
}

void writeScheduleJson(std::ostream& stream, const std::vector<ScheduledCc>& schedule) {
    stream << "[";
    if (!schedule.empty()) stream << '\n';
    for (std::size_t index = 0; index < schedule.size(); ++index) {
        const auto& event = schedule[index];
        stream << "          {\"cc\": " << static_cast<unsigned>(event.controller)
               << ", \"sample\": " << event.sample
               << ", \"sequence\": " << event.sequence
               << ", \"value\": " << static_cast<unsigned>(event.value) << '}';
        stream << (index + 1U == schedule.size() ? "\n" : ",\n");
    }
    stream << "        ]";
}

void writeManifest(
    const juce::File& output_directory,
    const std::vector<RenderResult>& results,
    std::uint32_t block_frames,
    bool clean_corroded_ledger_equal,
    bool clean_corroded_audio_distinct
) {
    const auto manifest_file = output_directory.getChildFile("cinderwheel-observation-manifest.json");
    std::ofstream stream(manifest_file.getFullPathName().toStdString(), std::ios::binary);
    stream.imbue(std::locale::classic());
    if (!stream) throw std::runtime_error("cannot create observation manifest");
    stream << "{\n"
           << "  \"artifact_schema\": \"cinderwheel-render-observation-v0\",\n"
           << "  \"audio_format\": {\"bits_per_sample\": 24, \"channels\": 2, \"encoding\": \"PCM WAV\"},\n"
           << "  \"block_frames\": " << block_frames << ",\n"
           << "  \"condition_count\": " << results.size() << ",\n"
           << "  \"cycle_count\": " << kCycles << ",\n"
           << "  \"cycle_rate_hz\": " << jsonNumber(kCyclesPerSecond) << ",\n"
           << "  \"determinism\": {\n"
           << "    \"clean_corroded_audio_distinct\": "
           << (clean_corroded_audio_distinct ? "true" : "false") << ",\n"
           << "    \"clean_corroded_ledger_bytes_equal\": "
           << (clean_corroded_ledger_equal ? "true" : "false") << ",\n"
           << "    \"timestamps_recorded\": false,\n"
           << "    \"wall_time_recorded_in_artifact\": false\n"
           << "  },\n"
           << "  \"evidence_boundary\": {\n"
           << "    \"audible_quality_claimed\": false,\n"
           << "    \"offline_host_signal_only\": true,\n"
           << "    \"physical_audio_or_midi_device_opened\": false,\n"
           << "    \"real_time_fitness_claimed\": false\n"
           << "  },\n"
           << "  \"frame_count\": " << kTotalFrames << ",\n"
           << "  \"midi_contract\": {\"channel\": 16, \"encoders\": \"CC20-35\", \"buttons\": \"CC40-47\"},\n"
           << "  \"results\": [\n";
    for (std::size_t result_index = 0; result_index < results.size(); ++result_index) {
        const auto& result = results[result_index];
        stream << "    {\n"
               << "      \"audio_fingerprint_fnv1a64\": \""
               << hex64(result.metrics.audio_fingerprint) << "\",\n"
               << "      \"description\": \"" << jsonEscape(result.condition.description) << "\",\n"
               << "      \"diagnostics\": ";
        writeDiagnosticsJson(stream, result.diagnostics);
        stream << ",\n"
               << "      \"final_state\": {\"pulse_divide\": "
               << static_cast<unsigned>(result.final_state.pulse_divide)
               << ", \"rate_hz\": " << jsonNumber(result.final_state.rate_hz)
               << ", \"stage_transition_index\": "
               << result.final_state.stage_transition_index
               << ", \"undertow_divisor\": "
               << static_cast<unsigned>(result.final_state.undertow_divisor) << "},\n"
               << "      \"ledger\": {\"bytes\": " << result.ledger_bytes
               << ", \"events\": " << result.ledger.size()
               << ", \"file\": \"" << jsonEscape(result.ledger_name) << "\"},\n"
               << "      \"measurements\": {\n"
               << "        \"dc_mean_left\": " << jsonNumber(result.metrics.dc_mean_left) << ",\n"
               << "        \"dc_mean_right\": " << jsonNumber(result.metrics.dc_mean_right) << ",\n"
               << "        \"finite\": " << (result.metrics.finite ? "true" : "false") << ",\n"
               << "        \"peak\": " << jsonNumber(result.metrics.peak) << ",\n"
               << "        \"rms\": " << jsonNumber(result.metrics.rms) << "\n"
               << "      },\n"
               << "      \"schedule\": ";
        writeScheduleJson(stream, result.schedule);
        stream << ",\n"
               << "      \"stem\": \"" << jsonEscape(result.condition.stem) << "\",\n"
               << "      \"wav\": {\"bytes\": " << result.wav_bytes
               << ", \"file\": \"" << jsonEscape(result.wav_name) << "\"}\n"
               << "    }" << (result_index + 1U == results.size() ? "\n" : ",\n");
    }
    stream << "  ],\n"
           << "  \"sample_rate_hz\": " << kSampleRate << "\n"
           << "}\n";
    stream.close();
    if (!stream) throw std::runtime_error("observation manifest write failed");
}

void checkOutputTargets(const juce::File& output_directory) {
    if (output_directory.exists() && !output_directory.isDirectory()) {
        throw std::runtime_error("output path exists but is not a directory");
    }
    if (!output_directory.exists()) {
        const auto created = output_directory.createDirectory();
        if (created.failed()) {
            throw std::runtime_error("cannot create output directory: " + created.getErrorMessage().toStdString());
        }
    }
    for (const auto& condition : conditions()) {
        for (const auto& suffix : {std::string(".wav"), std::string(".ledger.csv")}) {
            if (output_directory.getChildFile(condition.stem + suffix).exists()) {
                throw std::runtime_error("refusing to overwrite existing render artifact");
            }
        }
    }
    if (output_directory.getChildFile("cinderwheel-observation-manifest.json").exists()) {
        throw std::runtime_error("refusing to overwrite existing observation manifest");
    }
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const auto options = parseOptions(argc, argv);
        checkOutputTargets(options.output_directory);
        const auto begin = std::chrono::steady_clock::now();
        std::vector<RenderResult> results;
        results.reserve(conditions().size());
        for (const auto& condition : conditions()) {
            const auto condition_begin = std::chrono::steady_clock::now();
            results.push_back(renderCondition(
                options.output_directory,
                condition,
                options.block_frames
            ));
            const auto milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - condition_begin
            ).count();
            std::cerr << condition.stem << ": " << milliseconds << " ms\n";
        }

        const auto& clean = results.at(3);
        const auto& corroded = results.at(5);
        const bool event_equal = clean.ledger.size() == corroded.ledger.size()
            && std::equal(
                clean.ledger.begin(),
                clean.ledger.end(),
                corroded.ledger.begin(),
                sameWakeEvent
            );
        const bool ledger_bytes_equal = event_equal && filesEqual(
            options.output_directory.getChildFile(clean.ledger_name),
            options.output_directory.getChildFile(corroded.ledger_name)
        );
        if (!ledger_bytes_equal) {
            throw std::runtime_error("clean/corroded ledger equality failed");
        }
        const bool audio_distinct = clean.metrics.audio_fingerprint
            != corroded.metrics.audio_fingerprint;
        if (!audio_distinct) throw std::runtime_error("clean/corroded audio did not differ");
        for (const auto& result : results) {
            if (!result.metrics.finite
                || result.metrics.peak > cinderwheel::kOutputCeiling
                || std::abs(result.metrics.dc_mean_left) >= kMaximumAbsoluteDcMean
                || std::abs(result.metrics.dc_mean_right) >= kMaximumAbsoluteDcMean) {
                throw std::runtime_error("render numeric-safety measurement failed");
            }
        }

        writeManifest(
            options.output_directory,
            results,
            options.block_frames,
            ledger_bytes_equal,
            audio_distinct
        );
        const auto total_milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - begin
        ).count();
        std::cerr << "total offline processing/write time: " << total_milliseconds << " ms\n";
        std::cout << options.output_directory.getFullPathName() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "cinderwheel-render: " << error.what() << '\n';
        printUsage(std::cerr, argc > 0 ? argv[0] : "cinderwheel-render");
        return 2;
    }
}
