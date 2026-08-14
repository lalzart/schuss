# Task 006: Minimal component-contract, implementation-binding, and DSP-graph contracts

Status: complete. Task 004 remains the accepted architecture; Task 006 is the
current completed component/binding/graph contract gate and Task 007 is next.

Work in the Schuss repository. Work only on Task 006.

This is a bounded schema-and-validation implementation task. It must implement
the minimum durable component-contract, implementation-binding, and
authoritative DSP-graph contracts needed to close the Task 005 deferred graph
reference. Do not implement target/backend selection, compilation, graph
editing operations, GUI/CLI behavior, firmware, or hardware behavior.

Before changing anything, read completely:

- `AGENTS.md`;
- `README.md`;
- `docs/PROJECT_CONTEXT.md`;
- `docs/ARCHITECTURE.md`;
- `docs/SCHEMA_STRATEGY.md`;
- `docs/COMPILER_STRATEGY.md`;
- `docs/SEMANTIC_CATALOG.md`;
- `docs/TAXONOMY.md`;
- `docs/PARAMETER_MODEL.md`;
- `docs/LEGACY_STRATEGY.md`;
- `docs/ROADMAP.md`;
- all accepted ADRs;
- Tasks 001-005;
- `docs/reference/CROSSFADER_DOMAIN_SLICE.md`;
- `docs/DEVICE_INSTRUMENT_CONTRACTS.md`;
- `schemas/README.md`;
- the Phase 4A pilot report, overlay, overlay schema, validator, and tests;
- the frozen legacy observations for Crossfader objects 458-460 and their
  pinned source/manifest evidence; and
- the Task 005 schemas, production records, validator, fixtures, and tests.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Context

Task 004 established this one-way identity and reference chain:

```text
implementation binding -> exact component contract -> exact catalog family
DSP graph -> exact component-contract revisions
instrument -> exact device profile + exact DSP graph
```

A catalog family is for musician-facing discovery, not graph typing. A
component contract is the target-independent nominal public type of one node
variant. An implementation binding realizes one exact contract without
redefining it. A graph references contracts, never families, implementation
bindings, legacy observations, paths, `.axo`, `.axs`, or `.axp` artifacts.

Task 005 created:

- device profile `schuss-device-profile-000001` revision 1;
- instrument `schuss-instrument-000001` revision 1;
- a deferred intention for `schuss-graph-000001` revision 1;
- intended public graph parameter `graph-facet-000001`, semantic key `blend`;
  and
- the mapping from one Gills knob to the instrument parameter and from that
  parameter to the deferred graph target.

The graph schema and resolver did not yet exist, so Task 005 correctly omitted
a graph content hash and reported graph resolution as deferred. Task 006 must
create the authoritative graph record, prove the public `blend` target, and
create a new instrument revision with an exact resolved graph reference. It
must retain the historical deferred instrument revision unchanged.

The Task 004 Crossfader document is illustrative. Task 006 must use a smaller
production slice: three exact Crossfader component contracts and companion
bindings prove that one family can contain several incompatible public
signatures, while one authoritative one-node graph uses the mixed-rate variant
to close the Task 005 mapping. Do not create the illustrative sine, noise,
control-to-audio adapter, audio-output, build, or compiler records merely to
make the example look complete.

## Goal and why it exists

Create deterministic, closed, versioned production contracts for:

1. target-independent component interfaces;
2. concrete implementation-to-contract seam mappings; and
3. authoritative typed DSP graphs.

The task exists to prove, with the smallest reviewable production slice, that:

```text
Crossfader family
    -> three distinct exact component contracts
    -> three retained Phase 4A implementation identities and seam maps

Gills knob
    -> instrument public parameter `blend`
    -> graph public parameter `graph-facet-000001`
    -> explicit graph parameter-to-port binding
    -> mixed-rate Crossfader node control inlet
```

This proof must preserve the boundary between browsing identity, node type,
implementation realization, graph structure, instrument behavior, and later
target/backend selection.

## In scope

- One minimal versioned component-contract JSON Schema.
- One minimal versioned implementation-binding JSON Schema.
- One minimal versioned authoritative DSP-graph JSON Schema.
- Reuse of the Task 005 common record envelope and
  `schuss-canonical-json-v1` without changing its meaning.
- The smallest exact-reference closure needed for a post-Task-004 component
  contract to reference the existing Crossfader family truthfully.
- Three production component contracts for the control-rate, audio-rate, and
  mixed-rate Crossfader signatures already evidenced by legacy observations
  458-460.
- Three production companion binding records keyed by the existing Phase 4A
  identities `schuss-implementation-000026`, `...000027`, and `...000028`.
- Complete, type-compatible mappings between each contract's public ports and
  the corresponding frozen legacy observation seams.
- One production `schuss-graph-000001` revision 1 record using the mixed-rate
  Crossfader component contract.
