# Development history

This is the concise index of completed Schuss work. Completed task contracts
are not live scheduling authority. Some remain in the working tree while they
are useful for review; Git retains every committed version whether or not a
contract is later archived.

```bash
git show COMMIT:docs/tasks/TASK_FILE.md
```

Retained schemas, records, record sets, and evidence remain authoritative for
their exact claims. A historical task or commit never upgrades an evidence
level.

## Completed milestones

| Work | Outcome | Completion commit | Retained authority |
| --- | --- | --- | --- |
| Tasks 001-003 | Raw and Java-resolved inventory, Phase 3 review, and Phase 4A semantic catalog foundation | `9487747`, `488ee03`, `03a2781` | `catalog/`, `docs/inventory/`, `docs/SEMANTIC_CATALOG.md` |
| Task 004 | Family/contract/binding ownership, compiler stages, and evidence separation | `a3ac76d` | ADRs 0005-0007, `SCHEMA_STRATEGY.md`, `COMPILER_STRATEGY.md` |
| Task 005 | Minimal Gills device and instrument contracts | `763c007` | `DEVICE_INSTRUMENT_CONTRACTS.md`, base schemas and records |
| Task 006 | Typed component, binding, graph, and exact instrument closure | `15f22d8` | `COMPONENT_GRAPH_CONTRACTS.md`, base schemas and records |
| Task 007 | Target, backend, build, artifact, resource, and evidence contracts | `5199420` | `TARGET_BACKEND_BUILD_CONTRACTS.md` |
| Task 008 | Shared validator core and client-neutral operation dispatcher | `e501b3a` | `OPERATION_CONTRACTS.md`, `packages/schuss_core/` |
| Task 009 prerequisites | Authenticated source, Java, ARM, and runtime closure | `8a936b1` | `contracts/prerequisite/`, `evidence/task-009-prerequisite-*` |
| Task 009 | Deterministic Blend legacy lowering and ARM compile/link | `c8c5f74`, `a77f6d7` | record set `schuss-record-set-000003@1`, `evidence/task-009-v1/` |
| Task 010 | Deterministic product CLI over shared operations | `c54f1b0` | `bin/schuss`, `packages/schuss_core/product_cli.py` |
| Task 011A | Browsable catalog projection and reviewed Gills-slice identities | `6414142`, `38e53d6` | record set `schuss-record-set-000004@1`, `CATALOG_OPERATIONS.md` |
| Task 011B | Eight-node graph, exact contracts/bindings, and fail-closed build closure | `9b6eaac` | record set `schuss-record-set-000005@1`, `contracts/task011b/` |
| Task 011C | Bounded eight-node legacy backend and ARM evidence | `3011b45` | record set `schuss-record-set-000006@1`, `evidence/task-011c-v1/` |
| Task 012A | Durable project/workspace and persistent graph authoring | `30300ce` | `PROJECT_WORKSPACE_CONTRACTS.md`, `fixtures/task012a/` |
| Task 013 | Reusable compiler front half through stage 6 | `69e5ae8` | record set `schuss-record-set-000007@1`, `COMPILER_FRONT_HALF.md` |
| Task 014 | Shared build execution and product CLI | `69e5ae8` | record set `schuss-record-set-000008@1`, `evidence/task014-completion-v1/` |
| Task 015 | Minimal normalized DSP and direct C++ frontend | `ff835a0` | record set `schuss-record-set-000009@1`, `evidence/task015-completion-v1/` |
| Task 016 | Complete accepted graph through the direct ARM path | `b28c7b6` | record set `schuss-record-set-000010@1`, ADR 0011, `evidence/task016-completion-v1/` |
| Task 017 | Twelve-family curated core and two headless references | `b28c7b6` | record set `schuss-record-set-000011@1`, `evidence/task017-completion-v1/` |
| Task 018 | Authenticated full Gills panel, total mappings/runtime closure, and one mapped direct ARM build | `0ee6939` | record set `schuss-record-set-000012@1`, `GILLS_PANEL_RUNTIME_CONTRACTS.md`, `evidence/task018-completion-v1/` |
| Task 021 | Versioned DMA-safe Gills OLED transport and exact volatile-RAM connected-device observation | `8ca4907` | record set `schuss-record-set-000013@1`, ADR 0013, `evidence/task021-completion-v1/` |
| Task 022 | Omitted-instrument panel diagnostic and retained failed connected promotion | `a5fa328` | record set `schuss-record-set-000014@1`, `evidence/task022-completion-v1/` |
| Task 023 | Client-neutral application capability description, coherent CLI v2, and read-only application smoke | `73502e1` | record set `schuss-record-set-000015@1`, `application_capabilities.py`, `validate_task023.py` |
| Task 024 | Current-Ksoloti-first candidate corpus, deterministic lineage for 3,602 frozen observations, 20 reviewed families with complete variant cohorts, and exact Task 025 selection | `71e85c0` | record set `schuss-record-set-000016@1`, `schuss-current-ksoloti-corpus-000001@1`, both Task 024 review directories, `validate_task024.py` |
| Task 025 | Five exact native-operation semantic promotions, deterministic host vectors, and a fail-closed eight-node plan that rejects the inconsistent reverb allocation before lowering | `71e85c0` | record set `schuss-record-set-000017@1`, `contracts/task025/reverb-allocation-boundary.md`, `evidence/task025-completion-v1/`, `validate_task025.py` |
| Task 026 | Identity-independent reverb-free executable profile plus project-owned create/edit/history/revert, atomic recovery, project-aware CLI build, and deterministic authored ARM ELF | `71e85c0` | record sets `schuss-record-set-000018@1` and `schuss-record-set-000019@1`, `contracts/task026/`, `evidence/task026-completion-v1/`, `validate_task026.py` |
| Task 027 | Exact 19-object extended-library and 53-candidate factory review, additive Mutable-derived provenance, 60-family preservation, and one catalogued-only Rings resonator implementation | `90704b2` | record set `schuss-record-set-000020@1`, `contracts/task027/`, `catalog/reviews/task027-mutable-sources-v1/`, `evidence/task027-completion-v1/`, `validate_task027.py` |
| Task 028 | Fifteen exact independent direct selections and normalized operation-IR lowerings, expanding the counted palette from five to twenty while preserving all later evidence gates | `5e57d29` | record set `schuss-record-set-000021@1`, `contracts/task028/`, `evidence/task028-completion-v1/`, `validate_task028.py` |
| Task 029 | Complete-machine domain layer with exact Palimpsest and Tide Pit source reviews, editable Gills panel/semantic map, fail-closed machine closure, shared read-only inspection operation, and isolated Viewer | `936d186` | record set `schuss-record-set-000022@1`, `contracts/task029/`, `assets/gills/`, `apps/schuss_machine_viewer/`, `evidence/task029-completion-v1/`, `validate_task029.py` |
| Task 030 | Complete exact 56-object Mutable-derived catalog cohort plus shared per-implementation search and CLI v3 object browsing | `0a875ba` | record set `schuss-record-set-000023@1`, `contracts/task030/`, `catalog/reviews/task030-mutable-catalog-v1/`, `evidence/task030-completion-v1/`, `validate_task030.py` |
| Task 031 | Exact seven-node desktop-host contracts, JUCE-independent C++ runtime, deterministic offline WAV, headless JUCE audio/MIDI engine, and process-local render/audio sessions | `932f310` | record set `schuss-record-set-000027@1`, `contracts/task031/`, `packages/schuss_rt/`, `apps/schuss_audio_engine/`, `fixtures/task031/` |
| Task 032 | Bounded variable-graph host lowering/runtime over the seven existing factories plus safe reset-state block-boundary replacement | `c1eaea0` | record set `schuss-record-set-000029@1`, `contracts/task032/`, `packages/schuss_rt/`, `fixtures/task032/`, `evidence/task032-completion-v1/` |
| Task 033 Phase 1 | Source-neutral collection/provider decision plus exact Mutable-derived and pinned-JUCE audit packets | `5dccfd2` | ADR 0017, `catalog/reviews/task033-*/`, `generate_task033_phase1_audits.py`, `validate_task033_phase1.py` |
| Task 034 | Controller-independent instrument successor, reusable performance-control graph, exact Gills/MIDI configurations, and shared read-only inspection | `6010f29` | record set `schuss-record-set-000030@1`, `contracts/task034/`, `performance_control_rules.py`, `performance.inspect`, `evidence/task034-completion-v1/` |
| Task 033 Phase 2 | Source releases, object collections, provider availability, seven exact native catalog companions, and shared read-only inspection | `ccafc1d` | record set `schuss-record-set-000031@1`, `contracts/task033/phase2/`, `collection_provider_rules.py`, `validate_task033_phase2.py` |
| Task 033 Phases 3-4 | One generated seven-entry native registry authority, exact Task 031/032 runtime preservation, evidence-ranked next tranche, later-UI brief, and final cross-layer handoff | `0bf22b6` | `contracts/task033/phase3/`, `generated_native_registry.py`, `033-RESULTS.md`, `033-NEXT-TRANCHE.md`, `033-UI-FOLLOWUP.md` |
| Task 035 | Proportional validation profiles, one-pass record-set ancestry validation, immutable historical reproduction, and structured current-work governance | `88788c5` | ADR 0018, `docs/tasks/035-validation-and-governance-consolidation.md`, `tools/validation/`, `retained_evidence.py` |
| Task 036 | Authenticated 21-file Mutable/Ksoloti physical source package, Task 033 authority audit, and exact Tide Pit migration without duplicate consumer source | `c6fad1f` | `packages/dsp_sources/mutable_ksoloti_v1/`, `docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json`, `docs/tasks/036-RESULTS.md`, `docs/tasks/036-GAPS.md` |
| Task 037 | Non-production Instrument Lab v1 with shared bounded host, MIDI, UI, renderer, build, generation, validation, and reproduction mechanics while musical DSP remains consumer-owned | `c6fad1f` | `research/prototype_support/instrument_lab/`, `tools/instrument_lab/`, `docs/tasks/037-RESULTS.md`, `docs/tasks/037-GAPS.md` |
| Task 038 | Repository-wide Instrument Lab consumer discovery, reusable relocation checks, source-release-bound Mutable source packages, and shared Braids adapter migration | `74d87cf` | record set `schuss-record-set-000032@1`, `contracts/task038/`, `packages/dsp_sources/`, `packages/dsp_adapters/mutable_braids_v1/`, `docs/tasks/038-RESULTS.md` |
| Task 039 | Five-entry noncanonical desktop audition library, exact local-build availability, bounded JUCE process sessions, and Instruments-first desktop with preserved Workshop | `b9a742e` | record set `schuss-record-set-000033@1`, `research/prototype_support/instrument_library/`, `packages/schuss_core/instrument_library.py`, `apps/schuss_desktop/`, `docs/tasks/039-desktop-instrument-library.md` |
| Task 040 Phase 1 | Planning-only Cinderwheel implementation-ready bundle and exact proposed allocation; closed and deferred before canonical or DSP implementation | `955084e` | `contracts/task040/phase1/`, `docs/tasks/040-cinderwheel-canonical-vertical-slice.md` |
| Task 041 | Exact Gills engine-support revision-1 authority, five immutable consumer bindings, deterministic self-contained release closures, and preserved portable/ARM evidence | `a6eeaab` | Gills commit `9b5e4f9`, `docs/tasks/041-shared-gills-engine-support-hardening.md`, `docs/tasks/041-RESULTS.md`, `docs/tasks/041-GAPS.md` |
| Task 042 | Noncanonical Layerwell desktop meta-instrument combining exact Tide Pit and Generative Drums Cores with three source-only layers and synthetic Launch Control 3 protocol evidence | `7a66949` | `research/proposals/layerwell.md`, `research/prototypes/layerwell/`, `docs/tasks/042-layerwell-meta-instrument.md` |
| Task 043 | Canonical Pamplist 0.6 catalog, seven-role graph, and instrument identity plus one exact audition-library v2 link; no canonical provider/runtime claim | working tree (uncommitted) | record set `schuss-record-set-000036@1`, `contracts/task043/`, `research/prototype_support/instrument_library/audition-library-v2.json`, `docs/tasks/043-pamplist-canonical-instrument.md` |
| Task 044 | Noncanonical Layerwell 0.2 with exactly Tide Pit and Pamplist, complete accepted-state embedded panels, three synchronized source-only layers, sole-layer non-destructive trim, deterministic evidence, and authenticated unlaunched app build | working tree (uncommitted) | `research/proposals/layerwell-r02.md`, `research/prototypes/layerwell/contract-r02/`, `docs/tasks/044-layerwell-r02-embedded-source-sampler.md` |
| Task 045 | Private macOS arm64 Pamplist 0.6 VST3 with stable parameter/state semantics, bounded 48 kHz processing, offline direct/module-host evidence, authenticated uninstalled Release build, and relocated reproduction | working tree (uncommitted) | `research/proposals/pamplist-vst3-local.md`, `research/prototypes/pamplist/contract-vst3-r01/`, `research/prototypes/pamplist/vst3/`, `docs/tasks/045-pamplist-local-vst3.md` |
| Task 046 | Private macOS arm64 Tide Pit VST3 preserving the exact 48 kHz Core, sixteen stable parameters, fresh-Core state, accepted-state UI, offline direct/module-host evidence, authenticated uninstalled Release build, and relocated reproduction | working tree (uncommitted) | `research/proposals/tide-pit-vst3-local.md`, `research/prototypes/tide-pit-gills/contract-vst3-r01/`, `research/prototypes/tide-pit-gills/vst3/`, `docs/tasks/046-tide-pit-local-vst3.md` |
| Task 047 | Shared fixed-capacity rational output resampling for the private Tide Pit and Pamplist VST3 adapters, preserving exact 48 kHz bypass while accepting seven declared host rates with bounded event translation, offline module-host evidence, authenticated uninstalled Release builds, and relocated reproduction | working tree (uncommitted) | `research/proposals/tide-pit-pamplist-vst3-resampling.md`, `research/prototypes/vst3-resampling/contract-r01/`, both prototype `vst3/` adapters, `docs/tasks/047-vst3-fixed-rate-resampling.md` |
| Task 048 | Noncanonical Wanderbody 0.1 standalone with bounded recent-memory capture, Hover and correlated Drunk motion, exact eight-tuple recurrence, four fragment voices, an original six-mode body, deterministic objective evidence, and an authenticated unlaunched arm64 target build | working tree (uncommitted) | `research/proposals/wanderbody-standalone-r01.md`, `research/prototypes/wanderbody/contract-r01/`, `research/prototypes/wanderbody/`, `docs/tasks/048-wanderbody-standalone-first-playable.md` |
| Unnumbered desktop initialization | Core-owned semantic boundary and inert Tauri/React application location | `0cddd56` | `docs/tasks/ui-desktop-initialization.md`, `docs/DESKTOP_UI_BOUNDARY.md` |
| Unnumbered read-only desktop catalog | Runnable Tauri catalog client over the shared operation bridge | `6d018d2` | `docs/tasks/ui-desktop-read-only-catalog.md`, `apps/schuss_desktop/` |
| Unnumbered desktop patcher | Consolidated Objects/Patches application with project-backed graph authoring and immutable history/revert | `6d018d2` | record set `schuss-record-set-000024@1`, `docs/tasks/ui-desktop-patcher-authoring.md`, `apps/schuss_desktop/` |
| Unnumbered desktop authoring performance | Exact validated base reuse, bounded semantic augmentation cache, and recoverable editor progress/error states | `6d018d2` | `docs/tasks/ui-desktop-authoring-performance.md`, `packages/schuss_core/project_service.py`, `apps/schuss_desktop/` |
| Unnumbered desktop build/device workflow | Process-local build sessions, structured diagnostics, explicit Ksoloti identity/compatibility sessions, and a fake-tested read-back-verified volatile-RAM upload path | `a741864` | record set `schuss-record-set-000025@1`, `docs/tasks/ui-desktop-build-device-workflow.md`, `packages/schuss_core/build_sessions.py`, `packages/schuss_core/device_sessions.py`, `apps/schuss_desktop/` |
| Unnumbered desktop project-object handoff | Separate project-local object browsing and placement plus guarded refresh of externally accepted project revisions | `10d43d9` | record set `schuss-record-set-000026@1`, `docs/tasks/ui-desktop-project-object-handoff.md`, `apps/schuss_desktop/` |
| Unnumbered desktop workspace shell | Always-on canvas, contextual Objects/Patches drawers, persistent local projects-root preference, core-owned project browsing/creation, and eager native core startup | `10d43d9` | record set `schuss-record-set-000028@1`, `docs/tasks/ui-desktop-workspace-shell.md`, `packages/schuss_core/workspace_library.py`, `apps/schuss_desktop/` |
| Unnumbered AI/MCP foundation | Dual-era local stdio MCP adapter over six existing read-only catalog/component/graph operations and one capability resource | `a741864` | record set `schuss-record-set-000025@1`, `docs/AI_MCP_BOUNDARY.md`, `docs/tasks/ai-mcp-read-only-foundation.md`, `packages/schuss_core/mcp_server.py`, `bin/schuss-mcp` |
| Unnumbered sonic-first AI authoring | Three-lane sonic planning, bounded project-local transparent compounds/native kernels, deterministic host audition, exact preview, recoverable atomic acceptance, and explicit project-mode MCP tools | `a741864` | record set `schuss-record-set-000026@1`, `docs/tasks/ai-sonic-authoring-foundation.md`, `packages/schuss_core/ai_authoring.py`, `packages/schuss_core/native_kernel.py`, `packages/schuss_core/project_service.py`, `packages/schuss_core/mcp_server.py` |
| VH-001 | Bounded audit of five configured historical golden/hash gates without rebaselining or source-configuration changes | `0cddd56` | `docs/validation/VH-001-historical-golden-hash-audit.md`, `evidence/validation-hygiene-v1/` |
| Compiler determinism matrix | Fresh-root/process determinism across Tasks 013-015 | `796dd52` | `tools/contracts/compiler_determinism_matrix.py` |
| Backbone governance guard | Backend-first routing and explicit UI deferral | `4a578de` | ADR 0010 and `tools/contracts/validate_backbone_governance.py` |

