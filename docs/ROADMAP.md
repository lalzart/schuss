# Roadmap

The phases are ordered to preserve legacy capability while moving authority
into transparent, typed Schuss models.

| Phase | Outcome | Status |
| --- | --- | --- |
| 1 | Project context and source locking | Established in this scaffold |
| 2 | Raw physical source inventory | Existing baseline migrated; validator retained |
| 3 | Java-resolved object and graph inventory | Established; resolved snapshot frozen |
| 3 review gate | Deterministic inventory review and impact packet | Complete; accepted frozen evidence |
| 4A | Versioned semantic overlay and 20-30-family pilot | Complete |
| 4 contract gate | Schema ownership, compiler stages, and evidence separation | Complete; current accepted Task 004 gate |
| 5 | Minimal Gills device-profile and instrument schemas | Next bounded task after Task 004 |
| 6 | Component-contract, implementation-binding, and DSP-graph schemas | Planned |
| 7 | Compute-target, backend-capability, build, artifact, and evidence schemas | Planned |
| 8 | Shared headless validation and typed operation layer | Planned |
| 9 | One minimal graph through the legacy `.axp` adapter and ARM compiler/linker | Planned |
| 10 | Deterministic structured CLI over shared operations | Planned |
| 4B / 11 | Incremental reviewed-core expansion with actual contracts and bindings | Gated on Phase 6 contract model |
| 12 | Basic object drawer and transparent graph canvas | Planned |
| 13 | Direct Schuss graph-to-C++ frontend behind the backend contract | Planned |
| 14 | Full Gills implementation and parameter/control mapping | Planned |
| 15 | Sampling and asset management | Planned |
| 16 | Additional compute targets and devices | Planned |

## Current architectural gate and next task

Phases 2 and 3 and their review gate are complete. Phase 2 remains an immutable
raw snapshot with two explicit source parse issues. Phase 3 retains the loaded
and post-construction legacy model, including partial, failed, ambiguous,
zombie, and unresolved outcomes. ADR 0004 accepts that evidence with known
limitations. Phase 4A is complete with a separate semantic overlay and a
validated 26-family manual pilot. Task 004 is the current architectural gate:
`docs/SCHEMA_STRATEGY.md`, `docs/COMPILER_STRATEGY.md`, and ADRs 0005-0007
define the family/contract/binding boundary, one-way references, compiler
stages, and build-evidence separation without implementing schemas or code
generation.

Task 005 is next. It is limited to minimal Gills device-profile and instrument
schemas, fixtures, and a read-only validator, including one knob-to-`blend`
mapping and one opaque exact graph target. It does not define graph nodes,
ports, bindings, targets, backends, operations, firmware, GUI/CLI, or
compilation. The exact scope is in
`docs/tasks/004-schema-and-compiler-contract-strategy.md`.

## Contract sequence constraints

- Introduce a minimal Gills device-profile and instrument reference contract
  before graph/editor contracts harden; full Gills implementation may remain
  later.
- Define component-contract, implementation-binding, and authoritative graph
  schemas before lowering a new Schuss graph through any backend.
- Define compute-target, backend-capability, and build/evidence schemas before
  invoking a compiler as Schuss.
- Treat the legacy compilation adapter as a backend/passthrough proof. Legacy
  `.axp` is an emitted boundary artifact and never the authoritative Schuss
  graph.
- Expose future catalog and graph operations through one typed operation layer.
  CLI output must be deterministic and structured, and GUI and AI clients must
  use the same operations.
- Do not let Phase 4B catalog expansion outrun component-contract and binding
  review. Additional families may be curated incrementally, but compiler-facing
  variants require the Phase 6 boundaries.

## Promotion rule

A phase advances when its task acceptance tests pass and its unresolved content
is named. Later work may refine a versioned schema but may not rewrite retained
raw evidence or erase diagnostics to make a gate appear clean.
