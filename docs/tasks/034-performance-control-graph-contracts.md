# Task 034: Controller-independent performance graphs and explicit device bindings

Status: explicitly activated by the user and implementation complete locally
on 2026-08-20 in the isolated
`codex/task034-performance-control-contracts` worktree. Focused, adjacent,
two copied-root reproduction, governance, and implementation-freeze checks
pass. The final aggregate completed with all Task 034 and Task 030 checks
passing; seven historical failures and one error are retained as two
pre-existing golden gates plus six checks whose ignored local-source
prerequisite is absent from the isolated worktree. No physical audio/MIDI or
Ksoloti device action, staging, commit, push, tagging, or publication is
authorized by this task.

## Goal and why it exists

Add the semantic layer that will eventually let one Schuss instrument be
played from Gills, MIDI, or another controller without putting hardware facts
inside the instrument or DSP graph.

Task 005's `instrument-v0` joined three independent concerns: the musical
instrument, its authoritative DSP graph, and one exact device-profile mapping.
That was an appropriate first vertical slice, but it is too narrow for an
application where several controller presentations may play the same
instrument. Task 034 adds a device-independent `instrument-v1`, a typed
performance-control graph, and an explicit performance configuration that
owns controller-to-instrument binding. Existing v0 records and every existing
project, Gills, compiler, build, and host-runtime path remain unchanged.

The intended reference direction is:

```text
controller protocol or device profile
  -> performance configuration
  -> performance-control graph
  -> public instrument facets
  -> instrument-to-DSP mappings
  -> authoritative DSP graph
  -> selected backend/runtime
```

Neither a controller source nor a performance-control graph may reference DSP
node IDs. The native JUCE graph, MIDI device discovery, and any future UI are
adapters or clients of this semantic closure, never its authority.

## Exact baseline and allocation

The activation audit found clean local and remote baselines at commit
`c1eaea0114630d07e59c859b9264c3de24909e54`, with exact parent record set
`schuss-record-set-000029@1`, content hash
`sha256:8d6d8e5b0c3a90862f1e7c9ddab9c054a7b5908f268db9fa356c131bdc37c55c`.
Task 032's historical schemas, projects, packages, WAVs, factories, and runtime
evidence are immutable inputs.

Task 034 exclusively allocates:

- successor record set `schuss-record-set-000030@1`, parented exactly to
  `schuss-record-set-000029@1`;
- schemas `instrument-v1`, `performance-control-contract-v0`,
  `performance-control-graph-v0`, `performance-configuration-v0`,
  `schuss-operation-request-v17`, `schuss-operation-result-v17`, and
  `schuss-application-capability-description-v10`;
- device-independent successor `schuss-instrument-000005@2`, preserving the
  exact DSP graph and musical facets of `schuss-instrument-000005@1` while
  removing its device profile and device mappings;
- performance-control contracts
  `schuss-performance-control-contract-000001@1` and
  `schuss-performance-control-contract-000002@1`;
- performance-control graph
  `schuss-performance-control-graph-000001@1`;
- performance configurations
  `schuss-performance-configuration-000001@1` for the exact Gills profile and
  `schuss-performance-configuration-000002@1` for a portable MIDI 1.0 CC
  source; and
- one shared read-only operation, `performance.inspect`.

Task 034 allocates no DSP graph, DSP component contract, implementation
binding, binding eligibility, compute target, backend, build request, host
factory, runtime package, project, device profile, or evidence-claim identity.
It does not allocate or infer a physical MIDI endpoint name or JUCE device ID.

## In scope

- Additive, closed, canonical schemas for device-independent instruments,
  reusable performance-control contracts, typed performance-control graphs,
  and configurations that bind controller sources to public graph inputs and
  public graph outputs to instrument facets.
- A device-independent successor of the exact Task 026 seven-node effects
  instrument. Its stable musical identity, DSP graph reference, public
  parameters, state declarations, graph mappings, and defaults remain exact;
  only the device ownership moves outward.
- Distinct value kinds for continuous, boolean, trigger, note, clock, and
  transport control data. Task 034 validates their structure and connection
  compatibility but executes none of them.
- Exact reusable node contracts and a small reference performance graph that
  maps two normalized control inputs to the existing Motion and Blend
  instrument parameters.
- Two configurations proving that the same exact instrument and performance
  graph may be presented by either Gills controls or portable MIDI CC
  selectors without changing the DSP graph or instrument.
- Deterministic semantic validation: exact-reference closure, stable local
  IDs, typed ports, one driver per required destination, complete public input
  and output binding, compatible domains, same-instrument lineage, and explicit
  rejection of controller/DSP leakage.
- Read-only `performance.inspect` through the shared core operation and
  capability surfaces. It returns the exact configuration, controller sources,
  performance graph and contracts, instrument, DSP graph, and boundary/evidence
  summary.
