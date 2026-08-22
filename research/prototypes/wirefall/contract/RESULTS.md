# Wirefall implementation results

> Status: Core-only implementation complete; host-signal acceptance failed

## Proposal and contract fingerprints

- Proposal: `research/proposals/wirefall.md` revision 0.1
- Proposal SHA-256: `cf9b5f58e50856a9d38d754ee476ced58c52473bb9f9ff1216c75e7ca28707b8`
- Approval reference: user message `Approve` immediately following presentation
  of the exact proposal fingerprint in this Codex task
- Implementation contract: `implementation-contract.json`
- Work type: `new-design`
- Working artifact: `wirefall_core_tests and wirefall_render`
- Evidence ceiling: `host-signal`

## Implemented artifact

- Original portable C++17 `wirefall_core` with fixed-capacity DSP, scheduler,
  state transitions, diagnostics, two voice-local space paths, and 4x/8x
  render configurations.
- Deterministic generated public-control descriptor and five literal condition
  fixtures.
- `wirefall_core_tests` and `wirefall_render`, linked only to the repository's
  Instrument Lab mechanics.
- Retained canonical metrics, event ledgers, objective summary, and observation
  manifest under `research/prototypes/wirefall/results/`. WAVs remain ignored
  under `build/wirefall-renders/`; their SHA-256 values are in the retained
  manifest.

The Core occupies 70,128 bytes, below the frozen 256 KiB limit. The processing
allocation probe, partition/state tests, Reset/Panic timing, event capacity,
finite bounds, and sanitizer run passed.

## Commands and results

The Sonic Research Lab skill package is
`sonic-research-lab/0.3.0+codex.20260820115751`. Paths below are relative to
that package where the command names the skill script.

| Command | Exit | Result |
|---|---:|---|
| `new_implementation_bundle.py --work-type new-design --proposal research/proposals/wirefall.md --title Wirefall --target "Instrument Lab v1 portable C++17 Core and deterministic renderer" --artifact "wirefall_core_tests and wirefall_render" --evidence-level host-signal --workspace-root . --output research/prototypes/wirefall/contract` | 0 | Created the v2 scaffold and bound proposal SHA-256. |
| `validate_implementation_bundle.py research/prototypes/wirefall/contract --workspace-root . --phase structure` | 0 | Initial generated structure valid before contract completion. |
| `validate_implementation_bundle.py research/prototypes/wirefall/contract --workspace-root . --phase ready` | 0 | Implementation bundle ready: valid. Proposal fingerprint, work type, working definition, conditions, state, controls, validation gates, source rationale, results, and gaps accepted. |
| `python3 research/prototypes/wirefall/tests/validate_contract_fixtures.py --repo-root .` | 0 | Frozen proposal, ready bundle, FIR bytes, controls, state, experiment, and generated fixtures authenticate. |
| `cmake -S research/prototypes/wirefall -B build/wirefall-release -DCMAKE_BUILD_TYPE=Release` | 0 | Core-only release tree configured with AppleClang 16.0.0; no dependency was installed. |
| `cmake --build build/wirefall-release --parallel` | 0 | `wirefall_core`, `wirefall_core_tests`, and `wirefall_render` built. |
| `ctest --test-dir build/wirefall-release --output-on-failure -R '^wirefall_(core_tests\|contract_fixtures)$'` | 0 | 2/2 focused source and host-structural tests passed. |
| `cmake -S research/prototypes/wirefall -B build/wirefall-sanitize -DCMAKE_BUILD_TYPE=Debug -DWIREFALL_ENABLE_SANITIZERS=ON` plus build and focused Core CTest | 0 | Address/undefined sanitizer Core test passed. |
| `python3 research/prototypes/wirefall/tests/validate_render_matrix.py --renderer build/wirefall-release/wirefall_render --contract research/prototypes/wirefall/contract/experiment.json --output build/wirefall-renders` | 1 | Every partition and fresh block-64 WAV/ledger was byte-identical, but nine frozen objective checks failed. The manifest was retained; exit 1 is the expected fail-closed result. |
| Same validator with `--output build/wirefall-renders-repeat --repeat-block-frames 64` | 1 | Fresh-process determinism reproduced; the same nine signal failures reproduced byte-identically. |
| `python3 tools/instrument_lab/reproduce.py --repo-root . --reproduce` | 0 | Shared Instrument Lab fresh/relocated smoke passed. This script currently reproduces the smoke consumer, so it is adjacent workflow evidence and is not claimed as Wirefall reproduction. |
| Temporary relocated-root copy of the proposal, Wirefall subtree, and shared Instrument Lab; then contract validation, release build, and five block-64 renders | 0 | All five relocated Wirefall WAV and ledger hashes matched the retained canonical manifest. No workspace source or external resource was mutated. |

No app, audio/MIDI endpoint, controller, target compiler, hardware, playback,
listening, publication, staging, commit, push, distribution, or production
command ran.

## Objective observations

