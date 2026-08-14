# Task 001: Legacy source and Java-resolved inventory

Status: complete. The Phase 2 raw baseline and Phase 3 Java-resolved baseline
are retained and validation-ready.

Read `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/TAXONOMY.md`, `docs/LEGACY_STRATEGY.md`, and this task before making
changes. If this task conflicts with an accepted decision, report the conflict
rather than silently changing the architecture.

## Goal

Produce a reproducible factual inventory of the pinned Ksoloti source universe,
then export the objects and compound graphs observed after legacy Java loading
and resolution.

## Why it exists

Schuss needs trustworthy evidence for a later source-agnostic catalog. The raw
filesystem is insufficient: `.axo` files may contain multiple definitions,
generated objects are emitted by Java, resolution depends on load order and
working directory, UUIDs may be generated, and unresolved graph instances
become zombies only after post-construction.

## In scope

- Phase 2 raw inventory of `.axo`, `.axs`, `.axp`, and generated-object Java
  source candidates.
- Exact byte hashes, source commits, factual path roles, parse outcomes, and
  structured issues.
- Phase 3 synchronous Java loading and export of ordered catalog variants.
- Explicit versus generated UUID identity.
- Duplicate UUID and overloaded-name candidates without map collapse.
- Native and generated object definitions with traceable provenance.
- Inlets, outlets, parameters, attributes, displays, modulators, dependencies,
  includes, and code-section presence as separate factual facets.
- Resolved `.axs`/`.axp` graph structure, instance values, endpoints, and zombie
  or missing-reference diagnostics.
- Deterministic summaries and validation.

## Out of scope

- Final functional taxonomy or preferred/core-library selection.
- A final Schuss object, graph, or instrument schema.
- GUI, object drawer, or canvas implementation.
- New graph mutation protocol or compiler frontend.
- Firmware changes, USB access, upload, flash, or connected-board testing.
- Inferring per-file licenses, musical quality, target feasibility, or function
  from paths, authors, or repository ownership.
- Cleaning or modifying any upstream checkout.

## Inputs

- `catalog/sources.lock.json` for portable source identities and exact commits.
- Ignored `catalog/sources.local.yml` for machine-local checkout paths.
- `catalog/snapshots/legacy-catalog-v0/` as the retained Phase 2 baseline.
- The pinned Ksoloti Java model and generated-object sources.
- The architecture observations in `docs/inventory/architecture-audit.md`.

The migrated baseline observed the patcher checkout as dirty. Its files are
byte-hashed and internally verifiable, but exact regeneration of every patcher
candidate from the pinned commit alone is not claimed until the relevant dirty
state is either eliminated or captured as an explicit input.

The retained Phase 2 traversal also treated every directory named `dist` or
`out` as generated output, even when those names were legitimate object
categories, and its suffix test missed the legacy-valid filename
`objects/rbrt/.axo`. This leaves 143 `.axo`, two `.axs`, and one `.axp`
candidate out of the raw snapshot. Phase 3 must include and explicitly
reconcile these 146 omissions; it must not rewrite the Phase 2 evidence.

## Deliverables

### Phase 2: retained

- raw exporter and tests under `tools/inventory/`;
- raw manifest, file records, issues, and summaries under
  `catalog/snapshots/legacy-catalog-v0/`; and
- matching `legacy-catalog-v0` schemas under `schemas/`.

### Phase 3: retained

- a bridge-local synchronous catalog loader/exporter;
- versioned schemas for resolved object, graph, issue, and manifest records;
- a new resolved snapshot directory that does not overwrite Phase 2;
- deterministic fixtures covering multi-object files, name overloads,
  duplicate UUIDs, explicit/generated UUIDs, generated objects, relative
  subpatch lookup, and zombies; and
- a summary reconciling physical candidates with emitted/resolved records.

## Acceptance tests

### Phase 2

1. `python3 -m unittest discover -s tools/inventory/tests` passes.
2. `python3 tools/inventory/validate_raw_inventory.py catalog/snapshots/legacy-catalog-v0`
   reports 4,209 files and two retained issues.
3. Durable artifacts contain no absolute local checkout paths.
4. Repeated export from identical bytes and Git state is byte-identical.

### Phase 3

1. Loading is synchronous and has no fixed sleeps, preference writes, device
   access, target-artifact generation, or compilation. Resolving `.axs` may
   perform the named legacy in-memory subpatch-interface projection needed to
   observe runtime ports; it must not call `Patch.WriteCode()` or emit C++ or
   binary artifacts.
2. Export order and serialization are deterministic across two fresh
   processes.
3. Every loaded variant is exported from the ordered collection; the UUID map
   is not treated as a complete catalog.
4. Explicit source UUID and legacy-generated runtime UUID are distinguishable.
5. Generated runtime objects are enumerated rather than inferred from Java file
   presence.
6. Resolved compound graphs preserve instances, nets, endpoint diagnostics,
   instance facet values, and zombies.
7. Every resolved record traces to a pinned source, generated-object provider,
   or explicit unresolved provenance.
8. Tests demonstrate that ambiguous and unsupported content fails closed while
   unrelated records continue to export.
9. No upstream checkout changes during the run.

## Completion evidence

The retained `legacy-resolved-catalog-v0` snapshot passed the Phase 3 gate:

- the harness built the pinned patcher commit from a Git archive, compiled the
  bridge with Java 21, exercised the behavioral fixture in two isolated JVMs,
  and then exported the production inputs in two more isolated JVMs;
- both production streams were byte-identical before materialization, and the
  manifest records no preferences, target-artifact generation, target
  compilation, device access, or timestamp input;
- all 3,602 ordered object records are preserved: 3,551 have file provenance
  and 51 have explicit provider-only provenance; generated nondeterministic
  UUID values are classified without retaining random runtime values;
- all 1,157 graph candidates are retained: 348 complete, 805 partial, and four
  failed. The records preserve 265 ambiguous instances, one serialized hard
  zombie, 364 zombies created by resolution, and endpoint/net diagnostics;
- 1,945 selections remain explicitly unproven. Of these, 1,942 are inline
  `patcher` or `patchobj` definitions that v0 cannot identify as ordinary
  catalog variants, and three are non-catalog object references;
- 125 graphs contain an explicit nonportable-value redaction issue, while the
  durable records contain no local checkout or temporary paths;
- 146 `RAW_BASELINE_OMISSION` issues reconcile the 143 `.axo`, two `.axs`, and
  one `.axp` candidates omitted by Phase 2 without rewriting that snapshot; and
- schema, index, source-hash, provenance, summary, path-leak, and unchanged
  upstream-state checks all passed. The six-graph fixture separately proves
  overload promotion, ambiguity, relative lookup, unsupported content, parse
  continuation, hard zombies, and resolution-created zombies.

This is host-side structural evidence. ARM compile/link, connected-board, and
audible evidence remain outside this task.

## Decisions this task may make

- resolved-inventory record shapes and diagnostic codes needed to represent
  legacy facts;
- the smallest registry/loader seam required for synchronous export;
- deterministic ordering and normalization rules;
- fixture organization; and
- whether the bridge exporter is a Java command, a thin wrapper, or both.

## Decisions this task must not make

- final category names or catalog ranking;
- final public Schuss graph-operation API;
- final instrument or parameter-mapping schema;
- replacement firmware or compiler architecture;
- a rule that hides duplicate, zombie, ambiguous, or unresolved content; or
- changes to upstream source bytes for the sake of a clean inventory.
