# Task 007: Compute-target, backend-capability, build, artifact, and evidence contracts

Status: complete. Accepted as the target/backend/build-record contract gate;
no executable backend stage or higher evidence level was performed.

Work in the Schuss repository. Work only on Task 007.

This is a bounded schema-and-validation implementation task. It must define the
minimum durable compute-target, backend-capability, implementation-eligibility,
build, artifact, resource, diagnostic, and evidence contracts needed before a
Schuss compiler operation can exist. It must not lower a graph, invoke the
legacy bridge or a compiler, generate `.axp`, access hardware, or claim an
evidence level that was not actually performed.

Before changing anything, read completely:

- `AGENTS.md`;
- `README.md`;
- `docs/PROJECT_CONTEXT.md`;
- `docs/ARCHITECTURE.md`;
- `docs/SCHEMA_STRATEGY.md`;
- `docs/COMPILER_STRATEGY.md`;
- `docs/LEGACY_STRATEGY.md`;
- `docs/SEMANTIC_CATALOG.md`;
- `docs/PARAMETER_MODEL.md`;
- `docs/ROADMAP.md`;
- `docs/DEVICE_INSTRUMENT_CONTRACTS.md`;
- `docs/COMPONENT_GRAPH_CONTRACTS.md`;
- ADRs 0005, 0006, and 0007;
- Tasks 004, 005, and 006, including their completion evidence;
- every Task 005 and Task 006 schema, production record, validator, fixture,
  and test;
- `catalog/sources.lock.json` and the exact pinned `patcher` source commit;
- any existing portable target, toolchain, firmware, linker, and ABI evidence
  that can be resolved at that commit without mutating an upstream checkout;
  and
- any relevant ignored local source configuration, using it only to locate
  pinned read-only evidence and never copying absolute paths into durable
  records.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Context

Task 006 completed this exact semantic chain:

```text
instrument r2 -> exact DSP graph r1 -> exact mixed Crossfader contract r1
                                      <- exact legacy binding r1
```

The exact production graph is `schuss-graph-000001` revision 1. Its sole node
references `schuss-component-contract-000003` revision 1. The corresponding
legacy realization is `schuss-implementation-000028` revision 1. The Task 006
binding proves a structural seam map to frozen observation 460, but its
selection state is deliberately `not-evaluated`. It does not prove that the
binding is eligible for any target or backend, that a toolchain/runtime pair
is usable, that a build can be attempted, or that any compiler or hardware
evidence exists.

Task 004 fixed this one-way build/evidence direction:

```text
build request -> exact graph/instrument + compute target + backend
build result  -> exact request closure + selected bindings + tools + artifacts
evidence      -> exact result, stage, artifact, target, or device subject
```

The authoritative graph never acquires target/backend or binding identity.
Implementation selection happens only after target-independent graph
validation and explicit target/backend validation. Build records never rewrite
families, contracts, graph semantics, compatibility, or preference. Evidence
claims point to immutable results or artifacts; results never point back to
evidence claims.

Task 007 must make that contract machine-readable and testable. It must stop
before executable lowering or compilation.

## Goal and why it exists

Create deterministic, closed, versioned contracts that can answer, without
running a backend:

1. What exact compute target and runtime constraints were requested?
2. What exact backend contract is being asked to process the graph?
3. Which implementation bindings are structurally eligible, excluded, or
   ambiguous under an explicit versioned policy?
4. What exact inputs and requested stopping stage define a build request?
5. How will later tasks record stage outcomes, diagnostics, artifacts,
   resource observations, toolchain/runtime identity, and evidence without
   overstating what occurred?
6. How is the complete exact-reference closure kept acyclic and portable?

This gate exists so Task 009 cannot define build truth ad hoc around the first
successful `.axp`, Java invocation, or ARM link. Task 008 and Task 009 must be
able to consume one accepted record model rather than inventing incompatible
operation and result shapes.

## In scope

- A minimal shared, versioned capability vocabulary used by targets, backends,
  and binding eligibility records.
- A compute-target schema and the smallest truthful Ksoloti Core production
  target record supported by pinned evidence.
- A backend schema and the smallest truthful transitional `legacy-ksoloti`
  backend record. It may declare forms and stages the backend contract is
  intended to accept; that declaration is not evidence that lowering works.
- Exact toolchain and firmware/runtime ABI identity representation needed by a
  future build result. Production records are allowed only for identities and
  facts proved by pinned portable evidence; unresolved required identity must
  remain explicit and must block a build-ready claim.
- A representation for implementation-binding target/backend eligibility,
  capability/resource requirements, explicitly curated selection policy, and
  required evidence level.
