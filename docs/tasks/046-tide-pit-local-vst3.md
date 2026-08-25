# Task 046: Tide Pit local VST3 host adapter

Status: completed in the current working tree by the user's 2026-08-25
implementation request; no installation, Ableton launch, endpoint, device,
Git, or publication action was authorized or performed.

## Goal and why it exists

Create a dependable private-use macOS arm64 VST3 of Tide Pit Gills 0.1 so the
existing instrument can run directly on an Ableton Live MIDI track for local
recording, freezing, resampling, and layering. This task adds one bounded host
form around the frozen Tide Pit Core; it does not change the instrument or make
JUCE/VST3 a canonical Schuss provider or runtime.

## In scope

- The frozen Task 046 source-reimplementation proposal and readiness bundle.
- One authenticated JUCE 8.0.15 arm64 VST3 instrument with zero inputs, stereo
  output, MIDI input, exact 48 kHz operation, and no copy-after-build install.
- Exact reuse of Tide Pit's Core, Q27 host bridge, controller map, UI model,
  source lock, defaults, fixed seed, state behavior, and existing oracle.
- Sixteen stable adapter parameters: eleven continuous source controls plus
  desired Source, Lock, FX Mode, Target, and Scale state.
- Mutate and Freeze as non-persistent editor/MIDI one-shots; fresh volatile Core
  state on recall, with captured audio and mutation/timeline history excluded.
- Versioned transactional state, arbitrary host blocks through the existing
  16-frame bridge, sample-offset channel-16 CC handling, and accepted-state UI.
- Focused model/processor/allocation/module tests, exact direct-Core comparison,
  authenticated target build, affected Tide Pit regressions, `current`, and one
  relocated reproduction.

## Out of scope

- Tide Pit DSP/default/scale/random/gesture/source/oracle/controller changes or
  edits to its retained standalone authority.
- Captured-buffer serialization, host tempo, note-trigger redesign, audio input,
  sidechain, MIDI output, sample export, preset browser, or rate conversion.
- Other plug-in formats, platforms, architectures, installer, identity signing,
  notarization, packaging, distribution, or production promotion.
- Canonical catalog/graph/component/binding/provider/runtime work, a generic
  plug-in system, or Pamplist/Layerwell/Gills firmware changes.
- Installing/copying the bundle, launching Ableton/apps, opening endpoints,
  physical controller/device use, structured listening, real-time promotion,
  staging, committing, pushing, or publication.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADRs 0016-0018,
   `docs/workflows/instrument-development.md`, and live governance.
2. `research/proposals/tide-pit-vst3-local.md` and its exact source hashes.
3. The clean Tide Pit prototype subtree, original Gills six-file authority,
   authenticated shared Mutable package, and JUCE 8.0.15 manifest.
4. The read-only local Ableton Live 12.4.1 architecture/version observation.
5. Existing Tide Pit source/Core/control/UI/MIDI/render and standalone evidence.

### Deliverables

1. Ready bundle `research/prototypes/tide-pit-gills/contract-vst3-r01/`.
2. JUCE-independent parameter/program model and focused tests.
3. Isolated `research/prototypes/tide-pit-gills/vst3/` processor, editor, entry,
   state, allocation, direct-signal, and module-host test seam.
4. Authenticated opt-in VST3 CMake target with fetching and installation off.
5. Uninstalled Release `Tide Pit.vst3`, portable receipt, results, gaps, and
   relocated reproduction result.

## Acceptance tests

1. Proposal, source, dependency, original Gills, and JUCE fingerprints pass the
   ready gate before plug-in code is written.
2. Exactly sixteen stable adapter parameters have unique IDs, exact domains,
   defaults/quantization, complete mapping, and a frozen fingerprint.
3. State validates schema/fingerprint/cardinality/IDs/values completely before
   applying and rejects malformed bytes without partial mutation.
4. Recall resets the Core and restores continuous/persistent desired state via
   existing source gestures, never replaying Mutate/Freeze or claiming captured
   audio, mutation, tail, timeline, diagnostic, or scope restoration.
5. At 48 kHz, processor PCM and accepted traces match the direct Core/bridge for
   controls, raw timestamped CCs, actions, recall, and the declared block matrix.
6. Unsupported rates/layouts and invalid/overflow inputs fail to silence or
   bounded deterministic drops; repeated processing has no adapter-owned heap,
   lock, file, endpoint, paint, JSON, or unbounded callback work.
7. Two instances are independent; editor create/destroy opens no endpoint and
   feeds no duplicate control event.
8. The exact arm64 Release bundle exposes one zero-input/stereo-output VST3
   instrument, scans and instantiates in a separate JUCE VST3 host, round-trips
   state, creates/destroys an editor, and emits the expected nonzero fixture.
9. Existing affected Tide Pit checks, authenticated standalone target, Schuss
   `current`, and one relocated VST3 reproduction pass after freeze.
10. Results keep all evidence levels separate and explicitly leave Live,
    real-time, physical-controller, listening, distribution, and production open.

## Decisions

### Task 046 may make

- Prototype-local VST3 identifiers, target/bundle names, parameter IDs, state
  schema, processor/editor classes, fixed capacities, dimensions, fixtures,
  receipt fields, and bounded host error presentation.
- The smallest desired-state reconciliation and fresh-Core recall rule that
  uses existing source gestures and does not invent musical behavior.
- Exact focused/native/reproduction checks inside this task's evidence ceiling.

### Task 046 must not make

- New Tide Pit behavior, source equivalence, canonical Schuss semantics, a
  provider/runtime/binding claim, or hidden evolving-Core serialization.
- A Live, real-time, device, listening, licensing/distribution, or production
  conclusion from source, offline signal, scanner, or target-build evidence.
- Mutation of external/configured/JUCE trees, frozen standalone bytes, inherited
  Task 043-045 changes, plug-in folders, applications, devices, Git state, or
  publication state.

## Validation classification

- Focused: ready-bundle validation; parameter model; processor state, MIDI,
  actions, partitions, negative cases, lifecycle, allocation, and multi-instance
  tests; separate VST3 module scan/instantiate/editor/state/render tests.
- Adjacent: existing Tide Pit Core/source/control/UI/MIDI/render suites and
  authenticated standalone target build.
- Configured/native: one final source/JUCE authentication, Release arm64 VST3
  build, architecture/metadata inspection, and applicable sanitizer checks.
- Reproduction: one copied-root Release VST3/module-host reproduction using
  runtime-only source/JUCE paths.
- Routine: `current` once after implementation/documentation freeze.
- Compatibility/release: not required because this is an isolated prototype host
  adapter and changes no shared schema, provider/runtime, canonical record, or
  distribution boundary.

## Evidence ceiling and stop condition

Stop when the ready source-equivalence contract, stable parameter/state model,
processor/editor, uninstalled arm64 VST3, direct/module-host evidence, affected
regressions, `current`, and one relocation reproduction pass with exact results
and gaps recorded. Completion proves at most target build and offline host
signal. It does not authorize copying/installing the plug-in, launching Live,
opening endpoints, accessing hardware, listening promotion, Git, distribution,
or production action.
