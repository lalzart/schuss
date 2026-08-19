#include "schuss_rt/runtime.hpp"
#include "schuss_rt/runtime_v1.hpp"

#include "schuss_rt/sha256.hpp"

#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

struct Options {
    std::string package_path;
    std::string package_hash;
    std::string output_path;
    std::string observation_path;
    std::uint32_t frames{48000};
    std::uint32_t block_frames{128};
};

std::uint32_t number(std::string_view value, const char* name) {
    std::uint64_t parsed = 0;
    if (value.empty()) throw std::runtime_error(std::string("HOST_ARGUMENT_INVALID: ") + name);
    for (const char character : value) {
        if (character < '0' || character > '9') throw std::runtime_error(std::string("HOST_ARGUMENT_INVALID: ") + name);
        parsed = parsed * 10U + static_cast<unsigned>(character - '0');
        if (parsed > std::numeric_limits<std::uint32_t>::max()) throw std::runtime_error(std::string("HOST_ARGUMENT_INVALID: ") + name);
    }
    return static_cast<std::uint32_t>(parsed);
}

Options options(int argc, char** argv) {
    Options result;
    std::map<std::string, std::string*> strings{
        {"--package", &result.package_path}, {"--package-hash", &result.package_hash},
        {"--output", &result.output_path}, {"--observation", &result.observation_path},
    };
    for (int index = 1; index < argc; ++index) {
        const std::string key = argv[index];
        if (index + 1 >= argc) throw std::runtime_error("HOST_ARGUMENT_MISSING_VALUE: " + key);
        const std::string value = argv[++index];
        const auto text = strings.find(key);
        if (text != strings.end()) {
            *text->second = value;
        } else if (key == "--frames") {
            result.frames = number(value, "frames");
        } else if (key == "--block") {
            result.block_frames = number(value, "block");
        } else {
            throw std::runtime_error("HOST_ARGUMENT_UNKNOWN: " + key);
        }
    }
    if (result.package_path.empty() || result.package_hash.empty() || result.output_path.empty() || result.observation_path.empty()) {
        throw std::runtime_error("HOST_ARGUMENT_REQUIRED");
    }
    if (result.frames == 0 || result.frames > 480000 || result.block_frames == 0 || result.block_frames > 512) {
        throw std::runtime_error("HOST_RENDER_BOUNDS_INVALID");
    }
    return result;
}

std::string read_text(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("HOST_PACKAGE_READ_FAILED");
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

void append_u16(std::vector<std::uint8_t>& output, std::uint16_t value) {
    output.push_back(static_cast<std::uint8_t>(value));
    output.push_back(static_cast<std::uint8_t>(value >> 8U));
}

void append_u32(std::vector<std::uint8_t>& output, std::uint32_t value) {
    output.push_back(static_cast<std::uint8_t>(value));
    output.push_back(static_cast<std::uint8_t>(value >> 8U));
    output.push_back(static_cast<std::uint8_t>(value >> 16U));
    output.push_back(static_cast<std::uint8_t>(value >> 24U));
}

void append_ascii(std::vector<std::uint8_t>& output, std::string_view value) {
    output.insert(output.end(), value.begin(), value.end());
}

std::int16_t pcm16(std::int32_t value) {
    constexpr std::int32_t q27 = 1 << 27;
    value = std::clamp(value, -q27, q27 - 1);
    const std::int32_t scaled = value / (1 << 12);
    return static_cast<std::int16_t>(std::clamp(scaled, -32768, 32767));
}

std::vector<std::uint8_t> wav_bytes(const std::vector<std::int32_t>& samples, std::uint32_t frames) {
    const std::uint32_t data_size = frames * 2U * sizeof(std::int16_t);
    std::vector<std::uint8_t> output;
    output.reserve(44U + data_size);
    append_ascii(output, "RIFF"); append_u32(output, 36U + data_size); append_ascii(output, "WAVE");
    append_ascii(output, "fmt "); append_u32(output, 16U); append_u16(output, 1U); append_u16(output, 2U);
    append_u32(output, 48000U); append_u32(output, 48000U * 2U * sizeof(std::int16_t));
    append_u16(output, 2U * sizeof(std::int16_t)); append_u16(output, 16U);
    append_ascii(output, "data"); append_u32(output, data_size);
    for (const auto value : samples) append_u16(output, static_cast<std::uint16_t>(pcm16(value)));
    return output;
}

void write_bytes(const std::string& path, const std::vector<std::uint8_t>& bytes) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream || !stream.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()))) {
        throw std::runtime_error("HOST_OUTPUT_WRITE_FAILED");
    }
}

void write_text(const std::string& path, const std::string& value) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream || !stream.write(value.data(), static_cast<std::streamsize>(value.size()))) {
        throw std::runtime_error("HOST_OBSERVATION_WRITE_FAILED");
    }
}

