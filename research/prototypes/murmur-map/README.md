# Murmur Map 0.1

Murmur Map is a noncanonical standalone Instrument Lab prototype. You author
four sound places on a two-dimensional map, let a seeded walker travel between
them, and decide how much of its destination history to keep. `MEMORY` at zero
continually writes fresh choices; at maximum it replays the visible route ring
exactly. `ROAM`, `HOME`, and `RADIUS` separate route behavior from sound-state
interpolation rather than collapsing them into one random amount.

The portable C++17 Core owns the musical state. JUCE supplies only the macOS
audio/MIDI lifecycle and presentation. Three fixed Braids-backed lanes provide
contrasting roles:

- **Anchor** — sine/triangle voice on every route arrival.
- **Thread** — FM voice on half-quarter musical ticks.
- **Spark** — filtered-noise voice on quarter-quarter musical ticks.

Continuous sound fields blend over the map. Pitch, probability, timbre,
envelope, level, and pan are frozen into each event when it is born, so changing
a waypoint does not rewrite an already sounding event.

## Launch Control 3 map

The standalone uses the repository's regular Launch Control 3 Custom Mode
topology: MIDI channel 16, encoders CC20-35, and momentary buttons CC40-47.

| Physical control | Murmur Map control |
|---|---|
| Top encoders CC20-27 | Tempo, Travel, Memory, Length, Roam, Home, Radius, Density |
| Bottom encoders CC28-35 | Selected draft lane: Interval, Activity, Timbre, Color, Decay, Level, Pan; then global Root |
| Buttons CC40-43 | Select waypoint A-D |
| Buttons CC44-46 | Select Anchor, Thread, or Spark |
| Button CC47 | Capture/Replace the complete selected draft |

Buttons act only on value 127; release value 0 is accepted without firing a
second action, and intermediate values fail closed. Draft edits do not affect
sound until Capture. Selecting another waypoint or lane discards an uncommitted
draft and increments the visible discard count.

The app exposes explicit audio start, MIDI-input refresh/selection, endpoint
state, receipt count, ignored count, last channel/CC/value, route/event counts,
and fault counters. It tries the first input whose name contains
`Launch Control 3` only after the user presses **Start Audio**. No outbound LED
feedback is implemented in revision 0.1.

## Build and validation

From the repository root, the focused portable checks are:

```sh
python3 research/prototypes/murmur-map/tests/run_structural.py --check
python3 research/prototypes/murmur-map/tests/render_evidence.py \
  --reproduce --output build/murmur-map-evidence
```

Build the standalone against an exact authenticated JUCE 8.0.15 source tree:

```sh
python3 research/prototypes/murmur-map/tests/build_juce.py \
  --build-dir build/murmur-map-juce-release \
  --juce-source-dir /absolute/path/to/authenticated/JUCE-8.0.15
```

The output is:

```text
build/murmur-map-juce-release/murmur-map_artefacts/Release/Murmur Map.app
```

Building does not launch or install the app. The retained source, structural,
offline-signal, and target-build checks do not establish live callback timing,
physical controller behavior, listening quality, distribution readiness, or a
canonical Schuss instrument/provider identity.

## Evidence boundary

The approved proposal remains frozen at
[`research/proposals/modular-generative-juce-instrument-study.md`](../../proposals/modular-generative-juce-instrument-study.md).
The implementation boundary and deferred work are recorded in `contract/`,
with exact reusable source identities in `source-dependencies.json`.
