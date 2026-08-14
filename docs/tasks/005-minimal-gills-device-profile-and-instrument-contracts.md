# Task 005: Minimal Gills device-profile and instrument contracts

Status: complete. Task 004 remains the accepted architecture; Task 005 is the
current completed device/instrument contract gate and Task 006 is next.

Work in the Schuss repository. Work only on Task 005.

This is a bounded schema-and-validation implementation task. It must implement
the minimum durable device-profile and instrument contracts required by the
Task 004 crossfader reference slice. Do not implement DSP graph, component,
binding, target, backend, build, compiler, GUI, CLI, firmware, or hardware
behavior in this task.

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
- Tasks 001-004;
- `docs/reference/CROSSFADER_DOMAIN_SLICE.md`;
- `schemas/README.md`; and
- the Phase 4A pilot report and overlay schema.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Context

Task 004 established these one-way references:

```text
instrument -> device profile + DSP graph
DSP graph -> exact component-contract revisions
```

It also established that Gills is a physical device profile, not a DSP graph,
instrument, compute target, or backend. An instrument owns musical public
facets and mappings into a graph. Device mappings connect physical controls and
feedback slots to those instrument facets; they never connect a device
directly to a graph.

Task 005 must implement only the first minimal production schemas and fixtures
for that boundary. The DSP graph schema does not exist yet. An instrument may
therefore carry a syntactically exact graph reference whose target-resolution
check is explicitly deferred to Task 006; that deferral must be represented as
data and must not be reported as successful graph resolution.

## Goal and why it exists

Create deterministic, closed, versioned device-profile and instrument
contracts that prove Schuss can describe a minimal Gills-facing musical
mapping without embedding DSP, target, backend, or legacy implementation
details.

The task exists so physical-device and musical-instrument identity are stable
before component-contract and graph schemas harden. It must prove the mapping:

```text
Gills physical knob
    -> instrument public parameter `blend`
    -> exact deferred graph public-parameter target `blend`
```

The schemas must be small enough to review completely and general enough that
later Gills work can add controls and mappings without changing the layer
boundary.

## In scope

- A minimal versioned device-profile JSON Schema.
- A minimal versioned instrument JSON Schema.
- The common identity/revision/content-hash envelope required by Task 004.
- A tested `schuss-canonical-json-v1` implementation for the restricted JSON
  value space accepted by these schemas.
- A minimal Gills device-profile record with evidence-backed or explicitly
  unresolved physical facts.
- A minimal reference instrument record with public `blend` parameter.
- One explicit Gills-knob-to-instrument mapping.
- One explicit instrument-`blend`-to-graph-public-parameter mapping.
- Explicit separation of parameters, actions, displays, state declarations,
  device inputs, gestures, feedback outputs, and physical I/O.
- Closed structural and semantic validation with deterministic diagnostics.
- Positive and negative fixtures focused on the layer boundary.
- Documentation of what the new records prove and what remains deferred.
- Necessary status/index links after all acceptance tests pass.

## Out of scope

- Component-contract, implementation-binding, or DSP-graph schemas.
- Resolving the deferred graph reference or inventing a graph record/stub to
  make it appear resolved.
- Port, rate, channel, unit-conversion, or graph-connection type systems.
- Compute-target, backend-capability, build-request, build-result, artifact, or
  evidence schemas.
- Shared graph operations, mutation transactions, or protocol transports.
- CLI commands, GUI models, object drawer, canvas, or editor behavior.
- Compiler stages, `.axp`, C++, ARM compilation/linking, firmware, runtime ABI,
  or Java bridge changes.
- Device access, panel scanning, upload, flash, SD-card writes, connected OLED,
  real-time measurements, or listening tests.
- A complete Gills hardware census or claim that every pot, button, encoder,
  LED, display feature, or I/O path has been electrically verified.
- Designing a complete musical instrument, mapping the full Gills panel, or
  applying the full Gills instrument-release gate.
- Copying existing Gills-instrument repository contracts as the Schuss domain
  model.
- Reclassifying Phase 4A families, adding component contracts, expanding Phase
  4B, or changing existing family/implementation IDs.
