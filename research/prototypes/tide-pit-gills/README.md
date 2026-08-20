# Tide Pit Gills portable JUCE prototype

Tide Pit Gills is an isolated, source-faithful desktop reimplementation of the
original Gills instrument. The musical DSP stays in a JUCE-independent C++17
Core; JUCE supplies the standalone window, audio/MIDI device shell, and offline
WAV renderer. It does not add a Schuss catalog object, runtime provider, plugin
format, or production controller graph.

The implementation is fixed at 48 kHz. Internally it preserves Tide Pit's
original 16-sample processing quantum, Q27 boundary, random streams, source
timing, four scales, three source modes, three effects, granular recorder, and
display state. The continuous startup values shown by the desktop app are a
labelled audition preset because the Gills source reads physical pots and does
not define canonical continuous defaults.

One build-time portability overlay replaces two undefined signed left shifts in
the original voice with defined multiplication by two. The generator verifies
the exact source hash, the result stays inside int32 range, fail-fast UBSan is
clean, and the canonical output remains byte-identical. Vendored source bytes
are not edited.

## Build and run

Core-only validation does not require JUCE:

```sh
cmake -S research/prototypes/tide-pit-gills \
  -B build/tide-pit-core \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build/tide-pit-core --parallel
ctest --test-dir build/tide-pit-core --output-on-failure
```

Build the offline renderer and standalone against an already authenticated
JUCE 8.0.15 source tree:

```sh
cmake -S research/prototypes/tide-pit-gills \
  -B build/tide-pit-juce \
  -DCMAKE_BUILD_TYPE=Release \
  -DTIDE_PIT_ENABLE_JUCE=ON \
  -DTIDE_PIT_JUCE_SOURCE_DIR=/absolute/path/to/JUCE-8.0.15
cmake --build build/tide-pit-juce --parallel
ctest --test-dir build/tide-pit-juce --output-on-failure
open "build/tide-pit-juce/tide-pit-gills-instrument_artefacts/Release/Tide Pit Gills.app"
```

The last command launches an audio/MIDI application and is intentionally not
part of automated validation. In the app, select a 48 kHz audio device and the
Launch Control 3 MIDI input. Unsupported sample rates fail closed.

## Launch Control 3

Reuse the same regular-model Custom Mode created for Cinderwheel: Custom Mode
slot 1, MIDI channel 16, encoders CC20-35 as 7-bit absolute controls, buttons
CC40-47 as momentary CC with press 127 and release 0, Merge off, MIDI Thru off,
and the main USB MIDI output. No controller rewrite is needed when moving from
Cinderwheel to Tide Pit.

| Physical row | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Top encoders | Stage 1 | Stage 2 | Stage 3 | Stage 4 | Rate | Memory | Material | Position |
| Bottom encoders | FX-A | FX-B | Root | — | — | — | — | — |
| Buttons | Source | Mutate | Lock | Freeze | FX Mode | Target | Scale | — |

FX-A and FX-B retain Tide Pit's contextual soft pickup. After changing effect
mode, turn the encoder through the recalled value before it takes over. The UI
shows the value actually accepted by the Core, so it will not falsely jump to
an uncaptured MIDI value. The controller sends no display or LED feedback.

## What to listen for

- The four Stage controls continuously define the gesture shape; Rate changes
  how quickly it circulates.
- Memory governs automatic mutations, while Mutate forces one and Lock keeps
  the current stage offsets.
- Source cycles REED, RND, and FOLD. Scale cycles MAJ5, MIN5, DOR, and the
  original `HARM` interval set.
- Freeze captures the two-second granular memory. Target cycles PIT, BODY,
  GRAIN, and ALL for stage mutation targeting.
- FX Mode cycles CLEAN, FILT, and DRIVE. FX-A/FX-B are contextual controls and
  remember independent values for each effect.

## Evidence boundary

The exact source lineage, dependency bytes, control graph, experiment, and
reference oracle are machine-readable beside this file. `RESULTS.md` records
the commands and observations after validation; `GAPS.md` keeps real-time,
physical-device, listening, packaging, and production-integration claims
separate. A successful build or offline render does not by itself prove those
later levels.
