#include "layerwell/source_adapters.hpp"

#include <array>
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

}  // namespace

int main() {
    layerwell::SourceRack rack;
    expect(rack.prepare(layerwell::kSampleRate, layerwell::kMaximumBlockFrames),
        "source rack prepares");

    const auto tide_before = rack.projection(layerwell::SourceId::tide_pit);
    expect(tide_before.encoder_assigned[0], "Tide encoder 1 is assigned");
    expect(!tide_before.encoder_assigned[15], "Tide encoder 16 is unassigned");
    expect(rack.applyRelativeEncoder(
               layerwell::SourceId::tide_pit, 0U, 65U, 1U)
            == layerwell::SourceControlStatus::accepted,
        "Tide relative encoder terminates at source reducer");
    const auto tide_after = rack.projection(layerwell::SourceId::tide_pit);
    expect(tide_after.encoder_values[0] == tide_before.encoder_values[0] + 1U,
        "Tide accepted projection advances one step");
    expect(rack.applyRelativeEncoder(
               layerwell::SourceId::tide_pit, 15U, 65U, 2U)
            == layerwell::SourceControlStatus::unassigned,
        "Tide unassigned slot remains explicit");

    std::array<std::int32_t, 16> left{};
    std::array<std::int32_t, 16> right{};
    expect(rack.render(layerwell::SourceId::tide_pit,
               left.data(), right.data(), 16U),
        "Tide renders through public Core");
    const auto tide_frames = rack.projection(layerwell::SourceId::tide_pit).processed_frames;
    expect(tide_frames == 16U, "Tide advances selected frames");

    expect(rack.render(layerwell::SourceId::generative_drums,
               left.data(), right.data(), 16U),
        "drums render through public streaming Core");
    expect(rack.projection(layerwell::SourceId::tide_pit).processed_frames == tide_frames,
        "inactive Tide source does not advance");
    expect(rack.projection(layerwell::SourceId::generative_drums).processed_frames == 16U,
        "selected drum source advances");

    expect(rack.applyRelativeEncoder(
               layerwell::SourceId::generative_drums, 8U, 65U, 3U)
            == layerwell::SourceControlStatus::inactive,
        "drum shaper encoder is inactive before lane selection");
    expect(rack.applyButton(
               layerwell::SourceId::generative_drums, 0U, 127U, 4U)
            == layerwell::SourceControlStatus::accepted,
        "drum lane button selects shaping through source reducer");
    expect(rack.applyRelativeEncoder(
               layerwell::SourceId::generative_drums, 8U, 65U, 5U)
            == layerwell::SourceControlStatus::accepted,
        "drum shaper encoder becomes accepted after lane selection");
    expect(rack.applyButton(
               layerwell::SourceId::generative_drums, 0U, 0U, 6U)
            == layerwell::SourceControlStatus::accepted_release,
        "source action release remains explicit");

    expect(layerwell::sourceEncoderLabel(
               layerwell::SourceId::tide_pit, 0U) == "STAGE 1",
        "Tide descriptor label is reused");
    expect(layerwell::sourceButtonLabel(
               layerwell::SourceId::generative_drums, 6U) == "FILL",
        "drum descriptor label is reused");

    if (failures != 0) {
        std::cerr << failures << " source adapter test(s) failed\n";
        return 1;
    }
    std::cout << "Layerwell source adapter tests passed\n";
    return 0;
}
