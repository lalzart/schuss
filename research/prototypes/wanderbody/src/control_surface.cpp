#include "wanderbody/control_surface.hpp"

namespace wanderbody {

const std::array<ControlDescriptor, kControlDescriptorCount>&
controlDescriptors() noexcept {
    static constexpr std::array<ControlDescriptor, kControlDescriptorCount> descriptors{{
        {"external", "External", ControlKind::continuous, 0.85, 0.0, 1.0},
        {"internal", "Internal", ControlKind::continuous, 0.25, 0.0, 1.0},
        {"anchor", "Anchor", ControlKind::continuous, 0.55, 0.0, 1.0},
        {"field", "Field", ControlKind::continuous, 0.22, 0.0, 1.0},
        {"motion", "Motion", ControlKind::categorical, 0.0, 0.0, 1.0},
        {"wander", "Wander", ControlKind::continuous, 0.35, 0.0, 1.0},
        {"recurrence", "Recurrence", ControlKind::categorical, 0.0, 0.0, 3.0},
        {"mutation", "Mutation", ControlKind::continuous, 0.30, 0.0, 1.0},
        {"fragment", "Fragment", ControlKind::continuous, 0.38, 0.0, 1.0},
        {"energy", "Energy", ControlKind::continuous, 0.42, 0.0, 1.0},
        {"body", "Body", ControlKind::continuous, 0.28, 0.0, 1.0},
        {"structure", "Structure", ControlKind::continuous, 0.42, 0.0, 1.0},
        {"brightness", "Brightness", ControlKind::continuous, 0.50, 0.0, 1.0},
        {"damping", "Damping", ControlKind::continuous, 0.48, 0.0, 1.0},
        {"position", "Position", ControlKind::continuous, 0.33, 0.0, 1.0},
        {"dry", "Dry", ControlKind::continuous, 0.55, 0.0, 1.0},
        {"memory", "Memory", ControlKind::continuous, 0.72, 0.0, 1.0},
        {"freeze", "Freeze", ControlKind::action, 0.0, 0.0, 1.0},
        {"clear", "Clear", ControlKind::action, 0.0, 0.0, 1.0},
        {"reset", "Reset", ControlKind::action, 0.0, 0.0, 1.0},
        {"panic", "Panic", ControlKind::action, 0.0, 0.0, 1.0},
    }};
    return descriptors;
}

}  // namespace wanderbody
