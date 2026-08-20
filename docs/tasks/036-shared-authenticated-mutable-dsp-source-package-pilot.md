# Task 036: Shared authenticated Mutable DSP source package pilot

Status: proposed and documented on 2026-08-20; not activated in this chat.
The user requested implementation in a new chat. This file does not change
`docs/governance/current-state.json`, where Task 033 Phase 3 remains the next
candidate and is still not activated.

## Goal and why it exists

Create one reusable, authenticated repository package for Tide Pit's exact
21-file Mutable/Ksoloti dependency closure, migrate Tide Pit to consume it, and
remove the duplicate instrument-local source copy without changing one sample,
state transition, control, or host result.

Tide Pit proved that source fidelity depends on exact bytes, initialization,
numeric profile, compile flags, random ownership, fixed memory, and timing. Its
prototype-local vendoring was correct for the first proof, but repeating that
intake in every Mutable-based instrument would duplicate source, notices,
hashes, audits, and portability decisions. Task 036 extracts only the stable
raw-source boundary. It deliberately leaves compiled/runtime policy with each
consumer until a second real consumer proves a common provider seam.

## Approval, activation, and scheduling boundary

The direct user request authorizes this documentation now and records intent to
implement in a new chat. The new chat must begin by naming this task, reading
the current workspace contract, and rechecking live branch, worktree, remote,
routing, source roots, and proposal/task fingerprints. It may activate Task 036
only through an explicit user instruction in that chat or an exact carried
handoff that cites this file.

Task 036 is not Task 033 Phase 3. Phase 3 is limited to generation/refactoring
of the existing seven native factories and may add no source dependency,
provider, or runtime capability. Task 036 may proceed only as this isolated
source-package/Tide Pit pilot, or after governance is deliberately rerouted.
It must not silently consume Task 033 semantic allocations or ancestry.

## Exact baseline and proposal binding

- Schuss `main` and `origin/main` were both
  `2b0180a47f7ac03011f56e9683c77060c8080f09` when this contract was written.
- The baseline contains the tracked Tide Pit Gills portable JUCE prototype.
- Proposal:
  `research/proposals/shared-authenticated-mutable-dsp-source-package-pilot.md`.
- Proposal revision: 0.2.
- Proposal SHA-256:
  `be4636f2550481bd45cb982fe47c01ee8fbe0de74621f22e9d27cffca680cf7a`.
- Accepted architectural authority: ADR 0017, SHA-256
  `572aa089409086bf593d1e3fdd79d3d6eb99d65beac204a1eab2d5adbd5b1387`.
- Ksoloti source revision:
  `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`.
- Existing 21-file closure manifest:
  `0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f`.
- Tide Pit source-lock SHA-256:
  `2c255076667f5772448e390ff7da6f97666180d82c6492eb75a78fb88856b9f6`.
- Tide Pit canonical Q27 comparator:
  `39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b`,
  exactly 1,536,000 bytes.

Any baseline or proposal drift requires review before source movement. Hash
drift is never rebaselined merely to make the task pass.

## Architectural result

```text
authenticated Ksoloti source revision
              |
              v
packages/dsp_sources/mutable_ksoloti_v1
  immutable upstream bytes + lock + notice + component metadata
              |
              v
consumer-owned build wrapper and portability policy
  Tide Pit: Q27 / 48 kHz / 16 frames / RNG + arena overlays
              |
              v
instrument Core -> renderer or JUCE host
```

The package is source evidence and build input. It is not a provider. No graph,
project, instrument, catalog, or component contract may reference its path or
package-local component name.

## In scope

- Add the exact package root
  `packages/dsp_sources/mutable_ksoloti_v1/`.
- Preserve all 21 upstream files byte-for-byte under
  `upstream/firmware/mutable_instruments/`.
- Add one deterministic `SOURCE_PACKAGE.json`, one retained
  `THIRD_PARTY_NOTICES.md`, and package documentation.
- Add a reusable read-only source-package validator and focused negative tests.
- Add a non-provider CMake discovery seam that exposes the authenticated include
  root and exact component file sets.
- Add an independent compile/link smoke consumer that has no path dependency on
  Tide Pit.
- Update Tide Pit's CMake and source validation to resolve the shared package.
- Keep Tide Pit's compiled `tide_pit_mutable` target local so it continues to
  own compile flags, sanitizer instrumentation, numeric profile, and linked
  component selection.
- Remove `research/prototypes/tide-pit-gills/third_party/ksoloti/` only after
  the new package, external-source comparison, CMake references, and recovery
  checks pass.
- Update Tide Pit and Task 036 result/gap records with exact evidence.

