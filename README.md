# Schuss

Schuss is a modern, CLI-first, source-agnostic environment for designing
embedded musical instruments. It initially targets Ksoloti Core, preserves the
existing firmware, toolchain, and DSP ecosystem through an isolated
compatibility bridge, and treats Gills as a device and instrument platform
above a transparent DSP graph.

Schuss is not replacement firmware or a reskinned Ksoloti Patcher. It is a new
domain model and authoring environment in which catalog discovery, typed DSP
graphs, projects, compiler planning, build execution, and evidence are explicit
and independently versioned.

## Current direction

[Development status](docs/STATUS.md) is the sole current-status authority.
Schuss has a persistent project model, shared CLI operations, a reusable
compiler front half, exact build execution, and deterministic direct ARM
compile/link evidence for one eight-node Gills slice. The
[Task 018 Gills contract](docs/tasks/018-full-gills-implementation-and-parameter-control-mapping.md)
is complete for a 63-slot authenticated panel model, explicit mappings, and
one exact mapped level-5 runtime closure. The
[Task 021 corrective contract](docs/tasks/021-gills-dma-safe-oled-and-connected-device-evidence.md)
preserves those bytes, adds a versioned DMA-safe OLED command path, and retains
one separately authorized exact connected-device observation at level 6.
The [Task 022 control-panel evidence contract](docs/tasks/022-connected-gills-control-panel-evidence.md)
completed its offline diagnostic build at level 5, then retained a failed
connected result after exactly one approved volatile-RAM upload. Board start,
OLED, LEDs, all ten pot slots, and approximate full pot travel were observed,
but ADC jitter destabilized last-moved telemetry; promotion stopped before
level 6 and the Task 021 replacement gate is closed.

[ADR 0014](docs/decisions/0014-sequence-application-spine-and-authorize-ui-architecture.md)
now accepts the [application-spine plan](docs/APPLICATION_SPINE_PLAN.md). The
[Task 023 contract](docs/tasks/023-cli-v2-and-application-surface-consolidation.md)
is accepted and complete: one client-neutral capability description, one
coherent CLI v2 grammar, one exact application record set, and a read-only
cross-service smoke path now form the application boundary. The
[Task 024 contract](docs/tasks/024-complete-catalog-coverage-and-deterministic-curation.md)
is also complete: all 3,602 frozen observations have deterministic factual
lineage dispositions, the current pinned first-party Ksoloti corpus contains
666 normal-definition cohorts plus 19 compounds, the reviewed projection
contains 60 families, and one exact eight-contract packet gates Task 025. Task
025 is complete as a fail-closed partial semantic tranche: five promotions
pass level 2, but the selected reverb allocation is inconsistent and the
complete graph fails before lowering. Task 026 is also complete: a separately
accepted reverb-free seven-node profile now supports project-owned
create/edit/history/revert and deterministic local ARM builds through level 5.
UI architecture is eligible as a separate unnumbered planning lane but has not
started; UI implementation remains separately gated.

The reviewed Task 017 core remains structurally useful but not yet generally
executable. Its two full-panel successors retain stable unsupported
diagnostics. Complete connected control-panel proof was not earned; real-time
and audible proof also remain `not-run` and require new authorization.

## Start here

- [Project context](docs/PROJECT_CONTEXT.md): stable purpose, layers, and
  principles.
- [Development status](docs/STATUS.md): current task, exact boundary, and proof
  gaps.
- [Architecture](docs/ARCHITECTURE.md): ownership and dependency direction.
- [Roadmap](docs/ROADMAP.md): current gate and later decisions.
- [Application-spine plan](docs/APPLICATION_SPINE_PLAN.md): Tasks 023-028,
  lettered children, dependencies, and safe parallel lanes.
- [Task 023 contract](docs/tasks/023-cli-v2-and-application-surface-consolidation.md):
  the completed CLI v2/application-surface boundary.
