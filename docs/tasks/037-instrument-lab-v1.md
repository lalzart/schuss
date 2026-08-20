# Task 037: Instrument Lab v1 repeatable validated scaffold

Status: proposed and documented on 2026-08-20; not activated. Task 037 is
strictly sequenced after completed Task 036 and may not begin from Task 036's
documentation-only or partially migrated state. This file does not alter
`docs/governance/current-state.json` or activate Task 033 Phase 3.

## Goal and why it exists

Create one non-production, repository-owned Instrument Lab that reuses the
proven host/controller/render/validation mechanics from Cinderwheel and Tide
Pit, while keeping every instrument's DSP, state, controls, source fidelity,
and musical decisions explicit and independently testable.

The task exists to reduce the repeated context, implementation effort, and
high-reasoning work spent on JUCE setup, MIDI intake, callback partitioning,
UI synchronization, renderer artifact mechanics, CMake/CTest wiring, and
evidence bookkeeping. It does not attempt to make novel DSP design or source
equivalence cheap; it makes the mechanical path around those hard decisions
repeatable.

## Approval, activation, and sequence boundary

The user authorized this documentation and requested that the next two steps
remain in sequence. Implementation is reserved for a separately activated
chat.

The required order is:

```text
Task 036
  shared authenticated Mutable source package
  + Tide Pit exact migration
  + complete machine-readable handoff
             |
             v
Task 037
  two-prototype differential audit
  + Instrument Lab v1
  + exact Cinderwheel/Tide Pit migrations
  + graph-promotion requirements
```

Before any Task 037 edit, the implementation chat must verify that
`docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json` exists, has status `complete`,
matches its live package and Tide Pit dependencies, and binds passing Task 036
results. Absence, partial status, malformed data, hash drift, or unproved Tide
Pit equivalence is a hard stop.

Task 037 is not Task 033 Phase 3, Task 034 execution, or a production graph or
provider task. If live governance routes another task first, the user must
explicitly reroute or schedule Task 037; task numbering does not override
governance.

## Exact baseline and proposal binding

- Proposal: `research/proposals/instrument-lab-v1.md`.
- Proposal revision: 0.1.
- Proposal SHA-256:
  `52344203b3520001f4266c25f226f7181f1a74ef89024e47e109e6a2a5bd50db`.
- Documentation baseline: tracked Schuss `main` and `origin/main` at
  `2b0180a47f7ac03011f56e9683c77060c8080f09`.
- Task 036 proposal SHA-256:
  `be4636f2550481bd45cb982fe47c01ee8fbe0de74621f22e9d27cffca680cf7a`.
- Task 036 contract SHA-256:
  `4bdd4b60fff8cc28c7f21a17763a949e2e123cafea84e2aad30252338be501f0`.
- Cinderwheel proposal SHA-256:
  `cd0c09e0df22f382d74bb380fa9ab91549faf1894199f5d02e4ac5e3795a1549`.
- Tide Pit proposal SHA-256:
  `3c2157eaa26ceed61afe87b256a395dccc5fbbd0dab889189926ffb72b5c2157`.
- Reusable regular Launch Control 3 topology SHA-256:
  `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`.

The implementation baseline is not the documentation baseline above. It is the
then-live tracked repository plus the exact completed Task 036 handoff. The
activation audit must fingerprint all post-Task-036 Cinderwheel and Tide Pit
inputs before shared-code extraction. It must preserve unrelated dirty and
untracked work and must not treat ambient working-tree bytes as normative.

## Working definition and evidence ceiling

The literal working artifact is one linked Instrument Lab v1 implementation
used successfully by:

1. the unchanged Cinderwheel musical Core;
2. the post-Task-036 unchanged Tide Pit musical Core; and
3. one generated non-musical smoke fixture.

All three must build and validate in fresh roots without copied shared host
implementation. Cinderwheel and Tide Pit must retain their exact accepted
Core/control/render behavior.

The required ceiling is host-signal evidence plus authenticated JUCE target
build. No app launch, physical controller, callback deadline, device lifecycle,
listening, plugin, distribution, or production-integration pass is implied.

## In scope

- Freeze a two-prototype differential audit before extracting shared code.
- Add `research/prototype_support/instrument_lab/` as the one prototype-only
  shared C++/CMake/template implementation root.
- Add `tools/instrument_lab/` as the deterministic generator, validator, and
  fresh-root reproduction entry point.
- Add lab-local, noncanonical schemas and negative fixtures below the lab/tool
  roots; do not add global semantic schemas.
