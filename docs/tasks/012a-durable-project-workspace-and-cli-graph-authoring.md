# Task 012A: Durable project/workspace and persistent CLI graph authoring

Status: complete locally on 2026-08-15. The user authorized implementation on
2026-08-15. All acceptance gates pass. The work remains unstaged and
uncommitted; no publication, push, or device action was authorized or taken.

Work in the Schuss repository. Before implementation, read `AGENTS.md`,
`docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/SCHEMA_STRATEGY.md`, `docs/OPERATION_CONTRACTS.md`, ADR 0008, and this
complete task. Work only on Task 012A.

## Goal and why it exists

Create the first portable, durable Schuss project/workspace boundary and make
the existing atomic graph-transaction semantics safely persistent through the
shared headless operation layer and product CLI.

The task exists because the current CLI operates on exact repository-owned
record-set fixtures. `graph.transact` can validate a proposed next graph in
memory, but it deliberately returns `persistence_status: not-written`.
Compiler, build, GUI, and AI clients need one durable authoring unit and one
safe persistence protocol before they can work on user projects without
inventing their own filesystem truth.

Task 012A is non-UI. It separates the project/persistence dependency formerly
combined with Phase 12 from the deferred, now unnumbered object-drawer and
graph-canvas milestone.

## Accepted inputs and frozen boundaries

Treat these as immutable inputs:

- all accepted Tasks 001-011C schemas, records, fixtures, artifacts, evidence,
  operation results, CLI goldens, and completion reports;
- the published implementation baseline at commit
  `3011b45fda2369dc4c47b83530014b55437b7c74`;
- the exact-reference, canonical-JSON, record-set, graph, instrument, target,
  backend, build, artifact, and evidence ownership rules;
- the existing pure `graph.transact` operation and its successful
  `persistence_status: not-written` contract;
- the existing product commands and their accepted defaults, streams, exit
  codes, help, completion, and canonical bytes; and
- ADR 0008 and the accepted headless-backbone sequence.

Implementation must begin from a clean reviewed baseline containing this task
contract. A later documentation commit may change the Git baseline hash but
does not change the accepted semantic inputs above.

## Required boundary decisions

Task 012A must preserve these distinctions:

- A **project** is the portable durable authoring unit. It pins exact semantic
  records and project-owned revisions.
- A **workspace** is the host directory and local coordination boundary used
  to load, lock, write, and recover a project. Its absolute path is not durable
  identity.
- A **record set** remains an exact semantic registry view. A project pins an
  immutable accepted base and must also enumerate every project-owned record
  through one exact closed overlay/index or successor view. The task may choose
  the smallest acyclic representation, but the project is not an ambient
  directory scan and may not mutate accepted base membership.
- A **DSP graph** remains an authoritative semantic record. A project points to
  an exact graph revision; it does not embed an unversioned mutable graph.
- A **presentation overlay** remains optional client data. Task 012A defines no
  canvas geometry, drawer state, or GUI document model.

If the smallest truthful implementation needs more than one project or
transaction record, references between those records must remain acyclic and
exactly hashable.

## In scope

### Durable project contract

- One closed, versioned project manifest schema and the smallest supporting
  schemas required for safe persistence.
- Opaque stable project identity, explicit revision, canonical content hash,
  and an exact parent reference for every successor revision.
- Exact references to the selected immutable base record set, every
  project-owned semantic record, the primary graph, and any included instrument
  or build requests. Base-plus-project closure and collision rules must be
  explicit and fail closed.
- Content-addressed asset references when already present in accepted inputs;
  no new asset import or transformation pipeline.
- A portable workspace layout with normalized relative locators. Absolute
  paths, usernames, timestamps, process IDs, and host-specific temporary names
  must not enter canonical project identity.
- Explicit separation between governed durable files and local lock,
  temporary, recovery, cache, or convenience state.

### Shared persistence protocol

- A client-neutral in-process project service beneath CLI, future GUI, and
  future AI clients.
- Additive versioned operation requests/results for the smallest complete set
  of project creation, inspection, validation, and graph-revision commit
  behavior.
- Reuse of the existing `graph.transact` edit vocabulary and semantic
  validation. Do not create a second graph-edit model.
- A deterministic write plan that names every expected old byte/hash, every
  proposed new byte/hash, the project revision transition, and the final
  commit marker or equivalent acceptance boundary.
- Exclusive local coordination sufficient to reject concurrent or stale
  writers without treating a lock file as durable project truth.
