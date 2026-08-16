# Schuss compiler strategy

This document is normative for compiler stage boundaries, authoritative
inputs, derived outputs, implementation selection, diagnostics, and evidence.
It defines two backend paths over the same Schuss graph. It does not implement
either path or define a complete optimizer or instruction-level IR.

## Compiler invariant

The authoritative input is an exact Schuss graph revision plus the exact
semantic-record closure it references. A catalog family, legacy observation,
source path, `.axo`, `.axs`, emitted `.axp`, generated C++, object file, or
firmware artifact is never a substitute for that graph.

The compiler MUST NOT mutate the graph to make an unsupported, ambiguous, or
ill-typed build succeed. Any migration or adapter insertion is a separate
authoring operation that creates a new graph revision before compilation.

## Build inputs and outputs

### Build request

A durable build request must bind at least:

- build-request ID, revision, schema version, and content hash;
- exact graph ID, revision, and hash;
- exact instrument ID, revision, and hash when an instrument is part of the
  build;
- exact compute-target ID, revision, and hash;
- exact backend ID, revision, and hash;
- normalized, versioned build options;
- exact asset/resource references;
- optional explicit implementation-binding overrides; and
- the requested stopping stage or evidence-producing action.

An implementation override may only narrow eligible bindings. It cannot make
an incompatible binding eligible or bypass type, capability, resource, or
evidence checks.

If an instrument is supplied, its graph reference MUST equal the graph in the
request. A mismatch is an input error, not a backend choice.

### Build result

A durable build result must bind at least:

- its request and the resolved exact input closure;
- every selected implementation-binding ID, revision, and hash, associated
  with the authoritative node or compound instance it realizes;
- toolchain identity and version/hash;
- firmware/runtime ABI identity and version/hash;
- normalized build options actually used;
- stage outcomes and stable diagnostic records;
- generated artifact kinds, byte hashes, and portable locators;
- estimated and measured resources as separate typed observations;
- stage outcomes sufficient for separate level-specific evidence claims; and
- a deterministic result status that distinguishes success, failure,
  unsupported, unresolved, and not-run.

The result never embeds a rewritten authoritative graph. Derived elaborated
graphs, normalized representations, and source maps are artifacts referenced
by hash. Separate evidence records reference the immutable result, stage, or
artifact; the result does not point back to those records.

## Common front half

Both the legacy and future backends use the following conceptual stages. Task
007 now fixes their closed record representation; executable operations remain
later tasks.

| Stage | Authoritative input | Derived output | Required failure/diagnostic behavior |
| --- | --- | --- | --- |
| 1. Schema and identity validation | Build request and referenced record bytes | Validated exact input closure | Reject unknown/breaking schema, hash mismatch, dangling reference, ID/revision collision, or nonportable required input |
| 2. Target-independent graph validation | Graph plus exact component contracts and assets | Typed authoritative graph view; no binding choices | Reject family/path/implementation node refs, missing facets, invalid connections/bindings, illegal implicit conversions, invalid hierarchy, or unresolved build-required semantics |
| 3. Target and backend validation | Explicit target/backend refs and typed graph requirements | Capability query context | Reject unsupported backend/target pair or undefined capability vocabulary; do not select implementations yet |
| 4. Implementation resolution | Validated graph, target/backend context, binding registry, explicit overrides | Immutable node-to-binding resolution plan | Require exact contract match and satisfied constraints; zero matches or unresolved priority ties fail closed |
| 5. Compound elaboration | Resolution plan and transparent compound graphs | Elaborated graph plus expansion/source map | Reject missing mappings, interface mismatch, recursive expansion, or hidden unresolved nodes; retain hierarchy and origin paths |
| 6. Dependency and resource planning | Elaborated graph, selected bindings, target constraints | Dependency closure and typed resource plan/estimates | Reject ambiguous dependencies, incompatible versions, hard-budget violations, or unknown facts required for safe lowering |
| 7. Backend lowering | Elaborated graph, resolution/dependency/resource plans | Backend-specific derived representation | Reject unsupported constructs explicitly and preserve diagnostic traceability; never alter the source graph |
| 8. Artifact generation | Lowered representation and pinned tools | Content-addressed source/boundary artifacts and source maps | Stable order/bytes for identical closure; report generation failures separately from lowering |
| 9. Target compile and link | Generated source/artifacts, target/toolchain/runtime closure | Objects, link map, executable/firmware artifact | Preserve compiler/linker diagnostics and resource figures without promoting them to runtime claims |
| 10. Packaging and evidence recording | All completed stage records | Build result, artifact manifest, individual evidence claims | Never infer unperformed evidence levels or rewrite semantic records |

