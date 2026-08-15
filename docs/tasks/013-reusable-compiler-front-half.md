# Task 013: Reusable compiler front half and deterministic planning artifacts

Status: complete on 2026-08-16; accepted locally through compiler stage 6.
The user authorized implementation by asking to run Task 013 on 2026-08-16.
No staging, commit, publication, push, compiler/toolchain invocation, or device
action was authorized or performed.

Work in the Schuss repository. Before implementation, read `AGENTS.md`,
`docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/SCHEMA_STRATEGY.md`, `docs/COMPILER_STRATEGY.md`,
`docs/TARGET_BACKEND_BUILD_CONTRACTS.md`, `docs/OPERATION_CONTRACTS.md`, ADRs
0005-0010, the completed Task 011C contract, the accepted Task 012A completion
report, and this complete task. Work only on Task 013.

## Goal and why it exists

Implement one reusable, backend-neutral compiler front half for exact Schuss
build requests through compiler stage 6:

```text
exact input closure
  -> schema and identity validation
  -> target-independent graph validation
  -> target/backend validation
  -> deterministic implementation resolution
  -> transparent compound elaboration
  -> dependency and resource planning
```

The task exists because Tasks 009 and 011C prove only bounded executable legacy
paths. Their handlers contain exact-slice orchestration and must not become the
general compiler by gradual special cases. Both the transitional legacy backend
and future direct frontend need the same deterministic plans, diagnostics, and
source trace before either performs lowering.

Task 013 stops before backend lowering. It strengthens the compiler backbone
without generating `.axp`, normalized DSP IR, C++, ARM artifacts, or runtime
evidence.

## Dependencies and accepted inputs

Task 013 may start only after Task 012A is accepted. Treat these as immutable
inputs:

- all accepted Tasks 001-012A schemas, records, fixtures, artifacts, evidence,
  operation results, CLI goldens, project fixtures, and completion reports;
- the authoritative compiler stages and ownership rules in
  `docs/COMPILER_STRATEGY.md` and `docs/SCHEMA_STRATEGY.md`;
- the accepted `records.validate`, `graph.inspect`, `build.resolve`,
  `graph.transact`, catalog, and Task 012A project operation semantics;
- Task 011C graph `schuss-graph-000002` revision 1, its exact eight-node
  selected binding closure, and its retained immutable planning/build/evidence
  artifacts as comparison evidence rather than files to rewrite;
- accepted transparent-compound contracts, graphs, mappings, and cycle rules;
- accepted target, backend, binding-eligibility, build-request, dependency,
  resource, artifact, diagnostic, and evidence vocabularies; and
- the isolated-legacy-bridge rule: core compiler packages may not import the
  Ksoloti Java model or bridge implementation.

Task 012A supplies a durable project loader, but project files do not become
compiler semantics. The compiler consumes an already validated exact request
and semantic closure and must also remain testable entirely in memory.

## In scope

### One common front-half API

- A headless compiler-front-half package with one public planning entry point
  over an exact validated build request and record closure.
- An immutable compilation context that records the exact request, graph,
  optional instrument, contracts, target, backend, bindings, eligibilities,
  dependencies, resources, assets, and policy versions used at each stage.
- Strict stage ordering and explicit stage results. A failed stage prevents all
  later stages and returns deterministic structured diagnostics.
- Reuse or extraction of accepted validator and resolver logic rather than
  copying domain rules into a compiler-specific implementation.
- No dependency from semantic models or shared validators upward into a
  backend, CLI, project filesystem adapter, or Java bridge.

### Stages 1-4: exact closure and binding resolution

- Exact schema, identity, hash, parentage, and reference validation for the
  selected build closure.
- Target-independent graph/type validation before any implementation choice.
- Explicit target/backend capability validation with controlled vocabulary.
- Deterministic node-to-binding candidate enumeration, exclusions,
  uncertainty, overrides, priority, and fail-closed ambiguity handling.
- Preservation of every accepted `build.resolve` result and diagnostic byte.
  The new compiler entry point may call or extract the same pure resolver; it
  may not create a competing selection algorithm.

### Stage 5: transparent compound elaboration

- Total public-facet mapping validation before expansion.
- Deterministic namespacing of derived internal instances and connections.
- Origin paths from every derived node/facet back to the authoritative outer
  graph node, selected binding, internal graph, and internal node/facet.
- Independent detection of recursive compound-definition expansion and legal
  signal-flow feedback.
