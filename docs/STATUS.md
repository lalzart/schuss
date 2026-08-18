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

Task 030 is accepted complete for exact prospective successor record set
`schuss-record-set-000023@1`, parented by `schuss-record-set-000022@1`. It
catalogues the complete exact Task 027 source-attributed Mutable cohort: the
six prior mappings are retained and the remaining fifty candidates become
`schuss-implementation-000112@1` through `000161@1`. Forty-seven new
function-first families bring the catalog to 107 families and 133
implementations. The sixteen extended-library entries without exact Mutable
attribution remain inventory-only.

Catalog corpus/projection v5 retains provenance per implementation. Shared
read-only operation `catalog.implementations.search` and CLI v3 command
`schuss catalog objects` expose individual objects from that same projection;
catalog commands now default to the Task 030 context. All fifty additions are
`catalogued-only`, compatibility `not-evaluated`, and unresolved. No component
contract, binding, compiler eligibility, build, project/machine mutation,
device, real-time/resource, audible, Git, or publication claim was added.
Structural/catalog provenance levels 1-2 pass and levels 3-8 remain `not-run`.
The dedicated Task 030 validator passes. The required one-shot repository
aggregate ran 394 tests in 1,199.802 seconds and retained three pre-existing
historical failures: two assertions over the already documented four
equal-length Task 023 catalog input-closure digest differences, and one Task
027 retained validation-summary projection-hash drift. No Task 030 test
failed; no historical golden or local source configuration was changed.

Task 030 does not activate compiler promotion, Machine Builder, UI
implementation, hardware work, or publication. No numbered implementation
task is automatically active after Task 030 completion.

The unnumbered desktop patcher implementation is locally complete for exact
prospective successor record set `schuss-record-set-000024@1`, parented by
Task 030. `apps/schuss_desktop/` is the sole maintained product UI: one Tauri
shell now exposes Patches and Objects, an exact React Flow graph projection,
contract-driven node inspection, proposal validation, project-backed Save,
and immutable history/revert through the shared operation layer. Additive v11
adds `component.inspect` and `set-graph-display-name`; application-capability
v4 describes twenty-one shared operations. The closed desktop adapter permits
only fourteen catalog, graph, and project operations and grants the renderer
only Tauri `core:default`.

ADR 0014 established that UI implementation remains separately gated. This
unnumbered lane began only after explicit user authorization. The earlier
object drawer and transparent graph canvas names remain historical planning
language; Task 012B remains retired and is not the authority for this work.

The live browser acceptance created and reopened a scratch Task 026 profile,
rendered seven nodes/seven connections, staged one exact contract-backed node,
and rejected one catalogued-only Mutable-derived object without changing the
graph. The scratch workspace was moved to Trash. Frontend, Rust, bridge,
structure, proposal, persistence, and reload regressions pass. Build execution,
compiler expansion, device sessions, USB upload, hardware, real-time/resource,
audible behavior, packaging, Git publication, and user acceptance remain
separate and `not-run`.

The final aggregate for this UI slice passed inventory 14/14 and catalog 6/6.
Contracts ran 397 tests in 1,428.008 seconds and retained only the three
pre-existing Task 011A/Task 023 golden and Task 027 projection-hash failures
already bounded by Task 030 and VH-001; each reproduces from untouched HEAD.
All desktop patcher, governance, project-authoring, and Task 030 tests pass.

The active unnumbered desktop authoring-performance slice is implemented
locally under its explicit 2026-08-18 authorization. The persistent process
now reuses the exact already validated record-set base only when both its
manifest path and full record-set reference match. A service-scoped eight-entry
LRU reuses only derived semantic augmentation keyed by that exact base and the
canonical project-owned records. Every project load still rereads and
validates governed workspace bytes, ancestry, schemas, hashes, assets,
symlinks, recovery state, and exact membership before semantic reuse.

