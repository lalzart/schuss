# Task 033: Source-neutral object collections and native implementation providers

Status: complete through Phase 4. Phase 1 is retained at commit `5dccfd2`;
Phase 2 is retained at commit `ccafc1d` with exact successor record set
`schuss-record-set-000031@1`; and Phases 3 and 4 completed at published commit
`0bf22b6`. The closeout authorizes no source import, dependency change, device
action, package/distribution work, UI implementation, or successor task.

Task 034 owns the accepted parent semantic record set and shared operation/
governance versions. Its integrated result is
`schuss-record-set-000030@1`, content hash
`sha256:199b3b2f8fe20ea6a2ce4751a9bd4d35a2e6522d69252ef916c7668ad5e93c54`.
Any Task 033 phase that needs a semantic record, record set, public operation,
application capability, or shared governance edit must consume that exact
accepted result in the current baseline, then allocate exact successors from
it. Task numbering does not override record-set ancestry.

Phase 2 was explicitly started by the user on 2026-08-20 in isolated worktree
`codex/task033-phase2-collection-provider-contracts`. The exact allocation
below was frozen against local `main` commit `2be7eb7` before any shared
semantic implementation file was changed. Its implementation, focused and
adjacent validation, reproduction, and review completed at `ccafc1d`. No push,
UI, source import, dependency change, or hardware action followed from that
completion.

## Goal and why it exists

Make Schuss's object architecture genuinely source- and target-neutral before
the catalog or native runtime grows further.

Ksoloti historically exposes several filesystem libraries, including a
factory library, and resolves their objects through library paths and load
order. Schuss already improves on that model: musicians browse functional
families, graphs reference exact target-independent component contracts, and
backends select exact implementation bindings for an explicit target. The
remaining implementation, catalog, and UI surfaces do not yet present that
separation coherently.

In particular, three different ideas are currently easy to confuse:

1. a Ksoloti factory or contrib **source library**, which is provenance and
   candidate evidence;
2. a Schuss **catalog implementation**, which belongs to a functional family
   and may have target-specific bindings; and
3. a Task 032 native **runtime factory descriptor**, which is a backend-local
   constructor/process entry for one exact eligible binding.

The first two are not runtime factories, and the third is not a catalog or
graph identity. Task 033 makes those distinctions explicit, makes native host
availability visible through the catalog without changing graph identity, and
replaces hand-maintained cross-language factory tables with one exact generated
provider manifest.

The task also performs two bounded compatibility audits:

- the exact 56-entry Mutable-derived cohort already catalogued by Task 030;
  and
- the `juce_dsp` module at Schuss's exact pinned JUCE 8.0.15 commit.

Those audits decide what is a useful candidate, what needs a new component
contract, what could be a host-only implementation, and what remains a utility
or unsupported dependency. Source presence never becomes automatic graph,
backend, real-time, or audible support.

## Architectural result

The intended reference and influence directions are:

```text
pinned source release ----> source audit ----> catalog implementation
                                                   |
catalog family --------> component contract <------+
                              ^                    |
                              |                    v
authoritative DSP graph ------+       implementation binding
                                                   |
                                      target/backend eligibility
                                                   |
                                      implementation provider
                                                   |
                                derived runtime factory descriptor
                                                   |
                                      selected backend/runtime

machine-local collection profile --influences--> browsing and local availability
machine-local collection profile --does not alter--> project or graph identity
```

The authoritative graph continues to reference only an exact component
contract ID, revision, and content hash. It never references a library,
collection, source path, JUCE class, runtime factory, provider, target, backend,
or display name. Target selection remains a later build decision.

## Terminology and ownership

### Source release

A source release is one portable source ID plus an exact repository/archive
identity, commit, hashes, scope-specific declared license evidence, and
importer boundary. It is evidence from which candidates may be reviewed. A
repository-level license is not silently applied as per-file evidence. The
release does not create catalog families or compatibility merely by being
installed or enabled.

Existing examples are `axoloti-factory`, `ksoloti-objects`, the two contrib
cohorts, the pinned Ksoloti patcher tree, and the pinned JUCE source release.
`mutable-instruments-derived` is not a source release: it remains an exact
per-implementation provenance facet across ordinary functional families.

### Object collection

An object collection is a curated, versioned discovery grouping over exact
catalog implementation references. It may support useful product views such
as Schuss Core, Ksoloti first-party, contributed, or an audited third-party
cohort. It is not a musical category, namespace, target promise, or stable
object identity. Membership changes create a collection successor, not new
family or implementation IDs.

