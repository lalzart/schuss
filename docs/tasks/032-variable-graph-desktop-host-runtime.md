# Task 032: Bounded variable-graph desktop host runtime and safe patch replacement

Status: explicitly activated by the user and completed locally on 2026-08-19.
All three serialized phases completed in order. No physical audio/MIDI or
Ksoloti device action, staging, commit, push, tagging, or publication was
performed. Final aggregate validation completed on 2026-08-20.

## Goal and why it exists

Turn Task 031's exact seven-node desktop-host proof into a reusable but still
bounded graph-execution path. An exact saved Schuss project should be able to
run when its graph contains any valid acyclic arrangement and repetition of the
seven already accepted Task 031 host node types, instead of matching one fixed
node count, identity list, role order, topology, and memory plan.

The task also establishes one safe process-local replacement path: Schuss core
prepares a complete successor package away from the audio callback, the native
engine activates it only at a declared block boundary, and the replacement
starts with reset state. A rejected replacement leaves the currently active
graph running and the project unchanged.

This exists because Task 031 proved the complete project-to-offline/JUCE route,
but its v0 runtime and lowerer intentionally recognize only the reference
seven-node profile. Adding product UI or a broad DSP palette before removing
that whole-profile assumption would turn a proof fixture into a permanent
creative restriction.

Precision remains a feature, not the restriction being removed. Every graph,
contract, binding, project revision, package, schedule, buffer, state region,
and replacement request remains exact, versioned, and fail-closed.

## Exact baseline and authority

Task 032 extends ADR 0016 without changing its ownership or evidence rules. Its
accepted implementation baseline is local commit `932f310`, exact Task 031
record set `schuss-record-set-000027@1` with content hash
`sha256:6b54936e301b18374b13bb178bfe683cb525b0d8ae9ed89e20d62e682616bb18`,
and current application successor `schuss-record-set-000028@1` with content
hash `sha256:f883bc214c859a758883768cef06d97b8de19b6f62c2908c0fa4758b5a2756a5`.

The frozen Task 031 reference consists of:

- `host-runtime-package-v0`, `schuss-rt-abi-v0`, and
  `schuss-audio-engine-protocol-v0`;
- host target `schuss-compute-target-000002@1` and backend
  `schuss-backend-000003@1`;
- eligible host bindings `schuss-implementation-000162@2` through
  `schuss-implementation-000168@2`, ordered as saw, PWM, soft clip,
  exponential smoother, crossfade, VCA, and stereo output;
- exact derived package hash
  `sha256:a18ee43608514571768e636f8e8600d0cb38b4109b86f789451160233bc7fc70`;
  and
- the 48,000-frame reference stereo WAV SHA-256
  `ae2b8eff76d079b85c74f4d33d555699f8812cb0b72ea459014ee9a90e9ead7c`.

Those v0 bytes remain immutable historical and regression authority. Task 032
must add successors rather than reinterpret, regenerate, or replace them.

The Task 028 twenty-item palette remains structural and normalized-lowering
evidence only. Task 030 catalog visibility, project-local transparent
compounds, and native kernels do not become host-executable merely because
Task 032 exists.

## Activation and allocation gate

This task became active when the user explicitly requested implementation on
2026-08-19. That request activates the complete task in the ordered phases
below. Before writing any schema, record, generated artifact, or runtime code,
the activation run must:

1. verify the live branch, worktree, exact parent record set, Task 031 fixture
   bytes, and absence of conflicting staged or user-owned changes;
2. inventory the then-current schema, operation, capability, target, backend,
   binding, eligibility, evidence, and record-set allocations;
3. freeze the exact additive successor allocations in this contract and its
   deterministic generator before emitting records; and
4. stop and report a conflict if the live parent or accepted ADR boundary no
   longer matches this proposal.

