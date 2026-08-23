# Task 040: Cinderwheel canonical vertical slice

Status: Phase 1 explicitly authorized and review-ready on 2026-08-22. The exact
allocation and implementation-ready bundle are frozen for user review. Phase 2
is not activated; no shared semantic/runtime implementation, device action,
Task 040 commit, or Task 040 push is authorized by this status.

## Goal and why it exists

Promote one deliberately narrow Cinderwheel path from an isolated Instrument
Lab prototype into the canonical Schuss model, so a saved project can resolve
one exact instrument through shared graph, instrument, performance-control,
target/backend, provider, build, runtime, and inspection authorities.

This is the next useful integration test for the backbone: it should prove that
Schuss can carry a musically coherent instrument rather than only individual
runtime primitives, while preserving access to the complete DSP topology and
without turning a prototype, controller map, JUCE class, or fused C++ factory
into graph identity.

## Work lane and approved authority

The lane is **new-design**. Normative musical intent is the approved pre-trial
Cinderwheel proposal revision 0.2 at Git blob
`c075035b9c844eedd29f7f172e557cc985ad6d48`, SHA-256
`d9b3a50cde3c25a4db6324bd8d20f1a65eaefcbd1ac8e9e7a42adc80713b5e84`.
The current proposal contains result backfill and is not a replacement for
that frozen approval fingerprint.

The isolated prototype supplies a falsifiable oracle and promotion needs:

- `research/prototypes/cinderwheel/prototype-index.json`, SHA-256
  `a15365efdbd731137a2d4b6d715114b920ecdf787086ba096b60b20dd341ab80`;
- `PROMOTION_NEEDS.json`, SHA-256
  `9abd9c3464885ab07541dfcdf6c65a5a8c19ee282d3299deb654762bce6e01fc`;
- `dsp-topology.json`, SHA-256
  `dff93dc5025be7280d2c565f9c388572acbe9707b13d967413cf471f21dc0b78`;
  and
- the regular Launch Control 3 map, SHA-256
  `d5df5f569bf37ed0dbd3e356a9c2f42ac01ed8364c2dc2bc6b07da2243e390f8`.

Prototype source is not automatically copied into a provider. The prototype's
float Core, objective renders, ledger, and host adapter are comparison evidence
only until Task 040 explicitly accepts a canonical realization.

This lane makes no source-faithful Tide Pit claim. Exact reuse or
reimplementation of the external Tide Pit/Mutable source closure would require
a separately approved source-reimplementation contract consuming Task 038's
authority. Task 040 may preserve the proposal's musical lineage, but may not
blend that claim with unreviewed source equivalence.

## Working artifact and evidence ceiling

“Working” means one repository-owned canonical Cinderwheel project/instrument
revision that can, without a GUI or physical device:

1. load through the ordinary project and record-set services;
2. expose the complete authoritative internal DSP graph and public instrument
   facets through shared inspection;
3. accept the frozen synthetic performance-control event stream through one
   executable canonical performance configuration;
4. resolve one explicit desktop target/backend/provider closure, lower and
   build deterministically, and render stereo host output through the accepted
   native runtime path; and
5. report accepted instrument state, diagnostics, exact package identity, and
   objective comparison evidence through shared Core operations.

The required ceiling is canonical model plus deterministic native host-signal
evidence. A built or rendered slice is not an application launch, callback
deadline, physical-controller session, listening result, packaging result, or
production release.

## Activation and allocation gate

Implementation may begin only after explicit Task 040 activation. The first
turn must:

1. verify the live branch, worktree, remote, active governance state, staged
   and untracked work, accepted Task 033 Phase 4 result, exact parent record
   set, current schema/operation/capability versions, and next stable-ID
   allocations;
2. stop on a task-number, ancestry, dirty-worktree ownership, or accepted-ADR
   mismatch;
3. create a deterministic implementation-ready bundle containing
   `implementation-contract.json`, `source-equivalence.json` with the explicit
   new-design rationale, `experiment.json`, `state-matrix.md`,
   `control-map.json`, `validation-plan.json`, `RESULTS.md`, and `GAPS.md`;
4. bind the exact approved proposal and prototype evidence above, literal
   comparator timelines, state transitions, numeric tolerances, output names,
   retention policy, and independent evidence gates;
