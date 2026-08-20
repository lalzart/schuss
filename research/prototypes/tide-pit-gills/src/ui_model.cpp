#include "tidepit/ui_model.hpp"

#include <algorithm>
#include <cmath>

namespace tidepit {

ButtonPresentation buttonPresentation(
    ControlId id,
    const Snapshot& snapshot,
    bool mutate_feedback
) noexcept {
    switch (id) {
        case ControlId::source_next:
            return {"SOURCE", sourceName(snapshot.source), false};
        case ControlId::mutate:
            return {"MUTATE", mutate_feedback ? "DONE" : "READY", mutate_feedback};
        case ControlId::lock_toggle:
            return {"LOCK", snapshot.locked ? "ON" : "OFF", snapshot.locked};
        case ControlId::capture_toggle:
            return {"FREEZE", snapshot.captured ? "ON" : "OFF", snapshot.captured};
        case ControlId::effect_next:
            return {"FX MODE", effectName(snapshot.effect), false};
        case ControlId::target_next:
            return {"TARGET", targetName(snapshot.target), false};
        case ControlId::scale_next:
            return {"SCALE", scaleName(snapshot.scale), false};
        case ControlId::unassigned:
            return {"UNASSIGNED", "--", false};
        default:
            return {"CONTROL", "--", false};
    }
}

void ScopeAccumulator::reset() noexcept {
    frame_ = ScopeFrame{};
    write_index_ = 0;
    next_generation_ = 1;
}

const ScopeFrame* ScopeAccumulator::pushSample(float left, float right) noexcept {
    if (write_index_ == 0) {
        frame_.sample_count = 0;
        frame_.peak_left = 0.0f;
        frame_.peak_right = 0.0f;
    }
    const auto safe_left = std::isfinite(left) ? left : 0.0f;
    const auto safe_right = std::isfinite(right) ? right : 0.0f;
    frame_.left[write_index_] = safe_left;
    frame_.right[write_index_] = safe_right;
    frame_.peak_left = std::max(frame_.peak_left, std::abs(safe_left));
    frame_.peak_right = std::max(frame_.peak_right, std::abs(safe_right));
    ++write_index_;
    if (write_index_ != kScopeFrameSamples) return nullptr;

    frame_.sample_count = kScopeFrameSamples;
    frame_.generation = next_generation_++;
    write_index_ = 0;
    return &frame_;
}

}  // namespace tidepit
