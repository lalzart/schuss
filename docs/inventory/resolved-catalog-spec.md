# Java-resolved legacy inventory v0

Schuss Phase 3 writes a factual observation snapshot under
`catalog/snapshots/legacy-resolved-catalog-v0/`:

- `manifest.json` records the pinned inputs, ordered object roots, Java runtime
  fingerprint, and side-effect policy;
- `resolved/objects.jsonl` records every observed object-definition variant;
- `resolved/graphs.jsonl` records serialized graph structure together with
  post-construction resolution outcomes;
- `resolved/issues.jsonl` records deterministic structured diagnostics; and
- `reports/summary.json` and `summary.md` reconcile the resolved observations
  with the retained Phase 2 raw snapshot.

The corresponding schema versions are `legacy-resolved-catalog-v0`,
`legacy-resolved-object-v0`, `legacy-resolved-graph-v0`,
`legacy-resolved-issue-v0`, and `legacy-resolved-summary-v0`. These are bridge
records, not the final Schuss object or graph model.

## Execution boundary

The exporter synchronously loads only explicitly configured, pinned source
roots. Durable records use portable source IDs and source-relative `/` paths;
absolute checkout paths remain local configuration. The manifest fingerprints
the Java class path actually used and binds the export to the Phase 2 manifest
and file-record bytes.

The legacy `.axs` path projects a resolved subpatch into an object interface.
This operation is named `subpatch_interface_projection` in the manifest and
object records. It may invoke the legacy method named `GenerateAxoObj`, but it
is not target artifact generation: it derives the subpatch's inlets, outlets,
parameters, attributes, displays, dependencies, includes, and code-section
presence in memory. Phase 3 does not generate a target `.axp` or C++ artifact,
invoke `GenerateCode3`, compile or link ARM code, access a device, or write
preferences. The manifest therefore records
`subpatch_interface_projection: true`, `target_artifact_generation: false`,
and `target_compilation: false` as separate facts.

Generator provenance is recorded only when an emitted object is observed
through an explicit provider seam or a verified provider-to-output mapping.
The presence of a generator Java source does not establish which objects it
emits. Production export must not invoke a generator that writes into an
upstream checkout.

## Object observations

`variant_index` is the snapshot-local observation reference. It is consecutive
in deterministic load order and is not a Schuss semantic object ID. The bridge
captures each definition occurrence before legacy `ObjectList.contains()` or
UUID-map replacement can collapse it. `legacy_object_list_index` separately
records whether and where the current Java collection retained the occurrence.

Each record keeps the legacy class and ID, a strict file/provider/unresolved
origin, direct description/author/license/help evidence, and these distinct
facets:

- ordered inlets, outlets, parameters, attributes, displays, and modulators;
- declared includes, dependencies, and SD-file dependencies; and
- presence of every current and deprecated code section as `absent`, `empty`,
  or `nonempty`, without exporting the code body.

Common facet fields are `index`, `name`, `legacy_type`, `description`,
`no_label`, `data_type`, `length`, and ordered typed `legacy_properties`.
Fields that do not apply to a facet are `null`; the arrays themselves are
always present. A versioned exporter allowlist must reject an unhandled legacy
facet type or property with an issue and mark the object `partial` rather than
silently omit it.

### UUID observation

The exporter reads source UUID presence before any call that can memoize a
generated value. Explicit source UUIDs use `runtime_kind: "explicit"` and are
retained as `durable_value`. The legacy normal-object generator uses a random
UUID, so an absent source UUID is represented deterministically as:

```json
{
  "source_presence": "absent",
  "source_value": null,
  "runtime_kind": "generated-nondeterministic",
  "durable_value": null
}
```

The concrete random value is intentionally excluded from durable artifacts.
Legacy sentinel values such as `unloaded` use `runtime_kind: "sentinel"`.
Comment and hyperlink definitions have an observably absent source UUID and a
legacy `GenerateUUID()` that returns null. They use `source_presence:
"absent"` with `runtime_kind: "unavailable"`; that combination is complete
evidence and does not itself require an issue. Truly unobservable UUID state
uses `source_presence: "unobservable"` with the same runtime kind and requires
a partial record and an issue.

## Graph observations

Graph files are deserialized first and their instance order, requested type
identity, parameter and attribute values, nets, and requested endpoints are
captured before `PostContructor()` mutates the model. The resolver then runs and
the exporter overlays:

- post-resolution instance and net indexes;
- UUID, global-name, relative `.axo`, or relative `.axs` resolution method;
- every ordered candidate and the candidate selected by legacy behavior;
- unambiguous, ambiguous, unresolved, unsupported, and zombie status;
- serialized hard zombies versus zombies created during resolution; and
- resolved, missing-instance, missing-port, or not-evaluated endpoint status.

This two-stage capture is mandatory because unresolved instances are replaced
and appended as zombies, while a missing net endpoint can cause the legacy
model to remove the entire net before later endpoints are evaluated.

