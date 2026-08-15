# Task 009: Minimal deterministic legacy-backend proof

Status: complete. Execution was explicitly authorized on 2026-08-15. The
complete restart preflight passed before bridge or ARM-tool invocation, the
authorized probe passed, ordinary `build.resolve` selected the promoted exact
binding, and the production handler reproduced deterministic artifacts through
ARM compile/link. No device, firmware installation, upload, flash, real-time,
or audible action occurred.

Prerequisites: `009-prerequisite-authenticated-environment-and-probe-contract`
and `009-prerequisite-closure-repair-and-reauthentication` must be complete
before this task can become active. Task 009 consumes their authenticated
environment, retained-product closure, explicit record sets, and accepted probe
contracts; it must not recreate or redesign them.

Work in the Schuss repository. Work only on Task 009 after the user explicitly
approves running this task.

This is a bounded executable-backend proof for the exact Task 006 Blend graph
on the Task 007 Ksoloti Core and transitional legacy-backend contract. It must
implement and exercise one deterministic path through legacy `.axp` generation,
the isolated Java compatibility bridge, generated source, and ARM compile/link.
It must not become a general compiler, a product CLI, a graph editor, a device
runtime, or a firmware/hardware task.

Before changing anything, read completely:

- `AGENTS.md`;
- `README.md`;
- `docs/PROJECT_CONTEXT.md`;
- `docs/ARCHITECTURE.md`;
- `docs/SCHEMA_STRATEGY.md`;
- `docs/COMPILER_STRATEGY.md`;
- `docs/LEGACY_STRATEGY.md`;
- `docs/ROADMAP.md`;
- `docs/OPERATION_CONTRACTS.md`;
- `docs/DEVICE_INSTRUMENT_CONTRACTS.md`;
- `docs/COMPONENT_GRAPH_CONTRACTS.md`;
- `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`;
- ADRs 0005, 0006, and 0007;
- Tasks 004 through 008, including their completion evidence;
- all Task 005-008 schemas, production records, validators, fixtures, tests,
  operation envelopes, and the backend-invocation seam;
- the complete Task 009 prerequisite contract, completion report, accepted and
  prospective record-set manifests, authenticated environment record, capture
  evidence, probe schemas, procedure, and `not-run` fixtures;
- the complete Task 009 prerequisite repair contract, repaired capture
  evidence, content-addressed product manifest, and stop-code verdicts;
- `legacy/ksoloti-bridge/README.md`;
- `catalog/sources.lock.json` and the exact pinned `patcher` source commit;
- ignored local source configuration only as a locator for pinned read-only
  evidence; and
- the exact locally available Java runtime, legacy application/runtime,
  firmware/runtime closure, and GNU Arm Embedded tools proposed for the proof.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Context

Task 008 completed the shared headless operation boundary. Production
`build.resolve` currently returns one candidate with status `unresolved`, no
selected binding, and no backend invocation. Its blocking reasons are:

```text
BINDING_TARGET_BACKEND_PAIR_NOT_EVALUATED
CAPABILITY_UNRESOLVED:audio-stream-fixed-q27
CAPABILITY_UNRESOLVED:control-stream-fixed-q27
COMPATIBILITY_EVIDENCE_MISSING
```

This is correct. Task 009 must not erase those facts or relabel the existing
records. It must establish new evidence and new exact record revisions.

The prerequisite establishes these exact starting boundaries:

```text
accepted default record set
    schuss-record-set-000001 r1
    sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6

prospective prerequisite record set
    schuss-record-set-000002 r1
    sha256:6f2855c384ef8bab88991a6cabdd8416c7f3c59a010eed0c6cda1ac08651ecaf

authenticated environment
    schuss-prerequisite-environment-000001 r1
    sha256:8c2021ba5cbbcc1cbb63ca5957baeba71cdedf6a987d5f7091f609858539b3e7

probe boundary
    conformance-probe-input-v0
    conformance-probe-result-v0
    conformance-probe-evidence-v0
    conformance-probe-procedure-v0
```

The retained prerequisite probe is deliberately `not-authorized` and
`not-run`. It is a contract fixture, not evidence that the backend proof ran.

The accepted production chain entering this task is:

```text
instrument r2
    -> Blend graph r1
    -> mixed Crossfader contract r1
    <- legacy implementation binding r1

build request r1
    -> Ksoloti Core target r1
    -> legacy Ksoloti backend r1
    -> unresolved toolchain/runtime identities r1
    -> unresolved eligibility r1
```

Task 007 deliberately requires compatibility evidence cited by a later binding
revision to name a strictly earlier binding revision. Therefore Task 009 has a
bootstrap problem: the exact revision-1 candidate must be tested before it can
be promoted, but normal production resolution must never select that candidate
while it remains uncertain.

Task 009 must solve that bootstrap explicitly through the conformance-probe
boundary below. It must not weaken `build.resolve`, treat a probe as a normal
build result, or manufacture circular evidence.

## Goal and why it exists

Prove, for one exact graph and one exact binding only, that Schuss can:

