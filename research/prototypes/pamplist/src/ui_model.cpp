#include "schuss/pamplist/ui_model.hpp"

#include <algorithm>
#include <cmath>

namespace schuss::pamplist {
namespace {

[[nodiscard]] SurfaceSlot slot(
    SurfaceSemantic semantic,
    std::string_view label,
    std::string_view tooltip,
    PresentationKind presentation,
    double minimum,
    double maximum,
    double interval,
    double value,
    bool enabled = true) noexcept {
    return SurfaceSlot{
        semantic,
        label,
        tooltip,
        presentation,
        minimum,
        maximum,
        interval,
        value,
        enabled,
    };
}

[[nodiscard]] double bounded(
    double value,
    double minimum,
    double maximum) noexcept {
    return std::clamp(value, minimum, maximum);
}

[[nodiscard]] std::uint8_t roundedU8(
    double value,
    std::uint8_t maximum) noexcept {
    return static_cast<std::uint8_t>(std::lround(
        bounded(value, 0.0, static_cast<double>(maximum))));
}

void populateSequence(
    SurfaceModel& result,
    const LaneControls& controls) noexcept {
    result.bottom = {{
        slot(SurfaceSemantic::sequence_rate, "RATE",
            "Clock ratio for this lane relative to the master tempo.",
            PresentationKind::rate, 0.0, 15.0, 1.0, controls.rate_index),
        slot(SurfaceSemantic::sequence_phase, "PHASE",
            "Moves this lane around the shared clock without changing its rate.",
            PresentationKind::phase, 0.0, 127.0, 1.0, controls.phase_u7),
        slot(SurfaceSemantic::sequence_shape, "SHAPE",
            "Motion shape generated on accepted steps.",
            PresentationKind::shape, 0.0, 7.0, 1.0,
            static_cast<std::uint8_t>(controls.shape)),
        slot(SurfaceSemantic::sequence_hits, "HITS",
            "Number of active steps in the lane's 16-step Euclidean pattern.",
            PresentationKind::hits, 0.0, 16.0, 1.0, controls.hits),
        slot(SurfaceSemantic::sequence_rotation, "ROTATE",
            "Rotates the 16-step pattern while keeping the hit count.",
            PresentationKind::rotation, 0.0, 15.0, 1.0, controls.rotation),
        slot(SurfaceSemantic::sequence_chance, "CHANCE",
            "Probability that an active pattern step is accepted.",
            PresentationKind::chance, 0.0, 1.0, 0.001, controls.probability),
        slot(SurfaceSemantic::sequence_repeat, "REPEAT",
            "Repeats the lane's deterministic random address cycle; Free never wraps it.",
            PresentationKind::repeat, 0.0, 64.0, 1.0, controls.repeat),
        slot(SurfaceSemantic::sequence_depth, "DEPTH",
            "Overall amount of lane motion; zero also prevents new triggers.",
            PresentationKind::depth, 0.0, 1.0, 0.001, controls.amplitude),
    }};
}

void populateVoice(
    SurfaceModel& result,
    const VoiceControls& voice) noexcept {
    result.context = SurfaceContext::voice;
    result.top_group = "VOICE SHAPE - direct lane sound";
    result.guide = "VOICE edits the base sound. The lower SEQUENCER row decides when and how the lane moves.";
    result.top = {{
        slot(SurfaceSemantic::voice_model, "MODEL",
            "Base synthesis model for this lane. Model Sweep moves from this model.",
            PresentationKind::model, 0.0, 23.0, 1.0, voice.engine),
        slot(SurfaceSemantic::voice_pitch, "PITCH",
            "Base MIDI note before lane Pitch motion is applied.",
            PresentationKind::note, 24.0, 96.0, 0.01, voice.note),
        slot(SurfaceSemantic::voice_harmonics, "HARMONICS",
            "Primary harmonic structure control for the selected model.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, voice.harmonics),
        slot(SurfaceSemantic::voice_timbre, "TIMBRE",
            "First model-dependent tone or texture control.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, voice.timbre),
        slot(SurfaceSemantic::voice_morph, "MORPH",
            "Second model-dependent tone or texture control.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, voice.morph),
        slot(SurfaceSemantic::voice_decay, "DECAY",
            "Controls the internal low-pass-gate decay time.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, voice.decay),
        slot(SurfaceSemantic::voice_colour, "COLOUR",
            "Controls the low-pass-gate response and brightness.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, voice.lpg_colour),
        slot(SurfaceSemantic::voice_level, "LEVEL",
            "Final level of this voice before the shared cohesion body.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, voice.level),
    }};
}

void populateMotion(
    SurfaceModel& result,
    const LaneControls& controls) noexcept {
    result.context = SurfaceContext::motion;
    result.top_group = "MOTION - lane shape into voice";
    result.guide = "MOTION sets where the lane shape is sent. Direct means no movement; Trigger is simply Off or On.";
    result.top = {{
        slot(SurfaceSemantic::motion_trigger, "TRIGGER",
            "Click the knob to toggle new notes from accepted steps. Off is intentionally silent; On has no negative depth.",
            PresentationKind::trigger_switch, 0.0, 1.0, 1.0,
            controls.routes[static_cast<std::size_t>(Destination::trigger)]),
        slot(SurfaceSemantic::motion_pitch, "PITCH",
            "Signed amount by which lane motion bends the base Pitch.",
            PresentationKind::signed_percent, -1.0, 1.0, 0.001,
            controls.routes[static_cast<std::size_t>(Destination::pitch)]),
        slot(SurfaceSemantic::motion_model_sweep, "MODEL SWEEP",
            "Signed amount by which lane motion walks through models from the base Model.",
            PresentationKind::signed_percent, -1.0, 1.0, 0.001,
            controls.routes[static_cast<std::size_t>(Destination::model)]),
        slot(SurfaceSemantic::motion_harmonics, "HARMONICS",
            "Signed lane motion sent to Harmonics.",
            PresentationKind::signed_percent, -1.0, 1.0, 0.001,
            controls.routes[static_cast<std::size_t>(Destination::harmonics)]),
        slot(SurfaceSemantic::motion_timbre, "TIMBRE",
            "Signed lane motion sent to Timbre.",
            PresentationKind::signed_percent, -1.0, 1.0, 0.001,
            controls.routes[static_cast<std::size_t>(Destination::timbre)]),
        slot(SurfaceSemantic::motion_morph, "MORPH",
            "Signed lane motion sent to Morph.",
            PresentationKind::signed_percent, -1.0, 1.0, 0.001,
            controls.routes[static_cast<std::size_t>(Destination::morph)]),
        slot(SurfaceSemantic::motion_decay, "DECAY",
            "Signed lane motion sent to Decay.",
            PresentationKind::signed_percent, -1.0, 1.0, 0.001,
            controls.routes[static_cast<std::size_t>(Destination::decay)]),
        slot(SurfaceSemantic::motion_level, "LEVEL",
            "Signed lane motion sent to voice Level.",
            PresentationKind::signed_percent, -1.0, 1.0, 0.001,
            controls.routes[static_cast<std::size_t>(Destination::level)]),
    }};
}

void populateGlobal(
    SurfaceModel& result,
    const Controls& controls) noexcept {
    const auto& effect = controls.cohesion;
    result.context = SurfaceContext::global;
    result.top_group = "COHESION - shared resonant body";
    result.bottom_group = "TRANSPORT / OUTPUT";
    result.guide = "COHERE brings all seven voices into one body. Set it to zero for the exact dry mix; Clear removes only the body's history.";
    result.top = {{
        slot(SurfaceSemantic::global_drive, "DRIVE",
            "Pressure into the shared body; it cannot leak when Cohere is zero.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, effect.drive),
        slot(SurfaceSemantic::global_cohere, "COHERE",
            "Crossfades the exact dry seven-voice mix into the shared resonant body.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, effect.cohere),
        slot(SurfaceSemantic::global_root, "ROOT",
            "Root MIDI note used to tune the shared body.",
            PresentationKind::note, 24.0, 84.0, 1.0, effect.root_note),
        slot(SurfaceSemantic::global_spread, "SPREAD",
            "Moves the body's six modes from harmonic toward inharmonic spacing.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, effect.spread),
        slot(SurfaceSemantic::global_tail, "TAIL",
            "Length of the shared resonant decay.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, effect.tail),
        slot(SurfaceSemantic::global_damping, "DAMP",
            "Darkens and shortens high resonant modes.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, effect.damping),
        slot(SurfaceSemantic::global_width, "WIDTH",
            "Stereo spread of the shared body.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, effect.width),
        slot(SurfaceSemantic::global_duck, "DUCK",
            "Makes space in the body for new dry attacks.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001, effect.duck),
    }};
    result.bottom = {{
        slot(SurfaceSemantic::global_bpm, "BPM",
            "Master tempo shared by all seven lane rates.",
            PresentationKind::bpm, 20.0, 300.0, 1.0,
            static_cast<double>(controls.tempo_milli_bpm) / 1000.0),
        slot(SurfaceSemantic::global_master, "MASTER",
            "Final stereo output gain.",
            PresentationKind::unit_percent, 0.0, 1.0, 0.001,
            controls.master_gain),
        slot(SurfaceSemantic::global_unassigned, "-",
            "Unassigned on the Global page.",
            PresentationKind::disabled, 0.0, 1.0, 1.0, 0.0, false),
        slot(SurfaceSemantic::global_unassigned, "-",
            "Unassigned on the Global page.",
            PresentationKind::disabled, 0.0, 1.0, 1.0, 0.0, false),
        slot(SurfaceSemantic::global_unassigned, "-",
            "Unassigned on the Global page.",
            PresentationKind::disabled, 0.0, 1.0, 1.0, 0.0, false),
        slot(SurfaceSemantic::global_unassigned, "-",
            "Unassigned on the Global page.",
            PresentationKind::disabled, 0.0, 1.0, 1.0, 0.0, false),
        slot(SurfaceSemantic::global_unassigned, "-",
            "Unassigned on the Global page.",
            PresentationKind::disabled, 0.0, 1.0, 1.0, 0.0, false),
        slot(SurfaceSemantic::global_unassigned, "-",
            "Unassigned on the Global page.",
            PresentationKind::disabled, 0.0, 1.0, 1.0, 0.0, false),
    }};
}

}  // namespace

SurfaceModel surfaceModel(const Snapshot& snapshot) noexcept {
    SurfaceModel result{};
    result.bottom_group = "SEQUENCER - timing, pattern, and motion shape";
    const auto selected_page = std::min<std::size_t>(
        snapshot.accepted.selected_page, kGlobalPageIndex);
    if (selected_page == kGlobalPageIndex) {
        populateGlobal(result, snapshot.accepted);
        return result;
    }
    const auto& lane = snapshot.accepted.lanes[selected_page];
    if (snapshot.accepted.lane_control_mode == LaneControlMode::motion) {
        populateMotion(result, lane);
    } else {
        populateVoice(result, snapshot.accepted.voices[selected_page]);
    }
    populateSequence(result, lane);
    return result;
}

bool applySurfaceValue(
    Controls& controls,
    SurfaceRow row,
    std::size_t column,
    double value) noexcept {
    if (column >= kSurfaceColumnCount || !std::isfinite(value)
        || controls.selected_page >= kPageCount) {
        return false;
    }
    if (controls.selected_page == kGlobalPageIndex) {
        if (row == SurfaceRow::bottom) {
            if (column == 0U) {
                controls.tempo_milli_bpm = static_cast<std::uint32_t>(
                    std::lround(bounded(value, 20.0, 300.0) * 1000.0));
                return true;
            }
            if (column == 1U) {
                controls.master_gain = static_cast<float>(
                    bounded(value, 0.0, 1.0));
                return true;
            }
            return false;
        }
        auto& effect = controls.cohesion;
        switch (column) {
            case 0U: effect.drive = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            case 1U: effect.cohere = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            case 2U: effect.root_note = static_cast<float>(bounded(value, 24.0, 84.0)); break;
            case 3U: effect.spread = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            case 4U: effect.tail = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            case 5U: effect.damping = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            case 6U: effect.width = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            case 7U: effect.duck = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            default: return false;
        }
        return true;
    }

    auto& lane = controls.lanes[controls.selected_page];
    if (row == SurfaceRow::bottom) {
        switch (column) {
            case 0U: lane.rate_index = roundedU8(value, 15U); break;
            case 1U: lane.phase_u7 = roundedU8(value, 127U); break;
            case 2U: lane.shape = static_cast<Shape>(roundedU8(value, 7U)); break;
            case 3U: lane.hits = roundedU8(value, 16U); break;
            case 4U: lane.rotation = roundedU8(value, 15U); break;
            case 5U: lane.probability = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            case 6U: lane.repeat = roundedU8(value, 64U); break;
            case 7U: lane.amplitude = static_cast<float>(bounded(value, 0.0, 1.0)); break;
            default: return false;
        }
        return true;
    }

    if (controls.lane_control_mode == LaneControlMode::motion) {
        if (column == 0U) {
            lane.routes[0] = value >= 0.5 ? 1.0F : 0.0F;
        } else {
            lane.routes[column] = static_cast<float>(bounded(value, -1.0, 1.0));
        }
        return true;
    }

    auto& voice = controls.voices[controls.selected_page];
    switch (column) {
        case 0U: voice.engine = roundedU8(value, 23U); break;
        case 1U: voice.note = static_cast<float>(bounded(value, 24.0, 96.0)); break;
        case 2U: voice.harmonics = static_cast<float>(bounded(value, 0.0, 1.0)); break;
        case 3U: voice.timbre = static_cast<float>(bounded(value, 0.0, 1.0)); break;
        case 4U: voice.morph = static_cast<float>(bounded(value, 0.0, 1.0)); break;
        case 5U: voice.decay = static_cast<float>(bounded(value, 0.0, 1.0)); break;
        case 6U: voice.lpg_colour = static_cast<float>(bounded(value, 0.0, 1.0)); break;
        case 7U: voice.level = static_cast<float>(bounded(value, 0.0, 1.0)); break;
        default: return false;
    }
    return true;
}

std::string_view surfaceContextName(SurfaceContext context) noexcept {
    switch (context) {
        case SurfaceContext::voice: return "VOICE";
        case SurfaceContext::motion: return "MOTION";
        case SurfaceContext::global: return "GLOBAL";
    }
    return "INVALID";
}

}  // namespace schuss::pamplist
