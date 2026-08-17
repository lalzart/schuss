# Task 024: Current-Ksoloti-first catalog structure and deterministic lineage

Status: accepted by the user and completed under the resumed overnight Tasks
024-026 goal. This revised contract supersedes the uncommitted first Task 024
draft while retaining its valid frozen-inventory audit evidence. The revision
passed all fifteen revised acceptance tests before Task 025 consumed the
successor.

## Goal and why it exists

Make the current pinned Ksoloti application's source-library and import model
the primary candidate reference for Schuss catalog curation, while preserving
all 3,602 observations in `legacy-resolved-catalog-v0` as immutable
provenance, lineage, and gap evidence. This exists because a frozen observation
rank is not a product backlog and a Ksoloti folder is not a musical category.
Schuss needs exact current source cohorts, complete overload accounting,
function-first family review, and an exact Task 025 handoff without conflating
catalog presence with support.

## Dependencies and verified baseline

ADR 0014, `docs/APPLICATION_SPINE_PLAN.md`, accepted Task 023, and
`contracts/task024/current-ksoloti-curation-decision.md` are the routing
authorities. The four current Ksoloti libraries and patcher source are pinned
in `catalog/sources.lock.json`. Ksoloti configures four enabled source-library
roots, recursively loads `.axo` normal definitions and `.axs` subpatches as
different forms, and forms deterministic normal-definition base references as
`library:canonical/path/id` with exact variants below them.

The primary first-party corpus is `axoloti-factory` plus `ksoloti-objects` at
their pinned commits: 668 `.axo` files, 835 normal definitions, 666 canonical
base references, and 19 `.axs` compounds. The contrib libraries remain pinned
deferred provenance cohorts. The frozen snapshot still contains exactly 3,602
ordered observations, but its raw traversal excludes legitimate directories
named `dist` and `out`; it is therefore not a complete current-source census.
The accepted catalog projection has 40 reviewed families after Task 017, and
the accepted effects graph names eight exact component contracts.

The frozen snapshot, Phase 3 packet, Phase 4A overlay, Task 017 records,
historical goldens, and accepted record sets remain immutable inputs.

## In scope

- A deterministic current-Ksoloti source corpus generated from the exact Git
  trees of all four configured libraries and the exact patcher model sources,
  never from ambient working-tree bytes.
- A candidate index for all 666 first-party normal-definition base references
  plus 19 separately marked `.axs` compounds. Each exact variant retains its
  library, canonical ID, source path/hash, identity, interface signature,
  declared include/dependency facts, and frozen lineage references.
- Explicit separation of library/provenance roots, import form, base-reference
  cohorts, variants, dependency closure, function-first family identity,
  drawer visibility, and readiness.
- Retention of the thirteen reviewed Schuss function categories. Current
  Ksoloti paths are candidate crosswalk evidence and always require
  object-level semantic review.
- Retention of the first Task 024 draft's exact 3,602-observation disposition,
  coverage, and frequency-ordered queue artifacts as historical lineage and
  gap evidence. The queue is not the presumed product-review backlog.
- Twenty reviewed family records, IDs `schuss-family-000041` through
  `schuss-family-000060`, treated as eleven retain, seven revise, and two
  reconsider decisions fixed by the decision record.
- Complete current variant cohorts for those twenty base references. The
  original selected implementation IDs remain `schuss-implementation-000061`
  through `schuss-implementation-000080`; nine additional overload variants
  use `schuss-implementation-000081` through
  `schuss-implementation-000089`.
- Exact catalog successor `schuss-catalog-000001@3`, selection successor
  `schuss-catalog-selection-000001@2`, current source corpus
  `schuss-current-ksoloti-corpus-000001@1`, and record set
  `schuss-record-set-000016@1` parented byte-for-byte by
  `schuss-record-set-000015@1`.
- Exact Task 025 packet `schuss-core-selection-000002@1`, derived only from
  the eight contracts in accepted graph `schuss-graph-000004@1`.
