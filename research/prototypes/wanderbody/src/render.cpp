#include "wanderbody/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace wb = wanderbody;
namespace fs = std::filesystem;

namespace {

constexpr std::uint32_t kSampleRate = 48000U;
constexpr std::uint64_t kDurationFrames = 12ULL * kSampleRate;
constexpr double kPi = 3.1415926535897932384626433832795;

struct Arguments final {
    std::string condition{};
    std::uint32_t block_frames{127U};
    fs::path output{};
};

struct SignalMetrics final {
    long double square_sum{};
    long double left_sum{};
    long double right_sum{};
    long double stereo_difference_sum{};
    float peak{};
    std::uint64_t non_finite_count{};

    void add(float left, float right) noexcept {
        if (!(std::isfinite(left) && std::isfinite(right))) {
            ++non_finite_count;
            return;
        }
        peak = std::max(peak, std::max(std::abs(left), std::abs(right)));
        left_sum += left;
        right_sum += right;
        square_sum += static_cast<long double>(left) * left
            + static_cast<long double>(right) * right;
        const auto difference = static_cast<long double>(left) - right;
        stereo_difference_sum += difference * difference;
    }
};

[[nodiscard]] Arguments parseArguments(int argc, char** argv) {
    Arguments result{};
    for (int index = 1; index < argc; ++index) {
        const std::string_view argument{argv[index]};
        if (argument == "--condition" && index + 1 < argc) {
            result.condition = argv[++index];
        } else if (argument == "--block" && index + 1 < argc) {
            const auto parsed = std::stoul(argv[++index]);
            if (parsed > std::numeric_limits<std::uint32_t>::max()) {
                throw std::invalid_argument("block size is out of range");
            }
            result.block_frames = static_cast<std::uint32_t>(parsed);
        } else if (argument == "--output" && index + 1 < argc) {
            result.output = argv[++index];
        } else {
            throw std::invalid_argument(
                "unknown or incomplete argument: " + std::string(argument));
        }
    }
    static constexpr std::array<std::string_view, 10U> conditions{{
        "WB01_HOVER", "WB02_DRUNK", "WB03_LOCKED", "WB04_SHUFFLED",
        "WB05_MUTATED", "WB06_BODY", "WB07_FREEZE_CLEAR", "WB08_EXTREMES",
        "WB09_SILENCE", "WB10_UNCORRELATED",
    }};
    const bool known = std::find(conditions.begin(), conditions.end(), result.condition)
        != conditions.end();
    if (!known || result.output.empty() || result.block_frames == 0U
        || result.block_frames > wb::kMaximumBlockFrames) {
        throw std::invalid_argument(
            "usage: wanderbody-render --condition WB01_HOVER --block 127 --output DIRECTORY");
    }
    return result;
}

void configureInitial(
    std::string_view condition,
    wb::Controls& controls,
    wb::Core& core) noexcept {
    if (condition == "WB01_HOVER" || condition == "WB02_DRUNK") {
        controls.internal = 0.0;
    } else if (condition == "WB03_LOCKED"
        || condition == "WB04_SHUFFLED"
        || condition == "WB05_MUTATED") {
        controls.internal = 0.0;
        controls.motion = wb::MotionMode::drunk;
        controls.wander = 0.62;
        controls.recurrence = wb::RecurrenceMode::fresh;
    } else if (condition == "WB06_BODY") {
        controls.external = 1.0;
        controls.internal = 0.0;
        controls.body = 0.0;
        controls.dry = 0.70;
        controls.memory = 0.70;
    } else if (condition == "WB09_SILENCE") {
        controls.external = 0.0;
        controls.internal = 0.0;
        controls.dry = 0.0;
        controls.memory = 0.0;
        controls.body = 0.0;
        controls.energy = 0.0;
    } else if (condition == "WB10_UNCORRELATED") {
        controls.internal = 0.0;
        controls.body = 0.0;
        controls.motion = wb::MotionMode::drunk;
        core.setGenerationMode(wb::GenerationMode::independent_uniform);
    }
}

void applyTimeline(
    std::string_view condition,
    std::uint64_t frame,
    wb::Controls& controls,
    wb::ActionSequences& actions) noexcept {
    if (frame == 2ULL * kSampleRate) {
        if (condition == "WB01_HOVER") {
            controls.motion = wb::MotionMode::hover;
            controls.anchor = 0.56;
            controls.field = 0.18;
            controls.wander = 0.45;
        } else if (condition == "WB02_DRUNK") {
            controls.motion = wb::MotionMode::drunk;
            controls.anchor = 0.50;
            controls.field = 0.42;
            controls.wander = 0.72;
        } else if (condition == "WB06_BODY") {
            controls.body = 0.72;
            controls.structure = 0.47;
            controls.brightness = 0.58;
            controls.damping = 0.62;
            controls.position = 0.31;
        } else if (condition == "WB10_UNCORRELATED") {
            controls.anchor = 0.50;
            controls.field = 0.42;
            controls.wander = 0.72;
        }
    }
    if (frame == 4ULL * kSampleRate && condition == "WB07_FREEZE_CLEAR") {
        ++actions.freeze;
    }
    if (frame == 6ULL * kSampleRate) {
        if (condition == "WB03_LOCKED") {
            controls.recurrence = wb::RecurrenceMode::locked;
        } else if (condition == "WB04_SHUFFLED") {
            controls.recurrence = wb::RecurrenceMode::shuffled;
        } else if (condition == "WB05_MUTATED") {
            controls.recurrence = wb::RecurrenceMode::mutated;
            controls.mutation = 0.55;
        } else if (condition == "WB07_FREEZE_CLEAR") {
            ++actions.freeze;
        }
    }
    if (frame == 8ULL * kSampleRate && condition == "WB07_FREEZE_CLEAR") {
        ++actions.clear;
    }
    if (condition == "WB08_EXTREMES") {
        if (frame == 0U) {
            controls.external = 1.0;
            controls.internal = 1.0;
            controls.anchor = 0.0;
            controls.field = 1.0;
            controls.motion = wb::MotionMode::drunk;
            controls.wander = 1.0;
            controls.mutation = 1.0;
            controls.fragment = 0.0;
            controls.energy = 1.0;
            controls.body = 1.0;
            controls.structure = 1.0;
            controls.brightness = 1.0;
            controls.damping = 1.0;
            controls.position = 0.0;
            controls.dry = 1.0;
            controls.memory = 1.0;
        } else if (frame >= 3ULL * kSampleRate && frame < 9ULL * kSampleRate
            && frame % 4096U == 0U) {
            const auto epoch = frame / 4096U;
            controls.anchor = (epoch & 1U) == 0U ? 0.0 : 1.0;
            controls.field = (epoch % 3U) == 0U ? 0.0 : 1.0;
            controls.wander = (epoch % 5U) == 0U ? 0.0 : 1.0;
            controls.fragment = (epoch % 7U) == 0U ? 1.0 : 0.0;
            controls.position = (epoch % 11U) == 0U ? 1.0 : 0.0;
            controls.motion = (epoch & 1U) == 0U
                ? wb::MotionMode::hover : wb::MotionMode::drunk;
            controls.recurrence = static_cast<wb::RecurrenceMode>(epoch % 4U);
        } else if (frame == 9ULL * kSampleRate) {
            ++actions.panic;
        } else if (frame == 9ULL * kSampleRate + 64U) {
            controls = wb::defaultControls();
            ++actions.reset;
        }
    }
}

[[nodiscard]] std::uint64_t nextTimelineBoundary(
    std::string_view condition,
    std::uint64_t frame) noexcept {
    auto boundary = std::numeric_limits<std::uint64_t>::max();
    const auto consider = [&](std::uint64_t candidate) {
        if (candidate > frame) boundary = std::min(boundary, candidate);
    };
    if (condition == "WB01_HOVER" || condition == "WB02_DRUNK"
        || condition == "WB06_BODY" || condition == "WB10_UNCORRELATED") {
        consider(2ULL * kSampleRate);
    }
    if (condition == "WB03_LOCKED" || condition == "WB04_SHUFFLED"
        || condition == "WB05_MUTATED") {
        consider(6ULL * kSampleRate);
    }
    if (condition == "WB07_FREEZE_CLEAR") {
        consider(4ULL * kSampleRate);
        consider(6ULL * kSampleRate);
        consider(8ULL * kSampleRate);
    }
    if (condition == "WB08_EXTREMES") {
        if (frame < 3ULL * kSampleRate) consider(3ULL * kSampleRate);
        if (frame >= 3ULL * kSampleRate && frame < 9ULL * kSampleRate) {
            consider(((frame / 4096U) + 1U) * 4096U);
        }
        consider(9ULL * kSampleRate);
        consider(9ULL * kSampleRate + 64U);
    }
    return boundary;
}

[[nodiscard]] float sourceSample(std::string_view condition, std::uint64_t frame) noexcept {
    if (condition == "WB09_SILENCE") return 0.0F;
    const double time = static_cast<double>(frame) / kSampleRate;
    if (condition == "WB06_BODY") {
        if (frame >= 2ULL * kSampleRate) return 0.0F;
        const double envelope = std::min(1.0, static_cast<double>(frame) / 480.0)
            * std::min(1.0, static_cast<double>(2ULL * kSampleRate - frame) / 2400.0);
        const double pulse = frame % 12000U < 80U
            ? 0.45 * std::exp(-static_cast<double>(frame % 12000U) / 16.0)
            : 0.0;
        return static_cast<float>(envelope
            * (0.22 * std::sin(2.0 * kPi * 97.0 * time)
               + 0.14 * std::sin(2.0 * kPi * 151.0 * time) + pulse));
    }
    const double impulse = frame % 24000U == 0U ? 0.7 : 0.0;
    return static_cast<float>(
        0.22 * std::sin(2.0 * kPi * 110.0 * time)
        + 0.11 * std::sin(2.0 * kPi * 173.0 * time)
        + impulse);
}

void writeU16(std::ostream& stream, std::uint16_t value) {
    stream.put(static_cast<char>(value & 0xffU));
    stream.put(static_cast<char>((value >> 8U) & 0xffU));
}

void writeU32(std::ostream& stream, std::uint32_t value) {
    for (unsigned shift = 0U; shift < 32U; shift += 8U) {
        stream.put(static_cast<char>((value >> shift) & 0xffU));
    }
}

void writeWav(const fs::path& path, const std::vector<float>& interleaved) {
    std::ofstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("cannot open WAV output");
    const auto data_size = static_cast<std::uint32_t>(interleaved.size() * 3U);
    stream.write("RIFF", 4);
    writeU32(stream, 36U + data_size);
    stream.write("WAVE", 4);
    stream.write("fmt ", 4);
    writeU32(stream, 16U);
    writeU16(stream, 1U);
    writeU16(stream, 2U);
    writeU32(stream, kSampleRate);
    writeU32(stream, kSampleRate * 6U);
    writeU16(stream, 6U);
    writeU16(stream, 24U);
    stream.write("data", 4);
    writeU32(stream, data_size);
    for (const auto sample : interleaved) {
        const auto integer = static_cast<std::int32_t>(std::clamp<long>(
            std::lround(std::clamp(sample, -1.0F, 1.0F) * 8388607.0F),
            -8388608L,
            8388607L));
        stream.put(static_cast<char>(integer & 0xff));
        stream.put(static_cast<char>((integer >> 8) & 0xff));
        stream.put(static_cast<char>((integer >> 16) & 0xff));
    }
}

void writeDecisions(
    const fs::path& path,
    std::string_view condition,
    const std::vector<wb::DecisionEvent>& decisions) {
    std::ofstream stream(path);
    if (!stream) throw std::runtime_error("cannot open decision output");
    stream << std::setprecision(17)
           << "{\n  \"condition\": \"" << condition << "\",\n  \"events\": [\n";
    for (std::size_t index = 0U; index < decisions.size(); ++index) {
        const auto& event = decisions[index];
        stream << "    {\"frame\":" << event.absolute_frame
               << ",\"ordinal\":" << event.ordinal
               << ",\"source_epoch\":" << event.source_epoch
               << ",\"source_start\":" << event.source_start_frame
               << ",\"position\":" << event.tuple.position
               << ",\"duration_seconds\":" << event.tuple.duration_seconds
               << ",\"rate\":" << event.tuple.rate
               << ",\"gain\":" << event.tuple.gain
               << ",\"pan\":" << event.tuple.pan
               << ",\"body_frequency_hz\":" << event.tuple.body_frequency_hz
               << ",\"direction\":" << static_cast<unsigned>(event.tuple.direction)
               << ",\"motion\":\"" << wb::motionName(event.motion)
               << "\",\"recurrence\":\"" << wb::recurrenceName(event.recurrence)
               << "\",\"history_index\":" << static_cast<unsigned>(event.history_index)
               << ",\"voice_index\":" << static_cast<unsigned>(event.voice_index)
               << ",\"replayed\":" << (event.replayed ? "true" : "false")
               << ",\"shuffled\":" << (event.shuffled ? "true" : "false")
               << ",\"mutated\":" << (event.mutated ? "true" : "false")
               << ",\"stolen\":" << (event.stolen ? "true" : "false") << '}'
               << (index + 1U == decisions.size() ? "\n" : ",\n");
    }
    stream << "  ]\n}\n";
}

void writeMetrics(
    const fs::path& path,
    const Arguments& arguments,
    const SignalMetrics& signal,
    const wb::Snapshot& snapshot,
    std::size_t decision_count,
    std::uint64_t freeze_hold_delta,
    long double body_early_difference_energy,
    long double body_late_difference_energy,
    long double body_mid_energy,
    long double bypass_mid_energy) {
    const long double frame_denominator = static_cast<long double>(kDurationFrames);
    const double body_ratio = bypass_mid_energy > 0.0L
        ? static_cast<double>(body_mid_energy / bypass_mid_energy) : 0.0;
    const double decay_ratio = body_early_difference_energy > 0.0L
        ? static_cast<double>(body_late_difference_energy / body_early_difference_energy) : 0.0;
    std::ofstream stream(path);
    if (!stream) throw std::runtime_error("cannot open metrics output");
    stream << std::setprecision(17)
           << "{\n  \"condition\": \"" << arguments.condition << "\",\n"
           << "  \"block_frames\": " << arguments.block_frames << ",\n"
           << "  \"frame_count\": " << kDurationFrames << ",\n"
           << "  \"peak_absolute\": " << signal.peak << ",\n"
           << "  \"rms_stereo\": " << std::sqrt(static_cast<double>(
                  signal.square_sum / (2.0L * frame_denominator))) << ",\n"
           << "  \"mean_left\": " << static_cast<double>(signal.left_sum / frame_denominator) << ",\n"
           << "  \"mean_right\": " << static_cast<double>(signal.right_sum / frame_denominator) << ",\n"
           << "  \"stereo_difference_energy\": "
           << static_cast<double>(signal.stereo_difference_sum) << ",\n"
           << "  \"non_finite_count\": " << signal.non_finite_count << ",\n"
           << "  \"decision_count\": " << decision_count << ",\n"
           << "  \"freeze_hold_delta\": " << freeze_hold_delta << ",\n"
           << "  \"body_mid_energy_over_bypass\": " << body_ratio << ",\n"
           << "  \"body_late_to_early_energy\": " << decay_ratio << ",\n"
           << "  \"capture_epoch\": " << snapshot.capture_epoch << ",\n"
           << "  \"capture_valid_frames\": " << snapshot.capture_valid_frames << ",\n"
           << "  \"history_count\": " << static_cast<unsigned>(snapshot.history_count) << ",\n"
           << "  \"active_voice_count\": " << static_cast<unsigned>(snapshot.active_voice_count) << ",\n"
           << "  \"diagnostic\": \"" << wb::diagnosticName(snapshot.latched_fault) << "\",\n"
           << "  \"decision_drop_count\": " << snapshot.diagnostics.decision_drop_count << ",\n"
           << "  \"invalid_read_count\": " << snapshot.diagnostics.invalid_read_count << ",\n"
           << "  \"voice_steal_count\": " << snapshot.diagnostics.voice_steal_count << ",\n"
           << "  \"voice_repair_count\": " << snapshot.diagnostics.voice_repair_count << ",\n"
           << "  \"body_repair_count\": " << snapshot.diagnostics.body_repair_count << ",\n"
           << "  \"final_fault_count\": " << snapshot.diagnostics.final_fault_count << ",\n"
           << "  \"non_finite_input_count\": " << snapshot.diagnostics.non_finite_input_count << ",\n"
           << "  \"freeze_count\": " << snapshot.diagnostics.freeze_count << ",\n"
           << "  \"clear_count\": " << snapshot.diagnostics.clear_count << ",\n"
           << "  \"reset_count\": " << snapshot.diagnostics.reset_count << ",\n"
           << "  \"panic_count\": " << snapshot.diagnostics.panic_count << "\n}\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const auto arguments = parseArguments(argc, argv);
        fs::create_directories(arguments.output);
        wb::Core core{};
        if (!core.prepare(kSampleRate, wb::kMaximumBlockFrames)) {
            throw std::runtime_error("Core preparation failed");
        }
        wb::Controls controls = wb::defaultControls();
        configureInitial(arguments.condition, controls, core);
        wb::ActionSequences actions{};

        wb::Core bypass{};
        wb::Controls bypass_controls = controls;
        const bool render_bypass = arguments.condition == "WB06_BODY";
        if (render_bypass && !bypass.prepare(kSampleRate, wb::kMaximumBlockFrames)) {
            throw std::runtime_error("bypass Core preparation failed");
        }

        std::vector<float> interleaved(static_cast<std::size_t>(kDurationFrames * 2U));
        std::vector<wb::DecisionEvent> decisions{};
        decisions.reserve(256U);
        std::array<float, wb::kMaximumBlockFrames> input_left{};
        std::array<float, wb::kMaximumBlockFrames> input_right{};
        std::array<float, wb::kMaximumBlockFrames> output_left{};
        std::array<float, wb::kMaximumBlockFrames> output_right{};
        std::array<float, wb::kMaximumBlockFrames> bypass_left{};
        std::array<float, wb::kMaximumBlockFrames> bypass_right{};
        SignalMetrics signal{};
        long double body_early_difference_energy{};
        long double body_late_difference_energy{};
        long double body_mid_energy{};
        long double bypass_mid_energy{};
        std::uint64_t freeze_write_start{};
        std::uint64_t freeze_hold_delta{};

        std::uint64_t frame{};
        while (frame < kDurationFrames) {
            if (arguments.condition == "WB07_FREEZE_CLEAR") {
                if (frame == 4ULL * kSampleRate) {
                    freeze_write_start = core.snapshot().capture_write_frame;
                } else if (frame == 6ULL * kSampleRate) {
                    freeze_hold_delta = core.snapshot().capture_write_frame - freeze_write_start;
                }
            }
            applyTimeline(arguments.condition, frame, controls, actions);
            bypass_controls = controls;
            bypass_controls.body = 0.0;
            const auto boundary = nextTimelineBoundary(arguments.condition, frame);
            auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(
                arguments.block_frames,
                kDurationFrames - frame));
            if (boundary != std::numeric_limits<std::uint64_t>::max()
                && frame + count > boundary) {
                count = static_cast<std::uint32_t>(boundary - frame);
            }
            if (count == 0U) throw std::logic_error("zero render chunk");
            for (std::uint32_t index = 0U; index < count; ++index) {
                input_left[index] = sourceSample(arguments.condition, frame + index);
                input_right[index] = input_left[index] * 0.91F;
            }
            const auto report = core.process(
                controls,
                actions,
                input_left.data(),
                input_right.data(),
                output_left.data(),
                output_right.data(),
                count);
            if (report.diagnostic != wb::DiagnosticCode::none) {
                throw std::runtime_error(
                    "Core rejected block: " + std::string(wb::diagnosticName(report.diagnostic)));
            }
            decisions.insert(
                decisions.end(),
                report.decisions.begin(),
                report.decisions.begin() + static_cast<std::ptrdiff_t>(report.decision_count));

            if (render_bypass) {
                const auto bypass_report = bypass.process(
                    bypass_controls,
                    actions,
                    input_left.data(),
                    input_right.data(),
                    bypass_left.data(),
                    bypass_right.data(),
                    count);
                if (bypass_report.diagnostic != wb::DiagnosticCode::none) {
                    throw std::runtime_error("bypass Core rejected block");
                }
            }
            for (std::uint32_t index = 0U; index < count; ++index) {
                const auto absolute = frame + index;
                const auto output_index = static_cast<std::size_t>(absolute * 2U);
                interleaved[output_index] = output_left[index];
                interleaved[output_index + 1U] = output_right[index];
                signal.add(output_left[index], output_right[index]);
                if (render_bypass) {
                    const long double actual_energy =
                        static_cast<long double>(output_left[index]) * output_left[index]
                        + static_cast<long double>(output_right[index]) * output_right[index];
                    const long double reference_energy =
                        static_cast<long double>(bypass_left[index]) * bypass_left[index]
                        + static_cast<long double>(bypass_right[index]) * bypass_right[index];
                    const long double dl = static_cast<long double>(output_left[index]) - bypass_left[index];
                    const long double dr = static_cast<long double>(output_right[index]) - bypass_right[index];
                    const auto difference_energy = dl * dl + dr * dr;
                    if (absolute >= 9ULL * kSampleRate / 4ULL
                        && absolute < 4ULL * kSampleRate) {
                        body_early_difference_energy += difference_energy;
                        body_mid_energy += actual_energy;
                        bypass_mid_energy += reference_energy;
                    }
                    if (absolute >= 8ULL * kSampleRate) {
                        body_late_difference_energy += difference_energy;
                    }
                }
            }
            frame += count;
        }

        const auto snapshot = core.snapshot();
        writeWav(arguments.output / "audio.wav", interleaved);
        writeDecisions(arguments.output / "decisions.json", arguments.condition, decisions);
        writeMetrics(
            arguments.output / "metrics.json",
            arguments,
            signal,
            snapshot,
            decisions.size(),
            freeze_hold_delta,
            body_early_difference_energy,
            body_late_difference_energy,
            body_mid_energy,
            bypass_mid_energy);
        std::cout << arguments.condition << " rendered " << kDurationFrames
                  << " frames at block " << arguments.block_frames << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
