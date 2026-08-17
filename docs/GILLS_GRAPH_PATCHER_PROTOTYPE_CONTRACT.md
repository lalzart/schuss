# Gills graph patcher prototype contract

Status: active implementation contract  
Scope owner: the isolated `codex/model-gills-machines-for-schuss` worktree  
Prototype application: `apps/schuss_gills_patcher/`

## Goal and reason

Create a runnable, visual-first React Flow prototype that explains a complete
Gills instrument as a patch: physical controls enter from a Gills device rack,
an instrument compound receives those mappings, and audio, LEDs, and OLED
feedback leave through a Gills output rack. The prototype exists to test a
faster and more legible authoring direction than the earlier panel-SVG viewer.

The reference machines are the checked-out Gills source projects with exact
names and locations:

- `projects/tide-pit-gills/tidepit-gills.axp` in the `gills-instruments`
  checkout;
- `projects/palimpsest-gills/palimpsest-gills.axp` in the same checkout.

The source `.axo` objects and included DSP headers are evidence for labels,
control destinations, signal structure, outputs, and honest compound
boundaries. A legacy `.axp` is source evidence and a backend boundary artifact;
it is not an authoritative Schuss graph.

## In scope

- A new isolated Vite/React/TypeScript application using React Flow.
- Tide Pit and Palimpsest machine switching.
- A Gills input rack with P1-P10, B1-B4, encoder turn, encoder push, and encoder
  hold represented as distinct stable controls.
- Exact source-backed control labels, including CLEAN/FILT/DRIVE alternatives
  for P9 and P10.
- Explicit, color-coded continuous-control, event, audio, and feedback edges.
- A source-defined instrument compound that can reveal a non-editable internal
  outline without pretending that private C++ helpers are selectable Schuss
  objects.
- A Gills output rack for stereo audio, four stage LEDs, and OLED feedback.
- A searchable catalog drawer whose draggable entries are exactly the five
  Task 025 and fifteen Task 028 accepted direct-palette selections.
- Direct HTML drag-and-drop, plus an accessible add button, for creating local
  draft catalog cards on the canvas.
- Selection inspection, node movement, local draft deletion, reference reset,
  fit-view controls, and an explicit local/not-buildable evidence banner.
- Focused model/UI tests, TypeScript checking, production build, and local
  browser verification.

## Out of scope

- Editing the existing SVG/panel prototype or machine viewer.
- Editing, reading from at runtime, merging, or depending on the separate
  desktop catalog-foundation worktree.
- Desktop shell integration, a transport adapter, operation registry changes,
  or changes to the Schuss desktop capability boundary.
- Durable graph writes, project persistence, catalog promotion, compiler
  lowering, DSP changes, source generation, build requests, hardware actions,
  staging, commits, or pushes.
- Claiming that Tide Pit or Palimpsest private helpers are standalone catalog
  objects, or expanding the accepted twenty-object palette to satisfy their
  imports.
- Inferring exact semantic ports for a dropped catalog item without loading its
  governed component contract. Prototype catalog cards therefore show exact
  identity and readiness but remain unwired local placements.
- Manufacturing an editable Gills panel SVG. The supplied photograph is
  reference evidence only for this node-patcher slice.

## Inputs

- Schuss architecture and operation contracts, especially
  `docs/PROJECT_CONTEXT.md`, `docs/SCHEMA_STRATEGY.md`,
  `docs/DESKTOP_UI_BOUNDARY.md`, and
  `docs/GILLS_PANEL_RUNTIME_CONTRACTS.md`.
- Task 025 and Task 028 selection packets and the Task 029 pinned record set.
- Tide Pit and Palimpsest `.axp`, `.axo`, and included DSP headers in the local
  `gills-instruments` checkout.
- The user-supplied current Gills photograph. It is not geometrically complete
  enough to become final panel artwork and is not copied into the application.

## Deliverables