- Modifying frozen inventory/review artifacts or upstream checkouts.
- Staging, committing, tagging, pushing, uploading, or flashing without
  separate explicit approval.

## Inputs

- The accepted Task 004 identity, hashing, ownership, mapping, and unresolved
  information rules.
- The illustrative Crossfader slice. It is an architecture example, not a
  production schema or evidence record.
- Existing Schuss schema and validator conventions.
- Any portable, pinned, repository-local evidence actually used to describe
  Gills physical facts.

Memory, another checkout, a path name, a historical instrument contract, or a
known panel layout may guide questions but is not durable evidence by itself.
If an exact Gills range, resolution, gesture, display, feedback, or I/O fact is
not supported by an accepted input, encode it as explicitly unresolved or omit
it when optional. Do not guess.

## Required schema architecture

### Common record envelope

Both record families must have:

- a closed `schema_version`;
- an opaque stable entity ID;
- a positive monotonically increasing entity revision;
- a `content_hash` rendered as `sha256:` plus 64 lowercase hexadecimal digits;
  and
- exact references expressed as stable ID, revision, and content hash.

The entity ID must not encode a display label, category, filesystem path,
device control label, graph label, target, backend, or array position. One
ID/revision pair must resolve to exactly one hash.

Implement and test the restricted `schuss-canonical-json-v1` contract from
`docs/SCHEMA_STRATEGY.md`:

1. validate the record structurally and semantically;
2. omit only the record's own `content_hash` field from its digest input;
3. preserve ordered-sequence arrays;
4. sort schema-declared set arrays by their canonical element bytes;
5. serialize the resulting value with RFC 8785-compatible canonical JSON for
   the restricted value space accepted by these schemas;
6. hash the UTF-8 bytes with SHA-256; and
7. reject nonportable numbers, duplicate identities, timestamps, random IDs,
   absolute local paths, or values outside the supported canonical profile.

Do not create a broad generic framework beyond what these two schema families
need. The helper may be reusable, but its public surface must remain minimal.

### Device profile

The device-profile schema owns only physical capability and stable
hardware-facing slots. It must be capable of representing, as distinct record
kinds:

- absolute controls such as knobs;
- relative controls such as encoders;
- buttons or other discrete controls;
- gestures derived from named physical controls;
- indicators and display/feedback slots;
- physical audio, MIDI, CV, or other I/O slots;
- physical ranges and resolution when known;
- feedback direction/capability; and
- explicit unresolved physical facts with question/evidence metadata.

Every slot and gesture has a stable local ID independent of mutable labels,
layout coordinates, or widget order. The schema must keep input controls,
gestures, feedback outputs, displays, and physical I/O distinct.

A device profile must not contain:

- a DSP graph or graph reference;
- instrument public behavior or parameter definitions;
- instrument mappings;
- component contracts or implementation bindings;
- compute-target, backend, toolchain, or firmware identity; or
- generated/legacy patch content.

The minimal Gills record should include only the evidence-backed slots needed
to exercise the schema and reference instrument. At minimum it must include a
stable absolute knob slot used by the `blend` mapping. Add representative
gesture, feedback/display, or physical-I/O slots only when needed to validate
the required distinct record kinds and only with supported or explicitly
unresolved facts.

Do not expand this fixture into an asserted complete ten-pot/four-button/
encoder/OLED panel specification merely because existing Gills instruments
use that panel. Completeness is a later bounded task.

### Instrument

The instrument schema owns:

- stable musical identity and revision;
- one exact device-profile reference;
- one syntactically exact graph reference;
- public runtime parameters;
- public actions;
- public read-only displays;
- state declarations and persistence/reset policy where used;
- device-control/gesture-to-instrument mappings;
- instrument-to-device-feedback mappings where used; and
- instrument-to-graph parameter/port/action mappings.

Parameters, actions, displays, and state declarations must remain distinct
types with stable local IDs. Empty collections are allowed only when the schema
defines their meaning and the semantic validator confirms no required mapping
is missing.

The instrument must not contain:

- copied DSP nodes, ports, nets, compound internals, or implementation source;
- implementation-binding, target, backend, toolchain, firmware, or `.axp`
  identity;
