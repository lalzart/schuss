# Wirefall revision 0.2 implementation results

> Status: completed through target-build

## Proposal and contract fingerprints

- Proposal: `research/proposals/wirefall-r02.md`
- Proposal revision: `0.2`
- Proposal SHA-256: `1862683de17018a0d6802cd2eee40a1cd273a3033d493713f6272cc3549744ee`
- Implementation contract: `implementation-contract.json`
- Ready validation: passed before DSP source and passed again at freeze

## Commands and results

| Command | Result | Evidence |
|---|---|---|
| `python3 .../validate_implementation_bundle.py research/prototypes/wirefall-r02/contract --workspace-root . --phase ready` | pass | Approved proposal fingerprint, state/control/experiment bundle readiness |
| `cmake -S research/prototypes/wirefall-r02 -B build/wirefall-r02-core -DWIREFALL_R02_ENABLE_JUCE=OFF` | pass | Portable host configuration |
| `cmake --build build/wirefall-r02-core -j4` | pass | Core, renderer, and focused test executables |
| `ctest --test-dir build/wirefall-r02-core --output-on-failure -R '^wirefall_r02_core_tests$'` | pass, 1/1 | Core defaults, exhaustive descriptor comparison, fixed capacities, no processing allocation, event rejection, partition equality, exact interruption, Reset, and Panic |
| `python3 research/prototypes/wirefall-r02/tests/validate_render_matrix.py build/wirefall-r02-core/wirefall_r02_render --output build/wirefall-r02-results` | pass | Four 24-second conditions across partitions 1, 16, 64, 257, 512 plus repeat |
| First JUCE configure attempt | failed as retained diagnosis | Prototype project declared only CXX; JUCE requires C for its compiled C sources |
| Same configure after adding C to project languages | pass | Existing local JUCE 8.0.15 source accepted; fetching remained disabled |
| `cmake --build build/wirefall-r02-juce --target wirefall-r02-instrument -j4` | pass | Standalone `.app` compiled and linked; it was not launched |
| `python3 tools/validation/run.py --profile current` | pass, 5/5 | Cheap repository current closure; no configured-source, native matrix, reproduction, network, or device work |

Toolchain: AppleClang 16.0.0.16000026, CMake 3.22-or-newer contract,
macOS arm64 host. JUCE source directory was the existing
`build/cinderwheel-juce-trial/_deps/juce-src`, authenticated by the Instrument
Lab 8.0.15 version contract. No fetch, package install, application launch, or
audio/device operation occurred.

## Objective observations

| Observation | Result | Frozen bound |
|---|---:|---:|
| ENERGY fundamental error, worst absolute | 0.1945 cents | at most 15 cents |
| ENERGY `.20` step rises | 646.6, 720.7, 766.4, 800.4 cents | 500–900 cents each |
| ENERGY centroid positive steps | 4 of 4 | at least 4 |
| ENERGY final/first centroid ratio | 17.596 | at least 2.5 |
| ENERGY final/first RMS gain | 2.878 dB | 0.5–4.0 dB |
| Highest non-harmonic below 20 kHz | -85.843 dBFS | at most -60 dBFS |
| Full BREAK, TICK zero interior peak | exactly 0 | at most one 24-bit LSB |
| Silence/tick schedule | exact | exact required |
| Tick interruption RMS | -21.575 dBFS | at least -36 dBFS |
| Tick peak | -9.874 dBFS | at most -9 dBFS |
| Main-signal suppression in closed tick interior | 581.13 dB numerical floor | at least 24 dB |
| Pulse boundary excess | 0.00815 | at most 0.032 |
| Condition peaks | 0.3274–0.4556 | at most 0.8912 |
| Absolute channel DC means | at most 0.00000226 | at most 0.0001 |
| Non-finite samples / safety clamps / dropped events | 0 / 0 / 0 | all zero |
| WAV and event bytes across partitions/repeat | exact for all four conditions | exact required |

Retained compact evidence is under `../results/`. WAV files and native build
products remain reproducible-only under ignored `build/` paths.

Target artifact:
`build/wirefall-r02-juce/wirefall-r02-instrument_artefacts/Wirefall 0.2.app`.
Executable SHA-256 at freeze:
`7ef1332c2d211a7a0f2795663b040ac92c35fbf3defef35a4464ff70b93e6513`.

## Corrections made during validation

1. The first exact-silence Core test exposed an asymptotic smoother defect:
   BREAK approached 1.0 but never became exactly 1.0, leaving a mathematical
   residual. Smoothed values now snap to an accepted target within `1e-12`.
   Core structural and all host-signal evidence were rerun after this DSP
   correction.
2. The first authenticated JUCE configure exposed a build-language omission.
   Adding C to the prototype project languages corrected target configuration.
   This did not change Core or renderer bytes, so it invalidated only target
   configuration/build evidence, which was rerun.
3. Before DSP source existed, the frozen proposal was corrected so ROOT is
   explicitly in semitones and the 36-semitone ENERGY curve's step tolerance is
   internally consistent. The proposal was re-fingerprinted and the ready
   bundle revalidated before implementation.
4. Final standalone source review found that PANIC feedback represented only
   the fully latched state, allowing the toggle to visually clear during the
   480-frame fade-down. Feedback now treats fade-down and latched states as the
   accepted active state. The standalone target was rebuilt after this UI-only
   correction; Core and host-signal evidence were unaffected.

No tolerance was weakened in response to an observed signal failure.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed/available | Wirefall 0.1 bounded sources plus current user design input | No universal novelty or cultural-authenticity claim |
| Proposal | passed | Revision 0.2 SHA-256-bound ready bundle | Later subjective preference remains open |
| Source | passed | Portable Core, renderer, analyzer, control surface, and standalone source | Prototype-local and noncanonical |
| Host structural | passed | Focused CTest and exhaustive control descriptor comparison | Does not prove sound quality or callback timing |
| Host signal | passed | Frozen objective summary and retained canonical metrics/ledgers | Does not prove listening preference |
| Target build | passed | Authenticated JUCE standalone compiled and linked | App not launched; no device or UI observation |
| Real-time | not run | None | Callback deadlines and lifecycle unproved |
| Connected device | not run | None | No endpoint or physical surface in scope |
| Listening | not run | Prior 0.1 response motivated this revision; no 0.2 audition | Musical sensitivity and usefulness unproved |
| Production integration | not run | None | No catalog, graph, provider, package, or release identity |
