# Task 012B: Object drawer and transparent graph canvas

Status: proposed prompt; immediate next task under ADR 0009; not started. The
user authorized removal of the obsolete UI-readiness gate and creation of this
exact Task 012B contract on 2026-08-15. This planning correction does not stage,
commit, publish, push, install dependencies, invoke a compiler, or access a
device.

Work in the Schuss repository. Before implementation, read `AGENTS.md`,
`docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/SCHEMA_STRATEGY.md`, `docs/OPERATION_CONTRACTS.md`,
`docs/CATALOG_OPERATIONS.md`, `docs/PROJECT_WORKSPACE_CONTRACTS.md`, ADRs
0005-0007 and 0009, the complete accepted Task 011A and Task 012A contracts,
and this complete task. Work only on Task 012B.

## Goal and why it exists

Create the first usable Schuss graphical authoring client: an immediate DSP
object drawer and a transparent graph canvas that can open, inspect, edit,
save, and reopen the accepted Task 012A project through the same catalog,
graph, validation, transaction, and persistence semantics already used by the
CLI.

The task exists to prove the central Schuss interaction model now that the
necessary project boundary is real. A musician should be able to find an
object by function, inspect what it is, see the complete graph, and make a
validated persistent edit without navigating a source tree or handing graph
truth to the GUI.

This is a bounded editor slice, not a compiler or device milestone. Build,
direct-frontend, and hardware capabilities that do not exist yet remain
visibly unavailable rather than blocking the drawer and canvas.

## Accepted inputs and frozen boundaries

Treat these as immutable inputs:

- all accepted Tasks 001-012A schemas, records, fixtures, artifacts, evidence,
  operation results, CLI goldens, project fixtures, and completion reports;
- ADR 0009's decision that Task 012B follows Task 012A without waiting for
  Tasks 013A-013D or B6;
- the Task 011A catalog projection, matching, filter, inspection, readiness,
  and provenance rules;
- the Task 008 `records.validate`, `graph.inspect`, and `graph.transact`
  semantics and ordered edit vocabulary;
- the Task 012A `project.inspect`, `project.validate`, and
  `project.graph.commit` behavior, explicit workspace selection, locking,
  recovery, and atomic acceptance boundary;
- project `schuss-project-000001` revision 1 and its exact Task 011C eight-node,
  nine-connection Gills graph as the positive reference project; and
- the rule that GUI, CLI, and AI clients share operations and that presentation
  data never becomes authoritative DSP identity.

The client must not require a compiler plan, build execution, direct frontend,
backend invocation, connected device, or expanded catalog to open and edit the
accepted project.

## Required boundary decisions

Task 012B must preserve these distinctions:

- The **object drawer** is a view of the accepted catalog projection. It does
  not own families, categories, filters, provenance, readiness, contracts, or
  implementations.
- The **graph canvas** is a view and interaction surface over one exact DSP
  graph revision. Nodes, facets, connections, and values remain graph and
  component-contract truth.
- A **presentation overlay** owns only client layout and interaction state such
  as node position, viewport, selection, panel expansion, and cable routing.
  It cannot alter graph identity, execution ordering, types, parameters,
  connections, or compiler meaning.
- A **project save** is one shared Task 012A persistent graph transaction. A UI
  success indication may appear only after the shared operation accepts the
  exact successor project revision.
- **Unavailable future capabilities** are explicit UI states. They are not
  client-side substitutes for Tasks 013A-013D, device operations, or evidence.

If the chosen client stack needs a local transport or adapter, it must be a
thin, testable projection of the shared in-process operations. It may not own
domain validation, hashing, locking, recovery, or persistence algorithms.

## In scope

### Application shell and explicit project lifecycle

- One local single-user graphical application shell with deterministic
  development and test entry points.
- Explicit workspace/project selection. No nearest-parent discovery, implicit
  `latest`, repository fixture assumption, or source-tree scan.
- Open, inspect, validate, save, and reopen flows for a Task 012A workspace.
- Clear project identity, revision, dirty/proposed state, accepted-save state,
  validation state, and stable diagnostics.
- Recovery and lock conditions rendered from shared service results without
  client-side guessing or destructive cleanup.
