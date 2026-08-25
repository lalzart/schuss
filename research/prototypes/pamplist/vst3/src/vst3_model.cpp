#include "schuss/pamplist/vst3_model.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <limits>
#include <sstream>
#include <utility>

namespace schuss::pamplist {
namespace {

constexpr std::size_t kTimelineStart = 1U;
constexpr std::size_t kDecisionStart = 15U;
constexpr std::size_t kMotionStart = 57U;
constexpr std::size_t kVoiceStart = 113U;
constexpr std::size_t kCohesionStart = 169U;
constexpr std::size_t kMasterIndex = 177U;

static_assert(kTimelineStart + kLaneCount * 2U == kDecisionStart);
static_assert(kDecisionStart + kLaneCount * 6U == kMotionStart);
static_assert(kMotionStart + kLaneCount * kDestinationCount == kVoiceStart);
static_assert(kVoiceStart + kLaneCount * 8U == kCohesionStart);
static_assert(kCohesionStart + 8U == kMasterIndex);
static_assert(kMasterIndex + 1U == kVst3RunParameterIndex);
static_assert(kVst3RunParameterIndex + 1U == kVst3ParameterCount);

[[nodiscard]] std::array<Vst3ParameterDescriptor, kVst3ParameterCount>
makeDescriptors() {
    std::array<Vst3ParameterDescriptor, kVst3ParameterCount> result{};
    const auto defaults = defaultControls();
    std::size_t index = 0U;
    const auto add = [&result, &index](
                         std::string id,
                         std::string name,
                         std::string unit,
                         Vst3ParameterTarget target,
                         PresentationKind presentation,
                         std::uint8_t lane,
                         std::uint8_t element,
                         float minimum,
                         float maximum,
                         float default_physical,
                         std::uint32_t step_count = 0U) {
        result[index++] = Vst3ParameterDescriptor{
            std::move(id),
            std::move(name),
            std::move(unit),
            target,
            presentation,
            lane,
            element,
            minimum,
            maximum,
            default_physical,
            step_count,
        };
    };

    add("pamp.tempo", "Tempo", "BPM", Vst3ParameterTarget::tempo,
        PresentationKind::bpm, 0U, 0U, 20.0F, 300.0F,
        static_cast<float>(defaults.tempo_milli_bpm) / 1000.0F);

    for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
        const auto lane_number = std::to_string(lane + 1U);
        const auto id = std::string{"pamp.lane"} + lane_number;
        const auto name = std::string{"Lane "} + lane_number;
        add(id + ".rate", name + " Rate", "", Vst3ParameterTarget::lane_rate,
            PresentationKind::rate, static_cast<std::uint8_t>(lane), 0U,
            0.0F, 15.0F, static_cast<float>(defaults.lanes[lane].rate_index), 16U);
        add(id + ".phase", name + " Phase", "", Vst3ParameterTarget::lane_phase,
            PresentationKind::phase, static_cast<std::uint8_t>(lane), 0U,
            0.0F, 127.0F, static_cast<float>(defaults.lanes[lane].phase_u7), 128U);
    }

