# Schemas

This directory contains only contracts that current Schuss artifacts use:

- `source-lock-v1.schema.json` validates portable upstream locks;
- `legacy-catalog-manifest-v0.schema.json` validates raw snapshot manifests;
- `legacy-catalog-file-v0.schema.json` validates raw candidate records;
- `legacy-catalog-issue-v0.schema.json` validates raw issues;
- `legacy-resolved-manifest-v0.schema.json` validates Java-resolved snapshot
  manifests;
- `legacy-resolved-object-v0.schema.json` validates ordered legacy object
  observations;
- `legacy-resolved-graph-v0.schema.json` validates pre/post-resolution graph
  observations;
- `legacy-resolved-issue-v0.schema.json` validates resolved-inventory issues;
- `legacy-resolved-summary-v0.schema.json` validates reconciliation reports;
- `phase3-review-manifest-v0.schema.json` validates the immutable-input and
  generated-file bindings for the Phase 3 review packet;
- `phase3-review-summary-v0.schema.json` validates the review gate's aggregate
  impact and sample census; and
- `semantic-catalog-overlay-v0.schema.json` validates the separate Phase 4A
  family/implementation classification overlay and its evidence references;
- `device-profile-v0.schema.json` validates closed physical control, gesture,
  feedback/display, physical-I/O, and unresolved-fact records; and
- `instrument-v0.schema.json` validates closed musical facets, exact device
  references, deferred graph intent, and device/graph mappings.

The resolved schemas describe factual compatibility-bridge evidence only. The
semantic overlay is a versioned curation foundation and pilot, not a complete
catalog census or a final graph, object-facet, instrument, device, or operation
contract.

Task 005 adds only the device-profile and instrument schemas. Component,
binding, graph, target, backend, build, evidence, presentation, and asset
contract families remain planned in the dependency order defined by
`docs/SCHEMA_STRATEGY.md`.
