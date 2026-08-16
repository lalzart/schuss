# Task 018: Full Gills implementation and parameter/control mapping

Status: completed on 2026-08-16 through deterministic local evidence level 5.
Tasks 016 and 017 remain exact dependencies, and ADR 0012 supplies the
executable mapped-instrument promotion gate.

## Goal and why it exists

Replace the deliberately minimal one-knob Gills contract with an authenticated,
complete panel model and prove the explicit runtime-facing chain from physical
Gills slots through instrument facets into exact graph facets. At least one
exact mapped reference must also build through the accepted direct path. This
task exists to make Gills a fully described and locally executable device and
performance surface without making the device profile, instrument, graph,
compute target, or backend share identity.

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

ADR 0011 owns that legacy-equivalent choice. ADR 0012 additionally requires one
exact mapped Gills reference to reach evidence level 5. The accepted Task 016
eight-node graph may satisfy the DSP side of that closure; stable unsupported
or invalid Task 017 plans do not satisfy the executable promotion gate.

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
- An exact mapped executable reference that reuses the accepted Task 016 graph,
  direct semantics, target, backend, and build boundary without inventing new
  DSP behavior.
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
- A successful level-5 build for at least one exact mapped Gills reference,
  including the runtime realization needed by its accepted mappings. A graph-
  only build that omits that runtime closure does not satisfy this requirement.
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
- New DSP semantics or catalog expansion merely to make a reference build;
  sampling/assets, additional compute targets or devices, UI, AI/MCP, firmware
  replacement, or a new transport.
- Connected-device execution, panel operation, real-time/resource measurement,
  listening, upload, flash, SD-card writes, or hardware access without separate
  explicit authorization and procedures.
- Staging, committing, tagging, or pushing without separate approval.

## Inputs and deliverables

Inputs are ADRs 0010-0012; the accepted Tasks 005-015 records and ownership
rules; the completed Task 016 direct frontend and Task 017 curated-core/
reference-instrument closure; and an authenticated Gills evidence packet.

The completed deliverables are this contract, its read-only validator, ADR
0012, the authenticated evidence packet, additive schemas,
device/instrument/runtime successors, exact mappings and total coverage, one
exact executable mapped reference, the successor record set,
compiler/operation integration, focused fixtures and tests, retained evidence,
and the completion report described above.

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
9. At least one exact mapped Gills reference, including its runtime-realization
   closure, builds through the accepted direct path and reaches evidence level
   5 in two fresh roots. A graph-only build or stable unsupported diagnostic
   does not satisfy this executable promotion gate.
10. Existing Task 011C and Tasks 013-017 accepted bytes and test results remain
   unchanged, including all direct-frontend semantic vectors.
11. Structural, compiler, ARM, connected-device, real-time, and audible
    evidence are reported separately. Levels 6-8 remain `not-run` unless
    separately authorized and actually performed.
12. Two fresh roots and fresh processes produce byte-identical canonical
    records, coverage reports, operation results, plans, diagnostics, and all
    generated artifacts within the performed evidence boundary.
13. Full validators, focused negative fixtures, schema checks, path/link
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
- The exact successor of the accepted Task 016 instrument/graph closure used
  to prove the mapped level-5 runtime path.

## Decisions Task 018 must not make

- Task 016's legacy-equivalent versus Schuss-native compatibility choice or
  Task 017's family/reference-instrument selection.
- Unsupported physical, electrical, timing, gesture, display, firmware, or
  runtime facts; unresolved evidence never becomes a default.
- New musical DSP behavior hidden inside a mapping or runtime adapter.
- New direct DSP semantics introduced solely to turn an unsupported Task 017
  reference into the required executable reference.
- Device/target/backend identity collapse, direct device-to-graph mapping, or
  a Gills-specific private control plane.
- Compatibility, connected-device, real-time, audible, safety, or release
  truth beyond the exact evidence actually produced.
- Sampling/asset semantics, another device or target, UI design, firmware
  replacement, hardware action, commit, or push.

## Readiness state

Task 018 is complete for exact record set `schuss-record-set-000012@1`. The
authenticated panel packet accounts for 63 slots, all three instrument
successors have total coverage and exact runtime closure, and the mapped Task
016 successor builds twice in fresh roots and fresh processes through local
ARM compile/link evidence level 5. The two Task 017 successors retain stable
unsupported diagnostics without fallback.

Levels 6-8 remain `not-run`. No connected-device, real-time/resource,
audible/listening, upload, flash, SD-card, stage, commit, or push action is
claimed. Task 019, Task 020, and the deferred UI are not activated by this
completion.
