# Desktop UI boundary

Status: the consolidated Tauri desktop implements catalog/object browsing,
exact graph visualization and proposal, project-backed authoring, process-local
build jobs, explicit Ksoloti Core discovery, and a read-back-verified
volatile-RAM upload path. It also presents accepted project-local objects and
safely follows externally accepted project revisions.
The canvas is now the application home; Objects and Patches are contextual
drawers, and one remembered projects root is browsed and mutated only through
shared core operations.
Connected-hardware execution, firmware/SD mutation, packaging, and publication
remain separately gated.

## End-to-end boundary

```text
React/TypeScript presentation
        -> dispatch_desktop_operation
        -> closed Rust validation
        -> persistent local Python adapter
        -> shared schuss_core dispatcher / ProjectService / session services
        -> exact compiler/build handler or bounded Ksoloti libusb transport
        -> canonical operation result
```

The product application is `apps/schuss_desktop/`. Browser-mode development
uses a localhost Vite proxy to the same Python adapter; production has no
renderer fallback. Both paths select exact record set
`schuss-record-set-000028@1` for new-project creation. Additive v15 supplies
`workspace.projects.list` and `workspace.project.create`; the renderer passes
one explicit absolute projects root and never scans it. The desktop also
retains only the v13 `project.objects.list` and `project.object.inspect` reads;
draft creation, evaluation, preview, and acceptance remain
available only to a separately configured project-scoped MCP authoring service.
Existing workspaces continue to load the immutable base record set pinned in
their project manifest.

## Implemented capability groups

| Group | Operations | Effect |
| --- | --- | --- |
| Catalog | `application.describe`, `catalog.search`, `catalog.inspect`, `catalog.implementations.search`, `component.inspect` | read-only |
| Graph | `graph.inspect`, `graph.transact` | read-only / proposal-only |
| Project | `project.init`, `project.inspect`, `project.validate`, `project.profile.fork`, `project.profile.transact`, `project.history.inspect`, `project.revert` | explicit workspace read/write |
| Project objects | `project.objects.list`, `project.object.inspect` | read-only accepted project-local definitions |
| Projects root | `workspace.projects.list`, `workspace.project.create` | bounded direct-child validation / explicit atomic child creation |
| Build session | `build.session.start`, `build.session.inspect` | process-local output write / read-only inspection |
| Device session | `device.session.discover`, `device.session.inspect` | explicit USB identity read / read-only inspection |
| Volatile upload | `device.upload.start`, `device.upload.inspect` | confirmed volatile device write / read-only inspection |

The adapter rejects every operation outside this list, including
raw `build.execute`, flash, DFU, reset, SD, filesystem export, and arbitrary
USB operations. The application capability description may report shared
operations that require other services; description does not grant the
desktop permission to invoke them.

## Ownership

Schuss core owns catalog, component, graph, instrument, project/workspace,
compiler, build, device, and evidence meaning. The renderer may construct an
allowed request and render its canonical result. It may not read semantic JSON,
scan a workspace, choose an implicit revision, infer a component contract,
write a project file, choose a handler, access artifact bytes/path, retain a USB
handle, or invoke a general process/filesystem/USB API.

The renderer owns only presentation state: selection, canvas viewport, node
coordinates, panel state, one projects-root preference, the last exact
workspace reference, loading/error state, and the
unsaved ordered edit draft. Node movement never changes a graph hash. Save is
one shared `project.profile.transact` request that validates the ordered graph
proposal before persistence and carries exact expected references plus explicit
write intent.

The open editor checks the exact accepted project reference through
`project.inspect`, including on window focus. A clean external successor
reloads through the ordinary project/graph inspection path and selects one
identifiable added node. A dirty editor retains its complete draft and presents
the successor revision plus a guarded reload action. The renderer never reads
or watches the workspace head directly.

The application always mounts one patcher canvas. Objects and Patches switch a
compact left drawer rather than application routes; the right inspector remains
node-contextual. The object drawer defaults to the existing `contracted`
readiness projection, exposes an explicit All catalog view, and expands exact
form, readiness, provenance, and project evidence in place. One Add action
performs exact component resolution and then emits only the existing unsaved
`add-node` edit.

`workspace.projects.list` examines at most 128 direct non-hidden child
directories and returns only exact projects accepted by `ProjectService`.
Symlinks, escaping children, duplicate stable project IDs, and malformed
projects are not openable entries. `workspace.project.create` allocates a
collision-safe child path and stable project identity, forks the accepted
starter profile, applies the display name, and publishes the complete child by
atomic directory rename. Local preferences carry no semantic authority.

## Process-local performance boundary

The persistent adapter validates the selected 421-record base once. Each
project service may reuse that base only for the exact validated manifest path
and full record-set reference. It may also retain at most eight derived
base-plus-owned semantic contexts under deterministic LRU eviction, keyed by
the exact base reference and canonical project-owned records.

This does not cache workspace authority. Every operation continues to read and
validate the head, immutable project ancestry, owned record bytes and hashes,
assets, symlink constraints, temporary/recovery state, and governed membership.
The cache creates no durable file and cache-disabled operations produce the
same canonical result and project bytes. Cold process startup still performs
the full exact record-set validation.

The native shell spawns the persistent core process during application setup,
before the first project request. The window and canvas remain visible while
the existing full record-set validation completes; startup, project browsing,
project inspection, and graph inspection are rendered as distinct stages. This
prewarm changes perceived open behavior but does not claim a faster cold
semantic load or bypass validation.

Catalogued-only Mutable-derived objects remain visible in All catalog and
unresolved. Add is enabled as an interaction, but succeeds only after exact
family inspection resolves one component contract; otherwise it changes no
draft or project.

## Build and device seam

Build start snapshots the accepted project revision and exact project-owned
request. The core selects a handler only when its backend/request policy matches
uniquely, writes to a fresh temporary root, and exposes structured progress,
stages, diagnostics, evidence levels, and portable artifact facts. Output roots
and bytes remain private and expire with the process.

Device discovery performs no work before explicit intent. The core lazily opens
libusb, inspects exact USB/CPU/firmware identity, and marks compatibility against
the retained Ksoloti 1.1.0.0 boundary. Upload requires a compatible session, one
exact target executable from a successful build session, and confirmed
`explicit-volatile-ram` intent. The core derives the device binary with the
authenticated local ARM tool, stops the current patch, writes fixed patch RAM,
verifies exact read-back, and starts only when separately requested.

These are process-local workflow observations, not governed evidence records.
Build success does not imply device success, and an upload-session success does
not imply control correctness, real-time stability, safety, or audibility.

The Tauri renderer capability remains only `core:default`; no filesystem,
shell, HTTP, updater, USB, device, or hardware plug-in permission is present.
Firmware flash, DFU, reset, SD-card writes, persistent install, background
monitoring, arbitrary memory access, and automatic upload remain absent.
