# Task 045: Pamplist 0.6 local VST3 host adapter

Status: completed locally in the current working tree on 2026-08-25; target-build
and offline host-signal evidence passed, and the work is not committed,
installed, launched in Ableton, or published.

## Goal and why it exists

Create a solid private-use macOS arm64 VST3 of the accepted Pamplist 0.6
instrument so it can run directly inside Ableton Live for recording, sampling,
freezing, resampling, and layering. The task adds one bounded prototype host
form around the frozen Pamplist Core; it does not promote JUCE/VST3 into
canonical Schuss provider or runtime authority.

## In scope

- The frozen Task 045 proposal and Sonic Research Lab source-reimplementation
  readiness bundle before plug-in implementation edits.
- One opt-in JUCE 8.0.15 VST3 instrument target for macOS arm64, with zero audio
  inputs, stereo output, MIDI input, and no copy-after-build installation.
- Exact reuse of the current Pamplist 0.6 Core, Macro Voice source adapter,
  control map, UI model, activity model, defaults, and deterministic seed.
- A stable prototype-local parameter model covering all 178 Pamplist musical
  controls plus a host-only persistent Run value.
- Clear Cohesion as a non-persistent one-shot; selected page and Voice/Motion
  mode as recalled private presentation state; fresh volatile Core state after
  recall.
- Versioned transactional state bytes, unsupported-rate/layout silence,
  arbitrary host-block partitioning into at most 512-frame Core calls, and
  sample-offset channel-16 CC handling through the existing controller adapter.
- A source-faithful editor with the eight-page contextual surface and accepted
  impact history, but no application/device/MIDI-endpoint lifecycle controls.
- Focused model/processor/module tests, deterministic direct-Core parity,
  multi-instance checks, authenticated Release target build, and bounded
  relocation reproduction.

## Out of scope

- Any Pamplist DSP equation, default, control law, controller gesture, source
  dependency, retained 0.6 evidence, or canonical Task 043 record change.
- A canonical implementation binding/provider/runtime, generic plug-in system,
  Tide Pit VST3, Layerwell change, host tempo synchronization, note-trigger
  mode, sidechain, audio input, sample recorder/exporter, or preset browser.
- Other plug-in formats, universal/x86_64 or non-macOS targets, installer,
  codesigning identity, notarization, packaging, distribution, or production
  promotion.
- Copying/installing the VST3, launching Ableton or another app, opening
  audio/MIDI endpoints, physical controller/device work, structured listening,
  callback-deadline promotion, staging, committing, pushing, or publication.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADRs 0016-0018,
   `docs/workflows/instrument-development.md`, and current live governance.
2. Completed but uncommitted Tasks 043 and 044. Task 045 consumes only the
   exact Pamplist authority and preserves unrelated inherited bytes.
3. `research/proposals/pamplist-vst3-local.md` and the exact source fingerprints
   it freezes from Pamplist 0.6, Task 043, the configured `patcher` checkout,
   authenticated JUCE 8.0.15, and local Ableton architecture/version inspection.
4. Pamplist 0.6's existing source verifier, focused suites, retained render
   evidence, standalone target receipt, and prototype freshness checks.

### Deliverables

1. Ready bundle `research/prototypes/pamplist/contract-vst3-r01/` with complete
   source-equivalence, state, control, experiment, and validation contracts.
2. JUCE-independent stable VST parameter/control conversion code and tests.
3. JUCE processor, editor, factory entry, state schema, direct processor tests,
   and separate VST3 module-host tests.
4. Opt-in authenticated CMake VST3 build wiring and updated exact dependency
   notices without installation or source fetching by default.
5. A Release `Pamplist.vst3` in the build tree, target-build receipt, results,
   gap register, validation record, and local completion routing.

## Acceptance tests

1. The proposal fingerprint, readiness bundle, every declared Pamplist input,
   configured Macro Voice checkout, and JUCE source authenticate before plug-in
   implementation begins.
2. Exactly 178 musical parameters plus Run have unique stable adapter IDs,
   complete source domains/defaults/quantization, and exhaustive lossless
   `Controls` mapping within declared quantization.
3. State applies only after complete schema/ID/value validation, restores the
   program, seed, Run, page, and mode, requests a fresh Core on the audio
   thread, excludes Clear, and rejects malformed bytes without partial change.
4. Direct and processor paths match for fixed controls, seed, block matrices,
   timestamped channel-16 CC events, Run, Clear, and recall; output remains
   finite and bounded.
5. Blocks larger than 512 partition safely; invalid sample rates and layouts
   produce deterministic silence; repeated processing performs no allocation,
   lock, file, endpoint, JSON, paint, or unbounded work owned by the adapter.
6. Two instances remain independent and deterministic, and editor
   create/destroy does not open an endpoint or feed accepted values back as
   duplicate events.
7. The Release arm64 bundle exposes one VST3 instrument with zero inputs and
   stereo output, scans and instantiates through a separate JUCE VST3 host,
   round-trips state, and emits the expected nonzero offline fixture.
8. Existing Pamplist focused/adjacent/source/freshness checks, authenticated
   standalone build, Task 043 freshness, Schuss `current`, and one relocated
   VST3 reproduction pass after implementation freeze.
9. Results keep source, host-structural, host-signal, target-build, real-time,
   Live, connected-device, listening, distribution, and production claims
   separate.

## Decisions

### Task 045 may make

- Prototype-local VST3 identifiers, target/bundle names, stable adapter
  parameter IDs, state schema, processor/editor classes, UI dimensions, and
  bounded host error presentation.
- The smallest host-only Run/Clear/page/mode adaptation that preserves source
  behavior and stable state/automation semantics.
- Direct processor and module-host fixtures, PCM/state comparators, build
  receipt fields, and exact final validation selection.

### Task 045 must not make

- New musical behavior, Task 043 canonical meanings, a provider/binding/runtime
  claim, source equivalence beyond frozen bytes, or hidden Core serialization.
- A Live, real-time, device, listening, licensing, distribution, or production
  conclusion from source, offline signal, or target-build evidence.
- Mutation of configured upstream/JUCE trees, unrelated Task 043/044 work,
  plug-in folders, applications, devices, Git index/history/remotes, or
  publication state.

## Validation classification

- Focused: readiness validator; parameter/control model; processor state,
  MIDI, block, negative, lifecycle, allocation, and multi-instance tests;
  VST3 module scan/instantiate/editor/state/render tests.
- Adjacent: all existing Pamplist Core/control/UI/activity/snapshot/allocation
  tests, retained evidence, prototype/source freshness, Task 043 freshness, and
  authenticated standalone target build.
- Configured/native: one final configured source authentication, Release VST3
  and test build, architecture/module metadata inspection, and applicable
  sanitizer checks after implementation freeze.
- Reproduction: one copied-root configured Release VST3/module-host reproduction
  using runtime-only source/JUCE paths.
- Routine: `current` once after implementation and documentation freeze.
- Full compatibility/release: not required because this remains a bounded
  prototype-local host adapter and changes no shared schema, provider/runtime,
  canonical record, or distribution boundary.

## Evidence ceiling and stop condition

Stop when the frozen source-equivalence contract, stable parameter/state model,
processor/editor, arm64 VST3 target, direct/module host evidence, affected
regressions, current profile, and one relocation reproduction pass with exact
results and gaps recorded. Completion proves at most target build and offline
host signal. Do not copy/install the plug-in, launch Ableton, open endpoints,
access hardware, claim real-time/listening/distribution/production success, or
perform a Git/publication action without separate explicit authorization.