Stage 2 completes before target/backend implementation selection. This allows
one graph to be validated as a target-independent typed structure even when a
requested backend has no realization for it.

Later stages MAY revalidate newly exposed compound internals, but they cannot
weaken an earlier rule. A failure after elaboration identifies both the
internal node and the authoritative compound instance path.

## Type checking and adapters

The component contract is the only public node type. Type checking uses the
independent port dimensions and facet rules in `docs/SCHEMA_STRATEGY.md`.

The compiler accepts exact/declared-compatible connections. It does not infer
that a common legacy datatype string makes different rates, units, semantic
roles, representations, channels, or ownership compatible. Rate conversion,
channel reshaping, unit conversion, parameter-to-stream promotion, event
latching, clamping, and ownership transfer require explicit graph nodes or
bindings already represented in the authoritative graph.

A backend MAY fuse or optimize explicit adapters later, but diagnostics and
source maps retain their graph identities. Optimization must not erase the
semantic explanation of a conversion.

## Implementation binding resolution

Resolution is deterministic and occurs only after the graph is typed and the
target/backend are explicit.

An eligible binding must satisfy all of the following:

1. It realizes the node's exact component-contract ID and revision and names
   the expected contract hash.
2. Its implementation form is supported by the selected backend.
3. Its target predicate and capability requirements are satisfied by the exact
   compute-target record.
4. Its public-facet realization map is complete and type-compatible.
5. Its dependency and resource declarations are structurally valid and all
   facts required specifically for eligibility are known; full closure and
   budget planning remain stage 6.
6. Any required compatibility claim has the named evidence level demanded by
   policy; absence of evidence is not support.
7. It is not excluded by a valid request override.

Selection then follows only explicitly curated priority rules in the binding
registry or an exact valid request override. Filesystem order, Java load order,
source repository, family membership, display name, graph frequency, and the
Phase 4A `not-evaluated` preferred status are not selection rules.

If no binding remains, resolution reports unsupported. If several equally
eligible bindings remain without an explicit total policy, resolution reports
ambiguity. It MUST NOT choose the first.

The resolution plan is a derived immutable artifact containing the candidate
set, exclusions with diagnostic codes, selected binding, policy version, and
trace to every authoritative node instance.

## Transparent compound elaboration

A transparent compound binding realizes a component contract with a referenced
Schuss graph. The contract owns the public facet IDs and compound mapping keys;
the graph owns the concrete exposed-interface targets; the binding joins them.

Elaboration must:

- validate a total, directionally and type-compatible public mapping;
- replace each selected compound instance with a derived namespaced copy of
  its internal graph;
- preserve stable origin links to the outer node, binding, inner graph, and
  internal node/facet;
- detect recursive compound-definition expansion independently from permitted
  signal-flow feedback;
- preserve state/lifecycle ownership and resource scoping; and
- retain enough hierarchy for inspection and diagnostics after lowering.

The elaborated graph is not a new authoritative graph revision. A user may
request it as an inspectable build artifact, but edits apply to the source
graph through future graph operations.

An implementation presented as a compound but lacking inspectable internals
cannot claim the transparent-compound form. Native opaque primitives and
target services may exist as other implementation forms with explicit
evidence and capability limits.

## Dependency and resource planning

The plan is derived from selected bindings, transparent graphs, target
constraints, assets, and build options. Dependencies and resources use stable
portable IDs and exact versions/hashes; ambient include paths and machine-local
search order cannot be authoritative inputs.

The planner distinguishes:

- hard declared requirements from estimates;
- static link-map measurements from runtime measurements;
- memory regions and alignment from aggregate byte totals;
- code/data/stack/heap/external-asset requirements;
- exclusive services and hardware resources;
- compile-time capacity from real-time headroom; and
- measured values from inferred or not-evaluated values.

A successful static plan or ARM link does not prove CPU headroom, connected I/O,
device stability, or sound quality.

## Transitional legacy backend

