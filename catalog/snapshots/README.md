# Catalog snapshots

Each directory is a retained, versioned inventory baseline. Snapshots contain
portable source IDs and byte-level observations, never absolute checkout paths.
New phases create new directories rather than rewriting earlier evidence.

`legacy-catalog-v0/` is the migrated raw-file baseline. Its manifest records
that the patcher source was dirty when observed, so internal hash validation is
stronger than a claim that the pinned commit alone regenerates every byte.
Its original traversal also pruned semantic `dist` and `out` category
directories and missed a legacy-valid file named `.axo`; the Phase 3 resolved
snapshot reconciles the resulting 146 candidate-file omissions without
rewriting this retained baseline.

`legacy-resolved-catalog-v0/` is the Phase 3 Java-resolved baseline. Its
manifest binds the pinned sources, Java runtime fingerprint, ordered roots,
Phase 2 evidence, and side-effect policy. Its JSONL streams retain ordered
object variants, graph/post-construction outcomes, and structured issues; its
reports reconcile 3,602 objects and 1,157 graphs with the raw candidate
universe. See `reports/summary.json` for the authoritative complete, partial,
failed, ambiguity, zombie, net, endpoint, and issue counts.

This directory is frozen evidence. Phase 3 review and Phase 4 classification
must write separate derived artifacts; they must never revise these files in
place.
