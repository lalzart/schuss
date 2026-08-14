# Catalog taxonomy

## Policy

Schuss browses by function, filters by form, and exposes provenance for
inspection. Filesystem layout and library ownership are evidence about origin;
they are not musical meaning.

This document fixes the classification rules, not the final category tree. The
final functional vocabulary belongs to the later taxonomy and manual
core-library curation phase.

## Classification axes

Each catalog entry may carry independent facets:

- **Function:** what the object does in a musical or signal-processing graph.
- **Abstraction level:** primitive, compound, or instrument.
- **Signal role:** audio, control, event, data, display, or mixed.
- **Form:** generator, native object, legacy subpatch, Schuss compound, asset,
  or target-specific implementation.
- **Provenance:** source repository, author evidence, original path, byte hash,
  and explicit license evidence.
- **Compatibility:** declared or verified target/backend support, with the
  evidence level attached.
- **Status:** raw, resolved, curated, deprecated, unresolved, or unsupported.

Function may be hierarchical and multi-valued. The other axes must not be
encoded by pretending they are function branches.

## Rules

1. Stable IDs never contain category paths, source-library names, or display
   labels that curators may change.
2. `factory`, `community`, `user`, repository names, and author names are
   provenance facets only.
3. `primitive`, `compound`, and `instrument` are abstraction levels only.
4. Help patches, examples, and demos retain those raw roles but are not
   automatically catalog categories.
5. A path or object name may suggest a candidate function, but raw inventory
   may not promote that suggestion to curated truth.
6. Missing, conflicting, or ambiguous classification remains explicit rather
   than being filled by a heuristic.
7. Compounds remain expandable to their complete graph.
8. Preferred/core status is a manual curation decision, separate from source
   priority or load order.

## Curation gate

A functional category becomes canonical only when its definition, inclusion
criteria, exclusions, and representative objects are reviewed together. The
inventory task may collect candidate labels and legacy paths as evidence but
must not establish the final tree.
