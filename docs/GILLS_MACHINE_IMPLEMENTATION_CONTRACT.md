# Task 029 contract: Gills machines and read-only Machine Viewer

Status: implemented in this isolated worktree; local acceptance checks pass.
The work is not staged or committed. Exact successor record set
`schuss-record-set-000022@1` has parent `schuss-record-set-000021@1`.

The evidence and architecture basis is
[GILLS_MACHINE_LAYER_PLAN.md](GILLS_MACHINE_LAYER_PLAN.md).

## Goal and why it exists

Introduce the smallest client-neutral machine layer needed to represent a
complete Gills instrument as a product distinct from individual catalog
objects, then expose it through a read-only Machine Viewer.

The task exists so users can understand what an instrument is, how audio and
control flow through it, how its ten pots/four buttons/encoder/OLED/LEDs map,
and exactly which dependencies are accepted, unresolved, private, absent, or
unsupported without flattening the instrument into one opaque catalog object.

## Execution baseline and isolation gate

Task 029 was activated against Schuss commit
`0cddd56eb1f3c0d9e82c1661054e39c93f41facb` and accepted record set
`schuss-record-set-000021@1` after the authority and ownership checks below.

The implementation owner completed these activation checks:

1. read `AGENTS.md`, `PROJECT_CONTEXT.md`, `STATUS.md`, accepted ADRs,
   `DEVICE_INSTRUMENT_CONTRACTS.md`, `GILLS_PANEL_RUNTIME_CONTRACTS.md`, and
   `GILLS_MACHINE_LAYER_PLAN.md`;
2. verify the active Schuss branch/worktree, diff, current accepted record set,
   live task ownership, and unallocated ID ranges;
3. confirmed the desktop catalog-foundation task was separately owned; Task
   029 created only the isolated `apps/schuss_machine_viewer/` client and did
   not inspect, import, merge, or modify that task's worktree;
4. verify the pinned Gills source bytes and source licenses or fail closed on
   drift;
5. revalidated the qualified v0.6 panel CAD, editable layout source, license,
   and photo hashes; retained only CAD-derived geometry plus CC BY 4.0
   attribution and did not retain or trace photograph pixels.

This task's domain design must not depend on outputs of the currently running
desktop catalog-foundation task. If both later share a desktop shell, that is a
serial integration decision after each task has an accepted client-neutral
operation boundary, not a semantic dependency.

## In scope

- deterministic schemas and validators for `machine-source-review-v0`,
  `panel-layout-v0`, `machine-presentation-v0`, and the smallest `machine-v0`;
- portable, hash-bound source reviews for Palimpsest and Tide Pit;
- an authenticated editable Gills panel SVG and separate semantic panel map,
  derived from the qualified pinned v0.6 CAD and visually checked against the
  supplied photo without embedding it;
- exact source-evidenced block diagrams and observed control/display mappings;
- a derived, client-neutral, read-only `machine.inspect` operation/result;
- exact-reference closure validation from a machine to its accepted instrument,
  device profile, authoritative graph, source review, and presentation;
- Palimpsest as the first inspection-only Viewer fixture; its `machine-v0`
  record remains correctly absent because exact graph/instrument prerequisites
  are unresolved;
- Tide Pit as an inspection-only source review unless its larger dependency and
  resource closure is separately accepted;
- a read-only Machine Viewer with identity/summary, block diagram, semantic
  Gills panel/mappings, and dependency/support evidence;
- shared-operation parity tests demonstrating that UI, CLI fixture/client, and
  AI-facing clients can consume the same inspection result;
- deterministic fixtures, negative cases, documentation, and exact evidence
  reporting.

## Out of scope

- a Machine Builder, graph canvas, object assembly, cable editing, parameter or
  mapping authoring, and implicit graph mutation;
- a general machine metadata Editor beyond read-only presentation;
- promoting, accepting, or adding objects to the current 20-object palette only
  to make an import resolve;
