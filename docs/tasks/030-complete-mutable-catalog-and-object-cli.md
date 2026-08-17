# Task 030: Complete Mutable-derived catalog cohort and object CLI

Status: accepted and complete on 2026-08-17. All fifteen Task 030 acceptance
criteria are satisfied at structural/catalog provenance levels 1-2; levels
3-8 remain `not-run`. The required one-shot repository aggregate ran 394 tests
and remains non-green only for three pre-existing historical checks outside
Task 030; no Task 030 test failed.

## Goal and why it exists

Catalog every member of the exact source-attributed Mutable cohort frozen by
Task 027 and make individual implementations directly discoverable from the
shared CLI/application boundary. This exists because Task 027 proved 56 exact
Mutable-derived source entries but catalogued only six; the default catalog
CLI still selects the older Task 023 context and searches families rather than
individual implementation objects.

"All" is exact and bounded here: the 56 Task 027 entries carrying
`mutable-instruments-derived`. The other 16 extended-library entries remain
inventory-only because Task 027 found no exact Mutable attribution for them.

## Exact baseline

The parent is `schuss-record-set-000022@1`. Its selected catalog contains 60
families and 83 implementation records. Task 027's immutable source review
contains 72 entries: 56 attributed, six already catalogued, 50 tagged
candidates, and 16 unattributed inventory-only entries. Task 028's twenty-item
direct palette and Task 029's machine layer remain independent and unchanged.

## In scope

- A reviewed successor disposition for all 72 Task 027 source entries.
- Exactly 50 new catalog implementation records for the attributed candidates,
  using allocations `schuss-implementation-000112@1` through `000161@1`.
- Function-first family curation for those implementations: reuse an existing
  family only for exact reviewed equivalence and otherwise allocate opaque
  families beginning at `schuss-family-000061@1`.
- Catalog corpus/projection v5, an exact selector successor, and prospective
  record set `schuss-record-set-000023@1`.
- Shared read-only operation `catalog.implementations.search` with request and
  result v10, plus `schuss catalog objects` over that same operation.
- A Task 030 catalog default for catalog commands, implementation provenance in
  human inspection, deterministic help/completion successors, negative cases,
  and current governance.
- Structural/catalog provenance evidence at levels 1-2 only.

## Out of scope

- Component contracts, implementation bindings, eligibility, compiler
  semantics, generated source, Java, `.axp`, ARM compile/link, projects,
  machine mutation, UI implementation, device access, resource/real-time
  measurement, listening, or audible claims for the 50 additions.
- Treating Task 028 native binding IDs `000097`-`000111` as catalog additions or
  changing the exact twenty-item palette.
- Repairing or promoting Rings reverb, Warps, or the Plaits macro voice from
  source metadata. Known link/build failures remain unresolved source facts.
- Tagging the 16 unattributed extended objects by inspiration, adjacency, path,
  or library reputation.
- Rewriting Task 011A/023/027 goldens, records, reviews, or historical hashes.
- Upstream checkout mutation, hardware action, staging, commit, push, release,
  or publication.

## Inputs and deliverables

Inputs are the accepted Task 029 parent record set; Task 027 source-review v0
and packet; Task 024 current-Ksoloti candidates and frozen observations; catalog
corpus/projection v4; the shared catalog projection/dispatcher; and accepted
CLI/application-capability schemas.

Deliverables are this contract; an exact curation decision; source-review v1
revision 2; catalog corpus/projection v5; selector revision 4; the 50 new
implementation records and any exact new families; operation request/result
v10; application-capability v3; the shared implementation search; product CLI
route, help, completion, and successor goldens; deterministic generation and
validation; evidence summary; and coherent status/history/roadmap indexes.

## Curation rules

- Provenance remains a filter facet, never a primary function or family tree.
- Every new implementation must bind one exact Task 027 source entry and its
  pinned observation or source-object bytes.
- One source entry produces one implementation. Family reuse requires exact
  reviewed musical equivalence; similar names or ancestry are insufficient.
