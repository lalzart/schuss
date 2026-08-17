# Task 028: Twenty-item direct selectable palette

Status: accepted and complete on 2026-08-17. All fifteen acceptance tests pass
within the exact local selection and normalized backend-lowering boundary. The
user's explicit request narrowed the catalog/compiler tranche to one bounded
palette promotion; the transparent-compound portion previously associated
with Task 028 remains deferred.

## Goal and why it exists

Expand the independently selectable, direct-backend-proven palette from the
five native implementations accepted by Task 025 to exactly twenty by adding
fifteen safe promotions. This exists to make a small, coherent musical palette
that can be assembled into modest graphs without claiming broad catalog
coverage or any target executable, device, realtime, or audible result.

## Dependencies and verified baseline

The exact parent is `schuss-record-set-000020@1`. Task 024 supplies sixty
function-first catalog families and eighty-two accepted implementations. Task
027 adds one catalog-only physical-resonator implementation, exact Mutable
Instruments provenance review, and no compiler support. Task 025 supplies the
five counted baseline promotions: native implementations 000090, 000091,
000092, 000093, and 000095. Task 026 carries their eligibility to exact backend
`schuss-backend-000002@4` and target `schuss-compute-target-000001@2`.

The known Rings-reverb source implementation 000056, absent native allocation
000094, failed evidence claim 000042, and unsupported eligibility 000031 remain
unchanged. The Task 027 physical-resonator implementation 000096 remains
catalogued-only.

## In scope

- One exact fifteen-entry selection packet with catalog/source identity,
  family, functional category, requirements, exclusions, evidence gap, and
  deterministic allocation.
- Native implementation bindings 000097 through 000111, direct-operation specs
  000015 through 000029, eligibility records 000033 through 000047, level-2
  evidence claims 000045 through 000059, and level-3 claims 000060 through
  000074.
- Reuse of the five exact Task 017 component contracts where they already fit;
  ten new primitive component contracts 000022 through 000031 only for the ten
  selected catalog implementations that lack one.
- Exact local selection and normalized operation-IR lowering against backend
  000002 revision 4, with deterministic fail-closed diagnostics for stale,
  absent, mismatched, duplicate, or weaker records.
- A balanced palette summary that explains the graphs the twenty promotions
  can support together with the already accepted seven-node Task 026 profile,
  while keeping all execution claims absent.
- Record set `schuss-record-set-000021@1`, focused and adjacent tests, two
  copied fresh-root reproductions, and integrated governance.

## Out of scope

- Broad catalog support, family/category reassignment, preferred-object policy,
  catalog taxonomy redesign, UI, projects, sessions, or jobs.
- Transparent compounds, the extended Rings physical resonator, Warps,
  Clouds, Elements, macro voice, topographic sequencing, or any candidate
  whose exact component/binding/lowering boundary is not in the closed packet.
- Repair, allocation, suppression, or promotion of Rings reverb or native ID
  000094.
- Generated C++, ARM compilation/linking, Java, legacy `.axp`, Ksoloti build or
  execution, device upload, hardware access, realtime/resource measurement,
  audible listening, release, publication, staging, commit, or push.
- Treating catalog presence, source attribution, source text, Ksoloti behavior,
  or Task 027 source metadata as compiler, target, device, or audible proof.

## Inputs and deliverables

Inputs are ADRs 0005, 0006, 0007, 0010, 0011, 0012, 0013, and 0015; the exact
Task 027 parent record set; Tasks 024-027 records and evidence; the compiler
front-half, component/binding/eligibility, backend, and evidence contracts; the
pinned source lock and exact accepted legacy observations; and the current
dirty worktree, preserved without cleanup.

Deliverables are this contract; the exact curation decision; selection-packet,
direct-operation, and lowering-proof schemas and records; the ten bounded
component contracts; fifteen native bindings and eligibilities; thirty
level-specific evidence claims; a deterministic local palette lowerer; the
balanced-palette and remaining-gap summaries; the exact successor record set;
tests, validators, two fresh-root evidence runs; and coherent status, history,
roadmap, task-index, and application-plan documentation.

## Exact counted palette

The count is deliberately narrow: only the five Task 025 native promotions and
the fifteen Task 028 native promotions count. The seven already accepted
Task 026 profile bindings remain useful supporting primitives but are not
silently added to the twenty.

