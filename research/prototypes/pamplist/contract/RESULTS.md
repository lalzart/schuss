# Pamplist 0.2 implementation results

> Status: completed through authenticated target-build; shared audition-library registration deferred at an accepted record-set boundary

## Fingerprints

- Proposal SHA-256:
  `bf110cd1bfe6b86e032bc993e0baf705d7459182c891d095a9a1a39ce1789af3`
- Ready implementation contract SHA-256:
  `9fc9a43492515c8ec5741b353c09697e79153a76b94c81edf129609da2bffaad`
- Control map SHA-256:
  `aa8c59a568c16999f72ef362b639c2d3fa24d02ee81ca47e7a7a9f4e2c096263`
- Source dependency authority SHA-256:
  `305957e264e6ea14a7e6b6e18a4100c49d36306bbf52dbd574c2e4711b0ec6be`
- Retained render manifest SHA-256:
  `e87b71a5f041517d8d788d64798713be4549ecd6c54823c4b4ababaf2f851f2d`
- Retained render file-set SHA-256 manifest:
  `7dea0a756e389676fd72c1580af26859b1cf362714c7220fc81e5f3e5aa1a43d`
- Authenticated JUCE build receipt SHA-256:
  `fc38576f755c83baced9d13e0bd4eac9f7081a506a6fafe5679c485ec56024b9`
- Built arm64 executable SHA-256:
  `ccdd496d2b7e523d9b7e2352a2f1db9a5f08237de3f35129da3bf0d9e9163e30`
  (8,325,528 bytes; ignored local build artifact)

