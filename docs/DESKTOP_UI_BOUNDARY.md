# Desktop UI boundary

Status: the consolidated Tauri desktop implements catalog/object browsing,
exact graph visualization and proposal, and project-backed authoring. Build
execution and device deployment remain separately gated.

## End-to-end boundary

```text
React/TypeScript presentation
        -> dispatch_desktop_operation
        -> closed Rust validation
        -> persistent local Python adapter
        -> shared schuss_core dispatcher / ProjectService
        -> canonical operation result
```

The product application is `apps/schuss_desktop/`. Browser-mode development
uses a localhost Vite proxy to the same Python adapter; production has no
renderer fallback. Both paths select exact record set
`schuss-record-set-000024@1`.

## Implemented capability groups

| Group | Operations | Effect |
| --- | --- | --- |
| Catalog | `application.describe`, `catalog.search`, `catalog.inspect`, `catalog.implementations.search`, `component.inspect` | read-only |
| Graph | `graph.inspect`, `graph.transact` | read-only / proposal-only |
| Project | `project.init`, `project.inspect`, `project.validate`, `project.profile.fork`, `project.profile.transact`, `project.history.inspect`, `project.revert` | explicit workspace read/write |

The adapter rejects every operation outside this list, including
`build.execute`. The application capability description may report shared
operations that require other services; description does not grant the
desktop permission to invoke them.

## Ownership

Schuss core owns catalog, component, graph, instrument, project/workspace,
compiler, build, device, and evidence meaning. The renderer may construct an
allowed request and render its canonical result. It may not read semantic JSON,
scan a workspace, choose an implicit revision, infer a component contract,
write a project file, or invoke a general process/filesystem/USB API.

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

## Future build and device seam

The status bar reserves product language for build and device state, but no
callable action exists. A later bounded slice should add a core-owned build
session/job contract with structured progress/diagnostics, followed by an
explicit device-session contract for discovery, identity, compatibility,
upload intent, verification, and recovery. The renderer must never own raw USB
packets or treat build success as connected-device, real-time, or audible
evidence.

The current Tauri capability remains only `core:default`; no filesystem, shell,
HTTP, updater, build, device, or hardware plug-in permission is present.
