#include "tidepit/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>

namespace {

class Sha256 {
public:
    void update(const std::uint8_t* data, std::size_t size) noexcept {
        for (std::size_t index = 0; index < size; ++index) {
            buffer_[buffer_size_++] = data[index];
            ++total_bytes_;
            if (buffer_size_ == buffer_.size()) {
                transform(buffer_.data());
                buffer_size_ = 0;
            }
        }
    }

    void updateLittleEndian(std::int32_t value) noexcept {
        const auto bits = static_cast<std::uint32_t>(value);
        const std::array<std::uint8_t, 4> bytes{{
            static_cast<std::uint8_t>(bits),
            static_cast<std::uint8_t>(bits >> 8U),
            static_cast<std::uint8_t>(bits >> 16U),
            static_cast<std::uint8_t>(bits >> 24U),
        }};
        update(bytes.data(), bytes.size());
    }

    std::string finish() noexcept {
        const std::uint64_t bit_length = total_bytes_ * 8U;
        buffer_[buffer_size_++] = 0x80U;
        if (buffer_size_ > 56U) {
            while (buffer_size_ < buffer_.size()) buffer_[buffer_size_++] = 0;
            transform(buffer_.data());
            buffer_size_ = 0;
        }
        while (buffer_size_ < 56U) buffer_[buffer_size_++] = 0;
        for (int shift = 56; shift >= 0; shift -= 8) {
            buffer_[buffer_size_++] = static_cast<std::uint8_t>(bit_length >> shift);
        }
        transform(buffer_.data());

        std::ostringstream stream;
        stream << std::hex << std::setfill('0');
        for (const auto word : state_) stream << std::setw(8) << word;
        return stream.str();
    }

private:
    static constexpr std::array<std::uint32_t, 64> constants_{{
        0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U,
        0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
        0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
        0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
        0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU,
        0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
        0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
        0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
        0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
        0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
        0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U,
        0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
        0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U,
        0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
        0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
        0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
    }};

    static std::uint32_t rotateRight(std::uint32_t value, unsigned shift) noexcept {
        return (value >> shift) | (value << (32U - shift));
    }

    void transform(const std::uint8_t* block) noexcept {
        std::array<std::uint32_t, 64> words{};
        for (std::size_t index = 0; index < 16; ++index) {
            const auto offset = index * 4U;
            words[index] = (static_cast<std::uint32_t>(block[offset]) << 24U) |
                (static_cast<std::uint32_t>(block[offset + 1U]) << 16U) |
                (static_cast<std::uint32_t>(block[offset + 2U]) << 8U) |
                static_cast<std::uint32_t>(block[offset + 3U]);
        }
        for (std::size_t index = 16; index < words.size(); ++index) {
            const auto s0 = rotateRight(words[index - 15U], 7U) ^
                rotateRight(words[index - 15U], 18U) ^
                (words[index - 15U] >> 3U);
            const auto s1 = rotateRight(words[index - 2U], 17U) ^
                rotateRight(words[index - 2U], 19U) ^
                (words[index - 2U] >> 10U);
            words[index] = words[index - 16U] + s0 + words[index - 7U] + s1;
        }

        auto a = state_[0];
        auto b = state_[1];
        auto c = state_[2];
        auto d = state_[3];
        auto e = state_[4];
        auto f = state_[5];
        auto g = state_[6];
        auto h = state_[7];
        for (std::size_t index = 0; index < words.size(); ++index) {
            const auto sum1 = rotateRight(e, 6U) ^ rotateRight(e, 11U) ^ rotateRight(e, 25U);
            const auto choose = (e & f) ^ (~e & g);
            const auto temporary1 = h + sum1 + choose + constants_[index] + words[index];
            const auto sum0 = rotateRight(a, 2U) ^ rotateRight(a, 13U) ^ rotateRight(a, 22U);
            const auto majority = (a & b) ^ (a & c) ^ (b & c);
            const auto temporary2 = sum0 + majority;
            h = g;
            g = f;
            f = e;
            e = d + temporary1;
            d = c;
            c = b;
            b = a;
            a = temporary1 + temporary2;
        }
        state_[0] += a;
        state_[1] += b;
        state_[2] += c;
        state_[3] += d;
        state_[4] += e;
        state_[5] += f;
        state_[6] += g;
        state_[7] += h;
    }