- A deterministic read-only eligibility/resolution validator that can explain
  candidates, exclusions, ambiguity, and the effect of a narrowing override.
- Build-request, build-result, stage-outcome, structured-diagnostic, artifact,
  resource-report, and level-specific evidence-claim schemas.
- A minimal exact build-request production record for the Task 006 reference
  graph only if every required reference is truthfully available. The request
  may stop at validation or implementation resolution; it does not assert that
  an executable build was performed.
- Focused non-production result, artifact, resource, diagnostic, evidence, and
  revision-stratification fixtures sufficient to validate their full shapes.
- Canonical serialization, content hashes, exact-reference registries,
  deterministic diagnostics, and fresh-process determinism.
- Documentation of facts proved, unresolved facts, and all evidence levels
  explicitly not reached.
- Necessary status and index links only after all acceptance tests pass.

## Out of scope

- Shared mutation/build operation APIs, transaction semantics, queues,
  cancellation, progress events, or remote protocol transport; Task 008 owns
  them.
- Graph lowering, transparent-compound elaboration as executable compiler work,
  dependency planning as an executable compiler work, or generation of a
  resolution-plan artifact.
- `.axp` generation, legacy XML serialization, Java resolution/code generation,
  C++ generation, ARM compilation/linking, packaging, or deployment; Task 009
  owns the first executable legacy-backend proof.
- A direct Schuss graph-to-C++ frontend, scheduler, optimizer, or instruction
  representation.
- Device connection, USB, SD-card writes, firmware upload/flash, runtime
  probes, timing/resource measurement, or listening.
- GUI, CLI, object browser, graph canvas, or AI-client behavior.
- New graph nodes, component contracts, instruments, device facts, Phase 4B
  catalog families, or changes to the Task 006 Crossfader semantics.
- Claims that Ksoloti Core memory, CPU, I/O, firmware, ABI, or toolchain facts
  are known merely because a source tree contains a name or a legacy build once
  existed.
- Automatic fallback, ambient source discovery, load-order selection, or
  inferred preference.

## Inputs and frozen boundaries

Treat these as immutable Task 007 inputs:

- all accepted Phase 2, Phase 3, Phase 3 review, and Phase 4A artifacts;
- the Task 005 schemas and production revision-1 records;
- the Task 006 family companion, component contracts, implementation bindings,
  graph, and instrument revision 2;
- all accepted Task 006 record content hashes and exact reference tuples; and
- the pinned upstream URLs/commits in `catalog/sources.lock.json`.

Do not rewrite Task 006 binding revision 1 to insert target/backend claims.
Choose one truthful migration shape:

1. create a new implementation-binding schema/version and new binding
   revisions retaining the same implementation IDs; or
2. create a separate exact binding-eligibility/constraint companion owned by
   the target/backend layer.

Document the choice. It must preserve the Task 006 bytes and avoid duplicating
or redefining the public contract seam map. A later compatibility promotion
that cites build evidence must always be a new semantic-record revision.

Before implementation, record pre-task SHA-256 baselines for:

- every Task 005 and Task 006 schema and production record;
- the frozen 27-file Phase 2/3/review aggregate;
- the Phase 4A family/implementation ID projection and raw overlay bytes; and
- the pinned source lock.

Acceptance must prove those baselines unchanged unless this task explicitly
creates a new revision beside an old record.

## Required record architecture

Exact filenames and the smallest sensible number of schemas are Task 007
implementation decisions, but the following ownership must remain distinct.
Combining closely related value shapes is allowed; collapsing semantic owners
is not.

### Shared capability vocabulary

Capabilities must use one versioned vocabulary rather than unrelated strings
inside targets, backends, and bindings. The bounded production vocabulary must
contain only capabilities required to express the Task 006 Crossfader slice
and the transitional legacy-backend boundary.

Each capability definition must state:

- a stable category-independent key;
- its owner and meaning;
- the subject kinds that may declare or require it;
- its value shape, unit, and comparison rule if it is not boolean;
- whether unknown or not-evaluated blocks eligibility; and
- the evidence level required before `supported` may be asserted.

Do not create a universal hardware ontology. A capability key must not encode a
target name, backend name, repository path, or mutable label. `supported`,
`unsupported`, `unresolved`, and `not-evaluated` are distinct closed states.
Absence is not support.

### Compute target

A compute-target record owns:

- opaque target ID, positive revision, schema version, and content hash;
- stable target kind and processor/architecture identity;
- ABI constraints and runtime assumptions;
- named memory regions, alignments, hard budgets, and explicit unknown facts;
- firmware/runtime interface identity or a blocking unresolved state;
- asset/storage limits relevant to build planning;
- supported capability declarations under the shared vocabulary;
- portable evidence references for every production fact; and
- explicit questions, owners, and earliest tasks for unresolved required facts.

