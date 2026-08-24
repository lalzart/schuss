#include "schuss/pamplist/macro_voice.hpp"

#include "macro_voice_dsp.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <new>
#include <utility>

namespace schuss::pamplist {
namespace {

constexpr std::int32_t kQ27One = INT32_C(1) << 27;
constexpr std::int32_t kSemitoneOneQ21 = INT32_C(1) << 21;

[[nodiscard]] std::int32_t unitQ27(float value) noexcept {
    const auto bounded = std::clamp(value, 0.0F, 1.0F);
    return static_cast<std::int32_t>(
        std::llround(static_cast<double>(bounded) * kQ27One));
}

[[nodiscard]] std::int32_t pitchQ21(float note) noexcept {
    const auto semitones = std::clamp(note, 24.0F, 96.0F) - 64.0F;
    return static_cast<std::int32_t>(
        std::llround(static_cast<double>(semitones) * kSemitoneOneQ21));
}

}  // namespace

struct MacroVoice::Impl final {
    alignas(KsolotiExtendedMacroVoiceDSP)
        unsigned char storage[sizeof(KsolotiExtendedMacroVoiceDSP)]{};
    KsolotiExtendedMacroVoiceDSP* voice{};

    explicit Impl(std::uint32_t seed) noexcept { reconstruct(seed); }

    ~Impl() {
        if (voice != nullptr) voice->~KsolotiExtendedMacroVoiceDSP();
    }

    void reconstruct(std::uint32_t seed) noexcept {
        if (voice != nullptr) voice->~KsolotiExtendedMacroVoiceDSP();
        plaits_stmlib::Random::Seed(seed);
        voice = new (storage) KsolotiExtendedMacroVoiceDSP();
        voice->Init();
    }
};

MacroVoice::MacroVoice(std::uint32_t seed)
    : impl_(std::make_unique<Impl>(seed)) {}

MacroVoice::~MacroVoice() = default;
MacroVoice::MacroVoice(MacroVoice&&) noexcept = default;
MacroVoice& MacroVoice::operator=(MacroVoice&&) noexcept = default;

void MacroVoice::reset(std::uint32_t seed) noexcept {
    impl_->reconstruct(seed);
}

void MacroVoice::process(
    const MacroVoiceControls& controls,
    std::array<std::int32_t, kMacroVoiceQuantumFrames>& main_q27,
    std::array<std::int32_t, kMacroVoiceQuantumFrames>& auxiliary_q27) noexcept {
    impl_->voice->Process(
        controls.trigger ? 1 : 0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        static_cast<std::int32_t>(std::min<std::uint8_t>(controls.engine, 23U)),
        pitchQ21(controls.note),
        unitQ27(controls.harmonics),
        unitQ27(controls.timbre),
        unitQ27(controls.morph),
        0,
        0,
        0,
        unitQ27(controls.decay),
        unitQ27(controls.lpg_colour),
        0,
        0,
        main_q27.data(),
        auxiliary_q27.data(),
        static_cast<int>(kMacroVoiceQuantumFrames));
}

}  // namespace schuss::pamplist
