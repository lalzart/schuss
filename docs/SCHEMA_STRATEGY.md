# Schuss schema strategy

This document is normative for the ownership, identity, revision, and reference
direction of future Schuss records. It deliberately defines contract families
and invariants rather than complete production fields. Machine-readable
schemas are introduced only by the bounded tasks named below.

The terms **MUST**, **MUST NOT**, **SHOULD**, and **MAY** express requirement
strength.

## Architectural rule

Schuss separates discovery, public node type, implementation, graph structure,
physical device, musical instrument, execution target, lowering backend, and
build evidence.

```text
frozen legacy observation
          ^ evidence
          |
implementation binding ----> component contract ----> catalog family
          |                         ^
          |                         |
          +----> transparent graph  +---- DSP graph nodes

instrument ----> device profile
     |
     +---------> DSP graph

project ----> immutable base record set + exact project-owned record closure
   |
   +-------> graph / instrument / build request / assets

build request ----> graph / instrument + compute target + backend
build result  ----> request + selected bindings + artifacts
evidence claim ----> build result / stage / artifact
```

An arrow means the record on the left may reference the record on the right.
No reverse ownership is implied. Reverse indexes and search views are derived,
never embedded merely for convenience.

## Record families and owners

| Record family | Normative owner | Owns | May reference | Must not own or redefine |
| --- | --- | --- | --- | --- |
| Catalog family | Catalog curation | Stable family identity, drawer name/aliases/docs, functional placement, review state | Taxonomy vocabulary and curation evidence | Node signature, backend, target, source path, implementation selection |
| Component contract | Component API | Stable contract identity/revision, typed facets, lifecycle/state requirements, capabilities, compound public mapping declarations | Exactly one catalog family and versioned vocabularies | Source code, legacy path, target-specific resource figures, implementation priority |
| Implementation binding | Backend implementation registry | Concrete realization form, exact contract realization, dependencies/resources, capability constraints, evidence links, explicitly curated selection priority | One exact component-contract revision; backend/capability declarations; target constraints; source evidence; optionally a transparent graph | New or altered public facets; family classification; graph node identity |
| DSP graph | Graph model | Graph identity/revision, node instances, exact contract refs, connections, facet values/bindings, hierarchy, exposed mappings, state/assets | Component contracts and content-addressed resources | Families, categories, legacy observations/paths, implementation bindings, device controls, target/backend choices |
| Device profile | Device owner | Physical controls/gestures, indicators/displays, physical I/O, feedback, ranges/resolution, stable hardware slots | Shared physical-unit and gesture vocabularies | DSP graph, instrument behavior, compute target, backend |
| Instrument | Instrument owner | Musical identity, public parameters/actions/displays/state, device mappings, graph mappings | One or more device-profile revisions and one authoritative graph revision | Embedded device design, copied graph structure, implementation binding, backend, target |
| Project/workspace | Project owner | Portable project identity/revision, immutable base record-set reference, exact project-owned member closure, selected graph/instrument/build references | Exact semantic records and content-addressed assets | Redefined graph/build semantics, ambient directory membership, absolute workspace identity, client-specific behavior |
| Compute target | Target owner | Processor/ABI constraints, memory regions/budgets, runtime assumptions, firmware interface, asset limits, supported capabilities | Toolchain/firmware declarations and capability vocabulary | Panel design, instrument behavior, catalog classification |
| Backend | Backend owner | Lowering identity/version, accepted inputs, emitted artifact kinds, supported capability vocabulary, deterministic stage contract | Shared capability vocabulary | Authoritative graphs, device profiles, catalog categories |
| Build request | Build orchestration | Exact requested inputs, target/backend choice, options, optional validated binding overrides | Graph, optional instrument, compute target, backend, immutable resources | Build conclusions, catalog mutations, implicit source discovery |
| Build result | Build orchestration | Exact request/input closure, selected bindings, stage outcomes, diagnostics, output hashes, resource reports | Request, binding, target, backend, toolchain/ABI and artifact records | Rewritten graph, automatic catalog preference or compatibility truth |
| Evidence claim | Evidence owner named by level | One bounded observation, method, subject hashes, outcome, limitations | Build result/stage, artifact, target/device as applicable | Inferred higher/lower evidence, catalog classification |
| Presentation overlay | Client/presentation owner | Coordinates, groups, colors, panels, drawer layout, client hints | Family, contract, graph, instrument, or device semantic IDs | Semantic identity, build inputs, hidden graph rewrites |
| Asset/resource descriptor | Asset owner | Media type, byte length, content hash, logical role and portable locator | Immutable content-addressed bytes | Absolute checkout path as durable identity |

