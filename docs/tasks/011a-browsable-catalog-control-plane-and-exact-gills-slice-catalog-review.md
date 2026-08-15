# Task 011A: Browsable catalog control plane and exact Gills-slice catalog review

Status: complete. The user explicitly authorized Task 011A implementation on
2026-08-15. All acceptance gates passed locally on 2026-08-15. The completed
implementation was later committed and pushed under separate explicit user
authorization. The user then explicitly removed the post-task GitHub Actions
workflow on 2026-08-15; local validation remains the acceptance boundary.

Work in the Schuss repository. Work only on Task 011A after the user explicitly
approves running it.

This is a bounded catalog-projection, shared-operation, product-CLI, and
reviewed-curation task. It must establish the first source-agnostic
catalog discovery boundary shared by future CLI, GUI, and AI clients while
reviewing only the seven component roles needed by the first simple Gills
vertical slice. It must not define the new component contracts, bindings,
graph, instrument, build closure, backend expansion, or hardware evidence.

Before changing implementation, read completely:

- `AGENTS.md`;
- `README.md`;
- `docs/PROJECT_CONTEXT.md`;
- `docs/ARCHITECTURE.md`;
- `docs/SCHEMA_STRATEGY.md`;
- `docs/COMPILER_STRATEGY.md`;
- `docs/SEMANTIC_CATALOG.md`;
- `docs/TAXONOMY.md`;
- `docs/ROADMAP.md`;
- `docs/OPERATION_CONTRACTS.md`;
- `docs/COMPONENT_GRAPH_CONTRACTS.md`;
- `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`;
- ADRs 0003 through 0007;
- Tasks 001 through 010, including completion and preservation evidence;
- `docs/tasks/011-first-non-ui-gills-vertical-slice-roadmap-proposal.md`;
- the Phase 4A semantic overlay, schema, report, validator, and tests;
- the Phase 3 review packet and exact resolved observations named below;
- every accepted family companion, component contract, implementation
  binding, eligibility, build result, artifact, resource, and evidence record;
- accepted record sets `schuss-record-set-000001` through `000003` and their
  exact parent chains;
- `schemas/operation-request-v1.schema.json` and
  `schemas/operation-result-v1.schema.json`;
- `packages/schuss_core/control_plane.py` and its public dispatcher;
- the accepted Task 010 parser, locator, renderer, help, completion, fixtures,
  and tests; and
- all inventory, catalog, contract, operation, and CLI test entry points used
  by local validation.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Context

Task 010 is complete. Schuss has one accepted product CLI over four shared
Task 008 operations:

```text
records.validate
graph.inspect
build.resolve
graph.transact
```

The CLI is a thin projection over `dispatch_operation()`. Direct API,
`schuss op`, and ergonomic `--json` calls produce the same canonical operation
bytes for the same request and exact record set. Task 011A must preserve that
ownership boundary.

The semantic catalog is not yet browsable through the shared control plane.
Phase 4A contains a manually reviewed 26-family, 38-implementation pilot, but
the catalog overlay is a curation layer rather than the finished typed
component library. Some families have component contracts, bindings,
eligibility, or evidence; many are catalogued only. Clients need one derived
view that reports those differences without creating a second catalog truth.

The first Gills vertical slice also needs a bounded catalog review for:

- Square LFO;
- Cyclic Counter;
- four-step Pitch Sequencer;
- Sine Oscillator;
- Crossfader;
- State-variable Filter; and
- stereo Audio Output.

Task 011A combines that review with the shared browse/search boundary. It does
not create the six new component contracts or their legacy bindings. Those
belong to proposed Task 011B.

## Goal and why it exists

Create one deterministic, versioned, source-agnostic catalog projection and
two shared operations:

```text
catalog.search
catalog.inspect
```

Expose those operations through thin product-CLI commands, make all accepted
Phase 4A pilot families discoverable, and add only the missing catalog
identities required by the simple Gills slice.

This task exists so future CLI, Task 012 GUI, and future AI clients do not
invent separate category, search, provenance, readiness, or ordering truth.

## In scope

- A versioned catalog-projection contract and deterministic derivation from
  exact accepted semantic, provenance, and evidence inputs.
- An exact family-reference mechanism sufficient for
  `FAMILY_ID@REVISION` inspection without fabricating a Phase 4A family
  revision or changing a stable family ID.
- Additive versioned operation request/result schemas for `catalog.search` and
  `catalog.inspect` while preserving accepted v1 schemas and bytes.
- Shared dispatcher handlers for both catalog operations.
- Thin product-CLI parsing, exact locator resolution, deterministic human
  rendering, and exact canonical JSON passthrough for both operations.
- Function-first browsing and deterministic query matching.
- Filters for abstraction/form, signal facets, capabilities, technique,
  readiness, and an explicitly separate provenance facet.
- Exact family inspection through implementations, contracts, bindings,
  target/backend eligibility/evidence, and provenance observations when those
  records exist.
- Derived, evidence-bounded readiness states.
- Discoverability of all accepted 26 Phase 4A families.
- Exact reviewed catalog work for only the seven Gills-slice roles above.
- New catalog family/implementation identities only for the missing Square
  LFO, Cyclic Counter, and four-step-sequencer realization required by the
  slice.
- Positive, negative, determinism, preservation, client-equality, and CI
  fixtures and tests.
- Documentation and a completion report only after every acceptance gate
  passes.

## Out of scope

- New component contracts or implementation bindings beyond the already
  accepted Crossfader records.
- New binding eligibility, compatibility promotion, build request/result,
  artifact, resource, or evidence records.