    for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
        const auto lane_number = std::to_string(lane + 1U);
        const auto id = std::string{"pamp.lane"} + lane_number;
        const auto name = std::string{"Lane "} + lane_number;
        const auto& value = defaults.lanes[lane];
        add(id + ".shape", name + " Shape", "", Vst3ParameterTarget::lane_shape,
            PresentationKind::shape, static_cast<std::uint8_t>(lane), 0U,
            0.0F, 7.0F, static_cast<float>(value.shape), 8U);
        add(id + ".hits", name + " Hits", "", Vst3ParameterTarget::lane_hits,
            PresentationKind::hits, static_cast<std::uint8_t>(lane), 0U,
            0.0F, 16.0F, static_cast<float>(value.hits), 17U);
        add(id + ".rotate", name + " Rotate", "", Vst3ParameterTarget::lane_rotation,
            PresentationKind::rotation, static_cast<std::uint8_t>(lane), 0U,
            0.0F, 15.0F, static_cast<float>(value.rotation), 16U);
        add(id + ".chance", name + " Chance", "%",
            Vst3ParameterTarget::lane_probability, PresentationKind::chance,
            static_cast<std::uint8_t>(lane), 0U, 0.0F, 1.0F, value.probability);
        add(id + ".repeat", name + " Repeat", "", Vst3ParameterTarget::lane_repeat,
            PresentationKind::repeat, static_cast<std::uint8_t>(lane), 0U,
            0.0F, 64.0F, static_cast<float>(value.repeat), 65U);
        add(id + ".depth", name + " Depth", "%", Vst3ParameterTarget::lane_amplitude,
            PresentationKind::depth, static_cast<std::uint8_t>(lane), 0U,
            0.0F, 1.0F, value.amplitude);
    }

    constexpr std::array<const char*, kDestinationCount> route_ids{{
        "trigger", "pitch", "model", "harmonics", "timbre", "morph", "decay", "level",
    }};
    constexpr std::array<const char*, kDestinationCount> route_names{{
        "Trigger", "Pitch", "Model Sweep", "Harmonics", "Timbre", "Morph", "Decay", "Level",
    }};
    for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
        const auto lane_number = std::to_string(lane + 1U);
        const auto id = std::string{"pamp.lane"} + lane_number + ".motion.";
        const auto name = std::string{"Lane "} + lane_number + " Motion ";
        for (std::size_t route = 0; route < kDestinationCount; ++route) {
            const bool trigger = route == 0U;
            add(id + route_ids[route], name + route_names[route],
                trigger ? "" : "%", Vst3ParameterTarget::lane_route,
                trigger ? PresentationKind::trigger_switch
                        : PresentationKind::signed_percent,
                static_cast<std::uint8_t>(lane), static_cast<std::uint8_t>(route),
                trigger ? 0.0F : -1.0F, 1.0F,
                defaults.lanes[lane].routes[route], trigger ? 2U : 0U);
        }
    }

    constexpr std::array<const char*, 8U> voice_ids{{
        "model", "pitch", "harmonics", "timbre", "morph", "decay", "colour", "level",
    }};
    constexpr std::array<const char*, 8U> voice_names{{
        "Model", "Pitch", "Harmonics", "Timbre", "Morph", "Decay", "Colour", "Level",
    }};
    constexpr std::array<Vst3ParameterTarget, 8U> voice_targets{{
        Vst3ParameterTarget::voice_engine,
        Vst3ParameterTarget::voice_note,
        Vst3ParameterTarget::voice_harmonics,
        Vst3ParameterTarget::voice_timbre,
        Vst3ParameterTarget::voice_morph,
        Vst3ParameterTarget::voice_decay,
        Vst3ParameterTarget::voice_colour,
        Vst3ParameterTarget::voice_level,
    }};
    for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
        const auto lane_number = std::to_string(lane + 1U);
        const auto id = std::string{"pamp.lane"} + lane_number + ".voice.";
        const auto name = std::string{"Lane "} + lane_number + " Voice ";
        const auto& value = defaults.voices[lane];
        const std::array<float, 8U> defaults_for_voice{{
            static_cast<float>(value.engine), value.note, value.harmonics, value.timbre,
            value.morph, value.decay, value.lpg_colour, value.level,
        }};
        for (std::size_t field = 0; field < voice_ids.size(); ++field) {
            const bool model = field == 0U;
            const bool note = field == 1U;
            add(id + voice_ids[field], name + voice_names[field],
                model ? "" : (note ? "note" : "%"), voice_targets[field],
                model ? PresentationKind::model
                      : (note ? PresentationKind::note
                              : PresentationKind::unit_percent),
                static_cast<std::uint8_t>(lane), 0U,
                note ? 24.0F : 0.0F, note ? 96.0F : (model ? 23.0F : 1.0F),
                defaults_for_voice[field], model ? 24U : 0U);
        }
    }

    const auto& cohesion = defaults.cohesion;
    add("pamp.global.drive", "Global Drive", "%", Vst3ParameterTarget::cohesion_drive,
        PresentationKind::unit_percent, 0U, 0U, 0.0F, 1.0F, cohesion.drive);
    add("pamp.global.cohere", "Global Cohere", "%", Vst3ParameterTarget::cohesion_cohere,
        PresentationKind::unit_percent, 0U, 0U, 0.0F, 1.0F, cohesion.cohere);
    add("pamp.global.root", "Global Root", "note", Vst3ParameterTarget::cohesion_root,
        PresentationKind::note, 0U, 0U, 24.0F, 84.0F, cohesion.root_note);
    add("pamp.global.spread", "Global Spread", "%", Vst3ParameterTarget::cohesion_spread,
        PresentationKind::unit_percent, 0U, 0U, 0.0F, 1.0F, cohesion.spread);
    add("pamp.global.tail", "Global Tail", "%", Vst3ParameterTarget::cohesion_tail,
        PresentationKind::unit_percent, 0U, 0U, 0.0F, 1.0F, cohesion.tail);
    add("pamp.global.damping", "Global Damping", "%",
        Vst3ParameterTarget::cohesion_damping, PresentationKind::unit_percent,
        0U, 0U, 0.0F, 1.0F, cohesion.damping);
    add("pamp.global.width", "Global Width", "%", Vst3ParameterTarget::cohesion_width,
        PresentationKind::unit_percent, 0U, 0U, 0.0F, 1.0F, cohesion.width);
    add("pamp.global.duck", "Global Duck", "%", Vst3ParameterTarget::cohesion_duck,
        PresentationKind::unit_percent, 0U, 0U, 0.0F, 1.0F, cohesion.duck);
    add("pamp.master", "Global Master", "%", Vst3ParameterTarget::master_gain,
        PresentationKind::unit_percent, 0U, 0U, 0.0F, 1.0F, defaults.master_gain);
    add("pamp.run", "Run", "", Vst3ParameterTarget::running,
        PresentationKind::trigger_switch, 0U, 0U, 0.0F, 1.0F,
        defaults.running ? 1.0F : 0.0F, 2U);

    return result;
}