The first target is Ksoloti Core, not Gills. Gills remains a device profile and
instrument platform. Do not copy panel controls or musical behavior into the
target record.

The validator must distinguish a source-declared maximum, a linker-region
budget, an estimate, and a runtime measurement. Only the first two may be
target constraints here; estimates and measurements belong in resource
reports. A production number without exact evidence fails closed.

### Backend capability contract

A backend record owns:

- opaque backend ID, revision, schema version, and content hash;
- lowering identity and contract version;
- accepted authoritative input schemas;
- supported implementation realization forms;
- required target capabilities and explicitly supported target pairing;
- ordered stage contract and permitted stopping stages;
- emitted artifact kinds and media types as declarations;
- determinism guarantees and diagnostic/source-map obligations; and
- exact toolchain/runtime requirements or explicit unresolved references.

The transitional backend is `legacy-ksoloti`. It may declare that its contract
uses the isolated bridge and is intended to emit a legacy boundary artifact in
a later task. It must not claim that `.axp` generation, Java resolution, C++
generation, ARM linking, or device execution has passed.

Do not add a production direct-C++ backend merely to exercise the schema.

### Binding eligibility and selection

Target/backend eligibility supplements one exact implementation binding. It
must not alter or repeat public facets. It must represent:

- the exact binding ID/revision/hash it constrains;
- exact allowed backend and target references or predicates over the shared
  vocabulary;
- required capability values and evidence levels;
- realization-form support;
- portable dependency requirements;
- typed hard resource requirements needed for eligibility;
- supported, unsupported, unresolved, and not-evaluated constraint states;
- an explicit versioned selection policy or exact priority declaration; and
- evidence references supporting each positive compatibility assertion.

The pure resolver order is fixed:

1. accept only bindings for the node's exact component-contract tuple;
2. check backend realization-form support;
3. check the exact backend/target pair;
4. evaluate every capability, dependency, resource, and evidence requirement;
5. apply a valid request override only as a narrowing exclusion; and
6. apply one explicit total selection policy.

Zero eligible candidates is `unsupported`. More than one equally ranked
candidate is `ambiguous`. Unknown facts required for eligibility are
`unresolved`. The resolver must never select the first candidate by file,
array, Java load, source, family, display-name, or registry order.

The Task 006 one-node graph should resolve to the mixed Crossfader binding only
if the new production target/backend/eligibility records actually prove all
required predicates. Otherwise the truthful production result is unresolved,
and the positive selected case remains a focused fixture.

### Toolchain and firmware/runtime ABI identity

A future successful build result must reference exact toolchain and runtime ABI
identity. The Task 007 shape must support:

- opaque ID, revision, schema version, and content hash;
- toolchain kind, version, executable/component hashes, and target triple where
  applicable;
- firmware/runtime ABI identity, version/hash, and compatibility boundary;
- portable locators/evidence, never an absolute installed path; and
- explicit unresolved identity when the pinned evidence cannot prove a fact.

Whether toolchain and runtime ABI are separate record families or two closed
variants of one environment schema is a Task 007 decision. Build results must
not encode ambient `PATH`, process environment, user preferences, or a mutable
application installation as identity.

### Build request

A build request must bind:

- opaque request ID, revision, schema version, and content hash;
- exact graph ID/revision/hash;
- optional exact instrument ID/revision/hash;
- exact compute-target ID/revision/hash;
- exact backend ID/revision/hash;
- normalized versioned build options;
- exact resource/asset references;
- optional exact implementation-binding overrides; and
- requested stopping stage or evidence-producing action.

If an instrument is present, its exact graph reference must equal the exact
graph in the request. An override may only remove otherwise eligible
candidates or select one from an already eligible set. It cannot make an
incompatible binding eligible, weaken a capability/resource rule, or skip an
evidence requirement.

The request contains no result, selected binding, diagnostics, output paths,
timestamps, or mutable execution state.

### Build result and stage outcomes

A build result must be immutable and bind:

- its exact request;
- the resolved exact semantic and build-environment closure;
- every authoritative node/compound instance and its exact selected binding;
- exact target, backend, toolchain, and firmware/runtime ABI records;
- normalized options actually used;
- one outcome for every declared compiler stage;
- stable structured diagnostics;
- exact artifact and resource-report references;
- deterministic overall status; and
- enough trace information for later level-specific evidence claims.

Closed result and stage statuses must distinguish at least `success`, `failed`,
`unsupported`, `unresolved`, and `not-run`. Stages after a stopping point or a
prior failure remain explicitly `not-run`; they are not omitted or inferred as
success. A schema/fixture result may describe a non-executing validation or
resolution outcome, but no production result may claim an operation that Task
007 did not perform.

