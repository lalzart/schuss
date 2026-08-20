#include "tidepit/core.hpp"
#include "schuss/instrument_lab/renderer_artifacts.hpp"

#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_core/juce_core.h>
#include <juce_cryptography/juce_cryptography.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
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

#ifndef TIDE_PIT_EXPERIMENT_PATH
#define TIDE_PIT_EXPERIMENT_PATH "experiment.json"
#endif

#ifndef TIDE_PIT_EXPERIMENT_SHA256
#define TIDE_PIT_EXPERIMENT_SHA256 \
    "f8baac381d1e83f2e5db6ee4b56988299d5ae7b3e5b1b2ff4bcdfd1a0459c9fd"
#endif

namespace {

constexpr std::uint32_t kSampleRate = 48000;
constexpr double kQ27Scale = 134217728.0;
constexpr std::string_view kManifestName = "render-manifest.json";

struct Options {
    juce::File output_directory;
    juce::File experiment_file{juce::String::fromUTF8(TIDE_PIT_EXPERIMENT_PATH)};
    std::uint32_t block_frames{128};
};

struct ScheduledEvent {
    std::uint64_t sample{};
    std::uint64_t ingress_sequence{};
    tidepit::SemanticAction action{tidepit::SemanticAction::set_stage_1};
    double value{};
};

struct Condition {
    std::string id;
    std::string purpose;
    std::uint64_t duration_samples{};
    std::vector<ScheduledEvent> events;
    bool canonical{};
};

struct Experiment {
    std::string schema_version;
    std::string sha256;
    std::string canonical_id;
    std::string canonical_sha256;
    std::uint64_t canonical_bytes{};
    std::int64_t canonical_peak_q27{};
    double canonical_rms_q27{};
    std::uint32_t sample_rate{};
    std::vector<std::uint32_t> supported_blocks;
    std::vector<Condition> conditions;
};

struct Measurements {
    std::int64_t peak_q27{};
    double normalized_peak{};
    double rms_q27{};
    double dc_mean_left{};
    double dc_mean_right{};
    bool finite{true};
};

struct RenderResult {
    std::string id;
    std::string purpose;
    std::uint64_t duration_samples{};
    std::string q27_sha256;
    std::uint64_t q27_bytes{};
    std::optional<std::string> retained_q27_name;
    std::optional<std::string> wav_name;
    std::optional<std::string> wav_sha256;
    std::int64_t wav_bytes{};
    Measurements measurements;
    tidepit::Diagnostics diagnostics;
    tidepit::Snapshot final_state;
};

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error(message);
}

using schuss::instrument_lab::jsonEscape;

std::string jsonNumber(double value) {
    return schuss::instrument_lab::finiteJsonNumber(value);
}

const juce::DynamicObject& requireObject(const juce::var& value, std::string_view context) {
    const auto* object = value.getDynamicObject();
    if (object == nullptr) fail(std::string(context) + " must be an object");
    return *object;
}

const juce::Array<juce::var>& requireArray(const juce::var& value, std::string_view context) {
    const auto* array = value.getArray();
    if (array == nullptr) fail(std::string(context) + " must be an array");
    return *array;
}

juce::var requireProperty(
    const juce::DynamicObject& object,
    const char* name,
    std::string_view context
) {
    const juce::Identifier identifier(name);
    if (!object.hasProperty(identifier)) {
        fail(std::string(context) + " is missing " + name);
    }
    return object.getProperty(identifier);
}

std::string requireString(const juce::var& value, std::string_view context) {
    if (!value.isString()) fail(std::string(context) + " must be a string");
    return value.toString().toStdString();
}

double requireNumber(const juce::var& value, std::string_view context) {
    if (!(value.isInt() || value.isInt64() || value.isDouble())) {
        fail(std::string(context) + " must be numeric");
    }
    const auto number = static_cast<double>(value);
    if (!std::isfinite(number)) fail(std::string(context) + " must be finite");
    return number;
}

std::uint64_t requireUnsigned(const juce::var& value, std::string_view context) {
    const auto number = requireNumber(value, context);
    if (number < 0.0
        || number > static_cast<double>(std::numeric_limits<std::uint64_t>::max())
        || std::floor(number) != number) {
        fail(std::string(context) + " must be a non-negative integer");
    }
    return static_cast<std::uint64_t>(number);
}