[[nodiscard]] float boundedNormalized(float value, float fallback) noexcept {
    return std::isfinite(value) ? std::clamp(value, 0.0F, 1.0F) : fallback;
}

[[nodiscard]] float readPhysical(
    const Controls& controls,
    const Vst3ParameterDescriptor& descriptor) noexcept {
    const auto lane = std::min<std::size_t>(descriptor.lane, kLaneCount - 1U);
    switch (descriptor.target) {
        case Vst3ParameterTarget::tempo:
            return static_cast<float>(controls.tempo_milli_bpm) / 1000.0F;
        case Vst3ParameterTarget::lane_rate:
            return static_cast<float>(controls.lanes[lane].rate_index);
        case Vst3ParameterTarget::lane_phase:
            return static_cast<float>(controls.lanes[lane].phase_u7);
        case Vst3ParameterTarget::lane_shape:
            return static_cast<float>(controls.lanes[lane].shape);
        case Vst3ParameterTarget::lane_hits:
            return static_cast<float>(controls.lanes[lane].hits);
        case Vst3ParameterTarget::lane_rotation:
            return static_cast<float>(controls.lanes[lane].rotation);
        case Vst3ParameterTarget::lane_probability:
            return controls.lanes[lane].probability;
        case Vst3ParameterTarget::lane_repeat:
            return static_cast<float>(controls.lanes[lane].repeat);
        case Vst3ParameterTarget::lane_amplitude:
            return controls.lanes[lane].amplitude;
        case Vst3ParameterTarget::lane_route:
            return controls.lanes[lane].routes[std::min<std::size_t>(
                descriptor.element, kDestinationCount - 1U)];
        case Vst3ParameterTarget::voice_engine:
            return static_cast<float>(controls.voices[lane].engine);
        case Vst3ParameterTarget::voice_note:
            return controls.voices[lane].note;
        case Vst3ParameterTarget::voice_harmonics:
            return controls.voices[lane].harmonics;
        case Vst3ParameterTarget::voice_timbre:
            return controls.voices[lane].timbre;
        case Vst3ParameterTarget::voice_morph:
            return controls.voices[lane].morph;
        case Vst3ParameterTarget::voice_decay:
            return controls.voices[lane].decay;
        case Vst3ParameterTarget::voice_colour:
            return controls.voices[lane].lpg_colour;
        case Vst3ParameterTarget::voice_level:
            return controls.voices[lane].level;
        case Vst3ParameterTarget::cohesion_drive: return controls.cohesion.drive;
        case Vst3ParameterTarget::cohesion_cohere: return controls.cohesion.cohere;
        case Vst3ParameterTarget::cohesion_root: return controls.cohesion.root_note;
        case Vst3ParameterTarget::cohesion_spread: return controls.cohesion.spread;
        case Vst3ParameterTarget::cohesion_tail: return controls.cohesion.tail;
        case Vst3ParameterTarget::cohesion_damping: return controls.cohesion.damping;
        case Vst3ParameterTarget::cohesion_width: return controls.cohesion.width;
        case Vst3ParameterTarget::cohesion_duck: return controls.cohesion.duck;
        case Vst3ParameterTarget::master_gain: return controls.master_gain;
        case Vst3ParameterTarget::running: return controls.running ? 1.0F : 0.0F;
    }
    return descriptor.default_physical;
}