No semantic stable ID is reserved merely by creating this proposed contract.
The conceptual successor names `host-runtime-package-v1`, `schuss-rt-abi-v1`,
and `schuss-audio-engine-protocol-v1` are owned by Task 032 if and when it is
explicitly activated.

### 2026-08-19 activation and exact allocation

The activation audit found clean `main` and `origin/main` at contract commit
`7eb8f927be87517eb56ae408b388993379e3d699`, with Task 031 implementation
baseline `932f310`, no staged or user-owned changes, fresh Task 031 generators,
and the frozen Task 031 package, observation, record-set, and WAV bytes intact.

Task 032 exclusively allocates:

- successor record set `schuss-record-set-000029@1`, parented exactly to
  `schuss-record-set-000028@1`;
- host build-request template `schuss-build-request-000007@1`, used only as a
  source for exact project-owned host requests and never as ambient runtime
  selection;
- schemas `host-runtime-package-v1`, `host-runtime-observation-v1`,
  `host-engine-protocol-v1`, `schuss-operation-request-v16`,
  `schuss-operation-result-v16`, and
  `schuss-application-capability-description-v9`; and
- retained fixture projects `schuss-project-000032`, `000033`, and `000034`
  for the smaller, seven-node reference, and larger graph respectively. Their
  deterministic owned graph/instrument/request IDs are `068746`/`237474`/`139035`,
  `508458`/`289694`/`413229`, and `667107`/`191798`/`808211` under the existing
  `schuss-graph`, `schuss-instrument`, and `schuss-build-request` prefixes.

Task 032 allocates no new compute target, backend, component contract,
implementation binding, eligibility, or evidence-claim stable ID. It reuses
the exact Task 031 target/backend and seven revision-2 eligible host bindings.
Any incompatible graph fails rather than allocating or inferring another
implementation. The accepted client-neutral operation addition is exactly
`audio.session.replace`; the six Task 031 host operations remain byte-frozen in
their v14 contract and are carried forward through the additive v16 surface.

## In scope

- An additive v1 host-runtime package and portable runtime ABI with bounded,
  variable node, connection, schedule, buffer, state, parameter, and event
  counts.
- A factory registry whose descriptors own exact ports, parameters, state
  size/alignment, preparation, reset, event, and processing functions. Package
  parsing and scheduling must not contain the reference graph's node IDs,
  fixed role order, or whole-topology whitelist.
- Repeated instances of one registered factory and arbitrary valid graph node
  IDs. The same saw, crossfade, VCA, or other accepted factory may appear more
  than once when every instance has exact contract and binding references.
- Deterministic acyclic scheduling, connection validation, and bounded buffer
  reuse derived from the complete validated graph rather than the Task 031
  role table.
- Bounded state, buffer, event, and node storage allocated completely during
  preparation. The processing callback retains Task 031's no-allocation,
  no-blocking-lock, no-parse, no-filesystem, no-IPC, and no-destruction rules.
- General host lowering for exact project-owned graph, instrument, and host
  build-request revisions composed only of the seven Task 031 host-supported
  component contracts. The lowerer must consume an explicit project member
  reference and may not rely on one global build-request ID or one semantic
  profile signature.
- An exact one-stereo-output initial boundary. Other node types may repeat or
  be absent where their typed connections permit; unsupported disconnected
  audio, missing output, extra output, or incompatible ports fail before
  package publication.
- The existing fixed-Q27, 48,000 Hz, maximum-512-frame numeric and block
  profile as the only Task 032 execution profile. Numeric and sample-rate
  expansion remain later decisions.
- At least three retained variable-graph fixtures: one smaller graph, the exact
  Task 031 seven-node reference, and one larger graph that repeats factories
  and uses a different valid topology and schedule.
- Deterministic offline rendering for every retained graph fixture, including
  supported block-size equivalence and two fresh-root/process reproduction for
  the final larger fixture.
- One additive client-neutral replacement operation and private engine message
  path. The request must identify the active session generation, expected
  active package, exact successor project revision, and exact successor host
  build request.
