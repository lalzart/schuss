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
  references, deferred or exact graph references, and device/graph mappings;
- `catalog-family-companion-v0.schema.json` binds an exact semantic-catalog
  family member into the revision/hash contract domain without copying its
  classification;
- `component-contract-v0.schema.json` validates target-independent typed public
  node interfaces and transparent-compound mapping keys;
- `implementation-binding-v0.schema.json` validates exact realization and
  public-facet seam maps; and
- `dsp-graph-v0.schema.json` validates exact contract nodes, connections,
  exposures, parameter bindings, hierarchy, and compound mappings;
- `capability-vocabulary-v0.schema.json`, `build-environment-v0.schema.json`,
  `compute-target-v0.schema.json`, and `backend-v0.schema.json` validate the
  reusable target/backend contract boundary;
- `binding-eligibility-v0.schema.json` validates exact target/backend
  eligibility without changing Task 006 bindings; and
- `build-request-v0.schema.json`, `build-result-v0.schema.json`,
  `artifact-descriptor-v0.schema.json`, `resource-report-v0.schema.json`, and
  `evidence-claim-v0.schema.json` validate the one-way future build/evidence
  record shapes.

The resolved schemas describe factual compatibility-bridge evidence only. The
semantic overlay is a versioned curation foundation and pilot, not a complete
catalog census or a final graph, object-facet, instrument, device, or operation
contract.

Tasks 005-007 add the device, instrument, component, binding, graph, exact
family, target, backend, build, artifact, resource, and evidence schemas.
Presentation and broader asset contracts remain later work. Processor,
toolchain/runtime, and backend identities are controlled stable values in the
reusable schemas; the records under `contracts/` choose Ksoloti-specific
values. See `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`.
