#pragma once

#include "cinderwheel/core.hpp"

#include <array>
#include <string_view>

namespace cinderwheel {

struct ButtonPresentation {
    std::string_view label;
    std::string_view value;
    bool active{};
};

[[nodiscard]] std::array<double, 16> encoderPresentation(
    const StateSnapshot& snapshot
) noexcept;

[[nodiscard]] ButtonPresentation buttonPresentation(
    ControlId id,
    const StateSnapshot& snapshot
) noexcept;

}  // namespace cinderwheel