- Every addition is `catalogued-only`, `not-evaluated`, and unresolved unless a
  separately accepted contract/binding/evidence record says otherwise. Task
  030 creates none of those records.
- Factory link statements and extended source compatibility fields remain
  source metadata, not Schuss evidence.
- Individual implementation search derives from the same exact projection as
  family search/inspect; the CLI owns no private catalog index.

## Validation cadence and acceptance tests

Focused checks cover this contract, exact 72-entry successor review, 56 tagged
catalog mappings, 50 additions, ID/family allocation, schemas, projection,
implementation search, CLI parsing/rendering, and negative mutations. Adjacent
regression covers Tasks 027-029, catalog operations, control-plane dispatch,
application capabilities, historical-golden preservation, and CLI hardening.

After implementation freeze, one copied-root/fresh-process reproduction must
prove byte-identical generated schemas, records, manifest, projection, CLI
JSON/human output, completion, and evidence. The full contract/inventory/catalog
aggregate runs once after that freeze; it is not repeated while implementation
changes remain planned.

Task 030 is accepted only when:

1. The exact parent and all parent schema/record members are preserved.
2. The Task 027 v0 review and packet bytes remain unchanged.
3. Successor review v1 contains the same 72 exact source identities, with 56
   tagged/catalogued mappings and 16 unattributed inventory-only entries.
4. Exactly 50 new implementations `000112`-`000161` resolve one-to-one to the
   former tagged candidates; no inventory-only entry is promoted.
5. Every new implementation has exact source authority, one exact family, and
   no contract/binding/eligibility/result/artifact/evidence reference.
6. The catalog retains all prior families/implementations and reports exactly
   56 Mutable-tagged implementation objects.
7. Warps retains its link-failure statement; the macro voice retains
   `h7-recommended`/`build-failed`; Rings reverb remains unsupported.
8. `catalog.implementations.search` validates closed filters, returns stable
   per-implementation summaries, and fails closed on stale/unknown inputs.
9. `schuss catalog objects --provenance mutable-instruments-derived` defaults
   to Task 030, dispatches exactly once, and returns all 56 implementation
   objects in canonical order; direct/API/CLI JSON bytes agree.
10. Family search/inspect remain available; human inspect exposes exact
    implementation provenance tags without changing old record-set bytes.
11. Request/result v10 and application-capability v3 reject unknown operations,
    fields, schema drift, and unavailable contexts deterministically.
12. Retained Task 011A/023 fixtures stay byte-identical; changed current CLI
    surfaces use a separate Task 030 successor fixture.
13. Two in-process generations and the post-freeze fresh-root/process run are
    byte-identical and portable, with no timestamp or absolute path.
14. Evidence levels 1-2 pass; levels 3-8 and all compiler/build/project/device/
    realtime/audible/publication actions are `not-run` or false.
15. Focused, adjacent, freshness, negative, governance, and diff checks pass
    after the implementation freeze. The final aggregate runs once and reports
    no Task 030 failure; any retained pre-existing historical gate is recorded
    exactly and is neither rewritten nor misreported as a Task 030 pass.

## Decisions Task 030 may make

- Exact function-first family membership, new family names/aliases/tags, and
  deterministic allocation within the fixed ID ranges.
- The closed per-implementation search result shape, ordering, query scoring,
  help text, and current CLI successor presentation.
- The smallest catalog/control-plane refactor required to keep family and
  implementation discovery on one shared projection.

## Decisions Task 030 must not make

- Compiler/backend/target behavior, component interfaces, graph or instrument
  semantics, implementation preference, device/resource/audio claims, or any
  promotion above catalog provenance level 2.
- A Mutable category hierarchy, inferred attribution, reduced wrapper, repaired
  upstream code, fallback implementation, or suppression of known failures.
- Mutation of accepted parents, upstream checkouts, hardware, Git publication,
  or activation of a later task.

## Activation state

The user's request activated this bounded task. Completion does not activate
compiler promotion, machine import, UI implementation, hardware work, Git
publication, or any later task.
