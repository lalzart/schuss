#include "schuss/dsp/mutable_braids_v1.hpp"

#include <array>
#include <cstdint>
#include <iostream>

namespace adapter = schuss::dsp::mutable_braids_v1;

std::array<std::int16_t, 32> renderReference(std::uint32_t seed) {
    adapter::seedRandom(seed);
    adapter::Voice voice;
    voice.reset(adapter::Model::kick, 7680, 16384, 16384);
    voice.strike();
    std::array<std::uint8_t, 32> sync{};
    std::array<std::int16_t, 32> output{};
    voice.render(sync.data(), output.data(), output.size());
    return output;
}

int main() {
    const auto first = renderReference(0x12345678U);
    const auto second = renderReference(0x12345678U);
    if (first != second) {
        std::cerr << "deterministic reference mismatch\n";
        return 1;
    }
    bool nonzero = false;
    for (const auto sample : first) {
        nonzero = nonzero || sample != 0;
    }
    if (!nonzero) {
        std::cerr << "reference render is silent\n";
        return 1;
    }
    std::uint64_t hash = 1469598103934665603ULL;
    for (const auto sample : first) {
        const auto value = static_cast<std::uint16_t>(sample);
        hash ^= static_cast<std::uint8_t>(value);
        hash *= 1099511628211ULL;
        hash ^= static_cast<std::uint8_t>(value >> 8U);
        hash *= 1099511628211ULL;
    }
    constexpr std::uint64_t kExpectedReferenceHash = 2265768653744534465ULL;
    if (hash != kExpectedReferenceHash) {
        std::cerr << "reference hash mismatch: " << hash << "\n";
        return 1;
    }
    return 0;
}