The first executable path preserves the Ksoloti Java code-generation path, ARM
compiler/linker, firmware, and runtime:

```text
authoritative Schuss graph
    -> schema and semantic validation
    -> exact component-contract resolution
    -> explicit target/backend validation
    -> legacy implementation-binding selection
    -> transparent compound elaboration
    -> dependency and resource planning
    -> deterministic legacy .axp boundary artifact + trace manifest
    -> isolated Ksoloti Java load/resolution/code generation
    -> existing ARM compiler and linker
    -> Ksoloti firmware artifact + build/evidence records
```

All Java, Swing/global-state compatibility, legacy resolution, XML handling,
and legacy tool invocation remain under `legacy/ksoloti-bridge/`. Core Schuss
packages exchange versioned records and content-addressed artifacts with the
bridge.

### Legacy `.axp` adapter contract

The adapter receives only the validated resolution, elaboration, dependency,
and resource plans. It emits:

- deterministic `.axp` bytes for the supported legacy subset;
- a manifest binding the `.axp` hash to the exact Schuss inputs and selected
  legacy bindings;
- a source map from legacy object/instance/endpoint serialization back to
  graph node, contract facet, and compound path; and
- explicit diagnostics for unsupported or lossy constructs.

The adapter MUST use exact legacy identity evidence from selected bindings. It
must not rediscover components by family name or ambient path. The bridge MUST
verify that legacy resolution selected the expected definitions and fail if
load order, UUID collision, overload, working directory, or missing source
makes that unprovable.

### What `.axp` proves

An emitted `.axp` plus its manifest can prove only that the validated supported
subset was deterministically serialized into the named legacy boundary format
and remains traceable to its Schuss inputs.

It does **not** prove that:

- Ksoloti Java will resolve the intended objects;
- legacy code generation succeeds or is semantically faithful;
- generated C++ compiles or links;
- the firmware artifact fits every runtime resource bound;
- the board boots or connected I/O works;
- timing and real-time CPU headroom are acceptable; or
- the instrument is audible, correct, stable, or musically useful.

An `.axp` is never imported back as the authoritative graph merely because it
was emitted successfully.

## Future Schuss compiler frontend

The future path shares the complete front half and authoritative graph:

```text
the same authoritative Schuss graph
    -> schema and semantic validation
    -> exact component-contract resolution
    -> explicit target/backend validation
    -> native implementation-binding resolution
    -> transparent compound elaboration
    -> dependency and resource planning
    -> target-independent normalized DSP representation + source map
    -> Schuss graph-to-C++ frontend
    -> Ksoloti runtime/ABI lowering
    -> existing ARM compiler and linker
    -> Ksoloti firmware artifact + build/evidence records
```

The normalized DSP representation is derived, deterministic, inspectable, and
content-addressed. It contains enough typed topology, state/lifecycle,
scheduling constraints, resources, and origin information for the frontend,
but is not the authoring source of truth. Task 004 does not freeze its complete
instruction set, scheduler, optimizer, or serialization.

The direct frontend has no semantic dependency on Ksoloti Java or `.axp`.
Ksoloti runtime/ABI lowering is a backend stage after target-independent
normalization. The existing ARM compiler/linker and firmware/runtime may remain
unchanged initially.

Using the same graph does not guarantee every backend has a binding for every
contract. A missing direct binding is an explicit backend-resolution failure,
not permission to rewrite the graph or fall back silently to Java.

## Diagnostics and traceability

Every diagnostic is a structured record with stable code, severity, stage,
message parameters, and subject references. Human text is a rendering, not the
only machine interface.

Where applicable, a diagnostic must retain:

- build request and exact graph ID/revision/hash;
- authoritative node-instance ID;
- component-contract ID/revision/hash;
- local port, parameter, attribute, action, display, state, or mapping ID;
- compound expansion path and internal graph/node/facet;
- implementation-binding ID/revision/hash;
- compute-target and backend ID/revision/hash;
- dependency, resource, toolchain, firmware ABI, source, or artifact reference;
- compiler stage and backend substage; and
- related diagnostics or evidence without implying them.

Generated `.axp`, C++, compiler line/column output, link-map symbols, and runtime
probe subjects use source maps to recover this chain. A backend-local file line
alone is not an adequate Schuss diagnostic identity.