[[nodiscard]] std::string compactNumber(float value, int precision) {
    std::ostringstream stream;
    stream << std::fixed << std::setprecision(precision) << value;
    auto result = stream.str();
    while (result.size() > 1U && result.back() == '0') result.pop_back();
    if (!result.empty() && result.back() == '.') result.pop_back();
    return result;
}

void fnvByte(std::uint64_t& value, std::uint8_t byte) noexcept {
    value ^= byte;
    value *= UINT64_C(1099511628211);
}

void fnvText(std::uint64_t& value, std::string_view text) noexcept {
    for (const auto character : text) {
        fnvByte(value, static_cast<std::uint8_t>(character));
    }
    fnvByte(value, 0U);
}

void fnvU32(std::uint64_t& value, std::uint32_t number) noexcept {
    for (unsigned int shift = 0U; shift < 32U; shift += 8U) {
        fnvByte(value, static_cast<std::uint8_t>((number >> shift) & 0xffU));
    }
}

void fnvFloat(std::uint64_t& value, float number) noexcept {
    std::uint32_t bits{};
    static_assert(sizeof(bits) == sizeof(number));
    std::memcpy(&bits, &number, sizeof(bits));
    fnvU32(value, bits);
}

}  // namespace

const std::array<Vst3ParameterDescriptor, kVst3ParameterCount>&
vst3ParameterDescriptors() noexcept {
    static const auto descriptors = makeDescriptors();
    return descriptors;
}

float vst3NormalizePhysical(
    const Vst3ParameterDescriptor& descriptor,
    float physical) noexcept {
    if (!std::isfinite(physical)
        || !std::isfinite(descriptor.minimum)
        || !std::isfinite(descriptor.maximum)
        || descriptor.maximum <= descriptor.minimum) {
        physical = descriptor.default_physical;
    }
    auto normalized = std::clamp(
        (physical - descriptor.minimum)
            / (descriptor.maximum - descriptor.minimum),
        0.0F,
        1.0F);
    if (descriptor.step_count > 1U) {
        const auto maximum_index = descriptor.step_count - 1U;
        const auto step = static_cast<std::uint32_t>(std::lround(
            static_cast<double>(normalized)
                * static_cast<double>(maximum_index)));
        normalized = static_cast<float>(step)
            / static_cast<float>(maximum_index);
    }
    return normalized;
}

