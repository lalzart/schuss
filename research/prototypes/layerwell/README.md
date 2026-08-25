# Layerwell

Layerwell is a noncanonical desktop Instrument Lab prototype: two resident
Schuss instruments feed a small, source-only, three-layer live sampler. It does
not require Ableton Live, host separate applications, or capture the current
layer mix.

Revision 0.2 contains exactly two sources—Tide Pit Gills 0.1 and Pamplist
0.6—plus three committed stereo layers and one provisional staging store. The
selected source's complete performance panel is embedded above a permanent
sampler strip. The first valid take establishes a 0.5-to-32-second session loop
at 48 kHz. While exactly one layer is occupied, integer start/end trim changes
the active window without rewriting its captured samples. Later takes wait for
phase zero, record exactly the trimmed cycle, and replace their target only
after a complete capture.

## Build the portable closure

```sh
cmake -S research/prototypes/layerwell -B build/layerwell -DCMAKE_BUILD_TYPE=Release
cmake --build build/layerwell --parallel
ctest --test-dir build/layerwell --output-on-failure -R '^layerwell_'
```

This parent selects only Layerwell's six tests. The resident source projects'
normal standalone CMake files, defaults, and source behavior remain unchanged.
Pamplist's configured Macro Voice source must be present in
`catalog/sources.local.yml` and pass its exact locked-source authentication.
Run the explicit adjacent regression command below to configure and test each
source independently.

## Validation commands

```sh
python3 research/prototypes/layerwell/tests/verify_source_authorities.py
python3 research/prototypes/layerwell/tests/run_focused.py
python3 research/prototypes/layerwell/tests/render_evidence.py --check
python3 research/prototypes/layerwell/tests/run_source_regressions.py
python3 research/prototypes/layerwell/tests/build_juce.py --check
python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/layerwell --check
python3 research/prototypes/layerwell/tests/reproduce_fresh_root.py
```

To reproduce the authenticated target build, supply an already authenticated
JUCE 8.0.15 source tree. Fetching remains disabled:

```sh
python3 research/prototypes/layerwell/tests/build_juce.py --reproduce --juce-source /absolute/path/to/authenticated/juce-8.0.15
```

The command compiles `Layerwell.app`; it does not launch it. The UI keeps audio
and MIDI closed until the user explicitly starts audio or selects endpoints.

## Regular Launch Control 3 surface

- Page Up/Down selects Tide Pit or Pamplist.
- DAW Control gives the selected source its existing 16 encoders and 8 buttons.
- DAW Mixer uses three pan encoders, three level encoders, monitor/master, layer
  select/mute buttons, capture, and source monitor. Top encoders 5 and 6 trim
  start/end by 48 frames per step; holding Shift uses 480-frame steps. Trim is
  read-only once more than one layer is occupied.
- Track Left/Right selects a layer; Shift plus Mixer button 8 clears it.
- Feedback is regenerated from accepted Core snapshots. Raw input is never the
  displayed state.

Only synthetic protocol behavior is proven. No physical endpoint, audio device,
app launch, listening result, distribution approval, or production integration
is claimed.