`Component contract -> catalog family` is the only compiler-domain reference
to a family. A family does not contain authoritative child-contract arrays;
clients derive “contracts in family” from the contract registry. This prevents
a family/contract ownership cycle.

A transparent implementation binding may reference both a component contract
and a graph. The graph references only contracts, not bindings. That keeps
transparent compounds inspectable without a binding/graph cycle.

The exact-record reference closure MUST be acyclic. The one revision-stratified
evidence pattern is a newly curated binding revision citing evidence whose
closure contains a build result that selected an earlier binding revision. The
validator MUST require the cited revision to be strictly earlier and MUST
reject evidence that closes through the current or a later binding revision.
Thus a result can pin what it built and a later binding revision can cite that
result without a content-hash cycle or reverse ownership.

## Identity hierarchy

### Catalog family

A catalog family is the musician-facing discovery item established in Phase
4A. It is not a type and is never directly compiled. One family may be
referenced by several non-interchangeable contracts, such as control-rate,
audio-rate, mixed-rate, and integer variants.

Phase 4A family IDs remain unchanged. Category moves, aliases, names, or
presentation edits MUST NOT allocate a new family ID.

### Component contract or node variant

A component contract is the target-independent nominal public type of a node.
It owns stable local IDs for all ports, parameters, attributes, actions, and
displays. Those facets remain distinct even where a legacy format serializes
them similarly.

Every contract MUST reference exactly one catalog family. Contract identity
MUST NOT contain a family label, category path, backend, target, provenance, or
legacy path. Different public signatures MUST be different contracts even when
they share one family.

A contract revision MAY evolve one continuing contract. Compatibility between
revisions is an explicit, directed claim backed by a validator rule or review;
it is never inferred from revision ordering. A materially different node
variant receives a different contract ID rather than using a revision to hide
non-interchangeability.

### Implementation binding

An implementation binding is a concrete realization of one exact component
contract revision. Realization forms include a legacy `.axo`, generated legacy
object, legacy `.axs`, Schuss-native transparent compound, native C/C++, or
target service.

The binding MUST provide an explicit mapping from each contract facet to its
implementation seam and MUST fail validation if the mapping is incomplete,
duplicated, directionally invalid, or type-incompatible. It may add private
state and observed dependencies. Resource requirements require the separate
Task 007 contract. A binding MUST NOT add, remove, rename, retype, or change
the meaning of the public contract.

Phase 4A `schuss-implementation-*` IDs remain the stable identities of the
concrete realizations already curated. Task 006 companion bindings for the
Crossfader slice use those same IDs and add exact component-contract
references; the Phase 4A overlay remains preserved evidence and is not
rewritten in place. The validator requires each binding's contract to
reference the same family recorded by Phase 4A.

### DSP graph

A graph is authoritative implementation structure. Every node instance MUST
reference an exact tuple:

```text
component_contract_id + contract_revision + content_hash
```

The graph MUST NOT reference a catalog family, category, display name, legacy
observation index, source/legacy path, implementation ID, or `.axp` as node
identity. Authoring tools may query families and propose contracts, but the
committed graph records the selected contract revision explicitly.

An exact graph reference is likewise:

```text
graph_id + graph_revision + content_hash
```

Optional canvas coordinates and visual groups belong in a presentation
overlay. Removing the overlay cannot change graph semantics or build output.

### Device profile, instrument, compute target, and backend

These records have independent stable IDs and revisions.

- Gills is a device profile. It owns physical control and feedback slots, not
  DSP or musical behavior.
- An instrument owns musical behavior and maps a device profile to a graph. It
  is neither Gills hardware nor a graph nor a target.
- `ksoloti-core` is a compute target. It owns execution constraints, not panel
  design or an instrument.
- `legacy-ksoloti` is a backend. It lowers a validated Schuss graph through the
  isolated bridge; it is not a component type or target.

## Stable identity, entity revision, and schema version

Every durable semantic record introduced after Task 004 MUST use a common
logical envelope containing:

- a record-family `schema_version`;
- an opaque stable entity ID;
- a positive, monotonically increasing entity `revision`;
- a `content_hash`; and
- explicit references using the target ID, revision, and content hash.

The three version concepts are independent:

- **Stable ID** answers “which enduring entity is this?”
- **Entity revision** answers “which semantic state of that entity?”
- **Schema version** answers “which record shape and validation rules encode
  that state?”

Changing a schema does not force untouched records to be rewritten when they
remain valid. Migrating one record into a different canonical representation
MUST create a new entity revision and content hash, even when the migration
declares `semantic_change: false`. Any semantic-content change also creates a
new entity revision and hash. One stable-ID/revision pair MUST resolve to
exactly one hash. Changing a display label or layout stored in a separate
presentation record does not revise the referenced semantic entity.

Stable IDs MUST be opaque and MUST NOT encode category paths, display labels,
filesystem paths, target/backend names, or array positions. Deleted published
IDs and revision numbers MUST NOT be reused.

## Exact references and content hashes

Durable semantic and build inputs MUST use exact references containing stable
ID, revision, and content hash. A user-facing query may request “latest
compatible,” but resolution of that query produces an explicit revised graph
or build request; a build never silently substitutes a newer record.

Future schema tasks MUST implement and test `schuss-canonical-json-v1` before
publishing hashed records. After structural and semantic validation, schemas
classify arrays as ordered sequences or mathematical sets; set arrays are
sorted by the canonical bytes of their elements, while sequence order is
preserved. The resulting value is serialized with RFC 8785 JSON Canonicalization
Scheme rules as UTF-8. The `content_hash` field itself is omitted from its own
digest, and the digest is rendered as `sha256:` plus 64 lowercase hexadecimal
digits. Timestamps and machine-local paths are prohibited from semantic hash
material. Values outside the RFC 8785/I-JSON number model MUST fail closed or
use a schema-defined exact string/rational representation.

The initial digest algorithm is SHA-256, named with the digest so a future
algorithm can coexist. External assets are stored or located by byte hash and
portable source ID. Absolute checkout paths remain only in ignored local
configuration.

## Schema evolution and migration

### Backward-compatible schema changes

A schema change is backward-compatible only when every previously valid record
retains the same decoded semantics and remains valid or has a deterministic,
lossless migration. Examples may include an optional field with a defined
semantic default or a newly accepted diagnostic code in an extensible
diagnostic envelope.

Compatible schema releases still receive an explicit schema version or pinned
schema digest. “Compatible” never means validators may ignore unknown fields;
durable contracts remain closed unless a schema explicitly defines an
extension point.

### Breaking changes

A change is breaking when it alters required fields, meanings, units, identity
rules, defaults, reference semantics, controlled-vocabulary meaning, or
canonical hashing. It requires a new schema version and an explicit migration.
No migration may overwrite its source artifact.

A component public-signature change always creates a new contract ID; it is a
different node variant even when a directed adapter can relate it to the old
one. A non-signature semantic edit creates a new revision, with compatibility
recorded explicitly. A graph remains pinned to the old exact contract until a
migration operation validates and writes a new graph revision.

