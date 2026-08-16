# Task 023: CLI v2 and application-surface consolidation

Status: accepted by the user and completed on 2026-08-16. Tasks 023A, 023B,
023C, and parent integration passed all sixteen acceptance tests. ADR 0014 and
the accepted application-spine plan remain the routing authorities.

## Goal and why it exists

Turn the already implemented headless capabilities into one coherent,
discoverable application surface before Schuss adds another client. The CLI
must present project, catalog, graph, instrument/Gills, compiler-planning, and
build capabilities consistently, while a client-neutral machine description
states what operations exist and which effects and prerequisites each one has.

This task exists because the current executable contains more functionality
than its accepted root help and completion surfaces disclose. Project commands
and build plan/execute are callable but deliberately hidden from the original
help and completion goldens, and `gills.inspect` has no ordinary product-CLI
route. Preserving that transitional arrangement would make future CLI, UI, and
AI clients discover different products.

Task 023 creates an explicit versioned successor. It does not reinterpret the
CLI as semantic authority: every exposed command remains an adapter over the
same client-neutral operation, project, compiler, or execution service.

## Dependencies and verified baseline

ADR 0014 and `docs/APPLICATION_SPINE_PLAN.md` authorize creation of this
contract and place Task 023 before Tasks 024-028 and the UI-architecture
milestone. Accepted Tasks 008, 010, 011A, 012A, 013, 014, 018, and 021 supply
the shared dispatcher, product CLI, catalog operations, durable project
service, compiler planning, exact build execution, and Gills inspection used
here. Task 022 is retained as a failed diagnostic result but is not a Task 023
dependency.

The verified pre-implementation baseline is:

- root help omits the callable `project` command;
- build help and ordinary completion expose only `build resolve`, while
  callable `build plan`, `build execute`, and their separate completion helper
  exist;
- `gills.inspect` is a shared v6 operation without an ordinary product command;
- non-project commands use several historical default record sets rather than
  one declared current application closure; and
- the full contract suite has one inherited Task 011A golden failure. Four
  catalog human/JSON digests differ at equal byte lengths because the exact
  input-closure hash changed from the retained historical value; help and
  completion digests still match.

Contract acceptance is required before any implementation file, schema,
record set, current golden, or runtime behavior may change.

## In scope after contract acceptance

- A client-neutral, schema-validated `application.describe` operation whose
  deterministic result inventories the supported application operations and
  their exact request/result versions, context requirements, effect classes,
  explicit-intent gates, and availability in the selected exact context.
- Additive operation-request/result successors for that operation, without
  rewriting operation v1-v6 bytes.
- Exact successor record set `schuss-record-set-000015@1`, parented by
  `schuss-record-set-000014@1`, adding only the schemas needed for this
  application surface and retaining every accepted parent member byte.
- One explicit CLI v2 surface that coherently exposes validation, application
  capabilities, catalog search/inspection, graph inspection/proposal,
  project init/inspect/validate/commit adapters, build resolve/plan/execute,
  Gills/instrument inspection, completion, and the canonical operation adapter.
- One authoritative Bash, Zsh, and Fish completion surface that mirrors the
  CLI v2 grammar, including project, build plan/execute, application, and
  Gills/instrument routes.
- A single documented non-project context rule: commands either use the exact
  Task 023 application record set by default or require an explicit exact
  record set. They may not silently select different legacy defaults by
  command family.
- Deterministic human rendering and unchanged canonical machine results for
  inherited operations.
- An explicit Task 023 successor golden set. The existing Task 011A golden
  fixture remains byte-identical as historical evidence and is not overwritten
  to conceal the inherited mismatch.
- A read-only smoke path that crosses application description, catalog,
  project inspect/validate, graph inspection, compiler planning, build
  capability inspection, and Gills/instrument inspection without executing a
  backend or writing a workspace.
- Focused positive, negative, compatibility, determinism, path/hash,
  governance, and full-suite validation.

## Out of scope

- New catalog families, classifications, implementation reviews, component
  contracts, implementation bindings, DSP operations, normalized semantics,
  graphs, instruments, mappings, or compiler lowering support.
- New project creation, editing, revision, history, revert, undo/redo, or
  persistence semantics. Task 023 may expose only the accepted Task 012A
  project behavior; Task 026 owns the complete authoring workflow.
