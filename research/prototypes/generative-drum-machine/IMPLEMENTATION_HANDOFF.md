# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `generative-drum-machine` revision `0.6`
- Lane: `new-design`
- Index: `research/prototypes/generative-drum-machine/prototype-index.json` (`ecfa9c33c60ba6e35ad61e34c245533ed5fb4515a9c6e53dbc1ae504f80f6d4e`)
- Working artifact: noncanonical portable C++17 fifteen-study/six-lane streaming drum Core with four pooled Braids voices, six persistent voice-shape banks, regular Tide Pit LC3 topology adapter, deterministic offline 48 kHz evidence, and built unlaunched revision 0.6 JUCE standalone audition app

## Exact authorities

- `control_map`: `research/prototypes/generative-drum-machine/contract/control-map.json` (`49b01bc54605d89a2a1feaa8b1e9edc071742a9c09c9708e8de3144608c00d0e`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/generative-drum-machine/dsp-topology.json` (`e6797ef5e83434aa6f12667be93dd903bb5a220ec7d034d1686c7b289aa51c2c`)
- `experiment`: `research/prototypes/generative-drum-machine/contract/experiment.json` (`36a28d746f02214a52a64a0d2bfbb7d0af2f92870968d209741fe6c5d6221df9`)
- `gaps`: `research/prototypes/generative-drum-machine/contract/GAPS.md` (`a5320a1f63f7eb1e9d0b2803e632beae7b8f2d09bfe9cfb8449384f5401f7b40`)
- `implementation_contract`: `research/prototypes/generative-drum-machine/contract/implementation-contract.json` (`79c4998fecbc9914c65cdaf89834e90b4c974af3521122ab42babd6e566211d2`)
- `proposal`: `research/proposals/schuss-generative-drum-machine.md` (`e64c62891f34cbe085bace71c4ea4536ec0665340ae566aa24734885da4728f7`)
- `results`: `research/prototypes/generative-drum-machine/contract/RESULTS.md` (`8e1ccc5a74939ed5508486448386bdc2dd32346c75c45436611dff507b719a9c`)
- `source_package_handoff`: `research/prototypes/generative-drum-machine/contract/source-dependencies.json` (`d61e5973840024075f72b40f63f6b3f06ba4cfb834c0c21c74eed1f21111ba13`)
- `state_matrix`: `research/prototypes/generative-drum-machine/contract/state-matrix.md` (`b7a82cff4112201a85452002fb07839589eb8d60979a157e074331d8973d9da6`)
- `validation_plan`: `research/prototypes/generative-drum-machine/contract/validation-plan.json` (`e0a3dd22610121f9e2b4bfc3ee2d6c634ee0ab9429b915867622e7db0c3ed09b`)

## Allowed edits

- prototype-owned rhythm, event, allocation, synthesis wrapper, streaming engine, renderer, fixture, and test mechanics
- prototype-owned selector descriptors and pure public-control mapping mechanics
- prototype-owned accepted-state UI projection, bounded control snapshot, and optional JUCE host presentation
- prototype-owned authored rhythm-bank definitions and persistent logical-lane voice-shape state
- prototype-only experiments and noncanonical topology annotations
- exact reusable dependency handoff, package, notice, and adapter corrections that preserve upstream bytes and source-release authority

## Reusable entry points

- SchussInstrumentLab::Core
- SchussMutableBraidsV1::Core
- generative_drum_machine_core
- schuss::generative_drum_machine::StreamingEngine
- schuss::generative_drum_machine::AtomicControlSnapshot
- schuss::generative_drum_machine::mapMidiCc
- schuss::generative_drum_machine::applyMapping
- schuss::generative_drum_machine::selectRhythmPreset
- schuss::generative_drum_machine::rhythmPresetInfo
- schuss::generative_drum_machine::resolvedLaneRecipes
- schuss-generative-drums
- schuss::generative_drum_machine::generateHits
- schuss::generative_drum_machine::render

## Required commands

- python3 tools/instrument_lab/generate_task038_source_dependencies.py --check
- python3 research/prototypes/generative-drum-machine/tests/run_structural.py --check
- python3 research/prototypes/generative-drum-machine/tests/render_evidence.py --reproduce --output build/generative-drum-machine-evidence
- python3 research/prototypes/generative-drum-machine/tests/benchmark_realtime.py --reproduce --output build/generative-drum-machine-realtime-benchmark.json
- cmake -S research/prototypes/generative-drum-machine -B build/generative-drum-machine-juce -DCMAKE_BUILD_TYPE=Release -DGDM_ENABLE_JUCE=ON -DGDM_JUCE_SOURCE_DIR=operator-supplied-authenticated-juce-8.0.15-root
- cmake --build build/generative-drum-machine-juce --parallel
- ctest --test-dir build/generative-drum-machine-juce --output-on-failure
- python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/generative-drum-machine --check

## Stop conditions

- approved proposal or implementation contract fingerprint changes
- rhythm-bank fixture, voice-shape law, generated descriptor, UI projection, control-snapshot protocol, streaming Core, JUCE target, source dependency handoff, physical package, adapter, event trace, allocator trace, synthetic benchmark, or expected render manifest drifts
- work requires accepted schemas, records, providers, factories, task activation, live endpoints, target hardware, listening, or publication
- an evidence level would be promoted without its named proof

## Open decisions

- accepted ownership of rational rhythm and semantic timed drum events
- standalone app launch, visual inspection, live deadline/xrun measurement, and revision 0.6 listening
- live Launch Control 3 endpoint selection, receipt diagnostics, reconnect, and feedback
- user-authored pattern and voice-shape preset persistence
- listening approval of each lane's shaping ranges and labels
- Braids model-selection and state-reset policy for shaped lanes
- MIDI note input, mirroring, and clock slices
- optional Ksoloti feasibility

No app launch, device, real-time, listening, distribution, or production claim is made.