- silently replacing private algorithms with similar catalog objects;
- changing the unsupported Rings reverb diagnosis;
- Ksoloti Java domain ownership or changes outside
  `legacy/ksoloti-bridge/`;
- new DSP algorithms, changes to Tide Pit or Palimpsest DSP, compiler lowering,
  runtime bridges, firmware changes, or generated legacy-patch equivalence;
- ARM builds, connected-device execution, flashing, SD-card writes, OLED/LED
  hardware tests, resource/real-time qualification, and audible approval;
- manufacturing or unit-specific artwork beyond the qualified generic v0.6
  design, or copying/deriving photo pixels without separate permission;
- staging, committing, pushing, publishing, or hardware actions without their
  own explicit authorization.

## Inputs

- `docs/GILLS_MACHINE_LAYER_PLAN.md` and its exact source/dependency inventory;
- the then-current accepted Schuss record set and source locks;
- exact Gills source records for:
  - `projects/palimpsest-gills/`;
  - `projects/tide-pit-gills/`;
- current device/instrument, catalog, component, compiler-support, project, and
  operation schemas/records;
- authenticated Gills hardware/panel CAD for the applicable revision;
- the user-provided `Photo 1.jpg` appearance reference, identified by SHA-256
  `725fc22a21d5fe78118ad865e36eb9626eb9f74aa003309144b48614c1801674`,
  used only for non-retained visual comparison unless separately authorized;
- pinned v0.6 panel PCB SHA-256
  `348e22c25b7b54bd9db989c581408ed7429b9d7c2df65f19e8beb6a99b0368c4`
  and its CC BY 4.0 attribution requirements.

Absolute local checkout paths are inspection inputs only and must not enter
durable artifacts.

## Deliverables

1. deterministic schemas with canonical examples and negative
   fixtures for machine source review, panel layout, presentation, and machine;
2. source-review records for Palimpsest and Tide Pit, each with exact file
   hashes, block/mapping evidence, dependency classifications, and proof gaps;
3. authenticated `assets/gills/gills-panel-v06.svg`, a separate semantic `panel-layout-v0`
   record, and visual-verification evidence against the supplied reference;
4. exact `machine.inspect` operation contract, implementation, and stable
   result fixtures;
5. an exact Palimpsest inspection fixture and optional accepted machine record
   only if all machine closure gates pass;
6. a Tide Pit inspection fixture that remains fail closed wherever its graph,
   dependency, resource, compiler, or runtime evidence is unresolved;
7. the read-only Machine Viewer first slice using only `machine.inspect`;
8. updated current governance/status/history documentation in this isolated
   implementation worktree;
9. an acceptance matrix recording every command, result, evidence level, and
   explicit not-run boundary.

### Implemented identities and paths

| Kind | Exact retained identity/path | State |
|---|---|---|
| Record set | `schuss-record-set-000022@1` | deterministic prospective successor; local validation passed |
| Panel | `schuss-panel-layout-000001@1`; `assets/gills/gills-panel-v06.svg` | 42 qualified semantic regions; level 1 passed |
| Palimpsest review | `schuss-machine-source-review-000001@1` | inspection-only |
| Tide Pit review | `schuss-machine-source-review-000002@1` | inspection-only |
| Presentations | `schuss-machine-presentation-000001@1`, `schuss-machine-presentation-000002@1` | source-evidenced, no graph-node claims |
| Completed machines | none | fail closed pending exact graph/instrument/dependency closure |
| Operation | `machine.inspect`, request/result v9 | shared, read-only, exact-reference |
| Viewer | `apps/schuss_machine_viewer/` | isolated, dependency-free, read-only |
| Evidence | `evidence/task029-completion-v1/` | local commands and proof limits |

Palimpsest and Tide Pit are reference machines for inspection and later import
work. They are not demo records and are not counted catalog objects.

## Required data and operation behavior

### Machine source review

The review must bind portable source identity and exact bytes, legacy patch
shell, explanatory source blocks, observed panel mappings, dependency
assessment, and proof limits. It is always labelled `inspection-only` and can
never satisfy a build/support predicate.

### Machine

