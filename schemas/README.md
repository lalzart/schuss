# Schemas

This directory contains versioned machine-readable contracts. A schema file
existing here does not make it active: exact record-set manifests enumerate the
schemas and records in each accepted closure.

## Schema groups

| Group | Examples and ownership |
| --- | --- |
| Source and inventory | Source locks, raw inventory, Java-resolved observations, and review packets |
| Catalog | Semantic overlays, exact catalog corpora/projections, selection packets, and family companions |
| Musical domain | Device profiles, instruments, component contracts, implementation bindings, and DSP graphs |
| Target and build | Compute targets, backends, eligibility, environments, requests/results, artifacts, resources, and evidence |
| Operations | Additive request/result envelopes v1-v5 for validation, graph, catalog, project, plan, and execute operations |
| Project/workspace | Portable projects, write plans, atomic heads, locks, and recovery |
| Compiler | Resolution/elaboration/dependency/resource plans, origin maps, normalized DSP, direct operation specs, and frontend results |
| Authenticated probes | Task 009 prerequisite environment, procedure, input/result, and evidence records |

## Rules

- Revisions are additive; accepted schema and record bytes are never rewritten.
- Durable records use stable IDs, exact revisions/content hashes, portable
  paths, normalized encoding, and closed controlled values.
- Directory presence, filesystem order, display names, and implicit latest
  revisions never establish membership or identity.
- Schemas describe structure and reference direction. They do not promote
  compatibility or evidence by themselves.
- Device, instrument, graph, target, backend, build, and evidence identities
  remain independent.

Normative ownership is documented in `docs/SCHEMA_STRATEGY.md`; compiler stages
are in `docs/COMPILER_STRATEGY.md`. Current implementation status is maintained
only in `docs/STATUS.md`.