The permanent function-first catalog remains the complete semantic view. A
collection is a filter or distribution unit over that view, not a second
catalog database.

Project-local object definitions remain owned by their exact project and are
presented as a separate source view. They are not installed globally or
silently promoted into an object collection.

### Catalog implementation

A catalog implementation is one concrete reviewed realization under one
functional family. Different Ksoloti, Schuss-native, JUCE-backed, user, or
community implementations may belong to the same family while retaining
different implementation IDs, provenance, bindings, eligibilities, resource
requirements, and evidence.

### Component contract and graph node

The component contract owns the target-independent public node signature and
behavioral contract. The graph node references that exact contract. A source
collection can be disabled, renamed, moved, or unavailable without changing
an already accepted graph revision.

### Implementation provider

An implementation provider is a statically known build/runtime module that
supplies exact realizations for named implementation bindings under named
target/backend pairs. Its manifest owns provider ABI, required source locks,
link requirements, callback constraints, factory descriptors, and release
boundary. It does not own families, contracts, graph nodes, or selection
priority.

The first provider is the JUCE-independent Schuss native core already embedded
in `schuss_rt`. A future JUCE DSP provider, if accepted by a successor ADR,
would be a separate host-only provider rather than a reason to turn JUCE
classes into graph identities or to put JUCE in the public `schuss_rt` ABI.

### Runtime factory descriptor

A runtime factory descriptor is a derived provider entry used to prepare and
process one exact eligible binding. It contains implementation details such as
ports, state size/alignment, reset/event/process functions, and provider-local
factory ID. It is never directly browseable or authored into a graph.

Product text and code should avoid an unqualified word `factory`. Use
`Ksoloti factory source`, `catalog implementation`, or `runtime factory
descriptor` according to the owned layer.

### Machine-local collection profile

A machine-local profile records only local preferences and availability:

- installed source/provider release;
- enabled for discovery;
- available for a named target/backend; and
- disabled or missing, with an exact reason.

Absolute source checkout paths remain only in ignored local configuration.
The durable profile refers to portable source/provider identities, never host
paths. Enabling a collection does not mutate a record set, import identities
into an existing project, change build priority, or make unsupported objects
addable.

An exact project remains loadable from its pinned base-plus-owned record
closure even if a collection is hidden locally. If a requested build requires
an unavailable provider or source dependency, resolution fails with the exact
missing dependency; it does not silently substitute another implementation.

## Proposal-time verified baseline

The proposal audit used clean `main` and `origin/main` at
`c1eaea0114630d07e59c859b9264c3de24909e54`, after completed Task 032. The
exact current host successor is `schuss-record-set-000029@1`, content hash
`sha256:8d6d8e5b0c3a90862f1e7c9ddab9c054a7b5908f268db9fa356c131bdc37c55c`.
These are audit facts, not a future activation baseline; activation must verify
the then-live parent again.

### Ksoloti source-library facts

`catalog/sources.lock.json` pins four Ksoloti object libraries plus the patcher
tree. Task 024 records the four enabled Ksoloti library roots separately:

- `axoloti-factory` and `ksoloti-objects` are the primary first-party candidate
  cohorts; and
- `axoloti-contrib` and `ksoloti-contrib` are pinned deferred provenance
  cohorts.

Task 024's primary census is 668 `.axo` files, 835 normal definitions, 666
canonical base references, and 19 `.axs` compounds. Those roots and paths are
candidate/provenance evidence, not functional categories or graph identity.
The ignored `catalog/sources.local.yml` maps only portable source IDs to local
checkouts for authenticated reproduction; it is not an application library
preference model.

### Current catalog and host facts

The exact Task 032 record-set projection retains 107 families and 133 catalog
implementations. Its readiness facets overlap: 112 implementations are
catalogued-only, 21 are contracted and bound, 8 are eligible, 7 are
compile-proven, and all 133 retain at least one unresolved fact. Those counts
do not describe one target unless the exact target/backend references are also
inspected.

Task 032 separately executes seven eligible native host implementations,
`schuss-implementation-000162@2` through `000168@2`, for Saw, PWM, Soft Clip,
Exponential Smoother, Crossfade, VCA, and stereo Output. Their runtime factory
descriptors are duplicated across the Python lowerer, generated package schema,
and C++ registry. The seven host implementation IDs do not appear as individual
entries in the 133-item catalog projection, so the current Objects view cannot
truthfully show this host availability per implementation.

This is a projection/provider integration gap, not permission to make graphs
reference host factories or to reuse a Ksoloti implementation identity for a
different realization.

