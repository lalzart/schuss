# Proposal: first non-UI Gills vertical slice after Task 010

Status: proposed planning document; discussion only. No task in this proposal is
active, and this document does not authorize implementation, compilation,
device access, upload, flash, staging, commit, or push.

This proposal turns the roadmap after Task 010 into a sequence of bounded
follow-on tasks for one simple Gills instrument. Task 010 is complete. Its
deterministic product CLI and the four accepted Task 008 operations are frozen
inputs; this proposal does not reopen or alter them.

## Goal and why it exists

The first non-UI vertical slice should be musically recognizable while small
enough that every semantic record, graph connection, backend construct, and
evidence claim can be reviewed directly.

The proposed instrument contains:

- two instances of one sine-oscillator contract;
- one four-step pitch sequencer;
- one state-variable filter using its low-pass output;
- the already accepted mixed-rate Crossfader to combine the oscillators;
- one clock source and one cyclic counter, unless exact type review proves a
  smaller truthful clock-to-step path;
- one built-in stereo audio-output endpoint; and
- the existing minimal Gills knob mapped to oscillator blend.

Everything else is fixed in the hand-authored graph: four pitches, tempo,
oscillator base pitches/detune, filter cutoff, and resonance. More panel
controls, envelopes, note gates, effects, displays, assets, and persistence are
not part of this first slice.

The plan exists to prevent one appealing demo from collapsing several
different claims into “it works.” Catalog and interface definition, graph
validity, backend support, generated artifacts, ARM compile/link, connected
execution, real-time behavior, and audible behavior remain separate gates.

## Accepted work this proposal consumes

This proposal does not reopen Tasks 005-010:

- Task 005 owns the minimal Gills device-profile and instrument schemas. The
  existing profile truthfully contains one normalized knob and unresolved
  physical range/resolution facts.
- Task 006 owns the component/binding/graph schemas, strict no-implicit-
  conversion rule, mixed-rate Crossfader contract, authoritative Blend graph,
  and exact instrument-to-graph mapping rules.
- Task 007 owns target, backend, eligibility, build, artifact, resource, and
  eight-level evidence records.
- Task 008 owns the shared operations and backend-invocation seam.
- Task 009 proves only the exact one-node Blend slice through deterministic
  legacy generation and ARM compile/link. Its handler is not a general
  compiler, and its level-5 result does not prove this proposed graph.
- Task 010 owns the accepted deterministic product-CLI projection over Task
  008. Task 011A may add catalog commands only as thin projections over new
  shared catalog operations; it must preserve every accepted Task 010 command,
  output byte, exit behavior, and ownership boundary.

Every follow-on task must preserve accepted records and evidence byte-for-byte
and must add new exact revisions or successor record sets rather than rewrite
history.

## Proposed exact slice

### Candidate legacy observations

The following frozen Phase 3 observations make the slice concrete. They are
candidates for review, not compatibility or runtime claims.
No new family, implementation, contract, graph, or instrument identity is
allocated by this proposal; every candidate identity decision belongs to the
reviewed Task 011A / VS-01 catalog task.

| Role | Frozen candidate | Existing Phase 4A identity |
| --- | --- | --- |
| Clock source | object 209, `lfo/square` | none; requires bounded Phase 4B curation |
| Cyclic step counter | object 215, `logic/counter` | none; requires bounded Phase 4B curation |
| Four-step pitch sequencer | object 918, `drj/seq/stepseq_4_pitch` | family `schuss-family-000022` exists, but its retained implementation `schuss-implementation-000032` is the distinct 16-step observation 920 |
| Sine oscillator, used twice | object 549, `osc/sine` | family `schuss-family-000003`; implementation `schuss-implementation-000007` |
| Oscillator mixer | accepted mixed Crossfader | contract `schuss-component-contract-000003`; implementation `schuss-implementation-000028` |
| State-variable filter | object 159, `filter/multimode svf m` | family `schuss-family-000009`; implementation `schuss-implementation-000015` |
| Stereo audio output | object 9, `audio/out stereo` | family `schuss-family-000002`; implementation `schuss-implementation-000004` |

