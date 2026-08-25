#include "schuss/murmur_map/core.hpp"

#include "schuss/dsp/mutable_braids_v1.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <utility>

namespace schuss::murmur_map {
namespace {

namespace braids_adapter = schuss::dsp::mutable_braids_v1;

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr std::uint64_t kQuarterQ32 = std::uint64_t{1} << 32U;
constexpr std::uint64_t kTempoDenominator = 60000ULL * kSampleRateHz;
constexpr std::uint64_t kThreadStepQ32 = kQuarterQ32 / 2U;
constexpr std::uint64_t kSparkStepQ32 = kQuarterQ32 / 4U;
constexpr std::uint64_t kControlStepQ32 = kQuarterQ32 / 64U;
constexpr std::uint32_t kParameterSlewFrames = 128U;
constexpr std::uint32_t kAttackFrames = 48U;
constexpr double kEnvelopeFloor = 1.0e-7;
constexpr std::uint32_t kInvalidWaypointId = std::numeric_limits<std::uint32_t>::max();

[[nodiscard]] constexpr std::uint16_t normalizedU15(double value) noexcept {
    return static_cast<std::uint16_t>(value * 32767.0 + 0.5);
}

[[nodiscard]] constexpr std::int16_t normalizedS15(double value) noexcept {
    return static_cast<std::int16_t>(value * 32767.0 + (value >= 0.0 ? 0.5 : -0.5));
}

[[nodiscard]] constexpr std::size_t laneIndex(Lane lane) noexcept {
    return static_cast<std::size_t>(lane);
}

[[nodiscard]] bool sameLaneState(const LaneState& left, const LaneState& right) noexcept {
    return left.interval_semitones == right.interval_semitones
        && left.activity_u15 == right.activity_u15
        && left.timbre_u15 == right.timbre_u15
        && left.color_u15 == right.color_u15
        && left.decay_ms == right.decay_ms
        && left.level_milli_db == right.level_milli_db
        && left.pan_s15 == right.pan_s15;
}

[[nodiscard]] bool validLaneState(const LaneState& lane) noexcept {
    return lane.interval_semitones >= -24
        && lane.interval_semitones <= 24
        && lane.activity_u15 <= 32767U
        && lane.timbre_u15 <= 32767U
        && lane.color_u15 <= 32767U
        && lane.decay_ms >= 40U
        && lane.decay_ms <= 4000U
        && lane.level_milli_db >= -60000
        && lane.level_milli_db <= -6000
        && lane.pan_s15 >= -32767
        && lane.pan_s15 <= 32767;
}

void setLane(
    LaneState& lane,
    int interval,
    double activity,
    double timbre,
    double color,
    int decay_ms,
    int level_db,
    double pan) noexcept {
    lane.interval_semitones = static_cast<std::int16_t>(interval);
    lane.activity_u15 = normalizedU15(activity);
    lane.timbre_u15 = normalizedU15(timbre);
    lane.color_u15 = normalizedU15(color);
    lane.decay_ms = static_cast<std::uint16_t>(decay_ms);
    lane.level_milli_db = level_db * 1000;
    lane.pan_s15 = normalizedS15(pan);
}

struct Pcg32 final {
    std::uint64_t state{};
    std::uint64_t increment{1U};

    void seed(std::uint64_t init_state, std::uint64_t stream) noexcept {
        state = 0U;
        increment = (stream << 1U) | 1U;
        static_cast<void>(next());
        state += init_state;
        static_cast<void>(next());
    }

    [[nodiscard]] std::uint32_t next() noexcept {
        const auto old = state;
        state = old * 6364136223846793005ULL + increment;
        const auto shifted = static_cast<std::uint32_t>(((old >> 18U) ^ old) >> 27U);
        const auto rotation = static_cast<std::uint32_t>(old >> 59U);
        return (shifted >> rotation) | (shifted << ((0U - rotation) & 31U));
    }