std::string escaped(std::string_view value) {
    std::string output;
    for (const unsigned char character : value) {
        switch (character) {
            case '"': output += "\\\""; break;
            case '\\': output += "\\\\"; break;
            case '\n': output += "\\n"; break;
            case '\r': output += "\\r"; break;
            case '\t': output += "\\t"; break;
            default:
                if (character < 0x20U) throw std::runtime_error("HOST_TOOLCHAIN_STRING_INVALID");
                output.push_back(static_cast<char>(character));
        }
    }
    return output;
}

std::string compiler_id() {
#if defined(__clang__)
    return "AppleClang";
#elif defined(__GNUC__)
    return "GNU";
#else
    return "unknown-cpp17";
#endif
}

std::string compiler_version() {
#if defined(__clang__)
    return __clang_version__;
#elif defined(__VERSION__)
    return __VERSION__;
#else
    return "unknown";
#endif
}

std::string target_triple() {
#if defined(__APPLE__) && defined(__aarch64__)
    return "arm64-apple-darwin";
#elif defined(__APPLE__) && defined(__x86_64__)
    return "x86_64-apple-darwin";
#elif defined(__linux__) && defined(__x86_64__)
    return "x86_64-linux-gnu";
#else
    return "unknown-portable-host";
#endif
}

std::string observation_without_hash(
    const Options& option,
    const schuss::rt::Metrics& metrics,
    std::size_t wav_size,
    const std::string& wav_hash
) {
    return "{\"canonical_profile\":\"schuss-canonical-json-v1\","
        "\"configuration\":{\"block_frames\":" + std::to_string(option.block_frames)
        + ",\"output_channels\":2,\"render_frames\":" + std::to_string(option.frames)
        + ",\"sample_rate_hz\":48000},"
        "\"device\":{\"status\":\"not-opened\"},"
        "\"diagnostics\":[],"
        "\"evidence_boundary\":{\"audible_level_8_promoted\":false,\"host_execution_only\":true,"
        "\"ksoloti_equivalence_claimed\":false,\"real_time_level_7_promoted\":false,\"release_readiness_claimed\":false},"
        "\"metrics\":{\"callback_cpu_ratio_max\":\"0.000000\",\"callback_duration_us_max\":0,"
        "\"midi_events_delivered\":" + std::to_string(metrics.events_delivered)
        + ",\"processed_frames\":" + std::to_string(metrics.processed_frames)
        + ",\"queue_overflows\":" + std::to_string(metrics.queue_overflows) + ",\"xruns\":0},"
        "\"observation_kind\":\"offline-render\","
        "\"output\":{\"byte_length\":" + std::to_string(wav_size) + ",\"byte_sha256\":\"" + wav_hash
        + "\",\"media_type\":\"audio/wav\"},"
        "\"package_content_hash\":\"" + option.package_hash + "\","
        "\"schema_version\":\"host-runtime-observation-v0\",\"status\":\"success\","
        "\"toolchain\":{\"compiler_id\":\"" + escaped(compiler_id()) + "\",\"compiler_version\":\""
        + escaped(compiler_version()) + "\",\"runtime_abi\":\"schuss-rt-abi-v0\",\"target_triple\":\""
        + escaped(target_triple()) + "\"}}";
}

std::string graph_execution(
    const schuss::rt::v1::PreparedPackage& package
) {
    std::map<std::string, std::size_t> counts;
    for (const auto& node : package.nodes) ++counts[node.factory_id];
    std::vector<std::string> encoded_instances;
    for (const auto& item : counts) {
        encoded_instances.push_back(
            "{\"count\":" + std::to_string(item.second)
            + ",\"factory_id\":\"" + escaped(item.first) + "\"}"
        );
    }
    std::sort(encoded_instances.begin(), encoded_instances.end());
    std::string instances;
    for (const auto& value : encoded_instances) {
        if (!instances.empty()) instances.push_back(',');
        instances += value;
    }
    return "{\"buffer_count\":" + std::to_string(package.buffer_count)
        + ",\"connection_count\":" + std::to_string(package.connection_count)
        + ",\"factory_instance_counts\":[" + instances + "]"
        + ",\"node_count\":" + std::to_string(package.nodes.size())
        + ",\"schedule_length\":" + std::to_string(package.schedule.size())
        + ",\"state_bytes\":" + std::to_string(package.state_bytes) + "}";
}