The result must not contain a rewritten authoritative graph. Derived
resolution, elaboration, dependency, resource, lowering, source-map, or
normalized-graph data is an artifact reference, not semantic graph state.

### Structured diagnostics

A diagnostic must have stable code, severity, stage, parameters, and exact
subject references. Where applicable it must identify:

- build request and graph;
- authoritative node and local facet;
- compound path;
- contract and binding;
- target and backend;
- capability, dependency, resource, toolchain, ABI, or artifact; and
- related diagnostic IDs without creating a cycle.

Human prose is a rendering. Canonical diagnostic identity cannot depend on
wall-clock time, host path, compiler temp filename, process ID, unordered log
text, or random UUID.

### Artifact descriptor

Every artifact descriptor must declare:

- opaque artifact ID, revision, schema version, and content hash;
- artifact kind and media type;
- exact byte length and SHA-256 of the described bytes;
- producer stage and producer contract/tool version;
- exact input-closure hash;
- portable content-addressed locator; and
- optional source-map/parent-artifact references with acyclic ownership.

Artifact descriptor `content_hash` and artifact-byte SHA-256 are different
facts and must not be conflated. Fixtures must prove both. No artifact bytes
need be generated in Task 007.

An artifact must not reference the build result that references it. This keeps
the exact closure acyclic. The result owns the reference to the independently
content-addressed artifact descriptor.

### Resource report

Resource records must distinguish:

- hard declared requirement;
- static estimate;
- compiler/link-map observation;
- connected-runtime measurement; and
- unresolved or not-evaluated fact.

They must retain named memory region, alignment, code/data/stack/heap/asset
kind, unit, method, subject, and evidence level. A total byte figure cannot
erase region or alignment. Static link size cannot become CPU headroom. An
estimate cannot become a measurement. Hard-budget comparison must be exact and
must fail closed if a required target budget is unresolved.

Task 007 uses fixtures for measured observations. It performs no measurement.

### Evidence claim

Use exactly the eight independent levels accepted by
`docs/COMPILER_STRATEGY.md`:

1. structural/schema validation;
2. component and graph resolution;
3. backend lowering;
4. source/artifact generation;
5. ARM compilation and linking;
6. connected-device execution;
7. real-time/resource validation; and
8. audible/listening validation.

One evidence claim owns one bounded observation. It must identify its exact
subject, level, method, outcome, evidence inputs, limitations, and producer
identity. It may reference an immutable result, stage, artifact, target, or
device as permitted by the level. It must never imply another level.

`not-run` is the absence of a performed evidence claim plus an explicit status
in a derived view or build stage; do not create a passing evidence record for
not running something. A level-5 link claim does not imply levels 3, 4, 6, 7,
or 8. A level-8 listening claim does not imply deterministic source or link
success.

No result may reference evidence claims that reference that result. Evidence
is downstream. A binding may cite build evidence only in a new revision whose
cited closure ends at a strictly earlier binding revision. Current- or
later-revision self-support must fail.

## Canonical identity and portability

Reuse `schuss-canonical-json-v1` only if every new schema explicitly declares
set versus sequence arrays and the existing implementation can canonicalize
the full shape without ambiguity. Otherwise version the canonical profile and
provide deterministic migration tests. Never silently reinterpret Task 005 or
Task 006 canonical bytes.

Every durable record must:

- use an opaque stable ID independent of names, paths, categories, tools, and
  labels;
- use a positive entity revision and verified content hash;
- use exact ID/revision/hash references;
- use restricted JSON numbers and exact decimal strings where required;
- close unknown fields and controlled vocabularies;
- use repository-relative or content-addressed portable locators only;
- omit timestamps, host paths, temp paths, process IDs, random identifiers,
  ambient environment, and unordered log content from canonical identity; and
- preserve explicit unresolved/not-evaluated states rather than guessing.

Generated test summaries and canonical record emission must be byte-identical
across fresh processes.

## Required deliverables

- Closed JSON schemas for the record owners above, using the smallest coherent
  grouping that preserves their distinctions.
- Minimal production shared capability, Ksoloti Core target,
  `legacy-ksoloti` backend, exact toolchain/runtime identity or blocking
  unresolved records, and binding-eligibility/selection records justified by
  pinned evidence.
- An exact Task 006 reference-graph build request only if its closure is
  truthful and build-request-valid.
- No production build result, artifact, resource measurement, or higher-level
  evidence claim unless Task 007 actually performs the claimed action—which it
  is not authorized to do.
- Focused positive fixtures for every schema and all pure validation/selection
  rules.
