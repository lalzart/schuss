# Durable project/workspace and persistence contracts

Task 012A establishes the first persistent Schuss authoring boundary. A
project is one portable exact semantic manifest. A workspace is the selected
host directory used to coordinate, publish, and recover that project. The
workspace path is never project identity.

## Exact ownership and closure

`project-v0` owns only:

- opaque project ID, revision, content hash, and exact project parent;
- one exact immutable base `record-set-v0` reference plus an installation-
  relative locator;
- one closed `owned_members` overlay/index;
- the exact primary graph and included instrument/build-request references;
  and
- already-present content-addressed asset references.

It does not own or redefine record-set, graph, instrument, build, asset,
catalog, contract, binding, target, backend, artifact, or evidence identity.
The base record set remains unchanged. The project closure is the union of its
pinned base and enumerated owned members; no directory scan supplies members.
Scanning is used only after the union is known, to reject missing or extra
governed files.

Each owned member records kind, stable ID, revision, semantic hash, schema
version, normalized locator, byte hash, and exact parent. Task 012A first
created only `dsp-graph-v0` successors. Task 026 additively creates and versions
project-owned `dsp-graph-v0`, `instrument-v0`, and `build-request-v0` closures.
Task 034's additive `instrument-v1` and performance-control records are not
silently admitted to this v0 project closure. A later project-schema successor
must version that migration explicitly; existing project/build/host behavior
continues to consume `instrument-v0` only.
The semantic-record bytes remain authoritative and are not changed merely to
add filesystem policy. The project member index retains every exact revision
parent, keeping the representation acyclic:

```text
project r2 -> graph r2 -> component contracts
     |
     +------ exact project parent r1
     +------ member exact graph parent r1
```

One stable-ID/revision collision between base and overlay, two overlay members
with the same identity, a missing parent, or a stale byte/content hash fails
closed. Project successors retain every earlier owned member and cannot change
the immutable base.

## Portable workspace layout

The governed layout is:

```text
schuss-project.json
project/revisions/schuss-project-NNNNNN-rRRRRRR.json
records/dsp-graphs/schuss-graph-NNNNNN-rRRRRRR.json
records/instruments/schuss-instrument-NNNNNN-rRRRRRR.json
records/build-requests/schuss-build-request-NNNNNN-rRRRRRR.json
records/object-definitions/schuss-project-object-NNNNNN-rRRRRRR.json
assets/...                         # only exact manifest-owned assets
```

`schuss-project.json` is a `workspace-head-v0` acceptance marker. It names one
exact project revision, its canonical locator, and its raw byte hash. Project
revisions and semantic records are immutable. All locators are normalized
relative paths. Absolute paths, parent traversal, and symlink traversal fail.
Copying the governed tree to another absolute location leaves its bytes,
identity, and validation result unchanged.

Local coordination is separate and excluded from canonical identity:

```text
.schuss/lock.json
.schuss/recovery/pending.json
.schuss/tmp/*.tmp
.schuss/cache/                    # reserved local convenience state
```

The lock contains a local PID only. It is not project truth. Malformed or live
locks fail closed. A dead lock without recovery state is removable as
abandoned local coordination. Temporary files never become accepted merely by
existing.

## Write plan and acceptance boundary

`project-write-plan-v0` deterministically names:

1. the exact old and new project references;
2. the exact graph parent and successor;
3. each create/replace locator in order;
4. expected absent or exact old byte length/hash;
5. exact proposed byte length/hash; and
6. the sole acceptance mutation.

A persistent graph transaction performs:

1. exclusive lock acquisition;
2. exact accepted-project and base-graph comparison;
3. one existing `graph.transact` proposal and its complete semantic
   validation;
4. deterministic graph, project, head, and write-plan construction;
5. local recovery-plan publication;
6. immutable graph publication;
7. immutable project-revision publication; and
8. atomic replacement of `schuss-project.json`.

Step 8 is the acceptance boundary. Before it, the old head still selects the
complete prior project; new immutable files are owned unreferenced candidates.
After it, the new head selects files already present at their expected hashes.
The implementation rechecks the expected old head bytes immediately before
replacement. A changed head, stale project, stale graph, live writer, or
pre-existing immutable target rejects without acceptance.

