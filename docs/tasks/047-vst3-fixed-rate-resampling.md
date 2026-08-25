# Task 047: Tide Pit and Pamplist fixed-rate VST3 resampling

Status: complete in the current working tree under the user's 2026-08-25
uninterrupted implementation authorization, "Sounds good. Let's go ahead and
implement this." The work is uncommitted and neither plug-in was installed or
launched. Task 047-specific gates and Schuss `current` passed; the sole
repository compatibility failure is the inherited Task 043 stale
five-versus-six instrument-count assertion recorded as GAP-010.

## Goal and why it exists

Let the existing private Tide Pit and Pamplist VST3 instruments run in Ableton
at the common 32, 44.1, 48, 88.2, 96, 176.4, and 192 kHz host rates without
changing either instrument's exact 48 kHz musical Core or requiring the user to
change a Live set's sample rate. The change belongs only to the two prototype
VST3 host adapters and one narrow shared Instrument Lab utility.

## In scope

- The approved source-reimplementation proposal and one implementation-ready
  Task 047 bundle before DSP-facing implementation edits.
- One JUCE-independent, fixed-capacity stereo output sample-rate converter and
  rational host/source timeline under Instrument Lab prototype support.
- Exact 48 kHz bypass with the existing processor PCM, event, state, and
  allocation evidence preserved byte-for-byte at the output boundary.
- Fixed internal 48 kHz operation for both Cores at every supported host rate.
- Common host rates 32, 44.1, 48, 88.2, 96, 176.4, and 192 kHz; all other rates
  continue to fail closed to deterministic silence.
- Causal 129-tap Kaiser-windowed sinc conversion with exact rational phases,
  per-phase DC normalization, an explicit transition band, persistent history,
  and host-reported integer latency.
- Host MIDI sample offsets mapped monotonically to the first source frame not
  earlier than the host event. Equal mapped frames retain ingress order.
- Tide Pit's existing 16-frame source scheduler and Pamplist's existing
  at-most-512-frame Core calls retained as instrument-owned event/render seams.
- A bounded non-48-kHz callback size of 8,192 host frames; larger callbacks
  fail to silence and increment existing processor failure diagnostics.
- Focused shared-converter, processor, allocation, sanitizer, actual-module,
  adjacent regression, current-profile, and relocated-reproduction evidence.
- Source-faithful status/editor text that reports the fixed 48 kHz Core and the
  active supported host rate without adding new controls.

## Out of scope

- Any Tide Pit or Pamplist DSP equation, seed, default, parameter, state schema,
  controller mapping, gesture, mode, accepted-state rule, or canonical identity.
- Running either Core natively at the host rate, oversampling inside either
  Core, audio input conversion, time stretching, pitch shifting, host tempo
  synchronization, MIDI-note redesign, or variable-rate modulation.
- A generic plug-in framework, public SDK, runtime/provider/catalog promotion,
  dynamic dependency, or new Schuss semantic authority.
- AU/AAX/CLAP/VST2, non-macOS or x86_64 targets, installation, Ableton launch,
  endpoint/device access, listening promotion, real-time promotion, packaging,
  signing identity, notarization, distribution, publication, or Git actions.
- Mutation of configured source trees, authenticated JUCE bytes, retained
  source locks/oracles, or unrelated inherited Task 043-046 work.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADRs 0016-0018, the Instrument Lab
   workflow, validation manifest, and current governance routing.
2. Completed but uncommitted Task 045 Pamplist and Task 046 Tide Pit VST3
   adapters, their frozen proposals, ready bundles, results, and gap ledgers.
3. The exact Tide Pit and Pamplist portable 48 kHz Cores, host adapters,
   controller maps, direct comparators, state models, and authenticated source
   closures already bound by Tasks 045 and 046.
4. Authenticated JUCE 8.0.15 local source and the existing no-install build and
   module-host reproduction paths.

### Deliverables

1. `research/proposals/tide-pit-pamplist-vst3-resampling.md` and the ready
   `research/prototypes/vst3-resampling/contract-r01/` bundle.
2. A narrow shared fixed-rate stereo converter/timeline in
   `research/prototype_support/instrument_lab/` with focused tests.
3. Tide Pit and Pamplist processor integration, status presentation, direct
   multi-rate tests, allocation tests, and actual-bundle module-host tests.