- Public audio input `a`, audio input `b`, audio output `out`, and public
  runtime parameter `graph-facet-000001` (`blend`) on that graph.
- An explicit graph-owned parameter-to-control-port binding for `blend`, with
  declared range, update, and smoothing behavior.
- Graph node, connection, public exposure, parameter binding, hierarchy, and
  type validation sufficient for the bounded production slice and focused
  fixtures.
- A focused non-production transparent-compound fixture proving public mapping
  totality, type compatibility, inspectability, and recursion rejection.
- A new revision of `schuss-instrument-000001` with an exact resolved graph
  reference and the same stable `blend` mapping intention.
- Positive and negative fixtures, deterministic diagnostics, and read-only
  semantic validation.
- Documentation of what the records prove and which compiler/evidence levels
  remain deferred.
- Necessary status and index links only after all acceptance tests pass.

## Out of scope

- Compute-target, backend-capability, toolchain, firmware/ABI, build-request,
  build-result, artifact, resource-estimate, or evidence-claim schemas.
- Deciding whether any binding is eligible, compatible, preferred, or safe for
  Ksoloti Core or another target/backend.
- Binding selection, dependency/resource planning, scheduling, lowering, code
  generation, `.axp`, C++, Java bridge invocation, ARM compilation, or link.
- A normalized compiler IR or optimization model.
- Shared graph operations, mutation transactions, protocol transports,
  conflict handling, CLI commands, GUI models, object drawer, or canvas.
- Phase 4B catalog expansion or contracts/bindings for families other than the
  exact Crossfader slice, except isolated non-production test fixtures.
- A complete universal port/type/capability vocabulary beyond what the slice
  and required boundary tests prove.
- Automatic adapters, implicit rate/channel/unit/representation conversions,
  or family-relative overload fallback.
- Reclassifying Crossfader, changing its Phase 4A membership, allocating new
  implementation identities for observations 458-460, or promoting their
  `not-evaluated` compatibility/preference status.
- Rewriting the Phase 4A overlay, frozen inventory/review artifacts, upstream
  checkouts, or Task 005 revision-1 records.
- Gills panel expansion, firmware, device access, upload, flash, SD-card
  writes, real-time measurement, or listening tests.
- Staging, committing, tagging, or pushing without separate explicit approval.

## Inputs

- The accepted Task 004 ownership, identity, exact-reference, type,
  conversion, migration, and evidence rules.
- The completed Task 005 canonical hashing, device/instrument contracts, and
  deferred graph intention.
- Existing schema and validator conventions in this repository.
- Crossfader family `schuss-family-000018` and retained implementation IDs
  `schuss-implementation-000026`, `...000027`, and `...000028` from the Phase
  4A overlay.
- Frozen legacy observations 458, 459, and 460 and the exact pinned manifests
  to which their evidence locators belong.

A legacy datatype string is evidence to translate; it is not the permanent
Schuss type model. A display label, array position, local checkout path,
legacy source path, or illustrative `example:` identity is not durable
identity. If the frozen evidence cannot support a required type or seam fact,
do not guess: encode a permitted explicit unresolved state or stop when the
fact is required for authoritative type safety.

## Required schema architecture

### Common envelope and exact reference closure

All new production records must use:

- a closed record-family `schema_version`;
- `canonical_profile: schuss-canonical-json-v1`;
- an opaque stable entity ID;
- a positive monotonically increasing entity revision;
- `content_hash` as `sha256:` plus 64 lowercase hexadecimal digits; and
- exact durable references containing target stable ID, revision, and content
  hash.

Reuse the Task 005 canonical implementation and restricted JSON value space.
Do not silently create a second canonical profile, change set/sequence rules,
or change the canonical bytes or content hashes of existing Task 005 records.
Extend reusable code only as required for the three new schema families.

Phase 4A family records predate the Task 004 revision/hash envelope. Do not
fabricate a family revision or claim that an unversioned family member is an
exact record reference. Resolve this bounded migration seam explicitly. The
preferred solution is the smallest closed post-Task-004 companion or migration
record for `schuss-family-000018` that:

- retains stable family ID `schuss-family-000018`;
- binds to the exact Phase 4A overlay bytes and pinned legacy manifest;
- records its own revision, content hash, source schema/version, and whether
  semantics changed;
- copies or projects no more family-owned semantics than necessary;
- does not rewrite the Phase 4A overlay or reclassify the family; and
- permits component contracts to carry an exact family ID/revision/hash
  reference.

An equally small exact-container reference is acceptable only if it satisfies
the Task 004 exact-entity semantics and makes the family member unambiguous.
Document the choice and test stale/wrong family resolution. If neither can be
implemented without contradicting the accepted architecture, stop and report
the conflict.

### Component contract

One component contract owns one exact target-independent public interface and
references exactly one exact catalog-family revision. Different Crossfader
signatures are different contract IDs, not revisions or overload aliases.