- An honest empty/error/unavailable state for missing, invalid, stale,
  concurrently changed, or recovery-ambiguous workspaces.

### Immediate object drawer

- Persistent visible drawer access without a modal source-library browser.
- Browse by functional category and search through accepted
  `catalog.search` results.
- Accepted filters for form, abstraction, signal domain/rate/role, capability,
  technique, readiness, and provenance, using the shared controlled values and
  AND/OR semantics.
- Family cards or rows that keep function primary and provenance/readiness as
  inspectable facets rather than primary categories.
- Exact `catalog.inspect` detail showing family identity, aliases,
  implementations, contract/signature facts, provenance, readiness/evidence,
  and unresolved or unsupported states without manufacturing compatibility.
- Keyboard-accessible search, filtering, selection, and insertion initiation.
- No filesystem path or upstream source name as the primary browsing model.

### Transparent graph canvas

- Render every node and all nine connections of the accepted Task 011C graph,
  with exact node, contract, port, parameter, and attribute identity available
  for inspection.
- Distinguish port direction, signal domain, signal rate, signal role, and
  transport/type without relying on color alone.
- Pan, zoom, selection, node movement, and a readable overview or fit-to-graph
  action.
- Inspect a node's exact component contract and catalog provenance without
  replacing the node's contract identity with its family or display name.
- Preserve access to transparent compound internals through explicit drill-in,
  breadcrumb, or equivalent hierarchy navigation. A compound may never become
  an opaque visual-only macro.
- Show proposed edits and shared diagnostics without mutating the accepted
  graph until explicit save succeeds.

### Graph editing through shared operations

- Support the existing ordered edit vocabulary only: add/remove node,
  add/remove connection, set node parameter, and set node attribute.
- Drawer insertion creates one explicit `add-node` proposal using an exact
  component-contract reference. The UI may allocate a new opaque node ID but
  may not derive identity from category or display name.
- Cable interaction creates or removes explicit graph connections. Type,
  cardinality, behavior, and complete graph validity are accepted only by the
  shared transaction/validation result; the UI may provide previews but cannot
  override the validator.
- Parameter and attribute editing preserves exact facet identity and canonical
  value representation.
- Explicit save supplies exact expected project revision/hash, graph
  revision/hash, ordered edits, and write intent to the shared Task 012A
  service exactly once.
- Stale project, stale graph, changed head bytes, concurrent writer, failed
  edit, invalid connection, or recovery ambiguity leaves the accepted project
  unchanged and produces a stable actionable UI diagnostic.

### Presentation overlay

- One closed versioned presentation-only model for node positions, viewport,
  selection-independent durable view preferences, group/comment presentation
  if included, and any explicitly supported cable-routing hints.
- Stable references from presentation entries to exact graph/node/connection
  identities without reverse references from semantic graph records.
- Local workspace persistence sufficient to reopen the same layout in the
  same workspace. The overlay remains outside canonical project/graph identity
  in this task unless a separately exact project-reference extension is both
  specified and proved without weakening Task 012A.
- Deterministic defaults for records without presentation entries. Layout must
  not depend on absolute paths, random IDs, locale, filesystem order, or
  unstable viewport timing.
- Moving or selecting a node changes no governed project or graph byte. A
  presentation failure cannot corrupt or block semantic project recovery.

### Accessibility, visual behavior, and testing

- Complete keyboard traversal for the drawer, graph nodes, inspector, and
  primary edit/save actions.
- Visible focus, textual diagnostic association, semantic labels, and no
  color-only encoding of port kind, readiness, selection, or error state.
- Bounded responsive behavior for the accepted desktop window sizes and a
  defined minimum usable viewport.
- Deterministic fixture/screenshot states for empty, loading, valid project,
  drawer search/filter, family inspection, graph selection, proposed edit,
  invalid edit, stale save, lock/recovery condition, and successful saved
  successor.
- Browser/application tests that exercise actual pointer and keyboard paths,
  shared-operation request counts, output state, console errors, and visual
  overflow rather than testing only isolated rendering helpers.

## Out of scope

- Task 013A compiler-front-half planning, compound elaboration as a compiler
  artifact, dependency/resource planning, or `build.plan`.
