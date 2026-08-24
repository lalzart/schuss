# Pamplist 0.3: Independent Lane Voices implementation results

> Status: implementation and all bounded revision 0.3 validation passed

## Proposal and contract fingerprints

- Proposal: `research/proposals/pamplist-r03.md`
- Proposal SHA-256: `ecafd12747c5afb1ad89eb4c073876e8c504c215192c0300c53a7358691e42e0`
- Implementation contract: `implementation-contract.json`
- Configured synthesis source: `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, tree `58917f3e2e46a30337cfb6292a3504845b1d5552`

## Commands and results

- `validate_implementation_bundle.py ... --phase ready`: passed before DSP edits.
- `python3 research/prototypes/pamplist/tests/verify_source_authority.py`: passed; exact configured source and locked file hashes authenticated.
- `python3 research/prototypes/pamplist/tests/run_focused.py`: passed Release and ASan/UBSan builds; all four focused tests passed in both configurations.
- `python3 research/prototypes/pamplist/tests/render_evidence.py --reproduce`: passed all eight conditions at host block sizes `1, 16, 64, 128, 257, 512`; retained evidence was then re-authenticated with `--check`.
- `python3 research/prototypes/pamplist/tests/build_juce.py --reproduce --juce-source ...`: authenticated JUCE 8.0.15, configured, compiled, and linked target `pamplist`; `--check` passed. The app was not launched and no audio or MIDI endpoint was opened.
- `python3 research/prototypes/pamplist/tests/reproduce_fresh_root.py`: passed prototype validation, configured-source authentication, clean relocated configure/build, all four focused tests, and retained-evidence authentication; relocated prototype tree SHA-256 was `d25f4788f3e5f1b91b103790f7316d3d80559752c2771c961712da0df27048c1` before this results-only backfill.
- `python3 tools/validation/run.py --profile current`: passed all eight selected current-closure checks.

## Objective observations

- `PAMP_R03_DUAL` retained independent base/resolved engines `08 Virtual Analog` and `21 Bass Drum`, with started-lane mask `0x03`. Peak main/aux values were `17,783,603` and `20,547,339` q27.
- `PAMP_R03_EIGHT` retained eight distinct base records `[0, 3, 6, 9, 12, 15, 18, 21]`, started-lane mask `0xff`, and 278 local triggers. Peak main/aux values were `19,390,169` and `15,773,479` q27.
- `PAMP_R03_MODEL_LOCAL` moved lane 1 from base engine 8 through resolved engines 8 through 16 while lane 2 remained at engine 20. Both voices started.
- `PAMP_R03_RNG_ISOLATION` produced byte-identical reference and interleaved stochastic output and equal final RNG state `493075423`.
- `PAMP_R03_24` produced finite, nonzero main and auxiliary output for every source-order engine and bound every index to its frozen descriptive name.
- `PAMP_R03_SILENCE` produced exact zero output for stopped, zero-hit, zero-amplitude, and zero-trigger-route cases.
- All retained nominal conditions reported 100 percent finite samples and zero final-mixer saturation. The intentionally shared-voice comparator diverged in both audio and event trace.
- The authenticated standalone executable is `8,344,536` bytes with SHA-256 `789421110358830f9ea9667977f2d5dce124f375bc2a5166e0d5693df3b23674`.

## Corrections made during validation

- The readiness validator initially rejected an unsupported evidence-retention spelling; the contract was corrected to the accepted `checked-in` value before implementation.
- Architecture review exposed the configured source's process-global random generator. Pamplist now saves and restores one deterministic RNG context per persistent voice. The standalone-versus-interleaved regression and retained render both prove the single-Core boundary.
- No source, DSP, or UI correction was required after the final implementation freeze.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | available | committed 0.2 behavior plus exact source inspection bounded the correction | not a new literature or product-equivalence study |
| Proposal | passed | frozen proposal and ready v2 implementation bundle | noncanonical prototype only |
| Source | passed | locked commit/tree and exact wrapper/vendor hashes | no distribution approval |
| Host structural | passed | Release, ASan/UBSan, state-isolation, snapshot, mapping, and no-allocation tests | no callback deadline measurement |
| Host signal | passed | retained eight-condition, six-partition render matrix and divergent comparator | objective offline evidence only |
| Target build | passed | authenticated JUCE standalone executable and receipt | built but not launched |
| Real-time | not run | none | audio-device timing, CPU, lifecycle, and xruns remain open |
| Connected device | not run | synthetic controller mapping only | no physical endpoint receipt or reconnect test |
| Listening | not run | prior 0.2 user report is design input only | 0.3 separation, balance, clicks, and labels need audition |
| Production integration | not run | none | no canonical records, provider/runtime, packaging, or release claim |
