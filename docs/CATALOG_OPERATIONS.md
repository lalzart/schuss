# Catalog projection and operations

Task 011A supplies the first browsable Schuss catalog control plane. The
authoritative inputs remain the frozen Phase 4A semantic overlay, exact
successor corpus, accepted component/binding records, and accepted
target/backend/build/evidence records. The projection is derived in memory; no
materialized cache or family-owned reverse index is committed.

## Exact input and identity boundary

Successor record set `schuss-record-set-000004` revision 1 contains one
`catalog-corpus-v1` record and the additive schemas. The corpus binds the exact
Phase 4A overlay byte hash and every source observation used by the bounded
review. It provides exact companion references for 25 pilot families;
Crossfader reuses its accepted Task 006 family record. A companion is a
successor contract record over a frozen member, not fabricated Phase 4A
history.

The complete view has 28 families and 41 implementations:

- all 26 Phase 4A families and all 38 implementations retain their stable IDs;
- Square LFO is `schuss-family-000027` with implementation `000039` from
  observation 209;
- Cyclic Counter is `schuss-family-000028` with implementation `000040` from
  observation 215; and
- the four-step pitch sequencer is implementation `000041` under existing
  family `000022`, from observation 918. Implementation `000032` remains the
  distinct sixteen-step observation 920.

No other family or implementation identity is allocated. No missing component
contract, binding, eligibility, graph, instrument, build, or evidence record is
created.

## Task 027 provenance successor

Exact record set `schuss-record-set-000020@1` adds catalog corpus/projection v4
and source review `schuss-catalog-source-review-000001@1`. It preserves all
sixty Task 024 reviewed families and every prior implementation, then adds only
`schuss-implementation-000096@1` under existing Physical-model Resonator family
`schuss-family-000010@1`.

The source review is a separate deterministic candidate artifact. It covers
the nineteen objects in the exact pinned `ai/sdk/ksoloti-extended` Git tree and
fifty-three Task 024 factory candidates whose own descriptions explicitly
attribute Mutable Instruments code or DSP. It does not use ambient source
bytes. Candidate membership does not itself make an object a catalog
implementation.

`mutable-instruments-derived` is an additive candidate- and
implementation-specific provenance tag. The family-level projection exposes
the union as a search facet so catalogued objects remain discoverable through
their ordinary functional families. `catalog.inspect` identifies the exact
tagged implementations; it does not impute ancestry to their siblings. Six
catalogued implementations across five families carry the tag. The extended
topographic sequencer, macro voice, and forty-eight attributed factory objects
remain tagged candidates outside the catalog, while sixteen other extended
objects remain inventory-only without exact Mutable-derivation evidence.

Source compatibility and build labels remain quoted source metadata. In
particular, the macro voice's `h7-recommended` and `build-failed` values and the
Warps wrapper's source link-failure statement are not Schuss compiler, ARM,
device, real-time, or audible evidence. The new Rings resonator remains
`catalogued-only` and `unresolved`; Task 027 does not alter the separate failed
Rings-reverb allocation claim.

## Task 030 complete attributed cohort

Exact record set `schuss-record-set-000023@1` adds catalog corpus/projection v5
and source-review revision 2. It retains the six Task 027 mappings, turns the
remaining fifty attributed candidates into exact implementations `000112`-
`000161`, and adds forty-seven function-first families `000061`-`000107`.
Elements string/tube reuse Physical-model Resonator family `000010`; Braids
saw reuses Band-limited Saw Oscillator family `000031`. The result contains
107 families, 133 implementations, and exactly 56 implementations carrying
`mutable-instruments-derived`.

The sixteen extended entries without exact attribution remain inventory-only.
Every new implementation is `catalogued-only`, compatibility `not-evaluated`,
and unresolved, with no contract, binding, eligibility, result, artifact, or
evidence reference. Catalog membership therefore proves only structural and
source provenance levels 1-2.

## Projection derivation

`schuss-catalog-projection-v1` validates the complete client-neutral view.
`schuss-catalog-match-v1` defines matching. The projection's
`input_closure_hash` binds the selected record-set reference, catalog reference,
frozen overlay byte hash, and ordered exact semantic-record content hashes.
Loading fails closed if the corpus schema/hash, overlay closure, companion
member hash, observation provenance closure, child content hash, or approved
identity set is stale.

Each family entry exposes presentation, primary musical function, controlled
technique tags, abstraction, implementation forms, provenance, exact
contract-derived signal and capability facets, readiness, unresolved facts,
and implementation chains. The direction is always authoritative records to
projection; clients never write these facts back.

