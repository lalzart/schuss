# Development status

This document is the single authority for Schuss's current development state.
Stable product intent belongs in `PROJECT_CONTEXT.md`, architecture belongs in
the architecture and contract documents, accepted decisions belong in ADRs,
and completed work belongs in `HISTORY.md` and retained evidence.

## Current direction

Task 018 is complete for exact record set `schuss-record-set-000012@1`.
Task 021 is complete for exact record set `schuss-record-set-000013@1`. It
preserves Task 018's exact record set `schuss-record-set-000012@1`, versions
the mapped OLED runtime with a dedicated DMA-visible command buffer, retains a
deterministic local level-5 ARM build, and records the separately authorized
volatile-RAM connected-device observation at level 6. No product task is
automatically active after this completion.

Task 022 Phase A is complete for exact artifact successor record set
`schuss-record-set-000014@1`. It adds no instrument, mapping, runtime
realization, product build request, or handler. A separate non-product panel
diagnostic was generated and ARM-linked twice in fresh roots and processes,
with exact 75,504-byte ELF SHA-256
`2f003cde514dcb48ecb09ecc0d61f880bb1ecdec5761ddb8b737bc3c68571231`
and exact 5,552-byte volatile upload binary SHA-256
`7c843acb42b17c13d0c535834d12ab620d312b451fd4ee435733e4acf7321113`.
Exactly one approved diagnostic volatile-RAM upload was performed on the exact
Task 021 board at `0x20011000`. Identity, firmware, byte-for-byte RAM readback,
start acknowledgement, three responsiveness probes, flags zero, upright and
stable OLED startup, all six LED channels, all ten pot slot identities, smooth
non-frozen response, and approximate `0000` to `4095` travel were observed.
Stationary ADC variation of approximately 5 to 15 counts exceeded the fixed
four-count last-moved threshold, so inactive pots repeatedly stole the OLED
event focus and exact per-pot low/middle/high telemetry could not be retained.
The retained result is `POT_EVENT_FOCUS_UNSTABLE`; promotion stopped before a
complete sweep and level 6 was not earned. Approval gate 2 is closed. No Task
021 replacement upload, second upload, reset, flash, SD-card write, persistent
install, or other connected-device action occurred. The retained Task 022
result is published on `main` at commit `a5fa328`.

ADR 0014 accepts the application-spine sequence in
`docs/APPLICATION_SPINE_PLAN.md`. Task 023 was explicitly accepted and
completed on 2026-08-16. Exact schema-only successor record set
`schuss-record-set-000015@1` adds application-capability-description v0 and
operation request/result v7 without adding any semantic record. The shared
`application.describe` operation inventories fourteen accepted public
operations, their contexts, effects, gates, availability, and evidence
boundaries. CLI v2 exposes validation, application, catalog, project, graph,
Gills, build, completion, and canonical-operation routes over the same shared
services. The parent integrated Tasks 023A, 023B, and 023C in order.

The read-only Task 023 smoke passes in two copied fresh roots and fresh
processes with varied CWD, locale, timezone, hash seed, terminal width, and
harmless host noise. Repository snapshots remained unchanged; backend
execution, project writes, and hardware access were `not-run`. Tasks 024-028
remain ordered planned successors rather than ambient authorization.

Task 012B remains retired. The object drawer and transparent graph canvas are
an unnumbered future client milestone. UI architecture planning is now
explicitly authorized by ADR 0014, but UI implementation remains separately
gated and must consume the shared client-neutral operations.

Tasks 019 and 020 are deferred and not automatically activated by completion
of Task 018 or Task 021.

## Accepted implementation boundary

| Boundary | Accepted result | Highest evidence |
| --- | --- | --- |
| Catalog and semantic identity | Frozen inventory, reviewed catalog families, typed contracts, and exact record sets | Structural and provenance evidence |
| Project authoring | Portable projects, immutable graph/project successors, atomic workspace-head persistence, and shared CLI operations | Host persistence evidence |
| Compiler front half | Exact validation, resolution, compound elaboration, dependency/resource planning, and origin mapping | Level 2 |
| Shared execution | Exact handler registration, plan-once execution, fresh-root publication, and product build commands | Level 5 through the retained legacy handler |
| Direct frontend | The accepted eight-node Gills slice lowers without Java or `.axp` under legacy-equivalent semantics | Level 5 |
| Curated core | Twelve reviewed families and two headless reference instruments; missing direct semantics fail closed | Level 2 |
| Full Gills panel/runtime | Authenticated 63-slot census, total mappings/coverage, exact runtime closure, and one mapped direct build | Level 5 |
| Corrected Gills OLED/runtime | Versioned DMA-safe command transport plus one exact volatile-RAM board/OLED observation | Level 6 |
| Gills panel diagnostic | Separate omitted-instrument telemetry source, deterministic host vectors, exact ARM artifacts, and one retained failed connected observation | Level 5; connected attempt failed before level 6 |
| Application surface | Fourteen client-neutral capability descriptions, coherent CLI v2, exact schema-only record-set successor, and read-only cross-service smoke | Host structural/application proof only; no new compile, device, real-time, audible, safety, or release evidence |

