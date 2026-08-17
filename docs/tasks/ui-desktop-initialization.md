# Unnumbered UI architecture: desktop initialization

Status: accepted and complete on 2026-08-17 at structural level only.

This is an unnumbered child boundary within the UI-architecture lane authorized
by ADR 0014. It is not Task 028: that identifier remains reserved for the
second catalog/compiler tranche and transparent compounds. The historical
Task 012B remains retired.

## Goal and why it exists

Establish one inert desktop-application boundary for a future Tauri 2 shell
with a React and TypeScript frontend, while keeping the existing Schuss Python
core and its versioned operations as the sole source of catalog, project,
graph, compiler-plan, and build semantics. This gives later visual work an
explicit home and a fail-closed ownership contract without starting product UI
implementation.

## In scope

- Create `apps/schuss_desktop/` with documentation and dependency-free,
  non-product configuration for the intended Tauri 2, React, and TypeScript
  stack.
- Define a versioned desktop-to-core contract that permits only named Schuss
  operations and canonical operation results.
- Separate core-owned semantic state from UI-only selection, layout, viewport,
  and panel state.
- Add deterministic static validation for the exact initialization structure,
  shared-operation references, dependency-free state, and absence of semantic
  record ownership inside the application tree.
- Record the order of the first later visual slices: read-only catalog
  browsing, graph visualization, and only then project mutation through
  existing operations.
- Reconcile current status and indexes without changing numbered-task
  allocation.

## Out of scope

- React components, HTML application entry points, styles, a graph canvas,
  React Flow integration, drawers, inspectors, drag/drop, or other product UI.
- Tauri commands, Rust source, Cargo metadata, a Python/Rust process bridge,
  transport selection, session/job implementation, or packaging.
- New or changed Schuss operations, schemas, catalog semantics, project or
  graph persistence, compiler behavior, build execution, or backend code.
- Package installation, lockfiles, downloaded dependencies, Rust/Node/Tauri
  setup, ARM or Java/legacy builds, hardware action, device/real-time/audible
  evidence, staging, commit, push, or publication.
- Any Task 028 catalog/compiler or palette-expansion work, any rewrite of
  retained task history, or revival of Task 012B.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADR 0014,
`docs/APPLICATION_SPINE_PLAN.md`, `docs/ARCHITECTURE.md`,
`docs/SCHEMA_STRATEGY.md`, `docs/OPERATION_CONTRACTS.md`,
`docs/PROJECT_WORKSPACE_CONTRACTS.md`, the live application capability
description, and the inherited dirty worktree state.

Deliverables are:

1. the inert `apps/schuss_desktop/` boundary and local documentation;
2. `schuss-desktop-core-boundary-v1`, containing no runtime capability and a
   closed, phased plan over existing operation names;
3. `docs/DESKTOP_UI_BOUNDARY.md`, including the ownership and next-slice plan;
4. a read-only deterministic validator plus negative tests; and
5. narrowly reconciled current routing that keeps Task 028 unchanged.

## Acceptance tests

1. The application tree contains only the exact documented initialization
   files; no `.tsx`, `.jsx`, `.rs`, HTML, CSS, Cargo, Tauri runtime, or lockfile
   exists.
2. `package.json` is private, declares the future stack, contains no dependency
   declarations, and exposes only the repository static validator.
3. The versioned boundary declares zero runtime capabilities because no
   transport exists, and lists only operations present in the shared Schuss
   capability registry for later phases.
4. Every planned operation retains its shared request schema, result schema,
   and effect class; the desktop contract defines no client-private operation
   or result shape.
5. The boundary rejects direct UI mutation of semantic JSON, catalog files, or
   project workspaces and keeps UI-only state separate.
6. Static validation fails closed when product source, a copied semantic
   record, a dependency declaration, or capability-plan drift is introduced.
7. The validator is read-only, CWD-independent, deterministic, and emits one
   canonical JSON line.
8. Current documentation states that this unnumbered initialization is
   complete, the broader architecture lane remains open, and UI implementation
   is still separately gated.
9. Focused and adjacent tests pass, followed by one final repository aggregate
   validation after the diff and acceptance matrix are frozen.
10. No dependency installation, backend/build/hardware action, Git staging or
    publication occurs.

## Validation cadence

- Focused: run `python3 -m unittest
  tools.contracts.tests.test_desktop_ui_structure` and
  `python3 tools/contracts/validate_desktop_ui_structure.py`.
- Adjacent regression: run
  `python3 -m unittest tools.contracts.tests.test_backbone_governance
  tools.contracts.tests.test_task023_application_capabilities` because the task
  changes current UI routing and pins existing capability metadata.
- Expensive reproduction: none. The focused test itself exercises the static
  validator from two CWDs and verifies unchanged governed bytes.
- Final aggregate: after the implementation-freeze review, run the inventory,
  catalog, and contract unittest discovery suites once. Do not run ARM, Java,
  connected-device, real-time, or audible checks.

## Decisions this task may make

- The exact `apps/schuss_desktop/` initialization paths and inert metadata.
- The version-1 client-boundary document shape and closed phase ordering.
- Which UI-only transient state names are reserved without defining their
  product behavior.
- The static validation diagnostics needed to freeze this structure.

## Decisions this task must not make

- Number or redefine Task 028, activate Task 027, declare the complete UI
  architecture milestone accepted, or authorize the UI vertical slice.
- Define catalog classification, graph or project semantics, persistence,
  compiler/build behavior, or a UI-specific operation.
- Select or implement the Tauri-to-Python transport, Tauri commands, Rust
  permissions, session/job behavior, React components, React Flow, or package
  versions.
- Add semantic records, schemas, record sets, dependencies, lockfiles,
  generated artifacts, build evidence, or device claims.
- Stage, commit, push, publish, upload, flash, or write an SD card.

## Retained validation result

The five focused desktop tests and fourteen adjacent governance/application-
capability tests pass. The final inventory and catalog aggregates also pass at
14/14 and 6/6 respectively. The final contract aggregate ran once: 344 tests,
with five failures, three errors, and one skip. No desktop-initialization or
adjacent-governance test failed.

The three errors are inherited Task 024/025 reproduction checks that require
the absent ignored `catalog/sources.local.yml`: one Task 024 generation check
and two Task 025 source-authority/generation checks. This task did not create
machine-local source configuration. The five failures are inherited legacy
stdout/result/human golden drift in Task 008, Task 009, Task 010 twice, and
Task 011A. Their expected hashes and the modified core/record-set surfaces
predate this task and are outside its UI-only ownership. This task did not
rewrite historical goldens or alter catalog/compiler behavior to hide them.

The repository-wide contract aggregate is therefore explicitly not green.
That is a retained external validation gap, not desktop structural evidence.
The exact added boundary remains valid, deterministic, read-only, and free of
runtime capabilities or semantic records under its focused and adjacent
checks.

## Completion boundary

Completion establishes directory, documentation, and static-contract evidence
only. It does not produce a runnable desktop application, satisfy the complete
UI-architecture milestone, activate Task 027 or Task 028, or authorize any
visual slice. Each later slice requires its own accepted boundary, and project
mutation additionally waits for the application session/job/diagnostic gate
and explicit UI-implementation authorization.
