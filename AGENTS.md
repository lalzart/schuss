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

## Change controls

- Preserve unrelated and untracked work.
- Do not stage, commit, push, upload to hardware, write an SD card, or flash
  firmware without explicit user approval.
- Prefer the smallest change that satisfies the active task.
