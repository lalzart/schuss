# Task 011B: Component contracts, Gills slice graph, and unresolved build closure

Status: complete on 2026-08-15. The user explicitly authorized Task 011B
implementation. Staging, commit, publication, push, backend execution,
compiler/toolchain invocation, and device access remained unauthorized and did
not occur.

Work in the Schuss repository. Work only on Task 011B. This task implements the
accepted Task 011 roadmap's VS-02 through VS-04 gates in order. A later gate may
consume an earlier accepted result, but it may not repair an earlier failure by
weakening types, inventing an adapter, selecting through uncertainty, or
performing Task 011C work.

## Goal and why it exists

Create the smallest exact target-independent component, graph, instrument, and
build-domain closure for the first non-UI Gills slice:

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

The task exists to prove the exact node interfaces, legacy seam maps,
target-independent topology, fixed slice values, and fail-closed build candidate
set before Task 011C expands the executable legacy backend. Structural success
must not become lowering, compile/link, device, real-time, or audible evidence.

## Accepted inputs and frozen boundaries

Treat these as immutable inputs:

- all accepted Tasks 001-011A schemas, records, fixtures, operation results,
  artifacts, evidence, and completion records;
- frozen Phase 2/3/review artifacts and the Phase 4A overlay;
- Task 011A catalog corpus and record set `schuss-record-set-000004` revision 1;
- exact observations 9, 159, 209, 215, 549, and 918 and their pinned source
  bytes;
- the accepted mixed Crossfader contract, binding revision chain, eligibility,
  and Task 009 evidence;
- the minimal Gills device profile and its unresolved physical facts;
- accepted target/backend/build, record-set, operation, and probe contracts; and
- the authenticated Task 009 environment record as identity-only input. Task
  011B must not invoke that environment or claim a new environment proof.

The pre-task repository baseline is the clean `main` state after the user's
ordinary-CI removal, commit `38e53d666ad091ff541edc75155e6c8453706bd3`.
All 14 inventory tests, 6 catalog tests, and 135 contract tests pass before Task
011B changes. All accepted validators pass with their recorded Task 011A output
bytes.

## In scope

### VS-02: exact component contracts and bindings

- Six exact component contracts for Square LFO, Cyclic Counter, four-step Pitch
  Sequencer, Sine Oscillator, State-variable Filter, and stereo Audio Output.
- Six companion implementation bindings that retain implementation identities
  `000039`, `000040`, `000041`, `000007`, `000015`, and `000004`.
- Exact Task 011A catalog-family references; no second family truth or rewritten
  catalog corpus.
- A bounded additive component-contract schema for semantics the accepted v0
  schema cannot express truthfully, plus a binding-schema successor whose only
  changes are the frozen observation's explicit null parameter datatype and
  the observed 39-through-42-hex durable UUID widths. Both v0 schemas and every v0
  record remain byte-identical.
- Machine-readable rising-edge inlet behavior and parameter-plus-inlet
  summation behavior, including semitone-offset pitch semantics.
- Complete maps for every public port, parameter, attribute, action, and display
  facet, with private component state and lifecycle validated separately.
- Positive and negative fixtures for Boolean clock transport, rising-edge
  reception, integer step selection, pitch summation, repeated contract use,
  output fan-out, and prohibited implicit conversions.
- Explicit adapter decisions for clock-to-counter and mono-low-pass-to-stereo.

### VS-03: authoritative graph and minimal instrument

- Exactly one new authoritative graph with eight baseline nodes and no hidden
  node.
- Explicit typed connections for the topology above.
- Fixed reviewed values for four pitch steps, LFO tempo-pitch, both oscillator
  base pitches/detune, filter cutoff/resonance, and counter maximum.
- One public normalized `blend` parameter bound to the accepted mixed
  Crossfader fade inlet.
- One new instrument identity referencing the exact graph and existing minimal
  Gills profile, with the device-to-instrument-to-graph mapping chain.