On the same scratch workspace used for the baseline, core initialization
remains about 9.41 seconds, first project inspection falls from about 18.5
seconds to about 0.92 seconds, and warm repeated inspection falls from about
18.7 seconds to about 0.012 seconds. These host timings are performance
evidence only. Cache-enabled and cache-disabled transactions produce
canonical-byte-identical results and governed files; tampered owned bytes fail
before a semantic cache hit. The renderer now announces create/open/save
stages, prevents duplicate actions, confirms navigation away from unsaved
work. Failed or conflicted saves retain the draft for retry or explicit
accepted-project reload. No operation, schema, record-set,
allowlist, renderer capability, build, USB, or device boundary changed.

Focused cache/parity, frontend, bridge, native-shell, browser, shared-operation,
Task 012A atomicity/recovery, and Task 026 authoring checks pass. The final
performance-slice aggregate passes inventory 14/14 and catalog 6/6. Contracts
ran 402 tests in 960.044 seconds and retained exactly the three previously
audited Task 011A/Task 023 golden and Task 027 projection-hash failures; no
desktop, performance, project, governance, or current Task 030 test failed.

The explicitly authorized unnumbered desktop build/device workflow is
implemented locally for exact schema-only successor record set
`schuss-record-set-000025@1`, parented by the desktop patcher set. Additive v12
defines six client-neutral operations: start/inspect build, discover/inspect
device, and start/inspect upload. Application-capability v5 describes
twenty-seven shared operations; the closed desktop allowlist exposes twenty.

Build start snapshots one accepted project revision and exact project-owned
request, selects the one uniquely matching registered handler, and executes
the existing compiler/build boundary in a fresh core-owned temporary root.
Inspection exposes monotonic progress, stages, diagnostics, evidence levels,
and portable artifact kind/hash/size while host paths and bytes remain private.
Sessions are bounded to eight and disappear with the core process.

Ksoloti discovery is lazy and only follows explicit intent. The core-owned
libusb transport inspects exact USB, CPU serial, firmware version/CRC, and patch
entrypoint; compatibility is currently fail-closed to the retained Ksoloti
1.1.0.0 / `5021D42A` boundary. A separately confirmed upload request accepts
only the exact target executable from one successful build session, derives raw bytes
with the authenticated ARM objcopy, revalidates the endpoint CPU and complete
firmware identity, stops the current patch, writes fixed
volatile address `0x20011000`, verifies byte-for-byte read-back, and starts only
when requested. Flash, DFU, reset, SD writes, persistent install, arbitrary
memory access, background monitoring, and automatic upload remain absent.

All device protocol tests use deterministic fakes. No USB enumeration, real
board connection, upload, start, reset, flash, SD write, or other hardware
action was performed for this implementation. Session outcomes are runtime
observations only and create no governed evidence record or automatic level-6,
real-time/resource, or audible claim.

A live browser smoke created one disposable seven-node project, rendered the
build/device drawer without an error overlay or page-console error, and
completed one local ARM build reported as a 69-KB target executable. The
scratch workspace and screenshots were moved to Trash. Renderer tests pass
12/12, the production bundle succeeds, Rust bridge tests pass 3/3, and the
focused build/device module passes 11/11. The final aggregate passed inventory
14/14 and catalog 6/6. Contracts ran 411 tests in 974.684 seconds and retained
only the three previously audited Task 011A/Task 023 golden and Task 027
freshness failures; no desktop build/device test failed.

This desktop uses Task 026 project operations rather than reviving Task 012B's
design.

The explicitly authorized unnumbered AI lane is implemented locally through
exact schema-only successor record set `schuss-record-set-000026@1`. Additive
request/result v13 supplies sonic planning, process-local object drafts,
deterministic host evaluation, exact preview/accept, and project-object
inspection. Application-capability v6 describes thirty-five shared operations.
Project manifest v1 additively indexes project-owned object definitions while
mixed project-v0/v1 history remains readable.