- The production Gills graph, a new instrument record, or new Gills physical
  facts.
- Graph persistence, project/workspace persistence, autosave, locking,
  undo/redo, or publication.
- Backend lowering, `.axp`, source-map, Java generation, generated C++, ARM
  compilation/linking, packaging, or deployment.
- Authenticated Task 009 environment capture, repair, probe, or execution.
- GUI, drawer, graph-canvas, AI prompting, MCP, remote service, or client-
  specific catalog semantics. Representative callers are fixtures only.
- Complete 3,602-observation classification or the 150-250-family reviewed-
  core expansion.
- Dynamic shell completion from live records, fuzzy search, embeddings,
  recommendations, popularity, telemetry, or network search.
- Hardware access, device discovery, USB, SD-card writes, firmware action,
  upload, flash, runtime measurement, or listening.
- Mutation of frozen inventory/review evidence, Phase 4A overlay bytes,
  accepted Task 005-010 records/evidence, or pinned upstream checkouts.
- Staging, committing, publishing, or pushing without separate explicit
  approval.

## Inputs and frozen boundaries

Treat these as immutable inputs:

- all frozen Phase 2, Phase 3, and Phase 3 review artifacts;
- the complete Phase 4A overlay and its existing family/implementation IDs;
- all accepted Task 005-010 schemas, records, fixtures, operation results,
  diagnostics, artifacts, evidence, and preservation hashes;
- accepted operation request/result v1 schema bytes and the four canonical
  Task 008 operation results;
- every accepted Task 010 existing-command JSON/human result for the same
  invocation and selected record set;
- record sets `000001`, `000002`, and `000003` and their exact parent/member
  closures;
- the accepted Crossfader family companion, contracts, binding revisions,
  eligibility, build result, and evidence chain; and
- pinned source identities and commits in `catalog/sources.lock.json`.

Before implementation, record exact baselines for the protected inputs above,
the current full test counts, all validator stdout bytes, the four v1 operation
results, and every existing Task 010 domain-command output.

Adding catalog commands necessarily adds new parser/help/presentation code.
Existing command results and accepted semantic/evidence bytes must remain
unchanged. Root help and static completion may gain only the new fixed catalog
grammar; if they change, Task 011A owns new deterministic golden bytes and must
retain the Task 010 historical goldens as evidence rather than rewriting the
Task 010 completion record.

## Catalog projection architecture

### Authority and derivation direction

The projection is authoritative for catalog-operation behavior only because
its derivation algorithm and exact input closure are versioned. It owns no
independent family, contract, binding, readiness, compatibility, provenance,
or evidence truth.

```text
exact selected record set + exact Phase 4A/catalog successor closure
    -> validate exact references and canonical hashes
    -> derive catalog projection
    -> catalog.search / catalog.inspect
    -> CLI, future GUI, future AI callers
```

The projection must be reproducible from its inputs. A checked-in projection,
generated index, or cache is optional, but when present it is a derived,
content-addressed artifact with the exact derivation version and input-closure
hash. It is never manually edited and is never accepted when stale. Deleting a
cache must not change operation results.

Reverse indexes such as “contracts in family,” “bindings for contract,” and
“evidence for binding” are derived. Do not add child arrays to authoritative
family records merely for query convenience.

### Exact family references

Every family returned by search must be inspectable through an exact stable
ID/revision/content-hash reference. Task 011A must not pretend that a Phase 4A
overlay member already had an entity revision/hash when it did not.

Use an additive exact companion or successor mechanism that:

- retains every existing Phase 4A family ID;
- binds each accepted pilot family to the exact overlay member and overlay
  bytes;
- declares whether semantics changed;
- provides a truthful entity revision and content hash owned by the new
  companion/successor record, not fabricated legacy history;
- preserves the Phase 4A overlay byte-for-byte; and
- lets `FAMILY_ID@REVISION` resolve exactly inside the explicitly selected
  catalog/record closure.

Creating exact companions for accepted pilot IDs is not allocation of new
family identities. Only Square LFO and Cyclic Counter may receive new family
IDs in this task, subject to review. The four-step realization may receive one
new implementation ID but must not receive implementation ID
`schuss-implementation-000032`, which already names the distinct 16-step
observation 920.

### Projection entries

Each family projection entry must include or make derivable:

- exact family reference;
- display name, aliases, description, primary musical function, controlled
  technique/function tags, and abstraction level;
- implementation forms actually present;
- signal facets from exact component contracts when contracts exist;
- capability requirements/declarations from exact records when they exist;
- separate provenance facets and exact observation references;
- exact implementation, contract, binding, eligibility, result, artifact,
  and evidence references used to derive inspection/readiness output;
- explicit unresolved facts and diagnostics; and
- the projection/derivation version and exact input-closure identity.

Absence is meaningful. A missing contract, binding, eligibility, or evidence
record is reported as absent/not-established, never filled from names,
historical use, source location, family membership, or another implementation.

### Discovery facets

The discovery model is fixed:

- browse by primary musical function;
- filter by abstraction level and implementation form;
- filter by exact available signal-domain, rate, role, channel, and facet
  characteristics derived from contracts;
- filter by exact capability keys derived from accepted contracts, targets,
  backends, or eligibility records;
- filter by controlled technique/function tags;
- filter by derived readiness state; and
- optionally filter or inspect provenance as an explicitly named provenance
  facet.

Factory, Mutable Instruments, community, user, demo, legacy, repository, and
source IDs are provenance or review facets. They must never be primary musical
functions or silently affect readiness/rank.

