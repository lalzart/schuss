# Device-profile and instrument contracts

This document is normative for the Task 005 `device-profile-v0` and
`instrument-v0` records. It implements only the physical-device and musical-
instrument boundary accepted by Task 004. Component contracts, DSP graphs,
implementation bindings, targets, backends, builds, compiler behavior, GUI
models, firmware, and hardware access remain outside these two schemas. Task
006 graph and component ownership is defined separately in
`docs/COMPONENT_GRAPH_CONTRACTS.md`.

## Ownership and reference direction

The dependency direction is:

```text
instrument -> exact device-profile revision
instrument -> historical deferred graph intention or exact graph revision
```

A device profile owns physical input controls, gestures, feedback outputs,
displays, physical I/O, and unresolved physical facts. It never owns a graph,
instrument behavior, implementation, target, backend, firmware, or legacy
patch.

An instrument owns musical parameters, actions, read-only displays, state
declarations, and mappings. It references a device profile instead of copying
physical slots, and references a graph instead of copying nodes, ports, nets,
implementation source, or generated content. Device input mappings terminate
at instrument facets. A separate graph mapping starts at an instrument facet;
there is no device-to-graph shortcut.

The production records are stored by family:

```text
contracts/
├── device-profiles/gills-minimal-v0.json
└── instruments/blend-reference-v0.json
```

## Identity and canonical content

Both record families use a closed common logical envelope:

- an exact `schema_version`;
- `canonical_profile: schuss-canonical-json-v1`;
- an opaque numeric stable entity ID;
- a positive entity `revision`; and
- `content_hash` as `sha256:` followed by 64 lowercase hexadecimal digits.

`schuss-device-profile-NNNNNN`, `schuss-instrument-NNNNNN`, and each local
numeric slot/facet namespace are allocation identifiers. Labels, category,
layout, order, paths, targets, and backend names do not determine them. One
stable-ID/revision pair may resolve to only one content hash. Any semantic
content change, including a stored display-label change, requires a new
revision and hash while retaining the stable entity ID.

`schuss-canonical-json-v1` is intentionally restricted to the values these two
schemas need:

1. JSON member names are unique and input is UTF-8 with LF endings.
2. Booleans, strings, arrays, objects, and exact I-JSON-range integers are
   accepted. Floating-point JSON numbers, non-finite numbers, and oversized
   integers fail closed. Fractional semantic values use schema-defined exact-
   decimal strings.
3. The record's own top-level `content_hash` is omitted; nested reference
   hashes remain in the digest input.
4. Every array schema declares `x-schuss-array-kind` as `set` or `sequence`.
   Set elements are recursively canonicalized and sorted by their UTF-8
   canonical bytes. Sequence order is preserved.
5. The normalized value is serialized with the RFC 8785-compatible JSON form
   for this restricted value space, then its UTF-8 bytes are hashed with
   SHA-256.

The two-point mapping curve is an ordered semantic sequence. Reversing its
points changes canonical bytes and fails the increasing-source transform
rule. Entity collections, mappings, evidence references, and unresolved-fact
subjects are sets, so source-array reordering does not change their canonical
bytes.

Timestamps, UUID-shaped random identifiers, machine-local absolute paths, and
mutable text in stable-ID fields fail validation. Repository-relative evidence
locators may appear only in their declared evidence fields.

## Device profile v0

The schema keeps these collections separate even when they are empty:

- `input_controls`: absolute, relative, and discrete input slots;
- `gestures`: derived events referencing named input-control slots;
- `feedback_outputs`: indicator or haptic slots directed from instrument to
  device;
- `displays`: read-only device presentation slots directed from instrument to
  device;
- `physical_io`: physical audio, MIDI, CV, or generic I/O slots; and
- `unresolved_facts`: closed question/evidence records for physical facts that
  are not yet supported.

Every slot and gesture has an opaque type-specific local ID. Input controls
separate kind, physical form, logical output domain, logical range, physical
range, and resolution. A physical range, resolution, recognition rule, or
capability is either tagged `known` with its exact payload or tagged
`unresolved` with a reference to a complete unresolved-fact record. No bare
null or guessed default is permitted.

The minimal Gills profile declares only `device-input-000001`, an absolute
knob with a normalized `0` to `1` authoring-domain contract. The record does
not claim a complete panel. Its electrical/physical range and resolution are
owned by `unresolved-fact-000001`, which records the question, rationale,
owner, earliest later task, evidence status, and empty accepted-evidence set.
No encoder, button, gesture, feedback, display, or physical-I/O slot is claimed
in the Gills production fixture merely to fill the schema.

An empty optional device collection means that the record declares no slots of
that kind. It does not mean the physical product was exhaustively inspected or
proved not to contain them.

## Instrument v0

The instrument keeps public runtime `parameters`, discrete `actions`, read-only
`displays`, and `state_declarations` as distinct closed record kinds. State
declarations own persistence and reset policy. An empty collection means this
instrument revision declares no public facets of that kind; mappings cannot
target an absent facet.

