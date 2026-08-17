# Task 025: Fail-closed direct-compiler core-library tranche

Status: accepted revised contract and completed under the resumed overnight
goal on 2026-08-17. All fifteen revised acceptance tests passed. The original
all-eight-node level-5 contract was materially revised after the authenticated
reverb allocation audit in `contracts/task025/reverb-allocation-boundary.md`.
Task 026 later satisfied its authoring dependency through a separately accepted
reverb-free seven-node executable profile; it did not weaken this failed
reverb boundary.

## Goal and why it exists

Promote the five Task 024 effects subjects whose exact source arithmetic,
state, and runtime contracts can be represented honestly as target-independent
direct operations: saw, PWM, exponential smoothing, audio soft clipping, and
interpolated VCA. Preserve the selected Rings-derived reverb as exact source
provenance but make it explicitly unsupported for the new backend after static
evidence proved that its 32,768-byte allocation is inconsistent with the
retained header's 65,536-byte initialization span.

This produces a useful native-operation tranche and an exact compiler plan
that resolves seven of the eight reference-graph nodes, then fails closed at
reverb. The five promotion claims pass at evidence level 2, the reverb claim
fails at level 2, and the complete graph therefore does not pass level 2. It
must not turn a successful compiler invocation into a false runtime or
resource-readiness claim.

## Dependencies and exact authority

ADR 0011 owns legacy-equivalent direct semantics. ADR 0014 and
`docs/APPLICATION_SPINE_PLAN.md` own sequencing and proof separation. The
selection authority remains `schuss-core-selection-000002@1` in exact parent
record set `schuss-record-set-000016@1`; Task 025 does not rewrite either.
The source graph remains `schuss-graph-000004@1` with exact component
contracts `000003`, `000009`, `000012`, `000013`, `000015`, `000016`,
`000017`, and `000020`.

The accepted Task 016 crossfader and output direct semantics are immutable
reused inputs. Task 017 bindings `000051`, `000052`, `000054`, `000055`,
`000056`, and `000059` are exact source authorities. The pinned factory and
patcher bytes are authenticated inputs. The reverb boundary decision is the
only authority for its unsupported state.

## In scope

- Five target-independent direct operation specifications: saw
  `schuss-direct-operation-spec-000008`, PWM `000009`, exponential smoothing
  `000010`, audio soft clipping `000011`, and VCA
  `schuss-direct-operation-spec-000013`. Reverb's original `000012` allocation
  remains unissued.
- Five distinct native C++ realization identities: saw
  `schuss-implementation-000090`, PWM `000091`, smoothing `000092`, soft clip
  `000093`, and VCA
  `schuss-implementation-000095`. Reverb's original
  `schuss-implementation-000094` allocation remains unissued. Each native
  identity links to one exact Task 017 source binding without changing it.
- Six explicit eligibility records `schuss-binding-eligibility-000027`
  through `schuss-binding-eligibility-000032`: five supported native
  target/backend pairs and one
  explicitly unsupported legacy reverb pair.
- Six level-2 evidence claims `schuss-evidence-claim-000038` through
  `schuss-evidence-claim-000043`: five passed semantic promotions, with VCA
  retaining `000043`, and failed reverb allocation claim `000042`.
- Carried crossfade and output eligibilities
  `schuss-binding-eligibility-000012@3` and
  `schuss-binding-eligibility-000014@3`, updated only to name backend revision
  3 while preserving their accepted bindings and evidence.
- Direct backend `schuss-backend-000002@3`, omitted-instrument build request
  `schuss-build-request-000004@3`, and successor record set
  `schuss-record-set-000017@1`.
- Version-aware validation of both retained selection-packet schemas without
  changing either historical packet.
- Exact source authority, arithmetic, initialization, state, schedule, runtime
  dependencies, semantic host vectors, deterministic schema/record generation,
  and stable fail-closed diagnostics.
- Ordinary compiler planning for exactly `schuss-graph-000004@1`, proving
  exact selection of the two reused Task 016 bindings and five new native
  bindings, plus deterministic rejection of the reverb node before lowering.
- Focused, adjacent, freshness, determinism, governance, and one final
  aggregate validation pass.

