# ADR 0005: Separate family, component-contract, and implementation identity

- Status: accepted
- Date: 2026-08-15

## Context

Phase 4A gives musicians stable catalog families and preserves stable identity
for concrete legacy implementations. One family can contain control-rate,
audio-rate, integer, compound, or target-service realizations whose public
interfaces are not interchangeable. Family identity is therefore insufficient
as a graph node type.

## Decision

Add a target-independent component-contract identity between catalog family
and implementation binding.

- A catalog family owns discovery and presentation semantics and is never
  compiled.
- A component contract owns one exact public node interface and references one
  catalog family.
- An implementation binding realizes one exact contract revision for named
  backend/target requirements and may not redefine that interface.
- A family may have many contracts, and a contract may have many bindings.
- Phase 4A `schuss-family-*` and `schuss-implementation-*` IDs remain
  unchanged. Later binding records enrich the existing implementation identity
  with contract references rather than deriving replacement IDs.

Stable IDs contain no category path, source path, backend name, target name,
or mutable display label. Revisions and content hashes identify exact record
states.

## Consequences

Catalog grouping can remain musician-friendly without weakening graph typing.
Alternative legacy, transparent-compound, native C/C++, and target-service
realizations can share a contract only when they implement the same public
interface. Contract schemas and migration validators are required before
Phase 4B expansion can claim compiler-facing variants.
