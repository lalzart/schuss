#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace wirefall::r02 {

enum class ControlId : std::uint8_t {
    energy,
    break_depth,
    pulse,
    tick,
    root,
    color,
    width,
    edge,
    space,
    output,
    tempo,
    count,
};

enum class ActionId : std::uint8_t {
    open_press,
    open_release,
    tick_preview,
    downbeat,
    panic_press,
    panic_release,
    reset,
    unsupported,
};

struct ControlDescriptor {
    ControlId id;
    std::string_view name;
    double minimum;
    double maximum;
    double default_value;
    bool stepped;
};

inline constexpr std::array<ControlDescriptor, 11> kControlDescriptors{{
    {ControlId::energy, "ENERGY", 0.0, 1.0, 0.32, false},
    {ControlId::break_depth, "BREAK", 0.0, 1.0, 0.0, false},
    {ControlId::pulse, "PULSE", 0.0, 7.0, 0.0, true},
    {ControlId::tick, "TICK", 0.0, 1.0, 0.0, false},
    {ControlId::root, "ROOT", -12.0, 12.0, 0.0, false},
    {ControlId::color, "COLOR", 0.0, 1.0, 0.55, false},
    {ControlId::width, "WIDTH", 0.0, 1.0, 0.35, false},
    {ControlId::edge, "EDGE", 0.0, 1.0, 0.34, false},
    {ControlId::space, "SPACE", 0.0, 1.0, 0.10, false},
    {ControlId::output, "OUTPUT", 0.0, 1.0, 0.82, false},
    {ControlId::tempo, "TEMPO", 40.0, 240.0, 120.0, false},
}};

inline constexpr std::array<double, 8> kPulseRatesPerBeat{{
    0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0,
}};

inline constexpr std::array<std::string_view, 8> kPulseNames{{
    "OFF", "x1/2", "x1", "x2", "x3", "x4", "x6", "x8",
}};

[[nodiscard]] constexpr const ControlDescriptor& descriptor(ControlId id) noexcept {
    return kControlDescriptors[static_cast<std::size_t>(id)];
}

}  // namespace wirefall::r02