Do not infer a signal facet from a legacy datatype when no component contract
exists. Do not infer a capability from family membership, source repository,
implementation form, or successful catalog resolution.

### Readiness derivation

Readiness is a derived set of exact states, not one manually curated scalar and
not necessarily a monotonic “best” status for an entire family. Inspection
must retain the implementation/contract/binding/target/backend subjects that
support each state.

At minimum derive and distinguish:

| State | Exact bounded meaning |
| --- | --- |
| `catalogued-only` | A reviewed family/implementation exists, but no exact component contract is established for the chain |
| `contracted` | An exact component contract references the family |
| `bound` | An exact implementation binding realizes the exact contract; this is not target support |
| `eligible` | An exact eligibility record supports the named binding/target/backend closure under its accepted evidence policy |
| `compile-proven` | A passing level-5 claim names the exact immutable result/artifact/binding closure |
| `device-tested` | A passing level-6 claim names the exact device/artifact subject |
| `real-time-tested` | A passing level-7 claim names the exact measured subject and method |
| `audible-tested` | A passing level-8 claim names the exact listening subject and method |
| `unresolved` | An exact unresolved fact or blocked requirement applies to the named chain |

Do not infer an earlier or later state from another evidence level. One
implementation's result does not promote all contracts or implementations in
its family. A family may truthfully expose several readiness chains at once.

### Deterministic matching and ordering

Define and document one language-neutral `schuss-catalog-match-v1` algorithm.
At minimum it must:

- index display name, stable family ID, description, aliases, controlled tags,
  and component-contract facet names when contracts exist;
- normalize ASCII case and whitespace by an exact documented algorithm;
- preserve non-ASCII code points exactly unless a pinned versioned Unicode
  normalization table is part of the contract;
- split the query deterministically and require every non-empty query token to
  match an indexed field;
- distinguish exact, prefix, and substring matches through a fixed score;
- apply filters as AND across facet kinds and OR within repeated values of one
  facet kind;
- use no stemming, locale collation, edit distance, fuzzy heuristic,
  popularity, filesystem order, hash-map order, or ambient database behavior;
  and
- break every score tie by fixed controlled-category order, normalized display
  name UTF-8 bytes, family stable ID, revision, and content hash.

An empty query is a valid browse request and returns all families satisfying
the filters. Pagination is unnecessary for the bounded pilot unless the task
adds a deterministic closed cursor contract with positive and negative tests.

## Shared operation contracts

### Additive versioning

Accepted `schuss-operation-request-v1` and `schuss-operation-result-v1` are
closed and immutable. Task 011A must add an explicit successor version rather
than add enum members or branches to the v1 schema files.

The dispatcher may accept both versions, but behavior is versioned:

- a valid v1 request for an existing operation returns the exact accepted v1
  result bytes;
- a successor request for any supported operation returns a successor result;
- `catalog.search` and `catalog.inspect` exist only in the successor contract;
  and
- an invalid or cross-version payload fails closed with the correct versioned
  result/adapter diagnostic.

Do not fork domain semantics into a second dispatcher. The public dispatcher
remains the only operation authority.

### `catalog.search`

The request contains:

- the successor schema/canonical profile;
- `operation: catalog.search`;
- an optional query string, with an empty string equivalent to browse-all;
- closed repeated filter collections for the approved facets; and
- no ambient path, clock, locale, random value, client identity, or mutable
  preference.

The result contains:

- exact selected catalog/record-set context;
- exact match-algorithm and projection versions;
- canonicalized query and filters;
- total match count;
- deterministically ordered result summaries; and
- structured diagnostics.

Each summary contains the exact family reference, display fields needed for
browsing, primary musical function, controlled tags, abstraction level,
implementation forms, derived readiness states, and a clear indication of
whether contract-derived signal/capability facets exist. Provenance summaries
remain separately labeled and never replace the primary function.

### `catalog.inspect`

The request contains one exact family ID/revision/content-hash reference
resolved from the explicitly selected context. The result exposes the complete
truthful chain available for that family:

```text
family
  -> implementations
  -> component contracts, when defined
  -> implementation bindings, when defined
  -> target/backend eligibility and evidence, when defined
  -> provenance observations
```

Every semantic child is an exact ID/revision/hash reference where its accepted
record family supplies one. Frozen observation locators remain snapshot-scoped
evidence references, not Schuss stable IDs. Inspection includes the exact
derived readiness chain and unresolved reasons per subject. It must not hide
duplicates, overloads, missing contracts, missing bindings, unsupported target
pairs, ambiguous selection, or absent evidence.

### Client-neutral equality

Provide fixture callers representing:

- direct in-process API use;
- the canonical `schuss op` machine boundary;
- the ergonomic product CLI;
- a minimal future-GUI caller; and
- a minimal future-AI caller.

The GUI/AI fixtures contain no presentation or prompting implementation. They
construct the same successor request and call the same public dispatcher. For
the same exact context/request, all five canonical result byte streams must be
identical, apart from the one final process LF where the existing adapter
contract requires it.

## Product CLI projection

Add exactly these command families:

```text
schuss catalog search [QUERY] [FILTERS] [--record-set MANIFEST] [--json]
schuss catalog inspect FAMILY_ID@REVISION [--record-set MANIFEST] [--json]
```

The fixed search filter surface should use explicit repeatable options for:

```text
--function KEY
--abstraction LEVEL
--form FORM
--signal-domain DOMAIN
--signal-rate RATE
--signal-role ROLE
--capability KEY
--technique TAG
--readiness STATE
--provenance SOURCE_OR_FACET
```

