# Architecture

## Dependency direction

Schuss owns semantic models. Backends and applications depend on those models;
the models do not depend on Java, Swing, legacy XML, or a particular board.

```text
GUI / CLI / AI clients
          |
    graph operations
          v
catalog + graph + instrument models
       /                    \
device profiles          compute targets
       \                    /
              backend
                 |
       legacy Ksoloti bridge
                 |
  Java resolver -> .axp -> ARM compiler
```

The initial backend passes through the Ksoloti Java resolver and existing ARM
compiler. Later backends may lower the same semantic graph without that bridge.

## Layer contracts

### Compute target

A compute target declares execution constraints: processor family, available
memory regions, audio block/runtime assumptions, supported toolchain, and
backend capabilities. It does not define panel controls or an instrument's
musical behavior.

`ksoloti-core` is the first target. A successful ARM link is target-build
evidence, not proof of real-time headroom, physical I/O, or sound quality.

### Device profile

A device profile declares physical controls, outputs, display capabilities,
I/O, and gestures. It provides stable hardware-facing slots that an instrument
may map, without embedding DSP implementation.

Gills is the first device profile. Its existing panel contracts can inform this
layer, but importing them is separate from the legacy inventory task.

### Instrument

An instrument owns musical identity, public parameters, actions, state,
performance mappings, and presentation. It references a device profile and a
DSP graph but remains distinguishable from both. Multiple device mappings may
eventually present one instrument, and multiple targets may execute it.

### DSP graph

The graph owns nodes, typed ports, connections, parameter bindings, attributes,
and compound structure. Compound nodes never make their internal graph
uninspectable. Editor coordinates and visual grouping are optional presentation
data, not node identity.

### Backend

A backend resolves object implementations for a compute target, checks target
capabilities and resources, lowers the graph, and emits build diagnostics and
artifacts. It must not mutate the authoritative graph to hide ambiguity.

## Catalog architecture

The catalog separates identity and behavior from navigation:

- stable object identity is category-independent;
- functional classification is curated and revisable;
- abstraction level, provenance, license evidence, target compatibility, and
  implementation form are facets;
- duplicates and overloads remain visible until an explicit resolution rule
  selects among them; and
- raw source observations and Java-resolved observations remain traceable.

The inventory pipeline is deliberately staged:

1. lock portable source identities and exact commits;
2. record physical candidate files and byte hashes;
3. export Java-resolved object variants, generated objects, compound graphs,
   ports, parameters, attributes, displays, dependencies, and diagnostics;
4. curate function and preferred presentation later.

## Operation boundary

The future headless model will expose the same typed operations to GUI, CLI,
and AI clients. Expected operation families include catalog query, graph
inspection, node/connection mutation, validation, explanation, and build.
Exact command names and protocol shapes are intentionally deferred until the
catalog and graph schemas exist.

## Legacy boundary

Only `legacy/ksoloti-bridge/` may depend directly on the legacy Java model. The
bridge may read `.axo`, `.axs`, and `.axp`, invoke resolution, and emit legacy
build artifacts. It must translate results into versioned Schuss records rather
than exposing Swing objects, static `MainFrame` state, preference paths, or
`patchMeta_t`/`ParameterExchange_t` as stable semantic APIs.

See `docs/LEGACY_STRATEGY.md` for the migration sequence.
