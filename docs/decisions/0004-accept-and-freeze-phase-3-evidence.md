# ADR 0004: Accept and freeze Phase 3 evidence

- Status: accepted
- Date: 2026-08-14

## Context

The Phase 3 resolved inventory and review packet reconcile all 3,602 exported
records and retain partial, failed, ambiguous, overloaded, provider-only,
zombie, and unresolved observations. The review gate identifies material work
for later taxonomy, migration, and compilation workflows without claiming that
affected records are invalid or uncompilable.

## Decision

Accept the Phase 3 snapshot and review packet as sufficient frozen evidence for
Phase 4A, with their documented limitations. Do not expand or repair the
inventory as part of semantic curation. Place all family, implementation,
category, alias, confidence, and preferred/core decisions in a separate
versioned overlay that references the frozen observations.

Snapshot-scoped references such as
`legacy-resolved-catalog-v0:object:164` remain evidence locators. They are not
Schuss IDs. Uncertainty that matters to curation remains explicit in the
overlay rather than being resolved by path or naming guesses.

## Consequences

- The Phase 2 raw snapshot, Phase 3 resolved snapshot, and Phase 3 review
  packet are immutable inputs to current catalog work.
- The reconciliation is fixed as 3,417 definition occurrences plus 134 catalog
  subpatch placeholders plus 51 provider-only observations, totaling 3,602.
- Later validators may resolve and inspect evidence references but may not
  rewrite the referenced records.
- A future inventory version requires a new bounded task and new versioned
  artifacts; it must not revise the accepted v0 evidence in place.
