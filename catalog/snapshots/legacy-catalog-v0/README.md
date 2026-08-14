# Legacy catalog v0 snapshot

This directory preserves the raw Ksoloti inventory that predates the Schuss
repository scaffold. The files, issues, manifest, and summaries were copied
byte-for-byte; the exporter, validator, tests, and schemas were retained in
their corresponding Schuss locations.

The snapshot records 4,209 candidate files:

- 3,017 `.axo` native-object candidates;
- 160 `.axs` subpatch candidates;
- 994 `.axp` patch candidates; and
- 38 generated-object Java source candidates.

There are two retained XML parse issues. They are source observations, not
snapshot corruption.

The patcher source was dirty at observation time. Each candidate has a byte
hash, so the snapshot is internally auditable, but the pinned patcher commit by
itself is not claimed to regenerate every observed candidate byte.
