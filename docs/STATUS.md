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
execution, project writes, and hardware access were `not-run`.

Task 024 is accepted complete for exact record set
`schuss-record-set-000016@1`. Its primary current-Ksoloti corpus records the
four configured source libraries while indexing the pinned first-party
`axoloti-factory` and `ksoloti-objects` cohorts: 668 `.axo` files, 835 normal
definitions, 666 canonical base references, and 19 separately marked `.axs`
compounds. Contrib libraries remain deferred provenance cohorts, and the
thirteen function-first Schuss categories remain independent of library paths.

The retained generated coverage packet gives all 3,602
frozen resolved observations one factual disposition: 69 reviewed-family,
2,929 implementation-variant, 414 overload-group, zero duplicate, two explicit
editor-only/non-headless, 187 unresolved, and one queued-human-review. The
counts are deterministic lineage accounting, not readiness, quality, or a
product backlog. The catalog projection retains all 40 prior families and adds
exactly 20 reviewed source-backed families for a total of 60. Their review
treatment is eleven retain, seven revise, and two reconsider; complete current
overload cohorts produce 29 Task 024 implementation records. Every new family
remains catalogued-only and unresolved, with default, advanced, or review-only
drawer visibility kept separate from readiness.

Task 024 also freezes `schuss-core-selection-000002@1`, containing exactly the
eight distinct component contracts already used by
`schuss-graph-000004@1`. This is Task 025 input authority, not compiler proof.
Task 024 reproduced levels 1-2 only; compiler/build and evidence levels 3-8
were `not-run`.

Task 025 is accepted complete for exact record set
`schuss-record-set-000017@1`. Five source-backed operations—saw, PWM,
exponential smoothing, audio soft clipping, and interpolated VCA—now have
distinct native semantic identities and passed level-2 promotion claims.
Together with the retained Task 016 crossfade and output bindings, the ordinary
compiler plan selects seven exact nodes.

The selected reverb wrapper allocates 32,768 bytes while its exact
`uint16_t` engine clears 65,536 bytes. Task 025 records that contradiction as
failed level-2 evidence and an explicitly unsupported eligibility. It creates
no reverb operation, native binding, handler, generated C++, or ARM evidence.
The complete plan rejects only reverb at implementation resolution, so level 1
passes, complete-graph level 2 fails, and levels 3-8 remain `not-run`. Two
fresh roots reproduced identical record-set, semantic-golden, and unsupported
plan bytes.

Task 026 is accepted complete for exact schema successor record set
`schuss-record-set-000019@1`. Its child 026A first established an
identity-independent seven-node, reverb-free semantic profile and exact direct
handler at local ARM compile/link level 5. Child 026B adds closed v8 operations
for project-owned profile creation/versioning, immutable history, explicit
revert/redo, and atomic multi-record recovery. CLI routes now expose
`project create`, `project edit`, `project history`, `project revert`, and
project-aware `build plan`/`build execute` over those same services.
The Task 026 application-capability successor describes eighteen operations;
the historical fourteen-operation Task 023 description remains byte-exact in
its own record set.

The deterministic acceptance flow begins with no project metadata, creates a
valid template head, atomically forks new project-owned graph, instrument, and
request identities, applies one complete edit batch, versions the whole
closure, performs undo and redo without rewriting history, closes/reopens,
plans the exact authored request, and produces an ARM ELF. Two fresh workspaces
reproduced byte-identical history, plan, generated source, and ELF. Exact
completion evidence is in `evidence/task026-completion-v1/`; levels 1-5 pass
and levels 6-8 remain `not-run`. Reverb is still explicitly unsupported and no
Java, `.axp`, device, real-time, audible, Git, or publication action occurred.