The schema must keep these public facet kinds distinct:

- input and output ports;
- runtime parameters;
- build-time attributes;
- discrete actions with typed payloads;
- read-only displays;
- state/lifecycle declarations where required; and
- stable compound public mapping keys where applicable.

Every local facet ID must be stable within its contract and independent of
labels, ordering, coordinates, widgets, backend seams, and legacy names.

For the bounded v0 vocabulary, a port type must independently encode at least:

- direction;
- domain;
- rate;
- channel shape and connection cardinality;
- semantic role;
- value representation and required width/encoding facts;
- unit and exact valid range, including inclusivity and clamp/wrap policy;
- optionality and exact absence/default behavior; and
- ownership, mutability, borrowing, lifetime, capacity, synchronization, and
  aliasing where the domain carries buffers/references.

Use the smallest closed controlled vocabularies that accurately represent the
three Crossfader observations and exercise the required distinct facet kinds
in fixtures. Do not add speculative variants. When a dimension is genuinely
not applicable, use a closed explicit state; do not erase it with a missing
field or bare `null`.

Compatibility between revisions, if represented, is an explicit directed
claim. It must never be inferred from revision numbers, similar signatures,
shared family membership, or shared legacy names. The production slice need
not publish a compatibility claim.

### Direct connection and conversion policy

A graph cable is valid only when its endpoint port types are compatible under
the declared target-independent rules. The initial legal no-adapter cases are:

- exact type equality;
- an output range proven to be a subset of an otherwise identical input
  range; and
- an unconnected optional inlet whose contract declares exact absence/default
  behavior.

All other transformations require an explicit visible adapter node or an
explicit binding already authored into the graph. In particular, the
validator must not silently perform control/audio rate conversion, event to
stream conversion, channel reshaping, numeric representation conversion,
unit/range/polarity conversion, scalar/buffer promotion, ownership transfer,
payload reinterpretation, or facet-kind conversion.

Task 006 may admit one additional lossless direct rule only if the rule is
named, narrowly specified, versioned, and supported by both positive and
negative fixtures. Convenience is not sufficient evidence.

### Implementation binding

A binding record is a companion record keyed by the same stable
`schuss-implementation-*` identity retained from Phase 4A. Each production
binding must:

- have its own entity revision and content hash;
- reference one exact component-contract revision;
- identify its realization form without making target/backend eligibility
  claims;
- reference the exact frozen legacy observation and pinned snapshot evidence;
- provide a total, nonduplicated, directionally valid, type-compatible mapping
  from every public contract facet to a concrete implementation seam;
- retain source/seam details only as evidence or realization locators, not as
  public contract identity; and
- prove that the referenced contract's family agrees with the Phase 4A
  implementation membership.

The binding must not add, remove, rename, retype, or reinterpret any public
facet. Private implementation details may be represented only when needed to
locate or validate the realization. Do not copy target, backend, resource,
toolchain, or compatibility claims out of Phase 4A as if they had been proved.
Task 007 owns the exact target/backend capability and build/evidence boundary;
until then these bindings are not evidence that a selectable build exists.

The three production bindings must retain this correspondence:

| Existing implementation ID | Frozen evidence | Exact contract meaning |
| --- | --- | --- |
| `schuss-implementation-000026` | object 458 | control-rate `a`, `b`, `fade`, and `out` |
| `schuss-implementation-000027` | object 459 | audio-rate `a`, `b`, `fade`, and `out` |
| `schuss-implementation-000028` | object 460 | audio-rate `a`, `b`, and `out`; control-rate `fade` |

Do not infer a fallback relationship among these bindings. Shared family
membership does not make their contracts interchangeable.

### Authoritative DSP graph

The graph is semantic implementation structure and must have independent
stable identity, revision, and content hash. It must support:

- node instances with stable graph-local IDs and exact component-contract
  ID/revision/hash references;
- typed connections between exact port endpoints;
- public graph ports, parameters, actions, and read-only displays as distinct
  facet kinds with stable local IDs;
- explicit exposure maps from public graph ports/facets to node facets;
- explicit parameter-to-port or parameter-to-parameter bindings with domain,
  update, smoothing, and multiplicity rules;
- parameter/attribute values without collapsing runtime and build-time state;
- transparent hierarchy and compound public mapping keys;
- deterministic set/sequence ownership;
- explicit asset/state references only if required by a fixture; and
- a presentation-independent semantic graph.

A graph node must never reference a family, category, implementation binding,
legacy observation, path, display label, `.axo`, `.axs`, or `.axp` as its
type. Canvas coordinates, visual groups, selected nodes, colors, and client
view state must not appear in the semantic graph record.

The semantic validator must resolve the entire exact component-contract
closure before type-checking connections and exposures. It must reject
dangling nodes/facets, wrong directions, duplicate drivers outside an explicit
cardinality rule, illegal implicit conversions, invalid parameter bindings,
hidden/unmapped public compound facets, hierarchy cycles, and recursive
transparent-compound expansion.

