# Murmur Map 0.1 implementation results

> Status: complete for the authorized noncanonical source, host-structural,
> host-signal, and target-build boundary

Passing these levels does not establish a launched app, live audio deadline,
physical Launch Control 3 behavior, listening quality, distribution readiness,
or production integration.

## Frozen proposal and readiness gate

- Approved proposal:
  `research/proposals/modular-generative-juce-instrument-study.md`
  (`65180864c42996a3e7a68de0b7356522329b25043e3ef5721e7e49fd3d49926f`).
- Ready implementation contract:
  `implementation-contract.json`
  (`31e408846cc14d22a973decccc6aa6eb238326b0cb21cb31fa397afe352637be`).
- Frozen experiment:
  `experiment.json`
  (`3b1bc8993f04b0650468fd120d6effc69c7f8cc223540c0036d52ec9a5042834`).
- Exact Launch Control 3 map:
  `control-map.json`
  (`b4bfd6692895f35dadf78ac3acf478552b074cbbe9972b8315a3d1158f9a9b15`).
- The proposal fingerprint stayed unchanged after approval. Work remained in
  the `new-design` lane and did not allocate a canonical record or provider.

## Implemented artifact

- Portable C++17 `murmur_map_core` at exactly 48 kHz with outer blocks through
  512 frames, three fixed voices, two source samples per output frame, and
  fixed capacities of eight waypoints, 32 route slots, and 64 semantic events
  per block.
- Four frozen initial waypoints with three lane states each. Map motion uses a
  raised-cosine edge, normalized radial-basis scene weights, logarithmic decay
  interpolation, and a fixed 128-frame continuous-parameter slew.
- A seeded route stream with exact two-draw fresh-choice accounting, separated
  lane streams, locality temperature, HOME return, cyclic destination memory,
  probabilistic erosion, and exact maximum-MEMORY replay.
- Persistent Q32 musical phase: Anchor fires at arrival, Thread every half
  quarter, and Spark every quarter quarter. Pitch, timbre, color, decay, level,
  and pan are immutable birth-time event snapshots.
- Three shared Braids-adapter models: sine/triangle, FM, and filtered noise.
  Each renders at 96 kHz and passes through the instrument-owned five-tap
  two-to-one decimator, attack/decay wrapper, equal-power pan, bounded mixer,
  and stereo DC blocker.
- Transactional selected-waypoint drafts, Capture/Replace, dirty-draft discard
  accounting, Reset, Panic, deferred Reseed, exact Lock/Unlock, validated
  reset-boundary state recall, fixed SPSC commands, and accepted-state snapshot
  exchange.
- Authenticated JUCE 8.0.15 macOS standalone with explicit Start Audio,
  refreshable MIDI input selection, Launch Control 3 name preference, receipt
  and mapping diagnostics, map drag/capture, two rows of eight controls, and
  accepted-state UI projection. The app was built and not launched.

## Launch Control 3 protocol

The exact regular topology is Custom Mode MIDI channel 16, encoders CC20-35,
and momentary buttons CC40-47.

| Selectors | Accepted semantic controls |
|---|---|
| CC20-27 | Tempo, Travel, Memory, Length, Roam, Home, Radius, Density |
| CC28-35 | Selected draft Interval, Activity, Timbre, Color, Decay, Level, Pan; global Root |
| CC40-43 | Select waypoint A-D |
| CC44-46 | Select Anchor, Thread, or Spark |
| CC47 | Capture/Replace the complete selected draft |

All 2,048 valid encoder combinations, button press/release edges, intermediate
button rejection, wrong-channel messages, unknown selectors, draft isolation,
single capture, and dirty-selection discard behavior passed pure protocol tests.
The app reports endpoint name/open state, receipt/ignored counts, last
channel/CC/value, accepted route/event state, and fault counters. This is
simulated protocol and target-build evidence only; no physical input was opened.

## Commands and results

Environment: Apple M1 Pro / arm64, macOS 15.6.1 (24G90), Apple clang 16.0.0
(`clang-1600.0.26.6`), CMake 4.4.2, and Python 3.10.4.

The following completed with exit status zero:

```sh
cmake -S research/prototypes/murmur-map -B build/murmur-map-core-debug \
  -DCMAKE_BUILD_TYPE=Debug -DMURMUR_MAP_ENABLE_JUCE=OFF
cmake --build build/murmur-map-core-debug --parallel
ctest --test-dir build/murmur-map-core-debug --output-on-failure

cmake -S research/prototypes/murmur-map -B build/murmur-map-sanitizers \
  -DCMAKE_BUILD_TYPE=Debug -DMURMUR_MAP_ENABLE_JUCE=OFF \
  '-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer' \
  '-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined'
cmake --build build/murmur-map-sanitizers --parallel
ctest --test-dir build/murmur-map-sanitizers --output-on-failure

python3 research/prototypes/murmur-map/tests/render_evidence.py \
  --reproduce --output build/murmur-map-evidence

python3 research/prototypes/murmur-map/tests/build_juce.py \
  --build-dir build/murmur-map-juce-release \
  --juce-source-dir build/cinderwheel-juce-trial/_deps/juce-src

PYTHONDONTWRITEBYTECODE=1 python3 tools/instrument_lab/reproduce.py \
  --repo-root . --consumer-root research/prototypes/murmur-map --reproduce

PYTHONDONTWRITEBYTECODE=1 python3 tools/validation/run.py --profile current
```