- Add one `prototype-index.json` per migrated/generated consumer.
- Add one validated `dsp-topology.json` per migrated/generated consumer.
- Reuse the exact regular Launch Control 3 topology without copying it.
- Extract exact JUCE authentication/configuration, target-registration,
  renderer-artifact, bounded MIDI-envelope, ordering/drop, and validation
  mechanics that pass the differential audit.
- Provide a parameterized host bridge supporting at least Cinderwheel's float
  path and Tide Pit's Q27/16-frame path without implicit conversion.
- Generate control descriptors and descriptor-driven UI structure from each
  instrument's control map or an exact exhaustive adapter.
- Ensure UI reflection uses accepted Core state through an instrument-owned
  snapshot projection.
- Either implement and prove a restart-safe latest-snapshot channel or leave
  the known mailbox-reset seam instrument-local and explicitly deferred.
- Migrate Cinderwheel and Tide Pit in recoverable, parity-gated stages.
- Add a synthetic smoke fixture that proves generation, linking, MIDI/control,
  snapshot, renderer, and validation behavior without becoming a catalogued
  musical instrument.
- Add `docs/workflows/instrument-development.md` describing the common flow for
  new design, observed-behavior reimplementation, and authorized source port.
- Add Task 037 results/gaps and a bounded plugin/skill follow-up packet.
- Register proportional focused/native/reproduction checks without making the
  `current` profile compile JUCE or render long matrices.

## Out of scope

- Any new musical instrument or modification of existing DSP sound/behavior.
- A universal Core class, universal controls/state/snapshot, or one numeric,
  rate, quantum, memory, RNG, gesture, reset, capture, or lifecycle policy.
- A change to Cinderwheel or Tide Pit algorithms, defaults, scales, source
  bytes, source overlays, golden comparator, event semantics, or tolerances.
- A second Mutable source intake or compiled shared Mutable provider.
- Canonical Schuss component, graph, instrument, performance-control,
  configuration, provider, runtime-factory, target/backend, operation, project,
  machine, record, schema, or stable-ID allocation.
- Running a Task 034 performance-control graph or changing Task 033's seven
  factory cohort.
- `juce_dsp`, plug-in formats, public SDK/ABI, dynamic loading, packaging,
  distribution, signing, notarization, or publication.
- Editing the externally installed Sonic Research Lab plugin. The task may
  produce an exact follow-up specification only.
- Audio/MIDI device access, controller Custom Mode writes, app launch, hardware,
  real-time promotion, listening, staging, commit, or push.

## Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/STATUS.md`, current governance,
   ADRs 0016-0018, and Tasks 033-036.
2. The exact approved proposal and this task fingerprint.
3. Completed and validated `036-INSTRUMENT-LAB-HANDOFF.json`.
4. Post-Task-036 Cinderwheel and Tide Pit complete source/build/test/result/gap
   trees, inventoried and fingerprinted at activation.
5. The existing Launch Control 3 topology and Cinderwheel reuse manifest.
6. The current Sonic Research Lab implementation-bundle contract and both
   prototype bundle artifacts.
7. The exact JUCE 8.0.15 source authority already used by the prototypes,
   supplied through the accepted local/authenticated mechanism.
8. The central validation-profile contract from ADR 0018 and its live manifest.

## Deliverables

1. `research/prototype_support/instrument_lab/README.md` with ownership and
   evidence boundaries.
2. `research/prototype_support/instrument_lab/DIFFERENTIAL_AUDIT.md` classifying
   every candidate seam as `extract`, `parameterized-adapter`,
   `instrument-owned`, or `defer`, with source fingerprints and reasons.
3. `research/prototype_support/instrument_lab/CMakeLists.txt` and
   `cmake/SchussInstrumentLab.cmake`.
4. Narrow C++17 shared headers/sources under
   `research/prototype_support/instrument_lab/include/` and `src/`.
5. Lab-local schemas for `prototype-index.json` and `dsp-topology.json`, plus
   complete positive/negative fixtures.
6. Shared deterministic templates that reference the lab implementation rather
   than copying it into each generated prototype.
7. `tools/instrument_lab/new_prototype.py`, `validate_prototype.py`, and a
   fresh-root reproduction runner with focused tests.
8. A generated non-musical smoke fixture under the lab fixture root.
9. Migrated Cinderwheel host/control/render/build surfaces with unchanged DSP
   Core and accepted evidence.
10. Migrated post-Task-036 Tide Pit host/control/render/build surfaces with
    unchanged DSP Core, source policy, and exact comparator.
