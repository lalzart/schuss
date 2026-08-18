# Unnumbered UI implementation: desktop build and device workflow

Status: accepted by explicit user authorization and active locally on
2026-08-18; implementation and local acceptance are complete. User acceptance
remains separate. Git publication and connected-hardware execution remain
separate.

This is the fourth bounded implementation in the unnumbered desktop UI lane.
It adds shared core operations for local build jobs and explicitly initiated
Ksoloti Core device sessions without moving compiler, artifact, or USB
authority into the renderer.

## Goal and why it exists

Let a desktop user build the accepted project, understand structured progress
and diagnostics, discover an exact compatible Ksoloti Core, and explicitly
upload the exact successful artifact to volatile patch RAM. The workflow must
remain small enough for the current product while establishing clean core-owned
seams for later cancellation, device profiles, recovery, and additional compute
targets.

## In scope

- Add versioned, client-neutral operations to start and inspect one process-local
  build session.
- Select a build handler only when the accepted build request and registered
  handler match uniquely and exactly; execute through the existing compiler
  front half and build executor.
- Retain build outputs only inside a core-owned temporary session root and
  expose portable artifact facts, progress, stages, evidence levels, and
  diagnostics rather than host paths.
- Add an injectable device transport boundary plus a lazy libusb Ksoloti
  transport for explicit discovery, exact identity/firmware inspection, and
  compatibility preflight.
- Add process-local upload sessions that derive the device binary from one exact
  successful target executable, write only volatile patch RAM, verify by exact
  read-back, and optionally start the patch after verification.
- Surface concise build/device actions, state, progress, and recovery guidance
  in the existing desktop patch editor.
- Test all device behavior with deterministic fakes. Real USB discovery or
  upload is not part of local acceptance for this implementation.

## Out of scope

- Firmware update, DFU, flash, reset, SD-card writes, persistent startup patch,
  filesystem export, raw memory tools, MIDI/audio streaming, telemetry, or
  background device probing.
- Automatic upload after build, automatic device selection, upload without an
  explicit current-session intent, or accepting a build/path supplied by the
  renderer.
- A daemon, database, general worker pool, durable job queue, cloud service,
  cross-process recovery, multi-device orchestration, or generalized USB
  framework.
- Compiler/frontend/backend redesign, catalog expansion, semantic promotion,
  new device profiles, real-time/resource measurements, audible claims, or
  packaging/signing.
- Mutation of project records by build/device work, mutation of upstream
  Ksoloti checkouts, connected hardware action during tests, or Git staging,
  commit, push, and publication.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0014 and 0015,
`docs/ARCHITECTURE.md`, `docs/PROJECT_WORKSPACE_CONTRACTS.md`,
`docs/OPERATION_CONTRACTS.md`, `docs/DESKTOP_UI_BOUNDARY.md`, the completed
desktop authoring slices, exact record set `schuss-record-set-000024@1`, the
existing `build.resolve`, `build.plan`, and `build.execute` operations, the
exact registered execution handlers, the Ksoloti Core device profile, and the
upstream Ksoloti bulk protocol inspected read only.

Deliverables are:

1. this accepted implementation contract;
2. an additive operation request/result schema and exact parent-preserving
   desktop record-set successor;
3. a core-owned process-local build-session service;
4. a core-owned Ksoloti device transport and device/upload-session service;
5. persistent Python and Rust desktop bridge allowlist updates;
6. compact build/device UI states inside the existing patch editor;
7. deterministic fake build/device tests and updated boundary documentation;
   and
8. focused, adjacent, diff, generated-artifact, and final aggregate evidence.

## Session and safety rules

1. Session identifiers are process-local opaque handles, not semantic stable
   IDs and not durable project records.
2. A build session snapshots one accepted project revision and one exact build
   request. A later project edit does not retarget the running or completed job.
3. Handler selection succeeds only for one unique registered descriptor whose
   backend and supported request/profile match the exact accepted request.
4. The renderer never receives an output root, artifact filesystem locator,
   executable bytes, USB handle, memory address, or arbitrary command surface.
5. Discovery happens only after explicit user intent. Opening a device session
   requires exact vendor/product identity plus firmware and CPU identity reads.
6. Compatibility is a distinct preflight result. Discovery never implies
   compatibility, upload success, connected-device evidence, real-time safety,
   or audibility.
7. Upload accepts only the target executable retained by one successful build
   session, derives a raw binary with the authenticated local tool, writes the
   fixed Ksoloti volatile patch address, and verifies byte-for-byte read-back.
8. Starting the patch is separately represented in the upload intent and is
   attempted only after read-back verification. No upload is automatic.
9. Device and build failures retain structured diagnostics and a retry path;
   they never mutate the accepted project or claim a higher evidence level.
10. Session state is bounded and disappears when the desktop core process exits.

## Validation cadence

- Focused: operation schema/generator checks; exact handler selection; build
  session state/progress/failure tests; fake discovery/identity/compatibility;
  fake upload chunking/read-back/start/failure tests; bridge allowlist/version
  tests; renderer request/state/accessibility tests; frontend build; Rust tests.
- Adjacent regression: v1-v11 operation compatibility, Task 014 build execution,
  Task 016/026 handler registration and project-owned build selection, desktop
  authoring persistence/cache tests, and governance/structure validation.
