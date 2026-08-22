#include "schuss/generative_drum_machine/control_snapshot.hpp"

#include <atomic>
#include <cstdint>
#include <iostream>
#include <thread>

namespace gdm = schuss::generative_drum_machine;

namespace {

bool sameState(const gdm::Controls& left, const gdm::Controls& right) noexcept {
    return gdm::sameSoundControls(left, right)
        && left.selected_voice_lane == right.selected_voice_lane
        && left.voice_shaping == right.voice_shaping;
}

gdm::Controls state(std::uint32_t salt) {
    gdm::Controls controls{};
    for (std::size_t lane = 0U; lane < gdm::kLogicalLaneCount; ++lane) {
        controls.complexity[lane] = static_cast<std::uint16_t>(1000U + salt + lane * 997U);
        auto& shape = controls.voice_shapes[lane];
        shape.tune_u7 = static_cast<std::uint8_t>((salt + lane * 3U) & 0x7fU);
        shape.timbre_u7 = static_cast<std::uint8_t>((salt + lane * 5U) & 0x7fU);
        shape.color_u7 = static_cast<std::uint8_t>((salt + lane * 7U) & 0x7fU);
        shape.decay_u7 = static_cast<std::uint8_t>((salt + lane * 11U) & 0x7fU);
        shape.pitch_env_u7 = static_cast<std::uint8_t>((salt + lane * 13U) & 0x7fU);
        shape.level_u7 = static_cast<std::uint8_t>((salt + lane * 17U) & 0x7fU);
    }
    controls.enthusiasm = static_cast<std::uint16_t>(20000U + salt);
    controls.tempo_milli_bpm = 90000U + salt;
    controls.swing_u15 = static_cast<std::uint16_t>(salt);
    controls.rhythm_preset = static_cast<std::uint8_t>(salt % gdm::kRhythmPresetCount);
    controls.selected_voice_lane = static_cast<std::uint8_t>(salt % gdm::kLogicalLaneCount);
    controls.voice_shaping = (salt & 1U) != 0U;
    return controls;
}

}  // namespace

int main() {
    if (!gdm::AtomicControlSnapshot::lockFreeContract()) {
        std::cerr << "required atomics are not always lock-free\n";
        return 1;
    }
    const auto first = state(17U);
    const auto second = state(88U);
    gdm::AtomicControlSnapshot snapshot;
    snapshot.publish(first);
    auto accepted = snapshot.load(gdm::Controls{});
    if (!sameState(accepted, first)) {
        std::cerr << "round-trip snapshot mismatch\n";
        return 1;
    }

    std::atomic<bool> running{true};
    std::atomic<std::uint32_t> torn_reads{0U};
    std::thread writer{[&] {
        for (std::uint32_t index = 0U; index < 200000U; ++index) {
            snapshot.publish((index & 1U) == 0U ? first : second);
        }
        running.store(false, std::memory_order_release);
    }};
    while (running.load(std::memory_order_acquire)) {
        accepted = snapshot.load(accepted);
        if (!sameState(accepted, first) && !sameState(accepted, second)) {
            torn_reads.fetch_add(1U, std::memory_order_relaxed);
        }
    }
    writer.join();
    if (torn_reads.load(std::memory_order_relaxed) != 0U) {
        std::cerr << "coherent snapshot test observed a torn read\n";
        return 1;
    }
    std::cout << "Generative drum-machine atomic control snapshot tests passed\n";
    return 0;
}