## Archived task documents

| Historical path | Retrieval commit |
| --- | --- |
| `docs/tasks/001-legacy-inventory.md` | `b28c7b6` |
| `docs/tasks/002-phase-3-inventory-review-gate.md` | `b28c7b6` |
| `docs/tasks/003-phase-4a-semantic-catalog-foundation.md` | `b28c7b6` |
| `docs/tasks/004-schema-and-compiler-contract-strategy.md` | `b28c7b6` |
| `docs/tasks/005-minimal-gills-device-profile-and-instrument-contracts.md` | `b28c7b6` |
| `docs/tasks/006-component-contract-binding-and-dsp-graph-contracts.md` | `b28c7b6` |
| `docs/tasks/007-compute-target-backend-build-and-evidence-contracts.md` | `b28c7b6` |
| `docs/tasks/008-shared-headless-control-plane-and-operation-contracts.md` | `b28c7b6` |
| `docs/tasks/009-prerequisite-authenticated-environment-and-probe-contract.md` | `b28c7b6` |
| `docs/tasks/009-prerequisite-closure-repair-and-reauthentication.md` | `b28c7b6` |
| `docs/tasks/009-minimal-deterministic-legacy-backend-proof.md` | `b28c7b6` |
| `docs/tasks/010-deterministic-product-cli-over-shared-operations.md` | `b28c7b6` |
| `docs/tasks/011-first-non-ui-gills-vertical-slice-roadmap-proposal.md` | `b28c7b6` |
| `docs/tasks/011a-browsable-catalog-control-plane-and-exact-gills-slice-catalog-review.md` | `b28c7b6` |
| `docs/tasks/011b-component-contracts-gills-slice-graph-and-unresolved-build-closure.md` | `b28c7b6` |
| `docs/tasks/011c-bounded-legacy-backend-expansion-and-arm-evidence.md` | `b28c7b6` |
| `docs/tasks/012a-durable-project-workspace-and-cli-graph-authoring.md` | `b28c7b6` |
| `docs/tasks/013-reusable-compiler-front-half.md` | `b28c7b6` |
| `docs/tasks/014-shared-build-execution-and-product-cli.md` | `b28c7b6` |
| `docs/tasks/015-normalized-dsp-and-minimal-direct-frontend.md` | `b28c7b6` |
| `docs/tasks/016-complete-gills-slice-direct-frontend.md` | `b28c7b6` |
| `docs/tasks/016-direct-semantics-decision-brief.md` | `b28c7b6` |
| `docs/tasks/017-curated-core-and-headless-reference-instruments.md` | `b28c7b6` |
| `docs/tasks/compiler-determinism-matrix.md` | `b28c7b6` |

Task 012B is retained in `docs/tasks/` as a retirement guard. The completed
Task 018 and Task 021 contracts remain present until their normal archival
step; no later product task is automatically active.
