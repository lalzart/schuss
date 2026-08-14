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

1. **Compute target** describes the processor, memory, audio runtime, and
   compiler constraints.
2. **Device profile** describes physical pots, buttons, encoders, displays,
   I/O, and gestures.
3. **Instrument** describes musical identity, public controls, state, and
   behavior.
4. **DSP graph** describes the complete signal and control implementation.
5. **Backend** resolves and lowers the graph into an executable form for a
   compute target.

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

The raw and Java-resolved inventories are frozen evidence. The current task is
the reporting-only Phase 3 review gate: it measures unique impact, reconciles
the resolved census, and produces deterministic review samples without
classifying objects or changing the snapshot. It does not settle the
functional taxonomy, select the Phase 4 core set, define the final Schuss graph
schema, implement a GUI, replace firmware, or create a new compiler frontend.
See `docs/tasks/002-phase-3-inventory-review-gate.md` for the exact contract.

## Terminology

| Term | Meaning |
| --- | --- |
| Schuss | The complete authoring, graph, catalog, and compilation platform |
| Gills | A physical device profile and instrument platform |
| Ksoloti Core | The initial compute target |
| Legacy bridge | The isolated adapter around the Ksoloti Java model and tools |
| Object | A graph node type with a stable identity and explicit facets |
| Compound | A reusable graph presented as one object without hiding internals |
| Instrument | A musical contract that maps a device profile onto behavior and a DSP graph |