The four-step sequencer must not reuse implementation identity `000032`:
observation 918 and observation 920 are different concrete realizations. The
catalog task should retain family `000022` for the shared pitch-step-sequencing
function and add a new implementation identity for observation 918. If review
finds that the retained family name “16-step Pitch Sequencer” cannot be
generalized through an additive successor without changing its meaning, the
task must stop and report the identity conflict instead of silently assigning
membership.

### Intended graph topology

The initial topology is:

```text
square clock -> cyclic counter -> four-step pitch sequencer
                                      |             |
                                      v             v
                                sine oscillator A  sine oscillator B
                                      |             |
                                      +-> mixed Crossfader <-+
                                                |
                                                v
                                      state-variable filter (LP)
                                                |
                                                v
                                      built-in stereo audio output

Gills knob -> instrument blend -> graph blend -> Crossfader fade
```

This topology is a planning input, not an instruction to coerce types. Two
specific joins are mandatory review points:

1. The square-clock outlet and counter input must have exactly compatible
   domain, rate, semantic role, representation, and edge behavior. If the
   rising-edge behavior is a conversion rather than counter-inlet semantics,
   an explicit reviewed edge-adapter component is required.
2. The filter's mono low-pass outlet may feed both stereo endpoint inlets only
   if the exact outlet cardinality permits two explicit connections and the
   endpoint inlet types match. Otherwise an explicit reviewed mono-to-stereo
   component is required.

No backend or validator may insert either adapter silently. Discovery of a
required adapter sends the proposal back to the component/binding gate before
the graph can pass.

## Roadmap reconciliation and proposed labels

The master roadmap already assigns Phase 4B / Task 011 to incremental
reviewed-core expansion, Phase 12 to UI, Phase 13 to a direct frontend, and
Phase 14 to full Gills implementation. This proposal does not renumber or
replace those phases.

The labels `VS-01` through `VS-08` below remain planning stages, not a promise
of eight separate implementation tasks. The proposed execution grouping is:

- **Task 011A:** VS-01 plus the first shared source-agnostic catalog discovery
  boundary and ordinary continuous integration;
- **Task 011B:** VS-02 through VS-04: contracts, bindings, the hand-authored
  graph, the minimal Gills instrument, and the unresolved build/probe closure;
- **Task 011C:** VS-05 and VS-06: bounded legacy backend expansion, generated
  source, ARM compile/link, and exact evidence promotion; and
- **VS-07 and VS-08:** separately authorized connected-device, real-time, and
  listening evidence tasks.

Task 011A is the immediate next task. Its bounded proposed contract is
`docs/tasks/011a-browsable-catalog-control-plane-and-exact-gills-slice-catalog-review.md`.
Tasks 011B and 011C remain roadmap groupings until their own contracts are
reviewed and approved.

UI and AI/MCP remain parked. Phase 12 is neither completed nor redesigned;
Phase 13's direct Schuss-to-C++ frontend is not used; Phase 14's complete Gills
panel and behavior mapping remains later work. VS-07/08 are not prerequisites
for Phase 12. The object drawer and transparent graph canvas should consume
accepted `catalog.search`, `catalog.inspect`, `graph.inspect`, and
`graph.transact` operations instead of defining separate discovery or graph
semantics.

## VS-01 / Task 011A: shared catalog discovery and exact slice review

### Goal

Create the first shared, source-agnostic browse/search boundary, make the
accepted 26-family Phase 4A pilot discoverable through it, and curate only the
seven logical component roles above into a truthful catalog closure. Reuse
accepted identities where they exist and add only the clock, counter, and
four-step-sequencer identities that the slice actually needs.

### Inputs

- Frozen observations 9, 159, 209, 215, 549, and 918.
- The accepted Crossfader records and Task 009 promoted revision closure.
- Phase 4A families and implementations for Audio Output, Sine Oscillator,
  State-variable Filter, Crossfader, and Pitch Step Sequencing.
