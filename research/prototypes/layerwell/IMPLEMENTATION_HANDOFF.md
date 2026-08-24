# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `layerwell` revision `0.1`
- Lane: `new-design`
- Index: `research/prototypes/layerwell/prototype-index.json` (`81de5558328a9bcdcd5b535f639d25f6518321527cad67896fb21b5234e8d32b`)
- Working artifact: noncanonical portable Layerwell revision 0.1 Core with two exact resident source Cores, three source-only aligned stereo layers, deterministic retained evidence, pure regular Launch Control 3 DAW-mode mapping, and authenticated Layerwell.app built but not launched

## Exact authorities

- `control_map`: `research/prototypes/layerwell/contract/control-map.json` (`0e358f91aa7573638088cc3e64ae54c32cbe358ec01a6eec6eae4659b8706449`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/layerwell/dsp-topology.json` (`33ecfa2e3b087bf58480b95cc2ca26f8af94b4d00eef3d33fd3582f87c923bf3`)
- `experiment`: `research/prototypes/layerwell/contract/experiment.json` (`4aed382b541a84c03d028a6c8b38c7445f3a500218cf70202372a1e5fd4d3a02`)
- `gaps`: `research/prototypes/layerwell/contract/GAPS.md` (`b7c9cbacf950730b6e3393745c86ca90f9b7b91cf8b250fa506d534c4efb037e`)
- `implementation_contract`: `research/prototypes/layerwell/contract/implementation-contract.json` (`b826c2380c3392cb2c50f34380e967403abe2ccccd3dad6e8562d1e89cd96777`)
- `proposal`: `research/proposals/layerwell.md` (`631084a81e5a012a6029f2a4a072772a6adae07e2e1156d92d90ceb567ea1b21`)
- `results`: `research/prototypes/layerwell/contract/RESULTS.md` (`7cea9f220e3f56338b2901081bd6eba6c37aae7f51dd770cd203f2cad1c7bf0a`)
- `source_package_handoff`: `research/prototypes/layerwell/source-dependencies.json` (`7dec0404d4a5b11acb28ab169c3451988a72a8dc48f133252b2166ddf533263f`)
- `state_matrix`: `research/prototypes/layerwell/contract/state-matrix.md` (`b320414fbab630dd6f38e6043776c86409c35b50df683f84c1cf5b69cf4987a6`)
- `validation_plan`: `research/prototypes/layerwell/contract/validation-plan.json` (`ea43e3fb2480655e908d06aaf9f95654da4f1b5ce1b177e8a468bdf8cea9a9cc`)

## Allowed edits

- prototype-owned capture, fixed storage, event ordering, mixing, diagnostics, renderer, fixture, and test mechanics that preserve revision 0.1 semantics
- prototype-owned source adapters that continue to terminate at the frozen public source mappings and Cores
- prototype-owned accepted-state surface projection, pure protocol adapter, and optional JUCE host presentation
- CMake-only composition corrections that retain upstream bytes, exact source authorities, and unchanged standalone defaults
- noncanonical topology, evidence, notice routing, and promotion annotations

## Reusable entry points

- SchussInstrumentLab::Core
- tide_pit_core
- generative_drum_machine_core
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
- persistence, recovery, external synchronization, richer sample operations, more resident sources, or more layers
- distribution licensing, packaging, signing, and notarization
- any canonical Schuss identity, graph, provider, application-library, or runtime promotion

No app launch, device, real-time, listening, distribution, or production claim is made.
