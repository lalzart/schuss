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

The exact 21-file Mutable/Ksoloti closure is retained once in
`packages/dsp_sources/mutable_ksoloti_v1`. Tide Pit resolves its three linked
resource/unit translation units from that physical package while keeping the
compiled target, numeric profile, random ownership, arena, overlays, and
sanitizer/optimization flags local. Accepted
`schuss-source-release-000005@1` remains authoritative for upstream identity,
provenance, and license/distribution review state.

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

## Private local VST3 adapter

The standalone remains fixed at 48 kHz. Task 047 extends the separate private
macOS arm64 VST3 adapter with bounded output resampling while the musical Core
continues to run at exactly 48 kHz. The VST3 accepts 32, 44.1, 48, 88.2, 96,
176.4, and 192 kHz hosts, bypasses the converter exactly at 48 kHz, and reports
its conversion latency to the host. Other rates and non-bypass callbacks above
8,192 frames fail closed to silence.

Build the uninstalled Release bundle from an authenticated JUCE 8.0.15 tree:

```sh
python3 research/prototypes/tide-pit-gills/vst3/tests/build_vst3.py \
  --juce-source /path/to/authenticated/juce-8.0.15
```

The build remains under `build/tide-pit-vst3-task047-release/`; it does not
install or launch the plug-in. Task 047 evidence and both current build receipts
live in `research/prototypes/vst3-resampling/contract-r01/`. Offline module
tests do not prove Ableton behavior, callback deadlines, physical MIDI,
listening quality, distribution readiness, or production integration.

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

## Desktop state and oscilloscope

The button faces show the state accepted by the Core rather than only their
action names: Source shows REED/RND/FOLD, Lock and Freeze show ON/OFF, FX Mode
shows CLEAN/FILT/DRIVE, Target shows PIT/BODY/GRAIN/ALL, and Scale shows the
active scale. Mutate briefly shows `DONE` only after its action count advances.
This feedback works for mouse and MIDI input because both paths are read back
from the same Core snapshot.

The stereo output scope overlays 1,024 recent left/right samples (about 21 ms
at 48 kHz) and reports the peak level for each channel. Its audio-thread side
uses fixed storage and a bounded mailbox; painting, path construction, and text
formatting stay on the UI thread. It is a performance display, not a triggered
measurement oscilloscope, and no real-time deadline claim is made.

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
