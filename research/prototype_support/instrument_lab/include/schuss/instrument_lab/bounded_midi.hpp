#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace schuss::instrument_lab {

struct RawMidiEnvelope {
    std::uint32_t sample_offset{};
    std::uint64_t ingress_sequence{};
    std::array<std::uint8_t, 3> bytes{};
    std::uint8_t size{};
};

class IngressSequence final {
public:
    void reset() noexcept { value_ = 0; }

    [[nodiscard]] std::uint64_t next() noexcept { return ++value_; }

    [[nodiscard]] std::uint64_t value() const noexcept { return value_; }

private:
    std::uint64_t value_{};
};

[[nodiscard]] inline std::uint32_t clampSampleOffset(
    int sample_position,
    std::uint32_t block_frames
) noexcept {
    const auto maximum = block_frames > 0
        ? static_cast<int>(std::min<std::uint32_t>(
              block_frames - 1U,
              static_cast<std::uint32_t>(std::numeric_limits<int>::max())))
        : 0;
    return static_cast<std::uint32_t>(
        std::clamp(sample_position, 0, maximum));
}

[[nodiscard]] inline std::uint8_t encodedByteCount(int byte_count) noexcept {
    return byte_count >= 0
            && static_cast<unsigned int>(byte_count)
                <= std::numeric_limits<std::uint8_t>::max()
        ? static_cast<std::uint8_t>(byte_count)
        : 0U;
}

[[nodiscard]] inline RawMidiEnvelope makeRawMidiEnvelope(
    const std::uint8_t* data,
    int byte_count,
    int sample_position,
    std::uint32_t block_frames,
    std::uint64_t ingress_sequence
) noexcept {
    RawMidiEnvelope result{};
    result.sample_offset = clampSampleOffset(sample_position, block_frames);
    result.ingress_sequence = ingress_sequence;
    result.size = encodedByteCount(byte_count);
    const auto safe_count = byte_count > 0
        ? static_cast<std::size_t>(byte_count)
        : 0U;
    const auto copied = std::min(result.bytes.size(), safe_count);
    if (data != nullptr) std::copy_n(data, copied, result.bytes.begin());
    return result;
}

template <typename Event, std::size_t Capacity>
class FixedEventBuffer final {
public:
    static_assert(Capacity > 0, "fixed event capacity must be positive");

    void clear() noexcept {
        size_ = 0;
        dropped_ = 0;
    }

    [[nodiscard]] bool push(const Event& event) noexcept {
        if (size_ == events_.size()) {
            ++dropped_;
            return false;
        }
        events_[size_++] = event;
        return true;
    }

    [[nodiscard]] const Event* data() const noexcept { return events_.data(); }
    [[nodiscard]] Event* data() noexcept { return events_.data(); }
    [[nodiscard]] std::size_t size() const noexcept { return size_; }
    [[nodiscard]] std::size_t capacity() const noexcept { return events_.size(); }
    [[nodiscard]] std::size_t dropped() const noexcept { return dropped_; }

private:
    std::array<Event, Capacity> events_{};
    std::size_t size_{};
    std::size_t dropped_{};
};

}  // namespace schuss::instrument_lab
