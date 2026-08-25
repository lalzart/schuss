#include "schuss/instrument_lab/bounded_midi.hpp"
#include "schuss/instrument_lab/fixed_rate_resampler.hpp"
#include "schuss/instrument_lab/host_bridge.hpp"
#include "schuss/instrument_lab/renderer_artifacts.hpp"
#include "schuss/instrument_lab/ui_projection.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <memory>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int failures = 0;

#define CHECK(condition)                                                       \
    do {                                                                       \
        if (!(condition)) {                                                    \
            std::cerr << __FILE__ << ':' << __LINE__                           \
                      << ": check failed: " #condition "\n";                  \
            ++failures;                                                        \
        }                                                                      \
    } while (false)

struct FloatAdapter {
    static constexpr schuss::instrument_lab::HostProfile profile() noexcept {
        return {
            schuss::instrument_lab::SampleRepresentation::float32,
            48000.0,
            512,
            0,
            false,
            true,
        };
    }

    void reset() noexcept {
        processed = 0;
        resets += 1;
    }

    bool process(float* left, float* right, std::uint32_t frames) noexcept {
        if (left == nullptr || right == nullptr || frames > 512) return false;
        for (std::uint32_t index = 0; index < frames; ++index) {
            left[index] = static_cast<float>(processed + index);
            right[index] = -left[index];
        }
        processed += frames;
        return true;
    }

    std::uint64_t processed{};
    std::uint64_t resets{};
};

struct Q27Adapter {
    static constexpr schuss::instrument_lab::HostProfile profile() noexcept {
        return {
            schuss::instrument_lab::SampleRepresentation::q27,
            48000.0,
            512,
            16,
            true,
            true,
        };
    }

    void reset() noexcept {
        carried = 0;
        dropped = 0;
        resets += 1;
    }

    void process(const std::uint32_t* events, std::size_t count) noexcept {
        if (events == nullptr && count != 0) {
            dropped += count;
            return;
        }
        for (std::size_t index = 0; index < count; ++index) {
            carried += events[index];
        }
    }

    std::uint64_t carried{};
    std::uint64_t dropped{};
    std::uint64_t resets{};
};

void testBoundedMidi() {
    using namespace schuss::instrument_lab;
    IngressSequence sequence;
    CHECK(sequence.next() == 1);
    CHECK(sequence.next() == 2);
    sequence.reset();
    CHECK(sequence.next() == 1);
    CHECK(clampSampleOffset(-5, 16) == 0);
    CHECK(clampSampleOffset(20, 16) == 15);
    CHECK(clampSampleOffset(20, 0) == 0);

    const std::array<std::uint8_t, 4> bytes{{0xbf, 20, 127, 99}};
    const auto raw = makeRawMidiEnvelope(bytes.data(), 4, 20, 16, 7);
    const std::array<std::uint8_t, 3> expected_bytes{{0xbf, 20, 127}};
    CHECK(raw.sample_offset == 15);
    CHECK(raw.ingress_sequence == 7);
    CHECK(raw.bytes == expected_bytes);
    CHECK(raw.size == 4);
    CHECK(makeRawMidiEnvelope(nullptr, 300, 0, 1, 1).size == 0);

    FixedEventBuffer<RawMidiEnvelope, 2> buffer;
    buffer.clear();
    CHECK(buffer.push(raw));
    CHECK(buffer.push(raw));
    CHECK(!buffer.push(raw));
    CHECK(buffer.size() == 2);
    CHECK(buffer.capacity() == 2);
    CHECK(buffer.dropped() == 1);
    buffer.clear();
    CHECK(buffer.size() == 0);
    CHECK(buffer.dropped() == 0);
}

