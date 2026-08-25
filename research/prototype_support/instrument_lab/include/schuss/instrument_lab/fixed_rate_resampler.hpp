#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <numeric>

namespace schuss::instrument_lab {

// Fixed-capacity stereo output conversion for 48 kHz Instrument Lab Cores.
// Coefficients and rational phases are prepared outside the audio callback;
// beginBlock(), source scratch access, sourceOffsetForHostOffset(), and
// finishBlock() perform no allocation or locking.
class FixedRateStereoResampler final {
public:
    static constexpr std::uint32_t kSourceRateHz = 48000U;
    static constexpr std::uint32_t kMaximumHostBlockFrames = 8192U;
    static constexpr std::size_t kTapCount = 129U;
    static constexpr std::int32_t kHalfTapCount = 64;
    static constexpr std::uint32_t kDesignDelaySourceFrames = 65U;
    static constexpr std::size_t kMaximumPhaseCount = 147U;
    static constexpr std::uint32_t kMaximumSourceBlockFrames = 12288U;

    static constexpr std::array<std::uint32_t, 7U> kSupportedHostRates{{
        32000U,
        44100U,
        48000U,
        88200U,
        96000U,
        176400U,
        192000U,
    }};

    struct BlockPlan final {
        std::uint32_t host_frames{};
        std::uint32_t source_frames{};
        std::uint64_t host_frame_start{};
        std::uint64_t source_frame_start{};
        std::uint64_t source_frame_end{};
    };

    [[nodiscard]] static bool supportsHostRate(double host_rate) noexcept {
        if (!std::isfinite(host_rate) || host_rate <= 0.0) return false;
        const auto rounded = std::llround(host_rate);
        if (rounded <= 0
            || rounded > static_cast<long long>(
                std::numeric_limits<std::uint32_t>::max())
            || std::abs(host_rate - static_cast<double>(rounded)) > 1.0e-6) {
            return false;
        }
        return supportsHostRate(static_cast<std::uint32_t>(rounded));
    }

    [[nodiscard]] static constexpr bool supportsHostRate(
        std::uint32_t host_rate
    ) noexcept {
        for (const auto supported : kSupportedHostRates) {
            if (host_rate == supported) return true;
        }
        return false;
    }

    [[nodiscard]] bool prepare(double host_rate) noexcept {
        prepared_ = false;
        block_active_ = false;
        if (!supportsHostRate(host_rate)) return false;
        const auto rounded = static_cast<std::uint32_t>(std::llround(host_rate));
        host_rate_hz_ = rounded;
        const auto divisor = std::gcd(kSourceRateHz, host_rate_hz_);
        ratio_numerator_ = kSourceRateHz / divisor;
        ratio_denominator_ = host_rate_hz_ / divisor;
        if (ratio_denominator_ == 0U
            || ratio_denominator_ > kMaximumPhaseCount) {
            return false;
        }
        bypassed_ = host_rate_hz_ == kSourceRateHz;
        latency_host_frames_ = bypassed_
            ? 0U
            : ceilUnsignedProduct(
                kDesignDelaySourceFrames,
                ratio_denominator_,
                ratio_numerator_);
        if (!bypassed_ && !buildPhaseBank()) return false;
        prepared_ = true;
        reset();
        return true;
    }

    void release() noexcept {
        prepared_ = false;
        block_active_ = false;
    }

    void reset() noexcept {
        host_frames_processed_ = 0U;
        source_frames_processed_ = 0U;
        failures_ = 0U;
        block_active_ = false;
        active_plan_ = {};
        source_left_.fill(0.0F);
        source_right_.fill(0.0F);
        history_left_.fill(0.0F);
        history_right_.fill(0.0F);
    }