- physical device definitions copied from the referenced device profile; or
- GUI coordinates or client view-model state as semantic identity.

### Deferred exact graph reference

The reference instrument must carry a stable graph ID, revision, and syntactic
content hash for the Task 004 illustrative graph target. Because no graph
schema or authoritative graph record exists yet, the reference must also carry
an explicit structured resolution state such as:

```text
status: deferred
owner: task-006
reason: graph-schema-not-yet-implemented
```

Exact field names are a Task 005 decision. The semantic validator must:

- validate the reference tuple's syntax;
- report the graph target as deferred, not resolved;
- reject `resolved` unless an accepted graph resolver proves the exact target;
- reject a missing owner/reason for deferred resolution; and
- never manufacture a graph file, placeholder graph hash, or legacy `.axp`
  identity to close the reference.

If a truthful syntactically exact content hash cannot be supplied without an
authoritative target, define a closed tagged unresolved-reference form instead
of inserting a fabricated digest. Document that choice and retain the
stable-ID/revision intention needed by Task 006. Do not weaken exact references
for records that claim resolution.

### Mapping boundary

The minimal reference instrument must contain:

```text
Gills knob slot -> instrument parameter `blend`
instrument parameter `blend` -> graph public parameter target `blend`
```

The device mapping must declare at least source and destination IDs, direction,
source/destination domains or ranges, transform/curve, polarity, response-time
or smoothing responsibility where applicable, and feedback/pickup behavior
where applicable. Unknown details remain explicit.

The graph mapping must identify the graph public facet kind and stable local
facet target. Until Task 006 provides graph resolution, the instrument must
declare that target inside the same closed deferred-reference structure so the
validator can check internal consistency without claiming the facet exists in
an authoritative graph. It must not target a legacy inlet, family,
implementation, category, path, `.axo`, or `.axp`.

The validator must reject:

- device control directly mapped to a graph facet;
- graph facets embedded in the device profile;
- unknown control or instrument-facet IDs;
- graph-facet IDs absent from or inconsistent with the instrument's declared
  deferred graph-target structure, while leaving authoritative target
  existence unresolved;
- parameter/action/display facet-kind mismatch;
- reversed mapping direction;
- incompatible or incomplete range transforms;
- duplicate drivers where the schema does not explicitly permit them; and
- mappings that silently redefine source or destination domains.

## Required deliverables

Choose the smallest coherent repository layout and document it. At minimum,
produce:

- `docs/tasks/005-minimal-gills-device-profile-and-instrument-contracts.md`
  updated with final status and completion evidence;
- one versioned device-profile JSON Schema under `schemas/`;
- one versioned instrument JSON Schema under `schemas/`;
- a concise normative device/instrument contract document under `docs/`;
- a minimal Gills device-profile record;
- a minimal `blend` reference-instrument record;
- focused positive and negative fixtures;
- a read-only semantic validator;
- canonical JSON/content-hash support limited to the accepted schemas;
- focused automated tests; and
- necessary schema-index, project-status, architecture, and roadmap links after
  validation succeeds.

Durable records must use portable repository-relative organization. Machine-
local paths belong only in ignored local configuration. Do not place generated
validation caches or timestamped reports in the repository.

## Validator requirements

The validator must be read only and fail closed. It must validate:

- closed JSON Schema structure;
- schema version and stable identity syntax;
- unique IDs and local facet/slot IDs;
- positive revisions and exact content hashes;
- canonical serialization and hash round-trip;
- deterministic ordering of schema-declared set collections;
- exact device-profile reference resolution;
- explicit deferred graph-reference state;
- mapping source/target existence, direction, facet kind, and transform shape;
- prohibition of cross-layer embedding;
- explicit unresolved records and required question ownership;
- absence of timestamps, random IDs, absolute checkout/temp paths, and legacy
  path identity; and
- deterministic diagnostics and summary output.

The validator must not access a device, invoke Java, generate `.axp`, compile,
write preferences, modify inputs, or update caches.

## Required fixtures and negative tests

At minimum, tests must cover:

