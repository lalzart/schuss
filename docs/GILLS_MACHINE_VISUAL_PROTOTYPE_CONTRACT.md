# Gills machine visual prototype contract

Status: active, explicitly authorized by the user on 2026-08-17.

This is an unnumbered UI-architecture prototype after Task 029. It does not
change Task 029's records, schemas, operation behavior, source reviews, or
evidence. The existing dependency-free Machine Viewer remains the exact
evidence-oriented reference client.

## Goal and why it exists

Create a working React Flow prototype that explains a complete Gills
instrument through the physical panel and musician-facing nested blocks rather
than through generic Ksoloti-style nodes and ports.

The prototype exists to test whether a user can quickly understand how the
four-stage gesture, root and scale, sound source, body, texture, effects,
output, and Gills feedback relate before Schuss commits to a desktop Machine
Viewer or later Machine Builder interaction grammar.

## Reference machines and invariants

The only reference machines are:

- **Tide Pit**, from `projects/tide-pit-gills/`;
- **Palimpsest**, from `projects/palimpsest-gills/`.

The user inputs `Tidepit` and `Palemphist` are treated as informal spellings,
not new stable identities. The prototype consumes their existing canonical
`machine.inspect` fixtures and the authenticated Gills v0.6 SVG. It must not
read the Gills source checkout at runtime or reinterpret fixture evidence.

The existing Gills projects, accepted Schuss record set, twenty-object palette,
unsupported dependencies, DSP, compiler, runtime, desktop catalog worktree,
and Task 029 Viewer must remain unchanged.

## In scope

- a new isolated `apps/schuss_machine_prototype/` React and TypeScript client;
- React Flow custom nodes and edges with ELK-assisted deterministic layout;
- the existing editable Gills panel SVG as the physical navigation surface;
- bidirectional selection between panel controls and machine blocks;
- mode-aware Pot 9 and Pot 10 meanings for CLEAN, FILT, and DRIVE;
- Tide Pit and Palimpsest switching without page reload;
- musician-facing nested compounds that can expand to show source-evidenced
  internal roles;
- distinct control/event, audio, and feedback paths without generic visible
  port circles;
- a concise selected-item explanation and a secondary evidence/proof-boundary
  drawer;
- responsive keyboard-accessible interaction and local focused tests;
- local development and production-build instructions.

## Out of scope

- the Machine Builder, object drawer, graph editing, cable creation, drag/drop
  authoring, persistence, undo/redo, or project mutation;
- integrating with `apps/schuss_desktop/`, Tauri, a runtime bridge, or the
  separately owned desktop catalog task;
- new or changed Schuss operations, records, schemas, fixtures, source reviews,
  support claims, catalog selections, or compiler bindings;
- treating a presentation compound as an accepted DSP graph or catalog object;
- source import, lowering, builds, hardware/device actions, DSP changes,
  audible claims, staging, commits, or pushes.

## Inputs

- `apps/schuss_machine_viewer/fixtures/palimpsest-machine-inspect.json`;
- `apps/schuss_machine_viewer/fixtures/tide-pit-machine-inspect.json`;
- `assets/gills/gills-panel-v06.svg`;
- Task 029's exact panel semantic regions, presentation blocks, links, mappings,
  dependency classifications, and evidence boundary;
- the current React/TypeScript target already selected for the future desktop
  presentation layer.

## Deliverables

1. A package-local React Flow prototype with a reproducible lockfile.
2. A Gills panel component backed by the authenticated SVG and exact semantic
   slot IDs.
3. Custom machine compounds, typed paths, expansion, selection, mode switching,
   and reference-machine switching.
4. A pure adapter from canonical `machine.inspect` fixtures to UI-owned view
   state; no copied semantic record store.
5. Focused adapter/component tests plus typecheck, production build, and browser
   interaction/visual verification.
6. Updated app documentation and exact proof limits.

## Gills-first interaction grammar

The panel answers **what can I touch?** and the machine canvas answers **what
does that touch change?**

1. The authenticated panel is always visible at desktop width and precedes the
   graph at narrow width.
2. Selecting a pot, button gesture, encoder gesture, LED, or OLED region
   highlights every exact presentation block linked by `machine.inspect`.
3. Selecting a block highlights all linked physical regions and lists only the
   applicable mapping meanings for the current mode.
4. Machine blocks use musical roles, not Ksoloti object names: gesture, pitch,
   source/voice, body, texture/events, effects, output, and feedback.
5. A compound is visually nested and expandable. Its child labels are
   source-evidenced explanatory roles, not accepted graph-node claims.
6. Paths use three stable meanings: blue control/event, warm audio, and green
   display/feedback. React Flow handles remain hidden in this Viewer prototype.
7. CLEAN/FILT/DRIVE is one visible performance state. Changing it updates the
   two mode-dependent pot labels and selection detail immediately.
8. Evidence and unsupported status remain available in a secondary drawer but
   cannot dominate the primary canvas or imply buildability.

## Acceptance tests

### Focused model and interaction checks

- both canonical fixtures adapt without mutation and retain exact reference
  identity;
- every rendered block references an exact Task 029 presentation block;
- every clickable panel target resolves through an exact semantic region and
  source mapping;
- selecting a panel control returns the exact linked block set;
- selecting a block returns the exact linked semantic slots;
- CLEAN/FILT/DRIVE resolves the correct Pot 9 and Pot 10 labels for each
  reference machine;
- machine switching clears stale selection and changes all machine-specific
  labels and compounds;
- intentionally unmapped gestures remain explicitly visible when inspected;
- no build, deploy, play, edit, promote, connect, delete, or persistence action
  is exposed.

### Build and browser checks

- `npm test` passes;
- `npm run typecheck` passes;
- `npm run build` passes from the package directory;
- the production output contains no absolute checkout paths;
- a desktop browser check switches Tide Pit/Palimpsest, changes effect modes,
  selects panel controls and blocks, and expands compounds;
- the view has no horizontal overflow at 360 CSS pixels and remains legible at
  1440 CSS pixels;
- keyboard focus and activation work for the machine picker, modes, panel
  targets, blocks, evidence drawer, and reset-selection action.

## Decisions this prototype may make

- exact custom-node visual treatment, layout spacing, responsive breakpoints,
  typography, and animation within this isolated prototype;
- exact UI-only child labels for source-evidenced compound explanation;
- ELK layout options and React component boundaries;
- selection and expansion behavior that does not mutate semantic data.

## Decisions this prototype must not make

- that a presentation block is an accepted component, graph node, instrument,
  or completed machine;
- that source similarity establishes catalog support or compiler eligibility;
- that the prototype's child labels, coordinates, or layout are Schuss domain
  identity;
- that a successful web build proves compiler, ARM, device, real-time,
  resource, OLED, or audible behavior;
- that prototype acceptance authorizes desktop integration or Machine Builder
  implementation.

## Validation classification

- **Focused:** adapter tests, mode/mapping tests, TypeScript, package build.
- **Adjacent regression:** existing dependency-free Machine Viewer tests and
  Task 029 validation that does not invoke compiler or hardware paths.
- **Expensive reproduction:** none; no compiler, fresh-root semantic record,
  device, or hardware claim is in scope.
- **Aggregate:** not required for this isolated UI prototype; the existing
  repository aggregate contains build-bearing paths outside this contract.