    std::array<std::uint32_t, 8> state_{{
        0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
        0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U,
    }};
    std::array<std::uint8_t, 64> buffer_{};
    std::size_t buffer_size_{};
    std::uint64_t total_bytes_{};
};

bool setCanonicalControls(tidepit::Core& core) {
    const std::array<std::pair<tidepit::SemanticAction, float>, 10> controls{{
        {tidepit::SemanticAction::set_stage_1, .18f},
        {tidepit::SemanticAction::set_stage_2, .52f},
        {tidepit::SemanticAction::set_stage_3, .83f},
        {tidepit::SemanticAction::set_stage_4, .34f},
        {tidepit::SemanticAction::set_rate, .55f},
        {tidepit::SemanticAction::set_memory, .78f},
        {tidepit::SemanticAction::set_material, .47f},
        {tidepit::SemanticAction::set_position, .31f},
        {tidepit::SemanticAction::set_fx_a, .42f},
        {tidepit::SemanticAction::set_fx_b, .58f},
    }};
    for (const auto& [action, value] : controls) {
        if (!core.setControlNormalized(action, static_cast<double>(value))) return false;
    }
    // Keep the oracle independent from any host-owned startup policy. The
    // normalized value 2/3 maps exactly to the bound MIDI root note 60.
    return core.setControlNormalized(
        tidepit::SemanticAction::set_root,
        2.0 / 3.0
    ) && core.snapshot().controls.root_note == 60;
}

}  // namespace

int main() {
    constexpr std::size_t block_count = 12000;
    constexpr std::size_t expected_bytes = 1536000;
    constexpr std::int64_t expected_peak = 39182832;
    constexpr double expected_rms = 14011444.589680206;
    [[maybe_unused]] constexpr const char* expected_sha =
        "39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b";

    tidepit::Core core;
    if (!core.prepare(48000.0, 16) || !setCanonicalControls(core)) {
        std::cerr << "failed to prepare canonical Tide Pit reference\n";
        return 1;
    }

    Sha256 sha;
    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    std::int64_t peak = 0;
    long double sum_squares = 0.0L;
    std::size_t bytes = 0;
    for (std::size_t block = 0; block < block_count; ++block) {
        const auto report = core.processQ27(left.data(), right.data(), 16);
        if (report.events_dropped != 0) return 2;
        for (const auto* channel : {&left, &right}) {
            for (const auto sample : *channel) {
                sha.updateLittleEndian(sample);
                bytes += sizeof(sample);
                peak = std::max<std::int64_t>(
                    peak,
                    std::llabs(static_cast<long long>(sample))
                );
                const auto precise = static_cast<long double>(sample);
                sum_squares += precise * precise;
            }
        }
        // Exercise every behavior-neutral state getter while proving that the
        // canonical output stream remains unchanged.
        if ((block & 255U) == 0U && !core.snapshot().prepared) return 3;
    }

    const auto digest = sha.finish();
    const auto rms = static_cast<double>(std::sqrt(
        sum_squares / static_cast<long double>(block_count * 32U)
    ));
    bool passed = bytes == expected_bytes && peak == expected_peak &&
        std::abs(rms - expected_rms) < 1.0e-3;
#if defined(__APPLE__) && defined(__clang__)
    passed = passed && digest == expected_sha;
#endif
    if (!passed) {
        std::cerr << std::setprecision(17)
                  << "canonical mismatch: bytes=" << bytes
                  << " sha=" << digest
                  << " peak=" << peak
                  << " rms=" << rms << '\n';
        return 1;
    }
    std::cout << std::setprecision(17)
              << "canonical Tide Pit reference passed: bytes=" << bytes
              << " sha=" << digest
              << " peak=" << peak
              << " rms=" << rms << '\n';
    return 0;
}
