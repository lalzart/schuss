#include "schuss/instrument_lab/bounded_midi.hpp"
#include "schuss/instrument_lab/host_bridge.hpp"
#include "schuss/instrument_lab/renderer_artifacts.hpp"
#include "schuss/instrument_lab/ui_projection.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

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

}  // namespace

int main() {
    testBoundedMidi();
    testParameterizedHostBridge();
    testRendererArtifacts();
    testUiProjection();
    if (failures != 0) return EXIT_FAILURE;
    std::cout << "instrument lab core tests passed\n";
    return EXIT_SUCCESS;
}