1. The valid minimal Gills plus `blend` instrument pair.
2. Two fresh-process validations of unchanged records produce byte-identical
   canonical bytes and summary output.
3. Reordering schema-declared set arrays does not change canonical bytes;
   reordering semantic sequence arrays either changes the hash or is rejected,
   as the schema declares.
4. Changing a display label while retaining the entity identity leaves the ID
   projection unchanged but requires a new revision/hash if that label is in
   semantic content.
5. Reusing one ID/revision with different content fails.
6. Wrong or stale content hash fails.
7. Device profile embedding graph, instrument, target, backend, or patch fields
   fails.
8. Instrument embedding DSP nodes, implementations, target/backend, physical
   slot definitions, or GUI coordinates fails.
9. Direct device-to-graph mapping fails.
10. Unknown knob or instrument parameter fails; a graph target absent from or
    inconsistent with the declared deferred graph-target structure fails,
    without claiming that the target exists in a graph record.
11. Mapping a knob to an action/display with parameter mapping kind fails.
12. Missing/incompatible transform range, polarity, direction, or duplicate
    driver fails.
13. A graph reference claiming `resolved` without a Task 006 resolver fails.
14. A deferred or unresolved record without code, owner, rationale, and
    evidence/question shape fails.
15. Absolute paths, timestamps, random identifiers, and mutable labels encoded
    into stable IDs fail.
16. Unknown fields and unknown controlled values fail closed.

## Acceptance criteria

1. All existing inventory and semantic-catalog tests and validators pass.
2. Frozen Phase 2, Phase 3, and review artifacts remain byte-identical.
3. Phase 4A family and implementation IDs remain unchanged.
4. The two new schemas are closed, versioned, and limited to device/instrument
   ownership.
5. `schuss-canonical-json-v1` is implemented for the accepted value space and
   is deterministic across two fresh processes.
6. Every new record has stable ID, revision, and verified content hash, or a
   closed unresolved reference form where Task 004 explicitly permits deferred
   target resolution.
7. Device slots, gestures, feedback/displays, and physical I/O are separate and
   use stable local IDs.
8. The Gills profile contains no graph, instrument behavior, target, backend,
   or implementation content.
9. The instrument references the Gills profile and deferred exact graph target
   without copying either record.
10. Parameters, actions, displays, and state remain distinct.
11. The fixture maps one Gills knob to public `blend`, then `blend` to a graph
    public parameter; no device-to-graph shortcut exists.
12. Mapping transforms and unresolved facts are explicit and fail closed.
13. Labels, ordering, layout, provenance, and paths do not determine stable
    identity.
14. Structural validation is reported separately from deferred graph
    resolution and from all compiler, target, device, real-time, and audible
    evidence.
15. The validator is read only and emits deterministic structured diagnostics
    and a deterministic summary.
16. Positive and negative fixtures exercise all stated prohibitions.
17. No production graph/component/binding/target/backend/build schema or
    implementation is added.
18. No GUI, CLI, Java bridge, compiler, firmware, hardware, upload, flash,
    staging, commit, or push action occurs without separate approval.
19. Documentation identifies Task 005 as the completed device/instrument
    contract gate only after all tests pass and identifies Task 006 as next.
20. All unresolved design questions are listed with an owner and earliest later
    task.

## Decisions this task may make

- Exact v0 filenames and record organization for the two schema families.
- Opaque device-profile, instrument, slot, gesture, and facet ID syntax and
  allocation rules consistent with Task 004.
- The restricted canonical JSON implementation surface and schema-declared
  set/sequence metadata mechanism.
- The smallest controlled vocabularies needed for physical slots, gestures,
  feedback, public instrument facets, mappings, transforms, and explicit
  unresolved states.
- Whether the minimal reference uses one record per entity or a deterministic
  manifest plus records.
- Exact diagnostic codes and deterministic summary shape.
- Whether additional negative fixtures are necessary to prove a boundary.

## Decisions this task must not make

- Component-contract, graph, binding, target, backend, build, or operation
  schema fields.
- Complete Gills panel identity, pin mapping, electrical ranges, ADC resolution,
  display timing, firmware ownership, or hardware completeness without accepted
  evidence.
