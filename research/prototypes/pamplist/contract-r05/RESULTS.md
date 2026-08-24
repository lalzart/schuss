# Pamplist 0.5 sixteen-knob surface implementation results

> Status: implementation, source, host structural, host signal, authenticated
> standalone, relocated, routine workspace, and the post-audition Trigger
> interaction correction passed

This file records only revision 0.5 evidence. Revision 0.4 remains predecessor
authority for its own design and retained artifacts.

## Proposal and contract fingerprints

- Proposal: `research/proposals/pamplist-r05.md`
- Proposal SHA-256: `8c15dd3c38ca8a585c2603d219daccbba9446dff7a08156e0ba579fac25e1423`
- Implementation contract: `implementation-contract.json`
- Revision 0.4 Trigger-On audio comparator SHA-256:
  `a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912`

## Commands and results

- `validate_implementation_bundle.py contract-r05 --phase structure` and
  `--phase ready`: passed before implementation source edits.
- `python3 research/prototypes/pamplist/tests/verify_source_authority.py`:
  passed for `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, synthesis
  tree `58917f3e2e46a30337cfb6292a3504845b1d5552`, with exact declared files.
- `python3 research/prototypes/pamplist/tests/run_focused.py`: passed five
  Release CTests and the same five ASan/UBSan CTests. They cover Core, contextual
  mapping, the pure sixteen-slot UI model, all seven lanes' independent Trigger
  Off/On application, whole snapshots, and post-prepare allocation.
- `python3 research/prototypes/pamplist/tests/render_evidence.py --reproduce
  --output build/pamplist-r05-trigger-evidence-new`: passed all four conditions
  at blocks 1, 16, 64, 128, 257, and 512 with byte-identical per-condition
  artifacts across partitions. The validated successor replaced the retained
  directory; its predecessor remains recoverable under
  `build/pamplist-r05-evidence-before-trigger-ui-fix`.
- `python3 research/prototypes/pamplist/tests/render_evidence.py --check`:
  passed retained file-set, hash, predecessor, Trigger, controller, surface,
  state, signal, and partition validation.
- `python3 research/prototypes/pamplist/tests/build_juce.py --reproduce
  --juce-source /Users/lanceship/Projects/schuss/build/cinderwheel-juce-trial/_deps/juce-src`:
  authenticated JUCE 8.0.15, asserted the two eight-slider rows plus the
  Trigger click-toggle and active-gesture projection guard, configured,
  compiled, and linked the standalone without launch. The 8,355,624-byte
  executable SHA-256 is
  `9beefec36337cc0543f17d6b079fdeca2e658d91460a4e32f822889c1096e7d5`.
- `python3 research/prototypes/pamplist/tests/build_juce.py --check`: passed the
  exact source/input/artifact receipt; app, audio, and MIDI endpoints remained
  unopened.
- `python3 tools/instrument_lab/validate_prototype.py --repo-root .
  --consumer-root research/prototypes/pamplist --write-derived`, followed by
  `--check`: passed authority hashes, topology, promotion needs, and generated
  handoff validation.
- `python3 research/prototypes/pamplist/tests/reproduce_fresh_root.py`: passed a
  relocated source-authenticated Release build, five CTests, retained evidence,
  and post-run tree equality.
- `python3 tools/validation/run.py --profile current`: passed all eight selected
  checks in 62.863 seconds with zero failed, incomplete, or unrun checks.

## Objective observations

- The portable model and JUCE source expose exactly sixteen rotary controls:
  eight contextual top-row slots and eight bottom-row slots. Voice and Motion
  each cover sixteen unique semantic targets; their Sequencer rows are exact.
- Global exposes eight cohesion controls, BPM, Master, and six explicitly
  disabled/no-op slots. Global editing and Clear preserve accepted lane mode
  and all lane/voice records.
- Accepted `LaneControlMode` is sanitized, included in whole snapshots, and is
  the sole mapping/presentation authority. One same-lane positive edge toggles
  it; a held positive and release do not. Selecting another lane preserves it.
- Trigger CC values 0 and 63 accept exact Off, produce no triggers or started
  voices, and render exact silence. Values 64 and 127 accept exact On and have
  byte-identical PCM, events, accepted state, and source RNG state.
- The application Trigger rotary now toggles once on mouse-down instead of
  requiring a half-scale drag through JUCE's default 250-pixel sensitivity.
  Accepted-state projection also leaves every rotary's local value untouched
  while its user gesture is active, then resumes from the accepted Snapshot.
- `PAMP_R05_AUDIO_CMP` audio SHA-256 is
  `a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912`,
  exactly matching revision 0.4 `PAMP_R04_DRY7`. All seven voices start and the
  accepted source-order base models remain 0, 3, 6, 9, 12, 15, and 21.
- All retained output is finite and Q27 bounded; nominal invalid, non-finite,
  recovery, and saturation diagnostics are zero. Evidence manifest SHA-256:
  `0fd7f86e9d205938ff789f390a3ee27d80a410362422ff9471512383cee5ef02`.
- The user's first revision 0.5 audition exposed the off-default Trigger GUI
  defect. Codex performed no app launch, endpoint access, physical controller
  session, or follow-up audition of this correction.

## Corrections made during validation

- The first JUCE source-cardinality assertion counted conditional references
  to the bottom slider bank as declarations. It was narrowed to the two exact
  typed member declarations before the authenticated receipt was retained.
- The first Trigger event comparator included concatenated-file frame offsets.
  It was corrected to compare each fresh-reset part on its own relative
  timeline; no DSP, mapping, or accepted-state tolerance was changed.
- The first revision 0.5 application used a generic continuous rotary for the
  binary Trigger. Its one-step range and JUCE's default drag sensitivity made
  Off-to-On require roughly 125 pixels, while periodic accepted projection
  could restore Off during a gesture. Trigger now has one-click binary
  interaction, and projection is suspended only for the actively operated
  control. DSP, Trigger threshold, MIDI mapping, and lane ownership are
  unchanged.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | Revision 0.5 proposal and predecessor audit | Reference analysis is not implementation identity |
| Proposal | passed | Approved fingerprint plus structure/ready gates | Approval is revision 0.5 only |
| Source | passed | Configured revision/tree/files and project-owned authorities | No distribution approval or canonical source release |
| Host structural | passed | Five Release plus five sanitizer CTests | Synthetic host only |
| Host signal | passed | Four-condition/six-partition retained matrix and exact predecessor comparator | Objective behavior is not musical approval |
| Target build | passed | Authenticated JUCE receipt, sixteen-control assertion, and executable hash | Built but not launched |
| Real-time | not run | Deferred | No callback deadline, CPU, lifecycle, or xrun proof |
| Connected device | not run | Deferred | No endpoint, installed mapping, gesture, feedback, or reconnect proof |
| Listening | partial defect report | User found the off-default Trigger rotary effectively inoperable | Corrected build still requires user retest |
| Production integration | not run | Deferred | Noncanonical prototype only |