- Shared catalog search and inspection over all sixty families, exposing
  review treatment, default/advanced/review-only visibility, current Ksoloti
  base references, complete candidate-versus-catalogued variant counts,
  function, form, provenance, readiness, and unresolved facts.
- Focused, adjacent, deterministic, fresh-root, governance, and one final
  aggregate validation pass.

## Out of scope

- Rewriting the frozen raw/resolved snapshots, Phase 3 packet, Phase 4A
  overlay, Task 017 corpus, accepted records, or historical evidence.
- Treating Ksoloti library IDs or folders as Schuss musical categories, or
  inferring family identity, quality, license, preferred status, compatibility,
  compiler support, target support, or audible value from source presence.
- Product-semantic curation of contrib/community libraries in this tranche.
- Resolving the two reconsidered family identities by silently merging or
  deleting lineage. Their identities remain reserved and review-only.
- Component contracts or implementation bindings for the Task 024 additions.
  They remain catalogued-only and unresolved unless an accepted exact record
  already proves more.
- DSP equations, lowering, host vectors, ARM compilation, backend execution,
  project writes, UI implementation, device access, electrical claims,
  real-time measurement, or listening claims. Task 025 owns its exact direct
  tranche.
- Staging, commit, push, release, upload, reset, flash, SD-card write, or
  persistent installation.

## Inputs and deliverables

Inputs are the exact Task 023 parent record set; pinned Ksoloti source lock and
ignored local source mapping; exact patcher library-loader/catalog sources;
frozen resolved-object and graph JSONL plus manifest; Phase 4A overlay; Task
017 corpus, effects graph, contracts, bindings, and readiness records; and the
accepted catalog projection service.

Deliverables are this contract and read-only contract validator; the durable
curation decision; schemas `current-ksoloti-candidate-v0`,
`current-ksoloti-corpus-v0`, `catalog-coverage-v0`,
`catalog-review-manifest-v0`, `task025-selection-packet-v0`,
`catalog-corpus-v3`, and `catalog-projection-v3`; the deterministic current
candidate index; retained frozen coverage packet; exact Task 024 records and
record set; bounded v3 catalog loading; focused tests; completion validation
and report; and integrated status, roadmap, history, task index, application
plan, and governance assertions.

## Current-source and curation rules

The source generator reads exact locked Git trees. It fails closed if a
configured library, commit, expected census, object XML definition, base
reference, variant identity, source hash, or decision-record hash changes.
Normal definitions group first by exact current Ksoloti base reference;
`.axs` compounds remain a separate form. Includes and dependency names remain
per-variant implementation facts and do not create families or library roots.

A current base reference is a review cohort, not automatic Schuss family
identity. The twenty accepted Task 024 reviews may group their complete exact
overloads because the decision record reviews those functions and explicitly
keeps rate/data type as form/contract distinctions. The two reconsidered
families remain review-only pending serialized identity integration. Their IDs
are not reassigned.

The frozen coverage generator still emits one factual disposition per frozen
observation using the original precedence. Its `review-queue.jsonl` remains a
deterministic historical prioritization artifact. Neither its count nor graph
frequency defines the current product backlog, acceptance, category, contract,
or support state.

## Task 025 selection boundary

The Task 025 packet is not a promise that its subjects compile. It resolves
exactly the eight contract references in accepted graph
`schuss-graph-000004@1`, binds each to its accepted family and source
implementation, reports current readiness independently, and retains levels
1-2 as passed only where reproduced. Levels 3-8 remain `not-run` for Task 024.
The current-source reset does not add any compiler subject.

## Validation cadence

Iteration uses the contract validator, current-source census/candidate tests,
catalog generator, frozen coverage, schema, projection, and negative tests
first. Adjacent catalog and record-set regressions run after focused stability.
The complete packet is generated twice and checked for byte identity only
after stabilization. The final diff and freshness checks are then frozen and
reviewed, followed by one aggregate contract/inventory/catalog suite. A
failure returns to the smallest focused test and permits one final aggregate
rerun after correction.

## Acceptance tests

