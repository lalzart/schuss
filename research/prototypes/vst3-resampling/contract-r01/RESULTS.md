# Tide Pit and Pamplist Fixed-Rate VST3 Resampling implementation results

> Status: Task 047 implementation, focused, adjacent, Schuss `current`, native
> target-build, receipt, and relocated-reproduction evidence passed. The
> repository-wide `compatibility` run completed with one inherited Task 043
> stale-count failure and no Task 047 failure; see GAP-010.

## Proposal and contract fingerprints

- Proposal: `research/proposals/tide-pit-pamplist-vst3-resampling.md`
- Proposal SHA-256:
  `064fb6fb4c9e74ee5285080940ed694d5b2136735c5211e8ed50454ac59b7e43`
- Implementation contract: `implementation-contract.json`
- Internal Core rate: exactly 48,000 Hz for both instruments
- Supported host rates: 32,000, 44,100, 48,000, 88,200, 96,000, 176,400,
  and 192,000 Hz
- Unsupported rates and non-bypass callbacks above 8,192 frames: exact silence

The ready bundle validator passed before implementation edits. It was not
re-run afterward because `source-equivalence.json` intentionally fingerprints
the preimplementation processor seams; postimplementation truth is held by the
source, signal, module, receipt, and reproduction evidence below.

## Environment