Exact spelling and option placement may be adjusted only to remain consistent
with Task 010 parser conventions; the final grammar must remain closed,
documented, and tested. There is no generic `--filter KEY=VALUE`, implicit
latest revision, display-name identity, ambient record discovery, fuzzy mode,
or client-side re-ranking.

Each catalog command constructs and dispatches exactly one successor operation
request through the public dispatcher. It must not import catalog validator
internals or derive, filter, rank, or reshape semantic results independently.

`--json` writes the exact canonical successor operation result plus one LF.
Human output is a deterministic Task 010-style rendering of the same result.
It preserves exact IDs, readiness limitations, unresolved states, diagnostic
order, and provenance/function separation. Human output may abbreviate long
descriptions only through fixed documented rules; it may not omit a readiness
limitation in a way that implies compatibility.

`FAMILY_ID@REVISION` is a CLI locator only. It resolves exactly one family
member inside the validated selected context and constructs the exact content-
hash reference before dispatch. There is no `latest`, display-name lookup, or
filesystem scan.

Keep Task 010 stdout/stderr and exit classes:

- `0` for successful dispatched results and successful help/completion;
- `1` for dispatched non-success results;
- `2` when usage, query/filter parsing, locator resolution, record-set loading,
  or input decoding prevents dispatch; and
- `3` for unexpected internal CLI failure.

If root help or static completion is extended, it must list only the fixed new
catalog grammar, perform no live catalog query, and receive new deterministic
Task 011A golden bytes.

## Exact Gills-slice catalog review

Review these frozen candidate observations only:

| Role | Observation | Required identity treatment |
| --- | ---: | --- |
| Square LFO | 209, `lfo/square` | allocate a new family and implementation only if review confirms a distinct low-frequency square-clock function |
| Cyclic Counter | 215, `logic/counter` | allocate a new family and implementation only if review confirms the bounded cyclic-counting function |
| four-step Pitch Sequencer | 918, `drj/seq/stepseq_4_pitch` | review as a possible new implementation of existing family `schuss-family-000022`; never reuse implementation `000032` |
| Sine Oscillator | 549, `osc/sine` | reuse family `000003` and implementation `000007` |
| Crossfader | accepted Task 006/009 chain | reuse family `000018`, mixed contract `000003`, and exact accepted binding/evidence revisions without modification |
| State-variable Filter | 159, `filter/multimode svf m` | reuse family `000009` and implementation `000015` |
| stereo Audio Output | 9, `audio/out stereo` | reuse family `000002` and implementation `000004` |

The task must preserve the distinction between observation 918 and observation
920. `schuss-implementation-000032` names the 16-step realization evidenced by
observation 920 and cannot identify the four-step realization. If observation
918 cannot truthfully join family `000022` without changing family meaning,
stop and report the family-identity decision instead of silently allocating or
reclassifying it.

For every slice entry, search and inspection must show exactly which of these
are present:

- catalog family and implementation membership;
- component contract;
- implementation binding;
- target/backend eligibility;
- compile/link evidence;
- device, real-time, or audible evidence; and
- unresolved facts.

Task 011A creates no missing contract, binding, eligibility, or evidence record
to improve those displays. The expected truthful contrast is valuable: the
accepted Crossfader chain has substantially more evidence than catalogued-only
slice candidates.

## Inputs and deliverables

Inputs are the accepted Tasks 001-010 repository closure, exact selected record
sets, Phase 4A pilot, Phase 3 observations named above, source lock, shared
dispatcher, and product CLI.

Deliverables are:

- this approved Task 011A contract, updated to active only after authorization
  and complete only after every acceptance gate passes;
- versioned projection schema/contract and deterministic derivation code;
- exact family companion/successor records needed to inspect the accepted
  pilot without fabricating history;
- only the approved missing Gills-slice catalog identities and review records;
- additive successor operation request/result schemas;
- shared `catalog.search` and `catalog.inspect` dispatcher handlers;
- thin product-CLI commands, human rendering, help, and static completion
  updates strictly needed for the new grammar;
- direct/API/process/CLI/GUI-fixture/AI-fixture equality cases;
- positive, negative, determinism, preservation, and local validation tests;
- updated catalog/operation/CLI documentation; and
- a completion report with exact hashes, counts, evidence limits, and next
  Task 011B boundary.

## Acceptance tests

Task 011A is accepted only if automated tests and recorded review evidence
prove all of the following:

1. All accepted Task 001-010 tests and validators pass before counting new
   Task 011A tests.
2. Frozen Phase 2/3/review and Phase 4A bytes remain unchanged.
3. Every accepted Task 005-010 semantic record, operation fixture/result,
   artifact, diagnostic, evidence record, and preservation hash remains
   unchanged.
4. Accepted operation request/result v1 schema bytes remain unchanged, and the
   four accepted v1 request/result byte streams remain exact.
5. Existing Task 010 domain-command JSON and human outputs remain exact for the
   same invocation/context. Any additive root-help/completion change receives
   a Task 011A-owned golden without rewriting Task 010 evidence.
6. The projection is reproducible from its exact input closure, uses a
   versioned derivation contract, and rejects stale or mismatched caches.
7. The projection contains no manually asserted reverse index, readiness,
   compatibility, provenance, signal, or evidence fact that can drift from its
   authoritative input record.
8. Every accepted 26-family Phase 4A pilot entry is discoverable and exactly
    inspectable without inventing a legacy family revision/hash.
9. Stable family IDs remain unchanged. Only reviewed missing slice identities
    are allocated, and the four-step realization does not reuse implementation
    `000032`.
