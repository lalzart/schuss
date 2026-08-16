# Headless packages

`schuss_core` owns the reusable headless product boundary. Clients construct
requests and render results; they do not duplicate catalog, graph, project,
compiler, or build rules.

| Module | Responsibility |
| --- | --- |
| `control_plane.py` | Versioned client-neutral operation dispatch and canonical results |
| `catalog_projection.py` | Exact record-set catalog projection, search, inspection, and readiness |
| `project_service.py` | Portable project loading, locking, immutable revision writes, atomic heads, and recovery |
| `compiler_front_half.py` | Validation, binding resolution, compound elaboration, dependency/resource planning, and origin maps |
| `build_execution.py` | Exact handler registry, plan-once execution, cancellation, and fresh-root publication |
| `direct_frontend.py` | Minimal normalized Q27/standalone C++ proof boundary |
| `gills_direct_frontend.py` | Accepted eight-node normalized direct lowering under ADR 0011 |
| `gills_direct_backend.py` | Exact registered direct handler and local ARM build boundary |
| `cli.py`, `product_cli.py` | Deterministic product command parsing and rendering |
| `project_cli.py` | Project-specific command projection over `ProjectService` |

The package imports no UI or device transport. Legacy Java and `.axp` handling
remain isolated under `legacy/ksoloti-bridge/`; exact legacy runners are
injected handlers, not an ambient fallback.

Current capability and proof gaps are maintained in `docs/STATUS.md`. Record-
set manifests, not directory scans or “latest” inference, define every accepted
input closure.