- Off-thread successor lowering and preparation, one bounded pending
  replacement per session, block-boundary activation, explicit reset-state
  reporting, and destruction of the retired runtime away from the callback.
- Failure containment: invalid, stale, ambiguous, oversized, unsupported, or
  failed successor preparation leaves the prior package active and produces a
  stable structured diagnostic without mutating either project.
- Additive schemas, target/backend/binding eligibility successors where exact
  compatibility requires them, one deterministic successor record set, shared
  core operation/capability integration, focused C++/Python tests, adjacent
  regressions, sanitizer/instrumentation checks, and current governance.

## Out of scope

- Adding host support for any Task 028 or Task 030 implementation beyond the
  seven exact Task 031 host node types.
- Broad catalog promotion, new musical families, new component contracts, new
  DSP algorithms, effects, sampling/assets, polyphony, voice allocation, scene
  behavior, or sequencer design.
- Transparent-compound or project-local native-kernel host lowering, arbitrary
  user C++, dynamic libraries, hot-loaded code, JIT compilation, plug-in
  hosting, VST, Audio Unit, or CLAP.
- Cyclic graphs, implicit feedback, algebraic loops, or inferred delay
  semantics. A later task must introduce an exact delay/lifetime contract
  before any cycle is executable.
- Implicit rate, representation, channel, unit, ownership, or facet-kind
  conversion. A client may later offer an explicit adapter node; Task 032 may
  not silently insert one.
- State migration between packages. Every successful Task 032 replacement
  starts the successor runtime from its declared reset state, even when node
  IDs, display names, contracts, or bindings match.
- Claiming click-free, gapless, musically seamless, or subjectively acceptable
  replacement. The task may select and measure one deterministic bounded
  transition policy, but listening remains separate.
- Float DSP, alternate numeric profiles, sample rates other than 48,000 Hz,
  blocks above 512 frames, more than two output channels, audio input, network
  audio, multiple audio devices, or distributed processing.
- React/Tauri presentation, Play/Stop buttons, device selectors, meters,
  node-editor behavior, MIDI-learn UI, CLI ergonomics, AI/MCP tools, prompting,
  or controller-mapping UX.
- Changes to the authoritative graph, project, instrument, or catalog model;
  use of a JUCE graph as semantic authority; or sample buffers through Python,
  JSON IPC, Tauri, or React.
- Ksoloti lowering, Java, `.axp`, ARM build/link, USB, connected hardware,
  upload, flash, reset, SD-card mutation, firmware work, or host/Ksoloti
  equivalence claims.
- Physical Core Audio/Core MIDI smoke, general real-time/resource level 7,
  audible/listening level 8, packaging, signing, notarization, distribution,
  monetization, release licensing, staging, commit, push, tagging, or
  publication.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADR 0016, the architecture,
compiler, operation, project/workspace, target/backend, and Task 031 contracts;
the exact Task 031 runtime/package/engine implementation and retained fixtures;
the current shared compiler front half and project service; the exact seven
host bindings and eligibilities; and the current successor application record
set verified at activation.

Deliverables are:

1. this activated contract with frozen exact allocations and unchanged scope;
2. additive v1 package, runtime ABI, engine protocol, operation, capability,
   and any exact target/backend/binding-eligibility successor contracts;
3. a deterministic generator and exact successor record set;
4. a registry-based variable-graph `schuss_rt` implementation with bounded
   preparation and processing storage;
5. project-aware variable-graph host lowering through the existing compiler
   front half, with an explicit project-owned host build request;
6. the smaller, frozen-v0 reference, and larger repeated-factory fixtures plus
   exact offline outputs and structured observations;
7. safe prepare/activate/fail-preserve replacement behavior in the private
   engine protocol and shared process-local session service;
8. focused, adjacent, expensive-reproduction, sanitizer/instrumentation, and
   final aggregate evidence; and
