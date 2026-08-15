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
| 4 contract gate | Schema ownership, compiler stages, and evidence separation | Complete; accepted Task 004 architecture |
| 5 | Minimal Gills device-profile and instrument schemas | Complete |
| 6 | Component-contract, implementation-binding, and DSP-graph schemas | Complete |
| 7 | Compute-target, backend-capability, build, artifact, and evidence schemas | Complete; Task 007 contract gate |
| 8 | Shared headless validation and typed operation layer | Next; begins with validator-core consolidation |
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
validated 26-family manual pilot. Task 004 remains the accepted architecture:
`docs/SCHEMA_STRATEGY.md`, `docs/COMPILER_STRATEGY.md`, and ADRs 0005-0007
define the family/contract/binding boundary, one-way references, compiler
stages, and build-evidence separation without implementing schemas or code
generation.

Tasks 005, 006, and 007 are complete. Task 005 adds the minimal Gills device-profile
and instrument boundary. Task 006 adds the exact Crossfader family companion,
three component signatures and legacy seam maps, the authoritative one-node
`blend` graph, transparent-compound validation, and exactly resolved
instrument revision 2 while retaining revision 1. Task 007 adds reusable
target/backend/build-domain schemas, the smallest truthful Ksoloti production
closure, a pure fail-closed resolver, and future result/evidence fixtures. The
production candidate remains unresolved and no backend stage ran. Task 008 is
next: first consolidate the one-way validator stack into a lower shared core,
then define shared headless typed operations. The completed boundaries are in
`docs/DEVICE_INSTRUMENT_CONTRACTS.md` and
`docs/COMPONENT_GRAPH_CONTRACTS.md`, and
`docs/TARGET_BACKEND_BUILD_CONTRACTS.md`.

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