- Application sessions, background jobs, progress streams, cancellation,
  recovery orchestration, or new diagnostic semantics; those belong to Task
  027.
- UI implementation, UI-owned state or semantics, a private UI transport, or
  revival of Task 012B. UI architecture remains a later unnumbered milestone.
- Build-handler, compiler, backend, firmware, device, panel, hardware,
  real-time, audible, safety, or release expansion.
- Treating the Task 022 diagnostic as a product command or advertising its
  failed level-6 result as an available product capability.
- Ambient record discovery, implicit latest revision, display-name selection,
  nearest-parent project discovery, handler fallback, or silent selection of a
  writable context.
- Device upload, reset, flash, SD-card write, persistent installation, staging,
  commit, push, tagging, or publication without separate approval.

## Inputs and deliverables

Inputs are ADR 0014; the accepted application-spine plan; the exact Task 022
parent record set `schuss-record-set-000014@1`; operation schemas and services
v1-v6; the Task 010/011A CLI fixtures; the Task 012A project fixture and
service; Tasks 013-016 compiler/build services; Task 018 `gills.inspect`; and
the retained Task 021 product closure.

Deliverables are this contract and its read-only validator; the three additive
schemas `application-capability-description-v0`, `operation-request-v7`, and
`operation-result-v7`; the client-neutral application-capability module and
operation; exact record set `schuss-record-set-000015@1`; the coherent CLI v2
help/completion and Gills/instrument adapter; Task 023 successor goldens;
read-only application-smoke fixtures and validator; focused regression tests;
and a completion report that states the exact evidence actually reached.

No new stable semantic ID is allocated by this task. The record-set identity
and schema versions above are reserved by the parent contract and may not be
reallocated by a child.

## Required application-capability contract

`application.describe` is a read-only shared operation, not a CLI-only help
projection. Its schema-validated result must, at minimum, describe each
accepted public operation using stable controlled fields for:

- operation name and request/result schema version;
- domain group and short client-neutral purpose;
- required exact context: record set, project workspace, execution service,
  and/or fresh output root;
- effect class: read-only, proposal-only, workspace-write, or build-output-
  write;
- required explicit intent or expected-reference gate;
- declared support versus availability in the selected exact context; and
- the evidence boundary, without turning availability into compile, device,
  real-time, audible, safety, or release proof.

The description must include at least `records.validate`, `catalog.search`,
`catalog.inspect`, `graph.inspect`, `graph.transact`, `project.init`,
`project.inspect`, `project.validate`, `project.graph.commit`, `build.resolve`,
`build.plan`, `build.execute`, `gills.inspect`, and `application.describe`.
Ordering is canonical and independent of registration order, process, CWD,
locale, timezone, terminal width, or environment noise. It contains no
absolute path, timestamp, host, user, temporary directory, or device probe.

The direct dispatcher fixture, CLI JSON adapter, and UI/AI-shaped test adapters
must receive byte-identical canonical results for the same exact request and
context. Human help and completion may project this registry, but neither may
add a capability absent from the shared description.

## Required CLI v2 surface

The Task 023 default root help must visibly include the coherent groups for
`validate`, `application`, `catalog`, `project`, `graph`, `build`,
Gills/instrument inspection, `completion`, and `op`. Build help must visibly
include `resolve`, `plan`, and `execute`; project help must visibly include all
accepted Task 012A routes. The exact public spelling of the Gills/instrument
group may be selected during implementation, but it must route to
`gills.inspect` and must not create a second inspection semantics.

Root completion for Bash, Zsh, and Fish must enumerate exactly the same command
and option grammar as help. The existing additive project/build completion
entry points may remain as compatibility helpers, but they are not the Task
023 authoritative surface and may not disagree with it.

Existing v1-v6 canonical operation request/result bytes remain immutable. CLI
v2 may intentionally change human help, human result presentation, and
completion bytes only through new named Task 023 goldens. Exact locators,
record-set membership, exit-code classes, safe text handling, broken-pipe and
interrupt containment, explicit project write intent, explicit build execution
intent, exact handler selection, and fresh-output-root rejection remain
fail-closed.

## Child work packages and ownership

The parent contract declares three exact children. None starts merely because
this file exists.

### Task 023A: shared application-capability operation

