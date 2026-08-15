# ADR 0008: Defer UI until the headless backbone is ready

- Status: superseded by ADR 0009
- Date: 2026-08-15

ADR 0009 removes this document's compiler/backbone readiness gate after Task
012A established the durable shared project boundary. This decision remains as
historical context only and no longer blocks Task 012B.

## Context

The original roadmap combined a basic object drawer, transparent graph canvas,
durable project/workspace behavior, and persistent graph editing under Phase
12. Tasks 008, 010, and 011A established shared headless operations and a
deterministic CLI, but graph transactions remain non-persisted proposals and
the product CLI cannot execute a general build. Task 011C reaches ARM
compile/link only through one bounded legacy-backend slice.

Implementing a GUI now would force it to depend on unsettled project,
persistence, build-execution, and compiler boundaries. Those boundaries must
be usable without a GUI because the CLI, future GUI, and future AI clients are
required to share the same operations and semantic model.

## Decision

Split the old Phase 12 plan:

- Task 012A owns the non-UI durable project/workspace format and persistent
  CLI graph-authoring boundary.
- Task 012B retains the object drawer and transparent graph canvas but is
  deferred until the roadmap's headless-backbone readiness gate passes.

Stage the old Phase 13 compiler jump as a sequence: reusable compiler front
half, shared build execution, normalized DSP representation and minimal direct
frontend, then complete-slice direct-frontend expansion. Follow that backbone
with a bounded reviewed-core expansion before resuming UI work.

The UI remains a client. It may not define separate catalog, graph, project,
build, compiler, persistence, or device semantics. Existing completed task
reports retain their historical references to the former combined Phase 12;
current planning documents use the split labels.

## Consequences

Near-term work is CLI-first and headless. The next two proposed tasks are Task
012A and Task 013A. UI implementation has no active target date and cannot be
used to repair missing project or compiler behavior.

Deferral does not remove the intended object drawer or graph canvas from
Schuss. Once the readiness gate passes, Task 012B can consume the same exact
project, catalog, graph, build, diagnostic, and compiler operations already
proved through the CLI.
