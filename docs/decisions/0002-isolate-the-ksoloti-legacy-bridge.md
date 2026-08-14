# ADR 0002: Isolate the Ksoloti legacy bridge

- Status: accepted
- Date: 2026-08-14

## Decision

Ksoloti Java resolution, Swing/global-state compatibility, legacy XML emission,
and existing compiler invocation are isolated under `legacy/ksoloti-bridge/`.
Core Schuss models do not depend on legacy Java classes.

## Consequences

The existing firmware, object ecosystem, and ARM toolchain remain useful while
Schuss develops independently. The bridge must translate into versioned data
and preserve diagnostics; it cannot become the implicit domain model.
