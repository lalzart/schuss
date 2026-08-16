# Gills panel and runtime contracts

Task 018 promotes the original minimal Gills model into one authenticated,
complete panel description and one exact mapped runtime closure. These
contracts preserve the existing Schuss layer boundaries:

```text
physical Gills slot
  -> device profile slot
  -> instrument facet
  -> graph facet
  -> exact compute target / backend / firmware runtime
```

A device slot never maps directly to a graph facet. The device profile owns
physical capabilities, an instrument owns the performance mapping, the graph
owns DSP behavior, and the runtime realization binds device slots to an exact
target/backend/runtime closure.

## Exact accepted closure

The accepted successor is `schuss-record-set-000012@1`. Its Task 018 records
are:

- `schuss-device-profile-000001@2`: complete reviewed Gills device profile;
- `schuss-panel-evidence-000001@1`: pinned source packet and slot census;
- `schuss-instrument-000002@2`: mapped executable successor of the Task 016
  instrument;
- `schuss-instrument-000003@2` and `schuss-instrument-000004@2`: full-panel
  successors of the two Task 017 references;
- `schuss-runtime-realization-000001@1`: exact mapped direct runtime;
- `schuss-runtime-realization-000002@1`: exact unsupported runtime boundary
  for the two Task 017 successors;
- `schuss-coverage-report-000001@1` through
  `schuss-coverage-report-000003@1`: total slot/facet coverage;
- `schuss-build-request-000002@4`, `schuss-build-request-000003@2`, and
  `schuss-build-request-000004@2`: exact successor requests.

Every reference includes ID, revision, and content hash. Filesystem order,
display names, mutable source paths, and implicit latest-revision selection are
not resolution mechanisms.

## Exact Task 021 corrective closure

ADR 0013 preserves the complete Task 018 closure above and adds
`schuss-record-set-000013@1`. The corrected exact path is:

- `schuss-instrument-000002@3` and `schuss-coverage-report-000001@2`:
  mechanical exact-identity successors with unchanged facets and mappings;
- `schuss-build-request-000002@5`;
- `schuss-build-handler-000003@2`; and
- `schuss-runtime-realization-000001@2`.

The mechanical instrument/coverage successors prevent the instrument-only
inspection operation from having to choose implicitly between runtime
revisions. `schuss-instrument-000002@2` still resolves exactly to the Task 018
runtime, while revision 3 resolves exactly to the Task 021 runtime.

## Panel evidence and census

The evidence packet pins the Gills hardware repository at commit
`280503036aee95e6c6ef91a1f1357443f4768faa` and the Gills object sources at
commit `3e236e503f490e2bb93187b9cbaf06781dd88b8b`. Each source entry records its
portable repository URL, commit, path, byte hash, observed license statement,
and limitation. Repository license text is recorded separately and is not
inferred as a per-file declaration.

The reviewed device contains 63 distinct slots:

| Slot kind | Count |
| --- | ---: |
| Input controls | 19 |
| Derived gestures | 16 |
| Feedback channels | 6 |
| Display capabilities | 2 |
| Physical I/O | 20 |

The evidence packet has one entry for every slot. Optional CV/PDM population,
the physical transfer of the two analog volume controls, exact dual-LED hues,
Core-owned connector revision, and connected OLED behavior remain explicit
unresolved facts. Static source and CAD inspection do not prove a particular
assembled board.

## Mapping semantics

The executable reference uses four explicit performance paths:

1. Pot 1 maps linearly from raw ADC `0..4095` to normalized Q27, is smoothed by
   signed error shift-right 3 per control update, uses soft pickup, reaches the
   instrument Blend parameter, and then reaches `graph-facet-000001`.
2. Button 1 press is debounced and triggers the instrument Reset Blend action.
3. Pickup-armed instrument state drives LED 1 on `GPIOG:6`.
4. The instrument Blend display drives the SH1106 text surface at I2C address
   `0x3c`.

The runtime executes one control update per 16-sample block at 48 kHz. Button
press/release recognition requires four identical updates; hold produces one
event after 1,500 debounced updates. The encoder follows the reviewed falling
edge-A/direction-from-B algorithm every four control updates. The OLED uses a
four-line text buffer and a 32 ms refresh thread.