- Phase 4B curation rules, source locks, provenance evidence, and frozen
  inventory/review diagnostics.
- The accepted Task 008 dispatcher/operation contracts and complete Task 010
  product CLI.

### Deliverables

- A versioned deterministic catalog projection derived from exact family,
  implementation, contract, binding, taxonomy, provenance, eligibility, and
  evidence records without becoming a parallel source of truth.
- Additive shared `catalog.search` and `catalog.inspect` operations that leave
  accepted Task 008 v1 request/result schemas and bytes unchanged.
- Thin Task 010-style CLI projections:
  `schuss catalog search [QUERY] [FILTERS] [--json]` and
  `schuss catalog inspect FAMILY_ID@REVISION [--json]`.
- Deterministic function-first discovery, facet filtering, exact inspection,
  and derived readiness states that keep provenance independent from musical
  function.
- A reviewed slice manifest naming every candidate observation and its exact
  portable source/hash provenance.
- Additive catalog family/implementation records or successor overlay records
  for only the missing Square LFO, Cyclic Counter, and four-step-sequencer
  realization.
- An explicit decision that observation 918 belongs to family `000022`, or a
  stop report explaining why that membership would change family meaning.
- A dependency note identifying any exact source, license, generated-object,
  overload, zombie, or ambiguity issue that blocks a later binding.

### Acceptance evidence

- Full inventory, review, catalog, contract, operation, and product-CLI
  validation passes locally.
- Frozen Phase 2/3/review and Phase 4A bytes and IDs remain unchanged.
- Direct API, canonical CLI JSON, and representative GUI/AI fixture callers
  receive byte-identical catalog operation results.
- All 26 accepted pilot families are discoverable. Search and inspection
  distinguish catalogued-only, contracted, bound, eligible, compile-proven,
  device-tested, and unresolved states only from exact records/evidence.
- Functional categories and provenance facets remain independently filtered
  and represented; factory, Mutable Instruments, community, user, demo, and
  legacy never become primary functions.
- Each new membership is human-reviewed and traceable to an exact observation;
  source location is provenance, never stable identity.
- No preferred binding, target compatibility, compiler eligibility, or
  runtime claim is created.

### Strictly out of scope

Component signatures or implementation seam maps beyond the accepted
Crossfader, graphs, instruments, new build requests, eligibility promotion,
lowering, artifact generation, compiler/linker invocation, persistent graph
editing, GUI/drawer implementation, AI/MCP implementation, full catalog
expansion, device access, firmware action, upload, flash, staging, commit, and
push.

### Dependencies

Task 010 is complete and accepted. Task 011A depends on accepted Tasks 001-010
and no UI, AI, compiler, or hardware work.

### Earliest remaining proof gaps

No target-independent node type or implementation seam is proved. The earliest
next owner is VS-02.

## VS-02: component contracts and legacy binding definitions

VS-02, VS-03, and VS-04 are successive internal evidence gates of proposed
Task 011B, not three independently authorized tasks unless a later review
chooses to split them.

### Goal

Define the smallest exact component-contract and implementation-binding set
needed for the hand-authored graph while reusing the accepted mixed Crossfader
without modification.

### Inputs

- The accepted VS-01 slice catalog closure.
- Frozen observations and pinned source bytes for each selected realization.
- Task 006 component, binding, type, lifecycle, mapping, canonicalization, and
  no-implicit-conversion rules.
- The existing Crossfader mixed-rate contract/binding and its Task 009
  evidence-supported revision chain.

### Deliverables

- New exact contracts for Square LFO, Cyclic Counter, four-step Pitch
  Sequencer, Sine Oscillator, State-variable Filter, and built-in stereo Audio
  Output.
- Companion bindings mapping every public port, parameter, action, display,
  attribute, and state facet to the exact legacy seam once and only once.
- A bounded additive type/schema revision only if the accepted v0 schema
  cannot truthfully express required clock, integer-step, rising-edge,
  pitch-unit, multi-output, display, or connection-cardinality semantics.
