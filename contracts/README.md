# Semantic and build records

This directory contains exact versioned records. Schemas live under `schemas/`,
validators under `tools/contracts/`, and record-set manifests under
`contracts/record-sets/`.

Record-set manifests are the only authority for accepted membership. Tools may
not infer a closure by scanning these directories or choosing a newest
revision.

## Layout

- The domain directories (`component-contracts/`, `graphs/`, `instruments/`,
  `compute-targets/`, and peers) retain the original accepted base records.
- `task009/`, `task011b/`, and `task011c/` retain bounded legacy proof and
  eight-node successor records.
- `task016/` retains the direct eight-node implementation and promotion
  evidence accepted under ADR 0011.
- `task017/` retains the reviewed twelve-family core, exact two reference
  instruments, and explicit unsupported direct semantics.
- `record-sets/` binds every closure by exact portable path, byte hash, stable
  identity, and revision.

Task labels in retained directory names are historical provenance, not current
scheduling authority. Completed milestones are indexed in `docs/HISTORY.md`;
current direction is maintained in `docs/STATUS.md`.

No record or successful link result implies firmware upload, connected-device
operation, real-time safety, or audible behavior. Those claims require their
own exact evidence.
