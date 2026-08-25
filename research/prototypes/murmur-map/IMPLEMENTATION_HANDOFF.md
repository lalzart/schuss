# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `murmur-map` revision `0.1`
- Lane: `new-design`
- Index: `research/prototypes/murmur-map/prototype-index.json` (`fb00e50293295f1f508a8b2b091784d7ae796cf00b678ed62b1f6bdbfb62440c`)
- Working artifact: noncanonical portable C++17 four-waypoint three-lane remembered-route instrument with exact regular Launch Control 3 mapping deterministic offline evidence and a built unlaunched Murmur Map 0.1 standalone app

## Exact authorities

- `control_map`: `research/prototypes/murmur-map/contract/control-map.json` (`b4bfd6692895f35dadf78ac3acf478552b074cbbe9972b8315a3d1158f9a9b15`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/murmur-map/dsp-topology.json` (`ff9714ba42b6a79480a10a00fd187fa8fd426214bb88eb0948f5f40b74472e47`)
- `experiment`: `research/prototypes/murmur-map/contract/experiment.json` (`3b1bc8993f04b0650468fd120d6effc69c7f8cc223540c0036d52ec9a5042834`)
- `gaps`: `research/prototypes/murmur-map/contract/GAPS.md` (`ae1887cea9383caa4542b1c15233ae509d4bc1535a84d1bde07e090a0c76aa2f`)
- `implementation_contract`: `research/prototypes/murmur-map/contract/implementation-contract.json` (`31e408846cc14d22a973decccc6aa6eb238326b0cb21cb31fa397afe352637be`)
- `proposal`: `research/proposals/modular-generative-juce-instrument-study.md` (`65180864c42996a3e7a68de0b7356522329b25043e3ef5721e7e49fd3d49926f`)
- `results`: `research/prototypes/murmur-map/contract/RESULTS.md` (`89c9321d2bad2634411ccf0a8ec0951ca21d00418aebc834eab6b31f98b08189`)
- `source_package_handoff`: `research/prototypes/murmur-map/source-dependencies.json` (`bb46315605a9c362770f92cf0609d4c0aea6b5e5def14ba63013d2d85de1d22a`)
- `state_matrix`: `research/prototypes/murmur-map/contract/state-matrix.md` (`b3e35f227851182586a1be394f691ec4e4b2a27d214b3845f6534fa49682b80e`)
- `validation_plan`: `research/prototypes/murmur-map/contract/validation-plan.json` (`0340c83335329033d683e149f260f5987002c80bce969dbea58484c85e6501d9`)

## Allowed edits

- prototype-owned route memory walker scene interpolation scheduler quantizer voice wrapper mixer renderer and focused tests
- prototype-owned pure public-control reducer draft transaction and accepted-state projection
- prototype-owned optional standalone audio input and presentation adapter
- prototype-only experiment conditions evidence scripts and noncanonical topology annotations
- exact reusable dependency handoff and notice corrections that preserve upstream bytes and source-release authority

## Reusable entry points

- SchussInstrumentLab::Core
- SchussMutableBraidsV1::Core
- murmur_map_core
- schuss::murmur_map::Core
- schuss::murmur_map::defaultControls
- schuss::murmur_map::mapMidiCc
- schuss::murmur_map::applyMapping
- schuss::murmur_map::applyUiCommand
- schuss::murmur_map::SnapshotMailbox
- schuss::murmur_map::SpscQueue
- murmur-map-render
- murmur-map

## Required commands

- python3 research/prototypes/murmur-map/tests/verify_source_authorities.py
- python3 research/prototypes/murmur-map/tests/run_structural.py --check
- python3 research/prototypes/murmur-map/tests/render_evidence.py --reproduce --output build/murmur-map-evidence
- python3 research/prototypes/murmur-map/tests/build_juce.py --build-dir build/murmur-map-juce-release --juce-source-dir operator-supplied-authenticated-juce-8.0.15-root
- python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/murmur-map --check
- python3 tools/instrument_lab/reproduce.py --repo-root . --consumer-root research/prototypes/murmur-map --reproduce
- python3 tools/validation/run.py --profile current

## Stop conditions

- approved proposal implementation contract or exact controller topology fingerprint changes
- route law draw accounting event timing interpolation mapping source dependency expected render manifest or accepted-state protocol drifts
- work requires shared source mutation accepted schemas records providers factories numbered task activation live endpoints physical hardware listening or publication
- an evidence level would be promoted without its named proof

## Open decisions

- listening approval of the route-coherence hypothesis and the waypoint sound ranges
- launched standalone layout interaction and endpoint lifecycle
- physical Launch Control 3 encoder feel receipt reconnect and any outbound feedback
- preset persistence and arbitrary waypoint-count authoring
- source-random isolation if more than one Core per process is requested
- accepted ownership of authored sound maps route memory event snapshots and interpolation contracts
- optional plug-in Ksoloti or Gills targets
- distribution branding notice packaging and release policy

No app launch, device, real-time, listening, distribution, or production claim is made.
