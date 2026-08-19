#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace schuss::engine {

struct StampedMidi {
    std::uint64_t timestamp_ns{};
    std::uint64_t sequence{};
    std::array<std::uint8_t, 3> bytes{};
    std::uint8_t size{};
};

// The first engine version opens at most one physical MIDI input, so this is
// intentionally a bounded single-producer/single-consumer queue.
template <std::size_t Capacity>
class MidiIngressQueue {
public:
    static_assert(Capacity > 0);
    static_assert(std::atomic<std::size_t>::is_always_lock_free);
    static_assert(std::atomic<std::uint64_t>::is_always_lock_free);

    bool enqueue(const StampedMidi& message) noexcept {
        if (message.size == 0 || message.size > message.bytes.size()) {
            overflows_.fetch_add(1, std::memory_order_relaxed);
            return false;
        }
        const auto write = write_.load(std::memory_order_relaxed);
        const auto next = increment(write);
        if (next == read_.load(std::memory_order_acquire)) {
            overflows_.fetch_add(1, std::memory_order_relaxed);
            return false;
        }
        values_[write] = message;
        write_.store(next, std::memory_order_release);
        return true;
    }

    bool pop(StampedMidi& destination) noexcept {
        const auto read = read_.load(std::memory_order_relaxed);
        if (read == write_.load(std::memory_order_acquire)) return false;
        destination = values_[read];
        read_.store(increment(read), std::memory_order_release);
        return true;
    }

    void reset() noexcept {
        read_.store(0, std::memory_order_relaxed);
        write_.store(0, std::memory_order_relaxed);
        overflows_.store(0, std::memory_order_relaxed);
    }

    std::uint64_t overflows() const noexcept {
        return overflows_.load(std::memory_order_relaxed);
    }

private:
    static constexpr std::size_t increment(std::size_t value) noexcept {
        return (value + 1U) % (Capacity + 1U);
    }

    std::array<StampedMidi, Capacity + 1U> values_{};
    std::atomic<std::size_t> read_{0};
    std::atomic<std::size_t> write_{0};
    std::atomic<std::uint64_t> overflows_{0};
};

}  // namespace schuss::engine