9. coherent status, roadmap, history-after-completion, task-index,
   architecture, compiler, operation, target/backend, and final completion
   documentation.

## Ordered implementation phases and ownership

Task 032 is one task with three serialized implementation phases. Explicitly
running Task 032 activates the full task, but a later phase may begin only after
the predecessor's focused checks pass.

### Phase 1: Successor contracts and exact allocation

Owns additive schemas, exact successor identity allocation, record generation,
package/ABI/protocol descriptors, operation/capability declarations, and
negative contract fixtures. It performs no native build, lowering execution,
process launch, or device access.

### Phase 2: Variable runtime, lowering, and offline fixtures

Owns `packages/schuss_rt/**`, the bounded host-lowering successor in
`packages/schuss_core/`, native offline-renderer changes, variable-graph
fixtures, registry/scheduler/buffer/state tests, native build, sanitizers, and
fresh-root offline reproduction. It performs no physical device access and no
session replacement activation.

### Phase 3: Safe process-local replacement

Owns the additive private engine prepare/activate messages, shared session
replacement service and operation, fake-engine/native callback harness,
stale-generation and failure-containment tests, and process-local telemetry.
It changes no renderer UI, AI/MCP route, physical-device policy, or project
semantics.

Current governance, final allocation publication, aggregate validation,
completion reporting, and any separately authorized Git action remain owned by
the Task 032 integrator. No phase may edit a surface owned by a later phase to
claim early completion.

## Runtime and replacement rules

1. The authoritative input is an exact accepted project revision. The v1
   package remains derived, immutable, canonical, content-addressed, and
   non-authoritative.
2. Runtime ceilings must be explicit package/ABI facts with focused boundary
   tests. Exceeding a ceiling fails during lowering or preparation, never after
   partial activation.
3. Factory selection uses exact eligible binding and factory identity. Unknown,
   missing, stale, duplicate, or ambiguous factories fail closed.
4. A factory descriptor may be instantiated repeatedly without parser,
   scheduler, or whole-graph source changes.
5. The schedule must be derived deterministically from typed connections with
   a declared tie-break rule. Array order, map iteration, filesystem order, or
   node display names may not choose execution order.
6. Every input is connected exactly once or has an explicit contract-defined
   package value. Multiple drivers, invalid facets, incompatible streams,
   dangling required inputs, and unsupported cycles fail before execution.
7. Buffer and state plans are exact, non-overlapping, aligned, and bounded.
   Preparation owns allocation; processing owns only preallocated storage.
8. A replacement first snapshots and revalidates the exact successor project
   and request, lowers and prepares it off-thread, and only then asks the audio
   thread to exchange one complete prepared-runtime handle.
9. The callback performs only a bounded atomic or lock-free activation step at
   a block boundary. It does not parse, allocate, destroy, block, log, access
   files, call Python, or wait for the control process.
10. Replacement success records old and new package hashes, the exact accepted
    project references, activation generation, reset-state policy, and measured
    transition facts. It does not rewrite the project or imply sound quality.
11. Replacement failure retains the old active package and session generation.
    The successor is disposed off-thread and cannot become partially visible.
12. Engine crash, device loss reported by fakes, stale handle, concurrent
    replacement, timeout, protocol mismatch, or callback rejection produces a
    stable diagnostic and never reports the successor active.

## Validation cadence

Focused checks cover the proposed/active status gate, additive schema and exact
allocation closure, v0 byte preservation, variable package validation, factory
registry, repeated instances, deterministic schedule, state/buffer bounds,
event addressing, callback guards, project/request selection, replacement
state machine, failure preservation, generator freshness, and governance.

Adjacent regression covers Task 031 package/WAV bytes and all six host
operations; Task 026 project authoring/history; the shared compiler front half;
Task 028's level-3-only palette boundary; desktop closed-operation allowlists;
AI/MCP isolation; and exact Ksoloti source/artifact paths. No historical golden
may be rewritten to make the successor pass.

