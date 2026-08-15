# Semantic contract tools

Validate the accepted production closures:

```bash
python3 tools/contracts/validate_component_graph_contracts.py
python3 tools/contracts/validate_target_backend_build_contracts.py
python3 tools/contracts/validate_task009_prerequisite.py
python3 tools/contracts/run_task009.py --check
python3 tools/contracts/validate_task011b.py
python3 tools/contracts/validate_task011c.py
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

Task 008 consolidates shared mechanics in `validator_core.py`. The three sibling
domain modules are `device_instrument_rules.py`,
`component_graph_rules.py`, and `target_backend_build_rules.py`; none imports a
sibling. `aggregate_validator.py` is the only composer. The historic
`validate_*` filenames remain compatible process adapters and retain their
accepted output bytes.

Task 008 operations and their minimal machine adapter are documented in
`docs/OPERATION_CONTRACTS.md`. Run the adapter with:

```bash
bin/schuss op --request request.json --json
```

Task 010 adds deterministic product commands over that same dispatcher:

```bash
bin/schuss validate
bin/schuss graph inspect schuss-graph-000001@1
bin/schuss graph transact schuss-graph-000001@1 --edits edits.json
bin/schuss build resolve schuss-build-request-000001@1
bin/schuss completion zsh
```

Add `--json` for the unchanged canonical operation result, or
`--record-set contracts/record-sets/task009-executed-prospective-v0.json` for
the explicit Task 009 successor context. `build resolve` does not execute a
backend, and transactions are never persisted.

`run_task009.py --check` is read only and validates the explicit Task 009
successor record set plus retained artifacts. Running it without `--check` is
the separately authorized executable proof path: it invokes the exact isolated
Java and ARM closure and writes only to its explicit task output roots. It is
not a general compiler or product CLI.

`validate_task011c.py` and `run_task011c.py --check` are read-only retained
validators for record set `schuss-record-set-000006`. Running
`run_task011c.py` without `--check` is the separately authorized exact
eight-node proof path: six candidate probes, ordinary resolution, and two
production runs through deterministic Java generation and authenticated ARM
compile/link. It does not access hardware or generalize the backend.