### Migration records

Migrations MUST name source and destination schema versions, tool/version,
input and output hashes, diagnostics, and whether semantics were preserved.
They MUST be deterministic for identical input and MUST retain the source
record. A migration failure produces diagnostics; it does not create a partial
authoritative destination.

## Unresolved and uncertain information

Unknown, unresolved, ambiguous, unsupported, and not-evaluated are different
states. Future schemas MUST use explicit tagged states with a stable diagnostic
or question code, affected field/reference, evidence references, rationale,
and recommended owner where relevant. A bare `null`, absent required fact,
empty string, guessed default, or load-order choice MUST NOT erase uncertainty.

Catalog and evidence records MAY retain unresolved information. An
authoritative graph MAY retain an unresolved authoring draft only when the
record is clearly non-buildable. Any unresolved fact required for identity,
typing, binding selection, resource safety, or lowering MUST fail the relevant
validation stage closed.

## JSON and JSON Schema

JSON plus JSON Schema Draft 2020-12 remains appropriate for durable Schuss
contracts because it is language-neutral, reviewable, deterministic under a
pinned canonicalization profile, and usable by GUI, CLI, AI, bridge, and build
tools. JSON Schema provides structural validation; closed semantic validators
remain necessary for reference resolution, graph topology, type compatibility,
identity, hashing, capability, and evidence rules.

JSON is not required for large binary assets, compiler intermediates, logs, or
firmware images. Those remain external content-addressed artifacts with JSON
descriptors. The future normalized DSP representation may be an internal
derived format; Task 004 does not declare it a stable public schema.

No generated Java class, Swing model, GUI view model, CLI output convenience
shape, `.axo`, `.axs`, or `.axp` becomes a Schuss domain schema.

## Component contract shape

The Task 006 component contract declares:

- stable contract identity, revision, hash, and family reference;
- typed inlets and outlets;
- runtime parameters;
- build-time attributes;
- discrete actions and typed payloads;
- read-only displays;
- state ownership, persistence, reset, and lifecycle where required;
- a closed capability-requirement collection, empty in v0 until Task 007;
- explicit parameter/port/action binding capabilities; and
- compound public-interface mapping declarations where applicable.

Local facet IDs are stable within the contract and independent of labels,
order, coordinates, widgets, or legacy names.

### Port type dimensions

A port type MUST keep at least these independent dimensions:

| Dimension | Required meaning |
| --- | --- |
| Direction | Inlet or outlet; never inferred from a label |
| Domain | Stream, event, buffer/table reference, or message/data |
| Rate | Audio, control, sporadic/event, compile-time where meaningful, or an explicit not-applicable value |
| Channels and cardinality | Channel shape plus allowed connection multiplicity; scalar, mono, and stereo are not synonyms |
| Semantic role | Audio, modulation, pitch, gate, trigger, clock, note, MIDI, or generic data role independent of representation |
| Value representation | Boolean, signed/unsigned integer, fixed point, float, enum, bytes, structured payload, reference, and width/encoding as required |
| Unit and valid range | Exact unit vocabulary, range bounds, inclusivity, wrap/clamp policy, and unknown state |
| Optionality | Required, optional with an explicit default/absence behavior, or conditionally present under an attribute |
| Ownership and lifetime | For buffers/references: owner, mutability, borrowing, lifetime, capacity, synchronization, and alias rules |

Task 006 implements the bounded Crossfader vocabularies documented in
`docs/COMPONENT_GRAPH_CONTRACTS.md`. A legacy datatype string is evidence to
translate; it MUST NOT collapse domain, rate, role, representation, or
ownership into one permanent field.

### Connection and conversion policy

The initial Schuss rule is strict: a direct cable is valid only when every
required port dimension is compatible under the component-contract type rules.
Backends MUST NOT insert adapters silently.

The following are not conversions and MAY be legal without an adapter:

