# Unnumbered UI implementation: unified desktop patcher authoring

Status: implemented locally from explicit user authorization; final user
acceptance and Git publication remain separate.

This is the second product implementation inside the unnumbered desktop UI
lane. It consolidates the accepted read-only catalog application with the
separately explored React Flow patcher direction. It does not promote the
standalone browser prototypes into product applications and does not activate
build execution, USB, device upload, flash, or hardware work.

## Goal and why it exists

Make `apps/schuss_desktop/` the sole maintained Schuss product UI and deliver
the smallest useful project-backed node patcher: list current implementation
objects, open or create an explicit patch workspace, render its exact graph,
propose semantic edits, save them through the shared project service, and
inspect or revert immutable history.

The slice exists because the accepted desktop app currently stops at catalog
browsing while the visual patcher exploration lives in a separate browser app
with copied fixtures and browser-local persistence. Product authoring must use
the same catalog, graph, and project operations as CLI and AI clients.

## In scope

- Integrate the accepted Tauri/React desktop product slice with exact Task 030
  catalog and application capabilities on one implementation branch.
- Keep `apps/schuss_desktop/` as the only product application. The existing
  browser patcher, machine prototype, and machine viewer remain unchanged
  reference implementations during this task.
- Add one read-only shared `component.inspect` operation returning one exact
  governed component contract.
- Add `set-graph-display-name` to a versioned successor of the shared graph
  edit language so the user-facing patch name remains the graph display name.
- Add additive request/result v11, application-capability v4, and exact
  successor record set `schuss-record-set-000024@1` without rewriting accepted
  v1-v10 schemas, records, results, or record sets.
- Update the capability-limited Rust/Python desktop adapter to the exact
  successor context and only the operations required by this slice.
- Present compact top-level Patches and Objects surfaces. Object discovery uses
  `catalog.implementations.search`; family and component detail use exact
  inspection operations.
- Render exact graphs with React Flow using one generic component-contract
  driven node representation. Parameters and attributes belong in the
  inspector rather than object-specific React components.
- Create a new patch only from the accepted Task 026 seven-node template; do
  not persist an empty or invalid graph and do not create new DSP semantics.
- Open only an explicitly selected workspace. A bounded local recent-workspace
  list is presentation state and never supplies project identity or semantic
  membership.
- Accumulate one ordered semantic draft over an exact base graph, validate it
  through shared graph transaction semantics, and persist it through
  `project.profile.transact` with exact expected references and write intent.
- Expose saved revision history and explicit revert. Selection, viewport,
  node positions, panel sizes, recent paths, loading state, and unsaved draft
  state remain presentation-owned.
- Add focused core, bridge, request-builder, model, component, accessibility,
  and production-build tests plus local browser and native-shell verification.

## Out of scope

- `build.execute`, build progress, application jobs, compiler expansion,
  artifact management, USB discovery, device sessions, upload, reset, flash,
  firmware update, SD-card access, real-time measurement, or audible claims.
- Importing Tide Pit or Palimpsest as accepted Schuss projects or buildable
  templates. Their current machine records remain inspection-only.
- Making catalogued-only implementations contracted or buildable, changing
  readiness, selecting preferred implementations, or expanding compiler
  support.
- A blank persisted graph, arbitrary template system, sampling/assets, cloud
  sync, collaboration, plug-in framework, updater, packaging, signing, or
  publication.
- Renderer access to semantic JSON, catalog files, project files, a general
  filesystem API, shell commands, raw processes, or raw USB packets.
- Reusing the prototype's localStorage patch records as Schuss projects.
- Deleting the prototype applications, staging, committing, pushing, or
  publishing.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0014 and
0015, `docs/APPLICATION_SPINE_PLAN.md`, `docs/ARCHITECTURE.md`,
`docs/OPERATION_CONTRACTS.md`, `docs/PROJECT_WORKSPACE_CONTRACTS.md`, the
accepted read-only desktop slice, exact Task 030 record set, accepted Task 026
authoring template and operations, and the two patcher prototype contracts as
presentation research only.

Deliverables are:

1. this accepted implementation contract;
2. additive component inspection and graph-rename operation successors;
3. exact parent-preserving record set `schuss-record-set-000024@1`;
4. one consolidated Tauri/React desktop application over a closed capability
   allowlist;
5. compact Patches, Objects, Patcher, and Inspector surfaces;
6. exact project creation/open/edit/save/history/revert flows; and
7. focused, adjacent, visual, native-shell, freshness, and diff validation.

## Interaction and state rules

1. A catalog implementation, family, component contract, graph node, project,
   instrument, target, and device remain distinct identities.
2. An implementation is addable only when exact catalog inspection resolves
   one component contract. Catalogued-only objects remain visible and
   unavailable rather than inferred.
3. Node ports, parameters, attributes, actions, and displays come only from the
   exact component contract. The renderer does not invent interface facets.
4. Semantic draft edits use the shared ordered edit language. Successful
   proposal validation does not imply persistence; Save performs the separate
   exact project transaction.
5. Node coordinates, selection, zoom, panel layout, recent paths, and unsaved
   draft state are non-semantic presentation state. They cannot change graph
   hashes or compile behavior.
6. Saved undo/redo uses immutable project ancestry and revert. Revert creates a
   successor and never deletes history.
7. The desktop adapter uses explicit workspace selection and a closed operation
   allowlist. It does not scan for projects or expose a general file/process
   bridge.
8. Build and Device navigation may appear only as unavailable future
   capability indicators; no callable product action exists in this slice.

