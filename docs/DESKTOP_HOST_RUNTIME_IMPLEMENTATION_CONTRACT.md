# Task 031: Portable desktop host runtime and JUCE audio/MIDI engine

Status: accepted by explicit user authorization and complete locally on
2026-08-19. The parent and all four serialized children completed in the fixed
order `031A -> 031B -> 031C -> 031D`. The one bounded local Mac audio/MIDI
smoke was performed; no Ksoloti hardware action, listening claim, packaging,
distribution, staging, commit, push, or publication was performed.

## Goal and why it exists

Give Schuss a dependable native desktop execution substrate so an exact saved
Schuss project can be lowered, rendered, and eventually run in real time on a
Mac without making the desktop application, node editor, MIDI controller, CLI,
or AI semantic layer the source of DSP truth.

The desktop host is intended to become the primary sandbox for experimentation:
it can offer much more CPU, memory, debugging support, and iteration speed than
Ksoloti. Ksoloti remains a separately selected constrained export target for
ideas whose exact implementations and resource requirements are compatible.
The Task 031 result therefore concerns core contracts, lowering, native DSP
execution, audio/MIDI devices, and process-local sessions. It does not design
how a musician edits or reasons about those capabilities.

## Dependencies and accepted baseline

Task 031 is governed by ADR 0016, `AGENTS.md`, `docs/PROJECT_CONTEXT.md`,
`docs/ARCHITECTURE.md`, `docs/COMPILER_STRATEGY.md`, the shared operation and
project/workspace contracts, and the evidence separation already established
by ADRs 0010, 0011, and 0014.

The implementation baseline includes:

- the authoritative component-contract and DSP-graph model;
- exact project-owned authoring, immutable history, and compiler planning from
  Task 026;
- the accepted reverb-free seven-node Task 026 profile and its retained local
  Ksoloti level-5 result;
- the Task 028 twenty-item palette at structural and normalized-lowering levels
  1-3, without source-generation, real-time, or audible proof;
- the maintained React/Tauri desktop as one closed client of shared operations;
- the independent AI/MCP authoring lane; and
- process-local build and device-session patterns that retain authority in
  Schuss core rather than the renderer.

No accepted Ksoloti record, generated source, build artifact, evidence result,
project revision, UI operation, or AI operation is reinterpreted as host-runtime
support merely because this parent exists.

## Parent result

The complete Task 031 result is one client-neutral path:

```text
exact saved Schuss project revision
        -> existing graph validation and compiler front half
        -> exact desktop-host implementation resolution
        -> canonical content-addressed host-runtime package
        -> portable schuss_rt execution
        -> deterministic offline render
        -> headless JUCE Core Audio/Core MIDI session
        -> structured process-local status and diagnostics
```

The equivalent Ksoloti path remains independent:

```text
same canonical Schuss project revision
        -> exact Ksoloti implementation resolution
        -> retained Ksoloti backend and ARM build
```

A host success does not imply a Ksoloti success, and a Ksoloti success does not
imply host equivalence. Both consume the canonical Schuss graph rather than one
another's generated output.

## In scope

- A target-independent host-runtime package that records exact project, graph,
  contract, implementation, ABI, parameter, connection, schedule, buffer,
  state, event, latency, tail, sample-rate, and block-policy facts.
- A desktop-host compute target and backend that remain independent of a
  physical device profile, a presentation client, and the Ksoloti target.
- Exact host implementation bindings for only the accepted Task 026 seven-node
  profile during this parent; unsupported nodes fail closed.
- A portable C++17 `schuss_rt` library whose public ABI contains no JUCE,
  Tauri, React, Python, Ksoloti Java, or legacy `.axp` type.
- A precompiled node registry, deterministic graph preparation, bounded buffer
  and state allocation, exact schedule execution, and timestamped events.
- A deterministic command-line offline renderer that consumes the same exact
  runtime package later used by the real-time engine.
- A headless `schuss-audio-engine` process using JUCE only for Core Audio,
  Core MIDI, device lifecycle, real-time callbacks, and bounded telemetry.
