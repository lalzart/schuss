# Roadmap

The phases are ordered to preserve legacy capability while moving authority
into transparent, typed Schuss models.

| Phase | Outcome | Status |
| --- | --- | --- |
| 1 | Project context and source locking | Established in this scaffold |
| 2 | Raw physical source inventory | Existing baseline migrated; validator retained |
| 3 | Java-resolved object and graph inventory | Established; resolved snapshot frozen |
| 3 review gate | Deterministic inventory review and impact packet | Complete; accepted frozen evidence |
| 4A | Versioned semantic overlay and 20-30-family pilot | Complete |
| 4 contract gate | Schema ownership, compiler stages, and evidence separation | Complete; accepted Task 004 architecture |
| 5 | Minimal Gills device-profile and instrument schemas | Complete |
| 6 | Component-contract, implementation-binding, and DSP-graph schemas | Complete |
| 7 | Compute-target, backend-capability, build, artifact, and evidence schemas | Complete; Task 007 contract gate |
| 8 | Shared headless validation and typed operation layer | Complete; shared dispatcher and minimal process gate |
| 9 | One minimal graph through the legacy `.axp` adapter and ARM compiler/linker | Complete; exact Blend slice reaches level 5 |
| 10 | Deterministic structured CLI over shared operations | [Complete](tasks/010-deterministic-product-cli-over-shared-operations.md) |
| 11A | Browsable catalog control plane and exact seven-role Gills-slice catalog review | [Complete](tasks/011a-browsable-catalog-control-plane-and-exact-gills-slice-catalog-review.md) |
| 11B | Six component contracts/bindings, authoritative slice graph, minimal Gills instrument, and unresolved build closure | [Complete](tasks/011b-component-contracts-gills-slice-graph-and-unresolved-build-closure.md) |
| 11C | Bounded legacy backend expansion and ARM compile/link for the slice | [Complete](tasks/011c-bounded-legacy-backend-expansion-and-arm-evidence.md) |
| 12A | Durable project/workspace format and persistent CLI graph authoring | [Proposed; immediate next task](tasks/012a-durable-project-workspace-and-cli-graph-authoring.md) |
| 12B | Basic object drawer and transparent graph canvas | Deferred until the headless-backbone readiness gate |
| 13A | Reusable compiler front half through dependency/resource planning | [Proposed; follows Task 012A](tasks/013a-reusable-compiler-front-half.md) |
| 13B | Shared build-execution operation and product CLI | Planned |
| 13C | Normalized DSP representation and minimal direct graph-to-C++ frontend | Planned |
| 13D | Direct-frontend expansion through the complete Task 011C graph | Planned |
| B6 | Curated core expansion and richer headless reference instruments | Planned after Task 013D; task number not yet assigned |
| 14 | Full Gills implementation and parameter/control mapping | Deferred behind the backbone sequence |
| 15 | Sampling and asset management | Deferred behind the backbone sequence |
| 16 | Additional compute targets and devices | Deferred behind the backbone sequence |

## Current architectural gate and next task

Phases 2 and 3 and their review gate are complete. Phase 2 remains an immutable
raw snapshot with two explicit source parse issues. Phase 3 retains the loaded
and post-construction legacy model, including partial, failed, ambiguous,
zombie, and unresolved outcomes. ADR 0004 accepts that evidence with known
limitations. Phase 4A is complete with a separate semantic overlay and a
validated 26-family manual pilot. Task 004 remains the accepted architecture:
`docs/SCHEMA_STRATEGY.md`, `docs/COMPILER_STRATEGY.md`, and ADRs 0005-0007
define the family/contract/binding boundary, one-way references, compiler
stages, and build-evidence separation without implementing schemas or code
generation.