5. run the bundle readiness validator and stop if it fails; and
6. amend this contract with the exact conflict-free record, schema, provider,
   operation, capability, and record-set allocation before changing a shared
   semantic or runtime file.

The audit must choose an exact numeric/provider route. It may extend the
JUCE-independent native provider or create another statically known provider
only when the component/binding/target/backend and source-release boundaries
are explicit. It may not imply float/Q27 equivalence or add `juce_dsp`.

## In scope after activation

- Exact canonical family, component-contract, implementation, binding,
  eligibility, instrument, DSP-graph, performance-control, project, provider,
  and record-set successors required by this one slice.
- A complete inspectable internal graph for the nine prototype promotion roles:
  stage clock, stage/mutation cycle, excitation voice, resonant body, bounded
  grain memory, wake ledger, mode-local effects, bounded stereo output, and
  their exact connections/state ownership.
- An explicit implementation-fusion description if several graph nodes share
  one compiled Core. Fusion may optimize execution but may not hide or replace
  authoritative graph internals.
- One regular Novation Launch Control 3 performance configuration using 16
  encoders, eight buttons, MIDI channel 16, CC20-35 and CC40-47, with the exact
  semantic transforms, gesture thresholds, takeover, Reset/Panic, feedback,
  and accepted-state rules frozen in the ready bundle.
- The minimum reusable performance-control executor needed to apply the
  synthetic event stream to public instrument facets. Controller selectors may
  not address DSP node IDs.
- The smallest canonical native DSP/provider realization that satisfies the
  experiment. A reusable primitive may be allocated only when its semantics
  and reuse boundary are independently exact; otherwise keep the role
  instrument-owned and inspectable.
- Deterministic lowering, package generation, host rendering, state/diagnostic
  inspection, objective comparator evidence, negative tests, and proportional
  fresh-root/native validation.
- Client-neutral operations needed for this slice, shared by CLI, desktop, and
  AI adapters. Opening a client allowlist remains a separate explicit decision.
- Documentation and evidence packets that preserve every correction and gap.

## Phase 1 activated allocation

The normative machine-readable freeze is
`contracts/task040/phase1/allocation.json`; the ready implementation bundle is
`contracts/task040/phase1/implementation-bundle/`. Both bind baseline
`b21a0c4aa88488adde04446f35a7fd1d91b06a38`, accepted Task 033 Phase 3/4
commit `0bf22b67b03862b2efecd9fed377118501bf5f8d`, and parent record set
`schuss-record-set-000033@1` at
`sha256:01dc913b0d637573adda283f84985e7196ee7162b6f2eaadf76b1d3a2890b786`.

The exact route reuses `schuss-compute-target-000002@1` and allocates
`schuss-backend-000003@2`,
`schuss-implementation-provider-000001@2`, source release
`schuss-source-release-000006@2`, registry
`schuss-rt-factory-registry-v2`, and factory
`schuss.rt.cinderwheel-q27-v0`. Audio and control remain explicit signed Q27
at 48 kHz with blocks 64, 128, and 512. There is no implicit float conversion,
float/Q27 equivalence claim, `juce_dsp`, or external DSP source.

The semantic allocation is family `schuss-family-000108@1`, outer contract
`schuss-component-contract-000032@1`, transparent compound implementation
`schuss-implementation-000169@1`, root graph
`schuss-graph-000007@1`, internal graph `schuss-graph-000008@1`, instrument
`schuss-instrument-000006@1`, project `schuss-project-000035@1`, performance
contract/graph/configuration `000003@1`/`000002@1`/`000003@1`, and build
request `schuss-build-request-000008@1`.

The prototype's eight local topology nodes carried nine promotion needs because
`role.node.stage-cycle` owned both pitch sequencing and bounded mutation. The
canonical freeze resolves that ambiguity as nine inspectable internal nodes
using component contracts `000033@1` through `000041@1`. Root inspection
expands the transparent compound to those nodes. Fusion
`schuss-implementation-fusion-000001@1` may select one factory only after
exact graph, contract, target, backend, provider, and implementation hashes
match; partial, stale, or ambiguous matches have no fallback.

