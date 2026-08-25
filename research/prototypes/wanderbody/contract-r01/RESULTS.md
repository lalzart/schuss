# Wanderbody 0.1 standalone first playable implementation results

> Status: passed at source, host-structural, host-signal, and authenticated
> target-build levels; real-time, connected-device, listening, distribution,
> and production evidence remain deferred

## Proposal and contract fingerprints

- Proposal: `research/proposals/wanderbody-standalone-r01.md`
- Proposal SHA-256: `2441ae557cd4a692cd3aa42b87b80bf42e401d35250f685912d1f288ba3d6682`
- Implementation contract: `contract-r01/implementation-contract.json`
- Retained render manifest SHA-256:
  `eb6ce67fb18038aa6f49fdff2cb51a905816c9aacf0ac114f368b6f75094df12`
- Toolchain: Apple Clang 16.0.0, CMake 4.4.2, Python 3.10.4, macOS arm64

## Commands and results

All commands ran from the Schuss repository root and exited zero after the
corrections listed below.

| Check | Command | Result |
|---|---|---|
| Frozen source/proposal boundary | `python3 research/prototypes/wanderbody/tests/verify_provenance.py` | Proposal, ready contract, new-design boundary, and JUCE authority exact |
| Focused portable suite | `python3 research/prototypes/wanderbody/tests/run_structural.py --check` | 3/3 CTest targets passed; Core property/state tests, zero-process-allocation test, and exhaustive control-surface comparison |
| ASan/UBSan | `python3 research/prototypes/wanderbody/tests/run_structural.py --sanitizers` | 3/3 CTest targets passed with ASan/UBSan; Apple leak detection is unsupported and explicitly disabled |
| Objective renderer | `python3 research/prototypes/wanderbody/tests/render_evidence.py --reproduce --output build/wanderbody-evidence` | 10 conditions x 7 block sizes passed; canonical block 127 exactly matched the frozen expected manifest |
| Instrument Lab consumer | `python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/wanderbody --check` | Noncanonical index, topology, authorities, promotion needs, and handoff exact |
| Relocated consumer | `python3 tools/instrument_lab/reproduce.py --repo-root . --consumer-root research/prototypes/wanderbody --reproduce` | Copied-root source, authority, build, and 3/3 CTest reproduction passed |
| JUCE target build | `python3 research/prototypes/wanderbody/tests/build_juce.py --build-dir build/wanderbody-juce-release --juce-source-dir build/cinderwheel-juce-trial/_deps/juce-src` | Authenticated JUCE 8.0.15 Release bundle compiled and linked; 3/3 CTest targets passed; app not launched |
| Schuss routine closure | `python3 tools/validation/run.py --profile current` | 9/9 declared current checks passed after governance and documentation freeze |

The retained canonical artifacts are under
`research/prototypes/wanderbody/results/`. Each condition contains
`audio.wav`, `decisions.json`, and `metrics.json`; the root `manifest.json`
binds their hashes to the proposal, contract, experiment, Core, and renderer.

## Objective observations

- The complete 70-render matrix produced zero non-finite samples, voice
  repairs, body repairs, or final numeric faults. The maximum absolute sample
  was `0.9336314797401428`, below the strict `0.98` ceiling. The largest
  absolute channel mean was `0.001763524227664268`, below `0.0025`.
- `WB01_HOVER` made 87 decisions and every resolved position remained inside
  its declared field.
- `WB02_DRUNK` produced 73 post-slew observations spanning
  `0.2927113610197501..0.7069358839909585`; non-overlapping signed-step lag-1
  correlation was `0.6877096742071228`, above `0.30` without exceeding the
  boundary-occupancy limit.
- `WB10_UNCORRELATED` used the same resolved field and produced correlation
  `-0.11766297503739166`; its absolute value remained below `0.15` and its
  trace differed from Drunk. Non-overlapping differences avoid the mechanical
  negative correlation introduced when adjacent differences share an IID
  middle position.
