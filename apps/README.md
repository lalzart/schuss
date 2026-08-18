# Applications

Schuss applications are clients of the shared catalog, graph, project,
compiler, build, and diagnostic operations; they do not own alternate
semantics or persistence.

`schuss_desktop/` is the sole maintained product UI. Its Tauri shell and React
renderer combine Objects and Patches over the exact shared operation boundary.
The superseded standalone React patcher and machine prototype were removed
after consolidation; their history remains recoverable from Git.

Task 029 implements the isolated, dependency-free
`schuss_machine_viewer/` reference client. It renders only canonical
`machine.inspect` results for Palimpsest and Tide Pit and exposes no build,
play, deploy, edit, catalog-promotion, persistence, or hardware action. It does
not integrate with or depend on `schuss_desktop/`.

The separate `schuss_machine_viewer/` is a retained Task 029 evidence client,
not a second product application. See `docs/STATUS.md` and
`docs/DESKTOP_UI_BOUNDARY.md` for the current desktop boundary.