- Preservation of hierarchy, state/lifecycle ownership, exposed facets, and
  diagnostic traceability.
- An inspectable elaborated-graph artifact that is explicitly derived and
  never accepted as an authoritative graph revision.

### Stage 6: dependency and resource planning

- Deterministic dependency closure over exact selected bindings, target,
  assets, and build options.
- Explicit version/hash conflict, missing dependency, ambiguous provider,
  exclusive-service, ordering, and portability diagnostics.
- Typed resource plans that distinguish declarations, unknowns, estimates,
  hard requirements, target regions, alignment, and budget decisions.
- Hard-budget failure where the accepted contracts provide enough facts;
  unknown facts required for safe planning remain unresolved rather than being
  guessed.
- No static-link measurement or runtime measurement may be relabeled as a
  planning estimate or vice versa.

### Deterministic planning artifacts and source maps

- Closed versioned schemas for the smallest truthful bundle of resolution,
  elaborated-graph, dependency, resource, and origin/source-map artifacts.
- Each artifact binds its exact producer stage/version, exact input-closure
  hash, media type, byte length, SHA-256, and portable locator.
- Stable ordering and canonical bytes across fresh roots, enumeration order,
  working directory, locale, and `PYTHONHASHSEED` variation.
- A deterministic top-level plan result whose status distinguishes success,
  unresolved, unsupported, invalid, ambiguous, budget failure, and not-run
  later stages without manufacturing a build result.

### Shared operation boundary

- An additive `build.plan`-equivalent operation submitted through the same
  control plane and canonical process adapter as existing operations.
- Exact build-request lookup only inside the selected validated record set or
  accepted Task 012A project context. No `latest`, ambient discovery, or
  filesystem-order selection.
- Existing operation envelope versions and current request/result bytes remain
  valid and unchanged.
- Task 013 may expose the new operation through `schuss op`; the ergonomic
  product `schuss build` execution/inspection surface belongs to Task 014.

### Fixtures and preservation

- Positive coverage for the exact Task 011C eight-node closure through stage 6.
- Positive transparent-compound coverage using accepted compound semantics.
- Focused fixtures for repeated contract/binding reuse, fanout, exposed graph
  parameters, state ownership, exact overrides, dependencies, resource
  regions, and hard budgets.
- Negative coverage for missing/stale closure members, type failure,
  unsupported backend/target pairs, zero candidates, ambiguous candidates,
  recursive compounds, incomplete/incompatible mappings, dependency conflict,
  unknown required resource facts, and hard-budget violations.
- Preservation checks for all accepted Task 009/011C handlers, artifacts,
  evidence, record sets, operation results, and CLI goldens.

## Out of scope

- Task 014 executable backend dispatch, handler registry, product build CLI,
  progress, cancellation, output-root publication, or build cache.
- Task 015 normalized DSP representation, scheduling IR, optimizer,
  graph-to-C++ frontend, Ksoloti runtime/ABI lowering, or direct backend.
- Task 016 full-slice direct compilation.
- Backend lowering of any kind, deterministic `.axp` generation, Java
  resolution/code generation, generated C++, ARM compiler/linker invocation,
  executable packaging, or new level-3-through-8 evidence.
- General scheduler, instruction-level IR, adapter insertion, implicit type or
  rate conversion, graph rewriting, or hidden optimization.
- Project persistence changes beyond consuming the accepted Task 012A service.
- Product-CLI grammar changes other than any minimal process-adapter support
  required to carry the additive operation envelope.
- Catalog expansion, new component semantics, new implementation support,
  binding/eligibility promotion, full Gills mapping, sampling/assets pipeline,
  additional targets/devices, UI, or AI/MCP.
- Network, USB, SD-card, upload, flash, firmware, connected execution,
  real-time measurement, or listening.
- Staging, commit, tagging, publication, or push without separate user
  authorization.

## Deliverables

- This task contract, updated to complete only after every acceptance gate
  passes.
- Normative compiler-front-half and planning-artifact documentation.
- Closed schemas for the accepted planning result/artifact bundle and additive
  operation envelope.
- A backend-neutral compiler-front-half package with the single public planning
  entry point.
- Additive shared control-plane support for the accepted planning operation.
- Positive, negative, preservation, determinism, and failure-stage fixtures.
- A read-only Task 013 validator and focused test suite.
- Necessary updates to active compiler, target/backend/build, operation,
  package, schema, project, and roadmap documentation.
