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

Task 012B remains retired. The object drawer and transparent graph canvas are
an unnumbered future client milestone that requires explicit user
authorization.

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
- No complete physical-control sweep was performed; level 6 is limited to the
  exact board execution and OLED observation recorded by Task 021.
- Real-time/resource and audible evidence levels 7-8 remain `not-run`.
- The authenticated Task 009 local content store is ignored and must be
  validated separately when present; a clean checkout cannot claim that local
  evidence merely from tracked manifests.
- No desktop application or UI client is implemented.
- The Task 011A CLI output-golden test is already stale on clean `HEAD`: its
  retained golden expects input-closure hash `291b695c...`, while current
  Task 011A execution emits `7aff3534...`. Task 021 preserves that unrelated
  historical golden and does not claim to repair it.

## Next decision

Task 021 completion does not automatically start sampling, another target, or
UI work. The next decision must choose a separately bounded control-panel,
real-time/resource, or audible proof step, or explicitly authorize a different
product direction. Task 019, Task 020, and the future client milestone remain
deferred.
