# Task 048: Wanderbody standalone first playable

Status: complete in the current working tree and uncommitted. The user's
2026-08-25 instruction, "implement it", authorized uninterrupted execution of
the referenced Wanderbody JUCE handoff through the bounded evidence ceiling
below. The retained result and gap records preserve the exact source,
host-structural, host-signal, and authenticated target-build evidence. No
application launch, endpoint access, listening, installation, distribution,
staging, commit, or push was performed.

## Goal and why it exists

Build the smallest noncanonical desktop instrument that proves Wanderbody can
listen to or internally generate a sound, hover over recent memory, wander away
through correlated motion, recall a recognizable decision gesture, and give
that gesture a source-preserving resonant body.

The task exists to turn the external implementation handoff into an exact,
testable Schuss Instrument Lab consumer without treating aspirational
real-time, device, listening, or product-completeness criteria as evidence that
already exists.

## In scope

- A completed new-design proposal and validator-ready implementation bundle
  before DSP implementation edits.
- One noncanonical `research/prototypes/wanderbody/` Instrument Lab consumer.
- A JUCE-independent portable C++17 Core with device-rate preparation,
  preallocated recent-memory capture, freeze, clear, wrap-safe interpolation,
  an internal exciter, Hover, bounded correlated Drunk motion, fixed-capacity
  decision recurrence, a fixed-capacity fragment renderer, an original modal
  body, source-preserving mix, and finite-output recovery.
- Seeded semantic decisions and deterministic offline evidence at 44.1, 48,
  and 96 kHz with variable, non-power-of-two block partitions.
- Versioned transactional state for controls, seed, motion, and recurrence;
  captured audio is deliberately not serialized in revision 0.1.
- A minimal JUCE 8.0.15 macOS arm64 standalone shell with audio/MIDI device
  settings, accepted-state controls, bounded UI-to-audio commands, and a
  decimated memory view that never reads the capture store directly.
- Focused Core/state/allocation tests, objective property renders, sanitizer
  coverage, authenticated unlaunched JUCE target build, Instrument Lab
  validation, one relocated Core-only reproduction, and Schuss `current`.
- Exact result, gap, topology, dependency, promotion, and handoff records.

## Out of scope

- Copying or adapting CDP, Mutable Instruments, or other external DSP source.
- A faithful CDP HOVER/DRUNK port, a Rings port, interaction/Warps processing,
  onset landmarks, more than four fragment voices, spectral processing,
  convolution, time-stretching, imported-file playback, export/bounce, or a
  general granular workstation.
- MIDI learn, a frozen controller map, physical MIDI/audio endpoint access,
  captured-audio preset persistence, crash recovery, distribution packaging,
  signing, notarization, or public/commercial licensing conclusions.
- A plug-in, AU/VST3/AAX/CLAP target, Ksoloti/Gills target, firmware, hardware,
  canonical catalog/graph/instrument/provider/runtime identity, or production
  desktop integration.
- Application launch, audio callback deadline measurement, physical device
  testing, subjective listening promotion, installation, staging, commit,
  push, publication, or mutation of configured/upstream source trees.
- Rewriting or cleaning inherited Task 043-047 work or unrelated dirty files.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADR 0016, ADR 0018, the Instrument
   Lab workflow, validation manifest, and current governance routing.
2. `/Users/lanceship/Downloads/Wanderbody_JUCE_Handoff.md` as user-supplied
   product and engineering reference, not as autonomous execution authority.
3. The user's explicit 2026-08-25 implementation instruction.
4. The repository-owned Instrument Lab support library and authenticated JUCE
   8.0.15 source-tree manifest.
5. Primary CDP documentation, Mutable Instruments manuals/source references,
   JUCE callback documentation, and modal-synthesis engineering references
   cited by the proposal.

### Deliverables

1. `research/proposals/wanderbody-standalone-r01.md` and ready bundle at
   `research/prototypes/wanderbody/contract-r01/`.
2. The portable Core, state/control seam, offline renderer, standalone shell,
   and focused tests under `research/prototypes/wanderbody/`.
3. Noncanonical `prototype-index.json`, `dsp-topology.json`, semantic control
   descriptor, source-dependency record, notices, promotion needs, and
   implementation handoff.
4. Retained objective metrics/manifests plus exact Task 048 results and gaps.
5. An authenticated, unlaunched macOS arm64 Wanderbody application bundle if
   the local exact JUCE prerequisite is available.

## Acceptance tests

1. Proposal and implementation-bundle fingerprints validate in ready mode
   before DSP edits; the work lane is `new-design` and no normative external
   implementation source is declared.