## Validation cadence

- Focused: v11 schemas, component inspection, rename proposal/persistence,
  successor manifest freshness, Python/Rust bridge tests, TypeScript request
  and editor-model tests, React component tests, frontend build, Rust tests,
  and desktop structure validation.
- Adjacent: Tasks 026 and 030, catalog operations, graph transactions, project
  persistence/history/recovery, application capability descriptions, retained
  v1-v10 canonical requests/results, and governance.
- Expensive: one local browser interaction run against the real Python core and
  one native `tauri dev` smoke after implementation freeze. No compiler, ARM,
  Java, USB, or hardware reproduction applies.
- Aggregate: one final inventory/catalog/contracts run after focused and
  adjacent checks, diff review, generated freshness, and acceptance review.

## Acceptance tests

1. The current branch contains the accepted desktop product implementation and
   every Task 029/030 headless artifact without modifying accepted parent
   bytes or promoting a prototype application.
2. Request/result v11 and application-capability v4 schemas are closed,
   deterministic, parent-preserving, and reject unknown fields, operations,
   edit kinds, and stale references.
3. `component.inspect` returns exactly one schema-valid component contract for
   an exact reference and fails closed on absent, stale, wrong-kind, or
   ambiguous references.
4. `set-graph-display-name` produces a validated proposed graph successor;
   project persistence versions graph, instrument, request, and project through
   the existing atomic head boundary. Existing v1/v8 transactions remain
   byte-identical.
5. The desktop loads exact `schuss-record-set-000024@1`, exposes only the
   contract allowlist, and rejects unknown operations, schema mismatches,
   malformed payloads, oversized messages, and unexpected result metadata in
   both Rust and Python.
6. Objects lists all Task 030 implementations from the live shared operation,
   uses compact function/form/readiness presentation, and enables Add only
   after exact contract resolution.
7. Patches lists only explicit recent/open workspaces. New Patch uses the exact
   Task 026 template and never persists a blank graph.
8. `graph.inspect` renders the exact graph, contract-owned ports, and exact
   connections with a generic node component. No implementation-specific node
   component or copied semantic fixture is introduced.
9. Add/remove node, add/remove connection, parameter/attribute edit, and patch
   rename produce ordered shared edits. Invalid or stale drafts write nothing.
10. Save, close, reopen, history inspection, and revert reproduce the exact
    persisted project state. Viewport or node movement never changes semantic
    revisions.
11. Keyboard navigation, accessible controls, loading, empty, invalid, stale,
    dirty, saved, and conflict states are usable without relying on color
    alone.
12. The visual system remains dense and restrained: warm charcoal surfaces,
    thin dividers, rectangular controls, compact lists, no gradients, glass,
    glow, generic dashboard cards, or required prose descriptions.
13. Frontend build/tests, Rust tests/check, focused Python tests, successor
    freshness, adjacent regressions, browser verification, native-shell smoke,
    `git diff --check`, and the final aggregate report complete with every
    inherited failure separated from this task.

## Decisions this task may make

- Exact v11 payload/result shapes, application capability v4 presentation, and
  the smallest shared dispatcher/project-service changes required for exact
  component inspection and graph rename.
- React Flow node/edge rendering, deterministic initial layout, compact screen
  composition, responsive behavior, and presentation-only local cache shape.
- Bounded recent-workspace storage and explicit path-entry/open behavior that
  does not expose general renderer filesystem access.
- Focused component boundaries, hooks, test organization, and adapter process
  lifecycle within the closed capability allowlist.

## Decisions this task must not make

- Catalog classification/readiness, component semantics, compiler selection or
  lowering, backend/target behavior, project atomicity, instrument/device
  semantics, build evidence, or hardware behavior.
- A private desktop graph model, persistence schema, component-interface
  inference, project scan, implicit latest revision, or fallback implementation
  selection.
- Acceptance of a reference machine, general blank-project semantics, build or
  device execution, or any Git publication or destructive prototype cleanup.

## Completion boundary

Completion proves one consolidated local desktop application can browse exact
objects, create/open one template-backed project, render and edit its exact
graph, persist immutable revisions, and inspect/revert history through shared
operations. It does not prove arbitrary catalog buildability, compiler output,
connected-device execution, real-time behavior, audibility, packaging, or
release readiness.

## Retained validation result

The completed local implementation passed its focused boundary on 2026-08-18:

- Vitest: three files and six tests passed; the TypeScript/Vite production
  build transformed 212 modules;
- generated v11/application-capability-v4 records, desktop bridge, structure,
  Python syntax, Rust tests, and native Tauri-shell launch passed;
- the fresh project init/fork/rename/reload regression passed two tests in
  201.825 seconds;
- 42 adjacent control-plane, application-capability, authoring, and Mutable
  catalog tests passed in 336.492 seconds; and
- browser verification loaded the exact seven-node project graph, added one
  contract-backed object, rejected a catalogued-only object, and reported no
  console error.

After governance routing was updated for the three explicitly authorized
unnumbered UI contracts, the required final aggregate ran once: inventory
passed 14/14, catalog passed 6/6, and contracts ran 397 tests in 1,428.008
seconds with exactly three inherited failures. The failures are the two
retained Task 011A/Task 023 catalog golden comparisons and the Task 027
generated projection-hash freshness check. Each reproduces in the untouched
HEAD comparison worktree; no desktop, governance, v11, project, Task 030, or
validation-hygiene test failed. Historical goldens and generated Task 027
evidence were not rewritten to conceal those gates.