- `WB03_LOCKED` repeated the exact eight-tuple oldest-to-newest cycle;
  `WB04_SHUFFLED` preserved the exact set in a non-identity fixed permutation;
  `WB05_MUTATED` changed only the declared dimensions within the normalized
  `0.25` bound.
- `WB06_BODY` retained stereo difference, measured
  `4186.657466808531` mid-window energy relative to the exact bypass, and a
  late-to-early body-difference energy ratio of
  `0.00021998720880111748`, below `0.45`.
- `WB07_FREEZE_CLEAR` held capture time exactly across Freeze
  (`freeze_hold_delta=0`), accepted two toggles and one Clear, and advanced the
  capture epoch without an invalid read. `WB09_SILENCE` emitted no decisions
  and byte-exact zero PCM.
- At 48 kHz the preallocated mono capture store is 384,000 float samples
  (`1,536,000` bytes). The process-time allocation counter remained exactly
  zero after preparation.

Early insufficient-capture scheduling attempts are retained in
`decision_drop_count`; they do not produce semantic decisions or invalid
reads. This counter is diagnostic evidence, not reclassified as a pass/fail
signal.

## Target-build receipt

- Bundle executable:
  `build/wanderbody-juce-release/wanderbody-instrument_artefacts/Release/Wanderbody 0.1.app/Contents/MacOS/Wanderbody 0.1`
- File identity: Mach-O 64-bit executable arm64
- Executable SHA-256:
  `5eeb318a41b57227bab7096cc2a34d30823e443d85edf4302412f034f18f6bb2`
- Executable size: `10,770,160` bytes
- The bundle was not launched, installed, signed, notarized, or copied to an
  application or plug-in directory. No audio or MIDI endpoint was opened.

## Corrections made during validation

1. The initial exact-silence test exposed a 20 ms ramp from default controls to
   the first submitted control snapshot. The Core now accepts the first valid
   post-prepare snapshot atomically, while later continuous changes still use
   the frozen slew.
2. `WB08_EXTREMES` initially changed after Reset across block partitions because
   the fixture kept submitting pre-reset controls for a block-dependent
   duration. The semantic schedule now restores default controls at the exact
   Reset frame, making audio and decisions partition exact.
3. Apple ASan rejected `detect_leaks=1` as unsupported. The runner now uses
   ASan/UBSan with `detect_leaks=0`; the separate global-allocation override
   continues to prove zero process-time allocation.
4. The first JUCE compile identified constness, `std::string_view` conversion,
   and C++17 constexpr-storage issues in the new shell. Those mechanical
   adapter errors were corrected before the successful authenticated build.
5. A final frozen-equation audit found that an earlier fragment draft applied
   the four-voice normalization twice and that its modal brightness/gain law
   preceded the approved equation. The extra fragment factor was removed and
   the exact `0.25 + 0.75 * brightness^(m/2+1)` modal weighting restored; all
   native, sanitizer, render, target-build, and relocated gates were then
   regenerated from those bytes.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | available | Frozen proposal claim ledger and cited primary sources | Bounded search; no novelty or source-equivalence claim |
| Proposal | available | Approved revision 0.1 and exact fingerprint | Approval covers only the declared vertical slice |
| Source | passed | Original Core/shell plus exact proposal and JUCE authority checks | Complete-diff review does not imply live behavior |
| Host structural | passed | Core/state/property/allocation/sanitizer/control and Instrument Lab checks | No callback deadline or endpoint evidence |
| Host signal | passed | Retained ten-condition 48 kHz matrix over seven exact partitions | Objective output is not listening approval |
| Target build | passed | Authenticated JUCE 8.0.15 macOS arm64 bundle and executable receipt | Bundle was deliberately not launched |
| Real-time | deferred | No live callback run authorized | Requires separate named device/profile gate |
| Connected device | deferred | No endpoint or physical device access authorized | Requires separate device gate |
| Listening | deferred | No listening protocol performed | Requires exact-build subjective evaluation |
| Production integration | deferred | Prototype is deliberately noncanonical | Requires identity/provider/runtime/release task |