- A completion report with exact stage outputs, schemas, hashes, diagnostics,
  preservation evidence, test counts, and remaining Tasks 014-016 gaps.

## Acceptance tests

Task 013 is accepted only if all of the following pass:

1. Every pre-existing test and validator passes before counting Task 013
   tests; accepted operation, CLI, Task 009, Task 011C, and Task 012A governed
   bytes remain unchanged.
2. The public compiler entry point accepts only an exact validated build
   request/record closure and returns explicit ordered stage outcomes.
3. Schema/identity or graph/type failure prevents target/backend validation and
   every later stage.
4. Target/backend failure prevents binding resolution and every later stage.
5. Binding resolution produces the same candidates, exclusions, uncertainty,
   selections, and diagnostic ordering as accepted `build.resolve` for every
   retained fixture.
6. Zero eligible candidates fail unsupported; unresolved evidence remains
   unresolved; equal-priority candidates fail ambiguous. No first-match,
   filesystem-order, display-name, family, or source-provenance selection is
   possible.
7. The exact Task 011C graph selects the same eight node/binding pairs,
   including reuse of the same Sine binding for two nodes, without invoking its
   backend handler.
8. Transparent compound elaboration preserves complete public mappings,
   deterministic derived identities, hierarchy, state/lifecycle ownership,
   and origin paths. Recursive definitions and incomplete or incompatible
   mappings fail before planning.
9. Dependency planning detects missing, ambiguous, version/hash-conflicting,
   cyclic where prohibited, exclusive, and nonportable requirements with
   stable subject references.
10. Resource planning keeps declarations, unknowns, estimates, requirements,
    regions, alignment, and budgets distinct. A required unknown or hard-budget
    violation fails closed.
11. Planning artifacts name exact input-closure and producer identities and are
    byte-identical across two fresh roots and all specified environment/order
    variations.
12. Every derived node, facet, dependency, resource subject, and diagnostic can
    trace back to its authoritative graph/contract/binding origin. A generated
    local path alone is never the only subject identity.
13. The elaborated graph and every plan are marked derived and cannot validate
    as an authoritative graph or silently enter a project as one.
14. The additive planning operation has byte-identical direct/process JSON
    results where specified, calls the compiler entry point once, and preserves
    all earlier operation envelopes and defaults.
15. A failed stage records all later stages `not-run`, creates no build result,
    executes no backend, and promotes no semantic or evidence record.
16. A successful Task 013 plan reaches at most evidence level 2. It creates no
    claim of backend lowering, source generation, ARM compile/link, device,
    real-time, or audible behavior.
17. Core compiler packages import no Ksoloti Java/bridge implementation,
    product CLI, UI, device transport, or task-specific executable handler.
18. No accepted graph, record set, project, binding, eligibility, build result,
    artifact, or evidence record is rewritten to make planning succeed.
19. `git diff --check` and the complete local ordinary-CI-equivalent gate pass.

## Decisions Task 013 may make

- Compiler-front-half package/module layout and its one public planning API.
- Exact closed schema names, derived artifact kinds, opaque IDs, filenames,
  portable locators, and canonical field layout for the planning bundle.
- Deterministic derived namespace/origin-path representation for compound
  expansion.
- The smallest explicit dependency ordering and resource-plan representation
  supported by accepted records.
- Exact additive operation version/name and stable diagnostic codes.
- Internal pure-data structures and algorithms, provided their serialized
  results and failure boundaries satisfy this contract.

## Decisions Task 013 must not make

- Authoritative graph rewrites, implicit adapter insertion, type weakening,
  inferred implementation support, first-match selection, or silent fallback.
- Normalized DSP instruction semantics, scheduler/optimizer policy, generated
  C++, runtime ABI lowering, executable backend behavior, output-root/cache
  policy, or product build-command UX.
- New component, instrument, device, target, backend, binding, eligibility, or
  compatibility truth merely to obtain a successful plan.
- A dependency from shared semantic validation into compiler, backend, CLI,
  project-filesystem, Java, UI, or hardware code.
- A claim that successful planning proves backend lowering, generation,
  compilation, connected-device execution, real-time behavior, or sound.
- Any mutation of accepted history or an action prohibited by workspace change
  controls.

## Stop conditions

Stop and report rather than broaden or weaken the task if accepted resolver
semantics cannot be reused without changing their results; if compound
elaboration requires an unowned graph/type decision; if dependency or resource
facts required for safe planning are absent; if plan identity would depend on
host paths or process state; if a direct or legacy backend must execute to make
the planning gate pass; if the operation boundary cannot remain additive; or
if completion requires Task 014/015 work, UI, hardware, staging, commit, or
push.

