#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace schuss::murmur_map {

template <typename Value>
class SnapshotMailbox final {
public:
    static_assert(std::is_trivially_copyable_v<Value>);

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

template <typename Value, std::size_t Capacity>
class SpscQueue final {
public:
    static_assert(Capacity >= 2U);
    static_assert(std::is_trivially_copyable_v<Value>);

    [[nodiscard]] static constexpr bool lockFreeContract() noexcept {
        return std::atomic<std::size_t>::is_always_lock_free;
    }

    [[nodiscard]] bool push(const Value& value) noexcept {
        const auto write = write_.load(std::memory_order_relaxed);
        const auto next = increment(write);
        if (next == read_.load(std::memory_order_acquire)) return false;
        values_[write] = value;
        write_.store(next, std::memory_order_release);
        return true;
    }

    [[nodiscard]] bool pop(Value& value) noexcept {
        const auto read = read_.load(std::memory_order_relaxed);
        if (read == write_.load(std::memory_order_acquire)) return false;
        value = values_[read];
        read_.store(increment(read), std::memory_order_release);
        return true;
    }

private:
    [[nodiscard]] static constexpr std::size_t increment(std::size_t value) noexcept {
        return (value + 1U) % Capacity;
    }

    std::array<Value, Capacity> values_{};
    std::atomic<std::size_t> write_{0U};
    std::atomic<std::size_t> read_{0U};
};

}  // namespace schuss::murmur_map
