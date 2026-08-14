# Schuss

Schuss is a modern, CLI-first, source-agnostic environment for designing
embedded musical instruments. It initially targets Ksoloti Core, preserves the
existing firmware, toolchain, and DSP ecosystem through an isolated
compatibility bridge, and supports a Gills-first instrument abstraction above
a transparent DSP graph.

Schuss is not a replacement firmware or a reskinned Ksoloti Patcher. It is a
new domain model and authoring environment that treats the legacy Java stack as
one compatibility backend.

## Current status

Schuss has completed the Phase 4A semantic-catalog foundation and the Task 005
device/instrument contract gate:

- the project boundaries and terminology are documented;
- upstream sources are pinned without committing machine-local paths;
- the existing deterministic raw Ksoloti inventory has been preserved as a
  baseline snapshot;
- the Java-resolved catalog and graph inventory is retained as a second,
  independently validated snapshot;
- a deterministic Phase 3 review packet quantifies unique taxonomy, migration,
  and compilation-readiness impact without changing that snapshot;
- the Phase 3 evidence and review packet are accepted and frozen with their
  documented limitations;
- a separate versioned overlay now defines family and implementation identity,
  the draft functional taxonomy, and a manually reviewed 26-family pilot;
- Phase 4A validation is complete; complete-census classification and the
  150-250-family reviewed core remain planned Phase 4B work;
- Task 004 remains the accepted architecture for catalog family, typed
  component contract, implementation binding, graph, device, instrument,
  target, backend, and build evidence;
- Task 005 is complete: closed minimal device-profile and instrument schemas,
  canonical hashing, a one-knob Gills/reference-instrument pair, and read-only
  validation now establish the device/instrument contract gate;
- graph resolution remains explicitly deferred to Task 006 rather than being
  represented by a graph stub or fabricated hash;
- no Schuss graph editor, compiler frontend, device runtime, or desktop app is
  implemented yet.

Start with [the project context](docs/PROJECT_CONTEXT.md), then read
[the architecture](docs/ARCHITECTURE.md),
[the schema strategy](docs/SCHEMA_STRATEGY.md),
[the compiler strategy](docs/COMPILER_STRATEGY.md), and
[the roadmap](docs/ROADMAP.md). Active implementation work is bounded by task
files under `docs/tasks/`.

## Inventory checks

```bash
python3 -m unittest discover -s tools/inventory/tests
python3 tools/inventory/validate_raw_inventory.py \
  catalog/snapshots/legacy-catalog-v0
python3 tools/inventory/validate_resolved_inventory.py \
  catalog/snapshots/legacy-resolved-catalog-v0
python3 tools/inventory/validate_phase3_review_packet.py \
  catalog/reviews/phase-3-inventory-review-v0
python3 tools/catalog/validate_semantic_catalog.py \
  catalog/overlays/phase-4a-semantic-catalog-v0
```

The raw snapshot records 4,209 candidate files and two retained XML parse
issues. The resolved snapshot records 3,602 object observations and 1,157 graph
observations, including partial and failed outcomes rather than hiding them. A
passing validator proves the retained records are structurally consistent,
portable, provenance-linked, and reconciled; it does not prove ARM compilation,
connected hardware, or audible behavior.

## Repository map

| Path | Responsibility |
| --- | --- |
| `docs/` | Project context, architecture, decisions, and bounded tasks |
| `schemas/` | Versioned machine-readable contracts that already exist |
| `tools/inventory/` | Raw and Java-resolved inventory tooling |
| `tools/catalog/` | Semantic-overlay validation tooling |
| `tools/contracts/` | Device-profile/instrument canonicalization and read-only validation |
| `catalog/` | Source locks, frozen evidence, reviews, and semantic overlays |
| `contracts/` | Versioned authoritative device-profile and instrument records |
| `legacy/ksoloti-bridge/` | Isolated Ksoloti Java compatibility work |
| `packages/` | Future headless model, compiler, and CLI packages |
| `apps/` | Future user-facing applications |

No license has been selected for Schuss yet. Upstream source licenses remain
independent and must not be inferred from their directory or catalog location.
