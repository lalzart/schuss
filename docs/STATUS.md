# Development status

This document is the single authority for Schuss's current development state.
Stable product intent belongs in `PROJECT_CONTEXT.md`, architecture belongs in
the architecture and contract documents, accepted decisions belong in ADRs,
and completed work belongs in `HISTORY.md` and retained evidence.

## Current direction

Task 018 is the only ready product task. Its revised contract is complete, its
Task 016 and Task 017 dependencies are satisfied, and implementation is not
started. The repository-maintenance work that introduced this status document
does not authorize Task 018 semantic records, runtime code, build execution, or
hardware action.

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

The accepted Task 016 result proves deterministic local ARM compile/link for
one exact graph. It does not prove connected-device execution, control-panel
operation, real-time safety, audible behavior, or release readiness.

## Active Task 018 exit gate

Task 018 starts with an authenticated, portable evidence packet for one exact
Gills hardware and panel revision. It must then establish all of the following:

1. A complete physical-slot census with evidence or explicit unresolved facts.
2. Device-to-instrument, instrument-to-graph, and instrument-to-device mappings
   with deterministic total coverage.
3. An independent runtime realization for pickup, smoothing, transforms,
   gestures, actions, state, feedback, displays, and physical I/O.
4. At least one exact mapped Gills reference instrument must reach evidence
   level 5 through the accepted direct build path. Stable unsupported
   diagnostics for the two Task 017 instruments remain truthful evidence but
   do not satisfy this executable promotion gate.
5. Levels 6-8 remain `not-run` unless separately authorized and actually
   performed.

The executable reference may reuse the accepted Task 016 eight-node graph and
legacy-equivalent semantics. Task 018 may not invent new DSP behavior merely
to pass this gate.

## Current proof gaps

- No complete authenticated Gills panel census or mapping successor exists.
- The two Task 017 reference instruments do not currently lower through the
  direct frontend: one is unsupported and one has unresolved compound
  internals.
- No mapped Gills runtime closure has reached ARM compile/link.
- Connected-device, real-time/resource, and audible evidence levels 6-8 remain
  `not-run`.
- The authenticated Task 009 local content store is ignored and must be
  validated separately when present; a clean checkout cannot claim that local
  evidence merely from tracked manifests.
- No desktop application or UI client is implemented.

## Next decision after Task 018

Task 018 completion does not automatically start sampling, another target, or
UI work. The next decision begins with a separately authorized Gills product
evidence gate for connected-device, control-panel, real-time, and audible
proof. Results from that gate determine whether the next bounded task should
expand direct DSP semantics, add sampling/assets, introduce another target or
device, or begin the future client milestone.