1. verify and consume the prerequisite's authenticated local Java, source,
   toolchain, and firmware/runtime ABI closure without substitution;
2. lower the accepted authoritative Blend graph deterministically to the
   smallest supported legacy `.axp` boundary;
3. retain a deterministic source map from Schuss graph identity to the legacy
   boundary and generated source;
4. invoke the pinned legacy Java path headlessly inside
   `legacy/ksoloti-bridge/`;
5. generate source and compile/link it with the exact ARM tools for the exact
   target/runtime closure;
6. record stage, diagnostic, artifact, resource, and evidence truth without
   overstating hardware or audible behavior;
7. promote compatibility only through new target, environment, backend,
   binding, eligibility, and request revisions supported by the probe evidence;
   and
8. rerun the ordinary Task 008 `build.resolve` operation successfully, pass its
   accepted `schuss-backend-invocation-input-v1` value to the new executable
   handler, and reproduce the proof through the production control-plane seam.

This task exists to prove the transitional compiler boundary before Schuss
attempts broader catalog support, a polished CLI, a direct C++ frontend, or
hardware execution.

## In scope

- Fail-closed preflight verification of every exact Java, source, classpath,
  GNU Arm Embedded, firmware, runtime, and ABI identity established by the
  prerequisite. Discovery may locate those exact bytes, but cannot substitute
  or silently refresh them.
- New revisions of existing build-environment records representing only exact
  identities actually used.
- The smallest truthful compute-target and backend revisions needed to point to
  those exact environment revisions, close the required ABI fact, and permit a
  `target-compile-link` stopping stage.
- Immutable probe input, result, and evidence records conforming to the
  prerequisite's accepted closed schemas and reference direction.
- One exact conformance probe of the revision-1 mixed Crossfader binding as
  `candidate-under-test`, outside normal production selection.
- One deterministic lowering implementation for the exact one-node mixed
  Crossfader graph slice only.
- Deterministic legacy `.axp` serialization as a generated boundary artifact,
  never as authoritative graph truth.
- A deterministic resolution plan and source map covering the exact graph,
  node, contract facets, binding, emitted legacy object identity, generated
  source regions, and structured diagnostics.
- A headless bridge implementation under `legacy/ksoloti-bridge/` that invokes
  only the exact pinned legacy Java behavior required for this proof.
- Deterministic generated C++, ARM object, linked target executable, and link
  map production if the exact local toolchain/runtime closure supports them.
- Static linker/resource observations derived from exact emitted artifacts and
  link outputs. These are not real-time measurements.
- Immutable artifact descriptors, build results, structured diagnostics,
  resource reports, and level-specific evidence claims for stages actually
  performed.
- A new implementation-binding revision retaining the exact public contract
  and realization meaning while establishing the required earlier-revision
  evidence boundary.
- A new binding-eligibility revision that cites probe evidence naming the
  strictly earlier binding revision and asserts only facts actually proved.
- A new compute-target revision asserting the two required fixed-Q27
  capabilities only if the exact pinned source/ABI/build evidence supports
  those claims under the accepted capability meanings.
- A new backend revision pointing to resolved environment identities and
  permitting the proved stopping stage.
- A new build-request revision for the same exact graph/instrument and the new
  target/backend closure, requesting no stage beyond the proof actually run.
- An executable handler behind the Task 008 backend-invocation data seam. It
  must consume the exact public seam value without a client-specific alternate
  request shape.
- Focused fixtures, failure injection, deterministic tests, documentation, and
  necessary status/index updates after the complete gate passes.

## Out of scope

- Connected-device execution, USB, upload, flash, SD-card writes, firmware
  installation, boot, runtime probing, or any physical hardware access.
- Real-time CPU, timing, memory, I/O, thermal, or stability measurement.
- Listening, audible-quality, or musical-quality claims.
- Firmware source modification, replacement firmware, bootloader work, or a
  new Ksoloti Core PCB/runtime.
- More than the exact one-node Blend/mixed-Crossfader graph slice.
- Support for arbitrary `.axp`, `.axo`, `.axs`, graph constructs, components,
  compounds, parameters, attributes, assets, MIDI, displays, actions, or I/O.
- A normalized compiler IR, optimizer, scheduler, general dependency planner,
  direct Schuss-to-C++ frontend, or multi-backend framework.
- Automatic binding fallback, unresolved selection, ambient object discovery,
  preference-dependent resolution, or filesystem/load-order precedence.
- A graph editor, catalog browser, GUI, AI prompting behavior, remote protocol,
  queue, cancellation system, progress protocol, or product CLI.
- Ergonomic Task 010 commands, formatting, flags, completion, progress UX, or
  installation packaging for `schuss`.
- Rewriting or deleting any Task 005-008 production record. Promotion is by new
  revision only.
- Treating a successful `.axp`, generated C++, object, or ELF as device,
  real-time, or audible evidence.
- Network downloads, package installation, upstream checkout mutation, source
  updates, or toolchain replacement without separate explicit approval.
- Staging, committing, tagging, pushing, publishing, uploading, or flashing
  without separate explicit approval.