std::string sha256(const juce::File& file) {
    if (!file.existsAsFile()) fail("file does not exist: " + file.getFullPathName().toStdString());
    return juce::SHA256(file).toHexString().toStdString();
}

std::string sha256(const juce::MemoryBlock& block) {
    return juce::SHA256(block).toHexString().toStdString();
}

std::optional<std::uint32_t> parseBlock(std::string_view text) {
    for (const auto value : {16U, 64U, 128U, 512U}) {
        if (text == std::to_string(value)) return value;
    }
    return std::nullopt;
}

void printUsage(std::ostream& stream, const char* executable) {
    stream << "Usage: " << executable
           << " --output-dir PATH [--block 16|64|128|512]"
           << " [--experiment PATH]\n";
}

Options parseOptions(int argc, char** argv) {
    std::optional<juce::File> output_directory;
    Options options;
    for (int index = 1; index < argc; ++index) {
        const std::string_view argument(argv[index]);
        if (argument == "--help" || argument == "-h") {
            printUsage(std::cout, argv[0]);
            std::exit(0);
        }
        if (argument == "--output-dir") {
            if (++index >= argc) fail("--output-dir requires a path");
            output_directory = juce::File(juce::String::fromUTF8(argv[index]));
            continue;
        }
        if (argument == "--experiment") {
            if (++index >= argc) fail("--experiment requires a path");
            options.experiment_file = juce::File(juce::String::fromUTF8(argv[index]));
            continue;
        }
        if (argument == "--block") {
            if (++index >= argc) fail("--block requires 16, 64, 128, or 512");
            const auto parsed = parseBlock(argv[index]);
            if (!parsed.has_value()) fail("--block must be 16, 64, 128, or 512");
            options.block_frames = *parsed;
            continue;
        }
        fail("unknown argument: " + std::string(argument));
    }
    if (!output_directory.has_value()) fail("--output-dir is required");
    options.output_directory = *output_directory;
    return options;
}

tidepit::SemanticAction actionForName(const std::string& name) {
    using Action = tidepit::SemanticAction;
    if (name == "source-next") return Action::source_next;
    if (name == "mutate") return Action::mutate;
    if (name == "lock-toggle") return Action::lock_toggle;
    if (name == "capture-toggle") return Action::capture_toggle;
    if (name == "effect-next") return Action::effect_next;
    if (name == "target-next") return Action::target_next;
    if (name == "scale-next") return Action::scale_next;
    if (name == "set-fx-a") return Action::set_fx_a;
    if (name == "set-fx-b") return Action::set_fx_b;
    if (name == "set-root") return Action::set_root;
    fail("unknown experiment action: " + name);
}

void appendEvent(
    Condition& condition,
    std::uint64_t sample,
    std::uint64_t& sequence,
    tidepit::SemanticAction action,
    double value
) {
    condition.events.push_back({sample, ++sequence, action, value});
}

void parseInitialControls(
    Condition& condition,
    const juce::DynamicObject& controls,
    std::uint64_t& sequence
) {
    using Action = tidepit::SemanticAction;
    appendEvent(condition, 0, sequence, Action::set_stage_1,
                requireNumber(requireProperty(controls, "stage_1", "controls"), "stage_1"));
    appendEvent(condition, 0, sequence, Action::set_stage_2,
                requireNumber(requireProperty(controls, "stage_2", "controls"), "stage_2"));
    appendEvent(condition, 0, sequence, Action::set_stage_3,
                requireNumber(requireProperty(controls, "stage_3", "controls"), "stage_3"));
    appendEvent(condition, 0, sequence, Action::set_stage_4,
                requireNumber(requireProperty(controls, "stage_4", "controls"), "stage_4"));
    appendEvent(condition, 0, sequence, Action::set_rate,
                requireNumber(requireProperty(controls, "rate", "controls"), "rate"));
    appendEvent(condition, 0, sequence, Action::set_memory,
                requireNumber(requireProperty(controls, "memory", "controls"), "memory"));
    appendEvent(condition, 0, sequence, Action::set_material,
                requireNumber(requireProperty(controls, "material", "controls"), "material"));
    appendEvent(condition, 0, sequence, Action::set_position,
                requireNumber(requireProperty(controls, "position", "controls"), "position"));
    appendEvent(condition, 0, sequence, Action::set_fx_a,
                requireNumber(requireProperty(controls, "fx_a", "controls"), "fx_a"));
    appendEvent(condition, 0, sequence, Action::set_fx_b,
                requireNumber(requireProperty(controls, "fx_b", "controls"), "fx_b"));
    appendEvent(condition, 0, sequence, Action::set_root,
                requireNumber(requireProperty(controls, "root", "controls"), "root"));
}