- A private versioned engine handshake and control protocol that never carries
  sample buffers through Python, Tauri, or JSON IPC.
- Client-neutral process-local operations for device inspection, offline render
  sessions, and start/inspect/stop audio sessions.
- Direct physical MIDI ingress to the native engine, a bounded timestamped
  event queue, and sample-offset event delivery to `schuss_rt`.
- Focused C++/Python contract tests, deterministic fake engine/device/MIDI
  tests, native sanitizers and real-time-path instrumentation where available,
  fresh-root offline reproduction, and one bounded local Mac real-time smoke.

## Out of scope

- React/Tauri node-editor changes, Start/Stop controls, meters, device selectors,
  MIDI-learn presentation, Web MIDI, or any other desktop interaction work.
- AI semantic planning, MCP tools, prompting, model orchestration, musical-intent
  rules, scene design, sequencer design, controller behavior, or product UX.
- Broad promotion of the Task 028 palette, Mutable-derived objects, transparent
  compounds, project-owned native kernels, or arbitrary user C++.
- VST, Audio Unit, CLAP, plug-in hosting, `juce::AudioProcessorGraph` as graph
  authority, dynamic-library hot loading, or a per-edit native compilation/JIT
  pipeline.
- Windows, Linux, iOS, Android, multi-process audio distribution, cloud audio,
  remote control, durable job recovery, or multi-device orchestration.
- Packaging, signing, notarization, distribution, monetization, public release,
  or a final JUCE/third-party release-license decision. Private personal use is
  the accepted development assumption until distribution is separately chosen.
- Modification, replacement, or weakening of the accepted Ksoloti backend,
  fixed-point semantics, firmware/toolchain boundary, artifacts, or evidence.
- Translation from JUCE/host code into Ksoloti firmware, silent omission of
  host-only nodes, inferred implementation equivalence, or target fallback.
- Connected Ksoloti execution, USB upload, flash, reset, SD-card writes,
  persistent installation, or other hardware mutation.
- A general real-time/resource level-7 claim, subjective audible/listening
  level-8 claim, product safety claim, or release-readiness claim.

## Inputs and deliverables

Inputs are ADR 0016; the accepted Task 026 project/profile, contracts, direct
semantics, compiler and build records; Task 028's exact bounded palette and gap
ledger; current target/backend/build schemas; operation and application
capability v1-v13; process-local build/device services; the current desktop
process boundary; and one pinned JUCE source revision selected for private
personal development.

Parent deliverables are:

1. this accepted parent contract and exact child ownership allocation;
2. additive host target/backend, runtime-package, runtime-observation,
   operation, application-capability, binding, eligibility, and record-set
   contracts introduced only by the child that owns them;
3. the JUCE-independent `packages/schuss_rt/` C++ runtime and unit tests;
4. the headless `apps/schuss_audio_engine/` offline and real-time executable;
5. exact host lowering and seven-node native implementation bindings;
6. deterministic package and WAV fixtures plus fresh-root reproduction;
7. a private engine protocol and process-local `AudioSessionService`;
8. structured device, session, CPU, callback, xrun, MIDI-queue, and failure
   diagnostics without host paths or semantic mutation;
9. focused, adjacent, expensive, and final aggregate evidence; and
10. coherent status, roadmap, architecture, decision/task indexes, and a final
    completion report owned only by the parent integrator.

## Core ownership and runtime rules

The canonical Schuss project and graph remain authoritative. The host-runtime
package is derived, immutable, canonical, and content-addressed. It may identify
exact records and executable implementation factories, but it is not a project,
graph, UI document, process snapshot, or durable session record.

`schuss_rt` owns graph execution. JUCE wraps one complete prepared runtime; an
individual node does not become a JUCE `AudioProcessor`, and a JUCE graph does
not become the Schuss graph. Runtime preparation must complete before graph
activation. The processing path performs no allocation, blocking lock, JSON
parse, filesystem access, logging, Python call, UI call, IPC call, node
construction, or graph destruction.

The engine owns physical audio and MIDI devices. Python Schuss core owns exact
project selection, lowering authority, package identity, process-local session
handles, and application diagnostics. A presentation client may eventually
request an accepted operation and render its result; it does not open devices
or submit unvalidated runtime structures.