An ambiguous lookup retains both the ordered candidates and the legacy
selection for compatibility evidence, but the instance and graph remain
`partial`; the selected candidate is not promoted to an unambiguous Schuss
resolution. Relative objects outside the ordered catalog use a portable
graph-local file reference rather than an absolute Java path.

Inline `patcher` and `patchobj` instances replace a generic catalog type with a
definition embedded in that graph instance. Version 0 has no nested embedded
definition identity, so it records the independently found generic candidates
but leaves `legacy_selected` null and emits `INSTANCE_RESOLUTION_UNPROVEN`.
Claiming that the generic catalog object was selected would be false evidence;
a future schema may add a typed graph-local embedded-definition reference.

Parameter values are recorded as signed raw `int32` or `frac32` values along
with source/default/zombie status, presets, MIDI metadata, and modulation
assignments. Attribute values are typed `int32` or string observations.
Displays are definitions and runtime readouts; Phase 3 does not invent a
serialized display value.

## Issues and fail-closed behavior

Issues have a stable stage and code, a portable structured location,
deterministic message text, sorted typed facts, and ordered candidate indexes.
Stages include `subpatch-interface-projection` separately from object and graph
resolution. Messages must not contain absolute paths, stack traces, timestamps,
random UUIDs, or environment-specific temporary names.

Ambiguous identity, unsupported classes or properties, unresolved provenance,
missing references, and nonportable values mark the affected record partial or
failed. They do not prevent unrelated records from exporting. Schema drift or
an invalid source configuration fails the overall validation.

## Null and unknown rules

- Arrays are required and use `[]` when no items were observed.
- `null` means that a defined optional legacy scalar was absent, a field does
  not apply, or no resolution target exists.
- An explicit empty string is preserved as `""` and is not converted to null.
- Free-form `"unknown"` values are forbidden. The schemas use explicit
  `unresolved`, `unsupported`, `unavailable`, or `not_evaluated` states, each
  accompanied by an issue when evidence is incomplete.
- Missing author or license remains null. Repository ownership and paths do not
  supply per-object license or provenance claims.

## Deterministic serialization

- Object records are written by consecutive `variant_index` in configured root
  order, legacy file traversal order, and definition/provider emission order.
- Graphs are sorted by `(source_id, path)` and assigned consecutive
  `graph_index` values.
- Instances, nets, endpoints, and list-backed facets preserve observed order.
- Set-backed includes and dependencies use Unicode code-point order.
- Issues are sorted by portable location, stage, code, and candidate indexes,
  then assigned consecutive `issue_index` values.
- Summary rows are sorted by their complete key tuple.
- JSON objects use sorted keys. JSONL is compact UTF-8 with LF endings and a
  trailing newline; formatted JSON uses two-space indentation and a trailing
  newline. No generated file contains a timestamp.

Two fresh Java processes given identical bytes, source order, and runtime
fingerprint must produce byte-identical artifacts.

## Reconciliation

The summary reports raw candidates, object-file load outcomes, definition
occurrences, retained and collapsed legacy variants, UUID/provenance classes,
name-overload and duplicate-UUID groups, graph and zombie outcomes, net and
endpoint outcomes, and issues by severity, stage, and code.

Because the retained raw v0 scanner omitted legacy-valid candidates,
object-file and graph summaries separately report Phase 2 raw candidates,
configured-but-not-enabled candidates, Java-attempted candidates, and locked
candidates absent from the raw baseline. Catalog `.axs` placeholders have a
separate reconciliation block because the same files are also graph inputs.
Every such absence emits a portable `RAW_BASELINE_OMISSION` issue. For object
files, `attempted = raw_candidates - not_enabled + not_in_raw_baseline`; graph
`candidates = raw_candidates + not_in_raw_baseline` because every locked graph
source is scanned; and catalog subpatch `registered = raw_candidates -
not_enabled + not_in_raw_baseline`.

The validator additionally proves:

1. object `variant_index` and graph/issue indexes are consecutive;
2. object records equal complete plus partial object counts;
3. every object has file, provider, or explicitly unresolved provenance;
4. unresolved provenance and every partial/failed observation have matching
   issues;
5. graph candidates equal complete plus partial plus failed graph counts;
6. nested instance, zombie, net, endpoint, and issue counts reconcile exactly;
7. every cross-record index exists and every portable source path hashes to its
   Phase 2 candidate; and
8. no durable string contains a configured absolute checkout root.

Physical `.axo` file count is not expected to equal resolved object count: one
file can contain multiple definitions, and an explicitly observed provider can
emit multiple objects.

## Retained v0 census

The retained snapshot contains 3,602 object records and 1,157 graph records.
Objects comprise 3,551 file-backed observations and 51 provider-only
observations. Graph outcomes are 348 complete, 805 partial, and four failed.
The 3,180 issues are evidence, not a validation failure: they include 146 raw
baseline omissions, 265 ambiguous instance resolutions, 1,945 explicitly
unproven selections, 365 zombie observations, 33 missing endpoint ports, and
125 graphs whose nonportable serialized values were explicitly redacted. The
machine-readable summary remains authoritative for the complete breakdown.
