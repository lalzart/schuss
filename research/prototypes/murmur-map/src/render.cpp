#include "schuss/murmur_map/core.hpp"

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

namespace mm = schuss::murmur_map;
namespace fs = std::filesystem;

namespace {

struct Arguments final {
    std::string condition;
    std::size_t block_frames{128U};
    fs::path output;
    std::uint64_t duration_override{};
};

[[nodiscard]] Arguments parse(int argc, char** argv) {
    Arguments result{};
    for (int index = 1; index < argc; ++index) {
        const std::string_view arg{argv[index]};
        if (arg == "--condition" && index + 1 < argc) result.condition = argv[++index];
        else if (arg == "--block" && index + 1 < argc) result.block_frames = std::stoul(argv[++index]);
        else if (arg == "--output" && index + 1 < argc) result.output = argv[++index];
        else if (arg == "--duration-frames" && index + 1 < argc) result.duration_override = std::stoull(argv[++index]);
        else throw std::invalid_argument("unknown or incomplete argument: " + std::string(arg));
    }
    if (result.condition.empty() || result.output.empty()
        || result.block_frames == 0U || result.block_frames > mm::kMaximumBlockFrames) {
        throw std::invalid_argument(
            "usage: murmur-map-render --condition MM01_LOCKED --block 128 --output DIRECTORY [--duration-frames N]");
    }
    return result;
}

[[nodiscard]] std::uint64_t conditionFrames(std::string_view condition) {
    if (condition == "MM02_SLOW_EROSION" || condition == "MM10_WHITE_SCENE") {
        return mm::kSampleRateHz * 120ULL;
    }
    if (condition == "MM08_EXTREMES") return mm::kSampleRateHz * 48ULL;
    if (condition == "MM09_EXACT_SILENCE") return mm::kSampleRateHz * 24ULL;
    if (condition == "MM01_LOCKED" || condition == "MM03_FRESH"
        || condition == "MM04_HOME_PULL" || condition == "MM05_MOVE_WAYPOINT"
        || condition == "MM06_CAPTURE_REPLACE" || condition == "MM07_RESEED") {
        return mm::kSampleRateHz * 96ULL;
    }
    throw std::invalid_argument("unknown condition ID");
}

void configureInitial(std::string_view condition, mm::Controls& controls, mm::Core& core) {
    if (condition == "MM01_LOCKED" || condition == "MM03_FRESH"
        || condition == "MM05_MOVE_WAYPOINT") controls.memory_u15 = 0U;
    if (condition == "MM02_SLOW_EROSION") controls.memory_u15 = 30146U;
    if (condition == "MM04_HOME_PULL") controls.home_u15 = 0U;
    if (condition == "MM08_EXTREMES") {
        controls.tempo_milli_bpm = 240000U;
        controls.density_u15 = 32767U;
        controls.travel_milli_quarters = 250U;
        controls.radius_u15 = 0U;
        controls.memory_length = 32U;
        controls.roam_u15 = 32767U;
        controls.home_u15 = 32767U;
    }
    if (condition == "MM09_EXACT_SILENCE") {
        controls.density_u15 = 0U;
        for (std::size_t waypoint = 0U; waypoint < controls.waypoint_count; ++waypoint) {
            for (auto& lane : controls.waypoints[waypoint].lanes) lane.activity_u15 = 0U;
        }
    }
    if (condition == "MM10_WHITE_SCENE") {
        controls.memory_u15 = 30146U;
        core.setGenerationMode(mm::GenerationMode::independent_white_scene);
    }
}

void applyTimeline(
    std::string_view condition,
    std::uint64_t frame,
    mm::Controls& controls,
    mm::ActionSequences& actions) {
    if ((condition == "MM01_LOCKED" || condition == "MM05_MOVE_WAYPOINT")
        && frame == mm::kSampleRateHz * 24ULL) {
        controls.memory_u15 = 32767U;
    }
    if (condition == "MM04_HOME_PULL" && frame == mm::kSampleRateHz * 32ULL) {
        controls.home_u15 = 27852U;
    }
    if (condition == "MM05_MOVE_WAYPOINT" && frame == mm::kSampleRateHz * 32ULL) {
        controls.waypoints[2].x_u15 = 17039U;
        controls.waypoints[2].y_u15 = 21626U;
    }
    if (condition == "MM06_CAPTURE_REPLACE" && frame == mm::kSampleRateHz * 32ULL) {
        auto& lane = controls.waypoints[1].lanes[1];
        lane.activity_u15 = 28500U;
        lane.timbre_u15 = 12000U;
        lane.color_u15 = 30000U;
        lane.decay_ms = 760U;
        lane.level_milli_db = -14000;
        lane.pan_s15 = -12000;
    }
    if (condition == "MM07_RESEED" && frame == mm::kSampleRateHz * 32ULL) {
        actions.reseed_value = 0x5245534545443031ULL;
        ++actions.reseed;
    }
    if (condition == "MM08_EXTREMES" && frame > 0U && frame % 4096U == 0U) {
        const auto epoch = frame / 4096U;
        controls.roam_u15 = (epoch & 1U) == 0U ? 0U : 32767U;
        controls.home_u15 = (epoch % 3U) == 0U ? 0U : 32767U;
        controls.density_u15 = (epoch % 5U) == 0U ? 16384U : 32767U;
        controls.radius_u15 = (epoch % 7U) == 0U ? 32767U : 0U;
    }
}

[[nodiscard]] std::uint64_t nextTimelineBoundary(std::string_view condition, std::uint64_t frame) {
    std::uint64_t boundary = std::numeric_limits<std::uint64_t>::max();
    const auto consider = [&](std::uint64_t candidate) {
        if (candidate > frame) boundary = std::min(boundary, candidate);
    };
    if (condition == "MM01_LOCKED" || condition == "MM05_MOVE_WAYPOINT") {
        consider(mm::kSampleRateHz * 24ULL);
    }
    if (condition == "MM04_HOME_PULL" || condition == "MM05_MOVE_WAYPOINT"
        || condition == "MM06_CAPTURE_REPLACE" || condition == "MM07_RESEED") {
        consider(mm::kSampleRateHz * 32ULL);
    }
    if (condition == "MM08_EXTREMES") consider(((frame / 4096U) + 1U) * 4096U);
    return boundary;
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
    stream.write("RIFF", 4); writeU32(stream, 36U + data_size); stream.write("WAVE", 4);
    stream.write("fmt ", 4); writeU32(stream, 16U); writeU16(stream, 1U); writeU16(stream, 2U);
    writeU32(stream, mm::kSampleRateHz); writeU32(stream, mm::kSampleRateHz * 6U);
    writeU16(stream, 6U); writeU16(stream, 24U);
    stream.write("data", 4); writeU32(stream, data_size);
    for (const auto sample : interleaved) {
        const auto integer = static_cast<std::int32_t>(std::clamp<long>(
            std::lround(std::clamp(sample, -1.0F, 1.0F) * 8388607.0F),
            -8388608L, 8388607L));
        stream.put(static_cast<char>(integer & 0xff));
        stream.put(static_cast<char>((integer >> 8) & 0xff));
        stream.put(static_cast<char>((integer >> 16) & 0xff));
    }
}

template <typename Value>
void writeBoolean(std::ostream& stream, Value value) { stream << (value ? "true" : "false"); }

}  // namespace