    [[nodiscard]] double unit() noexcept {
        return static_cast<double>(next()) / 4294967296.0;
    }
};

[[nodiscard]] std::uint64_t splitmix64(std::uint64_t& value) noexcept {
    value += 0x9e3779b97f4a7c15ULL;
    auto mixed = value;
    mixed = (mixed ^ (mixed >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    mixed = (mixed ^ (mixed >> 27U)) * 0x94d049bb133111ebULL;
    return mixed ^ (mixed >> 31U);
}

[[nodiscard]] braids_adapter::Model adapterModel(Lane lane) noexcept {
    switch (lane) {
        case Lane::anchor: return braids_adapter::Model::sine_triangle;
        case Lane::thread: return braids_adapter::Model::fm;
        case Lane::spark: return braids_adapter::Model::filtered_noise;
    }
    return braids_adapter::Model::sine_triangle;
}

[[nodiscard]] std::uint8_t quantizePitch(int raw, Scale scale) noexcept {
    static constexpr std::array<std::array<int, 12>, 9> intervals{{
        {{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}},
        {{0, 2, 4, 5, 7, 9, 11, -1, -1, -1, -1, -1}},
        {{0, 2, 3, 5, 7, 8, 10, -1, -1, -1, -1, -1}},
        {{0, 2, 3, 5, 7, 9, 10, -1, -1, -1, -1, -1}},
        {{0, 2, 4, 5, 7, 9, 10, -1, -1, -1, -1, -1}},
        {{0, 2, 4, 7, 9, -1, -1, -1, -1, -1, -1, -1}},
        {{0, 3, 5, 7, 10, -1, -1, -1, -1, -1, -1, -1}},
        {{0, 2, 4, 6, 8, 10, -1, -1, -1, -1, -1, -1}},
        {{0, 1, 3, 4, 6, 7, 9, 10, -1, -1, -1, -1}},
    }};
    static constexpr std::array<std::size_t, 9> counts{{12U, 7U, 7U, 7U, 7U, 5U, 5U, 6U, 8U}};
    const auto scale_index = static_cast<std::size_t>(scale);
    if (scale_index >= intervals.size()) return static_cast<std::uint8_t>(std::clamp(raw, 12, 108));
    int best = 12;
    int best_distance = std::numeric_limits<int>::max();
    for (int octave = -2; octave <= 10; ++octave) {
        for (std::size_t index = 0U; index < counts[scale_index]; ++index) {
            const int candidate = octave * 12 + intervals[scale_index][index];
            if (candidate < 12 || candidate > 108) continue;
            const int distance = std::abs(candidate - raw);
            if (distance < best_distance || (distance == best_distance && candidate < best)) {
                best = candidate;
                best_distance = distance;
            }
        }
    }
    return static_cast<std::uint8_t>(best);
}

[[nodiscard]] std::uint16_t toU15(double value) noexcept {
    return static_cast<std::uint16_t>(std::clamp<long>(std::lround(value * 32767.0), 0L, 32767L));
}

[[nodiscard]] std::int16_t toS15(double value) noexcept {
    return static_cast<std::int16_t>(std::clamp<long>(std::lround(value * 32767.0), -32767L, 32767L));
}

struct SceneLane final {
    double activity{};
    double timbre{};
    double color{};
    double log_decay{std::log(0.04)};
    double level_db{-60.0};
    double pan{};
};

struct Voice final {
    braids_adapter::Voice oscillator{};
    Lane lane{Lane::anchor};
    bool active{};
    double envelope{};
    double decay_multiplier{};
    std::uint32_t attack_position{kAttackFrames};
    double level_gain{};
    double pan_left{0.7071067811865476};
    double pan_right{0.7071067811865476};
    std::array<std::int16_t, 5> decimator{};
    float last_left{};
    float last_right{};
    float bridge_left{};
    float bridge_right{};
    std::uint32_t bridge_remaining{};

    void reset(Lane next_lane) noexcept {
        lane = next_lane;
        oscillator.reset(adapterModel(lane), 48 * 128, 0, 0);
        active = false;
        envelope = 0.0;
        decay_multiplier = 0.0;
        attack_position = kAttackFrames;
        level_gain = 0.0;
        pan_left = 0.7071067811865476;
        pan_right = 0.7071067811865476;
        decimator.fill(0);
        last_left = 0.0F;
        last_right = 0.0F;
        bridge_left = 0.0F;
        bridge_right = 0.0F;
        bridge_remaining = 0U;
    }

    void trigger(const MusicalEvent& event) noexcept {
        bridge_left = last_left;
        bridge_right = last_right;
        bridge_remaining = active ? kAttackFrames : 0U;
        oscillator.setPitch(static_cast<std::int16_t>(event.pitch_midi * 128U));
        oscillator.setParameters(
            static_cast<std::int16_t>(event.timbre_u15),
            static_cast<std::int16_t>(event.color_u15));
        oscillator.strike();
        envelope = 1.0;
        decay_multiplier = std::exp(
            -1.0 / (static_cast<double>(event.decay_ms) * 0.001 * kSampleRateHz));
        attack_position = 0U;
        level_gain = std::pow(10.0, static_cast<double>(event.level_milli_db) / 20000.0);
        const double pan = static_cast<double>(event.pan_s15) / 32767.0;
        pan_left = std::cos(kPi * (pan + 1.0) / 4.0);
        pan_right = std::sin(kPi * (pan + 1.0) / 4.0);
        active = true;
    }

    [[nodiscard]] std::pair<float, float> render() noexcept {
        double mono = 0.0;
        if (active) {
            std::array<std::uint8_t, 2> sync{{0U, 0U}};
            std::array<std::int16_t, 2> samples{{0, 0}};
            oscillator.render(sync.data(), samples.data(), samples.size());
            for (const auto sample : samples) {
                for (std::size_t index = decimator.size() - 1U; index > 0U; --index) {
                    decimator[index] = decimator[index - 1U];
                }
                decimator[0] = sample;
            }
            const auto filtered =
                static_cast<std::int64_t>(decimator[0]) * 2048
                + static_cast<std::int64_t>(decimator[1]) * 8192
                + static_cast<std::int64_t>(decimator[2]) * 12288
                + static_cast<std::int64_t>(decimator[3]) * 8192
                + static_cast<std::int64_t>(decimator[4]) * 2048;
            mono = static_cast<double>(filtered) / (32768.0 * 32768.0);
            const double attack = attack_position >= kAttackFrames
                ? 1.0
                : static_cast<double>(attack_position) / kAttackFrames;
            mono *= envelope * attack * level_gain * 0.24;
            if (attack_position < kAttackFrames) ++attack_position;
            envelope *= decay_multiplier;
            if (envelope < kEnvelopeFloor) {
                envelope = 0.0;
                active = false;
            }
        }
        double left = mono * pan_left;
        double right = mono * pan_right;
        if (bridge_remaining > 0U) {
            const double bridge = static_cast<double>(bridge_remaining) / kAttackFrames;
            left += static_cast<double>(bridge_left) * bridge;
            right += static_cast<double>(bridge_right) * bridge;
            --bridge_remaining;
        }
        last_left = static_cast<float>(left);
        last_right = static_cast<float>(right);
        return {last_left, last_right};
    }
};

}  // namespace

Controls defaultControls() noexcept {
    Controls controls{};
    controls.run = true;
    controls.tempo_milli_bpm = 120000U;
    controls.travel_milli_quarters = 500U;
    controls.memory_u15 = normalizedU15(0.85);
    controls.memory_length = 16U;
    controls.roam_u15 = normalizedU15(0.55);
    controls.home_u15 = normalizedU15(0.10);
    controls.radius_u15 = normalizedU15((0.28 - 0.05) / 0.95);
    controls.density_u15 = normalizedU15(0.70);
    controls.root_midi_note = 48U;
    controls.scale = Scale::minor_pentatonic;
    controls.waypoint_count = 4U;
    controls.home_index = 0U;

    auto& a = controls.waypoints[0];
    a.id = 0U; a.x_u15 = normalizedU15(0.12); a.y_u15 = normalizedU15(0.18);
    setLane(a.lanes[0], 0, 0.85, 0.20, 0.28, 900, -12, -0.35);
    setLane(a.lanes[1], 7, 0.30, 0.25, 0.20, 240, -18, 0.15);
    setLane(a.lanes[2], -12, 0.12, 0.18, 0.22, 110, -24, -0.10);

    auto& b = controls.waypoints[1];
    b.id = 1U; b.x_u15 = normalizedU15(0.82); b.y_u15 = normalizedU15(0.16);
    setLane(b.lanes[0], 5, 0.70, 0.42, 0.55, 600, -13, -0.10);
    setLane(b.lanes[1], 12, 0.78, 0.72, 0.68, 180, -17, 0.35);
    setLane(b.lanes[2], 0, 0.25, 0.64, 0.72, 90, -22, 0.65);

    auto& c = controls.waypoints[2];
    c.id = 2U; c.x_u15 = normalizedU15(0.78); c.y_u15 = normalizedU15(0.84);
    setLane(c.lanes[0], 12, 0.60, 0.70, 0.80, 1400, -15, 0.45);
    setLane(c.lanes[1], 3, 0.58, 0.88, 0.92, 320, -18, 0.70);
    setLane(c.lanes[2], 7, 0.72, 0.82, 0.90, 160, -21, -0.55);

    auto& d = controls.waypoints[3];
    d.id = 3U; d.x_u15 = normalizedU15(0.18); d.y_u15 = normalizedU15(0.80);
    setLane(d.lanes[0], -5, 0.78, 0.32, 0.18, 750, -13, -0.55);
    setLane(d.lanes[1], 10, 0.36, 0.46, 0.30, 420, -19, -0.25);
    setLane(d.lanes[2], -7, 0.48, 0.28, 0.36, 260, -23, 0.20);
    return controls;
}

bool validControls(const Controls& controls) noexcept {
    if (controls.tempo_milli_bpm < 30000U || controls.tempo_milli_bpm > 240000U
        || controls.travel_milli_quarters < 250U || controls.travel_milli_quarters > 8000U
        || controls.memory_u15 > 32767U || controls.memory_length < 2U
        || controls.memory_length > kMaximumRouteMemory || controls.roam_u15 > 32767U
        || controls.home_u15 > 32767U || controls.radius_u15 > 32767U
        || controls.density_u15 > 32767U || controls.root_midi_note < 24U
        || controls.root_midi_note > 84U
        || static_cast<std::size_t>(controls.scale) > static_cast<std::size_t>(Scale::octatonic_half_whole)
        || controls.waypoint_count < 2U || controls.waypoint_count > kMaximumWaypoints
        || controls.home_index >= controls.waypoint_count) {
        return false;
    }
    for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
        const auto& waypoint = controls.waypoints[index];
        if (waypoint.x_u15 > 32767U || waypoint.y_u15 > 32767U) return false;
        for (std::size_t prior = 0U; prior < index; ++prior) {
            if (controls.waypoints[prior].id == waypoint.id) return false;
        }
        for (const auto& lane : waypoint.lanes) {
            if (!validLaneState(lane)) return false;
        }
    }
    return true;
}

bool sameControls(const Controls& left, const Controls& right) noexcept {
    if (left.run != right.run || left.tempo_milli_bpm != right.tempo_milli_bpm
        || left.travel_milli_quarters != right.travel_milli_quarters
        || left.memory_u15 != right.memory_u15 || left.memory_length != right.memory_length
        || left.roam_u15 != right.roam_u15 || left.home_u15 != right.home_u15
        || left.radius_u15 != right.radius_u15 || left.density_u15 != right.density_u15
        || left.root_midi_note != right.root_midi_note || left.scale != right.scale
        || left.waypoint_count != right.waypoint_count || left.home_index != right.home_index) {
        return false;
    }
    for (std::size_t index = 0U; index < left.waypoint_count; ++index) {
        const auto& a = left.waypoints[index];
        const auto& b = right.waypoints[index];
        if (a.id != b.id || a.x_u15 != b.x_u15 || a.y_u15 != b.y_u15) return false;
        for (std::size_t lane = 0U; lane < kLaneCount; ++lane) {
            if (!sameLaneState(a.lanes[lane], b.lanes[lane])) return false;
        }
    }
    return true;
}

const char* scaleName(Scale scale) noexcept {
    switch (scale) {
        case Scale::chromatic: return "Chromatic";
        case Scale::major: return "Major";
        case Scale::natural_minor: return "Natural Minor";
        case Scale::dorian: return "Dorian";
        case Scale::mixolydian: return "Mixolydian";
        case Scale::major_pentatonic: return "Major Pentatonic";
        case Scale::minor_pentatonic: return "Minor Pentatonic";
        case Scale::whole_tone: return "Whole Tone";
        case Scale::octatonic_half_whole: return "Octatonic H-W";
    }
    return "Invalid";
}

const char* laneName(Lane lane) noexcept {
    switch (lane) {
        case Lane::anchor: return "Anchor";
        case Lane::thread: return "Thread";
        case Lane::spark: return "Spark";
    }
    return "Invalid";
}

struct Core::Impl final {
    Controls controls{defaultControls()};
    std::uint64_t seed{kDefaultSeed};
    std::array<Pcg32, 4U> random{};
    std::array<std::uint32_t, kMaximumRouteMemory> memory{};
    std::array<bool, kMaximumRouteMemory> memory_valid{};
    std::uint8_t memory_head{};
    std::uint32_t current_id{};
    std::uint32_t destination_id{};
    std::uint8_t edge_memory_slot{};
    bool edge_replayed{};
    bool edge_replaced{};
    std::uint64_t route_elapsed_q32{};
    std::uint64_t route_duration_q32{1U};
    std::uint64_t musical_time_q32{};
    std::uint64_t tempo_remainder{};
    std::uint64_t next_thread_q32{kThreadStepQ32};
    std::uint64_t next_spark_q32{kSparkStepQ32};
    std::uint64_t next_control_tick_q32{};
    std::uint64_t absolute_frame{};
    std::array<double, kMaximumWaypoints> scene_weights{};
    std::array<SceneLane, kLaneCount> scene_target{};
    std::array<SceneLane, kLaneCount> scene_smoothed{};
    std::uint32_t scene_slew_remaining{};
    std::array<Voice, kLaneCount> voices{};
    float dc_x_left{};
    float dc_x_right{};
    float dc_y_left{};
    float dc_y_right{};
    std::array<std::uint32_t, kUiRouteTraceCapacity> route_trace_ids{};
    std::uint8_t route_trace_count{};
    std::array<std::uint64_t, kLaneCount> lane_event_counts{};
    std::uint64_t route_transition_count{};
    std::uint64_t dropped_event_count{};
    std::uint64_t repair_count{};
    std::uint64_t clamp_count{};
    std::uint64_t panic_count{};
    std::uint64_t control_epoch{};
    DiagnosticCode latched_fault{DiagnosticCode::none};
    std::uint64_t last_reset_sequence{};
    std::uint64_t last_panic_sequence{};
    std::uint64_t last_reseed_sequence{};
    bool reseed_pending{};
    std::uint64_t pending_reseed_value{kDefaultSeed};
    GenerationMode generation_mode{GenerationMode::route_memory};