- Instrument DSP behavior, source selection, sound design, complete panel
  mapping, or release readiness.
- Graph public-interface semantics beyond the opaque deferred target needed by
  the `blend` mapping.
- Port conversion, rate/channel typing, resource budgets, backend selection,
  compiler lowering, runtime ABI, or artifact formats.
- A rule that turns unresolved facts into defaults or treats structural
  validation as graph, ARM, device, real-time, or audible evidence.
- Any change to accepted Task 004 decisions, frozen evidence, or Phase 4A IDs.

## Required completion report

When finished, report:

- files added or changed;
- final schema and record IDs/versions;
- device-profile and instrument ownership boundaries;
- canonicalization and content-hash rules actually implemented;
- the Gills slots and unresolved physical facts represented;
- public instrument facets and both `blend` mappings;
- positive and negative fixtures;
- structured diagnostic codes;
- tests and validators run, including deterministic fresh-process evidence;
- confirmation that frozen evidence and Phase 4A IDs were unchanged;
- explicit evidence levels reached and not reached;
- questions deliberately deferred with owners; and
- the recommended exact scope of Task 006.

Do not claim completion merely because the schema files exist. Check every
acceptance criterion and record concrete evidence in this task file. Do not
stage, commit, push, upload, flash, or access hardware without separate explicit
approval.

## Completion evidence

1. The task added `device-profile-v0.schema.json` and
   `instrument-v0.schema.json`; production records live under
   `contracts/device-profiles/` and `contracts/instruments/`. The normative
   boundary is in `docs/DEVICE_INSTRUMENT_CONTRACTS.md`, and the read-only
   implementation, tests, fixture matrix, and tool notes are under
   `tools/contracts/`.
2. The device record is `schuss-device-profile-000001` revision 1 with content
   hash
   `sha256:d6ad487f5444b1e39667ed8b4e43dde32ce7f06accac0be4fd5930c9b7eb82fe`.
   The instrument is `schuss-instrument-000001` revision 1 with content hash
   `sha256:3543d631ceb32b17be95c84eccc07d38ad29f1dc71c5a267b40306f69711bc53`.
3. Both schemas are Draft 2020-12 closed records. Every object shape rejects
   unknown fields, every array declares set or sequence semantics, entity and
   local IDs use opaque numeric allocation namespaces, revisions are positive,
   and exact record references use ID/revision/hash tuples.
4. `schuss-canonical-json-v1` rejects duplicate JSON members, floats,
   non-finite or oversized integers, timestamps, UUID-shaped random IDs, and
   absolute local paths. It omits only the record's own top-level
   `content_hash`, preserves nested reference hashes and sequence order, sorts
   set arrays by canonical element bytes, emits the restricted RFC
   8785-compatible UTF-8 JSON form, and hashes it with SHA-256.
5. The minimal Gills profile declares only
   `device-input-000001`: one absolute knob with a normalized authoring range.
   `unresolved-fact-000001` explicitly leaves its electrical/physical range
   and resolution unsupported, with code, affected subject, owner, earliest
   task, rationale, question, evidence status, and an empty accepted-evidence
   set. Empty gesture, feedback, display, and physical-I/O collections do not
   claim an exhaustive Gills census.
6. The schemas and positive tests independently exercise absolute, relative,
   and discrete controls; gestures; feedback outputs; displays; physical I/O;
   parameters; actions; read-only displays; state persistence/reset policy;
   device input and feedback mappings; and graph parameter, port, and action
   targets without adding those unsupported facts to the Gills production
   record.
7. The reference instrument owns public
   `instrument-parameter-000001` (`Blend`, exact decimal normalized `0` to `1`,
   default `0.5`). `device-mapping-000001` maps
   `device-input-000001` to that parameter with direct linear endpoints,
   control-update response, graph-owned smoothing, and instrument-owned soft
   pickup. `graph-mapping-000001` maps the same parameter to the declared
   deferred parameter target `graph-facet-000001`, semantic key `blend`.
