# Task 041: Shared Gills engine-support dependency hardening

Status: explicitly authorized and completed in the worktree on 2026-08-23. The
required first read-only audit confirmed the exact five proposed consumers and
unchanged support-header bytes. The bounded implementation and validation are
complete; `041-RESULTS.md` and `041-GAPS.md` retain the evidence and limits, and
no active task remains. Authorization covered only the named support directory,
five consumer projects, and their narrow existing validator/release seam; it
did not adopt the rest of either dirty worktree or authorize Git publication.

## Activation baseline

- Schuss: local `main` at published `955084e581ebf21e979f039fb7bba088787b8f71`,
  with the inherited Task 040 closeout work preserved and nothing staged.
- Gills Instruments: local `main` at
  `33038b5de6315bce9bbe167062f2876823ff1adc`, even with `origin/main`, with
  the support directory and all five consumers user-owned and untracked
  inside a larger unrelated tranche; nothing was staged.
- Exact support header SHA-256:
  `79b125d08103b7383e18aefc66a40f5d3ea9a7df59420f8d855dccb45408278d`.
- Repository-wide direct/transitive search found exactly the five direct
  consumers named below and no transitive consumer.
- All five pre-change portable project gates passed. The recoverable 64-file
  byte baseline and preservation rules are frozen in
  `projects/gills-engine-support/TASK041_BASELINE.json` in the Gills checkout.
- The audit also found that the support and consumer notices referenced a
  missing repository-root `license.txt`; closing that exact notice gap is part
  of the already-declared license/closure scope.

## Goal and why it exists

Record a restrained selective-reuse architecture and, only after separate
explicit activation, harden the one shared Gills dependency that already has
demonstrated consumers: `gills_engine_support.h`.

Five Gills synthesis engines currently include that mutable sibling header.
The shared implementation is useful and has offline test evidence, but the
consumers do not bind an immutable version or revision and a project folder by
itself does not carry a deterministic self-contained dependency closure. A
later edit to the sibling header can therefore change all five instruments,
and packaging one instrument without the sibling support directory is
incomplete.

Task 041 exists to close that concrete integrity and packaging gap while
preserving all five instruments' behavior. It does not assume that one shared
header justifies a general module system.

## Demonstrated current problem

At proposal-revision time, the sibling Gills Instruments checkout contained
the untracked directory `projects/gills-engine-support/`. Its support header
had SHA-256:

`79b125d08103b7383e18aefc66a40f5d3ea9a7df59420f8d855dccb45408278d`

The following five headers included it through the mutable sibling path
`../gills-engine-support/gills_engine_support.h`:

1. `projects/coupled-resonator-gills/coupled_resonator_dsp.h`
2. `projects/feedback-pm-gills/feedback_pm_dsp.h`
3. `projects/pulsar-fof-gills/pulsar_fof_dsp.h`
4. `projects/scanned-gills/scanned_dsp.h`
5. `projects/wave-terrain-gills/wave_terrain_dsp.h`

The support report records portable host checks and two-path Cortex-M4
compile/link identity for those instruments. That evidence establishes useful
shared implementation and offline build behavior at the recorded bytes. It
does not create an immutable consumer pin, make each project self-contained,
or prove physical OLED behavior, callback margin, analog behavior, or audible
quality.

These are proposal-time observations, not accepted authority. The Gills
support directory and all five consumers are part of substantial user-owned
dirty or untracked work. An activation audit must re-establish their exact
bytes, ownership, consumers, and evidence before treating them as inputs.

## Architectural record: selective reuse

Schuss and Gills should reuse work at its narrowest stable owner:

1. **Generated mechanics** belong to the generator: fixed panel plumbing,
   deterministic patch/Object SDK glue, bounded display/control support, and
   generated validation harness structure should not be rewritten from prose
   for every instrument.
2. **Authenticated sources and adapters** retain their exact source-release,
   license, physical-closure, and adapter authorities. A consumer references
   those authorities rather than creating a parallel source shelf.
3. **Target-safe helpers** may be shared when real consumers demonstrate one
   stable interface and the helper has exact ownership, constraints, resource
   bounds, integrity, and focused tests.
4. **Musical behavior** remains instrument-owned by default. Oscillators,
   resonators, sequencing, voice state, effects, mappings, defaults, and
   gestures are not extracted merely because code looks similar.