Condition parseCondition(
    const juce::var& value,
    const std::string& canonical_id
) {
    const auto& object = requireObject(value, "condition");
    Condition condition;
    condition.id = requireString(requireProperty(object, "id", "condition"), "condition.id");
    condition.purpose = requireString(
        requireProperty(object, "purpose", "condition"),
        "condition.purpose"
    );
    condition.canonical = condition.id == canonical_id;

    const bool has_samples = object.hasProperty(juce::Identifier("duration_samples"));
    const bool has_blocks = object.hasProperty(juce::Identifier("duration_internal_blocks"));
    if (has_samples == has_blocks) {
        fail("condition must contain exactly one duration field: " + condition.id);
    }
    condition.duration_samples = has_samples
        ? requireUnsigned(object.getProperty(juce::Identifier("duration_samples")), "duration_samples")
        : requireUnsigned(
              object.getProperty(juce::Identifier("duration_internal_blocks")),
              "duration_internal_blocks"
          ) * tidepit::kReferenceQuantumFrames;
    if (condition.duration_samples == 0
        || condition.duration_samples % tidepit::kReferenceQuantumFrames != 0) {
        fail("condition duration must be a positive multiple of 16: " + condition.id);
    }

    std::uint64_t sequence = 0;
    parseInitialControls(
        condition,
        requireObject(requireProperty(object, "controls", "condition"), "condition.controls"),
        sequence
    );
    const auto& events = requireArray(
        requireProperty(object, "events", "condition"),
        "condition.events"
    );
    for (const auto& event_value : events) {
        const auto& event = requireObject(event_value, "event");
        const auto action_name = requireString(
            requireProperty(event, "action", "event"),
            "event.action"
        );
        const auto sample = requireUnsigned(
            requireProperty(event, "sample_index", "event"),
            "event.sample_index"
        );
        if (sample >= condition.duration_samples) {
            fail("event lies outside condition: " + condition.id);
        }
        double event_value_number = 0.0;
        if (event.hasProperty(juce::Identifier("value"))) {
            event_value_number = requireNumber(
                event.getProperty(juce::Identifier("value")),
                "event.value"
            );
        }
        appendEvent(
            condition,
            sample,
            sequence,
            actionForName(action_name),
            event_value_number
        );
    }
    std::stable_sort(
        condition.events.begin(),
        condition.events.end(),
        [](const auto& left, const auto& right) {
            if (left.sample != right.sample) return left.sample < right.sample;
            return left.ingress_sequence < right.ingress_sequence;
        }
    );
    return condition;
}