- A deterministic generator, successor record set, negative fixtures, focused
  tests, adjacent regression, two copied-root/fresh-process reproductions, and
  current architecture/governance documentation.

## Out of scope

- MIDI input, MIDI learn, MIDI output, MPE, OSC, CV scanning, physical endpoint
  enumeration, Core MIDI, JUCE MIDI callbacks, or any live controller I/O.
- Executing a performance-control graph, scheduling control events, timestamp
  policy, sample-accurate automation, smoothing implementation, conflict
  merging, takeover/pickup, feedback loops, controller display rendering, or
  real-time resource claims.
- Polyphony, voice allocation, note stealing, zones, channel modes, transport
  ownership, clock arbitration, sequencer behavior, scenes, macros, or preset
  design. The type vocabulary reserves no behavior for those future policies.
- UI, node-editor behavior, factory-object presentation, JUCE DSP graph
  architecture, host factory expansion, DSP algorithms, native builds, offline
  audio rendering, audio-session replacement, or changes to Task 031/032
  runtime packages.
- Mutating `instrument-v0`, migrating existing project revisions, changing
  Gills runtime/panel contracts, changing Ksoloti lowering, or claiming that a
  v1 instrument is executable through an existing project/build path.
- CLI, MCP, AI, Tauri, React, or JUCE routes for the new operation. They may be
  added later as clients of the same operation.
- ARM build/link, USB, upload, flash, reset, SD-card mutation, physical
  audio/MIDI device access, audible evaluation, packaging, signing, release,
  staging, commit, push, tagging, or publication.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADR 0016, the architecture,
schema, operation, device/instrument, project/workspace, and Task 032 contracts;
the exact parent record set; `instrument-v0`; the exact Task 026 seven-node DSP
graph and instrument; the reviewed Gills device profile; and the current shared
operation/capability implementation.

Deliverables are:

1. this active contract with frozen exact allocation and parallel ownership;
2. the four additive semantic schemas and their deterministic validation rules;
3. the device-independent instrument successor, two control contracts, one
   control graph, and two controller configurations;
4. operation-request v17, operation-result v17, capability-description v10,
   and shared-core `performance.inspect` integration;
5. one deterministic generator and exact successor record set;
6. focused positive and negative fixtures plus adjacent and fresh-process
   regression evidence; and
7. coherent architecture, schema, operation, device/instrument, status,
   roadmap, history, and task-index documentation.

## Parallel ownership boundary

The user's separate factory-object/JUCE task may proceed in parallel when it
owns only UI/native-host presentation and runtime-adapter files. Task 034 owns
the semantic contracts, exact identities, generator, record set, performance
validation, shared operation/capability additions, and shared governance files.

The parallel task must consume these semantic interfaces rather than create a
second controller or instrument model. It must not edit `instrument-v1`, any
performance-control schema or record, record set `000030`, operation v17,
capability v10, `record_set_rules.py`, `control_plane.py`,
`application_capabilities.py`, or the shared status/task indexes while Task 034
is active. If the JUCE work genuinely requires one of those shared files, that
part must wait for Task 034 to merge and then rebase. Editing disjoint files is
safe; independently deciding shared identities or reference direction is not.

## Contract and validation rules

1. `instrument-v0` remains byte-exact and is validated only by its historical
   v0 paths. `instrument-v1` is additive and is not silently admitted to old
   project, Gills, target, build, or runtime services.
2. A v1 successor lineage reference must resolve exactly, use the same
   `instrument_id`, and point to an earlier revision. The pilot successor must
   preserve all musical/DSP-owned fields of v0 after the three device-owned
   fields are removed.
3. Performance-control contracts and graphs contain no device-profile,
   physical-control, instrument, DSP graph, DSP node, backend, or runtime
   references. They describe reusable typed control transformation only.
4. A configuration is the sole owner of controller-source bindings. Its exact
   instrument, performance graph, optional device-profile sources, and portable
   protocol sources must resolve without ambient/latest selection.
5. A device source selector names only a slot or gesture declared by its exact
   device profile. A MIDI selector declares protocol facts such as message kind,
   one-based channel, and controller number; it contains no OS endpoint name,
   native handle, or framework-specific identifier.
6. Every required graph input is driven exactly once by the configuration and
   every graph output is mapped exactly once to a compatible public instrument
   facet. Multiple drivers, dangling references, mismatched value kinds or
   domains, and direct controller-to-DSP destinations fail closed.
7. Graph connections resolve exact contract ports, preserve value kind and
   domain, have one driver per destination, and are acyclic. Canonical set and
   sequence ordering never depends on filesystem or map iteration order.
8. Structural validation is the highest evidence earned. Runtime execution,
   backend lowering, native build, physical device, real-time/resource, and
   audible evidence are explicitly `not-run`.