- Exact-reference, topology, cardinality, fixed-value, behavior, and instrument
  target validation.

### VS-04: unresolved build and probe closure

- Successor record set `schuss-record-set-000005` revision 1, preserving exact
  parent `000004` and leaving all accepted default contexts unchanged.
- One exact build request for the new graph, instrument, promoted Ksoloti Core
  target, and promoted legacy backend, requesting no later than artifact
  generation.
- One eligibility companion per new binding. Each remains unsupported or
  unresolved unless strictly earlier evidence supports the exact binding and
  target/backend pair.
- A closed, immutable, not-authorized candidate-under-test probe procedure and
  exact probe inputs covering only the six new binding revisions and the new
  graph.
- A deterministic `build.resolve` result that exposes every candidate,
  exclusion, and unresolved reason and emits no backend invocation while any
  node remains unsupported or unresolved.

## Out of scope

- Task 011C backend code, lowering, dependency execution, `.axp`, source maps,
  Java generation, generated C++, ARM compiler/linker invocation, packaging, or
  evidence promotion.
- Any change to the accepted mixed Crossfader contract or promoted binding,
  eligibility, result, artifact, or evidence bytes.
- Catalog expansion beyond the exact Task 011A seven-role closure.
- New target/backend support claims, selection through uncertainty, implicit
  fallback, or compatibility inferred from source, family, form, or historical
  use.
- Product-CLI grammar/default changes, new operations, graph persistence, GUI,
  drawer, canvas, AI/MCP, remote transport, progress, queues, or cancellation.
- Additional Gills physical facts, full panel mapping, firmware behavior,
  device access, USB, SD-card writes, upload, flash, execution, measurement, or
  listening.
- Staging, committing, tagging, publishing, or pushing.

## Adapter decisions

The task must decide both mandatory joins from exact contract semantics:

1. A Boolean control-rate clock stream may connect directly to a Boolean
   control-rate clock inlet whose component contract declares that the inlet
   advances internal state on a rising edge. Edge recognition is receiver
   behavior, not a transport conversion. If this cannot be represented and
   validated exactly, stop before the graph rather than inserting a hidden
   adapter.
2. The filter low-pass outlet may connect explicitly to both audio-output
   inlets only when its exact transport type matches both inlet types and the
   outlet cardinality permits two consumers. Otherwise stop and return to the
   component gate for a visible mono-to-stereo adapter identity.

No validator or backend may insert an adapter.

## Deliverables

- This active task contract, updated to complete only after every gate passes.
- The bounded additive component-contract and implementation-binding schemas
  and normative Task 011B contract documentation.
- Six component records and six binding records under a Task 011B-owned record
  root.
- One authoritative graph and one instrument record under the same owned root.
- Six eligibility records, one build request, one probe procedure, and exact
  not-authorized probe inputs.
- One successor record-set manifest with exact parentage and hashes.
- Deterministic generation limited to the owned records above.
- Additive shared validator support for mixed accepted-v0 and Task-011B
  component contracts without changing accepted default output bytes.
- Focused Task 011B tests and a read-only Task 011B validator.
- Necessary status, architecture, contract, schema, and roadmap documentation
  updates only after the acceptance gates pass.
- A completion report with exact IDs, revisions, hashes, test counts,
  preservation evidence, resolver traces, adapter decisions, and remaining
  proof gaps.

## Acceptance tests

Task 011B is accepted only if all of the following pass:

1. All pre-existing 155 tests pass before counting Task 011B tests.
2. Frozen evidence, Phase 4A, Task 005-011A schemas/records/artifacts/evidence,
   accepted operation fixtures, and accepted CLI goldens remain byte-identical.
3. Every accepted default validator and operation result retains its prior
   canonical bytes and meaning.
4. The additive schemas are closed, canonical, deterministic, and limited to
   missing target-independent behavior/type semantics plus exact null legacy
   parameter datatypes and observed durable UUID widths.
5. Six contracts reference exact Task 011A families and retain distinct public
   node identities.
