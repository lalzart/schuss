# Compiler determinism matrix

Status: implementation and bounded validation complete on 2026-08-16; the
repository-wide contract suite retains six pre-existing failures reproduced
before this side task and from an untouched clean worktree at the same HEAD.

## Goal and why it exists

Harden the completed Tasks 013-015 compiler backbone by proving its planning,
diagnostic, origin/source-map, normalized-DSP, direct-C++, and portable
execution-result bytes do not depend on common host-environment variation.
This closes a reusable regression-test gap without selecting Task 016 musical
or runtime semantics.

## In scope

- A reusable fresh-process matrix for `CompilationContext`, `plan_build`, and
  `lower_minimal_direct`.
- Variation of fresh repository root, current working directory, available
  locale, `PYTHONHASHSEED`, record enumeration, timezone, source-date, and
  unrelated environment noise.
- Canonical byte/hash, stage/artifact/diagnostic order, origin/source-map,
  path/timestamp leak, host-compiled arithmetic, and parent semantic-record
  checks.
- Task 014 execution only through `schuss-build-handler-000001@1`, only after
  the retained prerequisite validates, and only into temporary scratch roots.
- Fixes only for determinism defects reproduced inside compiler/build modules
  or their focused tests/validators.

## Out of scope

- Task 016 algorithms or compatibility-mode selection, runtime ABI work,
  compatibility promotion, new semantic records, retained-evidence rewriting,
  UI, hardware, device, real-time, or audible work.
- Staging, commit, push, publication, upload, flash, or removable-media writes.

## Inputs and deliverables

Inputs are the exact Task 013-015 contracts, record sets, compiler/build
modules, Task 015 Blend graph/contract, and the optional authenticated Task 014
adapter closure. Deliverables are
`tools/contracts/compiler_determinism_matrix.py`, its focused tests, this
completion report, and the usage note in `tools/contracts/README.md`.

## Acceptance tests

1. The harness writes only into temporary fresh/scratch roots and authenticates
   source parent semantic bytes before and after each matrix.
2. Four fresh-process cells cover two relocated roots, three working-directory
   forms outside/inside those roots, two locales when available, four hash
   seeds, forward/reverse record enumeration, four timezone/source-date pairs,
   and four unrelated environment values.
3. Successful Task 013 and Task 015 plans, a multi-diagnostic invalid plan,
   every artifact and origin/source map, the normalized module, direct result,
   C++, and source map remain canonically identical.
4. Generated C++ compiles as C++17 and 38 arithmetic vectors match the pure Q27
   evaluator in every cell.
5. Task 014 execution runs only when its exact prerequisite validates; absence
   is an explicit `not-run`, never fallback to a fake or ambient handler.
6. Run the matrix twice, focused tests, record-set freshness checks, Tasks
   013-015 validators, the full contract suite, and `git diff --check`.

## Decisions this side task may make

- Harness/test layout, fixed scenario identifiers, portable result summary,
  deterministic negative fixture, leak classifications, and scratch layout.

## Decisions this side task must not make

- Direct semantics beyond Task 015, Task 016 compatibility choice, target ABI,
  implementation eligibility, semantic/evidence promotion, or any higher
  evidence claim.

## Completion report

The matrix runs four cells and returns one canonical
`compiler-determinism-matrix-result-v1`. Two required complete invocations
produced identical 6,794-byte stdout with SHA-256
`700b863f5a9aee9fd078dcf35f8c6d6c9733a56c78715faf6644d4e6c0b18527`.

The exact Task 013 successful plan remains 95,210 bytes with SHA-256
`d0fa1cc5375317cce3fec77fc91642d2ff28820897b1be2585b5c2e9ad1022b5`.
Its five artifact payload identities and 61-entry origin map are unchanged.
The negative matrix plan remains 21,225 bytes with SHA-256
`ac61c030db2e3f286fd9924764cef02563f0a8dcf455b1b38d7d026833e6caf9`
and preserves two ordered `COMPILER_CONTENT_HASH_MISMATCH` diagnostics followed
by one `COMPILER_ID_REVISION_DUPLICATE` diagnostic.

The Task 015 direct result remains 4,056 canonical bytes with SHA-256
`caa40eb4e8f170c19ecb5c2a6d5356abe37ae34cb84e3bfcc27360e08d1c66e4`.
The normalized module remains
`60aa4a2dc07ba64bb65c37d36841505e361f15245f39126b37cf7e9ddf3bdfdd`,
the 991-byte C++ remains
`a14f0733cf7e724e347e2edbafc8337bb26b18a6a16b6109aefd894cd540023d`,
and the source map remains
`7a06c1a8c3fb6d06a26929728d4ed86b157c09a91c8d0bca6534f6766296ef0f`.
All 38 compiled host vectors match the pure evaluator. No absolute path or
timestamp entered canonical compiler output.

All 144 inherited semantic record files were authenticated before and after
the matrix, with combined portable-path/hash digest
`d5365dbfcc27cd780a433062715ac6082dd8bc7d127572fb757a87c1592042bd`.
Task 013-015 manifests and record members are unchanged. No compiler/build
determinism defect reproduced, so no compiler or build semantic module was
changed.

Forty-nine focused harness/Task 013-015 tests pass. All six Task 013-015
record-set generator/validator checks pass. The complete contract suite was
run before and after this task. The final run executes 226 tests: 220 pass and
the same six inherited tests fail. Five failures are preservation/golden checks
that expect older target/build validator or `records.validate` hashes. All six
reproduce in the pre-change isolated baseline; the target/build validator drift
also reproduces from an untouched clean worktree at the same HEAD. The sixth
expects ignored Task 009 content-addressed files absent from both the source and
isolated worktree. These failures are not repaired here because rewriting
retained hashes/evidence or importing the absent ignored capsule is outside
this task and would violate its explicit boundary.

Structural and host-compiled evidence pass. A fresh ARM compile/link matrix was
not run because this isolated current-tree worktree does not contain the
ignored authenticated Task 009 content-addressed capsule; the harness reports
`skipped-prerequisite-unavailable`. The read-only Task 014 validator still
authenticates its retained seven-artifact evidence through level 5. Connected
device, real-time, and audible evidence remain `not-run`.