    explicit Impl(std::uint64_t initial_seed) { resetInternal(initial_seed, defaultControls()); }

    [[nodiscard]] std::size_t indexForId(std::uint32_t id) const noexcept {
        for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
            if (controls.waypoints[index].id == id) return index;
        }
        return controls.waypoint_count;
    }

    [[nodiscard]] std::uint32_t homeId() const noexcept {
        return controls.waypoints[controls.home_index].id;
    }

    void seedStreams(std::uint64_t next_seed) noexcept {
        seed = next_seed;
        auto mixer = seed;
        for (std::size_t index = 0U; index < random.size(); ++index) {
            const auto init = splitmix64(mixer);
            const auto stream = splitmix64(mixer);
            random[index].seed(init, stream);
        }
        braids_adapter::seedRandom(static_cast<std::uint32_t>(seed ^ (seed >> 32U)));
    }

    void clearAudio() noexcept {
        for (std::size_t index = 0U; index < voices.size(); ++index) {
            voices[index].reset(static_cast<Lane>(index));
        }
        dc_x_left = 0.0F; dc_x_right = 0.0F; dc_y_left = 0.0F; dc_y_right = 0.0F;
    }

    [[nodiscard]] double distance(std::uint32_t first_id, std::uint32_t second_id) const noexcept {
        const auto first = indexForId(first_id);
        const auto second = indexForId(second_id);
        if (first >= controls.waypoint_count || second >= controls.waypoint_count) return 0.0;
        const double dx = static_cast<double>(controls.waypoints[first].x_u15)
            / 32767.0 - static_cast<double>(controls.waypoints[second].x_u15) / 32767.0;
        const double dy = static_cast<double>(controls.waypoints[first].y_u15)
            / 32767.0 - static_cast<double>(controls.waypoints[second].y_u15) / 32767.0;
        return std::sqrt(dx * dx + dy * dy);
    }

