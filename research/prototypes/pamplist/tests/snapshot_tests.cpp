#include "schuss/pamplist/control_snapshot.hpp"

#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>

namespace pam = schuss::pamplist;

namespace {

[[noreturn]] void fail(const std::string& message) {
    std::cerr << "pamplist_snapshot_tests: " << message << '\n';
    std::exit(1);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

pam::Controls stamped(std::uint32_t stamp) {
    auto value = pam::defaultControls();
    value.seed = stamp;
    value.tempo_milli_bpm = 20000U + stamp % 280001U;
    value.selected_page = static_cast<std::uint8_t>(stamp % pam::kPageCount);
    value.lane_control_mode = (stamp & 1U) == 0U
        ? pam::LaneControlMode::voice
        : pam::LaneControlMode::motion;
    value.effect_clear_generation = stamp * 17U;
    value.cohesion.drive = static_cast<float>(stamp % 101U) / 100.0F;
    value.cohesion.cohere = static_cast<float>(stamp % 97U) / 96.0F;
    value.cohesion.root_note = static_cast<float>(24U + stamp % 61U);
    for (std::size_t lane = 0; lane < pam::kLaneCount; ++lane) {
        value.lanes[lane].rate_index = static_cast<std::uint8_t>(
            (stamp + lane) % pam::kRateCount);
        value.lanes[lane].phase_u7 = static_cast<std::uint8_t>(stamp % 128U);
        value.lanes[lane].hits = static_cast<std::uint8_t>((stamp + lane) % 17U);
        value.lanes[lane].rotation = static_cast<std::uint8_t>((stamp + lane) % 16U);
        value.voices[lane].engine = static_cast<std::uint8_t>(
            (stamp + lane * 3U) % 24U);
        value.voices[lane].note = static_cast<float>(
            24U + (stamp + lane) % 73U);
    }
    return value;
}

bool coherent(const pam::Controls& value) {
    const auto expected = stamped(value.seed);
    return value.tempo_milli_bpm == expected.tempo_milli_bpm
        && value.selected_page == expected.selected_page
        && value.lane_control_mode == expected.lane_control_mode
        && value.effect_clear_generation == expected.effect_clear_generation
        && value.cohesion.drive == expected.cohesion.drive
        && value.cohesion.cohere == expected.cohesion.cohere
        && value.cohesion.root_note == expected.cohesion.root_note
        && value.lanes[0].rate_index == expected.lanes[0].rate_index
        && value.lanes[6].hits == expected.lanes[6].hits
        && value.lanes[5].rotation == expected.lanes[5].rotation
        && value.voices[0].engine == expected.voices[0].engine
        && value.voices[6].note == expected.voices[6].note;
}

}  // namespace

int main() {
    expect(pam::AtomicControlSnapshot::lockFreeContract(),
        "32-bit atomic publication contract is not lock-free");
    pam::AtomicControlSnapshot mailbox;
    mailbox.publish(stamped(1U));
    std::atomic<bool> start{false};
    std::atomic<bool> done{false};
    std::atomic<bool> torn{false};
    std::thread writer([&]() {
        while (!start.load(std::memory_order_acquire)) {}
        for (std::uint32_t stamp = 2U; stamp < 200000U; ++stamp) {
            mailbox.publish(stamped(stamp));
        }
        done.store(true, std::memory_order_release);
    });
    start.store(true, std::memory_order_release);
    auto fallback = stamped(1U);
    while (!done.load(std::memory_order_acquire)) {
        const auto value = mailbox.load(fallback);
        if (!coherent(value)) torn.store(true, std::memory_order_relaxed);
        fallback = value;
    }
    writer.join();
    expect(!torn.load(std::memory_order_relaxed),
        "whole-control snapshot tore under contention");
    std::cout << "pamplist_snapshot_tests: pass\n";
    return 0;
}