- This contract.
- The runnable `apps/schuss_gills_patcher/` prototype and its local tests.
- Source-backed machine fixtures for Tide Pit and Palimpsest.
- A pinned prototype catalog fixture containing exactly twenty selectable
  records and a small, explicitly disabled reference-only set.
- Exact local validation commands and proof limits in the implementation
  handoff.

## Model and interaction rules

1. Physical Gills slots, instrument mapping facets, graph facets, and catalog
   identities stay distinct. A rack handle is a presentation of a device slot,
   not a DSP node identity.
2. Reference mappings are literal edges from stable rack control handles to
   stable compound-input handles. Encoder hold is mapped for Tide Pit and shown
   explicitly as unmapped for Palimpsest.
3. Reference output edges are literal audio/feedback edges from the compound to
   stereo output, LED1-LED4, and OLED endpoints.
4. Canvas coordinates, selection, expansion, and locally added cards are
   presentation state only.
5. A dropped catalog card carries an exact family and component-contract
   reference. It has no connectable semantic handles in this slice because the
   governed contract adapter is not implemented here.
6. Unsupported or catalogued-only records are fail-closed: visible where useful,
   labelled with the reason, and not draggable or addable.
7. The compound outline is a source review aid. Its rows are not graph nodes,
   cannot receive edges, and must be labelled as non-editable source structure.
8. Mode-dependent P9/P10 labels change presentation only; no source semantics
   are rewritten.

## Acceptance tests

The slice is accepted when local checks prove all of the following:

- Both exact reference machines load without an empty or missing control rack.
- Both contain P1-P10, B1-B4, encoder turn, encoder push, and encoder hold.
- Tide Pit maps encoder hold to Destination; Palimpsest marks encoder hold
  unmapped.
- CLEAN, FILT, and DRIVE select the source-backed P9/P10 meanings.
- Each reference renders stereo, LED1-LED4, and OLED output relationships.
- Edge colors are stable by signal kind and a visible legend explains them.
- The selectable catalog count is exactly twenty and disabled items cannot be
  dropped or added.
- Dropping or adding a selectable item creates a visibly local, unwired draft
  card carrying its exact family and component-contract references.
- Switching machines and resetting restores the corresponding source template.
- A production build succeeds and local browser verification finds the machine
  switch, mode switch, catalog search/add path, compound expansion, canvas, and
  evidence boundary without console errors or unintended horizontal overflow.

## Decisions this task may make

- Visual styling, spacing, responsive layout, node dimensions, and canvas
  navigation appropriate to the prototype.
- Presentation-only grouping and fixed initial coordinates.
- Accessible labels and keyboard alternatives for drag-and-drop.
- Which small set of catalogued-only records best demonstrates fail-closed
  status, provided none become selectable.

## Decisions this task must not make

- The authoritative persisted Schuss graph or machine schema.
- Runtime operation payloads, desktop adapter design, write authority, or
  persistence semantics.
- Promotion eligibility or support status for any catalog family.
- Compiler, backend, DSP, firmware, or hardware behavior.
- Final Gills panel artwork or panel geometry.

## Evidence and proof limits

The strongest possible result here is a locally built and browser-verified UI
prototype whose reference labels and relationships are traced to inspected
source. It does not prove that the reference machines are accepted Schuss
graphs, that locally added cards can be serialized or compiled, that any
machine runs on ARM/Gills hardware, or that audio is correct or audible.

If panel artwork returns later, the visual source of truth should be an editable
SVG silhouette/layout paired with a separate semantic panel map of stable
control IDs, kinds, labels, and SVG anchors/regions. Creation requires at least
a square, uncropped, high-resolution overhead photograph; known faceplate
dimensions; control-center measurements or trusted CAD; confirmation of the
encoder, button, pot, LED, OLED, jack, and label geometry; and permission to
derive the asset. The current angled/cropped photograph is useful visual
evidence but insufficient for final geometry.
