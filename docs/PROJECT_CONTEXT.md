# Project context

## Core statement

Schuss is a modern, CLI-first, source-agnostic environment for designing
embedded musical instruments. It initially targets Ksoloti Core, preserves the
existing firmware, toolchain, and DSP ecosystem through an isolated
compatibility bridge, and supports a Gills-first instrument abstraction above
a transparent DSP graph.

## The problem

Ksoloti's embedded runtime and DSP ecosystem are valuable, but its current
authoring model makes the filesystem and source library act as navigation. The
patcher hides objects behind a difficult library/search structure, while DSP
graphs, editor state, Java resolution, code generation, device communication,
and UI concerns are tightly coupled.

This is especially awkward when designing a coherent physical instrument.
Today, a Gills instrument is assembled as a pseudo-modular patch and its panel
is attached afterward. There is no stable headless model through which a GUI,
CLI, and AI agent can inspect and perform the same operations.

## Intended result

Schuss should provide:

- a persistent, immediate DSP-object drawer;
- functional, source-agnostic catalog navigation;
- inspectable primitive and compound DSP graphs;
- stable, versioned object, graph, and instrument contracts;
- a CLI that is as authoritative as the GUI;
- a Gills abstraction that designs an instrument from the physical device
  inward;
- access to existing Ksoloti objects and patches through a compatibility
  bridge; and
- a compiler architecture that can grow beyond the first hardware target.

## Independent layers

1. **Catalog family** describes the musician-facing discovery item, not a node
   type or compiler input.
2. **Component contract** describes one target-independent typed public node
   interface.
3. **Implementation binding** realizes one exact component-contract revision
   for named backend and target requirements.
4. **Compute target** describes the processor, memory, audio runtime, and
   compiler constraints.
5. **Device profile** describes physical pots, buttons, encoders, displays,
   I/O, and gestures.
6. **Instrument** describes musical identity, public controls, state, and
   behavior.
7. **DSP graph** describes the complete signal and control implementation by
   referencing exact component-contract revisions.
8. **Backend** resolves implementation bindings and lowers the graph into an
   executable form for a compute target.

No layer may silently borrow identity from another. A Gills instrument can
target Ksoloti Core initially without making Gills synonymous with that board,
and a Ksoloti object can be cataloged without making its source directory a
musical category.

## Non-negotiable principles

- Browse by function; filter by form; inspect provenance.
- Factory, Mutable Instruments, user, and community are never primary
  categories.
- Primitive, compound, and instrument describe abstraction level, not
  function.
- The complete DSP graph remains accessible.
- GUI, CLI, and AI clients use the same graph operations.
- Stable IDs never contain category paths.
- Ports, parameters, attributes, actions, and displays remain distinct.
- Ksoloti Java is an isolated compatibility bridge, not the new domain model.
- Existing firmware and the ARM compiler are retained initially.
- A new compiler frontend is introduced incrementally.
- Raw inventory records facts and does not invent semantics.
- Dirty upstream trees are never cleaned or modified unexpectedly.
- Generated artifacts are deterministic and reproducible.
- Uncertainty and unresolved content are reported explicitly.

## Present boundary

The raw and Java-resolved inventories and the Phase 3 review packet are
accepted frozen evidence with documented limitations. Phase 4A is complete: a
separate versioned family/implementation overlay, draft functional taxonomy,
and manually reviewed 26-family pilot pass their validation gates. Phase 4B is
gated so catalog expansion cannot outrun typed component contracts. Task 004
remains the accepted architecture for schema ownership, reference direction,
compiler stages, and evidence separation. Task 005 implements the first
production device-profile and instrument contracts. Task 006 now adds the
exact Crossfader family companion, three non-interchangeable component
contracts and implementation seam maps, one authoritative typed graph, and an
exactly resolved instrument revision 2 while retaining deferred revision 1.
Structural, exact-reference, target-independent type, legacy seam-map, and
graph-target evidence pass. Task 007 now adds reusable target/backend/build
contracts and a Ksoloti-specific revision-1 production closure. Its default
pure resolver still reports that frozen candidate unresolved. Task 008 now consolidates
the validator core and provides one shared headless dispatcher for validation,
inspection, build resolution, and atomic graph transactions, plus a minimal
canonical-JSON process boundary. Its operation layer remains pure and stops
before lowering. See `docs/TARGET_BACKEND_BUILD_CONTRACTS.md` and
`docs/OPERATION_CONTRACTS.md`.

The Task 009 prerequisite is complete. Default validation and operations now
load the exact frozen Task 005-008 record set, while the prerequisite view is an
explicit exact superset. A pinned source/Java/classpath/GNU Arm/firmware closure
and a closed `candidate-under-test` probe contract are established. The
retained prerequisite probe remains `not-authorized` and `not-run`.

Task 009 is now complete for the exact Blend/mixed-Crossfader slice. Successor
record set `schuss-record-set-000003` revision 1 adds an authorized probe,
strictly-earlier binding evidence, promoted revision-2 target/backend/
environment/binding/eligibility/request records, one successful build result,
14 probe/production artifact descriptors, a static resource report, and
separate evidence claims through ARM compile/link level 5. The production
handler consumes the exact Task 008 seam; it is not a general compiler.
Connected-device, real-time, and audible levels 6-8 remain `not-run`.

Task 010 now adds the deterministic product CLI over the unchanged Task 008
dispatcher. Exact graph/build-request locators resolve only through the
selected validated record set; human output, canonical JSON, fixed help, and
static Bash/Zsh/Fish completion share one command boundary. The default remains
record set `schuss-record-set-000001` revision 1, while Task 009 set `000003`
is explicit opt-in. `build resolve` does not invoke the Task 009 handler, and
`graph transact` remains an in-memory non-persisted proposal.

Task 011A now adds the first browsable client-neutral catalog projection. It
retains every Phase 4A byte, resolves all 26 pilot families through exact
companion references, and adds only the reviewed Square LFO and Cyclic Counter
families plus their implementations and the distinct four-step pitch-sequencer
implementation. Successor record set `schuss-record-set-000004` revision 1
owns the exact corpus and additive operation v2 schemas. `catalog.search` and
`catalog.inspect` use the same dispatcher for direct, process, CLI, and future
GUI/AI clients. This task creates no new component contract, binding,
eligibility, graph, instrument, build, or runtime evidence.

## Terminology

| Term | Meaning |
| --- | --- |
| Schuss | The complete authoring, graph, catalog, and compilation platform |
| Gills | A physical device profile and instrument platform |
| Ksoloti Core | The initial compute target |
| Legacy bridge | The isolated adapter around the Ksoloti Java model and tools |
| Object | A graph node type with a stable identity and explicit facets |
| Family | The category-independent item a musician discovers in the catalog |
| Component contract | One target-independent typed public node interface belonging to a family |
| Implementation binding | A concrete realization of one exact component-contract revision for named backend/target requirements |
| Legacy observation | A snapshot-scoped evidence record, not a Schuss ID |
| Compound | A reusable graph presented as one object without hiding internals |
| Instrument | A musical contract that maps a device profile onto behavior and a DSP graph |
| Build evidence | An immutable, level-specific observation about exact build inputs or runtime validation; never catalog truth by side effect |
