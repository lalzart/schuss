#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace schuss::instrument_lab {

[[nodiscard]] std::string jsonEscape(std::string_view text);
[[nodiscard]] std::string finiteJsonNumber(double value);

class Sha256 final {
public:
    void reset() noexcept;
    void update(const std::uint8_t* data, std::size_t size) noexcept;
    [[nodiscard]] std::string finish() noexcept;

private:
    void transform(const std::uint8_t* block) noexcept;

    std::array<std::uint32_t, 8> state_{};
    std::array<std::uint8_t, 64> buffer_{};
    std::size_t buffer_size_{};
    std::uint64_t total_bytes_{};
    bool initialized_{};
};

[[nodiscard]] std::string sha256(const std::uint8_t* data, std::size_t size) noexcept;
[[nodiscard]] inline std::string sha256(std::string_view value) noexcept {
    return sha256(
        reinterpret_cast<const std::uint8_t*>(value.data()), value.size());
}

}  // namespace schuss::instrument_lab