### Production Crossfader graph

Create `schuss-graph-000001` revision 1 as the smallest authoritative graph
that closes the Task 005 intention. It must:

- contain one node instance typed by the exact mixed-rate Crossfader component
  contract associated with `schuss-implementation-000028`;
- expose the node's audio `a` and `b` inlets as two public audio input ports;
- expose its audio `out` outlet as one public audio output port;
- define public runtime parameter `graph-facet-000001` with semantic key
  `blend`, exact normalized domain `0` to `1`, and a declared default;
- bind that parameter explicitly to the node's control-rate `fade` inlet;
- declare update boundary, range transform, smoothing responsibility, and
  duplicate-driver policy for the parameter-to-port binding; and
- contain no backend, target, implementation, Gills, device, GUI, compiler,
  or legacy path identity.

The one-node graph requires no internal cable. Focused fixtures must still
exercise legal and illegal graph connections so the connection model is not
left structurally unproved.

This production graph intentionally differs from the larger illustrative Task
004 graph. Document why the smaller transparent graph is sufficient to prove
the schema boundary without inventing unrelated production contracts.

### Transparent compound capability

The schema and validator must prove the accepted transparent-compound model:

```text
compound component contract owns public facet IDs and mapping keys
    -> transparent implementation binding references an exact graph
    -> graph maps those keys to inspectable internal node facets
```

Use focused non-production fixtures unless a production identity is already
required by the Crossfader closure. The fixture must prove total and
type-compatible public mapping, preserved inspectability, exact references,
and rejection of direct or indirect recursive expansion. Do not add an opaque
legacy subpatch merely to satisfy this test.

### Instrument revision and graph resolution

Retain the Task 005 revision-1 instrument bytes and hash unchanged. Add a new
revision of `schuss-instrument-000001` that:

- replaces the deferred graph branch with an exact reference to
  `schuss-graph-000001` revision 1 and its verified content hash;
- preserves the exact device-profile reference;
- preserves the public instrument `blend` parameter and device mapping unless
  a documented schema migration mechanically requires a new encoding;
- maps instrument `blend` to graph public parameter
  `graph-facet-000001`; and
- changes its own revision and content hash.

Extend the instrument validator through the smallest explicit graph-resolver
interface. A `resolved` graph reference passes only when the supplied
authoritative graph registry proves the exact tuple and graph public facet
kind/domain. The historical deferred revision remains valid and reports
deferred; it must not be overwritten, retroactively marked resolved, or given
a fabricated hash.

If the existing `instrument-v0` schema can express the exact reference without
changing its semantics, keep it. If a schema migration is required, retain
the source, produce a deterministic lossless migration record, and explain why
the change could not be represented compatibly.

### Evidence separation

Validation output must report these levels separately:

- structural/schema validation;
- exact reference and content-hash closure;
- target-independent contract/type validation;
- implementation seam-map validation against frozen observations; and
- instrument-to-graph target resolution.

Backend lowering, source/artifact generation, ARM compile/link,
connected-device execution, real-time/resource validation, and audible
listening must remain `not-run`. A legacy resolved observation proves only the
recorded host-model/export fact; it does not prove target compatibility,
compiler success, device execution, performance, or sound quality.

## Required deliverables

Choose the smallest coherent repository layout and document it. At minimum,
produce:

- this task file updated with final status and completion evidence only after
  every acceptance criterion passes;
- `schemas/component-contract-v0.schema.json`;
- `schemas/implementation-binding-v0.schema.json`;
- `schemas/dsp-graph-v0.schema.json`;
- the minimal exact Crossfader-family companion/migration schema and record if
  required to satisfy the accepted exact-reference rule;
- one concise normative component/binding/graph contract document under
  `docs/`;
- three Crossfader component-contract production records;
- three companion implementation-binding production records using the
  retained Phase 4A implementation IDs;
- `schuss-graph-000001` revision 1;
- retained instrument revision 1 plus a new exact graph-resolved instrument
  revision;
- read-only reference, hash, type, graph, binding, compound, and instrument
  validation;
- focused positive and negative fixtures;
- focused automated tests; and
- necessary schema-index, project-status, architecture, and roadmap links
  after validation succeeds.

Durable records must use portable repository-relative organization. Machine-
local paths belong only in ignored local configuration. Do not commit Python
bytecode, generated caches, timestamped reports, compiler artifacts, or
machine-local state.

## Validator requirements

The validator must be read only and fail closed. It must validate:

- closed JSON Schema structure and controlled vocabularies;
- schema versions, opaque stable IDs, positive revisions, and local IDs;
- canonical serialization, content hashes, and ID/revision uniqueness;
- exact reference closure and stale/wrong reference rejection;
- exact Crossfader family resolution without a fabricated legacy revision;
- one family to several non-interchangeable contract identities;
- distinct facet kinds and complete port-type dimensions;
- strict direct-connection compatibility and explicit conversion ownership;
- total, unique, directional, type-compatible binding seam maps;
- agreement between each binding's exact contract family and its Phase 4A
  implementation membership;