- Focused negative fixtures covering every fail-closed boundary below.
- A read-only aggregate validator/resolver extending the Task 006 validator
  through explicit target/backend/build registries.
- Deterministic canonical-record emission and structured summary output.
- A normative `docs/TARGET_BACKEND_BUILD_CONTRACTS.md` documenting ownership,
  capabilities, selection, build/result/artifact/resource/evidence shapes,
  facts proved, and deferrals.
- Necessary README, architecture, schema-strategy, roadmap, schema, contract,
  and tool index updates only after acceptance passes.
- A completion report in this task file with exact IDs, revisions, hashes,
  evidence sources, diagnostics, tests, frozen baselines, and next-task scope.

## Validator requirements

The validator must be read only and fail closed. It must validate:

- schema versions, canonical profiles, opaque IDs, revisions, hashes, and
  ID/revision uniqueness;
- exact reference closure across Task 005, Task 006, and Task 007 records;
- capability keys, value kinds, comparison rules, declaration/requirement
  subject kinds, and evidence thresholds;
- compute-target facts, memory regions, budgets, ABI/runtime closure, and
  evidence/unresolved status;
- backend input schema, realization form, target-pair, stage, artifact-kind,
  toolchain/runtime, and capability declarations;
- binding exact-contract continuity without public facet redefinition;
- eligibility candidate/exclusion reasoning, overrides, deterministic priority,
  zero-candidate and tie failures;
- build-request graph/instrument equality, options, assets, overrides, target,
  backend, and stopping stage;
- result request/input closure, node-to-binding totality, exact environment,
  ordered stage outcomes, diagnostics, artifacts, resources, and status;
- diagnostic subject validity and stable ordering;
- artifact descriptor hash/byte-hash separation, kind/media type, byte length,
  stage, input closure, source maps, and portable locators;
- resource observation kind, unit, region, alignment, method, evidence level,
  and exact hard-budget comparison;
- evidence claim subject/level/method/outcome/limitations and prohibition of
  cross-level implication;
- result/evidence direction and the strictly-earlier binding-revision evidence
  rule;
- absence of reference cycles, unknown fields, absolute paths, timestamps,
  random IDs, mutable-label IDs, ambient environment, implicit discovery, and
  presentation state; and
- deterministic diagnostics, canonical bytes, and aggregate summaries.

The validator must not invoke Java, a compiler, linker, generator, backend,
device, preference system, upload/flash path, or external mutation. It must not
write caches or generated records as a validation side effect.

## Required fixtures and negative tests

At minimum, tests must cover:

1. The complete valid production closure from exact graph/instrument through
   target, backend, capability vocabulary, environment identity, eligibility,
   and any production build request.
2. Two fresh-process validations and canonical emissions are byte-identical.
3. All Task 005/006 bytes and hashes remain unchanged.
4. Set reordering is canonical-byte invariant; ordered stage and policy
   sequence reordering changes bytes or fails as declared.
5. Stable ID/revision collision, stale nested hash, wrong revision, ambiguous
   exact reference, and missing registry member fail.
6. Unknown capability, wrong value type/unit, unsupported declaration subject,
   missing required evidence, and unresolved eligibility-critical capability
   fail.
7. Target facts without exact evidence, duplicate memory regions, invalid
   region bounds/alignment, negative budgets, and guessed ABI/runtime identity
   fail.
8. Backend with unknown input schema, unsupported realization form, undeclared
   artifact kind, invalid stage ordering, false target pairing, or premature
   lowering/generation claim fails.
9. Eligibility with wrong contract/binding, target/backend mismatch, incomplete
   requirements, unsupported form, insufficient evidence, unresolved required
   resource, or public-facet redefinition fails.
10. A unique eligible candidate passes; zero candidates, unresolved facts, and
    equal-priority candidates produce distinct deterministic failures.
11. An exact valid override narrows candidates; an override naming an
    ineligible binding or weakening a requirement fails.
12. A build request with stale graph/instrument/target/backend, instrument graph
    mismatch, unknown option, unresolved asset, invalid override, or invalid
    stopping stage fails.
13. A result with missing/duplicate node selection, ineligible selected
    binding, wrong environment, changed options, invalid stage transition,
    success after failed prerequisite, or omitted later `not-run` stages fails.
14. Diagnostics with unknown subjects, random IDs, unstable order, wall-clock
    identity, host/temp paths, or unstructured compiler text as sole identity
    fail.
15. Artifact descriptor content-hash/byte-hash confusion, invalid SHA, wrong
    byte length, unknown kind/media type, missing input closure, absolute path,
    timestamp, or result/artifact reference cycle fails.
