#include "schuss/murmur_map/realtime_exchange.hpp"
#include "schuss/murmur_map/ui_model.hpp"

#include <atomic>
#include <cstdint>
#include <iostream>
#include <thread>

namespace mm = schuss::murmur_map;

int main() {
    if (!mm::SnapshotMailbox<mm::PresentationSnapshot>::lockFreeContract()
        || !mm::SpscQueue<mm::UiCommand, 64U>::lockFreeContract()) {
        std::cerr << "required exchange atomics are not always lock-free\n";
        return 1;
    }
    mm::SnapshotMailbox<mm::PresentationSnapshot> mailbox;
    mm::PresentationSnapshot first{};
    first.core.absolute_frame = 111U;
    first.core.accepted_controls = mm::defaultControls();
    mm::PresentationSnapshot second = first;
    second.core.absolute_frame = 999U;
    second.core.accepted_controls.root_midi_note = 84U;
    mailbox.publish(first);
    auto accepted = mailbox.load({});
    if (accepted.core.absolute_frame != 111U) return 1;

    std::atomic<bool> running{true};
    std::atomic<std::uint32_t> torn{0U};
    std::thread writer{[&] {
        for (std::uint32_t index = 0U; index < 100000U; ++index) {
            mailbox.publish((index & 1U) == 0U ? first : second);
        }
        running.store(false, std::memory_order_release);
    }};
    while (running.load(std::memory_order_acquire)) {
        accepted = mailbox.load(accepted);
        const bool is_first = accepted.core.absolute_frame == 111U
            && accepted.core.accepted_controls.root_midi_note == 48U;
        const bool is_second = accepted.core.absolute_frame == 999U
            && accepted.core.accepted_controls.root_midi_note == 84U;
        if (!is_first && !is_second) torn.fetch_add(1U, std::memory_order_relaxed);
    }
    writer.join();
    if (torn.load(std::memory_order_relaxed) != 0U) {
        std::cerr << "snapshot mailbox observed torn state\n";
        return 1;
    }

    mm::SpscQueue<mm::UiCommand, 4U> queue;
    if (!queue.push({mm::UiCommandKind::set_tempo, 90000, 0, 1U})
        || !queue.push({mm::UiCommandKind::set_memory, 1234, 0, 2U})
        || !queue.push({mm::UiCommandKind::capture, 0, 0, 3U})
        || queue.push({mm::UiCommandKind::panic, 0, 0, 4U})) {
        std::cerr << "SPSC bounded-capacity contract failed\n";
        return 1;
    }
    mm::UiCommand command{};
    for (std::uint64_t sequence = 1U; sequence <= 3U; ++sequence) {
        if (!queue.pop(command) || command.sequence != sequence) {
            std::cerr << "SPSC order failed\n";
            return 1;
        }
    }
    if (queue.pop(command)) return 1;
    std::cout << "Murmur Map realtime exchange tests passed\n";
    return 0;
}