## Completion report requirements

On completion, record every delivered file; exact schemas, operation versions,
artifact kinds, IDs, revisions, and hashes; the public compiler API; ordered
stage outcomes; Task 011C selection comparison; compound expansion and source
map results; dependency/resource-plan facts; every negative/failure-stage
diagnostic; determinism and preservation evidence; pre-existing and final test
counts; evidence levels reached and not reached; scope confirmation; and the
exact remaining Task 014, Task 015, Task 016, Task 017, device, real-time,
audible, and UI proof gaps.

## Completion report

Task 013 is complete within its declared front-half boundary. It implements one
pure backend-neutral planning API, an additive operation, five derived artifact
kinds, exact stage/failure outcomes, transparent-compound elaboration,
dependency/resource planning, and retained read-only validation. It does not
implement or execute stages 7-10.

### Delivered files

The Task 013 implementation delivers these files:

- control plane and package:
  `packages/schuss_core/compiler_front_half.py`,
  `packages/schuss_core/control_plane.py`,
  `packages/schuss_core/project_service.py`,
  `packages/schuss_core/__init__.py`, and `packages/README.md`;
- exact record/evidence closure:
  `contracts/record-sets/task013-compiler-front-half-v1.json` and
  `evidence/task013-completion-v1/validation-summary.json`;
- schemas: `schemas/compiler-artifact-descriptor-v0.schema.json`,
  `schemas/compiler-dependency-facts-v0.schema.json`,
  `schemas/compiler-dependency-plan-v0.schema.json`,
  `schemas/compiler-elaborated-graph-v0.schema.json`,
  `schemas/compiler-origin-map-v0.schema.json`,
  `schemas/compiler-plan-result-v0.schema.json`,
  `schemas/compiler-resolution-plan-v0.schema.json`,
  `schemas/compiler-resource-plan-v0.schema.json`,
  `schemas/operation-request-v4.schema.json`,
  `schemas/operation-result-v4.schema.json`, and `schemas/README.md`;
- focused tooling: `tools/contracts/generate_task013_record_set.py`,
  `tools/contracts/validate_task013.py`,
  `tools/contracts/tests/test_task013_compiler_front_half.py`, and
  `tools/contracts/README.md`;
