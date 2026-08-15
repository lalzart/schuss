# ADR 0010: Restore the backend-first sequence and retire Task 012B

- Status: accepted
- Date: 2026-08-15
- Supersedes: ADR 0009
- Reaffirms: ADR 0008's backend-first direction

## Context

The headless-backbone plan originally split durable project work from a
deferred UI milestone. It named the completed persistence task Task 012A and
the next compiler task Task 013A, while leaving Task 012B attached to the old
UI idea. That mixture made the phrase “the next two tasks” sound like Tasks
012A and 012B even though the active backend sequence meant Tasks 012A and
013A.

After Task 012A completed, a request to remove the mistaken 12B blockage was
interpreted as permission to reactivate the old UI task. ADR 0009 then made an
object drawer and graph canvas immediate work, contrary to the user's stated
priority to continue strengthening the CLI, compiler, and backend before UI.

The same plan also used `B6` as shorthand for “backbone step 6” because older
roadmap numbers 14-16 already named unimplemented future phases. That
placeholder mixed phase, task, and sequence labels and made the roadmap harder
to follow.

## Decision

Retire Task 012B. It is not an active or deferred implementation task and must
not be run. The object drawer and transparent graph canvas remain an unnumbered
future UI milestone requiring new explicit user authorization.

Use one ordinary integer sequence for the active backbone:

1. Task 013: reusable compiler front half and deterministic planning artifacts.
2. Task 014: shared build execution and product CLI.
3. Task 015: normalized DSP representation and minimal direct graph-to-C++
   frontend.
4. Task 016: direct frontend for the complete Task 011C graph.
5. Task 017: curated core expansion and richer headless reference instruments.

The older unimplemented Phase 14-16 placeholders move to Tasks 018-020:

- Task 018: full Gills implementation and parameter/control mapping;
- Task 019: sampling and asset management; and
- Task 020: additional compute targets and devices.

Completed historical task reports may retain the roadmap labels that were
current when they completed. Active planning documents and executable task
contracts use the sequence above. Planning must not introduce lettered or
informal task labels merely to avoid renumbering unstarted future work.

## Consequences

Task 013 is the one immediate next task. Tasks 014-017 follow in numerical
order. No UI task is active, and a request to run Task 012B must stop at its
retirement notice instead of resolving to graphical-client work.

ADR 0009 and its UI contract remain visible only as historical evidence of the
misinterpretation. They have no authority over current task selection.
