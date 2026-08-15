# Task 014: Shared build execution and product CLI

Status: complete on 2026-08-16; accepted locally through evidence level 5.

Work in the Schuss repository. Before implementation, read `AGENTS.md`,
`docs/PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/COMPILER_STRATEGY.md`, `docs/COMPILER_FRONT_HALF.md`,
`docs/TARGET_BACKEND_BUILD_CONTRACTS.md`, `docs/OPERATION_CONTRACTS.md`, ADRs
0005-0010, the completed Task 011C and Task 013 contracts, and this complete
task. Work only on Task 014.

## Goal and why it exists

Add one client-neutral execution boundary after the accepted Task 013 plan and
expose it through a deterministic product CLI. The boundary must select one
exact registered handler, consume one successful exact compiler plan, publish
one fresh output root atomically, and report portable artifact facts without
making the CLI, project service, or legacy bridge authoritative compiler
layers.

This task exists because Task 013 can plan but deliberately cannot execute.
Task 011C can execute only its exact Gills slice through a task-specific proof
driver. Task 014 turns that retained handler into the first conforming adapter
behind a reusable boundary while keeping its exact limitations visible.

## Dependencies and accepted inputs

- All accepted Tasks 001-013 schemas, records, operations, CLI bytes, project
  semantics, artifacts, evidence, and completion reports are immutable inputs.
- `plan_build(...)` remains the only common front-half planner and must succeed
  through stage 6 before a handler can run.
- Task 011C's exact build request revision 2, selected eight-binding closure,
  pinned local execution environment, and handler validation remain the only
  executable production slice accepted by this task.
- Existing evidence levels remain separate. Re-executing an accepted local
  path does not create device, real-time, or audible evidence.

## In scope

- A backend-neutral handler descriptor, exact handler registry, execution
  request, cancellation token, progress-event callback, and one shared
  `execute_build(...)` API.
- Fail-closed exact handler selection by stable ID, revision, content hash,
  backend reference, and supported build-request reference.
- Automatic use of the Task 013 plan; unresolved, invalid, ambiguous,
  unsupported, or budget-failed plans prevent handler invocation.
- A conforming transitional adapter for the exact Task 011C legacy handler.
  Ksoloti/Java knowledge remains in the adapter boundary and does not enter
  compiler-front-half or semantic modules.
- Additive `build.execute` operation envelopes and shared dispatcher support.
  The dispatcher accepts an injected execution service; an absent service
  returns a deterministic unavailable result and performs no effect.
- Product commands `schuss build plan` and `schuss build execute`. Execution
  requires an exact build-request locator, exact record set, explicit fresh
  output root, and explicit `--execute` intent.
- Deterministic structured and human results, static completion updates, stable
  exit codes, and containment of adapter/tool failures.
- Output-root staging followed by one atomic rename only after success.
  Failures and cancellation publish no final root. No existing path is
  overwritten.
- Portable artifact identities, stage outcomes, handler identity, plan hash,
  and evidence-level status in the result. Host paths and timestamps are
  excluded from canonical results.
- Deterministic progress events at shared boundary transitions. Cancellation
  is honored before planning, before handler dispatch, and before publication;
  the exact transitional handler is not claimed to support mid-subprocess
  preemption.
- An explicit disabled-cache policy. Task 014 defines cache keys and reports a
  miss but does not reuse outputs until a later task proves safe cache
  materialization.

## Out of scope

- New lowering semantics, normalized DSP IR, direct C++ generation, scheduling,
  optimization, or runtime ABI work; those begin in Task 015.
- Generalizing the Task 011C handler beyond its exact graph, request, target,
  backend, bindings, or pinned local environment.
- New semantic records merely to make execution succeed, catalog expansion,
  additional graphs/instruments, new targets/devices, or compatibility
  promotion.
- Persistent build-result/evidence promotion into a record set or project,
  remote workers, daemon/job queues, resumable builds, or cache hits.
- Destructive output replacement, ambient project/record discovery, implicit
  handler fallback, network access, USB, SD card, upload, flash, connected
  execution, real-time measurement, or audible validation.
