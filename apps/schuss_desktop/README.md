# Schuss desktop

Status: structure-only initialization; no desktop application is implemented.

This directory is the future application boundary for a Tauri 2 shell with a
React and TypeScript frontend. It is intentionally inert: there is no HTML
entry point, React component, Rust source, Cargo project, Tauri configuration,
transport adapter, package dependency, or lockfile.

The existing Schuss Python core remains the sole semantic authority. A future
desktop adapter may submit only the named, versioned operations in
`contracts/ui-core-boundary-v1.json` and must consume their canonical results
without client-specific reshaping. The UI must never edit catalog files,
semantic JSON records, or project workspace files directly.

## Layout

- `contracts/` contains the versioned, capability-limited client boundary.
- `src/` reserves the future React/TypeScript frontend location.
- `src-tauri/` reserves the future Tauri 2 shell and transport location.
- `package.json` and `tsconfig.json` record only inert project metadata and
  intended TypeScript constraints; they install or execute nothing.

The normative ownership rules and next-slice sequence are in
`../../docs/DESKTOP_UI_BOUNDARY.md`. The completed bounded task contract is
`../../docs/tasks/ui-desktop-initialization.md`.

## Static validation

From the repository root:

```bash
python3 tools/contracts/validate_desktop_ui_structure.py
python3 -m unittest tools.contracts.tests.test_desktop_ui_structure
```

The validator is dependency-free and read-only. It intentionally fails if
product source, package dependencies, lockfiles, semantic-record copies, or an
unreviewed capability change appears in this initialization boundary.

