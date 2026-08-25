#include "layerwell/source_adapters.hpp"

#include "schuss/pamplist/ui_model.hpp"
#include "tidepit/control_map.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <string>

namespace {

int failures = 0;

void expect(bool condition, const std::string& message) {
    if (condition) return;
    std::cerr << "FAIL: " << message << '\n';
    ++failures;
}

void testTidePit(layerwell::SourceRack& rack) {
    const auto before = rack.projection(layerwell::SourceId::tide_pit);
    expect(before.encoder_assigned[0], "Tide encoder 1 is assigned");
    expect(!before.encoder_assigned[15], "Tide encoder 16 position is explicitly unassigned");
    for (std::size_t slot = 0U; slot < before.encoder_labels.size(); ++slot) {
        expect(!before.encoder_labels[slot].empty(),
            "every Tide encoder position has an accepted label");
    }
    for (std::size_t slot = 0U; slot < before.button_labels.size(); ++slot) {
        expect(!before.button_labels[slot].empty(),
            "every Tide button position has an accepted label");
    }
    expect(rack.applyRelativeEncoder(
               layerwell::SourceId::tide_pit, 0U, 65U, 1U)
            == layerwell::SourceControlStatus::accepted,
        "Tide relative encoder terminates at source reducer");
    const auto after = rack.projection(layerwell::SourceId::tide_pit);
    expect(after.encoder_values[0] == before.encoder_values[0] + 1U,
        "Tide accepted projection advances one step");
    expect(rack.applyAbsoluteEncoder(
               layerwell::SourceId::tide_pit, 1U, 127U, 2U)
            == layerwell::SourceControlStatus::accepted,
        "Tide absolute desktop encoder terminates at source reducer");
    expect(rack.applyRelativeEncoder(
               layerwell::SourceId::tide_pit, 15U, 65U, 3U)
            == layerwell::SourceControlStatus::unassigned,
        "Tide unassigned slot remains explicit");
    expect(rack.applyButton(
               layerwell::SourceId::tide_pit, 0U, 127U, 4U)
            == layerwell::SourceControlStatus::accepted,
        "Tide source action press queues exact semantic event");
    expect(rack.applyButton(
               layerwell::SourceId::tide_pit, 0U, 0U, 5U)
            == layerwell::SourceControlStatus::accepted_release,
        "Tide action release is accepted without a duplicate Core action");

    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    for (std::size_t quantum = 0U; quantum < layerwell::kTideScopeSamples / 16U;
         ++quantum) {
        expect(rack.render(layerwell::SourceId::tide_pit,
                   left.data(), right.data(), 16U),
            "Tide renders through public Core");
    }
    const auto projected = rack.projection(layerwell::SourceId::tide_pit);
    expect(projected.processed_frames == layerwell::kTideScopeSamples,
        "Tide advances only its selected frames");
    expect(projected.panel.tide_scope.sample_count == layerwell::kTideScopeSamples,
        "Tide embedded panel receives a bounded complete scope");
    expect(projected.panel.tide_scope.generation != 0U,
        "Tide scope generation advances");
    expect(projected.panel.tide_pit.absolute_sample == projected.processed_frames,
        "Tide exact source snapshot is panel authority");
    for (const auto& line : projected.panel.tide_pit.display_lines) {
        expect(line[0] != '\0', "all four Tide display lines are projected");
    }
}

void testPamplist(layerwell::SourceRack& rack) {
    namespace pam = schuss::pamplist;
    std::array<std::int32_t, 16> main{};
    std::array<std::int32_t, 16> auxiliary{};

    auto projection = rack.projection(layerwell::SourceId::pamplist);
    const auto initial_surface = pam::surfaceModel(projection.panel.pamplist);
    expect(projection.panel.pamplist.accepted.selected_page == 0U,
        "Pamplist starts on lane one");
    expect(initial_surface.context == pam::SurfaceContext::voice,
        "Pamplist starts in Voice context");
    for (std::size_t slot = 0U; slot < 16U; ++slot) {
        const auto& model = slot < 8U
            ? initial_surface.top[slot]
            : initial_surface.bottom[slot - 8U];
        expect(projection.encoder_labels[slot] == model.label,
            "Pamplist contextual encoder label comes from exact surface model");
        expect(projection.encoder_tooltips[slot] == model.tooltip,
            "Pamplist dependency help comes from exact surface model");
    }
    for (std::size_t page = 0U; page < 8U; ++page) {
        expect(projection.button_assigned[page]
                && !projection.button_labels[page].empty(),
            "all eight Pamplist page button positions are present");
    }

    expect(rack.applyAbsoluteEncoder(
               layerwell::SourceId::pamplist, 0U, 127U, 10U)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist absolute encoder terminates at contextual reducer");
    expect(rack.render(layerwell::SourceId::pamplist,
               main.data(), auxiliary.data(), 16U),
        "Pamplist renders through public Core");
    projection = rack.projection(layerwell::SourceId::pamplist);
    expect(projection.panel.pamplist.accepted.voices[0].engine == 23U,
        "Pamplist accepted model value follows exact CC mapping");

    expect(rack.applyButton(
               layerwell::SourceId::pamplist, 1U, 127U, 11U)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist page press terminates at existing controller reducer");
    expect(rack.applyButton(
               layerwell::SourceId::pamplist, 1U, 0U, 12U)
            == layerwell::SourceControlStatus::accepted_release,
        "Pamplist page release remains explicit");
    expect(rack.render(layerwell::SourceId::pamplist,
               main.data(), auxiliary.data(), 16U),
        "Pamplist page change renders");
    projection = rack.projection(layerwell::SourceId::pamplist);
    expect(projection.panel.pamplist.accepted.selected_page == 1U
            && projection.button_active[1],
        "Pamplist accepted page and button projection agree");

    expect(rack.setContext(layerwell::SourceId::pamplist, 1U)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist Motion context uses existing public control state");
    expect(rack.applySurfaceValue(
               layerwell::SourceId::pamplist, 8U, 12.0, 13U)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist exact SurfaceModel value terminates at applySurfaceValue");
    expect(rack.render(layerwell::SourceId::pamplist,
               main.data(), auxiliary.data(), 16U),
        "Pamplist Motion update renders");
    projection = rack.projection(layerwell::SourceId::pamplist);
    expect(projection.panel.pamplist.accepted.lane_control_mode
                == pam::LaneControlMode::motion,
        "Pamplist accepted Motion context is panel authority");
    expect(projection.panel.pamplist.accepted.lanes[1].rate_index == 12U,
        "Pamplist exact surface value reaches the selected lane");

    expect(rack.setContext(layerwell::SourceId::pamplist, 0U)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist Voice context is directly selectable by embedded panel");
    expect(rack.applySurfaceValue(
               layerwell::SourceId::pamplist, 1U, 72.0, 14U)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist Voice note uses exact SurfaceModel range");
    expect(rack.toggleRun(layerwell::SourceId::pamplist)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist Run Stop is available to embedded panel");
    expect(rack.clearEffect(layerwell::SourceId::pamplist)
            == layerwell::SourceControlStatus::accepted,
        "Pamplist Clear FX retains exact effect-only source action");

    for (std::uint32_t frame = 0U; frame < 2400U; frame += 16U) {
        expect(rack.render(layerwell::SourceId::pamplist,
                   main.data(), auxiliary.data(), 16U),
            "Pamplist activity render remains valid");
    }
    projection = rack.projection(layerwell::SourceId::pamplist);
    expect(projection.panel.pamplist.accepted.voices[1].note == 72.0F,
        "Pamplist accepted Voice value is projected");
    expect(!projection.panel.pamplist.accepted.running,
        "Pamplist accepted Run Stop state is projected");
    expect(projection.panel.pamplist.accepted.effect_clear_generation == 1U,
        "Pamplist accepted Clear generation is projected");
    expect(projection.panel.pamplist_impact.sample_count != 0U
            && projection.panel.pamplist_impact.generation != 0U,
        "Pamplist embedded panel receives bounded seven-lane impact history");

    std::uint64_t sequence = 100U;
    for (std::size_t page = 0U; page < pam::kPageCount; ++page) {
        expect(rack.applyButton(
                   layerwell::SourceId::pamplist, page, 127U, sequence++)
                == layerwell::SourceControlStatus::accepted,
            "every Pamplist page press terminates at the existing reducer");
        expect(rack.applyButton(
                   layerwell::SourceId::pamplist, page, 0U, sequence++)
                == layerwell::SourceControlStatus::accepted_release,
            "every Pamplist page release remains explicit");
        expect(rack.render(layerwell::SourceId::pamplist,
                   main.data(), auxiliary.data(), 16U),
            "every Pamplist page acceptance renders");

        const auto context_count = page < pam::kLaneCount ? 2U : 1U;
        for (std::size_t context = 0U; context < context_count; ++context) {
            if (page < pam::kLaneCount) {
                expect(rack.setContext(
                           layerwell::SourceId::pamplist,
                           static_cast<std::uint8_t>(context))
                        == layerwell::SourceControlStatus::accepted,
                    "every lane page accepts both Voice and Motion context");
                expect(rack.render(layerwell::SourceId::pamplist,
                           main.data(), auxiliary.data(), 16U),
                    "every Pamplist context acceptance renders");
            }

            projection = rack.projection(layerwell::SourceId::pamplist);
            const auto surface = pam::surfaceModel(projection.panel.pamplist);
            expect(projection.panel.pamplist.accepted.selected_page == page,
                "accepted Pamplist page is the embedded panel authority");
            const auto expected_context = page == pam::kGlobalPageIndex
                ? pam::SurfaceContext::global
                : (context == 0U
                    ? pam::SurfaceContext::voice
                    : pam::SurfaceContext::motion);
            expect(surface.context == expected_context,
                "accepted Pamplist context is the embedded panel authority");

            std::array<double, 16> targets{};
            for (std::size_t slot = 0U; slot < 16U; ++slot) {
                const auto& model = slot < 8U
                    ? surface.top[slot]
                    : surface.bottom[slot - 8U];
                expect(projection.encoder_labels[slot] == model.label,
                    "every Pamplist page/context label is exact");
                expect(projection.encoder_tooltips[slot] == model.tooltip,
                    "every Pamplist page/context help string is exact");
                expect(projection.encoder_assigned[slot] == model.enabled,
                    "every Pamplist page/context enabled state is exact");
                targets[slot] = model.maximum;
                const auto status = rack.applySurfaceValue(
                    layerwell::SourceId::pamplist,
                    slot,
                    targets[slot],
                    sequence++);
                expect(status == (model.enabled
                        ? layerwell::SourceControlStatus::accepted
                        : layerwell::SourceControlStatus::inactive),
                    "every Pamplist surface slot has an explicit terminus");
            }
            expect(rack.render(layerwell::SourceId::pamplist,
                       main.data(), auxiliary.data(), 16U),
                "every complete Pamplist surface edit renders");
            const auto accepted = pam::surfaceModel(
                rack.projection(layerwell::SourceId::pamplist).panel.pamplist);
            for (std::size_t slot = 0U; slot < 16U; ++slot) {
                const auto& model = slot < 8U
                    ? accepted.top[slot]
                    : accepted.bottom[slot - 8U];
                if (!model.enabled) continue;
                const auto tolerance = std::max(1.0e-6, model.interval * 0.51);
                expect(std::abs(model.value - targets[slot]) <= tolerance,
                    "every enabled Pamplist slot projects its accepted value");
            }
        }
    }
}

}  // namespace

int main() {
    layerwell::SourceRack rack;
    expect(rack.prepare(layerwell::kSampleRate, layerwell::kMaximumBlockFrames),
        "source rack prepares");
    testTidePit(rack);
    const auto tide_frames = rack.projection(
        layerwell::SourceId::tide_pit).processed_frames;
    testPamplist(rack);
    expect(rack.projection(layerwell::SourceId::tide_pit).processed_frames
            == tide_frames,
        "inactive Tide source retains state and does not advance");
    expect(layerwell::sourceEncoderLabel(
               layerwell::SourceId::tide_pit, 0U) == "STAGE 1",
        "Tide descriptor label remains reusable");
    expect(layerwell::sourceButtonLabel(
               layerwell::SourceId::pamplist, 7U) == "GLOBAL / CLEAR",
        "Pamplist page descriptor label is explicit");

    if (failures != 0) {
        std::cerr << failures << " source adapter test(s) failed\n";
        return 1;
    }
    std::cout << "Layerwell Tide Pit/Pamplist source adapter tests passed\n";
    return 0;
}
