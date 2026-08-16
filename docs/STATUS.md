# Development status

This document is the single authority for Schuss's current development state.
Stable product intent belongs in `PROJECT_CONTEXT.md`, architecture belongs in
the architecture and contract documents, accepted decisions belong in ADRs,
and completed work belongs in `HISTORY.md` and retained evidence.

## Current direction

Task 018 is complete for exact record set `schuss-record-set-000012@1`. One
authenticated 63-slot Gills panel model, three immutable instrument
successors, total coverage, exact runtime realizations, shared inspection, and
one mapped local level-5 ARM build are retained. No product task is
automatically active after this completion.

Task 012B remains retired. The object drawer and transparent graph canvas are
an unnumbered future client milestone that requires explicit user
authorization.

Tasks 019 and 020 are deferred and not automatically activated by completion
of Task 018.

## Accepted implementation boundary

| Boundary | Accepted result | Highest evidence |
| --- | --- | --- |
| Catalog and semantic identity | Frozen inventory, reviewed catalog families, typed contracts, and exact record sets | Structural and provenance evidence |
| Project authoring | Portable projects, immutable graph/project successors, atomic workspace-head persistence, and shared CLI operations | Host persistence evidence |
| Compiler front half | Exact validation, resolution, compound elaboration, dependency/resource planning, and origin mapping | Level 2 |
| Shared execution | Exact handler registration, plan-once execution, fresh-root publication, and product build commands | Level 5 through the retained legacy handler |
| Direct frontend | The accepted eight-node Gills slice lowers without Java or `.axp` under legacy-equivalent semantics | Level 5 |
| Curated core | Twelve reviewed families and two headless reference instruments; missing direct semantics fail closed | Level 2 |
| Full Gills panel/runtime | Authenticated 63-slot census, total mappings/coverage, exact runtime closure, and one mapped direct build | Level 5 |

The accepted Task 018 result proves deterministic local ARM compile/link for
one exact mapped graph/instrument/device/runtime closure. It does not prove
connected-device execution, physical control-panel operation, real-time
safety, audible behavior, or release readiness.

## Completed Task 018 boundary

Task 018 established all of the following:

1. A complete physical-slot census with evidence or explicit unresolved facts.
2. Device-to-instrument, instrument-to-graph, and instrument-to-device mappings
   with deterministic total coverage.
3. An independent runtime realization for pickup, smoothing, transforms,
   gestures, actions, state, feedback, displays, and physical I/O.
4. `schuss-instrument-000002@2` reaches evidence level 5 through the exact
   mapped handler and runtime realization in two fresh roots and processes.
5. The two Task 017 successors retain stable unsupported diagnostics without
   fallback, and levels 6-8 remain `not-run`.

The executable reference reuses the accepted Task 016 eight-node graph and
legacy-equivalent semantic goldens. Panel mapping/runtime code is retained as
separate artifacts and adds no DSP operation.

## Current proof gaps

- The two Task 017 successors do not lower through the direct frontend: one is
  unsupported and one has unresolved compound internals.
- Connected-device, real-time/resource, and audible evidence levels 6-8 remain
  `not-run`.
- The authenticated Task 009 local content store is ignored and must be
  validated separately when present; a clean checkout cannot claim that local
  evidence merely from tracked manifests.
- No desktop application or UI client is implemented.

## Next decision

Task 018 completion does not automatically start sampling, another target, or
UI work. The next decision begins with a separately authorized Gills product
evidence gate for connected-device, control-panel, real-time, and audible
proof. Results from that gate determine whether the next bounded task should
expand direct DSP semantics, add sampling/assets, introduce another target or
device, or begin the future client milestone.
