# Pamplist 0.6: Control Response and Impact Trails implementation results

> Status: host-signal and authenticated target-build closure passed; live, visual, listening, device, and production evidence remain deferred

## Proposal and contract fingerprints

- Proposal: `research/proposals/pamplist-r06.md`
- Proposal SHA-256: `a923b9665a6024d986a5ae8ac094aa9d41cd634de03c45c8ca954630ea43e917`
- Implementation contract: `implementation-contract.json`
- Implementation contract SHA-256: `a0ae706d4943be17e290297f06a9587c40222a8cbe6f412184b52af9f57b971c`
- Retained evidence manifest SHA-256: `16ca1acc389c843417f6b30b24216fc80f80e356adc77ff07eb1748a4f476f94`
- Authenticated JUCE receipt SHA-256: `e9101756eb78d3f1a1ca7b13a8d5804383b9dbcc772ea83ab71152b59ee2b908`

## Commands and results

- `python3 research/prototypes/pamplist/tests/verify_source_authority.py`:
  passed for configured `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`,
  tree `58917f3e2e46a30337cfb6292a3504845b1d5552`.
- `python3 research/prototypes/pamplist/tests/run_focused.py`: passed six
  Release and six ASan/UBSan CTests, including Core response, controller,
  sixteen-slot UI, whole accepted-Snapshot publication, zero-allocation audio,
  and activity reduction/history.
- `python3 research/prototypes/pamplist/tests/render_evidence.py --reproduce`:
  passed all four conditions at host blocks 1, 16, 64, 128, 257, and 512 with
  byte-exact artifacts within the frozen build.
- `python3 research/prototypes/pamplist/tests/render_evidence.py --check`:
  authenticated the retained revision 0.6 evidence and revision 0.5 dry
  comparator.
- `python3 research/prototypes/pamplist/tests/build_juce.py --reproduce
  --juce-source /Users/lanceship/Projects/schuss/build/cinderwheel-juce-trial/_deps/juce-src`:
  authenticated JUCE 8.0.15 and built `Pamplist.app` without launch or endpoint
  access.
- `python3 research/prototypes/pamplist/tests/build_juce.py --check`: passed.
- `python3 tools/instrument_lab/validate_prototype.py --repo-root .
  --consumer-root research/prototypes/pamplist --write-derived` followed by
  `--check`: passed and advanced the existing noncanonical prototype identity
  to revision 0.6.
- `python3 research/prototypes/pamplist/tests/reproduce_fresh_root.py`: passed
  isolated configure/build, six CTests, source authentication, prototype
  validation, and retained-evidence authentication; copied consumer tree
  SHA-256 `a5eeaba41525a5ea76b9726cda2fe61397fa40773da2fa67eb6a7ce78a30c1c5`.
- `python3 tools/validation/run.py --profile current`: passed all eight selected
  current checks with zero failed, incomplete, or not-run checks.

## Objective observations

- Exact dry comparator: `audio.wav` SHA-256
  `a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912`,
  byte-identical to revision 0.5.
- Phase trigger frames moved from `[0, 24000, 42000, 60000, 78000]` at 0 to
  `[0, 21008, 39008, 57008, 75008, 93008]` at 64 while accepted Rate and Hits
  stayed fixed. Rotate 3 produced `[6000, 24000, 42000, 60000, 78000]` with
  the same five-of-sixteen cardinality.
- Trigger-only Pulse and Triangle audio/events were exact. With Pitch Motion
  at 0.8, every other frozen Shape differed from Pulse by normalized stereo
  RMS `0.05559` through `0.06919`.
- Individual Global low/high normalized stereo RMS differences were Drive
  `0.076970`, Root `0.000582`, Spread `0.001392`, Tail `0.004861`, Damping
  `0.002297`, Width `0.002786`, and Duck `0.002044`. All exceeded `5e-4` with
  zero nominal saturation or recovery.
- The silent-input pre-Clear tail peaked at `0.0009083` normalized. After
  Clear had zero nonzero samples; the matched no-Clear continuation had
  16,381 nonzero stereo samples. Musical, scheduler, and source state matched
  the reference except the declared Clear generation/count/effect history.
- All seven cumulative lane-energy values were finite, nonzero, monotone, and
  partition exact. The portable history reached and held capacity 192, emitted
  one Clear marker, and produced an exact-zero rebase on rollback.
- Built binary: 8,373,160 bytes, SHA-256
  `4cb81b67b272cecbb9f7d0a38e32ebb0aceca1c85bc11c29f0502b81b94e7219`.

## Corrections made during validation

- The first Global response fixture attenuated both Master and every voice,
  making Root fall below the frozen listening-level threshold. The fixture was
  corrected to Pamplist's normal seven-voice operating level; coefficients and
  tolerance were not weakened.
- The first lane-energy test assumed an inactive lane would trigger within its
  first 512 samples while leaving its Depth at zero. The fixture now sets Depth
  explicitly and observes a deterministic trigger window.
- A first broad response render used the dry-comparator all-hit pattern, which
  under-excited several modal comparisons. The response condition now uses the
  same varied five-through-eleven-hit fixture as the passing focused test; the
  retained dry comparator remains unchanged.
- Duplicate accepted UI polls initially looked like rollback. The reducer now
  treats equal frame counts as a quiet duplicate and only smaller counts as a
  reset/rebase.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | bounded predecessor/source inspection and user audition report | no external novelty or product search |
| Proposal | passed | exact proposal and ready revision 0.6 bundle | approval applies only to this bounded prototype revision |
| Source | passed | configured macro-voice and authenticated JUCE source receipts | no new source release or provider identity |
| Host structural | passed | Release, ASan/UBSan, allocation, snapshot, surface, activity, prototype, and current-profile tests | not live callback evidence |
| Host signal | passed | four-condition six-partition retained matrix and exact dry comparator | not subjective audibility or musical approval |
| Target build | passed | authenticated 8.0.15 standalone compiled, linked, fingerprinted, and copied-root Core/evidence reproduction passed | app not launched; visual layout not inspected |
| Real-time | deferred | no endpoint opened | deadline, CPU, xruns, and lifecycle unknown |
| Connected device | deferred | synthetic mapping only | physical identity, receipt, feel, feedback, and reconnect unknown |
| Listening | deferred | no revision 0.6 playback performed by this validation | control strength, Clear usefulness, and trail readability need user audition |
| Production integration | deferred | prototype identity remains noncanonical | library/runtime, package, signing, distribution, and release unclaimed |
