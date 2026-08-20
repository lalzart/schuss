#pragma once

#include <array>
#include <cstdint>
#include <string_view>

namespace cinderwheel {

enum class ControlId : std::uint8_t {
    wave_1,
    wave_2,
    wave_3,
    wave_4,
    rate,
    memory,
    body,
    position,
    fx_a,
    fx_b,
    root,
    undertow,
    pulse_divide,
    wake,
    structure,
    ember,
    source_scale,
    mutate,
    lock,
    freeze,
    fx_mode,
    wave_target,
    bloom,
    reset_panic,
};

enum class ControlShape : std::uint8_t {
    continuous,
    stepped,
    momentary,
};

struct EncoderDescriptor {
    ControlId id;
    std::uint8_t cc;
    std::string_view physical_control;
    std::string_view oled_label;
    std::string_view semantic_key;
    ControlShape shape;
    double default_normalized;
};

struct ButtonDescriptor {
    ControlId id;
    std::uint8_t cc;
    std::string_view physical_control;
    std::string_view oled_label;
    std::string_view semantic_key;
    std::uint32_t hold_threshold_ms;
};

inline constexpr std::array<EncoderDescriptor, 16> kLaunchControl3Encoders{{
    {ControlId::wave_1, 20, "top-1", "WAVE1", "wave-1", ControlShape::continuous, 0.20},
    {ControlId::wave_2, 21, "top-2", "WAVE2", "wave-2", ControlShape::continuous, 0.70},
    {ControlId::wave_3, 22, "top-3", "WAVE3", "wave-3", ControlShape::continuous, 0.35},
    {ControlId::wave_4, 23, "top-4", "WAVE4", "wave-4", ControlShape::continuous, 0.85},
    {ControlId::rate, 24, "top-5", "RATE", "rate", ControlShape::continuous, 0.533104},
    {ControlId::memory, 25, "top-6", "MEMORY", "memory", ControlShape::continuous, 0.65},
    {ControlId::body, 26, "top-7", "BODY", "body", ControlShape::continuous, 0.55},
    {ControlId::position, 27, "top-8", "POSITION", "position", ControlShape::continuous, 0.35},
    {ControlId::fx_a, 28, "bottom-1", "FX-A", "fx-a", ControlShape::continuous, 0.50},
    {ControlId::fx_b, 29, "bottom-2", "FX-B", "fx-b", ControlShape::continuous, 0.25},
    {ControlId::root, 30, "bottom-3", "ROOT", "root", ControlShape::stepped, 0.333333},
    {ControlId::undertow, 31, "bottom-4", "UNDERTOW", "undertow", ControlShape::stepped, 0.0},
    {ControlId::pulse_divide, 32, "bottom-5", "PULSE DIV", "pulse-divide", ControlShape::stepped, 0.0},
    {ControlId::wake, 33, "bottom-6", "WAKE", "wake", ControlShape::continuous, 0.0},
    {ControlId::structure, 34, "bottom-7", "STRUCTURE", "structure", ControlShape::continuous, 0.50},
    {ControlId::ember, 35, "bottom-8", "EMBER", "ember", ControlShape::continuous, 0.0},
}};

inline constexpr std::array<ButtonDescriptor, 8> kLaunchControl3Buttons{{
    {ControlId::source_scale, 40, "button-1", "SOURCE", "source-scale", 600},
    {ControlId::mutate, 41, "button-2", "MUTATE", "mutate", 0},
    {ControlId::lock, 42, "button-3", "LOCK", "lock", 0},
    {ControlId::freeze, 43, "button-4", "FREEZE", "freeze", 0},
    {ControlId::fx_mode, 44, "button-5", "FX MODE", "fx-mode", 0},
    {ControlId::wave_target, 45, "button-6", "TARGET", "wave-target", 0},
    {ControlId::bloom, 46, "button-7", "BLOOM", "bloom", 0},
    {ControlId::reset_panic, 47, "button-8", "RESET", "reset-panic", 1200},
}};

const EncoderDescriptor* encoderDescriptor(std::uint8_t cc) noexcept;
const ButtonDescriptor* buttonDescriptor(std::uint8_t cc) noexcept;
double normalizedFromMidi(std::uint8_t value) noexcept;
double rateHzFromMidi(std::uint8_t value) noexcept;
std::int32_t rootNoteFromMidi(std::uint8_t value) noexcept;
std::uint8_t undertowDivisorFromMidi(std::uint8_t value) noexcept;
std::uint8_t pulseDivideFromMidi(std::uint8_t value) noexcept;

}  // namespace cinderwheel
