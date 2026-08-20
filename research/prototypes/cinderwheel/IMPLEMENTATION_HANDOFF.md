# Instrument Lab implementation handoff

This compact noncanonical index does not replace the approved proposal or task.

- Prototype: `cinderwheel` revision `0.1`
- Lane: `new-design`
- Index: `research/prototypes/cinderwheel/prototype-index.json` (`a15365efdbd731137a2d4b6d715114b920ecdf787086ba096b60b20dd341ab80`)
- Working artifact: portable float Core plus optional authenticated JUCE renderer, adapter, and standalone target

## Exact authorities

- `control_map`: `research/prototypes/cinderwheel/fixtures/launch-control-3-test-map-v0.json` (`d5df5f569bf37ed0dbd3e356a9c2f42ac01ed8364c2dc2bc6b07da2243e390f8`)
- `controller_topology`: `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` (`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`)
- `dsp_topology`: `research/prototypes/cinderwheel/dsp-topology.json` (`dff93dc5025be7280d2c565f9c388572acbe9707b13d967413cf471f21dc0b78`)
- `experiment`: `research/prototypes/cinderwheel/src/render.cpp` (`fb612c3e26ec0a236d2d2d8859ca802ab371d71fecc62c65d7102bb418595810`)
- `gaps`: `research/prototypes/cinderwheel/TRIAL_GAPS.md` (`8866b8d962ca6f350ab791b9d26439f14737e2a5eb15912745ae11b1b639b863`)
- `implementation_contract`: `research/prototypes/cinderwheel/README.md` (`0cff98936464389e25d0a675e4e612dd5ed632eb25a48cbe935b450f204b80d6`)
- `proposal`: `research/proposals/cinderwheel.md` (`cd0c09e0df22f382d74bb380fa9ab91549faf1894199f5d02e4ac5e3795a1549`)
- `results`: `research/prototypes/cinderwheel/RESULTS.md` (`02670d7a4d244c692b2953ec1cf20249e47834fcf385a867bef98330b02fa551`)
- `state_matrix`: `research/prototypes/cinderwheel/README.md` (`0cff98936464389e25d0a675e4e612dd5ed632eb25a48cbe935b450f204b80d6`)
- `validation_plan`: `research/prototypes/cinderwheel/tests/validate_render_matrix.py` (`4569226c08c8f485fb31f1caf5b65a2950bad4c0759c508b08f4be47bede1021`)

## Allowed edits

- instrument-owned adapter and presentation mechanics
- prototype-only experiments and tests
- noncanonical topology annotations

## Reusable entry points

- SchussInstrumentLab::Core
- cinderwheel_core
- cinderwheel_ui_model
- cinderwheel::JuceMidiAdapter

## Required commands

- cmake -S research/prototypes/cinderwheel -B BUILD -DCMAKE_BUILD_TYPE=Release
- cmake --build BUILD --parallel
- ctest --test-dir BUILD --output-on-failure

## Stop conditions

- Core or map bytes change
- render matrix changes
- unsupported evidence promotion

## Open decisions

- future component-contract promotion

No app launch, device, real-time, listening, distribution, or production claim is made.