The machine record owns only identity, display name/summary, and exact
references to an accepted instrument, source review, and presentation. The
instrument transitively resolves the exact device profile and authoritative DSP
graph. Duplicated mappings, graph snapshots, target/backend choices, and cached
support claims are validation errors.

### Panel

The editable SVG is the visual source of truth for authenticated physical
layout. The separate semantic map owns stable Gills control IDs, kinds,
physical labels, SVG element anchors, and optional highlight regions. Machine
meanings come from the instrument mapping. SVG DOM order, visible text, and raw
coordinates are never identity.

The shared physical map represents 42 qualified slots and excludes only power.
Each reference source review assigns meanings to ten performance pots, sixteen
button/encoder gestures, six feedback channels, and two display capabilities.
It does not duplicate those gesture meanings onto the four raw button and two
raw encoder input slots; input/output volume remain represented hardware slots
without patch-controlled meanings.

### Inspection operation

`machine.inspect` resolves exact references and returns identity/summary,
evidence-labelled blocks/edges, device/panel mapping overlays, dependencies,
support states, evidence levels, reasons, and first proof gaps. It fails closed
on stale hashes, unknown IDs, incomplete closure, unsupported required
dependencies, or presentation claims without source/graph traces.

The operation is read-only and client-neutral. No client may discover records,
catalog files, Gills checkouts, or legacy patches directly.

## Read-only Viewer behavior

The Viewer must show:

- exact identity/revision/provenance, summary, inspection/import state, and
  proof boundary;
- the machine block diagram, with evidence/graph trace details available for
  every node and edge;
- the authenticated Gills SVG and semantic mappings for ten pots, four buttons,
  encoder turn/switch gestures, four LEDs, and OLED;
- mode-dependent mappings and explicit unmapped gestures (for example,
  Palimpsest encoder hold);
- dependency classification, exact matching Schuss record when any, accepted
  versus selectable state, evidence level, reason, and unresolved/unsupported
  boundary.

Selecting a diagram block or instrument facet highlights its mapped panel
controls. Selecting a control lists all mode-dependent meanings. The UI must
not expose build, deploy, play, edit, promote, or “supported” affordances for an
inspection-only review.

## Acceptance tests

### Focused schema and record tests

- canonical serialization is stable and contains no timestamps or absolute
  checkout paths;
- all references use exact ID/revision/hash and reject stale hashes;
- duplicate machine IDs, semantic control IDs, SVG element IDs, and mappings
  fail closed; shared anchors are allowed only for semantic slots that name the
  same reviewed physical button, encoder, LED, or OLED region;
- unknown device slots, invalid control kinds, missing SVG regions, and
  incomplete Gills control coverage fail closed;
- an inspection-only review cannot be referenced where an accepted machine or
  supported/buildable instrument is required;
- a machine with duplicated graph/mapping/support state is rejected;
- presentation blocks without exact source evidence, or completed-machine
  blocks without graph traces, are rejected;
- dependency assessments distinguish selectable, accepted support,
  catalogued-only, observed-only, absent, private, non-object, unsuitable, and
  unsupported states without inference from display names;
- the `Pamulist` input is retained only as corrected source-review evidence and
  cannot become Palimpsest's stable identity.

### Panel asset tests

- the SVG is editable, deterministic, self-contained, normalized, and free of
  embedded mutable/raster references unless an explicit reviewed exception is
  accepted;
- the retained SVG is a reviewed self-contained technical adaptation rather
  than a timestamp-bearing raw KiCad export;
- the SVG uses the exact 158 x 100 mm v0.6 top-panel coordinate system and the
  qualified control/display anchors in `GILLS_MACHINE_LAYER_PLAN.md`;
- the semantic map points to the exact SVG hash and accepted Gills device
  profile;
- every semantic SVG target exists exactly once and every accepted mapped Gills
  control has the correct kind;
- the four physical LED regions preserve six semantic feedback slots, with the
  two channels of LED3 and LED4 sharing regions without sharing identity;