float vst3DenormalizeParameter(
    const Vst3ParameterDescriptor& descriptor,
    float normalized) noexcept {
    const auto fallback = vst3NormalizePhysical(
        descriptor, descriptor.default_physical);
    auto bounded = boundedNormalized(normalized, fallback);
    if (descriptor.step_count > 1U) {
        const auto maximum_index = descriptor.step_count - 1U;
        const auto step = static_cast<std::uint32_t>(std::lround(
            static_cast<double>(bounded)
                * static_cast<double>(maximum_index)));
        bounded = static_cast<float>(step)
            / static_cast<float>(maximum_index);
    }
    return descriptor.minimum
        + bounded * (descriptor.maximum - descriptor.minimum);
}

float vst3DefaultNormalized(
    const Vst3ParameterDescriptor& descriptor) noexcept {
    return vst3NormalizePhysical(descriptor, descriptor.default_physical);
}

std::string vst3FormatParameter(
    const Vst3ParameterDescriptor& descriptor,
    float normalized) {
    const auto physical = vst3DenormalizeParameter(descriptor, normalized);
    switch (descriptor.presentation) {
        case PresentationKind::model: {
            const auto model = static_cast<std::uint8_t>(std::clamp(
                static_cast<int>(std::lround(physical)), 0, 23));
            return std::to_string(static_cast<unsigned int>(model)) + " "
                + modelName(model);
        }
        case PresentationKind::note:
            return compactNumber(physical, 2);
        case PresentationKind::unit_percent:
        case PresentationKind::chance:
        case PresentationKind::depth:
            return compactNumber(physical * 100.0F, 1) + "%";
        case PresentationKind::signed_percent:
            if (std::abs(physical) < 0.0005F) return "Direct";
            return std::string{physical > 0.0F ? "+" : ""}
                + compactNumber(physical * 100.0F, 1) + "%";
        case PresentationKind::trigger_switch:
            return physical >= 0.5F ? "On" : "Off";
        case PresentationKind::rate: {
            const auto index = static_cast<std::size_t>(std::clamp(
                static_cast<int>(std::lround(physical)), 0, 15));
            const auto& rate = rateTable()[index];
            return std::to_string(rate.numerator) + "/"
                + std::to_string(rate.denominator);
        }
        case PresentationKind::phase:
            return std::to_string(static_cast<int>(std::lround(physical)))
                + "/127";
        case PresentationKind::shape:
            return shapeName(static_cast<Shape>(std::clamp(
                static_cast<int>(std::lround(physical)), 0, 7)));
        case PresentationKind::hits:
            return std::to_string(static_cast<int>(std::lround(physical)))
                + "/16";
        case PresentationKind::rotation:
            return "Step "
                + std::to_string(static_cast<int>(std::lround(physical)));
        case PresentationKind::repeat:
            return physical < 0.5F
                ? std::string{"Free"}
                : "x" + std::to_string(static_cast<int>(std::lround(physical)));
        case PresentationKind::bpm:
            return compactNumber(physical, 3) + " BPM";
        case PresentationKind::disabled:
            return "-";
    }
    return "?";
}

float vst3ReadNormalizedParameter(
    const Controls& controls,
    std::size_t parameter_index) noexcept {
    const auto& descriptors = vst3ParameterDescriptors();
    if (parameter_index >= descriptors.size()) return 0.0F;
    const auto& descriptor = descriptors[parameter_index];
    return vst3NormalizePhysical(descriptor, readPhysical(controls, descriptor));
}

