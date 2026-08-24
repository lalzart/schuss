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
constexpr std::uint32_t kFallbackRandomSeed = UINT32_C(0x21);

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
    std::uint32_t random_state{kFallbackRandomSeed};

    explicit Impl(std::uint32_t seed) noexcept { reconstruct(seed); }

    ~Impl() {
        if (voice != nullptr) voice->~KsolotiExtendedMacroVoiceDSP();
    }

    void reconstruct(std::uint32_t seed) noexcept {
        if (voice != nullptr) voice->~KsolotiExtendedMacroVoiceDSP();
        plaits_stmlib::Random::Seed(seed == 0U ? kFallbackRandomSeed : seed);
        voice = new (storage) KsolotiExtendedMacroVoiceDSP();
        voice->Init();
        random_state = plaits_stmlib::Random::state();
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
    // The authenticated source uses one process-global RNG. Context-switch it
    // at this adapter boundary so every Pamplist lane owns its random history.
    plaits_stmlib::Random::Seed(impl_->random_state);
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
    impl_->random_state = plaits_stmlib::Random::state();
}

std::uint32_t MacroVoice::randomState() const noexcept {
    return impl_->random_state;
}

}  // namespace schuss::pamplist
