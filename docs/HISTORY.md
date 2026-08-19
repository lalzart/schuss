# Development history

This is the concise index of completed Schuss work. Completed task contracts
are not live scheduling authority and are omitted from the current working
tree. Git retains their exact bytes; use the command below with the commit and
path recorded in the archive table.

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
| Task 023 | Client-neutral application capability description, coherent CLI v2, and read-only application smoke | Not committed | record set `schuss-record-set-000015@1`, `application_capabilities.py`, `validate_task023.py` |
| Task 024 | Current-Ksoloti-first candidate corpus, deterministic lineage for 3,602 frozen observations, 20 reviewed families with complete variant cohorts, and exact Task 025 selection | Not committed | record set `schuss-record-set-000016@1`, `schuss-current-ksoloti-corpus-000001@1`, both Task 024 review directories, `validate_task024.py` |
| Task 025 | Five exact native-operation semantic promotions, deterministic host vectors, and a fail-closed eight-node plan that rejects the inconsistent reverb allocation before lowering | Not committed | record set `schuss-record-set-000017@1`, `contracts/task025/reverb-allocation-boundary.md`, `evidence/task025-completion-v1/`, `validate_task025.py` |
| Task 026 | Identity-independent reverb-free executable profile plus project-owned create/edit/history/revert, atomic recovery, project-aware CLI build, and deterministic authored ARM ELF | Not committed | record sets `schuss-record-set-000018@1` and `schuss-record-set-000019@1`, `contracts/task026/`, `evidence/task026-completion-v1/`, `validate_task026.py` |
| Task 027 | Exact 19-object extended-library and 53-candidate factory review, additive Mutable-derived provenance, 60-family preservation, and one catalogued-only Rings resonator implementation | Not committed | record set `schuss-record-set-000020@1`, `contracts/task027/`, `catalog/reviews/task027-mutable-sources-v1/`, `evidence/task027-completion-v1/`, `validate_task027.py` |
| Task 028 | Fifteen exact independent direct selections and normalized operation-IR lowerings, expanding the counted palette from five to twenty while preserving all later evidence gates | Not committed | record set `schuss-record-set-000021@1`, `contracts/task028/`, `evidence/task028-completion-v1/`, `validate_task028.py` |
| Task 029 | Complete-machine domain layer with exact Palimpsest and Tide Pit source reviews, editable Gills panel/semantic map, fail-closed machine closure, shared read-only inspection operation, and isolated Viewer | Not committed | record set `schuss-record-set-000022@1`, `contracts/task029/`, `assets/gills/`, `apps/schuss_machine_viewer/`, `evidence/task029-completion-v1/`, `validate_task029.py` |
| Task 030 | Complete exact 56-object Mutable-derived catalog cohort plus shared per-implementation search and CLI v3 object browsing | Not committed | record set `schuss-record-set-000023@1`, `contracts/task030/`, `catalog/reviews/task030-mutable-catalog-v1/`, `evidence/task030-completion-v1/`, `validate_task030.py` |
| Task 031 | Exact seven-node desktop-host contracts, JUCE-independent C++ runtime, deterministic offline WAV, headless JUCE audio/MIDI engine, and process-local render/audio sessions | `932f310` | record set `schuss-record-set-000027@1`, `contracts/task031/`, `packages/schuss_rt/`, `apps/schuss_audio_engine/`, `fixtures/task031/` |
| Task 032 | Bounded variable-graph host lowering/runtime over the seven existing factories plus safe reset-state block-boundary replacement | Not committed | record set `schuss-record-set-000029@1`, `contracts/task032/`, `packages/schuss_rt/`, `fixtures/task032/`, `evidence/task032-completion-v1/` |
| Unnumbered desktop initialization | Core-owned semantic boundary and inert Tauri/React application location | Not committed | `docs/tasks/ui-desktop-initialization.md`, `docs/DESKTOP_UI_BOUNDARY.md` |
| Unnumbered read-only desktop catalog | Runnable Tauri catalog client over the shared operation bridge | Not committed | `docs/tasks/ui-desktop-read-only-catalog.md`, `apps/schuss_desktop/` |
| Unnumbered desktop patcher | Consolidated Objects/Patches application with project-backed graph authoring and immutable history/revert | Not committed | record set `schuss-record-set-000024@1`, `docs/tasks/ui-desktop-patcher-authoring.md`, `apps/schuss_desktop/` |
| Unnumbered desktop authoring performance | Exact validated base reuse, bounded semantic augmentation cache, and recoverable editor progress/error states | Not committed | `docs/tasks/ui-desktop-authoring-performance.md`, `packages/schuss_core/project_service.py`, `apps/schuss_desktop/` |
| Unnumbered desktop build/device workflow | Process-local build sessions, structured diagnostics, explicit Ksoloti identity/compatibility sessions, and a fake-tested read-back-verified volatile-RAM upload path | Not committed | record set `schuss-record-set-000025@1`, `docs/tasks/ui-desktop-build-device-workflow.md`, `packages/schuss_core/build_sessions.py`, `packages/schuss_core/device_sessions.py`, `apps/schuss_desktop/` |
| Unnumbered desktop project-object handoff | Separate project-local object browsing and placement plus guarded refresh of externally accepted project revisions | Not committed | record set `schuss-record-set-000026@1`, `docs/tasks/ui-desktop-project-object-handoff.md`, `apps/schuss_desktop/` |
| Unnumbered desktop workspace shell | Always-on canvas, contextual Objects/Patches drawers, persistent local projects-root preference, core-owned project browsing/creation, and eager native core startup | Not committed | record set `schuss-record-set-000028@1`, `docs/tasks/ui-desktop-workspace-shell.md`, `packages/schuss_core/workspace_library.py`, `apps/schuss_desktop/` |
| Unnumbered AI/MCP foundation | Dual-era local stdio MCP adapter over six existing read-only catalog/component/graph operations and one capability resource | Not committed | record set `schuss-record-set-000025@1`, `docs/AI_MCP_BOUNDARY.md`, `docs/tasks/ai-mcp-read-only-foundation.md`, `packages/schuss_core/mcp_server.py`, `bin/schuss-mcp` |
| Unnumbered sonic-first AI authoring | Three-lane sonic planning, bounded project-local transparent compounds/native kernels, deterministic host audition, exact preview, recoverable atomic acceptance, and explicit project-mode MCP tools | Not committed | record set `schuss-record-set-000026@1`, `docs/tasks/ai-sonic-authoring-foundation.md`, `packages/schuss_core/ai_authoring.py`, `packages/schuss_core/native_kernel.py`, `packages/schuss_core/project_service.py`, `packages/schuss_core/mcp_server.py` |
| VH-001 | Bounded audit of five configured historical golden/hash gates without rebaselining or source-configuration changes | Not committed | `docs/validation/VH-001-historical-golden-hash-audit.md`, `evidence/validation-hygiene-v1/` |
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