- graph node, endpoint, connection, public exposure, parameter binding,
  cardinality, hierarchy, and compound rules;
- prohibition of family/binding/path/observation identity in graph nodes;
- exact instrument graph resolution and public target kind/domain matching;
- explicit historical deferred graph resolution state;
- absence of timestamps, random IDs, absolute checkout/temp paths, hidden
  fallback, and presentation state in semantic records; and
- deterministic diagnostics and summary output.

The validator must not invoke Java, generate `.axp`, select a backend or
binding for a build, compile, access a device, write preferences, modify
inputs, or update caches.

## Required fixtures and negative tests

At minimum, tests must cover:

1. The valid exact Crossfader family closure, all three contracts, all three
   companion bindings, production graph, device profile, and both instrument
   revisions.
2. Two fresh-process validations of unchanged records produce byte-identical
   canonical bytes and deterministic summary output.
3. Existing Task 005 canonical bytes and content hashes remain unchanged.
4. Reordering schema-declared sets does not change canonical bytes; reordering
   semantic sequences changes the hash or fails as declared.
5. One stable ID/revision resolving to different bytes/hash fails; stale or
   wrong nested exact references fail.
6. A fabricated family revision/hash, ambiguous family member, or family
   mismatch between binding and Phase 4A membership fails.
7. The three different Crossfader public signatures cannot share one contract
   ID or masquerade as revisions of one public signature.
8. Unknown, duplicate, directionally wrong, incomplete, or type-incompatible
   public facets fail.
9. Collapsing parameter, attribute, action, display, or port kinds fails.
10. A binding with a missing/duplicate seam, wrong observation, wrong contract,
    redefined public facet, or unsupported compatibility/preference claim
    fails.
11. A graph node referencing a family, implementation, legacy observation,
    path, display label, `.axo`, `.axs`, or `.axp` fails.
12. Unknown node/facet endpoints, inlet-to-inlet, outlet-to-outlet, duplicate
    drivers, illegal self/cyclic topology where prohibited, and dangling
    public exposures fail.
13. Every prohibited implicit rate, channel, representation, unit/range,
    ownership, payload, and facet-kind conversion has a negative test or one
    table-driven test covering the complete closed list.
14. Exact compatible connections and the permitted output-range-subset and
    optional-unconnected cases pass; near-miss cases fail.
15. A graph parameter driving a port without explicit update, smoothing,
    transform/range, or driver policy fails.
16. The production graph resolves `graph-facet-000001` as a public parameter
    with semantic key `blend` and rejects a kind/domain mismatch.
17. A graph embedding implementation selection, target/backend data, device
    mappings, Gills slots, canvas state, or compiler artifacts fails.
18. A transparent compound with total compatible public mappings passes;
    missing, duplicate, incompatible, hidden, direct-recursive, and
    indirect-recursive mappings fail.
19. Instrument revision 2 resolves the exact graph and `blend` target;
    revision 1 remains valid and deferred; a false resolved claim, stale graph
    hash, unknown target, or wrong facet kind/domain fails.
20. Absolute paths, timestamps, random identifiers, mutable labels encoded in
    stable IDs, unknown fields, and unknown controlled values fail closed.

## Acceptance criteria

1. All existing inventory, review, semantic-catalog, and Task 005 tests and
   validators pass.
2. Frozen Phase 2, Phase 3, and review artifacts remain byte-identical.
3. The Phase 4A overlay and its family/implementation ID projection remain
   byte-identical; no upstream checkout is mutated.
4. The three new schemas are closed, versioned, deterministic, and limited to
   component, binding, and graph ownership.
5. Existing Task 005 canonical bytes, schema meaning, production revision-1
   records, and hashes remain unchanged.
6. Every new production record has an opaque stable ID, positive revision,
   verified content hash, and exact references.
7. `schuss-family-000018` is referenced through a truthful exact closure; no
   revision/hash or classification fact is fabricated.
8. Three distinct Crossfader contracts reference the same exact family and
   accurately preserve the control-rate, audio-rate, and mixed-rate public
   signatures.
9. The three companion bindings reuse implementation IDs 000026-000028, map
   every contract facet exactly once to observations 458-460, and make no new
   target/backend compatibility or preference claim.
10. Ports, parameters, attributes, actions, displays, state/lifecycle, and
    compound mapping keys remain distinct.
11. Required port-type dimensions are explicit, controlled, and validated;
    legacy datatype strings do not become the Schuss public type system.
12. Direct connections are strict, all implicit conversions remain prohibited
    except any narrowly proved versioned addition, and adapters are never
    invented by validation.