bool vst3ApplyNormalizedParameter(
    Controls& controls,
    std::size_t parameter_index,
    float normalized) noexcept {
    const auto& descriptors = vst3ParameterDescriptors();
    if (parameter_index >= descriptors.size() || !std::isfinite(normalized)) {
        return false;
    }
    const auto& descriptor = descriptors[parameter_index];
    const auto physical = vst3DenormalizeParameter(descriptor, normalized);
    const auto lane = std::min<std::size_t>(descriptor.lane, kLaneCount - 1U);
    switch (descriptor.target) {
        case Vst3ParameterTarget::tempo:
            controls.tempo_milli_bpm = static_cast<std::uint32_t>(std::lround(
                static_cast<double>(physical) * 1000.0));
            break;
        case Vst3ParameterTarget::lane_rate:
            controls.lanes[lane].rate_index = static_cast<std::uint8_t>(std::lround(physical));
            break;
        case Vst3ParameterTarget::lane_phase:
            controls.lanes[lane].phase_u7 = static_cast<std::uint8_t>(std::lround(physical));
            break;
        case Vst3ParameterTarget::lane_shape:
            controls.lanes[lane].shape = static_cast<Shape>(
                static_cast<std::uint8_t>(std::lround(physical)));
            break;
        case Vst3ParameterTarget::lane_hits:
            controls.lanes[lane].hits = static_cast<std::uint8_t>(std::lround(physical));
            break;
        case Vst3ParameterTarget::lane_rotation:
            controls.lanes[lane].rotation = static_cast<std::uint8_t>(std::lround(physical));
            break;
        case Vst3ParameterTarget::lane_probability:
            controls.lanes[lane].probability = physical;
            break;
        case Vst3ParameterTarget::lane_repeat:
            controls.lanes[lane].repeat = static_cast<std::uint8_t>(std::lround(physical));
            break;
        case Vst3ParameterTarget::lane_amplitude:
            controls.lanes[lane].amplitude = physical;
            break;
        case Vst3ParameterTarget::lane_route:
            controls.lanes[lane].routes[std::min<std::size_t>(
                descriptor.element, kDestinationCount - 1U)] = physical;
            break;
        case Vst3ParameterTarget::voice_engine:
            controls.voices[lane].engine = static_cast<std::uint8_t>(std::lround(physical));
            break;
        case Vst3ParameterTarget::voice_note: controls.voices[lane].note = physical; break;
        case Vst3ParameterTarget::voice_harmonics: controls.voices[lane].harmonics = physical; break;
        case Vst3ParameterTarget::voice_timbre: controls.voices[lane].timbre = physical; break;
        case Vst3ParameterTarget::voice_morph: controls.voices[lane].morph = physical; break;
        case Vst3ParameterTarget::voice_decay: controls.voices[lane].decay = physical; break;
        case Vst3ParameterTarget::voice_colour: controls.voices[lane].lpg_colour = physical; break;
        case Vst3ParameterTarget::voice_level: controls.voices[lane].level = physical; break;
        case Vst3ParameterTarget::cohesion_drive: controls.cohesion.drive = physical; break;
        case Vst3ParameterTarget::cohesion_cohere: controls.cohesion.cohere = physical; break;
        case Vst3ParameterTarget::cohesion_root: controls.cohesion.root_note = physical; break;
        case Vst3ParameterTarget::cohesion_spread: controls.cohesion.spread = physical; break;
        case Vst3ParameterTarget::cohesion_tail: controls.cohesion.tail = physical; break;
        case Vst3ParameterTarget::cohesion_damping: controls.cohesion.damping = physical; break;
        case Vst3ParameterTarget::cohesion_width: controls.cohesion.width = physical; break;
        case Vst3ParameterTarget::cohesion_duck: controls.cohesion.duck = physical; break;
        case Vst3ParameterTarget::master_gain: controls.master_gain = physical; break;
        case Vst3ParameterTarget::running: controls.running = physical >= 0.5F; break;
    }
    return true;
}

