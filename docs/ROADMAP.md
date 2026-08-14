# Roadmap

The phases are ordered to preserve legacy capability while moving authority
into transparent, typed Schuss models.

| Phase | Outcome | Status |
| --- | --- | --- |
| 1 | Project context and source locking | Established in this scaffold |
| 2 | Raw physical source inventory | Existing baseline migrated; validator retained |
| 3 | Java-resolved object and graph inventory | Established; resolved snapshot frozen |
| 3 review gate | Deterministic inventory review and impact packet | Packet ready for human review |
| 4 | Functional taxonomy and manual core-library curation | Planned after review gate |
| 5 | New object and catalog schemas | Planned |
| 6 | Headless catalog/search CLI | Planned |
| 7 | Legacy patch compilation adapter | Planned |
| 8 | New graph model and operation protocol | Planned |
| 9 | Basic object drawer and canvas | Planned |
| 10 | Gills device and instrument contract | Planned |
| 11 | Parameter, macro, and physical-control mapping | Planned |
| 12 | New graph-to-C++ compiler frontend | Planned |
| 13 | Sampling and asset management | Planned |
| 14 | Additional compute targets and devices | Planned |

## Current gate

Phases 2 and 3 are complete under `docs/tasks/001-legacy-inventory.md`. Phase 2
remains an immutable raw snapshot with two explicit source parse issues. Phase
3 retains the loaded and post-construction legacy model, including partial,
failed, ambiguous, zombie, and unresolved outcomes. Before Phase 4,
`docs/tasks/002-phase-3-inventory-review-gate.md` must quantify unique material
impact and produce deterministic review samples without changing either
snapshot.

## Promotion rule

A phase advances when its task acceptance tests pass and its unresolved content
is named. Later work may refine a versioned schema but may not rewrite retained
raw evidence or erase diagnostics to make a gate appear clean.
