# Unnumbered UI implementation: desktop workspace shell

Status: accepted by explicit user authorization and active locally on
2026-08-18; the implementation and contracted local validation are complete.
Git publication, packaging, target lowering, and connected-hardware execution
remain separate.

This is a visual and workflow successor to the completed desktop patcher and
project-object handoff. It consolidates the maintained desktop around the
patcher canvas without replacing the shared project, graph, catalog, build, or
device contracts.

## Goal and why it exists

Make the useful patcher state the desktop's immediate home instead of requiring
users to navigate through separate Patches and Objects pages, repeatedly enter
workspace metadata, and explicitly create or open a patch before seeing the
canvas. The desktop should remember one projects root, reopen an accepted
project, expose objects and patches as compact contextual drawers, and keep
long core initialization from looking like a frozen open action.

The existing canvas and graph-edit interaction are retained. The task removes
navigation and setup friction around them and gives object detail an
expandable, patch-contextual home.

## In scope

- Replace the top-level Patches/Objects/editor routing with one always-present
  patcher shell.
- Add compact Objects and Patches drawer tabs beside the canvas, a contextual
  object detail surface, remembered drawer state, and a smaller adjustable
  drawer footprint.
- Default object browsing to patcher-relevant entries while retaining an
  explicit complete-catalog view and exact provenance/readiness detail.
- Make a patcher-relevant catalog entry resolvable and addable through one
  intentional action; retain closed-contract failure reporting.
- Persist a versioned projects-root setting and last accepted project in local
  desktop preferences. New-patch UI asks for a display name, not project IDs or
  raw project paths.
- Add shared `workspace.projects.list` and `workspace.project.create`
  operations so project discovery, validation, identity allocation, template
  selection, and creation remain core-owned rather than renderer filesystem
  logic.
- Reopen the last accepted project when possible. When a configured empty root
  is first used, create one valid template-backed Untitled project through the
  same shared create operation.
- Start the persistent desktop core process during native application launch,
  render the patcher shell while it becomes ready, and distinguish core startup
  from project-open progress and errors.
- Add focused renderer, request, workspace-service, bridge, structure,
  governance, and generated-record tests plus adjacent project/catalog/MCP
  regression coverage and current documentation.

## Out of scope

- A renderer-owned workspace index, direct renderer directory scanning,
  semantic-file access, hidden graph persistence, or a client-owned database.
- Changing stable project/object/graph identity rules, graph-edit semantics,
  accepted project atomicity, catalog taxonomy, provenance, readiness, target
  eligibility, compiler/backend selection, or evidence promotion.
- Replacing the existing Python repository-context validation with a weaker or
  stale semantic cache. Deeper cold-load decomposition is a separately measured
  core-performance concern; this task may prewarm it and improve truthful UI
  staging but must not bypass validation to manufacture a faster result.
- AI draft/evaluation/preview/acceptance mutation, model providers, chat,
  background agents, automatic build, automatic upload, or automatic device
  discovery.
- ARM/Java compilation, USB access, connected-device execution, flash, DFU,
  reset, SD writes, package installation, Git staging, commit, push, or
  publication.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0014 and 0015,
`docs/ARCHITECTURE.md`, `docs/OPERATION_CONTRACTS.md`,
`docs/PROJECT_WORKSPACE_CONTRACTS.md`, `docs/DESKTOP_UI_BOUNDARY.md`, the
completed desktop UI contracts, exact record set
`schuss-record-set-000026@1`, its accepted starter graph/instrument/build
references, and the persistent desktop adapter.

Deliverables are:

1. this accepted unnumbered successor contract;
2. versioned shared workspace list/create operation contracts and record set;
3. a core-owned bounded workspace-library service;
4. the consolidated always-on desktop shell and versioned local preferences;
5. eager native core startup and explicit staged loading/error presentation;
6. focused and adjacent regression tests; and
7. updated desktop boundary, operation, status, history, and application docs.

## Workspace and interaction rules

1. A projects root is a user preference, not semantic project state. The
   desktop may remember it locally, but every shared operation still receives
   one explicit absolute root and fails closed outside it.
2. Project discovery is bounded to direct child directories and validated by
   the core project service. Symlinks, malformed projects, duplicate stable
   identities, and escaping paths never become openable entries.
3. Project creation allocates stable identity and a collision-safe directory in
   the core, uses the accepted starter/profile references, and publishes the
   completed project atomically inside the configured root.
4. The renderer stores only display preferences and canonical references. It
   never derives accepted graph or project semantics from files.
5. Objects and patches are alternate browsing contexts around one canvas, not
   independent application modes. Object inspection is expandable in context.
6. Patcher-relevant is a presentation filter over existing readiness facts, not
   a new readiness state. Complete catalog access and provenance remain
   available.
7. Core startup, workspace discovery, project inspection, and graph inspection
   are distinct visible stages. Failure in one stage must not leave a blank
   application shell or silently substitute semantic state.