ADR 0015 retargets the previously unstarted Task 027 assignment. Task 027 is
accepted complete for exact record set `schuss-record-set-000020@1`. It
reviews the exact nineteen-object `ai/sdk/ksoloti-extended` tree from pinned
`patcher` commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c` together with
fifty-three exact factory candidates whose descriptions attribute Mutable
Instruments code or DSP. The additive `mutable-instruments-derived` tag does
not change any of the sixty reviewed families or thirteen functional
categories.

The review retains seventy-two exact source entries. Fifty-six are tagged
candidates: all fifty-three factory entries plus the extended Rings resonator,
Grids-derived topographic sequencer, and Plaits macro voice. Six catalogued
implementations across five ordinary families carry the tag. The only new
implementation is `schuss-implementation-000096@1`, the extended Rings
resonator under existing `schuss-family-000010@1`; it remains
`catalogued-only` and `unresolved`. The other sixteen extended objects remain
inventory-only because the exact library license does not establish Mutable
derivation for them.

The two factory Warps objects remain candidates: `fx/wrps/vocoder` is
uncurated and `fx/wrps/wrps` retains its exact source statement that it does
not currently link. The extended macro voice retains source metadata
`h7-recommended` and `build-failed`; neither is Schuss support evidence. Task
027 reproduced catalog structural/provenance levels 1-2 only. Compiler, ARM,
Java, `.axp`, project, device, real-time, audible, Git, and publication work
were `not-run`.

Task 028 is accepted complete for exact record set
`schuss-record-set-000021@1`. It adds exactly fifteen independently selectable
native bindings, for a counted total of twenty when combined with the five
Task 025 promotions. The additions are Attack-Decay Envelope, Clocked Logic
Toggle, Pseudo-Euclidean Gate Sequencer, Struck Drum Voice, Struck Bell Voice,
Uniform Noise, Standard ADSR, Standard Sine LFO, Decay Envelope, Control
Low-pass Filter, Two-pole Resonant Audio Low-pass, Saturating Gain, Two-input
Audio Mixer, Audio-rate Addition, and Triggered Value Latch.

Each addition resolves exactly once for target 000001 revision 2 and existing
backend 000002 revision 4, then lowers to normalized operation IR. Task 028
passes levels 1-3 only. Source artifact generation, ARM compile/link, Java,
`.axp`, project, device, realtime/resource, audible, Git, and publication work
were `not-run`. The seven Task 026 profile bindings remain useful supporting
primitives but are not double-counted. The full 83-implementation accepted
catalog is accounted for: twenty source implementations back counted
promotions and sixty-three remain outside this bounded palette.

Drum and Bell retain Task 027 Mutable-derived provenance without changing
their sound-source families or raising their evidence. The Rings reverb
failure and absent native allocation 000094 remain unchanged; physical
resonator 000096 remains catalogued-only. Transparent compounds remain
deferred.

Task 029 is implemented with local acceptance complete in its isolated
worktree for exact prospective successor record set
`schuss-record-set-000022@1`, parented by `schuss-record-set-000021@1`. It adds
the client-neutral distinction between catalog objects and complete machines:
`machine-source-review-v0`, `panel-layout-v0`, `machine-presentation-v0`, the
smallest exact-reference `machine-v0`, and read-only `machine.inspect` request
and result v9. The application-capability v2 surface contains nineteen
operations. The accepted twenty-item palette and every parent record remain
unchanged.

The exact reference machines are Palimpsest at
`projects/palimpsest-gills/` and Tide Pit at `projects/tide-pit-gills/`. Task
029 retains one portable, hash-bound source review and one source-evidenced
inspection presentation for each. Both presentations are explicitly
inspection-only and contain no authoritative graph-node claims. No completed
`machine-v0` record is accepted because neither source project yet has the
exact Schuss graph, instrument, and required-dependency closure; the validator
rejects promotion across that boundary.

The shared v0.6 Gills panel asset is a self-contained 158 x 100 mm editable SVG
derived from pinned CC BY 4.0 CAD/editable sources, paired with a separate
42-region semantic map. The supplied photograph was used only as a
hash-identified, non-retained appearance reference. The isolated
`apps/schuss_machine_viewer/` client renders identity, block diagram, panel
mappings, and dependency/evidence sections solely from canonical
`machine.inspect` results. It does not integrate with or depend on the
separately owned desktop foundation.

Focused schema/record/operation tests, four fresh CLI processes across two
CWDs, explicit pinned-source blob verification, Viewer tests, and local
Chrome-headless rendering pass. Structural level 1 passes; graph/instrument,
compiler, artifact, ARM, device, real-time/resource, and audible levels 2-8
remain `not-run`. Tide Pit's 251,408 source-declared SDRAM bytes are not a
measurement. Its Clouds diffusion tail is preserved; unrelated Rings reverb
remains a non-required unsupported non-dependency. No catalog promotion, DSP,
Task 029 compiler/build evidence, runtime bridge, device, hardware, staging,
commit, or push action occurred. One adjacent `validate_task018.py` invocation
unexpectedly ran its historical two-root ARM reproduction in disposable
directories before failing on inherited local-evidence drift; it retained no
artifact, performed no device action, and is not Task 029 evidence. Further
build-bearing aggregate checks remain not run by scope.

Task 029 does not activate its later Machine Builder or the Palimpsest/Tide Pit
graph-import prerequisites. The authorized desktop UI-architecture lane remains
separately owned. Task 029 was activated by explicit user authorization.
No numbered implementation task is automatically active after Task 028 completion.

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
| Catalog structure and lineage | Current pinned first-party Ksoloti corpus with 666 normal-definition cohorts plus 19 compounds, all 3,602 frozen observations retained as lineage/gap evidence, 60-family reviewed projection, and exact eight-contract Task 025 packet | Level 2 structural/provenance only; new families remain catalogued-only |
| Effects semantic tranche | Five exact Task 025 native-operation promotions plus two reused routing operations; reverb remains explicitly unsupported | Five component claims pass level 2; complete graph fails level 2; levels 3-8 not-run |
| Complete authoring workflow | Project-owned graph/instrument/request allocation and versioning, atomic multi-record persistence, immutable history/revert, project-aware CLI planning/execution, and two-root authored ELF reproduction | Levels 1-5 passed for the exact reverb-free profile; levels 6-8 not-run |
| Mutable-related catalog provenance | Exact 19-object extended-source review plus 53 attributed factory candidates, additive per-candidate/per-implementation provenance, 60-family preservation, and one catalogued-only Rings resonator implementation | Levels 1-2 structural/provenance only; compiler/build and levels 3-8 not-run |
| Twenty-item direct palette | Five retained Task 025 promotions plus fifteen exact independent Task 028 selections and normalized operation-IR lowerings; seven Task 026 support bindings remain separate | Levels 1-3 passed; source generation, ARM, device, realtime/resource, and audible levels 4-8 not-run |
| Gills machine layer | Exact Palimpsest and Tide Pit source reviews, source-evidenced inspection presentations, editable v0.6 panel plus semantic map, fail-closed completed-machine schema, shared read-only inspection operation, and isolated Viewer | Level 1 structural/source-identity/host inspection proof; completed machines zero; levels 2-8 not-run |

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
- The 20 Task 024 families and their 29 exact current variants have no Task 024-created component contract,
  binding, compiler eligibility, or execution evidence. Their unresolved state
  is intentional.
- Fifty Task 027 tagged candidates remain outside the catalog: forty-eight
  attributed factory variants plus the extended topographic sequencer and
  macro voice. Sixteen other extended objects remain inventory-only and are
  not tagged without exact derivation evidence. Candidate presence is not
  compiler, device, real-time, or audible support.
- Rings-derived reverb remains ineligible until its exact allocation and
  ownership contract is independently resolved; Tasks 026-028 do not
  redesign, repair, or consume it.
- Sixty-three accepted catalog implementations remain outside the bounded
  twenty-item palette. Task 028's exact gap ledger preserves their prior
  readiness and accounts separately for all seventy-two Task 027 source-review
  entries; absence from this first palette is not a quality judgment.

## Current planning boundary

Task 022 is stopped at the failed diagnostic result. Approval gate 2 is closed;
the contract does not authorize a corrected diagnostic, another upload, the
Task 021 product-binary replacement, firmware flash, SD-card write, persistent
installation, or reset. Any diagnostic successor or repeated hardware
procedure requires a new bounded decision and explicit approval.

Tasks 023-028 are accepted complete. Task 025's retained fail-closed result is
bounded by `docs/tasks/025-direct-compiler-core-library-tranche.md` and
`contracts/task025/reverb-allocation-boundary.md`; it does not authorize or
claim lowering, ARM, device, real-time, audible, Git, or publication action.
Task 026 consumes only the separately accepted reverb-free seven-node profile
and is bounded by its completed contract and evidence. Task 027 is bounded by
its completed source-review and provenance contract and does not activate
Task 028. Task 028 is bounded by its completed twenty-item direct-palette
contract; its prior transparent-compound outcome is deferred. No numbered
implementation lane is currently planned. The already authorized unnumbered
UI-architecture milestone remains eligible but has not started. The
original application sessions/jobs/diagnostics outcome is deferred without a
replacement task number. Tasks 019 and 020 remain deferred.
