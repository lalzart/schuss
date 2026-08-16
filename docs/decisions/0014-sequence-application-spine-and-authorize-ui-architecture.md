# ADR 0014: Sequence the application spine and authorize UI architecture

- Status: accepted
- Date: 2026-08-16
- Extends: ADR 0010

## Context

Tasks 013-021 established the shared compiler front half, deterministic build
execution, direct C++ path, curated core, complete Gills contracts, and one
corrected connected-device observation. Task 022 then retained a failed panel
diagnostic result after its last-moved telemetry proved too sensitive to normal
ADC variation. That diagnostic gap does not block safe offline development of
the catalog, compiler, shared operations, CLI, or application architecture.

Schuss now has strong headless pieces but not yet one coherent application
spine. Some implemented project and build operations remain deliberately
separate from the accepted root help/completion surface, the reviewed catalog
covers only a bounded subset of the frozen legacy observations, the direct
compiler supports only a narrow exact slice, and no client can yet create a
complete project from an empty workspace through a normal authoring flow.

The user explicitly selected continued CLI/compiler/catalog development and
authorized UI architecture planning. They did not authorize another hardware
diagnostic, UI implementation, Task 019 sampling work, Task 020 target/device
expansion, or Git publication as part of this decision.

## Decision

Schuss adopts the application-spine sequence defined in
`docs/APPLICATION_SPINE_PLAN.md`:

1. Task 023: CLI v2 and application-surface consolidation.
2. Task 024: complete catalog coverage and deterministic curation pipeline.
3. Task 025: direct-compiler core-library tranche for the selected effects
   reference.
4. Task 026: complete client-neutral authoring operations and CLI workflow.
5. Task 027: client-neutral application sessions, jobs, and diagnostics.
6. Task 028: second catalog/compiler tranche and transparent compounds.

Task 023 is the next planned task. Planning acceptance does not activate its
implementation, create its task contract, or authorize any later task.
Tasks 019 and 020 remain deferred.

UI architecture is explicitly authorized as an unnumbered planning milestone.
It may define client boundaries, state ownership, transport, interaction,
wireframes, fixtures, packaging constraints, and a technical spike. UI
implementation remains separately gated and must consume the same catalog,
graph, project, compiler, build, and diagnostic operations as CLI and AI
clients. This decision does not revive retired Task 012B.

A numbered parent may declare exact lettered children such as `023A`, `023B`,
and `023C`. Those identifiers are child work packages, not aliases or
independent roadmap tasks. The parent contract must define each child's scope,
dependencies, acceptance contribution, and write ownership before any child is
started. Completion of one child never completes or activates another parent.

Parallel work is permitted only under the ownership and integration rules in
the application-spine plan. Shared schemas and operations, stable-ID and
record-set allocation, authoritative graph/instrument/build records, current
status documents, and publication remain serialized single-writer surfaces.
The default maximum is two implementation lanes plus one read-only or design
lane.

The Task 022 diagnostic successor is not on the application-spine critical
path. Complete connected panel evidence remains an explicit proof gap and must
be revisited before Schuss claims complete hardware-control support or release
readiness.

## Consequences

Catalog expansion is coupled to a concrete authoring and compiler consumer
rather than treated as an unbounded mass-import exercise. Compiler breadth is
proved against exact reference graphs, while catalogued, contracted, bound,
compile-proven, device-tested, real-time-tested, and audible readiness remain
separate.

The first UI work is architecture, not a private semantic implementation. A
later vertical slice may begin only after its shared authoring and job
boundaries are accepted. Hardware upload, firmware flash, SD-card write,
staging, commit, push, and publication retain their independent approval
gates.
