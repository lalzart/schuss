# Task 011C: Bounded legacy-backend expansion and ARM evidence

Status: complete on 2026-08-15. The user explicitly authorized running Task 011C.
That authorization covers the local isolated Java bridge and authenticated GNU
Arm compiler/linker actions required by VS-05 and VS-06. It does not authorize
device access, firmware installation or modification, upload, flash, SD-card
writes, staging, commit, publication, or push.

Work in the Schuss repository. Work only on Task 011C. This task implements the
accepted Task 011 roadmap's VS-05 and VS-06 gates for the exact Task 011B graph.
It may consume the accepted Task 009 executable proof, but it may not generalize
that proof into an arbitrary legacy compiler or change any authoritative
catalog, component-contract, graph, device, or instrument semantics.

## Goal and why it exists

Extend the transitional legacy backend from the accepted one-node Blend proof
to exactly the eight-node, nine-connection Task 011B Gills slice, then establish
deterministic backend-lowering, source-generation, and ARM compile/link evidence
for that exact closure:

```text
Square LFO -> Cyclic Counter -> four-step Pitch Sequencer
                                      |              |
                                      v              v
                                Sine Oscillator A  Sine Oscillator B
                                      |              |
                                      +-> mixed Crossfader <-+
                                                |
                                                v
                                      State-variable Filter (LP)
                                                |
                                                v
                                      stereo Audio Output

Gills knob -> instrument blend -> graph blend -> Crossfader fade
```

The task exists to prove only that this exact graph and exact legacy binding
revisions lower, generate deterministic source, and compile/link against the
authenticated Ksoloti Core runtime. A successful link is level-5 build evidence;
it is not device, real-time, audible, or release evidence.

## Accepted inputs and frozen boundaries

Treat these as immutable inputs:

- all accepted Tasks 001-011B schemas, records, fixtures, operations, CLI
  results, artifacts, evidence, and completion records;
- authoritative graph `schuss-graph-000002` revision 1 and instrument
  `schuss-instrument-000002` revision 1;
- Task 011B successor record set `schuss-record-set-000005` revision 1;
- the six Task 011B binding and eligibility revision-1 candidates and the six
  immutable not-authorized probe inputs under procedure `000002`;
- promoted mixed Crossfader binding/eligibility revision 2 and its complete
  Task 009 evidence chain;
- the exact Task 009 Java, classpath, patcher-source, GNU Arm, firmware/runtime,
  command, and retained-product closure;
- pinned `axoloti-factory` commit
  `25d2615ed5233546d617017666a4ab1e60a8c506` and `axoloti-contrib` commit
  `2e994478c0ab15fb1daa3bb4b86c88e22952d99c` as read-only source evidence;
  and
- the accepted Task 008 backend-invocation seam and Task 009 handler boundary.

The pre-task repository baseline is clean `main` at commit
`9b6eaaca12dd6859fae26533891f23a757d56b85`. Fourteen inventory tests, six
catalog tests, and 148 contract tests pass. The accepted validator hashes are
recorded in the completion section after final equality verification.

## In scope

### VS-05: lowering and deterministic source generation

- A separate Task 011C bounded backend entry point for only graph `000002`.
- Reuse or parameterize Task 009 adapters only where Task 009 behavior and
  governed bytes remain exact.
- Exact support for the eight authoritative nodes, repeated Sine instances,
  nine graph connections, fixed parameter values, graph `blend` binding,
  `generated-legacy-object`, and the one reviewed `legacy-native-object` form.
- Deterministic resolution-plan, `.axp`, source-map, bridge-result, and
  generated-C++ outputs.
- An isolated headless Java bridge that registers only the exact approved
  legacy definitions by authenticated path, definition index, and UUID.
- Exact verification of generated factory definitions against their pinned
  factory records where the binding form is generated.
- Exact verification of the four-step sequencer definition from the pinned
  contrib commit and source bytes without ambient library scanning.
- Stable first-terminal diagnostics and focused failure injection for lowering,
  Java generation, and ARM compile/link.

### VS-06: probes, promotion, production execution, and evidence

