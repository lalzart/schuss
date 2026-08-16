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
one exact mapped level-5 runtime closure.

The reviewed Task 017 core remains structurally useful but not yet generally
executable. Its two full-panel successors retain stable unsupported
diagnostics. Connected-device, real-time, and audible proof for the successful
mapped reference remain separate and require new authorization.

## Start here

- [Project context](docs/PROJECT_CONTEXT.md): stable purpose, layers, and
  principles.
- [Development status](docs/STATUS.md): current task, exact boundary, and proof
  gaps.
- [Architecture](docs/ARCHITECTURE.md): ownership and dependency direction.
- [Roadmap](docs/ROADMAP.md): current gate and later decisions.
- [Decision log](docs/decisions/README.md): accepted and superseded choices.
- [Development history](docs/HISTORY.md): concise completed-work index and Git
  retrieval instructions.

Normative domain details are in the schema, compiler, device/instrument,
component/graph, target/build, operation, project/workspace, catalog-operation,
and compiler-front-half documents under `docs/`.

## Command line

`bin/schuss` is the product and machine-operation boundary. Use
`bin/schuss --help` and subcommand help for the complete fixed grammar.

Representative read-only commands are:

```bash
bin/schuss validate
bin/schuss catalog search oscillator
bin/schuss graph inspect schuss-graph-000002@1 \
  --record-set contracts/record-sets/task011c-executed-v1.json
bin/schuss build plan schuss-build-request-000002@3 \
  --record-set contracts/record-sets/task016-complete-gills-direct-v1.json
bin/schuss build plan schuss-build-request-000002@4 \
  --record-set contracts/record-sets/task018-full-gills-v1.json
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