## Out of scope

- Importing the complete Ksoloti or any complete Mutable Instruments repository.
- Adding a new algorithm, source revision, generated table, asset, or file.
- Editing, formatting, normalizing, or patching shared upstream bytes.
- Moving Tide Pit's own six Gills files or its defined-C++ voice generator.
- Moving Tide Pit's `sdram_malloc`, random-state, zero-storage, gesture, control,
  renderer, MIDI, UI, or host seams into the shared package.
- Creating a monolithic compiled Mutable library or public ABI.
- Creating or changing source-release, catalog, collection, component,
  binding, provider, runtime-factory, target/backend, project, or record-set
  semantics.
- Editing Task 033's provider manifest or generated registry.
- Claiming support for any of the 56 Mutable-derived catalog implementations.
- Hardware, audio/MIDI devices, listening, network fetches, dependency
  installation, packaging, signing, distribution, publication, staging,
  commit, or push.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/STATUS.md`, and
   `docs/governance/current-state.json`.
2. ADR 0017 and the Task 033 Phase 1/2 contracts.
3. The bound proposal and its 21-entry source table.
4. `research/prototypes/tide-pit-gills/third_party/SOURCE_LOCK.json`.
5. Tide Pit's notices, CMake, source validator, source-equivalence contract,
   golden test, renderer experiment, `RESULTS.md`, and `GAPS.md`.
6. An authenticated machine-local Ksoloti root at exact revision `08d3e6e1`,
   passed as a command-line prerequisite and never written into a durable file.
7. The exact existing JUCE 8.0.15 prerequisite for the adjacent target build.

### Deliverables

1. `packages/dsp_sources/mutable_ksoloti_v1/README.md`.
2. `packages/dsp_sources/mutable_ksoloti_v1/SOURCE_PACKAGE.json`.
3. `packages/dsp_sources/mutable_ksoloti_v1/THIRD_PARTY_NOTICES.md`.
4. The exact `upstream/firmware/mutable_instruments/` 21-file closure.
5. `packages/dsp_sources/mutable_ksoloti_v1/cmake/MutableKsolotiSource.cmake`.
6. A generic validator under `tools/source_packages/` and focused tests beside
   that tool.
7. A package-owned independent CMake/CTest smoke consumer.
8. Updated Tide Pit CMake/source-lock/validator references with no duplicated
   Mutable source subtree.
9. `docs/tasks/036-RESULTS.md` and `docs/tasks/036-GAPS.md`, or an equivalently
   clear retained result/gap section if repository convention changes before
   activation.
10. An implementation freeze review and exact validation report.
11. `docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json`, a deterministic completion
    handoff consumed by Task 037. It records only exact repository-relative
    package, validator, CMake-seam, Tide Pit consumer, and evidence references;
    it is not a semantic record or an activation signal.

## Package contract

### Immutable source boundary

Only the 21 files enumerated in the proposal may exist below `upstream/`.
Their repository-relative paths and bytes must remain exact. Package-owned
metadata, documentation, CMake, validators, fixtures, and overlays stay outside
`upstream/`.

### `SOURCE_PACKAGE.json`

The pilot manifest is build metadata, not a new canonical semantic schema or
stable-ID namespace. It must use normalized UTF-8/LF JSON with sorted keys and
stable array rules and contain at least:

- a package-local schema/version string;
- a package ID and revision that do not resemble Schuss semantic stable IDs;
- upstream repository URL and exact commit;
- immutable upstream root;
- all 21 paths and SHA-256 values;
- the sorted manifest algorithm and required manifest hash;
- per-file reviewed-license/notice scope;
- closed component groups naming only exact file paths;
- explicit claims that the package provides source identity/build input only;
- exclusions for runtime support, provider identity, graph identity, device,
  real-time, audible, and distribution evidence.

The manifest must not store an absolute path, timestamp, branch name as release
identity, machine hostname, build directory, or mutable display-path identity.

### Component groups

At minimum represent the existing closure without implying runtime support:

- `stmlib-core-headers`;
- `stmlib-units-source`;
- `stmlib-random-source`;
- `braids-resources`;
- `clouds-resources`; and
- `clouds-granular-headers`.

Every group contains only paths present in the 21-file manifest. Every file is
either part of at least one group or explicitly classified as transitive
support. Tide Pit may select the three existing linked translation units while
continuing to exclude `stmlib/utils/random.cpp` from its binary.

### CMake seam

`MutableKsolotiSource.cmake` may expose one `INTERFACE` header/include target and
one deterministic function that resolves named component groups into absolute
build-time source paths. It must validate the package manifest before returning
paths. It must not:

- compile a runtime provider;
- add global compile definitions or options;
- own sanitizer or optimization flags;
- supply global random-state ownership;
- link every source automatically;
- leak package paths into DSP graph or project identity; or
- fetch source from the network.

Tide Pit retains a local compiled target using the returned exact source list.
This prevents one consumer's Q27, block-size, `TEST`, sanitizer, or floating-
point profile from becoming package policy.

## Migration and recovery order

1. Verify live state, proposal/task fingerprints, external source revision,
   target cleanliness, and the current Tide Pit golden before writes.
2. Create the shared package alongside the existing Tide Pit copy. Do not use
   `git mv`, because it stages changes.
3. Validate byte identity, manifest, notices, component closure, source-root
   comparison, and independent smoke consumer.
4. Change Tide Pit's source-lock validator and CMake paths. Keep its consumer-
   local target name and compile policy.
5. Run focused Tide Pit Release and source/golden checks while both copies
   still exist.
6. Prove no code or durable contract still references the old subtree.
7. Remove only the exact duplicate
   `research/prototypes/tide-pit-gills/third_party/ksoloti/` subtree. The shared
   verified copy and Git baseline provide recovery.
8. Rerun all affected checks and perform an independent freeze review.

If any gate fails before step 7, retain both copies and diagnose. If a gate
fails after step 7, do not reset or silently recopy different bytes; report the
failure and restore only from the exact bound Git/source authority through an
explicit, reviewed operation.

## Acceptance tests

1. The shared `upstream/` tree contains exactly the 21 proposal paths, no
   missing or extra files, byte-identical to both the original Tide Pit closure
   and the authenticated Ksoloti revision.
2. The sorted path-sensitive manifest remains exactly
   `0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f`.
3. The source-package validator fails closed on a modified byte, missing file,
   extra file, duplicate path, unsorted or duplicate set member, absolute or
   escaping path, unknown component, component path outside the file closure,
   wrong revision/hash, absent notice, malformed encoding, and unknown field.
4. Validation output is deterministic, carries no timestamp or absolute path,
   and can compare an optional runtime-only authoritative source root.
5. An independent minimal CMake consumer includes representative stmlib,
   Braids, and Clouds headers and links the three existing resource/unit
   translation units without any Tide Pit source/include directory.
6. Tide Pit has no remaining regular file under
   `third_party/ksoloti`, no source/CMake/validator reference to that path, and
   no second copy of any of the 21 upstream paths within tracked Schuss source.
7. Tide Pit retains the same source-package paths, source selections, compile
   definitions, sanitizer coverage, Apple Release `-O2` profile, and exclusion
   of upstream `random.cpp` from the linked binary.
8. Tide Pit Release CTest passes all five tests and the reference output remains
   exactly 1,536,000 bytes with SHA-256 `39d8...ad2b`, peak 39,182,832, and RMS
   14,011,444.589680206.
9. Fail-fast ASan/UBSan CTest passes all five tests with every linked Mutable TU
   instrumented and no sanitizer diagnostic in retained output.
10. The authenticated JUCE tree builds the renderer, adapter test, and
    standalone; all seven CTests pass.
11. The 16/64/128/512 render artifacts and complete final snapshots remain
    equal; overwrite, experiment-tamper, and fresh-process repeat negatives
    remain exact.
12. Tide Pit control-map, experiment, source-equivalence, UI, adapter, and DSP
    source bytes change only where a portable dependency path/reference must
    change; all other differences require explicit review.
13. No schema, semantic record, record set, catalog projection, provider
    manifest, native registry, operation, graph, project, or current governance
    byte changes.
14. Focused, adjacent, final freshness/diff review, and one final `current`
    profile pass with the external Ksoloti and Gills source targets unchanged.
15. `036-INSTRUMENT-LAB-HANDOFF.json` validates, reports Task 036 completion
    rather than merely documentation or partial progress, binds the final
    source-package manifest and Tide Pit evidence hashes, and contains no
    absolute path, timestamp, ambient branch selection, Task 037 activation,
    provider claim, or mutable latest reference.

## Validation plan and cadence

### Focused fast checks

- Source-package manifest and validator unit tests.
- Package-local external-source comparison.
- CMake discovery/helper negative tests.
- Independent include/link smoke consumer.
- Tide Pit source-lock and reference-golden tests.

### Adjacent native checks

- Tide Pit Release CMake/build/CTest.
- Tide Pit Debug fail-fast ASan/UBSan CMake/build/CTest.
- Authenticated Tide Pit JUCE build and seven-test CTest.
- Tide Pit four-partition render matrix and retained hashes.

### Reproduction and integration

- One copied-root or relocated-package reproduction because path independence
  is the fact under test.
- One Schuss `current` profile after implementation freeze.
- `compatibility` and `release` are not required because no accepted shared
  runtime/schema/record behavior changes. They become required if the task
  expands into those layers.
- Do not mutate or fabricate `catalog/sources.local.yml`. Missing configured
  source prerequisites remain explicit rather than passing.

After a failure, iterate only the affected focused/adjacent checks. Rerun each
affected native/reproduction matrix once after the correction freezes.

## Required successor handoff

Task 037 is the first permitted consumer of Task 036's completion handoff. The
handoff file must use schema string
`task036-instrument-lab-source-handoff-v1` and contain:

- Task 036 task and approved-proposal SHA-256 values;
- status `complete` only after every Task 036 acceptance test passes;
- the exact shared package path, revision, final manifest SHA-256, upstream
  revision, and 21-file path-sensitive manifest hash;
- the validator command and repository-relative validator/test paths;
- the CMake include path, interface target, component-resolution function, and
  closed component-group names actually implemented;
- the migrated Tide Pit consumer target, consumer-owned compile policy path,
  source-equivalence path, reference-golden path, and final evidence hashes;
- the retained Task 036 result and gap paths; and
- explicit negative claims for provider, graph, runtime, device, real-time,
  listening, distribution, and publication promotion.

The handoff must not duplicate upstream source bytes, proposal prose, build
artifacts, absolute machine paths, or commands that mutate source or hardware.
Task 037 must fail closed if this file is absent, not complete, malformed, or
does not match the live package and Tide Pit bytes.

## Decisions Task 036 may make

- The package-local manifest's exact non-semantic key names and deterministic
  canonicalization.
- Component grouping names and membership within the exact 21 files.
- The validator's portable CLI and diagnostic codes.
- The non-provider CMake discovery function and interface target name.
- Focused fixtures, smoke-consumer implementation, and retained result layout.
- Mechanical Tide Pit path/reference changes and removal of the verified
  duplicate subtree.

## Decisions Task 036 must not make

- Any upstream source edit or source-oracle rebaseline.
- Any import of additional Ksoloti/Mutable files or a different revision.
- Any public/runtime ABI, compiled shared provider, dynamic loading, symbol-
  interposition, global RNG, allocator, numeric, block, sanitizer, optimization,
  or lifecycle policy.
- Any source-release-v0 successor, stable ID, schema, record, record set,
  catalog, collection, graph, component, binding, provider, target/backend,
  operation, capability, or priority decision.
- Any claim that source/package presence implies host eligibility, equivalence
  for another instrument, device execution, real-time safety, sound quality, or
  distribution permission.
- Any Task 033 Phase 3 implementation or alteration of the current scheduling
  authority without explicit activation.
- Any stage, commit, push, package installation, network fetch, hardware,
  audio/MIDI device, signing, publication, or distribution action.

## Expected implementation evidence

`docs/tasks/036-RESULTS.md` must retain:

- live baseline and exact proposal/task/source/package hashes;
- old and new scoped file inventories proving one upstream copy;
- validator positive and negative results;
- package and smoke-consumer commands;
- Tide Pit Release/sanitizer/JUCE/render commands and results;
- exact golden/render measurements and hashes;
- source-target cleanliness and worktree preservation;
- corrections made during validation; and
- an evidence ladder separating source, host structural, host signal, target
  build, real-time, device, listening, and production results.

`docs/tasks/036-GAPS.md` must retain at least:

- absence of a second real consumer;
- unresolved compiled shared-target/provider ABI;
- cross-revision coexistence policy beyond parallel package roots;
- distribution review;
- generic provider/catalog integration; and
- every real-time/device/listening limitation inherited from Tide Pit.

## Completion boundary

Task 036 completes only when the shared source package exists once, Tide Pit
consumes it, every exact source and Tide Pit equivalence gate passes, no
semantic/provider/governance layer changes, retained results/gaps are
review-ready, and the exact successor handoff above validates against those
final bytes.

Completion does not activate Task 033, authorize a second Mutable consumer,
promote catalog availability, create a provider, authorize publication, or
permit staging/commit/push. Those remain separate user and governance actions.

## New-chat handoff

The next chat should begin with:

> Implement Task 036 from
> `docs/tasks/036-shared-authenticated-mutable-dsp-source-package-pilot.md`.
> Treat the task as explicitly activated for this chat, recheck live governance
> and source prerequisites, preserve unrelated work, and stop if the bound
> proposal or source fingerprints drift.