Physical MIDI enters the JUCE engine directly. Its callback performs only the
bounded work needed to normalize, timestamp, and enqueue a message. The audio
callback drains accepted events, converts timestamps to valid frame offsets,
and applies declared ordering and overflow rules. UI and Python are absent from
this performance path.

The first version resets graph state when a package starts or is replaced. No
state migration is inferred from matching display names, node IDs, contract
IDs, or implementations. State-preserving live replacement requires a later
explicit contract with exact state-schema and migration identity.

## Evidence boundary

Task 031 preserves the existing independent evidence meanings:

- schema, identity, reference closure, binding resolution, and deterministic
  package generation are structural/compiler facts;
- a successful native C++ build is a host artifact fact, not an execution fact;
- an offline WAV proves only execution under its exact inputs, seed, package,
  toolchain, processor, numeric profile, and render configuration;
- a JUCE session smoke is a process-local host observation, not proof of other
  machines, sustained real-time headroom, safety, or sound quality;
- physical MIDI receipt proves only the exact observed message path and does not
  validate a future controller mapping UX;
- host behavior never implies Ksoloti implementation availability, numeric
  equivalence, resource fit, compile success, device execution, or audibility;
- no Task 031 result proves packaging, distribution, safety, or release readiness.

The existing Schuss levels may be reported where they fit, but the completion
report must not collapse host compile, offline execution, real-time/resource,
and listening into one success state.

## Child work packages and ownership

The four children are serialized. A child starts only after explicit user
activation and after every predecessor acceptance required below. Child
completion never activates the next child and never completes Task 031.

### 2026-08-19 activation and identity allocation

The user's explicit request to run Tasks 031A-031D activates the complete
serialized parent. The parent integrator starts 031A now and advances to each
later child only after its predecessor's focused acceptance contribution
passes. The previously local desktop workspace-shell successor collided with
031A's already reserved operation v14, capability v7, and record-set 000027
identities. Parent integration preserves that feature by moving it forward to
operation v15, capability v8, and record set 000028; no renderer behavior or
semantic ownership changes as part of that prerequisite repair.

031A exclusively allocates the following additional identities:

- build environments `schuss-build-environment-000003@1` and
  `schuss-build-environment-000004@1`;
- host build request `schuss-build-request-000006@1`;
- host native implementation bindings `schuss-implementation-000162@1-2`
  through `schuss-implementation-000168@1-2`, ordered as saw, PWM, soft clip,
  exponential smoother, crossfade, VCA, and stereo output; revision 1 is the
  structural candidate cited by the level-2 claim and revision 2 is the exact
  eligible successor, preserving the strict earlier-evidence rule;
- eligibility companions `schuss-binding-eligibility-000048@1` through
  `schuss-binding-eligibility-000054@1` in that same order;
- structural compatibility claims `schuss-evidence-claim-000075@1` through
  `schuss-evidence-claim-000081@1` in that same order; and
- private JUCE source lock `schuss-third-party-source-lock-000001@1`.

The already reserved target `schuss-compute-target-000002@1`, backend
`schuss-backend-000003@1`, and record set `schuss-record-set-000027@1` remain
unchanged. Tasks 031B-031D allocate no semantic stable IDs. Their package,
render, process, device, and session handles are derived or process-local.

Operation v14 is frozen to six client-neutral operations:
`host.render.start`, `host.render.inspect`, `audio.devices.inspect`,
`audio.session.start`, `audio.session.inspect`, and `audio.session.stop`.

### Task 031A: Host-runtime contracts and exact execution boundary

Goal: define the smallest client-neutral target/backend, package, ABI, operation,
and evidence contracts needed by the later native implementation.

Owned write surface:

- the Task 031 additive schemas, including one host-runtime package v0, one
  host-runtime observation v0, operation request/result v14, and application
  capability description v7;
- exact desktop-host compute-target and backend records;
- the exact Task 031 successor record set and deterministic generator/check
  path;
- host implementation-binding and eligibility allocations for the seven-node
  reference only;