Diagnostics are deterministic for identical inputs: stable ordering, stable
codes, portable paths/IDs, and no random IDs or wall-clock data in canonical
output.

## Artifacts and deterministic builds

Every generated artifact descriptor records artifact kind, media type, byte
length, SHA-256, producer stage/version, input-closure hash, and portable
locator. Generated bytes must have stable ordering and normalized encoding and
must omit timestamps unless a later task explicitly requires and tests a
non-semantic timestamp field.

Host paths, process IDs, temporary directories, ambient environment variables,
and unordered compiler output are normalized or recorded outside canonical
identity. A result is reproducible only when the exact semantic closure,
bindings, tools, runtime ABI, options, and assets are pinned.

Reproducible bytes are evidence of deterministic generation at the named
stage. They are not evidence of device or audible equivalence.

## Evidence levels

Evidence claims use these independent levels:

| Level | Name | Bounded claim |
| --- | --- | --- |
| 1 | Structural/schema validation | Named records satisfy their structural schemas, hashes, and closed identity/reference checks |
| 2 | Component and graph resolution | Exact contracts, graph topology, bindings, compounds, dependencies, and required semantic references resolve under the named policy |
| 3 | Backend lowering | The selected backend accepts and lowers the validated input closure |
| 4 | Source/artifact generation | Named deterministic boundary/source artifacts were generated with recorded hashes |
| 5 | ARM compilation and linking | The named ARM toolchain compiled and linked the recorded artifacts for the target/runtime closure |
| 6 | Connected-device execution | A named physical device executed the artifact and only the stated behaviors were observed |
| 7 | Real-time/resource validation | Named load, memory, timing, I/O, or stability measurements passed stated methods and limits |
| 8 | Audible/listening validation | Named playback/listening procedure supports only the stated audible or musical claim |

No level implies any other. A level-8 listening record does not silently prove
reproducible source, and a level-5 link does not prove device execution. A
derived evidence view for a build result lists every claim actually established
and marks others not-run, not-evaluated, failed, or unsupported as appropriate.

Compatibility claims in implementation bindings cite immutable evidence
records and the exact subject revisions. Running a build does not update a
binding. Promotion requires a separate reviewed curation operation that emits
a new binding revision and cites the evidence.

## Backend conformance

A backend conforms only if it:

- accepts exact validated Schuss record references;
- advertises a versioned capability contract;
- resolves bindings after type and target/backend validation;
- fails closed on ambiguity and unsupported constructs;
- preserves compound and diagnostic traceability;
- produces deterministic content-addressed outputs for deterministic stages;
- never mutates the authoritative graph or semantic registry;
- reports evidence at the exact level reached; and
- can run headlessly without implicit device access or firmware mutation.

The transitional legacy backend may rely on Java only inside the isolated
bridge. The direct frontend must not require Java or `.axp`. Both remain
backends beneath the same graph, contract, target, build, and evidence model.

Task 007 validates only the declarative contract and pure selection boundary.
Task 008 consolidates the shared validator core and exposes typed headless
operations plus a data-only accepted-request seam. Task 009 separately owns actual legacy lowering,
`.axp` serialization/source maps, exact toolchain/runtime closure, and ARM
compile/link execution.

## Implemented headless compiler boundary

The compiler path is now staged and reusable rather than a single frontend
jump:

1. durable projects preserve an explicit base-plus-overlay closure;
2. the common front half resolves and elaborates exact records, dependencies,
   resources, and origin maps without backend lowering;
3. shared build execution selects an exact backend descriptor and publishes
   only fresh successful output roots;
4. normalized DSP and the direct frontend lower the bounded accepted closure;
5. the reviewed core admits richer graphs but stops deterministically where
   native semantics have not been established.

ADR 0011 fixes the accepted direct route as legacy-equivalent for its bounded
closure. Missing direct bindings or lowering rules remain explicit unsupported
results; the implementation may not silently fall back to Java or `.axp`.
General optimization, replacement firmware/ABI work, connected-device
execution, and audible validation remain separate authorization and evidence
levels.

The current Gills promotion gate is defined by ADR 0012 and
`docs/tasks/018-full-gills-implementation-and-parameter-control-mapping.md`.
Live status and later decision gates belong in `docs/STATUS.md` and
`docs/ROADMAP.md`, not in this stable architecture document.