Goal: implement the schema-validated client-neutral capability description.

Owned write surface:

- `schemas/application-capability-description-v0.schema.json`;
- `schemas/operation-request-v7.schema.json`;
- `schemas/operation-result-v7.schema.json`;
- new `packages/schuss_core/application_capabilities.py`;
- the bounded v7 integration in `packages/schuss_core/control_plane.py` and
  exports in `packages/schuss_core/__init__.py`;
- `tools/contracts/tests/test_task023_application_capabilities.py`; and
- fixtures named `tools/contracts/tests/fixtures/task023-application-*`.

It owns no semantic stable IDs or record-set manifest. It must not edit CLI
grammar, historical goldens, project persistence, status, roadmap, indexes, or
publication. It contributes acceptance tests 2-5, 11, and 13-15.

### Task 023B: coherent CLI v2, help, and completion

Goal: expose the accepted operation surface coherently through the product
adapter and create explicit successor presentation goldens.

Owned write surface:

- `packages/schuss_core/cli.py` and
  `packages/schuss_core/product_cli.py`;
- `tools/contracts/tests/test_task023_cli_v2.py`;
- the bounded compatibility assertions in
  `tools/contracts/tests/test_task011a_catalog.py`;
- fixtures named `tools/contracts/tests/fixtures/task023-cli-v2-*`.

The historical fixture
`tools/contracts/tests/fixtures/task011a-cli-golden-hashes.json` is read-only.
Task 023B owns no schema, dispatcher, project-service, compiler, build-handler,
stable-ID, or record-set write. It contributes acceptance tests 1, 6-10, 12,
14, and 15.

### Task 023C: read-only application smoke and integration proof

Goal: prove the bounded application spine across existing services without
creating or mutating a project or executing a backend.

Owned write surface:

- `tools/contracts/validate_task023.py`;
- `tools/contracts/tests/test_task023_application_smoke.py`; and
- fixtures named `tools/contracts/tests/fixtures/task023-smoke-*`.

Task 023C starts only after 023A and 023B outputs are integrated. It may not
change implementation behavior, schemas, historical goldens, record sets,
status, roadmap, shared indexes, or publication. It contributes acceptance
tests 4, 5, 10-16.

### Parent integration ownership and order

The Task 023 parent integrator exclusively owns this contract, the Task 023
contract validator, `contracts/record-sets/task023-application-spine-v1.json`,
its deterministic generator/check path, current README/status/roadmap/task
indexes, governance summaries, aggregate validation, and any Git action.

After explicit contract acceptance, Tasks 023A and 023B may proceed as two
implementation lanes because their write surfaces are disjoint and the parent
has already fixed operation v7, the capability-description v0 schema, the
record-set identity, and the operation name `application.describe`. Shared
integration is serialized. Task 023C waits for both. A child completion does
not complete Task 023 or activate Task 024 or UI architecture.

## Acceptance tests

1. Every accepted v1-v6 operation schema, canonical request/result fixture,
   Task 011A historical golden fixture, Task 012A project behavior, compiler
   plan, build result, Gills record, Task 021 artifact, and Task 022 retained
   evidence byte remains unchanged.
2. The additive capability-description, request-v7, and result-v7 schemas pass
   deterministic schema/meta-schema validation and reject unknown operations,
   effect classes, context claims, extra properties, and non-portable values.
3. `application.describe` returns a schema-valid canonical inventory of all
   required operations, exact schema versions, contexts, effects, explicit
   gates, and selected-context availability without claiming semantic or
   evidence readiness it cannot prove.
4. Direct dispatcher, CLI JSON, UI-shaped, and AI-shaped adapters return
   byte-identical `application.describe` results for the same exact context.
5. Two fresh roots and processes with varied CWD, locale, timezone,
   `PYTHONHASHSEED`, terminal width, and harmless environment noise reproduce
   identical capability descriptions, CLI JSON, help, completion, and smoke
   results.
6. Root help visibly exposes application, catalog, project, graph, build,
   Gills/instrument, validation, completion, and canonical-operation routes;
   build help visibly exposes resolve, plan, and execute.
7. Bash, Zsh, and Fish authoritative completion enumerate the same root groups,
   child commands, and options as the CLI v2 grammar, with no hidden callable
   command and no advertised nonexistent command.