Experiment loadExperiment(const juce::File& file, std::uint32_t selected_block) {
    if (!file.existsAsFile()) {
        fail("experiment does not exist: " + file.getFullPathName().toStdString());
    }
    Experiment experiment;
    experiment.sha256 = sha256(file);
    if (experiment.sha256 != TIDE_PIT_EXPERIMENT_SHA256) {
        fail(
            "experiment SHA-256 mismatch: expected "
            TIDE_PIT_EXPERIMENT_SHA256 " but observed " + experiment.sha256
        );
    }

    const auto document = juce::JSON::parse(file.loadFileAsString());
    const auto& root = requireObject(document, "experiment");
    experiment.schema_version = requireString(
        requireProperty(root, "schema_version", "experiment"),
        "experiment.schema_version"
    );
    if (experiment.schema_version != "sonic-research-lab-experiment-v1") {
        fail("unsupported experiment schema: " + experiment.schema_version);
    }
    experiment.sample_rate = static_cast<std::uint32_t>(requireUnsigned(
        requireProperty(root, "sample_rate_hz", "experiment"),
        "sample_rate_hz"
    ));
    if (experiment.sample_rate != kSampleRate) fail("experiment must remain at 48000 Hz");
    const auto seed = requireUnsigned(requireProperty(root, "seed", "experiment"), "seed");
    if (seed != 33U) fail("experiment seed must remain the source LCG seed 33");
    experiment.canonical_id = requireString(
        requireProperty(root, "comparator_condition_id", "experiment"),
        "comparator_condition_id"
    );

    for (const auto& block : requireArray(
             requireProperty(root, "supported_block_frames", "experiment"),
             "supported_block_frames")) {
        experiment.supported_blocks.push_back(static_cast<std::uint32_t>(
            requireUnsigned(block, "supported block")
        ));
    }
    if (std::find(
            experiment.supported_blocks.begin(),
            experiment.supported_blocks.end(),
            selected_block) == experiment.supported_blocks.end()) {
        fail("selected block size is absent from the experiment");
    }

    const auto& tolerances = requireObject(
        requireProperty(root, "tolerances", "experiment"),
        "tolerances"
    );
    experiment.canonical_sha256 = requireString(
        requireProperty(tolerances, "canonical_clean_sha256", "tolerances"),
        "canonical_clean_sha256"
    );
    experiment.canonical_bytes = requireUnsigned(
        requireProperty(tolerances, "canonical_clean_bytes", "tolerances"),
        "canonical_clean_bytes"
    );
    experiment.canonical_peak_q27 = static_cast<std::int64_t>(requireUnsigned(
        requireProperty(tolerances, "canonical_clean_peak_q27", "tolerances"),
        "canonical_clean_peak_q27"
    ));
    experiment.canonical_rms_q27 = requireNumber(
        requireProperty(tolerances, "canonical_clean_rms_q27", "tolerances"),
        "canonical_clean_rms_q27"
    );

    const auto& condition_values = requireArray(
        requireProperty(root, "conditions", "experiment"),
        "conditions"
    );
    for (const auto& value : condition_values) {
        experiment.conditions.push_back(parseCondition(value, experiment.canonical_id));
    }
    if (experiment.conditions.size() != 3U
        || std::count_if(
               experiment.conditions.begin(),
               experiment.conditions.end(),
               [](const auto& condition) { return condition.canonical; }) != 1) {
        fail("experiment must contain exactly three conditions and one comparator");
    }

    const auto& outputs = requireArray(
        requireProperty(root, "outputs", "experiment"),
        "outputs"
    );
    std::vector<std::string> output_names;
    for (const auto& output_value : outputs) {
        const auto& output = requireObject(output_value, "output");
        output_names.push_back(requireString(
            requireProperty(output, "name", "output"),
            "output.name"
        ));
    }
    const std::array<std::string, 4> expected_outputs{{
        experiment.canonical_id + ".q27le",
        "performance-state-trace.wav",
        "parameter-extremes.wav",
        std::string(kManifestName),
    }};
    for (const auto& expected : expected_outputs) {
        if (std::find(output_names.begin(), output_names.end(), expected) == output_names.end()) {
            fail("experiment output set is missing " + expected);
        }
    }
    if (output_names.size() != expected_outputs.size()) {
        fail("experiment output set contains an unexpected artifact");
    }
    return experiment;
}

void checkOutputDirectory(const juce::File& directory) {
    if (directory.exists() && !directory.isDirectory()) {
        fail("output path exists but is not a directory");
    }
    if (directory.isDirectory() && directory.getNumberOfChildFiles(juce::File::findFilesAndDirectories) != 0) {
        fail("refusing to overwrite a non-empty output directory");
    }
    if (!directory.exists()) {
        const auto result = directory.createDirectory();
        if (result.failed()) {
            fail("cannot create output directory: " + result.getErrorMessage().toStdString());
        }
    }
}

void appendInt32LittleEndian(juce::MemoryBlock& destination, std::int32_t value) {
    const auto bits = static_cast<std::uint32_t>(value);
    const std::array<std::uint8_t, 4> bytes{{
        static_cast<std::uint8_t>(bits & 0xffU),
        static_cast<std::uint8_t>((bits >> 8U) & 0xffU),
        static_cast<std::uint8_t>((bits >> 16U) & 0xffU),
        static_cast<std::uint8_t>((bits >> 24U) & 0xffU),
    }};
    destination.append(bytes.data(), bytes.size());
}

