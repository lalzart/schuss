# Task 013A: Reusable compiler front half and deterministic planning artifacts

Status: proposed prompt; not started. The user authorized creation of this task
contract on 2026-08-15 but did not authorize implementation, staging, commit,
publication, push, compiler/toolchain invocation, or device action.

Work in the Schuss repository. Before implementation, read `AGENTS.md`,
`docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/SCHEMA_STRATEGY.md`, `docs/COMPILER_STRATEGY.md`,
`docs/TARGET_BACKEND_BUILD_CONTRACTS.md`, `docs/OPERATION_CONTRACTS.md`, ADRs
0005-0008, the completed Task 011C contract, the accepted Task 012A completion
report, and this complete task. Work only on Task 013A.

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

Task 013A stops before backend lowering. It strengthens the compiler backbone
without generating `.axp`, normalized DSP IR, C++, ARM artifacts, or runtime
evidence.

## Dependencies and accepted inputs

Task 013A may start only after Task 012A is accepted. Treat these as immutable
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
- Task 013A may expose the new operation through `schuss op`; the ergonomic
  product `schuss build` execution/inspection surface belongs to Task 013B.

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

- Task 013B executable backend dispatch, handler registry, product build CLI,
  progress, cancellation, output-root publication, or build cache.
- Task 013C normalized DSP representation, scheduling IR, optimizer,
  graph-to-C++ frontend, Ksoloti runtime/ABI lowering, or direct backend.
- Task 013D full-slice direct compilation.
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
- A read-only Task 013A validator and focused test suite.
- Necessary updates to active compiler, target/backend/build, operation,
  package, schema, project, and roadmap documentation.
- A completion report with exact stage outputs, schemas, hashes, diagnostics,
  preservation evidence, test counts, and remaining Task 013B-013D gaps.

## Acceptance tests

Task 013A is accepted only if all of the following pass:

1. Every pre-existing test and validator passes before counting Task 013A
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
16. A successful Task 013A plan reaches at most evidence level 2. It creates no
    claim of backend lowering, source generation, ARM compile/link, device,
    real-time, or audible behavior.
17. Core compiler packages import no Ksoloti Java/bridge implementation,
    product CLI, UI, device transport, or task-specific executable handler.
18. No accepted graph, record set, project, binding, eligibility, build result,
    artifact, or evidence record is rewritten to make planning succeed.
19. `git diff --check` and the complete local ordinary-CI-equivalent gate pass.

## Decisions Task 013A may make

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

## Decisions Task 013A must not make

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
if completion requires Task 013B/013C work, UI, hardware, staging, commit, or
push.

## Completion report requirements

On completion, record every delivered file; exact schemas, operation versions,
artifact kinds, IDs, revisions, and hashes; the public compiler API; ordered
stage outcomes; Task 011C selection comparison; compound expansion and source
map results; dependency/resource-plan facts; every negative/failure-stage
diagnostic; determinism and preservation evidence; pre-existing and final test
counts; evidence levels reached and not reached; scope confirmation; and the
exact remaining Task 013B, Task 013C, Task 013D, device, real-time, audible, and
UI proof gaps.
