# Semantic and build-domain contracts

This directory contains authoritative Task 005-011B records organized
by record family. The schemas are under `schemas/`, the normative boundaries
are documented in `docs/DEVICE_INSTRUMENT_CONTRACTS.md` and
`docs/COMPONENT_GRAPH_CONTRACTS.md`, and read-only validation is under
`tools/contracts/`.

The current pair is deliberately minimal:

- `device-profiles/gills-minimal-v0.json` declares one normalized Gills knob
  slot and explicitly unresolved physical range/resolution; and
- `instruments/blend-reference-v0.json` retains the historical deferred graph
  intention byte-for-byte;
- `catalog-families/`, `component-contracts/`, and
  `implementation-bindings/` close the exact Crossfader family, three public
  signatures, and frozen observations 458-460;
- `graphs/blend-crossfader-v0.json` is the authoritative one-node mixed-rate
  graph with public audio `a`, `b`, `out` and parameter `blend`; and
- `instruments/blend-reference-v0-r2.json` resolves that graph and public
  target exactly;
- `capabilities/`, `build-environments/`, `compute-targets/`, and `backends/`
  declare the smallest truthful Ksoloti target/backend closure;
- `binding-eligibility/` adds an exact, unresolved eligibility companion
  without modifying the Task 006 binding; and
- `build-requests/` pins the exact Blend graph/instrument/target/backend
  closure and stops at implementation resolution; and
- `catalog/task011a-corpus-v1.json` closes exact successor references for all
  26 Phase 4A pilot families and the bounded seven-role Gills-slice identity
  review without rewriting the overlay or creating missing DSP contracts.

Task 011B records live under `task011b/` so every accepted default directory
scan remains unchanged. They add six exact component contracts and bindings,
six unresolved eligibility companions, one eight-node graph, one Gills
instrument, one artifact-generation-stopping request, and six not-authorized
probe inputs under one closed probe procedure. Record set
`schuss-record-set-000005` revision 1 selects that explicit successor view and
retains parent `000004` exactly.

Task 009 successor records retain one bounded production build/evidence chain
through compile/link level 5. Task 011A merely projects those exact records;
Task 011B adds no build result, artifact, or compatibility promotion. No GUI,
firmware, connected
hardware, real-time, or audible action is implied. See
`docs/TARGET_BACKEND_BUILD_CONTRACTS.md` and `docs/CATALOG_OPERATIONS.md`.