8. Every ordinary product command constructs and dispatches the accepted
   client-neutral request; no CLI branch reimplements catalog, graph, project,
   compiler, build, Gills, identity, or evidence semantics.
9. Exact ID@revision and content-hash selection remains fail-closed: implicit
   latest, display names, ambiguous membership, wrong kinds, unavailable
   contexts, ambient manifests, and handler fallback return stable errors.
10. The read-only smoke path succeeds across application description, catalog
    search/inspect, project inspect/validate, graph inspect, build plan,
    build-capability inspection, and Gills/instrument inspection, while a full
    before/after filesystem snapshot proves no workspace, output-root, source,
    record, cache, or hardware mutation.
11. Capability effects distinguish proposal-only `graph.transact`, persistent
    `project.graph.commit`, and output-writing `build.execute`; `build.execute`
    still requires explicit execution intent, one exact handler, and a fresh
    output root, while project writes retain exact expected-reference gates.
12. Task 023 successor human/JSON/help/completion goldens pass. The retained
    Task 011A golden stays byte-identical and the inherited four equal-length
    closure-hash digest differences are explained and tested rather than
    overwritten or treated as semantic catalog drift.
13. Unsupported schema versions, absent application schemas, malformed v7
    requests, unavailable project/execution contexts, and unknown operation
    registry entries fail closed with canonical diagnostics rather than an
    internal error or fallback.
14. Task 023 adds no catalog family, implementation, component, binding, DSP,
    graph, instrument, device, mapping, build-request, handler, artifact, or
    evidence record; record set `schuss-record-set-000015@1` is an exact
    parent-preserving schema/application-surface successor only.
15. Existing focused CLI, catalog, project, compiler, build, Gills, Task 021,
    Task 022, governance, inventory, and catalog suites pass, including the
    previously failing Task 011A test under its explicit historical/successor
    split.
16. The Task 023 contract validator, Task 023 focused validator, record-set
    freshness/path/hash checks, full contract suite, two fresh-root smoke runs,
    and `git diff --check` pass with zero unexplained failures.

## Decisions Task 023 may make

- The exact fields and controlled values inside the bounded capability
  description, provided the required ownership, context, effect, explicit-gate,
  availability, and evidence boundaries remain explicit.
- The exact public spelling and human presentation for the Gills/instrument
  CLI group, provided it dispatches the existing `gills.inspect` operation.
- The exact CLI v2 help wording, option ordering, successor golden shape, and
  treatment of older project/build completion helper commands.
- The smallest shared registry/refactor needed to prevent help, completion,
  and application description from drifting, without moving domain semantics
  into presentation code.
- The exact deterministic smoke fixture references drawn from accepted record
  sets and projects.

## Decisions Task 023 must not make

- Any catalog review/curation choice, compiler or DSP semantics, component or
  binding support, instrument behavior, mapping, project-write semantics,
  session/job behavior, UI design, device behavior, or evidence promotion.
- A new client-private operation, CLI-owned truth, UI-owned truth, or duplicate
  implementation of a shared operation.
- A claim that operation declaration or availability proves build success,
  connected-device execution, real-time safety, audible behavior, electrical
  safety, or release readiness.
- Mutation of accepted historical schemas, records, record sets, artifacts,
  evidence, machine request/result bytes, or the Task 011A historical golden.
- Implicit latest selection, ambient discovery, display-name identity,
  handler/backend fallback, writable nearest-project discovery, or device
  access.
- Activation of Task 024, Task 025, Task 026, Task 027, Task 028, UI
  architecture, or UI implementation.
- Staging, commit, push, tag, release, upload, reset, flash, SD-card write, or
  persistent installation.

## Readiness and activation state

This complete contract was explicitly accepted by the user and completed on
2026-08-16. Tasks 023A and 023B were integrated before Task 023C; the read-only
smoke and parent integration then passed all sixteen acceptance tests. No build
output, project write, device action, Git publication, or evidence promotion
occurred.

Task 023 completion does not activate Task 024, Task 025-028, UI architecture,
or UI implementation. Task 024 still requires its own complete accepted
contract. The already authorized unnumbered UI-architecture milestone is now
eligible to begin as a separate planning lane, but remains not started. Git
and hardware actions remain separately approval-gated.
