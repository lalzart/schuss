# Instrument Lab v1: Repeatable Validated Instrument Scaffold

> Status: proposed
> Proposal revision: 0.1
> Work type: workflow infrastructure supporting both Sonic Research Lab lanes;
> this is neither a new instrument design nor a source reimplementation.
> Original request: Preserve the lessons from Cinderwheel and Tide Pit in a
> cheaper, more reliable, graph-aware process that can build novel instruments,
> observed-behavior reimplementations, and authorized source ports without
> repeatedly recreating JUCE, MIDI, UI, renderer, and validation machinery.
> Implementation target: non-production Schuss research/prototype support plus
> migrations of the two existing prototypes as exact regression consumers.
> Decision gate: Task 036 must complete first. Documentation is approved in this
> chat; implementation requires a separately activated chat.

## 1. Thesis and working definition

### One-sentence thesis

Turn an approved, implementation-ready instrument bundle into a deterministic
portable-Core project, controller/host shell, objective renderer, validation
suite, and compact handoff by linking shared mechanics rather than copying
them, while keeping musical DSP and canonical Schuss identity instrument-owned.

### Why this exists

Cinderwheel proved that a novel instrument can move from proposal to a useful
JUCE standalone, but much of its experiment, control, host, and evidence
machinery was created during implementation. Tide Pit improved the process with
an exact source-equivalence bundle, generated control descriptors, a source
oracle, partition testing, and authoritative Core-state UI reflection. It still
required another instrument-local JUCE bootstrap, MIDI adapter, renderer,
manifest writer, UI shell, CMake surface, and validation driver.

The two prototypes now provide enough differential evidence to extract narrow
mechanics. They do not justify a universal DSP superclass, common musical state
model, or production runtime provider.

### Literal working artifact and evidence level

Instrument Lab v1 is working when all three consumers below build and validate
from one shared lab implementation in a fresh root:

1. Cinderwheel, with its existing float Core and retained render evidence;
2. Tide Pit after Task 036, with its fixed-Q27, 48 kHz, 16-frame source-exact
   Core and retained `39d8...ad2b` comparator; and
3. a non-musical generated smoke fixture proving the scaffold has no hidden
   dependency on either instrument.

The highest required evidence is host signal plus authenticated JUCE target
build. App launch, callback deadlines, physical controllers, listening,
packaging, canonical graph/provider integration, and production release remain
separate and unproved.

## 2. Exact authority and sequencing

### Frozen audit baseline

The proposal was written against tracked Schuss `main` and `origin/main` at
`2b0180a47f7ac03011f56e9683c77060c8080f09`. Ambient dirty or untracked files
are never normative inputs; activation must inventory and preserve them.

| Input | SHA-256 or exact identity | Role |
|---|---|---|
| Cinderwheel proposal | `cd0c09e0df22f382d74bb380fa9ab91549faf1894199f5d02e4ac5e3795a1549` | novel-design authority and implementation record |
| Cinderwheel README | `0cff98936464389e25d0a675e4e612dd5ed632eb25a48cbe935b450f204b80d6` | prototype scope and host/control architecture |
| Cinderwheel RESULTS | `02670d7a4d244c692b2953ec1cf20249e47834fcf385a867bef98330b02fa551` | retained structural/signal evidence |
| Tide Pit proposal | `3c2157eaa26ceed61afe87b256a395dccc5fbbd0dab889189926ffb72b5c2157` | source-port authority and fidelity boundary |
| Tide Pit workflow notes | `6e17c9a257f38c14acf4b92ea5e627caaba10d3e36a70e426f7dbd6637228e55` | two-prototype workflow findings |
| Tide Pit RESULTS | `0e6a07cbf01252b4e45cb6f23b24ce218554709b4a67765be27dbea751125836` | retained source/host/target evidence |
| Tide Pit GAPS | `eac5e576631ef69176ecf40a31c21e3ac3888f687551d4edda0e2f7279a96e8d` | explicit non-generalized and deferred seams |
| Launch Control 3 topology | `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b` | reusable physical surface contract |
| Cinderwheel reuse manifest | `19425167e2c27a37508a7acf594ed2263f36b06ea0051d177c6b9cf21c2320a9` | previously fingerprinted host candidates |
| Task 036 proposal | `be4636f2550481bd45cb982fe47c01ee8fbe0de74621f22e9d27cffca680cf7a` | shared-source design authority |
| Task 036 contract | `4bdd4b60fff8cc28c7f21a17763a949e2e123cafea84e2aad30252338be501f0` | predecessor scope and handoff contract |