void updateMeasurements(
    Measurements& measurements,
    const std::int32_t* left,
    const std::int32_t* right,
    std::uint32_t frames,
    double& square_sum,
    double& left_sum,
    double& right_sum
) {
    for (std::uint32_t frame = 0; frame < frames; ++frame) {
        const auto left_value = static_cast<std::int64_t>(left[frame]);
        const auto right_value = static_cast<std::int64_t>(right[frame]);
        measurements.peak_q27 = std::max(
            measurements.peak_q27,
            std::max(std::llabs(left_value), std::llabs(right_value))
        );
        square_sum += static_cast<double>(left_value) * static_cast<double>(left_value);
        square_sum += static_cast<double>(right_value) * static_cast<double>(right_value);
        left_sum += static_cast<double>(left_value) / kQ27Scale;
        right_sum += static_cast<double>(right_value) / kQ27Scale;
        measurements.finite = measurements.finite
            && std::isfinite(static_cast<double>(left[frame]) / kQ27Scale)
            && std::isfinite(static_cast<double>(right[frame]) / kQ27Scale);
    }
}

void appendQuantumPlanar(
    juce::MemoryBlock& output,
    const std::int32_t* left,
    const std::int32_t* right,
    std::uint32_t frames
) {
    if (frames % tidepit::kReferenceQuantumFrames != 0) {
        fail("renderer received a partial source quantum");
    }
    for (std::uint32_t origin = 0; origin < frames;
         origin += tidepit::kReferenceQuantumFrames) {
        for (std::uint32_t frame = 0; frame < tidepit::kReferenceQuantumFrames; ++frame) {
            appendInt32LittleEndian(output, left[origin + frame]);
        }
        for (std::uint32_t frame = 0; frame < tidepit::kReferenceQuantumFrames; ++frame) {
            appendInt32LittleEndian(output, right[origin + frame]);
        }
    }
}

std::size_t applyInitialControls(tidepit::Core& core, const Condition& condition) {
    constexpr std::size_t initial_control_count = 11;
    if (condition.events.size() < initial_control_count) {
        fail("condition is missing its frozen initial controls");
    }
    for (std::size_t index = 0; index < initial_control_count; ++index) {
        const auto& event = condition.events[index];
        if (event.sample != 0) fail("initial control is not at sample zero");
        bool accepted = false;
        if (event.action == tidepit::SemanticAction::set_root) {
            const auto normalized = (event.value - 36.0) / 36.0;
            accepted = core.setControlNormalized(event.action, normalized);
        } else {
            // The source contract enters controls through 32-bit float/Q27.
            // Decimal JSON values are narrowed before the setter so the
            // canonical source fixture is not silently promoted to double.
            accepted = core.setControlNormalized(
                event.action,
                static_cast<double>(static_cast<float>(event.value))
            );
        }
        if (!accepted) fail("Core rejected a frozen initial control");
    }
    return initial_control_count;
}

