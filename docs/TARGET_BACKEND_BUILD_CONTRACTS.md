# Target, backend, build, and evidence contracts

Task 007 closes the record boundary between the authoritative Task 006 graph
and any future executable compiler operation. It defines records and a pure
resolver. It does not implement or run lowering, generation, Java, `.axp`, a
compiler/linker, device access, measurement, or listening.

## Record families

The v0 contract consists of ten closed schema families:

| Schema | Owner |
| --- | --- |
| `capability-vocabulary-v0` | the bounded shared meanings used by targets, backends, and eligibility |
| `build-environment-v0` | exact or explicitly unresolved toolchain and firmware/runtime ABI identity |
| `compute-target-v0` | processor, ABI constraints, runtime constants, memory regions, capabilities, and unresolved target facts |
| `backend-v0` | accepted inputs/forms, target requirements, ordered stages, artifacts, diagnostics, environment references, and bridge boundary |
| `binding-eligibility-v0` | one exact Task 006 binding, contract, target/backend pair, requirements, evidence threshold, and selection policy |
| `build-request-v0` | exact graph/instrument/target/backend closure, options, assets, narrowing overrides, and stopping stage |
| `build-result-v0` | immutable input closure, total node selection, environments, options, stages, diagnostics, artifacts, resources, and status |
| `artifact-descriptor-v0` | independently content-addressed portable artifact metadata and acyclic ownership/source-map references |
| `resource-report-v0` | typed observations plus exact aligned, same-region hard-budget aggregation |
| `evidence-claim-v0` | one bounded claim at exactly one of eight evidence levels |

The schemas are reusable. Processor, ABI target triple, toolchain identity,
firmware/runtime identity, backend kind/version, and bridge kind/location are
controlled stable values, not Ksoloti constants. The production records select
Ksoloti-specific values. Tests prove a second processor, environment identity,
and backend identity can use the same schemas.

## Production closure

The production closure is intentionally small:

| Record | Revision | Content hash |
| --- | ---: | --- |
| `schuss-capability-vocabulary-000001` | 1 | `sha256:37770109d3aff88a67ab031a6ee21c49eb4d301e2933c4659efd38c4496cca92` |
| `schuss-build-environment-000001` | 1 | `sha256:b8f87da1147faceb472e464fce0a36e3379b100993540946249d69b7aabf97fc` |
| `schuss-build-environment-000002` | 1 | `sha256:4475da81044f40c37e95cd01dcd0a17e3d612c664cc5baa904e0bf1e58e8ae47` |
| `schuss-compute-target-000001` | 1 | `sha256:c1fa5a49ab9474068c70ffc03f5bbfc216936d1fcfa1514e257ec7d5361c866d` |
| `schuss-backend-000001` | 1 | `sha256:5070f9e9c667d6f16fb5b0022f045a1990243c2acbedf4585e8f41420e7c3178` |
| `schuss-binding-eligibility-000001` | 1 | `sha256:7dbfa34a34042af730166e2f1581e2a04b18b9e19a4975234c1b7397bae484f8` |
| `schuss-build-request-000001` | 1 | `sha256:0ba7e74977ac7ebcf50cb73826c349040d998541f688bb32cbedf88140259e95` |

The two capability keys are exactly those required by the mixed Crossfader
seams: `audio-stream-fixed-q27` and `control-stream-fixed-q27`. This is a
bounded vocabulary, not a universal processor or backend ontology.

## Ksoloti facts and unresolved boundaries

Pinned source evidence at patcher commit
`08d3e6e1e2b61230308c20a15ded58ffdaf4656c` supports these production target
facts:

- STM32F427, Cortex-M4, Thumb, `fpv4-sp-d16`, `arm-none-eabi`, hard-float;
- 48,000 Hz and 16-frame audio blocks; and
- the exact linker-declared CCMSRAM, SRAM1, SRAM2, SRAM3, and SDRAM regions.

Those are source/linker declarations, not compilation or device evidence.
Endianness, usable asset capacity after runtime reservations, the installed
toolchain binary closure, firmware/runtime ABI identity, the two stream
capabilities, binding compatibility, and hard binding resource requirements
remain explicitly unresolved. Each unresolved record names an owner and
earliest Task 009 resolution point.

The transitional backend declares the intended Ksoloti pairing, generated
legacy-object form, all ten ordered compiler stages, artifact kinds/media
types, deterministic diagnostics, exact unresolved environments, and the
isolated `legacy/ksoloti-bridge` boundary. A declaration is not a performed
stage. Bridge execution remains `not-run`.

## Eligibility and pure resolution

Eligibility is a separate exact companion, leaving the Task 006 binding
revision-1 bytes and seam map unchanged. Resolution order is fixed:

1. exact component contract;
2. backend-supported realization form;
3. exact target/backend pair;
4. capabilities, dependencies, resources, and evidence;
5. an optional override that may only narrow eligible candidates; and
6. explicit higher-priority ranking, with equal priority reported ambiguous.

The resolver emits sorted candidates, exclusion reasons, unresolved reasons,
the policy ID, and one of `selected`, `unsupported`, `unresolved`,
`ambiguous`, or `invalid-override`. It never selects by path, source, display
name, load order, or file order. The production request stops at
`implementation-resolution`; its sole candidate is deterministically
`unresolved`.

## Result, artifact, resource, and evidence direction

No production result, artifact, resource report, or evidence claim exists.
Complete non-production fixtures validate those future shapes.

- Results contain exact references and derived stage/output records, never an
  embedded authoritative graph, catalog family, public signature, device, or
  instrument behavior.
- Artifact descriptor identity and artifact-byte SHA-256 are distinct. Parent
  and source-map references are exact and acyclic; results point to artifacts,
  never the reverse.
- Resource observations distinguish declarations, estimates, link-map facts,
  and connected measurements. Alignment is applied per observation before
  exact same-region aggregation against a pinned budget.
- Evidence claims point downstream to an immutable subject and cover exactly
  one level. Results never point back to evidence. Compatibility evidence in
  a new eligibility/binding revision must cite a strictly earlier binding
  revision.

The eight independent levels are structural/schema, component/graph
resolution, backend lowering, source/artifact generation, ARM compile/link,
connected-device execution, real-time/resource validation, and
audible/listening validation. Task 007 reaches levels 1 and 2 only; levels
3-8 are `not-run`.

## Validator boundary and next tasks

`validate_target_backend_build_contracts.py` is read only. It imports the Task
006 validator, which imports the Task 005 canonical/schema core. No existing
validator imports upward, so the dependency remains acyclic. The three files
now contain shared logic that should not be copied again.

The first prerequisite of Task 008 is therefore a bounded validator-core
consolidation: extract canonical JSON, schema traversal, portability,
diagnostic, and exact-reference primitives into a lower-level module without
changing record bytes or validation behavior. Task 008 can then define shared
headless operations over the accepted records. Task 009 remains separate: one
minimal deterministic legacy backend path, `.axp` boundary, source map, exact
toolchain/runtime closure, and ARM compile/link evidence. Neither scope is
implemented by Task 007.
