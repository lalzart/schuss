# Unnumbered UI implementation: read-only desktop catalog

Status: accepted by explicit user authorization and complete locally on
2026-08-17 at the read-only host/UI boundary.

This is the first product implementation inside the unnumbered UI lane. It is
not Task 028, does not revive Task 012B, and does not activate the deferred
application session/job/diagnostic lane.

## Goal and why it exists

Create a runnable local Tauri 2 desktop shell whose first useful Schuss surface
is a dense, accessible, read-only catalog browser. The slice proves that a
desktop presentation can use the same exact versioned operations as the CLI
without becoming a second catalog, semantic store, or source of readiness and
evidence claims.

## In scope

- Install the minimum React, TypeScript, Vite, Tauri 2, test, and individually
  selected Radix primitive dependencies required by this slice.
- Expose only `application.describe`, `catalog.search`, and `catalog.inspect`
  through one capability-limited local bridge.
- Bind the bridge to exact accepted record set `schuss-record-set-000021@1` and
  return canonical Schuss operation results unchanged on success.
- Render function-first browsing, exact operation-backed search, category and
  provenance filtering, readiness/evidence indications, and exact family
  inspection.
- Present canonical signal and named interface facets, implementation sources,
  provenance tags, exact references, evidence references, and unresolved facts
  when the catalog inspection result provides them.
- Add focused renderer, request-builder, Rust boundary, and Python bridge tests,
  plus one local browser and one native-shell smoke check.
- Document launch commands, installed dependencies, exposed routes, and the
  next bounded UI steps.

## Out of scope

- Catalog classification, curation, semantic records, source locks, record-set
  membership, or operation/result schema changes.
- Graph visualization or mutation, a block editor, React Flow, Blockly,
  project/workspace writes, build/compile execution, sessions/jobs, device
  access, real-time/resource claims, or audible claims.
- Direct renderer access to catalog files, semantic JSON, repository records,
  project workspaces, a shell, or a general filesystem API.
- A UI-private catalog index, fuzzy matcher, readiness inference, component
  schema projection, or copied catalog fixture used as product data.
- Packaging, signing, publishing, staging, committing, pushing, uploading,
  flashing, SD-card writes, or any hardware action.
- Changes to Task 028 palette selection, compiler lowering, historical evidence,
  or accepted test goldens.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0014 and 0015,
`docs/APPLICATION_SPINE_PLAN.md`, `docs/ARCHITECTURE.md`,
`docs/OPERATION_CONTRACTS.md`, `docs/CATALOG_OPERATIONS.md`,
`docs/DESKTOP_UI_BOUNDARY.md`, the completed desktop initialization boundary,
the exact Task 028 record set, and the explicit user authorization for this
read-only slice.

Deliverables are:

1. a runnable `apps/schuss_desktop/` Tauri 2 + React + TypeScript application;
2. a Rust/Python adapter whose closed runtime allowlist contains exactly three
   read-only shared operations;
3. a function-first catalog drawer and exact inspection surface with a custom
   Schuss design system;
4. focused bridge and UI tests, static boundary validation, and visual/native
   smoke evidence; and
5. concise launch, boundary, dependency, validation, and deferral documentation.

## Acceptance tests

1. `npm run build`, `npm test`, `cargo test`, and `cargo check` pass locally.
2. The Python bridge loads exact record set `schuss-record-set-000021@1` once,
   dispatches all three allowed operations through `schuss_core`, returns
   canonical results, rejects unknown routes, and remains usable after a
   rejected request.
3. The Rust bridge independently rejects unknown operations, schema/version
   mismatches, malformed payloads, oversized requests, and unexpected result
   metadata before exposing data to the renderer.
4. Neither the renderer nor installed Tauri plugins receive filesystem, shell,
   project-write, build, network, or hardware capabilities.
5. Empty-query browsing returns all sixty exact Task 028 families; the
   Mutable-derived provenance filter returns the five matching reviewed
   families; selecting a family requests its exact reference.
6. Search, category, provenance, readiness, keyboard selection, loading,
   empty, and explicit error states are usable in the renderer.
