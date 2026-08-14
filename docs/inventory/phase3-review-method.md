# Phase 3 inventory review method v0

The Phase 3 review packet is a deterministic derivative of the frozen
`legacy-resolved-catalog-v0` snapshot. It does not change that evidence and it
does not add functional classifications.

## Evidence references

Review reports use snapshot-scoped references such as
`legacy-resolved-catalog-v0:object:123` and
`legacy-resolved-catalog-v0:graph:456`. Source-file references use a complete
SHA-256 of the portable source ID and relative path. These references are
stable inside the frozen snapshot but are not final Schuss item IDs.

## Unique affected items

An issue's direct affected record is selected in this order:

1. its object `variant_index`;
2. its graph `graph_index`, including instance, net, and endpoint issues;
3. its portable source ID and relative path; or
4. the global inventory when no narrower record exists.

`unique_location_count` retains the finer object, graph, instance, net, and
endpoint location tuple. `implicated_object_refs` separately includes every
candidate variant named by an issue. Material-impact totals union direct
records with those implicated candidates so overload and ambiguity review does
not count only the first catalog variant.

Issue counts, direct record counts, detailed location counts, and implicated
candidate counts therefore answer different questions and must not be
substituted for one another.

## Impact policy

The versioned `phase3-review-impact-v0` policy assigns each observed issue code
one of four review levels for taxonomy, migration, and compilation readiness:

- `none`: no direct interference for that workflow;
- `context`: preserve or down-weight the evidence, but do not block the item;
- `material`: explicit handling or review is required before relying on it; and
- `blocking`: the current evidence is insufficient for that workflow on the
  affected item.

These levels are engineering judgment. In particular, compilation readiness
does not mean that target code generation, ARM compile/link, device execution,
or listening tests occurred.

## Deterministic samples

Samples use `sha256-rank-v1` with the public seed
`schuss-phase3-inventory-review-v0`. The seed, cohort name, and evidence
reference are separated by NUL bytes and hashed; the 25 lowest hashes are
selected.

The representative-object sample first selects one hash-ranked object from
each observed `(origin kind, legacy kind, source ID)` stratum, then fills the
remaining positions by global hash rank. Complete and partial graph samples are
ranked independently. The overload sample is drawn only from instance
resolutions that retain more than one catalog candidate and have legacy status
`ambiguous`.

## Frequency boundary

Complete graphs may initially provide strong object-reference-frequency
evidence. References from partial graphs remain usable only with lower
confidence and their complete reason-code set. Failed graphs provide source
presence and failure evidence, not resolved frequency evidence.

## Portability and immutability

The packet manifest records the SHA-256 and portable relative path of every
frozen snapshot input and every generated packet file. The generator checks the
snapshot hashes before and after two fresh report generations. The validator
rejects undeclared files and scans both snapshot and packet for common macOS,
Unix, temporary-directory, and Windows user-home path forms.