Both ordinary and ASan/UBSan suites passed 6/6 tests. They cover block
partition equality, route/event determinism, HOME behavior, exact silence,
state validation/recall, every controller value, transactional drafts,
lock-free exchange coherence, UI projection, exact source authorities, and the
shared Mutable adapter regression.

The relocated copied-root validation and all six focused tests also passed.
The repository `current` profile passed all 9 selected checks with no failures
or incomplete checks.

## Objective host-signal observations

The retained render matrix ran MM01-MM10 in 60 fresh renderer processes: every
condition at outer blocks 1, 16, 64, 128, 511, and 512. Stereo 24-bit WAV,
route trace, and event trace bytes were identical across all six partitions;
normalized objective metrics were also equal. The frozen and reproduced
manifest is
`c9c7fbab76388990fbdbd6589e9e61f0f96c98017a9acbc9d36ab7964a8a1173`.

| Condition | Frames | Routes | Events | Peak | Stereo RMS | Max absolute DC mean |
|---|---:|---:|---:|---:|---:|---:|
| MM01 Locked | 4,608,000 | 326 | 526 | 0.0647580 | 0.0125260 | 2.38e-8 |
| MM02 Slow erosion | 5,760,000 | 451 | 712 | 0.0649181 | 0.0130010 | 1.34e-8 |
| MM03 Fresh | 4,608,000 | 320 | 541 | 0.0627559 | 0.0127980 | 5.89e-8 |
| MM04 Home pull | 4,608,000 | 344 | 536 | 0.0636024 | 0.0128749 | 1.99e-8 |
| MM05 Move waypoint | 4,608,000 | 344 | 550 | 0.0647580 | 0.0126644 | 1.95e-9 |
| MM06 Capture/replace | 4,608,000 | 356 | 565 | 0.0670825 | 0.0137942 | 8.30e-8 |
| MM07 Reseed | 4,608,000 | 326 | 481 | 0.0649181 | 0.0122954 | 9.41e-8 |
| MM08 Extremes | 2,304,000 | 673 | 865 | 0.0693174 | 0.0164074 | 5.99e-9 |
| MM09 Exact silence | 1,152,000 | 83 | 0 | 0 | 0 | 0 |
| MM10 White scene | 5,760,000 | 0 | 701 | 0.0504229 | 0.0125630 | 6.16e-8 |

Every condition reported zero non-finite samples, dropped events, repairs, and
clamps. MM09's entire stereo PCM data section is byte-zero while its route
continues. After MM01 locks, all 247 observed post-lock destinations repeat the
same 16-slot sequence, for recurrence 1.0. MM02 observed 406 replays and 45
replacements; MM03 observed zero replays. Raising HOME in MM04 increased the
observed non-home-to-HOME transition rate from 21.7% (20/92) to 49.3% (72/146).
MM06 changed future Thread event snapshots, and MM07 restarted fresh choices
from HOME at the first following node boundary.

MM02 slow erosion and the MM10 independent white-scene comparator produced
different event and PCM hashes under their matched fixed inputs. That is an
objective distinction, not evidence that the route version sounds better or is
more steerable; the blinded listening gate remains open.

## Authenticated target build

- JUCE: 8.0.15 at authenticated commit
  `91ad83ae34a81e0833b1a2b0866f54846370ae53`; fetching disabled.
- Product: `Murmur Map.app`; CMake target `murmur-map`.
- Executable: Mach-O 64-bit arm64, 8,233,368 bytes.
- Executable SHA-256:
  `66aa4f629aca9620c42d8470be291b838e33ef70139156f20ebb651362eb6717`.
- Build path:
  `build/murmur-map-juce-release/murmur-map_artefacts/Release/Murmur Map.app`.
- The build script compiled every target and passed 6/6 CTests. It did not
  launch the application, open audio/MIDI endpoints, install, sign, notarize,
  package, or distribute it.

## Corrections made during validation

1. The first focused compile caught an accidental bitwise expression where the
   control reducer required a logical expression. The reducer was corrected,
   then all focused tests and later evidence were run from the corrected source.
2. The first native wrapper compile caught two unqualified JUCE character-type
   names. They were qualified, the complete standalone target rebuilt, and all
   target-build tests passed. No renderer or Core evidence was retained before
   the final source freeze.
3. The first relocated-root check correctly rejected local generated Python
   bytecode caches because relocation intentionally excludes them. Only the
   generated Murmur Map `__pycache__` directory was removed; the copied-root
   validation and all six tests then passed without a source change.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | Approved evidence-labelled modular study | No global novelty claim |
| Proposal | passed | Exact approved proposal fingerprint and ready bundle | Approval is limited to revision 0.1 |
| Source | passed | Exact JUCE, Braids, stmlib, adapter, topology, and notices | Distribution review remains open |
| Host structural | passed | Release plus ASan/UBSan 6/6 suites | Noncanonical prototype only |
| Host signal | passed | Frozen/reproduced 10-condition, six-partition matrix | Offline objective evidence is not listening |
| Target build | passed | Exact arm64 app executable hash | App was not launched or visually inspected |
| Real-time | deferred | No live audio callback run | Deadline, allocation, xrun, and lifecycle proof required |
| Connected device | deferred | Pure map and endpoint diagnostics only | Physical Launch Control 3 session required |
| Listening | deferred | Matched comparator artifacts retained | Frozen blinded protocol required |
| Production integration | deferred | No canonical records changed | Separate accepted ownership and release task required |
