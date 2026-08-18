# Schuss desktop

Status: one consolidated local desktop application with exact catalog browsing,
project-backed node patching, process-local build jobs, explicit Ksoloti Core
discovery, and a read-back-verified volatile-RAM upload path. Device acceptance
uses fakes. Accepted project-local objects remain separate from the permanent
catalog and appear in the patcher through read-only shared operations;
firmware flash, DFU, reset, SD writes, packaging, and automatic hardware access
are not implemented.
The app opens directly onto the patcher canvas. Objects and Patches are drawer
tabs rather than separate pages, and a versioned local setting remembers one
projects root and the last accepted project.

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

The first core load validates exact additive record set
`schuss-record-set-000027@1`; new desktop projects pin that additive
workspace-shell base while the allowlist retains the two project-object reads
and adds only the shared workspace list/create operations. The persistent
bridge reuses the validated context and a bounded process-local semantic
augmentation cache. Existing projects retain and load their exact immutable
base, and each project load rereads and validates all governed workspace bytes
before any cache hit.
Renderer-only verification uses the same Python adapter:

```bash
npm run dev:web
```

## Product surfaces

- **Patcher** is the always-present application home and renders exact graph
  nodes, contract-owned ports, and connections;
  node movement and viewport state remain non-semantic.
- **Patches drawer** lists only core-validated direct children of the remembered
  projects root. New asks only for a name; core allocates the path and ID and
  forks the accepted seven-object profile.
- **Objects drawer** defaults to patcher-relevant contracted implementations,
  retains an All catalog view over all 133 Task 030 implementations, and
  expands readiness/provenance detail inline.
- **Project objects** lists accepted local definitions separately from catalog
  implementations and places their exact component contracts through the same
  unsaved graph edit path. A changed accepted project reloads automatically
  only when the editor is clean.
- **Inspector** edits contract-owned parameter values. Save validates the
  ordered proposal and versions graph/instrument/build-request/project through
  one `project.profile.transact` operation.
- **History** reads immutable ancestry and makes revert an explicit successor
  operation.
- **Build** starts a core-owned background job over the accepted project and
  surfaces structured progress, stage outcomes, diagnostics, and artifact facts.
- **Device** performs discovery only after an explicit action, checks exact
  board and firmware identity, and gates a confirmed volatile-RAM upload on one
  successful target executable. Read-back verification precedes optional start.

Catalogued-only implementations stay visible under All catalog. One Add action
resolves the exact family and requires exactly one component contract; it fails
closed without changing the graph otherwise.

## Runtime boundary

One Tauri command, `dispatch_desktop_operation`, carries a closed twenty-four
operation allowlist covering catalog/object inspection, graph inspection and
proposal, project authoring/history and project-object reads, build sessions,
device discovery, and verified volatile upload.
Rust and Python independently enforce request/result versions, size limits,
canonical metadata, and absolute workspace paths.

The main window grants only `core:default`. No filesystem, shell, HTTP, USB, or
hardware plugin is installed or granted to the renderer. Build outputs and
libusb handles remain private to the persistent core process. React Flow
`12.11.3` is a presentation dependency, not a semantic graph model.

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
  tools.contracts.tests.test_desktop_build_device_sessions \
  tools.contracts.tests.test_desktop_patcher_bridge \
  tools.contracts.tests.test_desktop_patcher_operations \
  tools.contracts.tests.test_desktop_workspace_shell \
  tools.contracts.tests.test_desktop_ui_structure
```

The patcher, performance, build/device, and project-object contracts are
`../../docs/tasks/ui-desktop-patcher-authoring.md` and
`../../docs/tasks/ui-desktop-authoring-performance.md`, and
`../../docs/tasks/ui-desktop-build-device-workflow.md`, and
`../../docs/tasks/ui-desktop-project-object-handoff.md`, and
`../../docs/tasks/ui-desktop-workspace-shell.md`; ownership and the
remaining gated seams are in `../../docs/DESKTOP_UI_BOUNDARY.md`.
