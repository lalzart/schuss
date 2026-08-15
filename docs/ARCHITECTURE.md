# Architecture

## Dependency direction

Schuss owns semantic models. Backends and applications depend on those models;
the models do not depend on Java, Swing, legacy XML, or a particular board.

```text
GUI / CLI / AI clients
          |
    graph operations
          v
instrument -> device profile
instrument -> DSP graph -> component contract -> catalog family
                          ^
                          |
              implementation binding -> legacy/source evidence

build request -> graph/instrument + compute target + backend
build result  -> request + selected bindings + artifacts
evidence      -> build result / stage / artifact

legacy backend -> .axp -> Ksoloti Java resolver/codegen -> ARM compiler
```

The initial backend passes through the Ksoloti Java resolver and existing ARM
compiler. Later backends may lower the same semantic graph without that bridge.

Exact ownership and permitted references are normative in
`docs/SCHEMA_STRATEGY.md`. Compiler stages and derived artifacts are normative
in `docs/COMPILER_STRATEGY.md`.

## Layer contracts

### Catalog family

A family owns musician-facing discovery, documentation, aliases, and canonical
drawer placement. It does not own a complete node signature, target/backend
choice, or source path and is never directly compiled. Several distinct
component contracts may reference one family.

### Component contract

A component contract is the target-independent nominal public type of a graph
node. It owns exact typed ports, runtime parameters, build-time attributes,
actions, displays, lifecycle/state requirements, capabilities, and compound
public mapping declarations. A graph pins an exact contract ID, revision, and
content hash.

### Implementation binding

An implementation binding realizes one exact contract revision as a legacy
definition, generated object, transparent graph, native implementation, or
target service. It owns dependencies, resources, backend/target constraints,
facet realization mappings, evidence, and only explicitly curated priority.
It cannot alter the contract it realizes. Selection happens after
target-independent graph validation and explicit target/backend validation.

### Compute target

A compute target declares execution constraints: processor family, available
memory regions, audio block/runtime assumptions, supported toolchain, and
backend capabilities. It does not define panel controls or an instrument's
musical behavior.

`ksoloti-core` is the first target. A successful ARM link is target-build
evidence, not proof of real-time headroom, physical I/O, or sound quality.
Task 007 keeps processor, ABI, environment, and backend identity fields
reusable; only its production records select Ksoloti values. Exact source and
linker declarations coexist with explicit unresolved runtime/build facts.

### Device profile

A device profile declares physical controls, outputs, display capabilities,
I/O, and gestures. It provides stable hardware-facing slots that an instrument
may map, without embedding DSP implementation.

Gills is the first device profile. Its existing panel contracts can inform this
layer, but importing them is separate from the legacy inventory task.

Task 005's production v0 contract declares only the reference knob needed by
the `blend` slice and leaves unsupported physical range/resolution facts
explicitly unresolved. See `docs/DEVICE_INSTRUMENT_CONTRACTS.md`.

### Instrument

An instrument owns musical identity, public parameters, actions, state,
performance mappings, and presentation. It references a device profile and a
DSP graph but remains distinguishable from both. Multiple device mappings may
eventually present one instrument, and multiple targets may execute it.

The Task 005 instrument revision 1 retains its closed deferred graph-reference
branch without a fabricated content hash. Task 006 instrument revision 2 uses
the same `instrument-v0` schema to reference the authoritative graph by exact
ID, revision, and content hash. Resolution passes only through the accepted
graph registry and exact public target kind/domain checks.

### DSP graph

The graph owns nodes, typed ports, connections, parameter bindings, attributes,
and compound structure. Compound nodes never make their internal graph
uninspectable. Editor coordinates and visual grouping are optional presentation
data, not node identity.

Every node references an exact component-contract revision. A graph never uses
a family, category, display name, implementation binding, legacy observation,
legacy path, or `.axp` as node identity.

### Backend

A backend resolves eligible implementation bindings for a compute target,
checks target capabilities and resources, lowers the graph, and emits build
diagnostics and artifacts. It must not mutate the authoritative graph to hide
ambiguity.

Task 007's transitional backend is a declarative contract. Its ordered stages,
artifact kinds, and Ksoloti bridge boundary are not claims that lowering or
generation occurred. The production resolver stops unresolved before any
executable stage. See `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`.

### Build request, result, and evidence

A build request pins graph/instrument, target, backend, options, and resources.
A result records selected bindings, toolchain/runtime ABI, stage outcomes,
artifact hashes, and diagnostics. Separate evidence claims reference immutable
results, stages, and artifacts; results do not point back to those claims.
Build records do not feed back automatically into families, contract semantics,
implementation priority, or compatibility curation.

## Catalog architecture

The catalog separates identity and behavior from navigation:

- stable object identity is category-independent;
- functional classification is curated and revisable;
- abstraction level, provenance, license evidence, target compatibility, and
  implementation form are facets;
- duplicates and overloads remain visible until an explicit resolution rule
  selects among them; and
- raw source observations and Java-resolved observations remain traceable.

The inventory pipeline is deliberately staged:

1. lock portable source identities and exact commits;
2. record physical candidate files and byte hashes;
3. export Java-resolved object variants, generated objects, compound graphs,
   ports, parameters, attributes, displays, dependencies, and diagnostics;
4. curate function and preferred presentation later.

Phase 4A adds a separate semantic overlay with the identity progression
`legacy observation -> implementation variant -> user-facing family`.
Snapshot-scoped legacy references remain evidence locators. Opaque family and
implementation IDs are independent of category, provenance, source path, and
display name. Families own drawer presentation; implementations own legacy
membership, backend/target compatibility evidence, and preferred selection.
See `docs/SEMANTIC_CATALOG.md`.

Task 004 extends the compiler-facing progression without changing those IDs:

```text
catalog family -> typed component contract -> implementation binding -> evidence
```

This is the user-to-realization selection progression, not semantic reference
direction; the one-way references are shown at the top of this document.

Phase 4A implementation records are curation precursors. Later companion
binding records retain their `schuss-implementation-*` identity and add exact
contract references and realization details.

## Operation boundary

Task 008 implements the shared headless model used by GUI, CLI, and AI clients.
The versioned operations are `records.validate`, `graph.inspect`,
`build.resolve`, and atomic `graph.transact`. One in-process dispatcher owns
their semantics; `bin/schuss` is a minimal canonical-JSON process adapter over
that exact API.

Shared canonical JSON, schema traversal, portability, diagnostic,
exact-reference, and domain-neutral registry mechanisms now live in a lower
validator core. Device/instrument, component/graph, and target/backend/build
rules are siblings that import only the core. The aggregate validator composes
them. Historic validator summaries and bytes remain unchanged.

The Task 009 invocation seam is data-only and stops before backend lowering;
Task 008 contains no executable handler. See `docs/OPERATION_CONTRACTS.md`.

## Legacy boundary

Only `legacy/ksoloti-bridge/` may depend directly on the legacy Java model. The
bridge may read `.axo`, `.axs`, and `.axp`, invoke resolution, and emit legacy
build artifacts. It must translate results into versioned Schuss records rather
than exposing Swing objects, static `MainFrame` state, preference paths, or
`patchMeta_t`/`ParameterExchange_t` as stable semantic APIs.

See `docs/LEGACY_STRATEGY.md` for the migration sequence.