- Authorized successors of probe inputs `000003` through `000008`, each naming
  one exact binding revision 1 as candidate-under-test while executing the
  complete graph closure.
- Immutable probe results and evidence companions through ARM compile/link.
- Strictly-earlier evidence claims for each candidate binding revision 1.
- Binding revision 2 and eligibility revision 2 for each of the six new
  realizations only after the matching probe passes.
- The smallest justified backend and build-request revisions. Accepted target,
  toolchain, and runtime revisions remain unchanged unless execution proves a
  new revision is required.
- One successful ordinary Task 008 `build.resolve` over the promoted exact
  record set, followed by two deterministic production-handler runs consuming
  its exact backend-invocation value.
- Immutable artifact descriptors, build result, static resource report,
  level-specific evidence claims, execution/preservation reports, and one exact
  parent-preserving successor record set.

## Out of scope

- Any graph, component-contract, instrument, device-profile, catalog-family, or
  Task 011B fixed-value change.
- Any hidden adapter, implicit conversion, fallback, ambient source lookup,
  first-match selection, or compatibility inferred from legacy datatype,
  source path, family membership, or historical use.
- Arbitrary `.axp`, `.axo`, `.axs`, graph, component, generated-object, native
  object, dependency, asset, display, action, MIDI, or backend support.
- A normalized IR, optimizer, scheduler, direct Schuss-to-C++ frontend, general
  compiler API, or Task 013 work.
- Product-CLI changes, new operations, graph persistence, UI, drawer, canvas,
  AI/MCP, transport, queues, progress, or cancellation.
- Device connection or execution, USB, firmware installation/modification,
  upload, flash, SD-card write, real-time/resource measurement, or listening.
- Staging, committing, tagging, publishing, or pushing.

## Deliverables

- This active contract, updated to complete only after all gates pass.
- A Task 011C-owned bounded Python backend and isolated Java bridge entry point.
- Focused Task 011C tests and a read-only retained-output validator.
- Authorized probe input/result/evidence records for all six candidate bindings.
- Deterministic probe and production artifacts in a content-addressed store,
  with exact descriptors and portable locators.
- Six strictly-earlier promotion chains, promoted binding/eligibility records,
  the smallest backend/request revisions, one result, one static resource
  report, and independent level 1-5 evidence claims.
- Successor record set `schuss-record-set-000006` revision 1 whose exact parent
  is Task 011B record set `000005` revision 1.
- Preservation, fresh-root determinism, failure-injection, operation-seam, and
  evidence-level reports.
- Necessary architecture, status, roadmap, bridge, and contract documentation
  updates only after the executable and preservation gates pass.

## Acceptance tests

Task 011C is complete only if all of the following pass:

1. Preflight revalidates every Task 009 source, Java/classpath, GNU Arm, and
   firmware/runtime byte before tool invocation.
2. The pinned factory and contrib checkouts match their locked commits; every
   selected object file matches its frozen observation SHA-256 before copying
   only the required bytes into fresh execution roots.
3. All 168 pre-existing tests pass before counting Task 011C tests.
4. Every accepted schema, record, artifact, evidence, validator output,
   operation fixture, CLI golden, and Task 009 backend artifact remains exact.
5. Task 011B build resolution remains `unresolved`, selects only the promoted
   Crossfader, and emits no backend invocation.
6. Each authorized probe preserves candidate-under-test state, names one exact
   binding revision 1, has no production selection authority, and executes the
   same complete exact graph closure.
7. The bridge resolves exactly nine legacy instances representing all eight
   graph nodes plus the public `blend` inlet; both Sine nodes resolve the same
   exact definition.
8. The `.axp` contains the exact nine authoritative graph connections plus the
   explicit public-parameter connection and no hidden adapter or node.
9. Fixed parameters preserve the exact Task 011B values and serialize through
   their exact legacy parameter seams.
10. The source map covers every graph node, component facet, binding seam,
    legacy object, connection, fixed parameter, public parameter binding, and
    stable generated-source region required by the slice.
