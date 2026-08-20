# Task 035: Proportional validation and governance consolidation

Status: explicitly authorized by the user on 2026-08-20 and review-ready in the
isolated `codex/task035-validation-consolidation` worktree.
This maintenance task creates no semantic record-set successor and authorizes
no staging, commit, push, publication, package installation, network source
fetch, native hardware access, upload, flash, or audible claim.

## Goal and why it exists

Make Schuss validation fast enough to use routinely while retaining the exact
fail-closed guarantees that protect accepted records, historical evidence, and
layer boundaries.

The existing suite has grown by replaying completed task validation inside
each later task. A single Task 034 context load validates 134 schemas and 462
records, then recursively validates the same cumulative members through a
30-manifest ancestry chain. That turns one logical validation into 2,112 schema
visits and 8,269 record visits. Focused, adjacent, and aggregate commands then
repeat many of the same modules, while ordinary discovery also includes copied
repositories, native compilation, and long render matrices. Recorded Task 032
and Task 034 end-of-task validation therefore took at least 37 and 34 minutes
respectively before all standalone reproductions were counted.

Task 035 changes the organization and implementation cost of validation, not
the facts it validates. One current record-set load must still authenticate the
complete cumulative closure and every exact parent relation. Expensive evidence
remains available through explicit profiles instead of running accidentally in
ordinary unit-test discovery.

## Exact baseline

The implementation baseline is commit
`ccafc1d403513c822d9294b6c257906820ff88eb`, containing Task 033 Phase 2 after
Task 034. The newest selected semantic snapshot is
`schuss-record-set-000031@1`; it and all accepted schemas, records, fixtures,
goldens, native packages, WAVs, evidence packets, and source locks are immutable
inputs to this task.

Task 035 allocates no product/domain schema version, stable ID, operation,
record, record-set revision, DSP factory, runtime ABI, compiler output, project
revision, or evidence level. It may version the maintenance-only governance
state, validation manifest/plan/report, and governance-summary formats that are
deliverables of this task.

## In scope

- Replace recursive cumulative-member revalidation with one load-scoped pass:
  validate every manifest and parent/subset edge, then validate the selected
  cumulative schema and record union exactly once.
- Preserve exact path containment, byte hashes, schema annotations, record
  structure and content hashes, stable identity/collision checks, enforced
  directory membership, parent ambiguity detection, and explicit parent-path
  override behavior.
- Reuse an already loaded exact context in tests whose `ProjectService`
  fixtures name that same base record set.
- Add one manifest-driven validation runner with separate `current`,
  `compatibility`, `configured-sources`, `native`, `reproduction`, and
  `release` profiles.
- Gate expensive copied-root/fresh-process matrices and native compile/render
  tests out of routine current validation. Small subprocess tests remain
  ordinary only when the process boundary is the behavior under test.
- Route checks requiring ignored `catalog/sources.local.yml` through an
  explicit configured-source prerequisite. Ordinary validation reports them as
  skipped; explicitly requested configured validation fails closed when the
  prerequisite is absent.
- Stop using intentionally historical Task 011A/023 presentation bytes as a
  current-behavior failure gate. Preserve their exact bytes and the VH-001
  audit; use current successor fixtures for current behavior.
- Standardize standalone evidence-runner terminology so `--check` verifies
  retained evidence and explicit reproduction performs fresh process,
  copied-root, compiler, or render work. The central validation runner uses
  `--only CHECK_ID` for an atomic selection at its declared cost.
- Adopt proportional validation policy in ADR 0018, workspace instructions,
  tool documentation, and the live task/status indexes. Correct the
  contradictory Task 033 Phase 2 status exposed by this audit.

## Out of scope

- Changing any product schema, record, record-set membership, catalog
  projection, operation result, DSP behavior, compiler behavior, runtime
  package, UI, device contract, source lock, or hardware path.
- Rebaselining, deleting, or modifying historical golden, WAV, package,
  observation, evidence, audit, or configured-source identity bytes.
- Treating an unavailable authenticated source as passing, fabricating
  `catalog/sources.local.yml`, or mutating an upstream checkout.
- Adding process-global production caches or allowing one top-level validation
  call to hide filesystem changes from a later call.
- Removing expensive reproduction, native, sanitizer, compiler, or configured
  checks. This task only gives them explicit ownership and cadence.
- Rewriting every historical task contract or archiving product contracts.
- Hardware, audio/MIDI device access, upload, flash, SD mutation, listening,
  packaging, distribution, staging, commit, push, tag, or publication.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADRs 0016 and 0017, Task 033
and Task 034 contracts, every current record-set manifest, the contract test
suite, retained Task 032/034 validation summaries, and VH-001.

Deliverables are:

1. this frozen maintenance contract and ADR 0018;
2. a one-pass, load-scoped record-set ancestry validator plus focused negative
   and visit-count tests;
3. test-harness context reuse at the exact already-supported service boundary;
4. a checked validation-plan manifest and runner with explicit profiles,
   stable prerequisite diagnostics, granular `--only` selection, and
   read-only `--plan`/`--list` inspection;
5. ordinary-test gates for native, reproduction, and configured-source work;
6. accurate current-versus-historical golden assertions without changing the
   retained bytes; and
7. coherent validation, status, history, roadmap, and task-index prose.

## Validation classes and cadence

`current` is the routine green gate. It owns inventory/catalog discovery, the
newest semantic closure, active-task focused checks, current freshness, and
governance. Expensive tests listed in the validation plan are skipped here.

`compatibility` owns ordinary historical contract discovery when a shared
loader, schema rule, dispatcher, CLI grammar, or other inherited boundary can
affect completed behavior. It is not automatically replayed for every product
phase.