| New native | Catalog/source | Existing family | Function | Exact local requirement | Explicit exclusion/evidence gap |
| --- | --- | --- | --- | --- | --- |
| 000097 | 000053 / observation 113 | 000033 Attack-Decay Envelope | modulation-control | Q27 control, pitch/fixed-point runtime identity | no source artifact, ARM, device, realtime, or audible proof |
| 000098 | 000049 / observation 229 | 000029 Clocked Logic Toggle | timing-sequencing | control Boolean edge/state identity | no scheduling beyond the normalized operation contract |
| 000099 | 000050 / observation 1208 | 000030 Pseudo-Euclidean Gate Sequencer | timing-sequencing | control state plus retained random-runtime identity | no statistical, realtime, or audible proof |
| 000100 | 000057 / observation 527 | 000037 Struck Drum Voice | sound-sources | Q27 audio/control plus exact Braids header locator | Mutable provenance is not support; no ARM/device/audio proof |
| 000101 | 000058 / observation 526 | 000038 Struck Bell Voice | sound-sources | Q27 audio/control plus exact Braids header locator | Mutable provenance is not support; no ARM/device/audio proof |
| 000102 | 000008 / observation 499 | 000004 Uniform Noise | sound-sources | Q27 audio plus retained random-runtime identity | no distribution measurement or audible proof |
| 000103 | 000011 / observation 115 | 000007 ADSR Envelope | modulation-control | Q27 control plus pitch/fixed-point runtime identity | no host/device timing equivalence proof |
| 000104 | 000013 / observation 208 | 000008 Sine LFO | modulation-control | Q27 control plus pitch/sine-table runtime identity | no rate accuracy or realtime proof |
| 000105 | 000069 / observation 123 | 000049 Decay Envelope | modulation-control | Q27 control plus pitch/fixed-point runtime identity | no host/device timing equivalence proof |
| 000106 | 000064 / observation 199 | 000044 Control Low-pass Filter | filters-resonators | Q27 control plus pitch/fixed-point runtime identity | no frequency-response measurement |
| 000107 | 000070 / observation 162 | 000050 Two-pole Resonant Audio Low-pass | filters-resonators | Q27 audio/control plus biquad/pitch runtime identity | no stability, resource, or frequency-response measurement |
| 000108 | 000078 / observation 318 | 000058 Saturating Gain | shaping-dynamics | exact audio overload plus Q27 fixed-point identity | control overload excluded; no artifact or audible proof |
| 000109 | 000077 / observation 421 | 000057 Two-input Audio Mixer | mixing-routing | exact audio overload plus Q27 fixed-point identity | other arities/rates excluded; no artifact or audible proof |
| 000110 | 000034 / observation 255 | 000023 Addition | mixing-routing | exact audio overload and Q27 addition identity | control/integer overloads excluded |
| 000111 | 000074 / observation 224 | 000054 Triggered Value Latch | data-math-logic | exact fractional-control overload and rising-edge state | Boolean/integer alternatives excluded |

No effect is added. The two Task 027-tagged additions are Drum and Bell; their
provenance remains a filter facet and does not change their sound-source
families or raise their evidence level.

## Evidence and lowering rules

Catalog membership and source identity are prerequisites, not support claims.
Each new level-2 claim proves only an exact component contract, catalog/source
identity, native binding, and eligible target/backend pair. Each level-3 claim
additionally requires the ordinary shared binding resolver to select exactly
one native binding and the Task 028 lowerer to emit the exact normalized
operation IR. No C++, object, executable, package, or runtime result is emitted.

The lowerer must reject any source hash, catalog/family identity, contract,
binding, eligibility, target/backend pair, operation opcode, facet map,
dependency locator, count, or allocation that differs from the packet. It must
also reject duplicate candidates and any attempt to include implementation
000094 or Rings reverb.

Task 028 reports levels 1-3 as `passed`. Level 4 source generation, level 5 ARM
compile/link, level 6 connected device, level 7 realtime/resource, and level 8
audible behavior remain `not-run`. A level never implies a later level.

## Practical palette boundary

The counted twenty now cover pitched saw/PWM and noise/percussion sources;
ADSR, AD, decay, LFO, and smoothing modulation; VCA, saturation, addition,
mixing, and latching; control and resonant audio low-pass filtering; and toggle
plus pseudo-Euclidean timing. Together with the already accepted Task 026 sine,
square-LFO, counter, four-step sequencer, crossfade, state-variable filter, and
output bindings, these records are sufficient at the structural and lowering
levels to describe modest subtractive voices, percussion voices, modulation
paths, mixes, and clocked patterns. This is not evidence that any such graph
has been compiled, run, timed, heard, or approved as a product.

