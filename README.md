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

Schuss has completed the Phase 4A semantic-catalog foundation, the bounded
Task 009 legacy-backend proof, the Task 010 product CLI, and Tasks 011A-011C
of the first non-UI Gills vertical slice:

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
- Task 006 is complete: three exact Crossfader component contracts and legacy
  seam-map companions, one authoritative typed graph, transparent-compound
  validation, and instrument revision 2 close the graph reference exactly;
- Task 007 is complete: reusable target/backend/build-domain schemas, a
  Ksoloti-specific production target/backend/request closure, and a pure
  fail-closed resolver establish the next contract boundary;
- Task 008 is complete: a shared validator core, three independent rule
  modules, one aggregate validator, four versioned headless operations, atomic
  graph transactions, and a minimal canonical-JSON `schuss op` adapter provide
  one client-neutral control plane;
- the Task 009 prerequisite is complete: exact accepted/prospective record-set
  views, a reproducible pinned Java/source/GNU Arm/firmware closure, and a
  closed non-production probe/evidence boundary are validated; the retained
  probe remains `not-authorized` and `not-run`;
- Task 009 is complete for one exact graph slice: an authorized non-production
  probe over binding revision 1 supports binding/eligibility revision 2, the
  ordinary Task 008 resolver emits its unchanged invocation seam, and the
  bounded handler deterministically emits `.axp`, source-map, generated C++,
  ARM object, ELF, and link-map artifacts;
- successor record set `schuss-record-set-000003` revision 1 retains all older
  records byte-identically and records separate evidence levels 1-5; connected
  device, real-time, and audible levels 6-8 remain `not-run`;
- Task 010 provides deterministic human and canonical-JSON commands for the
  four shared operations, exact record-set locator resolution, fixed help, and
  static Bash/Zsh/Fish completion without adding a backend-execution path; and
- Task 011A derives a 28-family client-neutral projection from the frozen
  26-family pilot plus two reviewed Gills-slice families, adds `catalog.search`
  and `catalog.inspect` through additive operation v2 contracts, and exposes
  them through the same dispatcher and product CLI;
- Task 011B adds six exact component contracts/bindings, one eight-node and
  nine-connection authoritative graph, one exact Gills instrument mapping,
  and successor record set `schuss-record-set-000005` revision 1; its build
  request remains fail-closed with only the promoted Crossfader selected and
  no backend invocation;
- Task 011C executes six bounded probes, promotes their exact bindings and
  eligibilities, expands only the required legacy forms, and produces
  deterministic `.axp`, source-map, C++, ARM object, ELF, link-map, and
  level-1-through-5 evidence for the exact eight-node slice; and
- Task 012A adds a portable exact project manifest, immutable project/graph
  revision history, deterministic write plans, exclusive local coordination,
  prior-or-successor recovery, additive v3 project operations, and persistent
  CLI graph transactions without changing accepted v1/v2 operation bytes;
- Task 013 adds one immutable, backend-neutral compiler context and pure
  `plan_build` entry point through stage 6, five content-addressed planning
  artifacts, origin maps, and additive `build.plan` operation v4 without
  backend execution; and
- Task 014 adds one exact handler registry, plan-once execution service,
  operation v5, atomic fresh-root publication, and deterministic product
  `build plan`/`build execute` commands;
- Task 015 adds the first closed normalized Q27 DSP module and directly lowers
  the exact one-node Blend graph to deterministic standalone C++17, with source
  mapping and compiled arithmetic-vector evidence through level 4; and
- no complete multi-node direct frontend, graphical editor, device runtime, or
  desktop app is implemented yet.

Tasks 013-015 are complete. ADR 0010 retires the misinterpreted Task 012B UI
contract. The Task 016 contract and pinned-source prerequisite audit are
complete, but implementation awaits one explicit choice between recommended
legacy-equivalent behavior and a separately designed Schuss-native sound. Task
017 has a concrete contract and waits for Task 016. The object drawer and
transparent graph canvas remain an unnumbered later UI milestone requiring new
explicit authorization.