- bounded host-package/lowering modules in `packages/schuss_core/` that stop
  before native execution;
- Task 031A contract tests and fixtures; and
- the pinned private JUCE revision locator and source-integrity rule, without
  packaging or distribution claims.

Reserved parent identities are `schuss-compute-target-000002@1`,
`schuss-backend-000003@1`, and `schuss-record-set-000027@1`. Operation v14,
application capability v7, and the host-runtime v0 schema names are exclusive
to Task 031. 031A owns any additional exact binding/eligibility IDs and must
freeze their complete allocation in its accepted activation contract before
writing records. Tasks 031B-031D allocate no stable semantic IDs.

031A must preserve every accepted parent record byte and must not compile C++,
open an audio/MIDI device, modify the desktop renderer, or claim runtime
behavior. It contributes acceptance tests 1-5 and 20.

### Task 031B: Portable `schuss_rt` runtime and node ABI

Goal: implement a JUCE-independent C++ runtime that can prepare and execute one
closed graph package using precompiled node factories.

Owned write surface:

- `packages/schuss_rt/**`;
- the native CMake target and C++ unit-test fixtures for the portable runtime;
- the closed node registry and exact runtime ABI implementation; and
- no Python, JUCE, Tauri, React, project, record, schema, or Ksoloti files except
  narrowly scoped test fixtures explicitly assigned by 031A.

031B must prove package validation, deterministic preparation/reset, bounded
state and buffer allocation, schedule execution, event ordering, unknown-node
rejection, and no allocation/blocking lock in the instrumented processing path.
It may use simple private test nodes before the seven-node host bindings exist.
It contributes acceptance tests 6-9 and 20.

### Task 031C: Exact host lowering and deterministic offline renderer

Goal: connect the accepted Task 026 seven-node project/profile to `schuss_rt`
and prove one deterministic headless offline execution path.

Owned write surface:

- the final bounded host lowering and package-generation implementation in
  `packages/schuss_core/`;
- exact C++ node realizations or adapters required only by the seven-node
  profile, within the 031A bindings;
- the offline portion of `apps/schuss_audio_engine/**`;
- deterministic runtime-package, input/event, output-WAV, and diagnostic
  fixtures; and
- Task 031C focused and fresh-root tests.

031C must lower an exact saved project revision, select every host binding once,
produce canonical package bytes, build the native renderer, and reproduce the
exact declared WAV in two fresh roots/processes under the pinned host
configuration. It must open no Core Audio/Core MIDI device and invoke no
Ksoloti build, Java, `.axp`, USB, or hardware operation. It contributes
acceptance tests 10-14 and 20.

### Task 031D: Headless JUCE engine and process-local audio sessions

Goal: host the accepted `schuss_rt` package through Core Audio and Core MIDI and
expose lifecycle and diagnostics through shared Schuss session operations,
without implementing any interaction client.

Owned write surface:

- the JUCE adapter, real-time engine, device registry, MIDI queue, telemetry,
  and private protocol in `apps/schuss_audio_engine/**`;
- `packages/schuss_core/audio_sessions.py` and the bounded engine-protocol
  adapter;
- the v14 dispatcher/capability integration fixed by 031A;
- deterministic fake-engine/audio/MIDI tests and one explicitly authorized
  local Mac smoke fixture; and
- no file under `apps/schuss_desktop/src/`, no React/Tauri presentation code,
  and no AI/MCP implementation file.

031D must prove explicit device inspection, exact engine handshake, off-thread
package preparation, start/inspect/stop lifecycle, direct native MIDI ingress,
bounded event delivery, structured crash/disconnect diagnostics, and project
immutability. One local real-time smoke may measure CPU, callback duration, and
xruns but may not claim general level-7 fitness or audible level-8 behavior.
It contributes acceptance tests 15-20.

### Parent integration ownership and order

The Task 031 parent integrator exclusively owns this contract, child activation
records, exact cross-child allocation, final operation/record-set publication,
current governance/index updates, aggregate validation, completion reporting,
and any Git action.