16. Exact hard-budget pass/equality/overflow cases; cross-region aggregation,
    alignment loss, estimate-as-measurement, link-size-as-runtime-headroom, and
    unresolved required budget fail.
17. One fixture for each of the eight evidence levels validates only its own
    bounded claim. Table-driven cross-level implication attempts all fail.
18. Result-to-evidence back-reference, evidence with stale result/stage/artifact
    subject, and binding evidence citation through its current or a later
    revision fail; a strictly earlier revision fixture passes.
19. A build result cannot mutate or embed an authoritative graph, catalog
    family, component public signature, device profile, instrument behavior,
    selection preference, or compatibility claim.
20. Absolute checkout/install/temp paths, timestamps, random IDs, mutable names
    in stable IDs, unknown fields, unknown controlled values, implicit source
    discovery, and presentation state all fail closed.

## Acceptance criteria

1. All inventory, review, semantic-catalog, Task 005, and Task 006 tests and
   validators pass.
2. Frozen Phase 2, Phase 3, review, Phase 4A, Task 005, and Task 006 bytes and
   identity projections remain unchanged.
3. Every new schema is closed, versioned, deterministic, and limited to its
   stated owner.
4. Every production record has an opaque ID, positive revision, verified hash,
   portable evidence, and exact references.
5. The bounded capability vocabulary is shared and contains no speculative
   universal target/backend ontology.
6. The Ksoloti Core target contains only pinned evidence-backed facts and
   explicit unresolved states; it is not confused with Gills.
7. The transitional backend contract declares accepted forms, stages,
   artifacts, and target requirements without claiming a stage was executed.
8. Task 006 binding revision-1 bytes remain unchanged. Any new eligibility or
   binding revision preserves its exact contract and seam map and adds no
   public facet semantics.
9. Eligibility and selection are exact, deterministic, evidence-aware, and
   fail closed on no candidate, ambiguity, and unresolved required facts.
10. Request overrides only narrow already eligible candidates.
11. A build request binds the exact graph/instrument/target/backend closure and
    rejects instrument/graph mismatch.
12. Build-result fixtures bind exact input closure, total node selections,
    tools/ABI, options, stages, diagnostics, artifacts, and resources without
    embedding or rewriting semantic inputs.
13. Stage outcomes distinguish success, failed, unsupported, unresolved, and
    not-run, with valid prerequisite ordering.
14. Artifact descriptors are independently content-addressed and portable;
    no artifact bytes are generated as Task 007 evidence.
15. Resource requirements, estimates, static observations, runtime
    measurements, regions, alignments, and hard budgets remain distinct.
16. All eight evidence levels are representable and independently validated;
    no claim or derived view implies an unperformed level.
17. Result/evidence direction and strictly-earlier binding-revision evidence
    stratification keep the exact closure acyclic.
18. Validators are read only and emit deterministic canonical bytes,
    diagnostics, candidate/exclusion traces, and summaries across fresh
    processes.
19. Positive and negative fixtures exercise every stated boundary and
    prohibition.
20. Documentation identifies Task 007 as complete only after every acceptance
    gate passes and names the exact separate scopes of Tasks 008 and 009.
21. No Java, `.axp`, compiler, linker, generated artifact, device, upload,
    flash, GUI/CLI, operation layer, firmware, hardware, stage, commit, or push
    action occurs without separate explicit approval.
22. Every unresolved target, backend, toolchain, ABI, resource, or evidence
    question has a named owner and earliest later task.

## Decisions this task may make

- Exact v0 schema filenames and portable record organization.
- Opaque IDs and revisions for target/backend/build-domain records.
- The minimal shared capability keys required by this slice.
- Whether binding eligibility is a new binding revision/schema or a separate
  exact companion, subject to the frozen Task 006 and ownership rules.
- Whether toolchain and runtime ABI use separate record families or closed
  variants of one environment schema.
- Whether diagnostics and stage outcomes are embedded closed values or exact
  referenced records, provided identity and cycles remain deterministic.
- The smallest truthful production request stopping point.
- Exact deterministic diagnostic codes, exclusion reasons, stage status, and
  summary shape.
- Additional focused fixtures needed to prove a stated boundary.

## Decisions this task must not make

- Compiler operation, transaction, cancellation, or client protocol semantics
  owned by Task 008.
- Legacy `.axp` subset, serialization, Java bridge invocation, dependency
  planner implementation, actual lowering, source maps, tool execution, ARM
  build, packaging, or executable artifacts owned by Task 009.
- Direct frontend IR, scheduling, optimization, or C++ lowering.
- New component contracts, graph rewrites, adapters, device mappings, Gills
  hardware facts, or Phase 4B catalog expansion.