13. `schuss-graph-000001` revision 1 references the exact mixed-rate component
    contract, never its family or binding, and contains no target/backend,
    device, legacy path, or presentation identity.
14. The production graph publicly exposes audio `a`, `b`, and `out` plus
    parameter `graph-facet-000001` (`blend`), and explicitly binds `blend` to
    the mixed-rate control inlet with complete policy.
15. Transparent compound fixtures prove exact references, total mappings,
    inspectable internals, type compatibility, and recursion rejection.
16. A new `schuss-instrument-000001` revision exactly resolves the production
    graph and public `blend` target while revision 1 remains byte-identical and
    truthfully deferred.
17. The validator is read only, deterministic across fresh processes, and
    emits stable structured diagnostics and a stable evidence-level summary.
18. Structural, reference, target-independent typing, legacy seam-map, and
    graph-target evidence are reported separately from every unrun compiler,
    target, device, real-time, and audible level.
19. Positive and negative fixtures exercise every stated boundary and
    prohibition.
20. No target/backend/build/operation schema, compiler, GUI/CLI, firmware,
    hardware, upload, flash, staging, commit, or push action occurs without
    separate explicit approval.
21. Documentation identifies Task 006 as complete only after all tests pass
    and names Task 007 as the next implementation gate.
22. All unresolved design questions are listed with an owner and earliest
    later task.

## Decisions this task may make

- Exact v0 filenames and portable record organization for the three schema
  families.
- Opaque contract, graph, node, local facet, connection, mapping, and binding
  revision allocation consistent with Task 004.
- The smallest exact companion/migration representation for the existing
  Crossfader family.
- The bounded target-independent port/type controlled vocabularies required by
  this slice and its tests.
- Exact graph public-exposure, parameter-binding, hierarchy, and transparent-
  compound field shapes.
- The smallest implementation seam-locator shape that resolves against frozen
  observations without turning paths or indexes into Schuss identity.
- Exact deterministic diagnostic codes and summary shape.
- Whether component, binding, graph, and migrated instrument validation shares
  one validator or a few narrowly composed read-only validators.
- Whether additional focused fixtures are needed to prove a stated boundary.

## Decisions this task must not make

- Target/backend capability vocabularies, compatibility, preference, binding
  selection, toolchain/ABI identity, resource limits, or build/evidence record
  shapes owned by Task 007.
- Compiler lowering, supported legacy subset, Java bridge invocation, `.axp`
  generation, scheduling, or artifact formats owned by later tasks.
- Shared mutation-operation or client protocol semantics owned by Task 008.
- GUI, CLI, object browser, canvas, or AI-client convenience models.
- Phase 4B family expansion or a universal type system beyond this bounded
  slice.
- New semantic meaning, family membership, implementation identity, or target
  support inferred from source order, path, shared name, shared family, or a
  successful structural export.
- Automatic implementation fallback or implicit adapter insertion.
- Any change to accepted Task 004 decisions, frozen evidence, the Phase 4A
  overlay, or Task 005 revision-1 record bytes.

## Sequencing and parallel-work boundary

Tasks 007-011, compiler/backend implementation, shared operations, CLI, and GUI
all consume the exact contracts produced here. Do not implement them in
parallel with Task 006 because their inputs are not yet stable.

Read-only preparation may independently gather pinned Ksoloti Core target,
toolchain, firmware/ABI, and resource evidence for Task 007, or physical Gills
evidence for a later device-profile revision. Such preparation must not alter
Task 006 schemas, assign production identities, make compatibility claims, or
be treated as Task 006 completion evidence.

## Required completion report

When finished, report:

- files added or changed;
- final schema IDs/versions and production record IDs/revisions/hashes;
- the exact-family migration/companion choice and why it is truthful;
- the three Crossfader contract signatures and retained family relationship;
- the three implementation seam maps and the evidence each uses;
- the graph nodes, public facets, exposures, and explicit `blend` binding;
- the instrument revision migration and proof that revision 1 was retained;
- the exact type and conversion rules implemented;
- transparent-compound and recursion evidence;
- positive and negative fixtures and structured diagnostic codes;
- tests and validators run, including fresh-process determinism;
- confirmation that frozen evidence, the Phase 4A overlay/IDs, and Task 005
  hashes were unchanged;
- evidence levels reached and explicitly not reached;
- questions deliberately deferred with owners; and
- the recommended exact scope of Task 007.

Do not claim completion merely because schema files exist. Check every
acceptance criterion and record concrete evidence in this task file. Do not
stage, commit, push, invoke a compiler, access hardware, upload, or flash
without separate explicit approval.

## Completion evidence

1. Added four closed schemas: `catalog-family-companion-v0`,
   `component-contract-v0`, `implementation-binding-v0`, and `dsp-graph-v0`.
   The companion is the smallest truthful exact-family bridge needed because
   the retained Phase 4A family member has no entity revision/content hash.
   Its Task 006 revision/hash envelope binds the exact overlay/member/manifest
   hashes, copies no taxonomy or presentation fields, and declares an
   identity-only migration with no semantic change.