10. Search supports primary function browsing and all approved filters with
    deterministic results and closed invalid-filter diagnostics.
11. Empty-query browse, exact ID, display-name, alias, description, controlled-
    tag, and contract-facet-name query cases behave under the documented match
    algorithm.
12. Query normalization, matching, scoring, filtering, and tie-breaking are
    byte-deterministic across fresh processes, record enumeration orders,
    working directories, locales, and hash-map insertion orders.
13. Functional category and provenance remain independent in schemas,
    projection values, filters, ordering, human output, and negative fixtures.
14. Factory, Mutable Instruments, community, user, demo, legacy, repository,
    and source labels are rejected as primary musical functions unless a
    separately accepted taxonomy record gives the same token an unrelated
    musical meaning.
15. Signal facets appear only from exact component contracts; legacy datatype
    observations do not silently create graph-safe signal claims.
16. Capability and readiness states appear only from exact accepted records
    and evidence, retain their exact subjects, and do not promote sibling
    implementations or whole families by association.
17. `catalog.inspect` exposes the complete available family -> implementation
    -> contract -> binding -> eligibility/evidence -> provenance chain and
    explicitly reports missing/unresolved links.
18. The Crossfader inspection truthfully exposes its accepted contract,
    binding, eligibility, and level-5 evidence chain without implying levels
    6-8 or support for other Crossfader variants.
19. Catalogued-only Gills-slice candidates are clearly distinguishable from
    Crossfader and do not acquire compatibility from membership or common use.
20. Successor operation schemas are closed, canonical, versioned, and reject
    v1/v2 payload mixing and unsupported members.
21. A valid v1 request still returns the exact v1 result; both catalog
    operations exist only through the accepted successor contract.
22. Direct API, `schuss op`, ergonomic `--json`, GUI fixture, and AI fixture
    return byte-identical canonical catalog results for the same exact request
    and context, except the existing process LF.
23. Each product catalog command calls the public dispatcher exactly once and
    does not import validator, catalog, or readiness internals.
24. CLI exact locator, record-set selection, stdout/stderr, exit, broken-pipe,
    interruption, human rendering, help, and static completion behavior are
    deterministic and tested at their reachable boundaries.
25. No command performs live completion, fuzzy search, ambient discovery,
    persistence, backend invocation, Java/ARM execution, network access, or
    client-specific semantic reshaping.
26. The complete-census and 150-250-family expansion remain absent; the only
    new reviewed scope is the exact seven-role slice.
27. No component/binding work beyond accepted Crossfader, graph/instrument,
    build/promotion, compiler, GUI/AI implementation, device, firmware,
    upload, flash, staging, commit, or push action occurs without separate
    approval.
28. `git diff --check` and the final clean-process local validation
    gate pass, and the completion report names every remaining proof gap.

## Decisions Task 011A may make

- Exact filenames and field shapes for the catalog projection and additive
  operation successor schemas.
- Whether a content-addressed projection is materialized or derived in memory,
  provided both obey the same versioned algorithm and exact closure.
- The exact additive companion/successor mechanism for Phase 4A family
  ID/revision/hash resolution, subject to the no-fabricated-history rule.
- New opaque stable IDs for the reviewed Square LFO, Cyclic Counter, and four-
  step realization only.
- Exact fixed option spelling consistent with the required catalog CLI facets.
- Exact `schuss-catalog-match-v1` score constants, normalization details, and
  stable diagnostic codes consistent with the fixed matching principles.
- Exact deterministic human catalog rendering and new Task 011A help/
  completion goldens.
- Additional focused negative fixtures needed to prove a stated boundary.

## Decisions Task 011A must not make

- New component signatures, seam maps, bindings, graph semantics, instrument
  behavior, target/backend eligibility, or build/evidence truth.
- A family-owned authoritative child index or manually curated readiness
  field.
- A rule that treats provenance, repository, source, or implementation form as
  musical function, quality, compatibility, or preference.
- A rule that treats catalog membership, a legacy observation, or a resolved
  Java export as a component contract or compile claim.
- Any mutation of accepted operation v1 schemas/bytes or a second dispatcher.
- Client-specific GUI/AI search, ranking, projection, or domain models.
- Persistent graph editing, project/workspace persistence, Task 012 drawer or
  canvas implementation.
- Task 011B contracts/graph/build closure or Task 011C backend/compiler work.
- General catalog expansion beyond the exact accepted pilot and seven-role
  slice.
- Task 009 authenticated execution.
- Hardware, firmware, device, upload, flash, runtime, real-time, or audible
  behavior.
- Staging, committing, publishing, or pushing without separate approval.

## Sequencing and later roadmap boundary

Task 011A is the immediate next task. After it is accepted:

- proposed Task 011B owns VS-02 through VS-04: component contracts, bindings,
  the hand-authored graph, the minimal Gills instrument, and an unresolved
  build/probe closure;
- proposed Task 011C owns VS-05 and VS-06: bounded legacy backend expansion,
  generated source, ARM compile/link, and exact evidence promotion; and
- VS-07 and VS-08 remain separately authorized hardware, real-time, and
  listening evidence tasks.

VS-07/08 are not prerequisites for Task 012. Task 012 should consume accepted
`catalog.search`, `catalog.inspect`, `graph.inspect`, and `graph.transact`
operations. It must not redefine discovery, readiness, provenance, graph
inspection, or transaction semantics in a GUI model.

No Task 011B, 011C, 012, GUI, AI, compiler, or hardware implementation may be
started merely because this Task 011A contract exists.

