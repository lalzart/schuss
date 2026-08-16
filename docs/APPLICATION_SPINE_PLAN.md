# Application-spine sequence and parallel-work plan

Status: accepted planning authority under ADR 0014. No Task 023-028
implementation contract has been created or activated.

## Goal

Advance Schuss from a collection of exact headless capabilities toward one
complete authoring application without allowing the CLI, UI, catalog, or
compiler to become a competing source of semantic truth.

The chosen product thread is:

```text
coherent shared operations and CLI
    -> complete catalog coverage plus reviewed application library
    -> broader exact direct-compiler semantics
    -> create/edit/save/build from an empty project
    -> application jobs and diagnostics
    -> thin UI over the same operations
```

The failed Task 022 diagnostic is retained but is not on this critical path.
It must be revisited before a complete connected-panel or release claim, not
before offline catalog, compiler, CLI, or UI-architecture development.

## Baseline

- The frozen inventory contains 4,209 candidate files, 3,602 resolved object
  observations, and 348 complete legacy graphs. These observations include
  overloads, duplicates, editor-only definitions, parse failures, and
  unresolved facts; they are not 3,602 automatically valid semantic families.
- The Task 011A projection contains 28 families and 41 implementations. Task
  017 adds twelve reviewed families in a later exact closure, but those
  additions are mostly structural and retain deterministic unsupported
  compiler results.
- The reusable compiler front half, exact build execution, direct frontend,
  durable project service, and graph transaction operations exist. The direct
  executable path remains intentionally narrow.
- Project and build-plan/build-execute commands exist, but compatibility code
  deliberately hides some implemented commands from the accepted root help and
  completion surfaces. `gills.inspect` has a shared operation but no equivalent
  ordinary product command.
- No desktop application is implemented.

## Planned numbered tasks

### Task 023: CLI v2 and application-surface consolidation

Goal: make the implemented headless product coherent and discoverable before
adding another client.

Required outcomes:

- define an explicit successor CLI/help/completion contract rather than hiding
  new commands to preserve the first human-output golden forever;
- expose project operations, build resolve/plan/execute, catalog, graph, and
  Gills/instrument inspection coherently;
- resolve the inherited Task 011A golden mismatch through an explicit
  successor while preserving accepted historical machine request/result bytes;
- expose one deterministic application-capability description usable by CLI,
  UI, and AI clients; and
- retain an end-to-end read-only smoke path across catalog, project, graph,
  compiler planning, and build capability inspection.

Task 023 does not expand DSP semantics, catalog families, project write
semantics, UI implementation, or hardware evidence.

### Task 024: Complete catalog coverage and deterministic curation

Goal: make the full frozen object population accountable without inventing
semantics or equating inventory with readiness.

Required outcomes:

- give every resolved observation an exact disposition: reviewed family,
  implementation variant, overload group, duplicate, editor-only/non-headless,
  unresolved, or queued for human review;
- generate deterministic review packets and coverage reports rather than a
  hand-maintained reverse index;
- preserve function-first family browsing, form filtering, provenance
  inspection, source evidence, uncertainty, and readiness separation;
- produce a broader reviewed catalog successor and an exact selection packet
  for Task 025; and
- initially target 16-24 additional high-value reviewed families, with the
  exact bounded count fixed by the Task 024 contract after audit rather than
  filled through weak or inferred reviews.

Catalogued-only, contracted, bound, eligible, compile-proven, device-tested,
real-time-tested, audible-tested, and unresolved remain distinct states.

### Task 025: Direct-compiler core-library tranche

Goal: turn the Task 024 application-library selection into a meaningful exact
executable slice.

The primary consumer is the existing modulated dual-oscillator/effects
reference. The tranche is expected to cover the selected saw/PWM oscillator,
smoothing, VCA, soft-clipping, reverb, routing, and support semantics needed by
that graph, subject to the exact Task 024 selection packet.

Required outcomes include target-independent semantic specifications,
deterministic host vectors, normalized-DSP operations, source maps, fail-closed
unsupported diagnostics, two fresh builds, and ARM compile/link evidence level
5 without Java or `.axp` fallback. Device, real-time, and audible evidence
remain separately authorized.

### Task 026: Complete authoring operations and CLI workflow

Goal: allow a client to progress from an empty explicit workspace to an exact
built artifact without fabricating records or editing canonical JSON by hand.

Required outcomes:

- create a blank graph/project through client-neutral operations;
- select an exact reviewed catalog contract, add/remove nodes, connect them,
  and edit parameters and attributes;
- create and version instrument and build-request records and include them in
  the durable project closure;
- preserve immutable revision history and provide an explicit history/revert
  operation suitable for undo/redo presentation;
- save, close, reopen, validate, plan, and build through the same service used
  by every client; and
- pass one scripted empty-workspace-to-deterministic-ELF acceptance flow using
  the Task 025 executable tranche.

### Task 027: Application sessions, jobs, and diagnostics

Goal: provide the orchestration a real application needs without moving
semantic or compiler decisions into the UI.