6. Six bindings retain the accepted implementation IDs, pin exact observations
   and seams, map every public facet exactly once, and make no eligibility or
   compatibility claim.
7. Square-clock to counter is proved as exact Boolean control-clock transport
   plus receiver-owned rising-edge behavior, or the task stops before graph
   publication.
8. Filter low-pass fan-out is proved by identical transport types and explicit
   cardinality two, or the task stops for an explicit adapter.
9. Pitch units, integer ranges, parameters, displays, state/lifecycle, and
   parameter-plus-inlet behavior are explicit and validated.
10. The two oscillator instances share one exact contract/binding; no per-node
    semantic identity is allocated.
11. The graph contains exactly the expected eight node IDs and nine explicit
    connections, with no family, binding, observation, path, target/backend,
    device, canvas, or artifact identity.
12. All fixed values validate against exact contract domains. Counter maximum 4
    yields the reviewed four-step selector closure; no implicit range narrowing
    is used to make the counter-to-sequencer connection pass.
13. Graph inspection exposes all eight nodes and the exact seven-contract
    closure, including the reused mixed Crossfader.
14. The new instrument resolves the exact graph and maps the existing Gills
    knob through public instrument `blend` to graph `blend`, with no physical
    fact or device-to-graph shortcut added.
15. Removing, retyping, rewiring, or changing required nodes, connections,
    behavior rules, fixed values, or mappings fails with stable diagnostics.
16. Record set `000005` is an exact parent-preserving superset of `000004`; no
    accepted default changes.
17. The build request is exact and valid, but every new binding is unsupported
    or unresolved unless supported by strictly earlier evidence.
18. `build.resolve` is deterministic, selects the already promoted Crossfader
    only for its nodes, reports all new-node blockers, and emits no backend
    invocation for the whole request.
19. Probe inputs are `candidate-under-test`, `not-authorized`, have no production
    selection authority, and name only the new graph and six new bindings.
20. No build result, artifact descriptor, resource report, compatibility
    promotion, level-3-or-higher evidence, backend execution, compiler action,
    device action, persistence, product-CLI change, staging, commit, or push is
    created or performed.
21. Fresh-process validation, canonical emission, record enumeration reversal,
    working-directory variation, locale variation, and `PYTHONHASHSEED`
    variation produce identical governed bytes.
22. `git diff --check` and the complete local ordinary-CI-equivalent gate pass.

## Decisions Task 011B may make

- Opaque IDs, local facet/node/mapping IDs, revisions, filenames, and the exact
  Task 011B-owned portable record layout.
- The smallest additive component-contract schema revision required for edge,
  semitone, and public behavior semantics, and a binding-schema revision that
  represents exact null legacy parameter datatypes and observed durable UUID
  widths without changing v0.
- Exact reviewed fixed pitch, tempo-pitch, detune, cutoff, resonance, and
  counter values, provided their evidence limits are explicit.
- Whether a mandatory join is exact or requires a visible adapter. Any adapter
  adds its own reviewed family/contract/binding/node and must remain inside the
  two mandatory joins only.
- Exact stable diagnostics and focused negative fixtures.
- Exact successor record-set, eligibility, request, and probe IDs consistent
  with existing allocation.

## Decisions Task 011B must not make

- Backend support, compatibility promotion, source generation, compiler/linker
  behavior, resource evidence, or any Task 011C implementation decision.
- A new family or implementation identity outside an explicitly required
  mandatory adapter.
- A rule that treats a legacy datatype, catalog membership, source path, common
  use, or Java observation as target support.
- An implicit conversion, hidden adapter, range coercion, mono duplication,
  event latch, rate conversion, or first-match binding selection.
- A new Gills physical fact, full device mapping, firmware behavior, hardware
  claim, runtime claim, real-time claim, or audible claim.
- Client-specific catalog/graph/build truth or a change to operation/CLI
  ownership.
- Any mutation of accepted history or an action prohibited by the workspace
  change controls.

