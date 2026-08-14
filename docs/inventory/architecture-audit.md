# Legacy inventory architecture audit

Status: Legacy architecture audit supporting Schuss Phase 2 raw inventory and
Phase 3 Java-resolved inventory. The resolved catalog exporter described in the
task contract is deliberately not implemented in the migrated baseline.

## Library discovery and loading

`Preferences.getObjectSearchPath()` is the effective ordered list of object
roots. `AxoObjects.LoadAxoObjects()` resets the tree, list, and UUID map, then
loads each root on a background `LoaderThread`. `LoadAxoObjects(String)` walks a
root recursively through `LoadAxoObjectsFromFolder`. When the root directory is
named `objects`, its parent is matched against configured `AxolotiLibrary`
locations and the library ID is used for the tree node. Library provenance is
therefore configuration-dependent and is not encoded reliably in every object.

Native `.axo` files are deserialized with Simple XML into `AxoObjectFile`; every
`objdef` in the file becomes a separate `AxoObjectAbstract`. Strict parsing is
attempted first and, for most failures, relaxed parsing follows. `.axs` files are
registered lazily as `AxoObjectUnloaded` and become `AxoObjectFromPatch` during
resolution. `.axp` files are patches, not catalog entries.

## Identity, lookup, and duplicates

Folder prefixes are prepended to each native object's source `id`. Lookup by
name linearly returns every matching item, preserving overloads. Relative
`./name` and `../name` requests first try a neighboring `.axo`, but that path
currently returns only the first `objdef` in a multi-object file; a neighboring
`.axs` is the fallback. Global unresolved names are also tested as `.axs` under
every configured search root.

UUID lookup uses a single `HashMap`. Duplicate UUIDs are logged, then the later
definition overwrites the map entry. The ordered `ObjectList` still retains
variants except where `AxoObjectAbstract.equals` collapses them by UUID or source
path. A factual exporter must derive duplicate reports from the full list, not
the UUID map.

`getUUID()` may generate and memoize a UUID when the source omitted one. An
inventory must distinguish explicit source UUIDs from generated runtime UUIDs;
calling `getUUID()` alone destroys that distinction.

## Generated objects

`generatedobjects.GeneratedObjects` calls the `GenerateAll()` methods in the
generator classes. Those classes construct model objects and write `.axo`
definitions through `gentools`; they are not injected directly by
`AxoObjects.LoadAxoObjects()`. Consequently, a loaded generated object is
indistinguishable from another `.axo` without a separately maintained
generator-to-output provenance map. Schuss Phase 2 inventories generator Java sources
as candidate files but does not claim that this proves which resolved objects
they produced or how many objects each generator emits. The resolved Java
exporter must enumerate those emitted runtime catalog objects explicitly.

## Patch, compound graph, and zombie handling

`Patch` is the Simple XML model for `.axp` and `.axs`. Its object instances and
nets are deserialized before `PostContructor()` resolves types and constructs
runtime ports, parameters, attributes, modulation links, and net endpoints.
Subpatch objects are represented by `AxoObjectFromPatch`; unloaded subpatch
catalog entries are `AxoObjectUnloaded`.

An unresolved instance is converted to `AxoObjectInstanceZombie` backed by
`AxoObjectZombie`. Zombie inlet/outlet instances use `DTZombie`. Net resolution
also logs missing source objects, outlets, destination objects, and inlets.
Raw XML alone can identify serialized zombie elements and requested type names,
but it cannot faithfully reproduce all post-construction resolution outcomes.

## Object facets

`AxoObject` keeps inlets, outlets, parameter definitions, attribute definitions,
display definitions, modulators, includes, dependencies, local/state code,
initialization, control-rate, sample-rate, MIDI, and dispose code as distinct
model facets. Instance values live in their corresponding instance classes.
These must remain separate in a future resolved export.

## GUI coupling and current command paths

Resolution is coupled to the static `MainFrame.axoObjects`; patch construction
and many instance classes also create Swing components. The existing command
line test path constructs a hidden `MainFrame`, starts another loader, sleeps a
fixed ten seconds, and then calls test methods. `-runTest` ultimately invokes
patch deserialization, `PostContructor()`, and `WriteCode()`; `WriteCode()` calls
the code-generation path including `GenerateCode3()` before the compile command.
The newer `HeadlessPatchCompiler` still assigns `MainFrame.axoObjects`, but it
loads and joins the loader deterministically and does not require a device.

No code generation or compilation is required to export native object
definitions, loaded catalog identity, graph structure, or serialized metadata.
Runtime-resolved ports on subpatches and definitive zombies do require the
post-constructor/resolver path.

## Recommended next seam

Extract a small `ObjectRegistry` interface (ordered variants, UUID candidates,
name resolution with a working directory) and inject it into patch resolution.
Provide a synchronous loader method returning an immutable registry plus
diagnostics. A future `LegacyCatalogExporter` can then use the same resolver
without `MainFrame`, Swing construction, sleeps, code generation, USB, or
preference writes.

## Licensing boundary

Repository-level license files, Git remote/commit data, and explicit object
`license`/`author` elements are evidence. Directory names and provenance do not
establish per-file licensing. Missing or conflicting license data must remain
unknown and be reported rather than inherited heuristically.