2. The exact family record is `schuss-family-000018` revision 1,
   `sha256:710afad6b087d18fb949b9749c9e9dc63d4fd26e94800369d437d90d956eed8d`.
   It binds overlay raw SHA-256
   `497a27d295d0ccda799848ac6fcba245139ca29156f509431b7cb7522d791858`,
   canonical member SHA-256
   `5141692aac29da13c1344e6938538a3aa87de640702c0746eee8d54eab61f388`,
   and resolved manifest SHA-256
   `0e3f3cb763f634ce490195e2cd4665c2e1a41764cd54c6526e6e219f18e1e959`.
3. Three independent component contracts reference that same exact family:
   control `schuss-component-contract-000001` r1
   (`sha256:4db27f00dde3c2a577a2817aec04f8a43997de1e47661ad2b005a75db90577a4`),
   audio `schuss-component-contract-000002` r1
   (`sha256:5de75541ca60b19b63846fff4f74279f0aa67466999371fb35b223745be917b4`),
   and mixed `schuss-component-contract-000003` r1
   (`sha256:96a29faf58769be5f2ac52de07aa80cae3dcdff28f0f3c158fb1fd12cc234a8d`).
   Their `a,b,fade,out` rates are respectively
   `control,control,control,control`, `audio,audio,audio,audio`, and
   `audio,audio,control,audio`. Validation rejects different public signatures
   sharing an ID or masquerading as revisions.
4. The bounded type model independently declares direction, domain, rate,
   channel shape, cardinality, semantic role, representation, unit, exact
   range/inclusivity/overflow, optionality/absence/default, and ownership,
   mutability, borrowing, lifetime, capacity, synchronization, and aliasing.
   The production representation is signed 32-bit two's-complement Q27.
   Direct connections admit exact type equality, output-range subset under
   otherwise identical typing, and explicitly defaulted optional inlets only.
   No implicit rate, channel, representation, unit/range, ownership, payload,
   or facet-kind conversion is admitted. Capability and compatibility-claim
   arrays are closed empty in v0 pending an accepted later vocabulary.
5. Companion bindings retain the Phase 4A identities and exact frozen seam
   evidence: `schuss-implementation-000026` r1 / observation 458 /
   `sha256:1fd65dd4a3bae9e47a739f0634ab27ad169c2f83bb213f2029eae0f5b23fe498`;
   `schuss-implementation-000027` r1 / observation 459 /
   `sha256:9ac532281d1e7dd666877019bb12b622c989bee4b17ec93653a499a8c20a363c`;
   and `schuss-implementation-000028` r1 / observation 460 /
   `sha256:6f1a0268c40ca192435bcd7a66f201ab0577ff8786590d3c05bace4911726b59`.
   Each maps all four public facets once, checks the manifest, observation,
   UUID, source ID/hash, seam index/name/type/datatype, and Phase 4A family/form.
   Every selection state remains `not-evaluated`, owned by Task 007; no target,
   compatibility, preference, fallback, or build claim was added.
6. `schuss-graph-000001` revision 1 has content hash
   `sha256:b38562dc2dcf80036e8fc1d78fe8ee425de01f4943495a23375bfb4e7f346e6e`.
   Its sole `graph-node-000001` references the exact mixed contract. Public
   audio `a`, `b`, and `out` each have one exposure. Public parameter
   `graph-facet-000001` has semantic key `blend`, exact normalized domain
   `0..1`, and default `0.5`; its control-rate `fade` binding declares both
   domains, ordered linear transform, control-cycle update boundary,
   graph-owned linear smoothing through the next control cycle, and exclusive
   driver policy. No unrelated production component or internal cable was
   invented.
7. `schuss-instrument-000001` revision 2 has content hash
   `sha256:f98290ae5a1b599466ff9429c08442492fb172e94f6012b6ddedecd2bafd6ce5`
   and resolves the exact graph and `blend` parameter kind/domain through the
   explicit graph registry. Revision 1 remains byte-identical with content hash
   `sha256:3543d631ceb32b17be95c84eccc07d38ad29f1dc71c5a267b40306f69711bc53`
   and remains truthfully deferred. The device reference and both musical
   mappings are retained.