9. `performance.inspect` is read-only, exact-reference-only, deterministic,
   and produces byte-identical results in direct and fresh-process use. It may
   not mutate a project, controller, device, graph, runtime, or filesystem.
10. No existing public operation changes behavior or bytes. No new public CLI,
    desktop bridge, or MCP allowlist is opened by this task.

## Validation cadence

Focused checks cover generator freshness, schema annotations, exact record-set
closure, positive Gills and MIDI configurations, instrument lineage and field
preservation, typed graph closure, boundary scans, deterministic ordering,
negative reference/type/driver/leakage cases, `performance.inspect`, result
schema validation, capability v10, and governance.

Adjacent regression covers byte-exact Task 005/018 device-instrument output,
Task 026 project behavior, Task 029 Gills machine closure, Task 031/032 host
operations and retained artifacts, the closed desktop bridge operation set,
MCP isolation, and the existing aggregate record-set/domain validators. Any
old validator that consumes record kind `instrument` must explicitly retain
its v0-only boundary rather than accidentally accepting or rejecting v1.

After implementation freeze, two copied roots and fresh processes must load
record set `000030`, run semantic validation, and produce the same canonical
`performance.inspect` bytes. No native build or physical hardware is required.
The complete diff, generated freshness, negative matrix, v0 byte preservation,
and acceptance matrix are reviewed before one final aggregate run. Known
unrelated inherited failures remain separate and are not rebaselined.

## Acceptance tests

1. Exact parent and allocations match this contract; generation is fresh and
   deterministic in the repository and two copied roots.
2. Every new schema is closed, annotated for array semantics, canonical, and
   rejects unknown fields, duplicate identities, floats, nonportable paths,
   and invalid exact references.
3. The v1 pilot instrument preserves the v0 pilot's musical/DSP-owned fields,
   contains no device profile or device mapping field, and resolves its exact
   predecessor and exact DSP graph.
4. The same exact v1 instrument and same exact performance graph resolve from
   both retained configurations; only their controller-source bindings differ.
5. Neither performance-control contract nor graph contains any device,
   instrument, DSP graph/node, backend, host-factory, JUCE, or runtime identity.
6. The Gills configuration resolves its exact device profile and declared
   input slots. The MIDI configuration uses only portable protocol selectors
   and contains no physical endpoint identity.
7. Unknown/stale references, duplicate local IDs, missing or multiple drivers,
   type/domain mismatch, cycles, unknown Gills slots, invalid MIDI ranges,
   and any controller-to-DSP shortcut fail with stable diagnostics.
8. `performance.inspect` returns the complete exact closure and boundary
   summary, validates against result v17, and is byte-identical across repeated
   direct calls and fresh processes.
9. Capability v10 describes exactly one additive read-only operation and all
   prior capabilities remain present with their historical request/result
   versions.
10. Existing v0 device/instrument, project, Gills, machine, target/build, host
    runtime, desktop bridge, and MCP tests retain their prior behavior and
    historical generated bytes.
11. Final evidence distinguishes structural success from every execution,
    native, hardware, real-time, and audible level that was not run.
12. No out-of-scope file, existing semantic record, historical golden, user
    work, hardware, or remote state is mutated.

## Decisions this task may make

- Closed field shapes and local-ID prefixes for the four additive schemas.
- The smallest useful typed control vocabulary, exact-domain representation,
  deterministic graph ordering, and stable diagnostics needed by the retained
  structural fixtures.
- The exact portable representation of Gills slot and MIDI CC selectors,
  provided neither becomes an operating-system or JUCE endpoint identity.
- The read-only shape of `performance.inspect` and its structural boundary
  summary.

## Decisions this task must not make

- UI layout, controller-mapping UX, MIDI-learn behavior, native factory-object
  architecture, JUCE graph ownership, callback/event timing, or runtime thread
  policy.
- Polyphony, voice allocation, note semantics, clock/transport arbitration,
  takeover/pickup, controller merging, modulation law, or feedback policy.
- New DSP nodes/algorithms, implementation bindings, eligibility promotions,
  backend lowering, target support, project migration, or executable claims.
- Any reinterpretation of v0 schemas/records, change to the seven accepted host
  factories, or claim beyond structural validation.
- Staging, commit, push, tag, publication, device access, upload, or flash.

## Completion boundary

Task 034 is complete only when the exact successor record set and both retained
configurations validate, the shared read-only operation/capability surface is
deterministic, every negative boundary case fails closed, v0 and Task 032
regressions remain intact, copied-root reproduction agrees, governance is
current, and the final aggregate result is recorded. Completion will not mean
that MIDI or Gills events are received, that control graphs execute, that JUCE
objects exist, that the instrument is playable, or that any audible result has
been earned.
