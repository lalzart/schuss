#include "schuss/pamplist/control_map.hpp"
#include "schuss/pamplist/core.hpp"
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

    namespace pam = schuss::pamplist;
    pam::Core pamplist;
    const auto pam_controls = pam::defaultControls();
    pam::ProcessReport pam_report{};
    if (!pamplist.process(
            pam_controls, left.data(), right.data(), left.size(), &pam_report)) {
        return 3;
    }
    if (pamplist.snapshot().absolute_frame != 16U) {
        return 4;
    }

    const auto tide_map = tidepit::mapMidiCc(16U, 20U, 64U);
    const auto pam_map = pam::mapMidiCc(
        pam::launchControlMidiChannel(), 20, 64, 0U,
        pam::LaneControlMode::voice);
    return tide_map.accepted() && pam_map.accepted() ? 0 : 5;
}