    [[nodiscard]] std::uint32_t freshDestination() noexcept {
        const double home_draw = random[0].unit();
        const double route_draw = random[0].unit();
        const auto home = homeId();
        if (current_id != home
            && home_draw < static_cast<double>(controls.home_u15) / 32767.0) {
            return home;
        }
        const double roam = static_cast<double>(controls.roam_u15) / 32767.0;
        const double temperature = 0.05 * std::pow(40.0, roam);
        std::array<double, kMaximumWaypoints> weights{};
        double sum = 0.0;
        for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
            if (controls.waypoints[index].id == current_id) continue;
            weights[index] = std::exp(-distance(current_id, controls.waypoints[index].id) / temperature);
            sum += weights[index];
        }
        if (!std::isfinite(sum) || sum <= 0.0) {
            std::uint32_t selected = kInvalidWaypointId;
            for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
                const auto id = controls.waypoints[index].id;
                if (id != current_id && (selected == kInvalidWaypointId || id < selected)) selected = id;
            }
            return selected == kInvalidWaypointId ? home : selected;
        }
        const double target = route_draw * sum;
        double cumulative = 0.0;
        std::uint32_t fallback = home;
        for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
            if (controls.waypoints[index].id == current_id) continue;
            fallback = controls.waypoints[index].id;
            cumulative += weights[index];
            if (target < cumulative) return fallback;
        }
        return fallback;
    }

    struct DestinationChoice final {
        std::uint32_t id{};
        std::uint8_t slot{};
        bool replayed{};
        bool replaced{};
    };

    [[nodiscard]] DestinationChoice chooseDestination() noexcept {
        if (memory_head >= controls.memory_length) memory_head = 0U;
        const auto slot = memory_head;
        const double reuse_draw = random[0].unit();
        bool replay = memory_valid[slot]
            && reuse_draw < static_cast<double>(controls.memory_u15) / 32767.0;
        std::uint32_t selected{};
        if (replay) {
            selected = memory[slot];
            if (indexForId(selected) >= controls.waypoint_count) {
                selected = homeId();
                memory[slot] = selected;
                ++repair_count;
            }
        } else {
            selected = freshDestination();
            memory[slot] = selected;
            memory_valid[slot] = true;
        }
        memory_head = static_cast<std::uint8_t>((memory_head + 1U) % controls.memory_length);
        return DestinationChoice{selected, slot, replay, !replay};
    }

    void setRouteDuration() noexcept {
        const double base = static_cast<double>(controls.travel_milli_quarters) / 1000.0;
        const double quarters = base * (0.5 + distance(current_id, destination_id));
        route_duration_q32 = std::max<std::uint64_t>(
            1U, static_cast<std::uint64_t>(std::llround(quarters * kQuarterQ32)));
    }

    void startNextEdge() noexcept {
        const auto choice = chooseDestination();
        destination_id = choice.id;
        edge_memory_slot = choice.slot;
        edge_replayed = choice.replayed;
        edge_replaced = choice.replaced;
        setRouteDuration();
    }

    void resetInternal(std::uint64_t next_seed, const Controls& next_controls) noexcept {
        controls = validControls(next_controls) ? next_controls : defaultControls();
        seedStreams(next_seed);
        memory.fill(0U);
        memory_valid.fill(false);
        memory_head = 0U;
        current_id = homeId();
        destination_id = homeId();
        edge_memory_slot = 0U;
        edge_replayed = false;
        edge_replaced = false;
        route_elapsed_q32 = 0U;
        route_duration_q32 = 1U;
        musical_time_q32 = 0U;
        tempo_remainder = 0U;
        next_thread_q32 = kThreadStepQ32;
        next_spark_q32 = kSparkStepQ32;
        next_control_tick_q32 = 0U;
        absolute_frame = 0U;
        route_trace_ids.fill(0U);
        route_trace_count = 0U;
        lane_event_counts.fill(0U);
        route_transition_count = 0U;
        dropped_event_count = 0U;
        repair_count = 0U;
        clamp_count = 0U;
        panic_count = 0U;
        control_epoch = 0U;
        latched_fault = DiagnosticCode::none;
        reseed_pending = false;
        pending_reseed_value = next_seed;
        clearAudio();
        updateSceneTarget();
        scene_smoothed = scene_target;
        scene_slew_remaining = 0U;
        startNextEdge();
    }

    void repairForControls(const Controls& next) noexcept {
        const auto old_current = current_id;
        const auto old_destination = destination_id;
        controls = next;
        if (indexForId(old_current) >= controls.waypoint_count) {
            current_id = homeId();
            ++repair_count;
        }
        if (indexForId(old_destination) >= controls.waypoint_count) {
            destination_id = homeId();
            ++repair_count;
        }
        for (std::size_t slot = 0U; slot < kMaximumRouteMemory; ++slot) {
            if (memory_valid[slot] && indexForId(memory[slot]) >= controls.waypoint_count) {
                memory[slot] = homeId();
                ++repair_count;
            }
        }
        if (memory_head >= controls.memory_length) memory_head = 0U;
    }

    [[nodiscard]] std::pair<double, double> position() const noexcept {
        const auto first = indexForId(current_id);
        const auto second = indexForId(destination_id);
        if (first >= controls.waypoint_count || second >= controls.waypoint_count) return {0.0, 0.0};
        const double phase = route_duration_q32 == 0U
            ? 1.0
            : std::clamp(
                static_cast<double>(route_elapsed_q32) / route_duration_q32,
                0.0, 1.0);
        const double eased = 0.5 - 0.5 * std::cos(kPi * phase);
        const auto& a = controls.waypoints[first];
        const auto& b = controls.waypoints[second];
        const double x = (1.0 - eased) * a.x_u15 / 32767.0 + eased * b.x_u15 / 32767.0;
        const double y = (1.0 - eased) * a.y_u15 / 32767.0 + eased * b.y_u15 / 32767.0;
        return {x, y};
    }

    void updateSceneTarget() noexcept {
        const auto [x, y] = position();
        const double radius = 0.05 + 0.95 * static_cast<double>(controls.radius_u15) / 32767.0;
        double sum = 0.0;
        for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
            const double dx = x - static_cast<double>(controls.waypoints[index].x_u15) / 32767.0;
            const double dy = y - static_cast<double>(controls.waypoints[index].y_u15) / 32767.0;
            scene_weights[index] = std::exp(-(dx * dx + dy * dy) / (2.0 * radius * radius));
            sum += scene_weights[index];
        }
        if (!std::isfinite(sum) || sum <= 0.0) {
            std::size_t nearest = 0U;
            double nearest_distance = std::numeric_limits<double>::infinity();
            for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
                const double dx = x - static_cast<double>(controls.waypoints[index].x_u15) / 32767.0;
                const double dy = y - static_cast<double>(controls.waypoints[index].y_u15) / 32767.0;
                const double squared = dx * dx + dy * dy;
                if (squared < nearest_distance) { nearest_distance = squared; nearest = index; }
                scene_weights[index] = 0.0;
            }
            scene_weights[nearest] = 1.0;
            sum = 1.0;
        }
        for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
            scene_weights[index] /= sum;
        }
        for (std::size_t lane = 0U; lane < kLaneCount; ++lane) {
            SceneLane target{};
            target.log_decay = 0.0;
            target.level_db = 0.0;
            for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
                const auto& source = controls.waypoints[index].lanes[lane];
                const double weight = generation_mode == GenerationMode::independent_white_scene
                    ? 1.0 / controls.waypoint_count : scene_weights[index];
                target.activity += weight * source.activity_u15 / 32767.0;
                target.timbre += weight * source.timbre_u15 / 32767.0;
                target.color += weight * source.color_u15 / 32767.0;
                target.log_decay += weight * std::log(static_cast<double>(source.decay_ms) / 1000.0);
                target.level_db += weight * static_cast<double>(source.level_milli_db) / 1000.0;
                target.pan += weight * static_cast<double>(source.pan_s15) / 32767.0;
            }
            scene_target[lane] = target;
        }
        scene_slew_remaining = kParameterSlewFrames;
    }

    void advanceSceneSlew() noexcept {
        if (scene_slew_remaining == 0U) return;
        const double proportion = 1.0 / static_cast<double>(scene_slew_remaining);
        for (std::size_t lane = 0U; lane < kLaneCount; ++lane) {
            auto& current = scene_smoothed[lane];
            const auto& target = scene_target[lane];
            current.activity += (target.activity - current.activity) * proportion;
            current.timbre += (target.timbre - current.timbre) * proportion;
            current.color += (target.color - current.color) * proportion;
            current.log_decay += (target.log_decay - current.log_decay) * proportion;
            current.level_db += (target.level_db - current.level_db) * proportion;
            current.pan += (target.pan - current.pan) * proportion;
        }
        --scene_slew_remaining;
    }

    [[nodiscard]] std::size_t choosePitchWaypoint(Lane lane) noexcept {
        auto& stream = random[1U + laneIndex(lane)];
        if (generation_mode == GenerationMode::independent_white_scene) {
            return static_cast<std::size_t>(stream.next() % controls.waypoint_count);
        }
        const double target = stream.unit();
        double cumulative = 0.0;
        for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
            cumulative += scene_weights[index];
            if (target < cumulative) return index;
        }
        return controls.waypoint_count - 1U;
    }

    void triggerLane(Lane lane, std::uint64_t frame, ProcessReport& report) noexcept {
        auto& stream = random[1U + laneIndex(lane)];
        const auto pitch_index = choosePitchWaypoint(lane);
        const double fire_draw = stream.unit();
        const auto& scene = scene_smoothed[laneIndex(lane)];
        const double probability = static_cast<double>(controls.density_u15) / 32767.0
            * std::clamp(scene.activity, 0.0, 1.0);
        if (fire_draw >= probability) return;
        if (report.musical_event_count >= report.musical_events.size()) {
            ++dropped_event_count;
            report.diagnostic = DiagnosticCode::event_capacity;
            return;
        }
        const auto& pitch_waypoint = controls.waypoints[pitch_index];
        const auto raw_pitch = static_cast<int>(controls.root_midi_note)
            + pitch_waypoint.lanes[laneIndex(lane)].interval_semitones;
        MusicalEvent event{};
        event.absolute_frame = frame;
        event.lane = lane;
        event.pitch_waypoint_id = pitch_waypoint.id;
        event.pitch_midi = quantizePitch(raw_pitch, controls.scale);
        event.timbre_u15 = toU15(std::clamp(scene.timbre, 0.0, 1.0));
        event.color_u15 = toU15(std::clamp(scene.color, 0.0, 1.0));
        event.decay_ms = static_cast<std::uint16_t>(std::clamp<long>(
            std::lround(std::exp(scene.log_decay) * 1000.0), 40L, 4000L));
        event.level_milli_db = static_cast<std::int32_t>(std::clamp<long>(
            std::lround(scene.level_db * 1000.0), -60000L, -6000L));
        event.pan_s15 = toS15(std::clamp(scene.pan, -1.0, 1.0));
        report.musical_events[report.musical_event_count++] = event;
        voices[laneIndex(lane)].trigger(event);
        ++lane_event_counts[laneIndex(lane)];
    }

    void appendUiRoute(std::uint32_t id) noexcept {
        if (route_trace_count < route_trace_ids.size()) {
            route_trace_ids[route_trace_count++] = id;
            return;
        }
        for (std::size_t index = 1U; index < route_trace_ids.size(); ++index) {
            route_trace_ids[index - 1U] = route_trace_ids[index];
        }
        route_trace_ids.back() = id;
    }

    void applyPendingReseed() noexcept {
        if (!reseed_pending) return;
        seedStreams(pending_reseed_value);
        memory.fill(0U);
        memory_valid.fill(false);
        memory_head = 0U;
        current_id = homeId();
        route_elapsed_q32 = 0U;
        reseed_pending = false;
    }

    void arrive(std::uint64_t frame, ProcessReport& report) noexcept {
        const auto from = current_id;
        current_id = destination_id;
        const auto arrived = current_id;
        const auto arrived_slot = edge_memory_slot;
        const auto arrived_replayed = edge_replayed;
        const auto arrived_replaced = edge_replaced;
        const auto prior_duration = route_duration_q32;
        if (route_elapsed_q32 >= prior_duration) route_elapsed_q32 -= prior_duration;
        applyPendingReseed();
        const auto choice = chooseDestination();
        destination_id = choice.id;
        edge_memory_slot = choice.slot;
        edge_replayed = choice.replayed;
        edge_replaced = choice.replaced;
        setRouteDuration();
        ++route_transition_count;
        appendUiRoute(arrived);
        if (generation_mode == GenerationMode::route_memory) {
            if (report.route_event_count >= report.route_events.size()) {
                ++dropped_event_count;
                report.diagnostic = DiagnosticCode::event_capacity;
            } else {
                report.route_events[report.route_event_count++] = RouteTraceEvent{
                    frame, from, arrived, arrived_slot, arrived_replayed, arrived_replaced,
                    from == arrived};
            }
        }
        updateSceneTarget();
        triggerLane(Lane::anchor, frame, report);
    }

    [[nodiscard]] std::uint64_t phaseIncrement() noexcept {
        const std::uint64_t numerator =
            static_cast<std::uint64_t>(controls.tempo_milli_bpm) * kQuarterQ32
            + tempo_remainder;
        const auto increment = numerator / kTempoDenominator;
        tempo_remainder = numerator % kTempoDenominator;
        return increment;
    }

    [[nodiscard]] bool validState(const CoreState& state) const noexcept {
        if (state.version != 1U || !validControls(state.controls)
            || state.route_duration_q32 == 0U
            || state.memory_head >= state.controls.memory_length
            || state.edge_memory_slot >= state.controls.memory_length
            || static_cast<std::size_t>(state.generation_mode)
                > static_cast<std::size_t>(GenerationMode::independent_white_scene)) {
            return false;
        }
        const auto contains = [&state](std::uint32_t id) {
            for (std::size_t index = 0U; index < state.controls.waypoint_count; ++index) {
                if (state.controls.waypoints[index].id == id) return true;
            }
            return false;
        };
        if (!contains(state.current_id) || !contains(state.destination_id)) return false;
        for (std::size_t index = 0U; index < kMaximumRouteMemory; ++index) {
            if (state.route_memory_valid[index] && !contains(state.route_memory[index])) return false;
        }
        for (const auto stream : state.random_streams) {
            if ((stream & 1U) == 0U) return false;
        }
        return true;
    }
};