## Stop conditions

Stop and report rather than broaden or weaken Task 011A if:

- exact inspection of the Phase 4A pilot would require fabricating historical
  family revisions or rewriting the overlay;
- the projection cannot be derived without a reference/ownership cycle or
  manually maintained semantic duplicate;
- readiness cannot retain the exact implementation/contract/binding/target/
  backend/evidence subject that supports it;
- catalog operations require changing accepted v1 schema or result bytes;
- CLI catalog commands require a second dispatcher or client-side search truth;
- observation 918 cannot truthfully join family `000022` without changing
  family meaning;
- a new slice identity is ambiguous under the frozen evidence;
- deterministic matching would require locale, filesystem, clock, random,
  network, or unpinned Unicode behavior; or
- any accepted Task 001-010 protected byte or diagnostic meaning would have to
  change outside the explicitly additive Task 011A boundary.

Partial investigation may be documented, but the task remains incomplete and
no unsupported family membership/readiness claim is published.

## Completion report requirements

On completion, update this status to complete and record:

- pre-existing and final test counts and every validator summary/hash;
- accepted Task 001-010 preservation hashes and post-task equality checks;
- exact v1 operation-schema/result preservation evidence;
- projection schema/version, derivation algorithm, input-closure identity,
  materialization/cache choice, and determinism hashes;
- exact family companion/successor mechanism and proof no Phase 4A history was
  fabricated;
- final `catalog.search` filters, matching/scoring/tie-breaking algorithm, and
  positive/negative matrix;
- final `catalog.inspect` chain and readiness derivation matrix;
- all 26 pilot discovery/inspection evidence;
- each Gills-slice family/implementation identity decision, including the
  observation 918 versus implementation `000032` proof;
- successor operation schema IDs/hashes and every direct/process/CLI/GUI/AI
  equality hash;
- exact catalog CLI grammar, output/help/completion goldens, stdout/stderr and
  exit matrix;
- confirmation that existing CLI operations/results remained unchanged;
- explicit confirmation that no new component/binding beyond Crossfader,
  graph, instrument, build/promotion, backend/compiler, GUI/AI implementation,
  authenticated Task 009 execution, device, firmware, upload, flash, staging,
  commit, or push occurred; and
- every remaining Task 011B, 011C, Task 012, device, real-time, and audible
  proof gap.

## Completion report

### Local validation and final gates

The complete local inventory, catalog, contract, operation, CLI, validator,
and `git diff --check` command set passed in fresh processes. The user later
removed the optional GitHub Actions workflow as unnecessary at this stage; it
is not part of the accepted Task 011A boundary.

Pre-task counts were 14 inventory, 6 catalog, and 117 contract tests. Final
counts are 14 inventory, 6 catalog, and 135 contract tests; Task 011A adds 18
focused contract/operation/CLI tests. All 155 final tests passed. Final
validator stdout is:

| Validator | Summary | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| raw inventory | 4,209 files, 2 retained issues, `ok: true` | 41 | `3a9ba2256592972c3e104b21b821d9befa9ac2c75c8f69af63020b4765271e80` |
| resolved inventory | 3,602 objects, 1,157 graphs, 3,180 issues, `ok: true` | 62 | `bb435d07670ccf4ce7dad5182a75ad9bc2c18dedb5c0b184ce9d6cca3691e738` |
| Phase 3 review | 20 issue classes, 157 overload groups, 805 partial graphs, 103 zombie groups, `ok: true` | 103 | `faf90cb359effe3b24f2c68ca66086d1acee813acf0ceacb7c3218e7e9ae62f4` |
| Phase 4A semantic catalog | 26 families, 38 implementations, 13-category coverage | 1,725 | `8d21352c7265a50a93646f93f9696e4b02ebcfbab3443da53a2cc47c8fc34238` |
| device/instrument | 1 device, 2 instruments; 1 graph resolved and 1 historical deferred | 684 | `254a77c534c911da759a21e438544b4b0e69e16093307e0fc269a0857b6d3af6` |
| component/graph | 1 family, 3 contracts, 3 bindings, 1 graph; historical deferred instrument retained | 1,069 | `d295106d38cdf9075a85d9e1a803b5df23e3ffbbe934dceb3cec9194b59ce6af` |
| target/backend/build | exact Task 007 counts; levels 1-2 passed and 3-8 not run | 1,964 | `7a898b3409e5ad7ef02eab1246f87756cc2af7cbd512d72f9a5eb43b1573a3a2` |
| Task 009 prerequisite | accepted 18/19 and prospective 23/25 record/schema counts; retained probe not authorized/not run | 1,930 | `3f8f3df84fd47ab51441ec6b3d30abc43fcfd18b2a69cffc6a508f5f0fe08a8b` |
| Task 011A catalog | 28 families, 41 implementations, 26 pilot families, 7 slice roles, no levels 6-8 | 1,162 | `da60081e4fed9e07f243ec906f8e9410c3c88385cc989286d76c0d373ae44c80` |

The pre-task manifest covered 301 tracked files. The final reconciliation found
288 byte-identical files, 13 intentional Task 011A code/document/test changes,
and no missing file. All frozen inventory/review/Phase 4A bytes and all accepted
Task 005-010 schemas, records, fixtures, artifacts, diagnostics, and evidence
outside those scoped presentation/control-plane files remain byte-identical.
The Phase 4A overlay remains 60,870 bytes with SHA-256
`497a27d295d0ccda799848ac6fcba245139ca29156f509431b7cb7522d791858`.

### Exact catalog closure and projection