- Atomic publication or an equivalently proved recoverable protocol. Failure
  before the acceptance boundary must leave the prior project valid; failure
  after it must load exactly the new project. Partially accepted state is
  forbidden.
- Explicit recovery behavior for temporary files, abandoned locks, orphaned
  unreferenced records, and interrupted writes. Recovery must fail closed when
  ownership or the accepted project revision is ambiguous.

### Product CLI

- Explicit project/workspace selection; no ambient nearest-parent project
  discovery unless the task both specifies and proves an unambiguous portable
  rule.
- Deterministic commands for project initialization, inspection, and
  validation.
- A persistent graph-transaction command that writes only when the user
  supplies an explicit write intent. Existing proposal-only behavior remains
  available and unchanged.
- Human and canonical-JSON results derived from the same shared operation
  results. CLI code may parse arguments and render results but may not own the
  project semantics, locking, transaction, or recovery algorithm.
- Stable stdout/stderr/exit-code rules and static shell completion for new
  commands.

The task may refine exact command spelling. The expected conceptual surface is
equivalent to:

```text
schuss project init ...
schuss project inspect ...
schuss project validate ...
schuss graph transact ... --project ... [--write]
```

### Validation and fixtures

- One minimal portable positive project fixture using accepted Task 011C
  records without copying or rewriting them.
- Successor graph/project revision fixtures produced through the shared
  transaction path.
- Negative fixtures for stale hashes, missing parents, invalid exact
  references, path escape, symlink escape, duplicate identities, concurrent
  writers, malformed locks, interrupted writes, and uncommitted partial state.
- Failure injection at each filesystem mutation boundary.
- Fresh-process and cross-directory determinism tests.

## Out of scope

- Object drawer, graph canvas, desktop/web GUI, presentation overlay,
  keyboard/mouse interaction, or visual layout.
- Task 013 compiler-front-half implementation, build planning, compound
  elaboration, dependency/resource planning, backend lowering, `.axp`, Java,
  generated C++, compiler/linker invocation, artifact execution, or new build
  evidence.
- A generalized `schuss build` execution command, progress protocol, queues,
  cancellation, remote transport, daemon, server, or collaborative editor.
- Undo/redo UX, branching, merge, multi-user synchronization, or a replacement
  version-control system. Retained append-only revisions may support explicit
  selection of an older revision, but no history rewrite.
- Broad catalog curation, new component contracts/bindings, automatic
  compatibility promotion, asset ingestion, sampling, or packaging.
- Device connection, USB, upload, SD-card write, flash, firmware change,
  real-time measurement, or listening.
- Mutation of upstream checkouts or accepted Tasks 001-011C bytes.
- Staging, commit, tagging, publication, or push without separate user
  authorization.

## Deliverables

- This task contract, updated to complete only after every acceptance gate
  passes.
- Normative project/workspace and persistence documentation.
- Closed project and supporting transaction/write-plan schemas.
- One positive project fixture plus focused negative and failure-injection
  fixtures.
- Additive shared operation schema versions and in-process project service.
- Product-CLI parsing, rendering, help, and completion for the accepted new
  commands.
- A read-only project/workspace validator and focused Task 012A test suite.
- Necessary updates to active architecture, schema, operation, CLI, package,
  and roadmap documentation.
- A completion report naming exact schemas, commands, fixtures, hashes,
  atomicity results, preservation evidence, test counts, and remaining Task
  013 and deferred UI gaps.

## Acceptance tests

Task 012A is accepted only if all of the following pass:

1. Every pre-existing test and accepted validator passes before counting Task
   012A tests; accepted canonical operation and CLI bytes remain unchanged.
2. A project created in two fresh roots from identical explicit inputs has
   identical governed bytes and semantic hashes.
3. Copying a project/workspace to another absolute path does not change its
   governed identity or validation result.
4. The manifest pins the exact immutable base record set and every
   project-owned graph/instrument/build member. Missing, stale, ambiguous,
   colliding, hash-mismatched, or extra governed members fail closed; the union
   never comes from ambient directory enumeration.
5. Project and graph successor revisions retain exact parents. Neither an
   accepted graph nor accepted project revision is overwritten in place.
6. The persistent transaction reuses the existing ordered graph edits and
   complete semantic validation. A failed edit emits no accepted new revision.
7. Proposal-only `graph.transact` retains its accepted `not-written` result and
   exact current behavior.
8. A successful explicit write produces exactly one accepted project revision
   transition and reloads to the same graph/project bytes returned by the
   shared operation.