## Validation cadence

Focused checks cover the task contract, exact packet, source/overload identity,
new contracts, total facet maps, eligibility, resolver traces, normalized IR,
negative mutations, gap ledger, and generated freshness. Adjacent regression
covers Tasks 024-027 catalog/provenance behavior, the retained Rings failure,
Task 026 backend selection, and record-set closure.

After implementation freeze, one expensive reproduction copies the repository
twice and requires byte-identical generated Task 028 outputs under different
process settings. The final aggregate contract/inventory/catalog suite runs
once after freeze. The hard prohibition on compilation and execution excludes
any aggregate command that would invoke ARM, Java, `.axp`, hardware, or audio.

## Acceptance tests

1. The contract validator confirms the goal, exact parent, fixed IDs, counted baseline, exact fifteen-entry cohort, decisions, evidence levels, validation classes, and prohibited actions.
2. The selection packet contains exactly fifteen unique catalog/source identities, family references, native allocations, requirements, exclusions, and evidence gaps in canonical order.
3. Every selected source resolves to the accepted Task 027 catalog projection and exact frozen observation; source path, source hash, definition/overload identity, and provenance tags remain unchanged.
4. The ten new component contracts match every observed inlet, outlet, parameter, attribute, action, and display exactly; the five existing Task 017 contracts are reused by exact reference.
5. Exactly fifteen native bindings 000097-000111 have complete one-to-one facet maps, unique portable symbols, explicit state/dependency facts, and no implicit fallback.
6. Exactly fifteen eligibilities 000033-000047 support only target 000001 revision 2 and backend 000002 revision 4 at evidence level 2; unresolved dependencies or resources fail closed.
7. The shared resolver independently selects exactly one intended native binding for each one-node candidate graph and rejects missing, stale, ambiguous, mismatched, or weaker records.
8. Exactly fifteen direct-operation specs 000015-000029 lower to canonical normalized operation IR with exact source, contract, binding, opcode, facet, state, dependency, schedule, and exclusion identity.
9. Exactly fifteen level-2 and fifteen level-3 claims are distinct; levels 4-8 remain `not-run` and no generated source, ARM object, executable, package, device, realtime, or audible record exists.
10. The final counted direct palette is exactly twenty: the fixed five Task 025 promotions plus the fifteen Task 028 additions; supporting Task 026 bindings are reported separately and not double-counted.
11. Drum and Bell retain Task 027 Mutable provenance, ordinary sound-source families, and exact source entries; provenance alone never produces eligibility or lowering.
12. Rings reverb implementation 000056, absent native 000094, failed claim 000042, unsupported eligibility 000031, and diagnostics remain byte-identical and unpromoted.
13. The remaining-gap ledger accounts for every accepted catalog implementation and every Task 027 source-review entry without turning an unreviewed candidate into support.
14. Two in-process generations and two copied fresh roots produce byte-identical schemas, records, packet, lowering proof, summaries, and record set under varied process settings.
15. Focused and adjacent suites pass, generated files are fresh, the complete diff and acceptance matrix are reviewed, and one permitted final aggregate suite passes after freeze.

## Decisions Task 028 may make

- The exact fifteen-candidate cohort, stable allocations fixed in this contract,
  task-specific schema layout, normalized operation-IR shape, canonical order,
  portable symbols, and deterministic diagnostic codes.
- The smallest component contracts and native binding/eligibility companions
  required for exact local selection and lowering.
- Whether any candidate must be withheld when its exact source, interface,
  dependency, resource, or lowering identity cannot be established. A withheld
  candidate creates an explicit shortfall gate; it may not be replaced with a
  weaker claim merely to reach twenty.

## Decisions Task 028 must not make

- A new family/category, family merge, taxonomy redesign, UI, preferred object,
  transparent compound, catalog-wide support policy, device mapping, firmware
  architecture, resource budget, or audible-quality decision.
- A Rings-reverb repair or physical-resonator promotion; a claim based only on
  source text, Ksoloti behavior, ancestry, or catalog presence; or any evidence
  above the exact locally reproduced lowering boundary.
- Mutation of accepted parent bytes or upstream checkouts; ambient discovery,
  fallback, generated C++, ARM/Java/AXP/build execution, hardware, publication,
  staging, commit, or push.

## Activation state

The user's explicit request activates this Task 028 contract. Completion does
not activate transparent compounds, broad catalog expansion, UI work, Task 029,
Git publication, or any build/hardware action.
