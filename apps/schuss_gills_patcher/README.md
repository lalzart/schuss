# Schuss Gills graph patcher prototype

This isolated prototype tests a visual node-patcher direction for complete
Gills instruments. It uses Tide Pit and Palimpsest as source-evidenced reference
machines, and it deliberately does not provide persistence, compilation, or a
desktop/runtime bridge.

From this directory:

```sh
npm install
npm run dev -- --host 127.0.0.1
```

Open the URL printed by Vite (normally <http://127.0.0.1:5173>). Use the machine
tabs to switch references, use the mode control inside the instrument compound
to inspect mode-dependent mappings, and drag an available object card onto the
canvas. The `+` button is the keyboard-accessible equivalent of drag-and-drop.

The library sidebar keeps **Objects** and **Patches** separate. Objects use the
accepted direct palette and function filters. Patches search the Tide Pit and
Palimpsest templates plus drafts saved in this browser. **Save patch** stores a
versioned presentation draft in browser `localStorage`; it is not yet a wired,
buildable, or authoritative Schuss project.

Validation:

```sh
npm test
npm run typecheck
npm run build
```

The governing task boundary is
[`docs/GILLS_GRAPH_PATCHER_LOCAL_LIBRARY_CONTRACT.md`](../../docs/GILLS_GRAPH_PATCHER_LOCAL_LIBRARY_CONTRACT.md),
which succeeds the original visual prototype contract.
