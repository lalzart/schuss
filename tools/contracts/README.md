# Contract tools

These tools validate, generate, or execute exact Schuss contract closures.
Read-only checks emit deterministic summaries and never access hardware.

## Validation profiles

```bash
python3 tools/validation/run.py --profile current
python3 tools/validation/run.py --profile compatibility
python3 tools/validation/run.py --profile configured-sources
python3 tools/validation/run.py --profile native
python3 tools/validation/run.py --profile reproduction
python3 tools/validation/run.py --profile release
```

The manifest at `tools/validation/manifest-v1.json` owns the atomic checks,
cost classes, prerequisites, and profile composition. Profile expansion is
deduplicated before execution. New ordinary tests default to `current`;
native, configured-source, and reproduction methods must be gated and listed
exactly once.

Use `--list` to inspect all IDs, `--plan` to see an expansion without running
it, and repeat `--only CHECK_ID` to select only affected atomic checks. An
atomic selection runs at its declared cost, including native or reproduction
work, and includes any declared preflight dependencies. Missing file/tool
prerequisites and selected authenticated preflight commands are resolved before
ordinary selected work starts. Explicit unit-test skips and unavailable
preflights are incomplete rather than passing. Checks stop on the first failure
by default; `--keep-going` is for deliberate audits and never bypasses a failed
preflight.

`current` validates the newest semantic closure and live governance without
replaying every completed task. `compatibility` is the ordinary historical
contract suite and is appropriate when shared record loading, schema rules,
dispatcher/CLI behavior, or another historical boundary changes. The raw
equivalent remains available for diagnosis:

```bash
python3 -m unittest discover -s tools/contracts/tests -p 'test_*.py'
```

Routine `current` validation skips explicitly gated work. Raw compatibility
discovery may still use small subprocess or temporary-directory tests when
that boundary is the behavior under test, but it does not run the listed native
build/render or copied-root reproduction matrices.

Configured source checks require the ignored machine-local mapping
`catalog/sources.local.yml`. Ordinary discovery reports named skips when it is
absent. Explicit `configured-sources` validation exits 2 with
`MISSING_CONFIGURED_SOURCE_PREREQUISITE`; this is not a pass. The compatibility
wrapper remains:

```bash
python3 tools/contracts/validate_task024_025_configured_sources.py
```

## Validation cadence

Choose checks by impact rather than treating every task ending as a release:

| Stage | Purpose | Typical invocation |
| --- | --- | --- |
| Focused | Exercise the implementation currently changing | `python3 -m unittest tools.contracts.tests.test_taskNNN_feature` |
| Adjacent regression | Protect exact earlier operations, records, or presentation bytes affected by the change | Run only the named neighboring test modules from the task contract |
| Current | Validate the newest closure and live governance | `python3 tools/validation/run.py --profile current` |
| Compatibility | Protect shared historical behavior when it can be affected | `python3 tools/validation/run.py --profile compatibility` |
| Native/configured/reproduction | Prove the explicitly changed external or expensive boundary once | Select the corresponding profile after freeze |
| Release | Deduplicate current, compatibility, native, and reproduction | `python3 tools/validation/run.py --profile release` |

Add `--profile configured-sources` separately when authenticated source inputs
are affected. It is deliberately not hidden inside every release run.

Before an expensive profile, review the complete diff, freshness checks,
negative cases, and acceptance matrix as the implementation freeze. If it
fails, iterate with the affected focused tests and rerun that broad profile
once after the correction. In standalone evidence runners, `--check` means
cheap retained-evidence verification. Fresh processes, copied roots,
compilation, or rendering use an explicit `--reproduce` mode or the
reproduction/native profiles.

Custom validation manifests are inspection-only and may be used with
`--validate-manifest`, `--list`, or `--plan`; execution always uses the checked
repository manifest.

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
