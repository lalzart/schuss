# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `pamplist` revision `0.2`
- Lane: `new-design`
- Index: `research/prototypes/pamplist/prototype-index.json` (`f1506f443621625229e3a9ea5fcedc9b93124f37f5d25901a6623eb8d356d40c`)
- Working artifact: noncanonical portable Pamplist 0.2 Core with eight deterministic clock-modulation lanes, one authenticated complete macro voice, two separate q27 outputs, retained objective renders, a regular Launch Control 3 adapter, and a built but unlaunched standalone app

## Exact authorities

- `control_map`: `research/prototypes/pamplist/contract/control-map.json` (`aa8c59a568c16999f72ef362b639c2d3fa24d02ee81ca47e7a7a9f4e2c096263`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/pamplist/dsp-topology.json` (`8218e529caf9991d9066f989432c631009f365a6ccd99ce7e172216f9efa0020`)
- `experiment`: `research/prototypes/pamplist/contract/experiment.json` (`63152aa19c967dd0343258a6755d4be8a97400e4299e420472b82a98209acdab`)
- `gaps`: `research/prototypes/pamplist/contract/GAPS.md` (`dccf4e25cb9a51979c56ba1b8f551cb8386d33c75f0cec284393fe53399249ef`)
- `implementation_contract`: `research/prototypes/pamplist/contract/implementation-contract.json` (`9fc9a43492515c8ec5741b353c09697e79153a76b94c81edf129609da2bffaad`)
- `proposal`: `research/proposals/pamplist.md` (`bf110cd1bfe6b86e032bc993e0baf705d7459182c891d095a9a1a39ce1789af3`)
- `results`: `research/prototypes/pamplist/contract/RESULTS.md` (`ce2c9ac378badd19f78bc1bbb6b3208ff077a84bcdb043d9f2216cc0e147d5b2`)
- `source_package_handoff`: `research/prototypes/pamplist/source-dependencies.json` (`305957e264e6ea14a7e6b6e18a4100c49d36306bbf52dbd574c2e4711b0ec6be`)
- `state_matrix`: `research/prototypes/pamplist/contract/state-matrix.md` (`ab7f54380fa795fca4b72c6e4e7ad0a2905c72c4b27be900c5486b4e6b7533c7`)
- `validation_plan`: `research/prototypes/pamplist/contract/validation-plan.json` (`5853897aa31e6eafaa3ea4c632099f7c22c67bf45d9ded3967f8f4c5c5cb0ba2`)

## Allowed edits

- prototype-owned rational timeline, masks, keyed decisions, lane shapes, modulation matrix, Core, renderer, fixtures, and tests
- prototype-owned accepted-state projection, whole-value control snapshots, controller mapping, and optional standalone presentation
- prototype-only topology, evidence, and handoff annotations
- exact source-authentication corrections that preserve upstream bytes and source identity

## Reusable entry points

- SchussInstrumentLab::Core
- schuss::pamplist::Core
- schuss::pamplist::MacroVoice
- schuss::pamplist::AtomicSnapshot
- schuss::pamplist::ControllerAdapter
- schuss::pamplist::mapMidiCc
- schuss::pamplist::applyMapping
- pamplist_core
- pamplist-render
- pamplist

## Required commands

- python3 research/prototypes/pamplist/tests/verify_source_authority.py
- python3 research/prototypes/pamplist/tests/run_focused.py
- python3 research/prototypes/pamplist/tests/render_evidence.py --check
- python3 research/prototypes/pamplist/tests/build_juce.py --check
- python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/pamplist --check
- python3 research/prototypes/pamplist/tests/reproduce_fresh_root.py

## Stop conditions

- the approved proposal or ready implementation-contract fingerprint changes
- a frozen rate, shape, control-map, experiment, render, source, or target-build authority drifts
- a failure is relabeled or an objective tolerance is weakened without a newly approved revision
- work expands to app launch, live endpoints, hardware, listening, distribution, canonical records, or production without explicit authorization
- an evidence level would be promoted without its named proof

## Open decisions

- hands-on balance, pattern legibility, route scale, and engine-transition approval
- fresh app launch, visual inspection, live callback timing, lifecycle, and xrun measurement
- physical Launch Control 3 endpoint selection, receipt, reconnect, feedback, and control feel
- optional external clock, variable Euclidean length, cross-lane operators, presets, polyphony, effects, and plug-in formats
- any Ksoloti or Gills adaptation and resource strategy
- any canonical identity, provider, application runtime, distribution, or production promotion

No app launch, device, real-time, listening, distribution, or production claim is made.