The two prototype file hashes above authenticate proposal-time evidence. Task
037 activation must bind the completed Task 036 handoff and then fingerprint
the resulting migrated Tide Pit baseline; it must not force the old Tide Pit
file hashes to remain after Task 036's permitted path-only migration.

### Hard predecessor gate

Task 037 may not begin extraction or prototype migration until
`docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json`:

- exists and reports `complete`;
- validates against the final shared Mutable package and Tide Pit bytes;
- binds passing Task 036 results and gaps; and
- contains no provider, graph, runtime, device, or publication promotion.

If Task 036 is incomplete or its hashes drift, Task 037 stops. The tasks may not
be collapsed into one implementation diff because the differential audit must
inspect Tide Pit's final shared-source shape rather than its temporary vendored
shape.

## 3. Scope and decision rights

### In scope

- A complete differential audit of Cinderwheel and post-Task-036 Tide Pit host,
  control, UI, build, render, and validation seams.
- A repository-owned, prototype-only Instrument Lab under
  `research/prototype_support/instrument_lab/`.
- A deterministic generator/validator under `tools/instrument_lab/`.
- Shared CMake helpers for exact JUCE selection, Core-only tests, optional JUCE
  targets, and CTest registration without fetching unless explicitly enabled.
- Fixed-capacity raw MIDI intake and deterministic timestamp/ingress ordering,
  separated from instrument-specific semantic mapping.
- A host bridge parameterized by sample representation, fixed internal quantum,
  maximum callback size, and instrument-owned process adapter.
- Reusable WAV/hash/measurement/manifest mechanics driven by each instrument's
  frozen experiment rather than by hidden shared musical timelines.
- Generated control descriptors and descriptor-driven UI layout from a
  validated control map, with interactive display state read from accepted Core
  snapshots.
- A restart-safe latest-snapshot delivery contract or an explicit omission if
  its lifecycle proof cannot be closed; the known unsafe reset pattern may not
  be generalized.
- A prototype-only `dsp-topology.json` contract and validator using Schuss graph
  vocabulary without allocating canonical IDs or claiming execution.
- A compact, generated implementation handoff that points to exact authoritative
  files and hashes without copying proposal/source bodies.
- Migration of Cinderwheel and Tide Pit to link the proven shared seams, with
  exact DSP/source/control/render parity and recoverable ordering.
- One generated non-musical smoke fixture covering a third configuration.
- Focused, native, reproduction, and current-profile integration appropriate to
  the exact files changed.

### Out of scope

- New instrument DSP, tuning, modulation, scales, presets, musical gestures, or
  sound-design decisions.
- A universal `Core` base class, universal snapshot layout, common random state,
  common Reset/Freeze/Panic semantics, or one required numeric/sample-rate
  profile.
- Rewriting Cinderwheel or Tide Pit algorithms, source overlays, source oracle,
  state machines, or accepted control meanings to fit the scaffold.
- Moving Mutable source or policy beyond Task 036's exact package contract.
- Canonical Schuss schemas, stable IDs, component contracts, DSP graphs,
  instruments, performance-control records, providers, runtime factories,
  targets/backends, operations, projects, or record sets.
- Executing Task 034 performance-control graphs or expanding Task 033 Phase 3.
- Adding `juce_dsp`, plug-in formats, dynamic loading, public extension ABI,
  package distribution, signing, or notarization.
- External Sonic Research Lab plugin mutation. A precise plugin follow-up may be
  documented, but repository-owned code and validators remain authoritative.