    [[nodiscard]] bool beginBlock(
        std::uint32_t host_frames,
        BlockPlan& plan
    ) noexcept {
        plan = {};
        if (!prepared_ || block_active_ || host_frames == 0U
            || host_frames > kMaximumHostBlockFrames
            || host_frames_processed_
                > std::numeric_limits<std::uint64_t>::max() - host_frames) {
            ++failures_;
            return false;
        }

        std::uint64_t expected_source_start = 0U;
        std::uint64_t source_end = 0U;
        if (!sourceBoundary(host_frames_processed_, expected_source_start)
            || expected_source_start != source_frames_processed_
            || !sourceBoundary(
                host_frames_processed_ + host_frames, source_end)
            || source_end < source_frames_processed_
            || source_end - source_frames_processed_
                > kMaximumSourceBlockFrames) {
            ++failures_;
            return false;
        }

        active_plan_ = {
            host_frames,
            static_cast<std::uint32_t>(
                source_end - source_frames_processed_),
            host_frames_processed_,
            source_frames_processed_,
            source_end,
        };
        std::fill_n(source_left_.data(), active_plan_.source_frames, 0.0F);
        std::fill_n(source_right_.data(), active_plan_.source_frames, 0.0F);
        block_active_ = true;
        plan = active_plan_;
        return true;
    }

    [[nodiscard]] std::uint32_t sourceOffsetForHostOffset(
        std::uint32_t host_offset
    ) const noexcept {
        if (!block_active_) return 0U;
        const auto bounded = std::min(host_offset, active_plan_.host_frames);
        std::uint64_t boundary = active_plan_.source_frame_start;
        if (!sourceBoundary(
                active_plan_.host_frame_start + bounded, boundary)
            || boundary < active_plan_.source_frame_start) {
            return active_plan_.source_frames;
        }
        const auto offset = boundary - active_plan_.source_frame_start;
        return static_cast<std::uint32_t>(std::min<std::uint64_t>(
            offset, active_plan_.source_frames));
    }

    [[nodiscard]] float* sourceLeft() noexcept { return source_left_.data(); }
    [[nodiscard]] float* sourceRight() noexcept { return source_right_.data(); }
    [[nodiscard]] const BlockPlan& activePlan() const noexcept {
        return active_plan_;
    }

    [[nodiscard]] bool finishBlock(
        float* output_left,
        float* output_right,
        std::uint32_t host_frames
    ) noexcept {
        if (!block_active_ || output_left == nullptr || output_right == nullptr
            || host_frames != active_plan_.host_frames) {
            clearOutputs(output_left, output_right, host_frames);
            block_active_ = false;
            ++failures_;
            return false;
        }

        appendSourceBlock();
        bool success = true;
        if (bypassed_) {
            if (active_plan_.source_frames != host_frames) {
                success = false;
            } else {
                std::copy_n(source_left_.data(), host_frames, output_left);
                std::copy_n(source_right_.data(), host_frames, output_right);
            }
        } else {
            success = renderResampled(output_left, output_right, host_frames);
        }

        host_frames_processed_ += host_frames;
        block_active_ = false;
        active_plan_ = {};
        if (!success) {
            clearOutputs(output_left, output_right, host_frames);
            ++failures_;
        }
        return success;
    }

    void cancelBlock() noexcept {
        if (block_active_) ++failures_;
        block_active_ = false;
        active_plan_ = {};
    }

    [[nodiscard]] bool prepared() const noexcept { return prepared_; }
    [[nodiscard]] bool bypassed() const noexcept { return bypassed_; }
    [[nodiscard]] std::uint32_t hostRateHz() const noexcept {
        return host_rate_hz_;
    }
    [[nodiscard]] std::uint32_t ratioNumerator() const noexcept {
        return ratio_numerator_;
    }
    [[nodiscard]] std::uint32_t ratioDenominator() const noexcept {
        return ratio_denominator_;
    }
    [[nodiscard]] std::uint32_t latencyHostFrames() const noexcept {
        return latency_host_frames_;
    }
    [[nodiscard]] std::uint64_t hostFramesProcessed() const noexcept {
        return host_frames_processed_;
    }
    [[nodiscard]] std::uint64_t sourceFramesProcessed() const noexcept {
        return source_frames_processed_;
    }
    [[nodiscard]] std::uint64_t failureCount() const noexcept {
        return failures_;
    }

private:
    static constexpr std::size_t kHistoryCapacity =
        static_cast<std::size_t>(kMaximumSourceBlockFrames)
        + (2U * kDesignDelaySourceFrames) + 16U;
    static constexpr double kPi = 3.14159265358979323846264338327950288;
    static constexpr double kKaiserBeta = 8.6;
    static constexpr double kWindowRadius = 65.0;

