# Component, binding, and DSP-graph contracts

This document is normative for the Task 006 `component-contract-v0`,
`implementation-binding-v0`, and `dsp-graph-v0` boundaries. It also documents
the narrow `catalog-family-companion-v0` exact-identity envelope used to bind
the retained Phase 4A Crossfader family without inventing a legacy family
revision or changing its classification.

## Ownership and reference direction

```text
legacy observation <- implementation binding -> exact component contract
                                                   -> exact family companion

instrument -> exact DSP graph -> exact component contracts

transparent binding -> exact DSP graph -> exact component contracts
```

A family owns browsing identity and classification. A component contract owns
one target-independent public node type. A binding owns the correspondence
between that type and one realization. A graph owns semantic implementation
structure. The graph therefore references contracts only: it contains no
family, implementation, observation, path, target, backend, device, Gills,
compiler-artifact, or canvas identity.

## Exact Crossfader family closure

`schuss-family-000018` revision 1 is an identity-only companion around the
single exact Phase 4A overlay member. Its source closure includes the overlay
ID and raw SHA-256, member schema and canonical member SHA-256, and frozen
legacy manifest SHA-256. The validator resolves exactly one overlay member and
checks all of those values. The companion does not copy presentation or
taxonomy fields and declares `semantics_changed: false`; its revision is the
new companion record's revision, not a fabricated revision of the legacy
overlay member.

## Component contracts and types

The three production contracts all reference that exact family companion but
have independent nominal identities because their public signatures are not
interchangeable:

| Contract | `a`, `b` | `fade` | `out` |
| --- | --- | --- | --- |
| `schuss-component-contract-000001` r1 | control | control | control |
| `schuss-component-contract-000002` r1 | audio | audio | audio |
| `schuss-component-contract-000003` r1 | audio | control | audio |

All four facets use stable contract-local IDs and a signed 32-bit,
two's-complement fixed-point representation with 27 fractional bits. Audio and
generic signal ranges are normalized `-1` through `1`; `fade` is normalized
`0` through `1`. Each port type separately declares domain, rate, channel
shape, connection cardinality, semantic role, representation, unit, valid
range and overflow policy, optionality/absence behavior, and ownership,
borrowing, lifetime, capacity, synchronization, and aliasing.

Ports, parameters, attributes, actions, displays, state declarations, and
lifecycle are separate schema fields and semantic namespaces. A public
signature change requires a new contract ID; a revision cannot disguise a
different public signature. The bounded v0 schema requires capability and
compatibility-claim collections to be empty; Task 007 owns the first accepted
capability vocabulary, and no compatibility relation is inferred.

Direct graph connections are deliberately strict. Domain, rate, channel
shape, semantic role, representation, unit, and ownership must match exactly.
The source valid range may equal or be a subset of the destination range with
compatible inclusive bounds and the same overflow policy. No implicit rate,
channel, representation, unit/range, ownership, event/payload, or facet-kind
conversion is performed. An unconnected inlet is valid only when its contract
explicitly declares optionality, absence behavior, and a default.

## Legacy companion bindings

The production bindings retain the Phase 4A implementation IDs and bind each
public contract facet exactly once:

| Implementation | Contract | Frozen observation | Shape |
| --- | --- | --- | --- |
| `schuss-implementation-000026` r1 | control | object 458 | scalar `Frac32`, positive scalar fade |
| `schuss-implementation-000027` r1 | audio | object 459 | buffer `Frac32`, positive buffer fade |
| `schuss-implementation-000028` r1 | mixed | object 460 | buffer signals, positive scalar fade |

Each locator checks the exact manifest, evidence reference, variant index,
legacy UUID, portable source ID, source SHA-256, ordered seam index/name, legacy
class, and datatype. These records prove only a structural legacy seam map.
Their `selection_state` remains `not-evaluated` and owned by Task 007; they
make no target compatibility, build eligibility, or preference claim.

## Production graph and instrument migration

`schuss-graph-000001` revision 1 contains one node referencing the exact mixed
Crossfader contract. Public audio ports `a`, `b`, and `out` expose the matching
node ports. Public parameter `graph-facet-000001`, semantic key `blend`, has an
exact normalized `0` to `1` domain and default `0.5`. Its binding to the
control-rate `fade` inlet declares the exact source and destination domains,
ordered linear transform, control-cycle update boundary, graph-owned linear
smoothing completed at the next control cycle, and exclusive driver policy.
The graph needs no internal cable; connection semantics are exercised by
focused two-node fixtures rather than unrelated production components.

`schuss-instrument-000001` revision 2 replaces only the deferred graph branch
with the exact graph ID/revision/hash tuple. It retains the device reference,
instrument parameter, device mapping, and graph mapping. Revision 1 remains
byte-identical and truthfully deferred. The extended Task 005 validator accepts
an explicit graph-target registry, validates the exact tuple and public
`blend` kind/domain, and continues to validate revision 1 from its closed
deferred target declaration.

## Transparent compounds

A transparent compound contract owns its public facets and stable mapping
keys. Its implementation binding references one exact graph and maps every
public runtime facet to one graph mapping key. The graph maps those keys to
inspectable node facets. Validation requires the three key sets to be total
and equal, the mapped kinds and port types to agree, exact graph and contract
references, and an acyclic expansion graph. Non-production fixtures prove the
positive case plus missing, duplicate, incompatible, hidden, direct-recursive,
and indirect-recursive failures. No opaque legacy subpatch is introduced.

## Validation and evidence boundary

Run the aggregate validator and all contract tests with:

```bash
python3 tools/contracts/validate_component_graph_contracts.py
python3 -m unittest discover -s tools/contracts/tests
```

Validation is read only. It checks closed schemas, portable restricted JSON,
canonical hashes, ID/revision uniqueness, exact family/contract/graph closure,
types, topology, cardinality, exposures, parameter policies, binding seam maps,
transparent compounds, and instrument graph targets. Diagnostics and summary
ordering are deterministic; fresh processes emit byte-identical canonical
records and summaries.

Passing establishes structural/schema, exact-reference,
target-independent-type, legacy-seam-map, and instrument graph-target evidence.
It does not select a binding or backend, lower or generate an artifact, invoke
Java, compile or link ARM code, access hardware, measure real-time resources,
or establish audible behavior. Those evidence levels remain `not-run`.

## Deferred decisions

| Decision | Owner | Earliest task |
| --- | --- | --- |
| Compute-target and backend capability vocabularies and exact compatibility claims | Target/backend owners | Task 007 |
| Binding selection, toolchain/ABI identity, build request/result, artifact, resource, and evidence records | Build/backend owners | Task 007 |
| Shared graph mutation operations and client protocol | Domain-operation owner | Task 008 |
| Legacy `.axp` lowering and ARM compile/link proof | Compiler/backend owner | Task 009 |
| Broader reviewed-core contracts and bindings | Catalog and contract owners | Task 011 |
| Physical Gills facts, real-time validation, and listening evidence | Device/evidence owners | Later bounded hardware tasks |

Task 007 should add only compute-target, backend-capability, build-request,
build-result, artifact, resource-report, and level-specific evidence schemas
and validators. It must consume the exact Task 006 contracts without adding
compiler lowering, graph operations, GUI/CLI behavior, or hardware claims.