5. **Canonical Schuss promotion** remains rare and separately activated.
   Shared Gills build code is not automatically a Schuss family, component,
   graph, binding, provider, instrument, project, or machine.

Similarity alone is not evidence of a reusable boundary. Two implementations
may differ in numeric domain, reset behavior, timing, state ownership,
licensing, resource bounds, or musical meaning despite repeated text.

This hierarchy is the architectural record retained by Task 041. It guides
future proposals, but it does not authorize Task 041 to create a generic Gills
Instrument Kit, module registry, or automatic reuse workflow.

## Review and activation gate

Creating or revising this contract authorizes documentation only. Task 041
implementation requires a later explicit activation that also confirms
whether the exact current Gills support directory and five consumer projects
are user-owned work that this task may modify.

The first implementation action must be read-only:

1. verify both repository identities, branches, remotes, worktrees, staged,
   tracked, and untracked status, and applicable repository instructions;
2. verify that Task 041 is the explicitly active task and no other task owns
   the affected boundary;
3. hash the complete support directory and the five complete consumer input
   closures;
4. enumerate every direct and transitive consumer of the support header;
5. map every support declaration to its real consumers and focused tests; and
6. record which current files are user-owned, generated, third-party, or
   proposed task output.

If ownership, consumer count, or current bytes differ materially from this
proposal and the difference is not already covered by the bounded decisions
below, stop for review. Task numbering does not override live governance.

## In scope after explicit activation

- Audit the complete `gills-engine-support` directory and all real direct and
  transitive consumers.
- Freeze a recoverable pre-change baseline for each of the five instruments:
  authoritative sources, generated outputs, controls, defaults, startup
  state, host-test results, target inputs, and exact dependency bytes.
- Establish one unambiguous repository owner, local identity, immutable
  revision or version, content-integrity record, license/notice boundary, and
  evidence ceiling for this existing shared dependency.
- Bind each real consumer to the exact accepted support revision and content
  hash, with no implicit `latest`, sibling-directory drift, or fallback.
- Add the smallest focused integrity and dependency checks needed to reject a
  missing, changed, ambiguous, or incorrectly packaged support dependency.
- Produce a deterministic self-contained release/dependency closure for each
  of the five consumers. Generated packaging or staging may copy the exact
  dependency bytes, but copied release bytes do not become a second authoring
  authority.
- Keep the header whole unless the consumer audit proves that a split or
  narrower ownership boundary is required. Any split must preserve behavior
  and remain specific to the demonstrated dependency; it must not become a
  speculative general module framework.
- Make only the mechanical include, validation, packaging, documentation, and
  test changes required for that exact closure.
- Retain one bounded audit/evidence report and one gaps report, then stop.

## Out of scope

- A generic Gills Instrument Kit or arbitrary reusable-module framework.
- A reusable-module schema, general module manifests, generated module index,
  registry, dependency solver, or package manager.
- Mandatory automatic reuse preflight, fuzzy or embedding search, AI candidate
  ranking, or module dispositions in `.gills.json`.
- General `.gills.json` module requirements or pin syntax beyond any narrow
  existing-consumer binding required for this one dependency.
- Cross-Schuss discovery projections, new catalog operations, or duplication
  of Schuss source/package/catalog authority.
- A broad pilot program, unrelated instrument migrations, new instruments, or
  addition of another legacy exemption.
- Changes to any instrument's musical DSP, control meanings, mappings,
  defaults, startup state, OLED behavior, sound tuning, or evidence claims.
- A universal DSP Core, public native-code SDK, dynamic loading, plug-in ABI,
  graph redesign, provider redesign, or compiler redesign.
- A new Schuss schema, stable ID, source release, catalog record, collection,
  component, graph, binding, provider, runtime factory, record set, project,
  instrument, or machine.
- Updates to the installed instrument-building skill or general AI authoring
  workflow. Those follow only if a separately allocated future system proves
  useful.
- Treating the entire dirty Gills tranche as one unit, adopting unrelated
  files, deleting superseded work, or normalizing third-party bytes.
- App launch, audio/MIDI endpoint access, controller configuration, USB or
  board access, firmware upload, SD-card mutation, listening, publication,
  distribution approval, staging, commit, push, or remote mutation.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, current status/governance, ADRs
   0017-0018, and the completed Task 038 source/adapter reuse boundaries.