- exact type equality;
- an output range proven to be a subset of an otherwise identical input range;
  and
- leaving an optional inlet unconnected when its contract defines the exact
  absence/default behavior.

All other transformations require an explicit typed adapter node or binding
already present in the authoritative graph. In particular, these are illegal
implicit conversions:

- control stream to audio stream, or audio stream to control value;
- event/trigger/gate to stream or parameter state;
- mono to stereo duplication, stereo to mono mixing, or channel reshaping;
- integer, fixed-point, or float representation changes;
- pitch/note/frequency conversion or unit scaling;
- bipolar/unipolar range changes, clamping, wrapping, or quantization;
- scalar-to-buffer promotion, buffer ownership transfer, or mutable aliasing;
- message/MIDI payload reinterpretation; and
- parameter, attribute, action, or display conversion into a port merely
  because a legacy widget or datatype made them look similar.

Task 006 admits no additional direct-conversion rule. Any later lossless rule
requires a versioned type contract and positive and negative fixtures.
Convenience wiring belongs in explicit authoring operations that add visible
adapter nodes.

## Facet exposure and mapping chain

The public-control chain is explicit:

```text
implementation seam
    -> component-contract facet
    -> compound public facet
    -> instrument public parameter/action/display
    -> device-profile control/gesture/feedback slot
```

Each arrow is owned by the layer on its left-to-right boundary:

- An implementation binding maps implementation seams to contract facets.
- A component contract declares stable public facets and, for a transparent
  compound, stable public mapping keys.
- A graph's exposed-interface map binds those keys to internal node facets.
- An instrument maps public instrument facets to graph public facets or exact
  node facets where the instrument contract permits that coupling.
- A device mapping maps physical controls/gestures to instrument parameters or
  actions and maps instrument displays/state back to device feedback slots.

A runtime parameter may drive a port only through an explicit typed binding or
adapter with defined update, smoothing, and range behavior. An attribute is
resolved at build time and cannot be driven by a performance control. An
action is discrete; a display is read-only.

For a transparent compound, the component contract owns the required public
facet IDs and mapping keys. The referenced graph owns concrete mappings from
those keys to internal node facets. The implementation binding joins the
contract and graph and MUST prove the mapping total and type-compatible. This
division preserves the required compound public contract without making a
contract own an internal graph or creating a graph/binding reference cycle.

## Semantic, presentation, generated, and evidence records

- Semantic records define families, contracts, bindings, graphs, devices,
  instruments, targets, and backends.
- Presentation overlays define client layout and labels that are not already
  musician-facing catalog semantics.
- Generated artifacts include normalized IR, `.axp`, C++, objects, maps, and
  firmware packages. They are derived and content-addressed.
- Build/evidence records say what exact inputs and actions produced or observed
  what results.

Generated artifacts and evidence never become authoritative semantic inputs by
reverse inference. A GUI or CLI may render or mutate semantic records only
through the same future typed operation layer.

To preserve acyclic exact hashing, build results do not reference evidence
claims that reference them. Results own stage outcomes and artifacts; separate
evidence claims point to the immutable result, stage, or artifact. A binding
may cite an evidence claim only in a new revision whose cited closure ends at
source/artifact and contract hashes or a strictly earlier binding revision.

## Explicit prohibitions

The following are invalid architecture:

- a graph referencing catalog categories or families as node types;
- a graph using snapshot indexes, legacy paths, display names, `.axo`, `.axs`,
  or `.axp` as permanent node identity;
- a device profile embedding a DSP graph or instrument behavior;
- a compute target embedding panel/device design;
- an implementation binding redefining or extending its component contract;
- a build result rewriting catalog compatibility, preference, or
  classification truth;
- a GUI view model, CLI response, Java class, or AI convenience structure
  becoming the authoritative domain model; or
- an unresolved selector being repaired by source order, load order, path, or
  silent fallback.

## Contract status and implementation sequence

