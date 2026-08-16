# Task 018 completion report

Task 018 is complete for exact `schuss-record-set-000012@1`. It replaces the
minimal Gills description with an authenticated 63-slot panel census, total
instrument and device coverage, explicit runtime realization, shared
inspection/planning/execution, and one mapped reference that reaches
deterministic local ARM compile/link evidence level 5.

## Evidence packet and semantic successors

The panel packet contains 24 portable sources. It pins the official Gills
hardware repository at commit
`280503036aee95e6c6ef91a1f1357443f4768faa` and the official Gills object
sources at commit `3e236e503f490e2bb93187b9cbaf06781dd88b8b`.
Every source entry carries repository URL, commit, path, byte hash, authority,
license observation, and limitation. The hardware repository license and
objects-repository license are separate evidence entries; neither is inferred
as a per-file declaration.

The device successor accounts for 19 input controls, 16 gestures, six LED
channels, two capabilities of one OLED, and 20 physical-I/O slots. Every one
of the 63 slots has one evidence-census entry. Optional assembly population,
analog volume transfer, exact dual-LED hue, independently owned Core connector
revision, and connected OLED behavior remain explicit unresolved facts.

Three immutable instrument successors retain their Task 016/017 graph
identities while referencing the complete device. Each has a total coverage
report: every physical slot and every public parameter, action, display, or
state facet is mapped, intentionally unused with rationale, or unresolved.
Absence is never counted as coverage.

## Mapped executable reference

`schuss-instrument-000002@2` provides four explicit chains:

- Gills pot 1 to the instrument Blend parameter to
  `graph-facet-000001`;
- Gills button 1 press to the instrument Reset Blend action;
- instrument Pickup Armed state to LED 1 on `GPIOG:6`; and
- instrument Blend display to the SH1106 text surface on `I2CD1` at `0x3c`.

The runtime fixes the ADC-to-Q27 transform, signed shift-right-3 smoothing,
soft crossing pickup, four-update debounce, 1,500-update hold, reviewed
encoder scan/direction behavior, LED update, and 32 ms OLED refresh policies.
Deterministic host vectors cover all pot endpoints, smoothing, a complete
pickup crossing, press/hold/release, both encoder directions, feedback, and
display text. A focused vector caught and closed an initial-sample pickup bug:
crossing detection now begins only after one real physical sample.

The mapped frontend reuses the accepted Task 016 DSP schedule and semantic
goldens without adding DSP behavior. Panel runtime, mapping origins, host
vectors, coverage, and runtime realization are separate artifacts. The exact
handler is `schuss-build-handler-000003@1`; it rejects any other request,
instrument, device, runtime, coverage, target, backend, firmware runtime, or
handler reference before output creation.

## Planning results

All three exact successors validate and inspect successfully. Their compiler
outcomes remain truthful and stable:

| Instrument | Exact request | Plan outcome | Diagnostic |
| --- | --- | --- | --- |
| Mapped Task 016 successor | `schuss-build-request-000002@4` | `success` | none |
| Percussion successor | `schuss-build-request-000003@2` | `invalid` | `COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED` |
| Effects successor | `schuss-build-request-000004@2` | `unsupported` | `COMPILER_BINDING_UNSUPPORTED` |

The latter two have no fallback and do not enter backend execution.

## Determinism and retained artifacts

Two fresh roots in two fresh Python processes produced byte-identical record
validation, all three inspections, all three plans and diagnostics, the
portable build-execution result, and all 16 generated artifacts. The exact
manifest has byte SHA-256
`d00a3dd4f26b1fb5dcc6d1df2f0b1aa965ccbf9a1fdb9fd3420a7a3396b3d0a4`
and semantic content hash
`sha256:b756e7def9fa459f5c97bfd5ee5b517b78a6e7bb38f15581335108406ec4fd67`.

Key retained artifact hashes are:

| Artifact | SHA-256 |
| --- | --- |
| Task 016 semantic goldens | `105cb9bcbc544671f88a839310cba2f40c6651e38f83b4e171ee7582a29d83e0` |
| Mapped generated C++ | `fb079c9e88988d5b30143bde5aca2c916f9425b798091d29bd781ccc95ec9a8a` |
| ARM object | `f276c2d48ec97feef826a4810029cf79776f3f028f6f2d1e51caf41c9c498e04` |
| ARM target executable | `dc48bba98db7858a6477ce9733118d854248f8fbe4b4558faf33bea97deda238` |

Every Task 017 parent schema and record member remains present with its prior
portable path and byte hash. The Task 013-017 regression slice passed all 65
tests. The Task 018 focused suite passed all nine tests, including four
negative fixtures and exact product-CLI handler execution. The governance
suite passed all five tests after advancing current routing to “Task 018
complete; no next task active.”

The repository-wide contract run executed 265 tests. It had 264 passes and one
pre-existing stale Task 011A help/completion/human/JSON golden assertion; the
current CLI help and completion bytes were not changed by Task 018. The exact
affected Task 008/010 compatibility assertions pass, as do Task 011C and Tasks
013-017. The stale historical golden remains an explicit repository-wide proof
gap rather than being silently rewritten here.

## Evidence boundary

Evidence levels 1-5 pass: schema/identity and provenance, graph/compiler
planning, mapped backend lowering, deterministic artifact generation, and
authenticated local ARM compile/link. Levels 6-8 remain `not-run`:
connected-device/control-panel execution, real-time/resource measurement, and
audible/listening validation were not authorized or performed.

Static KiCad/source inspection and ARM compilation do not prove assembly,
electrical behavior, OLED operation, real-time safety, or sound. No upload,
flash, SD-card write, connected-hardware action, stage, commit, push, or
publication occurred.

## Reproduction

```bash
python3 tools/contracts/generate_task018_records.py --check
python3 -m unittest tools.contracts.tests.test_task018_gills_mapping
python3 tools/contracts/run_task018.py --check
python3 tools/contracts/validate_task018.py
python3 tools/contracts/validate_task018_contract.py
python3 tools/contracts/validate_backbone_governance.py
```
