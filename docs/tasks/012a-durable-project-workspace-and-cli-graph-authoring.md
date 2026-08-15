# Task 012A: Durable project/workspace and persistent CLI graph authoring

Status: proposed prompt; not started. The user authorized creation of this task
contract on 2026-08-15 but did not authorize implementation, staging, commit,
publication, push, or any device action.

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
combined with Phase 12 from deferred Task 012B's object drawer and graph
canvas.

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

- Task 012B object drawer, graph canvas, desktop/web GUI, presentation overlay,
  keyboard/mouse interaction, or visual layout.
- Task 013A compiler-front-half implementation, build planning, compound
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
  013A/012B gaps.

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
remaining Task 013A, Task 013B, and deferred Task 012B proof gaps.
