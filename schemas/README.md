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
- `component-contract-v1.schema.json` additively validates semitone-offset
  ports/parameters plus closed rising-edge, parameter-sum, indexed-selection,
  and bounded-counter behavior rules without changing v0;
- `implementation-binding-v1.schema.json` additively retains exact null legacy
  parameter datatypes and the frozen 39-through-42-hex durable UUID widths
  without changing v0; and
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
  record shapes; and
- `operation-request-v1.schema.json` and `operation-result-v1.schema.json`
  validate the shared Task 008 headless envelope, while
  `backend-invocation-input-v1.schema.json` defines the non-executable Task 009
  handoff seam; and
- `catalog-corpus-v1.schema.json` validates the exact Task 011A Phase 4A
  companion and Gills-slice review closure, `catalog-projection-v1.schema.json`
  validates its derived client-neutral view, and
  `operation-request-v2.schema.json`/`operation-result-v2.schema.json` add the
  catalog operations without changing the v1 bytes; and
- `project-v0.schema.json` defines the portable exact project overlay,
  `workspace-head-v0.schema.json` defines its atomic acceptance marker,
  `project-write-plan-v0.schema.json` binds expected old and proposed new
  bytes, and `workspace-lock-v0.schema.json` plus
  `workspace-recovery-v0.schema.json` keep local coordination outside project
  identity; `operation-request-v3.schema.json` and
  `operation-result-v3.schema.json` add Task 012A project operations without
  changing v1/v2 bytes.

The resolved schemas describe factual compatibility-bridge evidence only. The
semantic overlay is a versioned curation foundation and pilot, not a complete
catalog census or a final graph, object-facet, instrument, device, or operation
contract.

Tasks 005-008 add the device, instrument, component, binding, graph, exact
family, target, backend, build, artifact, resource, evidence, and operation
schemas. Presentation and broader asset contracts remain later work. Processor,
toolchain/runtime, and backend identities are controlled stable values in the
reusable schemas; the records under `contracts/` choose Ksoloti-specific
values. See `docs/TARGET_BACKEND_BUILD_CONTRACTS.md` and
`docs/OPERATION_CONTRACTS.md`.

Task 011B is the first selected mixed v0/v1 component-and-binding view. Q21 is
used for semitone-offset legacy `Frac32` seams; Q27 remains the accepted
normalized/audio representation. The successor schemas do not imply backend
support or executable evidence.

Task 012A does not revise `dsp-graph-v0`. Project-owned member entries retain
the exact graph parent while the graph bytes remain authoritative semantic
records. See `docs/PROJECT_WORKSPACE_CONTRACTS.md`.