11. Per-consumer `prototype-index.json`, `dsp-topology.json`, and compact
    `IMPLEMENTATION_HANDOFF.md` artifacts.
12. `docs/workflows/instrument-development.md` covering all three user-facing
    creation paths and their common evidence ladder.
13. `docs/tasks/037-PLUGIN-FOLLOWUP.md`, specifying the smallest future Sonic
    Research Lab routing/build-skill changes after repository interfaces freeze.
14. `docs/tasks/037-RESULTS.md` and `docs/tasks/037-GAPS.md`.
15. Central validation-manifest additions only for the exact new focused,
    native, and reproduction checks owned by this task.

## Differential-audit gate

Before shared C++ implementation, the audit must enumerate corresponding files,
types, responsibilities, invariants, and evidence from both prototypes. At a
minimum it covers:

- JUCE source authentication and module boundaries;
- CMake configuration, targets, and CTest registration;
- raw MIDI collection, message validation, timestamping, ingress order,
  capacity, and drop accounting;
- semantic mapping and gesture ownership;
- float/Q27 conversion and internal-quantum buffering;
- Core prepare/process/reset/snapshot/diagnostic ownership;
- UI descriptors, authoritative value reflection, soft pickup, and diagnostics;
- state mailbox and audio-device restart lifecycle;
- experiment parsing, event timeline ownership, WAV/Q27 writing, hashes,
  metrics, manifests, overwrite policy, partitions, and repeatability;
- sanitizer, golden, adapter parity, render matrix, and fresh-root evidence;
- source/dependency fingerprints and generated-artifact freshness.

No candidate may be extracted merely because files look similar. `extract`
requires one contract that both prototypes can consume without musical or
evidence drift. `parameterized-adapter` requires explicit differences. An
unproved or unsafe seam remains instrument-owned or deferred.

## Artifact and API contracts

### Instrument Lab linkage

Generated and migrated prototypes must link one lab target. Templates may
generate index, adapter, trait, and instrument-owned stub files, but they may
not copy shared lab source. One CMake entry point must configure:

- a Core-only build that has no JUCE dependency;
- optional authenticated-JUCE renderer/adapter/standalone targets;
- focused CTest registration;
- sanitizer instrumentation selected by the consumer; and
- exact source/experiment/control/topology freshness inputs.

The helper cannot fetch by default, add global flags, link `juce_dsp`, choose a
numeric profile, or infer unsupported sample rates or layouts.

### Core adapter

Composition or traits adapt existing Cores. The boundary declares sample type,
rate, maximum host block, internal quantum, semantic-event type/capacity,
process contract, output-clearing policy, snapshot projection, diagnostics, and
lifecycle. There is no inherited universal musical Core API.

Shared code must not translate units, quantize controls, synthesize musical
gestures, reseed RNG, clear instrument state, or normalize source quirks unless
the exact instrument adapter owns and tests that behavior.

### MIDI/control boundary

Raw MIDI processing is bounded and diagnostic. It produces a controller-neutral
surface event or calls an instrument-supplied exact mapper. New instrument
Cores receive timestamped semantic events unless their approved source contract
makes raw MIDI normative.

The existing Launch Control 3 artifact owns only physical topology/protocol.
Each instrument owns labels, assignments, curves, defaults, gestures, feedback,
and Core actions. Physical-device evidence remains separate.

### UI boundary

Generated UI structure consumes validated descriptors. Interactive values come
from the accepted Core snapshot projection, not raw MIDI. Raw receive counts,
last messages, or rejected values are diagnostic surfaces only.

The shared layer may own lifecycle-safe transport of immutable UI models. It
does not own instrument visual identity, semantic names, display copy, or
musical state.

### Renderer boundary

The lab may own deterministic encoding, hashing, standard measurements, result
manifests, overwrite refusal, partition enumeration, and artifact-directory
policy. The instrument's `experiment.json` owns conditions, comparator, source
signals, seed, event timeline, checkpoints, tolerances, and interpretation.

### Prototype graph boundary

`dsp-topology.json` is required but explicitly noncanonical and non-executable.
It uses typed public facets, local roles, nodes, connections, feedback/state
boundaries, and implementation/fusion annotations. It prohibits Schuss stable
IDs, physical controller selectors, JUCE classes, source paths, providers,
runtime factories, targets, and backends.

A validator produces a deterministic promotion-needs report listing unresolved
component contracts and implementation boundaries. It cannot allocate records
or claim that a compiled Core is the authoritative Schuss graph. The complete
topology, including internals of a fused Core, remains inspectable.