    [[nodiscard]] static constexpr std::uint32_t ceilUnsignedProduct(
        std::uint32_t left,
        std::uint32_t right,
        std::uint32_t divisor
    ) noexcept {
        return divisor == 0U
            ? 0U
            : static_cast<std::uint32_t>(
                (static_cast<std::uint64_t>(left) * right + divisor - 1U)
                / divisor);
    }

    [[nodiscard]] bool sourceBoundary(
        std::uint64_t host_frame,
        std::uint64_t& source_frame
    ) const noexcept {
        if (ratio_numerator_ == 0U || ratio_denominator_ == 0U
            || host_frame > (
                std::numeric_limits<std::uint64_t>::max()
                - (ratio_denominator_ - 1U)) / ratio_numerator_) {
            return false;
        }
        source_frame = (
            host_frame * ratio_numerator_ + ratio_denominator_ - 1U)
            / ratio_denominator_;
        return true;
    }

    [[nodiscard]] static double besselI0(double value) noexcept {
        const auto scaled = value * value * 0.25;
        double sum = 1.0;
        double term = 1.0;
        for (std::uint32_t index = 1U; index <= 48U; ++index) {
            const auto denominator = static_cast<double>(index) * index;
            term *= scaled / denominator;
            sum += term;
            if (term <= sum * 1.0e-17) break;
        }
        return sum;
    }

    [[nodiscard]] static double normalizedSinc(double value) noexcept {
        if (std::abs(value) < 1.0e-15) return 1.0;
        const auto angle = kPi * value;
        return std::sin(angle) / angle;
    }

    [[nodiscard]] bool buildPhaseBank() noexcept {
        const auto output_per_source = static_cast<double>(ratio_denominator_)
            / static_cast<double>(ratio_numerator_);
        const auto cutoff = 0.475 * std::min(1.0, output_per_source);
        const auto window_denominator = besselI0(kKaiserBeta);
        if (!std::isfinite(cutoff) || cutoff <= 0.0 || cutoff >= 0.5
            || !std::isfinite(window_denominator)
            || window_denominator <= 0.0) {
            return false;
        }

        for (std::uint32_t phase = 0U;
             phase < ratio_denominator_;
             ++phase) {
            const auto fraction = static_cast<double>(phase)
                / static_cast<double>(ratio_denominator_);
            double sum = 0.0;
            for (std::size_t tap = 0U; tap < kTapCount; ++tap) {
                const auto offset = static_cast<std::int32_t>(tap)
                    - kHalfTapCount;
                const auto distance = fraction - static_cast<double>(offset);
                const auto normalized_distance = distance / kWindowRadius;
                const auto radial = std::max(
                    0.0, 1.0 - normalized_distance * normalized_distance);
                const auto window = besselI0(
                    kKaiserBeta * std::sqrt(radial)) / window_denominator;
                const auto coefficient = 2.0 * cutoff
                    * normalizedSinc(2.0 * cutoff * distance) * window;
                coefficient_scratch_[tap] = coefficient;
                sum += coefficient;
            }
            if (!std::isfinite(sum) || std::abs(sum) < 1.0e-12) return false;
            for (std::size_t tap = 0U; tap < kTapCount; ++tap) {
                const auto normalized = coefficient_scratch_[tap] / sum;
                if (!std::isfinite(normalized)) return false;
                coefficients_[phase][tap] = static_cast<float>(normalized);
            }
        }
        return true;
    }

    void appendSourceBlock() noexcept {
        for (std::uint32_t frame = 0U;
             frame < active_plan_.source_frames;
             ++frame) {
            const auto absolute = source_frames_processed_ + frame;
            const auto slot = static_cast<std::size_t>(
                absolute % kHistoryCapacity);
            history_left_[slot] = source_left_[frame];
            history_right_[slot] = source_right_[frame];
        }
        source_frames_processed_ = active_plan_.source_frame_end;
    }