## Inputs and frozen boundaries

Treat as immutable inputs:

- all accepted Phase 2, Phase 3, Phase 3 review, and Phase 4A artifacts;
- all Task 005-008 schemas and production semantic records;
- accepted record set `schuss-record-set-000001` revision 1 and its exact
  manifest/content hash;
- prospective prerequisite record set `schuss-record-set-000002` revision 1,
  its exact parent reference, and every listed prerequisite member;
- authenticated environment `schuss-prerequisite-environment-000001` revision
  1 and every exact retained capture artifact it names;
- the additive prerequisite repair evidence under
  `evidence/task-009-prerequisite-repair-v1/`, its exact repair-evidence
  manifest, and every content-addressed byte named by its retained-product
  manifest;
- the prerequisite probe, result, evidence, procedure, and record-set schemas;
- the Task 008 validator dependency direction and public operation envelopes;
- the Task 008 `records.validate`, `graph.inspect`, `build.resolve`, and
  `graph.transact` semantics;
- the production Blend graph revision 1;
- implementation binding `schuss-implementation-000028` revision 1;
- build request `schuss-build-request-000001` revision 1;
- the pinned source URLs/commits in `catalog/sources.lock.json`; and
- every accepted content hash and diagnostic code/order entering Task 009.

Before implementation, record SHA-256 baselines for:

- the complete Task 005-008 schema and production-record trees;
- the three compatibility-validator stdout byte streams;
- the Task 008 direct-API and CLI canonical result bytes for all four operation
  fixtures;
- the production build request and Blend graph files;
- the pinned source lock and relevant pinned source evidence; and
- the full 58-test Task 008 contract baseline.

All existing bytes must remain unchanged. New Task 009 records must live in a
dedicated prospective Task 009 contract directory and be admitted only by a
new exact successor record-set manifest whose parent is
`schuss-record-set-000002` revision 1. Do not place new files inside directories
whose exact membership is enforced by the accepted Task 005-008 manifest.

## Execution authorization and safety boundary

Creating this prompt performs no executable work. A later explicit instruction
to run Task 009 authorizes only these local actions after the preflight gate:

- execute the exact identified Java runtime against the isolated legacy bridge;
- write generated proof artifacts only beneath a dedicated Task 009 temporary
  or content-addressed output root;
- execute the exact identified GNU Arm Embedded compiler, assembler, linker,
  binary utilities, and size tools against generated proof inputs; and
- create the bounded Task 009 code, tests, probe records, new production record revisions,
  artifact descriptors, build result, resource report, and evidence claims.

It does not authorize network installation, upstream mutation, device access,
firmware action, staging, commit, or push. Print the resolved executable paths,
versions, and byte hashes during preflight, but never place absolute local paths
in durable records or canonical identities.

If an exact required Java, legacy, firmware/runtime, or ARM identity is absent,
ambiguous, incompatible, or cannot be pinned without a download or upstream
change, stop before tool execution and report the blocker. Do not substitute a
different tool or infer identity from a command name on `PATH`.

## Required bootstrap: conformance probe before promotion

Normal `build.resolve` must remain fail closed. Task 009 may not change the
production eligibility state or emit a normal build result that selects binding
revision 1 before evidence exists.

Implement this exact sequence:

1. Reproduce the current production `unresolved` trace and its four reasons.
2. Load `schuss-record-set-000002` revision 1 explicitly and verify every
   immutable revision-1 source, Java/classpath, ARM-tool, firmware/runtime,
   symbol, and manifest byte against `schuss-prerequisite-environment-000001`
   revision 1. Then verify every additive repair-evidence byte and all six
   retained content-addressed products before executing Ant, the legacy bridge,
   or an ARM tool. Use the repaired expanded-command manifest for command
   provenance; the preserved quiet-build artifact is historical evidence only.
   Stop on any missing, extra, ambiguous, or hash-mismatched member.
3. Re-run the prerequisite validator and confirm the retained probe fixture is
   still `not-authorized`, `not-run`, rejected by `build.resolve`, and grants no
   production selection authority.
4. Create the authorized immutable probe input/result records only through
   `conformance-probe-input-v0` and `conformance-probe-result-v0` in the new
   successor prospective record set. Do not modify those schemas or use
   `build-request-v0`/`build-result-v0` for the probe.
5. Run the probe against binding revision 1 using the same pure lowering and
   bridge/tool adapters intended for the production handler.
6. Record probe failures truthfully and stop promotion if any required stage
   fails, is unsupported, or remains unresolved.
7. If the evidence passes, create a `conformance-probe-evidence-v0` companion
   naming the exact immutable result, binding revision 1, and procedure. Create
   level-specific immutable evidence claims whose semantic-record input closure
   names that companion and binding revision 1. Results must not point back to
   evidence.
8. Create implementation-binding revision 2 with unchanged public contract and
   realization semantics. Do not add target/backend facts to the Task 006 seam
   map.
9. Create eligibility revision 2 referencing binding revision 2 and citing
   evidence that names strictly earlier binding revision 1.