void testParameterizedHostBridge() {
    using namespace schuss::instrument_lab;
    HostBridge<FloatAdapter> floating;
    CHECK(floating.profile().sample_representation
        == SampleRepresentation::float32);
    CHECK(floating.profile().internal_quantum == 0);
    std::array<float, 7> left{};
    std::array<float, 7> right{};
    CHECK(floating.process(left.data(), right.data(), 3));
    CHECK(floating.process(left.data() + 3, right.data() + 3, 4));
    CHECK(left[0] == 0.0f && left[6] == 6.0f);
    CHECK(right[6] == -6.0f);
    CHECK(!floating.process(nullptr, right.data(), 1));
    floating.reset();
    CHECK(floating.adapter().processed == 0);
    CHECK(floating.adapter().resets == 1);

    HostBridge<Q27Adapter> q27;
    CHECK(q27.profile().sample_representation == SampleRepresentation::q27);
    CHECK(q27.profile().internal_quantum == 16);
    const std::array<std::uint32_t, 3> first{{1, 2, 3}};
    const std::array<std::uint32_t, 2> second{{4, 5}};
    q27.process(first.data(), first.size());
    q27.process(second.data(), second.size());
    CHECK(q27.adapter().carried == 15);
    q27.process(nullptr, 2);
    CHECK(q27.adapter().dropped == 2);
    q27.reset();
    CHECK(q27.adapter().carried == 0);
    CHECK(q27.adapter().dropped == 0);
    CHECK(q27.adapter().resets == 1);

    std::array<float, 4> cleared_left{{1, 1, 1, 1}};
    std::array<float, 4> cleared_right{{1, 1, 1, 1}};
    float* outputs[] = {cleared_left.data(), cleared_right.data()};
    clearStereoOutputs(outputs, 2, 4);
    const std::array<float, 4> cleared{};
    CHECK(cleared_left == cleared);
    CHECK(cleared_right == cleared);
}

