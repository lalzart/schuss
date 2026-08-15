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
| 12A | Durable project/workspace format and persistent CLI graph authoring | [Complete](tasks/012a-durable-project-workspace-and-cli-graph-authoring.md) |
| 13 | Reusable compiler front half through dependency/resource planning | [Complete](tasks/013-reusable-compiler-front-half.md) |
| 14 | Shared build-execution operation and product CLI | [Complete](tasks/014-shared-build-execution-and-product-cli.md) |
| 15 | Normalized DSP representation and minimal direct graph-to-C++ frontend | [Complete](tasks/015-normalized-dsp-and-minimal-direct-frontend.md) |
| 16 | Direct-frontend expansion through the complete Task 011C graph | Contract and evidence audit complete; awaits one compatibility-mode choice |
| 17 | Curated core expansion and richer headless reference instruments | Contract complete; waits for Task 016 |
| 18 | Full Gills implementation and parameter/control mapping | Deferred behind the backbone sequence |
| 19 | Sampling and asset management | Deferred behind the backbone sequence |
| 20 | Additional compute targets and devices | Deferred behind the backbone sequence |
| Deferred UI | Object drawer and transparent graph canvas | Unnumbered; requires new explicit user authorization |

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

Task 012A now completes the durable project/workspace and persistent
graph-authoring dependency formerly combined with Phase 12 UI work. It adds an
exact portable overlay, immutable graph/project revisions, prior-or-successor
atomic recovery, shared v3 operations, and explicit persistent CLI commands.
ADR 0010 retires the misinterpreted Task 012B UI contract. Task 013 now
completes the reusable compiler front half through deterministic dependency
and resource planning, operation v4, and five derived artifact kinds without
executing a backend. Task 014 now adds the exact handler registry, plan-once
execution service, atomic fresh-root publication, portable
progress/cancellation/cache policy, operation v5, and product `build plan` and
`build execute` commands. The retained Task 011C adapter succeeds through
local ARM compile/link with byte-identical portable results across fresh
roots. Task 015 now defines the first normalized Q27 DSP module and lowers the
one-node Blend graph directly to deterministic standalone C++ with source-map
and compiled arithmetic-vector evidence through level 4. Task 016's pinned
source audit now supplies a complete conditional legacy-equivalent
specification; implementation awaits the explicit legacy-equivalent versus
Schuss-native choice. UI work remains unnumbered and deferred.
The completed boundaries are in
`docs/DEVICE_INSTRUMENT_CONTRACTS.md` and
`docs/COMPONENT_GRAPH_CONTRACTS.md`, and
`docs/TARGET_BACKEND_BUILD_CONTRACTS.md`, and
`docs/OPERATION_CONTRACTS.md`.

## Active backbone sequence and deferred UI

The active sequence is:

```text
Task 012A durable project/workspace + persistent CLI graph authoring
  -> Task 013 reusable compiler front half and deterministic plans
  -> Task 014 shared build execution and product CLI
  -> Task 015 normalized DSP representation + minimal direct frontend
  -> Task 016 direct frontend for the complete Task 011C graph
  -> Task 017 curated core expansion + richer headless reference instruments
```

Task 012B is retired and must not be run. The object drawer and transparent
graph canvas remain a future client milestone, but they receive no task number
until the user explicitly resumes UI work. Tasks 013-015 are complete. Task 016
is the active compiler gate, with implementation stopped on one explicit
compatibility-mode choice; Task 017 waits for it.

VS-07 connected-device execution remains an optional, separately authorized
evidence track. It is not a prerequisite for Tasks 014-017 and cannot
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
