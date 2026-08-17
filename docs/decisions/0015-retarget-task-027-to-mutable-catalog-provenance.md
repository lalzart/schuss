# ADR 0015: Retarget Task 027 to Mutable-related catalog provenance

- Status: accepted
- Date: 2026-08-17
- Supersedes: ADR 0014 only for the unstarted Task 027 assignment

## Context

ADR 0014 reserved Task 027 for application sessions, jobs, and diagnostics.
That work never started. After Tasks 024-026 completed, the user explicitly
assigned Task 027 to a bounded catalog integration of Mutable
Instruments-related Ksoloti objects. The new request is narrower than a second
catalog/compiler tranche and requires no session, job, compiler, device, or UI
semantics.

Task 024's primary source corpus indexed the pinned `axoloti-factory` and
`ksoloti-objects` libraries but did not index the separate 19-object library at
`ai/sdk/ksoloti-extended` inside the already pinned Ksoloti patcher commit.
Factory Mutable-derived candidates, including two Warps wrappers, were present
as source candidates but were not all reviewed catalog implementations.

## Decision

Task 027 is retargeted to Mutable-related catalog provenance and exact
extended-library review. The original application sessions, jobs, and
diagnostics outcome is deferred and receives no replacement task number in
this decision. Task 028 remains the planned second catalog/compiler and
transparent-compound tranche; Task 027 does not consume or broaden it.

Task 027 must preserve the sixty reviewed catalog families and the thirteen
function-first categories. Mutable Instruments ancestry is an additive
provenance tag attached only to exact source-backed candidates or
implementations. It is never a musical category, family hierarchy, readiness
state, preferred status, or compiler claim.

The exact Ksoloti extended tree is read from the locked `patcher` Git commit.
Ambient working-tree changes are excluded. Extended objects may become
implementations of an existing family only where the reviewed family meaning
is equivalent. All other objects remain exact candidates with their review
disposition and proof gaps retained.

## Consequences

Catalog search can filter reviewed families by the exact
`mutable-instruments-derived` provenance tag without moving those families out
of their ordinary functional categories. Candidate source presence remains
separate from catalog implementation membership, component contracts,
bindings, compiler or ARM support, connected-device behavior, real-time
fitness, audible behavior, preference, and release readiness.

The original sessions/jobs work remains available for a future explicit
planning decision. This decision authorizes no Java or legacy `.axp` run, ARM
build, hardware action, staging, commit, push, or publication.