Sonic planning returns exact existing-object, transparent-compound, and native
kernel lanes in parallel. Validity is a hard gate; no cost objective exists,
and catalog matches carry no fabricated sonic-quality score. Transparent
compounds preserve exact internal graphs and public mappings. Native objects
use a closed 128-instruction declarative kernel, deterministic bounded host
audition, and a non-governed content-addressed WAV cache. Their bindings remain
target-ineligible; host metrics do not imply listening, quality, ARM, device,
or real-time/resource evidence.

`bin/schuss-mcp` defaults to seven read-only discovery/planning tools over
stable MCP `2026-07-28` plus the exact `2025-11-25` compatibility era. Supplying
one explicit absolute `--project` workspace adds seven project-scoped
draft/evaluate/preview/accept/object tools with schemas derived from v13 and
truthful effect annotations. The adapter still exposes no generic operation,
arbitrary code, arbitrary filesystem/process/network, build, device, USB,
upload, reset, flash, SD, persistent-install, model-provider, sampling, task,
or remote HTTP authority.

The focused sonic-authoring run passes 5/5 and the MCP run passes 10/10. They
cover both object forms, the closed function taxonomy, schema-valid but
semantically invalid kernel reload, deterministic and input-sensitive WAV
hashes, no governed write before acceptance, foreign/stale/fingerprint/
expiry/replay rejection, atomic acceptance, fresh-service reload,
project-scoped MCP tools, and interrupted-publication recovery to the exact
prior project. The neighboring project/compiler/desktop regression run passes
42/42; governance passes 5/5, generated-record freshness passes, Python
compilation passes, and `git diff --check` is clean.

The final aggregate passes inventory 14/14 and catalog 6/6. Contracts ran 428
tests in 1,043.013 seconds and retained exactly the three previously audited
failures: the Task 011A historical/Task 023 successor catalog golden, the Task
023 CLI-v2 successor/historical golden, and Task 027 generated-output
freshness. No AI authoring, project-v1, native-kernel, MCP, recovery,
governance, desktop, or current Task 030 test failed. No historical golden was
rebaselined. The AI operations themselves invoked no package, model provider,
network listener, compiler/build, USB, or hardware authority.

A subsequent local Codex integration smoke exposed one fail-closed seam: the
desktop still created projects against `schuss-record-set-000025@1`, which does
not contain the v13 AI-authoring contract required by project-mode MCP. The
desktop creation context now selects the additive exact successor
`schuss-record-set-000026@1` without adding v13 mutation operations to its
closed allowlist. One existing revision-3 project pinned to `000025` still loaded
successfully, proving that no historical base migration is required or
performed. A fresh desktop-equivalent project pinned to `000026` initialized
the MCP `2025-11-25` compatibility flow, advertised all fourteen project-mode
tools, and completed `project.objects.list` successfully. Renderer tests pass
12/12, focused bridge/structure checks pass 5/5, and the adjacent desktop,
project, session, MCP, and sonic-authoring set passes 33/33. This integration
test performed no AI acceptance, compiler/build, USB, upload, or hardware
action. The post-repair aggregate passes inventory 14/14 and catalog 6/6;
contracts ran 428 tests in 1,045.075 seconds and retained exactly the same
three Task 011A/Task 023 golden and Task 027 freshness failures, with no new
desktop, project, MCP, or AI failure.

The explicitly authorized unnumbered desktop project-object handoff is active
locally. The closed desktop adapter now adds only the read-only v13
`project.objects.list` and `project.object.inspect` operations. The patch drawer
presents accepted project-local definitions separately from the permanent
catalog, resolves their exact component contracts, and reuses the ordinary
unsaved `add-node` graph edit. The editor checks the accepted project reference
through `project.inspect`: a clean external successor reloads and selects one
identifiable inserted node, while a dirty editor reports the successor revision
and never discards its draft without confirmation. The exact prior
`Throat Ripper` workspace resolves one local object through this desktop path;
its host evaluation remains distinct from target lowering `not-run`. Focused
renderer/request tests pass 11/11, the production frontend build succeeds,
Python bridge/structure tests pass 5/5, and Rust bridge tests pass 3/3. No AI
draft/evaluate/preview/accept, catalog promotion, compiler, build execution,
USB, upload, or hardware action is added by this slice.

