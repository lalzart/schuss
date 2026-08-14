# Task 004: Schema and compiler contract strategy

Status: complete. This remains the accepted architectural foundation. Task 005
has since completed the device/instrument contract gate; Task 006 is next.

Read `AGENTS.md`, `README.md`, `docs/PROJECT_CONTEXT.md`,
`docs/ARCHITECTURE.md`, `docs/SEMANTIC_CATALOG.md`, `docs/TAXONOMY.md`,
`docs/PARAMETER_MODEL.md`, `docs/LEGACY_STRATEGY.md`, `docs/ROADMAP.md`, all
accepted ADRs, Tasks 001-003, and the Phase 4A pilot report and overlay schema
before making changes. If this task conflicts with an accepted decision,
report the conflict rather than changing the architecture.

## Goal and why it exists

Define the overall Schuss schema architecture, identity hierarchy, reference
direction, type boundary, and compiler stages before individual production
schemas or compiler code are implemented.

Phase 4A established stable musician-facing family and concrete implementation
identity, but a family may group implementations with different public
interfaces. A graph therefore cannot use a family, legacy path, `.axo`
observation, or backend implementation as its node type. Task 004 introduces
the missing target-independent component-contract layer and fixes how later
Gills, graph, CLI, and compiler work must depend on it.

## In scope

- A normative schema strategy and dependency direction.
- A normative transitional and future compiler strategy over one authoritative
  Schuss graph.
- Durable ADRs for family/contract/binding identity, graph references and
  implementation selection, and build-evidence separation.
- The required shape of a future port and interaction type system, including
  explicit conversion responsibility.
- An illustrative crossfader domain slice exercising family, contract,
  implementation, graph, compound, instrument, Gills, target, backend, and
  evidence boundaries.
- A bounded implementation sequence beginning with Task 005.
- Concise links and terminology repairs in existing architecture documents.

## Out of scope

- Production JSON Schemas for the new domain records.
- A complete port-type vocabulary or optimizing DSP IR.
- Full legacy-census classification or immediate Phase 4B expansion.
- Graph mutation operations or shared-operation protocol implementation.
- CLI, GUI, object drawer, canvas, compiler, or adapter implementation.
- `.axp`, C++, object, firmware, or binary generation.
- ARM compilation/linking, device access, upload, flash, SD-card writes, or
  audible validation.
- Replacing the Ksoloti Java resolver, ARM toolchain, firmware, or runtime.
- Selecting preferred implementations without evidence.
- Rewriting Phase 4A family or implementation IDs or any frozen inventory or
  review artifact.
- Staging, committing, tagging, or pushing.

## Inputs

- The accepted architecture and ADRs 0001-0004.
- The frozen Phase 2 and Phase 3 snapshots and Phase 3 review packet.
- The Phase 4A semantic-catalog overlay, schema, validator, and pilot report.
- The requirements in the attached Task 004 brief.

## Deliverables

- `docs/SCHEMA_STRATEGY.md`.
- `docs/COMPILER_STRATEGY.md`.
- ADRs 0005-0007.
- `docs/reference/CROSSFADER_DOMAIN_SLICE.md`.
- This task contract and completion evidence.
- Focused updates to the project context, architecture, semantic catalog,
  parameter model, legacy strategy, roadmap, README, schema index, and ADR
  index.

## Decisions this task may make

- Planned schema-family boundaries, owners, and one-way reference direction.
- Stable-identity, entity-revision, schema-version, content-hash, migration,
  and unresolved-data rules.
- The minimum future port-type dimensions and strict conversion policy.
- Compiler stage boundaries, derived artifacts, diagnostic traceability, and
  evidence vocabulary.
- The exact bounded order and ownership of Tasks 005 onward.
- Illustrative field names and example IDs that are explicitly non-production.

## Decisions this task must not make

- Complete field-level production schemas or final controlled vocabularies.
- The complete target-capability model or Ksoloti Core resource limits.
- A stable optimizing IR or graph mutation API.
- A new firmware ABI, replacement runtime, or final direct-C++ design.
- Automatic implementation preference, implicit type coercion, or inferred
  compatibility unsupported by named evidence.
- Changes to existing Phase 4A identity allocation or frozen evidence.

## Accepted architectural outcome

The normative identity and reference hierarchy is:

```text
implementation binding -> legacy observation (evidence only)
implementation binding -> component contract -> catalog family

DSP graph -> exact component-contract revisions
instrument -> device profile + DSP graph
build request -> graph/instrument + compute target + backend
build result -> request + selected bindings + artifacts
evidence claim -> build result/stage/artifact
```