### Mutable-derived facts

The exact Task 030 cohort contains 56 `mutable-instruments-derived`
implementations across the normal functional catalog. In the Task 032 context:

- 53 are catalogued-only;
- Struck Drum, Struck Bell, and the Rings-derived reverb are contracted and
  bound but remain unresolved;
- all 56 retain unresolved facts; and
- none has accepted desktop-host eligibility.

Mutable provenance therefore has high product importance but currently proves
source identity and catalog placement, not native JUCE execution, Ksoloti
equivalence, real-time behavior, or sound.

### JUCE facts

Schuss currently pins JUCE tag 8.0.15 at commit
`91ad83ae34a81e0833b1a2b0866f54846370ae53`, archive SHA-256
`04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70`.
The current source-lock record names only `juce_audio_basics`,
`juce_audio_devices`, `juce_core`, and `juce_events`. It does not import or
link `juce_dsp`.

The exact pinned `juce_dsp` umbrella includes 39 public utility/processor
headers. They cover buffer/SIMD helpers, filter design, FFT/windowing,
convolution, delay, oversampling, panning, filters, oscillator, gain,
waveshaping, dynamics, reverb, chorus, phaser, and other processors. These are
not 39 ready-made Schuss objects: several are utilities or composition
mechanisms, and every musical candidate still needs explicit family,
component-contract, parameter/state/lifecycle, provider, eligibility,
resource, and evidence review.

The module declares `juce_audio_formats` as a dependency and is
AGPLv3/commercial under the pinned JUCE source. Its APIs use JUCE process
specifications, audio blocks, preparation/reset lifecycles, and generally
floating-point-oriented templates. The accepted Task 032 runtime is instead a
JUCE-independent fixed-Q27 provider with one exact numeric profile. Direct
compatibility is therefore unproved. Importing `juce_dsp`, silently converting
Q27 and float, or placing JUCE types in the portable runtime would conflict
with ADR 0016 and Task 032 unless an explicit successor decision changes that
boundary.

## Activation and allocation gate

Creating this contract does not activate Task 033. On explicit activation, the
task must first:

1. verify the live branch/worktree, staged/untracked state, Task 034 status,
   exact accepted parent record set, current operation/capability versions,
   and current schema/stable-ID allocations;
2. stop if Task 034 is still changing shared semantic or governance surfaces
   needed by Task 033;
3. rebase or otherwise consume the accepted Task 034 successor before
   allocating a new record-set descendant;
4. verify all Task 030 catalog, Task 031 source-lock, and Task 032 package/WAV/
   registry fixtures before writing a generator or successor record;
5. verify the exact pinned JUCE archive and source-license/module declarations
   without trusting ambient installed headers; and
6. freeze exact schemas, records, providers, operations, and record-set
   allocations in this contract before implementation begins.

If Task 034's result, ADR 0016, Task 032's provider boundary, or the exact
catalog counts have changed, update the proposal explicitly rather than
forcing the stale baseline to pass. No conceptual name below reserves a stable
ID or schema version before that audit.

### Activation audit and Phase 1 result

Activation re-verified local `main` and `origin/main` at
`c1eaea0114630d07e59c859b9264c3de24909e54`, with Task 032 record set
`schuss-record-set-000029@1` and only Task 033 work untracked in the main
worktree. The separate Task 034 worktree completed its focused, adjacent,
copied-root, inventory, catalog, native-regression, and aggregate review. It
owns record set `schuss-record-set-000030@1` at content hash
`sha256:199b3b2f8fe20ea6a2ce4751a9bd4d35a2e6522d69252ef916c7668ad5e93c54`,
operation/result v17, application capability v10, instrument v1, performance
schemas, and shared semantic/governance integration. The reviewed result was
committed as `6010f29` and fast-forwarded into local `main` on 2026-08-20.
At that point Phases 2-4 were no longer blocked by Task 034 ownership. Phase 2
subsequently froze the allocation below and completed at `ccafc1d`; Phases 3
and 4 completed at `0bf22b6`.

Phase 1 produced and focused-validated:

- accepted ADR 0017, separating source releases, collections, catalog
  implementations, component contracts, providers, runtime descriptors, and
  machine-local profiles;
- a canonical 56-entry Mutable audit: 51 contract-first candidates, two
  existing-contract resolution lanes, two retained source-failure deferrals,
  and one retained unsupported deferral; and