std::string observation_v1_without_hash(
    const Options& option,
    const schuss::rt::Metrics& metrics,
    const std::string& graph_facts,
    std::size_t wav_size,
    const std::string& wav_hash
) {
    return "{\"canonical_profile\":\"schuss-canonical-json-v1\","
        "\"configuration\":{\"block_frames\":" + std::to_string(option.block_frames)
        + ",\"output_channels\":2,\"render_frames\":" + std::to_string(option.frames)
        + ",\"sample_rate_hz\":48000},"
        "\"device\":{\"status\":\"not-opened\"},"
        "\"diagnostics\":[],"
        "\"evidence_boundary\":{\"audible_level_8_promoted\":false,\"host_execution_only\":true,"
        "\"ksoloti_equivalence_claimed\":false,\"real_time_level_7_promoted\":false,\"release_readiness_claimed\":false},"
        "\"graph_execution\":" + graph_facts + ","
        "\"metrics\":{\"callback_cpu_ratio_max\":\"0.000000\",\"callback_duration_us_max\":0,"
        "\"midi_events_delivered\":" + std::to_string(metrics.events_delivered)
        + ",\"processed_frames\":" + std::to_string(metrics.processed_frames)
        + ",\"queue_overflows\":" + std::to_string(metrics.queue_overflows) + ",\"xruns\":0},"
        "\"observation_kind\":\"offline-render\","
        "\"output\":{\"byte_length\":" + std::to_string(wav_size) + ",\"byte_sha256\":\"" + wav_hash
        + "\",\"media_type\":\"audio/wav\"},"
        "\"package_content_hash\":\"" + option.package_hash + "\","
        "\"schema_version\":\"host-runtime-observation-v1\",\"status\":\"success\","
        "\"toolchain\":{\"compiler_id\":\"" + escaped(compiler_id()) + "\",\"compiler_version\":\""
        + escaped(compiler_version()) + "\",\"runtime_abi\":\"schuss-rt-abi-v1\",\"target_triple\":\""
        + escaped(target_triple()) + "\"}}";
}

std::string with_content_hash(const std::string& without_hash) {
    const std::string marker = "\"device\"";
    const auto position = without_hash.find(marker);
    if (position == std::string::npos) throw std::runtime_error("HOST_OBSERVATION_INTERNAL_INVALID");
    return without_hash.substr(0, position)
        + "\"content_hash\":\"sha256:" + schuss::rt::sha256_hex(without_hash) + "\","
        + without_hash.substr(position);
}

template <typename RuntimeType>
std::vector<std::int32_t> render_samples(
    RuntimeType& runtime, const Options& option
) {
    std::vector<std::int32_t> samples(static_cast<std::size_t>(option.frames) * 2U);
    std::vector<std::int32_t> left(option.block_frames), right(option.block_frames);
    std::uint32_t cursor = 0;
    while (cursor < option.frames) {
        const auto count = std::min(option.block_frames, option.frames - cursor);
        const auto processed = runtime.process(left.data(), right.data(), count);
        if (!processed) throw std::runtime_error(processed.diagnostic);
        for (std::uint32_t frame = 0; frame < count; ++frame) {
            samples[static_cast<std::size_t>(cursor + frame) * 2U] = left[frame];
            samples[static_cast<std::size_t>(cursor + frame) * 2U + 1U] = right[frame];
        }
        cursor += count;
    }
    return samples;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Options option = options(argc, argv);
        const std::string package_json = read_text(option.package_path);
        std::vector<std::int32_t> samples;
        schuss::rt::Metrics metrics;
        std::string graph_facts;
        const bool variable = package_json.find(
            "\"schema_version\":\"host-runtime-package-v1\""
        ) != std::string::npos;
        if (variable) {
            schuss::rt::v1::PreparedPackage package;
            const auto parsed = schuss::rt::v1::parse_package(
                package_json, option.package_hash, package
            );
            if (!parsed) throw std::runtime_error(parsed.diagnostic);
            schuss::rt::v1::Runtime runtime;
            const auto prepared = runtime.prepare(package);
            if (!prepared) throw std::runtime_error(prepared.diagnostic);
            samples = render_samples(runtime, option);
            metrics = runtime.metrics();
            graph_facts = graph_execution(package);
        } else {
            schuss::rt::PreparedPackage package;
            const auto parsed = schuss::rt::parse_package(
                package_json, option.package_hash, package
            );
            if (!parsed) throw std::runtime_error(parsed.diagnostic);
            schuss::rt::Runtime runtime;
            const auto prepared = runtime.prepare(package);
            if (!prepared) throw std::runtime_error(prepared.diagnostic);
            samples = render_samples(runtime, option);
            metrics = runtime.metrics();
        }
        const auto wav = wav_bytes(samples, option.frames);
        const std::string wav_hash = schuss::rt::sha256_hex(wav);
        write_bytes(option.output_path, wav);
        std::string observation_body;
        if (variable) {
            observation_body = observation_v1_without_hash(
                option, metrics, graph_facts, wav.size(), wav_hash
            );
        } else {
            observation_body = observation_without_hash(
                option, metrics, wav.size(), wav_hash
            );
        }
        const std::string observation = with_content_hash(observation_body) + "\n";
        write_text(option.observation_path, observation);
        std::cout << "HOST_RENDER_SUCCESS " << wav_hash << " " << option.frames << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
