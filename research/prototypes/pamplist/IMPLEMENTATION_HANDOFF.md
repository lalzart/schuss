# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `pamplist` revision `0.5`
- Lane: `new-design`
- Index: `research/prototypes/pamplist/prototype-index.json` (`9108b37d5eb0e841eed075caea22e98370ffaa7aedb7c3f44faad9e57e715acb`)
- Working artifact: noncanonical portable Pamplist 0.5 Core with seven independent deterministic lane/voice systems, accepted Voice/Motion context, exactly sixteen visible semantic controls, binary Trigger Enable, source-order model names, an exact-dry clearable six-mode post-sum cohesion body, retained objective renders, and a built but unlaunched standalone app

## Exact authorities

- `control_map`: `research/prototypes/pamplist/contract-r05/control-map.json` (`1cdc7010eee169caeaf21026ecf448db5317a130a24423578a17d357d35c07cf`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/pamplist/dsp-topology.json` (`4be41de61132b78423e12c6a3ab25680633ea6a441906c3f227b3d89afb7a014`)
- `experiment`: `research/prototypes/pamplist/contract-r05/experiment.json` (`ea6c542ce6e5c873acccae93f424f345e23d90330163ac074b49d37c04f4f568`)
- `gaps`: `research/prototypes/pamplist/contract-r05/GAPS.md` (`ab89c258c1298fa8a55011c3577d5df05dbf995302fbdb22efe5e425ca032212`)
- `implementation_contract`: `research/prototypes/pamplist/contract-r05/implementation-contract.json` (`63b95b295a67f8712845bcb460b1511f5cfc6ddb4274b88ac104eb4ce9761e4d`)
- `proposal`: `research/proposals/pamplist-r05.md` (`8c15dd3c38ca8a585c2603d219daccbba9446dff7a08156e0ba579fac25e1423`)
- `results`: `research/prototypes/pamplist/contract-r05/RESULTS.md` (`66b396b68934233fd613dca6f04cefb28a187b267fccc71d3a26210e20895659`)
- `source_package_handoff`: `research/prototypes/pamplist/source-dependencies.json` (`d4d16dab1cb3225c012f2be3d2edf841107e82f7cd92e15ce64f856c668bf443`)
- `state_matrix`: `research/prototypes/pamplist/contract-r05/state-matrix.md` (`b02893d98bf48327f3e210284ac8de5d3f46091765345778e4e67cb91e657656`)
- `validation_plan`: `research/prototypes/pamplist/contract-r05/validation-plan.json` (`dc67acc53e79cd7dd865da7782ecb9384260bf3884bd71dca96a1832d5a95a06`)

## Allowed edits

- prototype-owned rational timeline, masks, keyed decisions, lane shapes, seven local modulation rows, seven-voice Core, dry mixer, shared cohesion body, final output, renderer, fixtures, and tests
- prototype-owned per-voice source RNG context isolation and source-order model labels without upstream mutation
- prototype-owned accepted-state projection, whole-value control snapshots, accepted Voice/Motion context, contextual controller mapping, portable sixteen-slot surface model, and optional standalone presentation
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

- hands-on voice separation, balance, pattern legibility, route scale, model-label clarity, common-body cohesion, masking, transition, Duck, and Clear approval
- fresh app launch, visual inspection, live callback timing, lifecycle, and xrun measurement
- physical Launch Control 3 endpoint selection, receipt, reconnect, feedback, and control feel
- optional mute, solo, pan, manual drone start, external clock, variable Euclidean length, cross-lane operators, presets, polyphony, additional effects, and plug-in formats
- any Ksoloti or Gills adaptation and resource strategy
- any canonical identity, provider, application runtime, distribution, or production promotion

No app launch, device, real-time, listening, distribution, or production claim is made.