The order is strictly `031A -> 031B -> 031C -> 031D`. The parent may explicitly
authorize a read-only design or test-fixture lane in parallel, but no two
children may write the same schema, package ABI, native runtime interface,
engine protocol, stable IDs, record-set manifest, current status, or
publication state.

## Validation cadence

Focused validation is child-specific:

- 031A: schema/meta-schema, exact-reference, record-set ancestry, deterministic
  generation, lowering/package negative cases, and no-execution assertions;
- 031B: C++ unit tests, malformed packages, state/buffer bounds, schedule/event
  order, reset determinism, sanitizers where available, and instrumented
  real-time-path allocation/lock guards;
- 031C: exact host resolution, package/WAV determinism, chunking behavior,
  native build, two fresh roots/processes, and no-device/no-Ksoloti assertions;
- 031D: fake engine/device/MIDI/session lifecycle, protocol mismatch, crash and
  disconnect containment, callback safety instrumentation, and one bounded
  local Mac smoke after implementation freeze.

Adjacent regression covers existing graph/project operations, compiler front
half, Task 026 authoring/build selection, Task 028 semantics, application
capabilities, desktop closed-operation boundaries, AI/MCP isolation, and exact
Ksoloti source/artifact regression. No child may reinterpret a retained
Ksoloti golden to make a host test pass.

Expensive reproduction occurs only after the relevant child implementation is
otherwise frozen. 031C performs the required two-root native build and offline
render once. 031D performs at most one declared local real-time smoke per final
candidate unless diagnosis requires a separately recorded rerun. No connected
Ksoloti, flash, SD, subjective listening, packaging, or distribution action is
part of this reproduction.

The parent reviews the complete diff, generated freshness, negative cases,
child acceptance matrix, and Ksoloti byte preservation before one final
inventory/catalog/contracts/native aggregate. A failed aggregate is diagnosed
with only affected focused and adjacent tests before one final rerun, following
`AGENTS.md`.

## Acceptance tests

1. ADR 0016 and this contract state that the portable native runtime and host
   backend are core execution components, while node UI, AI semantics, and
   client interaction remain separate.
2. The parent fixes four serialized children, their goals, dependencies, owned
   write surfaces, stable-ID authority, acceptance contributions, and parent
   integration ownership; none is automatically activated.
3. 031A adds only additive schemas/records and exact parent-preserving record
   set `schuss-record-set-000027@1`; every accepted Ksoloti and project byte
   remains unchanged.
4. The host-runtime package is canonical, content-addressed, derived, and
   non-authoritative; it contains no absolute path, timestamp, UI layout,
   process ID, JUCE class, Tauri state, Python object, or Ksoloti Java object.
5. Host target/backend and every seven-node host binding resolve exactly once;
   missing, stale, duplicate, ambiguous, ABI-mismatched, or ineligible records
   fail before package publication or execution.
6. `packages/schuss_rt/` builds and tests without linking or including JUCE,
   Tauri, React, Python, Ksoloti Java, legacy `.axp`, or platform GUI code.
7. Runtime preparation performs all node creation and state/buffer allocation
   before processing; the instrumented processing path allocates no memory,
   acquires no blocking lock, parses no JSON, and performs no filesystem or IPC
   operation.
8. Runtime reset, event ordering, graph schedule, buffer routing, and output are
   deterministic under the exact declared package, input, seed, ABI, toolchain,
   and host configuration.
9. Unknown node IDs, invalid ports, cycles unsupported by the declared schedule,
   undersized state/buffer plans, non-finite parameters, and malformed events
   fail closed without out-of-bounds access or partial activation.
10. One exact saved Task 026 project revision lowers through the desktop-host
    backend to one exact runtime package using only its accepted seven-node
    profile and exact host bindings.
11. Two fresh roots/processes reproduce byte-identical package JSON, structured
    diagnostics, render configuration, and WAV output for the exact pinned
    offline test environment.
12. Supported renderer chunk sizes produce the declared equivalent output, or
    the package explicitly rejects an unsupported block policy before execution.