The arrows mean “references”; they do not imply ownership in the opposite
direction. In particular, graphs never reference families or implementation
bindings, and catalog families never own compiler choices.

Phase 4A `schuss-implementation-*` IDs remain the stable identities of their
concrete realizations. A later compiler-facing binding record will add the
required exact contract reference to the same identity; it will not rewrite
the Phase 4A overlay or allocate a replacement merely because the schema grew.

Detailed normative rules are in `docs/SCHEMA_STRATEGY.md` and
`docs/COMPILER_STRATEGY.md`. ADRs 0005-0007 record the durable decisions.

## Deferred questions and owners

| Question | Recommended owner | Earliest task |
| --- | --- | --- |
| Exact Gills control IDs, gesture vocabulary, resolution, ranges, and feedback capabilities | Device-profile owner | Task 005 |
| Minimum instrument state, mapping transforms, and graph-target reference fields | Instrument owner | Task 005 |
| Complete scalar, stream, event, buffer, unit, range, and cardinality vocabularies | Component-contract and graph owner | Task 006 |
| Whether a contract revision needs a compact compatibility class in addition to explicit directed compatibility claims | Component-contract owner | Task 006 |
| Exact representation of transparent-compound recursion and public endpoint mappings | Graph owner | Task 006 |
| Ksoloti Core memory regions, ABI identity, toolchain lock, runtime assumptions, and capability vocabulary | Compute-target and legacy-backend owners | Task 007 |
| Resource-estimate confidence and measurement record shapes | Build-evidence owner | Task 007 |
| Shared operation names, mutation transactions, conflict handling, and protocol transport | Headless-operation owner | Task 008 |
| Exact supported Schuss-to-legacy subset and Java resolver invocation envelope | Legacy-backend owner | Task 009 |
| Direct frontend normalized-IR instruction set, scheduling, optimization, and ABI lowering | Compiler owner | Task 013 or a later bounded task |
| Phase 4B family expansion policy after contract adoption | Catalog owner | Task 011 |

## Acceptance tests

1. Existing raw, resolved, Phase 3 review, and semantic-catalog tests and
   validators pass.
2. Every file in the frozen Phase 2, Phase 3, and review roots is byte-identical
   to the pre-task hash set.
3. The Phase 4A family and implementation ID projection is byte-identical to
   the pre-task projection.
4. The schema strategy names every planned authoritative contract and its
   owner.
5. Reference directions are explicit and have no circular semantic ownership.
6. A graph references an exact component-contract revision and never only a
   family, implementation, category, path, or legacy observation.
7. Several typed component contracts may reference one catalog family.
8. An implementation binding cannot redefine the contract it realizes.
9. Primitive, transparent compound, opaque native, and target-service
   realizations can coexist below component-contract identity.
10. Ports, parameters, attributes, actions, displays, device mappings, and
    instrument mappings remain distinct.
11. Legal and illegal implicit conversions and explicit adapter ownership are
    stated.
12. Gills, instrument, graph, Ksoloti Core, and backend identities remain
    independent.
13. The transitional compiler emits `.axp` only as a deterministic boundary
    artifact.
14. The future compiler consumes the same authoritative graph without making
    Java or `.axp` authoritative.
15. Build results and evidence cannot silently mutate catalog classification
    or compatibility truth.
16. Diagnostics trace through graph, node, contract facet, compound path,
    implementation binding, target, backend, and stage.
17. The reference slice exercises every required boundary and is unmistakably
    illustrative.
18. No out-of-scope implementation, generation, compiler, firmware, device,
    or Git publication action occurs.
19. Project documentation identifies Task 004 as the current accepted
    architectural gate.
20. Every unresolved design question has a recommended owner and later task.

## Exact Task 005 scope

Task 005 should implement only a minimal Gills device-profile schema and a
minimal instrument schema plus fixtures and a read-only validator.

It should define opaque identity/revision/hash envelopes; physical control,
gesture, display, feedback, and I/O slots required by the reference slice; an
instrument with public parameters/actions/displays/state; device-to-instrument
and instrument-to-graph mapping records; and an opaque exact graph reference
whose target is validated only after the graph schema exists. It should prove
deterministic serialization, stable IDs independent of labels/layout, explicit
mapping transforms, and failure on cross-layer embedding.

It must not define DSP node/port schemas, implementation bindings, compute
targets, backends, build records, graph operations, Gills firmware, panel
scanning, GUI/CLI behavior, or compilation. The reference fixture should map
one Gills knob to an instrument `blend` parameter and that parameter to the
illustrative graph target without copying graph structure into either device
or instrument records.