### Normative now

- The ownership, reference, identity, hashing, migration, type-shape, and
  separation rules in this document.
- The compiler stages and evidence rules in `docs/COMPILER_STRATEGY.md`.
- ADRs 0005-0007.
- Existing source-lock, inventory, review, and Phase 4A overlay schemas for the
  artifacts they already validate.
- Task 005 `device-profile-v0` and `instrument-v0` schemas, their restricted
  `schuss-canonical-json-v1` profile, and the read-only ownership/mapping checks
  documented in `docs/DEVICE_INSTRUMENT_CONTRACTS.md`.
- Task 006 `catalog-family-companion-v0`, `component-contract-v0`,
  `implementation-binding-v0`, and `dsp-graph-v0` schemas, exact Crossfader
  closure, and read-only validators documented in
  `docs/COMPONENT_GRAPH_CONTRACTS.md`.
- Task 011B additive `component-contract-v1` and
  `implementation-binding-v1` schemas, the exact seven-contract/eight-node
  Gills-slice closure, and mixed-version read-only validation. Q21 semitone
  offsets, Q27 normalized/audio values, public behavior rules, exact null
  legacy parameter datatypes, and observed durable UUID widths remain bounded
  successor semantics; no v0 byte changes.
- Task 007 capability, environment, compute-target, backend, eligibility,
  build-request/result, artifact, resource, and evidence schemas; the
  Ksoloti-specific production closure; and the pure resolver documented in
  `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`. Reusable schema families use
  controlled stable processor, ABI, environment, firmware/runtime, backend,
  and bridge identity values rather than Ksoloti constants.
- Task 012A `project-v0`, `workspace-head-v0`,
  `project-write-plan-v0`, local lock/recovery schemas, and additive operation
  v3 envelopes. The project owns an explicit base-plus-overlay closure and
  exact revision parentage; it does not revise accepted records or make
  workspace paths semantic identity.

### Current compiler sequence

Tasks 008-012A are complete: the Task 005-007 mechanisms are consolidated
beneath three sibling rule modules; versioned headless validation, inspection,
resolution, catalog, and transaction operations are implemented; two bounded
legacy-backend slices reach ARM compile/link; and the product CLI projects the
shared operations; Task 012A now adds project persistence without general build
execution.

Tasks 013-017 are complete. The completed gated sequence was:

1. **Task 016:** direct-frontend expansion through the complete Task 011C
   graph after legacy-equivalent versus Schuss-native behavior is selected.
2. **Task 017:** a bounded reviewed-core expansion and richer non-UI reference
   instruments after Task 016 completes.
3. **Task 018:** full Gills implementation and parameter/control mapping after
   both completed dependencies.

Task 016 is accepted through local evidence level 5 under the selected
legacy-equivalent route. Task 017 is accepted through levels 1-2 with exact
unsupported diagnostics for direct semantics not established by its review.
Task 018's dependency gate is satisfied; its contract is complete and the
implementation is ready to begin with authenticated Gills panel evidence.

Task 012B is retired. UI and presentation work remain an unnumbered future
milestone and cannot introduce client-specific catalog, graph, project, build,
or compiler semantics.

### Deliberately deferred

- Complete controlled vocabularies and production schema fields.
- Complete Ksoloti target budgets and measured resource envelopes.
- Remote protocol transport, queues, cancellation, and progress events.
- General optimizer, instruction-level IR, and replacement ABI design beyond
  the bounded Tasks 013-016 compiler stages.
- Additional targets/devices, asset pipelines, and complete Phase 4B curation.

The remaining device questions and Task 006's target/backend/build deferrals
have named owners and earliest tasks in `docs/DEVICE_INSTRUMENT_CONTRACTS.md`
and `docs/COMPONENT_GRAPH_CONTRACTS.md`; the wider deferred decision set
remains in `docs/tasks/004-schema-and-compiler-contract-strategy.md`.