10. Create only the supported target/environment/backend revisions justified by
    the evidence, then create the new exact build-request revision.
11. Run ordinary Task 008 `build.resolve`. It must select exactly one binding
    with no exclusion or unresolved reason and return the accepted backend
    invocation value.
12. Pass that exact value to the production backend handler and reproduce the
    deterministic stages through the requested stopping point.

The probe is an evidence-acquisition mechanism, not a hidden production build
path. The final production proof must enter through the Task 008 seam.

## Required environment identity closure

The accepted revision-1 environment remains authoritative for semantic
identity. The additive repair manifests are authoritative for executable
command provenance, Ant closure, bridge isolation, and retained source/class/
firmware products. Task 009 may record verified identities in new
build-environment revisions, but it must neither rebuild the identity contract
nor substitute any closure member. Machine-local paths are execution locators
only and are excluded from canonical records.

### Java and legacy bridge

Verify against the prerequisite capture, then report in evidence:

- exact Java executable version and byte hash;
- exact legacy class/source/application closure and pinned commit;
- exact classpath members and byte hashes;
- headless flags and working-directory contract;
- object search roots derived only from portable pinned source IDs;
- the exact ordered registry behavior used for the mixed Crossfader object;
- locale, encoding, and other inputs that can affect generated bytes; and
- proof that USB, upload, flash, GUI presentation, and mutable preferences are
  disabled or unreachable.

All direct Java-model coupling remains inside `legacy/ksoloti-bridge/`.

### ARM toolchain

Carry into a new build-environment revision only after exact preflight verifies:

- exact identity kind and version;
- exact hashes for every compiler/linker/binutils component actually invoked;
- target triple and exact target/ABI flags;
- a content-addressed portable locator, never a local absolute path;
- exact pinned source evidence supporting the compatibility boundary; and
- any deterministic-build flags required to remove timestamps, build IDs,
  random seeds, or local path leakage.

### Firmware/runtime ABI

Carry into a new build-environment revision only after exact preflight verifies:

- the exact runtime/firmware identity used for the link boundary;
- exact hashes of firmware artifact, import/export, header, linker-script, and
  library inputs actually required;
- the exact target triple and compatibility boundary;
- source evidence for the declared firmware/runtime version and ABI;
- the endianness evidence needed to close the target fact; and
- explicit limitations: link compatibility is not connected-device execution.

Do not call a source directory, version string, or successfully parsed header
an exact runtime artifact identity.

## Required lowering boundary

The lowering implementation consumes only the exact accepted closure:

```text
backend invocation input
    -> exact build request
    -> exact graph/instrument/target/backend
    -> exact selected binding and eligibility
    -> exact environment identities
```

It must:

- reject any missing, stale, extra, ambiguous, or hash-mismatched member;
- revalidate the Task 008 input envelope before execution;
- support only graph `schuss-graph-000001` at its accepted exact revision and
  the promoted binding revision created by this task;
- represent unsupported input with a structured diagnostic, not fallback;
- preserve ordered compiler stages and stop at the requested stage;
- keep lowering, serialization, Java generation, and ARM tools as distinct
  adapters with distinct stage outcomes;
- perform no implicit filesystem or object discovery;
- write only to a fresh explicit output root; and
- return immutable stage/output facts to the build-result recorder.

No backend adapter may import GUI or device-control code.

## Deterministic `.axp` boundary

Emit the smallest legacy patch that truthfully represents the one-node mixed
Crossfader graph and the exact public/control mapping needed for generation.

The serializer must define and test:

- XML declaration, encoding, newline, whitespace, attribute, and element order;
- stable legacy object identity and instance identity derived from controlled
  inputs, never random UUID generation;
- exact parameter/attribute/port mapping from the selected binding;
- explicit representation of graph public ports and the `blend` control seam;
- absence of hidden nodes, adapters, defaults, or object lookup fallback;
- a canonical artifact byte hash; and
- a source-map entry for every emitted semantic element.

The `.axp` is an artifact referenced by the build result. It is never written
back into the authoritative graph or treated as graph truth.

## Source-map and diagnostic contract

The source map must be a deterministic, versioned artifact that connects:

- build request and graph exact references;
- graph node ID and component-contract facets;
- selected binding and legacy observation/object identity;
- `.axp` element/attribute locations;
- Java resolution and generated-source identities;
- generated C++ byte or line regions where stable;
- ARM diagnostic subjects; and
- related structured diagnostic IDs.

Raw Java or compiler text may be retained as non-canonical evidence bytes, but
canonical diagnostics must use stable codes, stable subject references, stable
parameters, and deterministic ordering. Absolute paths, temporary directory
names, locale-specific prose, and unordered log lines never enter canonical
identity.

## Java bridge and ARM execution stages

The bridge must be callable headlessly through a documented machine interface.
It must accept the exact `.axp` and pinned registry/source configuration, then
emit deterministic resolution and generated-source outputs or a structured
failure. It must not access a device or silently consult user preferences.

The ARM adapter must consume only the recorded generated source and exact
runtime closure. It must capture:

- the canonical argument vector with portable locators;
- exit status for every invoked component;
- normalized structured diagnostics;
- generated object, ELF, link-map, and size/resource facts;
- exact byte hashes and lengths; and
- the first terminal failure, with all later stages `not-run`.

Successful compile/link establishes at most evidence level 5. Do not execute
the linked output.

## Production revision and promotion rules

- Retain every revision-1 record byte-identically.
- Use the existing stable entity IDs when revising the same semantic owner.
- New content hashes must cover the complete new record bytes.
- Binding revision 2 retains the exact Task 006 public contract/seam semantics;
  compatibility evidence remains owned by the eligibility layer.
- Eligibility revision 2 may assert `supported` only for the exact promoted
  target/backend pair and only with passing evidence that cites binding
  revision 1.
- Target capability declarations may become `supported` only if the evidence
  supports the full controlled meaning, including representation and declared
  scheduler lifetime. If compile/link evidence proves less, retain
  `unresolved` and report the proof gap.
- Toolchain and firmware/runtime environment revisions must name exact bytes,
  not merely versions or directories.
- Backend revision 2 points to the exact environment revisions and may permit
  only stopping stages the handler actually implements.
- Build-request revision 2 must retain the same authoritative graph and
  instrument references, name the promoted target/backend revisions, and
  request no stage beyond the proved handler.
- A normal build result may select only the evidence-supported promoted binding
  and eligibility revisions returned by ordinary `build.resolve`.
- Evidence points to immutable records/results/artifacts. Results never point
  back to evidence claims.

If these rules cannot be satisfied without an ownership or hash cycle, stop and
report the contract conflict. Do not weaken the validator.

## Required build result, artifacts, resources, and evidence

On a successful final run, create the smallest accepted production record set
covering:

- one build result for the promoted build request;
- stage outcomes for the complete fixed stage sequence, with stages after the
  requested stop marked `not-run`;
- structured deterministic diagnostics, including an empty collection when no
  diagnostic occurred;
- artifact descriptors for every retained resolution plan, `.axp`, source map,
  generated C++, ARM object, target executable, and link map actually emitted;
- a resource report derived from exact static compiler/linker facts if such
  facts are retained;
- level-specific evidence claims for each level actually established; and
- explicit limitations naming levels 6, 7, and 8 as not run.

Do not create descriptors for transient files that are not retained as
evidence. Do not call a static link map a level-7 real-time resource result.

## Failure behavior

Fail closed before invoking the next stage when any of these occurs:

- stale or missing exact reference;
- unresolved or ambiguous source/tool identity;
- source lock or byte-hash mismatch;
- unsupported graph, contract, binding, port, parameter, attribute, or legacy
  construct;
- non-selected production binding;
- conformance-probe input presented to the normal production handler;
- normal backend input presented to the probe without explicit probe state;
- Java lookup ambiguity, zombie, unresolved reference, GUI/device dependency,
  or unexpected preference use;
- nondeterministic `.axp`, source map, generated source, object, ELF, or link
  map bytes;
- compiler/linker error;
- local absolute path, timestamp, build ID, random identifier, or unstable log
  text entering canonical identity; or
- an attempt to continue after the first terminal stage outcome.

Failure must return no false successful result, no promoted eligibility record,
and no evidence claim above the exact level reached. Task-local failed outputs
may be retained only when explicitly referenced by a failed probe/result and
useful for deterministic diagnosis.

## Deliverables

- This approved Task 009 contract, updated to active only when execution begins
  and complete only after every acceptance test passes.
- Exact equality report proving every prerequisite environment/source identity
  and retained capture artifact matched before execution.
- An exact successor prospective record-set manifest whose parent is
  `schuss-record-set-000002` revision 1.
- Authorized probe input/result/evidence records conforming to the prerequisite
  schemas, with no probe-schema redesign.
- Pure exact-slice lowering, dependency/resource planning, `.axp`
  serialization, source-map, diagnostic, and build-result recording code.
- A headless isolated legacy bridge under `legacy/ksoloti-bridge/`.
- The executable backend handler consuming
  `schuss-backend-invocation-input-v1`.
- New environment, target, backend, binding, eligibility, and build-request
  revisions justified by evidence.
- Deterministic retained artifacts and their descriptors.
- One final immutable build result, applicable resource report, and
  level-specific evidence claims.
- Positive, negative, failure-injection, determinism, and preservation tests.
- Documentation of the exact supported subset, invocation boundary, evidence
  reached, limitations, and all deferred work.
- Necessary roadmap/status/index links only after the complete acceptance gate
  passes.

## Acceptance tests

Task 009 is accepted only if automated tests and recorded execution evidence
prove all of the following:

1. All 58 Task 005-008 contract tests, all 14 prerequisite contract tests, and
   every inventory/catalog test and validator still pass before counting Task
   009 tests.
2. Every Task 005-008 schema, production record, validator summary, canonical
   byte stream, content hash, diagnostic code/order, and operation fixture
   result remains unchanged.
3. Production preflight reproduces the original unresolved trace and never
   returns a backend invocation for revision-1 eligibility.
