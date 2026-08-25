# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `layerwell` revision `0.2`
- Lane: `new-design`
- Index: `research/prototypes/layerwell/prototype-index.json` (`121261a24d43da849e8a746f644a2e52b3b6fd33a93fcae394e98833f0bb4cc7`)
- Working artifact: noncanonical Layerwell revision 0.2 Core and authenticated but unlaunched app with complete accepted Tide Pit/Pamplist panels, three source-only aligned stereo layers, sole-layer non-destructive trim, deterministic retained evidence, and pure regular Launch Control 3 DAW-mode mapping

## Exact authorities

- `control_map`: `research/prototypes/layerwell/contract-r02/control-map.json` (`21309639e5f258259f8bc61982412da02298483e1fb7072368e99c205a326007`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/layerwell/dsp-topology.json` (`fd6be26b6ba09e8b5e11a381a8562021396f58510dcee61d44859754fe27c13f`)
- `experiment`: `research/prototypes/layerwell/contract-r02/experiment.json` (`9b5467b182603d0670cad0425f1f198b5f69e343dc1e89c3a9bc49e74434d35b`)
- `gaps`: `research/prototypes/layerwell/contract-r02/GAPS.md` (`5ec8c9671f37a92c45b4340d2fb48cb83d72cfb798d400fd6ff50c4d6ae54559`)
- `implementation_contract`: `research/prototypes/layerwell/contract-r02/implementation-contract.json` (`f365ce466626df13f9f96fc307aabfadbde807044f9d7fe87da3749074c92456`)
- `proposal`: `research/proposals/layerwell-r02.md` (`56d1ab8ab8575e4a6f59eabbe976db11986ab02cf9ae750ae5cfae88584efeb6`)
- `results`: `research/prototypes/layerwell/contract-r02/RESULTS.md` (`e36750d80160e8e31802e205d823fd778157134919787ac30fd056fe46cf94e4`)
- `source_package_handoff`: `research/prototypes/layerwell/source-dependencies.json` (`1ff5079cb8f029ebbf681948f24b60836b4d50cf02e32854d4c02b23602a3471`)
- `state_matrix`: `research/prototypes/layerwell/contract-r02/state-matrix.md` (`921c7a9aeba9ec6311c91b8b25ae159fec2ee598db887e6945538afee2fa8ccb`)
- `validation_plan`: `research/prototypes/layerwell/contract-r02/validation-plan.json` (`74862e7efd2029b1c350b800f4199fea18858db0eb790ca033e56e88af327cf7`)

## Allowed edits

- prototype-owned capture, fixed storage, event ordering, mixing, diagnostics, renderer, fixture, and test mechanics that preserve revision 0.1 capture semantics while adding the revision 0.2 sole-layer trim window
- prototype-owned source adapters that terminate at the frozen Tide Pit and Pamplist public mappings, UI models, actions, and Cores
- prototype-owned accepted-state embedded panel projection, bounded visual reductions, fixed GUI command queue, pure protocol adapter, and optional JUCE host presentation
- CMake-only composition corrections that retain upstream bytes, exact source authorities, and unchanged standalone defaults
- noncanonical topology, evidence, notice routing, and promotion annotations

## Reusable entry points

- SchussInstrumentLab::Core
- tide_pit_core
- tide_pit_ui_model
- pamplist_core
- layerwell_core
- layerwell::Core
- layerwell::SourceRack
- layerwell::AtomicSnapshot
- layerwell::LaunchControl3Adapter
- layerwell-render
- layerwell-instrument

## Required commands

- python3 research/prototypes/layerwell/tests/verify_source_authorities.py
- python3 research/prototypes/layerwell/tests/run_focused.py
- python3 research/prototypes/layerwell/tests/render_evidence.py --check
- python3 research/prototypes/layerwell/tests/run_source_regressions.py
- python3 research/prototypes/layerwell/tests/build_juce.py --check
- python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/layerwell --check
- python3 research/prototypes/layerwell/tests/reproduce_fresh_root.py

## Stop conditions

- the approved proposal or ready-contract fingerprint drifts
- a resident source index, contract, source-equivalence record, dependency handoff, adapter, notice, mapping, or public Core drifts
- partition PCM, accepted state, capture boundary, source advance, committed storage, allocator count, protocol trace, target-build receipt, or negative comparator drifts
- work expands to app launch, endpoint access, physical hardware, listening, distribution, canonical records, production runtime, or Git publication without new authorization
- an evidence level would be promoted without its named proof

## Open decisions

- authorized app launch, fresh visual inspection, live audio deadline measurement, and listening
- physical regular Launch Control 3 endpoint selection, receipt, reconnect, and feedback
- visual approval, trim feel and seam audition, persistence, recovery, external synchronization, richer sample operations, more resident sources, or more layers
- distribution licensing, packaging, signing, and notarization
- any canonical Schuss identity, graph, provider, application-library, or runtime promotion

No app launch, device, real-time, listening, distribution, or production claim is made.
