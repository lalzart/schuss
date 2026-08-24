# Layerwell Desktop Meta-Instrument implementation results

> Status: complete for the explicitly authorized revision 0.1 evidence boundary

Passing structural, synthetic, or target-build evidence does not establish app
launch, real-time audio, physical controller behavior, listening quality,
distribution readiness, or production integration.

## Frozen proposal and readiness gate

- Approved proposal:
  `research/proposals/layerwell.md`
  (`631084a81e5a012a6029f2a4a072772a6adae07e2e1156d92d90ceb567ea1b21`).
- Ready contract:
  `research/prototypes/layerwell/contract/implementation-contract.json`.
- The Sonic Research Lab structure and ready validators passed before the first
  Layerwell DSP source edit. The proposal fingerprint remains unchanged.
- Work type: `new-design`; source equivalence for the whole instrument is not
  applicable. Both resident source instruments retain their own exact source
  authorities and evidence.

## Implemented artifact

- Portable C++17 `layerwell_core` at exactly 48 kHz with 16-frame source
  quantum, outer blocks through 512 frames, and capacity for 128 semantic events
  per request.
- Four prepare-time stereo float stores: three committed layer owners and one
  staging owner, 1,536,000 frames per channel, 49,152,000 sample bytes total.
- Immediate first capture, stop-exclusive first-loop establishment, phase-zero
  one-cycle later capture, provisional owner swap, cancellation, failure
  preservation, three layer levels/pans/mutes, source monitor, master level,
  seam bridge, finite recovery, and output limiting diagnostics.
- Exact resident Tide Pit Gills 0.1 and Schuss Generative Drums 0.6 public Cores.
  Only the selected source advances; each source control terminates at its
  existing descriptor and reducer.
- Pure regular Launch Control 3 DAW-mode protocol adapter with Page source
  selection, Track layer selection, Control source mapping, Mixer layer/capture
  mapping, Shift-clear, lifecycle messages, and accepted-snapshot feedback.
- Restrained JUCE 8.0.15 standalone UI with explicit audio start and MIDI
  endpoint selection. The app was built but not launched.

## Commands and observed results

Environment: Apple clang 16.0.0 arm64, CMake 4.4.2, Python 3.10.4, macOS host.

1. `python3 research/prototypes/layerwell/tests/verify_source_authorities.py`
   passed 10 exact authority fingerprints and all composition guards.
2. `python3 research/prototypes/layerwell/tests/run_focused.py` passed six
   Release tests and the same six Debug ASan/UBSan tests. The allocation fixture
   observed zero allocations across 100 repeated processing calls.
3. `python3 research/prototypes/layerwell/tests/render_evidence.py --check`
   authenticated the retained production and falsifying-comparator artifacts.
4. `python3 research/prototypes/layerwell/tests/run_source_regressions.py`
   passed Tide Pit's 6/6 standalone tests with symbol isolation off and
   Generative Drums' 8/8 standalone tests with its normal source closure.
5. `python3 research/prototypes/layerwell/tests/build_juce.py --check` passed
   the authenticated target-build receipt for `layerwell-instrument`.
6. `python3 tools/instrument_lab/validate_prototype.py --repo-root .
   --consumer-root research/prototypes/layerwell --check` passed the complete
   noncanonical index, topology, promotion-needs, and handoff closure.
7. `python3 research/prototypes/layerwell/tests/reproduce_fresh_root.py` passed
   the isolated relocated Core build and all six Layerwell tests.
8. `python3 tools/validation/run.py --profile current` passed the routine Schuss
   closure after implementation and documentation freeze.

## Objective host-signal observations

The frozen 144,000-frame timeline produced byte-identical WAV, accepted-state,
controller, and metric artifacts at outer blocks 16, 64, 128, and 512.

| Observation | Value |
|---|---:|
| Frames / finite samples | 144,000 / 288,000 |
| Peak absolute | 0.12469605356454849 |
| RMS | 0.015420317764667148 |
| Reported DC mean | 0.005545143407787191 |
| Limited samples | 0 |
| Capture commits / aborts | 2 / 0 |
| Accepted / dropped events | 5 / 0 |
| Sample storage | 49,152,000 bytes |
| Sample-exact WAV SHA-256 | `296ed46aaff493b6cbdb0d37c6ef3979607621579f0a9f334d053384afae0237` |
| Callback-edge 512 WAV SHA-256 | `4ec84ee5ecf3b636c2b29adf89be6271526ede936a049a8a9e1109263c01ebab` |

