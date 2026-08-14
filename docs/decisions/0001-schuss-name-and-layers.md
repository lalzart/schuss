# ADR 0001: Schuss name and independent layers

- Status: accepted
- Date: 2026-08-14

## Decision

The platform is named **Schuss**. Gills names a device profile and instrument
platform within Schuss. Ksoloti Core names the initial compute target and
legacy backend.

Compute target, device profile, instrument, DSP graph, and backend remain
independent layers.

## Consequences

Schuss can preserve Ksoloti compatibility without binding its domain model to
one board. Gills instruments can be designed from the panel inward without
making their musical identity synonymous with a patch file or compute target.
