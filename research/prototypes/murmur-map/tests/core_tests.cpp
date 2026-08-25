#include "schuss/murmur_map/core.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <string_view>
#include <tuple>
#include <vector>

namespace mm = schuss::murmur_map;

namespace {

int failures = 0;

void expect(bool condition, std::string_view message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

struct Rendered final {
    std::vector<float> left;
    std::vector<float> right;
    std::vector<std::tuple<std::uint64_t, std::uint32_t, std::uint32_t, bool, bool>> route;
    std::vector<std::tuple<std::uint64_t, std::uint8_t, std::uint32_t, std::uint8_t>> events;
    mm::Snapshot snapshot{};
};

Rendered render(
    std::size_t block,
    std::uint64_t frames,
    mm::Controls controls,
    mm::ActionSequences actions = {},
    mm::GenerationMode mode = mm::GenerationMode::route_memory) {
    mm::Core core;
    core.setGenerationMode(mode);
    Rendered result{};
    result.left.resize(static_cast<std::size_t>(frames));
    result.right.resize(static_cast<std::size_t>(frames));
    std::array<float, mm::kMaximumBlockFrames> left{};
    std::array<float, mm::kMaximumBlockFrames> right{};
    for (std::uint64_t start = 0U; start < frames;) {
        const auto count = static_cast<std::size_t>(std::min<std::uint64_t>(block, frames - start));
        mm::ProcessReport report{};
        expect(core.process(controls, actions, left.data(), right.data(), count, &report),
            "render block accepted");
        std::copy_n(left.data(), count, result.left.begin() + static_cast<std::ptrdiff_t>(start));
        std::copy_n(right.data(), count, result.right.begin() + static_cast<std::ptrdiff_t>(start));
        for (std::size_t index = 0U; index < report.route_event_count; ++index) {
            const auto& event = report.route_events[index];
            result.route.emplace_back(
                event.absolute_frame, event.from_id, event.to_id, event.replayed, event.replaced);
        }
        for (std::size_t index = 0U; index < report.musical_event_count; ++index) {
            const auto& event = report.musical_events[index];
            result.events.emplace_back(
                event.absolute_frame, static_cast<std::uint8_t>(event.lane),
                event.pitch_waypoint_id, event.pitch_midi);
        }
        start += count;
    }
    result.snapshot = core.snapshot();
    return result;
}

}  // namespace

int main() {
    const auto defaults = mm::defaultControls();
    expect(mm::validControls(defaults), "frozen defaults validate");
    expect(defaults.waypoint_count == 4U, "four default waypoints");
    expect(defaults.memory_length == 16U, "default memory length");
    expect(defaults.scale == mm::Scale::minor_pentatonic, "default scale");
    expect(defaults.waypoints[2].lanes[1].interval_semitones == 3,
        "frozen C thread interval");

    auto invalid = defaults;
    invalid.waypoints[1].id = invalid.waypoints[0].id;
    expect(!mm::validControls(invalid), "duplicate waypoint ID rejected");
    invalid = defaults;
    invalid.waypoints[0].lanes[0].decay_ms = 39U;
    expect(!mm::validControls(invalid), "invalid lane decay rejected");

    constexpr std::uint64_t deterministic_frames = mm::kSampleRateHz * 4ULL;
    const auto block_1 = render(1U, deterministic_frames, defaults);
    const auto block_16 = render(16U, deterministic_frames, defaults);
    const auto block_511 = render(511U, deterministic_frames, defaults);
    expect(block_1.left == block_16.left && block_1.left == block_511.left,
        "left PCM is block-partition invariant");
    expect(block_1.right == block_16.right && block_1.right == block_511.right,
        "right PCM is block-partition invariant");
    expect(block_1.route == block_16.route && block_1.route == block_511.route,
        "route trace is block-partition invariant");
    expect(block_1.events == block_16.events && block_1.events == block_511.events,
        "event trace is block-partition invariant");
    expect(!block_1.events.empty(), "default render produces events");
    expect(block_1.snapshot.clamp_count == 0U, "default render does not clamp");
    for (const auto value : block_1.left) expect(std::isfinite(value), "left sample finite");
    for (const auto value : block_1.right) expect(std::isfinite(value), "right sample finite");

    auto home_controls = defaults;
    home_controls.memory_u15 = 0U;
    home_controls.memory_length = 2U;
    home_controls.home_u15 = 32767U;
    const auto home_render = render(128U, mm::kSampleRateHz * 8ULL, home_controls);
    expect(home_render.route.size() > 8U, "HOME test has route transitions");
    for (const auto& event : home_render.route) {
        expect(std::get<1>(event) != std::get<2>(event), "fresh HOME route has no self-edge");
        if (std::get<1>(event) != home_controls.waypoints[home_controls.home_index].id) {
            expect(std::get<2>(event) == home_controls.waypoints[home_controls.home_index].id,
                "HOME=1 returns every non-home fresh edge");
        }
    }

    auto silence_controls = defaults;
    silence_controls.density_u15 = 0U;
    for (std::size_t waypoint = 0U; waypoint < silence_controls.waypoint_count; ++waypoint) {
        for (auto& lane : silence_controls.waypoints[waypoint].lanes) lane.activity_u15 = 0U;
    }
    mm::ActionSequences panic{};
    panic.panic = 1U;
    const auto silence = render(64U, mm::kSampleRateHz, silence_controls, panic);
    expect(std::all_of(silence.left.begin(), silence.left.end(), [](float value) { return value == 0.0F; }),
        "Panic plus zero density is exact left silence");
    expect(std::all_of(silence.right.begin(), silence.right.end(), [](float value) { return value == 0.0F; }),
        "Panic plus zero density is exact right silence");
    expect(!silence.route.empty(), "route remains active during exact silence");

    mm::Core first{};
    const auto reset_boundary_state = first.captureState();
    std::array<float, mm::kMaximumBlockFrames> first_left{};
    std::array<float, mm::kMaximumBlockFrames> first_right{};
    mm::ProcessReport first_report{};
    expect(first.process(defaults, {}, first_left.data(), first_right.data(), 512U, &first_report),
        "first reset-boundary continuation processes");
    mm::Core recalled{};
    expect(recalled.recallState(reset_boundary_state), "valid reset-boundary state recalls");
    std::array<float, mm::kMaximumBlockFrames> recalled_left{};
    std::array<float, mm::kMaximumBlockFrames> recalled_right{};
    mm::ProcessReport recalled_report{};
    expect(recalled.process(defaults, {}, recalled_left.data(), recalled_right.data(), 512U, &recalled_report),
        "recalled continuation processes");
    expect(first_left == recalled_left && first_right == recalled_right,
        "reset-boundary recall restores exact PCM continuation");

    auto bad_state = reset_boundary_state;
    bad_state.random_streams[0] &= ~1ULL;
    const auto before_bad_recall = recalled.captureState();
    expect(!recalled.recallState(bad_state), "invalid random stream state rejected");
    expect(mm::sameControls(recalled.captureState().controls, before_bad_recall.controls),
        "invalid recall preserves accepted controls");

    if (failures != 0) {
        std::cerr << failures << " Murmur Map Core test(s) failed\n";
        return 1;
    }
    std::cout << "Murmur Map Core tests passed\n";
    return 0;
}