- The proposal bytes match the approved SHA-256 at final readiness validation.
- `wirefall-fir-63.json` declares 63 little-endian binary32 words. Independent
  byte authentication reproduced SHA-256
  `a99f4e674be713a0b0f2405711cff20b6a0676a13f4af63380165c4984e70b1a`;
  tap count and bit-exact symmetry passed.
- Every JSON artifact parsed, no machine-local absolute path or unresolved
  marker remained, and the two directly linked DSP authority hashes matched
  `implementation-contract.json`.
- All five conditions stayed finite and below the `0.8912` peak ceiling; normal
  fixtures dropped no events and triggered no containment. The smallest
  scheduler boundary spacing was 1,125 frames, above the 32-frame minimum.
- Audio and accepted-event ledgers were byte-identical for block partitions
  `1,16,64,257,512` and a fresh block-64 process. The normalized Wire schedule
  for `WF02`, `WF03`, and `CMP02` matched exactly.
- TENSION fundamentals tracked the equation within 0.22 cents, all four
  adjacent centroid changes were positive, and the final/first centroid ratio
  was 35.36. The final/first hold RMS was instead -0.596 dB, failing the
  required `(0,+4]` dB energy relation.
- The aligned 4x/8x residual was -26.91 dBFS against a required <=-55 dBFS;
  the highest non-harmonic component below 18 kHz was -46.34 dBFS against a
  required <=-50 dBFS.
- Every condition exceeded the `1e-4` absolute channel-DC bound; observed
  maxima ranged from 0.00175 (`WF01`) to 0.00871 (`WF03`).
- The `WF02` cut-interior peak was 0.06619 rather than <=`1e-5`. The frozen
  post-gate DC blocker retains a decaying state after the complementary edge,
  so the proposed immediate true-void invariant is not met by the frozen
  processing order.
- Shadow cut low-band energy exceeded Void by 66.06 dB, but Wire-band rejection
  was only 7.20 dB against the required >=20 dB.
- The continuous-low comparator selected gain `0.795041561126709` by the
  frozen 32-iteration lower-tie bisection.

The retained objective summary SHA-256 is
`ccb4bd3fbf496e7ffcd78cccdbfabcb93d7b984e0bccc93860e22314416ee376`;
the retained observation manifest SHA-256 is
`429a6bd22199c16842def8631081533db1c458869781fb4160580912fca32ca5`.

## Corrections made during validation

- The generated scaffold contained placeholders by design. The approved
  proposal was translated into literal conditions, state operations, controls,
  checks, gaps, exact TPT-SVF equations, and fixed FIR coefficient bytes.
- Fixture generation now escapes C++ reserved identifiers (`VOID`) and retains
  the literal start value of linear-ramp events.
- Raised-cosine endpoint counting, Reset/Panic clear boundaries, restarted
  Reset behavior, Shadow ratio-crossfade ownership, event drop diagnostics,
  and Panic cleanup were corrected under focused tests before the final render
  freeze.
- Comparator parity normalization excludes fixture-local ingress sequence
  numbers because the frozen WF02/WF03/CMP02 fixtures intentionally offset
  those numbers while retaining the same accepted Wire event times/values.
- No DSP curve, output order, tolerance, condition, or listening claim was
  changed to make the failed host-signal run pass.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | retained | Proposal Sections 3-8 and claim ledger | Bounded search only; no global novelty or patent-freedom claim. |
| Proposal | approved; fingerprint matched | `research/proposals/wirefall.md` revision 0.1 | Approval authorizes bundle readiness only. |
| Ready implementation contract | passed | This contract directory and Sonic Research Lab readiness validator | This is an executable plan, not source or sound evidence. |
| Source | passed | Authenticated generated fixtures and original C++17 Core/renderer source | Proposal remains frozen; source does not prove output acceptance. |
| Host structural | passed locally | Release build, 2/2 focused CTests, sanitizer Core test, 70,128-byte state, allocation/partition/state tests, direct Instrument Lab consumer validation | No real-time, target, device, or listening inference. |
| Host signal | evidence obtained; acceptance failed | Retained five-condition metrics, ledgers, summary, manifest, all-partition and fresh-repeat hashes | Nine objective failures prevent promotion; no listening inference is permitted. |
| Target build | deferred | None | No target selected or authorized. |
| Real-time | deferred | None | No callback or deadline evidence. |
| Connected device | deferred | Provisional selectors only | No endpoint, receipt, feedback, or lifecycle evidence. |
| Listening | deferred | Protocol only | No sound has been rendered or heard. |
| Production integration | out of scope | None | No canonical Schuss identity or integration task is active. |

## Task 038 workflow maintenance

Task 038 refreshed only the Instrument Lab workflow dependency fingerprint and
derived implementation handoff. The workflow now explains that the proposal's
retained `proposed` header is the frozen pre-approval snapshot, while the ready
v2 implementation contract owns and binds the later approval reference. The
repository validator checks that exact proposal path, SHA-256, work lane, and
approval state. Relocated Core-only reproduction passed without changing DSP,
tolerances, retained metrics, or the failed host-signal disposition above.