- Expensive reproduction: one authenticated local ARM build may be run after
  implementation freeze if its prerequisites remain exact. No connected-board,
  Java, real-time, or audible reproduction is authorized. The final aggregate
  already covers broad contract discovery and is not repeated during iteration.
- Aggregate: run the complete inventory/catalog/contracts discovery once after
  the diff, generated files, negative cases, and acceptance matrix are frozen.

## Acceptance tests

1. Starting a build from the desktop snapshots the exact accepted project and
   uniquely selected handler, returns promptly, and exposes monotonic structured
   progress through inspection until one terminal state.
2. Missing, ambiguous, mismatched, or unsupported build requests/handlers fail
   closed without invoking a backend or publishing an artifact.
3. Successful build inspection exposes artifact kind/hash/size, stage outcomes,
   diagnostics, and existing evidence levels but no host path or artifact bytes.
4. Build output is written only to a fresh core-owned temporary root, is bounded
   to the owning process, and mutates no authoritative project record.
5. Device discovery performs no work before explicit intent and returns exact
   vendor/product, transport locator, serial/CPU identity, firmware facts, and
   compatibility status without opening a renderer USB capability.
6. Unsupported product, incomplete identity, incompatible firmware/profile,
   missing build, non-success build, wrong artifact hash, or stale session IDs
   reject upload before a write.
7. A fake successful upload proves exact fixed-address begin/chunk/end order,
   byte-for-byte read-back, optional start only after verification, and terminal
   progress visible through inspection.
8. Fake write, acknowledgement, verification, disconnect, and start failures
   produce stable diagnostics, do not report success, and offer rediscovery or
   retry guidance without project mutation.
9. The desktop UI disables build for unsaved edits, never uploads automatically,
   labels volatile upload explicitly, is usable without color, and keeps graph
   authoring responsive while polling a job.
10. Python and Rust bridges expose only the six new exact operations and retain
    rejection of legacy raw `build.execute`, shell, filesystem, network, reset,
    flash, DFU, and arbitrary USB requests.
11. Existing v1-v11 operations, project atomicity/history/cache behavior, exact
    record-set ancestry, and current catalog/graph presentation remain intact.
12. Focused and adjacent checks, `git diff --check`, generated-artifact freshness,
    and the final aggregate complete with inherited historical failures reported
    separately.

## Decisions this task may make

- Private process-local session representation, bounded retention count,
  synchronization primitive, polling interval, and compact UI placement.
- Exact additive operation names and payload/result shapes within this task's
  six-operation surface.
- A minimal injectable transport protocol and fail-closed libusb adapter for the
  already accepted Ksoloti Core target.
- Chunk size, timeouts, retry-free acknowledgement handling, and concise recovery
  copy when they match the inspected protocol and remain private implementation
  details.

## Decisions this task must not make

- New semantic device identity, profile compatibility meaning beyond the
  accepted Ksoloti target, compiler/backend fallback, automatic hardware
  action, durable job persistence, or generalized device management.
- Permission to upload to a real board, flash, reset, write SD, mutate an
  upstream checkout, stage, commit, push, or publish.
- Promotion of structural or host build evidence to connected-device,
  real-time/resource, stable-runtime, or audible evidence.

## Local implementation evidence

- The focused build/device module passes 11/11 tests. It covers
  exact handler selection, bounded asynchronous build state, portable artifact
  facts, explicit discovery, incompatible firmware, cross-project session
  rejection, write/acknowledgement/disconnect/read-back/start failures, lazy USB
  loading, upload-time handshake and identity/firmware revalidation, rejection
  of a second active upload to one device, and the concrete stop/begin/
  32-KB-chunk/close/read-back/start protocol order with deterministic fakes.
- The adjacent Python run covered 66 tests across desktop bridging, authoring,
  structure, governance, Task 014 execution, Task 016 direct lowering, Task 023
  capabilities, and Task 026 authoring. Its only failure was a stale expected
  desktop-operation count; after correction the four structure tests pass.
- Renderer tests pass 12/12, the TypeScript/Vite production build succeeds,
  and the Rust bridge passes 3/3 tests. Generated v12/v5 files are fresh; the
  desktop structure and backbone-governance validators both report `valid`;
  `git diff --check` passes.
- A live Vite/Chrome smoke created a disposable seven-node project, rendered
  the editor and build/device drawer without an error overlay or page-console
  error, and completed one local ARM build. The UI reported `success` and a
  69-KB target executable. The disposable workspace and screenshots were moved
  to Trash after inspection.
- The one final aggregate passed inventory 14/14 and catalog 6/6. Contracts
  ran 411 tests in 974.684 seconds and retained exactly three pre-existing
  historical failures: the two audited Task 011A/Task 023 golden assertions
  and the Task 027 generated-output freshness assertion. No desktop,
  build/device, project, governance, or current Task 030 test failed.
- No USB enumeration, board connection, upload, patch start, reset, flash,
  DFU, SD-card write, persistent install, Git staging, commit, or push occurred.

## Completion boundary

Completion proves a client-neutral, process-local workflow from accepted project
to structured local build and from an explicit fake/available device session to
verified volatile upload. It does not prove a real board was connected or
changed, that a patch runs stably, that controls work, or that output is audible.
