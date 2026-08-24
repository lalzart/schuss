# Pamplist 0.4: Seven Voices and Cohesion Bus implementation results

> Status: implementation, source, host, authenticated standalone, relocated,
> and routine workspace evidence passed

## Proposal and contract fingerprints

- Proposal: `research/proposals/pamplist-r04.md`
- Proposal SHA-256: `d5ef3c2d37e4472d34f383eddd4deee148ede4794c6dfcbecf110dbc851ba193`
- Implementation contract: `implementation-contract.json`

## Commands and results

- `validate_implementation_bundle.py contract-r04 --phase structure`: passed.
- `validate_implementation_bundle.py contract-r04 --phase ready`: passed.
- `python3 research/prototypes/pamplist/tests/verify_source_authority.py`:
  passed for `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, synthesis
  tree `58917f3e2e46a30337cfb6292a3504845b1d5552`, with a clean authenticated
  subtree and all declared file hashes exact.
- `python3 research/prototypes/pamplist/tests/run_focused.py`: passed four
  Release CTests and the same four sanitizer CTests. These cover Core,
  contextual control mapping, whole snapshots, and post-prepare allocation.
- `python3 research/prototypes/pamplist/tests/render_evidence.py --reproduce
  --output research/prototypes/pamplist/contract-r04/evidence`: passed all eight
  conditions at host blocks 1, 16, 64, 128, 257, and 512 with identical
  per-condition artifacts across partitions.
- `python3 research/prototypes/pamplist/tests/render_evidence.py --check`:
  passed retained file-set, hash, comparator, state, and signal validation.
- `python3 research/prototypes/pamplist/tests/build_juce.py --reproduce
  --juce-source /Users/lanceship/Projects/schuss/build/cinderwheel-juce-trial/_deps/juce-src`:
  authenticated the exact JUCE 8.0.15 tree, configured, compiled, and linked the
  standalone without launch. The 8,327,528-byte executable SHA-256 is
  `9675f6ad0c2c4522be9f52be8006b628e19f22730e14b29d1003a424843aa0a8`.
- `python3 research/prototypes/pamplist/tests/build_juce.py --check`: passed the
  retained source/input/artifact receipt; the app and audio/MIDI endpoints were
  not opened.
- `python3 tools/instrument_lab/validate_prototype.py --repo-root .
  --consumer-root research/prototypes/pamplist --write-derived`, followed by
  `--check`: passed exact authority hashes, topology, promotion needs, and
  generated handoff validation.
- `python3 research/prototypes/pamplist/tests/reproduce_fresh_root.py`: passed a
  relocated repository validation, clean Release build, four CTests, source
  authentication, retained evidence check, and post-run tree equality.
- `python3 tools/validation/run.py --profile current`: passed all eight selected
  checks in 63.706 seconds with zero failed, incomplete, or unrun checks.

## Objective observations

- Cardinality is exactly seven lane/voice records, seven started bits, eight
  page states, and no hidden eighth source instance.
- `PAMP_R04_DRY7` and `PAMP_R04_DRY_CMP` have byte-identical audio; both report
  zero dry/effect difference energy. This includes maximum Drive on the bypass
  comparator, so Drive cannot leak when Cohere has settled to zero.
- `PAMP_R04_COHERE` diverges in PCM and state from the dry comparator with
  difference energy `74.29340914420621`; `PAMP_R04_SWEEP` reports
  `1215.8661539311593` while retaining a maximum pole of
  `0.9999948143959045`, below one.
- `PAMP_R04_CLEAR` retains a nonzero tail before Clear, then exact-zero mode,
  duck, and output state after one accepted generation. Global controller
  traces select first, clear on the next positive edge, and count 18 deliberate
  Global no-ops without changing any lane or voice record.
- Every retained sample is finite and Q27 bounded. Nominal final saturation,
  source non-finite, effect recovery, invalid-control, and unsupported-process
  diagnostics are all zero. `PAMP_R04_SILENCE` is exact silence and all 24
  source-order models remain active with isolated source randomness.
- Evidence manifest SHA-256:
  `ed6c1e33a46d69c5a4d6cd5efc527ae9ae078c4a063da27f2f2eedc0d611aa7f`.
- No subjective audition was performed; musical cohesion, masking, and control
  feel remain open.

## Corrections made during validation

- Complete metadata review found that a simultaneous seed change and effect
  Clear could reset the modal history but omit Clear count/event provenance.
  The acceptance order was corrected and a focused regression added. Focused,
  sanitizer, render, and target-build evidence were then regenerated.
- The first relocated attempt found an ignored Python `__pycache__` present in
  the source tree while the relocation helper intentionally excluded caches.
  Removing that generated cache made the unchanged source/evidence tree compare
  exactly; no implementation or retained-evidence byte was altered for it.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | Proposal evidence table and claims ledger | Design reference is not implementation equivalence |
| Proposal | passed | Approved fingerprint plus structure/ready gates | Approval is revision 0.4 only |
| Source | passed | Configured revision, tree, clean status, and exact file hashes | No distribution approval or canonical source release |
| Host structural | passed | Release and sanitizer CTests | Synthetic host only |
| Host signal | passed | Retained eight-condition/six-partition render matrix | Objective behavior is not musical approval |
| Target build | passed | Authenticated JUCE receipt and executable hash | Built but not launched |
| Real-time | not run | Deferred | No callback deadline, CPU, lifecycle, or xrun proof |
| Connected device | not run | Deferred | No physical endpoint or Custom Mode receipt |
| Listening | not run | Deferred | No audition or control-feel judgment |
| Production integration | not run | Deferred | Noncanonical prototype only |
