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

## Task 009 prerequisite boundary

The accepted Task 009 prerequisite does not promote any production record or
perform levels 3-8. It establishes a separately selected record-set view and
an authenticated local execution closure:

- pinned source commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, tree
  `75b75dba0c3734a8a53464ac93cdc20ec7203bb6`, and reproducible archive
  SHA-256 `2f2d6c9e985e5b8609c847a0b21ad7611e614e7dd2a0cb3c51d9b50a77a36f32`;
- exact Java/Javac, 896 compiled classes, 69 dependency JARs, and classpath
  fingerprint `5ebd2f2b7f2aa6dc1d3d10a04edb5f2bbedd97cfb4372dab56dc22c778b17710`;
- exact GNU Arm Embedded 9-2020-q2-update component bytes; and
- a two-clean-root firmware reproduction whose retained bin SHA-256 is
  `fd61a6a109a234d1c72e445a0542ab59c407a6896b9aafe2bfcbcadaf775e258`
  and stripped link-ELF SHA-256 is
  `df65f2153eb999386cc1bc30b382cafeac63aea8495bf8cb4cdad1c01fca944b`.

`prerequisite-environment-v0` records those identities and their retained
manifests without local absolute paths. This proves a reproducible execution
environment and firmware/ABI source closure only. It is not Schuss graph
lowering, generated patch source, patch compile/link, device, real-time, or
audible evidence.

The prerequisite also defines closed `conformance-probe-input-v0`,
`conformance-probe-result-v0`, `conformance-probe-evidence-v0`, and
`conformance-probe-procedure-v0` contracts. Their retained fixture names
binding revision 1 as `candidate-under-test`, is `not-authorized` and `not-run`,
and grants no production selection authority. Evidence points to an immutable
probe result; results never point back to evidence. A later evidence claim can
cite the probe-evidence companion as a semantic record, preserving the rule
that a promoted eligibility revision cites evidence naming a strictly earlier
binding revision.

## Task 009 bounded executable proof

Successor record set `schuss-record-set-000003` revision 1 is an exact superset
of the prerequisite set. It retains every revision-1 record and adds:

- an authorized immutable probe over mixed-Crossfader binding revision 1;
- evidence claim `schuss-evidence-claim-000001` naming that earlier revision;
- binding and eligibility revision 2, plus resolved environment, target,
  backend, and request revision 2 records;
- a successful ordinary `build.resolve` seam and production build result;
- deterministic plan, `.axp`, source-map, C++, ARM object, ELF, and link-map
  descriptors; and
- a compiler/link-map resource report and separate evidence claims for levels
  1 through 5.

Two fresh probe roots and two fresh production-handler roots produced identical
retained bytes. The exact ELF is little-endian ARM and linked against the
authenticated runtime boundary, but it was not executed. Levels 6-8 remain
`not-run`: no connected device, real-time measurement, or listening procedure
occurred.

## Task 011B unresolved successor closure

Successor record set `schuss-record-set-000005` revision 1 retains exact parent
`000004` and adds only the Task 011B target-independent graph/build candidate
set. Its exact request `schuss-build-request-000002` revision 1 names graph
`000002`, instrument `000002`, promoted Ksoloti Core target revision 2, and
promoted legacy backend revision 2, and stops at `artifact-generation`.

Each of the six new binding revisions has one exact eligibility companion.
Every pair state is `not-evaluated`, cites no compatibility evidence, preserves
the backend's complete target-capability requirements, and names Task 011C as
the earliest evidence owner. A realization form absent from the backend's
supported forms is a valid fail-closed candidate when its pair state is
explicitly `not-evaluated` or `unsupported`; resolution still excludes it as
`REALIZATION_FORM_UNSUPPORTED`. This permits the native four-step sequencer to
remain visible without pretending it is eligible.

The deterministic resolution trace is:

| Node | Role | Status |
| --- | --- | --- |
| `graph-node-000001` | Square LFO | unresolved |
| `graph-node-000002` | Cyclic Counter | unresolved |
| `graph-node-000003` | four-step Pitch Sequencer | unsupported form |
| `graph-node-000004` | Sine Oscillator A | unresolved |
| `graph-node-000005` | Sine Oscillator B | unresolved |
| `graph-node-000006` | promoted mixed Crossfader | selected |
| `graph-node-000007` | State-variable Filter | unresolved |
| `graph-node-000008` | stereo Audio Output | unresolved |

Overall `build.resolve` is `unresolved` and `backend_invocation` is `null`.
Procedure `schuss-procedure-000002` and probe inputs `000003` through `000008`
are immutable `candidate-under-test` records for only the six new bindings and
graph. Every input is `not-authorized` and grants no production selection
authority. No build result, artifact descriptor, resource report, evidence
claim, backend execution, lowering, generation, compile/link, or device action
is part of this closure.

## Validator boundary and next tasks

`validate_target_backend_build_contracts.py` is read only. It imports the Task
006 validator, which imports the Task 005 canonical/schema core. No existing
validator imports upward, so the dependency remains acyclic. The three files
now contain shared logic that should not be copied again.

Task 008 completed the bounded validator-core consolidation and shared headless
operations. Task 009 consumes that boundary without changing accepted Task
005-008 output bytes. The default accepted view remains unresolved by design;
the explicit Task 009 successor view resolves only the promoted exact pair.
Task 010 remains separate and now provides only deterministic product commands
over those unchanged operations; it does not execute the Task 009 handler.
Task 011B consumes the same pure dispatcher under explicit record set `000005`;
Task 011C is the earliest owner of backend expansion and executable evidence
for the eight-node slice.

## Task 011C executed successor closure

Successor record set `schuss-record-set-000006` revision 1 retains exact
parent `000005`. Additive probe-input schema v1 names `task-011c-authorized`
without changing prior authorization values. Probe inputs `000003` through
`000008` revision 2 remain candidate-only and grant no production authority;
each has a level-5 result/evidence companion and a strictly-earlier level-2
promotion claim naming binding revision 1.

The six new bindings and eligibility companions advance to revision 2 only
after those probes pass. Backend revision 3 adds only
`legacy-native-object`; the accepted target, toolchain, and runtime remain at
revision 2. Crossfader eligibility revision 3 names the exact additive backend
revision without changing Crossfader binding revision 2. Build request `000002`
revision 2 stops at `target-compile-link`.

Ordinary resolution selects exactly eight nodes. The production handler then
retains artifact descriptors `000022` through `000028`, build result `000002`,
resource report `000002`, and independent evidence claims `000013` through
`000017`. Static link-map observations fit the declared regions. These are
compile/link facts only: evidence levels 6-8 are explicitly `not-run`.