RenderResult renderCondition(
    const juce::File& output_directory,
    const Experiment& experiment,
    const Condition& condition,
    std::uint32_t block_frames
) {
    RenderResult result;
    result.id = condition.id;
    result.purpose = condition.purpose;
    result.duration_samples = condition.duration_samples;

    tidepit::Core core;
    if (!core.prepare(kSampleRate, block_frames)) {
        fail("Core rejected the frozen renderer configuration");
    }
    const auto initial_schedule_index = applyInitialControls(core, condition);

    std::array<std::int32_t, tidepit::kMaximumBlockFrames> left{};
    std::array<std::int32_t, tidepit::kMaximumBlockFrames> right{};
    juce::AudioBuffer<float> audio(2, static_cast<int>(block_frames));
    juce::MemoryBlock q27_bytes;

    std::unique_ptr<juce::AudioFormatWriter> writer;
    if (!condition.canonical) {
        result.wav_name = condition.id + ".wav";
        std::unique_ptr<juce::OutputStream> stream =
            output_directory.getChildFile(*result.wav_name).createOutputStream();
        if (stream == nullptr) fail("cannot create " + *result.wav_name);
        juce::WavAudioFormat format;
        const auto options = juce::AudioFormatWriterOptions()
            .withSampleRate(kSampleRate)
            .withNumChannels(2)
            .withBitsPerSample(24);
        writer = format.createWriterFor(stream, options);
        if (writer == nullptr) fail("cannot create WAV writer for " + *result.wav_name);
    }

    std::size_t schedule_index = initial_schedule_index;
    std::uint64_t origin = 0;
    double square_sum = 0.0;
    double left_sum = 0.0;
    double right_sum = 0.0;
    while (origin < condition.duration_samples) {
        const auto frames = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            block_frames,
            condition.duration_samples - origin
        ));
        if (frames == 0 || frames % tidepit::kReferenceQuantumFrames != 0) {
            fail("experiment duration is incompatible with selected block size");
        }

        std::array<tidepit::SemanticEvent, tidepit::kMaximumSemanticEvents> block_events{};
        std::size_t event_count = 0;
        while (schedule_index < condition.events.size()
            && condition.events[schedule_index].sample < origin + frames) {
            const auto& event = condition.events[schedule_index++];
            if (event.sample < origin || event_count == block_events.size()) {
                fail("experiment event ordering/capacity failure");
            }
            block_events[event_count++] = {
                static_cast<std::uint32_t>(event.sample - origin),
                event.ingress_sequence,
                event.action,
                event.value,
            };
        }

        const auto report = core.processQ27(
            left.data(),
            right.data(),
            frames,
            block_events.data(),
            event_count
        );
        if (report.events_dropped != 0 || report.events_accepted != event_count) {
            fail("Core rejected a frozen experiment event");
        }

        appendQuantumPlanar(q27_bytes, left.data(), right.data(), frames);
        updateMeasurements(
            result.measurements,
            left.data(),
            right.data(),
            frames,
            square_sum,
            left_sum,
            right_sum
        );
        if (writer != nullptr) {
            for (std::uint32_t frame = 0; frame < frames; ++frame) {
                audio.setSample(0, static_cast<int>(frame),
                                static_cast<float>(static_cast<double>(left[frame]) / kQ27Scale));
                audio.setSample(1, static_cast<int>(frame),
                                static_cast<float>(static_cast<double>(right[frame]) / kQ27Scale));
            }
            if (!writer->writeFromAudioSampleBuffer(audio, 0, static_cast<int>(frames))) {
                fail("WAV write failed for " + *result.wav_name);
            }
        }
        origin += frames;
    }
    if (schedule_index != condition.events.size()) fail("render ended before event schedule");
    writer.reset();

    result.q27_sha256 = sha256(q27_bytes);
    result.q27_bytes = q27_bytes.getSize();
    result.measurements.normalized_peak =
        static_cast<double>(result.measurements.peak_q27) / kQ27Scale;
    result.measurements.rms_q27 = std::sqrt(
        square_sum / static_cast<double>(condition.duration_samples * 2U)
    );
    result.measurements.dc_mean_left = left_sum / static_cast<double>(condition.duration_samples);
    result.measurements.dc_mean_right = right_sum / static_cast<double>(condition.duration_samples);
    result.diagnostics = core.diagnostics();
    result.final_state = core.snapshot();

    if (condition.canonical) {
        result.retained_q27_name = condition.id + ".q27le";
        const auto file = output_directory.getChildFile(*result.retained_q27_name);
        std::unique_ptr<juce::OutputStream> stream = file.createOutputStream();
        if (stream == nullptr
            || !stream->write(q27_bytes.getData(), q27_bytes.getSize())) {
            fail("canonical Q27 write failed");
        }
        stream->flush();
        if (result.q27_sha256 != experiment.canonical_sha256
            || result.q27_bytes != experiment.canonical_bytes
            || result.measurements.peak_q27 != experiment.canonical_peak_q27
            || std::abs(result.measurements.rms_q27 - experiment.canonical_rms_q27) >= 1.0e-6) {
            fail(
                "source reference differs: expected " + experiment.canonical_sha256
                + " but observed " + result.q27_sha256
            );
        }
    } else {
        const auto file = output_directory.getChildFile(*result.wav_name);
        result.wav_sha256 = sha256(file);
        result.wav_bytes = file.getSize();
    }
    return result;
}

std::string displayLine(const std::array<char, 22>& line) {
    return std::string(line.data(), 21U);
}