- UI or AI/MCP clients.
- Staging, commit, publication, tagging, or push without separate user
  authorization.

## Inputs and deliverables

Inputs are one exact build-request reference, one exact validated record or
project closure, an exact handler reference, an explicit fresh local output
root supplied by the host adapter, and explicit execution intent.

Deliverables are this contract; closed execution/operation schemas; the shared
execution module; the exact Task 011C adapter; additive dispatcher and product
CLI support; one parent-preserving Task 014 record set; focused positive,
negative, determinism, cancellation, preservation, and CLI tests; a read-only
validator; normative documentation; and a completion report.

## Acceptance tests

1. Every pre-existing validator and test passes; accepted operation and CLI
   bytes remain unchanged where their commands are unchanged.
2. `execute_build(...)` invokes `plan_build(...)` exactly once and no handler
   unless stages 1-6 all succeed.
3. Exact Task 011C request revision 2 resolves the sole registered handler;
   stale, missing, duplicate, wrong-backend, wrong-request, and ambiguous
   registry entries fail before an output root exists.
4. Direct shared API, machine operation, and product CLI produce the same
   portable result semantics for the same execution.
5. `schuss build plan` exposes the accepted Task 013 operation without
   executing a handler.
6. `schuss build execute` rejects absent `--execute`, absent/occupied output
   roots, malformed locators, invalid record sets, and unavailable services
   with stable diagnostics and exit codes.
7. A successful conforming Task 011C adapter run reaches the same deterministic
   artifact hashes and local evidence levels 1-5 as the retained handler.
8. Two fresh roots produce identical canonical results, artifact hashes,
   command vectors, bridge results, and resource facts; canonical output
   contains neither host root nor current working directory.
9. Injected failures at planning, registry, lowering, generation, compile/link,
   cancellation, and publication leave no final output root and never promote
   a record or evidence claim.
10. Progress events have a fixed ordered vocabulary and portable subjects.
    Cancellation is deterministic at each promised shared boundary.
11. Output publication is absent-to-present and atomic. Existing roots and
    symlink targets are rejected; no overwrite or recursive deletion occurs.
12. Cache identity binds the exact plan, handler, and policy, but cache status
    is always `disabled`/`miss` and no cached artifact is read.
13. Compiler-front-half and semantic modules import no handler, CLI, Java,
    bridge, filesystem-output, or device implementation.
14. No device, real-time, or audible evidence is claimed. No network, upload,
    flash, stage, commit, external publication, or push occurs.
15. `git diff --check` and the complete ordinary-CI-equivalent gate pass.

## Decisions Task 014 may make

- Exact execution/handler schema names, IDs, result shape, registry API,
  portable progress vocabulary, cancellation boundary, cache-key format, and
  output staging layout.
- Additive operation version and product build-command grammar consistent with
  the accepted CLI.
- The adapter module layout needed to isolate the exact Task 011C handler.

## Decisions Task 014 must not make

- New compiler, graph, component, target, backend, compatibility, or evidence
  truth.
- Implicit handler selection, first-match fallback, execution after a failed
  plan, output overwrite, host-path serialization, or cache reuse.
- Direct-frontend semantics, broader legacy support, persistent promotion,
  hardware behavior, or UI design.
- Any mutation of accepted history or action prohibited by workspace controls.

## Stop conditions

Stop and report rather than broaden the task if the Task 013 plan cannot feed
the handler boundary without competing resolution; if the retained Task 011C
handler must be weakened or generalized; if atomic publication requires
overwriting an existing path; if exact handler identity cannot be portable; or
if completion requires Task 015 semantics, network, hardware, UI, staging,
commit, or push.

## Completion report requirements

Record every delivered file; schema/operation/handler IDs and hashes; exact API
and CLI grammar; plan and registry gates; progress/cancellation/cache policy;
artifact equality; negative diagnostics; test/validator counts; evidence levels
reached and not reached; scope confirmation; and the remaining Task 015-017,
device, real-time, audible, and UI gaps.