The exact corpus is `contracts/catalog/task011a-corpus-v1.json`: 20,750 bytes,
file SHA-256
`c7a65e485a960bcc868be5fd5ce10309a29158538fb9967017c47a10550dd2cf`,
and content hash
`sha256:725d7ba0df11ed15ec2c8a35e8463e246d48fa544c72fa3067c343fadbeb850d`.
Successor record set `schuss-record-set-000004` revision 1 has content hash
`sha256:c0ce942e6e65a79197a88e795044beea5ede3c0299f2926ccd445016ba9cd982`;
its file is 24,649 bytes with SHA-256
`5665e930da3213d82da321d0d2716cf65ccc3fd70ee8486c986194777fe8215d`.

The projection is derived in memory, not materialized or cached. Version
`schuss-catalog-projection-v1` under match algorithm
`schuss-catalog-match-v1` has exact input-closure hash
`sha256:291b695cc11339da44a0ddc473f948c8154f111f31e3b37ea2d1d1644647b3a4`.
Its 53,127 canonical bytes hash to
`d85345fd72023f7b1b5e3159dacb49b25095b1ff508153e0a42a8a5d7bdf0895`.
Repeated generation and reordered record enumeration produce the same bytes;
fresh-process tests vary cwd, locale, and `PYTHONHASHSEED` without changing the
result.

`catalog-corpus-v1` binds the frozen overlay byte hash, each companion's exact
canonical overlay-member hash, and each reviewed observation's canonical hash,
portable source ID/path, source byte hash, legacy ID, and durable UUID. Twenty-
five nested exact companion records cover pilot families other than
Crossfader; Crossfader reuses the accepted Task 006 exact family record. These
are explicitly successor companions and never claim to be historical Phase 4A
revisions. The generator validates every child content hash and only the three
approved new implementation IDs.

### Search, inspection, and evidence truth

`catalog.search` accepts an optional query and repeatable filters for function,
abstraction, form, signal domain, signal rate, signal role, capability,
technique, readiness, and provenance. Within-kind values are ORed and
different kinds are ANDed. Unsupported values fail closed. Tests cover empty
browse, exact family ID, display name, alias, description, controlled tag,
contract facet name, every filter, combined filters, and provenance/function
separation. Factory/provenance is rejected as musical function.

Normalization performs ASCII-only case folding and ASCII-whitespace collapse,
preserving every other code point. Every query token must match. Per-token
scores are exact 300, prefix 200, and substring 100. Ties use fixed Phase 4A
category order, normalized UTF-8 display bytes, family ID, revision, and
content hash. No stemming, fuzzy match, embedding, locale collation,
popularity, clock, random, filesystem order, or network input exists.

`catalog.inspect` returns each implementation's exact observation/provenance,
contract, binding, eligibility, target, backend, build-result, artifact, and
evidence references plus unresolved facts. Signal facets come only from exact
component contracts. `catalogued-only`, `contracted`, `bound`, `eligible`,
`compile-proven`, `device-tested`, `real-time-tested`, `audible-tested`, and
`unresolved` are derived per implementation. The relevant exact references
remain beside each state chain; no sibling or whole-family promotion is made.

The accepted mixed-rate Crossfader implementation `000028` is contracted,
bound, eligible, compile-proven, and unresolved. Exact inspection exposes its
contract, two binding revisions, two eligibility revisions, both target/backend
revisions, exact build result, seven build artifacts, and the passing evidence
claims. It does not claim levels 6-8. New implementations `000039`, `000040`,
and `000041` are only catalogued and unresolved.

All 26 Phase 4A family references were individually dispatched through
`catalog.inspect` and matched their exact projection entries. The seven-role
identity result is:

| Role | Family | Implementation | Evidence decision |
| --- | --- | --- | --- |
| Square LFO | `000027` new | `000039` new | observation 209 confirms distinct low-frequency square/clock function |
| Cyclic Counter | `000028` new | `000040` new | observation 215 confirms bounded rising-edge cyclic counting |
| four-step Pitch Sequencer | reuse `000022` | `000041` new | observation 918 joins the generalized pitch-step-sequencer presentation |
| Sine Oscillator | reuse `000003` | reuse `000007` | observation 549 |
| Crossfader | reuse `000018` | reuse `000028` | observation 460 and accepted Task 006/009 chain |
| State-variable Filter | reuse `000009` | reuse `000015` | observation 159 |
| stereo Audio Output | reuse `000002` | reuse `000004` | observation 9 |

Observation 918 is pinned only to new four-step implementation `000041`.
Existing implementation `000032` remains pinned only to the distinct
sixteen-step observation 920.

### Operation, client, and CLI evidence

Accepted v1 files remain exact:

- operation request v1: 8,302 bytes,
  `975a5374c04e1e9282d963ef470284ac704e1a66e776054cd27750aacb7f4ce1`;
- operation result v1: 1,455 bytes,
  `e10f60568c26d646cd17bc167460f08a81fe4aeb104ce3ce7f31fefbb2b14c5e`;
- Task 008 operation requests: 2,136 bytes,
  `cb21063005fdb18abd4362f3537b7286eb94db23d2c1d2963eac247616fac99a`;
  and
- Task 010 golden fixture: 2,483 bytes,
  `2373c57ed53676470eb077b79156c4f7f44b1e21c4f1f3d6bd98393e8c2fc146`.