int main(int argc, char** argv) {
    try {
        const auto args = parse(argc, argv);
        const auto total_frames = args.duration_override == 0U
            ? conditionFrames(args.condition) : args.duration_override;
        fs::create_directories(args.output);

        mm::Controls controls = mm::defaultControls();
        mm::Core core{};
        configureInitial(args.condition, controls, core);
        mm::ActionSequences actions{};
        actions.reset = 1U;
        if (args.condition == "MM09_EXACT_SILENCE") actions.panic = 1U;

        std::vector<float> interleaved;
        interleaved.resize(static_cast<std::size_t>(total_frames * 2U));
        std::vector<mm::RouteTraceEvent> routes;
        std::vector<mm::MusicalEvent> events;
        std::array<float, mm::kMaximumBlockFrames> left{};
        std::array<float, mm::kMaximumBlockFrames> right{};
        double sum_left = 0.0;
        double sum_right = 0.0;
        long double sum_squares = 0.0;
        float peak = 0.0F;
        std::uint64_t non_finite = 0U;
        std::uint64_t frame = 0U;
        while (frame < total_frames) {
            applyTimeline(args.condition, frame, controls, actions);
            const auto next_boundary = nextTimelineBoundary(args.condition, frame);
            auto count = static_cast<std::size_t>(std::min<std::uint64_t>(
                args.block_frames, total_frames - frame));
            if (next_boundary != std::numeric_limits<std::uint64_t>::max()
                && frame + count > next_boundary) {
                count = static_cast<std::size_t>(next_boundary - frame);
            }
            if (count == 0U) throw std::logic_error("zero render chunk");
            mm::ProcessReport report{};
            if (!core.process(controls, actions, left.data(), right.data(), count, &report)) {
                throw std::runtime_error("Core rejected condition block");
            }
            routes.insert(routes.end(), report.route_events.begin(),
                report.route_events.begin() + static_cast<std::ptrdiff_t>(report.route_event_count));
            events.insert(events.end(), report.musical_events.begin(),
                report.musical_events.begin() + static_cast<std::ptrdiff_t>(report.musical_event_count));
            for (std::size_t index = 0U; index < count; ++index) {
                const auto output_index = static_cast<std::size_t>((frame + index) * 2U);
                interleaved[output_index] = left[index];
                interleaved[output_index + 1U] = right[index];
                if (!std::isfinite(left[index]) || !std::isfinite(right[index])) ++non_finite;
                peak = std::max(peak, std::max(std::abs(left[index]), std::abs(right[index])));
                sum_left += left[index];
                sum_right += right[index];
                sum_squares += static_cast<long double>(left[index]) * left[index]
                    + static_cast<long double>(right[index]) * right[index];
            }
            frame += count;
        }
        const auto snapshot = core.snapshot();
        writeWav(args.output / "condition-stereo.wav", interleaved);

        {
            std::ofstream stream(args.output / "condition-route.json");
            stream << "{\n  \"condition\": \"" << args.condition << "\",\n  \"events\": [\n";
            for (std::size_t index = 0U; index < routes.size(); ++index) {
                const auto& event = routes[index];
                stream << "    {\"frame\":" << event.absolute_frame
                       << ",\"from\":" << event.from_id << ",\"to\":" << event.to_id
                       << ",\"slot\":" << static_cast<unsigned>(event.memory_slot)
                       << ",\"replayed\":"; writeBoolean(stream, event.replayed);
                stream << ",\"replaced\":"; writeBoolean(stream, event.replaced);
                stream << ",\"dwell\":"; writeBoolean(stream, event.dwell);
                stream << '}' << (index + 1U == routes.size() ? "\n" : ",\n");
            }
            stream << "  ]\n}\n";
        }
        {
            std::ofstream stream(args.output / "condition-events.json");
            stream << "{\n  \"condition\": \"" << args.condition << "\",\n  \"events\": [\n";
            for (std::size_t index = 0U; index < events.size(); ++index) {
                const auto& event = events[index];
                stream << "    {\"frame\":" << event.absolute_frame
                       << ",\"lane\":" << static_cast<unsigned>(event.lane)
                       << ",\"waypoint\":" << event.pitch_waypoint_id
                       << ",\"pitch\":" << static_cast<unsigned>(event.pitch_midi)
                       << ",\"timbre\":" << event.timbre_u15
                       << ",\"color\":" << event.color_u15
                       << ",\"decay_ms\":" << event.decay_ms
                       << ",\"level_milli_db\":" << event.level_milli_db
                       << ",\"pan\":" << event.pan_s15 << '}'
                       << (index + 1U == events.size() ? "\n" : ",\n");
            }
            stream << "  ]\n}\n";
        }
        {
            const double frame_denominator = total_frames == 0U ? 1.0 : static_cast<double>(total_frames);
            std::ofstream stream(args.output / "condition-metrics.json");
            stream << std::setprecision(12)
                   << "{\n  \"condition\": \"" << args.condition << "\",\n"
                   << "  \"block_frames\": " << args.block_frames << ",\n"
                   << "  \"frame_count\": " << total_frames << ",\n"
                   << "  \"peak_absolute\": " << peak << ",\n"
                   << "  \"rms_stereo\": " << std::sqrt(static_cast<double>(sum_squares)
                        / (2.0 * frame_denominator)) << ",\n"
                   << "  \"mean_left\": " << sum_left / frame_denominator << ",\n"
                   << "  \"mean_right\": " << sum_right / frame_denominator << ",\n"
                   << "  \"non_finite_count\": " << non_finite << ",\n"
                   << "  \"route_event_count\": " << routes.size() << ",\n"
                   << "  \"musical_event_count\": " << events.size() << ",\n"
                   << "  \"dropped_event_count\": " << snapshot.dropped_event_count << ",\n"
                   << "  \"repair_count\": " << snapshot.repair_count << ",\n"
                   << "  \"clamp_count\": " << snapshot.clamp_count << "\n}\n";
        }
        std::cout << args.condition << " rendered " << total_frames
                  << " frames at block " << args.block_frames << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
