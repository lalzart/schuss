# Desktop UI boundary

Status: the consolidated Tauri desktop implements catalog/object browsing,
exact graph visualization and proposal, project-backed authoring, process-local
build jobs, explicit Ksoloti Core discovery, and a read-back-verified
volatile-RAM upload path.
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
`schuss-record-set-000026@1` for new-project creation. The desktop allowlist
does not gain the v13 AI operations; selecting the additive successor only
makes a newly created project eligible for a separately configured MCP
authoring service. Existing workspaces continue to load the immutable base
record set pinned in their project manifest.

## Implemented capability groups

| Group | Operations | Effect |
| --- | --- | --- |
| Catalog | `application.describe`, `catalog.search`, `catalog.inspect`, `catalog.implementations.search`, `component.inspect` | read-only |
| Graph | `graph.inspect`, `graph.transact` | read-only / proposal-only |
| Project | `project.init`, `project.inspect`, `project.validate`, `project.profile.fork`, `project.profile.transact`, `project.history.inspect`, `project.revert` | explicit workspace read/write |
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
coordinates, panel state, recent explicit paths, loading/error state, and the
unsaved ordered edit draft. Node movement never changes a graph hash. Save is
one shared `project.profile.transact` request that validates the ordered graph
proposal before persistence and carries exact expected references plus explicit
write intent.

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

Catalogued-only Mutable-derived objects remain visible and unresolved. Add is
enabled as an interaction, but succeeds only after exact family inspection
resolves one component contract; otherwise it changes no draft or project.

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
