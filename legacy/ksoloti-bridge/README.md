# Ksoloti compatibility bridge

This boundary contains the code that interacts directly with the legacy
Ksoloti Java object model, patch resolver, XML format, and generated-object
providers. New Schuss code must not depend directly on those classes.

The Phase 3 implementation is a synchronous, device-free exporter for ordered
catalog objects and compound graphs. Its behavioral source matrix lives under
`fixtures/resolved-inventory/`; the record and evidence contract is documented
in `docs/inventory/resolved-catalog-spec.md`.

The bridge may perform the named in-memory subpatch-interface projection needed
to observe runtime ports. It does not generate target artifacts, compile or
link ARM code, access a device, write preferences, or mutate the upstream
checkouts. The production harness builds and reads Git archives of the pinned
commits, runs two fresh JVMs, and requires byte-identical output.

Code outside this directory must consume versioned Schuss records rather than
legacy Java or Swing objects.
