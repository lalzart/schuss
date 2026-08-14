# Ksoloti legacy strategy

## What Schuss retains initially

Schuss initially retains:

- Ksoloti Core firmware and audio runtime;
- the existing ARM compiler and linker path;
- native `.axo` objects and their DSP code;
- `.axs` compound/subpatch graphs and `.axp` patch compatibility;
- generated-object definitions; and
- the Java model where it is required to reproduce legacy resolution and code
  generation.

Retaining these assets reduces migration risk. It does not make their current
Java or XML representation the new platform model.

## Isolation rule

All direct Java-model, Swing, preference, and legacy code-generation coupling
belongs under `legacy/ksoloti-bridge/`. Core Schuss packages exchange versioned
records with the bridge. They do not import legacy model classes or depend on
static `MainFrame` state.

The bridge must be callable without USB, upload, flash, or a visible GUI. It may
use a hidden or compatibility runtime only while the resolver is being
extracted; that dependency must remain named and testable.

## Migration sequence

1. Inventory exact source files without executing or interpreting them.
2. Export the loaded Java catalog, including every variant and diagnostic.
3. Export post-construction compound graphs and resolution outcomes.
4. Introduce an ordered object-registry seam with working-directory-aware name
   and UUID resolution.
5. Add component contracts and exact legacy implementation bindings, then make
   deterministic `.axp` generation and compilation an explicit backend
   adapter.
6. Replace legacy resolution components incrementally only when Schuss fixtures
   prove compatible behavior.
7. Introduce a new graph-to-C++ frontend behind the same backend contract.

No phase requires replacing firmware first.

## Compatibility evidence

Compatibility claims must identify the tested layer:

- raw parsing proves byte presence and XML well-formedness only;
- Java-resolved export proves observed legacy model behavior for pinned inputs;
- legacy code generation proves translation through that Java version;
- ARM compile/link proves the emitted target artifact links;
- connected-board checks prove only the exercised hardware behavior; and
- listening tests are required for audible claims.

These levels are reported separately.

The complete eight-level build evidence model, including structural,
resolution, lowering, generation, ARM, connected-device, real-time/resource,
and audible claims, is normative in `docs/COMPILER_STRATEGY.md`. No level
implies another.

## `.axp` boundary

The transitional backend emits `.axp` only after validating an authoritative
Schuss graph, resolving exact contracts and legacy bindings, elaborating
transparent compounds, and planning dependencies/resources. The emitted bytes
and trace manifest prove only deterministic serialization of the supported
legacy subset. Java resolution/code generation, ARM link, device execution,
real-time behavior, and listening require separate stage results and evidence.

The future direct frontend consumes the same graph without Java or `.axp`.
See `docs/COMPILER_STRATEGY.md`.

## Known legacy hazards

- object provenance depends partly on configured search paths;
- lookup preserves name overloads, while the UUID map may overwrite earlier
  duplicate UUIDs;
- calling legacy `getUUID()` can generate and memoize a UUID, obscuring whether
  it was explicit in source;
- relative neighboring `.axo` lookup may select only the first definition in a
  multi-object file;
- generated Java sources do not by themselves identify their emitted runtime
  objects;
- unresolved instances and missing endpoints become zombie diagnostics only
  after post-construction resolution; and
- current resolution is coupled to Java/Swing global state.

The bridge must preserve these observations as data and diagnostics before any
compatibility behavior is deliberately changed.