13. Offline rendering opens no physical audio/MIDI device, invokes no JUCE
    real-time callback, and performs no Ksoloti build, Java, `.axp`, USB, upload,
    flash, reset, SD, or hardware action.
14. A host render result records only exact offline execution facts and does not
    promote real-time/resource, audible/listening, Ksoloti-equivalence, safety,
    packaging, or release evidence.
15. The JUCE engine validates one exact protocol/runtime/package ABI handshake,
    enumerates devices only after explicit intent, prepares the graph off-thread,
    and starts only an accepted package/session.
16. Core Audio invokes one complete `schuss_rt` graph; physical Core MIDI input
    enters the native engine directly, is timestamped into a bounded queue, and
    reaches the graph as declared sample-offset events without React or Python
    in the performance path.
17. Session start snapshots one exact project revision. Later project edits,
    stale handles, engine restarts, or another workspace cannot silently
    retarget the active session.
18. Engine crash, device removal, protocol mismatch, queue overflow, preparation
    failure, and stop failure produce stable structured diagnostics, leave the
    project unmodified, and never report a successful active session.
19. One declared local Mac smoke reports exact device, sample rate, buffer size,
    package hash, CPU/callback measurements, and xrun count without claiming
    general real-time headroom or subjective audible quality.
20. Focused and adjacent suites, deterministic generation, two-root offline
    reproduction, native sanitizers/instrumentation where available, Ksoloti
    regression, governance checks, `git diff --check`, and one final aggregate
    complete with inherited failures reported separately.

## Decisions Task 031 may make

- The smallest portable C++ node ABI, package layout, buffer planner, state
  ownership model, event representation, registry API, and deterministic
  schedule needed by the seven-node reference.
- The exact private engine protocol framing, process-local session handles,
  bounded queue capacities, telemetry fields, device locator representation,
  and failure diagnostics within the fixed security and real-time rules.
- The pinned JUCE revision and minimal headless JUCE modules used for private
  personal development.
- Whether the initial seven-node host realization uses one compatibility numeric
  profile, one native float profile, or both, provided each is explicitly named,
  tested, and never presented as implicit Ksoloti equivalence.
- The exact child-local file layout and test harness within the parent-owned
  paths, so long as semantic ownership remains in Schuss core and JUCE remains
  outside `schuss_rt`.

## Decisions Task 031 must not make

- A new authoritative graph, project, instrument, catalog, or UI model; a JUCE
  `AudioProcessorGraph` source of truth; or a private semantic route for Tauri,
  CLI, AI, MCP, or a MIDI controller.
- Node-editor, AI reasoning, scene, sequencer, mapping UX, controller behavior,
  product interaction, or visual design decisions.
- Silent host/Ksoloti fallback, omission of unsupported nodes, inferred target
  equivalence, rewrite of accepted Ksoloti semantics, or translation of host
  generated code into firmware.
- Broad catalog or Mutable promotion, arbitrary native code, plug-in hosting,
  packaging, signing, notarization, distribution, monetization, or release
  licensing approval.
- Connected Ksoloti execution, firmware/SD mutation, hardware upload, general
  real-time/resource promotion, audible/listening approval, staging, commit,
  push, tagging, or publication except when the user separately authorizes the
  exact Git action for the parent integration.

## Activation and completion state

The user's explicit 2026-08-19 request activated the complete serialized
parent. All four child contributions and the exact end-to-end headless path are
complete locally. Record set `schuss-record-set-000027@1`, the portable
`schuss_rt` runtime, deterministic offline package/WAV, headless JUCE engine,
process-local services, and retained bounded observations are the parent result.

The local Mac observation does not promote general real-time/resource level 7
or audible level 8. No physical MIDI input was available, so physical Core MIDI
receipt remains unproved. UI and AI presentation, Ksoloti equivalence or device
work, packaging, distribution, release licensing, staging, commit, push, and
publication remain outside this completion and require separate authority.

The final aggregate completed after the implementation freeze: inventory and
catalog suites pass, and the 446-test contract suite retains only the three
previously audited historical catalog/CLI/freshness failures. No Task 031 or
adjacent current-record regression failed, and no historical golden was
rebaselined to obtain this completion.
