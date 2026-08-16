# Task 018: Full Gills implementation and parameter/control mapping

Status: contract complete on 2026-08-16; Tasks 016 and 017 are complete, so
implementation is ready but not started.

## Goal and why it exists

Replace the deliberately minimal one-knob Gills contract with an authenticated,
complete panel model and prove the explicit runtime-facing chain from physical
Gills slots through instrument facets into exact graph facets. This task exists
to make Gills a fully described device and performance surface without making
the device profile, instrument, graph, compute target, or backend share identity.

For this task, complete means complete against one pinned and reviewed Gills
hardware/panel revision: every physical input, gesture source, feedback output,
display capability, and physical I/O slot is either represented with accepted
evidence or covered by an explicit unresolved fact. It does not mean that
connected-device, real-time, audible, electrical-safety, or release evidence is
automatically established.

## Dependencies

Task 017 must be complete before Task 018 may create a Gills evidence packet,
semantic successor, runtime realization, mapping, build request, or evidence
claim. Task 017 itself depends on Task 016. Both requirements are now
satisfied: Task 016 is complete under the accepted legacy-equivalent route
through local evidence level 5, and Task 017 is complete through local evidence
level 2. Task 018 may not bypass either dependency or reopen Task 016's accepted
compatibility-mode choice.

The implementation phase also requires portable, pinned, license/provenance-
reviewed evidence for the exact Gills hardware/panel revision. A sibling
checkout, remembered panel layout, mutable path, display label, or historical
instrument file may guide the evidence review but is not durable proof.

## In scope after the dependencies close

- A deterministic evidence packet for one exact Gills hardware/panel revision,
  including a complete physical-slot census and the authority and limitations
  for every asserted range, resolution, gesture, feedback, display, and I/O
  fact.
- Immutable successors to the accepted Gills device profile and the two exact
  Task 017 reference instruments, retaining all earlier record bytes.
- Explicit device-control/gesture-to-instrument and instrument-to-graph
  mappings, plus instrument-to-device feedback/display mappings where the
  accepted panel and instrument contracts require them.
- A deterministic coverage matrix in which every accepted physical slot and
  every public instrument facet is mapped, intentionally unused with rationale,
  or explicitly unresolved; absence is never treated as coverage.
- Exact pickup, smoothing, transform, update-boundary, action-trigger, gesture,
  state, feedback, and display semantics required by those mappings.
- The smallest reusable runtime-realization boundary needed to bind physical
  Gills slots to an exact compute-target/backend/runtime closure while keeping
  device profile, instrument, graph, compute target, and backend independent.
- Shared headless validation, inspection, planning, and build execution through
  the accepted operation/compiler boundaries, with deterministic host vectors
  and ARM compile/link evidence where the exact handler supports the closure.
- A successor exact record set, focused positive and negative fixtures,
  deterministic validators, documentation, and a completion report.

## Out of scope

- Starting semantic or runtime implementation before Tasks 016 and 017 pass.
- Guessing panel identity, pin assignments, electrical ranges, ADC resolution,
  gesture recognition, display timing, firmware ABI, or mapping behavior.
- Rewriting accepted Task 005 records, Task 017 graphs/instruments, component
  contracts, or frozen inventory and catalog evidence.
- Making Gills synonymous with Ksoloti Core, embedding graph behavior in the
  device profile, mapping a device slot directly to a graph facet, or hiding a
  client/backend-specific mapping path.
- New DSP semantics or catalog expansion, sampling/assets, additional compute
  targets or devices, UI, AI/MCP, firmware replacement, or a new transport.
- Connected-device execution, panel operation, real-time/resource measurement,
  listening, upload, flash, SD-card writes, or hardware access without separate
  explicit authorization and procedures.
- Staging, committing, tagging, or pushing without separate approval.

## Inputs and deliverables

Inputs are ADR 0010; the accepted Tasks 005-015 records and ownership rules;
the completed Task 016 direct frontend and Task 017 curated-core/reference-
instrument closure; and an authenticated Gills evidence packet.

The completed planning deliverables are this executable contract, a read-only
contract validator, and current-routing documentation. The remaining
implementation deliverables are the evidence packet, any additive schema
revision required by reviewed facts, device/instrument/runtime records, exact
mappings and coverage report, record set, compiler/operation integration,
fixtures, tests, validators, evidence, and completion report described above.

## Acceptance tests

1. Tasks 016 and 017 are complete before any Task 018 semantic record,
   runtime realization, mapping, build record, or evidence claim is created.
2. The evidence packet pins one exact Gills hardware/panel revision and proves
   census coverage without treating a repository name or remembered layout as
   authority.
3. Earlier records remain byte-identical; all semantic changes are immutable
   successors with exact ID, revision, and content-hash references.
4. Every physical slot and public instrument facet has one deterministic
   mapped, intentionally-unused, or unresolved coverage result, and every
   asserted fact traces to accepted evidence.
5. Device mappings terminate at instrument facets and graph mappings start at
   instrument facets; direct device-to-graph shortcuts fail closed.
6. Parameters, actions, displays, state, controls, gestures, feedback, and I/O
   remain distinct, with explicit range, transform, direction, update, pickup,
   smoothing, and ownership rules where applicable.
7. Any runtime realization preserves independent device, target, runtime, and
   backend identity and resolves only through exact references; ambient source
   or filesystem discovery fails closed.
8. The two exact Task 017 reference instruments validate, plan, and either
   build through one exact supported handler or return stable unsupported
   diagnostics without fallback.
9. Existing Task 011C and Tasks 013-017 accepted bytes and test results remain
   unchanged, including all direct-frontend semantic vectors.
10. Structural, compiler, ARM, connected-device, real-time, and audible
    evidence are reported separately. Levels 6-8 remain `not-run` unless
    separately authorized and actually performed.
11. Two fresh roots and fresh processes produce byte-identical canonical
    records, coverage reports, operation results, plans, diagnostics, and all
    generated artifacts within the performed evidence boundary.
12. Full validators, focused negative fixtures, schema checks, path/link
    checks, and `git diff --check` pass.

## Decisions Task 018 may make

- The exact evidence-packet and coverage-report shape, after evidence sources
  and authority are reviewed.
- Additive schema revisions, successor IDs, mapping IDs, controlled values,
  diagnostics, and operation-version additions needed for the bounded Gills
  closure.
- The smallest runtime-realization record shape and lowering representation
  that preserve the accepted layer boundaries.
- Exact mapping assignments, transforms, pickup/smoothing responsibility, and
  feedback/display policies supported by the accepted Task 017 instruments and
  authenticated Gills evidence.

## Decisions Task 018 must not make

- Task 016's legacy-equivalent versus Schuss-native compatibility choice or
  Task 017's family/reference-instrument selection.
- Unsupported physical, electrical, timing, gesture, display, firmware, or
  runtime facts; unresolved evidence never becomes a default.
- New musical DSP behavior hidden inside a mapping or runtime adapter.
- Device/target/backend identity collapse, direct device-to-graph mapping, or
  a Gills-specific private control plane.
- Compatibility, connected-device, real-time, audible, safety, or release
  truth beyond the exact evidence actually produced.
- Sampling/asset semantics, another device or target, UI design, firmware
  replacement, hardware action, commit, or push.

## Readiness state

The former dependency stop condition is resolved. Task 016 accepted the
legacy-equivalent route and completed, then Task 017 completed its bounded
curated core and two reference instruments. Task 018 may now start at the
authenticated Gills evidence-packet gate.

No Task 018 implementation has occurred yet: no complete Gills census,
additive schema, semantic record, runtime code, mapping, build record, or
evidence level is claimed by this reconciliation.
