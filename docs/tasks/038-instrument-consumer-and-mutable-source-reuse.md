# Task 038: Instrument consumer and Mutable source reuse hardening

Status: explicitly activated by the user on 2026-08-22 for uninterrupted
implementation. This task is a bounded successor to Tasks 033 Phase 2, 036,
and 037. It does not activate Task 033 Phase 3 and does not change
`docs/governance/current-state.json`.

## Goal and why it exists

Close the reliability and reuse findings exposed by the Schuss Generative Drum
Machine and Wirefall implementations:

1. make the Instrument Lab repository gate discover every live consumer rather
   than silently checking a fixed historical list;
2. make relocated consumer reproduction a reusable command rather than a
   consumer-specific manual procedure;
3. replace the drum machine's instrument-local 17-file Mutable/Braids intake
   with authoritative source-release references, two exact reusable physical
   closures, and one reusable non-provider Braids adapter; and
4. bind local JUCE builds to the accepted source-release authority and an exact
   extracted-tree fingerprint rather than accepting version macros alone.

This exists so later instrument work spends effort on new musical behavior,
not repeated source archaeology, copied dependency shelves, host authentication,
or remembered validation commands.

## Activation baseline

- Repository: `/Users/lanceship/Projects/schuss` on local `main` at
  `c6fad1f2530ada727092468cc05d4a366b6885c8`.
- Live governance: no active task; Task 033 Phase 3 remains the next unactivated
  candidate.
- Accepted source/provider parent:
  `schuss-record-set-000031@1` with content hash
  `sha256:09ef78ec79d72736add893045973070fa0b2c43e06fc124d05392213d73fc789`.
- Existing source releases end at `schuss-source-release-000007@1`; the next
  conflict-free source-release IDs are `000008` and `000009`, and the next
  record-set ID is `schuss-record-set-000032`.
- `catalog/sources.lock.json` pre-task SHA-256:
  `77af227973e89ade0f7410e3dc4588c1fb9f63b249cda4e45710d71fe745eb27`.
- Drum-machine source-lock pre-task SHA-256:
  `b9815983e4fc19e542fbb9fe0da81aecf27b1000c1993c778e8a427a107ecbff`.
- Drum-machine frozen render-manifest SHA-256:
  `c173d54bce78d4d4110a8de7d3adcb891df1fa5ae896ae2dcc5d198730adf5fe`.
- Five live musical Instrument Lab consumers are present: Cinderwheel, Tide
  Pit, Schuss Generative Drum Machine, Wirefall revision 0.1, and Wirefall
  revision 0.2. The smoke fixture remains a separate non-musical consumer.
- All prototype/proposal work for the two recent instruments is untracked and
  must be preserved. No staging, commit, or cleanup is authorized.

## In scope

- Discover live `research/prototypes/*/prototype-index.json` consumers in
  stable repository-relative order and validate all of them.
- Apply duplicate shared-lab implementation detection to every discovered
  musical consumer.
- Validate Sonic Research Lab v2 approval binding when a consumer uses that
  contract, while retaining the explicitly identified Cinderwheel legacy
  contract.
- Add a reusable relocated-consumer reproduction mode with explicit CMake and
  CTest selection and no implicit device, network, or JUCE work.
- Preserve the exact legacy-inventory `catalog/sources.lock.json`; add one
  task-scoped, generated source audit for `mutable-eurorack` and
  `mutable-stmlib` because that retained lock is not an appendable dependency
  registry.
- Add source releases `schuss-source-release-000008@1` and
  `schuss-source-release-000009@1` under one exact Task 038 successor record
  set, preserving all Task 033 Phase 2 members byte-for-byte.
- Add two source-only physical packages: the exact 12-file Eurorack Braids
  closure and exact 5-file stmlib closure currently authenticated by the drum
  machine.
- Keep repository URL, commit, provenance, license, and distribution authority
  in the source-release records; package manifests own only physical closure
  paths, hashes, component groups, and negative claims.
- Add one repository-internal, non-provider Braids adapter for initialization,
  model selection, render calls, and deterministic global RNG seeding.
- Migrate the drum machine to the adapter and shared closures only after its
  current structural and render baselines are captured.
- Bind the accepted JUCE `schuss-source-release-000007@1` to a deterministic
  extracted-tree manifest and make local Instrument Lab JUCE configuration
  fail closed on tree drift.
- Correct durable validation commands that contain machine-local absolute JUCE
  paths.
- Record exact results and gaps.

## Out of scope

- New or changed musical DSP, rhythms, presets, controls, mappings, defaults,
  UI behavior, render tolerances, or listening decisions.
- Combining the direct-upstream closures with Task 036's Ksoloti closure merely
  because four files have identical hashes.
- A monolithic Mutable package, complete Mutable repository import, public ABI,
  plug-in system, dynamic loading, or stable SDK.
- Catalog implementation, collection, component contract, graph, instrument,
  performance-control, binding, eligibility, provider, runtime-factory,
  target/backend, operation, project, or machine allocation.
