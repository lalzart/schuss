# Task 017 completion report

Task 017 is complete for the exact `schuss-record-set-000011@1` closure. It
adds a balanced reviewed core of twelve families and exactly two immutable,
non-UI reference instruments without claiming new direct DSP/runtime behavior
that the retained evidence does not establish.

## Selection and semantic records

The immutable selection packet retains the inventory-audit baseline of 3,602
resolved observations and 348 complete graphs. Complete-graph frequency is a
prioritization signal only: lower-frequency musical building blocks were
selected over higher-frequency string, GPIO, display, editor-control, MIDI,
and ambiguous-overload candidates where that produced the requested balanced
core. Provenance remains a facet and is never a primary function.

The twelve selected families are:

| Function | Families |
| --- | --- |
| Timing/sequencing | Clocked Logic Toggle; Pseudo-Euclidean Gate Sequencer |
| Sound sources/percussion | Band-limited Saw; Band-limited PWM; Struck Drum; Struck Bell; Dual Percussion Voice compound |
| Modulation/control | Attack-Decay Envelope; Exponential Control Smoother |
| Shaping/dynamics | Audio Soft Clipper; Interpolated Audio VCA |
| Delay/reverb | Rings-derived Stereo Reverb |

Each family has an exact component contract, candidate and promoted binding,
target/backend eligibility, compatibility-evidence record, catalog entry, and
explicit unresolved facts. Eleven source-backed families retain the exact
frozen observation, source hash, seam map, object-metadata license observation,
and observed dependencies. Random UUID-shaped source identifiers are retained
only through authenticated SHA-256 closure fields. The Schuss-authored compound
has no inferred license declaration.

## Headless reference instruments

- `schuss-instrument-000003@1` uses the transparent Dual Percussion Voice,
  Square LFO, and stereo output. Its inspectable internal graph combines a
  pseudo-Euclidean sequencer, toggle, drum, bell, attack-decay envelope,
  crossfader, and VCA. It exercises state, fanout, modulation, parameter
  promotion, and compound reuse.
- `schuss-instrument-000004@1` combines saw and PWM voices, exact audio soft
  clipping, Rings reverb, smoothing, crossfade, VCA, and stereo output. It
  exercises source fanout, stereo effects, modulation, and two graph parameter
  mappings.

Both instruments have no actions or displays and use the same client-neutral
graph/instrument/CLI operations as earlier work.

## Direct and planning boundary

The Task 017 backend revision adds only `transparent-compound` to the accepted
Task 016 `native-cpp` realization form. All seven Task 016 native bindings are
carried forward exactly for that backend. No Java, `.axp`, legacy-object call,
hidden adapter, ambient discovery, or fallback was introduced.

The eleven newly reviewed legacy-backed families have `not-evaluated` direct
eligibility with `DIRECT_OPERATION_UNSUPPORTED`; source/seam review is not
treated as behavioral equivalence. Therefore the effects instrument returns
stable `COMPILER_BINDING_UNSUPPORTED` diagnostics. The percussion wrapper is
structurally supported, but its internal reviewed legacy bindings return stable
`COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED` diagnostics before lowering.
No exact handler exists for either unsupported Task 017 request, so direct
execution was not attempted.

## Determinism and preservation

The generated successor manifest has byte SHA-256
`72ca0d857f83eb2ca3c1c8583c8eb32918d82846882de4afe3eadefb8c769c69` and
content hash
`sha256:1db0091c378d38ed7050a46ea1457a74c40b4301af655dd9d045974572fc5db8`.
Two fresh CLI processes produced identical bytes for catalog search/inspection,
both graph inspections, and both build plans. Retained evidence includes those
six canonical operation results, a validation summary, and a preservation
manifest.

The successor includes every Task 016 parent schema and record member without
changing its tuple or byte hash. The preservation gate also authenticates the
accepted Task 011C completion manifest, Tasks 013-015 validation summaries,
Task 016 semantic goldens and validation summary, and the Task 016 exact record
set.

The dedicated Task 017 suite passes all 10 tests. The affected compatibility
slice ran 92 tests: 90 passed and the only two failures were already-documented
stale legacy golden assertions. Ordinary repository discovery ran 255 tests:
249 passed and retained the exact six inherited Task 016 baseline failures—five
stale expected-hash/golden assertions in Tasks 008-011A and one absent ignored
Task 009 content-addressed prerequisite. No Task 017 test failed. Repairing
those unrelated historical gates is not silently folded into this task, so
repository-wide green status remains an explicit proof gap.

## Evidence boundary

Levels 1-2 pass: schema/identity/portability and component/graph resolution.
Levels 3-8 are explicitly `not-run`: backend lowering, source generation, ARM
compile/link, connected-device execution, real-time/resource measurement, and
audible/listening validation. UI, hardware, and publication evidence are also
absent. No device action, upload, flash, SD-card write, stage, commit, push, or
publication occurred.

## Reproduction

```bash
python3 tools/contracts/generate_task017_records.py --check
python3 -m unittest tools.contracts.tests.test_task017_curated_core
python3 tools/contracts/run_task017.py --check
python3 tools/contracts/validate_task017_contract.py
python3 tools/contracts/validate_task017.py
python3 tools/contracts/validate_backbone_governance.py
```