- Positive and negative fixtures for clock/trigger compatibility, integer
  step/pitch roles, repeated oscillator use, parameter-plus-inlet pitch
  behavior, output fan-out, and all prohibited implicit conversions.
- An explicit adapter decision for the two mandatory review points. Any
  required adapter receives its own catalog identity, contract, binding, and
  visible later graph node.

### Acceptance evidence

- Closed schema, canonical hash, exact-reference, facet-seam, type, lifecycle,
  and deterministic-diagnostic validation passes in fresh processes.
- Every existing Task 005-010 record, validator output, operation result, and
  Task 009 artifact/evidence byte remains unchanged.
- The two oscillator instances can truthfully share one exact contract and
  binding; no duplicate semantic identity is allocated per graph instance.
- Compatibility and selection remain `not-evaluated` for every newly bound
  realization. A legacy-resolved observation is not target support.

### Strictly out of scope

Production graph or instrument records, binding eligibility/promotion, build
requests, lowering, `.axp`, Java generation, ARM compilation/linking, resource
claims, UI, AI/MCP, device actions, firmware actions, upload, flash, staging,
commit, and push.

### Dependencies

Task 011A / VS-01 must be accepted. The accepted Task 006 schemas and
validators remain the authority; VS-02 may add a versioned extension but may
not weaken them.

### Earliest remaining proof gaps

The contracts are not yet assembled into an authoritative graph and no
instrument mapping or build eligibility exists. VS-03 owns the graph; VS-04
owns build readiness.

## VS-03: one hand-authored graph and structural instrument validation

### Goal

Create exactly one authoritative, manually reviewable graph for the proposed
instrument and a new instrument record that maps the existing minimal Gills
knob to Crossfader blend.

### Inputs

- The accepted exact contracts/bindings from VS-02.
- The accepted mixed Crossfader contract.
- The existing minimal Gills device profile and Task 005 instrument-mapping
  rules.
- The exact topology and fixed musical values approved for this proposal.

### Deliverables

- One new graph with the expected eight baseline node instances: Square LFO,
  Cyclic Counter, four-step Pitch Sequencer, two Sine Oscillators, mixed
  Crossfader, State-variable Filter, and stereo Audio Output. An explicitly
  approved adapter may increase that count; no hidden node may do so.
- Explicit typed connections matching the intended topology.
- Fixed, reviewed values for four step pitches, tempo, oscillator base
  pitches/detune, filter cutoff/resonance, and any counter bound.
- One public normalized `blend` parameter bound to the accepted Crossfader
  fade inlet.
- One new instrument identity referencing the exact graph and the existing
  minimal Gills profile, with `device-input-000001 -> instrument blend ->
  graph blend` and no device-to-graph shortcut.
- Structural, exact-reference, topology, connection, parameter-binding,
  cardinality, and instrument-target fixtures and validation.

### Acceptance evidence

- The hand-authored graph and instrument have verified canonical hashes and
  pass target-independent validation deterministically.
- Removing, retyping, or rewiring any required node/connection fails with a
  stable diagnostic.
- Direct graph inspection exposes the complete graph and exact contract
  closure, including any adapter; no compound or legacy patch hides internals.
- The existing Gills record remains truthfully minimal. The new instrument
  makes no claim about physical knob range, resolution, connected hardware, or
  audible response.
- `build.resolve` for this graph is absent or explicitly unresolved; it is not
  made successful in this task.

### Strictly out of scope

Catalog expansion beyond discovered adapter needs, new implementation
eligibility, backend support, lowering, artifact generation, compilation,
linking, graph persistence operations, product-CLI changes, UI, AI/MCP, full
Gills mapping, hardware access, firmware action, upload, flash, staging,
commit, and push.

### Dependencies

VS-02 must pass. If a connection needs an adapter or schema behavior not
accepted by VS-02, VS-03 stops and returns to VS-02 rather than inserting a
conversion.

### Earliest remaining proof gaps

The graph is structurally valid only. New bindings are not selected, the
Task 009 handler rejects the graph, and evidence levels 3-8 remain unproved.
VS-04 owns the exact build/probe closure.

