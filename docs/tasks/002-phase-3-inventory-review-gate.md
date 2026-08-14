# Task 002: Phase 3 inventory review gate

Status: complete. The packet passed its mechanical gates and its documented
limitations were accepted for Phase 4A in ADR 0004.

Read `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/TAXONOMY.md`, `docs/LEGACY_STRATEGY.md`,
`docs/inventory/resolved-catalog-spec.md`, and this task before making changes.
If this task conflicts with an accepted decision, report the conflict rather
than silently changing the architecture.

## Goal

Produce a deterministic review packet that explains how many unique legacy
items are materially affected by Phase 3 diagnostics and which issue classes
may interfere with taxonomy, migration, or later compilation work.

## Why it exists

The Phase 3 snapshot is deliberately fail-closed: 3,180 issues can include
several observations for one object, graph, or source file. Aggregate issue
counts alone do not say whether the resolved evidence is suitable for
classification or migration. The 3,602-object census also needs an explicit
reconciliation before a representative core set is selected.

## In scope

- Group issues by code, severity, source, and unique affected item.
- Reconcile definition occurrences, legacy `ObjectList` retention, and exported
  records.
- Report every overloaded-name group, its candidates, and graph-selection
  evidence.
- Group resolution-created zombies by requested legacy identifier.
- Group partial graphs by individual reason and by reason combination.
- Cross-tabulate graph status by source repository and graph file type.
- Measure inlet, outlet, port, parameter, attribute, and display coverage by
  legacy object kind and class.
- Produce deterministic samples of 25 complete graphs, 25 partial graphs,
  25 overloaded selections, and 25 representative objects.
- Add an explicitly labeled engineering review of which issue classes are
  material to taxonomy, migration, or compilation readiness.
- Bind the packet to exact hashes of the frozen Phase 3 snapshot and verify
  that all durable paths are portable.

## Out of scope

- Modifying any file under
  `catalog/snapshots/legacy-resolved-catalog-v0/`.
- Defining the final taxonomy or classification-overlay schema.
- Assigning functional categories, confidence scores, preferred/core status,
  or final Schuss item IDs.
- Selecting or classifying the Phase 4 core set.
- Treating graph frequency from partial graphs as strong evidence.
- Changing the bridge, legacy resolution behavior, source locks, or upstream
  checkouts.
- Code generation, ARM compilation, device access, or audible validation.
- Staging, committing, tagging, or pushing without separate approval.

## Inputs

- `catalog/snapshots/legacy-resolved-catalog-v0/`, treated as immutable evidence;
- the resolved v0 schemas and validator;
- `catalog/snapshots/legacy-catalog-v0/` for inherited raw reconciliation; and
- the issue-impact policy recorded by the review generator.

Snapshot-local references such as
`legacy-resolved-catalog-v0:object:123` are review evidence references only.
They are not final Schuss item IDs.

## Deliverables

- `tools/inventory/build_phase3_review_packet.py`;
- `tools/inventory/validate_phase3_review_packet.py`;
- focused review-packet tests under `tools/inventory/tests/`;
- versioned review schemas under `schemas/`;
- a generated packet under
  `catalog/reviews/phase-3-inventory-review-v0/`; and
- a concise human review summary naming material unique-item counts and the
  classes that need attention before Phase 4 or later migration work.

## Required packet reports

1. Issue groups with issue count, severity, source, and unique affected-item
   counts.
2. Object-count reconciliation for 3,417 definition occurrences, 3,548
   retained `ObjectList` entries, and 3,602 exported records.
3. All 157 overloaded-name groups with ordered candidates and selection
   evidence.
4. Resolution-created zombies grouped by requested name, UUID, and SHA.
5. Partial graphs grouped both by reason and by complete reason combination.
6. Complete, partial, and failed graph counts by repository and `axs`/`axp`
   type.
7. Facet coverage by legacy object kind and legacy Java class.
8. Four deterministic, seed-bound 25-record samples: complete graphs, partial
   graphs, overloaded selections, and representative objects.