- Audio/MIDI device access, physical controller configuration, app launch,
  listening, callback deadline claims, hardware, staging, commit, or push.

### Decisions this work may make

- Names and layout inside the prototype-only lab and tool roots.
- The narrow C++17 adapter/traits boundary required by the three consumers.
- Fixed capacities and stable diagnostics for shared host mechanics, provided
  instrument behavior and existing overflow accounting remain exact.
- Lab-local JSON shapes, deterministic canonicalization, code generation, and
  validation diagnostics.
- Which audited seam is `extract`, `adapter-owned`, `instrument-owned`, or
  `defer`, when evidence and migrations justify the classification.
- The smallest recoverable migration order and retained evidence layout.

### Decisions this work must not make

- Any canonical identity, graph/provider selection, product support, evidence
  promotion, or governance-routing decision.
- A shared abstraction chosen only because one prototype happens to implement
  it that way.
- Silent semantic conversion between float/Q27, sample rates, block quanta,
  units, gesture timing, or state models.
- Rebaselining a golden, render, state, or control result to make extraction
  pass.
- Copying shared implementation into generated prototypes instead of linking or
  referencing the one shared lab source.

## 4. Architecture

```text
approved proposal + ready implementation bundle
                         |
                         v
             prototype-index.json
        / control map / experiment / state /
       dsp topology / source equivalence when used
                         |
                         v
instrument-owned Core + thin InstrumentLabAdapter
                         |
        +----------------+----------------+
        |                |                |
 bounded MIDI      host partition     objective render
 and ordering      and sample bridge  utilities
        |                |                |
        +----------------+----------------+
                         |
       optional JUCE standalone + generated UI
                         |
       level-specific validation and evidence
```

Instrument Lab is an adapter and experiment environment. The Core remains the
only prototype musical authority. JUCE remains outside the Core. The lab does
not become a Schuss backend, provider, or canonical graph runtime.

### Shared versus instrument-owned boundary

| Candidate | v1 disposition |
|---|---|
| JUCE pin/version/archive authentication helper | extract |
| CMake target and CTest registration mechanics | extract |
| fixed-capacity raw MIDI envelope, ordering, and drop accounting | extract after differential parity |
| internal-quantum/sample-format host partition mechanics | parameterized shared bridge |
| WAV writing, SHA-256, common measurements, overwrite policy, manifests | extract |
| controller physical topology | reuse existing fingerprinted artifact |
| control labels, defaults, semantic actions, curves, gestures | instrument-owned data |
| generated descriptor mechanics | extract |
| Core snapshot-to-widget projection | instrument adapter generated or explicitly supplied |
| GUI visual identity and instrument-specific status content | instrument-owned |
| DSP state, algorithms, random state, buffers, source overlays | never extract in v1 |
| Reset, Panic, Freeze, capture, mutation, and mode semantics | instrument-owned |
| experiment conditions, comparator, seed, tolerances | instrument-owned data |
| callback real-time proof and physical-device lifecycle | defer |

The implementation must produce a row-by-row differential audit before moving
code. A candidate may remain duplicated temporarily when the common contract is
not proven; the task must not manufacture reuse to satisfy a line-count goal.

## 5. Artifact contracts

### `prototype-index.json`

Each lab consumer has one deterministic index containing:

- noncanonical prototype ID and revision;
- Sonic Research Lab lane (`new-design` or `source-reimplementation`);
- proposal, implementation-contract, state, control, topology, experiment,
  validation, result, and gap paths plus SHA-256 values;
- Core adapter target and supported host profile;
- optional source-package handoff references;
- exact reusable controller topology reference;
- evidence levels requested and explicitly deferred; and
- generated-artifact freshness relationships.

The index stores repository-relative paths only and rejects latest/ambient
selection, timestamps, build directories, hostnames, and absolute paths.

### `dsp-topology.json`

This is a required design and promotion-planning artifact, not a canonical
Schuss graph. It contains:

