# Pamplist 0.5

Pamplist is a noncanonical Instrument Lab prototype with seven independent
clock lanes and seven persistent 24-model macro voices. Page 8 is not another
voice: it owns the shared clock, final output level, and one clearable resonant
body after the seven voices have been mixed.

Revision 0.5 presents exactly 16 rotary controls at once. The top eight change
with the accepted page/context; the bottom eight stay together as a coherent
row. Hover any label or knob in the app for a short explanation.

## Lane pages: Voice, Motion, Sequencer

Each lane has two views of the same independent lane/voice record:

- `VOICE` top row: `MODEL`, `PITCH`, `HARMONICS`, `TIMBRE`, `MORPH`, `DECAY`,
  `COLOUR`, `LEVEL`. These set the lane's starting sound directly. Model shows
  its accepted number and source-order engine name; the banner also shows the
  currently resolved model after motion.
- `MOTION` top row: `TRIGGER`, `PITCH`, `MODEL SWEEP`, `HARMONICS`, `TIMBRE`,
  `MORPH`, `DECAY`, `LEVEL`. These decide where the lane's moving shape is
  sent. `DIRECT` means no motion at that destination. Trigger is deliberately
  just `OFF` or `ON`; click its app knob to toggle it. There is no misleading
  negative Trigger range.
- `SEQUENCER` bottom row in both views: `RATE`, `PHASE`, `SHAPE`, `HITS`,
  `ROTATE`, `CHANCE`, `REPEAT`, `DEPTH`. Rate is relative to the global BPM;
  Hits/Rotate form the 16-step pattern; Chance accepts or skips its hits;
  Repeat loops the deterministic variation (`FREE` does not loop it); Depth is
  the overall lane-shape amount.

The similarly named Voice and Motion controls are not duplicates. For example,
Voice `MORPH` is the base setting; Motion `MORPH` is how far this lane is
allowed to move that setting.

## Global page

The Global top row is the shared cohesion body:

- `DRIVE` pushes its excitation; `COHERE` moves from the exact dry seven-voice
  mix toward that body.
- `ROOT` and `SPREAD` tune its six modes; `TAIL` and `DAMP` shape the decay.
- `WIDTH` opens it in stereo; `DUCK` makes room for new dry attacks.

The Global bottom row has `BPM`, `MASTER`, and six visibly disabled positions.
`CLEAR FX` (or a second press of the Global controller button) removes only the
body's resonant history. It does not reset lanes, voices, transport, or source
randomness.

## Regular Launch Control 3

Use Custom Mode 1 on MIDI channel 16:

- Buttons 1-7 (`CC40-46`) select lanes. Press the already-selected lane again
  to switch Voice/Motion once; a held press and release do not repeat it.
- Button 8 (`CC47`) enters Global. Release and press it again while Global is
  selected to Clear once.
- Top encoders (`CC20-27`) follow Voice, Motion, or Global.
- Bottom encoders (`CC28-35`) are always Sequencer on a lane. On Global they
  are BPM, Master, then six counted no-ops.
- In Motion, Trigger maps `0-63` to Off and `64-127` to On.

The standalone distinguishes GUI injection from physical receipt. Audio and
MIDI stay off until you explicitly start audio, refresh the MIDI list, and
select an endpoint. Repository tests prove the synthetic mapping, not an
installed Custom Mode or physical controller session.

## What is reused and what is fresh

Reused unchanged from earlier Pamplist revisions:

- the rational scheduler, Euclidean patterns, lane shapes, deterministic
  Chance/Repeat decisions, lane-local routing, signed 64-bit dry mixer, and
  whole-state snapshot/controller seam;
- seven authenticated Macro Voice source instances and the thin adapter that
  gives each instance its own deterministic random context;
- the revision 0.4 six-mode cohesion body, smoothing, ducking, effect-only
  Clear, and all voice/audio equations.

Fresh Pamplist 0.5 code is the accepted Voice/Motion context, contextual
controller transforms, binary Trigger acceptance, portable 16-slot surface
model, JUCE grouping/tooltips/value formatting, and their tests/evidence. No
other library instrument's DSP was copied into this revision. With Trigger On,
the retained seven-voice dry audio is byte-identical to revision 0.4.

## Build and validate

```sh
python3 research/prototypes/pamplist/tests/verify_source_authority.py
python3 research/prototypes/pamplist/tests/run_focused.py
python3 research/prototypes/pamplist/tests/render_evidence.py --check
python3 research/prototypes/pamplist/tests/build_juce.py --check
```

A fresh standalone build needs an operator-supplied authenticated JUCE 8.0.15
tree:

```sh
python3 research/prototypes/pamplist/tests/build_juce.py \
  --reproduce --juce-source /path/to/authenticated/juce-8.0.15
```

These commands do not launch the app. Revision 0.5 evidence lives in
`contract-r05/`; older contracts remain historical authority for their own
designs. No retained check proves live deadline, physical endpoint, listening,
embedded, distribution, or production behavior.
