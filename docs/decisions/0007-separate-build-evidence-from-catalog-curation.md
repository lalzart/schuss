# ADR 0007: Separate build evidence from catalog curation

- Status: accepted
- Date: 2026-08-15

## Context

Legacy observation, schema validation, lowering, ARM linking, device execution,
real-time measurement, and listening tests establish different facts. A build
result is also tied to exact graph, target, backend, binding, toolchain, and
firmware states. Treating it as catalog truth would make classification depend
on mutable build state and would overstate evidence.

## Decision

Build requests, build results, artifacts, diagnostics, resource reports, and
evidence claims are separate immutable records. A result binds exact input
revisions and hashes, selected implementation bindings, toolchain and firmware
ABI identity, options, output hashes, diagnostics, and stage outcomes. Separate
level-specific evidence records point to the immutable result, stage, or
artifact; the result does not point back to them.

No evidence level implies another. Build results never rewrite catalog
families, contract semantics, implementation preference, or compatibility
claims. A separate reviewed curation action may cite immutable evidence and
create a new semantic-record revision.

## Consequences

Structural validation cannot be reported as ARM, device, real-time, or audible
proof. Reproducible builds remain traceable without making logs, timestamps, or
machine-local paths semantic identity. Compatibility promotion becomes an
explicit, reviewable decision rather than a side effect of invoking a backend.