Core::Core(std::uint64_t seed) : impl_(std::make_unique<Impl>(seed)) {}
Core::~Core() = default;
Core::Core(Core&&) noexcept = default;
Core& Core::operator=(Core&&) noexcept = default;

bool Core::process(
    const Controls& controls,
    const ActionSequences& actions,
    float* left,
    float* right,
    std::size_t frame_count,
    ProcessReport* report) noexcept {
    ProcessReport local{};
    local.absolute_frame_start = impl_->absolute_frame;
    if (left == nullptr || right == nullptr) {
        local.diagnostic = DiagnosticCode::invalid_buffer;
        if (report != nullptr) *report = local;
        return false;
    }
    if (frame_count > kMaximumBlockFrames) {
        local.diagnostic = DiagnosticCode::oversized_block;
        if (report != nullptr) *report = local;
        return false;
    }
    std::fill_n(left, frame_count, 0.0F);
    std::fill_n(right, frame_count, 0.0F);
    if (!validControls(controls)) {
        local.diagnostic = DiagnosticCode::invalid_controls;
        if (report != nullptr) *report = local;
        return false;
    }

    if (actions.reset != impl_->last_reset_sequence) {
        const auto reset_sequence = actions.reset;
        impl_->resetInternal(kDefaultSeed, controls);
        impl_->last_reset_sequence = reset_sequence;
    } else if (!sameControls(impl_->controls, controls)) {
        impl_->repairForControls(controls);
        ++impl_->control_epoch;
        impl_->updateSceneTarget();
    }
    if (actions.panic != impl_->last_panic_sequence) {
        impl_->last_panic_sequence = actions.panic;
        impl_->clearAudio();
        ++impl_->panic_count;
    }
    if (actions.reseed != impl_->last_reseed_sequence) {
        impl_->last_reseed_sequence = actions.reseed;
        impl_->reseed_pending = true;
        impl_->pending_reseed_value = actions.reseed_value;
    }
    if (impl_->latched_fault != DiagnosticCode::none) {
        local.diagnostic = impl_->latched_fault;
        impl_->absolute_frame += frame_count;
        if (report != nullptr) *report = local;
        return false;
    }

    for (std::size_t frame = 0U; frame < frame_count; ++frame) {
        const auto absolute = impl_->absolute_frame + frame;
        if (impl_->controls.run) {
            while (impl_->route_elapsed_q32 >= impl_->route_duration_q32) {
                impl_->arrive(absolute, local);
            }
            while (impl_->musical_time_q32 >= impl_->next_control_tick_q32) {
                impl_->updateSceneTarget();
                impl_->next_control_tick_q32 += kControlStepQ32;
            }
            while (impl_->musical_time_q32 >= impl_->next_thread_q32) {
                impl_->triggerLane(Lane::thread, absolute, local);
                impl_->next_thread_q32 += kThreadStepQ32;
            }
            while (impl_->musical_time_q32 >= impl_->next_spark_q32) {
                impl_->triggerLane(Lane::spark, absolute, local);
                impl_->next_spark_q32 += kSparkStepQ32;
            }
        }
        impl_->advanceSceneSlew();
        double mixed_left = 0.0;
        double mixed_right = 0.0;
        for (auto& voice : impl_->voices) {
            const auto sample = voice.render();
            mixed_left += sample.first;
            mixed_right += sample.second;
        }
        const float input_left = static_cast<float>(mixed_left);
        const float input_right = static_cast<float>(mixed_right);
        const float dc_left = input_left - impl_->dc_x_left + 0.995F * impl_->dc_y_left;
        const float dc_right = input_right - impl_->dc_x_right + 0.995F * impl_->dc_y_right;
        impl_->dc_x_left = input_left; impl_->dc_x_right = input_right;
        impl_->dc_y_left = dc_left; impl_->dc_y_right = dc_right;
        if (!std::isfinite(dc_left) || !std::isfinite(dc_right)) {
            impl_->latched_fault = DiagnosticCode::numeric_fault;
            local.diagnostic = DiagnosticCode::numeric_fault;
            std::fill_n(left, frame_count, 0.0F);
            std::fill_n(right, frame_count, 0.0F);
            impl_->absolute_frame += frame_count;
            if (report != nullptr) *report = local;
            return false;
        }
        if (std::abs(dc_left) >= 0.98F || std::abs(dc_right) >= 0.98F) ++impl_->clamp_count;
        left[frame] = std::clamp(dc_left, -0.98F, 0.98F);
        right[frame] = std::clamp(dc_right, -0.98F, 0.98F);
        if (impl_->controls.run) {
            const auto increment = impl_->phaseIncrement();
            impl_->musical_time_q32 += increment;
            impl_->route_elapsed_q32 += increment;
        }
    }
    impl_->absolute_frame += frame_count;
    if (report != nullptr) *report = local;
    return local.diagnostic == DiagnosticCode::none;
}