    [[nodiscard]] bool sampleAt(
        const std::array<float, kHistoryCapacity>& history,
        std::int64_t absolute,
        float& value
    ) const noexcept {
        if (absolute < 0) {
            value = 0.0F;
            return true;
        }
        const auto unsigned_absolute = static_cast<std::uint64_t>(absolute);
        if (unsigned_absolute >= source_frames_processed_) return false;
        const auto oldest = source_frames_processed_ > kHistoryCapacity
            ? source_frames_processed_ - kHistoryCapacity
            : 0U;
        if (unsigned_absolute < oldest) return false;
        value = history[static_cast<std::size_t>(
            unsigned_absolute % kHistoryCapacity)];
        return true;
    }

    [[nodiscard]] bool renderResampled(
        float* output_left,
        float* output_right,
        std::uint32_t host_frames
    ) const noexcept {
        if (host_frames_processed_
            > static_cast<std::uint64_t>(
                std::numeric_limits<std::int64_t>::max())) {
            return false;
        }
        for (std::uint32_t frame = 0U; frame < host_frames; ++frame) {
            const auto absolute_host = host_frames_processed_ + frame;
            if (absolute_host > static_cast<std::uint64_t>(
                    std::numeric_limits<std::int64_t>::max())) {
                return false;
            }
            const auto delayed_host = static_cast<std::int64_t>(absolute_host)
                - static_cast<std::int64_t>(latency_host_frames_);
            if (delayed_host > std::numeric_limits<std::int64_t>::max()
                    / static_cast<std::int64_t>(ratio_numerator_)
                || delayed_host < std::numeric_limits<std::int64_t>::min()
                    / static_cast<std::int64_t>(ratio_numerator_)) {
                return false;
            }
            const auto numerator = delayed_host
                * static_cast<std::int64_t>(ratio_numerator_);
            auto base = numerator / static_cast<std::int64_t>(ratio_denominator_);
            auto remainder = numerator
                % static_cast<std::int64_t>(ratio_denominator_);
            if (remainder < 0) {
                remainder += static_cast<std::int64_t>(ratio_denominator_);
                --base;
            }
            const auto phase = static_cast<std::size_t>(remainder);
            double left = 0.0;
            double right = 0.0;
            for (std::size_t tap = 0U; tap < kTapCount; ++tap) {
                const auto source_index = base
                    + static_cast<std::int64_t>(tap)
                    - static_cast<std::int64_t>(kHalfTapCount);
                float source_left = 0.0F;
                float source_right = 0.0F;
                if (!sampleAt(history_left_, source_index, source_left)
                    || !sampleAt(history_right_, source_index, source_right)) {
                    return false;
                }
                const auto coefficient = static_cast<double>(
                    coefficients_[phase][tap]);
                left += static_cast<double>(source_left) * coefficient;
                right += static_cast<double>(source_right) * coefficient;
            }
            if (!std::isfinite(left) || !std::isfinite(right)) return false;
            output_left[frame] = static_cast<float>(left);
            output_right[frame] = static_cast<float>(right);
        }
        return true;
    }

    static void clearOutputs(
        float* output_left,
        float* output_right,
        std::uint32_t host_frames
    ) noexcept {
        if (output_left != nullptr) std::fill_n(output_left, host_frames, 0.0F);
        if (output_right != nullptr) std::fill_n(output_right, host_frames, 0.0F);
    }

    std::array<float, kMaximumSourceBlockFrames> source_left_{};
    std::array<float, kMaximumSourceBlockFrames> source_right_{};
    std::array<float, kHistoryCapacity> history_left_{};
    std::array<float, kHistoryCapacity> history_right_{};
    std::array<std::array<float, kTapCount>, kMaximumPhaseCount> coefficients_{};
    std::array<double, kTapCount> coefficient_scratch_{};

    BlockPlan active_plan_{};
    std::uint64_t host_frames_processed_{};
    std::uint64_t source_frames_processed_{};
    std::uint64_t failures_{};
    std::uint32_t host_rate_hz_{};
    std::uint32_t ratio_numerator_{};
    std::uint32_t ratio_denominator_{};
    std::uint32_t latency_host_frames_{};
    bool prepared_{};
    bool bypassed_{};
    bool block_active_{};
};

}  // namespace schuss::instrument_lab
