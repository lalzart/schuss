#include "schuss/generative_drum_machine/core.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <new>
#include <vector>

namespace {

thread_local bool track_allocations = false;
thread_local std::uint64_t tracked_allocation_count = 0U;

}  // namespace

void* operator new(std::size_t size) {
    if (track_allocations) ++tracked_allocation_count;
    if (void* memory = std::malloc(size == 0U ? 1U : size)) return memory;
    throw std::bad_alloc{};
}

void* operator new[](std::size_t size) {
    return ::operator new(size);
}

void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

namespace {

namespace gdm = schuss::generative_drum_machine;
using Clock = std::chrono::steady_clock;

struct Measurement final {
    std::size_t block_frames{};
    std::uint32_t iterations{};
    std::uint64_t median_ns{};
    std::uint64_t p99_ns{};
    std::uint64_t maximum_ns{};
    std::uint64_t deadline_ns{};
    std::uint64_t maximum_deadline_ratio_ppm{};
    std::uint64_t allocation_count{};
    std::uint64_t process_failure_count{};
};

Measurement measure(std::size_t block_frames, std::uint32_t iterations) {
    gdm::Controls controls{};
    controls.complexity.fill(65535U);
    controls.enthusiasm = 65535U;
    controls.tempo_milli_bpm = 240000U;
    controls.rhythm_preset = 7U;
    gdm::StreamingEngine engine{0x53434855U};
    std::array<std::int32_t, gdm::kMaximumStreamingBlockFrames> left{};
    std::array<std::int32_t, gdm::kMaximumStreamingBlockFrames> right{};
    std::uint64_t fill_sequence = 0U;
    for (std::uint32_t index = 0U; index < 256U; ++index) {
        if ((index % 64U) == 0U) ++fill_sequence;
        static_cast<void>(engine.process(
            controls, fill_sequence, left.data(), right.data(), block_frames));
    }

    std::vector<std::uint64_t> durations;
    durations.reserve(iterations);
    tracked_allocation_count = 0U;
    std::uint64_t failures = 0U;
    for (std::uint32_t index = 0U; index < iterations; ++index) {
        auto& shape = controls.voice_shapes[index % gdm::kLogicalLaneCount];
        shape.tune_u7 = static_cast<std::uint8_t>((index * 17U) & 0x7fU);
        shape.timbre_u7 = static_cast<std::uint8_t>((index * 29U) & 0x7fU);
        shape.color_u7 = static_cast<std::uint8_t>((index * 43U) & 0x7fU);
        shape.decay_u7 = static_cast<std::uint8_t>((index * 11U) & 0x7fU);
        shape.pitch_env_u7 = static_cast<std::uint8_t>((index * 31U) & 0x7fU);
        shape.level_u7 = static_cast<std::uint8_t>(32U + ((index * 7U) % 96U));
        if ((index % 64U) == 0U) ++fill_sequence;
        const auto start = Clock::now();
        track_allocations = true;
        const auto ok = engine.process(
            controls, fill_sequence, left.data(), right.data(), block_frames);
        track_allocations = false;
        const auto end = Clock::now();
        failures += ok ? 0U : 1U;
        durations.push_back(static_cast<std::uint64_t>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count()));
    }
    std::sort(durations.begin(), durations.end());
    const auto percentile_index = [](std::size_t size, std::uint32_t numerator) {
        return std::min<std::size_t>(
            size - 1U,
            (size * numerator + 99U) / 100U - 1U);
    };
    Measurement result{};
    result.block_frames = block_frames;
    result.iterations = iterations;
    result.median_ns = durations[percentile_index(durations.size(), 50U)];
    result.p99_ns = durations[percentile_index(durations.size(), 99U)];
    result.maximum_ns = durations.back();
    result.deadline_ns = static_cast<std::uint64_t>(block_frames) * 1000000000ULL
        / gdm::kSampleRateHz;
    result.maximum_deadline_ratio_ppm = result.deadline_ns == 0U
        ? 0U
        : result.maximum_ns * 1000000ULL / result.deadline_ns;
    result.allocation_count = tracked_allocation_count;
    result.process_failure_count = failures;
    return result;
}

const char* compilerName() noexcept {
#if defined(__apple_build_version__)
    return "AppleClang";
#elif defined(__clang__)
    return "Clang";
#elif defined(__GNUC__)
    return "GNU";
#else
    return "unknown";
#endif
}

}  // namespace

int main() {
    constexpr std::array<std::size_t, 3> block_sizes{{64U, 128U, 512U}};
    constexpr std::uint32_t iterations = 2000U;
    std::array<Measurement, block_sizes.size()> results{};
    bool passed = true;
    for (std::size_t index = 0U; index < block_sizes.size(); ++index) {
        results[index] = measure(block_sizes[index], iterations);
        passed = passed
            && results[index].allocation_count == 0U
            && results[index].process_failure_count == 0U;
    }
    std::cout << "{\n"
              << "  \"claim_boundary\": \"synthetic callback-kernel measurement; not live-device realtime evidence\",\n"
              << "  \"compiler\": \"" << compilerName() << "\",\n"
              << "  \"measurements\": [\n";
    for (std::size_t index = 0U; index < results.size(); ++index) {
        const auto& value = results[index];
        std::cout << "    {\"allocation_count\": " << value.allocation_count
                  << ", \"block_frames\": " << value.block_frames
                  << ", \"deadline_ns\": " << value.deadline_ns
                  << ", \"iterations\": " << value.iterations
                  << ", \"maximum_deadline_ratio_ppm\": "
                  << value.maximum_deadline_ratio_ppm
                  << ", \"maximum_ns\": " << value.maximum_ns
                  << ", \"median_ns\": " << value.median_ns
                  << ", \"p99_ns\": " << value.p99_ns
                  << ", \"process_failure_count\": "
                  << value.process_failure_count << "}"
                  << (index + 1U == results.size() ? "\n" : ",\n");
    }
    std::cout << "  ],\n"
              << "  \"passed\": " << (passed ? "true" : "false") << ",\n"
              << "  \"sample_rate_hz\": " << gdm::kSampleRateHz << ",\n"
              << "  \"schema_version\": \"schuss-gdm-synthetic-callback-benchmark-v1\"\n"
              << "}\n";
    return passed ? 0 : 1;
}