Task 018 allocated the two-byte OLED command payload on the OLED thread stack
in CCM. The Task 021 successor instead allocates `SchussOledCommand[2]` in
`.sram2`, which is visible to the DMA-backed I2C path. It does not reuse
`SchussOledTx`: the 129-byte page buffer remains independent and byte zero is
set to the `0x40` data-control value before every page transfer.

Every other accepted slot and every public instrument facet is present in a
coverage report as mapped, intentionally unused with rationale, or unresolved.
Absence is never coverage. The generated C++ reads and smooths all ten pots,
recognizes all button and encoder gestures, initializes all six LED channels,
and binds both OLED capabilities; the exact executable instrument consumes
only its reviewed mapping subset.

## Shared operations and compiler boundary

`gills.inspect` is operation request/result version 6. It accepts one exact
instrument reference and returns the exact device, instrument, evidence
packet, coverage report, runtime realization, build support, and validation
summary. It uses the same control-plane dispatcher as record validation,
compiler planning, and build execution.

The compiler front half includes panel evidence, coverage, and runtime
realizations in its immutable input closure. Stage 1 requires exactly one
runtime realization for the selected build request. The mapped handler then
checks the exact request, instrument, device, evidence, coverage, target,
backend, firmware runtime, and handler references before generation. There is
no ambient source discovery or fallback.

The mapped frontend reuses the Task 016 normalized DSP schedule and semantic
goldens byte-for-byte as semantic values. It adds separate panel-runtime,
mapping-source-map, host-vector, coverage, and runtime-realization artifacts;
the panel code does not introduce new DSP operations.

## Task 018 evidence boundary

The exact mapped executable builds twice in fresh roots and fresh processes
through deterministic local ARM compile/link. Evidence levels 1-5 pass:
schema/identity, graph/planning, lowering, artifact generation, and ARM
compile/link. Levels 6-8 remain `not-run`: no connected device, control-panel
operation, real-time/resource measurement, or audible/listening validation was
performed.

## Task 021 evidence boundary

Task 021 repeats the corrected build twice in fresh roots and processes.
Generated C++ SHA-256 is
`e69155998e91c7c3af6b6e0aaebbac965f4cf822b67382f25de5776453af2928`;
target ELF SHA-256 is
`4f9bd68f5f71fc9d5bf70bd88988e7e20ff980fb46a886beff52f60c968874de`.
Build execution itself still reports levels 1-5 passed and levels 6-8
`not-run`.

A separate `schuss-evidence-claim-000037@1` records level 6 for the exact
corrected instrument and target executable. On Ksoloti Core USB serial
`003D00363532511735393330`, firmware `1.1.0.0` CRC `5021D42A`, the derived
6,440-byte binary was uploaded to volatile RAM at `0x20011000`, read back
byte-for-byte, acknowledged start, and passed three responsiveness probes over
six seconds with flags zero. The user confirmed the display was upright and
showed `SCHUSS`, `BLEND`, `PICKUP`, and `TASK018`.

That claim does not establish a complete control sweep, audio behavior,
real-time margin, endurance, persistence, electrical safety, or release
readiness. Levels 7 and 8 remain `not-run`; no firmware flash or SD-card write
was performed.

The percussion successor continues to return
`COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED`; the effects successor
continues to return `COMPILER_BINDING_UNSUPPORTED`. These stable diagnostics
have no fallback and do not weaken the successful mapped reference.

## Reproduction

```bash
python3 tools/contracts/generate_task018_records.py --check
python3 -m unittest tools.contracts.tests.test_task018_gills_mapping
python3 tools/contracts/run_task018.py --check
python3 tools/contracts/validate_task018.py
python3 tools/contracts/validate_task018_contract.py
python3 tools/contracts/generate_task021_records.py --check
python3 -m unittest tools.contracts.tests.test_task021_dma_safe_oled
python3 tools/contracts/run_task021.py --check
python3 tools/contracts/validate_task021.py
python3 tools/contracts/validate_task021_contract.py
python3 tools/contracts/validate_backbone_governance.py
```

These checks perform local validation and authenticated ARM compilation only.
They do not upload, flash, write an SD card, or access connected hardware.