- normative/status documentation: `docs/COMPILER_FRONT_HALF.md`, this task
  file, `README.md`, `docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
  `docs/SCHEMA_STRATEGY.md`, `docs/COMPILER_STRATEGY.md`,
  `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`,
  `docs/OPERATION_CONTRACTS.md`, and `docs/ROADMAP.md`.

The generic `bin/schuss op` adapter already carries versioned operation
envelopes, so no product-CLI grammar or executable build command changed.

### Exact API, schemas, and closure

The public API is the immutable
`CompilationContext.from_values(...)` constructor plus the sole public
`plan_build(compilation_context)` planning entry point. The module accepts only
canonical in-memory exact references, records, schemas, closure source, and
policy versions. It imports the accepted shared validator/resolver modules and
no legacy bridge, Ksoloti Java model, executable handler, project filesystem
service, product CLI, UI, or device transport.

The additive operation is `build.plan` in request/result envelope v4. Direct,
process, and explicit Task 012A project contexts call `plan_build` once and
produce the same canonical plan semantics. Operation v1-v3 contracts and bytes
remain unchanged.

Record set `schuss-record-set-000007` revision 1 has content hash
`sha256:0b5b8567f6924e86dbe5f41569f55112999e9c140b5cf07069ecf64f3c419011`
and file-byte SHA-256
`8bd05860485932bade374cc5b989ea2eb4409989ab0549291b617427192d7efd`.
It binds exact parent `schuss-record-set-000006` revision 1 content hash
`sha256:fcf8f43d4139a16796b17bf2bdb95e5cd03ac279c60c55f8218349ef8a7cc842`,
retains all 144 parent record members byte-for-byte, and adds only ten schema
members for a total of 42 schemas. No compiler-dependency-facts production
record is admitted.

Exact new schema file hashes are:

| Schema | File-byte SHA-256 |
| --- | --- |
| `compiler-artifact-descriptor-v0` | `2aeb4973f4ae1f8e8f4d403a00e2287d2a42079e827707bca0db75bb63b90e8b` |
| `compiler-dependency-facts-v0` | `c653372de27e63a009f938fd09871bc9a3f47f0c5634df2dc707e42f31e5ac5d` |
| `compiler-dependency-plan-v0` | `d7a24d6b0a4460f8db1a19cd68ab370e4a7a880d54538f55271e11c292742854` |
| `compiler-elaborated-graph-v0` | `3ac20c71577b505ce39b801a866243335c7236ad8e0ec1d6b1c5c1c1acce3f03` |
| `compiler-origin-map-v0` | `74a76b3b05cda62f263bc116b7c541e4f1a2c18549ba2520b8f42b133420268a` |
| `compiler-plan-result-v0` | `51465ff3d5582bf56eae5fcbf507aa40fd575cceeb27103ef06b6eabf8062167` |
| `compiler-resolution-plan-v0` | `400d001b4a6346d921ad023b2b50b21bf2f0dd1165b14607b98b9265c1d20088` |
| `compiler-resource-plan-v0` | `323cc2395b7d6b37ed746f19d1881bf1177e9333e49c4859f246dccb4e18e2f4` |
| `operation-request-v4` | `4a5159895d4c07b85d7a9739729823be0a5845f1b364fef6ec0bc4f299719469` |
| `operation-result-v4` | `1ff814fe8f107f3295471f41791ae50af284882da16487f946cf27074451e99c` |

All are closed, annotated, portable, backend-neutral schemas. The dependency
facts schema is compiler-input planning data for focused fixtures, not new
component, binding, eligibility, target, backend, or catalog truth.

### Exact successful plan

The retained Task 011C build request produces input-closure hash
`sha256:2f951d56240d0bea533b47eb36973ec0d3c96510b94554e380f4c6f490c1becb`.
The closure description names 78 relevant record members, 34 exact schemas,
and all planner policy versions. Its canonical top-level plan is 95,210 bytes
with SHA-256
`d0fa1cc5375317cce3fec77fc91642d2ff28820897b1be2585b5c2e9ad1022b5`.
The six ordered outcomes are:

1. `schema-identity-validation`: `success`;
2. `target-independent-graph-validation`: `success`;
3. `target-backend-validation`: `success`;
4. `implementation-resolution`: `success`;
5. `compound-elaboration`: `success`;
6. `dependency-resource-planning`: `success`.

The exact artifacts are:

| Kind / ID | Producer | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `resolution-plan` / `schuss-compiler-artifact-f53bd96b3f26f210` | stage 4 v1 | 13,431 | `f53bd96b3f26f210fafda08ede956756f7afb0656ecdd64b019c0b76c34c36ab` |
| `elaborated-graph` / `schuss-compiler-artifact-a6c28e3b06a17906` | stage 5 v1 | 17,479 | `a6c28e3b06a179068ce3f83139ce0182da878755de52272883b35167c49d2009` |
| `dependency-plan` / `schuss-compiler-artifact-5adae32531fd1244` | stage 6 v1 | 406 | `5adae32531fd124487fbe6316f5fba1f00290115e58756c6d52a38f9bab78776` |
| `resource-plan` / `schuss-compiler-artifact-02588c060250c7da` | stage 6 v1 | 1,906 | `02588c060250c7da9dbdd1b641c22e2afe8cc5a400639250ae269273b5005320` |
| `origin-source-map` / `schuss-compiler-artifact-39886674b0658c3e` | stage 6 v1 | 38,821 | `39886674b0658c3e24f2e8a36d4c8dbbf90a39442fd6cdfa77c2d91a45880f93` |

Every descriptor repeats the exact input-closure hash, producer stage/version,
media type, canonical byte length, byte SHA-256, and a
`compiler-plans/sha256/<digest>.json` portable locator.

The resolution artifact is byte-for-byte equal in trace content and ordering
to accepted `build.resolve`. It selects these exact binding revisions:

- node `000001` -> implementation `000039` revision 2;
- node `000002` -> implementation `000040` revision 2;
- node `000003` -> implementation `000041` revision 2;
- nodes `000004` and `000005` -> the same Sine implementation `000007`
  revision 2;
- node `000006` -> implementation `000028` revision 2;
- node `000007` -> implementation `000015` revision 2; and
- node `000008` -> implementation `000004` revision 2.

The retained elaborated graph has eight derived nodes and nine connections,
preserves the exposed `blend` parameter and its remapped destination, state
ownership, and hierarchy, and is marked `derived: true` and
`authoritative: false`. Its origin map has 61 stable subject entries. The
transparent-compound fixture expands to namespaced derived node
`derived-node:graph-node-000001/graph-node-000001`, retains its compound
ancestor, and remaps public facets through total mapping keys.

The accepted Task 011C closure has no dependency or selected-binding resource
requirements. Its dependency plan therefore contains zero dependencies. Its
resource plan retains five target-region declarations and five within-budget
decisions, with zero requirements, unknowns, estimates, or measurements.
Focused fixtures separately prove topological provider-before-consumer order,
hard alignment/budget accounting, and repeated-binding requirements. An
unresolved eligibility resource fact remains unresolved at accepted binding
resolution stage 4; it is not guessed or relabeled as an estimate.

### Failure and determinism evidence

The focused matrix verifies deterministic structured failures for:

- stage 1: `COMPILER_SCHEMA_STRUCTURE_INVALID`,
  `COMPILER_CONTENT_HASH_MISMATCH`, `COMPILER_ID_REVISION_DUPLICATE`,
  `COMPILER_BUILD_REQUEST_REFERENCE_INVALID`, and
  `COMPILER_INPUT_NONPORTABLE`;
- stage 2: `GRAPH_CONNECTION_TYPE_INCOMPATIBLE`;
- stage 3: `BUILD_REQUEST_TARGET_BACKEND_PAIR_UNDECLARED`;
- stage 4: unsupported zero-candidate, unresolved eligibility/resource
  evidence, equal-priority ambiguity, and exact override behavior from the
  accepted resolver;
- stage 5: `COMPILER_COMPOUND_RECURSION`,
  `COMPILER_COMPOUND_MAPPING_INCOMPLETE`, and
  `COMPILER_COMPOUND_MAPPING_INCOMPATIBLE`; and
- stage 6: `COMPILER_DEPENDENCY_MISSING`,
  `COMPILER_DEPENDENCY_PROVIDER_AMBIGUOUS`,
  `COMPILER_DEPENDENCY_HASH_CONFLICT`,
  `COMPILER_DEPENDENCY_VERSION_HASH_CONFLICT`,
  `COMPILER_DEPENDENCY_CYCLE_PROHIBITED`,
  `COMPILER_DEPENDENCY_EXCLUSIVE_SERVICE_CONFLICT`, required resource
  hard-budget accounting, and `COMPILER_RESOURCE_HARD_BUDGET_EXCEEDED`.

Every failed stage marks all later stages `not-run`, creates no build result,
executes no backend, and promotes no record. Stage-6 diagnostics are themselves
present in the origin map. Enumeration shuffling and fresh processes with
different working inputs, `PYTHONHASHSEED`, and locale produce identical
canonical plan bytes. Direct/process operation results are byte-identical.

### Validation, preservation, and scope

The pre-Task-013 ordinary baseline was 197 passing tests: 14 inventory, 6
catalog, and 177 contract tests. The final ordinary gate is 221 passing tests:
14 inventory, 6 catalog, and 201 contract tests, including 24 focused Task 013
tests. `git diff --check` passes.

All read-only validators pass: component/graph, target/backend/build, Task 009
prerequisite, retained Task 009, Task 011B, Task 011C, Task 012A, the Task 013
record-set freshness check, and Task 013. The retained Task 013 summary exactly
matches live read-only validation. Task 013 record members equal parent `000006`
and every accepted Task 009/011C artifact, result, evidence member, operation
default, CLI golden, and Task 012A project byte remains unchanged. Pre-existing
unrelated and untracked workspace changes were preserved.

Evidence levels 1 and 2 pass. Levels 3-8 are `not-run`. Stages 7-10 are
`not-run`; `build_result_status` is `not-created`; backend execution is
`not-run`; authoritative records are not mutated. No Java, `.axp`, generated
C++, ARM compiler/linker, network, USB, SD-card, device, upload, flash,
real-time, listening, stage, commit, or push action occurred.

The remaining gaps are explicit. Task 014 owns executable handler dispatch,
progress/cancellation/output/cache policy, and the product build CLI. Task 015
owns normalized DSP representation, scheduling, and the first bounded direct
graph-to-C++ frontend. Task 016 owns direct compilation of the complete Task
011C graph. Task 017 owns reviewed-core expansion. Connected-device execution,
real-time validation, audible validation, full Gills implementation, and UI
remain separately unauthorized and unproved.
