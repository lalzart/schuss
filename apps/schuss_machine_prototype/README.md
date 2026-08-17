# Gills machine visual prototype

This isolated React Flow client tests a Gills-first way to understand the exact
Tide Pit and Palimpsest machine inspections. The authenticated physical panel
is the primary navigator; the canvas shows source-evidenced musical compounds
and their downstream signal path.

It is a read-only presentation prototype. It does not edit a Schuss graph,
connect objects, build, deploy, play, promote catalog entries, or communicate
with hardware. The dependency-free `apps/schuss_machine_viewer/` remains the
canonical evidence-oriented reference client.

## Run locally

```sh
cd apps/schuss_machine_prototype
npm install
npm run dev
```

Open the URL printed by Vite. Use the Tide Pit/Palimpsest switch, choose an
effect path, and then select a physical panel region or a machine compound.
The `+` control expands a compound's source-evidenced explanatory roles.

## Local verification

```sh
npm test
npm run typecheck
npm run build
```

The full task boundary and acceptance checks are in
`docs/GILLS_MACHINE_VISUAL_PROTOTYPE_CONTRACT.md`.