- a canonical 39-header JUCE audit from the authenticated pinned archive: 20
  musical node candidates, 12 utilities, five composition helpers, one
  asset-dependent processor with a host-service trait, and one deferred
  implementation subject.

The exact focused commands are:

```text
python3 tools/contracts/generate_task033_phase1_audits.py \
  --juce-root <extracted-pinned-JUCE-root> \
  --juce-archive <pinned-JUCE-archive> --check
python3 tools/contracts/validate_task033_phase1.py
python3 -m unittest tools.contracts.tests.test_task033_phase1_audits
```

The source-authenticated generator check, committed-output validator, and three
focused unit tests pass. Phase 1 creates no provider, catalog promotion,
runtime dependency, source-lock change, graph/project change, or target
eligibility.

### Phase 2 frozen allocation

Phase 2 consumes exactly `schuss-record-set-000030@1` at content hash
`sha256:199b3b2f8fe20ea6a2ce4751a9bd4d35a2e6522d69252ef916c7668ad5e93c54`
and allocates only the following additive successors:

- record set `schuss-record-set-000031@1`;
- catalog corpus `schuss-catalog-000001@6`, projection
  `schuss-catalog-projection-v6`, and selector
  `schuss-catalog-selection-000001@5`;
- schema families `source-release-v0`, `object-collection-v0`,
  `implementation-provider-v0`, `implementation-availability-policy-v0`,
  `collection-profile-v0`, `catalog-corpus-v6`, `catalog-projection-v6`,
  operation request/result v18, and application capability description v11;
- source releases `schuss-source-release-000001` through `000007`, assigned in
  order to `axoloti-factory`, `ksoloti-objects`, `axoloti-contrib`,
  `ksoloti-contrib`, the pinned Ksoloti patcher tree, the unchanged Task 032
  Schuss native runtime source, and pinned JUCE 8.0.15;
- collections `schuss-object-collection-000001` through `000004`, assigned in
  order to Schuss Native Core, Ksoloti first-party, Ksoloti contributed, and
  the exact Mutable-derived audited cohort;
- provider `schuss-implementation-provider-000001`, the statically linked,
  JUCE-independent `schuss_rt` native core under ABI `schuss-rt-abi-v1` and
  registry version `schuss-rt-factory-registry-v1`;
- availability policy `schuss-implementation-availability-policy-000001`,
  reporting the exact desktop-host pair
  `schuss-compute-target-000002@1` / `schuss-backend-000003@1` and the exact
  current direct-Ksoloti pair `schuss-compute-target-000001@2` /
  `schuss-backend-000002@4` independently; and
- read-only operations `collections.inspect` and
  `implementation.availability.inspect`, carried only by request/result v18
  and capability v11. Existing CLI, desktop, AI, and MCP allowlists remain
  closed.

Catalog corpus revision 6 adds exactly seven catalog members using the already
allocated host implementation identities `schuss-implementation-000162`
through `000168`. Each member remains a catalog companion at revision 1 and
joins, through exact references, to the accepted revision-2 component binding,
eligibility, component contract, provider entry, target, and backend. No
Task 030 member byte is rewritten and no new DSP implementation identity is
allocated.

An exact catalog implementation locator for collection membership is the
immutable catalog reference plus one implementation ID that resolves exactly
once in that catalog projection. This keeps all frozen Phase 4A and Task 030
members addressable without inventing revisions or hashes for legacy overlay
members. It is not valid graph identity.

`collection-profile-v0` is a non-semantic operation input. It may name exact
installed source/provider releases, enabled discovery collections, and a local
presentation order. It is not a record-set member, project dependency, build
priority, or selection input. Phase 2 allocates no profile stable ID and no
mutation operation. Project-owned objects remain a separate exact-project
source view and are never installed into these collections.

The provider record binds the seven exact accepted host bindings to their
existing provider-local factory IDs, but Phase 2 does not allocate the Phase 3
canonical factory manifest or modify Python/C++ registry tables. Phase 3 alone
owns descriptor shape, generated language surfaces, and the registry refactor.

## In scope after explicit activation

- A durable architecture decision that fixes the source-release, object-
  collection, catalog-implementation, implementation-provider, runtime-factory,
  and machine-local-profile boundaries described here.
- Exact, closed contracts for pinned source releases, curated object
  collections, implementation providers, and the derived runtime factory
  registry, using portable identities and no host paths.
- Deterministic source/provider descriptions for the existing Ksoloti cohorts,
  Schuss native core, project-local objects as a distinct ownership form, and
  the pinned JUCE release as an audited candidate source.
