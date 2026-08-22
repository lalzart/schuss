# Task 033 later Settings and Objects UI brief

Status: requirements only. This is not an active UI task and opens no client
allowlist.

## Goal

Give a musician one compact, function-first view of installed collections,
exact provenance, and target-specific implementation readiness without moving
catalog, graph, provider, or project authority into the renderer.

## Shared data boundary

The UI must consume the accepted v18 shared operations:

- `collections.inspect`, with one explicit non-semantic
  `collection-profile-v0`; and
- `implementation.availability.inspect`, with one exact catalog
  implementation locator and explicit target/backend references.

The existing profile is request context, not a durable project record. Phase 2
defines no mutation operation. A later settings-write task would need a
separately authorized, atomic, path-safe local preference operation; renderer
filesystem access or an ad hoc second store is prohibited.

## Minimum surfaces

### Settings: Collections and providers

- List each exact collection version and enabled-for-discovery state.
- Show installed source/provider references, missing prerequisites, use
  context, and license/distribution-review state without implying support.
- Show Desktop Host and Ksoloti availability independently.
- Make local ordering and enablement visibly presentational. Disabling a
  collection must never remove a graph node or rewrite a project.

### Objects drawer and inspector

- Browse by musical function and filter by provenance, collection,
  implementation form, and selected-target readiness.
- Keep family, catalog implementation, component contract, binding,
  eligibility, provider, and evidence details distinguishable in inspection.
- Display the authoritative accepted/Core state after an operation; raw input
  or optimistic renderer state is not truth.
- When an implementation cannot run, show its exact diagnostic and missing
  dependency. Never silently substitute another family member or provider.

### Project dependency view

- Show the exact implementations and providers needed by the saved project.
- A disabled discovery collection may hide an item from browsing but cannot
  make an accepted project incomplete.
- Provide no destructive “disable and remove from graph” combined action.

## Presentation constraints

Avoid a global “compatible” badge and permanent Factory, Mutable, JUCE, user,
or community drawer roots. Use compact separate labels for catalogued,
contracted, bound, eligible, compile-proven, device-tested, real-time-tested,
audible-tested, unresolved, and the selected target/backend.

Keyboard, CLI, desktop, and AI clients must receive the same canonical
operation result shapes. The UI may decide layout, density, disclosure, focus,
and accessibility behavior; it must not decide identity, selection priority,
compatibility, source/license truth, or evidence promotion.

## Acceptance boundary for a later task

A later UI contract must register operation-adapter tests, canonical-state
rendering tests, inaccessible/keyboard states, stale-profile and
missing-provider diagnostics, and a visual review. It must separately authorize
any local settings mutation. Task 033 performs no React/Tauri edit, app launch,
device access, or visual validation.