Snapshot Core::snapshot() const noexcept {
    Snapshot result{};
    result.accepted_controls = impl_->controls;
    result.absolute_frame = impl_->absolute_frame;
    const auto [x, y] = impl_->position();
    result.route_x_u15 = toU15(x);
    result.route_y_u15 = toU15(y);
    result.route_progress_u15 = impl_->route_duration_q32 == 0U
        ? 32767U
        : toU15(std::clamp(
            static_cast<double>(impl_->route_elapsed_q32) / impl_->route_duration_q32,
            0.0, 1.0));
    result.current_index = static_cast<std::uint8_t>(impl_->indexForId(impl_->current_id));
    result.destination_index = static_cast<std::uint8_t>(impl_->indexForId(impl_->destination_id));
    result.memory_head = impl_->memory_head;
    result.route_memory = impl_->memory;
    result.route_memory_valid = impl_->memory_valid;
    result.route_trace_ids = impl_->route_trace_ids;
    result.route_trace_count = impl_->route_trace_count;
    for (std::size_t lane = 0U; lane < kLaneCount; ++lane) {
        result.envelope_u15[lane] = toU15(std::clamp(impl_->voices[lane].envelope, 0.0, 1.0));
    }
    result.lane_event_counts = impl_->lane_event_counts;
    result.route_transition_count = impl_->route_transition_count;
    result.dropped_event_count = impl_->dropped_event_count;
    result.repair_count = impl_->repair_count;
    result.clamp_count = impl_->clamp_count;
    result.panic_count = impl_->panic_count;
    result.control_epoch = impl_->control_epoch;
    result.latched_fault = impl_->latched_fault;
    return result;
}

