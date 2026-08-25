# Schuss desktop

Status: one consolidated local desktop application that opens on an exact
six-entry Schuss instrument library. Pamplist has canonical musical identity;
the other five entries remain noncanonical Instrument Lab prototypes. A
separate Workshop retains
catalog browsing, project-backed node patching, process-local build jobs,
explicit Ksoloti Core discovery, and a fake-tested read-back-verified
volatile-RAM upload path. Firmware flash, DFU, reset, SD writes, packaging, and
automatic hardware access are not implemented.

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

The first core load validates exact additive application record set
`schuss-record-set-000036@1`. The instrument library binds six exact prototype
revisions, resolves Pamplist's canonical instrument and graph records, and
checks only declared native build artifacts. Workshop project
creation deliberately remains pinned to its established workspace-shell base,
`schuss-record-set-000028@1`; existing projects continue to load their exact
immutable base. The contexts are separate rather than silently rebasing old
patch-authoring behavior onto the audition library.
Renderer-only verification uses the same Python adapter:

```bash
npm run dev:web
```

## Product surfaces

- **Instruments** is the default home. It lists six exact revisions, labels
  Pamplist as canonical and the remaining entries as prototypes, shows
  verified-build or unavailable state, and launches only a declared JUCE
  standalone executable whose current SHA-256 matches retained evidence.
- **Workshop** retains the complete patcher, project, build, and Ksoloti
  workflow. Its patcher renders exact graph nodes, contract-owned ports, and connections;
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

One Tauri command, `dispatch_desktop_operation`, carries a closed twenty-seven
operation allowlist. It adds only `instrument.library.list`,
`instrument.session.start`, and `instrument.session.inspect` to the retained
catalog, graph, project, build, and device operations.
Rust and Python independently enforce request/result versions, size limits,
canonical metadata, and absolute workspace paths.

The renderer supplies only exact prototype identity plus the literal
`explicit-native-juce-audition` intent. It never receives an executable path or
command. The core revalidates a repository-controlled regular executable and
starts it through direct argv without a shell. The main window grants only
`core:default`; no filesystem, shell, HTTP, USB, or hardware plug-in is granted
to the renderer. Pamplist's canonical musical identity does not turn this
prototype launch path into a canonical provider. An audition session is
process-local observation and does not establish application-launch,
controller-receipt, listening, real-time, device, or production evidence.

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
  tools.contracts.tests.test_task039_instrument_library \
  tools.contracts.tests.test_task043_pamplist_canonical \
  tools.contracts.tests.test_desktop_patcher_operations \
  tools.contracts.tests.test_desktop_workspace_shell \
  tools.contracts.tests.test_desktop_ui_structure
```

The patcher, performance, build/device, and project-object contracts are
`../../docs/tasks/ui-desktop-patcher-authoring.md` and
`../../docs/tasks/ui-desktop-authoring-performance.md`, and
`../../docs/tasks/ui-desktop-build-device-workflow.md`, and
`../../docs/tasks/ui-desktop-project-object-handoff.md`, and
`../../docs/tasks/ui-desktop-workspace-shell.md`, with the Instruments-first
slice in `../../docs/tasks/039-desktop-instrument-library.md`; ownership and the
remaining gated seams are in `../../docs/DESKTOP_UI_BOUNDARY.md`.