The explicitly authorized unnumbered desktop workspace-shell successor is
active locally for exact schema-only record set `schuss-record-set-000027@1`,
parented by `000026`. Additive v14 exposes only
`workspace.projects.list` and `workspace.project.create`; application
capability v7 describes thirty-seven shared operations. The core validates a
bounded set of direct project children, rejects symlinks, escaping paths,
duplicate project IDs, and malformed projects, and owns collision-safe stable
ID/path allocation plus atomic template-backed creation. The renderer stores
only a versioned projects-root, last-workspace, and drawer preference.

The desktop now always mounts the patcher canvas. Separate Patches and Objects
application routes are removed; both are compact left-drawer tabs, the drawer
is bounded/resizable and remembered, and the existing node inspector remains
contextual on the right. Objects default to the existing contracted readiness
projection, All catalog retains the complete 133-item implementation view, and
form/readiness/provenance/evidence detail expands in the drawer. One Add action
performs exact contract resolution and then emits only the existing unsaved
`add-node` edit. New Patch asks only for a name, reopens the last valid project,
and creates one valid Untitled starter through v14 when a configured root is
empty.

The native shell now spawns its persistent Python core during application
setup and renders truthful core/project/graph stages over the already mounted
canvas. Full cold semantic validation is unchanged and remains a separately
measured roughly nine-second boundary; no weakened or stale semantic cache was
introduced. Focused frontend tests pass 21/21, the production bundle succeeds,
workspace-service tests pass 6/6, structure checks pass 4/4 with 24 closed
runtime operations and zero semantic renderer records, the Python bridge smoke
passes 1/1, and Rust adapter tests pass 3/3. The adjacent project, session,
application, MCP, and sonic-authoring regression set passes 60/60. A live
browser smoke verified first-run setup, automatic Untitled creation, remembered
reopen, 21-item Patcher and 133-item All catalog projections, one successful
ordinary add/discard flow, and the closed catalog-only add path over a
disposable workspace now moved to Trash. The reviewed diff and generated
record set are clean. The final aggregate passes inventory 14/14 and catalog
6/6. Contracts ran 434 tests in 1,090.532 seconds and retained exactly the
three previously audited failures: the Task 011A historical/Task 023 successor
catalog golden, the Task 023 CLI-v2 successor/historical golden, and Task 027
generated-output freshness assertion. No desktop workspace-shell, project,
bridge, governance, renderer, or current-record test failed. No build
execution, USB, upload, hardware, package, Git publication, or audible action
was performed by this successor.

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
| Complete Mutable-derived catalog cohort | All 56 exactly attributed Task 027 entries catalogued as individual implementations across 107 function-first families, with shared implementation search and CLI v3 object browsing | Levels 1-2 structural/provenance only; all 50 additions remain catalogued-only and levels 3-8 not-run |
| Twenty-item direct palette | Five retained Task 025 promotions plus fifteen exact independent Task 028 selections and normalized operation-IR lowerings; seven Task 026 support bindings remain separate | Levels 1-3 passed; source generation, ARM, device, realtime/resource, and audible levels 4-8 not-run |
| Gills machine layer | Exact Palimpsest and Tide Pit source reviews, source-evidenced inspection presentations, editable v0.6 panel plus semantic map, fail-closed completed-machine schema, shared read-only inspection operation, and isolated Viewer | Level 1 structural/source-identity/host inspection proof; completed machines zero; levels 2-8 not-run |
| Desktop patcher | One consolidated Tauri shell, exact 133-implementation browsing, seven-node template creation, graph projection/proposal, atomic project save, and history/revert through shared operations | Host UI and project-persistence proof only; build, device, real-time/resource, audible, packaging, and publication not-run |
| Desktop build/device workflow | Core-owned process-local build jobs, structured progress/diagnostics, explicit Ksoloti identity/compatibility sessions, and a fake-tested read-back-verified volatile-RAM upload path | Host implementation, local ARM build, and fake-transport proof; real connected-device action, governed level 6, real-time/resource, audible, packaging, and publication not-run |
| AI/MCP authoring | Dual-era local stdio adapter with seven default read-only tools plus seven explicitly project-scoped sonic planning/object/patch tools; bounded transparent compounds/native kernels and atomic project acceptance | Host structural, deterministic host-audition, protocol, and project-persistence proof only; target lowering, model behavior, build, device, real-time/resource, audible, remote security, packaging, and publication not-run |

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
- The desktop now has process-local build and Ksoloti device/upload session
  contracts, but this implementation performed no real discovery or upload and
  created no governed connected-device evidence. Firmware/SD mutation,
  persistent install, background monitoring, real-time/resource, audible, and
  release paths remain absent. Cold startup still validates the full selected
  record set and remains about nine seconds on the measured development machine.
