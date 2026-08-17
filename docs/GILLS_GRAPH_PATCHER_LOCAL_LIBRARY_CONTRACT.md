# Gills graph patcher local-library contract

Status: active successor prototype contract  
Predecessor: `docs/GILLS_GRAPH_PATCHER_PROTOTYPE_CONTRACT.md`  
Application: `apps/schuss_gills_patcher/`

## Goal and reason

Extend the visual Gills patcher so object discovery and patch discovery are
clearly different workflows, and so a user can assemble, name, save, search,
reload, update, and delete a local patch draft. Move the CLEAN/FILT/DRIVE choice
out of the global application toolbar and into the Tide Pit or Palimpsest
compound that owns those meanings.

This successor exists because browser-local draft saving was explicitly out of
scope in the predecessor. It does not redefine Schuss project persistence.

## In scope

- Separate **Objects** and **Patches** tabs in the library sidebar.
- Independent object and patch search state.
- Object filtering by function, preserving the exact accepted twenty-object
  palette and fail-closed reference-only records.
- Patch search across the two source templates and browser-local saved drafts.
- A versioned local patch-library record stored in browser `localStorage`.
- Save, update, load, search, and delete actions for local patch drafts.
- Saved presentation state for reference-node positions, accepted catalog-card
  positions, source-machine identity, and the source machine's selected effect
  mode.
- A visible dirty/saved state and the current local patch name.
- CLEAN/FILT/DRIVE controls rendered inside the Tide Pit and Palimpsest source
  compound nodes. The data model permits another machine to expose no such
  mode switch.
- Focused model/UI tests, production build, and browser interaction checks.

## Out of scope

- Claiming that local browser storage is an authoritative Schuss project,
  workspace, DSP graph, instrument, or machine record.
- `project.profile.transact`, filesystem writes through the desktop adapter,
  cross-client synchronization, cloud storage, export/import, or migrations
  beyond this prototype's own local-library version.
- Semantic port loading, new connections, graph validation, compilation,
  catalog promotion, DSP changes, backend work, or hardware actions.
- Treating a dropped catalog card as wired or buildable. In this slice,
  "building a patch" means arranging exact accepted identities around the
  source-evidenced reference machine; semantic wiring remains a later governed
  adapter task.
- Editing the earlier SVG prototype, machine viewer, or separate desktop
  catalog-foundation worktree.
- Staging, commits, or pushes.

## Inputs

- The predecessor prototype and its accepted source-backed Tide Pit and
  Palimpsest fixtures.
- The exact Task 025 and Task 028 palette references already validated by the
  prototype test suite.
- Schuss layer rules in `docs/PROJECT_CONTEXT.md` and the root `AGENTS.md`.

## Deliverables

- This successor contract.
- A versioned local patch-library model with strict decode, normalization, and
  fail-closed behavior.
- Updated library, toolbar, compound-node, canvas, save-dialog, and application
  components.
- Focused persistence and interaction tests plus recorded local validation.

## Local patch record

The smallest prototype record contains:

- an opaque stable local patch ID unrelated to its mutable name;
- a mutable display name;
- the exact reference-machine key;
- the machine-owned effect mode, when supported;
- presentation placements for the three reference nodes; and
- presentation placements for locally added accepted catalog identities.

It deliberately stores no semantic connections, parameter values, compiler
claims, timestamps, source paths as identity, or copied component contracts.
Reference edges and exact machine mappings remain derived from the inspected
machine fixture.

Malformed storage is decoded record by record. Unsupported schema versions,
invalid identities, non-finite positions, unknown machine keys, invalid modes,
and malformed catalog placements fail closed and produce a visible warning.
Successful writes use stable ordering and no timestamps.

## Acceptance tests

- Objects and Patches have distinct tabs, search boxes, counts, and empty
  states; typing in one search does not overwrite the other.
- Object search continues to expose exactly twenty selectable items and keeps
  unsupported entries disabled.
- Patch search covers Tide Pit, Palimpsest, and saved local drafts.
- Saving a named draft writes one versioned local record; saving it again
  updates the same stable ID rather than deriving identity from the name.
- Loading restores the reference machine, supported mode, accepted catalog
  cards, and node positions.
- Deleting removes only the selected local draft and cannot remove a source
  template.
- Corrupt/unknown local records do not render as patches and surface a warning.
- CLEAN/FILT/DRIVE no longer appears in the global toolbar and appears inside
  Tide Pit and Palimpsest only.
- Palimpsest encoder hold remains explicitly unmapped and Tide Pit encoder hold
  remains mapped after save/load.
- Browser verification exercises save, patch search, load, update, delete,
  template switching, mode switching, and responsive layout without console
  errors or page-level horizontal overflow.

## Decisions this task may make

- Browser-local storage key, schema-version string, modal layout, patch-card
  presentation, dirty-state wording, and deterministic sort order.
- Reasonable limits for local names and placement counts.
- Whether an already loaded local draft uses Save as an update action.

## Decisions this task must not make

- The authoritative Schuss project or graph save schema.
- Desktop write authority, operation payloads, persistence locations, or
  conflict-resolution semantics.
- Component-contract port inference or semantic graph connectivity.
- Whether CLEAN/FILT/DRIVE is a universal machine concept. It is explicitly a
  source-machine-owned presentation for these two references only.
- Compiler, DSP, firmware, device, or audible behavior.

## Proof limit

Passing evidence proves only that a versioned browser-local UI draft can be
round-tripped in this prototype. It does not prove durable Schuss persistence,
valid graph construction, buildability, target compilation, device execution,
or audible behavior.