Start with [the project context](docs/PROJECT_CONTEXT.md), then read
[the architecture](docs/ARCHITECTURE.md),
[the schema strategy](docs/SCHEMA_STRATEGY.md),
[the compiler strategy](docs/COMPILER_STRATEGY.md), and
[the roadmap](docs/ROADMAP.md). The Task 006 boundary is documented in
[the component and graph contracts](docs/COMPONENT_GRAPH_CONTRACTS.md), and the
Task 007 boundary in
[the target, backend, build, and evidence contracts](docs/TARGET_BACKEND_BUILD_CONTRACTS.md).
[The shared operation contracts](docs/OPERATION_CONTRACTS.md) document the Task
008 dispatcher, atomic transaction, process, and Task 009 seam boundaries.
[The catalog operation contract](docs/CATALOG_OPERATIONS.md) documents the Task
011A projection, matching, filters, inspection chain, and evidence limits.
[The project/workspace contracts](docs/PROJECT_WORKSPACE_CONTRACTS.md) document
the Task 012A portable closure, persistence, lock, recovery, operation, and CLI
boundaries. [The compiler-front-half contract](docs/COMPILER_FRONT_HALF.md)
documents the completed Task 013 planning boundary, and
[the Task 013 completion report](docs/tasks/013-reusable-compiler-front-half.md)
records its exact evidence. The Task 012B file is a
retirement notice, not an implementation contract.
The Task 011B component, graph, and unresolved build closure is documented in
[the component and graph contracts](docs/COMPONENT_GRAPH_CONTRACTS.md) and
[the target/build contracts](docs/TARGET_BACKEND_BUILD_CONTRACTS.md). The
completed Task 011C-015 work and the gated Task 016-017 contracts are bounded
by their task files under `docs/tasks/`.

## Command-line interface

`bin/schuss` is the product and machine-operation boundary:

```bash
bin/schuss validate [--record-set MANIFEST] [--json]
bin/schuss catalog search [QUERY] [FILTER ...] [--record-set MANIFEST] [--json]
bin/schuss catalog inspect FAMILY_ID@REVISION [--record-set MANIFEST] [--json]
bin/schuss graph inspect GRAPH_ID@REVISION [--record-set MANIFEST] [--json]
bin/schuss graph transact GRAPH_ID@REVISION --edits FILE_OR_STDIN [--record-set MANIFEST] [--json]
bin/schuss build resolve REQUEST_ID@REVISION [--record-set MANIFEST] [--json]
bin/schuss build plan REQUEST_ID@REVISION [--record-set MANIFEST] [--json]
bin/schuss build execute REQUEST_ID@REVISION --output-root DIRECTORY --execute [--record-set MANIFEST] [--json]
bin/schuss build completion {bash|zsh|fish}
bin/schuss project init --project WORKSPACE --project-id ID --record-set MANIFEST --graph GRAPH_ID@REVISION [--json]
bin/schuss project inspect --project WORKSPACE [--json]
bin/schuss project validate --project WORKSPACE [--json]
bin/schuss project transact GRAPH_ID@REVISION --project WORKSPACE --expected-project PROJECT_ID@REVISION --project-content-hash HASH --graph-content-hash HASH --edits FILE_OR_STDIN --write [--json]
bin/schuss project op --project WORKSPACE --request REQUEST_FILE_OR_STDIN --json
bin/schuss project completion {bash|zsh|fish}
bin/schuss completion {bash|zsh|fish}
bin/schuss op --request REQUEST_FILE_OR_STDIN --json
```

Human output is deterministic plain text. `--json` emits the exact canonical
shared-operation result plus one LF. Catalog commands default to exact successor
record set `schuss-record-set-000004` revision 1. Every pre-existing command
keeps accepted record set `schuss-record-set-000001` revision 1 as its default;
other later sets are explicit opt-ins. Task 014 `build plan` and `build
execute` default to exact record set `schuss-record-set-000008` revision 1;
`build resolve` stops before backend lowering, while `build execute` requires
an exact handler, fresh output root, and explicit `--execute`. The original
`graph transact` remains a non-persisted proposal;
`project transact` writes only with explicit exact project/graph expectations
and `--write`. No progress protocol is exposed.

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
python3 tools/catalog/validate_task011a_catalog.py
python3 tools/contracts/validate_task011b.py
python3 tools/contracts/validate_task012a.py
python3 tools/contracts/validate_task013.py
python3 tools/contracts/validate_task014.py
python3 tools/contracts/validate_task015.py
python3 tools/contracts/validate_task016_contract.py
python3 tools/contracts/validate_task017_contract.py
python3 tools/contracts/validate_backbone_governance.py
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
| `tools/contracts/` | Contract canonicalization, exact-reference resolution, and read-only validation |
| `catalog/` | Source locks, frozen evidence, reviews, and semantic overlays |
| `contracts/` | Versioned family, component, binding, graph, device, instrument, target, backend, eligibility, environment, and request records |
| `legacy/ksoloti-bridge/` | Isolated Ksoloti Java compatibility work |
| `packages/` | Shared headless control plane and future compiler/CLI packages |
| `apps/` | Future user-facing applications |

No license has been selected for Schuss yet. Upstream source licenses remain
independent and must not be inferred from their directory or catalog location.