- The MCP adapter is local and has not been tested through every third-party
  host. Explicit project mode can author bounded project-local objects and
  patches, but provides no model-provider, desktop chat, target lowering,
  build, device, remote HTTP/OAuth, or autonomous background-agent behavior.
  Those remain separate product and security decisions.
- The historical Task 011A CLI golden remains byte-identical. Task 023 records
  its successor golden separately and tests the inherited four equal-length
  input-closure digest changes without treating them as semantic catalog drift.
- Validation-hygiene task VH-001 retains five configured historical
  golden/hash gates as environment-dependent mismatches. It changes no source
  configuration or golden and makes no product or evidence promotion claim.
- The 20 Task 024 families and their 29 exact current variants have no Task 024-created component contract,
  binding, compiler eligibility, or execution evidence. Their unresolved state
  is intentional.
- All fifty former Task 027 tagged candidates are now catalogued, but none has
  a Task 030-created contract, binding, eligibility, compiler/build, device,
  real-time, or audible claim. Sixteen other extended objects remain
  inventory-only and untagged because exact Mutable derivation is absent.
- Rings-derived reverb remains ineligible until its exact allocation and
  ownership contract is independently resolved; Tasks 026-028 do not
  redesign, repair, or consume it.
- One hundred thirteen accepted catalog implementations remain outside the
  bounded twenty-item palette. Task 028's exact parent-era gap ledger accounts
  for its 83-implementation catalog; Task 030 adds fifty catalogued-only
  objects without changing that palette. Absence is not a quality judgment.

## Current planning boundary

Task 022 is stopped at the failed diagnostic result. Approval gate 2 is closed;
the contract does not authorize a corrected diagnostic, another upload, the
Task 021 product-binary replacement, firmware flash, SD-card write, persistent
installation, or reset. Any diagnostic successor or repeated hardware
procedure requires a new bounded decision and explicit approval.

Tasks 023-030 are accepted complete. Task 025's retained fail-closed result is
bounded by `docs/tasks/025-direct-compiler-core-library-tranche.md` and
`contracts/task025/reverb-allocation-boundary.md`; it does not authorize or
claim lowering, ARM, device, real-time, audible, Git, or publication action.
Task 026 consumes only the separately accepted reverb-free seven-node profile
and is bounded by its completed contract and evidence. Task 027 is bounded by
its completed source-review and provenance contract and does not activate
Task 028. Task 028 is bounded by its completed twenty-item direct-palette
contract; its prior transparent-compound outcome is deferred. Task 029 is
bounded to source-evidenced machine inspection and Task 030 to catalog
provenance plus read-only object discovery. No numbered
implementation lane is currently planned. The unnumbered desktop patcher is
implemented locally with its process-local build/device and project-object
handoff successors and awaits user acceptance/publication. The unnumbered AI/MCP lane is implemented locally
through explicit project-scoped object and patch authoring. Real
connected-device execution, firmware/SD
mutation, packaging, real-time/resource, and audible work remain separately
gated. The original numbered application sessions/jobs/diagnostics outcome
remains retired without a replacement number; its bounded product need is now
served by the unnumbered v12 workflow. Tasks 019 and 020 remain deferred.