1. The contract validator confirms goal, scope, exact current and frozen
   inputs, deliverables, decisions, cadence, stable-ID allocations, evidence
   boundaries, and prohibited actions without mutating the repository.
2. The exact Task 023 parent, source lock, patcher model sources, frozen
   snapshot, and decision record validate before generation; accepted parent
   and upstream bytes remain unchanged.
3. The four configured library roots are exact, with factory and Ksoloti
   objects primary and both contrib libraries deferred provenance cohorts.
4. The first-party census is exactly 668 `.axo` files, 835 normal definitions,
   666 canonical base references, 19 `.axs` compounds, 685 candidates, and 854
   total candidate variants/forms.
5. Every candidate has portable source identity and hash, exact import form,
   deterministic ordering, declared include/dependency facts, and explicit
   complete/partial/absent frozen-lineage status; no absolute path, host,
   timestamp, or user enters durable output.
6. Exactly 3,602 retained dispositions remain in consecutive variant-index
   order, their counts sum to 3,602, and the frozen queue remains labelled
   `prioritization-only` and non-authoritative for product backlog.
7. Two independent generations produce byte-identical schemas, candidates,
   retained audit artifacts, records, selection packet, and record-set
   manifest.
8. The catalog successor contains exactly 60 families, retains every v2 family
   and implementation byte, and accounts for all twenty decisions as eleven
   retain, seven revise, and two reconsider records.
9. Every Task 024 family names its exact current base reference, drawer
   visibility, treatment, complete candidate variant count, and exact
   catalogue implementation IDs; the nine overload additions occupy IDs
   81-89 without collision.
10. Catalog v3 search and inspect are deterministic and expose function,
    form, provenance, treatment, visibility, variant coverage, readiness, and
    unresolved facts separately.
11. The Task 025 packet still resolves exactly the eight component contracts
    present in accepted graph `schuss-graph-000004@1`, with no current-library
    or unsupported addition.
12. Task 024 reports structural evidence only: catalog levels 1-2 according to
    reproduced results and levels 3-8 `not-run`; it performs no compiler,
    build, project, UI, device, real-time, audible, safety, or release action.
13. Missing source mappings, stale commits/hashes, malformed XML, changed
    census, incomplete selected variant cohorts, stale decision hash,
    ambiguous family/implementation references, and extra records fail closed
    with deterministic diagnostics.
14. Exact parent preservation, record-set closure, generated freshness, and
    current governance validation pass after integration.
15. Focused and adjacent suites pass, the complete diff is reviewed, and one
    final aggregate contract/inventory/catalog suite passes.

## Decisions Task 024 may make

- The exact current-source candidate schema, artifact layout, ordering,
  portable identity representation, and lineage crosswalk needed for the
  bounded first-party corpus.
- The reviewed names, categories, aliases, visibility, treatment, rationale,
  and complete base-reference variant membership fixed by the durable decision
  record.
- The smallest v3 catalog/projection generalization needed to expose these
  facts without changing stable family identity.

## Decisions Task 024 must not make

- DSP, state, timing, parameter-transfer, component-interface, binding,
  compiler, backend, target/resource, device, electrical, real-time, or
  audible semantics.
- A family merge from path, name, source, frequency, or load order alone;
  silent overload collapse; contrib product acceptance; or promotion from
  catalogued-only without exact accepted evidence.
- Any project/history operation, UI implementation, hardware action, or
  evidence above what is reproduced.
- Mutation of historical bytes or upstream checkouts; ambient/latest
  discovery; fallback; staging; commit; push; release; upload; reset; flash;
  or SD-card write.

## Readiness and activation state

The user explicitly authorized this current-Ksoloti-first Task 024 revision as
the resumed first step of the overnight Tasks 024-026 goal. Task 024 passed all
fifteen revised acceptance tests at structural evidence level 2. Task 025 is
active under its separate complete contract and exact selection packet.
Completion does not broaden Task 025, activate Task 027/028, implement UI,
authorize Git publication, or authorize hardware action.
