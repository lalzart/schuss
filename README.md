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
Task 027 is complete for exact record set `schuss-record-set-000020@1`: the
exact nineteen-object extended library and fifty-three attributed factory
candidates are reviewed without changing the sixty functional families, and
Mutable-derived ancestry is exposed only as an additive provenance facet. The
only new catalog implementation is an unresolved, catalogued-only Rings
resonator variant; no compiler or device support follows.
Task 028 is complete for exact record set `schuss-record-set-000021@1`: fifteen
exact candidates now resolve independently and lower to normalized operation
IR, expanding the counted direct palette from five to twenty. The additions
cover sources, envelopes/modulation, gain/mixing/routing, filtering/resonance,
timing, and state. Evidence stops at level 3; no generated source, ARM build,
Java/AXP route, device, realtime/resource, or audible result follows. Rings
reverb and physical resonator support remain gated, and transparent compounds
remain deferred.
Task 029 is complete for exact record set `schuss-record-set-000022@1`: two
source-evidenced Gills machine presentations are available for read-only
inspection, while zero completed machines are accepted. Task 030 is complete
for exact record set `schuss-record-set-000023@1`: all 56 exactly attributed
Mutable-derived entries are catalogued as individual implementation objects
across 107 function-first families. CLI v3 adds shared `catalog objects`
discovery; all 50 additions remain catalogued-only and unresolved.
Task 031 is complete locally under
[ADR 0016](docs/decisions/0016-adopt-portable-desktop-host-runtime.md) for
exact record set `schuss-record-set-000027@1`. The exact Task 026 seven-node
profile now lowers to a canonical derived host package, executes through the
JUCE-independent C++17 `schuss_rt` runtime, and produces a byte-reproducible
offline WAV. A separate headless JUCE adapter and process-local core services
provide explicit device inspection and audio-session lifecycle. One bounded
Mac callback observation passed with no xruns; it is not general real-time or
audible evidence, and no physical MIDI input was available.
Task 032 is complete locally for exact record set
`schuss-record-set-000029@1`. Bounded acyclic graph shapes made only from those
seven host node types now share one registry-based runtime, and one prepared
successor can replace the active graph at a block boundary with reset state.
The host DSP palette did not widen, and physical-device, general real-time,
audible, packaging, and release claims remain separate.
The explicitly authorized unnumbered desktop lane is locally implemented
through its build/device workflow. `apps/schuss_desktop/` is the sole maintained
React/Tauri product UI: it combines object browsing and project-backed node
patching with core-owned build jobs, explicit Ksoloti identity/compatibility,
and an explicit read-back-verified volatile-RAM upload path over the shared
operation layer.
The explicitly authorized AI lane now includes a separate local MCP adapter
and sonic-first project authoring. `bin/schuss-mcp` exposes seven read-only
discovery/planning tools by default. An explicit absolute project argument adds
bounded transparent-compound/native-kernel drafts, deterministic host
audition, exact preview/accept, and project-object inspection through the same
canonical operations. It contains no model provider, target lowering, build,
device, arbitrary filesystem, or network authority.
No Ksoloti hardware action was performed for these implementations. Firmware/SD
mutation, packaging, remote publication, sustained real-time/resource evidence,
and audible evidence remain separate gates.

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
- [Task 027 contract](docs/tasks/027-mutable-instruments-catalog-provenance.md):
  completed exact extended-source review and additive Mutable-derived catalog
  provenance with the existing function-first taxonomy preserved.
- [Task 028 contract](docs/tasks/028-twenty-item-direct-palette.md): completed
  fifteen-item direct selection/lowering tranche and exact twenty-item counted
  palette, with levels 4-8 explicitly not run.
- [Task 029 machine contract](docs/GILLS_MACHINE_IMPLEMENTATION_CONTRACT.md):
  completed source-evidenced inspection layer with zero completed machines.
- [Task 030 contract](docs/tasks/030-complete-mutable-catalog-and-object-cli.md):
  completed exact Mutable-derived catalog cohort and implementation-object CLI.
- [Task 031 host-runtime contract](docs/DESKTOP_HOST_RUNTIME_IMPLEMENTATION_CONTRACT.md):
  completed portable runtime, deterministic offline renderer, headless JUCE
  adapter, and process-local audio-session boundary.
- [Task 032 variable-graph host contract](docs/tasks/032-variable-graph-desktop-host-runtime.md):
  completed bounded graph execution and safe reset-state patch replacement
  using only the seven existing host node types.