## Completion evidence

1. The existing suites passed: 14 inventory tests and six catalog tests. The
   raw validator reported 4,209 files and two retained issues; the resolved
   validator reported 3,602 objects, 1,157 graphs, and 3,180 issues; the Phase
   3 review validator reported 20 issue classes, 157 overload groups, 805
   partial graphs, and 103 zombie groups; and the semantic validator reported
   26 families and 38 implementations with all required difficult cases.
2. Two semantic-validator runs produced the same SHA-256 summary digest,
   `8d21352c7265a50a93646f93f9696e4b02ebcfbab3443da53a2cc47c8fc34238`.
3. The pre/post aggregate SHA-256 over all 27 files in the Phase 2 raw, Phase 3
   resolved, and Phase 3 review roots remained
   `764b1c5a0b65ade0160dd0db049246f6cd754e58bb5a31073ae0f301eb78faa7`.
   `git diff --name-only` for those roots was empty.
4. The pre/post projection of all Phase 4A family and implementation IDs
   remained
   `c317f06ab7749c3d25f763e71355efdde1486d869c05127dc2eb1faa7f915cf7`.
   The existing overlay still contains 26 families and 38 implementations.
   A pre-existing rationale edit in the dirty overlay was preserved; Task 004
   did not rewrite the overlay.
5. `docs/SCHEMA_STRATEGY.md` names every planned authoritative record family,
   its owner, permitted references, prohibited ownership, exact-reference
   envelope, revision/hash rules, migration behavior, unresolved states, JSON
   strategy, and implementation sequence.
6. Its dependency diagram and acyclic exact-closure rule establish the
   one-way family, contract, graph, binding, instrument, device, target,
   backend, build, artifact, and evidence relationships. The only
   revision-stratified evidence path must terminate in a strictly earlier
   binding revision.
7. Graph nodes pin exact component-contract ID/revision/hash tuples. The
   strategy prohibits family, category, label, implementation, observation,
   path, `.axo`, `.axs`, and `.axp` node identity and demonstrates three
   contracts in one Crossfader family.
8. Bindings require a complete type-compatible realization map and cannot
   alter a contract. Legacy, generated, transparent compound, native C/C++,
   and target-service forms coexist below contract identity.
9. Ports, parameters, attributes, actions, displays, device mappings, and
   instrument mappings remain distinct. The minimum port dimensions and the
   exact-match/range-subset/optional-input legal cases are stated alongside
   the illegal implicit conversion list and explicit-adapter rule.
10. `docs/COMPILER_STRATEGY.md` defines the common ten-stage compiler boundary,
    deterministic binding selection, compound elaboration, dependency/resource
    planning, legacy and direct paths, artifact hashing, diagnostic source
    maps, and eight independent evidence levels.
11. The legacy path makes `.axp` a generated boundary artifact before isolated
    Java resolution/code generation. The future path consumes the same graph
    through a derived normalized representation and direct C++ frontend without
    Java or `.axp` authority.
12. Build results own exact inputs, selected bindings, stage outcomes,
    diagnostics, and artifact hashes. Separate evidence records reference
    immutable results/stages/artifacts; catalog promotion requires a reviewed
    new semantic revision.
13. Structured diagnostics retain graph, node, contract/facet, compound path,
    binding, target, backend, toolchain/artifact, and stage traceability.
14. `docs/reference/CROSSFADER_DOMAIN_SLICE.md` is explicitly illustrative and
    exercises the existing Crossfader family, three typed contracts, retained
    legacy implementation IDs, two sources, explicit rate adapter, audio
    output, compound parameter exposure, instrument `blend`, Gills knob,
    Ksoloti Core request, legacy selection, separate evidence, and future
    direct backend.
15. ADRs 0005-0007 record family/contract/binding identity, graph reference and
    binding selection, and build-evidence separation. Existing architecture,
    context, catalog, parameter, legacy, roadmap, README, schema index, and ADR
    index point to the accepted boundary.
16. The deferred-question table assigns every open design area to a named
    owner and earliest task. The exact Task 005 scope is minimal Gills
    device-profile/instrument schemas, fixtures, and read-only validation.
17. A local-reference check passed for 37 links/paths across the 14 changed or
    new primary documentation files. `git diff --check` passed, the scan found
    no absolute local paths in new Task 004 artifacts, and no Java source exists
    outside `legacy/ksoloti-bridge/`.
18. No production schema, graph operation, compiler, adapter, `.axp`, C++, ARM
    artifact, firmware, device operation, tag, or push was performed. The Task
    004 documentation was staged and committed only after separate user
    approval.