8. The graph reference is a closed unresolved form naming intended
   `schuss-graph-000001` revision 1, `GRAPH_REFERENCE_DEFERRED`, owner
   `task-006`, reason `graph-schema-not-yet-implemented`, rationale, question,
   architecture-only evidence, and declared target set. It contains no graph
   content hash. The validator checks internal target/kind consistency and
   reports graph resolution as deferred; it always rejects a `resolved` claim
   because no accepted Task 006 resolver exists.
9. The negative fixture matrix contains 35 cases covering stale hashes;
   device/instrument/graph/target/backend/legacy/GUI layer embedding; direct
   device-to-graph mapping; unknown device, instrument, and deferred graph
   IDs; facet-kind mismatch; missing or incompatible domains/transforms,
   polarity, direction, pickup, owner, rationale, question, and unresolved
   evidence shape; duplicate drivers; false graph resolution; absolute paths,
   timestamps, UUIDs, label-derived IDs, unknown fields, and unknown controlled
   values. Focused tests additionally cover ID/revision collisions, stale exact
   device references, nonportable numbers, set-order invariance, and ordered-
   sequence rejection.
10. The validator emits stable structured codes including schema, portability,
    identity/hash, exact-reference, mapping, range, control-shape, and
    unresolved-fact failures. Valid output is one deterministic compact JSON
    summary with status `valid-with-deferred-graph`, one resolved device
    reference, one deferred graph, zero resolved graphs, and no diagnostics.
11. Ten Task 005 tests pass. Two fresh validator processes produce
    byte-identical summary output, and two fresh canonical-emission processes
    per record produce byte-identical output. Set reordering preserves
    canonical bytes; reversing the ordered transform points changes bytes and
    fails semantic validation. The stable summary output including its final LF
    has SHA-256
    `d7c25b851dc4ca1915bc91eb82e06e42a956e4834f898b0b1be44e4a16b01206`.
12. All 14 inventory tests and all six semantic-catalog tests pass. The raw
    validator reports 4,209 files and two retained issues; the resolved
    validator reports 3,602 objects, 1,157 graphs, and 3,180 issues; the Phase 3
    review validator reports 20 issue classes, 157 overload groups, 805 partial
    graphs, and 103 zombie groups; and the semantic validator still reports 26
    families and 38 implementations with every required pilot case.
13. The aggregate SHA-256 over all 27 frozen Phase 2, Phase 3, and review files
    remains
    `764b1c5a0b65ade0160dd0db049246f6cd754e58bb5a31073ae0f301eb78faa7`,
    and `git diff --name-only` for those roots is empty. The newline projection
    of all Phase 4A family and implementation IDs remains
    `c317f06ab7749c3d25f763e71355efdde1486d869c05127dc2eb1faa7f915cf7`;
    the overlay remains 26 families and 38 implementations and was not changed.
14. The evidence level reached is structural/schema validation for the two
    records, their hashes, the exact device reference, closed deferred-target
    consistency, and mapping semantics. Component/graph resolution is
    explicitly deferred. Backend lowering, artifact generation, ARM
    compile/link, connected-device execution, real-time/resource validation,
    and audible/listening validation are all `not-run`.
15. Deliberately deferred questions are recorded with owners in
    `docs/DEVICE_INSTRUMENT_CONTRACTS.md`: complete Gills hardware facts belong
    to the device-profile owner in Task 014 or a separate evidence task; the
    authoritative graph and public `blend` target belong to the graph owner in
    Task 006; graph type details belong to Task 006; and runtime, target,
    hardware, real-time, and audible evidence belong to later explicit tasks.
16. Task 006 should add only the component-contract, implementation-binding,
    and DSP-graph schemas and typed reference slice needed to create an
    authoritative graph record, prove its public `blend` facet, and replace the
    deferred reference with an exact ID/revision/hash tuple. Compute-target,
    backend/build records, operations, compiler lowering, GUI/CLI, firmware,
    and hardware behavior remain outside that next task.
17. `git diff --check` and repository-local link/path checks passed. No graph,
    component, binding, target, backend, build, operation, GUI, CLI, Java,
    `.axp`, C++, ARM, firmware, device, upload, flash, SD-card, stage, commit,
    tag, or push action occurred.