4. The conformance probe uses explicit `candidate-under-test` state, exact
   immutable inputs, and cannot be accepted as a normal build request/result or
   selected production binding.
5. Probe failure at lowering, Java generation, or ARM compile/link prevents all
   later stages, promotion records, and unsupported evidence claims.
6. Probe evidence names binding revision 1; promoted eligibility references
   binding revision 2; the strictly-earlier revision rule passes without a
   result/evidence ownership cycle.
7. Exact toolchain and firmware/runtime environment records include all invoked
   component hashes, portable locators, target triple, compatibility boundary,
   and pinned evidence; no durable absolute path is present.
8. The target's ABI and two fixed-Q27 capability assertions are supported by
   exact evidence or remain unresolved. No weaker fact is promoted to satisfy
   the resolver.
9. The handler rejects any stale, extra, missing, ambiguous, unsupported, or
   non-selected input before side effects.
10. The lowering slice accepts only the exact Blend/mixed-Crossfader closure and
    reports every other graph or binding as unsupported.
11. Two isolated fresh output roots given the same exact closure emit
    byte-identical resolution plan, `.axp`, source map, generated C++, ARM
    object, target executable, and link-map bytes for every artifact retained
    under the determinism contract.
12. Generated bytes contain no timestamps, random IDs, local absolute paths,
    temporary-root names, unstable build IDs, or locale-dependent identity.
13. The source map resolves every emitted graph/node/facet/legacy/generated
    source relationship required by the exact slice, and structured diagnostics
    point through it deterministically.
14. The Java bridge is headless, stays inside `legacy/ksoloti-bridge/`, uses
    only the exact pinned registry/source closure, and cannot access USB,
    upload, flash, or GUI presentation behavior.
15. The exact generated source compiles and links with the recorded ARM tools,
    or the task records a truthful failed/unresolved result and does not claim
    level 5.
16. Ordinary Task 008 `build.resolve` over the promoted revisions returns
    `success`, one selected binding, no exclusion/unresolved reason, and the
    exact accepted backend-invocation value.
17. The production handler consumes that exact value without a second
    client-specific request model and honors the requested stopping stage.
18. The final build result has the exact complete input closure, deterministic
    stage order, correct first-terminal behavior, exact selected binding and
    eligibility, exact artifacts/resources, and correct overall status.
19. Artifact descriptors keep descriptor identity separate from artifact-byte
    identity and use content-addressed portable locators.
20. Static resource facts are exact and correctly aligned/budgeted; no static
    observation is labeled real-time evidence.
21. Evidence levels 1-5 are separate and claim only the levels actually passed.
    Levels 6-8 remain `not-run`; no connected-device, real-time, or audible
    claim exists.
22. The authoritative graph remains byte-identical and contains no target,
    backend, implementation-binding, `.axp`, Java, or artifact identity.
23. Existing revision-1 environment, target, backend, binding, eligibility, and
    build-request records remain byte-identical. New revisions exist only in
    the explicitly selected prospective Task 009 record set.
24. Direct API and minimal Task 008 CLI inspection/validation/resolution remain
    byte-identical. Task 009 adds no Task 010 product CLI behavior.
25. Operations and handlers write only to explicit task output roots and do not
    mutate pinned upstream checkouts, user preferences, hardware, firmware, or
    unrelated workspace files.
26. `git diff --check` passes and the completion report names every generated
    record/artifact hash, tool identity, command boundary, evidence level, and
    remaining proof gap.

Run the complete repository validation and test suite, not only Task 009 tests.
Fresh-process and fresh-output-root determinism checks are mandatory.

## Decisions Task 009 may make

- Stable IDs and revisions for the authorized probe records that conform to the
  fixed prerequisite probe schemas.
- Exact filenames and package layout for the bounded lowering, bridge, handler,
  source-map, and build-recording implementation.
- The minimal legacy XML subset and exact deterministic serialization rules for
  the one supported graph.
- The exact machine interface used to call the bridge headlessly.
- Stable new diagnostic codes owned by lowering, serialization, bridge, and
  tool-execution stages.
- The smallest deterministic artifact storage layout and content-addressed
  portable locators.
- Which static resource observations are retained when supported by exact
  linker/tool output.
- Whether the requested final stopping stage is artifact generation or ARM
  compile/link if the exact environment cannot truthfully support the latter;
  the task must report the reduced proof and may not call a reduced result a
  complete level-5 success.

## Decisions Task 009 must not make

- Changes to catalog-family, component-contract, graph, device, or instrument
  semantics.
- Changes to the prerequisite record-set, environment, probe input/result,
  probe evidence, or probe procedure schemas and accepted fixtures.
- Selection through uncertainty, implicit fallback, ambient discovery, or
  preference/load-order authority.
- A general compiler IR, optimizer, scheduler, direct C++ backend, or broader
  legacy-object support.
- New firmware behavior, runtime architecture, hardware pinout, device protocol,
  or product deployment behavior.
- GUI, AI, remote-operation, or Task 010 CLI-product design.
- Evidence-level collapse or claims that compile/link implies device execution,
  real-time performance, or audible behavior.
