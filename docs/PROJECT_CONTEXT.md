# Project context

## Core statement

Schuss is a modern, CLI-first, source-agnostic environment for designing
embedded musical instruments. It initially targets Ksoloti Core, preserves the
existing firmware, toolchain, and DSP ecosystem through an isolated
compatibility bridge, and supports a Gills-first instrument abstraction above
a transparent DSP graph.

## The problem

Ksoloti's runtime and DSP ecosystem are valuable, but its authoring model makes
the filesystem and source library act as navigation. Graph state, Java object
resolution, code generation, device communication, and UI concerns are tightly
coupled. A physical Gills instrument is consequently assembled as a patch with
panel behavior attached afterward instead of being expressed through stable,
headless contracts.

Schuss separates those concerns so a CLI, future GUI, and future AI client can
inspect and perform the same operations without making any client the source
of semantic truth.

## Intended result

Schuss should provide:

- functional, source-agnostic catalog navigation;
- inspectable primitive and compound DSP graphs;
- stable, versioned component, graph, project, and instrument contracts;
- reusable performance-control graphs that can present one instrument through
  Gills, MIDI, or another controller without changing its DSP graph;
- persistent authoring through shared client-neutral operations;
- a CLI that is as authoritative as any future GUI;
- a Gills abstraction that designs an instrument from the physical device
  inward;
- access to existing Ksoloti objects and patches through a compatibility
  backend; and
- a compiler architecture that can grow beyond the first target.

## Independent layers

1. **Catalog family** owns musician-facing discovery and presentation.
2. **Component contract** owns one target-independent typed node interface.
3. **Implementation binding** realizes one exact component contract for named
   backend and target requirements.
4. **DSP graph** owns the complete signal/control implementation through exact
   component-contract references.
5. **Performance-control graph** owns reusable typed control transformations;
   it knows neither hardware nor DSP node identities.
6. **Device profile** owns physical controls, gestures, feedback, display, and
   I/O slots.
7. **Instrument** owns musical identity, public facets, state, graph mappings,
   and behavior independently of its controller.
8. **Performance configuration** owns the exact controller/device bindings to
   a performance-control graph and that graph's bindings to one instrument.
9. **Machine** owns the completed instrument product identity and exact
   references to its accepted instrument, evidence, and presentation; it is
   neither a catalog object nor a copied DSP graph.
10. **Project/workspace** groups exact graph, instrument, build-request,
   record-set, and asset references for durable authoring.
11. **Compute target** owns processor, memory, audio-runtime, and toolchain
   constraints.
12. **Backend** resolves implementations and lowers an exact graph for a target.
13. **Build and evidence** record exact requests, outputs, diagnostics, and the
   proof level actually reached.

No layer silently borrows identity from another. Gills can initially target
Ksoloti Core without becoming synonymous with it, and a legacy object can be
cataloged without making its source directory a musical category.

## Non-negotiable principles

- Browse by function, filter by form, and inspect provenance.
- Factory, Mutable Instruments, user, and community are provenance facets,
  never primary categories.
- Primitive, compound, and instrument are abstraction levels, not functions.
- The complete DSP graph, including compound internals, remains accessible.
- GUI, CLI, and AI clients use the same graph and project operations.
- Stable IDs never contain category paths or mutable display names.
- Ports, parameters, attributes, actions, and displays remain distinct.
- Ksoloti Java stays inside the compatibility bridge and never becomes the
  Schuss domain model.
- Existing firmware and the ARM compiler are retained initially while the new
  compiler frontend grows incrementally.
- Raw inventory records facts and does not invent semantics, quality, license,
  or compatibility.
- Generated artifacts are deterministic, portable, and content-addressed.
- Ambiguity, unsupported behavior, schema drift, and missing evidence fail
  closed.

## Evidence boundary

Schuss reports evidence independently:

1. schema and identity;
2. component and graph resolution;
3. backend lowering;
4. source/artifact generation;
5. target compile/link;
6. connected-device execution;
7. real-time/resource behavior; and
8. audible/listening behavior.

One level never implies another. A generated legacy `.axp` is a derived
boundary artifact, not authoritative graph truth, and a linked ARM executable
does not prove panel behavior or sound.

## Present boundary

The exact current implementation, active task, and proof gaps are maintained
only in [Development status](STATUS.md). Completed milestones and their retained
authority are indexed in [Development history](HISTORY.md). This document
deliberately contains no task-by-task status chronicle.

## Terminology

| Term | Meaning |
| --- | --- |
| Schuss | The complete catalog, authoring, graph, compilation, and evidence platform |
| Gills | A physical device profile and instrument platform within Schuss |
| Ksoloti Core | The initial compute target |
| Legacy bridge | The isolated adapter around Ksoloti Java and existing tools |
| Family | The category-independent item a musician discovers |
| Component contract | One target-independent typed public node interface |
| Implementation binding | A concrete realization of one exact component-contract revision |
| DSP graph | The authoritative complete signal/control implementation |
| Instrument | Controller-independent musical identity and mappings to one authoritative DSP graph |
| Performance-control graph | Reusable typed transformation from public control inputs to public control outputs |
| Performance configuration | Exact controller/device bindings to a control graph and exact control outputs to instrument facets |
| Machine | Completed instrument product identity with exact instrument, evidence, and presentation references |
| Project/workspace | Portable exact authoring manifest plus local coordination state |
| Build evidence | An immutable level-specific observation about exact inputs and outputs |