8. Build/device controls retain their current explicit authority and evidence
   labels. No operation in this task performs automatic hardware access.

## Validation cadence

- Focused: workspace list/create service and schemas, request builders, local
  preference migration, default canvas state, drawer tabs/detail/add flow,
  project switching/creation, native eager-start allowlist, structure and
  generated-record freshness, frontend build, and task routing.
- Adjacent regression: existing project init/fork/transact/history/atomicity,
  catalog/object inspection, desktop project-object handoff, MCP project mode,
  desktop build/device session behavior, and application-capability selection.
- Expensive reproduction: after implementation freeze, run one live browser
  smoke against an explicit scratch projects root and one native Rust adapter
  check. No ARM, Java, USB, device, real-time, or audible reproduction is
  required. Broad contract discovery in the final aggregate is not repeated as
  a separate expensive run.
- Aggregate: after complete diff review, negative cases, generated freshness,
  and the acceptance matrix are frozen, run inventory, catalog, and contract
  discovery once. Diagnose failures narrowly; repeat the aggregate only after a
  complete correction and new freeze.

## Acceptance tests

1. The app renders the patcher canvas on launch without a New Patch or Open
   Patch gate and has no standalone Objects application route.
2. Objects and Patches are compact drawer tabs; drawer open state and bounded
   width persist, object detail expands in patch context, and the canvas remains
   the dominant surface.
3. The default object collection is derived only from existing patcher-relevant
   readiness facts; All catalog exposes the complete canonical collection with
   provenance/readiness detail.
4. One Add action performs exact contract resolution and, on success, emits
   only the existing unsaved `add-node` graph edit. Unsupported entries remain
   inspectable and explain why they cannot be placed.
5. Settings persist one explicit absolute projects root. Patch creation asks
   only for a display name; the core allocates path and stable ID and creates a
   valid template-backed project below that root.
6. The last accepted project reopens when valid. A configured root with no
   valid project creates and opens one Untitled project through the canonical
   operation. Invalid roots/projects produce recoverable setup or browse states.
7. Rust and Python accept only the exact new workspace operations with an
   explicit root. Traversal, symlink escape, malformed project, duplicate ID,
   and unauthorized operation negative cases fail closed.
8. Native launch starts the persistent core process before the first project
   open request, while the visible shell reports truthful startup/open stages.
9. Existing project-object handoff, graph authoring, save/history, build/device
   presentation, historical-project fallback, and closed hardware authority
   remain intact.
10. Focused and adjacent checks, `git diff --check`, structure/governance
    validation, browser/native smoke, and the one final aggregate complete with
    inherited failures classified separately.

## Decisions this task may make

- Drawer dimensions within a canvas-dominant layout, compact tab and detail
  interaction, preference schema/migration, loading copy, empty/error states,
  keyboard and pointer affordances, and focused component boundaries.
- Bounded direct-child discovery limit, collision-safe slug/directory format,
  deterministic stable-ID allocation, and atomic temporary-directory strategy
  inside an explicit root.
- Operation/schema version increments and the exact immutable record-set
  successor required to expose workspace list/create through every client.
- Native prewarm timing that does not weaken semantic validation or block
  window creation.

## Decisions this task must not make

- Semantic project-root inference, recursive workspace indexing, stable-ID
  meaning, starter/profile contents, graph edit language, catalog membership or
  readiness, target lowering, compiler/backend behavior, or evidence claims.
- Direct renderer filesystem/process access, automatic project acceptance,
  hidden saves, destructive cleanup of an existing project, or hardware
  authority.
- Permission to install, stage, commit, push, publish, connect, upload, flash,
  reset, or write an SD card.

## Completion boundary

Completion proves that the maintained desktop reaches and preserves the useful
patcher state with substantially less navigation and setup, and that workspace
browsing/creation still uses canonical shared operations. It does not prove
target lowering, ARM build, connected-device behavior, real-time/resource
fitness, audible quality, package readiness, or publication.

## Completion evidence

- Frontend tests pass 21/21 and the production bundle builds; workspace-service
  and structure checks pass 10/10, the Python bridge smoke passes 1/1,
  governance passes 5/5, and Rust adapter tests pass 3/3.
- The adjacent project, session, application, MCP, and sonic-authoring set
  passes 60/60. Generated-record freshness, Python compilation, structure
  validation, and `git diff --check` are clean.
- Live browser acceptance verified first-run root setup, automatic Untitled
  creation, remembered reopen, Patcher/All catalog projections, contextual
  detail, successful ordinary Add/Discard, and a closed catalog-only Add path.
  The disposable workspace was moved to Trash.
- The final aggregate passes inventory 14/14 and catalog 6/6. Contracts ran 434
  tests in 1,090.532 seconds and retained exactly the three pre-existing Task
  011A/Task 023 golden and Task 027 freshness failures; no current desktop
  workspace-shell test failed.
