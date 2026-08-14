# Raw legacy inventory v0

Schuss Phase 2 writes `manifest.json`, `raw/files.jsonl`, `raw/issues.jsonl`,
and `reports/summary.json`/`summary.md`. The remaining Java-resolved catalog
files belong to Phase 3 and are outside this migrated baseline.

`files.jsonl` contains one object per candidate file, sorted by
`(source_repository, path)`. Required fields are `source_repository`, `path`,
`file_type`, `size_bytes`, `sha256`, `detected_legacy_roles`, and
`parse_status`. `library_name` is the explicitly supplied portable source name.

`parse_status` is `ok`, `error`, or `not_applicable`. XML candidates are parsed
with the standard library solely to establish well-formedness and the root
element. Java generator sources are not parsed as Java and therefore use
`not_applicable`. Every parse or read failure also emits a structured issue.
For an unreadable candidate, `size_bytes` and `sha256` are `null`; the record is
retained with `parse_status: "error"`.

Hashes cover the exact source bytes. Paths use `/` separators and are relative
to the supplied source root. No canonical IDs, generated UUIDs, dependencies,
or semantic classifications are inferred in Schuss Phase 2.

Normalized files have UTF-8 encoding, LF endings, sorted keys, compact JSONL,
and a trailing newline. The manifest intentionally has no timestamp by default.
The validator checks schemas, ordering, path portability, hashes, issue
reconciliation, and summary counts. Repeated runs against identical bytes and
Git state must be byte-identical.

The summary additionally reconciles counts by source and extension and lists
source-relative paths that occur in more than one explicitly named source.

## Retained traversal caveat

The migrated v0 scanner prunes directories named `build`, `dist`, `out`, or
`target` at every depth. At the locked commits, `dist` and `out` also occur as
legitimate object-category names. It also uses `Path.suffix`, which does not
recognize the legacy-valid filename `objects/rbrt/.axo`. Comparing the locked
Git trees with the retained snapshot identifies 146 omitted candidates: 143
`.axo`, two `.axs`, and one `.axp`. Phase 2 remains immutable evidence for the
scan it actually performed; Phase 3 loads those legacy candidates and reports
each omission explicitly during reconciliation.