4. Updated build/reproduction receipts, Task 045/046 successor results and gap
   dispositions, and Task 047 status/history/routing documentation.
5. Authenticated uninstalled arm64 Release VST3 bundles for both instruments.

## Acceptance tests

1. The proposal, Task 047 bundle, both predecessor VST3 authorities, both Core
   authorities, configured Pamplist source, Tide Pit source lock, and JUCE
   manifest authenticate before implementation.
2. The shared converter accepts only the seven declared integer rates, derives
   exact reduced rational ratios, reports deterministic latency, maps event
   offsets monotonically, and produces the exact cumulative source-frame count
   independent of host block partitioning.
3. The 48 kHz path bypasses the converter and continues to pass every existing
   exact direct-Core PCM/event/state comparison for both instruments.
4. At 32, 44.1, 88.2, 96, 176.4, and 192 kHz, both processors emit finite,
   bounded, nonzero stereo PCM; duration, pitch, envelope/timeline progress,
   MIDI ordering, reset, state recall, and multi-instance isolation meet the
   frozen tolerances.
5. Converter impulse/DC/sine/sweep fixtures meet the frozen latency, gain,
   passband, and alias-rejection thresholds, and a no-filter linear comparator
   fails the 48-to-44.1-kHz alias threshold.
6. Repartitioning the same host timeline across 1, 16, 64, 127, 128, 511, 512,
   513, 2,048, and 4,096-frame callbacks produces equal source progress and
   signal-equivalent output after the declared latency relation.
7. Repeated non-48-kHz processing performs no adapter-owned heap allocation,
   lock, file, endpoint, JSON, paint, or unbounded callback work; unsupported
   rates/layouts and oversized callbacks remain exact silence.
8. Both exact Release modules scan, instantiate, report their host latency,
   round-trip existing state, create/destroy editors, and render nonzero
   fixtures at 44.1, 48, and 96 kHz in the separate JUCE module host.
9. Affected Instrument Lab and instrument regressions, applicable sanitizer
   checks, Schuss `current`, and one relocated reproduction per VST3 pass after
   implementation freeze.
10. Results keep source, host structural, host signal, target build, Live,
    real-time, connected-device, listening, distribution, and production
    claims separate.

## Decisions

### Task 047 may make

- The shared converter class/API, exact supported-rate list, rational phase
  convention, FIR length/window/cutoff, fixed capacities, latency convention,
  failure diagnostics, and objective test tolerances.
- The smallest VST3 processor branching and event-offset translation needed to
  preserve the existing exact 48 kHz lane and add the declared resampled lane.
- Task-local fixtures, receipts, result/gap updates, and proportional validation
  selection inside this evidence ceiling.

### Task 047 must not make

- New musical behavior, new parameters or state fields, Core-native multi-rate
  behavior, controller remapping, or a correction to an inherited source quirk.
- Canonical catalog/graph/binding/provider/runtime identity or a general
  resampling service beyond the two evidenced VST3 consumers.
- A Live, real-time, device, listening, licensing/distribution, or production
  conclusion from offline tests or target builds.
- Installation, app launch, endpoint/device access, dependency installation,
  staging, commit, push, publication, or mutation of upstream/configured trees.

## Validation classification

- Focused: ready-bundle validation; shared converter signal/timeline tests;
  both VST3 processor, allocation, and module suites.
- Adjacent: existing Tide Pit and Pamplist Core/control/UI/render/source tests
  and the Instrument Lab core suite.
- Compatibility: selected because a shared Instrument Lab header is added, but
  only after focused/native stability; no release-wide replay is implied.
- Configured/native: one final Pamplist source authentication, Tide Pit source
  lock, authenticated JUCE check, two Release VST3 builds, and applicable
  sanitizer checks.
- Reproduction: one copied-root Release VST3/module-host reproduction per
  changed consumer after freeze.
- Routine: `current` once after implementation and documentation freeze.
- Release: not required; this remains private prototype host support and does
  not change a release, canonical provider/runtime, or distribution boundary.

## Evidence ceiling and stop condition

Stop when the ready Task 047 contract, shared converter, both integrations,
focused/adjacent/current/native/reproduction gates, final uninstalled arm64
bundles, and exact result/gap records pass. Completion proves at most source,
host structural, host signal, and target-build behavior. It does not install or
launch the plug-ins or prove Ableton behavior, callback deadlines, physical
controller routing, listening quality, distribution readiness, or production
integration.