- A catalog successor that gives the seven existing Task 031/032 host native
  implementation IDs explicit browseable companions under their exact
  families and contracts, without rewriting Task 030 or reusing a Ksoloti
  realization as a host realization.
- A target/backend availability projection that reports, per exact catalog
  implementation, the bindings and eligibility for desktop host and Ksoloti
  separately. `catalogued-only`, contracted, bound, eligible, compile-proven,
  device-tested, real-time-tested, audible-tested, and unresolved remain
  independent.
- A single canonical provider/factory manifest from which the Task 032 Python
  lowering table, package validation values, and C++ registry are generated or
  validated. The manifest must bind exact component contract, implementation
  binding, target, backend, provider ABI, factory identity, facets, state,
  lifecycle, dependencies, and content hashes.
- Preservation of the Task 031 v0 and Task 032 v1 package/runtime ABIs and all
  retained package, observation, and WAV bytes while the existing seven-entry
  provider moves behind generated metadata.
- A deterministic audit packet covering all 56 Mutable-derived catalog
  implementations. Every entry receives one evidence-bounded disposition,
  required contract/dependency/resource gaps, current target matrix, and a
  reasoned promotion lane or deferral.
- A deterministic audit packet for the pinned JUCE `juce_dsp` public surface.
  It distinguishes musical node candidates, implementation utilities,
  composition helpers, host services, asset-dependent processors, and deferred
  or unsuitable subjects. It records exact source spans/hashes, module and
  license dependencies, numeric/channel/lifecycle semantics, allocation and
  callback concerns, and the Schuss contract work required before promotion.
- A bounded next-tranche selection packet prioritizing musically useful
  default/core coverage. Selection must use exact evidence and may return fewer
  candidates than desired; it may not pad a tranche with inferred support.
- Client-neutral read operations sufficient for a later Settings/Object drawer
  to show collections, installed/enabled state, exact provenance, and per-
  target provider availability. Any machine-local mutation operation must be
  separately justified, atomic, path-safe, and unable to alter project or
  graph identity.
- Focused, adjacent, expensive-reproduction, negative, freshness, and final
  aggregate validation with exact results retained.

## Out of scope

- Implementing or redesigning the Settings panel, toolbar, Object drawer,
  graph canvas, inspector, add-node flow, target chooser, or any other React/
  Tauri presentation. This task only records the data and operation
  requirements for that later UI slice.
- Treating a Ksoloti library path, `factory`, Mutable Instruments, JUCE, Schuss,
  user, community, collection, or provider name as a primary musical category.
- Making source/library order, installation order, search path, display name,
  JUCE class name, or runtime factory ID a stable graph or catalog identity.
- Runtime cloning, pulling, updating, cleaning, or mutating any upstream
  checkout; arbitrary folder scanning; network-backed catalog truth; or
  automatic import from ambient JUCE/Ksoloti installations.
- Wholesale JUCE DSP import, `juce::AudioProcessorGraph` authority, plug-in
  hosting, VST/AU/CLAP scanning, dynamic libraries, hot loading, JIT
  compilation, arbitrary user C++, or a public provider SDK.
- Adding `juce_dsp` to `schuss_rt`, expanding the JUCE source lock, or executing
  a JUCE DSP node before an accepted successor ADR and bounded implementation
  task explicitly own the provider/numeric/license boundary.
- Implicit fixed-point/float, rate, channel, unit, ownership, event, or facet
  conversion. A different desktop-float target/backend or explicit adapter
  nodes require separate accepted contracts and graph revisions.
- Promoting all 56 Mutable-derived entries merely because source exists, or
  claiming that JUCE supplies equivalent Mutable algorithms.
- New oscillator/effect semantics, sampling/assets, polyphony, voice
  allocation, feedback cycles, scenes, sequencing, controller behavior, or
  performance-control semantics owned by Task 034.
- Ksoloti Java/`.axp` changes, ARM build/link expansion, USB, connected
  hardware, upload, flash, reset, SD mutation, physical audio/MIDI smoke,
  general real-time/resource promotion, listening, packaging, distribution,
  monetization, or release-license approval.
- Rewriting accepted Task 024/027/030 catalog records, Task 031/032 runtime
  bytes, historical goldens, or unrelated user work.
- Editing Task 034-owned shared files while that task is active, or staging,
  committing, pushing, tagging, or publishing without separate authorization.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs and architecture
contracts, the exact Task 030 catalog and Mutable source review, Task 031 host
source lock/bindings/runtime contract, Task 032 provider/lowering/runtime
implementation and retained fixtures, the Ksoloti source locks/current-source
corpus, the accepted result of Task 034 before semantic implementation, and the
exact pinned JUCE 8.0.15 archive.