2. The live sibling Gills Instruments repository instructions and exact
   working-tree status at activation.
3. `projects/gills-engine-support/README.md`, `LICENSE.md`,
   `IMPLEMENTATION_REPORT.md`, and `gills_engine_support.h`.
4. The five consumer DSP headers listed above plus each consumer's complete
   README, license, contract, compact patch, Object SDK manifest, generated
   `.axo`/`.axp`, forwarding headers, render helper, and host tests.
5. The live Gills project validator/release gate and the Ksoloti compiler
   evidence it already records.

### Deliverables

1. A retained audit identifying the exact support owner, bytes, declarations,
   consumers, tests, license boundary, current include behavior, and gaps.
2. The smallest machine-consumed identity/revision/content-integrity authority
   for `gills_engine_support.h`; it is specific to this dependency and is not
   an arbitrary-module schema.
3. Exact bindings from all five real consumers to that frozen dependency.
4. Deterministic self-contained dependency/release closure generation and
   verification for each consumer.
5. Focused positive and negative integrity, resolution, closure, and behavior-
   preservation checks.
6. Only the necessary support/consumer documentation corrections.
7. `041-RESULTS.md` and `041-GAPS.md`, or activation-time equivalents, with
   structural, host, target, device, real-time, OLED, and audible evidence
   reported independently.

## Integrity and packaging contract

- One repository-owned location is authoritative for the shared source.
- The authority has an explicit local identity and immutable revision or
  version bound to exact content hashes. The representation may be a narrow
  dependency record, generated closure manifest, or equivalently consumed
  existing format; Task 041 must choose the smallest form that the validator
  and packager actually use.
- Every consumer resolves the exact authority. Missing, changed, duplicate,
  or ambiguous bytes fail closed before target compilation.
- Updating the shared support requires a new revision and explicit consumer
  migration. It never retargets an existing instrument silently.
- A self-contained release closure contains the consumer's checked project
  sources plus the exact support source, license/notice material, and a
  deterministic inventory of included paths and hashes.
- Release closure ordering, encoding, and hashes are stable and contain no
  timestamps or machine-local absolute paths.
- A relocated release validates without depending on the original sibling
  repository layout or ambient global object paths.
- Generated closure copies are packaging outputs. They do not create five
  independently editable support implementations.

## Acceptance tests

1. The audit names every support declaration and all direct/transitive real
   consumers; unknown, dead, or consumer-specific declarations remain explicit
   rather than being silently generalized.
2. All five consumers bind one exact support identity, revision/version, and
   content hash. A one-byte header mutation, stale revision, missing source,
   duplicate authority, or mismatched license/notice fails with a stable
   diagnostic and no fallback.
3. A successor support revision can coexist without changing the five frozen
   consumers. Revalidating an old closure selects its old bytes or reports a
   missing exact prerequisite; it never selects `latest`.
4. Each consumer produces a deterministic self-contained release closure with
   the same path inventory and hashes in a relocated temporary root. Removing
   the sibling `projects/gills-engine-support/` directory from that relocated
   environment does not break the packaged closure.
5. The five instruments preserve their pre-change authoritative sources,
   controls, defaults, startup behavior, generated object/patch semantics, and
   host behavior. Any unavoidable byte change is explained and checked by a
   preservation comparator declared before the change.
6. Existing focused host/stress tests pass for all five consumers. After
   implementation freeze, each affected release gate produces successful
   source-tree and fresh installed-process Cortex-M4 compile/link evidence with
   deterministic generated C++ and binary identity.
7. The result does not add a generic module schema, index, registry, preflight,
   `.gills.json` module system, Schuss discovery projection, unrelated pilot,
   or canonical Schuss identity.
8. Results and gaps do not infer connected-device execution, callback margin,
   physical OLED behavior, analog quality, listening quality, distribution
   approval, or production readiness from structural, host, or ARM evidence.
9. No unrelated dirty or untracked file is overwritten, deleted, staged,
   committed, pushed, or promoted.

## Validation plan

Validation follows ADR 0018 and both repositories' local instructions:

1. While implementing, run focused tests for support declarations, exact
   revision/hash checks, negative mutations, include resolution, closure
   inventory, and relocated validation.
2. Run the existing project-local host/control/stress tests for the five
   consumers as the adjacent regression boundary. Do not run unrelated
   instrument suites while iterating.
3. Freeze implementation and preservation comparators before expensive work.
4. Run each of the five affected Gills release gates once after freeze. These
   establish offline source generation and target compile/link identity only;
   they do not access hardware.
5. Run the exact fresh-root/self-contained closure reproduction once after
   freeze.
6. Schuss `current`, compatibility, native, reproduction, and release profiles
   are not required unless implementation changes a Schuss-owned executable,
   schema, validation registration, or accepted authority beyond Task 041
   documentation/results. Select only the affected profile if that boundary
   changes.

Full Schuss release validation, repository-wide Gills release validation,
configured-source work, app launch, and hardware validation are not part of
this task by default.

## Deferred future reuse-system task

The following work is deliberately deferred and requires a new task number,
fresh contract, and separate explicit activation:

- a generic Gills Instrument Kit;
- reusable-module manifests or schemas;
- a generated module index or registry;
- mandatory automatic reuse preflight;
- general module pins or dispositions in `.gills.json`;
- cross-Schuss candidate discovery;
- broad pilot migrations; and
- general skill, prompt, or workflow automation around module lookup.

That future task should not be allocated merely because Task 041 succeeds. A
new proposal must first show all of the following from real repository work:

1. at least two distinct shared implementation dependencies, each with more
   than one independent instrument consumer, so this header is no longer the
   only demonstrated case;
2. the same discovery, identity, or packaging failure recurring in at least
   two independent later instrument efforts despite Task 041's narrow
   dependency hardening; and
3. a bounded experiment on those real dependencies showing that an index or
   preflight reduces inspected/recreated source, packaging steps, or failures
   enough to outweigh its persistent schema, validator, maintenance, and AI
   context cost.

The experiment must identify who consumes every proposed persistent field and
must compare against direct deterministic enumeration. Meeting these evidence
conditions supports review of a future proposal; it does not activate one.

## Decisions Task 041 may make after activation

- The exact repository-relative authoritative location, local identity,
  revision/version spelling, integrity representation, and deterministic
  closure layout for this one dependency.
- Whether the current header stays whole or is split/narrowed when the complete
  consumer and test audit demonstrates a real ownership boundary.
- The minimum mechanical include or forwarding-header changes required for
  exact binding and self-contained packaging.
- The smallest focused validator, packager, fixtures, comparators, and
  documentation changes needed to satisfy this contract.
- Exact stable diagnostics for missing, stale, changed, duplicate, ambiguous,
  or incomplete dependency closure.

## Decisions Task 041 must not make

- It must not generalize the one dependency into a kit, module platform,
  registry, discovery service, or public extension mechanism.
- It must not change or reinterpret any consumer's musical DSP, controls,
  mappings, defaults, startup state, display behavior, or evidence status.
- It must not merge the support dependency with Schuss catalog, component,
  graph, provider, runtime-factory, instrument, project, or machine identity.
- It must not infer source licensing, compatibility, real-time safety, device
  success, OLED success, audible quality, or production readiness.
- It must not mass-adopt the dirty Gills tranche, migrate unrelated
  instruments, rewrite accepted historical artifacts, or rebaseline a failed
  preservation result.
- It must not activate Task 040, the deferred reuse-system task, hardware work,
  publication, or any successor.

## Stop conditions

Stop before modifying Gills files if Task 041 is not explicitly active,
ownership of the current untracked support/consumer work is unresolved, live
governance assigns another task, the observed consumer set has materially
changed, licensing cannot be established, or a recoverable pre-change baseline
cannot be frozen.

During implementation, stop if exact pinning or self-contained closure would
require a general module framework, if a proposed split changes consumer
behavior, if an existing authority would be duplicated, if any preservation
comparator fails, or if the work expands into unrelated instruments, Schuss
semantic architecture, app/device access, or evidence promotion.

Completion means only that the already-shared Gills engine support is owned,
immutable by explicit revision, integrity-checked, reproducibly packaged, and
behavior-preserving for its five demonstrated consumers. Task 041 then stops.
It does not establish that a general reuse system would be useful.
