# Task 026: Complete authoring operations and CLI workflow

Status: accepted and complete. Child 026A established the reverb-free level-5
executable profile. Child 026B completed the authoring operations, immutable
history, CLI workflow, recovery proof, and two-root authored-ELF reproduction.

## Goal and why it exists

Allow every Schuss client to create an explicit empty workspace, author a
project-owned graph and instrument, persist immutable history, and build the
same exact authored closure without fabricating records or editing canonical
JSON by hand. This is the shared application-writing boundary that a later UI
must consume rather than reimplement.

## Dependencies and child sequence

Task 023 supplies the shared capability and CLI surface. Task 024 supplies the
current-Ksoloti-first catalog and provenance model. Task 025 supplies five safe
new operation semantics, two reusable routing operations, and an exact failed
reverb boundary, but no complete executable handler.

The preflight decision accepts the reverb-free seven-node route. Child 026A is
governed by `contracts/task026/executable-profile-prerequisite.md` and must
reach exact local ARM compile/link level 5 for an identity-independent semantic
profile with an included instrument. Child 026B then consumes only that
accepted seam for the authored application flow. The children are serialized
because they share compiler, record-set, and status authority.

## In scope

- Client-neutral operations and CLI routes to create an empty workspace and
  atomically fork the exact validated seven-node template into allocated
  project-owned graph, instrument, and build-request identities. A blank or
  partially valid DSP graph is never persisted.
- Exact catalog inspection and contract selection followed by add/remove node,
  connect/disconnect, parameter, attribute, and public-mapping edits through
  the shared graph transaction service.
- Creation and versioning of project-owned instrument and build-request
  records whose exact references are included in the durable project closure.
- Immutable revision history, explicit history inspection, and an explicit
  revert operation that creates a new head revision suitable for undo/redo
  presentation.
- Atomic save, close, reopen, validation, planning, and exact build of the
  authored graph/instrument/request through shared services.
- One deterministic scripted empty-workspace-to-ELF flow using only the
  separately accepted executable profile.
- CLI help/completion, machine-operation schemas, negative diagnostics,
  portable fixtures, focused tests, adjacent regression, two fresh-root
  reproductions, and one final aggregate validation.

## Out of scope

- Resolving reverb allocation inside Task 026, changing DSP math/state/timing,
  or silently omitting a node from an accepted profile.
- General compilation of arbitrary catalog objects or graphs, ambient/latest
  discovery, automatic compatibility fallback, Java, `.axp`, or private CLI
  semantics.
- Sessions, background jobs, progress/cancellation, desktop UI implementation,
  sampling/assets, additional targets/devices, hardware actions, connected
  proof, real-time proof, audible proof, release, staging, commit, push, or
  publication.

## Inputs and deliverables

Inputs are ADR 0014; the application-spine plan; exact accepted Task 023-025
record sets and evidence; the Task 026 preflight boundary; the accepted
executable-profile prerequisite; existing project/workspace, graph transaction,
compiler-plan, and execution services; and the current product CLI contract.

Deliverables are versioned operation request/result schemas; shared dispatcher
and project-service operations; CLI routes/help/completion; exact project-owned
graph, instrument, request, and project-history fixtures; a successor record
set only where durable semantic records are required; deterministic build and
origin evidence; two fresh-root flow results; a completion report; and updated
status, roadmap, history, application plan, and governance checks.

## Required authored closure

The acceptance flow starts with no project metadata. Initialization first
creates one valid head selecting the exact immutable Task 026A template; the
next shared operation atomically forks that complete closure into project-owned
identities. This two-boundary sequence avoids weakening `dsp-graph-v0`, whose
graph must be complete and valid at every persisted revision. Every stable
identity is allocated through the shared operation, every revision has one
exact parent, and every mutation creates a new immutable revision before
atomically moving the workspace head. Revert creates a successor whose selected
state intentionally matches an earlier revision; it never deletes or rewrites
history.

The final request includes the newly authored graph and instrument by exact
reference. Planning and execution must consume that closure. Building a
historical fixture, substituting a different graph, or using an exact-ID-only
handler does not satisfy Task 026.

## Diagnostics and evidence boundary