`configured-sources` owns checks that authenticate ignored machine-local source
locations. It must return a stable prerequisite failure when the mapping is
absent; a skip in `current` is not a source-evidence pass.

`native` owns native compilation, sanitizer, CTest, and render matrices.
`reproduction` owns expensive copied-root, fresh-process, and retained-evidence
reproduction commands. Small isolation fixtures may remain in compatibility.
A task selects only the entries affected by its change.

`release` explicitly composes `current`, `compatibility`, `native`, and
`reproduction`. It is required for a release, a task whose contract claims full
historical integration, or a change to shared validation/record-set
infrastructure such as Task 035. `configured-sources` is orthogonal and is
added explicitly when source-dependent inputs changed; this prevents a missing
machine-local mapping from blocking unrelated release evidence while retaining
an exit-code-2 fail-closed prerequisite.

Task 035 iterates with focused loader/runner tests, then runs adjacent current
record-set and service tests. After implementation freeze it runs each
applicable newly gated native/reproduction check at most once through one
`release` execution. Because Task 035 changes no configured-source semantic
input, the full configured profile is explicitly not applicable; its
standalone preflight must still return exit 2 rather than being synthesized.
Task 035 does change the Task 016, 017, 018, 021, 022, 027, and 028 historical
runners themselves. Tasks 016, 017, 018, 021, 022, and 028 reproduce their
immutable completion commits rather than asking successor code to recreate
historical presentation bytes. Task 018, Task 021, and Task 027
source-authenticated reproductions may
read an existing authenticated mapping passed by `--source-configuration`
without creating or changing a mapping in this worktree; these configured
historical checks remain explicit-only and run outside `release`. A later
documentation-only correction invalidates only governance checks, not already
frozen native or reproduction evidence.

## Acceptance tests

1. Loading the newest record set returns the exact existing schema and record
   closure and visits each selected schema/record member at most once per
   top-level call.
2. Every manifest in the ancestry remains schema/content-hash valid; stale or
   ambiguous parents, non-subset children, cycles, conflicting member
   declarations, missing/hash-mismatched members, identity collisions,
   directory extras/omissions, and path escapes still fail closed.
3. No mutable validation result or filesystem observation is cached across
   independent public `load_record_set` calls.
4. Task 031/032 service fixtures reuse an exact preloaded base and retain the
   same project, package, operation, and negative-case results.
5. Ordinary `current` validation launches no copied-root reproduction, native
   compiler, sanitizer, long render matrix, hardware, or network action.
6. Every gated test is named exactly once in the validation plan in both
   directions. New ordinary test modules default safely to `current`; malformed,
   duplicate, omitted, or unknown plan entries fail before execution.
7. Missing `catalog/sources.local.yml` produces named ordinary skips and an
   exit-code-2 prerequisite result when `configured-sources` is explicitly
   selected.
8. Historical Task 011A/023/VH-001 fixtures remain byte-identical, while the
   ordinary aggregate has no intentional known-red assertion.
9. `native` and `reproduction` entries execute only when explicitly selected
   and no entry runs twice in one composed validation session.
10. The runner emits deterministic structured results containing profile,
    status, command/test identity, prerequisite state, and measured duration;
    duration is evidence, never a brittle pass threshold.
11. Task 033 governance states one coherent Phase 2 result and no longer passes
    simultaneous “started” and “not started” claims.
12. Focused, adjacent, final diff/freshness/negative review, and the one
    applicable release validation complete without modifying product or
    historical evidence bytes.

## Review-ready evidence

- The final `release` profile passed all 33 unique selected checks in
  669.321 seconds. Its routine `current` portion completed in 17.842 seconds;
  the intentionally broad 485-test compatibility pass ran once in 430.498
  seconds.
- All twelve native execution checks plus the authenticated prerequisite
  passed, including CMake/CTest, compiler determinism, both desktop render
  paths, ASan/UBSan, and TSan.
- All fifteen release-owned reproduction checks passed. Tasks 016, 017, 022,
  and 028 replayed their immutable completion commits; the later copied-root
  and fresh-process checks each ran once.
- Explicit configured historical reproductions for Tasks 018, 021, and 027
  passed using the existing authenticated source mapping outside this
  worktree. The worktree mapping remained absent, and selecting the ordinary
  `configured-sources` profile returned the required exit-code-2
  `MISSING_CONFIGURED_SOURCE_PREREQUISITE` result rather than a pass.
- The final 43 focused Task 035/governance tests passed with only the expected
  reproduction-gated subprocess test skipped. Manifest validation, governance,
  `git diff --check`, immutable baseline-path comparison, and release-plan
  deduplication also passed.
- No product schema, record, record-set, fixture, source lock, package, WAV,
  or retained evidence byte changed. No hardware, audio/MIDI device, network
  source, packaging, staging, commit, push, or publication action occurred.

## Decisions Task 035 may make

- Internal organization and load-scoped caching of record-set validation.
- Validation profile names, manifest structure, runner output, prerequisite
  diagnostics, and safe default classification.
- Which existing expensive checks belong to native or reproduction profiles.
- Test-only reuse of exact contexts through already-supported APIs.
- Current-versus-historical assertion routing and concise governance wording.

## Decisions Task 035 must not make

- Any product identity, semantic, compiler, runtime, UI, device, source,
  evidence-level, or release decision.
- Any weakening of exact hashes, parent closure, source authentication,
  negative validation, or layer boundaries.
- Any historical rebaseline or claim that a skipped prerequisite passed.
- Any product-global cache or implicit dependence on test execution order.
- Any Git publication or hardware action.
