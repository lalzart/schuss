# Semantic contract tools

Validate the aggregate Task 006 production closure, including Task 005 device
and instrument records:

```bash
python3 tools/contracts/validate_component_graph_contracts.py
python3 tools/contracts/validate_target_backend_build_contracts.py
python3 -m unittest discover -s tools/contracts/tests
```

`validate_device_instrument_contracts.py` remains the compatible focused entry
point and uses the Task 006 graph registry when graph records are present.
All validators are read only and emit deterministic one-line JSON summaries.
They do not access hardware, invoke Java, generate a legacy patch, compile, or
write caches. The fixture matrices under `tests/fixtures/` cover cross-layer,
type-conversion, topology, seam-map, compound, and exact-resolution failures.
Task 007 adds target/backend/eligibility resolution, future build/result,
artifact, resource, diagnostic, and eight-level evidence fixtures.

The import direction is Task 007 -> Task 006 -> Task 005. Do not add upward or
circular imports. Extracting their shared canonical/schema/diagnostic helpers
into a lower validator core is the first prerequisite of Task 008.