Deliverables after activation are:

1. this contract updated with the verified live baseline and exact allocation;
2. one accepted architecture decision for source collections and
   implementation providers;
3. closed schemas and deterministic records for source releases, collections,
   providers, registry generation, and any local-profile read model;
4. a catalog successor exposing the seven existing host implementations and
   exact per-target/backend availability without changing prior bytes;
5. one canonical provider manifest plus deterministic generated/validated
   Python, schema, and C++ registry surfaces;
6. complete exact Mutable and JUCE audit packets and a bounded next-tranche
   recommendation;
7. client-neutral read operations for collection/provider inspection, with no
   UI allowlist opened by implication;
8. a concise UI follow-up brief describing Settings and Object drawer
   requirements without implementing them;
9. focused and adjacent tests, negative fixtures, fresh-root/source
   reproduction, native regression, and one final aggregate result; and
10. coherent status, roadmap, history-after-completion, task index,
    architecture, catalog, compiler, target/backend, and operation documentation
    updated only after Task 034 ownership is released.

## Serialized implementation phases

### Phase 1: Exact audits and architecture decision

Owns the two complete audit packets, terminology, record/reference direction,
provider placement alternatives, licensing/dependency facts, and accepted ADR.
It performs no catalog promotion, C++ build, JUCE module addition, runtime
execution, project mutation, or UI work.

The JUCE decision must explicitly choose among:

1. keep selected DSP algorithms as JUCE-independent Schuss native
   implementations;
2. define a later statically linked JUCE host-only provider behind a separate
   provider ABI and, if needed, a desktop-float target/backend; or
3. defer the JUCE candidate.

It may not choose an implicit mixed numeric graph or put JUCE in graph
identity.

### Phase 2: Collection/provider contracts and catalog availability

Owns additive schemas, exact records, catalog implementation companions,
target-matrix projection, read operations, successor record set, generators,
and negative reference/identity tests. It starts only after Task 034 has merged
and Task 033's exact allocations are frozen.

### Phase 3: Generated native registry

Owns the canonical provider/factory manifest and narrow Task 032 Python/C++/
schema refactor. The existing seven factories and all v0/v1 package/runtime
behavior remain exact. It adds no DSP node, provider, source dependency, or
runtime capability.

The 2026-08-22 activation freezes this exact allocation before implementation:

- no semantic record, stable ID, public operation, capability, record set, or
  provider successor is allocated; Phase 3 consumes
  `schuss-implementation-provider-000001@1` and
  `schuss-record-set-000031@1` unchanged;
- canonical manifest schema and artifact:
  `schemas/native-provider-registry-v1.schema.json` and
  `contracts/task033/phase3/native-provider-registry-v1.json`;
- deterministic generator, validator, unit/negative test, and copied-root
  reproduction runner:
  `generate_task033_phase3_registry.py`, `validate_task033_phase3.py`,
  `test_task033_phase3_generated_registry.py`, and
  `run_task033_phase3_reproduction.py` under `tools/contracts/`;
- generated language artifacts:
  `packages/schuss_core/generated_native_registry.py` and
  the descriptor-table region of `packages/schuss_rt/src/runtime_v1.cpp`;
- the two accepted v1 host schema files remain byte-compatible except that
  their factory-ID enumerations become generator-owned from the canonical
  manifest; and
- the existing role enum, function implementations, runtime ABI, registry
  version, factory IDs, exact contract/binding references, facet shapes,
  fractional bits, state size/alignment, lifecycle symbols, diagnostics, and
  output bytes are immutable Phase 3 inputs.

The activation audit found that Phase 2 source release
`schuss-source-release-000006@1` authenticates every `packages/schuss_rt` file
and its exact membership. Phase 3 therefore generates the C++ descriptor table
in place while retaining `runtime_v1.cpp` byte-for-byte and adds no file below
that authenticated source root. This preserves the frozen no-successor
allocation and lets the existing source-release stale-evidence check guard all
non-descriptor runtime code.

### Phase 4: Integration and follow-up packets

Owns final cross-layer validation, the bounded next-tranche packet, the UI
follow-up brief, documentation integration, implementation freeze, and final
aggregate. It does not implement the follow-up UI, Mutable tranche, or JUCE
provider pilot.

## Core rules

1. Source availability, catalog membership, graph contract, binding,
   eligibility, build, device, real-time, and audible evidence remain separate.