9. Stale base graph hash, stale project revision, concurrent writer, or changed
   expected old bytes rejects before the acceptance boundary.
10. Failure injection before, during, and after each mutation step leaves
    either the exact prior project or the exact successor project loadable,
    never a partially accepted mix.
11. Temporary, lock, recovery, cache, and orphan state is excluded from
    canonical project identity. Ambiguous recovery fails with stable
    diagnostics rather than guessing.
12. Relative locator and symlink/path traversal tests cannot escape the
    workspace or smuggle an absolute checkout path into durable records.
13. The direct in-process API, canonical process adapter, ergonomic CLI JSON,
    and reload path agree on exact operation-result bytes where their envelopes
    are specified to match.
14. Human output, JSON output, help, completion, stdout/stderr separation, and
    exit codes are deterministic across working directory, locale,
    `PYTHONHASHSEED`, and record enumeration order.
15. The CLI invokes the shared project/transaction service exactly once and
    contains no independent graph mutation, hashing, locking, write, or
    recovery semantics.
16. No presentation/UI schema, build execution, compiler stage, backend
    invocation, artifact/evidence promotion, device action, or accepted-history
    mutation occurs.
17. `git diff --check` and the complete local ordinary-CI-equivalent gate pass.

## Decisions Task 012A may make

- Exact project/workspace schema names, opaque IDs, initial revisions, file
  layout, portable locator vocabulary, and canonical filenames.
- The smallest acyclic split between project manifest, transaction write plan,
  commit marker, and local recovery metadata.
- The local lock and atomic/recoverable publication protocol, provided its
  acceptance boundary and failure behavior are fully tested.
- Exact additive operation names/envelopes and CLI spelling within the required
  conceptual surface.
- Whether explicit old-revision selection is exposed now, provided it does not
  rewrite history or add undo/redo semantics.
- Stable project/persistence diagnostic codes and focused fixture layout.

## Decisions Task 012A must not make

- Canvas, drawer, presentation, GUI, AI-client, compiler, backend, runtime, or
  device semantics.
- A rule that makes the project or filesystem own graph, instrument, build,
  record-set, catalog, contract, binding, target, backend, artifact, or evidence
  identity.
- Implicit `latest`, ambient record scanning, path-derived stable IDs, display
  names as identity, silent migration, hidden graph rewrites, or destructive
  accepted-record updates.
- CLI-only persistence semantics or a second graph transaction language.
- Automatic build, compatibility promotion, hardware access, upload, flash,
  commit, or push as a side effect of save.
- Any change to an accepted Tasks 001-011C schema, record, fixture, artifact,
  evidence record, operation result, or CLI golden merely to make this task
  pass.

## Stop conditions

Stop and report rather than broaden or weaken the task if project and record-set
ownership cannot remain distinct; if exact graph/project parentage would become
cyclic; if the persistence protocol cannot prove prior-or-successor recovery;
if accepted operation bytes must change instead of using an additive version;
if portable identity requires an absolute path; if the CLI would need to own
semantics unavailable to other clients; or if completion requires UI, compiler,
backend, device, staging, commit, or push work.

## Completion report requirements

On completion, record every delivered file; exact schema and fixture IDs,
revisions, and hashes; the durable/local file classification; operation and CLI
surface; write acceptance boundary; lock and recovery model; every failure
injection result; portability and determinism evidence; pre-existing and final
test counts; accepted-byte preservation; scope confirmation; and the exact
remaining Task 013, Task 014, and deferred UI proof gaps.

## Completion report

Task 012A completed from clean baseline
`056ca1e09e3a09f8cf10c6e7e330c5cca4aa1981`. It adds one portable project
manifest, one accepted-head marker, a deterministic write plan, local lock and
recovery records, additive operation v3 envelopes, a client-neutral
`ProjectService`, and explicit product commands. The existing ordered
`graph.transact` edit language and semantic validator remain the sole graph
mutation boundary.

### Delivered files

The delivered file set is exactly:

- root and normative documentation: `README.md`,
  `docs/PROJECT_WORKSPACE_CONTRACTS.md`, `docs/PROJECT_CONTEXT.md`,
  `docs/ARCHITECTURE.md`, `docs/SCHEMA_STRATEGY.md`,
  `docs/OPERATION_CONTRACTS.md`, `docs/COMPILER_STRATEGY.md`,
  `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`, `docs/ROADMAP.md`, and this task;