7. The detail surface labels only the canonical fields actually returned by
   `catalog.inspect`; it never guesses port/parameter kind, support, evidence,
   preference, or audibility.
8. The visual system uses warm charcoal surfaces, compact spacing, thin
   dividers, rectangular controls, crisp type, and restrained route accents,
   with no gradients, glass panels, generic dashboard cards, or large rounding.
9. A local browser run uses the real read-only Python/core adapter, renders
   meaningful content without an error overlay, and produces a screenshot.
10. A native `tauri dev` smoke reaches a running desktop process without
    enabling or performing a write, build, device, or hardware action.
11. The implementation validator stays CWD-independent, deterministic, and
    rejects semantic-record copies or runtime-capability drift.
12. Focused and adjacent tests pass, followed by one final repository aggregate
    validation after the diff and acceptance matrix are frozen.

## Validation cadence

- Focused: renderer unit/integration tests, TypeScript/Vite build, Rust unit
  tests and check, Python bridge tests, and desktop structure validation.
- Adjacent regression: catalog operation, Mutable provenance, application
  capability, Task 028, and backbone-governance tests because this UI binds
  their exact operation metadata and record set without changing them.
- Expensive reproduction: one browser visual run against the real local bridge
  and one native Tauri development-shell smoke after the implementation is
  otherwise stable. No compiler, ARM, Java, or hardware reproduction applies.
- Final aggregate: after the implementation-freeze review, run inventory,
  catalog, and contract unittest discovery once. If inherited failures remain,
  report them exactly without rewriting historical goldens.

## Decisions this task may make

- Exact local Tauri/React tooling and narrowly selected accessible primitives.
- Read-only adapter process lifecycle, bounded transport error codes, request
  size limits, and local development verification transport.
- UI-only selection, query text, active filters, panel layout, scroll position,
  loading state, and other ephemeral presentation state.
- Typography, tokens, density, dividers, route accent mapping, and responsive
  layout within the stated visual direction.
- Focused test organization and local launch commands.

## Decisions this task must not make

- New or changed Schuss operations, request/result schemas, catalog families,
  tags, categories, readiness rules, record sets, or semantic records.
- Graph/project mutation, persistence, compiler/build/session/device semantics,
  a general shell/filesystem bridge, or renderer-side record access.
- Port/parameter classification not present in the canonical inspection result.
- Install React Flow, Blockly, a broad visual component kit, Material UI,
  shadcn/ui, analytics, telemetry, an updater, or release infrastructure.
- Claim packaging, release readiness, device execution, real-time behavior,
  audible behavior, or permission to stage, commit, push, or publish.

## Completion boundary

Completion proves one runnable local read-only catalog client over the exact
shared operation boundary. It does not accept the complete UI architecture or
authorize graph viewing, project mutation, build execution, sessions/jobs,
packaging, hardware access, or any later slice.

## Retained validation result

The completed implementation passed its focused boundary on 2026-08-17:

- TypeScript/Vite production build: passed, 60 modules transformed;
- Vitest: 2 files and 6 tests passed;
- Rust: 4 tests passed and `cargo check` passed;
- desktop bridge/structure/backbone unittest group: 10 tests passed;
- affected catalog, capability, Mutable-provenance, Task 028, and governance
  adjacency: 15 tests passed; and
- `git diff --check`: passed.

The final live browser check loaded all 60 families from
`schuss-record-set-000021@1`, returned 5 Mutable-derived families, resolved an
exact stable-ID search, rendered Struck Bell Voice signal/interface facts, and
reported no browser warning, error, or Vite overlay. The final native
`tauri dev` smoke reached the running desktop process and spawned the
Rust-owned persistent Python core adapter without any write or hardware route.

The required one-shot repository aggregate is not wholly green for inherited
reasons outside this task. Inventory passed 14 tests and catalog passed 6.
Contracts ran 368 tests with 6 failures, 1 error, and 4 skips: five historical
validator/CLI/catalog digest checks remain stale, validation hygiene still
lacks `VH-001` routing in `docs/STATUS.md`, and Task 027 regeneration still
requires ignored `catalog/sources.local.yml`. No historical golden, semantic
record, Task 028 selection, or retained evidence was changed to conceal those
gaps.
