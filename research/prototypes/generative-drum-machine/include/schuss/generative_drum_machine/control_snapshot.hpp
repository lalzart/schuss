#pragma once

#include "schuss/generative_drum_machine/core.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace schuss::generative_drum_machine {

// Single-writer/single-reader publication boundary for the callback-owned
// StreamingEngine. Multiple GUI/MIDI writers must serialize before calling
// publish(). Three immutable-at-read slots let load() remain bounded without
// asking the audio callback to spin or lock.
class AtomicControlSnapshot final {
public:
    AtomicControlSnapshot() noexcept = default;

    [[nodiscard]] static constexpr bool lockFreeContract() noexcept {
        return std::atomic<std::uint32_t>::is_always_lock_free;
    }

    void publish(const Controls& controls) noexcept {
        const auto active = active_slot_.load(std::memory_order_seq_cst);
        const auto reader = reader_slot_.load(std::memory_order_seq_cst);
        std::uint32_t target = kNoReader;
        for (std::uint32_t candidate = 0U; candidate < kSlotCount; ++candidate) {
            if (candidate != active && candidate != reader) {
                target = candidate;
                break;
            }
        }
        // With three slots and one reader, one non-active/non-read slot always
        // exists. The fallback keeps this function total if that invariant is
        // ever violated by an unsupported caller topology.
        if (target == kNoReader) return;
        slots_[target] = controls;
        active_slot_.store(target, std::memory_order_seq_cst);
    }

    [[nodiscard]] Controls load(Controls fallback) const noexcept {
        for (int attempt = 0; attempt < 4; ++attempt) {
            const auto slot = active_slot_.load(std::memory_order_seq_cst);
            reader_slot_.store(slot, std::memory_order_seq_cst);
            if (active_slot_.load(std::memory_order_seq_cst) != slot) {
                reader_slot_.store(kNoReader, std::memory_order_seq_cst);
                continue;
            }
            const auto next = slots_[slot];
            reader_slot_.store(kNoReader, std::memory_order_seq_cst);
            return next;
        }
        return fallback;
    }

private:
    static constexpr std::uint32_t kSlotCount = 3U;
    static constexpr std::uint32_t kNoReader = kSlotCount;

    std::array<Controls, kSlotCount> slots_{};
    std::atomic<std::uint32_t> active_slot_{0U};
    mutable std::atomic<std::uint32_t> reader_slot_{kNoReader};
};

}  // namespace schuss::generative_drum_machine
