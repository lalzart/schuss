# Desktop UI boundary

Status: the first unnumbered product slice is implemented locally for read-only
catalog browsing. Schuss core remains the authority; later UI phases remain
gated.

## End-to-end boundary

```text
React/TypeScript presentation
        -> one capability-limited Tauri command
        -> persistent local Python adapter
        -> existing packages/schuss_core dispatcher and services
        -> canonical Schuss operation result
        -> presentation rendering only
```

The application lives in `apps/schuss_desktop/`. The Rust adapter accepts one
structured request, enforces the closed read-only allowlist and expected
versions, and passes it to a persistent Python process. Python loads exact
record set `schuss-record-set-000021@1` once, independently enforces the same
allowlist, dispatches through the existing core, and emits canonical result
bytes. Unknown operations, request versions, result versions, malformed
payloads, and oversized requests fail explicitly.

Browser-mode development uses a localhost-only Vite proxy to the same Python
adapter so visual verification exercises live operations rather than copied
catalog data. That proxy is absent from production output; production requires
the Tauri command.

## Implemented capabilities

Exactly three shared operations are exposed:

| Operation | Request | Result | Effect |
| --- | --- | --- | --- |
| `application.describe` | `schuss-operation-request-v7` | `schuss-operation-result-v7` | read-only |
| `catalog.search` | `schuss-operation-request-v2` | `schuss-operation-result-v2` | read-only |
| `catalog.inspect` | `schuss-operation-request-v2` | `schuss-operation-result-v2` | read-only |

The UI renders function-first browsing, exact search/filter results,
provenance including `mutable-instruments-derived`, readiness states, signal
facets, collective named interface facets, source observations, exact
implementation references, evidence references, and unresolved facts.

`catalog.inspect` currently reports signal facets and collective contract facet
names; it does not label every name as a port, parameter, attribute, action, or
display. The desktop therefore preserves that collective label and does not
guess a kind. A future richer component-inspection operation would be core
work, not a renderer projection.

## Semantic ownership

The existing Schuss Python core and versioned operations remain the sole source
of catalog, component, graph, instrument, project/workspace, compiler-plan,
build, and evidence semantics. The desktop may construct one allowed request
and render its canonical result. It may not:

- read or edit catalog source files as application state;
- load, rewrite, or persist semantic JSON records directly;
- scan project directories to infer record membership;
- create a UI-private catalog matcher, readiness rule, graph edit language,
  persistence format, compiler path, diagnostic meaning, or result projection;
- invoke a shell, build, device, real-time, or audible operation; or
- infer a newer revision, capability, readiness, evidence, or support claim.

Selection, filters, query text, scroll state, active tabs, panel layout, and
loading/error state are UI-owned ephemeral state. The Tauri window has only
core default permissions. It has no filesystem, shell, network, project-write,
build, or hardware plugin capability.

## Capability phases

### 1. Read-only catalog browsing

Implemented by the active unnumbered task. It calls `application.describe`,
`catalog.search`, and `catalog.inspect` and writes no semantic or workspace
state.

### 2. Graph visualization

Not implemented. After this slice is accepted, a separately authorized task
may call `graph.inspect` and render the exact graph plus component-contract
closure. React Flow remains uninstalled. Compound internals must remain
inspectable and graph semantics remain core-owned.

### 3. Project mutation through existing operations

Not authorized. A later task may expose existing project operations only after
the graph phase and the explicit application gates are satisfied. Proposal,
persistence, history, and revert must use shared operations and exact write
intent; the UI never edits workspace JSON files.

Build progress and structured diagnostics still depend on a future contracted
session/job boundary. Build, device upload, real-time/resource, and audible
behavior are outside all implemented desktop capabilities.

## Security and dependency boundary

The renderer imports only `@tauri-apps/api/core`; no Tauri plugin package is
installed. The Rust process uses standard child-process I/O only inside the
native shell and never exposes a general process command. The selected Radix
packages are Scroll Area, Tabs, and Tooltip only. No broad visual kit, React
Flow, Blockly, updater, analytics, telemetry, packaging, or publishing
dependency is present.

The original structural initialization remains retained in
`docs/tasks/ui-desktop-initialization.md`. This implementation is the separate
explicitly authorized task in `docs/tasks/ui-desktop-read-only-catalog.md`; it
does not rewrite Task 028, revive Task 012B, or activate a later UI phase.