void writeSnapshot(std::ostream& stream, const tidepit::Snapshot& snapshot) {
    stream << "{\n"
           << "        \"absolute_sample\": " << snapshot.absolute_sample << ",\n"
           << "        \"active_stage\": " << static_cast<unsigned>(snapshot.stage + 1U) << ",\n"
           << "        \"capture\": " << (snapshot.captured ? "true" : "false") << ",\n"
           << "        \"controls\": {\n"
           << "          \"fx_a\": " << jsonNumber(snapshot.controls.fx_a) << ",\n"
           << "          \"fx_b\": " << jsonNumber(snapshot.controls.fx_b) << ",\n"
           << "          \"material\": " << jsonNumber(snapshot.controls.material) << ",\n"
           << "          \"memory\": " << jsonNumber(snapshot.controls.memory) << ",\n"
           << "          \"position\": " << jsonNumber(snapshot.controls.position) << ",\n"
           << "          \"rate\": " << jsonNumber(snapshot.controls.rate) << ",\n"
           << "          \"root_note\": " << snapshot.controls.root_note << ",\n"
           << "          \"stages\": [";
    for (std::size_t index = 0; index < snapshot.controls.stages.size(); ++index) {
        if (index != 0) stream << ", ";
        stream << jsonNumber(snapshot.controls.stages[index]);
    }
    stream << "]\n"
           << "        },\n"
           << "        \"display_lines\": [";
    for (std::size_t index = 0; index < snapshot.display_lines.size(); ++index) {
        if (index != 0) stream << ", ";
        stream << '"' << jsonEscape(displayLine(snapshot.display_lines[index])) << '"';
    }
    stream << "],\n"
           << "        \"effect\": \"" << tidepit::effectName(snapshot.effect) << "\",\n"
           << "        \"effect_crossfade\": " << jsonNumber(snapshot.effect_crossfade) << ",\n"
           << "        \"effect_parameters\": [";
    for (std::size_t mode = 0; mode < snapshot.effect_parameters.size(); ++mode) {
        if (mode != 0) stream << ", ";
        stream << '['
               << jsonNumber(snapshot.effect_parameters[mode][0]) << ", "
               << jsonNumber(snapshot.effect_parameters[mode][1]) << ']';
    }
    stream << "],\n"
           << "        \"effective_fx_a\": " << jsonNumber(snapshot.effective_fx_a) << ",\n"
           << "        \"effective_fx_b\": " << jsonNumber(snapshot.effective_fx_b) << ",\n"
           << "        \"fx_a_pickup_active\": "
           << (snapshot.fx_a_pickup_active ? "true" : "false") << ",\n"
           << "        \"fx_b_pickup_active\": "
           << (snapshot.fx_b_pickup_active ? "true" : "false") << ",\n"
           << "        \"granular_available\": "
           << (snapshot.granular_available ? "true" : "false") << ",\n"
           << "        \"lock\": " << (snapshot.locked ? "true" : "false") << ",\n"
           << "        \"mutation\": [";
    for (std::size_t index = 0; index < snapshot.mutation.size(); ++index) {
        if (index != 0) stream << ", ";
        stream << static_cast<int>(snapshot.mutation[index]);
    }
    stream << "],\n"
           << "        \"prepared\": " << (snapshot.prepared ? "true" : "false") << ",\n"
           << "        \"record_write_head\": " << snapshot.record_write_head << ",\n"
           << "        \"root_note\": " << snapshot.controls.root_note << ",\n"
           << "        \"scale\": \"" << tidepit::scaleName(snapshot.scale) << "\",\n"
           << "        \"source\": \"" << tidepit::sourceName(snapshot.source) << "\",\n"
           << "        \"sympathetic_division\": "
           << static_cast<unsigned>(snapshot.sympathetic_division) << ",\n"
           << "        \"target\": \"" << tidepit::targetName(snapshot.target) << "\"\n"
           << "      }";
}

void writeDiagnostics(std::ostream& stream, const tidepit::Diagnostics& diagnostics) {
    stream << "{\n"
           << "        \"events_dropped\": " << diagnostics.semantic_events_dropped << ",\n"
           << "        \"gesture_queue_overflows\": "
           << diagnostics.gesture_queue_overflows << ",\n"
           << "        \"invalid_events\": " << diagnostics.invalid_events << ",\n"
           << "        \"processed_frames\": " << diagnostics.processed_frames << ",\n"
           << "        \"processed_quanta\": " << diagnostics.processed_quanta << ",\n"
           << "        \"semantic_events_accepted\": "
           << diagnostics.semantic_events_accepted << ",\n"
           << "        \"unsupported_process_calls\": "
           << diagnostics.unsupported_process_calls << "\n"
           << "      }";
}