- rendered overlays are visually checked against the authenticated oblique
  appearance reference, while metric geometry remains CAD-owned;
- discrepancies between CAD, photograph, and SVG are recorded rather than
  silently reconciled.

### Instrument evidence fixtures

- Palimpsest reflects the exact four-stage/event/voice/modal/effect structure,
  ten-pot/four-button/encoder/LED/OLED mapping, and its unmapped encoder hold;
- Tide Pit reflects the exact source/waveguide/string/body/granular/reverb/effect
  structure, mapping, and 251,408 source-declared SDRAM bytes;
- Tide Pit's Clouds diffusion reverb is not resolved through the unsupported
  Rings reverb binding;
- apparently similar filter, drive, limiter/soft-clip, scale, mixer, and
  oscillator objects remain unresolved unless exact semantic vectors prove the
  match;
- no new counted direct-palette selection appears as a side effect.

### Operation and client tests

- `machine.inspect` returns byte-identical canonical results across repeated
  fresh processes and supported alternate CWDs;
- UI and a non-UI client consume the same operation result without private
  record/catalog/source reads;
- the Viewer renders all four required sections from deterministic fixtures;
- block-to-panel and panel-to-mapping highlighting is total and mode-aware;
- unresolved and unsupported states remain visible and disable unsupported
  affordances;
- missing source/photo/asset/record prerequisites produce deterministic,
  actionable failures rather than fallbacks.

### Adjacent regression and freeze review

- current device/instrument and Gills panel-runtime validators remain green;
- current catalog/compiler-support/palette validators remain green and the
  exact 20-object palette and unsupported Rings diagnostic are unchanged;
- source-lock validation rejects ambient discovery and absolute durable paths;
- full diff, generated-artifact freshness, negative fixtures, exact record-set
  membership, and acceptance matrix are reviewed before final handoff;
- the repository aggregate is classified before execution. It remains not run
  when it would invoke the expressly out-of-scope compiler/build paths; focused
  and adjacent non-build results plus inherited parent failures are recorded
  exactly instead.

## Decisions this task may make

- exact deterministic field names/normalization for the four machine-layer schema
  types, consistent with existing Schuss record conventions;
- exact operation/result names and query shape for read-only inspection;
- which Palimpsest implementation units remain transparent machine-private
  compounds versus references to already exact accepted contracts;
- presentation-only block grouping, provided every group traces to exact source
  evidence and graph nodes;
- SVG authoring mechanics, anchors, and highlight geometry after reference
  authentication;
- read-only Viewer layout and interaction details inside the required sections,
  without creating a second domain model.

## Decisions this task must not make

- that machine, instrument, project, device profile, compute target, backend,
  or catalog object are the same layer;
- that a local `.axo` wrapper is an acceptable opaque machine graph;
- that similar names or DSP shapes establish semantic equivalence;
- that import convenience justifies public catalog or 20-object palette
  promotion;
- that Task 021 display evidence generalizes beyond its exact retained closure;
- that Tide Pit repairs or supersedes the unsupported Rings reverb diagnosis;
- that source structure proves ARM, device, real-time, resource, or audible
  behavior;
- final panel geometry/artwork from memory or unauthenticated reference;
- a Machine Builder, compiler/runtime change, device action, or publication;
- concurrent-task ownership, parent record set, stable IDs, staging, commit, or
  push without their required coordination and authorization.

## Evidence levels and completion rule

Schema, canonicalization, source-review, and host operation tests can establish
structural/host evidence only. ARM compile/link, generated boundary-artifact,
connected-device, resource/real-time, and audible levels remain explicitly not
run unless separately contracted and authorized.

The bounded Task 029 layer is complete when every retained in-scope deliverable
has an exact record/fixture, every acceptance row has a command and result,
unsupported dependencies remain fail closed, the Viewer consumes the shared
operation, and unresolved machine closure remains visible. The panel asset is
qualified and retained. The exact Palimpsest and Tide Pit instrument graphs are
unavailable, so completed machine records remain documented later
prerequisites; they are not fabricated to make the UI appear complete.