Malformed, stale, ambiguous, unsupported, or out-of-profile edits fail closed
with stable `PROJECT_*`, `GRAPH_*`, `COMPILER_*`, or `BUILD_*` diagnostics and
no partial persistence. A failed build does not roll back valid authoring
history, but it cannot publish an artifact or advance evidence.

Schema/identity, host persistence, compiler planning, generated source, and
ARM compile/link evidence are reported separately. Local level 5 does not
imply device execution, resource/real-time suitability, audible behavior,
safety, or release readiness; levels 6-8 remain `not-run`.

## Validation cadence

Focused validation covers each new operation, atomic persistence, revision
history, CLI parsing, and failure diagnostics. Adjacent validation covers the
existing project service, graph transactions, compiler front half, build
execution, CLI v2, and application smoke after focused behavior stabilizes.
The expensive flow reproduces from two copied fresh roots only after the diff
freezes and is not repeated separately when the final aggregate already
covers identical commands. One final inventory/catalog/contract aggregate runs
after documentation and governance are coherent.

## Acceptance tests

1. The accepted contract fixes the chosen executable profile, exact parent,
   scope, inputs, deliverables, IDs, diagnostics, evidence boundary, validation
   cadence, and prohibited actions.
2. An empty explicit workspace creates one portable project and one complete
   project-owned graph without ambient discovery or hand-authored canonical
   JSON; no blank or invalid graph revision is ever persisted.
3. Shared operations select one exact reviewed contract and add/remove nodes,
   connect/disconnect ports, and edit parameters/attributes atomically.
4. Every operation has one versioned closed request/result schema and the CLI,
   API, and future UI boundary use the same dispatcher behavior.
5. The flow creates exact project-owned graph, instrument, and build-request
   identities and includes all three in the durable project closure.
6. Save, close, and reopen reproduce byte-identical current state from the
   workspace head and fail closed on stale or corrupt heads.
7. History inspection returns deterministic immutable ancestry and revert
   creates a new revision without deleting or mutating prior revisions.
8. The exact authored topology/profile is validated independently of graph ID;
   any topology, contract, mapping, parameter, target, or backend drift fails
   before lowering.
9. Planning selects only exact eligible bindings for the authored graph and
   preserves deterministic resolution/origin traces.
10. Build execution invokes only the accepted profile handler and produces the
    deterministic authored ELF; no historical fixture is substituted.
11. Interrupted or failed writes leave the prior head valid, and failed plan
    or build operations create no partial semantic record or artifact claim.
12. CLI help, completion, human output, machine output, and exit codes expose
    the complete authoring workflow without breaking retained CLI v2 goldens.
13. Mutated IDs, revisions, hashes, parents, history edges, profile shape, or
    handler registration fail closed with stable diagnostics and no output.
14. Two fresh roots reproduce exact project history, plan, generated source,
    command vector, ELF, and evidence bytes with Java, `.axp`, device,
    real-time, audible, and publication actions false.
15. Focused and adjacent suites, generated freshness, governance, diff review,
    and one final aggregate suite pass before Task 026 is marked complete.

## Decisions Task 026 may make

- Operation/schema names and versions, project-owned stable-ID allocation,
  immutable revision/revert representation, atomic head-update mechanics,
  CLI grammar within the accepted Task 023 surface, and deterministic fixture
  layout.
- The smallest shared-service refactor needed for all clients to use identical
  authoring operations.

## Decisions Task 026 must not make

- The reverb allocation/ownership resolution or a different executable
  profile from the one explicitly authorized at activation.
- DSP arithmetic, state, schedule, component contracts, backend semantics,
  target/device/instrument layer collapse, or private UI/CLI semantic rules.
- General compiler support, connected-device/resource/real-time/audible proof,
  release readiness, staging, commit, push, publication, upload, flash, reset,
  or SD-card action.

## Completion state

The activation gate was closed by the accepted preflight decision. 026A passed
its validator, focused suite, adjacent suite, and two-root level-5
reproduction. 026B then passed its focused suite, interrupted-write recovery,
project-based planning, and two-root empty-workspace-to-authored-ELF flow.
Exact completion authority is `schuss-record-set-000019@1` and
`evidence/task026-completion-v1/`. Reverb remains unsupported and evidence
levels 6-8 remain `not-run`.
