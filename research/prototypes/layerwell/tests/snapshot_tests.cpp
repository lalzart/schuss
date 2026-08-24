#include "layerwell/state_snapshot.hpp"

#include <atomic>
#include <cstdint>
#include <iostream>
#include <thread>

int main() {
    if (!layerwell::AtomicSnapshot::lockFreeContract()) {
        std::cerr << "32-bit snapshot atomics are not always lock free\n";
        return 1;
    }

    layerwell::AtomicSnapshot mailbox;
    std::atomic<bool> start{false};
    std::atomic<bool> done{false};
    std::atomic<bool> torn{false};

    std::thread writer([&] {
        while (!start.load(std::memory_order_acquire)) {}
        for (std::uint64_t sequence = 1U; sequence <= 50000U; ++sequence) {
            layerwell::Snapshot snapshot{};
            snapshot.accepted_sequence = sequence;
            snapshot.absolute_frame = sequence;
            snapshot.loop_length_frames = static_cast<std::uint32_t>(sequence & 0xffffffffU);
            snapshot.phase_frames = snapshot.loop_length_frames;
            snapshot.layers[0].level = static_cast<float>(sequence % 128U) / 127.0f;
            snapshot.diagnostics.snapshot_sequence = sequence;
            mailbox.publish(snapshot);
        }
        done.store(true, std::memory_order_release);
    });

    std::thread reader([&] {
        start.store(true, std::memory_order_release);
        std::uint64_t last = 0U;
        while (!done.load(std::memory_order_acquire)) {
            const auto snapshot = mailbox.load();
            if (snapshot.accepted_sequence == 0U) continue;
            if (snapshot.accepted_sequence != snapshot.absolute_frame
                || snapshot.accepted_sequence != snapshot.diagnostics.snapshot_sequence
                || snapshot.loop_length_frames != snapshot.phase_frames
                || snapshot.accepted_sequence < last) {
                torn.store(true, std::memory_order_release);
                return;
            }
            last = snapshot.accepted_sequence;
        }
    });

    writer.join();
    reader.join();
    if (torn.load(std::memory_order_acquire)) {
        std::cerr << "snapshot mailbox returned torn or regressing state\n";
        return 1;
    }
    std::cout << "Layerwell snapshot tests passed\n";
    return 0;
}
