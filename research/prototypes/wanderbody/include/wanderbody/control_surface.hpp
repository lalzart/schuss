#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace wanderbody {

enum class ControlKind {
    continuous,
    categorical,
    action,
};

struct ControlDescriptor final {
    std::string_view id;
    std::string_view label;
    ControlKind kind;
    double default_value;
    double minimum;
    double maximum;
};

inline constexpr std::size_t kControlDescriptorCount = 21U;

[[nodiscard]] const std::array<ControlDescriptor, kControlDescriptorCount>&
controlDescriptors() noexcept;

}  // namespace wanderbody
