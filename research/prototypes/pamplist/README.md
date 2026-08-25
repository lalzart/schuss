# Pamplist 0.6

Pamplist is a noncanonical Instrument Lab prototype with seven independent
clock lanes and seven persistent 24-model macro voices. Page 8 is not another
voice: it owns the shared clock, final output level, and one clearable resonant
body after the seven voices have been mixed.

Revision 0.6 presents exactly 16 rotary controls at once. The top eight change
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

Three interaction details are important: Phase changes a lane's alignment but
not its rate or tone; Shape is audible only when at least one continuous Motion
destination is away from `DIRECT`; Rotate has no distinct result when Hits is
0 or 16. These dependencies are also stated in the app tooltips.

The similarly named Voice and Motion controls are not duplicates. For example,
Voice `MORPH` is the base setting; Motion `MORPH` is how far this lane is
allowed to move that setting.

## Global page

The Global top row is the shared cohesion body:

- `DRIVE` pushes its excitation; `COHERE` moves from the exact dry seven-voice
  mix toward that body.
- `ROOT` and `SPREAD` tune its six modes; `TAIL` and `DAMP` shape the decay.
- `WIDTH` opens it in stereo; `DUCK` makes room for new dry attacks.

All of those body controls require `COHERE` above zero. Revision 0.6 raises the
existing modal return and Duck range so their effect is musically legible,
while Cohere zero remains byte-identical to the revision 0.5 dry mix.

The Global bottom row has `BPM`, `MASTER`, and six visibly disabled positions.
`CLEAR FX` (or a second press of the Global controller button) removes only the
body's resonant history. It does not reset lanes, voices, transport, or source
randomness. The button changes to `CLEARED` when the audio Core accepts it.

## Impact trails

The persistent display is deliberately not an oscilloscope. It shows about
9.6 seconds of recent percussive activity in seven horizontal rows:

- each lane keeps its own established colour;
- brighter marks mean more post-Level, pre-Cohesion sound energy;
- bright sparks mean one or more triggers arrived during that display slice;
- pink haze is energy added or changed by the shared Cohesion body; and
- a vertical pink line marks an accepted Clear.

The display reads cumulative accepted-state telemetry. It never reads the
audio buffers from the paint thread, and a transport reset clears the history
instead of drawing a false full-scale hit.

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
- the revision 0.4 six-mode cohesion body, smoothing, and effect-only Clear
  design. Revision 0.6 changes only its existing modal-return and Duck gain
  staging; no second effect was added.

Fresh Pamplist 0.6 code is the cumulative per-lane energy telemetry, portable
activity reducer and fixed history, JUCE Impact Trails component, clearer
dependency tooltips, accepted Clear feedback, and their tests/evidence. No
other library instrument's visualizer or DSP was copied into this revision.
The retained seven-voice dry audio is byte-identical to revision 0.5.

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

## Private local VST3 adapter

Task 045 added a separate, noncanonical VST3 build under `vst3/`; Task 047
extends that adapter with bounded output resampling without changing the frozen
standalone or Task 043 authority closure. The adapter is an arm64 instrument
with no audio input, stereo output, host MIDI input, exactly 178 musical
parameters plus persistent `Run`, and a versioned fresh-Core recall rule.
`Clear FX` remains a one-shot and is never saved into a Live Set.

Build the uninstalled Release bundle from an authenticated JUCE 8.0.15 tree:

```sh
cmake -S research/prototypes/pamplist/vst3 \
  -B build/pamplist-vst3-task047-release \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DPAMPLIST_JUCE_SOURCE_DIR=/path/to/authenticated/juce-8.0.15 \
  -DPAMPLIST_ALLOW_JUCE_FETCH=OFF
cmake --build build/pamplist-vst3-task047-release \
  --target pamplist-vst3-module-tests --parallel
ctest --test-dir build/pamplist-vst3-task047-release \
  -C Release --output-on-failure -R '^pamplist_vst3_'
```

The resulting bundle stays under
`build/pamplist-vst3-task047-release/pamplist-vst3_artefacts/Release/VST3/`;
the build never copies it to a plug-in folder. The authenticated JUCE wrapper
also exposes one standard bypass parameter and its non-automatable VST3 MIDI-CC
service parameters; the 179 Pamplist-owned parameters remain first, unique,
and exhaustively tested. Its musical Core remains exactly 48 kHz; the VST3
accepts 32, 44.1, 48, 88.2, 96, 176.4, and 192 kHz hosts, exactly bypasses the
converter at 48 kHz, and reports conversion latency to the host. Other rates
and non-bypass callbacks above 8,192 frames fail closed to silence.

These commands do not launch the app. Revision 0.6 evidence lives in
`contract-r06/`; older contracts remain historical authority for their own
designs. The historical Task 045 VST3 contract and receipt live in
`contract-vst3-r01/`; Task 047 evidence and current receipts live in
`../vst3-resampling/contract-r01/`.
No retained check proves Ableton operation, live deadline, physical endpoint,
listening, embedded, distribution, or production behavior.