Vst3ProgramState defaultVst3ProgramState() noexcept {
    return vst3ProgramFromControls(defaultControls());
}

Vst3ProgramState vst3ProgramFromControls(const Controls& controls) noexcept {
    const auto accepted = sanitizeControls(controls);
    Vst3ProgramState result{};
    for (std::size_t index = 0; index < result.normalized.size(); ++index) {
        result.normalized[index] = vst3ReadNormalizedParameter(accepted, index);
    }
    result.seed = accepted.seed;
    result.selected_page = accepted.selected_page;
    result.lane_control_mode = accepted.lane_control_mode;
    return result;
}

Controls vst3ControlsFromProgram(
    const Vst3ProgramState& program,
    std::uint32_t effect_clear_generation) noexcept {
    if (!validVst3ProgramState(program)) return defaultControls();
    auto result = defaultControls();
    for (std::size_t index = 0; index < program.normalized.size(); ++index) {
        static_cast<void>(vst3ApplyNormalizedParameter(
            result, index, program.normalized[index]));
    }
    result.seed = program.seed;
    result.selected_page = program.selected_page;
    result.lane_control_mode = program.lane_control_mode;
    result.effect_clear_generation = effect_clear_generation;
    return sanitizeControls(result);
}

bool validVst3ProgramState(const Vst3ProgramState& program) noexcept {
    if (program.selected_page >= kPageCount
        || (program.lane_control_mode != LaneControlMode::voice
            && program.lane_control_mode != LaneControlMode::motion)) {
        return false;
    }
    return std::all_of(
        program.normalized.begin(),
        program.normalized.end(),
        [](float value) {
            return std::isfinite(value) && value >= 0.0F && value <= 1.0F;
        });
}

std::optional<std::size_t> vst3ParameterIndexForId(
    std::string_view id) noexcept {
    const auto& descriptors = vst3ParameterDescriptors();
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        if (descriptors[index].id == id) return index;
    }
    return std::nullopt;
}

std::optional<std::size_t> vst3ParameterIndexForSurface(
    const Controls& controls,
    SurfaceRow row,
    std::size_t column) noexcept {
    if (column >= kSurfaceColumnCount || controls.selected_page >= kPageCount) {
        return std::nullopt;
    }
    const auto page = static_cast<std::size_t>(controls.selected_page);
    if (page == kGlobalPageIndex) {
        if (row == SurfaceRow::top) return kCohesionStart + column;
        if (column == 0U) return 0U;
        if (column == 1U) return kMasterIndex;
        return std::nullopt;
    }
    if (row == SurfaceRow::bottom) {
        if (column == 0U) return kTimelineStart + page * 2U;
        if (column == 1U) return kTimelineStart + page * 2U + 1U;
        return kDecisionStart + page * 6U + (column - 2U);
    }
    if (controls.lane_control_mode == LaneControlMode::motion) {
        return kMotionStart + page * kDestinationCount + column;
    }
    if (controls.lane_control_mode == LaneControlMode::voice) {
        return kVoiceStart + page * 8U + column;
    }
    return std::nullopt;
}

std::uint64_t vst3ParameterContractFingerprint() noexcept {
    std::uint64_t result = UINT64_C(14695981039346656037);
    for (const auto& descriptor : vst3ParameterDescriptors()) {
        fnvText(result, descriptor.id);
        fnvText(result, descriptor.name);
        fnvText(result, descriptor.unit);
        fnvU32(result, static_cast<std::uint32_t>(descriptor.target));
        fnvU32(result, static_cast<std::uint32_t>(descriptor.presentation));
        fnvU32(result, descriptor.lane);
        fnvU32(result, descriptor.element);
        fnvFloat(result, descriptor.minimum);
        fnvFloat(result, descriptor.maximum);
        fnvFloat(result, descriptor.default_physical);
        fnvU32(result, descriptor.step_count);
    }
    return result;
}

}  // namespace schuss::pamplist