Expensive reproduction occurs once after the implementation is otherwise
frozen: native warnings-as-errors builds, sanitizers/instrumentation where
available, all declared offline block sizes, and two fresh roots/processes for
the larger variable graph. No physical audio/MIDI device or Ksoloti hardware is
part of the expensive reproduction.

The integrator then reviews the complete diff, generated freshness, exact v0
preservation, negative cases, and acceptance matrix as the implementation
freeze. One final inventory/catalog/contracts/native aggregate runs after that
freeze. If it fails, only affected focused and adjacent checks are repeated
until the correction is frozen, followed by at most one final aggregate rerun.

## Acceptance tests

1. The task remained implementation-inactive until the explicit 2026-08-19
   request to run Task 032; contract creation alone changed no runtime or
   semantic record.
2. Activation verifies and freezes the exact parent, successor allocations,
   and write ownership before any generator or implementation change.
3. Every accepted Task 031 v0 schema, record, package, observation, and WAV
   remains byte-identical, including the declared reference WAV hash.
4. The additive v1 package and runtime ABI declare tested finite ceilings for
   nodes, connections, buffers, state, parameters, events, and schedule length.
5. Package parsing and scheduling contain no fixed Task 031 node IDs, seven-role
   order, exact node count, exact connection count, or whole-profile signature.
6. The registry resolves every package node through one exact eligible factory
   descriptor and permits repeated factory instances without changing parser
   or scheduler source.
7. The lowerer consumes one exact project-owned graph, instrument, and host
   build request through the shared compiler front half; it does not use the
   global Task 031 request ID or ambient/latest record discovery.
8. Typed port validation rejects invalid facets, incompatible stream types,
   multiple drivers, missing required values, unsupported disconnected audio,
   missing/extra outputs, and implicit conversion before package publication.
9. The scheduler produces one deterministic topological order under its exact
   tie-break rule and rejects every unsupported cycle before preparation.
10. State and buffer planning is deterministic, aligned, non-overlapping, and
    within declared bounds; malformed plans fail without out-of-bounds access
    or partial activation.
11. The smaller graph, exact seven-node reference, and larger repeated-factory
    graph all lower and render through the same v1 path. Their package bytes,
    diagnostics, and WAVs are deterministic under the pinned configuration.
12. Every supported offline chunk size produces the declared identical output
    for each fixture, or an unsupported size fails before execution.
13. The instrumented processing path allocates no memory, takes no blocking
    lock, parses no data, performs no filesystem/IPC/logging call, and creates
    or destroys no node/runtime object.
14. A valid successor package is lowered and prepared off-thread, activated as
    one complete runtime at a block boundary, begins from reset state, and
    reports exact old/new identity without mutating either project.
15. Stale generation, unexpected active hash, concurrent replacement,
    malformed package, unsupported graph, preparation failure, protocol error,
    and activation rejection all leave the old graph active and observable.
16. The retired runtime is reclaimed off-thread only after the callback can no
    longer reach it; sanitizers and deterministic stress tests find no leak,
    use-after-free, race accepted by the declared model, or allocation guard
    violation.
17. The replacement operation is client-neutral and capability-declared. No
    React/Tauri, CLI, AI/MCP, or controller client receives a private semantic
    or device route in this task.
18. No new public DSP node type or broad palette support is claimed; Task 028,
    Task 030, compounds, native kernels, Ksoloti, physical-device, real-time
    level 7, audible level 8, packaging, and release states remain unchanged.
19. Focused and adjacent checks pass; final larger-fixture fresh-root outputs
    are byte-identical; the reviewed frozen diff is clean; and one final
    aggregate completes with inherited unrelated failures reported separately.

## Decisions Task 032 may make

- The exact additive schema, operation, capability, target/backend successor,
  eligibility/evidence, and record-set allocations after the activation audit.
