# Task 017: Curated core expansion and richer headless reference instruments

Status: complete on 2026-08-16; accepted locally through evidence level 2;
new direct realizations remain explicitly unsupported except for transparent
compound elaboration.

## Goal and why it exists

Expand the reviewed component core and prove it through richer, deterministic
headless reference instruments after the complete direct compiler path is
accepted. The task turns compiler breadth into useful musical breadth without
using UI work or allowing catalog classification to outrun contracts,
bindings, and executable evidence.

## Dependency

Task 016 must be complete with accepted direct DSP/runtime specifications,
full-slice lowering, and exact handler evidence. Task 016 satisfied this
dependency through the accepted legacy-equivalent route and local evidence
level 5 before Task 017 records were created. Task 017 may not begin semantic
promotion or implementation without separate task authorization; that
authorization was supplied for this completed implementation.

## In scope after the dependency closes

- A review packet selecting a bounded first expansion batch by function and
  form, with provenance only as facets.
- For every selected family: exact contract, one or more implementation
  bindings, target/backend eligibility, compatibility evidence, catalog
  readiness, and explicit unresolved facts.
- At least two immutable non-UI reference graphs/instruments that exercise
  state, modulation, fanout, compounds, parameter mapping, and reusable
  components beyond the Task 011C slice.
- Shared validation, compiler planning, direct execution where supported,
  deterministic CLI inspection/build results, and separate evidence levels.
- A review ceiling of 12 new families and two reference instruments so the
  task cannot become an uncontrolled catalog census.

## Out of scope

- Reopening Task 016 semantics, choosing families by source/provenance category,
  bulk import, unreviewed compatibility, complete catalog coverage, sampling
  assets, additional targets/devices, full Gills mapping, UI, AI/MCP, hardware,
  audible claims, commit, or push.

## Inputs and deliverables

Inputs are the accepted Phase 4A catalog, Tasks 005-016, raw/resolved
observations, source locks, and explicit review criteria. Deliverables are an
immutable selection packet; schema-compatible families/contracts/bindings/
eligibilities; two graphs/instruments; compiler/build evidence; catalog and
CLI fixtures; tests/validator; documentation; and a completion report.

## Acceptance tests

1. Task 016 is complete before any Task 017 semantic record is created.
2. The selection packet names inclusion/exclusion rationale and never treats
   provenance as primary function.
3. No more than 12 new families and exactly two reference instruments enter
   the accepted closure.
4. Every compiler-facing variant has exact contract, binding, eligibility,
   target/backend, dependency/resource, and evidence joins; missing joins remain
   unresolved rather than guessed.
5. Both graphs validate structurally, plan deterministically, and either build
   through an exact handler or report stable unsupported diagnostics.
6. Existing Task 011C, 013, 014, and 015 results remain byte-identical.
7. CLI catalog/graph/build output is deterministic and no UI-specific semantic
   path is introduced.
8. Evidence levels are reported independently; device/real-time/audible levels
   require separate authorization.
9. Full tests, validators, schema checks, and `git diff --check` pass.

## Decisions Task 017 may make

- Review scoring, the bounded family batch, exact two reference-instrument
  concepts, new stable IDs, graph topology using already owned semantics, and
  catalog readiness based on retained evidence.

## Decisions Task 017 must not make

- Task 016's compatibility-mode decision or any resulting Schuss-native
  DSP/runtime/license specifications, implicit compatibility, uncontrolled bulk
  expansion, UI design, hardware proof, commit, or push.

## Completion report

Task 017 accepts `schuss-record-set-000011@1`, twelve reviewed family additions,
and exactly two immutable headless reference instruments. Eleven legacy-backed
families retain exact source/seam review but no invented direct implementation;
their direct eligibility is `not-evaluated`. The Schuss-authored Dual
Percussion Voice is supported only as a transparent compound form, and its
unsupported internal legacy bindings stop planning with deterministic
diagnostics. The second effects graph stops with deterministic unsupported
binding diagnostics.

Structural/schema and component/graph evidence levels 1-2 pass. Backend
lowering, source generation, ARM compile/link, connected-device, real-time,
and audible evidence levels 3-8 are `not-run` for the two Task 017 instruments.
No UI, device, hardware, publication, stage, commit, or push action occurred.
The detailed report and retained CLI/planning evidence are under
`evidence/task017-completion-v1/`.

All ten dedicated Task 017 tests pass. Ordinary repository discovery retains
the same six inherited baseline failures documented by Task 016; none names
Task 017. The completion report keeps that repository-wide green-status gap
explicit rather than changing unrelated historical goldens or ignored inputs.