`device_profile_reference` is an exact ID/revision/hash tuple. Validation
resolves it against the supplied device-profile records and rejects missing or
stale tuples.

Device mappings are directional and closed:

- `parameter-control` maps one device input-control slot to one instrument
  parameter and declares source/destination domains, a linear curve, polarity,
  ordered points, response-time class, smoothing responsibility, and pickup
  policy; and
- `action-trigger` maps one declared device gesture to one instrument action.

Feedback mappings run from an instrument parameter, display, or state facet to
a device feedback-output or display slot. Graph mappings support parameter-to-
parameter, parameter-to-port, and action-to-action intentions. Task 005
validates only source-facet existence, closed deferred-target consistency,
direction, mapping kind, range ownership, and transform shape. It does not
define or validate graph ports, rates, channels, units, connections, or node
types.

The reference instrument declares one public normalized parameter,
`instrument-parameter-000001`, displayed as `Blend`. It proves:

```text
device-input-000001
    -> instrument-parameter-000001 (Blend)
    -> graph-facet-000001 (deferred semantic key: blend)
```

Both mappings are direct linear `0` to `1` mappings. The device mapping assigns
soft pickup to the instrument and assigns smoothing to the graph. Those are
musical mapping policies, not claims about physical scan timing or firmware.

## Historical deferred and exact graph references

No authoritative graph schema or graph record existed in Task 005, so inserting
a graph content hash would fabricate exact-resolution evidence. The reference
instrument therefore uses the closed deferred branch:

- intended opaque graph ID and positive revision;
- `code: GRAPH_REFERENCE_DEFERRED`;
- `owner: task-006`;
- `reason: graph-schema-not-yet-implemented`;
- rationale, resolution question, and architecture-only evidence reference;
  and
- a closed set of intended public graph targets used by this instrument.

The validator checks that every revision-1 graph mapping names a target in that deferred
set and agrees with its facet kind. This proves internal Task 005 consistency
only. It does not prove that the target or graph exists. Task 006 retains that
record byte-for-byte and adds revision 2 with the exact `schuss-graph-000001`
revision/hash tuple. A `resolved` reference passes only when the accepted graph
registry resolves the exact tuple and the mapped public target kind/domain.
No graph stub, placeholder hash, legacy `.axp`, or implementation identity is
manufactured.

## Read-only validation

Run:

```bash
python3 tools/contracts/validate_device_instrument_contracts.py
python3 -m unittest discover -s tools/contracts/tests
```

The validator reads schemas and records, emits one compact deterministic JSON
summary, and performs no writes, device access, Java invocation, generation,
compilation, preference update, or cache update. Its diagnostic codes include:

- `SCHEMA_CONTRACT_INVALID`, `SCHEMA_STRUCTURE_INVALID`;
- `NONPORTABLE_NUMBER`, `NONPORTABLE_ABSOLUTE_PATH`,
  `NONPORTABLE_TIMESTAMP`, `NONPORTABLE_RANDOM_ID`;
- `CONTENT_HASH_MISMATCH`, `ID_REVISION_COLLISION`, `DUPLICATE_RECORD`,
  `DUPLICATE_LOCAL_ID`;
- `DEVICE_REFERENCE_UNRESOLVED`, `GRAPH_RESOLUTION_UNAVAILABLE`,
  `GRAPH_TARGET_NOT_DECLARED`;
- `MAPPING_SOURCE_UNKNOWN`, `MAPPING_DESTINATION_UNKNOWN`,
  `MAPPING_FACET_KIND_MISMATCH`, `MAPPING_DOMAIN_REDEFINITION`,
  `MAPPING_TRANSFORM_INCOMPATIBLE`, `DUPLICATE_DRIVER`; and
- `UNRESOLVED_FACT_UNKNOWN`, `UNRESOLVED_FACT_SCOPE_MISMATCH`,
  `CONTROL_SHAPE_INCOMPATIBLE`, `RANGE_INVALID`.

A valid aggregate Task 006 summary reports structural/schema evidence as
passed, the device-profile and revision-2 graph references as resolved, and
revision 1 as historical deferred evidence. Backend lowering, artifact
generation, ARM compile/link,
connected-device execution, real-time/resource validation, and audible
listening remain `not-run`.

## Deliberately deferred questions

| Question | Owner | Earliest task |
| --- | --- | --- |
| Exact Gills physical control range, resolution, complete slot census, gesture recognition, feedback/display capabilities, and I/O | Device-profile owner | Task 018 or a separate bounded Gills evidence task |
| Runtime smoothing implementation, timing, target behavior, and compiler lowering | Graph/backend owners | Tasks 007-009 |
| Connected hardware, real-time safety, and audible behavior | Device and evidence owners | Later explicit hardware tasks |

Task 006 completed the component-contract, implementation-binding, DSP-graph,
and exact `blend` target boundary documented in
`docs/COMPONENT_GRAPH_CONTRACTS.md`. Task 007 is next; it should add only
compute-target, backend-capability, build, artifact, resource, and evidence
contracts, not GUI/CLI, firmware, or hardware behavior.
