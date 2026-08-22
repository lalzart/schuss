# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `wirefall-r02` revision `0.2`
- Lane: `new-design`
- Index: `research/prototypes/wirefall-r02/prototype-index.json` (`57a884402e389fd3c029779028b71ed0ff5a14acf13e128005bdd655bf610b7e`)
- Working artifact: portable Wirefall revision 0.2 Core, deterministic renderer, retained passing host-signal evidence, and an authenticated standalone target built but not launched

## Exact authorities

- `control_map`: `research/prototypes/wirefall-r02/contract/control-map.json` (`aa789e9f807f2886e1472d1fac999dee877ee1b0bfaf600e8dc1ea9f159e000c`)
- `controller_topology`: `contracts/task018/gills-device-profile-r2.json` (`52fdbc3e671068851e85a4a8dcd6237b85fb81f71c63395634e697ab3e23f189`)
- `dsp_topology`: `research/prototypes/wirefall-r02/dsp-topology.json` (`520a2b707b3749de1eecb68e37e17ce4c4a26a4aad2722fd705fb63e681b7d7c`)
- `experiment`: `research/prototypes/wirefall-r02/contract/experiment.json` (`1498fe93ed4d47bf7d6e2a245cb5c8198bb0aa75ebf63d7112ecb6fff7eb19d9`)
- `gaps`: `research/prototypes/wirefall-r02/contract/GAPS.md` (`203274f4cb18c6f71e1bec711bcfb0972a27e6f1dcd0fb6b9a4f1aabd1478afa`)
- `implementation_contract`: `research/prototypes/wirefall-r02/contract/implementation-contract.json` (`096c936bac00b13375b245a883576f75091ca0924ce17477c013bbf19c04223c`)
- `proposal`: `research/proposals/wirefall-r02.md` (`1862683de17018a0d6802cd2eee40a1cd273a3033d493713f6272cc3549744ee`)
- `results`: `research/prototypes/wirefall-r02/contract/RESULTS.md` (`a77546817d415684086bf42d7f030064eaf991d7528ecfa7b0fd82ce33dac95a`)
- `state_matrix`: `research/prototypes/wirefall-r02/contract/state-matrix.md` (`f1094844df8124cf934926c25c64ea85dec3750c41fdbc072130e44ff535f344`)
- `validation_plan`: `research/prototypes/wirefall-r02/contract/validation-plan.json` (`eaf79cc6227c212e48410e86611ad80dc65adbe6906d8d7c331d8549f8a87515`)

## Allowed edits

- prototype-local corrections that preserve the frozen control semantics and do not weaken objective tolerances
- a later instrument-owned musical revision after a newly approved proposal fingerprint
- noncanonical topology and evidence annotations

## Reusable entry points

- SchussInstrumentLab::Core
- wirefall_r02_core
- wirefall_r02_render
- wirefall-r02-instrument

## Required commands

- python3 tools/instrument_lab/validate_prototype.py --repo-root . --consumer-root research/prototypes/wirefall-r02 --check
- cmake -S research/prototypes/wirefall-r02 -B build/wirefall-r02-core -DWIREFALL_R02_ENABLE_JUCE=OFF
- cmake --build build/wirefall-r02-core -j4
- ctest --test-dir build/wirefall-r02-core --output-on-failure -R ^wirefall_r02_core_tests$
- python3 research/prototypes/wirefall-r02/tests/validate_render_matrix.py build/wirefall-r02-core/wirefall_r02_render --output build/wirefall-r02-results
- cmake -S research/prototypes/wirefall-r02 -B build/wirefall-r02-juce -DWIREFALL_R02_ENABLE_JUCE=ON -DWIREFALL_R02_JUCE_SOURCE_DIR=OPERATOR_AUTHENTICATED_JUCE_8_0_15
- cmake --build build/wirefall-r02-juce --target wirefall-r02-instrument -j4

## Stop conditions

- the approved proposal or ready-bundle fingerprint drifts
- an objective failure is relabeled or a tolerance weakened without a new approved revision
- work expands to launch, device access, listening, packaging, distribution, or production without explicit authorization

## Open decisions

- preferred ENERGY sensitivity distribution after hands-on audition
- preferred tick character and level after hands-on audition
- fresh visual and real-time lifecycle acceptance after explicit launch authorization
- any later physical layout, package format, or canonical production identity

No app launch, device, real-time, listening, distribution, or production claim is made.