IDs `000081` through `000089` remain Task 024 overload implementations.
`schuss-direct-operation-spec-000012`, `schuss-implementation-000094`, and
`schuss-build-handler-000004` remain unallocated; their earlier reservation
does not authorize unsafe records or handler dispatch.

## Out of scope

- A native reverb operation or binding, supported reverb eligibility, reverb
  wrapper generation, support-header publication, handler dispatch, ARM
  compile/link, device execution, resource-safety, real-time, or audible proof.
- Removing reverb from the Task 024 selection packet, rewriting Task 017/024
  history, allocating 65,536 bytes, shrinking the header, treating bytes as
  elements, or otherwise choosing a corrected reverb realization.
- A successful full-effects build, general graph scheduling, arbitrary object
  translation, Java, `.axp`, compatibility fallback, UI, project authoring,
  Gills panel mapping, staging, commit, push, release, upload, flash, or SD
  write.

## Inputs and deliverables

Inputs are this contract; the reverb boundary record; ADRs 0011 and 0014;
exact record set `000016`; the Task 024 packet; accepted Task 016 direct
records; Task 017 graph/contracts/source bindings; the pinned factory object
bytes; and the pinned patcher fixed-point/runtime sources.

Deliverables are this revised contract and read-only validator; one direct
operation schema successor and five operation records; five native bindings;
six eligibility/evidence records; backend/request successors; record set
`000017`; a pure five-operation semantic module and deterministic goldens;
exact compiler-plan and negative fixtures; a completion validator/report; and
integrated status, roadmap, history, task index, application plan, and
governance rules.

No build handler, generated full-graph C++, ELF, or level-3-through-5 evidence
is a Task 025 deliverable after the fail-closed revision.

## Semantic rules

Saw and PWM retain exact phase wrapping, BLEP voice rotation, BLEP table
stepping, crossing order, integer division branches, and `MTOFEXTENDED`
dependency. Host fixtures inject deterministic pitch and BLEP tables without
claiming ownership of runtime lookup bytes.

Smoothing retains the exact `___SMMLA` recurrence and one control-rate update
per block. Its fixture fixes only the existing graph default time value and
does not define a general authoring transfer function. Soft clipping retains
signed-28 saturation and the reviewed Q31 cubic arithmetic. VCA retains prior
gain, `(gain-prev)>>4`, one Q27 audio multiply per sample, and state advance
order.

Crossfade and output reuse Task 016 records unchanged. The exact graph schedule
remains source evidence only; backend lowering must not begin because reverb
has no eligible realization for backend revision 3.

## Reverb unsupported rule

The pinned object calls `sdram_malloc(32768)`, whose pinned runtime argument is
bytes. The exact header uses a 32,768-element `uint16_t` engine and clears the
entire array. The new eligibility `000031` therefore selects exact source
binding `000056@2` only to state `unsupported`, backed by failed level-2 claim
`000042`. There is no direct operation spec or native binding for reverb.

Compiler planning must resolve the other seven graph nodes exactly once and
return stable unsupported diagnostics identifying the reverb contract/binding
boundary. Stages 5-10 remain `not-run`; no handler can register for request
`000004@3`.

## Diagnostics and evidence boundary

Wrong parent, packet, source hash, operation set, binding, eligibility,
backend, graph, or reverb disposition fails closed with a stable
`EFFECTS_DIRECT_*` validation diagnostic. Compiler planning additionally
retains its accepted stable `COMPILER_*` diagnostic vocabulary.

Level 1 passes for the complete compiler plan. At level 2, five promotion
claims pass and the reverb allocation claim fails, so complete-graph level 2
is `failed`. Levels 3-8 remain `not-run`. Catalog review, host vectors, and a
failed resource contract do not imply source generation, ARM acceptance,
device behavior, corruption, timing, stability, or sound.

## Validation cadence

Run the contract validator, semantic unit tests, schema/record generation,
exact planner tests, and negative diagnostics first. Run adjacent direct
frontend, compiler-front-half, catalog, and application tests once focused
behavior stabilizes. Reproduce generated records and goldens from fresh roots
after the diff freezes. Do not run the ARM toolchain. Review the complete diff
and run the aggregate contract/inventory/catalog suite once at completion; a
failure returns to the smallest focused test and permits one final aggregate
rerun after correction.