- [Task 024 contract](docs/tasks/024-complete-catalog-coverage-and-deterministic-curation.md):
  current-Ksoloti-first candidate structure, frozen lineage coverage, 20
  reviewed families with complete overload cohorts, and the exact Task 025
  selection packet.
- [Task 025 contract](docs/tasks/025-direct-compiler-core-library-tranche.md):
  complete fail-closed semantic tranche with five passed promotions and one
  failed reverb boundary.
- [Task 026 contract](docs/tasks/026-complete-authoring-operations-and-cli-workflow.md):
  completed client-neutral empty-workspace-to-project-owned-build workflow over
  the exact reverb-free executable profile.
- [Decision log](docs/decisions/README.md): accepted and superseded choices.
- [Development history](docs/HISTORY.md): concise completed-work index and Git
  retrieval instructions.

Normative domain details are in the schema, compiler, device/instrument,
component/graph, target/build, operation, project/workspace, catalog-operation,
and compiler-front-half documents under `docs/`.

## Command line

`bin/schuss` is the product and machine-operation boundary. CLI v2 visibly
exposes validation, application capabilities, catalog, project, graph, Gills,
build, completion, and canonical-operation routes. Non-project commands use
exact application record set `schuss-record-set-000015@1` by default; the
Task 024 catalog successor is `schuss-record-set-000016@1`. Historical CLI
goldens remain retained separately rather than being rewritten.

Representative read-only commands are:

```bash
bin/schuss validate
bin/schuss application describe
bin/schuss catalog search oscillator
bin/schuss graph inspect schuss-graph-000002@1
bin/schuss build plan schuss-build-request-000002@5
bin/schuss gills inspect schuss-instrument-000002@3
```

Build execution requires an exact registered handler, a fresh output root, and
explicit `--execute`. Project writes likewise require exact expectations and
explicit `--write`. Neither command implies device access.

## Local validation

The ordinary Python suites and current routing guards are read only:

```bash
python3 -m unittest discover -s tools/inventory/tests
python3 -m unittest discover -s tools/catalog/tests
python3 -m unittest discover -s tools/contracts/tests
python3 tools/contracts/validate_backbone_governance.py
python3 tools/contracts/validate_task018_contract.py
python3 tools/contracts/validate_task021_contract.py
python3 tools/contracts/validate_task022_contract.py
python3 tools/contracts/validate_task023_contract.py
python3 tools/contracts/generate_task023_records.py --check
python3 tools/contracts/validate_task023.py
python3 tools/contracts/validate_task024_contract.py
python3 tools/contracts/generate_task024_records.py --check
python3 tools/contracts/validate_task024.py
python3 tools/contracts/validate_task025_contract.py
python3 tools/contracts/generate_task025_records.py --check
python3 tools/contracts/generate_task025_evidence.py --check
python3 tools/contracts/validate_task025.py
python3 tools/contracts/validate_task022.py
```

Some authenticated legacy checks additionally require the ignored local Task
009 content store. Their absence in a clean checkout is not evidence failure or
success; run the explicitly documented authenticated validators when that
store is available. No ordinary validation command uploads, flashes, or writes
hardware.

## Repository map

| Path | Responsibility |
| --- | --- |
| `docs/` | Stable context, status, architecture, decisions, roadmap, and history |
| `schemas/` | Versioned machine-readable contracts |
| `contracts/` | Exact semantic/build records and record-set manifests |
| `catalog/` | Source locks, frozen inventory/review evidence, and semantic overlays |
| `evidence/` | Retained level-specific build and validation evidence |
| `packages/schuss_core/` | Shared headless operations, project, compiler, and execution services |
| `tools/` | Read-only validators plus explicitly gated generators/runners |
| `legacy/ksoloti-bridge/` | Isolated Ksoloti Java compatibility backend |
| `apps/` | Future clients of the shared headless model |

No license has been selected for Schuss. Upstream licenses remain independent
and must not be inferred from repository or catalog placement.
