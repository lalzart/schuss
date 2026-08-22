# Wirefall revision 0.2 Instrument Lab prototype

Wirefall 0.2 is a non-production `new-design` Instrument Lab v1 consumer. Its
musical center is deliberately small:

- **ENERGY** is the large, sensitive main gesture. It raises fundamental pitch,
  harmonic density, tracked squeal, filter energy, and level continuously.
- **BREAK** controls how deeply the main stream is interrupted.
- **PULSE** selects `OFF`, x1/2, x1, x2, x3, x4, x6, or x8 per beat without
  resetting normalized pulse phase.
- **TICK** moves the interruption from exact silence toward a short marker.

ROOT, COLOR, WIDTH, EDGE, SPACE, OUTPUT, and TEMPO are supporting settings.
OPEN, TICK PREVIEW, DOWNBEAT, PANIC, and RESET are implemented as semantic
actions. The standalone presents all controls with mouse input and projects
accepted Core state back into its controls.

The portable C++17 Core owns the complete synthesis, pulse, gate, tick,
transition, fixed-buffer, and diagnostic state. Instrument Lab supplies shared
artifact and authenticated-host mechanics only. The desktop source consumes
JUCE 8.0.15 from an existing local authenticated tree with fetching disabled.

## Evidence and boundary

The ready contract, Core focused tests, four-condition objective render matrix,
and authenticated standalone target build pass. In particular, full BREAK with
TICK zero reaches exact digital silence, while the tick condition uses the same
pulse schedule. All declared block partitions and the repeat produced exact WAV
and event bytes.

The app was **built but not launched**. There is no application, fresh visual,
audio-device, callback-deadline, physical-control, listening, packaging,
distribution, or production-integration evidence. This subtree allocates no
canonical Schuss identity.

See `contract/RESULTS.md`, `contract/GAPS.md`, and
`results/wirefall-r02-objective-summary.json` for the retained evidence and
limits.

## Reproduction

Core-only:

```sh
cmake -S research/prototypes/wirefall-r02 -B build/wirefall-r02-core \
  -DWIREFALL_R02_ENABLE_JUCE=OFF
cmake --build build/wirefall-r02-core -j4
ctest --test-dir build/wirefall-r02-core --output-on-failure \
  -R '^wirefall_r02_core_tests$'
python3 research/prototypes/wirefall-r02/tests/validate_render_matrix.py \
  build/wirefall-r02-core/wirefall_r02_render \
  --output build/wirefall-r02-results
```

Authenticated target build, only after the objective command passes:

```sh
cmake -S research/prototypes/wirefall-r02 -B build/wirefall-r02-juce \
  -DWIREFALL_R02_ENABLE_JUCE=ON \
  -DWIREFALL_R02_JUCE_SOURCE_DIR=/operator/authenticated/JUCE-8.0.15
cmake --build build/wirefall-r02-juce \
  --target wirefall-r02-instrument -j4
```

Neither command launches the application.
