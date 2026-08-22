#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace schuss::dsp::mutable_braids_v1 {

enum class Model : std::uint8_t {
    kick,
    snare,
    cymbal,
    sine_triangle,
    fm,
    filtered_noise,
};

class Voice final {
public:
    Voice();
    Voice(const Voice&) = delete;
    Voice& operator=(const Voice&) = delete;
    ~Voice();

    void reset();
    void reset(Model model, std::int16_t pitch, std::int16_t timbre, std::int16_t color);
    void setModel(Model model);
    void setPitch(std::int16_t pitch);
    void setParameters(std::int16_t timbre, std::int16_t color);
    void strike();
    void render(std::uint8_t* sync, std::int16_t* output, std::size_t size);

private:
    static constexpr std::size_t kOpaqueStorageBytes = 18U * 1024U;
    alignas(16) std::array<std::byte, kOpaqueStorageBytes> storage_{};
    bool constructed_{};

    void reconstruct();
};

void seedRandom(std::uint32_t seed) noexcept;

}  // namespace schuss::dsp::mutable_braids_v1
