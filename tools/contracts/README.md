# Semantic contract tools

Validate the accepted production closures:

```bash
python3 tools/contracts/validate_component_graph_contracts.py
python3 tools/contracts/validate_target_backend_build_contracts.py
python3 tools/contracts/validate_task009_prerequisite.py
python3 tools/contracts/run_task009.py --check
python3 tools/contracts/validate_task011b.py
python3 tools/contracts/validate_task011c.py
python3 tools/contracts/validate_task012a.py
python3 tools/contracts/generate_task013_record_set.py --check
python3 tools/contracts/validate_task013.py
python3 tools/contracts/generate_task014_record_set.py --check
python3 tools/contracts/validate_task014.py
python3 tools/contracts/generate_task015_record_set.py --check
python3 tools/contracts/validate_task015.py
python3 tools/contracts/generate_task016_records.py --check
python3 tools/contracts/run_task016.py --check
python3 tools/contracts/validate_task016.py
python3 tools/contracts/generate_task017_records.py --check
python3 tools/contracts/run_task017.py --check
python3 tools/contracts/validate_task017.py
python3 tools/contracts/compiler_determinism_matrix.py
python3 tools/contracts/validate_task016_contract.py
python3 tools/contracts/validate_task017_contract.py
python3 tools/contracts/validate_task018_contract.py
python3 tools/contracts/validate_backbone_governance.py
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

`validate_task012a.py` is the read-only retained project/workspace validator.
It refuses local state requiring recovery, verifies the exact Task 011C base,
portable project fixture, governed bytes, semantic closure, and schema hashes,
and confirms the target workspace bytes are unchanged.

`generate_task013_record_set.py --check` verifies the exact additive schema
closure in record set `schuss-record-set-000007` without writing. Running it
without `--check` deterministically refreshes only that Task 013 manifest.
`validate_task013.py` is read only: it plans the exact Task 011C eight-node
request through stage 6, compares every resolution trace with accepted
`build.resolve`, authenticates artifact bytes and origins, proves the semantic
record members equal parent record set `000006`, checks compiler import
isolation, and confirms stages 7-10 and evidence levels 3-8 remain `not-run`.

`generate_task014_record_set.py --check` verifies exact additive record set
`schuss-record-set-000008`. `validate_task014.py` is read only: it validates
the exact handler descriptor, successful stage-6 plan, retained two-root
execution equality, seven artifact identities, levels 1-5, and core/legacy
import isolation. Focused tests exercise intent, cancellation, registry
ambiguity, failure cleanup, atomic publication, operation parity, and CLI.

`generate_task015_record_set.py --check` verifies exact additive record set
`schuss-record-set-000009`. `validate_task015.py` is read only: it authenticates
the exact Blend plan/graph/contract closure, normalized Q27 module, standalone
C++17 and source map, compiled arithmetic vectors, and evidence levels 1-4.

`compiler_determinism_matrix.py` copies the current tracked and non-ignored
untracked tree into two temporary fresh roots, then compares four fresh-process
Tasks 013-015 cells across repository location, working directory, available
locale, `PYTHONHASHSEED`, record enumeration, timezone, source-date, and
unrelated environment noise. It authenticates canonical plans, diagnostics,
origin/source maps, direct C++, host-compiled arithmetic vectors, and unchanged
parent semantic bytes. The source worktree is read only; all generated files
stay in temporary scratch roots. Task 014 execution defaults to `auto` and can
run only through the exact authenticated Task 011C adapter when its retained
prerequisite validates. Use `--task014-execution require` to fail instead of
skip when that local closure is unavailable, or `skip` for a structural and
host-only run.

`validate_task016_contract.py` validates the accepted decision and completion
boundary; `validate_task016.py` checks the exact semantic records, direct
frontend, authenticated inputs, two fresh ARM build roots, retained artifacts,
and unchanged Task 015 output. `generate_task017_records.py --check` validates
the bounded reviewed-core successor bytes, `run_task017.py --check` reproduces
the deterministic catalog/graph/build CLI evidence without execution, and
`validate_task017.py` checks all family joins, the exact two headless
instruments, fail-closed plans, preserved earlier results, and evidence-level
separation. `validate_task017_contract.py` retains the completed Task 017 scope.
`validate_task018_contract.py` validates that both dependencies are complete
and that the bounded full-Gills implementation is ready but not yet started.

`validate_backbone_governance.py` is the read-only, fail-closed current-routing
guard. It checks ADR 0010 authority and ADR 0009 supersession, the ordinary
Task 013-020 sequence, live Task 012B-018 status/dependency gates, and the
unnumbered explicitly authorized UI milestone across the README, project
context, roadmap, decisions index, and task contracts. Superseded ADR bodies
and completed-task report sections remain valid historical evidence and are
excluded from current alias scans. The command emits one deterministic JSON
line and never rewrites or normalizes a document.
The exact validation evidence and limitations are retained in
`evidence/backbone-governance-guard-v1/completion-report.md`.