## Completion report

Task 014 is complete within its declared shared-execution boundary. The public
API is `ExecutionService.from_values(...)` plus `execute_build(...)`, with
`HandlerRegistration`, `CancellationToken`, and exact `handler_reference(...)`
support. It calls the accepted front half once, rejects every non-successful
plan, resolves exactly one handler, stages into a deterministic private sibling
root, and atomically renames only a successful output. Cache policy is
explicitly `disabled`/`miss`; shared cancellation is honored before planning,
handler dispatch, and publication.

The additive protocol is `build.execute` in operation request/result v5.
Product commands are `schuss build plan REQUEST@REVISION` and
`schuss build execute REQUEST@REVISION --output-root DIRECTORY --execute`,
with exact handler `schuss-build-handler-000001@1` selected by default. The
separate `schuss build completion` surface exposes the new grammar while all
accepted Task 010 completion and unchanged help bytes remain unchanged.

Record set `schuss-record-set-000008` revision 1 has content hash
`sha256:860810363fc21b54b78197e2dfed7d8541408bd276fad1e4ed54a11e55084643`
and file-byte SHA-256
`7ae63c6067180edad4ef5116eb12f34cb87ec8310b96dd233c1d6d517a0427b2`.
It adds only four schemas to the complete Task 013 parent:

| Schema | File-byte SHA-256 |
| --- | --- |
| `build-execution-result-v0` | `61388d7a7bd82ceb4a874340da4fea26146aece542ab731c835477a05eb7bf1b` |
| `build-handler-descriptor-v0` | `69982edb02f4e87fac3132f57b2925f31bc8b1897d6692198ff00073a717607c` |
| `operation-request-v5` | `2d4b4c53fbfbf9260e59e9efeecbf6eb58a7aa2d7fe1f90ec21852610c517080` |
| `operation-result-v5` | `3a3b798fd73c732767c46921844e1940b52e8dfa56ced5bf38ac0625a9bbc055` |

The exact transitional descriptor has content hash
`sha256:31f74bb32eb8203262fd5867545f3ee9be8b75cad2fbcce3fb4434801293e360`
and supports only build request `schuss-build-request-000002@2` through backend
`schuss-backend-000001@3`. Ksoloti Java/toolchain paths and Task 011C handler
knowledge remain in `legacy/ksoloti-bridge/task011c_adapter.py`; neither the
compiler front half nor shared execution module imports that adapter.

Two fresh product executions produced byte-identical 4,900-byte canonical
results with SHA-256
`7a983e31a8e0572908a4ffe73b4b54f3346ebdd44f758d4904b1e4cab3725f90`.
They reproduced seven retained artifact identities: resolution plan
`b9cb83cf...`, boundary `.axp` `84f87501...`, source map `8992679f...`,
generated C++ `7877897b...`, ARM object `c059b2ee...`, ELF `d04cc20d...`, and
link map `30357b88...`. Full byte lengths and hashes are retained in
`evidence/task014-completion-v1/validation-summary.json`.

Fourteen focused tests pass. The complete gate passes 215 contract tests, 14
inventory tests, and 6 catalog tests, for 235 tests total. Negative coverage
includes absent intent, cancellation, unresolved plans, missing/duplicate and
wrong-backend handlers, existing/symlink output roots, handler failure cleanup,
operation service absence, malformed product use, and fresh-root equality.
`validate_task014.py`, the record-set generator check, schema annotation checks,
`git diff --check`, and preserved historical help/completion tests pass.

Evidence levels 1-5 passed for the exact local transitional path. Levels 6-8
remain `not-run`: no connected device, real-time measurement, or audible
procedure occurred. No semantic/evidence record was promoted, no cache output
was reused, and no network, upload, flash, stage, commit, external publication,
or push occurred. Task 015 must define normalized DSP representation and a minimal
direct frontend; Task 016 must expand that frontend to the complete Task 011C
graph; Task 017 must expand the curated core and richer headless instruments.