Task 026 adds `project-write-plan-v1`, which retains the same exact project
transition and atomic head boundary while permitting any ordered set of
project-owned graph, instrument, and build-request immutable records before
the new project manifest. Recovery selects the plan schema explicitly and
never infers it from the mutation count.

The sonic-authoring successor retains write-plan v1 and additively introduces
project manifest v1 plus `object-definition` ownership. One object definition
contains its project-local family facts, exact component contract, exact
implementation binding, and either an inspectable transparent compound graph
or bounded native kernel. Those nested domain values are validated against
their own exact schemas and enter the same base-plus-project component/graph
closure; they are not a client-owned catalog or compiler database.

Project-v0 revisions remain immutable and readable inside a history whose
accepted successor is project-v1. Object acceptance appends one immutable
object member and, when placement is requested, versions the selected
project-owned graph, instrument, and build request before publishing the v1
manifest. The atomic workspace-head replacement remains the sole acceptance
boundary.

## Recovery

Recovery reads only a closed local plan and compares the current head with the
plan's exact old and new bytes:

- old head: delete only exact plan-owned unaccepted immutable files and load
  the prior project;
- new head: require every proposed file at the exact new bytes and load the
  successor project; or
- neither: report `PROJECT_RECOVERY_AMBIGUOUS` and do not guess.

Orphaned governed files without an owning recovery plan fail validation.
Failure injection covers before/during/after recovery, graph, project, and
head publication plus recovery/lock cleanup. Every tested interruption reloads
as exactly revision 1 or revision 2, never a mixed accepted state.

## Shared operation and CLI surface

Additive `schuss-operation-request-v3` and
`schuss-operation-result-v3` envelopes add:

- `project.init`;
- `project.inspect`;
- `project.validate`; and
- `project.graph.commit`.

`ProjectService` is the client-neutral in-process owner. The existing
`dispatch_operation` delegates v3 requests to that explicit service. Persistent
commit calls the existing v1 `graph.transact` once; there is no second edit
language. Existing v1/v2 requests, results, defaults, and canonical bytes are
unchanged.

The ergonomic commands are:

```text
schuss project init --project WORKSPACE --project-id ID --record-set MANIFEST --graph ID@REV ...
schuss project inspect --project WORKSPACE [--json]
schuss project validate --project WORKSPACE [--json]
schuss project transact GRAPH_ID@REV --project WORKSPACE \
  --expected-project PROJECT_ID@REV --project-content-hash HASH \
  --graph-content-hash HASH --edits FILE_OR_STDIN --write [--json]
schuss project op --project WORKSPACE --request FILE_OR_STDIN --json
schuss project completion {bash|zsh|fish}
```

Explicit project/workspace selection is mandatory. `--write` is mandatory for
the persistent command. The existing `schuss graph transact` command is
unchanged and remains proposal-only with `persistence_status: not-written`.
Task 012A completion is additive so the accepted legacy completion bytes also
remain unchanged.

Task 026 additively supplies closed request/result v8 operations:

- `project.profile.fork` allocates opaque project-owned graph, instrument, and
  request identities from one exact complete template closure;
- `project.profile.transact` applies one ordered shared graph-edit batch and
  versions the selected graph, instrument, request, and project atomically;
- `project.history.inspect` returns deterministic immutable ancestry; and
- `project.revert` creates a successor selecting one exact ancestor state and
  never deletes history.

The corresponding ergonomic commands are `project create`, `project edit`,
`project history`, and `project revert`. `build plan` and `build execute` accept
an explicit `--project` workspace and consume its exact selected request. The
Task 023 CLI golden remains retained; Task 026 records a separate successor
golden for the expanded help and project-completion surface.

## Evidence and exclusions

Task 012A proves portable structural project validation and recoverable local
persistence. Task 026 separately proves the exact reverb-free authored closure
through local ARM compile/link level 5 in two fresh roots. Neither task proves
connected-device execution, real-time/resource suitability, audible behavior,
safety, or release readiness; Task 026 uses no Java or `.axp` fallback.
It defines no presentation overlay, drawer state, canvas geometry, GUI, build
execution, compiler front half, or collaboration protocol.
