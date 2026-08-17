# Schuss Machine Viewer

This dependency-free reference client renders only canonical
`machine.inspect` results. It owns no machine, graph, catalog, device, or
support semantics and does not read source checkouts or contract records.

The initial fixtures are the exact inspection-only reference machines
Palimpsest (`projects/palimpsest-gills/`) and Tide Pit
(`projects/tide-pit-gills/`, local wrapper `tidepit`). Their diagrams are
source-evidenced presentations, not accepted Schuss DSP graphs.

From the repository root, serve static files and open this directory:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000/apps/schuss_machine_viewer/`. The client has
no build, play, deploy, edit, promotion, or hardware action.
