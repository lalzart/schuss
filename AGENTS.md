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

Validation must satisfy the active contract, but replaying all historical work
is not the default definition of completion. Use the manifest-driven profiles
from ADR 0018 and `tools/validation/manifest-v1.json`:

- `current` is the routine current-closure, focused maintenance, and governance
  gate;
- `compatibility` is the ordinary historical contract suite for changes that
  can affect shared behavior;
- `configured-sources` authenticates ignored machine-local source locations;
- `native` owns compilation, sanitizer, CTest, and render matrices;
- `reproduction` owns expensive copied-root and fresh-process evidence; and
- `release` is the deduplicated current/compatibility/native/reproduction
  composition used for releases or explicitly full-integration tasks;
  `configured-sources` is added when source-dependent inputs are applicable.

Classify checks before implementation and use this order:

1. Run focused tests for the files and behavior being changed.
2. Run adjacent regression for the exact boundaries the change can affect.
3. Run `current` once the implementation is stable enough to review.
4. Use `--plan` and granular `--only` IDs to run each affected configured,
   native, or reproduction check once after implementation freeze.
5. Run `compatibility` or `release` only when the task contract, a release, or
   the changed shared boundary requires it.

If a broad profile fails, diagnose and iterate with only the affected focused
and adjacent checks. Complete the correction and repeat the freeze review
before rerunning that broad profile once. A prose-only governance edit does not
invalidate frozen native or reproduction evidence; code, schema, record,
fixture, generator, toolchain, or source-lock changes invalidate only the
profiles whose declared inputs they affect.

The `current` profile must not compile, render long matrices, copy repositories,
access hardware/network resources, or require `catalog/sources.local.yml`.
Expensive checks must be explicitly gated and listed once in the validation
manifest; compatibility tests may retain small temporary-root or subprocess
fixtures when isolation is the behavior being tested. Missing configured
sources are reported as a prerequisite, never a pass. Use already-loaded exact
contexts when process isolation is not the fact under test. In standalone
evidence runners, `--check` means cheap retained-evidence verification; fresh
work uses an explicit reproduction profile or `--reproduce` mode. The central
validation runner's `--only CHECK_ID` selects that atomic check at its declared
cost.

## Change controls

- Preserve unrelated and untracked work.
- Do not stage, commit, push, upload to hardware, write an SD card, or flash
  firmware without explicit user approval.
- Prefer the smallest change that satisfies the active task.
