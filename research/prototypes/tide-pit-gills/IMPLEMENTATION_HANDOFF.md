# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `tide-pit-gills` revision `0.1`
- Lane: `source-reimplementation`
- Index: `research/prototypes/tide-pit-gills/prototype-index.json` (`8056df4d779b077247d0829a371205a47f74e916fcf514207eff9faca69616e2`)
- Working artifact: source-authenticated fixed-Q27 Core plus optional authenticated JUCE renderer, adapter, UI, and standalone target

## Exact authorities

- `control_map`: `research/prototypes/tide-pit-gills/control-map.json` (`a91f4ee46b3339f455d5d277f4b8f25d378c652eb946d6c017076e44fd356f60`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/tide-pit-gills/dsp-topology.json` (`8bf0267454a6fa30cb01d1a6ae3970bc24e3d4d0fefd835634d2c06670b467a9`)
- `experiment`: `research/prototypes/tide-pit-gills/experiment.json` (`f8baac381d1e83f2e5db6ee4b56988299d5ae7b3e5b1b2ff4bcdfd1a0459c9fd`)
- `gaps`: `research/prototypes/tide-pit-gills/GAPS.md` (`e5a3922a37f1e587e8071d4aedfa15207f684e6b8b5dcd3aecdb46229ca9a543`)
- `implementation_contract`: `research/prototypes/tide-pit-gills/implementation-contract.json` (`81071c9cac8b76770eb4184d9afd07dda5bc47a1b0bfcdd6075d56a42e01b8c2`)
- `proposal`: `research/proposals/tide-pit-gills-juce-port.md` (`3c2157eaa26ceed61afe87b256a395dccc5fbbd0dab889189926ffb72b5c2157`)
- `results`: `research/prototypes/tide-pit-gills/RESULTS.md` (`29e7bdda6a54431623f1969fc3f89868e689b9f7fde3b581fa1c5fe441b8255b`)
- `source_package_handoff`: `docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json` (`313a3acf451b926739baa14d13ef2abf6747208b5774cfcd5ea9111fbf94938b`)
- `state_matrix`: `research/prototypes/tide-pit-gills/state-matrix.md` (`4ab9467b645dd4e75c2b633c39d94db2f535e91fd527498a5c07aa54c2455d8e`)
- `validation_plan`: `research/prototypes/tide-pit-gills/validation-plan.json` (`8af0e49522c235b1cb6f3be368742de004e23d8949070447f379b28e7345d594`)

## Allowed edits

- instrument-owned adapter and presentation mechanics
- prototype-only experiments and tests
- noncanonical topology annotations

## Reusable entry points

- SchussInstrumentLab::Core
- tide_pit_core
- tidepit::ParameterizedQ27HostBridge
- tidepit::JuceMidiAdapter

## Required commands

- cmake -S research/prototypes/tide-pit-gills -B BUILD -DCMAKE_BUILD_TYPE=Release
- cmake --build BUILD --parallel
- ctest --test-dir BUILD --output-on-failure

## Stop conditions

- Task 036 handoff drifts
- source lock or exact golden changes
- control, UI, adapter, or render parity changes

## Open decisions

- restart-safe snapshot transport
- future component-contract promotion

No app launch, device, real-time, listening, distribution, or production claim is made.