- Ksoloti-only processor, ABI, toolchain, firmware, or backend identities as
  `const` values in reusable schemas. Exact production records may use
  controlled stable values and vocabulary references.
- A result/evidence cycle or compatibility promotion citing the same or a later
  binding revision.
- Mutation of accepted records, pinned sources, hardware, or firmware.
- Staging, committing, pushing, publishing, uploading, or flashing without
  separate explicit approval.

## Stop conditions

Stop and report rather than broadening the task if:

- any required prerequisite Java, legacy, toolchain, firmware/runtime, source,
  symbol, or manifest byte is absent or hash-mismatched;
- the accepted prerequisite probe contracts cannot be consumed without schema
  changes or an ownership cycle;
- the one-node graph requires an unsupported legacy construct or hidden adapter;
- deterministic artifact bytes cannot be achieved without changing the pinned
  legacy/toolchain inputs or weakening the backend determinism contract;
- the fixed-Q27 capability meanings cannot be supported without connected
  runtime evidence;
- Java generation requires GUI/device/preference behavior that cannot be
  isolated safely; or
- ARM compile/link requires firmware, linker, library, or ABI facts outside the
  exact approved closure.

Partial investigation evidence may be documented, but the task remains
incomplete and no production compatibility promotion occurs.

## Completion report requirements

On completion, update this status to complete and record:

- exact source, Java, legacy, ARM toolchain, and firmware/runtime identities;
- pre-task preservation hashes and post-task equality checks;
- pre-existing and final test counts;
- conformance-probe input, result, stage, and artifact hashes;
- the strictly-earlier binding-revision evidence chain;
- every new production record ID/revision/hash;
- the final successful or terminal `build.resolve` trace;
- the exact backend-invocation seam bytes received by the handler;
- deterministic `.axp`, source-map, generated-source, object, ELF, link-map,
  build-result, resource-report, and evidence hashes actually retained;
- exact commands or argument-vector records used at each executable stage, with
  local paths excluded from durable identities;
- separate evidence status for levels 1 through 8;
- explicit confirmation that no device, firmware, real-time, audible, Task 010,
  staging, commit, push, upload, or flash action occurred; and
- every remaining proof gap and the earliest later task that owns it.

## Completion report: 2026-08-15

The complete restart preflight passed. It reloaded accepted record set
`schuss-record-set-000001` r1
(`sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6`),
prerequisite set `schuss-record-set-000002` r1
(`sha256:6f2855c384ef8bab88991a6cabdd8416c7f3c59a010eed0c6cda1ac08651ecaf`),
and authenticated environment `schuss-prerequisite-environment-000001` r1
(`sha256:8c2021ba5cbbcc1cbb63ca5957baeba71cdedf6a987d5f7091f609858539b3e7`).
Every prerequisite and repair-evidence member and all six retained products
matched before execution. The frozen request-r1 `build.resolve` result remained
1,367 bytes with SHA-256
`643a063d1553ff000a4776fd2a4eb5b7d300c0ba34ccbb977f3babd78abf7de9`
and retained its four exact unresolved reasons.

The exact executable identities used were OpenJDK Java 21.0.7
(`b56748e35a76328d8a33e52d298930806484e39fa4a68a10d7a54debf51a9151`),
Javac 21.0.7
(`7937caa17b49a97957cb0d2cc9ff18d148f4a20f98e49c8278cdc45b43a67ba4`),
and GNU Arm Embedded 9-2020-q2-update. The ARM component hashes are retained
in `contracts/task009/arm-none-eabi-v0-r2.json`. The link boundary used firmware
bin `fd61a6a109a234d1c72e445a0542ab59c407a6896b9aafe2bfcbcadaf775e258`
and stripped firmware link ELF
`df65f2153eb999386cc1bc30b382cafeac63aea8495bf8cb4cdad1c01fca944b`.
The pinned patcher source is commit
`08d3e6e1e2b61230308c20a15ded58ffdaf4656c`; the pinned factory source is
commit `25d2615ed5233546d617017666a4ab1e60a8c506`.

The authorized immutable probe is `schuss-conformance-probe-000002` r1
(`sha256:33d569a221a35ce7ec5c38bcb112e4e43b695b8442658cfd210204c15214646d`).
Its result is `schuss-conformance-probe-result-000002` r1
(`sha256:24e7b5a7b7b0370f46f94dd5f69cbbada41a3acbf722a13cc0fbf7f7bf1edf19`)
and all three stages passed. Its evidence companion is
`schuss-conformance-probe-evidence-000002` r1
(`sha256:c7fdfb21a6cf6e6074d747aa2a2ce0c21c8600cfb5a3a5b09923e401d9bdfca6`).
The companion grants no production selection authority.

The strictly-earlier evidence chain is:

```text
binding schuss-implementation-000028 r1
  -> authorized probe evidence r1
  -> evidence claim schuss-evidence-claim-000001 r1
  -> binding schuss-implementation-000028 r2
  -> eligibility schuss-binding-eligibility-000001 r2
```