void testRendererArtifacts() {
    using namespace schuss::instrument_lab;
    CHECK(jsonEscape("a\n\"b\\") == "a\\n\\\"b\\\\");
    CHECK(finiteJsonNumber(0.5) == "0.5");
    CHECK(sha256("abc")
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    bool rejected = false;
    try {
        static_cast<void>(finiteJsonNumber(
            std::numeric_limits<double>::infinity()));
    } catch (const std::runtime_error&) {
        rejected = true;
    }
    CHECK(rejected);
}

void testUiProjection() {
    struct Descriptor { int id; };
    struct Snapshot { double base; };
    const std::array<Descriptor, 3> descriptors{{{1}, {2}, {3}}};
    const Snapshot snapshot{4.0};
    const auto projected = schuss::instrument_lab::projectControlValues(
        descriptors,
        snapshot,
        [](const Descriptor& descriptor, const Snapshot& state) noexcept {
            return state.base + descriptor.id;
        });
    const std::array<double, 3> expected{{5.0, 6.0, 7.0}};
    CHECK(projected == expected);
}

template <typename Generator>
[[nodiscard]] std::vector<float> renderFixedRate(
    std::uint32_t host_rate,
    std::uint32_t host_frames,
    const std::vector<std::uint32_t>& partitions,
    Generator generator
) {
    using schuss::instrument_lab::FixedRateStereoResampler;
    auto resampler = std::make_unique<FixedRateStereoResampler>();
    CHECK(resampler->prepare(static_cast<double>(host_rate)));
    std::vector<float> left(host_frames, 0.0F);
    std::vector<float> right(host_frames, 0.0F);
    std::uint32_t host_offset = 0U;
    std::size_t partition_index = 0U;
    while (host_offset < host_frames) {
        const auto requested = partitions.empty()
            ? host_frames - host_offset
            : partitions[partition_index++ % partitions.size()];
        const auto chunk = std::min(requested, host_frames - host_offset);
        FixedRateStereoResampler::BlockPlan plan{};
        CHECK(resampler->beginBlock(chunk, plan));
        for (std::uint32_t frame = 0U; frame < plan.source_frames; ++frame) {
            const auto sample = generator(plan.source_frame_start + frame);
            resampler->sourceLeft()[frame] = sample;
            resampler->sourceRight()[frame] = -sample;
        }
        CHECK(resampler->finishBlock(
            left.data() + host_offset,
            right.data() + host_offset,
            chunk));
        host_offset += chunk;
    }
    for (std::uint32_t frame = 0U; frame < host_frames; ++frame) {
        CHECK(std::isfinite(left[frame]));
        CHECK(right[frame] == -left[frame]);
    }
    return left;
}

[[nodiscard]] double rms(
    const std::vector<float>& samples,
    std::size_t first,
    std::size_t last
) {
    CHECK(first < last && last <= samples.size());
    double energy = 0.0;
    for (auto index = first; index < last; ++index) {
        const auto sample = static_cast<double>(samples[index]);
        energy += sample * sample;
    }
    return std::sqrt(energy / static_cast<double>(last - first));
}

void testFixedRateConfigurationAndTimeline() {
    using schuss::instrument_lab::FixedRateStereoResampler;
    struct ExpectedRate final {
        std::uint32_t host_rate;
        std::uint32_t numerator;
        std::uint32_t denominator;
        std::uint32_t latency;
    };
    constexpr std::array<ExpectedRate, 7U> expected{{
        {32000U, 3U, 2U, 44U},
        {44100U, 160U, 147U, 60U},
        {48000U, 1U, 1U, 0U},
        {88200U, 80U, 147U, 120U},
        {96000U, 1U, 2U, 130U},
        {176400U, 40U, 147U, 239U},
        {192000U, 1U, 4U, 260U},
    }};

    CHECK(!FixedRateStereoResampler::supportsHostRate(0.0));
    CHECK(!FixedRateStereoResampler::supportsHostRate(48000.5));
    CHECK(!FixedRateStereoResampler::supportsHostRate(48001.0));
    for (const auto& item : expected) {
        auto resampler = std::make_unique<FixedRateStereoResampler>();
        CHECK(resampler->prepare(static_cast<double>(item.host_rate)));
        CHECK(resampler->hostRateHz() == item.host_rate);
        CHECK(resampler->ratioNumerator() == item.numerator);
        CHECK(resampler->ratioDenominator() == item.denominator);
        CHECK(resampler->latencyHostFrames() == item.latency);
        CHECK(resampler->bypassed() == (item.host_rate == 48000U));

        std::uint64_t host_total = 0U;
        const std::array<std::uint32_t, 10U> partitions{{
            1U, 16U, 64U, 127U, 128U, 511U, 512U, 513U, 2048U, 4096U,
        }};
        std::uint32_t previous_event = 0U;
        for (const auto partition : partitions) {
            FixedRateStereoResampler::BlockPlan plan{};
            CHECK(resampler->beginBlock(partition, plan));
            CHECK(plan.host_frame_start == host_total);
            const auto expected_start = (
                host_total * item.numerator + item.denominator - 1U)
                / item.denominator;
            const auto expected_end = (
                (host_total + partition) * item.numerator
                    + item.denominator - 1U)
                / item.denominator;
            CHECK(plan.source_frame_start == expected_start);
            CHECK(plan.source_frame_end == expected_end);
            CHECK(plan.source_frames == expected_end - expected_start);
            for (const auto offset : {0U, partition / 2U, partition}) {
                const auto mapped = resampler->sourceOffsetForHostOffset(offset);
                const auto absolute_host = host_total + offset;
                const auto expected_event = (
                    absolute_host * item.numerator + item.denominator - 1U)
                    / item.denominator;
                CHECK(plan.source_frame_start + mapped == expected_event);
                CHECK(mapped >= previous_event || offset == 0U);
                previous_event = mapped;
            }
            CHECK(resampler->finishBlock(
                resampler->sourceLeft(),
                resampler->sourceRight(),
                partition));
            host_total += partition;
            const auto expected_source = (
                host_total * item.numerator + item.denominator - 1U)
                / item.denominator;
            CHECK(resampler->hostFramesProcessed() == host_total);
            CHECK(resampler->sourceFramesProcessed() == expected_source);
            previous_event = 0U;
        }
        FixedRateStereoResampler::BlockPlan rejected{};
        CHECK(!resampler->beginBlock(8193U, rejected));
    }
}

void testFixedRateSignalAndPartitionInvariance() {
    constexpr double pi = 3.14159265358979323846264338327950288;
    const std::vector<std::uint32_t> single_partition{4096U};
    const std::vector<std::uint32_t> varied_partitions{
        1U, 16U, 64U, 127U, 128U, 511U, 512U, 513U, 2048U, 4096U,
    };
    const auto sine = [](double frequency, std::uint64_t frame) {
        return static_cast<float>(std::sin(
            2.0 * pi * frequency * static_cast<double>(frame) / 48000.0));
    };

    const auto reference = renderFixedRate(
        44100U, 32768U, single_partition,
        [&sine](std::uint64_t frame) { return sine(1000.0, frame); });
    const auto partitioned = renderFixedRate(
        44100U, 32768U, varied_partitions,
        [&sine](std::uint64_t frame) { return sine(1000.0, frame); });
    CHECK(reference == partitioned);

    const auto dc = renderFixedRate(
        44100U, 16384U, varied_partitions,
        [](std::uint64_t) { return 1.0F; });
    double maximum_dc_error = 0.0;
    for (std::size_t index = 1024U; index < dc.size(); ++index) {
        maximum_dc_error = std::max(
            maximum_dc_error,
            std::abs(static_cast<double>(dc[index]) - 1.0));
    }
    CHECK(maximum_dc_error <= 2.0e-5);

    const auto one_khz = rms(reference, 2048U, reference.size());
    const auto one_khz_db = 20.0 * std::log10(one_khz * std::sqrt(2.0));
    CHECK(std::abs(one_khz_db) <= 0.05);

    const auto high_passband = renderFixedRate(
        44100U, 32768U, varied_partitions,
        [&sine](std::uint64_t frame) { return sine(18000.0, frame); });
    const auto high_rms = rms(high_passband, 2048U, high_passband.size());
    const auto high_db = 20.0 * std::log10(high_rms * std::sqrt(2.0));
    CHECK(std::abs(high_db) <= 0.35);

    const auto stopband = renderFixedRate(
        44100U, 32768U, varied_partitions,
        [&sine](std::uint64_t frame) { return sine(23000.0, frame); });
    const auto stopband_rms = rms(stopband, 2048U, stopband.size());
    const auto stopband_db = 20.0 * std::log10(
        std::max(stopband_rms, 1.0e-20));
    CHECK(stopband_db < -70.0);

    std::vector<float> unfiltered(32768U, 0.0F);
    constexpr double ratio = 48000.0 / 44100.0;
    for (std::size_t frame = 0U; frame < unfiltered.size(); ++frame) {
        const auto position = static_cast<double>(frame) * ratio;
        const auto base = static_cast<std::uint64_t>(std::floor(position));
        const auto fraction = position - static_cast<double>(base);
        const auto first = static_cast<double>(sine(23000.0, base));
        const auto second = static_cast<double>(sine(23000.0, base + 1U));
        unfiltered[frame] = static_cast<float>(
            first + fraction * (second - first));
    }
    const auto unfiltered_db = 20.0 * std::log10(
        rms(unfiltered, 2048U, unfiltered.size()));
    CHECK(unfiltered_db >= -40.0);

    auto impulse_resampler = std::make_unique<
        schuss::instrument_lab::FixedRateStereoResampler>();
    CHECK(impulse_resampler->prepare(44100.0));
    const auto impulse = renderFixedRate(
        44100U, 1024U, {1024U},
        [](std::uint64_t frame) { return frame == 0U ? 1.0F : 0.0F; });
    const auto peak = static_cast<std::size_t>(std::distance(
        impulse.begin(),
        std::max_element(
            impulse.begin(), impulse.end(),
            [](float left, float right) {
                return std::abs(left) < std::abs(right);
            })));
    CHECK(peak == impulse_resampler->latencyHostFrames());
}

}  // namespace

int main() {
    testBoundedMidi();
    testParameterizedHostBridge();
    testRendererArtifacts();
    testUiProjection();
    testFixedRateConfigurationAndTimeline();
    testFixedRateSignalAndPartitionInvariance();
    if (failures != 0) return EXIT_FAILURE;
    std::cout << "instrument lab core tests passed\n";
    return EXIT_SUCCESS;
}
