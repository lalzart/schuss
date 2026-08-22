# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `wirefall` revision `0.1`
- Lane: `new-design`
- Index: `research/prototypes/wirefall/prototype-index.json` (`4a8db98824d4bbf55f095efcfbc975b858d6e586157ff11bcfe35a302a4251fa`)
- Working artifact: portable float Core, deterministic renderer, and retained failed host-signal evidence

## Exact authorities

- `control_map`: `research/prototypes/wirefall/contract/control-map.json` (`f97dde2a8d2d8d52e29249466b8325afbc703fad847aa9ef337649bae11e2ccd`)
- `controller_topology`: `contracts/task018/gills-device-profile-r2.json` (`52fdbc3e671068851e85a4a8dcd6237b85fb81f71c63395634e697ab3e23f189`)
- `dsp_topology`: `research/prototypes/wirefall/dsp-topology.json` (`45021920055f13cd11f8ca6a3e9be82d5fb95cd8343489aaf3869c50ac051457`)
- `experiment`: `research/prototypes/wirefall/contract/experiment.json` (`aeee17bb3b0ad296824a6cfc559a0aff6ebeb0ca85372d2e9f9105e021a6662c`)
- `gaps`: `research/prototypes/wirefall/contract/GAPS.md` (`775cb84d8e75a36dc682f55535a55ddb5b1e3f8c58ed0409c4a8c717bf523806`)
- `implementation_contract`: `research/prototypes/wirefall/contract/implementation-contract.json` (`8c130286deec12b95a44c84674542677a46f009eaaf414a5c2326953016c2058`)
- `proposal`: `research/proposals/wirefall.md` (`cf9b5f58e50856a9d38d754ee476ced58c52473bb9f9ff1216c75e7ca28707b8`)
- `results`: `research/prototypes/wirefall/contract/RESULTS.md` (`20c28dd8b81bfff8eac907e989aa5155a1efaf9ddc1990f175477b490abe87a3`)
- `state_matrix`: `research/prototypes/wirefall/contract/state-matrix.md` (`9899e868b58cfed4f8f52a37f7b0caa25856d83ac3f363935c0e240544dcad50`)
- `validation_plan`: `research/prototypes/wirefall/contract/validation-plan.json` (`d214d48e82a780d78e08280bbbbca02b54c14ffe1fccb27d5bd9c20fa8fd0b98`)

## Allowed edits

- prototype-local validation corrections that do not weaken frozen tolerances
- instrument-owned DSP revision only after a newly approved proposal fingerprint
- noncanonical topology and evidence annotations

## Reusable entry points

- SchussInstrumentLab::Core
- wirefall_core
- wirefall_render

## Required commands

- python3 research/prototypes/wirefall/tests/validate_contract_fixtures.py --repo-root .
- cmake -S research/prototypes/wirefall -B BUILD -DCMAKE_BUILD_TYPE=Release
- cmake --build BUILD --parallel
- ctest --test-dir BUILD --output-on-failure -R ^wirefall_(core_tests|contract_fixtures)$
- python3 research/prototypes/wirefall/tests/validate_render_matrix.py --renderer BUILD/wirefall_render --contract research/prototypes/wirefall/contract/experiment.json --output RENDER_OUTPUT

## Stop conditions

- approved proposal or frozen ready-bundle bytes change
- a failed host-signal tolerance is weakened or relabeled without approval
- work expands to JUCE, real-time, target, device, listening, or production scope

## Open decisions

- DC and true-void processing order for revision 0.2
- Wire antialias strategy for revision 0.2
- TENSION energy compensation for revision 0.2
- Shadow harmonic rejection for revision 0.2

No app launch, device, real-time, listening, distribution, or production claim is made.