2. A collection contains exact implementation references; it never contains
   category paths or uses membership as compatibility.
3. A family may contain implementations from multiple sources/providers. A
   single implementation may have different bindings only when those bindings
   realize that exact implementation truthfully; a materially different
   algorithm/runtime realization gets a distinct implementation identity.
4. Every graph node retains one exact component-contract reference and no
   provider-specific identity.
5. Provider selection occurs only after target-independent graph validation
   and explicit target/backend selection. Zero candidates, missing provider,
   stale identity, or equal priority fails closed.
6. A runtime factory descriptor must resolve one exact binding and provider.
   No descriptor is selected by table order, path, display name, or collection
   enablement.
7. The canonical provider manifest is the single reviewed source for registry
   identity and shape. Generated language bindings may add only mechanically
   derived constants/function wiring and must be freshness-tested.
8. A local profile affects what a user sees and what installed provider can be
   selected. It does not rewrite accepted record sets, project heads, graphs,
   bindings, eligibility, or priority.
9. Opening an exact project never drops nodes because a collection is disabled.
   A missing executable provider is reported at build/session resolution.
10. Provenance remains inspectable per implementation. Mutable-derived and
    factory labels never become drawer roots by architecture.
11. `juce_dsp` utilities are not catalog objects. A JUCE processing class is
    only a candidate until an exact Schuss family/contract/binding/provider/
    eligibility chain is accepted.
12. Provider license and distribution state are explicit release facts. Private
    local use does not silently approve a distributable binary.

## UI follow-up requirements, not implementation

A later unnumbered desktop slice may add a compact Settings surface, but it
must consume Task 033's shared operations. The expected concepts are:

- Collections: Installed, enabled for discovery, and source/version status;
- Targets: Desktop Host and Ksoloti availability shown separately;
- Providers: exact native/provider version, missing dependencies, and license
  or distribution review state;
- Objects: function-first browsing with provenance, collection membership,
  contract availability, and the selected target's readiness visible without
  expanding every row; and
- Project dependencies: exact required implementations/providers with no
  destructive "disable and remove from graph" behavior.

The UI should not present one global "compatible" badge, because desktop host
support, Ksoloti support, compile proof, device proof, real-time proof, and
audible proof are different claims. It should also avoid separate permanent
Factory/Mutable/JUCE category trees; those are filters and source/provider
facets around the same functional catalog.

## Validation cadence

Focused validation covers contract activation/allocation guards, schemas,
canonical bytes, source and collection closure, target-matrix derivation,
catalog implementation companions, complete 56-entry Mutable disposition,
complete pinned-JUCE audit accounting, provider manifest closure, generated
registry freshness, duplicate/stale/missing provider negatives, local-profile
non-authority, and Task 031/032 byte preservation.

Adjacent regression covers Task 024/027/030 catalog and provenance, Task 031
source lock and host bindings, every Task 032 package/runtime/replacement
fixture, compiler selection, project authoring, desktop closed-operation
allowlists, MCP isolation, and the accepted Task 034 semantic closure. No
historical golden or source configuration may be changed merely to make the
successor pass.

Expensive reproduction runs once after implementation stability: authenticate
the exact JUCE archive and reviewed source spans, generate the collection/
provider/audit outputs in two copied roots and fresh processes, build the
unchanged seven-entry native registry with warnings as errors and existing
sanitizers, and reproduce the retained Task 032 reference outputs. No physical
audio/MIDI or Ksoloti hardware is part of this reproduction.

The complete diff, source hashes, generated freshness, negative matrix,
Task 034 ownership release, Task 031/032 byte preservation, and acceptance
matrix are then reviewed as the implementation freeze. One final inventory,
catalog, contract, and native aggregate runs after that freeze. If correction
is required, only affected focused/adjacent checks repeat before one final
aggregate rerun.

## Acceptance tests

1. The explicit activation is recorded, while no stable ID, schema, record
   set, operation, or provider is allocated before the Task 034 serialization
   gate opens.
2. Activation verifies the live accepted Task 034 result and freezes a
   conflict-free successor allocation before any shared semantic edit.
3. The accepted architecture keeps source release, collection, catalog
   implementation, component contract, binding, eligibility, provider, and
   runtime factory descriptor as distinct owned layers.
4. No graph, project node, family, or implementation stable identity contains
   or derives from a library path, collection name, JUCE class, runtime factory
   ID, target, backend, or mutable display name.
5. Existing Ksoloti source cohorts are represented as portable source/releases
   and collection facets without changing their Task 024 evidence or turning
   Factory/contrib into function categories.