The deliberately naive comparator quantized every event to the next outer
callback edge and diverged at 512 frames. That negative control is retained as
`callback-edge-512.wav` plus a hash-binding JSON record; it proves the
production partition equality is not an artifact of an insensitive fixture.

Focused Core fixtures additionally passed:

- exact 24,000-frame minimum capture and exact 23,999-frame rejection;
- later-capture boundary start, full-cycle commit, waiting cancellation,
  recording cancellation, overflow abort, and unsupported-shape preservation;
- committed-buffer byte preservation through every provisional failure tested;
- all three occupied layers with distinct sample-store owners, shared session
  phase, independent level/pan/mute state, and last-layer clear returning to
  no-loop state;
- source reducer termination, inactive-source zero advance, fixed-size mailbox
  coherence, malformed protocol input, reconnect/resync, and cleanup messages;
- finite output within `[-1, 1]` and zero processing allocations.

## Authenticated target build

- JUCE source tree: 4,425 files, authenticated extracted-tree manifest
  `ee764637fc4d1358d74f2797f8f059cbd8ff8878d663a28632de9737a11b2db7`.
- Product: `Layerwell.app`, target `layerwell-instrument`.
- Executable bytes: 8,415,496.
- Executable SHA-256:
  `89d0858cf5dd3d9dfdef4fcdb53f7ef6124a7fea92435e2e5d654dc4285dccdf`.
- Build-input fingerprint:
  `4d58f3cca0f9cf612b7cb2db398f0a03b5561d6b6b8e62317ad342bb5608ff95`.
- Receipt explicitly records `app_launched=false`,
  `audio_endpoint_opened=false`, and `midi_endpoint_opened=false`.

## Corrections made during validation

1. The first optimized combined-source process terminated while each source
   passed alone. Bisection identified overlapping global `braids` and `stmlib`
   namespaces in the two exact Mutable closures. Layerwell now privately
   prefixes only Tide Pit's internal Mutable namespaces in the parent build.
   No upstream byte, public source API, mapping, or standalone default changed;
   the combined link/process gate and both standalone suites pass.
2. An early composition edit added guards and test options to the source
   projects, which changed Tide Pit's frozen Task 036 compile-policy hash; the
   first Schuss `current` run correctly rejected that drift.
   Layerwell now owns the entire composition seam: both source CMake files are
   restored byte-for-byte, Tide Pit supplies the sole Instrument Lab authority,
   and the parent recreates only the Generative Drums public Core target from
   its exact declared source list. Layerwell selects only its own test names;
   both unchanged standalone suites run independently.
3. The first sanitizer build linked instrumented libraries into an
   uninstrumented renderer. Adding the same sanitizer helper to the renderer
   fixed the runtime linkage. The next attempt used a leak-detection option that
   Apple ASan explicitly does not support; the final fail-fast ASan/UBSan run
   omits that unsupported option and passes all six tests.
4. The first relocated-root check copied a generated Python bytecode cache and
   correctly rejected it as consumer drift. Removing that non-source cache
   restored a clean relocation input; the fresh-root build and all six tests
   then passed.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | proposal sources and official LC3 protocol references | no novelty claim |
| Proposal | passed before implementation | frozen proposal plus ready v2 contract | approval covers revision 0.1 only |
| Source | passed | 10 exact authorities, retained notices, unchanged upstream bytes | distribution review deferred |
| Host structural | passed | Release plus ASan/UBSan 6/6; source regressions 6/6 and 8/8; Instrument Lab and Schuss current | no live callback deadlines |
| Host signal | passed | partition-identical retained render, divergent negative comparator, and relocated reproduction | synthetic offline signal only |
| Target build | passed | authenticated `Layerwell.app` executable and receipt | app not launched or visually inspected |
| Real-time | not run | none | explicit launch and audio-device measurement required |
| Connected device | not run | synthetic protocol trace only | physical regular LC3 receipt/feedback required |
| Listening | not run | receipt says false | documented audition required |
| Production integration | not run | noncanonical prototype only | separate governance, packaging, and release work required |