Signal domain, rate, role, and channel count appear only when an exact component
contract declares them. Legacy datatype observations do not become graph-safe
signals. Provenance stays independent from function and ordering.

## Search and filtering

The operation is `catalog.search`. The CLI form is:

```text
schuss catalog search [QUERY]
  [--function VALUE] [--abstraction VALUE] [--form VALUE]
  [--signal-domain VALUE] [--signal-rate VALUE] [--signal-role VALUE]
  [--capability VALUE] [--technique VALUE] [--readiness VALUE]
  [--provenance VALUE] [--record-set MANIFEST] [--json]
```

An omitted or whitespace-only query browses all matching families. Query and
filter text use ASCII-only case folding and ASCII whitespace collapse; other
Unicode code points are preserved. Every query token must match at least one
indexed display name, stable family ID, alias, description, controlled tag,
contract facet name, implementation display name, or contract-derived signal
token.

Per token, exact field equality scores 300, field prefix scores 200, and field
substring scores 100. Token scores add. Results order by descending score,
then the Phase 4A functional-category order, normalized UTF-8 display name,
exact family ID, revision, and content hash. The algorithm uses no locale,
clock, randomness, filesystem ordering, fuzzy matching, embeddings, or network
state.

Repeated values within one filter kind are ORed. Different non-empty filter
kinds are ANDed. Every filter value must exist in that exact projection;
unsupported values fail with `CATALOG_FILTER_VALUE_UNSUPPORTED`. In particular,
factory, repository, source, user, community, and demo labels are not musical
functions merely because they may be provenance values.

Task 030 adds `catalog.implementations.search` and the CLI form:

```text
schuss catalog objects [QUERY]
  [--function VALUE] [--abstraction VALUE] [--form VALUE]
  [--signal-domain VALUE] [--signal-rate VALUE] [--signal-role VALUE]
  [--capability VALUE] [--technique VALUE] [--readiness VALUE]
  [--provenance VALUE] [--record-set MANIFEST] [--json]
```

It uses the same normalization, closed filters, AND/OR rules, exact projection,
and deterministic scoring as family search, but returns one summary per
implementation. Provenance filtering is implementation-specific, so a tagged
implementation never tags an untagged sibling by family association. Current
catalog search, object search, and inspect commands default to Task 030; other
product command defaults remain unchanged.

## Inspection and readiness

`catalog.inspect` accepts only an exact `FAMILY_ID@REVISION` locator at the CLI
boundary; the selected record set supplies the content hash before dispatch.
There is no display-name identity, `latest`, or ambient revision discovery.
The result shows every implementation's observation/provenance source and its
exact available component-contract, binding, eligibility, and evidence
references, plus missing/unresolved facts.

Readiness is derived separately for each implementation:

| State | Required exact input |
| --- | --- |
| `catalogued-only` | Catalog membership exists and no matching component contract is reached through a binding |
| `contracted` | A matching exact binding reaches an exact component contract |
| `bound` | At least one exact implementation binding exists |
| `eligible` | An exact eligibility record for that binding has supported pair state |
| `compile-proven` | A passing level-5 evidence claim names an exact selected build-result chain for the binding |
| `device-tested` | A passing level-6 claim names the exact subject |
| `real-time-tested` | A passing level-7 claim names the exact subject and method |
| `audible-tested` | A passing level-8 claim names the exact subject and method |
| `unresolved` | The exact source records retain an unresolved question or not-evaluated state |

The accepted mixed-rate Crossfader implementation is contracted, bound,
eligible, compile-proven, and unresolved. It is not device-, real-time-, or
audible-tested. The three new reviewed slice implementations are
catalogued-only and unresolved. Evidence never promotes sibling
implementations or a whole family by association.

## Client and execution boundary

The family operations use additive operation v2 schemas. Task 030 object search
uses additive request/result v10. All three use the same pure
`dispatch_operation` API as existing operations. Direct API, raw `schuss op`,
ergonomic CLI, and future GUI/AI callers receive the same canonical result.
Human output and static Bash/Zsh/Fish completion are CLI presentation only.

No catalog operation persists state, discovers ambient records, invokes a
backend handler, lowers a graph, runs Java or ARM tools, accesses hardware, or
claims connected-device, real-time, or audible behavior. Later accepted
component, graph, and backend records remain separate inputs to the projection;
they do not change this operation boundary. Current readiness and proof gaps
are maintained in `docs/STATUS.md`.
