# Pamplist 0.6 Local VST3 Host Migration implementation results

> Status: implemented and validated through target-build and offline host-signal
> evidence; the bundle remains uninstalled and Ableton was not launched

## Proposal and authority fingerprints

- Proposal: `research/proposals/pamplist-vst3-local.md`
- Proposal SHA-256:
  `125826a47e649bc91d757d62d7b2a1543238769614c9b5f8b843c819291ee650`
- State schema: `schuss-pamplist-vst3-state-v1`
- Parameter-model fingerprint: `14882405573471441702`
- JUCE authority: authenticated 8.0.15 source manifest SHA-256
  `db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5`
- Macro Voice authority: configured `patcher` revision
  `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, synthesis tree
  `58917f3e2e46a30337cfb6292a3504845b1d5552`

Task 045 lives under `research/prototypes/pamplist/vst3/`. This isolation keeps
the frozen Pamplist 0.6 standalone source closure and its retained Task 043
receipt byte-for-byte authoritative.

## Implemented boundary

- One macOS arm64 JUCE VST3 instrument, zero audio inputs, stereo output, MIDI
  input, exact 48 kHz operation, and no copy-after-build installation.
- 178 stable Pamplist musical parameters plus persistent host-only Run. Clear
  remains a non-persistent one-shot; page and Voice/Motion mode are private
  recalled presentation state.
- Transactional bounded XML state with complete schema, ID, cardinality,
  finite-value, range, duplicate, truncation, and size validation before apply.
  Recall restores program, seed, Run, page, and mode, then creates a fresh Core.
- Arbitrary positive host blocks are partitioned into Core calls of at most 512
  frames. Sample-offset channel-16 CCs use the existing controller adapter.
- A source-faithful eight-page editor exposes the 16 contextual slots, Run,
  Clear Cohesion, and accepted activity history without endpoint ownership.
- Per-instance Core, scratch buffers, controller adapter, parameters, and state.

JUCE also publishes one standard bypass parameter and 2,080 non-automatable
MIDI-controller service parameters required for its VST3 CC mapping. The first
179 parameters are the complete stable Pamplist adapter surface; the additional
entries are wrapper protocol, not Pamplist controls or canonical Schuss
parameters.

## Validation results

| Check | Result | Observation |
|---|---|---|
| Ready bundle and frozen source equivalence | passed | Proposal, contract, control, state, experiment, validation, source hashes, configured Macro Voice source, and JUCE authority authenticated |
| VST model, processor, allocation, and module suites | 4/4 passed in Release | Actual bundle scanned as one instrument, instantiated twice as 0-in/2-out, and created/destroyed its editor |
| Parameter model | passed | 179 unique stable adapter parameters; exhaustive Controls conversion and declared quantization round-trips |
| Direct Core parity | passed | Exact PCM parity for host blocks 1, 16, 64, 128, 512, 513, 2048, and 4096 at 48 kHz |
| MIDI and actions | passed | Timestamped regular CCs plus page, mode, Run, and Clear sequences matched the direct path |
| State | passed | Fresh-Core twin matched after recall; malformed, incomplete, duplicate, nonfinite, out-of-range, and over-1-MiB inputs were rejected transactionally |
| Invalid host shapes | passed | 44.1/96 kHz and mono runtime shapes returned deterministic silence |
| Instance/lifecycle boundary | passed | Two instances remained isolated; unattached editor construction/destruction passed |
| Allocation probe | passed | Zero observed C++ heap allocations across 256 calls of 4,096 frames with two timestamped CC events per call |
| Sanitizers | passed where supported | Model and processor passed Apple arm64 AddressSanitizer/UndefinedBehaviorSanitizer; LeakSanitizer is unsupported on this platform |
| Existing Pamplist regression | passed | 6/6 Release plus 6/6 sanitizer tests, retained r06 render evidence, source authority, standalone receipt, prototype freshness, and Task 043 freshness |
| Relocated reproduction | passed | Copied-root Release rebuild and all 4 VST suites passed without source mutation; the exact pre-build consumer-tree hash is emitted by the reproduction runner |

## Release artifact

- Bundle:
  `build/pamplist-vst3-task045-release/pamplist-vst3_artefacts/Release/VST3/Pamplist.vst3`
- Architecture/kind: Mach-O 64-bit bundle, arm64
- Plug-in binary SHA-256:
  `45050475abb33353b543ea409be4a12139d318b27cb803f7b1efd6500f305d06`
- Bundle-tree SHA-256:
  `8bb72da3719cfaec16d6fdb53947536039e1c852ecee480e80efda6b85f2310c`
- Receipt: `vst3-build.json`, status `passed`
- Signature evidence: valid local ad-hoc seal only; no identity signing or
  notarization claim

The separate JUCE module host loaded the exact retained bundle, exercised its
state and MIDI seams, and observed matching nonzero PCM. No plug-in folder,
application, audio/MIDI endpoint, or physical device was touched.

## Corrections made during validation

1. Moved the adapter into its own CMake/source subtree after the initial layout
   would have changed the frozen standalone source closure.
2. Replaced JUCE binary `ValueTree` decoding with bounded XML validation so
   truncated hostile state is rejected before JUCE can assert.
3. Moved editor resizing until after child construction to remove a null-child
   lifecycle fault.
4. Split module scan identity from instantiated bus-shape proof because JUCE's
   scanner description does not populate output channels before instantiation.
5. Re-applied the local ad-hoc seal after JUCE's post-build module-info write.
6. Recorded JUCE's bypass and MIDI CC service parameters separately from the
   179 plug-in-owned stable parameters.
7. Corrected the frozen validation-plan command to the repository's actual
   `tools/validation/run.py` entry point after the stale path failed before any
   check could start.

Each correction invalidated and reran its affected focused or target check.

## Evidence ladder

| Level | Result | Remaining limitation |
|---|---|---|
| Research | passed | Personal-use licensing is bounded; redistribution remains unreviewed |
| Proposal | approved | The request did not authorize installation, app launch, device, Git, or publication actions |
| Source | passed | The authenticated upstream signed-shift concern remains retained |
| Host structural | passed | Offline structure is not callback-deadline evidence |
| Host signal | passed | Deterministic PCM parity is not a listening judgment |
| Target build | passed | The arm64 bundle is uninstalled and untested in Live |
| Real-time | not run | No callback, xrun, CPU, memory, or multi-instance host measurements |
| Connected device | not run | No Live MIDI route or physical controller session |
| Listening | not run | No single/layered creative audition |
| Production integration | not run | No canonical provider, host matrix, release signing, notarization, packaging, or distribution review |