- Task 033 Phase 3 provider generation or changes to its seven native bindings.
- Real-time, connected-device, Ksoloti, listening, distribution, packaging,
  signing, publication, app launch, audio/MIDI endpoint, or hardware work.
- Network fetches, dependency installation, upstream-checkout mutation,
  staging, commit, push, or removal of unrelated/untracked work.

## Inputs

1. `AGENTS.md`, project context/status, ADRs 0017-0018, and Tasks 033, 036,
   and 037.
2. The accepted Task 033 Phase 2 source-release schema and record set.
3. The Task 036 physical-source-package manifest, generator, validator, CMake
   seam, results, gaps, and completion handoff.
4. Instrument Lab workflow, validators, generator, reproduction runner,
   templates, negative fixtures, and central validation manifest.
5. All live consumer indexes, implementation contracts, CMake files,
   validation plans, results, and gaps.
6. Drum-machine exact source bytes, source lock, notices, Core, CMake, tests,
   and frozen render manifest.
7. Accepted JUCE source release `schuss-source-release-000007@1` and the local
   extracted source tree previously produced from its exact retained archive.

## Deliverables

1. This task contract plus `038-RESULTS.md` and `038-GAPS.md`.
2. Automatic Instrument Lab consumer discovery and expanded focused tests.
3. Consumer-specific relocated reproduction mode and tests/documentation.
4. Task 038 source audit, two source-release records, their deterministic
   generator/validator, and record set `schuss-record-set-000032@1`.
5. `packages/dsp_sources/mutable_eurorack_braids_v1/` and
   `packages/dsp_sources/mutable_stmlib_v1/`, each with generated manifest,
   notice, validator integration, CMake source-resolution seam, and smoke test.
6. `packages/dsp_adapters/mutable_braids_v1/` with a narrow C++17 API,
   deterministic tests, and no canonical/provider identity.
7. A generated drum-machine source-dependency handoff and migrated build with
   no instrument-local Mutable source subtree.
8. JUCE source-tree fingerprint authority, validator, and authority-driven
   Instrument Lab CMake authentication.
9. Updated workflow, validation plan, current/native/reproduction registrations,
   and exact completion evidence.

## Acceptance tests

1. The repository validator discovers exactly the five current musical
   consumers plus the smoke fixture and fails when any newly added consumer is
   invalid or contains copied shared implementation.
2. Each live consumer validates individually; v2 bundles bind an approved
   proposal path and SHA-256, while Cinderwheel is explicitly retained as the
   only legacy contract.
3. The relocated reproduction command configures, builds, and runs the selected
   focused CTests for both the drum machine and Wirefall without manual copy
   assembly.
4. Task 033 Phase 2 generated files and all parent record-set members remain
   byte-identical; Task 038 adds only source releases `000008` and `000009` and
   record set `000032`.
5. Each new `SOURCE_PACKAGE.json` is canonical, generated from its source
   release and physical bytes, has no duplicated upstream/license/catalog/
   provider metadata, and passes the existing negative package validator.
6. The shared packages contain exactly 12 Braids and 5 stmlib files. The drum
   machine contains zero files below its former `third_party/eurorack` path.
7. The reusable adapter builds independently and its deterministic reference
   test passes.
8. The migrated drum machine passes its complete focused suite and reproduces
   the exact pre-task render manifest without rebaselining.
9. A mutated JUCE source tree fails authentication even when its version macros
   still say 8.0.15; the exact retained extracted tree passes.
10. The cheap `current` profile remains free of compilation, long rendering,
    source fetches, machine-local source prerequisites, and device work.
11. Required affected native and reproduction checks pass after implementation
    freeze, with evidence levels reported independently.

## Decisions this task may make

- Exact package/component names, adapter API spelling, deterministic tree-hash
  algorithm, discovery exclusions, and focused reproduction CLI shape.
- Exact source-audit fields permitted by the accepted source-release schema.
- Mechanical Core/CMake changes required to preserve existing drum-machine
  behavior while consuming the reusable adapter.
- New Task 038-only validation IDs and generated evidence formats.

## Decisions this task must not make

- It must not change or reinterpret the instruments' musical contracts.
- It must not weaken, rebaseline, or relabel a failed or passing signal result.
- It must not infer provider eligibility, target compatibility, real-time
  safety, physical control success, listening quality, or production readiness.
- It must not mutate accepted Task 033 records, collection membership, catalog
  implementations, provider bindings, runtime factories, or governance routing.
- It must not treat matching hashes from different source releases as authority
  to merge their source closures.
- It must not delete the drum-machine source copy until authority, package,
  adapter, focused tests, and exact render parity all pass from the shared path.

## Working definition

The working artifact is a repository-internal source/reuse and validation
infrastructure successor with source, host-structural, host-signal preservation,
authenticated-JUCE target-input, and relocated-reproduction evidence. It is not
a production provider or a new musical instrument.
