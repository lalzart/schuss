#pragma once

#include "schuss/pamplist/core.hpp"

#include <array>
#include <atomic>
#include <cstdint>

namespace schuss::pamplist {

// Bounded single-writer/single-reader whole-value publication. UI and MIDI
// writers serialize before publish(); the callback and UI readers never spin
// indefinitely and never observe torn multi-field state.
template <typename Value>
class AtomicSnapshot final {
public:
    AtomicSnapshot() noexcept = default;

    [[nodiscard]] static constexpr bool lockFreeContract() noexcept {
        return std::atomic<std::uint32_t>::is_always_lock_free;
    }

    void publish(const Value& value) noexcept {
        const auto active = active_slot_.load(std::memory_order_seq_cst);
        const auto reader = reader_slot_.load(std::memory_order_seq_cst);
        std::uint32_t target = kNoReader;
        for (std::uint32_t candidate = 0U; candidate < kSlotCount; ++candidate) {
            if (candidate != active && candidate != reader) {
                target = candidate;
                break;
            }
        }
        if (target == kNoReader) return;
        slots_[target] = value;
        active_slot_.store(target, std::memory_order_seq_cst);
    }

    [[nodiscard]] Value load(Value fallback) const noexcept {
        for (int attempt = 0; attempt < 4; ++attempt) {
            const auto slot = active_slot_.load(std::memory_order_seq_cst);
            reader_slot_.store(slot, std::memory_order_seq_cst);
            if (active_slot_.load(std::memory_order_seq_cst) != slot) {
                reader_slot_.store(kNoReader, std::memory_order_seq_cst);
                continue;
            }
            const auto value = slots_[slot];
            reader_slot_.store(kNoReader, std::memory_order_seq_cst);
            return value;
        }
        return fallback;
    }

private:
    static constexpr std::uint32_t kSlotCount = 3U;
    static constexpr std::uint32_t kNoReader = kSlotCount;
    std::array<Value, kSlotCount> slots_{};
    std::atomic<std::uint32_t> active_slot_{0U};
    mutable std::atomic<std::uint32_t> reader_slot_{kNoReader};
};

using AtomicControlSnapshot = AtomicSnapshot<Controls>;
using AtomicAcceptedSnapshot = AtomicSnapshot<Snapshot>;

}  // namespace schuss::pamplist
