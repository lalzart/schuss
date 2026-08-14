# Legacy content sources

The raw exporter accepts explicit `NAME=PATH` sources. It does not discover or
mutate user preferences. Each source is scanned independently and identified in
output only by its supplied portable name and repository-relative path.

For every source, the manifest records the Git top-level directory (as a
portable basename), remote URL, commit, branch, dirty state, and detected
repository license files when Git metadata is available. Dirty trees are never
cleaned. A source outside Git is reported as such.

Traversal does not follow directory or file symlinks. The resolved output
directory is excluded when it is inside a source. Directories named `.git`,
`.gradle`, `__pycache__`, `build`, `dist`, `out`, or `target` are pruned
case-insensitively as repository metadata or generated build output. Candidate
extension and path-role matching are case-insensitive. Duplicate source names
are rejected. An unreadable candidate or directory produces an issue and does
not abort the remaining scan.

Candidate roles are factual and extension-based:

| Input | Raw role |
|---|---|
| `.axo` | native object source; may contain multiple `objdef` elements |
| `.axs` | legacy subpatch graph and lazy catalog candidate |
| `.axp` | legacy patch graph |
| `src/main/java/generatedobjects/*.java` | Java generator source |

Files beneath directories named `help`, `example(s)`, `patches`, or `demo(s)`
gain an additional detected role. Case-insensitive `help`, `example`, or `demo`
filename tokens separated by punctuation, whitespace, or underscores are also
recognized. This is provenance only, not a functional category. Embedded
elements are recorded only as raw XML observations in later resolved phases.

Recommended invocation from the Schuss checkout, writing to a scratch
directory rather than over the retained snapshot:

```bash
KS_SOURCE_ROOT=/absolute/path/to/ksoloti/1.1.0

python3 tools/inventory/export_raw_inventory.py \
  --output /tmp/schuss-legacy-catalog-v0 \
  --source patcher=/absolute/path/to/ksoloti \
  --source axoloti-factory="$KS_SOURCE_ROOT/axoloti-factory" \
  --source ksoloti-objects="$KS_SOURCE_ROOT/ksoloti-objects" \
  --source ksoloti-contrib="$KS_SOURCE_ROOT/ksoloti-contrib" \
  --source axoloti-contrib="$KS_SOURCE_ROOT/axoloti-contrib"
```

Absolute roots are used only while reading. They are never serialized.

The Java records prove only that generator source files exist. Schuss Phase 2 does not
execute those generators or count their emitted catalog objects. The later
Java-resolved exporter must enumerate the actual generated objects through the
legacy model and retain generator-to-object provenance separately.