Tasks 005, 006, and 007 are complete. Task 005 adds the minimal Gills device-profile
and instrument boundary. Task 006 adds the exact Crossfader family companion,
three component signatures and legacy seam maps, the authoritative one-node
`blend` graph, transparent-compound validation, and exactly resolved
instrument revision 2 while retaining revision 1. Task 007 adds reusable
target/backend/build-domain schemas, the smallest truthful Ksoloti production
closure, a pure fail-closed resolver, and future result/evidence fixtures. The
production candidate remains unresolved and no backend stage ran. Task 008 now
adds the lower shared validator core, three sibling rule modules, one aggregate
validator, four versioned headless operations, atomic in-memory graph
transactions, a data-only Task 009 seam, and the minimal canonical-JSON
`schuss op` process boundary. The Task 009 prerequisite now adds exact accepted
and prospective record-set views, an authenticated pinned Java/source/ARM/
firmware closure, and a closed non-production probe/evidence boundary. Task
009 then executes an authorized probe, promotes only new exact revisions, runs
ordinary `build.resolve`, and carries its exact seam through deterministic
`.axp`, Java generation, and ARM compile/link for the one-node Blend slice.
Successor record set `schuss-record-set-000003` records levels 1-5 as passed;
levels 6-8 remain `not-run`. Task 010 now supplies deterministic product
commands, exact record-set locator resolution, human/canonical output, fixed
help, and static completion over the unchanged Task 008 dispatcher. It adds no
general build execution or persistent graph write.
Task 011A now adds the derived 28-family catalog projection, exact inspection,
deterministic browse/search and approved filters, additive v2 catalog
operations, and product catalog commands. The seven-role review reuses the
accepted Sine Oscillator, Crossfader, State-variable Filter, stereo Audio
Output, and pitch-sequencer family identities; allocates only Square LFO,
Cyclic Counter, and the distinct four-step implementation; and leaves all
missing contracts, bindings, graph, instrument, and build work to Task 011B.
Task 011B now closes that exact target-independent boundary with additive Q21
pitch/behavior contracts, exact legacy seam maps, an eight-node and
nine-connection graph, the minimal Gills blend mapping, and successor record
set `000005`. Both mandatory joins need no adapter: the Boolean clock transport
is exact and the counter owns rising-edge reception; the low-pass outlet has
the same transport type as both endpoint inlets and cardinality two. The build
closure is intentionally unresolved, selects only the already promoted mixed
Crossfader, emits no backend invocation, and leaves lowering and ARM evidence
to Task 011C.
Task 011C now executes six candidate probes, promotes only their exact binding
and eligibility successors, adds the one required native realization form,
and produces deterministic source and ARM compile/link evidence for the exact
slice. Record set `000006` selects all eight nodes and records levels 1-5 as
passed. Connected-device, real-time, and audible gates remain separately
unauthorized and unproved; the general backend and direct frontend also remain
future work.

The immediate next execution unit is Task 012A. It separates the durable
project/workspace and persistent graph-authoring dependency from the old
combined Phase 12 UI milestone. Task 013A is the second proposed task and owns
only the reusable compiler front half through deterministic dependency and
resource planning. Task 012B retains the object drawer and transparent graph
canvas as a deferred client of accepted operations; it owns no independent
catalog, graph, project, build, or compiler semantics.
The completed boundaries are in
`docs/DEVICE_INSTRUMENT_CONTRACTS.md` and
`docs/COMPONENT_GRAPH_CONTRACTS.md`, and
`docs/TARGET_BACKEND_BUILD_CONTRACTS.md`, and
`docs/OPERATION_CONTRACTS.md`.

## Headless-backbone sequence and UI readiness gate

The active sequence is:

```text
Task 012A durable project/workspace + persistent CLI graph authoring
  -> Task 013A reusable compiler front half and deterministic plans
  -> Task 013B shared build execution and product CLI
  -> Task 013C normalized DSP representation + minimal direct frontend
  -> Task 013D direct frontend for the complete Task 011C graph
  -> B6 curated core expansion + richer headless reference instruments
```

Task 012B is not on that critical path. UI work remains deferred until all of
the following are true:

- a portable project can be created, inspected, validated, revised, and
  reopened through the CLI without repository-owned fixture assumptions;
- graph persistence is atomic, exact-reference-safe, and recoverable without
  making a client or filesystem layout authoritative graph truth;
- compiler planning and build execution use shared client-neutral boundaries;
- the legacy and direct paths conform for at least one exact graph without
  silent fallback;
- the direct frontend reaches level 5 for the complete Task 011C graph; and
- the reviewed core supports several useful non-UI reference instruments.

VS-07 connected-device execution remains an optional, separately authorized
evidence track. It is not a prerequisite for Tasks 012A-013D or B6 and cannot
substitute for their structural, persistence, compiler, or CLI acceptance
gates.

## Contract sequence constraints

- Introduce a minimal Gills device-profile and instrument reference contract
  before graph/editor contracts harden; full Gills implementation may remain
  later.
- Define component-contract, implementation-binding, and authoritative graph
  schemas before lowering a new Schuss graph through any backend.
- Define compute-target, backend-capability, and build/evidence schemas before
  invoking a compiler as Schuss.
- Treat the legacy compilation adapter as a backend/passthrough proof. Legacy
  `.axp` is an emitted boundary artifact and never the authoritative Schuss
  graph.
- Expose future catalog and graph operations through one typed operation layer.
  CLI output must be deterministic and structured, and GUI and AI clients must
  use the same operations.
- Do not let Phase 4B catalog expansion outrun component-contract and binding
  review. Additional families may be curated incrementally, but compiler-facing
  variants require the Phase 6 boundaries.

## Promotion rule

A phase advances when its task acceptance tests pass and its unresolved content
is named. Later work may refine a versioned schema but may not rewrite retained
raw evidence or erase diagnostics to make a gate appear clean.
