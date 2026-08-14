# ADR 0003: Inventory facts before semantics

- Status: accepted
- Date: 2026-08-14

## Decision

Legacy ingestion is staged. First record portable source identity, paths,
bytes, and parse outcomes. Then record Java-resolved objects and graphs. Curate
function, preferred objects, and the final Schuss schema only after those
factual layers are reproducible.

## Consequences

Raw inventory may retain path-derived roles such as help or example, but it may
not infer musical function, license, quality, or compatibility. Duplicate and
unresolved content stays visible instead of being normalized away.