- package surface and implementation: `packages/README.md`,
  `packages/schuss_core/__init__.py`, `packages/schuss_core/cli.py`,
  `packages/schuss_core/control_plane.py`,
  `packages/schuss_core/product_cli.py`,
  `packages/schuss_core/project_cli.py`, and
  `packages/schuss_core/project_service.py`;
- schema surface: `schemas/README.md`, `schemas/project-v0.schema.json`,
  `schemas/workspace-head-v0.schema.json`,
  `schemas/project-write-plan-v0.schema.json`,
  `schemas/workspace-lock-v0.schema.json`,
  `schemas/workspace-recovery-v0.schema.json`,
  `schemas/operation-request-v3.schema.json`, and
  `schemas/operation-result-v3.schema.json`;
- retained positive fixture:
  `fixtures/task012a/minimal-project/schuss-project.json` and
  `fixtures/task012a/minimal-project/project/revisions/schuss-project-000001-r000001.json`;
  and
- retained validation: `tools/contracts/README.md`,
  `tools/contracts/validate_task012a.py`,
  `tools/contracts/tests/test_task012a_project.py`, and fixture files
  `task012a-graph-edits.json`, `task012a-project-negative-fixtures.json`, and
  `task012a-successor-golden-hashes.json` under
  `tools/contracts/tests/fixtures/`.

### Exact schemas and retained fixture

The seven schema IDs and their raw-file SHA-256 values are:

| Schema ID | SHA-256 |
| --- | --- |
| `project-v0.schema.json` | `3d59925cfbf65adc66376053f034abdb05c47849776f4a4b17de1df69cc4670d` |
| `workspace-head-v0.schema.json` | `dedf5226819c55dc0159c3860c592459f1501d914f7862b49f4beb3eee8d4ee2` |
| `project-write-plan-v0.schema.json` | `5de48d139c478325ab5f11c730fb0d70396823dd93c76fb55d6ce66748825cd5` |
| `workspace-lock-v0.schema.json` | `470375d465f45667e841b7e0a00c168c779671b60c9a9bf59c4334dbfe573b0d` |
| `workspace-recovery-v0.schema.json` | `21f5c22eeb4e6c62560b5382ab2c0e28c7cc06ce3881d2ab711dfa23f3275c9d` |
| `operation-request-v3.schema.json` | `5405ad385574706b0c82989e1cbc2e02ef24a443836ec04030eb519075e98a30` |
| `operation-result-v3.schema.json` | `f1f0c90c95846a4b2a3836fa981000d2f006b1911354afcf0b13f76a5c681802` |

The retained positive manifest is project `schuss-project-000001` revision 1,
semantic hash
`sha256:61ebe4b3bb3ddea3a710449205f5aa5fc7bea77ff6462a2b48f2c1b1919e6f47`.
Its parent is omitted. It pins exact Task 011C record set
`schuss-record-set-000006` revision 1 at
`sha256:fcf8f43d4139a16796b17bf2bdb95e5cd03ac279c60c55f8218349ef8a7cc842`,
graph `schuss-graph-000002` revision 1 at
`sha256:ea98b4cbf1ecb58d70338e5aaaef02385a6ede707b9b78bbc90fac09d53c7460`,
instrument `schuss-instrument-000002` revision 1 at
`sha256:d20e0f108397987a4b102fab35afc8fb00a42acfa33d48522226de2c343e7adb`,
and build request `schuss-build-request-000002` revision 2 at
`sha256:dfc54339dc8ce4a243babad40de659437d67aa05c4c2f61be04e39741e4b0351`.
The 1,065-byte manifest has raw SHA-256
`ff8d4aba68e2517cd8507416e655854109f9d94063674d07d21e45650a74d556`;
the revision-1 head has raw SHA-256
`502782a23485f88f6fd330e41ce1ef07c5ee6edd180eb860eab1e40e5ca5d5d3`.

The retained successor golden names graph `000002` revision 2 at semantic hash
`sha256:4448a27e4e6913de9ef7a29453e1cd65950f533c4b9001fd984f95095d2ca0a0`,
project `000001` revision 2 at semantic hash
`sha256:1468133fea4b40a9086396ec5a3ed6a966d31b69bd824e676f2cfc84811eeef1`,
and write plan hash
`sha256:3701f3da7f7d6649adfa0abd8a0c96d8d2a5f24745adc19826ec96e9a5879a88`.
Its governed raw bytes are graph revision 2: 6,109 bytes,
`58c92b67a818248930ed627c1893940fcef1dc883b7ad6e5d2e7fdb591083cbc`;
project revision 2: 1,757 bytes,
`e0667e3027c6e5c81604e83b818f2256381e5cdb2990ef0a841ae914e76ab9be`;
and successor head: 436 bytes,
`ee564e58a08ccf411f2b67d29f74ae34e1af6af9323c81e6d71a8341fe52d0bc`.

