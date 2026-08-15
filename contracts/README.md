# Semantic and build-domain contracts

This directory contains authoritative Task 005-007 records organized
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
  closure and stops at implementation resolution.

There is no production build result, artifact, resource report, or evidence
claim. The production candidate remains unresolved and no legacy patch,
compiler, GUI, firmware, hardware, real-time, or audible action is implied.
See `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`.