Phase 2 allocates semantic record set `schuss-record-set-000034@1` over
`000033@1`. Phase 3 allocates native/evidence record set
`schuss-record-set-000035@1` over `000034@1`, provider binding
`provider-binding-000008`, eligibility `schuss-binding-eligibility-000055@1`,
evidence claims `schuss-evidence-claim-000082@1` through `000086@1`, catalog
`schuss-catalog-000001@7`, and selection
`schuss-catalog-selection-000001@6`.

Additive schemas are frozen as catalog corpus/projection v7, performance
control contract/graph/configuration v1, performance event stream v0,
implementation fusion v0, binding eligibility v1, backend v1, provider v1,
operation request/result v20, and application capability description v13.
The only new client-neutral operations are `performance.events.apply` and
`instrument.state.inspect`; the capability count becomes 52.

The experiment retains the prototype's six exact conditions and adds a seventh
fixed-round-robin comparator required by the approved proposal. It freezes seed
`0x43494e44`, 32 cycles at 0.8 cycles/s, literal sample events, output names,
event/pitch/safety tolerances, and checked-in retention. Readiness does not
execute that experiment.

## Out of scope

- A general instrument SDK, arbitrary native C++, public provider SDK, dynamic
  provider loading, plug-in hosting, JIT, or broad DSP palette expansion.
- Importing JUCE DSP, Mutable, VCV, or external Tide Pit source; claiming Rings,
  Braids, Plaits, Clouds, or Tide Pit source equivalence; or using their names
  as graph identity.
- Implementing the full Task 033 Settings/Object UI brief, redesigning the
  desktop shell, or making a prototype UI authoritative.
- A second controller page, a Launch Control XL mapping, faders, arbitrary MIDI
  learn, or direct controller-to-node mappings.
- App launch, audio/MIDI endpoint access, controller Custom Mode write, MIDI
  output/feedback capture, disconnect/reconnect testing, hardware upload,
  firmware/SD mutation, or connected-device evidence unless a later explicit
  subgate authorizes the exact action.
- General real-time, listening, cultural-authenticity, packaging,
  distribution-license, publication, or production-release claims.
- Rewriting Task 031/032/033 historical packages, observations, WAVs, source
  releases, provider bytes, or unrelated user work.
- Staging, commit, push, tag, or publication without separate authorization.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0016-0018,
Tasks 031-034 and the complete Task 033 Phase 4 handoff, the approved
Cinderwheel proposal fingerprint, the isolated prototype index/topology/control
map/results/gaps, and the repository instrument-development workflow.

Deliverables are:

1. the ready implementation bundle and frozen exact allocation;
2. additive semantic and project record-set successors for one Cinderwheel
   instrument and complete internal graph;
3. an executable performance configuration and deterministic synthetic event
   fixture using public instrument facets;
4. an exact implementation binding/provider/runtime closure with no implicit
   numeric conversion or source dependency;
5. one saved canonical project and deterministic build/render package;
6. accepted-state and diagnostic inspection through shared Core operations;
7. objective prototype comparator and state-equivalence results;
8. focused, adjacent, native, copied-root, negative, and freshness checks; and
9. `RESULTS.md`, `GAPS.md`, status, roadmap, task index, and architecture
   integration after implementation freeze.

## Serialized phases

### Phase 1: readiness and exact allocation

Freeze the ready bundle, current parent closure, new identities, numeric route,
graph decomposition/fusion boundary, operation changes, experiment, and
validation plan. Perform no shared implementation edit before this passes.

### Phase 2: canonical model and performance execution

Add the exact graph, instrument, project, public facets, controller-independent
performance-control semantics, regular-controller configuration, synthetic
event executor, and client-neutral inspection. No native DSP implementation is
promoted until the semantic closure passes.

### Phase 3: native realization and objective host signal

Bind and implement the smallest provider realization, deterministic package,
runtime path, and objective comparator. Preserve prior runtime bytes and
allocate exact successors wherever accepted authority changes.

### Phase 4: freeze and handoff

Run affected native and copied-root checks once after stability, review the
complete diff/evidence matrix, integrate documentation, and leave device,
real-time, listening, packaging, and release gates explicitly unresolved.

## Acceptance tests