### Compact context handoff

Each `IMPLEMENTATION_HANDOFF.md` is a concise index, not a substitute for the
task and approved bundle. It contains exact paths/hashes, lane, working artifact,
allowed edits, reusable entry points, required commands, stop conditions, and
open decisions. It contains no copied proposal/source body, chat transcript,
absolute path, build log, or mutable latest reference.

## Migration and recovery order

1. Verify Task 036 and fingerprint the live two-prototype baseline.
2. Complete/freeze the differential audit and API/fixture contracts.
3. Implement and validate the lab with the smoke fixture only.
4. Migrate one Cinderwheel seam at a time, retaining the old path until focused
   parity passes.
5. Run the complete Cinderwheel comparator before removing verified duplicates.
6. Migrate one Tide Pit seam at a time, retaining its source/Core policies.
7. Run source/golden/control/adapter/UI/render/target parity before removing
   verified duplicates.
8. Run two fresh-root generations and one relocated-root reproduction.
9. Review the complete diff, generated freshness, Task 036 closure, and evidence
   ladder before final proportional profiles.

Failures roll back only the currently additive migration seam through a
reviewed recoverable edit. Do not reset the worktree or restore from ambient
source. A failed abstraction may remain deferred without failing the task if
all migrated consumers use only the smaller proven shared set and the gap is
recorded.

## Acceptance tests

1. Task 037 refuses to run without an exact complete Task 036 handoff and fails
   closed on every bound-hash/status/path mismatch.
2. The differential audit accounts for every required seam and precedes shared
   implementation edits in retained evidence.
3. Lab-local schemas reject unknown fields, canonical Schuss IDs, absolute or
   escaping paths, ambiguous/latest references, invalid hashes, missing
   authorities, and forbidden controller/provider/runtime leakage.
4. The generator emits byte-identical trees in two fresh roots and a relocated
   root, with no timestamps, host paths, or copied shared implementation.
5. The smoke fixture builds Core-only and authenticated-JUCE targets, passes
   MIDI/control/snapshot/renderer/freshness tests, and makes no musical claim.
6. Shared MIDI intake accepts/rejects exact supported messages, preserves bytes
   needed by the mapper, clamps or rejects timestamps by contract, orders by
   timestamp/ingress sequence, reports overflow, and performs no callback
   allocation in the proven span.
7. The host bridge passes irregular partition, internal-boundary, carried-event,
   reset, unsupported-format, overflow, allocation, audio, snapshot, and
   diagnostic parity for both float and Q27/16-frame adapters.
8. Generated control descriptors exhaustively match each authoritative map;
   every selector, transform, default, gesture boundary, label, unassigned
   control, and feedback limitation is accounted for.
9. UI-model tests prove displayed interactive values follow accepted Core
   snapshot state across MIDI input, direct UI changes, quantization, pickup,
   mode recall, rejected input, and reset.
10. Any shared snapshot transport is proven safe across producer/consumer reset
    and restart; otherwise no shared mailbox is delivered and the gap is
    explicit.
11. Common renderer utilities preserve each instrument's exact experiment,
    artifact count, output encoding, overwrite policy, metrics, hashes,
    partitions, repeat behavior, and complete final state.
12. Cinderwheel's full Core, mapping, adapter, renderer, and authenticated-JUCE
    checks pass before and after migration with no accepted behavior drift.
13. Tide Pit's full Task-036-bound source/Core/fail-fast-sanitizer/control/UI/
    adapter suite, exact 1,536,000-byte `39d8...ad2b` golden, render
    partitions/snapshots, and authenticated-JUCE suite pass before and after
    migration. The completed Task 036 handoff, not an older remembered test
    count, defines that exact live suite.
14. Neither prototype Core, source overlay, source bytes, musical defaults,
    semantic action meanings, state operations, experiment tolerances, or
    accepted evidence is rebaselined.
15. Every consumer links the one lab implementation and retains only explicit
    instrument adapter/trait, map, UI projection, experiment, source, and DSP
    files; duplicate shared files fail a freshness/duplication check.
16. Each `dsp-topology.json` validates, exposes complete prototype internals,
    and produces a deterministic promotion-needs report without canonical
    allocation or executable claim.
17. Each compact handoff resolves every authority and command exactly and fails
    when any referenced input changes.
18. The central `current` profile remains compiler/render/network/device free;
    affected focused, native, and reproduction checks pass once after freeze.
