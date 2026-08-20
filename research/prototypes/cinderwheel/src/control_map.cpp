#include "cinderwheel/control_map.hpp"

#include <algorithm>
#include <cmath>

namespace cinderwheel {

const EncoderDescriptor* encoderDescriptor(std::uint8_t cc) noexcept {
    const auto match = std::find_if(
        kLaunchControl3Encoders.begin(),
        kLaunchControl3Encoders.end(),
        [cc](const auto& descriptor) { return descriptor.cc == cc; }
    );
    return match == kLaunchControl3Encoders.end() ? nullptr : &*match;
}

const ButtonDescriptor* buttonDescriptor(std::uint8_t cc) noexcept {
    const auto match = std::find_if(
        kLaunchControl3Buttons.begin(),
        kLaunchControl3Buttons.end(),
        [cc](const auto& descriptor) { return descriptor.cc == cc; }
    );
    return match == kLaunchControl3Buttons.end() ? nullptr : &*match;
}

double normalizedFromMidi(std::uint8_t value) noexcept {
    return static_cast<double>(value) / 127.0;
}

double rateHzFromMidi(std::uint8_t value) noexcept {
    return 0.08 * std::pow(75.0, normalizedFromMidi(value));
}

std::int32_t rootNoteFromMidi(std::uint8_t value) noexcept {
    return 36 + static_cast<std::int32_t>(
        (static_cast<unsigned>(value) * 36U + 63U) / 127U
    );
}

std::uint8_t undertowDivisorFromMidi(std::uint8_t value) noexcept {
    return value == 0
        ? 0
        : static_cast<std::uint8_t>(
            1U + ((static_cast<unsigned>(value) - 1U) * 16U) / 127U
        );
}

std::uint8_t pulseDivideFromMidi(std::uint8_t value) noexcept {
    return static_cast<std::uint8_t>(
        1U + (static_cast<unsigned>(value) * 15U + 63U) / 127U
    );
}

}  // namespace cinderwheel