The accepted Task 018 result proves deterministic local ARM compile/link for
one exact mapped graph/instrument/device/runtime closure. Its exact original
binary did not pass connected-device OLED initialization. Task 021 preserves
that result and adds a corrected exact closure.

## Completed Task 018 boundary

Task 018 established all of the following:

1. A complete physical-slot census with evidence or explicit unresolved facts.
2. Device-to-instrument, instrument-to-graph, and instrument-to-device mappings
   with deterministic total coverage.
3. An independent runtime realization for pickup, smoothing, transforms,
   gestures, actions, state, feedback, displays, and physical I/O.
4. `schuss-instrument-000002@2` reaches evidence level 5 through the exact
   mapped handler and runtime realization in two fresh roots and processes.
5. The two Task 017 successors retain stable unsupported diagnostics without
   fallback, and levels 6-8 remain `not-run`.

The executable reference reuses the accepted Task 016 eight-node graph and
legacy-equivalent semantic goldens. Panel mapping/runtime code is retained as
separate artifacts and adds no DSP operation.

## Completed Task 021 boundary

Task 021 established all of the following:

1. Task 018 generated records, handler selection, artifacts, and retained
   evidence remain byte-exact.
2. `schuss-build-request-000002@5`, `schuss-build-handler-000003@2`,
   `schuss-runtime-realization-000001@2`, and mechanical instrument/coverage
   successors form one exact corrected closure without fallback.
3. The corrected source uses a dedicated two-byte `.sram2` OLED command buffer
   and leaves the 129-byte page buffer independent.
4. Two fresh roots and processes reproduce generated C++ SHA-256
   `e69155998e91c7c3af6b6e0aaebbac965f4cf822b67382f25de5776453af2928`
   and target ELF SHA-256
   `4f9bd68f5f71fc9d5bf70bd88988e7e20ff980fb46a886beff52f60c968874de`.
5. The exact volatile-RAM candidate passed RAM readback, start acknowledgement,
   responsiveness probes, and upright four-word OLED observation on one exact
   board. This is separate level-6 evidence; the build handler itself still
   reports levels 6-8 as `not-run`.

## Current proof gaps

- The two Task 017 successors do not lower through the direct frontend: one is
  unsupported and one has unresolved compound internals.
- No complete physical-control sweep was performed. Task 022 retained the
  connected `POT_EVENT_FOCUS_UNSTABLE` result after the exact per-pot telemetry
  surface failed; buttons, encoder, final device checks, Task 021 mapping, and
  both proposed level-6 claims remain `not-run`.
- Real-time/resource and audible evidence levels 7-8 remain `not-run`.
- The authenticated Task 009 local content store is ignored and must be
  validated separately when present; a clean checkout cannot claim that local
  evidence merely from tracked manifests.
- No desktop application or UI client is implemented. UI architecture is
  eligible but has not started.
- The historical Task 011A CLI golden remains byte-identical. Task 023 records
  its successor golden separately and tests the inherited four equal-length
  input-closure digest changes without treating them as semantic catalog drift.

## Current planning boundary

Task 022 is stopped at the failed diagnostic result. Approval gate 2 is closed;
the contract does not authorize a corrected diagnostic, another upload, the
Task 021 product-binary replacement, firmware flash, SD-card write, persistent
installation, or reset. Any diagnostic successor or repeated hardware
procedure requires a new bounded decision and explicit approval.

Task 023 is accepted complete. Task 024 is the next numbered implementation
gate, but no Task 024 contract exists and no successor task is active. The
already authorized unnumbered UI-architecture milestone is now eligible as a
separate planning lane but has not started. Task 023 completion does not
authorize staging, commit, push, publication, project writes, build execution,
hardware action, or UI implementation. Tasks 019 and 020 remain deferred.