- [Desktop patcher contract](docs/tasks/ui-desktop-patcher-authoring.md):
  consolidated object browsing and project-backed graph authoring in the one
  maintained desktop product UI.
- [Desktop performance contract](docs/tasks/ui-desktop-authoring-performance.md):
  bounded exact-context reuse, semantic caching, and recoverable editor states.
- [AI/MCP boundary](docs/AI_MCP_BOUNDARY.md): the local MCP adapter, exact tool
  modes, project-authoring safety boundary, protocol compatibility, and gates.
- [AI/MCP task contract](docs/tasks/ai-mcp-read-only-foundation.md): the first
  explicitly authorized AI-client implementation boundary.
- [Sonic AI authoring contract](docs/tasks/ai-sonic-authoring-foundation.md):
  sonic-first candidate lanes, project-local objects, audition evidence,
  preview, and atomic acceptance.
- [Decision log](docs/decisions/README.md): accepted and superseded choices.
- [Development history](docs/HISTORY.md): concise completed-work index and Git
  retrieval instructions.

Normative domain details are in the schema, compiler, device/instrument,
component/graph, target/build, operation, project/workspace, catalog-operation,
and compiler-front-half documents under `docs/`.

## Command line

`bin/schuss` is the product and machine-operation boundary. CLI v3 visibly
exposes validation, application capabilities, catalog, project, graph, Gills,
build, completion, and canonical-operation routes. Most non-project commands
use exact application record set `schuss-record-set-000015@1` by default;
catalog commands use `schuss-record-set-000023@1`. Historical CLI goldens
remain retained separately rather than being rewritten.

Representative read-only commands are:

```bash
bin/schuss validate
bin/schuss application describe
bin/schuss catalog search oscillator
bin/schuss catalog objects --provenance mutable-instruments-derived
bin/schuss graph inspect schuss-graph-000002@1
bin/schuss build plan schuss-build-request-000002@5
bin/schuss gills inspect schuss-instrument-000002@3
```

Build execution requires an exact registered handler, a fresh output root, and
explicit `--execute`. Project writes likewise require exact expectations and
explicit `--write`. Neither command implies device access.

## Local AI/MCP adapter

`bin/schuss-mcp` is a dedicated protocol process, not a chat application. An
MCP host launches it over stdio:

```bash
/absolute/path/to/schuss/bin/schuss-mcp
```

It defaults to exact record set `schuss-record-set-000026@1`. Without a project,
the seven tools cover application capability description, catalog/component/
graph inspection, and sonic-intent planning. To enable project-local object and
patch authoring, the human-owned MCP configuration must supply an absolute
workspace:

```bash
/absolute/path/to/schuss/bin/schuss-mcp \
  --project /absolute/path/to/a/schuss-project
```

Codex can register that exact local stdio command directly:

```bash
codex mcp add schuss -- \
  /absolute/path/to/schuss/bin/schuss-mcp \
  --project /absolute/path/to/a/schuss-project
codex mcp list
```

Schuss validates the complete pinned record set before serving. Codex's default
ten-second MCP startup window is too tight on some hosts, so set
`startup_timeout_sec = 30` for this server in Codex `config.toml`; the full
example is in the boundary document below.

See [AI and MCP boundary](docs/AI_MCP_BOUNDARY.md) for the fourteen-tool project
mode and exact safety/evidence limits.

## Local validation

The ordinary Python suites and current routing guards are read only:

```bash
python3 -m unittest discover -s tools/inventory/tests
python3 -m unittest discover -s tools/catalog/tests
python3 -m unittest discover -s tools/contracts/tests
python3 -m unittest tools.contracts.tests.test_mcp_read_only_server
python3 -m unittest tools.contracts.tests.test_ai_sonic_authoring
python3 tools/contracts/generate_ai_sonic_authoring_records.py --check
python3 tools/contracts/generate_task031_records.py --check
python3 tools/contracts/generate_task031_fixtures.py --check
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
python3 tools/contracts/validate_task027_contract.py
python3 tools/contracts/generate_task027_records.py --check
python3 tools/contracts/validate_task027.py
python3 tools/contracts/validate_task028_contract.py
python3 tools/contracts/generate_task028_records.py --check
python3 tools/contracts/validate_task028.py
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
| `apps/` | Desktop product client plus bounded evidence/reference clients of the shared headless model |

No license has been selected for Schuss. Upstream licenses remain independent
and must not be inferred from repository or catalog placement.
