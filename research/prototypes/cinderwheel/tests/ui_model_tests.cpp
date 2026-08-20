#include "cinderwheel/ui_model.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>

namespace {

int failures = 0;
#define CHECK(condition) do { if (!(condition)) { \
    std::cerr << __FILE__ << ':' << __LINE__ << ": " #condition "\n"; ++failures; \
} } while (false)

bool close(double left, double right, double tolerance = 1.0e-9) {
    return std::abs(left - right) <= tolerance;
}

}  // namespace

int main() {
    cinderwheel::StateSnapshot state{};
    state.stage_values = {{0.0f, 0.25f, 0.5f, 1.0f}};
    state.rate_hz = 6.0;
    state.memory = 0.65;
    state.body = 0.55;
    state.position = 0.35;
    state.fx_a = 0.5;
    state.fx_b = 0.25;
    state.root_note = 72;
    state.undertow_divisor = 16;
    state.pulse_divide = 16;
    state.wake = 1.0;
    state.structure = 0.5;
    state.ember = 0.75;
    const auto values = cinderwheel::encoderPresentation(state);
    CHECK(close(values[0], 0.0));
    CHECK(close(values[3], 127.0));
    CHECK(close(values[4], 127.0));
    CHECK(close(values[5], 0.65 * 127.0));
    CHECK(close(values[10], 127.0));
    CHECK(close(values[12], 127.0));
    CHECK(close(values[15], 0.75 * 127.0));

    state.locked = true;
    state.frozen = true;
    state.panic_latched = true;
    CHECK(cinderwheel::buttonPresentation(cinderwheel::ControlId::lock, state).active);
    CHECK(cinderwheel::buttonPresentation(cinderwheel::ControlId::freeze, state).active);
    CHECK(cinderwheel::buttonPresentation(cinderwheel::ControlId::reset_panic, state).active);
    return failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
