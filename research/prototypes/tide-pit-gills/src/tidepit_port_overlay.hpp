#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <math.h>

#include "port_overrides/stmlib/utils/random.h"

#ifndef BUFSIZE
#define BUFSIZE 16
#endif

// The exact upstream source calls this Ksoloti service without a namespace.
// Core preparation installs a thread-local, bounded arena context around Init.
void* sdram_malloc(std::size_t bytes) noexcept;

// Load the complete dependency closure before the narrow access overlay. The
// access-specifier macro below therefore cannot rewrite Mutable Instruments or
// tidepit_voice classes; their include guards are already established.
#include "clouds/dsp/audio_buffer.h"
#include "clouds/dsp/grain.h"
#include "clouds/dsp/parameters.h"
#include "clouds/resources.h"
#include "stmlib/dsp/rsqrt.h"
#include "stmlib/dsp/units.h"
#include "tidepit_voice_ported.h"

// Keep the authoritative source bytes immutable. This one-TU overlay exposes
// Tide Pit Instrument state for behavior-neutral getters and renames the
// source's unscoped EffectMode type so it can coexist with the public strongly
// typed API. Mutable dependency access specifiers remain untouched above.
#define EffectMode PortedSourceEffectMode
#if defined(__clang__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wkeyword-macro"
#endif
#define private public
#include "../third_party/tidepit/upstream/tidepit_dsp.h"
#undef private
#if defined(__clang__)
#pragma clang diagnostic pop
#endif
#undef EffectMode

namespace tidepit::port {

inline std::uint8_t sourceMode(const Instrument& instrument) noexcept {
    return instrument.oscillator_mode_;
}

inline std::uint8_t scaleMode(const Instrument& instrument) noexcept {
    return instrument.scale_;
}

inline std::uint8_t effectMode(const Instrument& instrument) noexcept {
    return instrument.effect_mode_;
}

inline float effectCrossfade(const Instrument& instrument) noexcept {
    return instrument.effect_crossfade_;
}

inline std::uint8_t waveTarget(const Instrument& instrument) noexcept {
    return instrument.wave_destination_;
}

inline bool locked(const Instrument& instrument) noexcept {
    return instrument.locked_;
}

inline bool captured(const Instrument& instrument) noexcept {
    return instrument.captured_;
}

inline float effectParameter(
    const Instrument& instrument,
    std::size_t mode,
    std::size_t parameter
) noexcept {
    return parameter == 0
        ? instrument.effect_parameter_a_[mode]
        : instrument.effect_parameter_b_[mode];
}

inline bool effectPickup(
    const Instrument& instrument,
    std::size_t mode,
    std::size_t parameter
) noexcept {
    return parameter == 0
        ? instrument.effect_parameter_pickup_a_[mode]
        : instrument.effect_parameter_pickup_b_[mode];
}

inline std::int8_t mutation(const Instrument& instrument, std::size_t index) noexcept {
    return instrument.mutation_[index];
}

inline std::uint8_t sympatheticDivision(const Instrument& instrument) noexcept {
    return instrument.sub_division_;
}

inline std::int32_t recordWriteHead(const Instrument& instrument) noexcept {
    return instrument.record_buffer_.head();
}

inline const char* displayLine(const Instrument& instrument, std::size_t index) noexcept {
    switch (index) {
        case 0: return instrument.line1_;
        case 1: return instrument.line2_;
        case 2: return instrument.line3_;
        default: return instrument.line4_;
    }
}

}  // namespace tidepit::port