19. No Task 033/034 semantic bytes, `schuss_rt` runtime behavior, catalog,
    project, graph, provider, operation, governance, hardware, remote, or
    external plugin state changes.

## Validation plan and cadence

### Focused fast checks

- Task 036 predecessor/handoff validator.
- Lab schema, canonicalization, negative fixture, and generator freshness tests.
- C++ Core-adapter/MIDI/bridge/UI-model/renderer utility unit tests.
- Per-instrument descriptor/topology/index/handoff freshness.
- Incremental Cinderwheel and Tide Pit parity after each migrated seam.

### Adjacent native checks

- Instrument Lab smoke fixture Release and fail-fast sanitizer builds.
- Complete Cinderwheel Core/JUCE/render matrix.
- Complete post-Task-036 Tide Pit source/Core/fail-fast sanitizer/JUCE/render
  matrix.
- Exact JUCE archive/module authentication for the targets actually linked.

### Reproduction and integration

- Generate/build/test the smoke fixture from two fresh roots.
- Repeat from a relocated lab/source root.
- Run deterministic promotion-needs and compact-handoff generation twice.
- Run one `current` profile after implementation freeze.
- Add only the exact Task 037 checks to ADR 0018 profiles. `release` is not
  required unless scope expands into accepted production/runtime semantics.

After failure, rerun only the affected focused or adjacent check until the fix
freezes. Repeat invalidated native/reproduction work once, then perform one
final diff/freshness review and current-profile run.

## Decisions Task 037 may make

- Prototype-lab paths, local schema keys, diagnostics, generator CLI, CMake
  entry points, adapter traits, fixed host-mechanics capacities, and test
  fixtures required by the accepted scope.
- Evidence-backed extraction/defer classifications.
- Instrument-local mechanical migrations that preserve every approved musical
  and evidence contract.
- The exact contents of the workflow guide, compact handoff, promotion-needs
  report, and external plugin follow-up packet.
- Proportional validation registrations owned only by Task 037.

## Decisions Task 037 must not make

- Canonical Schuss graph/instrument/component/provider/runtime identity or
  behavior.
- Task 033 Phase 3 or Task 034 runtime execution.
- New DSP algorithms, musical semantics, source equivalence decisions, or
  evidence rebaselines.
- A public/general plugin ABI, dynamic loading, distribution approval, or
  external skill/plugin mutation.
- Physical device, real-time, listening, release, Git staging/commit/push, or
  publication decisions.

## Expected implementation evidence

`docs/tasks/037-RESULTS.md` must retain:

- live baseline, Task 036 handoff, and all proposal/task/consumer fingerprints;
- the completed differential audit hash;
- shared versus consumer-owned file inventories;
- generator outputs and two-fresh-root/relocated-root hashes;
- focused/native/reproduction commands and exact results;
- pre/post Cinderwheel and Tide Pit comparator results;
- JUCE modules/source authentication and target-build results;
- corrections made during extraction and migrations;
- exact generated handoff/topology/promotion report hashes; and
- the separated evidence ladder.

`docs/tasks/037-GAPS.md` must retain at least:

- every seam left instrument-owned or deferred;
- callback deadline, collector, device restart, controller, launch, listening,
  distribution, and production limitations;
- the absence of canonical graph/performance/provider execution;
- any remaining source/numeric/profile-specific adapter cost;
- measured evidence about context/code reduction without unsupported token-cost
  claims; and
- the exact successor architecture/plugin work needed before production use.

## Completion boundary and successor packet

Task 037 completes only when the shared lab is consumed by the two existing
prototypes and generated smoke fixture, their exact accepted behavior remains
intact, graph-aware artifacts and compact handoffs validate, fresh-root
reproduction agrees, and all remaining nonproduction limitations are explicit.

Completion does not make Instrument Lab a Schuss provider/backend, make a
prototype topology canonical or executable, authorize a third musical
instrument, update the external Sonic Research Lab plugin, or activate a graph
promotion/runtime task.

The final plugin follow-up and promotion-needs reports are inputs to a later
separately proposed task. They allocate no Task 038 identity or authority.

## New-chat handoff

After Task 036 is complete, start Task 037 with:

> Implement Task 037 from `docs/tasks/037-instrument-lab-v1.md`. Treat the task
> as explicitly activated for this chat only after validating the complete
> Task 036 Instrument Lab handoff. Recheck live governance and all consumer
> fingerprints, preserve unrelated work, complete the differential audit before
> shared C++ edits, and stop on any source, golden, control, render, or scope
> drift.