Required outcomes include explicit workspace sessions, background build jobs,
progress events, cancellation boundaries, structured diagnostics, recovery,
and deterministic final operation results. CLI and UI adapters may present
those events differently but must receive the same canonical final result.
No job or session identity becomes project, graph, build, or evidence identity.

### Task 028: Second catalog/compiler tranche and transparent compounds

Goal: expand usefulness after the first complete authoring flow and close the
current transparent-compound/percussion compiler gap.

The exact scope is selected from Task 024 coverage plus feedback from Tasks
025-027. It must retain inspectable compound internals, origin/source maps,
deterministic binding resolution, and explicit unsupported results. It may not
become an unbounded promise to compile every legacy observation.

## Unnumbered UI milestones

### UI architecture

UI architecture is explicitly authorized now. It may begin after the Task 023
contract fixes the application capability boundary and may overlap Task 024.
It owns:

- client shell and transport evaluation;
- semantic state versus UI-only selection/layout/zoom state;
- object drawer, transparent graph canvas, inspector, project, build,
  diagnostics, and evidence information architecture;
- wireframes and fixture-driven interaction prototypes;
- accessibility, recovery, packaging, and performance constraints; and
- a bounded technical spike against canonical operation fixtures.

It does not own catalog classification, graph edits, project persistence,
compiler/build behavior, device evidence, or production UI implementation.
It does not revive Task 012B.

### UI vertical slice

UI implementation remains separately gated. When authorized after Tasks
025-027, the first vertical slice should browse by function, place and connect
exact components, inspect parameters and transparent internals, save/reopen a
project, and present build progress and structured diagnostics. It must match
the CLI/shared-operation fixtures and initially performs no device upload.

## Subtask identifiers

A parent task may be divided into exact children such as `023A`, `023B`, and
`023C` when that reduces coordination risk or enables useful parallel work.
These are child work packages, not aliases or new top-level roadmap positions.

Before a child starts, the accepted parent contract must declare:

- the child's goal, inputs, deliverables, and acceptance contribution;
- its exact dependencies and start gate;
- its owned files, schemas, IDs, and output namespace;
- the shared surfaces it must not edit;
- its merge/integration order; and
- whether child completion is required for parent completion.

Children may not allocate stable IDs or record-set revisions independently
unless the parent assigned disjoint exact ranges. A child may not edit current
status, roadmap, shared indexes, or publication state. Those remain parent
integration responsibilities. One child passing never activates the next
numbered parent.

## Dependency and concurrency plan

```text
Task 023
  |-- Task 024 -- Task 025 -- Task 026 -- Task 027
  |                     |          |
  |                     |          `-- Task 028 scheduling gate
  |                     `------------- Task 028 semantic dependencies
  `-- UI architecture

Tasks 025 + 026 + 027 + UI architecture -> gated UI vertical slice
```

Useful parallel windows are intentionally bounded:

1. After Task 023 is accepted, Task 024 implementation and the read-only/design
   UI-architecture milestone may run concurrently.
2. After Task 024 freezes its selection packet, family-specific Task 025
   semantic specifications and host vectors may use disjoint child work
   packages. Shared normalized-operation vocabulary and stable IDs are fixed
   first; integration is serialized.
3. Task 026 contract/design work may overlap late Task 025 validation, but its
   end-to-end implementation gate waits for the accepted Task 025 executable
   tranche.
4. After Task 026 is accepted, Task 027 session/job implementation and Task 028
   family/compound work may run as two implementation lanes because their
   primary code ownership differs. Record-set publication, shared status, and
   aggregate validation still integrate one at a time.
5. The UI vertical slice waits for Tasks 025-027 and accepted UI architecture.
   Fixture-only UI prototyping may occur earlier but cannot become production
   semantics or persistence.

The default concurrency ceiling is two implementation lanes plus one
read-only/design lane. More concurrency is not considered a speedup when it
creates overlapping semantic ownership.

## Serialized ownership surfaces

The following always have one writer and one integration order:

- operation and schema version allocation;
- stable semantic IDs, record-set revisions, and manifest publication;
- shared dispatcher/control-plane behavior;
- authoritative graph, instrument, build-request, and project records;
- CLI root grammar, canonical completion fixtures, and compatibility goldens;
- `README.md`, `docs/STATUS.md`, `docs/ROADMAP.md`, decision/task indexes, and
  governance summaries; and
- staging, commit, push, release, hardware upload, flash, and SD-card action.

Safe parallel ownership may include read-only audits, disjoint review packets,
family-specific semantic specifications and vectors after central allocation,
UI wireframes against immutable fixtures, and task-local negative tests with
separate output namespaces.

## Activation and approval rules

- This plan does not itself start Task 023 or create any Task 023-028 contract.
- Each numbered task requires a complete contract before implementation.
- Completion of one task does not automatically authorize the next.
- UI architecture planning is authorized; UI implementation remains gated.
- Tasks 019 and 020 remain deferred.
- A new hardware diagnostic or connected-device action requires its own exact
  task boundary and explicit approval.
- Staging, commit, push, publication, upload, flash, and SD-card writes remain
  separately authorized actions.
