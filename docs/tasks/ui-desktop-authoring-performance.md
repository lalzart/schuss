# Unnumbered UI implementation: desktop authoring performance and reliability

Status: accepted by explicit user authorization and active locally on
2026-08-18; implementation is complete locally; user acceptance remains
separate; Git publication remains separate.

This is the third bounded implementation inside the unnumbered desktop UI
lane. It improves the already accepted project-backed patcher without adding a
new product capability, semantic operation, build route, or device route.

## Goal and why it exists

Make repeated project open, create, save, history, and revert practical in the
persistent desktop process while preserving the exact project/workspace,
record-set, validation, and atomic-write contracts.

The measured baseline initializes the exact desktop context in about 9.0
seconds and then spends about 18.5 seconds on every repeated inspection of an
unchanged project. Profiling attributes the dominant repeated cost to loading
and validating the same immutable 421-record base closure again. That delay
makes the authoring UI unsuitable as the foundation for later build or device
work.

## In scope

- Retain the exact validated loaded record set inside its in-memory operation
  context so an explicit `ProjectService` can reuse that exact base snapshot.
- Cache one project service's immutable base only when its portable locator and
  exact record-set reference match the already validated context.
- Add a small bounded in-memory cache for project semantic augmentation keyed
  by the exact base reference and canonical project-owned record bytes.
- Continue reading, parsing, hashing, schema-validating, ancestry-validating,
  and membership-validating every governed project file on each load. Only the
  expensive derived semantic validation may be reused after exact bytes match.
- Reuse a validated proposed context for the post-publication reload of the
  same exact immutable successor.
- Prove cache hits, misses, bounded eviction, stale/tampered-file rejection,
  deterministic result parity, and zero durable cache state.
- Add concise staged create/open/save progress, protect unsaved drafts on close,
  and keep conflict/error actions usable without discarding the draft.
- Measure cold initialization, first project open, warm repeated open, and the
  exact init/fork/rename workflow before and after the change on the current
  development machine.

## Out of scope

- New or changed public operations, request/result schemas, record sets,
  semantic records, graph edits, project formats, record-set membership, or
  validation rules.
- Skipping governed-file reads, trusting filesystem timestamps as semantic
  proof, accepting a stale locator/reference, weakening atomic recovery, or
  persisting a cache.
- A general background-job framework, worker pool, database, daemon, cloud
  service, telemetry, analytics, or cross-process cache.
- Build planning/execution, compiler changes, artifacts, USB discovery, device
  sessions, upload, reset, flash, SD-card writes, hardware action, real-time
  measurement, audible claims, packaging, signing, or publication.
- Catalog expansion, implementation promotion, Mutable-derived readiness
  changes, patch templates, graph-layout persistence, or prototype cleanup.
- Staging, committing, pushing, or rewriting historical golden/evidence files.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0014 and
0015, `docs/ARCHITECTURE.md`, `docs/PROJECT_WORKSPACE_CONTRACTS.md`,
`docs/DESKTOP_UI_BOUNDARY.md`, the completed desktop patcher contract, exact
record set `schuss-record-set-000024@1`, `OperationContext`, `ProjectService`,
the persistent Python desktop adapter, and the measured baseline above.

Deliverables are:

1. this accepted unnumbered implementation contract;
2. exact process-local base and augmentation reuse inside the shared core;
3. deterministic cache/parity/invalidation/performance-focused tests;
4. compact authoring progress, unsaved-close, and recoverable error states;
5. updated current UI boundary/status documentation; and
6. focused, adjacent, live desktop, diff, and final aggregate evidence.

## Cache and reliability rules

1. A cache key includes the exact base record-set ID, revision, content hash,
   and canonical project-owned record values. Display names, paths, or mutable
   UI state never establish semantic cache identity.
2. The cached base may be reused only for the exact validated manifest path and
   reference already carried by the operation context.
3. Every load still validates workspace head bytes, complete immutable project
   ancestry, every owned record's schema/content/byte hash, parent chains,
   assets, governed membership, temporary state, and recovery state.
4. A changed exact record produces a cache miss after its bytes pass ordinary
   validation; malformed, stale, missing, extra, or hash-mismatched files fail
   before semantic reuse.
5. Cache entries are process-local, service-scoped, bounded, and discarded on
   process exit. They create no file and are not included in project identity.
6. Cached and uncached dispatch return byte-identical canonical results.
7. Failure injection, stale writers, atomic publication, and recovery retain
   their existing ordering and behavior.
8. Closing an editor with unsaved semantic edits requires explicit user
   confirmation. Failed/conflicted saves retain the draft and offer reload or
   retry without silently changing the accepted project.

