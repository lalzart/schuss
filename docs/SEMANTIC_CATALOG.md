# Semantic catalog foundation

## Identity progression

Schuss separates three identities that the legacy patcher often presents as
one name:

```text
frozen legacy observation -> implementation variant -> user-facing family
```

### Frozen legacy observation

A legacy observation is a snapshot-scoped fact exported by the compatibility
bridge. Phase 4A references object and graph observations as
`legacy-resolved-catalog-v0:object:<index>` and
`legacy-resolved-catalog-v0:graph:<index>`. The index is meaningful only with
that frozen snapshot and its manifest hash. It is an evidence locator, not a
stable Schuss identity.

Observations may be duplicate definitions, overload candidates, catalog
subpatch placeholders, provider-only emissions, or partial records. Curation
does not rewrite them or make an ambiguous legacy selection definitive.

### Implementation variant

An implementation is a concrete component that a backend may select. It has an
opaque ID of the form `schuss-implementation-NNNNNN`. The numeric allocation is
manual, monotonic within the Schuss registry, never derived from record order,
and never reused after publication.

An implementation belongs to exactly one family in overlay v0. It records its
form, provenance, evidence-backed compatibility status, preferred status,
membership rationale and confidence, and any unresolved questions. A legacy
implementation references at least one frozen object observation; compounds
may additionally reference their graph observation. A future Schuss-native
implementation may use a later schema that defines non-legacy evidence.

Multiple observations become one implementation only when evidence shows they
describe one concrete component. A file-backed definition and an unmatched
provider emission are separate implementations until their identity is
proved. An uncertain family membership is marked `low`, uses `needs-review`,
and carries a written membership question; it is never guessed silently.

Compatibility is an implementation property. Phase 4A records only
`not-evaluated` target status with the `legacy-resolved-export` evidence level.
That means the pinned Java model observed the definition. It does not prove
legacy code generation, ARM compile/link, real-time headroom, connected-device
behavior, or audible quality.

Phase 4A implementation records are not yet compiler-facing implementation
bindings because no typed component contract existed when overlay v0 was
defined. Task 004 preserves every `schuss-implementation-*` ID and defines a
future companion binding record keyed by that same identity. The binding will
reference one exact component-contract revision and map its public facets to
the concrete realization. During migration, its contract's family MUST agree
with the overlay `family_id`; the overlay is not rewritten in place.

### User-facing family

A family is the item a musician normally discovers in the object drawer. It
has an opaque ID of the form `schuss-family-NNNNNN`, allocated and retained by
the same rules as implementation IDs. A family owns its display name, aliases,
concise description, one canonical primary category, controlled secondary
function tags, abstraction level, review state, classification confidence,
core/pilot status, rationale, and unresolved classification questions.

A family may contain several implementations. Backend and compute-target
selection happen below family identity. Renaming a family, changing aliases,
moving it to a different category, or revising tags never changes either the
family ID or its implementation IDs.

## Navigation and facets

Every family has exactly one `primary_category` from the versioned functional
tree for deterministic drawer placement. Additional roles use controlled
`secondary_function_tags`; they do not duplicate the family in the primary
tree. Provenance, abstraction, implementation form, compatibility, review
status, and curation status remain independent facets.

Category labels and hierarchy are mutable vocabulary. Category slugs are
versioned classification values, not object identity. Factory, Mutable
Instruments, repository, author, community, user, and demo names are prohibited
as primary categories. Primitive, compound, and instrument are abstraction
levels. Native object, generated object, legacy subpatch, service, and example
are implementation forms.

## Overlay representation

Phase 4A uses one UTF-8 JSON document at
`catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json`. JSON is suitable
for the pilot because it is dependency-free, directly schema-validatable,
reviewable in Git, and consumable by future GUI, CLI, and AI clients. Separate
`families` and `implementations` arrays keep navigation records independent
from backend membership and compatibility evidence.

The representation is deterministic:

- UTF-8 without a BOM, LF endings, and a final LF;
- no timestamps, random IDs, checkout paths, or generated ordering;
- families and implementations sorted by their opaque IDs;
- aliases, tags, evidence references, and provenance references sorted and
  unique; and
- validator output serialized with sorted JSON keys and compact separators.

The top-level `legacy_evidence` record binds the overlay to the exact Phase 3
manifest hash. The validator applies the committed JSON Schema, resolves every
evidence reference, checks source provenance against the referenced
observations, rejects unsupported compatibility claims, and derives the pilot
coverage/difficult-case summary from the frozen evidence.

## Review and confidence

`review_status` distinguishes `pilot-reviewed`, `needs-review`, and `deferred`.
Confidence is `high`, `medium`, or `low` and always has written rationale. Low
classification confidence requires a classification question; low membership
confidence requires a membership question. A record may therefore have one
canonical placement while openly naming why that placement may change.

`pilot` means only that the family exercises the Phase 4A model. `core_status`
and implementation `preferred_status` remain manual judgments; neither follows
from source order, graph-reference frequency, repository ownership, or a
passing structural export.

## Deferred design

Overlay v0 still does not define public ports or parameters, the authoritative
Schuss graph, device profiles, instruments, shared graph operations, target
capability negotiation, or compiler lowering. Task 004 defines their normative
ownership and reference direction in `docs/SCHEMA_STRATEGY.md` and the compiler
stages in `docs/COMPILER_STRATEGY.md`. Task 005 now supplies separate minimal
production device-profile and instrument schemas; graph, component, binding,
target, backend, build, and operation schemas remain bounded future work.
Phase 4B must not expand compiler-facing variants faster than actual component
contracts and bindings are reviewed. No later contract may infer a stable
identity from the legacy `.axp` boundary artifact.
