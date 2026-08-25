# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `pamplist` revision `0.6`
- Lane: `new-design`
- Index: `research/prototypes/pamplist/prototype-index.json` (`25cef61387c088ebb7f721d2803202712cdbbe11f900167dee115a7e404a1cd3`)
- Working artifact: noncanonical portable Pamplist 0.6 Core with seven independent deterministic lane/voice systems, accepted Voice/Motion context, exactly sixteen visible semantic controls, dependency-aware Phase/Shape/Rotate help, materially responsive exact-dry shared cohesion, cumulative accepted lane telemetry, a fixed seven-colour Impact Trails display, retained objective renders, and a built but unlaunched standalone app

## Exact authorities

- `control_map`: `research/prototypes/pamplist/contract-r06/control-map.json` (`d7a4a602ec55d27def522939eff47a75210412cdb1ec669f8ca0463e2c7285ab`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/pamplist/dsp-topology.json` (`eebed4e7eb880122031863e1adad348b7fa75f3e6e6f453aa7f567a8b9a54be9`)
- `experiment`: `research/prototypes/pamplist/contract-r06/experiment.json` (`5ad30e07bcb410df5a67c93d5bd446decd98ccf40f6ab44f61211b76bee975b2`)
- `gaps`: `research/prototypes/pamplist/contract-r06/GAPS.md` (`6f101e703a77bde18ded0817955c3985fa5013c77b78fdcbc7682b9839ff7da7`)
- `implementation_contract`: `research/prototypes/pamplist/contract-r06/implementation-contract.json` (`a0ae706d4943be17e290297f06a9587c40222a8cbe6f412184b52af9f57b971c`)
- `proposal`: `research/proposals/pamplist-r06.md` (`a923b9665a6024d986a5ae8ac094aa9d41cd634de03c45c8ca954630ea43e917`)
- `results`: `research/prototypes/pamplist/contract-r06/RESULTS.md` (`a9c29d66f542e7d047b86c502695d7fd981b62930e12e073bb01f77e5327d5eb`)
- `source_package_handoff`: `research/prototypes/pamplist/source-dependencies.json` (`d7b82c51046bf96d68b726eba1ebbfc989e0d03fc4daab47f4e71f6fd71f5c38`)
- `state_matrix`: `research/prototypes/pamplist/contract-r06/state-matrix.md` (`d20ff9114591fb1bdd0fed8a1fa62b43953b95d9daec168094dea4c640444567`)
- `validation_plan`: `research/prototypes/pamplist/contract-r06/validation-plan.json` (`fe084a5ff2b11669516bb66e99aefef36eda105f64d2cc7eac687a91a5bac1bc`)

## Allowed edits

- prototype-owned rational timeline, masks, keyed decisions, lane shapes, seven local modulation rows, seven-voice Core, dry mixer, shared cohesion body, final output, renderer, fixtures, and tests
- prototype-owned per-voice source RNG context isolation and source-order model labels without upstream mutation
- prototype-owned accepted-state projection, whole-value control and accepted snapshots, accepted Voice/Motion context, contextual controller mapping, portable sixteen-slot surface model, cumulative lane telemetry, fixed activity history, and optional standalone presentation
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
- schuss::pamplist::surfaceModel
- schuss::pamplist::applySurfaceValue
- schuss::pamplist::ActivityReducer
- schuss::pamplist::ImpactHistory
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
- a frozen rate, shape, model-name table, control-map, experiment, render, source, or target-build authority drifts
- a failure is relabeled or an objective tolerance is weakened without a newly approved revision
- work expands to app launch, live endpoints, hardware, listening, distribution, canonical records, or production without explicit authorization
- an evidence level would be promoted without its named proof

## Open decisions

- hands-on voice separation, balance, pattern legibility, route scale, model-label clarity, common-body cohesion, masking, transition, Duck, Clear, colour separation, trail persistence, and visual readability approval
- fresh app launch, visual inspection, live callback timing, lifecycle, and xrun measurement
- physical Launch Control 3 endpoint selection, receipt, reconnect, feedback, and control feel
- optional mute, solo, pan, manual drone start, external clock, variable Euclidean length, cross-lane operators, presets, polyphony, additional effects, and plug-in formats
- any Ksoloti or Gills adaptation and resource strategy
- any canonical identity, provider, application runtime, distribution, or production promotion

No app launch, device, real-time, listening, distribution, or production claim is made.
