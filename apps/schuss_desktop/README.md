# Schuss desktop

Status: one consolidated local desktop application with exact catalog browsing
and project-backed node patching. Build execution, device sessions, USB
upload, flash, packaging, and hardware access are not implemented.

The app is a Tauri 2 shell around React, TypeScript, and React Flow. Schuss
core remains the semantic authority: the renderer submits versioned operations
through one closed adapter and never reads or writes catalog, graph, or project
JSON directly.

## Launch

Requirements are Python 3, Node.js/npm, stable Rust/Cargo, and the normal
macOS Xcode command-line tools.

```bash
cd apps/schuss_desktop
npm install
npm run dev
```

The first core load validates exact record set
`schuss-record-set-000024@1`; the persistent bridge reuses that exact validated
base and a bounded process-local semantic augmentation cache. Each project load
still rereads and validates all governed workspace bytes before any cache hit.
Renderer-only verification uses the same Python adapter:

```bash
npm run dev:web
```

## Product surfaces

- **Patches** opens explicit Schuss workspaces and creates a project-owned fork
  of the accepted seven-object Task 026 profile.
- **Objects** lists the 133 Task 030 implementation records by function, form,
  readiness, and provenance without requiring prose descriptions.
- **Patcher** renders exact graph nodes, contract-owned ports, and connections;
  node movement and viewport state remain non-semantic.
- **Inspector** edits contract-owned parameter values. Save validates the
  ordered proposal and versions graph/instrument/build-request/project through
  one `project.profile.transact` operation.
- **History** reads immutable ancestry and makes revert an explicit successor
  operation.

Catalogued-only implementations stay visible. Add resolves the exact family
and requires exactly one component contract; it fails closed otherwise.

## Runtime boundary

One Tauri command, `dispatch_desktop_operation`, carries a closed fourteen
operation allowlist covering catalog/object inspection, graph inspection and
proposal, and explicit project creation/inspection/versioning/history/revert.
Rust and Python independently enforce request/result versions, size limits,
canonical metadata, and absolute workspace paths.

The main window grants only `core:default`. No filesystem, shell, HTTP, build,
device, or hardware plugin is installed or granted. React Flow `12.11.3` is a
presentation dependency, not a semantic graph model.

## Validation

```bash
npm run build
npm test
cargo test --manifest-path src-tauri/Cargo.toml
python3 ../../tools/contracts/validate_desktop_ui_structure.py
```

From the repository root:

```bash
python3 -m unittest \
  tools.contracts.tests.test_desktop_authoring_performance \
  tools.contracts.tests.test_desktop_patcher_bridge \
  tools.contracts.tests.test_desktop_patcher_operations \
  tools.contracts.tests.test_desktop_ui_structure
```

The patcher and performance contracts are
`../../docs/tasks/ui-desktop-patcher-authoring.md` and
`../../docs/tasks/ui-desktop-authoring-performance.md`; ownership and future
build/device seams are in `../../docs/DESKTOP_UI_BOUNDARY.md`.
