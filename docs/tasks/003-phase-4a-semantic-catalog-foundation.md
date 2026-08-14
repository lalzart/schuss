# Task 003: Phase 4A semantic catalog foundation

Status: complete. Phase 3 evidence is accepted and frozen; the Phase 4A
overlay and 26-family pilot pass their schema, semantic, determinism, and
frozen-evidence gates.

Read `AGENTS.md`, `README.md`, `docs/PROJECT_CONTEXT.md`,
`docs/ARCHITECTURE.md`, `docs/TAXONOMY.md`, `docs/PARAMETER_MODEL.md`,
`docs/LEGACY_STRATEGY.md`, `docs/ROADMAP.md`, Tasks 001 and 002, and the Phase
3 review summary before making changes. If this task conflicts with an accepted
decision, report the conflict rather than changing the architecture.

## Goal and why it exists

Create the smallest versioned semantic catalog foundation that separates
musician-facing catalog identity from the 3,602 frozen legacy observations.
The foundation must support manual curation, predictable drawer placement, and
future structured queries without rewriting the inventory evidence.

The 3,602 records reconcile as 3,417 definition occurrences, 134 catalog
subpatch placeholders, and 51 provider-only observations. They are not 3,602
Schuss modules. Phase 4A proves the progression
`legacy observation -> implementation variant -> user-facing family` with a
manually reviewed pilot rather than classifying the entire census.

## In scope

- Accept and freeze the Phase 3 evidence with its documented limitations.
- Define category-independent family and implementation identities.
- Define a reviewed draft of the 13-category functional taxonomy.
- Add a separate versioned semantic overlay schema and fail-closed validator.
- Curate 20-30 representative families with evidence-linked implementations.
- Exercise compounds, generated/provider observations, overloads, merged
  implementation families, uncertainty, dense facets, and multiple sources.
- Correct the roadmap sequence for the minimal Gills, graph, backend, adapter,
  and shared-operation contracts.

## Out of scope

- Classifying all 3,602 observations or selecting the complete 150-250-family
  reviewed core.
- Resolving every overload, partial graph, provider mismatch, or zombie.
- Final graph, device-profile, instrument, parameter-mapping, or operation
  schemas.
- A GUI, editor, CLI implementation, compiler frontend, target build, firmware
  change, device access, upload, flash, SD-card write, or audible test.
- Replacing the Java resolver or changing any frozen snapshot/review artifact.
- Staging, committing, tagging, or pushing.

## Inputs

- `catalog/snapshots/legacy-catalog-v0/` and
  `catalog/snapshots/legacy-resolved-catalog-v0/`, read only.
- `catalog/reviews/phase-3-inventory-review-v0/`, read only.
- The accepted architecture, taxonomy policy, parameter model, legacy
  strategy, and source lock.

## Deliverables

- ADR 0004 accepting and freezing the Phase 3 evidence.
- Updated project status, architecture links, taxonomy, and roadmap.
- `docs/SEMANTIC_CATALOG.md` for identity and overlay semantics.
- `schemas/semantic-catalog-overlay-v0.schema.json`.
- `catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json` and a concise
  pilot report.
- `tools/catalog/validate_semantic_catalog.py` and focused tests.

## Acceptance tests

1. Existing raw, resolved, and Phase 3 review validators pass.
2. Every file in the Phase 2 and Phase 3 snapshot/review directories is
   byte-identical to the pre-task hash set.
3. The overlay validates against its committed schema.
4. Two validations of unchanged data emit identical structured summaries.
5. Each pilot family has exactly one controlled primary category.
6. No primary category or stable ID encodes provenance, source paths, category
   paths, authors, or mutable labels.
7. Display-name and category edits cannot derive or rewrite family or
   implementation IDs.
8. Every legacy evidence reference resolves to a frozen observation.
9. Ambiguous or unsupported relationships are explicit and fail closed.
10. The pilot has 20-30 families and covers all required difficult cases.
11. Durable artifacts contain no absolute checkout paths, timestamps, random
    IDs, or machine-specific values.
12. No Java dependency exists outside `legacy/ksoloti-bridge/`.
13. No out-of-scope implementation or external mutation occurs.
14. Project documentation consistently calls Phase 4A current and Phase 3
    frozen evidence rather than the Schuss catalog.

## Decisions this task may make

- Opaque ID syntax and allocation rules for the v0 family and implementation
  namespaces.
- Overlay file organization, deterministic serialization, controlled v0 tags,
  review/confidence vocabulary, and validator diagnostics.
- The draft primary category definitions and pilot classifications.
- Which 20-30 families best exercise the model.

## Decisions this task must not make

- The final 150-250-family core or a complete legacy-to-family mapping.
- Final graph, instrument, device-profile, operation, or compiler contracts.
- Target compatibility beyond the evidence level actually recorded.
- A rule that guesses ambiguous membership or hides legacy diagnostics.
- A category or ID derived from provenance, path, display name, or author.
- Any change to the frozen evidence or an upstream checkout.

## Completion evidence

1. All 14 existing inventory tests passed. The raw validator reported 4,209
   files and two issues; the resolved validator reported 3,602 objects, 1,157
   graphs, and 3,180 issues; the Phase 3 packet validator reported 20 issue
   classes, 157 overload groups, 805 partial graphs, and 103 zombie groups.
2. Pre- and post-task SHA-256 lists for all 27 files under the two snapshot
   roots and the Phase 3 review root compared byte-identically.
3. The overlay passed `semantic-catalog-overlay-v0.schema.json` and the closed
   semantic validator.
4. Two fresh validator runs emitted byte-identical one-line JSON summaries.
5. The pilot contains 26 families and 38 implementations, with exactly two
   families in each of all 13 primary categories.
6. The primary-category enum contains only the functional vocabulary; stable
   IDs match opaque numeric patterns and cannot contain provenance or paths.
7. A focused test changes family display names and swaps controlled categories,
   then proves the complete family/implementation ID projection is unchanged.
8. All 38 distinct object references and both graph references resolve to the
   frozen snapshot, and each provenance source agrees with its observation.
9. The granular family is confirmed under Sampling & Buffers. The provider-only
   RFFT implementation remains the sole low-confidence membership question,
   flagged as `PROVIDER_FILE_IDENTITY_UNPROVEN`.
10. Derived pilot gates confirm native primitives, two complete `.axs`
    compounds, generated/provider-backed and provider-only observations, three
    overloaded families, eight multi-implementation families, dense parameter
    and port cases, and four provenance sources.
11. Durable overlay/schema/report scans found no checkout paths, timestamps,
    random IDs, or machine-specific values.
12. A repository search found no Java source outside
    `legacy/ksoloti-bridge/`.
13. No GUI, CLI implementation, target compilation, device access, upload,
    firmware change, upstream mutation, staging, commit, or push occurred.
14. `README.md`, project context, architecture, taxonomy, roadmap, ADR index,
    Task 002, and this task consistently identify Phase 3 as frozen evidence
    and Phase 4A as current.
