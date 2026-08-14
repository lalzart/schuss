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
  generated-file bindings for the Phase 3 review packet; and
- `phase3-review-summary-v0.schema.json` validates the review gate's aggregate
  impact and sample census.

The resolved schemas describe factual compatibility-bridge evidence only. They
do not establish the final Schuss catalog, graph, object, instrument, or
operation contracts.