| Item | Observed identity |
|---|---|
| Host | macOS 15.6.1, arm64 |
| C/C++ | Apple clang 16.0.0 (`clang-1600.0.26.6`) |
| CMake | 4.4.2 |
| Python | 3.10.4 |
| JUCE source | authenticated JUCE 8.0.15 tree, 4,425 files, tree SHA-256 `ee764637fc4d1358d74f2797f8f059cbd8ff8878d663a28632de9737a11b2db7` |
| Pamplist source | `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, subtree `58917f3e2e46a30337cfb6292a3504845b1d5552` |

## Implemented boundary

One JUCE-independent `FixedRateStereoResampler` now owns the exact rational
host/source timeline and a causal 129-tap Kaiser-windowed sinc output
converter. It uses fixed storage, normalized phases, persistent history, and a
48 kHz bypass. Both VST3 processors retain their existing musical Core,
parameters, state schema, control maps, and instrument-owned render seams.

Tide Pit adds a bounded pending-event queue so a MIDI event received during a
high-rate callback that produces zero new 48 kHz frames is applied exactly
once at the next source frame. Pamplist maps host MIDI segment boundaries to
the same rational source timeline and renders only the required Core ranges.

## Commands and results

| Gate | Command or build | Result |
|---|---|---|
| Ready bundle | `validate_implementation_bundle.py ... --phase ready` before implementation | passed |
| Shared converter | configure/build plus `ctest --test-dir build/instrument-lab-task047 --output-on-failure` | 1/1 passed |
| Tide Pit focused and adjacent | complete Debug build and CTest in `build/tide-pit-vst3-task047-dev` | 10/10 passed |
| Pamplist focused and adjacent | complete Debug build and CTest in `build/pamplist-vst3-task047-dev` | 10/10 passed |
| Tide Pit Release VST3 cohort | model, processor, allocation, and actual-module tests in `build/tide-pit-vst3-task047-release` | 4/4 passed |
| Pamplist Release VST3 cohort | model, processor, allocation, and actual-module tests in `build/pamplist-vst3-task047-release` | 4/4 passed |
| Allocation | repeated processor callbacks at 48, 44.1, and 96 kHz | zero adapter-owned heap allocations for both processors |
| Actual modules | separate JUCE module host at 44.1, 48, and 96 kHz | both modules scanned, instantiated, reported latency, round-tripped state, created/destroyed editors, and emitted bounded nonzero signal |
| Tide Pit sanitizer | selected model and processor checks with ASan/UBSan and halt-on-error | 2/2 passed |
| Pamplist sanitizer | selected model and processor checks with ASan/UBSan | model passed; processor halt-on-error stopped at the authenticated upstream findings recorded under GAP-009; recoverable 2/2 run completed |
| Receipts | both `vst3/tests/build_vst3.py --check` paths | passed |
| Tide Pit copied root | `reproduce_vst3.py --juce-source ...` | 4/4 Release tests, arm64 slice, local seal, source/JUCE authentication, and no source-tree mutation passed |
| Pamplist copied root | `reproduce_vst3.py --juce-source ... --source-root ...` | 4/4 Release tests, arm64 slice, local seal, source/JUCE authentication, and no source-tree mutation passed |
| Schuss routine | `python3 tools/validation/run.py --profile current` | 9/9 checks passed in 69.913 seconds |
| Schuss compatibility | `python3 tools/validation/run.py --profile compatibility` | failed after 550.668 seconds: 486 tests ran with one failure and 24 skips; the unchanged bridge test expected Task 039's old count of five while inherited Task 043 authority returned six |

The two relocated closeout trees authenticated these hashes:

- Tide Pit consumer tree:
  `feb3738268b759bc27de8950c8f2e71336e518f38760e2e0dce1c854d570b08c`
- Pamplist consumer tree:
  `03295647b69e33387847abd97c5e4c715500d419dfd327c82ef2712e1cfe3458`
- Shared Instrument Lab support tree:
  `bc5336c3a3577396c30be167b88c4b386b1141baf426f79c3720f1929fccf363`

## Objective observations

| Host rate | Exact ratio, 48 kHz source/host | Reported host latency |
|---:|---:|---:|
| 32,000 | 3/2 | 44 frames |
| 44,100 | 160/147 | 60 frames |
| 48,000 | 1/1, exact bypass | 0 frames |
| 88,200 | 80/147 | 120 frames |
| 96,000 | 1/2 | 130 frames |
| 176,400 | 40/147 | 239 frames |
| 192,000 | 1/4 | 260 frames |

- Every declared rate produced finite, bounded, nonzero stereo output for both
  processors with no processor failure count.
- The 48 kHz lane retained the pre-existing exact direct-Core PCM, event,
  state, and fresh-twin comparisons.
- The shared converter produced identical 44.1 kHz samples across the frozen
  callback partitions. Tide Pit was likewise exact across 44.1 kHz partitions;
  Pamplist was exact across 96 kHz partitions, including mapped MIDI.
- The shared signal suite passed DC error at or below `2e-5`, 1 kHz gain within
  0.05 dB, 18 kHz gain within 0.35 dB, and 23 kHz rejection below -70 dB for
  48-to-44.1-kHz conversion. The deliberately unfiltered linear comparator
  remained at or above -40 dB at that stopband fixture and therefore failed the
  accepted alias threshold as intended.
- Impulse peaks matched the declared latency. Exact rational cumulative source
  progress and monotonic event mapping held across 1, 16, 64, 127, 128, 511,
  512, 513, 2,048, and 4,096-frame partitions.
- Tide Pit's zero-source-frame high-rate event fixture applied one manual
  mutation exactly once with zero bridge or processor event drops.
- Rate 48,001 Hz, invalid layouts, and 8,193-frame non-bypass callbacks rendered
  exact silence; the oversized path incremented the existing failure diagnostic.

## Authenticated uninstalled artifacts

| Module | Bundle tree SHA-256 | Binary SHA-256 | Input fingerprint SHA-256 |
|---|---|---|---|
| Tide Pit | `0b72c144d996c6dafc6bc244441d2a4b654139e4e31729de3d00d10d9ff81d46` | `ee3cedb0942871bfb59f2358bc6ce27f243f75419481c72083bc96ccc8df4d77` | `ffd8ede953c2aa3a044380979d14fd630eac64a2270154ca2fd77af8215eee4a` |
| Pamplist | `01df1f867798940d5da01a82d44a1a6fc0aa6ff03282cea222c0d867799c53a0` | `8eef66b740d8ad9e0362482fc8e80e75f3f54bbb42e22065a3a5dd460a3a2f2b` | `201f8bdef9f68e4f4c2c89b43ac4052ea77f50405b5e14563a9ca304563c530c` |

Both bundles remain under `build/`, use only the local ad-hoc build seal, and
were not copied into any plug-in directory.

## Corrections made during validation

1. The first compile exposed one unused lambda capture; the capture was removed
   before any frozen target-build or reproduction evidence.
2. The first broad VST3 CTest invocation reported registered adjacent tests as
   `Not Run` because their executables had not been built. All registered
   targets were then built and each complete 10-test Debug suite passed. This
   was build-target selection, not a processor failure.
3. The first Tide Pit deferred-event fixture sent Source (`CC40`) while checking
   the manual-mutation counter. The fixture was corrected to Mutate (`CC41`);
   no implementation code changed for that correction.
4. Pamplist's fail-fast processor sanitizer reproduced authenticated upstream
   signed-left-shift findings at `macro_voice_dsp.h:122` and `:123`. The source
   was not mutated. A recoverable sanitizer run completed both selected tests,
   and GAP-009 retains the limitation; this is not an undefined-behavior-clean
   claim for Pamplist.
5. The one frozen compatibility run exposed
   `test_instrument_list_crosses_the_closed_bridge_without_launching`, whose
   tracked assertion still expects five instruments. The inherited Task 043
   implementation selects audition-library v2 with six entries, and its exact
   Task 043 validator passed in `current`. A focused replay reproduced `5 != 6`.
   Task 047 changed neither the desktop bridge test nor the library authority,
   so the unrelated inherited work was preserved and GAP-010 records the
   repository-level failure.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | source/consumer, host-rate, timeline, capacity, and risk audit in the proposal and contract bundle | no listening inference |
| Proposal | passed | approved proposal SHA and ready bundle | approval does not prove implementation |
| Source | passed | exact source/JUCE authentication, shared converter tests, processor integration, receipt fingerprints | Pamplist upstream GAP-009 retained |
| Host structural | passed | actual arm64 VST3 scan/instantiate/state/editor/latency checks in the separate module host | not Ableton Live |
| Host signal | passed | seven-rate processor fixtures; actual modules at 44.1/48/96 kHz; exact bypass and partition tests | offline only |
| Target build | passed | authenticated uninstalled Release bundles, receipts, arm64 slices, local seals, copied-root reproduction | no distribution identity |
| Real-time | not run | none | deadlines, xruns, CPU, memory, and useful instance counts remain open |
| Connected device | not run | synthetic MIDI only | no physical controller or endpoint receipt |
| Listening | not run | none | converter and instrument sound not judged by ear |
| Production integration | not run | none | no installation, Ableton session, packaging, publication, or production claim |