- Task 013B build execution, handler registry, progress/cancellation, output
  roots, cache, or product build command.
- Tasks 013C-013D normalized DSP representation, scheduling, direct lowering,
  generated C++, or direct frontend support.
- Java, `.axp`, ARM compiler/linker invocation, artifact creation, executable
  packaging, or evidence promotion.
- Device discovery, USB, MIDI transport, upload, SD-card write, flash,
  firmware, connected execution, real-time measurement, or listening.
- Automatic compatibility promotion, new contracts/bindings, broad catalog
  curation, asset ingestion, sampling, instrument-panel completion, or release
  packaging.
- Multi-user collaboration, remote service, cloud storage, accounts,
  permissions, branches, merge, or a replacement version-control system.
- General undo/redo history, copy/paste interchange, plugin hosting, automation
  lanes, timeline/sequencer UI, custom theming system, or final product polish.
- A second catalog, graph-edit language, validator, project format, persistence
  algorithm, build path, compiler model, or client-owned semantic cache.
- Staging, commit, publication, push, package installation, or network access
  without the authority required for those actions.

## Deliverables

- This task contract, updated to complete only after every acceptance gate
  passes.
- ADR 0009 and reconciled live context, architecture, schema, operation, and
  roadmap documents.
- One bounded local graphical client and deterministic development/test entry
  point.
- The thin client adapter required to call accepted shared catalog, graph, and
  project operations, if the chosen stack cannot call them directly.
- One closed presentation-overlay schema/model and local non-semantic storage
  boundary.
- Object drawer, family inspector, graph canvas, node inspector, project status,
  diagnostics, and explicit save/reopen interaction surfaces.
- Positive, negative, stale/concurrent/recovery, accessibility, interaction,
  deterministic-state, and visual-regression fixtures/tests.
- A read-only Task 012B structural validator for retained UI fixtures and
  presentation records where applicable.
- Necessary package, schema, operation-client, application, and user-facing
  documentation updates.
- A completion report naming every delivered file, chosen client/runtime
  boundary, operation calls, presentation schema/hash, fixture identities,
  interaction and visual results, preservation evidence, test counts, and
  remaining Task 013/device/product gaps.

## Acceptance tests

Task 012B is accepted only if all of the following pass:

1. Every pre-existing test and retained validator passes before counting Task
   012B tests; accepted schema, record, project, operation, CLI, artifact, and
   evidence bytes remain unchanged.
2. The client opens the explicit Task 012A positive workspace from two
   different absolute roots and renders the same project identity, revision,
   graph, drawer, and semantic state.
3. Opening never depends on current working directory, nearest-parent search,
   filesystem enumeration, implicit newest revision, or an absolute durable
   path.
4. The drawer's unfiltered, searched, filtered, and inspected semantic results
   equal the canonical shared catalog-operation results for the same requests.
5. Function remains primary navigation. Form, abstraction, readiness, and
   provenance remain filters/facets and do not silently become categories.
6. The accepted graph renders exactly eight nodes and nine connections with
   inspectable exact contracts and facets; the two Sine nodes remain distinct
   node instances over the same exact contract.
7. Port direction and complete type/rate/role information are accessible
   without color. Every connection resolves to visible exact endpoint facets.
8. Transparent compound internals remain reachable, with stable hierarchy and
   breadcrumbs, and are never copied into a client-owned opaque semantic
   model.
9. Add/remove node, add/remove connection, parameter, and attribute actions
   produce only the accepted ordered edit vocabulary and dispatch one shared
   proposal operation per explicit proposal action.
10. The UI does not claim an edit valid merely because a local preview permits
    it. Invalid types, cardinality, mappings, cycles, stale hashes, or complete-
    closure failures render the shared deterministic diagnostics and create no
    accepted revision.
11. Explicit save calls the shared persistent service exactly once with exact
    project/graph expectations and write intent. Success renders the exact
    returned successor and reopening yields identical graph/project bytes.
12. Failed, stale, concurrent, locked, or recovery-ambiguous save states leave
    the exact prior accepted project loadable and never present a false saved
    state.