2. The Core prepares at 44.1, 48, and 96 kHz for maximum callback sizes from 1
   through 2048 frames, allocates only during prepare, and processes 1, 17, 64,
   127, 256, 511, and 1024-frame partitions without process-time allocation.
3. Capture reads remain valid across ring wrap; Freeze holds source time; Clear
   invalidates memory through a bounded transition; invalid reads, oversized
   blocks, bad layouts, and non-finite inputs fail silent or recover without
   stale pointers or unbounded work.
4. Hover decisions stay inside the resolved anchor field and are locally
   recognizable at minimum Wander. Drunk uses a correlated bounded walk with
   reflection and approaches stillness at minimum Wander.
5. The same sample rate, input, controls, seed, actions, and semantic event
   timeline produce identical decision tuples across supported block
   partitions. Locked repeats one finite ordered history, Shuffled permutes
   only that history, and Mutated retains tuple identity while changing only
   declared bounded dimensions.
6. Fragment start/end/reverse/wrap transitions remain finite and bounded; the
   fixed voice allocator never exceeds four voices and exposes steals/drops.
7. Body bypass is signal-transparent at its declared mix boundary; enabled
   body produces a decaying modal response from fragment excitation, remains
   bounded under full-range gestures, and cannot erase the dry/memory source.
8. Silence, impulse, DC, sine, deterministic noise, rapid mode/freeze/clear
   changes, and extreme control fixtures meet the frozen peak, DC, finite,
   recurrence, locality, and determinism tolerances. The uncorrelated-position
   comparator fails the frozen locality/step-correlation criterion.
9. Version-1 state round-trips transactionally and rejects unknown versions,
   invalid enums, non-finite values, or out-of-range fields without partially
   mutating accepted state. Captured audio has explicit missing-state behavior.
10. The standalone target compiles and links against the authenticated JUCE
    tree without launching or installing; its callback path contains no file
    I/O, blocking lock, logging, large destruction, or unbounded loop.
11. Instrument Lab consumer/freshness checks, applicable sanitizers, one
    relocated Core-only reproduction, and Schuss `current` pass after freeze.
12. Results keep source, host-structural, host-signal, target-build, real-time,
    endpoint/device, listening, distribution, and production claims separate.

## Decisions

### Task 048 may make

- The smallest original equations and fixed capacities needed for the declared
  vertical slice, including provisional capture duration, fragment count,
  history length, interpolation, envelope, body mode count, and test bounds.
- A mono recent-memory Core with stereo presentation if channel assumptions
  remain isolated and recorded as provisional rather than a public contract.
- Semantic revision-0.1 controls, defaults, smoothing times, action timing,
  fixed state schema, objective fixtures, and target-local UI layout.
- Task-local source organization, build helpers, diagnostics, evidence
  retention, and proportional validation selection inside this ceiling.

### Task 048 must not make

- A canonical Schuss identity, accepted provider/runtime route, executable
  canonical graph, stable public file format, general DSP module framework, or
  embedded/plugin commitment.
- A source-equivalence, CDP-fidelity, Rings-fidelity, novelty, real-time,
  connected-device, listening, product-quality, distribution, or production
  conclusion from the bounded implementation.
- A permanent answer to the handoff's open capture duration, channel topology,
  voice count, interpolation, pitch/time, body resolution, oversampling,
  controller layout, persistence, OS, or release questions.
- Dependency installation/fetch, upstream/configured-source mutation,
  application or endpoint launch, hardware action, staging, commit, push, or
  publication.

## Validation classification

- Focused: ready-bundle validation; Core, state, recurrence, capture, modal,
  allocation, and UI-exchange unit/property tests.
- Adjacent: Instrument Lab Core tests and consumer validator only; unrelated
  instrument musical regressions are not affected.
- Native: Release and ASan/UBSan Core/offline builds plus one authenticated
  JUCE 8.0.15 standalone compile/link when its exact source root is available.
- Reproduction: one relocated Core-only consumer reproduction after freeze;
  no JUCE fetch, app launch, or endpoint work.
- Routine: Schuss `current` once after implementation and documentation freeze.
- Compatibility/release: not required because this adds an isolated
  noncanonical consumer and changes no shared schema, provider, runtime, or
  release boundary.

## Evidence ceiling and stop condition

Stop when the ready bundle, portable implementation, objective host signal,
authenticated unlaunched target build when locally available, focused native
checks, relocated reproduction, `current`, and exact result/gap records pass.
Completion proves at most proposal, source, host-structural, host-signal, and
target-build evidence. Callback deadlines, live endpoint lifecycle, physical
devices, listening quality, packaging, distribution, and production
integration remain separate work.
