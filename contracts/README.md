# Semantic contracts

This directory contains authoritative Task 005 records organized by record
family. The schemas are under `schemas/`, the normative boundary is documented
in `docs/DEVICE_INSTRUMENT_CONTRACTS.md`, and read-only validation is under
`tools/contracts/`.

The current pair is deliberately minimal:

- `device-profiles/gills-minimal-v0.json` declares one normalized Gills knob
  slot and explicitly unresolved physical range/resolution; and
- `instruments/blend-reference-v0.json` maps that slot to public `Blend`, then
  maps `Blend` to a Task 006-owned deferred graph public target.

These records contain no graph structure, implementation, target, backend,
legacy patch, build, compiler, GUI, firmware, or hardware evidence.
