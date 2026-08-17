# Schuss desktop

Status: runnable first product slice. Read-only catalog browsing is implemented;
graph, project, build, device, and hardware actions are absent.

The local app is a Tauri 2 shell around a React and TypeScript presentation.
Schuss core remains the semantic authority. The renderer submits exactly one of
three documented operations through a capability-limited adapter and consumes
the canonical result; it must never edit catalog files, semantic JSON records,
or project workspace files directly.

## Launch

Requirements: Python 3, a stable Rust/Cargo toolchain, Node.js, npm, and the
normal macOS Xcode command-line tools.

```bash
cd apps/schuss_desktop
npm install
npm run dev
```

`npm run dev` starts the Vite frontend and native Tauri window. The first core
load validates exact record set `schuss-record-set-000021@1`; subsequent
catalog operations reuse that in-memory context.

For renderer-only browser development and visual checks:

```bash
npm run dev:web
```

Browser development still uses the real Python `schuss_core` dispatcher via a
localhost-only Vite adapter. It does not use copied product catalog data. A
production frontend build without Tauri has no fallback bridge.

## Runtime boundary

One Tauri command, `dispatch_read_only_operation`, exposes exactly:

- `application.describe` using request/result v7;
- `catalog.search` using request/result v2; and
- `catalog.inspect` using request/result v2.

Rust and Python both reject unknown operations and mismatched request/result
versions. Successful responses are canonical Schuss results. Bridge failures
use a separate structured transport error and never become catalog meaning.
The Tauri capability file grants only `core:default`; no filesystem, shell,
HTTP, project-write, build, device, or hardware plugin is installed or granted.

## Exact direct dependencies

Runtime:

- React and React DOM `19.2.8`;
- Tauri JavaScript API `2.11.1`; and
- Radix Scroll Area `1.2.18`, Tabs `1.1.21`, and Tooltip `1.2.16`.

Development and tests:

- Tauri CLI `2.11.4`, Vite `8.2.1`, React plugin `6.0.5`, and TypeScript
  `7.0.2`;
- Vitest `4.1.10`, jsdom `30.0.1`, Testing Library React `16.3.2`, user-event
  `14.6.4`, and jest-dom `7.0.1`; and
- Node types `26.2.0`, React types `19.2.18`, and React DOM types `19.2.4`.

Rust resolves Tauri `2.11.5`, Tauri Build `2.6.3`, Serde `1.0.229`, and
Serde JSON `1.0.151` in `src-tauri/Cargo.lock`.

No broad visual kit, Material UI, shadcn base, React Flow, or Blockly is
installed.

## Validation

```bash
npm run build
npm test
cargo test --manifest-path src-tauri/Cargo.toml
cargo check --manifest-path src-tauri/Cargo.toml
python3 ../../tools/contracts/validate_desktop_ui_structure.py
python3 -m unittest tools.contracts.tests.test_desktop_read_only_bridge
```

The last unittest command is run from the repository root. The normative task
and ownership boundaries are in
`../../docs/tasks/ui-desktop-read-only-catalog.md` and
`../../docs/DESKTOP_UI_BOUNDARY.md`.

## Deliberately deferred

The next bounded UI step is acceptance of this read-only slice, followed by a
separately authorized read-only graph-inspection task. Project mutation must
remain behind the existing project operations and its later gates. Packaging,
signing, updating, build execution, device upload, real-time testing, and
audible testing are not part of this application.