- The finite v1 node, connection, buffer, state, parameter, event, and schedule
  ceilings, justified by deterministic preparation/resource tests.
- The registry descriptor layout, prepared-node representation, function
  dispatch mechanism, deterministic topological tie-break, and bounded buffer
  reuse algorithm.
- The exact smaller and larger fixture topologies using only the seven accepted
  host node types.
- The private prepare/activate protocol framing, one client-neutral replacement
  operation shape, process-local handle fields, timeout, and stable diagnostics.
- One deterministic reset-state transition policy, including a bounded mute or
  crossfade only if its resource ownership and exact output are specified and
  tested without a subjective claim.
- Narrow internal refactoring needed to preserve Task 031 v0 compatibility and
  remove whole-profile assumptions from the v1 path.

## Decisions Task 032 must not make

- A new authoritative project, graph, instrument, catalog, family, component,
  or UI model, or a JUCE graph as source of truth.
- New public DSP semantics or host support outside the seven exact Task 031
  node types; broad Task 028/030 promotion; or inferred implementation
  compatibility from catalog/source presence.
- Silent node omission, implicit adapters/conversions, ambient/latest lookup,
  fallback to another binding/backend, or host/Ksoloti equivalence.
- Cyclic scheduling, inferred feedback delay, state migration, polyphony,
  assets/sampling, float or alternate-rate execution, arbitrary code, JIT,
  dynamic libraries, or plug-in hosting.
- React/Tauri presentation, node-editor behavior, CLI product design, AI/MCP
  behavior, controller mappings, scenes, sequencing, or any other interaction
  design.
- Ksoloti Java/`.axp` changes, ARM build, USB, connected device, upload, flash,
  reset, SD mutation, physical audio/MIDI smoke, listening approval, general
  real-time/resource promotion, packaging, distribution, or release licensing.
- Mutation or rebaselining of accepted Task 031 v0 bytes, historical goldens,
  source evidence, or unrelated user work.
- Staging, commit, push, tagging, or publication without a separate explicit
  user request after the complete implementation diff is reviewed.

## Completion boundary and retained result

Task 032 is complete for exact record set `schuss-record-set-000029@1`, content
hash `sha256:8d6d8e5b0c3a90862f1e7c9ddab9c054a7b5908f268db9fa356c131bdc37c55c`.
The smaller, seven-node reference, and larger repeated-factory projects all
lower and execute through the same bounded registry-based v1 runtime. The
larger package is
`sha256:63463753a23753c0a03b362be3f9b953493f95dad6f588b514eaf6dbd7f5419c`;
two isolated copied roots reproduced its retained WAV SHA-256
`586199d4773cb84941752eb6265b525f442e4840a3cbb85346446b677f25b363`.

The replacement slot prepares one complete successor off the callback,
exchanges it at one audio-block boundary using lock-free atomics, starts it
with reset state, and reclaims the retired runtime off the callback. Focused
fake-engine tests, a 64-swap concurrent native stress test, warnings-as-errors
builds, AddressSanitizer/UndefinedBehaviorSanitizer, and ThreadSanitizer pass.
The retained Task 031 package, observation, and WAV bytes remain exact.

After the reviewed implementation freeze, inventory passed 14 tests, catalog
passed 6 tests, and the native aggregate passed 3 tests. The contracts
aggregate completed 458 tests with only the three pre-existing unrelated
retained-golden failures in Task 011A/023 catalog output, Task 023 CLI-v2
output, and Task 027 generated catalog freshness. Every Task 032 test passed;
no historical golden was changed. The exact acceptance matrix and command
results are retained in
`evidence/task032-completion-v1/validation-summary.json`.

Completion does not mean that every catalog object runs, that replacement is
click-free or sounds seamless, that Ksoloti is equivalent, or that physical
device, general real-time/resource level 7, audible level 8, packaging, or
release evidence has been earned.
