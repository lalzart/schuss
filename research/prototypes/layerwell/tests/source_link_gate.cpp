#include "schuss/generative_drum_machine/control_map.hpp"
#include "schuss/generative_drum_machine/core.hpp"
#include "tidepit/control_map.hpp"
#include "tidepit/core.hpp"

#include <array>
#include <cstdint>

int main() {
    tidepit::Core tide;
    if (!tide.prepare(48000.0, 16U)) {
        return 1;
    }

    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    const auto tide_report = tide.processQ27(left.data(), right.data(), 16U);
    if (tide_report.events_dropped != 0U || tide.snapshot().absolute_sample != 16U) {
        return 2;
    }

    namespace drums = schuss::generative_drum_machine;
    drums::StreamingEngine drum_engine{0x4C415952U};
    auto drum_controls = drums::desktopAuditionControls();
    drums::StreamingProcessReport drum_report{};
    if (!drum_engine.process(
            drum_controls,
            0U,
            left.data(),
            right.data(),
            left.size(),
            &drum_report)) {
        return 3;
    }
    if (drum_engine.absoluteFrame() != 16U) {
        return 4;
    }

    const auto tide_map = tidepit::mapMidiCc(16U, 20U, 64U);
    const auto drum_map = drums::mapMidiCc(16U, 20U, 64U);
    return tide_map.accepted() && drum_map.accepted() ? 0 : 5;
}