11. Two differently named fresh roots produce byte-identical plan, `.axp`,
    source-map, generated C++, stripped ARM object, stripped ELF, and link map,
    plus identical bridge results, command vectors, and static resource facts.
12. No retained deterministic artifact contains timestamps, random IDs, local
    paths, output-root names, unstable build IDs, or locale-dependent identity.
13. Lowering, Java-generation, and ARM failure injection each stops all later
    stages and creates no promotion or unsupported evidence.
14. Each promoted eligibility cites evidence naming its strictly earlier
    binding revision 1; no result/evidence ownership cycle exists.
15. Ordinary `build.resolve` selects exactly one promoted binding for each of
    eight nodes, including the same Sine binding for both Sine nodes, with no
    exclusion or unresolved reason.
16. The production handler consumes the exact Task 008 invocation bytes and
    rejects stale, extra, missing, unselected, unsupported, or ambiguous input
    before creating an output root.
17. The exact generated source compiles and links against the authenticated
    target/runtime boundary; the ELF is little-endian ARM and its static
    sections fit declared linker regions.
18. Build result, artifacts, resources, stages, diagnostics, and input closure
    are complete, deterministic, and exact.
19. Evidence claims separately record only levels 1-5 reached. Levels 6-8 are
    explicitly `not-run`.
20. Record set `000006` is an exact parent-preserving superset of `000005` and
    accepted defaults remain unchanged.
21. Full inventory, catalog, contract, prerequisite, Task 009, Task 011B, and
    Task 011C validation passes in fresh processes with deterministic bytes.
22. `git diff --check` passes and no upstream checkout, hardware, firmware,
    device, unrelated workspace file, stage, commit, or remote was mutated.

## Decisions Task 011C may make

- Exact Task 011C-owned file layout, diagnostic codes, bridge machine
  interface, portable execution vectors, artifact IDs, result/evidence IDs,
  and content-addressed storage layout.
- The deterministic legacy instance names, coordinates, XML formatting, and
  generated artifact filenames, provided source maps retain authoritative
  identity and no presentation value becomes semantic truth.
- The smallest backend revision that adds exactly the one required native form
  and exact supported stopping stage.
- The smallest build-request revision naming the promoted closure.
- Static link-map resource observations justified by exact compiler outputs.

## Decisions Task 011C must not make

- Any semantic or fixed-value change to the accepted Task 011B graph or its
  component, instrument, device, or catalog closure.
- Any support claim beyond the exact six binding revisions and graph constructs
  exercised by this task.
- Any implicit adapter, selection fallback, ambient discovery, schema
  weakening, result/evidence cycle, or evidence-level collapse.
- Any inference that compile/link proves device execution, real-time behavior,
  physical Gills behavior, sound, musical value, or release readiness.
- Any client/UI/direct-frontend/hardware/firmware decision or prohibited change
  control action.

## Stop conditions

Stop and report rather than broaden or weaken the task if an accepted byte or
semantic result must change; a pinned tool/source/runtime byte is absent or
mismatched; exact Java resolution requires ambient preferences, a source scan,
GUI, or device state; the sequencer definition cannot be pinned uniquely; the
graph needs an unsupported construct or hidden adapter; deterministic source,
object, ELF, or map bytes cannot be produced; compiler/linker input falls
outside the authenticated closure; promotion cannot satisfy the strictly-
earlier rule; or completion would require hardware, firmware, network install,
upstream mutation, staging, commit, or push.

## Completion report requirements

On completion, record all delivered files; exact source/tool/runtime identities;
pre-task and final test counts; accepted-byte preservation hashes; each probe,
result, evidence, binding, eligibility, backend, request, artifact, result,
resource, record-set, and operation-seam identity; fresh-root and failure-
injection outcomes; level 1-8 status; scope confirmation; and remaining device,
real-time, audible, UI, direct-frontend, and general-backend proof gaps.

## Completion report

Task 011C completed within the authorized local Java and ARM compile/link
boundary. It added additive conformance-probe-input schema v1 solely to encode
`task-011c-authorized`; every earlier schema and authorization value remains
unchanged. The bounded Python backend and `GillsSliceBridge` accept only graph
`000002`, eight exact binding identities, the pinned factory/contrib sources,
and the authenticated Task 009 tool/runtime closure.