CoreState Core::captureState() const noexcept {
    CoreState state{};
    state.controls = impl_->controls;
    state.seed = impl_->seed;
    for (std::size_t index = 0U; index < impl_->random.size(); ++index) {
        state.random_states[index] = impl_->random[index].state;
        state.random_streams[index] = impl_->random[index].increment;
    }
    state.route_memory = impl_->memory;
    state.route_memory_valid = impl_->memory_valid;
    state.memory_head = impl_->memory_head;
    state.current_id = impl_->current_id;
    state.destination_id = impl_->destination_id;
    state.edge_memory_slot = impl_->edge_memory_slot;
    state.edge_replayed = impl_->edge_replayed;
    state.edge_replaced = impl_->edge_replaced;
    state.route_elapsed_q32 = impl_->route_elapsed_q32;
    state.route_duration_q32 = impl_->route_duration_q32;
    state.musical_time_q32 = impl_->musical_time_q32;
    state.tempo_remainder = impl_->tempo_remainder;
    state.next_thread_q32 = impl_->next_thread_q32;
    state.next_spark_q32 = impl_->next_spark_q32;
    state.next_control_tick_q32 = impl_->next_control_tick_q32;
    state.absolute_frame = impl_->absolute_frame;
    state.reseed_pending = impl_->reseed_pending;
    state.pending_reseed_value = impl_->pending_reseed_value;
    state.lane_event_counts = impl_->lane_event_counts;
    state.route_transition_count = impl_->route_transition_count;
    state.dropped_event_count = impl_->dropped_event_count;
    state.repair_count = impl_->repair_count;
    state.control_epoch = impl_->control_epoch;
    state.generation_mode = impl_->generation_mode;
    return state;
}