## Stop conditions

Stop and report rather than broaden or weaken the task if exact source/identity
evidence does not support a required public facet or behavior; if a family,
implementation, seam, type, or exact reference is ambiguous; if either mandatory
join needs an unreviewed adapter; if accepted bytes or result meaning must
change; if record-set parentage cannot remain exact; if build resolution selects
through uncertainty; or if completion would require Task 011C execution,
hardware access, persistence, staging, commit, or push.

## Completion report requirements

On completion, record all delivered files; exact schema/record IDs, revisions,
and hashes; the two adapter decisions; contract facets and behavior rules;
binding/observation/seam closure; graph nodes, connections, fixed values, and
public mappings; instrument mapping; successor record-set parentage; eligibility
and resolver traces; probe authorization state; pre-existing/final test counts;
validator and determinism hashes; accepted-byte preservation; evidence levels
reached and not reached; scope confirmation; and the exact remaining Task 011C,
Task 012, device, real-time, and audible proof gaps.

## Completion report

### Delivered closure and exact identities

Task 011B completed VS-02 through VS-04 against clean baseline commit
`38e53d666ad091ff541edc75155e6c8453706bd3`. The deterministic generator emits
31 governed files: two additive schemas, 28 Task-owned records, and successor
record-set manifest `schuss-record-set-000005` revision 1. The manifest has
content hash
`sha256:b84ccbbb916560b4f46c8e5619d5c0f7ecf00f50d16ed8209c58461e19e87da3`;
its 34,653 file bytes hash to
`59499fad2858e80c76b5a9b8f977bb61357076b4f36273a0e2217db6ff3ce57b`.
Its exact parent is record set `000004` revision 1 at
`sha256:c0ce942e6e65a79197a88e795044beea5ede3c0299f2926ccd445016ba9cd982`.

The additive schema bytes are:

| Schema | SHA-256 |
| --- | --- |
| `component-contract-v1` | `adcbc1f7131c4ef060226ff4c4f06163cddecb45ee484cf4a314282f36712ddf` |
| `implementation-binding-v1` | `8eaab9b43c984fad6382329965e9dd6c173c7824cec9edce01471634b59579ca` |

Every v0 schema and record remains unchanged. Component v1 adds Q21
`semitone-offset` facets and closed behavior rules; normalized/audio `Frac32`
remains Q27. Binding v1 admits the exact frozen null parameter datatype and
39-through-42-hex durable UUID widths. It makes no compatibility or selection
claim.

The six exact contract/binding pairs are:

| Role | Contract r1 content hash | Binding r1 content hash | Observation |
| --- | --- | --- | ---: |
| Square LFO | `000004` / `sha256:987acb05ac5334d69a87af584395d3d9728a2e566d8f932d7767176324701877` | `000039` / `sha256:1ebc80f66077124dfd1c2a9fa1b59327e0f4a1603a7f795889da5666c4ba6248` | 209 |
| Cyclic Counter | `000005` / `sha256:09e0ccff23775d0b01b8792aa92f370fb3f741d7baa541eb92123bcfcbf871e1` | `000040` / `sha256:7d0a525eedd5ca8bacf61a89c67042340f9732619710da0f69ceaf165e45daf3` | 215 |
| four-step Pitch Sequencer | `000006` / `sha256:f1aa523d117d6516a72bbb7ab70c36399abf34d2dbfe6a27bf1d14e8a6e58023` | `000041` / `sha256:b7a19f4b0b87adc12fedc17346b2af99a50219ba320e191431f50a7a43b11d64` | 918 |
| Sine Oscillator | `000007` / `sha256:6c3bdbe18269794e885c392b3cd40d90c445ed0b207ab4dedb79abe8c28ec410` | `000007` / `sha256:3bd25ea0d236141a8d6e615b4328f9c9e7f5637ab05f762586708e7c7e1beff0` | 549 |
| State-variable Filter | `000008` / `sha256:b4a4f03947665ff8d100371427d886b7217fcc68199f3b164f8c1ca37cdd1c77` | `000015` / `sha256:d52a9f134ab1ad2595d728d7fc6a3adb759fdcee3b24d5a56d5328d276a7205f` | 159 |
| stereo Audio Output | `000009` / `sha256:179c1526ed2bd6d9ad1c6fbfc9caa7abc21f479bef50cf93c8599b5817ca8718` | `000004` / `sha256:e72dd177c4984b525782b0395c96cdc816907b1bf0731902acc729c1c49062bd` | 9 |

