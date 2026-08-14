# Phase 3 inventory review gate

The frozen Phase 3 snapshot is deterministic evidence, not a fully resolved Schuss catalog.
This packet separates observed counts from engineering review routing.

## Object census reconciliation

- 3,417 definition occurrences + 134 catalog subpatch placeholders + 51 provider-only records = 3,602 exported objects.
- 3,417 definition occurrences - 3 legacy-equality collapses + 134 placeholders = 3,548 retained ObjectList entries.
- The 54 exported records absent from ObjectList are the three preserved collapsed occurrences plus 51 provider-only records.

## Unique material review impact

Impact means that the item needs explicit handling before the named workflow relies on it; compilation impact is not proof of an ARM compile failure.

| Dimension | Material issue classes | Unique affected records |
| --- | ---: | ---: |
| Taxonomy | 8 | 495 |
| Migration | 19 | 1301 |
| Compilation | 13 | 904 |

## Issues by code

| Code | Issues | Direct records | Locations | Taxonomy | Migration | Compilation |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `AMBIGUOUS_INSTANCE_RESOLUTION` | 265 | 63 | 265 | context | material | material |
| `GENERATED_DEFINITION_COUNT_MISMATCH` | 3 | 3 | 3 | material | material | context |
| `GENERATED_EMISSION_UNMATCHED` | 51 | 51 | 51 | material | material | context |
| `GENERATED_OUTPUT_REDEFINED` | 1 | 1 | 1 | material | material | context |
| `GENERATED_OUTPUT_REPEATED_IDENTICAL` | 1 | 1 | 1 | context | material | none |
| `GRAPH_POST_CONSTRUCTION_FAILED` | 2 | 2 | 2 | material | blocking | blocking |
| `GRAPH_XML_SCAN_FAILED` | 2 | 2 | 2 | material | blocking | blocking |
| `INSTANCE_BECAME_ZOMBIE` | 364 | 180 | 364 | context | blocking | blocking |
| `INSTANCE_RESOLUTION_UNPROVEN` | 1945 | 671 | 1945 | context | material | material |
| `LEGACY_OBJECT_LIST_COLLAPSE` | 3 | 3 | 3 | material | material | context |
| `NET_ENDPOINT_PORT_MISSING` | 33 | 17 | 33 | context | blocking | blocking |
| `NET_REMOVED_DURING_RESOLUTION` | 33 | 17 | 33 | context | blocking | blocking |
| `NET_STRUCTURALLY_INCOMPLETE` | 19 | 6 | 19 | context | blocking | blocking |
| `NONPORTABLE_GRAPH_VALUE_REDACTED` | 125 | 125 | 125 | none | material | material |
| `OVERLOADED_NAME_CANDIDATES` | 157 | 157 | 157 | material | material | context |
| `RAW_BASELINE_OMISSION` | 146 | 146 | 146 | none | none | none |
| `SERIALIZED_ATTRIBUTE_NOT_PROJECTED` | 7 | 3 | 5 | context | material | material |
| `SERIALIZED_HARD_ZOMBIE` | 1 | 1 | 1 | context | blocking | blocking |
| `SERIALIZED_PARAMETER_NOT_PROJECTED` | 21 | 16 | 20 | context | material | material |
| `UNSUPPORTED_ATTRIBUTE_VALUE` | 1 | 1 | 1 | material | material | material |

## Graph status by source and type

| Source | Type | Complete | Partial | Failed |
| --- | --- | ---: | ---: | ---: |
| axoloti-contrib | axs | 103 | 30 | 0 |
| axoloti-contrib | axp | 210 | 697 | 4 |
| axoloti-factory | axs | 8 | 18 | 0 |
| axoloti-factory | axp | 24 | 49 | 0 |
| ksoloti-contrib | axs | 0 | 0 | 0 |
| ksoloti-contrib | axp | 1 | 0 | 0 |
| ksoloti-objects | axs | 1 | 2 | 0 |
| ksoloti-objects | axp | 0 | 8 | 0 |
| patcher | axs | 0 | 0 | 0 |
| patcher | axp | 1 | 1 | 0 |

## Partial graph reasons

Reason groups overlap; reason combinations in `reports/partial-graphs.json` form the exact 805-graph partition.

| Reason | Graphs | Issues |
| --- | ---: | ---: |
| `INSTANCE_RESOLUTION_UNPROVEN` | 671 | 1945 |
| `INSTANCE_BECAME_ZOMBIE` | 180 | 364 |
| `NONPORTABLE_GRAPH_VALUE_REDACTED` | 125 | 125 |
| `AMBIGUOUS_INSTANCE_RESOLUTION` | 63 | 265 |
| `NET_ENDPOINT_PORT_MISSING` | 17 | 33 |
| `NET_REMOVED_DURING_RESOLUTION` | 17 | 33 |
| `SERIALIZED_PARAMETER_NOT_PROJECTED` | 16 | 21 |
| `NET_STRUCTURALLY_INCOMPLETE` | 6 | 19 |
| `SERIALIZED_ATTRIBUTE_NOT_PROJECTED` | 3 | 7 |
| `SERIALIZED_HARD_ZOMBIE` | 1 | 1 |
| `UNSUPPORTED_ATTRIBUTE_VALUE` | 1 | 1 |

## Gate conclusion

The resolved catalog is suitable as frozen evidence and as an input to a separate Phase 4 classification overlay. Complete graphs may provide strong reference-frequency evidence; partial graph references must remain lower-confidence and retain their reason codes. Migration and compilation work must preserve overload candidates, embedded-definition opacity, zombie context, and missing-net diagnostics rather than treating the legacy selected object as definitive.
