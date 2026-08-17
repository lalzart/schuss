# Desktop UI boundary

Status: unnumbered structural initialization complete; product UI not started.

## End-to-end boundary

```text
future React/TypeScript presentation
        -> capability-limited desktop adapter (not implemented)
        -> one versioned Schuss operation request
        -> existing packages/schuss_core dispatcher and services
        -> canonical Schuss operation result
        -> presentation rendering only
```

The future application boundary is `apps/schuss_desktop/`, targeting a Tauri 2
shell and a React/TypeScript frontend. The stack choice does not create a
runnable client in this task. Transport, Tauri commands, Rust permissions,
Python process management, packaging, and runtime dependencies remain
unselected and unimplemented.

## Semantic ownership

The existing Schuss Python core and its versioned operations remain the sole
source of catalog, component, graph, instrument, project/workspace,
compiler-plan, build, and evidence semantics. The desktop may construct one
allowed versioned request and render its canonical result. It may not:

- read or edit catalog source files as application state;
- load, rewrite, or persist semantic JSON records directly;
- scan project directories to infer record membership;
- create a UI-private graph edit language, persistence format, compiler path,
  diagnostic meaning, or result projection; or
- infer a newer revision, capability, readiness, build, device, real-time, or
  audible claim.

Selection, viewport, panel layout, and unsaved form values are UI-owned
ephemeral state. Coordinates and groups may later live in a versioned
presentation overlay, but that overlay must reference stable semantic IDs and
must never redefine a node, connection, family, graph, or project.

The machine-readable `schuss-desktop-core-boundary-v1` contract lists zero
runtime capabilities because no adapter exists. Its phased operation lists are
planning allowlists, not implemented routes or authorization. Unknown
operations, schema versions, and result shapes must fail closed.

## Capability phases

### 1. Read-only catalog browsing

The first separately authorized visual slice should call
`application.describe`, `catalog.search`, and `catalog.inspect`. It should
present function-first browsing, form filters, provenance, readiness, and exact
family inspection from canonical results. It must not cache a second catalog
database or write classifications back from the UI.

### 2. Graph visualization

After the catalog slice is accepted, a read-only graph view should call
`graph.inspect` and render the exact graph plus component-contract closure.
React Flow is a likely presentation library, but library selection and package
installation belong to that later task. Canvas coordinates, zoom, selection,
and collapsed groups are presentation state; compound internals remain
inspectable and the graph remains core-owned.

### 3. Project mutation through existing operations

Only after Task 027 is accepted complete and UI implementation is explicitly
authorized may a later slice expose project changes. Proposal, persistence,
history, and revert must use the existing `graph.transact`,
`project.graph.commit`, `project.init`, `project.inspect`,
`project.validate`, `project.profile.fork`, `project.profile.transact`,
`project.history.inspect`, and `project.revert` operations with their exact
references and write-intent gates. The UI never edits workspace JSON files.

Build progress and structured diagnostics additionally depend on the future
Task 027 session/job boundary. Build, device upload, real-time, and audible
behavior are not part of these three visual steps.

## Initialization structure

The directory intentionally contains documentation, a private dependency-free
`package.json`, an inert TypeScript configuration, and reserved `src/` and
`src-tauri/` directories only. The static validator freezes that boundary and
fails when product source, Rust/Tauri runtime files, dependencies, lockfiles,
copied semantic records, or operation metadata drift appears without a new
accepted task.

This initialization is not Task 028. ADR 0014 already reserves Task 028 for
the second catalog/compiler tranche and transparent compounds. The desktop
work stays in the unnumbered UI-architecture lane, and completing this bounded
initialization does not complete the broader architecture milestone or
authorize a visual implementation slice.
