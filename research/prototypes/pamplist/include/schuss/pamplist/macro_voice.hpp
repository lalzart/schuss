#pragma once

#include <array>
#include <cstdint>
#include <memory>

namespace schuss::pamplist {

inline constexpr std::size_t kMacroVoiceQuantumFrames = 16U;

struct MacroVoiceControls final {
    bool trigger{};
    std::uint8_t engine{};
    float note{48.0F};
    float harmonics{0.5F};
    float timbre{0.5F};
    float morph{0.5F};
    float decay{0.5F};
    float lpg_colour{0.5F};
    float level{0.8F};
};

// One exact, authenticated Ksoloti Extended Macro Voice source instance. The
// implementation is hidden so configured source bytes never become a public
// include dependency of Pamplist consumers.
class MacroVoice final {
public:
    explicit MacroVoice(std::uint32_t seed);
    ~MacroVoice();

    MacroVoice(const MacroVoice&) = delete;
    MacroVoice& operator=(const MacroVoice&) = delete;
    MacroVoice(MacroVoice&&) noexcept;
    MacroVoice& operator=(MacroVoice&&) noexcept;

    void reset(std::uint32_t seed) noexcept;

    void process(
        const MacroVoiceControls& controls,
        std::array<std::int32_t, kMacroVoiceQuantumFrames>& main_q27,
        std::array<std::int32_t, kMacroVoiceQuantumFrames>& auxiliary_q27) noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}  // namespace schuss::pamplist