- public ports, parameters, actions, and displays;
- typed nodes, connections, feedback edges, and state-owning boundaries;
- local role IDs that cannot match Schuss stable-ID patterns;
- source-derived, newly designed, adapter, and fused-implementation labels;
- the instrument-owned Core/fusion boundary;
- unresolved mappings to future component contracts; and
- explicit `canonical_schuss_record: false` and `executable_graph: false` flags.

The validator fails on controller selectors, JUCE classes, source paths,
provider IDs, runtime factory IDs, target/backend IDs, or direct physical
controller-to-DSP references inside the topology. A deterministic promotion
needs report may describe missing contracts and implementation boundaries but
cannot allocate them.

### Core adapter boundary

The lab uses composition or C++17 traits, not inheritance imposed on existing
Cores. Each adapter declares:

- sample representation and conversion ownership;
- accepted sample rate and maximum host block;
- internal processing quantum, including one-frame/none;
- bounded semantic-event representation and ordering precondition;
- prepare/reset/process/snapshot/diagnostic functions;
- output clearing and unsupported-call behavior; and
- thread/lifecycle claims actually proved.

Raw MIDI cannot enter an instrument Core unless its approved source contract
makes raw bytes normative. New instruments receive timestamped semantic events.

### Control and UI boundary

Physical surface topology, protocol selectors, semantic mappings, and Core/UI
state are separate:

```text
controller topology -> surface assignment -> semantic map -> Core action
                                                     |
Core snapshot -> UI model ---------------------------+
```

Generated widgets display accepted Core state. Raw MIDI values remain
diagnostic observations and cannot overwrite contextual pickup, pending,
quantized, or rejected state in the UI.

### Renderer and validation boundary

Shared renderer code may own file encoding, hashes, metric calculations,
artifact manifests, overwrite refusal, partition iteration, and deterministic
result formatting. The instrument owns the source signal, event timeline,
conditions, comparator, state checkpoints, tolerances, and interpretation.

## 6. Minimal falsifying experiment

The central claim is false if shared mechanics cannot host both existing Cores
and one generated fixture without changing their accepted behavior or adding
instrument-specific copies of the shared implementation.

### Conditions

1. Build/test Cinderwheel before and after migration from identical tracked
   inputs; compare Core tests, control-map behavior, adapter parity, complete
   render matrix, metrics, hashes, and final state.
2. Build/test post-Task-036 Tide Pit before and after migration; compare source
   validation, exact Q27 golden, control/adapter/UI behavior, complete snapshots,
   render partitions, metrics, hashes, and target build.
3. Generate the smoke fixture in two fresh roots from the same index; require
   byte-identical generated source/configuration and identical test/render
   outputs.
4. Relocate the lab and generated fixture within a temporary copied root; prove
   no durable absolute path or ambient build dependency.
5. Mutate each authoritative input class separately and require a stable
   freshness or contract failure rather than stale evidence reuse.

### Stop or pivot conditions

- An extraction changes either instrument's DSP, control semantics, exact
  source comparator, retained render/state result, or supported host profile.
- The shared API requires Cinderwheel or Tide Pit to expose false capabilities.
- Generated projects copy the shared C++/JUCE implementation into each
  instrument instead of linking it.
- The topology artifact becomes a second canonical graph model or leaks
  controller/provider/runtime identity into DSP topology.
- A lifecycle or real-time claim depends on an unmeasured JUCE collector,
  callback, device restart, or GUI race.
- Task 036 source identity or handoff cannot be authenticated.

## 7. Acceptance matrix

