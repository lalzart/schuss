# Schuss workspace instructions

These rules apply to the entire Schuss workspace.

## Begin with the contract

Before making changes, read this file, `docs/PROJECT_CONTEXT.md`, the relevant
architecture documents, and the active task specification. If a task conflicts
with an accepted decision, report the conflict rather than silently changing
the architecture.

Every implementation task must state:

- goal and why it exists;
- in-scope and out-of-scope work;
- inputs and deliverables;
- acceptance tests;
- decisions the task may make;
- decisions the task must not make.

Keep work inside the active task boundary. Do not use a narrow inventory,
schema, bridge, or UI task to redesign adjacent layers.

## Naming and layer boundaries

- Schuss is the authoring and patching platform.
- Gills is a device profile and instrument platform within Schuss.
- Ksoloti Core is the initial compute target and legacy compiler backend.
- Keep compute target, device profile, instrument, DSP graph, and backend
  independent.
- Ksoloti Java belongs only in `legacy/ksoloti-bridge/`; it is not the Schuss
  domain model.

## Non-negotiable model rules

- Browse by function, filter by form, and inspect provenance.
- Factory, Mutable Instruments, user, and community are provenance facets,
  never primary categories.
- Primitive, compound, and instrument are abstraction levels, not functions.
- Preserve access to the complete DSP graph, including compound internals.
- GUI, CLI, and AI clients must use the same graph operations.
- Stable IDs never contain category paths or mutable display names.
- Ports, parameters, attributes, actions, and displays are distinct.
- Retain the existing Ksoloti firmware and ARM compiler initially; introduce a
  new compiler frontend incrementally.

## Inventory and source safety

- Raw inventory records facts. It must not invent function, quality, license,
  compatibility, or preferred-object semantics.
- Use portable source IDs in durable artifacts. Keep absolute checkout paths
  only in ignored `catalog/sources.local.yml`.
- Pin upstream URLs and commits in `catalog/sources.lock.json`.
- Never clean, reset, rewrite, update, or otherwise mutate an upstream checkout
  as a side effect of inventory work.
- Preserve duplicate definitions, overloads, parse failures, unresolved
  references, zombies, and uncertainty as explicit data.
- Do not infer per-file licensing from a repository or directory name.

## Determinism and evidence

- Generated artifacts must have stable ordering, normalized encoding, and no
  timestamps unless a task explicitly requires and tests them.
- Fail closed on ambiguous identity, unsupported constructs, schema drift, or
  unresolved source configuration.
- Report structural, host-model, ARM compile/link, connected-device, and
  audible evidence separately. One level never implies another.
- A generated legacy `.axp` is a boundary artifact, not the authoritative
  Schuss graph.

## Validation cadence and cost

Validation must satisfy the active contract, but repeated aggregate runs are
not a substitute for choosing the smallest relevant test while iterating.
Classify the task's checks before implementation as focused, adjacent
regression, expensive reproduction, and aggregate.

Use this order unless the accepted task contract requires a stricter one:

1. Run focused tests for the files and behavior currently being changed.
2. Run adjacent regression tests for the exact historical boundaries the
   change can affect.
3. When the implementation is otherwise stable, run required fresh-root,
   fresh-process, compiler, or retained-evidence reproduction checks once.
4. Review the complete diff, generated-artifact freshness, negative cases,
   and contract acceptance matrix. Treat this as the implementation freeze.
5. Run the full aggregate suite once after that freeze and before declaring
   the task complete.

If the aggregate suite fails, diagnose and iterate with only the affected
focused and adjacent tests. Finish the complete correction and repeat the
freeze review before one final aggregate rerun. Do not rerun the full suite
after every small fix, and do not begin it while additional implementation
changes are still planned.

Avoid separately repeating an expensive check already exercised by the same
final aggregate run unless the task explicitly requires the standalone result
or it is needed for diagnosis. Record the exact command and result so a passing
unchanged check is not rerun merely to restate the evidence. A later change
invalidates only the validation layers it can affect: for example, a prose-only
governance edit requires its focused governance check, while code, schema,
record, fixture, or generator changes require the relevant regression layers
and may require a new aggregate run.

Tests should use cached or in-process contexts when process isolation is not
the fact under test. Reserve subprocesses, copied roots, alternate CWDs, and
environment matrices for contracts that actually claim those boundaries.
This cadence never reduces an explicit evidence requirement and never turns a
missing authenticated prerequisite into a pass.

## Change controls

- Preserve unrelated and untracked work.
- Do not stage, commit, push, upload to hardware, write an SD card, or flash
  firmware without explicit user approval.
- Prefer the smallest change that satisfies the active task.