6. All 133 Task 030 catalog implementations retain exact historical bytes in
   their record set. The successor exposes each of the seven existing host
   implementations as a distinct exact catalog/provider chain under the right
   family and contract.
7. Per-target availability distinguishes desktop host and Ksoloti binding,
   eligibility, and evidence. No unioned family state or source presence is
   rendered as target compatibility.
8. The canonical provider manifest resolves exactly the seven Task 032
   bindings and produces/validates matching Python, package-schema, and C++
   registry identities without hand-maintained duplicate tables.
9. Every accepted Task 031 v0 and Task 032 v1 schema, package, observation,
   registry behavior, offline WAV, replacement result, and diagnostic remains
   byte- or behavior-exact as its contract requires.
10. The Mutable audit accounts for exactly 56 attributed implementations and
    records current contract/binding/target gaps without inventing host or
    Ksoloti support.
11. The JUCE audit authenticates the exact pinned archive, accounts for all 39
    `juce_dsp` public umbrella headers, distinguishes utilities from candidate
    nodes, and records source/license/dependency/numeric/lifecycle constraints.
12. No JUCE class becomes a Schuss object or provider entry without an exact
    accepted family, component contract, binding, target/backend eligibility,
    and provider decision. `juce_dsp` remains unlinked in Task 033 unless a
    separately accepted successor scope explicitly permits one bounded pilot.
13. Enabling, disabling, or reordering a local collection profile changes only
    the declared discovery/availability read model. Exact project/graph bytes,
    record-set closure, and deterministic build selection remain unchanged.
14. Missing source, unavailable provider, stale hash, duplicate factory,
    ambiguous binding, unsupported target, disabled collection, and unreviewed
    license states produce stable distinct diagnostics with no fallback.
15. The bounded next-tranche packet is evidence-ranked, names all proof gaps,
    and permits a shortfall instead of padding the result.
16. No Task 034-owned surface, UI behavior, upstream checkout, historical
    record, hardware, or remote state is mutated outside the authorized phase.
17. Focused and adjacent checks pass; copied-root/source/native reproduction
    agrees; the reviewed frozen diff is clean; and one final aggregate result
    records inherited unrelated failures separately.

## Decisions Task 033 may make after activation

- Exact names, closed schemas, local IDs, and deterministic ordering for source
  releases, object collections, implementation providers, registry manifests,
  and local availability read models.
- The exact catalog companion representation for the already allocated host
  implementation IDs, provided Task 030 bytes and graph identity remain exact.
- The generated-registry layout and build integration needed to remove
  cross-language identity duplication without changing Task 032 behavior.
- Complete evidence-bounded Mutable and JUCE candidate classifications and the
  bounded next-tranche recommendation.
- Whether to recommend JUCE-independent native implementations, a later
  statically linked JUCE host provider/desktop-float backend, or deferral for
  each audited JUCE candidate.
- The smallest client-neutral read operations and data shape a later Settings/
  Objects UI needs, after Task 034 releases shared operation ownership.

## Decisions Task 033 must not make

- A new authoritative graph, project, instrument, performance-control, device,
  catalog-family hierarchy, or UI model.
- Source-, collection-, provider-, path-, class-, display-name-, or load-order-
  based identity or implementation selection.
- Inferred Mutable or JUCE compatibility; silent implementation substitution;
  family-wide promotion; or one readiness badge standing for several targets
  or evidence levels.
- A change to ADR 0016's JUCE-independent portable runtime or the accepted Q27
  profile without an explicit successor ADR and separately bounded execution
  task.
- Implicit numeric/rate/channel/unit conversions, dynamic provider loading,
  plug-in hosting, arbitrary code, or a public extension SDK.
- Task 034 controller/performance semantics, runtime MIDI behavior, UI layout,
  real device access, listening claims, packaging/distribution approval, or
  any Git/remote action.

## Completion boundary

Task 033 is complete only when its architecture decision, exact source and
provider contracts, successor catalog availability, single generated native
registry, complete Mutable/JUCE audit packets, read operations, negative
matrix, copied-root/native regressions, and final acceptance evidence all pass
from the post-Task-034 baseline.

Completion will not mean that every Ksoloti or Mutable object runs on the
desktop, that JUCE DSP has been imported, that a settings panel exists, that
desktop and Ksoloti implementations sound equivalent, or that device,
real-time, audible, packaging, distribution, or release evidence has been
earned. Those remain separately authorized follow-up tasks.