13. Moving nodes, panning, zooming, selecting, opening inspectors, and changing
    other presentation-only state change no governed graph/project bytes or
    semantic hashes.
14. Presentation defaults and retained local layout are deterministic across
    fresh processes, locale, `PYTHONHASHSEED`, enumeration order, and supported
    viewport sizes. Malformed presentation state fails independently of
    semantic project loading.
15. Keyboard-only tests can search the drawer, inspect a family, focus every
    graph node, open node detail, initiate/cancel an edit, reach diagnostics,
    and save. Focus is visible and no required meaning is color-only.
16. Actual application/browser tests cover pointer and keyboard workflows,
    report no uncaught console errors, and detect clipped, overlapping, or
    unreachable primary controls at the defined viewport sizes.
17. Human-visible project, validation, dirty, proposed, saving, saved, error,
    and unavailable states are stable and cannot be confused with build,
    compiler, device, real-time, or audible evidence.
18. Client modules contain no independent catalog matching, graph validation,
    semantic hashing, lock, recovery, atomic-write, binding-selection,
    compiler, backend, or device algorithm.
19. No backend handler, Java process, source generator, compiler/linker,
    hardware transport, firmware mutation, upload, flash, evidence promotion,
    or accepted-history rewrite occurs.
20. `git diff --check` and the complete local ordinary-CI-equivalent gate pass.

## Decisions Task 012B may make

- The smallest maintainable local UI stack, application directory layout,
  deterministic development command, and test runner consistent with the
  repository's offline and portability constraints.
- Component composition, visual language, drawer width, inspector placement,
  canvas navigation, node geometry, cable rendering, focus order, and keyboard
  shortcuts within the accepted accessibility boundary.
- The presentation-overlay schema name, local locator, viewport units,
  coordinate representation, deterministic initial layout, and failure/reset
  behavior, provided none becomes semantic project or graph truth.
- A thin local adapter/transport and typed client result mapping where required
  by the selected UI runtime.
- Exact UI diagnostic wording and stable presentation test IDs, provided
  underlying diagnostic codes and subjects remain intact.
- Whether a valid edit is proposed continuously or only on an explicit action,
  provided accepted persistence still requires explicit save and exact write
  intent.

## Decisions Task 012B must not make

- New family, category, contract, binding, graph-type, instrument, target,
  backend, build, compiler, runtime, device, artifact, or evidence semantics.
- A private search/ranking rule, graph-edit language, validator, implicit type
  conversion, adapter insertion, connection repair, ID derived from a display
  name/category/path, or silent selection of a newest revision.
- A rule that makes node coordinates, cable paths, colors, grouping, viewport,
  source path, or UI component identity authoritative DSP meaning.
- An implicit save, destructive recovery guess, accepted-record overwrite,
  hidden graph rewrite, or success state before shared project acceptance.
- A fake build button that invokes a bounded Task 009/011C handler as if it
  were general execution, or any claim that structural editing proves lowering,
  compile/link, device, real-time, or audible behavior.
- Any action prohibited by workspace change controls.

## Stop conditions

Stop and report rather than broaden or weaken the task if the drawer cannot use
the accepted catalog operations; if graph rendering requires copying or
rewriting semantic truth; if persistent editing cannot use the Task 012A
service exactly; if the chosen client would need its own validator, locking,
recovery, build, compiler, or device semantics; if layout persistence would
require changing graph identity; if the complete graph or compound internals
must be hidden; if an accepted byte must change rather than using an additive
client/presentation boundary; or if completion requires Tasks 013A-013D,
hardware, network installation, staging, commit, or push.

## Completion report requirements

On completion, record every delivered file; client/runtime versions and
dependency hashes; exact presentation schema/model identity and bytes; every
shared operation request/result used; positive project/graph/family identities;
drawer search/filter/inspect equality; graph node/connection/facet rendering;
each edit and save/reload result; stale/concurrent/recovery behavior; keyboard
and accessibility coverage; viewport and visual-regression results;
determinism and cross-root evidence; pre-existing and final test counts;
accepted-byte preservation; evidence levels reached and not reached; scope
confirmation; and the exact remaining Task 013A-013D, B6, device, real-time,
audible, collaboration, and product-polish gaps.
