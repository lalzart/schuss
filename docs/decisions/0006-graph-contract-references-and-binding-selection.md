# ADR 0006: Graphs reference contracts and backends select bindings

- Status: accepted
- Date: 2026-08-15

## Context

A graph must remain portable across the transitional legacy backend and a
future direct Schuss compiler. Referencing a family is under-typed; referencing
a legacy path, `.axo`, `.axp`, observation, or implementation binding couples
the graph to one realization.

## Decision

Every graph node references an exact component-contract ID, revision, and
content hash. Graph schema and target-independent type validation occur before
compute-target/backend selection and implementation binding resolution.

A backend selects an eligible binding only after the graph is valid and the
target/backend are explicit. Eligibility requires an exact contract match and
satisfied capability constraints. Explicit build-request overrides may narrow
selection but cannot bypass compatibility checks. Zero matches or unresolved
priority ties fail closed.

Transparent compound bindings may reference a graph and map the contract's
public facets to that graph's exposed endpoints. Graphs do not reference
bindings, so this does not create circular semantic ownership. Expansion is a
derived compiler stage and retains a trace from every elaborated node to its
authoritative node and compound path.

## Consequences

The same graph can use legacy or native bindings without an identity rewrite.
Backends cannot insert silent type conversions, hide ambiguity by mutating the
graph, or treat load order as selection policy. Explicit adapter nodes and
curated priorities remain inspectable authoring or binding data.