Every public port, parameter, attribute, action, and display maps exactly once
to the frozen observation seam. Contract state/lifecycle and implementation
private state are validated separately. The Sine binding is reused by both
oscillator nodes; no per-node contract or implementation identity exists.

### Graph, instrument, and adapter decisions

Graph `schuss-graph-000002` revision 1 has content hash
`sha256:ea98b4cbf1ecb58d70338e5aaaef02385a6ede707b9b78bbc90fac09d53c7460`.
It contains exactly eight nodes and nine connections. Its seven-contract
closure reuses accepted mixed Crossfader contract `000003` unchanged. Reviewed
fixed values are:

| Value owner | Exact values |
| --- | --- |
| Square LFO | base pitch `-48` |
| Cyclic Counter | maximum `4` |
| four-step sequencer | `0`, `5`, `7`, `12` |
| Sine A / B | `-24`, `-23.875` |
| State-variable Filter | cutoff pitch `24`, resonance `0.125` |

The only public graph parameter is normalized `blend`; it binds directly to
the accepted mixed Crossfader fade inlet. Instrument
`schuss-instrument-000002` revision 1 has content hash
`sha256:d20e0f108397987a4b102fab35afc8fb00a42acfa33d48522226de2c343e7adb`
and preserves `device-input-000001 -> instrument blend -> graph blend` with no
new physical Gills fact.

No adapter is required at either mandatory join. Square LFO and counter use
the same Boolean control-rate clock transport; rising-edge recognition is an
explicit receiver behavior. The filter low-pass outlet and both audio endpoint
inlets have identical transport types, the outlet cardinality is exactly two,
and the graph contains two explicit connections.

### Eligibility, probe, and fail-closed build result

Build request `schuss-build-request-000002` revision 1 has content hash
`sha256:2569cde83cada208a626f14fe6762a193e4d99f3f8d43de1bd376f4e8bead449`
and stops at `artifact-generation`. Procedure `schuss-procedure-000002`
revision 1 has content hash
`sha256:86954dd767c3d49e396f25313f467d843b4d168d24e317e435fd61737c111985`.

The six eligibility and probe pairs are:

| Role | Eligibility r1 content hash | Probe input r1 content hash |
| --- | --- | --- |
| Square LFO | `000002` / `sha256:5c1afa3bb5560527a87b61d2ddf39127616deac111c0205bddca5d3c9a255743` | `000003` / `sha256:a38c8ae4c3c74cbe321e6725272f1bb9c2668a918d3988aa8c1897bf95eb803e` |
| Cyclic Counter | `000003` / `sha256:9017d8b69e2fe78f199a36779e07bf2b93765a6ca03165002d95ee1718a395c4` | `000004` / `sha256:ecd175b915b3128eaae26aa95560e6f39f20297f9096e453a3f04f748fd094a8` |
| four-step Pitch Sequencer | `000004` / `sha256:e7f08cfbc7ed42dbe400fa96e3a1391b67cbe97e2e72fb266a3b0626826503ee` | `000005` / `sha256:0fdb81eb5cd3182ba9b8abbc942a8dcb7edbb62ceaa5a10b8eb867b7d22d4c6d` |
| Sine Oscillator | `000005` / `sha256:4b2fe299c035fac2824b06d74777cc3dacf067138300ecee46ed40939151d480` | `000006` / `sha256:7739901517f3e3d458d2dccb6417252124e59e9663349af897dfc61b56294552` |
| State-variable Filter | `000006` / `sha256:9f50d84170beef0a14da1e1456f3ecfcdfb873ac19df0c2f0c337f8f1da03879` | `000007` / `sha256:dc2d990716dc4027e65e438fa064d2b61cc47c34b2de35e569ab49c42562fe60` |
| stereo Audio Output | `000007` / `sha256:2b90c30d6df9d8911bc0d4f6d8ec57e3a7f2eebdfd3a24a45021cd9e59e198e2` | `000008` / `sha256:a57a842ada50df8daa5a33ade8c18b2550405877a08ff83af5227337bdff5d64` |