Probe inputs `000003` through `000008` revision 2 each executed the complete
candidate closure. Results `000003` through `000008` and evidence companions
all passed through level 5 without production authority. Claims `000007`
through `000012` name only the strictly earlier binding revision 1. The six
bindings and eligibilities then advance to revision 2. Backend `000001`
revision 3 adds only `legacy-native-object`; Crossfader eligibility revision 3
names that additive backend revision while preserving Crossfader binding
revision 2. Target, toolchain, and runtime remain revision 2. Build request
`000002` revision 2 stops at `target-compile-link`.

Ordinary `build.resolve` selected all eight graph nodes with the same Sine
binding for nodes `000004` and `000005`. Its 16,104-byte backend invocation has
SHA-256 `594d4cd157468c0d8a2161cae9095693d8d320a5dded61c1598c7f314329f2f9`.
Stale, extra, missing, unselected, unsupported, and ambiguous mutations were
rejected before output-root creation. Lowering, Java-generation, and ARM
failure injections stopped every later stage.

Two fresh production roots produced exact retained bytes:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| resolution plan | 21,256 | `b9cb83cfb05ae29d9f0f37e5e04c6df6a17d1ce1cbe21395ffa31f0be4fea261` |
| legacy `.axp` | 3,062 | `84f875018cbbc859eecf5627ffab5c50ade66a369203d3a79fcb794dcb86865a` |
| source map | 19,982 | `8992679f5d12c5f1d46d1ed0a30220b2ee8dd3511240c7bcaab80d3a95837d7c` |
| generated C++ | 18,359 | `7877897b3112dcbb7ee1239f3187f535d6113875cacbb49c76bd30a0321bcfd3` |
| stripped ARM object | 10,208 | `c059b2ee38be7dbca6828dc06b1d5890bb0600ab606dd59786fb1dccbd308c1b` |
| stripped ARM ELF | 69,404 | `d04cc20d5dc0cfe195ce38ee850857c0b8af8675f7616898f50dd6e77372db2a` |
| link map | 152,502 | `30357b886ca808d38a61b2ad624d3086e66babb0df169caa5af36eda8c15531f` |

Artifact descriptors are `000022` through `000028`. Build result `000002`
hashes to `a9fc365dc385342bf0925fc44f2097affa0b7e941f8388d27500dfde1e17168d`.
Resource report `000002` hashes to
`acd3fe10ed6f71313378e8c0a9370ef55a9676ecad784f0ba868d09439482420`
and records 2,472 code bytes, 152 read-only bytes, and 624 data bytes within
declared static regions. Evidence claims `000013` through `000017` separately
record levels 1-5. Levels 6-8 are `not-run`.

Successor record set `schuss-record-set-000006` revision 1 hashes to
`fcf8f43d4139a16796b17bf2bdb95e5cd03ac279c60c55f8218349ef8a7cc842`
and is an exact parent-preserving superset of `000005`. Its read-only validator
reports 144 total records, 60 Task 011C records, 14 Task 011C artifact
descriptors, six passing probes, eight selected nodes, and no diagnostics.

Pre-task tests were 14 inventory, 6 catalog, and 148 contract tests. Final
counts are 14, 6, and 159; all 179 pass, including 11 focused Task 011C tests.
The preservation report retains accepted validator hashes and confirms both
pinned upstream checkouts stayed clean at their exact commits. Authored-file
`git diff --check` passes; the byte-retained generated C++ and linker map are
excluded because whitespace normalization would change their authenticated
artifact hashes. No device, firmware mutation, upload, flash, SD-card write,
real-time measurement, listening, staging, commit, or push occurred.

Remaining proof gaps are connected-device execution, real-time behavior,
audible behavior, broader Gills panel/release validation, arbitrary legacy
backend support, the Phase 12 UI, and the Phase 13 direct frontend. Compile/link
success makes none of those claims.