## Validation cadence

- Focused: base reuse, semantic cache hit/miss/eviction, exact output parity,
  tamper rejection, no durable cache files, desktop bridge persistence,
  renderer loading/conflict/unsaved-close tests, frontend build, Rust tests,
  and structure/governance validation.
- Adjacent: Task 012A project atomicity/recovery, Task 026 authoring/history,
  v1/v3/v8/v11 operation compatibility, and desktop patcher persistence.
- Expensive: one before/after current-machine benchmark plus one browser and
  native-shell smoke after implementation freeze. No ARM, Java, build, USB,
  device, real-time, or audible reproduction applies.
- Aggregate: one final inventory/catalog/contracts discovery after the diff,
  generated-artifact, negative-case, and acceptance review is frozen.

## Acceptance tests

1. A persistent desktop service performs no second repository-context or
   record-set load for the exact base already validated at process startup.
2. Repeated unchanged project inspection hits the bounded semantic cache while
   still rereading and validating every governed project byte.
3. Init/fork/rename/save publication reuses the exact proposed semantic context
   for post-write reload and invokes full augmentation no more than once for
   each distinct exact owned closure.
4. Cache-disabled and cache-enabled project inspect, validate, transaction,
   history, and revert results are canonical-byte identical.
5. Wrong base locator/reference, stale head, changed owned bytes, malformed
   records, missing/extra governed members, symlinks, and recovery ambiguity
   continue to fail closed before a cache hit can authorize them.
6. The cache is service-scoped, bounded to a small documented count, evicts
   deterministically, and writes no durable file or presentation state.
7. The measured warm repeated inspection improves by at least 10x from the
   18.5-second baseline on the current development machine; the result records
   cold and warm timings without turning host timing into semantic evidence.
8. Create/open/save surfaces name the current stage, prevent duplicate actions,
   and remain keyboard/screen-reader understandable without relying on color.
9. Unsaved close requires confirmation. Save failure or conflict preserves the
   draft and exposes retry/reload; successful save clears the draft only after
   the accepted successor reloads.
10. The renderer gains no filesystem, shell, network, build, device, or USB
    capability and the desktop allowlist remains unchanged.
11. Existing project/workspace bytes, public operation schemas/results,
    record-set bytes, Task 026 authoring behavior, and atomic recovery remain
    unchanged.
12. Focused and adjacent checks, browser/native smoke, `git diff --check`, and
    the final aggregate complete with inherited golden/hash failures reported
    separately.

## Local implementation evidence

The same existing seven-node scratch workspace was measured before and after
the final cache implementation in fresh Python processes on the current
development machine:

| Measurement | Before | After |
| --- | ---: | ---: |
| Exact desktop core initialization | 9.047 s | 9.407 s |
| First `project.inspect` | 18.494 s | 0.918 s |
| Repeated unchanged `project.inspect` | 18.674 s | 0.012 s |

The repeated inspection is about 1,556 times faster and exceeds the bounded
10x acceptance threshold. These timings are host performance evidence only;
they do not change or promote any structural, build, device, real-time, or
audible claim.

Focused frontend, bridge, cache, parity, governance, structure, shared
operation, Task 012A atomicity/recovery, and Task 026 authoring checks pass.
The native Tauri shell starts without an error, and browser development mode
loads the existing seven-node/seven-cable project with no console warning,
error overlay, or operation alert. The final aggregate passes inventory 14/14
and catalog 6/6. Contracts ran 402 tests in 960.044 seconds and retained only
the three already audited Task 011A/Task 023 golden and Task 027 projection-hash
failures; no performance, desktop, project, governance, or current Task 030
test failed.

## Decisions this task may make

- The exact private in-memory cache representation, bounded entry count,
  deterministic eviction policy, instrumentation hooks, and focused tests.
- Whether reusable base/record-set metadata lives directly on
  `OperationContext` or in an equivalent private exact-value carrier.
- Compact progress labels, retry/reload placement, and unsaved-close behavior
  inside the existing desktop presentation boundary.

## Decisions this task must not make

- Semantic identity, validation meaning, project atomicity, catalog readiness,
  compiler/backend selection, build/device evidence, public schema allocation,
  or a new persistence/session/job protocol.
- A global mutable semantic cache, a cache keyed only by path/mtime, direct
  renderer filesystem access, or optimistic success before core acceptance.
- Permission to build, connect, upload, flash, stage, commit, push, or publish.

## Completion boundary

Completion proves that the existing desktop authoring workflow reuses exact
validated process-local work safely and becomes materially faster and more
recoverable. It does not add or prove build execution, artifacts, device
communication, real-time/resource behavior, audibility, packaging, or release
readiness.