All six eligibility pair states remain `not-evaluated`, all compatibility
evidence collections are empty, and all six probe inputs are
`candidate-under-test`, `not-authorized`, and without production selection
authority. `build.resolve` returns overall `unresolved`: Square LFO, Counter,
both Sines, Filter, and Output are unresolved; the native-object Sequencer is
unsupported; only the already promoted mixed Crossfader is selected.
`backend_invocation` is `null`. The canonical resolution result hashes to
`64ca8e19d0695aab2a34f3908968c31016376105bf4a63ae25d2a94a464095f0`.

### Validation, preservation, and evidence limits

Pre-task counts were 14 inventory, 6 catalog, and 135 contract tests. Final
counts are 14 inventory, 6 catalog, and 148 contract tests: all 168 pass, with
13 focused Task 011B tests. Negative fixtures cover missing/rewired topology,
changed fixed values, missing edge behavior, clock mismatch, low-pass
cardinality, out-of-range values, implicit Boolean-to-integer conversion, and
a prohibited third low-pass consumer. Fresh-process runs vary working
directory, locale, `PYTHONHASHSEED`, and record enumeration order without
changing governed bytes.

The Task 011B validator emits 1,441 bytes with SHA-256
`3a06c3ebb9651e7a7e4ffda085117e0555a180a0b96d0277e6ac529383c2d2b0`.
Its exact graph-inspection hash is
`e87a1acf68edf1ab94477e5f4679b42691547cf67af2e1c2f21da7299bf9784d`.
All accepted default validator bytes remain exact: raw inventory
`3a9ba2256592972c3e104b21b821d9befa9ac2c75c8f69af63020b4765271e80`,
resolved inventory
`bb435d07670ccf4ce7dad5182a75ad9bc2c18dedb5c0b184ce9d6cca3691e738`,
Phase 3 `faf90cb359effe3b24f2c68ca66086d1acee813acf0ceacb7c3218e7e9ae62f4`,
Phase 4A `8d21352c7265a50a93646f93f9696e4b02ebcfbab3443da53a2cc47c8fc34238`,
Task 011A `da60081e4fed9e07f243ec906f8e9410c3c88385cc989286d76c0d373ae44c80`,
component/graph
`d295106d38cdf9075a85d9e1a803b5df23e3ffbbe934dceb3cec9194b59ce6af`,
device/instrument
`254a77c534c911da759a21e438544b4b0e69e16093307e0fc269a0857b6d3af6`,
target/build
`7a898b3409e5ad7ef02eab1246f87756cc2af7cbd512d72f9a5eb43b1573a3a2`,
and Task 009 prerequisite
`3f8f3df84fd47ab51441ec6b3d30abc43fcfd18b2a69cffc6a508f5f0fe08a8b`.

Task 011B reaches structural/schema and target-independent component/graph
resolution only. It creates no build result, artifact descriptor, resource
report, compatibility promotion, or evidence claim. Backend lowering,
artifact generation, ARM compile/link, connected-device execution, real-time
measurement, and audible/listening evidence all remain `not-run`. Task 011C
owns the earliest backend expansion and levels 3-5 for this slice; Task 012
owns UI clients; device, real-time, and audible levels require later separate
authorization. No staging, commit, publication, push, upload, flash, SD-card,
firmware, compiler, or hardware action occurred.