## VS-04: build request, eligibility, and probe closure

### Goal

Prepare a fail-closed, non-executable build-domain closure for the exact graph
so backend work begins from an explicit unresolved candidate set rather than
ad hoc selection.

### Inputs

- The exact VS-03 graph and instrument.
- Task 007 target/backend/build/evidence schemas and resolver policy.
- Task 008 operation boundary and backend-invocation seam.
- Task 009 record-set, authenticated environment, probe, strictly-earlier
  evidence, and promotion patterns.

### Deliverables

- An exact successor record set containing the new graph closure without
  changing any accepted default context.
- One build request for the exact graph/instrument, Ksoloti Core target, and
  legacy backend, stopping no later than source/artifact generation.
- One eligibility companion per new binding, initially unsupported or
  unresolved unless strictly earlier evidence already supports the exact
  realization and target/backend pair.
- An immutable candidate-under-test probe input and procedure for only the new
  bindings and graph constructs.
- A deterministic `build.resolve` trace naming every exclusion and unresolved
  reason; no executable backend invocation is produced while uncertainty
  remains.

### Acceptance evidence

- Record-set parentage, exact input closure, resolver determinism, narrowing-
  only overrides, and all fail-closed outcomes validate.
- The accepted Task 009 Blend request still resolves and its exact handler and
  artifacts remain unchanged.
- No new binding is selected by family, path, source order, legacy load order,
  common historical use, or similarity to the Blend proof.

### Strictly out of scope

Backend code changes, lowering, `.axp`, Java or ARM tool invocation, artifact
descriptors, compatibility promotion, compile/link evidence, device access,
UI, AI/MCP, firmware action, upload, flash, staging, commit, and push.

### Dependencies

VS-03 must be accepted. Existing Task 009 environment bytes must reproduce
exactly or the task stops with an environment blocker.

### Earliest remaining proof gaps

No new backend construct is supported and no source artifact exists. VS-05
owns bounded lowering and generation; ARM compile/link remains VS-06.

## VS-05: bounded legacy build-path expansion through source generation

VS-05 and VS-06 are successive internal evidence gates of proposed Task 011C,
not two independently authorized tasks unless a later review chooses to split
them.

### Goal

Expand the transitional legacy backend from the exact one-node Blend slice to
only the graph constructs and legacy realizations used by this instrument,
ending at deterministic generated source.

### Inputs

- The accepted VS-04 candidate-under-test closure.
- The exact Task 009 lowering, `.axp`, source-map, bridge, and handler boundary.
- The authenticated source/Java/classpath/runtime closure.
- Exact selected legacy observations and bindings from VS-02.

### Deliverables

- A bounded multi-node lowering path supporting repeated component instances,
  the exact connection forms, fixed node parameters, graph parameter binding,
  and selected generated/native legacy forms used by this graph.
- Deterministic resolution-plan, `.axp`, source-map, bridge-resolution, and
  generated-C++ outputs for the candidate-under-test path.
- Stable diagnostics and first-terminal-stage behavior for every unsupported
  node, facet, connection, parameter, object resolution, and source-generation
  failure.
- Refactoring, if necessary, that preserves the exact Task 009 Blend path and
  never converts the handler into an unbounded “compile anything” claim.
- Level-3 and level-4 evidence only if those stages are actually executed and
  recorded under the accepted probe/evidence contracts.

### Acceptance evidence

- Two fresh, differently named roots emit byte-identical retained plan,
  `.axp`, source-map, bridge result, and generated source bytes.
- Source maps cover every graph node, contract facet, binding seam, legacy
  object, and stable generated-source region required by the slice.
- Failure injection at each stage prevents later stages and unsupported
  evidence.
- The Task 009 Blend artifacts, operation bytes, handler behavior, and evidence
  remain byte-identical.

### Strictly out of scope

ARM compiler or linker invocation, production compatibility promotion,
connected hardware, real-time measurement, listening, general compiler IR,
direct Schuss-to-C++, UI, AI/MCP, graph persistence, firmware action, upload,
flash, staging, commit, and push.

