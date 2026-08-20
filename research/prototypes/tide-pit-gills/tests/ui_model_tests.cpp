#include "tidepit/ui_model.hpp"

#include <cmath>
#include <iostream>
#include <limits>
#include <string_view>
#include <type_traits>

namespace {

int failures = 0;

#define CHECK(condition)                                                        \
    do {                                                                        \
        if (!(condition)) {                                                     \
            std::cerr << __FILE__ << ':' << __LINE__                            \
                      << " CHECK failed: " #condition << '\n';                 \
            ++failures;                                                         \
        }                                                                       \
    } while (false)

void testButtonStateReflection() {
    tidepit::Snapshot snapshot{};

    auto presentation = tidepit::buttonPresentation(
        tidepit::ControlId::source_next,
        snapshot
    );
    CHECK(presentation.label == "SOURCE");
    CHECK(presentation.state == "REED");
    CHECK(!presentation.latched_active);

    snapshot.source = tidepit::SourceMode::fold;
    snapshot.scale = tidepit::ScaleMode::dorian;
    snapshot.effect = tidepit::EffectMode::drive;
    snapshot.target = tidepit::WaveTarget::grain;
    snapshot.locked = true;
    snapshot.captured = true;

    CHECK(tidepit::buttonPresentation(
              tidepit::ControlId::source_next,
              snapshot).state == "FOLD");
    CHECK(tidepit::buttonPresentation(
              tidepit::ControlId::scale_next,
              snapshot).state == "DOR");
    CHECK(tidepit::buttonPresentation(
              tidepit::ControlId::effect_next,
              snapshot).state == "DRIVE");
    CHECK(tidepit::buttonPresentation(
              tidepit::ControlId::target_next,
              snapshot).state == "GRAIN");

    const auto lock = tidepit::buttonPresentation(
        tidepit::ControlId::lock_toggle,
        snapshot
    );
    CHECK(lock.state == "ON");
    CHECK(lock.latched_active);

    const auto freeze = tidepit::buttonPresentation(
        tidepit::ControlId::capture_toggle,
        snapshot
    );
    CHECK(freeze.state == "ON");
    CHECK(freeze.latched_active);

    const auto mutate_ready = tidepit::buttonPresentation(
        tidepit::ControlId::mutate,
        snapshot,
        false
    );
    const auto mutate_done = tidepit::buttonPresentation(
        tidepit::ControlId::mutate,
        snapshot,
        true
    );
    CHECK(mutate_ready.state == "READY");
    CHECK(!mutate_ready.latched_active);
    CHECK(mutate_done.state == "DONE");
    CHECK(mutate_done.latched_active);
}

void testScopeAccumulator() {
    static_assert(std::is_trivially_copyable_v<tidepit::ScopeFrame>);

    tidepit::ScopeAccumulator accumulator;
    accumulator.reset();
    for (std::size_t index = 0; index + 1 < tidepit::kScopeFrameSamples; ++index) {
        CHECK(accumulator.pushSample(
                  static_cast<float>(index) * 0.001f,
                  static_cast<float>(index) * -0.002f) == nullptr);
    }

    const auto* first = accumulator.pushSample(0.75f, -0.9f);
    CHECK(first != nullptr);
    CHECK(first->sample_count == tidepit::kScopeFrameSamples);
    CHECK(first->generation == 1);
    CHECK(std::abs(first->left.back() - 0.75f) < 0.000001f);
    CHECK(std::abs(first->right.back() + 0.9f) < 0.000001f);
    CHECK(first->peak_left >= 1.0f);
    CHECK(first->peak_right >= 2.0f);

    const auto* second = static_cast<const tidepit::ScopeFrame*>(nullptr);
    for (std::size_t index = 0; index < tidepit::kScopeFrameSamples; ++index) {
        second = accumulator.pushSample(
            index == 0 ? std::numeric_limits<float>::quiet_NaN() : 0.25f,
            index == 1 ? std::numeric_limits<float>::infinity() : -0.5f
        );
    }
    CHECK(second != nullptr);
    CHECK(second->generation == 2);
    CHECK(second->left[0] == 0.0f);
    CHECK(second->right[1] == 0.0f);
    CHECK(std::abs(second->peak_left - 0.25f) < 0.000001f);
    CHECK(std::abs(second->peak_right - 0.5f) < 0.000001f);

    accumulator.reset();
    const tidepit::ScopeFrame* after_reset = nullptr;
    for (std::size_t index = 0; index < tidepit::kScopeFrameSamples; ++index) {
        after_reset = accumulator.pushSample(0.0f, 0.0f);
    }
    CHECK(after_reset != nullptr);
    CHECK(after_reset->generation == 1);
}

}  // namespace

int main() {
    testButtonStateReflection();
    testScopeAccumulator();
    if (failures != 0) {
        std::cerr << failures << " UI-model checks failed\n";
        return 1;
    }
    std::cout << "Tide Pit UI-model checks passed\n";
    return 0;
}