8. The read-only aggregate validator composes family, component, binding,
   graph, device, and instrument validation. It resolves the complete exact
   contract closure before graph typing; checks endpoints, direction,
   cardinality, connection and exposure IDs, driver uniqueness, public
   exposures, parameter policies, signal/hierarchy cycles, and graph target
   kind/domain; and emits sorted structured diagnostics. Representative codes
   include `FAMILY_MEMBER_AMBIGUOUS`, `FAMILY_REFERENCE_UNRESOLVED`,
   `CONTRACT_SIGNATURE_REVISION_MISMATCH`, `BINDING_MAP_INCOMPLETE`,
   `BINDING_SEAM_DUPLICATE`, `BINDING_TYPE_INCOMPATIBLE`,
   `GRAPH_ENDPOINT_UNKNOWN`, `GRAPH_CONNECTION_TYPE_INCOMPATIBLE`,
   `GRAPH_EXPOSURE_INCOMPLETE`, `DUPLICATE_DRIVER`,
   `GRAPH_PARAMETER_DOMAIN_MISMATCH`, `COMPOUND_MAPPING_INCOMPLETE`,
   `COMPOUND_MAPPING_TYPE_INCOMPATIBLE`, `COMPOUND_RECURSION`, and the
   existing instrument mapping/reference codes.
9. Focused test constructors prove exact and subset connections, optional
   unconnected input behavior, every prohibited type dimension, payload and
   facet-kind separation, unknown/directionally invalid endpoints, duplicate
   drivers and IDs, dangling exposures, cycles, and all required parameter
   policies. Transparent-compound fixtures prove exact inspectable closure and
   total compatible mapping, then reject missing, duplicate, incompatible,
   hidden, direct-recursive, and indirect-recursive mappings. The portable
   negative mutation file contains 31 cases covering exact-family, schema,
   seam, forbidden ownership, portability, and controlled-vocabulary failures.
10. All 26 contract tests pass: 16 Task 006 tests plus the ten retained Task
    005 tests. Two fresh aggregate validator processes emit byte-identical
    summaries, SHA-256
    `d295106d38cdf9075a85d9e1a803b5df23e3ffbbe934dceb3cec9194b59ce6af`;
    two fresh canonical-emission processes for every new production record
    also agree. Set reordering is canonical-byte invariant while ordered
    transform-point reversal changes bytes and fails validation. The aggregate
    status is `valid-with-historical-deferred` with one family companion,
    three contracts, three bindings, one graph, one device, two instruments,
    one exactly resolved graph reference, one historical deferred reference,
    and no diagnostics.
11. All 14 inventory tests and six semantic-catalog tests pass. The raw
    validator retains 4,209 files and two issues; resolved validation retains
    3,602 objects, 1,157 graphs, and 3,180 issues; the Phase 3 review retains 20
    issue classes, 157 overload groups, 805 partial graphs, and 103 zombie
    groups; semantic validation retains 26 families and 38 implementations.
12. The 27-file frozen Phase 2/3/review aggregate remains
    `764b1c5a0b65ade0160dd0db049246f6cd754e58bb5a31073ae0f301eb78faa7`.
    The Phase 4A ID projection remains
    `c317f06ab7749c3d25f763e71355efdde1486d869c05127dc2eb1faa7f915cf7`;
    its raw overlay hash is unchanged, and `git diff --name-only` is empty for
    every frozen root and the overlay. Task 005 raw SHA-256 values remain
    `5c81b6ced640165342a471edc19aa5523c1b9ba44e8d666adcf6e46cb6a13ccc`
    (device schema),
    `94a6f720647dd6b9099708a1f31d84790a9ec2b5254330334bd694c5ef31c5c8`
    (instrument schema),
    `2dd75c58ebea79be11abf8bbd8bb8ff320c77eb303d35388fc8baa6a49d3d855`
    (device record), and
    `d88769280887ec54ee5e9cfbb631c4150d7c5a0878a8cd17e9bf7c7005216d0c`
    (instrument revision 1). No upstream checkout mutation
    command was executed; the pinned Ksoloti evidence checkout remained at
    commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`.
13. Reached evidence levels are structural/schema, exact-reference closure,
    target-independent contract typing, legacy implementation seam mapping,
    and exact instrument graph-target resolution. Backend lowering, artifact
    generation, ARM compile/link, connected-device execution, real-time
    resource measurement, and audible listening are all explicitly `not-run`.
14. Added records under `contracts/catalog-families/`,
    `contracts/component-contracts/`, `contracts/implementation-bindings/`, and
    `contracts/graphs/`, plus instrument revision 2; added the four schemas,
    aggregate validator, Task 006 tests/fixtures, and
    `docs/COMPONENT_GRAPH_CONTRACTS.md`; extended the Task 005 validator only
    through its explicit graph-registry input and updated the necessary status
    and index documentation. `git diff --check` passes.
15. Deferred decisions have named owners in
    `docs/COMPONENT_GRAPH_CONTRACTS.md`. Task 007 should add only exact
    compute-target, backend-capability, build-request/result, artifact,
    resource-report, and level-specific evidence schemas and validators. It
    must consume this exact closure without implementing lowering, operations,
    GUI/CLI behavior, firmware, hardware access, upload, or flash.
16. No Java invocation, `.axp` generation, compiler, device access, preference
    or cache write, stage, commit, push, upload, SD-card write, or firmware
    flash occurred.
