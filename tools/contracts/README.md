# Contract tools

These tools validate, generate, or execute exact Schuss contract closures.
Read-only checks emit deterministic summaries and never access hardware.

## Ordinary read-only checks

```bash
python3 tools/contracts/validate_component_graph_contracts.py
python3 tools/contracts/validate_target_backend_build_contracts.py
python3 tools/contracts/validate_task009_prerequisite.py
python3 tools/contracts/validate_task011b.py
python3 tools/contracts/validate_task011c.py
python3 tools/contracts/validate_task012a.py
python3 tools/contracts/validate_task013.py
python3 tools/contracts/validate_task014.py
python3 tools/contracts/validate_task015.py
python3 tools/contracts/validate_task016_contract.py
python3 tools/contracts/validate_task016.py
python3 tools/contracts/validate_task017_contract.py
python3 tools/contracts/validate_task017.py
python3 tools/contracts/validate_task018_contract.py
python3 tools/contracts/validate_task021_contract.py
python3 tools/contracts/validate_task022_contract.py
python3 tools/contracts/validate_task023_contract.py
python3 tools/contracts/validate_task023.py
python3 tools/contracts/validate_task022.py
python3 tools/contracts/validate_backbone_governance.py
python3 -m unittest discover -s tools/contracts/tests
```

`generate_task013_record_set.py --check` through
`generate_task017_records.py --check`, `run_task016.py --check`,
`run_task017.py --check`, `generate_task022_records.py --check`,
`run_task022.py --check`, and `generate_task023_records.py --check` are also
read-only freshness/reproduction checks.

The Task 016/017 contract validators authenticate retained ADR/evidence
boundaries; completed task Markdown is intentionally archived through Git.

## Authenticated local closure

Task 009 and Task 011C execution checks require the ignored authenticated local
content store at `build/task009-prerequisite-repair-v1/content-addressed/`.
Ordinary discovery explicitly skips only that local-store presence assertion
when the store is absent. This is neither a pass nor a failure claim for the
authenticated closure.

When the store exists, run the explicit fail-closed checks:

```bash
python3 tools/contracts/run_task009.py --check
python3 tools/contracts/run_task011c.py --check
```

Running either command without `--check` invokes exact Java/ARM execution and
writes its explicit output roots. That requires separate authorization. The
commands do not access connected hardware, upload, or flash.

## Architecture

`validator_core.py` owns shared canonical/schema/reference mechanics. Domain
rules remain in sibling modules; `aggregate_validator.py` is the only composer.
The public product boundary is `packages/schuss_core/control_plane.py`, and the
CLI must not import validator internals.

The compiler front half plans through stage 6. `build_execution.py` invokes
only an exact registered handler. The retained legacy handler, direct graph
handler, and mapped Gills panel handler remain exact boundaries beneath the
same graph/target/build contracts, with no silent fallback. Task 018 adds
`gills.inspect`, total panel/coverage validation, and a separate runtime
realization without making the device profile a graph or backend.

Task 022 deliberately does not register a product build request, runtime
realization, instrument, handler, or CLI selector for its diagnostic. Its
standalone exact builder authenticates the Task 021 parent plan and direct ARM
toolchain, then produces an omitted-instrument, silent-output panel telemetry
candidate. The retained connected observation records exactly one approved
volatile-RAM upload and `POT_EVENT_FOCUS_UNSTABLE`; no level-6 promotion or
Task 021 replacement upload occurred. Any new device action remains separately
approval-gated.

Task 023 adds the client-neutral `application.describe` operation and exact
record set `schuss-record-set-000015@1`, then exposes the accepted operations
through one CLI v2 grammar. `validate_task023.py` is a read-only cross-service
smoke and two-fresh-root determinism check; it does not execute a backend,
write a project, or access hardware.

Every check must keep structural, lowering, generation, ARM compile/link,
connected-device, real-time, and audible evidence distinct. See
`docs/STATUS.md` for the current boundary.