The promoted binding r2 hash is
`sha256:7afa2bd29077c10c2f9e9313d7d803c0092c6e059aee89f7f4de2b230ed688cf`;
the eligibility r2 hash is
`sha256:e42922685ad42b0fb10affd2aff1d9dfcafe728ebef4069cf25e2a64306091f1`.
The other promoted production records are toolchain environment r2
`sha256:d460d5414ec534c242f9b3146b1123cb04b35fcf9af9a02452c11ada84b97bff`,
runtime environment r2
`sha256:a656a898798cad529dfec7b02f0a881b61b93e150dd0788b7028ec8e5e4ce2df`,
compute target r2
`sha256:d8a9652bd079d0f2a8806cc4922f2a380c8092549f267047d5a4a0360b4a6753`,
backend r2
`sha256:5286059e0a36918c78fadc0f5613c332178ebbe3e5468b26e03053c6ab5a087d`,
and build request r2
`sha256:7093aa5ce9c1752360a05eec855331b0781ba8fc6c0969c45e3220d24e9ce1ae`.

Ordinary Task 008 `build.resolve` returned `success`. Its exact accepted
backend-invocation value was 3,257 bytes, SHA-256
`fd4e424ce62182829fa17e351bdda989df696c276789626b4222014a51c8abe4`,
and selected binding r2 with no exclusion or unresolved reason. The handler
received that value unchanged, rejected a stale request before creating an
output root, and stopped after the requested `target-compile-link` stage.

The final production artifact-byte identities are:

- resolution plan: 1,289 bytes,
  `4a1cf154ee864953658d42db8255be0662e3b0342c1b42791271dc8a8f448da4`;
- legacy `.axp` boundary: 1,461 bytes,
  `f9492e2e959e9f49f0f4c26136f4071e39e8cf17a7b0d231e9fb0f7be8c60f6f`;
- source map: 1,406 bytes,
  `c1f2d270df37ca016f360d441960c78653e9e39c1589be3f31412d9935d71ee0`;
- generated C++: 10,083 bytes,
  `3ae83bec33951e1c6a0ea760754f2c4cabb452ba8b1f318f8f33563f73b42e48`;
- stripped ARM object: 7,380 bytes,
  `cf8eb67a66dbc4938ea7f695298b92f7c3509dc86c1ad96e538b2abf46583d39`;
- stripped target ELF: 67,276 bytes,
  `767ebb35f0dc41e0565e4736bc3debb272b8951f27148f38510b6b5f4b77bdba`;
  and
- link map: 149,761 bytes,
  `d27603a4fa85425badbac601f4e3c22fc8618dc4dec1a756df593ccf2bc28da4`.

Two differently named fresh probe roots and two differently named production
handler roots produced identical bytes for all seven artifacts, identical
portable command vectors, identical bridge results, and identical static
resource facts. The portable command vectors, including headless Java flags,
exact Make invocation, deterministic relink, strip, `objdump`, and `size`
steps, are retained in `evidence/task-009-v1/probe-execution.json` and
`production-execution.json`; no local path participates in their identities.
Injected lowering, generation, and ARM failures each stopped all later stages.

The final build result is `schuss-build-result-000001` r1
(`sha256:17faf3eff20111ce6ee4e92d10290b1de1d11ccafb9faaf97579e55e22d79e18`).
Its static resource report is `schuss-resource-report-000001` r1
(`sha256:9293ed1485a193964c2d6e7c0af98cdf53885900b47ba157c67267b2e8c6797c`):
1,240 code bytes plus 40 read-only bytes fit the 45,056-byte SRAM1 region,
and 552 data bytes fit the 51,200-byte CCM region. These are compiler/link-map
observations, not real-time measurements.

Evidence claims `schuss-evidence-claim-000002` through `000006` separately
record levels 1 through 5 as passed. Levels 6 connected-device execution, 7
real-time resource validation, and 8 audible listening validation are
`not-run`. The exact target ELF was never executed.

The successor manifest is `schuss-record-set-000003` r1
(`sha256:2f3706b7ccf08b59356bbfcadbdb37d0437b01857a9c50ba6e5d84e24a9b95c0`).
It contains 55 records, including 32 dedicated Task 009 records and 14 artifact
descriptors. All accepted schemas, records, graph bytes, validator output
bytes, diagnostic order, and Task 008 operation bytes remained unchanged. The
exact post-task comparison is retained in
`evidence/task-009-v1/post-task-equality.json`.

Final automated results were 96 contract tests, 14 inventory tests, and 6
catalog tests, all passing. Every contract, inventory, catalog, prerequisite,
and Task 009 validator passed; `git diff --check` passed. The pre-Task-009
contract baseline was 80 tests. No network download, package installation,
upstream checkout mutation, device access, firmware installation, SD write,
upload, flash, stage, commit, or push was performed.

Remaining gaps belong to later tasks: general graph/backend support, Task 010
product CLI design, connected-device execution, real-time timing/CPU/resource
measurement, and audible validation. Compile/link success does not answer any
of those gaps.