### Durable state, local state, operations, and commands

Governed durable files are only `schuss-project.json`, immutable
`project/revisions/*.json`, explicitly indexed `records/dsp-graphs/*.json`,
and explicitly owned content-addressed assets. Local `.schuss/lock.json`,
`.schuss/recovery/pending.json`, `.schuss/tmp/`, and `.schuss/cache/` are
coordination or convenience state and never canonical identity.

Additive `schuss-operation-request-v3` and `schuss-operation-result-v3` expose
`project.init`, `project.inspect`, `project.validate`, and
`project.graph.commit`. Product commands are `project init`, `project inspect`,
`project validate`, `project transact ... --write`, canonical `project op`, and
static `project completion` for Bash, Zsh, and Fish. All require an explicit
workspace. Human and JSON forms derive from the same shared result. The direct
API, canonical process adapter, ergonomic CLI JSON, and reload paths produced
the expected equal canonical bytes.

### Atomicity, locking, recovery, and failure injection

Atomic replacement of `schuss-project.json` is the sole acceptance boundary.
The exact old head bytes are rechecked immediately before replacement.
Immutable graph and project successors are published before that boundary and
are not accepted by existence alone. A live writer rejects; a malformed lock
fails closed; a dead lock without recovery is removed as abandoned local
state.

Recovery compares the accepted head against the plan's exact old and new head
bytes. Exact old rolls back only plan-owned unaccepted files; exact new
verifies and retains the successor; neither produces
`PROJECT_RECOVERY_AMBIGUOUS`. Each of these injected interruption labels
recovered to one exact valid revision 1 or revision 2 project, never a mixed
state: `before:recovery.temp-create`, `during:recovery.temp-write`,
`after:recovery.publish`, `before:graph.temp-create`,
`during:graph.temp-write`, `after:graph.publish`,
`before:project.temp-create`, `during:project.temp-write`,
`after:project.publish`, `before:head.temp-create`,
`during:head.temp-write`, `before:head.publish`, `after:head.publish`,
`before:recovery.remove`, and `before:lock.remove`. Separately tampered recovery
state failed closed as ambiguous.

### Validation and preservation

Two differently named fresh roots produced identical governed bytes and
semantic hashes. Copying the fixture to a different absolute path preserved
identity and validation. Fresh-process and cross-working-directory CLI output
remained deterministic across locale, `PYTHONHASHSEED`, enumeration order, and
terminal width. Absolute, parent-traversal, and symlink locators could not
escape the workspace. Missing, extra, colliding, duplicate, stale-hash,
changed-old-head, missing-parent, malformed-lock, live-lock, and invalid exact
references all failed closed.

The pre-task baseline passed 14 inventory, 6 catalog, and 159 contract tests:
179 total. The final suite passes 14 inventory, 6 catalog, and 177 contract
tests: 197 total, including 18 focused Task 012A tests. Every retained raw,
resolved, Phase 3, semantic catalog, Task 011A, Tasks 005-007, Task 009
prerequisite/check, Task 011B, Task 011C/check, and Task 012A validator passed;
`git diff --check` passed. The accepted Task 010 CLI golden file remains exact
at SHA-256
`2373c57ed53676470eb077b79156c4f7f44b1e21c4f1f3d6bd98393e8c2fc146`,
and the accepted Task 011A CLI golden remains exact at
`f4530b7e13e1275df11fdb17a99abaf70758547db36d1025e666cb1aa8c94ed4`.
Proposal-only `graph.transact` still returns
`persistence_status: not-written`; accepted v1/v2 operation and CLI bytes,
schemas, records, fixtures, artifacts, and evidence were not rewritten.

No presentation/UI model, compiler front half, lowering, Java invocation,
generated artifact, backend execution, build execution, evidence promotion,
device connection, upload, SD-card write, flash, firmware mutation, real-time
measurement, listening, upstream-checkout mutation, stage, commit, or push
occurred.

Task 013 still must prove reusable implementation resolution, compound
elaboration, dependency/resource planning, and deterministic compiler-front-
half artifacts without lowering. Task 014 still must define and prove the
shared executable-backend boundary and product build command. The unnumbered
future UI milestone still owns the object drawer, graph canvas, presentation
overlay, and all visual interaction behavior. Task 012A makes none of those
claims.
