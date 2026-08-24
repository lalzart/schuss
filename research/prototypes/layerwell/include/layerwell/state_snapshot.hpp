#pragma once

#include "layerwell/core.hpp"

#include <array>
#include <atomic>
#include <cstdint>

namespace layerwell {

// Three immutable-at-read slots provide one bounded callback-writer/UI-reader
// publication boundary. Multiple non-audio writers are unsupported.
class AtomicSnapshot final {
public:
    [[nodiscard]] static constexpr bool lockFreeContract() noexcept {
        return std::atomic<std::uint32_t>::is_always_lock_free;
    }

    void publish(const Snapshot& snapshot) noexcept {
        const auto active = active_slot_.load(std::memory_order_seq_cst);
        const auto reader = reader_slot_.load(std::memory_order_seq_cst);
        auto target = kNoReader;
        for (std::uint32_t candidate = 0U; candidate < kSlotCount; ++candidate) {
            if (candidate != active && candidate != reader) {
                target = candidate;
                break;
            }
        }
        if (target == kNoReader) return;
        slots_[target] = snapshot;
        active_slot_.store(target, std::memory_order_seq_cst);
    }

    [[nodiscard]] Snapshot load(Snapshot fallback = {}) const noexcept {
        for (int attempt = 0; attempt < 4; ++attempt) {
            const auto slot = active_slot_.load(std::memory_order_seq_cst);
            reader_slot_.store(slot, std::memory_order_seq_cst);
            if (active_slot_.load(std::memory_order_seq_cst) != slot) {
                reader_slot_.store(kNoReader, std::memory_order_seq_cst);
                continue;
            }
            const auto result = slots_[slot];
            reader_slot_.store(kNoReader, std::memory_order_seq_cst);
            return result;
        }
        return fallback;
    }

private:
    static constexpr std::uint32_t kSlotCount = 3U;
    static constexpr std::uint32_t kNoReader = kSlotCount;

    std::array<Snapshot, kSlotCount> slots_{};
    std::atomic<std::uint32_t> active_slot_{0U};
    mutable std::atomic<std::uint32_t> reader_slot_{kNoReader};
};

}  // namespace layerwell