bool Core::recallState(const CoreState& state) noexcept {
    if (!impl_->validState(state)) return false;
    impl_->controls = state.controls;
    impl_->seed = state.seed;
    for (std::size_t index = 0U; index < impl_->random.size(); ++index) {
        impl_->random[index].state = state.random_states[index];
        impl_->random[index].increment = state.random_streams[index];
    }
    braids_adapter::seedRandom(static_cast<std::uint32_t>(state.seed ^ (state.seed >> 32U)));
    impl_->memory = state.route_memory;
    impl_->memory_valid = state.route_memory_valid;
    impl_->memory_head = state.memory_head;
    impl_->current_id = state.current_id;
    impl_->destination_id = state.destination_id;
    impl_->edge_memory_slot = state.edge_memory_slot;
    impl_->edge_replayed = state.edge_replayed;
    impl_->edge_replaced = state.edge_replaced;
    impl_->route_elapsed_q32 = state.route_elapsed_q32;
    impl_->route_duration_q32 = state.route_duration_q32;
    impl_->musical_time_q32 = state.musical_time_q32;
    impl_->tempo_remainder = state.tempo_remainder;
    impl_->next_thread_q32 = state.next_thread_q32;
    impl_->next_spark_q32 = state.next_spark_q32;
    impl_->next_control_tick_q32 = state.next_control_tick_q32;
    impl_->absolute_frame = state.absolute_frame;
    impl_->reseed_pending = state.reseed_pending;
    impl_->pending_reseed_value = state.pending_reseed_value;
    impl_->lane_event_counts = state.lane_event_counts;
    impl_->route_transition_count = state.route_transition_count;
    impl_->dropped_event_count = state.dropped_event_count;
    impl_->repair_count = state.repair_count;
    impl_->control_epoch = state.control_epoch;
    impl_->generation_mode = state.generation_mode;
    impl_->route_trace_ids.fill(0U);
    impl_->route_trace_count = 0U;
    impl_->latched_fault = DiagnosticCode::none;
    impl_->clearAudio();
    impl_->updateSceneTarget();
    impl_->scene_smoothed = impl_->scene_target;
    impl_->scene_slew_remaining = 0U;
    return true;
}

void Core::setGenerationMode(GenerationMode mode) noexcept {
    if (mode == GenerationMode::route_memory || mode == GenerationMode::independent_white_scene) {
        impl_->generation_mode = mode;
        impl_->updateSceneTarget();
    }
}

}  // namespace schuss::murmur_map