### Dependencies

VS-04 and its environment preflight must pass. If Java resolution needs
ambient preferences, GUI, device state, or an unpinned object, stop rather than
weaken isolation.

### Earliest remaining proof gaps

Generated source has not compiled or linked, no production eligibility is
promoted, and levels 5-8 remain unproved. VS-06 owns compile/link evidence.

## VS-06: ARM compile/link artifacts and production evidence

### Goal

Compile and link the exact generated slice with the authenticated ARM/runtime
closure, then promote only the exact bindings and build request supported by
strictly earlier probe evidence.

### Inputs

- Deterministic VS-05 outputs and candidate-under-test result.
- The authenticated Java, GNU Arm, firmware/runtime ABI, source, command, and
  retained-product closure from Task 009.
- Task 007 result, artifact, resource, evidence, and revision-stratification
  contracts.

### Deliverables

- An explicitly authorized probe result through ARM compile/link for the exact
  new graph/binding closure.
- Immutable object, ELF, link-map, command-vector, artifact-descriptor, static
  resource-report, build-result, and level-specific evidence records.
- New binding and eligibility revisions only after evidence names the strictly
  earlier candidate revisions.
- The smallest justified target/backend/environment revisions and a promoted
  build-request revision.
- A successful ordinary Task 008 `build.resolve`, followed by one production
  handler run through the unchanged backend-invocation seam.
- Independent evidence claims for levels 1-5 actually reached, with levels
  6-8 explicitly `not-run`.

### Acceptance evidence

- Fresh-root determinism holds for every retained plan, boundary, source,
  object, ELF, and link-map artifact governed by deterministic contracts.
- The linked ELF uses the exact authenticated target/runtime boundary and
  static sections fit declared linker regions.
- Probe failure or compiler/linker failure blocks promotion and all later
  stages.
- A successful link is described only as level 5; it creates no device,
  real-time, or audible claim.

### Strictly out of scope

Executing the ELF, connecting hardware, firmware installation or modification,
USB/device operations, runtime probes, real-time measurement, listening,
general compiler support, direct frontend work, UI, AI/MCP, upload, flash,
staging, commit, and push without separate authorization.

### Dependencies

VS-05 must pass and exact tool/runtime preflight must reproduce every approved
byte before any tool invocation.

### Earliest remaining proof gaps

The exact ELF has not executed. Connected-device level 6, real-time/resource
level 7, and audible level 8 remain separate tasks.

## VS-07: connected-device execution evidence

### Goal

Establish only that one named physical Ksoloti Core/Gills assembly executes the
exact VS-06 artifact under a bounded, explicitly authorized procedure.

### Inputs

- The exact VS-06 artifact and complete immutable build/evidence closure.
- A named device identity and a reviewed, reversible execution procedure.
- Any separate authorization required for USB, RAM load, SD-card write, upload,
  or other device interaction. Flash or firmware installation is not implied.

### Deliverables

- A preflight record proving artifact, device, connection method, firmware
  identity, power state, and safety boundary.
- One level-6 evidence claim recording only observed boot/load/execution and
  explicitly exercised control/audio-I/O behaviors.
- Failure and recovery records that do not relabel an unobserved behavior as
  passed.

### Acceptance evidence

- The device reports or otherwise demonstrates execution of the exact artifact
  hash under the stated procedure.
- Any observed Gills knob or audio-I/O response is named individually; omitted
  behavior remains not-run.
- No timing, CPU-headroom, stability-duration, or sound-quality inference is
  made from basic execution.

### Strictly out of scope

Firmware replacement, bootloader work, destructive flash, broad device-profile
completion, real-time acceptance, listening-quality judgment, UI, AI/MCP,
staging, commit, and push. Any upload, SD-card write, or flash action requires
its own explicit authorization at execution time.

### Dependencies

VS-06 must pass. If the execution method changes firmware or persistent media,
the task stops until the user approves that exact action.

### Earliest remaining proof gaps

CPU headroom, timing, sustained stability, I/O limits, and audible behavior
remain unproved. VS-08 owns real-time evidence; a later listening task owns
level 8.