The four accepted v1 result hashes remain: `records.validate`
`cb0735df54a0baade54c8cc16807a94771c1e7cbbc93a6710291084fcb656543`,
`graph.inspect`
`88d5a4f52f4d3bfc31ff361ebe3a8835860e7b5890e9c9791be21cd86c179ee1`,
`build.resolve`
`643a063d1553ff000a4776fd2a4eb5b7d300c0ba34ccbb977f3babd78abf7de9`,
and `graph.transact`
`6def7986739604e807b3b95e26513fe6a9a41cd1d827ea4e417809b9027c48b8`.
The same Task 010 domain JSON/human invocations remain exact. Only allowed root
help/static completion changed; their historical fixture was not rewritten.

Successor schema hashes are:

| Schema ID | Bytes | SHA-256 |
| --- | ---: | --- |
| `catalog-corpus-v1` | 8,859 | `66515307ba8a93e5cfb08817f38cad94a565a4ec5cea065b52408653a755cc78` |
| `catalog-projection-v1` | 7,093 | `aaea46a4f7faa182e315a4fb510c6f31e04d6c27d6bcdea07880d9451f584547` |
| `operation-request-v2` | 3,572 | `3aa986982c63693f1663b958e460e77ccd1b562e84c4bb30d112d7a7a94827cd` |
| `operation-result-v2` | 1,486 | `bb223a50ca3430518a9d35f6050f3a625e0987174aad205a76a4c9b78d8a65b8` |

Catalog v2 rejects v1/v2 mixing and unsupported members. A v2 request against
a v1-only record set returns a deterministic `invalid-request` v1 result
rather than an internal adapter error.

For the exact search fixture, direct API, raw `schuss op`, ergonomic CLI,
future-GUI fixture, and future-AI fixture produce 1,522 canonical bytes with
SHA-256
`2d79eb3ff9ebc8af3c9e28421a8cf0dd2b38ced6917f4e2d0be5717ddd1c589e`;
the process LF yields 1,523 bytes and
`b69d23004fc79fccacbc8270b0bd91c0be1e563be074c63e7ea12fac6f6779ed`.
The inspect fixture produces 7,652 canonical bytes with
`95ac6a9f91c34fd0240a511c23ecaf2c0f8c0979d2c76ea036cb0dd16a5322b7`;
the LF form is 7,653 bytes and
`240adb006bb5275da8f64288e82e3593f426be36b076a9a877df083bb09b5517`.

The CLI grammar is:

```text
schuss catalog search [QUERY]
  [--function VALUE] [--abstraction VALUE] [--form VALUE]
  [--signal-domain VALUE] [--signal-rate VALUE] [--signal-role VALUE]
  [--capability VALUE] [--technique VALUE] [--readiness VALUE]
  [--provenance VALUE] [--record-set MANIFEST] [--json]
schuss catalog inspect FAMILY_ID@REVISION [--record-set MANIFEST] [--json]
```

Catalog commands default to exact record set `000004`; all old commands retain
default `000001`. Each catalog command calls the public dispatcher exactly
once. Exact family locators are resolved before dispatch; malformed, implicit,
`latest`, display-name, absent, ambiguous, and wrong-context inputs fail at
exit 2 without stdout. Successful human/JSON operations exit 0; dispatched
invalid operations exit 1 with canonical stdout; unexpected contained adapter
faults exit 3. Broken pipe and interruption exit 1. Help and static completion
exit 0 without loading records. Human output identifies exact record-set,
catalog, family, implementation, readiness, chain, and diagnostic values.

Task 011A golden fixture
`tools/contracts/tests/fixtures/task011a-cli-golden-hashes.json` is 1,477 bytes
with SHA-256
`f4530b7e13e1275df11fdb17a99abaf70758547db36d1025e666cb1aa8c94ed4`.
It pins root/catalog/search/inspect help; Bash/Zsh/Fish completion; and search/
inspect human and canonical-JSON process output. Help hashes are root
`f0cfe4c99ace639652c8d127c1def34055510cb8cfcf1990f86427728196aa93`,
catalog `c65555efb0afbde93d56d74c8041af991ac68f7ff712dd847dd84bc103c8691c`,
search `ca8108bfdc891e57e125d36ee3e510ae315bd81b1b04a9bea5197138413e2534`,
and inspect
`2463da75a47daebd2fc55f7eef33706efe1e91855a6fb72331d5e69e0bda290b`.
Completion hashes are Bash
`54b604a3ca4cfd768bc20e21744eb19a175906767e4cdf2f46c2441468c94c51`,
Zsh `32b548eb3b28b89c84c193bc9de32f1ef2c92ea3d7d1393471fb9fc5e1067f2c`,
and Fish
`17cc15956e4a5b392e209e328badf7fd51fdcb0c1534610f00daf0dff6b1aeda`.

### Scope confirmation and remaining proof gaps

No new component contract or implementation binding was created. No graph,
instrument, build/promotion record, backend/compiler implementation, GUI/AI
implementation, authenticated Task 009 execution, Java/ARM invocation, device,
firmware, upload, flash, or SD-card action occurred. During the bounded
implementation, no staging, commit, publication, or push occurred before the
later separate publication authorization. No command adds persistence, live
completion, fuzzy search, ambient discovery, backend execution, network access,
or client-specific catalog truth.

Proposed Task 011B still owns six target-independent component contracts and
exact bindings, the authoritative seven-node graph, minimal Gills instrument,
and unresolved build closure. Proposed Task 011C still owns bounded legacy
backend expansion, generated source, and ARM compile/link evidence. Task 012
still owns the object drawer and canvas as clients of these accepted
operations. Connected-device level 6, real-time level 7, and audible level 8
remain separately authorized later evidence, not Task 011A claims.