## Acceptance tests

1. The contract validator fixes the revised goal, scope, exact inputs,
   deliverables, IDs, semantic rules, diagnostics, validation cadence,
   evidence boundary, and prohibited actions.
2. Parent record set `000016`, Task 024 packet, Task 017 source bindings, and
   all historical parent bytes validate unchanged.
3. The direct-operation schema successor admits exactly the five new opcodes,
   with reverb gap `000012` and VCA `000013` preserved;
   stale versions and extra opcodes fail closed while Task 016 specs retain
   their own accepted schema.
4. Each new operation spec binds one exact packet contract/source binding,
   records numeric/state/schedule/runtime semantics, and names its exact
   deterministic vector section.
5. Five native bindings preserve distinct identity, map every contract facet
   exactly once, and retain source-observation plus semantic evidence.
6. Eligibilities `000027`-`000030` and `000032` support only the exact
   Ksoloti/backend-3 pair with no fallback; eligibility `000031` marks exact
   legacy reverb binding `000056@2` unsupported with evidence claim `000042`;
   carried eligibilities `000012@3` and `000014@3` preserve crossfade/output.
7. Backend `000002@3` and request `000004@3` are exact, instrument-omitted,
   and have no executable handler registration.
8. Host vectors cover saw/PWM state and BLEP scheduling, smoother recurrence,
   soft-clip arithmetic, VCA interpolation, and deterministic two-block
   transitions for the five-operation semantic fixture.
9. The ordinary compiler front half selects Task 016 bindings `000046` and
   `000048`, selects new bindings `000090`-`000093` plus `000095`, and
   identifies reverb as the sole unsupported graph node.
10. The exact plan stops before compound elaboration/backend lowering, emits
    no generated C++, support header, command vector, or ELF, and records
    level 1 `passed`, complete-graph level 2 `failed`, and levels 3-8
    `not-run`.
11. The reverb audit validates exact object/header/runtime hashes, 32,768-byte
    allocation, 65,536-byte clear span, and the absence of any native reverb
    record or handler.
12. Mutated parent, packet, source hash, binding, eligibility, backend, graph,
    or reverb disposition fails closed with stable diagnostics and no output.
13. Two fresh roots produce byte-identical records, semantic goldens, and
    unsupported compiler-plan results without invoking Java, `.axp`, ARM, or
    hardware.
14. Completion evidence states Java, `.axp`, ambient discovery, build handler,
    ARM, device, real-time, and audible actions are false; it distinguishes
    the five passed component promotions from the failed reverb/complete-graph
    level-2 boundary, and records levels 3-8 explicitly `not-run`.
15. Generated freshness, parent preservation, governance, focused and
    adjacent suites pass; the diff is frozen and one final aggregate suite
    passes before Task 025 is marked complete.

## Decisions Task 025 may make

- Exact opcode names, state keys, host fixtures, schema successor, portable
  provenance fields, native symbol names, and deterministic evidence layout
  for the five supported subjects.
- The smallest version-aware compiler-context schema handling needed to keep
  Task 016 direct-operation records and both retained selection-packet schemas
  valid beside their Task 025 successors.
- Exact stable unsupported diagnostics and plan fixture for the reverb node.

## Decisions Task 025 must not make

- A reverb fix, native reverb realization, allocation-size reinterpretation,
  changed DSP math/timing/state, or a full-effects executable claim.
- Changes to Task 024 selection history, Task 017 source records, public
  component contracts, graph topology, instrument semantics, project history,
  UI behavior, or client orchestration.
- Evidence above level 2, release readiness, connected-device safety, runtime
  failure, memory corruption, audible quality, or real-time suitability.
- Upstream mutation, ambient/latest discovery, staging, commit, push, release,
  upload, reset, flash, or SD write.

## Readiness and activation state

The user authorized this evidence-led fail-closed revision. Task 025 may
complete only as the partial level-2 tranche above. Task 026 may be documented
as proposed but cannot be accepted or implemented until a separate authorized
prerequisite resolves the reverb allocation/ownership contract and the
project-authored graph identity seam.