## VS-08: real-time and audible validation as two independent gates

VS-08 is one roadmap discussion item but must execute as two separately
approved task contracts, `VS-08A` and `VS-08B`. Neither result implies the
other.

### VS-08A goal and deliverables

Measure the exact artifact on the exact device for bounded CPU load/headroom,
audio deadline behavior, memory usage, sustained stability, parameter-update
behavior, and required I/O behavior. Deliver a method, thresholds, raw
measurements, normalized results, limitations, and one level-7 claim per
bounded assertion.

Acceptance requires predeclared loads/durations/limits, exact device and
artifact identity, repeatable measurements, and truthful failed or unresolved
outcomes. Listening, musical value, UI, full Gills release readiness, firmware
redesign, and catalog/compiler promotion by side effect are out of scope.

Its earliest remaining proof gap is level-8 audible behavior.

### VS-08B goal and deliverables

Run a separately specified listening procedure that can distinguish, at
minimum, the four-step pitch cycle, both oscillator contributions across the
blend control, low-pass filtering, and stereo output. Deliver exact stimulus
and parameter settings, capture/listening conditions, observations,
limitations, and narrowly worded level-8 claims.

Acceptance requires the exact device/artifact identity and a procedure whose
observations are reproducible enough for its stated claim. “Audible” does not
mean musically polished, alias-free, release-ready, or real-time safe unless a
separate method proves those properties.

UI, AI/MCP, effects, expanded controls, subjective product approval, broad
sound-quality claims, full Gills mapping, and automatic compatibility/catalog
promotion are out of scope.

### Dependencies

VS-08A and VS-08B each depend on VS-07. They may be scheduled independently
after level 6, but evidence records and completion reports must remain
separate.

### Earliest remaining proof gaps

After both pass, only this exact artifact/device/method slice has evidence
through level 8. General backend support, complete Phase 4B catalog coverage,
full Gills panel mapping and release validation, Phase 12 UI, Phase 13 direct
frontend, other devices/targets, and broader musical quality remain open.

## Sequence and promotion gates

```text
Task 011A
  VS-01 shared catalog discovery + exact slice review
    -> Task 011B
       VS-02 contracts and bindings
       -> VS-03 hand-authored graph and instrument
       -> VS-04 unresolved build/probe closure
    -> Task 011C
       VS-05 bounded lowering and source generation
       -> VS-06 ARM compile/link and exact promotion
  -> VS-07 connected-device execution
  -> VS-08A real-time validation
  -> VS-08B audible validation
```

No task may pull success forward from a later gate. A new adapter, unresolved
identity, ambiguous binding, unsupported graph construct, nondeterministic
artifact, or missing environment byte returns work to the earliest owning gate
instead of being repaired through fallback.

## Decisions this proposal makes

- The first slice is non-UI and non-AI.
- The shared catalog discovery operations precede Task 012 and are reused by
  CLI, future GUI, and future AI callers.
- It uses the legacy backend, not the Phase 13 direct frontend.
- It reuses the mixed Crossfader and minimal one-knob Gills boundary.
- It starts with one clock, one counter, one four-step pitch sequencer, one sine
  contract instantiated twice, one Crossfader, one filter, and one stereo
  output.
- It treats artifact generation, ARM compile/link, connected execution,
  real-time behavior, and audible behavior as separate evidence gates.

## Decisions deferred to the bounded tasks

- Exact new stable IDs, revisions, and content hashes.
- Whether family `000022` can truthfully gain the four-step implementation
  through an additive successor presentation.
- Whether clock-to-counter and mono-to-stereo joins are exact connections or
  require explicit visible adapters.
- Exact fixed pitches, tempo, detune, cutoff, resonance, and safe output level.
- Whether the existing schemas can express every required type/facet without
  an additive version.
- Exact backend subset changes, tool commands, device execution method,
  measurement thresholds, and listening method.

Those decisions are local to their owning tasks. None permits a redesign of
adjacent layers or a claim above the evidence actually collected.
