# Roadmap

The phases are ordered to preserve legacy capability while moving authority
into transparent, typed Schuss models.

| Phase | Outcome | Status |
| --- | --- | --- |
| 1 | Project context and source locking | Established in this scaffold |
| 2 | Raw physical source inventory | Existing baseline migrated; validator retained |
| 3 | Java-resolved object and graph inventory | Established; resolved snapshot frozen |
| 3 review gate | Deterministic inventory review and impact packet | Complete; accepted frozen evidence |
| 4A | Versioned semantic overlay and 20-30-family pilot | Current |
| 4B | Expand the validated reviewed core toward about 150-250 families | Planned only after 4A validation |
| 5 | Minimal Gills device-profile and instrument reference contract | Planned before graph/editor contracts harden |
| 6 | Minimal Schuss graph/backend contract and shared typed operations | Planned |
| 7 | Legacy compilation adapter and `.axp` passthrough proof | Planned |
| 8 | Deterministic structured catalog/graph CLI over shared operations | Planned |
| 9 | Basic object drawer and canvas over shared operations | Planned |
| 10 | Full Gills implementation and parameter/control mapping | Planned |
| 11 | Incremental new graph-to-C++ compiler frontend | Planned |
| 12 | Sampling and asset management | Planned |
| 13 | Additional compute targets and devices | Planned |

## Current gate

Phases 2 and 3 and their review gate are complete. Phase 2 remains an immutable
raw snapshot with two explicit source parse issues. Phase 3 retains the loaded
and post-construction legacy model, including partial, failed, ambiguous,
zombie, and unresolved outcomes. ADR 0004 accepts that evidence with known
limitations. Phase 4A is current and may add only a separate semantic overlay
and a 20-30-family manual pilot. Phase 4B may expand toward roughly 150-250
families only after the pilot model is validated.

## Contract sequence constraints

- Introduce a minimal Gills device-profile and instrument reference contract
  before graph/editor contracts harden; full Gills implementation may remain
  later.
- Define a minimal authoritative Schuss graph/backend contract before lowering
  a new Schuss graph through the legacy adapter.
- Treat the legacy compilation adapter as a backend/passthrough proof. Legacy
  `.axp` is an emitted boundary artifact and never the authoritative Schuss
  graph.
- Expose future catalog and graph operations through one typed operation layer.
  CLI output must be deterministic and structured, and GUI and AI clients must
  use the same operations.

## Promotion rule

A phase advances when its task acceptance tests pass and its unresolved content
is named. Later work may refine a versioned schema but may not rewrite retained
raw evidence or erase diagnostics to make a gate appear clean.