| Claim | Required evidence | Explicit limit |
|---|---|---|
| Two-lane scaffold | generated new-design and source-port indexes validate | does not prove musical quality |
| Shared mechanics | three consumers link one lab implementation | does not create production ABI |
| Cinderwheel preservation | pre/post tests and render/state hashes agree | no new listening/device claim |
| Tide Pit preservation | source lock, exact `39d8...`, tests, renders, snapshots agree | Apple/compiler limits remain |
| Control correctness | exhaustive descriptors/selectors/actions and Core-state UI parity | simulated protocol is not physical device proof |
| Graph awareness | topology validates and promotion-needs report is deterministic | not canonical or executable |
| Fresh generation | two fresh roots and relocated root agree | build cache speed is not evidence |
| Context handoff | compact index/handoff resolves every required authority exactly | does not replace reading task/contract |
| Host build | exact authenticated JUCE build passes | no callback deadline or distribution claim |
| Workspace integrity | focused/adjacent/native/reproduction/current gates pass | no release profile unless scope expands |

## 8. Implementation stages

1. Verify Task 036 completion and freeze post-migration Tide Pit fingerprints.
2. Produce the differential audit and extraction/defer matrix before shared C++
   edits.
3. Freeze lab-local schemas, Core adapter profiles, capacities, diagnostics,
   generator outputs, migration order, and negative fixtures.
4. Implement CMake/JUCE authentication and validation/scaffold mechanics with
   the synthetic fixture first.
5. Extract bounded MIDI, host bridge, renderer utilities, generated controls,
   and UI-model seams one at a time, running focused parity after each.
6. Migrate Cinderwheel without altering its Core or musical contract.
7. Migrate Tide Pit without altering its Core, source profile, or oracle.
8. Generate compact handoffs and the deterministic graph promotion-needs
   reports.
9. Run affected native/reproduction checks once after freeze, perform an
   independent diff/freshness review, and record results/gaps.

Every migration is additive until its before/after comparator passes. Removal
of an instrument-local duplicate is permitted only after no remaining reference
uses it and the shared version has recoverable exact provenance.

## 9. Risks and unresolved decisions

| ID | State | Risk or question | Required disposition |
|---|---|---|---|
| IL-001 | EVIDENCE | Cinderwheel and Tide Pit differ in sample type, event API, internal quantum, and state | use explicit adapters; do not normalize DSP semantics |
| IL-002 | EVIDENCE | Tide Pit records an unsafe live mailbox-reset lifecycle gap | fix and prove a restart-safe shared contract or omit mailbox extraction |
| IL-003 | EVIDENCE | Task 034 performance graphs are structural only | keep topology non-executable and defer runtime execution |
| IL-004 | INFERENCE | shared renderer/JUCE/control mechanics will reduce future context | validate through the generated fixture and next instrument; do not claim token totals from code alone |
| IL-005 | UNRESOLVED | whether a fused compiled Core can later implement an inspectable compound graph | emit promotion needs; successor architecture task decides |
| IL-006 | UNRESOLVED | exact plugin/skill changes needed to route lower-cost models | write a bounded follow-up packet after repository interfaces freeze |
| IL-007 | EVIDENCE | JUCE distribution/module review remains incomplete | retain local authenticated-build boundary |
| IL-008 | HYPOTHESIS | two prototypes are enough to freeze a narrow host seam | reject or defer any seam that cannot pass both migrations unchanged |

## 10. Follow-up boundary

After Instrument Lab v1 passes, a separately proposed task may own:

- executable performance-control graphs;
- conversion of prototype topology into accepted component contracts and a
  canonical Schuss graph;
- a graph-preserving fused-compound/provider strategy;
- production instrument/project/machine identities;
- plugin/skill routing over the repository-owned lab; and
- the next real instrument as an end-to-end acceptance test.

Instrument Lab v1 may generate evidence and requirements for that task, but it
must not allocate its identities or silently implement it.

## 11. Approval and implementation record

The user approved creation of this documentation on 2026-08-20. That approval
does not activate implementation, alter `docs/governance/current-state.json`,
or authorize staging, commit, push, external plugin mutation, device access, or
publication.

Implementation begins in a new chat only after Task 036 is complete and the
user explicitly activates the bound Task 037 contract.

### Implementation fingerprints

To be completed after approval and readiness validation.

### Commands and results

Not run; documentation only.

### Deviations and remaining gaps

No implementation deviation exists yet. The risks above remain open until the
task's retained evidence resolves or defers them explicitly.