- Compatibility or preferred-binding promotion as a side effect of validation
  or a fixture result.
- Target support inferred from source location, legacy name, family, form,
  observation presence, load order, or common historical use.
- Higher evidence inferred from structural validation, a declared backend
  capability, a static resource plan, or another evidence level.
- GUI/CLI behavior, firmware behavior, upload/flash, SD-card, USB, or hardware
  access.

## Sequencing and parallel-work boundary

Task 008 may consume the accepted Task 007 schemas to define shared headless
operations only after this gate completes. Task 009 may implement one minimal
legacy-backend path only after both the Task 007 record contract and the Task
008 operation boundary are accepted.

Read-only evidence gathering may inspect the exact pinned Ksoloti checkout for
target, linker, toolchain, firmware, and ABI facts. It must not mutate that
checkout, invoke its tools, update caches/preferences, assign unsupported
production claims, or be treated as compiler evidence.

Do not implement Tasks 008 or 009 in parallel merely to make Task 007 fixtures
look realistic. Fixtures describe closed future record shapes; they are not
permission to execute the stages they model.

## Required completion report

When finished, report:

- files added or changed;
- final schema IDs/versions and production record IDs/revisions/hashes;
- the shared capability vocabulary and why every production key is required;
- exact Ksoloti Core facts, evidence, unresolved fields, and owners;
- exact transitional backend declarations and explicit non-claims;
- the binding-eligibility migration choice and proof Task 006 bytes remained
  unchanged;
- deterministic candidate, exclusion, ambiguity, and override behavior;
- build-request closure and stopping-stage choice;
- build-result, diagnostic, artifact, resource, toolchain/ABI, and evidence
  shapes proved only through fixtures;
- exact-reference and cycle rules, including evidence revision stratification;
- positive and negative fixtures and structured diagnostic codes;
- tests and validators run, including fresh-process determinism;
- confirmation that all frozen evidence, Phase 4A IDs, and Task 005/006 bytes
  remained unchanged;
- evidence levels reached and every level explicitly not reached;
- deliberately deferred questions with owners; and
- the recommended exact, separate scopes of Tasks 008 and 009.

Do not claim completion merely because schema files exist. Check every
acceptance criterion and record concrete evidence in this task file. Do not
stage, commit, push, invoke Java, generate `.axp`, run a compiler/linker, access
hardware, upload, or flash without separate explicit approval.

## Completion evidence

Task 007 is complete within its schema, production-record, pure-resolution,
fixture, validation, and documentation boundary.

### Final record model and production closure

The accepted closed v0 schema families are:

- `capability-vocabulary-v0`;
- `build-environment-v0`;
- `compute-target-v0`;
- `backend-v0`;
- `binding-eligibility-v0`;
- `build-request-v0`;
- `build-result-v0`;
- `artifact-descriptor-v0`;
- `resource-report-v0`; and
- `evidence-claim-v0`.

Reusable record-family schemas do not const-lock Ksoloti processor, ABI target
triple, toolchain, firmware/runtime, backend, or bridge identities. Those are
controlled stable values; tests validate an alternate processor, environment
identity, and backend identity against the same schemas. The production
records remain Ksoloti-specific:

| Record | Revision | Content hash |
| --- | ---: | --- |
| `schuss-capability-vocabulary-000001` | 1 | `sha256:37770109d3aff88a67ab031a6ee21c49eb4d301e2933c4659efd38c4496cca92` |
| `schuss-build-environment-000001` | 1 | `sha256:b8f87da1147faceb472e464fce0a36e3379b100993540946249d69b7aabf97fc` |
| `schuss-build-environment-000002` | 1 | `sha256:4475da81044f40c37e95cd01dcd0a17e3d612c664cc5baa904e0bf1e58e8ae47` |
| `schuss-compute-target-000001` | 1 | `sha256:c1fa5a49ab9474068c70ffc03f5bbfc216936d1fcfa1514e257ec7d5361c866d` |
| `schuss-backend-000001` | 1 | `sha256:5070f9e9c667d6f16fb5b0022f045a1990243c2acbedf4585e8f41420e7c3178` |
| `schuss-binding-eligibility-000001` | 1 | `sha256:7dbfa34a34042af730166e2f1581e2a04b18b9e19a4975234c1b7397bae484f8` |
| `schuss-build-request-000001` | 1 | `sha256:0ba7e74977ac7ebcf50cb73826c349040d998541f688bb32cbedf88140259e95` |

The shared capability vocabulary contains only
`audio-stream-fixed-q27` and `control-stream-fixed-q27`, the two stream forms
required by the exact mixed Crossfader contract and legacy seam map.