1. The implementation-ready bundle is complete, portable, deterministic, and
   binds the approved proposal/prototype bytes before DSP or semantic edits.
2. Live parent ancestry and every allocation are frozen before shared changes;
   old record-set members and historical fixtures remain exact.
3. One canonical Cinderwheel project loads and resolves without depending on a
   machine-local path, collection order, runtime factory ID, or display name.
4. The authoritative graph exposes all nine promotion roles, connections,
   feedback/state boundaries, public facets, and any compilation fusion. No
   fused provider implementation hides compound internals.
5. The canonical instrument preserves the proposal's four-stage, Undertow,
   Pulse Divide, Wake, Ember, Bloom, freeze, mode-local effect, Reset, Panic,
   bounded-event, and output-safety semantics within the frozen tolerances.
6. The performance configuration covers all 16 encoders and eight buttons of
   the regular Launch Control 3 map exactly once, targets only public instrument
   facets, and produces deterministic accepted-state transitions for the
   synthetic event stream.
7. UI/CLI inspection reports authoritative accepted state and endpoint/event
   diagnostics separately from raw selector input. No physical success is
   inferred from synthetic receipt.
8. Target-independent graph validation precedes explicit target/backend and
   provider selection. Missing, stale, ambiguous, disabled, or unsupported
   resolution fails closed with stable diagnostics and no fallback.
9. The numeric profile, coefficient updates, smoothing, capacities, lifecycle,
   allocation, non-finite containment, DC/peak ceiling, and reset equivalence
   are exact and tested. Float/Q27 differences are measured, not waived.
10. The canonical render and event ledger are invariant under the registered
    block partitions and fresh-process repeat. The comparator can falsify the
    central mechanism and records all deviations from prototype evidence.
11. Prior Task 031/032 package/runtime behavior and the Task 033 seven-entry
    registry remain exact unless an allocated successor explicitly changes the
    affected authority; no historical golden is rebaselined.
12. Focused, adjacent, negative, native, sanitizer where applicable, and
    copied-root reproduction checks pass, followed by one final `current` gate.
13. Structural, native build, host signal, callback real-time, application,
    physical-device, listening, packaging, distribution, and production
    evidence remain independent in results and gaps.
14. No out-of-scope source, UI, hardware, Git, or remote mutation occurs.

## Decisions Task 040 may make after activation

- Exact additive IDs/revisions/hashes, schemas, record set, operation versions,
  graph decomposition, inspectable fusion metadata, and deterministic ordering
  required by this one slice.
- Whether a local role becomes an instrument-owned component or one narrowly
  reusable Schuss-native primitive, based on exact reuse and contract evidence.
- The explicit native numeric/provider route, coefficient/tolerance details,
  state equivalence relation, fixed capacities, diagnostic names, and package
  representation needed to meet the frozen experiment.
- The minimum device-independent performance executor and accepted-state
  inspection shape shared by all clients.
- Narrow implementation corrections that preserve the approved musical thesis
  and are recorded in the result/gap packets.

## Decisions Task 040 must not make

- Provider-, collection-, controller-, source-path-, JUCE-class-, runtime-
  factory-, target-, backend-, or display-name-based graph identity.
- An opaque instrument whose complete graph internals cannot be inspected.
- Implicit implementation substitution, float/Q27 equivalence, source
  compatibility, family-wide promotion, or evidence promotion.
- General graph cycles, polyphony, sequencing, MIDI learn, UI architecture,
  public extension ABI, or palette policy beyond the exact Cinderwheel need.
- Physical controller behavior, callback headroom, audible quality, cultural
  identity, distribution terms, or production readiness without their own
  authorized evidence.

## Stop conditions

Stop before implementation if the live task or parent allocation differs, the
ready bundle fails, the approved proposal bytes cannot be recovered, a required
source lane becomes mixed or ambiguous, or the canonical model would require
an opaque graph. During implementation, stop on unbounded callback work,
unresolved provider ambiguity, comparator invalidation, historical-byte drift,
or a request to promote evidence beyond the active gate.

Completion of this contract would make Cinderwheel canonical at the named
model/native host-signal ceiling only. It would not automatically activate a
desktop UI, physical controller, real-time, listening, packaging, or release
successor.