The configured macro-voice source authenticated as
`patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, with synthesis subtree Git
tree `58917f3e2e46a30337cfb6292a3504845b1d5552`. The checkout was consumed
read-only and no upstream source bytes were copied into Pamplist.

## Implemented behavior

Pamplist is one noncanonical portable C++17 instrument Core. It owns eight
persistent rational clock/modulation lanes, fixed 16-step Euclidean masks,
keyed probability and repeat decisions, eight unipolar shapes, and a signed
8-by-8 matrix focused on Trigger, Pitch, Model, Harmonics, Timbre, Morph,
Decay, and Level. One authenticated complete 24-engine macro voice renders
separate main and auxiliary Q27 outputs through a persistent 16-frame quantum.

The Core accepts whole bounded control states, publishes coherent accepted
snapshots through a fixed-capacity exchange, and writes every requested output
frame. Its process path performs no lock, allocation, file I/O, JSON, or UI
work. Fresh stopped, zero-hit, zero-amplitude, and zero-route programs remain
exactly silent.

The regular Launch Control 3 mapping is synthetic Custom Mode 1 on channel 16:
CC20-27 edit the selected lane's eight signed routes, CC28-35 edit its Rate,
Phase, Shape, Hits, Rotation, Probability, Repeat, and Amplitude, and rising
edges on CC40-47 select lanes 1-8. The standalone presents accepted Core state,
keeps audio off until an explicit Start Audio action, and keeps physical input
off until an explicit refresh and endpoint selection. It distinguishes GUI
injection from physical receipt.

## Environment

- macOS 15.6.1, arm64
- Apple Clang 16.0.0 (`clang-1600.0.26.6`)
- CMake 4.4.2
- Python 3.10.4
- 48 kHz signed Q27 host representation
- Authenticated existing JUCE 8.0.15 extracted tree; fetching disabled

No package install, network fetch, application launch, endpoint access,
hardware access, listening session, staging, commit, push, or publication was
performed.

## Commands and results

| Command | Result | Bounded evidence |
|---|---|---|
| `python3 .../validate_implementation_bundle.py research/prototypes/pamplist/contract --workspace-root . --phase structure` | pass | Complete v2 bundle structure before DSP edits |
| `python3 .../validate_implementation_bundle.py research/prototypes/pamplist/contract --workspace-root . --phase ready` | pass before DSP and at freeze | Approved proposal fingerprint, exact experiment, state matrix, control map, and evidence plan |
| `python3 research/prototypes/pamplist/tests/verify_source_authority.py --json` | pass | Lock revision, subtree tree, clean relevant subtree, wrapper/manifest/notice hashes, controller authority, and JUCE manifest |
| `python3 research/prototypes/pamplist/tests/run_focused.py` | pass | Four Release CTests and the same four ASan/UBSan CTests; Core, controller map, snapshot contention, and no-process-allocation coverage |
| `python3 research/prototypes/pamplist/tests/render_evidence.py --reproduce` | pass | Seven retained conditions across block sizes 1, 16, 64, 128, 257, and 512 |
| `python3 research/prototypes/pamplist/tests/render_evidence.py --check` | pass | Retained file set, hashes, objective bounds, exact partitions, loop, silence, engine sweep, and comparator |
| `python3 research/prototypes/pamplist/tests/build_juce.py --reproduce --juce-source build/cinderwheel-juce-trial/_deps/juce-src --build-dir build/pamplist-juce` | pass | Authenticated configure, compile, link, executable identity, and receipt; no launch |
| `python3 research/prototypes/pamplist/tests/build_juce.py --check` | pass | Frozen source/build input fingerprint and exact executable hash |
| `python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/pamplist --check` | pass | Exact noncanonical index, topology, authorities, promotion needs, and handoff |
| `python3 research/prototypes/pamplist/tests/reproduce_fresh_root.py` | pass | Relocated repository copy, explicit locked external source, rebuilt four Core tests, retained render authentication, and no consumer-tree mutation |
| `python3 -m unittest tools.contracts.tests.test_task039_instrument_library` | pass, 7/7 | Frozen five-entry library and bounded service behavior remained unchanged after the registration conflict was removed |
| `python3 tools/validation/run.py --profile current` | pass, 8/8 at final freeze | Routine repository closure including all discovered Instrument Lab consumers |

## Objective observations

| Observation | Result | Frozen requirement |
|---|---:|---:|
| Supported outer block sizes | 1, 16, 64, 128, 257, 512 | all exact |
| PCM, event trace, accepted snapshots, metrics, manifests, and synthetic control trace across partitions | byte-identical | exact |
| Finite samples | 100% in every condition | 100% |
| Saturated frames | 0 in every condition | 0 |
| Nominal invalid, clamp, recovery, unsupported-process, and non-finite-source diagnostics | 0 | 0 |
| `PAMP_SILENCE` stopped / zero-hit / zero-amplitude / zero-route nonzero frames | 0 / 0 / 0 / 0 | all zero |
| `PAMP_24` engines with nonzero main and auxiliary output | 24 of 24 | 24 of 24 |
| `PAMP_24` overall main / auxiliary peak Q27 | 69,793,216 / 69,793,216 | below 134,217,728 |
| `PAMP_LOOP` repeat addresses observed consistently | all 7 | all 7 |
| `PAMP_MATRIX` trigger count | 7 | nonzero |
| `PAMP_MATRIX` main / auxiliary RMS | 0.060670590 / 0.067157455 | finite, nonzero |
| `PAMP_MATRIX` main / auxiliary peak Q27 | 45,364,204 / 45,364,204 | bounded |
| Phaseless comparator | audio and event trace both diverged | both must diverge |

The objective matrix demonstrates deterministic bounded host signal. It is not
a listening result and does not establish live callback deadlines or endpoint
behavior.

## Corrections and invalidation trail

1. Before DSP source existed, readiness review found an erroneous `*16` tempo
   factor and an inconsistent seven/eight-shape count. Revision 0.2 froze the
   intended sixteenth-note `*4` clock law, exact 16-rate table, and eight exact
   shape formulas. The proposal was re-fingerprinted and both bundle phases
   passed before implementation began.
2. The first exact-silence Core test exposed a source-boundary error: external
   level mode could emit signal before any trigger. The adapter now uses the
   source's internal trigger/dynamics path, Pamplist applies Level after the
   voice, and the Core skips voice rendering until its first accepted trigger.
   Release, sanitizer, render, relocated, and standalone evidence were all
   regenerated or rechecked after this signal correction. No tolerance was
   weakened.
3. Adding sanitizer instrumentation to the final CMake input closure correctly
   made the earlier standalone receipt stale. The authenticated target was
   rebuilt and the final receipt above replaced it; Core semantics did not
   change.
4. A provisional attempt to append Pamplist to Task 039's generated library
   changed `schuss-record-set-000033@1`. The current gate rejected it because
   Task 040's retained Phase 1 authority binds the exact parent file and closure
   while reserving record sets 000034 and 000035. All provisional shared
   generator, schema, record-set, library, and test changes were removed; the
   original Task 039 generator and seven tests pass byte-exactly. Pamplist's
   standalone therefore remains a direct local build rather than a registered
   Instruments-home entry.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | Bounded observable-behavior and exact source research in the approved proposal | No firmware, algorithm-equivalence, or novelty claim |
| Proposal | passed | Revision 0.2 SHA-256-bound approval and ready v2 bundle | Later design changes need a new approved fingerprint |
| Source | passed | Locked configured macro-voice dependency and read-only exact adapter | Private prototype provenance is not distribution approval |
| Host structural | passed | Release and sanitizer CTests, exhaustive synthetic mapping, snapshots, allocation, topology, and current closure | Noncanonical and not a live endpoint |
| Host signal | passed | Frozen seven-condition render matrix and relocated authentication | Objective renders are not listening evidence |
| Target build | passed | Exact authenticated JUCE executable and receipt | App was not launched or visually inspected |
| Real-time | not run | None | Deadline, xrun, and lifecycle behavior unproved |
| Connected device | not run | Synthetic protocol only | No physical Launch Control 3 receipt or reconnect evidence |
| Listening | not run | None | Pattern, balance, transitions, and usefulness unjudged |
| Production integration | not run | Noncanonical prototype only | No shared library entry, canonical identity, target adaptation, packaging, or release |