9. A portability report confirming that neither the frozen snapshot nor the
   generated review packet contains machine-specific absolute paths.
10. An impact report that separates observed counts from engineering judgment
    about taxonomy, migration, and compilation readiness.

## Acceptance tests

1. The resolved snapshot validates before report generation.
2. Its complete file-hash set is recorded before generation and is unchanged
   afterward.
3. Two fresh report generations are byte-identical.
4. Every issue, overload group, resolution-created zombie, and partial graph is
   accounted for exactly once in the appropriate partition and at least once
   in non-exclusive reason groupings.
5. The object reconciliation equations equal the retained Phase 3 summary.
6. Graph status matrices equal 1,157 total graphs and reconcile by source,
   type, and status.
7. Facet totals recompute exactly from all 3,602 object records.
8. Each sample contains 25 distinct, valid evidence references and records its
   deterministic selection method and seed.
9. Every generated file validates against its versioned schema or an explicit
   closed validator contract.
10. No generated report contains a timestamp, random UUID, temporary path,
    checkout path, or other machine-specific absolute path.
11. The generator does not modify the frozen snapshot or any upstream Git
    state.

## Decisions this task may make

- Review-packet file organization and report row shapes.
- Snapshot-scoped evidence-reference syntax.
- The deterministic sample seed and hash-ranking method.
- Unique affected-item grouping rules.
- A versioned, explicitly judgmental issue-impact policy for review routing.

## Decisions this task must not make

- Final Schuss stable-ID syntax.
- Final category names, function tags, aliases, or confidence rules.
- Which 150–250 objects belong to the Phase 4 core set.
- That a partial graph is broken, uncompilable, or musically invalid without
  the corresponding evidence level.
- That legacy selection is definitive when candidate identity is ambiguous or
  unproven.
- Any change to the frozen Phase 3 snapshot.

## Review evidence

The retained packet under `catalog/reviews/phase-3-inventory-review-v0/`
passed two-generation byte comparison, its closed validator, all 14 inventory
tests, and the unchanged snapshot-hash check.

The unusually large object census reconciles without a hidden duplication
step:

- 3,139 loaded `.axo` files contain 3,417 definition occurrences;
- 157 of those files contain more than one definition, contributing 278
  occurrences beyond a one-definition-per-file count; the largest contains 18;
- 134 `.axs` files contribute catalog subpatch placeholders; and
- 51 observed provider emissions have no exact file-backed match.

Therefore `3,417 + 134 + 51 = 3,602` exported records. Separately,
`3,417 - 3 legacy-equality collapses + 134 = 3,548` retained legacy
`ObjectList` entries. The 51 provider-only records are not silently inserted
into that legacy search collection.

The packet also records:

- 20 issue classes and 1,167 unique direct affected records;
- 437 unique object variants implicated through candidate sets;
- 157 overloaded-name groups containing 392 candidate definitions, 10,644
  graph-selection evidence records, and 265 ambiguous selections; 45 overload
  groups have no observed graph-selection evidence in this snapshot;
- 364 resolution-created zombies grouped into 103 requested identifier tuples
  across 180 graphs;
- an exact 805-partial-graph reason-combination partition;
- all repository, graph-type, and status cells, including zero-count cells;
- facet coverage by legacy kind and Java class; and
- four distinct 25-record samples bound to the public
  `schuss-phase3-inventory-review-v0` hash seed.

The versioned engineering policy routes 495 unique records to material
taxonomy review, 1,301 to material migration review, and 904 to material
compilation-readiness review. These unions include directly affected records
and implicated candidate variants. They do not claim that those records are
invalid, uncompilable, or musically unsuitable.

No snapshot or upstream file changed, and neither the frozen snapshot nor the
review packet contains a detected machine-specific absolute path.

## Human review conclusion

The review gate is accepted. The packet is sufficient frozen input for a
separate semantic overlay; its partial, ambiguous, overloaded, provider-only,
zombie, failed, and unresolved records remain evidence limitations that later
work must preserve rather than silently repair.
