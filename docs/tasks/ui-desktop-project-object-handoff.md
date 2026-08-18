# Unnumbered UI implementation: desktop project-object handoff

Status: accepted by explicit user authorization and active locally on
2026-08-18. Git publication, target lowering, and connected-hardware execution
remain separate.

This is a bounded successor inside the unnumbered desktop UI lane. It exposes
accepted project-local objects and external accepted-project revisions through
the existing shared operations without adding desktop AI mutation, a second
catalog, or a renderer-owned workspace model.

## Goal and why it exists

Make an object accepted through project-scoped MCP visible in the maintained
desktop as part of the exact project that owns it. A placed object should
appear in the live graph, and a library-only object should remain available for
placement without promotion into the permanent catalog.

The existing project and graph operations already preserve this semantic
state, but the desktop neither exposes the two read-only project-object
operations nor notices when another accepted client advances the atomic
workspace head. The handoff must preserve unsaved desktop edits and keep host,
target, build, device, real-time, and listening states separate.

## In scope

- Add only `project.objects.list` and `project.object.inspect` from the
  accepted v13 operation surface to the closed Rust/Python desktop allowlist.
- Present accepted project-local objects separately from permanent catalog
  implementations, including their exact form and evidence states.
- Resolve an accepted local object's exact component contract through
  `project.object.inspect` and place it with the existing `add-node` graph edit.
- Check the accepted project reference through `project.inspect` while an
  editor is open and when the window regains focus.
- Reload an externally accepted successor automatically only when the desktop
  draft is clean. When it is dirty, retain every edit and present an explicit
  guarded reload action.
- Select a newly inserted node after a clean external refresh when one exact
  added node can be identified from the prior graph.
- Add focused renderer, request, bridge, structure, and synchronization tests
  plus adjacent project/MCP regression coverage and current documentation.

## Out of scope

- Desktop draft creation, host evaluation, preview, acceptance, model-provider
  integration, chat, background agents, or any other AI mutation operation.
- A renderer-owned object database, direct semantic-file access, workspace
  scanning, filesystem watching, implicit project selection, or a second graph
  edit language.
- Global catalog promotion, catalog taxonomy/readiness changes, target
  eligibility, native-kernel lowering, compiler/backend changes, automatic
  build, automatic upload, or any new evidence claim.
- USB discovery without an explicit user action, connected-board execution,
  flash, DFU, reset, SD writes, persistent install, package installation, Git
  staging, commit, push, or publication.
- Broad visual redesign of the current desktop.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0014 and 0015,
`docs/ARCHITECTURE.md`, `docs/OPERATION_CONTRACTS.md`,
`docs/PROJECT_WORKSPACE_CONTRACTS.md`, `docs/DESKTOP_UI_BOUNDARY.md`,
`docs/AI_MCP_BOUNDARY.md`, the completed desktop and sonic-authoring task
contracts, exact record set `schuss-record-set-000026@1`, the v13 project-object
results, and the persistent desktop adapter.

Deliverables are:

1. this accepted unnumbered implementation contract;
2. the two-operation read-only desktop bridge successor;
3. a compact project-local object surface using canonical results;
4. safe accepted-head refresh and dirty-draft conflict presentation;
5. focused and adjacent regression tests; and
6. updated desktop, MCP, status, history, and application documentation.

## Handoff and evidence rules

1. The permanent catalog and a project's accepted local objects remain visibly
   distinct. The renderer derives neither collection from the other.
2. Object inspection supplies the exact component contract. Placement reuses
   the accepted graph edit language and remains an unsaved desktop draft until
   the user saves through `project.profile.transact`.
3. Accepted-head checks use `project.inspect`; the renderer never reads or
   watches `schuss-project.json` directly.
4. A clean external successor may reload automatically. A dirty editor must
   retain its graph, name, ordered edits, and selection until the user confirms
   a reload or successfully saves.
5. Project-object structural and host-evaluation facts are rendered as named
   states. They never imply target lowering, ARM build, connected-device,
   real-time/resource, listening, or quality evidence.
6. The bridge continues to reject every v13 draft, evaluation, preview, and
   acceptance operation. Build and device authority remains unchanged.
7. Historical projects whose immutable base lacks v13 remain openable and
   editable; their project-object surface falls back without rewriting the
   base record set.

## Validation cadence

- Focused: v13 request builders, project-object drawer behavior, clean and
  dirty external-revision behavior, Python/Rust allowlist versions, structure
  validation, frontend build, and task routing.
- Adjacent regression: sonic-authoring project-object operations, MCP project
  mode, project history/cache/atomicity, desktop authoring, and build/device
  session behavior.
- Expensive reproduction: one live browser smoke against an explicit scratch
  workspace may run after implementation freeze. No ARM, Java, USB, device,
  real-time, or audible reproduction is required. The aggregate already covers
  broad contract discovery and is not repeated during iteration.
- Aggregate: after the complete diff, negative cases, generated freshness, and
  acceptance matrix are frozen, run inventory, catalog, and contract discovery
  once and classify inherited failures separately.

## Acceptance tests

1. Rust and Python independently accept the two exact v13 read-only operations
   only with an explicit absolute workspace and continue rejecting all v13 AI
   mutation operations.
2. Project objects appear in a separate source with exact display name,
   function, realization form, provenance, and evidence states; they do not
   appear as permanent catalog entries.
3. Inspecting one exact local object returns its accepted component contract,
   and Add creates only the ordinary unsaved `add-node` edit.
4. A clean editor that observes a changed exact project reference reloads the
   successor graph and selects the one newly inserted node when identifiable.
5. A dirty editor that observes a changed exact project reference preserves
   every local edit, reports the successor revision, and reloads only after
   explicit discard confirmation.
6. Unavailable v13 project-object schemas do not prevent historical project
   open, graph editing, history, build, or device presentation.
7. No renderer filesystem/process permission, semantic record, authoring
   mutation, build/device behavior, or automatic hardware action is added.
8. Focused and adjacent checks, `git diff --check`, structure/governance
   validation, and the one final aggregate complete with inherited failures
   reported separately.

## Decisions this task may make

- Compact source switching, status labels, refresh interval, focus behavior,
  newly added node selection, component organization, and focused test shape.
- Private process-local association between an explicit project service and
  the already accepted sonic-authoring service, while the closed adapter grants
  only the two named read operations.
- Documentation wording that accurately separates project-local, host,
  target, build, device, real-time, and listening states.

## Decisions this task must not make

- Project/object stable identity, object-definition fields, catalog membership
  or readiness, compiler/backend selection, target eligibility, project
  atomicity, graph-edit semantics, or evidence promotion.
- Automatic acceptance, hidden graph persistence, implicit workspace choice,
  direct renderer filesystem access, target lowering, or hardware authority.
- Permission to install, stage, commit, push, publish, connect, upload, flash,
  reset, or write an SD card.

## Completion boundary

Completion proves that the maintained desktop can discover and place exact
accepted project-local objects and safely follow an externally accepted
project successor. It does not prove that an object sounds good, lowers for
Ksoloti, compiles, runs on a board, meets real-time limits, belongs in the
permanent catalog, or is published.