Pinned patcher commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`
supports the production STM32F427/Cortex-M4/Thumb/FPv4-SP-D16,
`arm-none-eabi` hard-float, 48 kHz, 16-frame, and five linker-region
declarations. Nine unique portable source references resolve and their bytes
verify against the configured read-only checkout. They prove source/linker
declarations only.

Endianness, exact installed toolchain identity, exact firmware/runtime ABI,
usable asset capacity, stream capability support, target/backend binding
compatibility, and hard binding resources remain unresolved with named owners
and earliest Task 009 questions. The backend declares its intended forms,
ten-stage contract, artifact/media declarations including source maps,
diagnostic/determinism obligations, and isolated bridge. It claims no stage
execution.

### Eligibility, request, and fixture-only future shapes

Eligibility is a separate exact companion. Task 006 implementation binding
`schuss-implementation-000028` revision 1 and its public seam map remain
byte-identical. The pure resolver applies exact contract, supported form,
target/backend pair, capability/dependency/resource/evidence, narrowing
override, then explicit priority. It reports selected, unsupported,
unresolved, ambiguous, and invalid-override distinctly and never selects by
file or load order.

The production request pins graph `schuss-graph-000001` revision 1,
instrument `schuss-instrument-000001` revision 2, the production target and
backend, deterministic options, no assets or override, and the
`implementation-resolution` stopping stage. Its one candidate is unresolved
for these deterministic reasons:

- `BINDING_TARGET_BACKEND_PAIR_NOT_EVALUATED`;
- `CAPABILITY_UNRESOLVED:audio-stream-fixed-q27`;
- `CAPABILITY_UNRESOLVED:control-stream-fixed-q27`; and
- `COMPATIBILITY_EVIDENCE_MISSING`.

No production build result, artifact descriptor, resource report, or evidence
claim was created. Non-production fixtures validate complete future result,
structured-diagnostic, artifact, resource, and all eight evidence-level
shapes. They cover descriptor/byte-hash separation, exact artifact bytes in a
fixture-only checker, same-region aligned budget pass/equality/overflow,
acyclic artifact and diagnostic references, exact total node selection,
stage prerequisites and later `not-run`, result-to-evidence direction,
cross-level rejection, and strictly-earlier binding revision stratification.
Results cannot embed or rewrite authoritative semantic records because the
closed result schema permits exact references and derived outputs only.

### Acceptance runs

The following completed successfully after the final changes:

- `python3 -m unittest discover -s tools/inventory/tests`: 14 tests passed;
- raw inventory validation: 4,209 files and two retained issues, valid;
- resolved inventory validation: 3,602 objects, 1,157 graphs, and 3,180
  retained issues, valid;
- Phase 3 review validation: valid;
- Phase 4A semantic catalog validation: 26 families and 38 implementations,
  valid;
- Task 005 focused validator: valid with the historical deferred graph;
- Task 006 aggregate validator: valid with the historical deferred instrument;
- Task 007 aggregate validator: valid, no diagnostics, nine source references
  locally verified, one unresolved resolver outcome;
- `python3 -m unittest discover -s tools/contracts/tests`: 42 tests passed;
  and
- `git diff --check`: clean.

The Task 007 tests compare every Task 005/006 schema and production record in
scope, the exact graph/bindings, the source lock, and the Phase 4A overlay
directly to `HEAD`; all bytes remain identical. Fresh-process aggregate
summaries and canonical-record emissions are byte-identical. Set reordering is
canonical-byte invariant and compiler-stage sequence reordering changes bytes
and fails semantic validation.

Evidence level 1 (structural/schema) and level 2 (component/graph resolution)
pass. Level 3 backend lowering, level 4 source/artifact generation, level 5 ARM
compile/link, level 6 connected-device execution, level 7 real-time/resource
validation, and level 8 audible/listening validation are all `not-run`.

### Next separate scopes

Task 008 must begin with a bounded validator-core consolidation. Extract the
canonical JSON, schema traversal, portability, structured diagnostic, and
exact-reference primitives from the current acyclic import chain
Task 007 -> Task 006 -> Task 005. Preserve all record bytes and validation
behavior, add no upward/circular imports, then define the shared typed
headless operation layer. This prerequisite is documented rather than
implemented here because consolidation is outside Task 007.

Task 009 remains a separate executable-backend task: resolve the remaining
toolchain/runtime/ABI and capability facts, implement one minimal deterministic
legacy `.axp` boundary plus source map, invoke the isolated legacy bridge and
ARM compiler/linker only under its own approval, and record only the evidence
levels actually reached.

No Java, `.axp`, generator, compiler, linker, device, upload, flash, firmware,
stage, commit, or push action occurred in Task 007.