void writeManifest(
    const juce::File& output_directory,
    const Experiment& experiment,
    const std::vector<RenderResult>& results,
    std::uint32_t block_frames
) {
    const auto manifest = output_directory.getChildFile(juce::String(kManifestName.data()));
    std::ofstream stream(manifest.getFullPathName().toStdString(), std::ios::binary);
    stream.imbue(std::locale::classic());
    if (!stream) fail("cannot create render manifest");
    const auto canonical = std::find_if(
        results.begin(),
        results.end(),
        [&experiment](const auto& result) { return result.id == experiment.canonical_id; }
    );
    if (canonical == results.end()) fail("canonical result is missing");

    stream << "{\n"
           << "  \"block_frames\": " << block_frames << ",\n"
           << "  \"canonical_reference\": {\"expected_sha256\": \""
           << jsonEscape(experiment.canonical_sha256) << "\", \"matches\": "
           << (canonical->q27_sha256 == experiment.canonical_sha256 ? "true" : "false")
           << "},\n"
           << "  \"condition_count\": " << results.size() << ",\n"
           << "  \"evidence_boundary\": {\n"
           << "    \"listening_claimed\": false,\n"
           << "    \"offline_host_signal_only\": true,\n"
           << "    \"physical_device_opened\": false,\n"
           << "    \"real_time_fitness_claimed\": false\n"
           << "  },\n"
           << "  \"experiment\": {\"schema_version\": \""
           << jsonEscape(experiment.schema_version) << "\", \"sha256\": \""
           << jsonEscape(experiment.sha256) << "\"},\n"
           << "  \"results\": [\n";
    for (std::size_t index = 0; index < results.size(); ++index) {
        const auto& result = results[index];
        stream << "    {\n"
               << "      \"diagnostics\": ";
        writeDiagnostics(stream, result.diagnostics);
        stream << ",\n"
               << "      \"duration_samples\": " << result.duration_samples << ",\n"
               << "      \"final_state\": ";
        writeSnapshot(stream, result.final_state);
        stream << ",\n"
               << "      \"id\": \"" << jsonEscape(result.id) << "\",\n"
               << "      \"measurements\": {\n"
               << "        \"dc_mean_left\": "
               << jsonNumber(result.measurements.dc_mean_left) << ",\n"
               << "        \"dc_mean_right\": "
               << jsonNumber(result.measurements.dc_mean_right) << ",\n"
               << "        \"finite\": "
               << (result.measurements.finite ? "true" : "false") << ",\n"
               << "        \"normalized_peak\": "
               << jsonNumber(result.measurements.normalized_peak) << ",\n"
               << "        \"peak_q27\": " << result.measurements.peak_q27 << ",\n"
               << "        \"rms_q27\": " << jsonNumber(result.measurements.rms_q27) << "\n"
               << "      },\n"
               << "      \"purpose\": \"" << jsonEscape(result.purpose) << "\",\n"
               << "      \"q27\": {\"bytes\": " << result.q27_bytes
               << ", \"retained_file\": ";
        if (result.retained_q27_name.has_value()) {
            stream << '"' << jsonEscape(*result.retained_q27_name) << '"';
        } else {
            stream << "null";
        }
        stream << ", \"sha256\": \"" << result.q27_sha256 << "\"},\n"
               << "      \"wav\": ";
        if (result.wav_name.has_value()) {
            stream << "{\"bytes\": " << result.wav_bytes
                   << ", \"file\": \"" << jsonEscape(*result.wav_name)
                   << "\", \"sha256\": \"" << jsonEscape(*result.wav_sha256) << "\"}";
        } else {
            stream << "null";
        }
        stream << "\n    }" << (index + 1U == results.size() ? "\n" : ",\n");
    }
    stream << "  ],\n"
           << "  \"sample_rate_hz\": " << experiment.sample_rate << ",\n"
           << "  \"schema_version\": \"tide-pit-render-manifest-v1\"\n"
           << "}\n";
    stream.close();
    if (!stream) fail("render manifest write failed");
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const auto options = parseOptions(argc, argv);
        const auto experiment = loadExperiment(options.experiment_file, options.block_frames);
        checkOutputDirectory(options.output_directory);
        std::vector<RenderResult> results;
        results.reserve(experiment.conditions.size());
        for (const auto& condition : experiment.conditions) {
            results.push_back(renderCondition(
                options.output_directory,
                experiment,
                condition,
                options.block_frames
            ));
            std::cerr << condition.id << ": " << results.back().q27_sha256 << '\n';
        }
        writeManifest(options.output_directory, experiment, results, options.block_frames);
        std::cout << options.output_directory.getFullPathName() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "tide-pit-render: " << error.what() << '\n';
        return 1;
    }
}
