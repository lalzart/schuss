# Layerwell 0.2: Embedded Tide Pit and Pamplist Sampler implementation results

> Status: complete at the explicitly authorized source, host-structural,
> objective host-signal, and authenticated target-build boundary

## Proposal and contract fingerprints

- Proposal: `research/proposals/layerwell-r02.md`
- Pre-implementation ready proposal SHA-256:
  `6374480a5b07ca2cfe56008c29a775e693a80f2d0b863a99e46f330c4a0fa6b6`
- Proposal with completed implementation record SHA-256:
  `56d1ab8ab8575e4a6f59eabbe976db11986ab02cf9ae750ae5cfae88584efeb6`
- Implementation contract: `implementation-contract.json`

## Commands and results

Environment: Apple arm64; AppleClang 16.0.0.16000026; CMake 4.4.2; Python
3.10.4.

1. The Sonic Research Lab bundle validator passed in `ready` phase before the
   first Layerwell 0.2 Core/source/controller/JUCE edit and passed again after
   the completed implementation record was bound.
2. `python3 research/prototypes/layerwell/tests/verify_source_authorities.py`
   passed 13 exact repository files, the exact Tide Pit and Pamplist
   CMake/include/src trees, and configured Pamplist source revision
   `08d3e6e1e2b61230308c20a15ded58ffdaf4656c` / synthesis tree
   `58917f3e2e46a30337cfb6292a3504845b1d5552`.
3. `python3 research/prototypes/layerwell/tests/run_focused.py` passed all six
   Release tests and all six bounded ASan/UBSan tests. The exact authenticated
   Macro Voice target retains the GAP-008 `shift-base` exception described
   below; all other instrumentation remains active.
4. `python3 research/prototypes/layerwell/tests/run_source_regressions.py`
   configured both sources standalone and passed Tide Pit 6/6 plus Pamplist
   6/6 tests. Pamplist's revision 0.6 retained render/build receipts and both
   source prototype freshness checks also passed.
5. `python3 research/prototypes/layerwell/tests/render_evidence.py --reproduce`
   produced exact-identical WAV, event, panel, controller, and metrics
   artifacts at 16, 64, 128, and 512 frames. The subsequent `--check` passed.
6. `python3 research/prototypes/layerwell/tests/build_juce.py --reproduce
   --juce-source /Users/lanceship/Projects/schuss/build/cinderwheel-juce-trial/_deps/juce-src`
   authenticated the 4,425-file JUCE 8.0.15 tree, configured, compiled, and
   linked target `layerwell-instrument`, then wrote the retained receipt. The
   subsequent `--check` passed. The application was not launched.
7. `python3 tools/instrument_lab/validate_prototype.py --repo-root .
   --consumer-root research/prototypes/layerwell --check` passed the frozen
   revision 0.2 authority graph.
8. `python3 research/prototypes/layerwell/tests/reproduce_fresh_root.py` passed
   one copied-root configure/build and all six Layerwell tests while supplying
   the exact configured Pamplist source as an explicit runtime prerequisite.
9. `python3 tools/validation/run.py --profile current` passed the routine
   repository closure without invoking native, configured-source, hardware, or
   reproduction work.

The complete-diff source comparator over Tide Pit and Pamplist CMake/include/src
remained exactly
`6c40a091d78cbfcd113956ddd912cdec890ebea22daf4d9b4ee2628a89e29eb4`
from the pre-change audit through completion. Task 044 therefore changed no
source-project byte.

## Objective observations

- Production timeline: 144,000 stereo frames at exactly 48 kHz. Layer 1 records
  48,000 Tide Pit frames, accepts window `[4800, 43200)`, and plays a 38,400
  frame active cycle. Layer 2 then records exactly 38,400 Pamplist frames from
  phase zero and commits at frame 124,800.
- Final accepted state: two capture commits, zero capture aborts, two accepted
  trim-bound updates, zero dropped events, zero playback-invariant faults, and
  49,152,000 fixed sample-storage bytes.
- Signal ceiling: 288,000/288,000 samples finite; peak absolute
  `0.0639972910284996`; RMS `0.016809778146076072`; no limiter activation.
- Production WAV SHA-256:
  `69f6fd2ff5055c9ac51f876a42caa74afec01e91b4fcdd6204a73d71f9f272c4`.
- Panel trace SHA-256:
  `15eb7a2af06a9a6c9bd4082b7198fb382616df73cc83f33e06e2befba23be6e8`.
- Synthetic controller trace SHA-256:
  `a5e90a9571e5c11ee3117bc2e11959fb260bc9f10d4171904193cf415822d1be`.
- The otherwise identical untrimmed comparator WAV SHA-256 is
  `fdc61c5d29a057be2f45e0a2a30a502932f986e1670b156bdf6d4d7dace470ea`;
  it differs from production as required.
- Authenticated unlaunched app binary: 8,583,784 bytes, SHA-256
  `ffdcecc3d9dd8115a34f9123e1afb3ca65fc640ca8d5f04b1ca9fe5dddeba618`.

No subjective audition was performed. These observations do not establish
seam quality, source identity by ear, controller feel, or callback deadlines.

## Corrections made during validation

1. The first JUCE link exposed a missing parent link to Tide Pit's exact UI
   model. Adding `tide_pit_ui_model` to the Layerwell target corrected only the
   passive panel dependency; the app target was rebuilt and reauthenticated.
2. The first sanitizer build exposed that the source-link test executable did
   not inherit sanitizer runtime link flags from instrumented static
   libraries. The parent target now receives the same sanitizer helper.
3. The next sanitizer run reached an inherited configured-source signed
   negative left shift in `macro_voice_dsp.h`. Source bytes remain exact;
   Layerwell excludes only Clang `shift-base` instrumentation for that one
   source-derived target and records the unresolved source correction as
   GAP-008. The affected sanitizer closure then passed and the final complete
   focused closure was rerun.
4. The original revision 0.1 render evidence helper still constructed its
   callback-edge comparator. Revision 0.2 now retains the frozen experiment's
   direct untrimmed comparator and binds both WAV hashes.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | available | exact local source/public-model inspection plus revision 0.1 retained evidence | no new external product or cultural claim |
| Proposal | passed | approved ready proposal and implementation bundle | authorization is bounded to revision 0.2 |
| Source | passed | 13 file authorities, two public source trees, configured Pamplist revision/tree/files, unchanged-diff comparator | GAP-008 requires an upstream source revision before a broader safety claim |
| Host structural | passed | 6/6 Release, 6/6 bounded sanitizer, exhaustive source-panel/trim/controller tests, both 6/6 standalone source suites | no launched GUI or live callback |
| Host signal | passed | exact 16/64/128/512 artifacts, finite/bounded metrics, untrimmed comparator divergence | objective output only; no listening |
| Target build | passed | authenticated 8,583,784-byte `Layerwell.app` executable and relocated Core/test build | app unlaunched; endpoints closed |
| Real-time | deferred | none | callback deadline and xrun measurements required |
| Connected device | deferred | synthetic regular Launch Control 3 protocol only | physical enumeration, receipt, feedback, and reconnect required |
| Listening | deferred | none | source identity, trim seam, and layered result require audition |
| Production integration | deferred | noncanonical prototype only | identity, provider/runtime, persistence, packaging, licensing, and release review required |
