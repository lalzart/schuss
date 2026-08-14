# Semantic contracts

This directory contains authoritative Task 005 and Task 006 records organized
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
  target exactly.

These records contain semantic graph structure and implementation seam maps,
but no target, backend, selected build implementation, legacy patch, compiler,
GUI, firmware, hardware, real-time, or audible evidence.
