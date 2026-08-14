# Illustrative crossfader domain slice

This is a worked architecture example, not a production schema, registry,
fixture, compatibility claim, or build result. It intentionally omits many
fields. IDs beginning with `example:` and hashes shown as `<hash>` are not
allocated Schuss identities. No `.axp`, C++, object, firmware, or binary was
generated for this example.

The existing Phase 4A IDs quoted below are retained facts:

- Crossfader family: `schuss-family-000018`.
- Control-rate implementation: `schuss-implementation-000026`, evidenced by
  `legacy-resolved-catalog-v0:object:458`.
- Audio-rate implementation: `schuss-implementation-000027`, evidenced by
  `legacy-resolved-catalog-v0:object:459`.
- Mixed-rate implementation: `schuss-implementation-000028`, evidenced by
  `legacy-resolved-catalog-v0:object:460`.

The frozen observations show three different interfaces under the legacy name
`mix/xfade`: control-rate inputs/control/output, audio-rate
inputs/control/output, and audio-rate inputs/output with a control-rate fade
input. Their shared family is useful for browsing but cannot type a graph node.

## Catalog family and component contracts

All three illustrative contracts reference the same existing family while
retaining different nominal identities:

| Contract ref | Family ref | Public ports | Meaning |
| --- | --- | --- | --- |
| `example:component-contract:000001@1#<hash>` | `schuss-family-000018` | control-stream `a`, `b`, `fade`; control-stream `out` | Control-rate crossfade |
| `example:component-contract:000002@1#<hash>` | `schuss-family-000018` | audio-stream `a`, `b`, `fade`; audio-stream `out` | Audio-rate crossfade |
| `example:component-contract:000003@1#<hash>` | `schuss-family-000018` | audio-stream `a`, `b`; control-stream `fade`; audio-stream `out` | Mixed-rate crossfade |

Every port also has explicit direction, representation, channel shape, unit,
range, optionality, and ownership fields. They are shortened here only to keep
the example readable.

The graph below selects contract `example:component-contract:000002`; it does
not select `schuss-family-000018`. A control-rate cable connected to its `fade`
port would be invalid without an explicit control-to-audio adapter.

## Implementation bindings

Future companion binding records can enrich the retained Phase 4A
implementation identities without changing those IDs:

| Implementation identity | Exact contract realized | Form/backend | Evidence seam |
| --- | --- | --- | --- |
| `schuss-implementation-000026` | `example:component-contract:000001@1#<hash>` | Generated legacy object / `legacy-ksoloti` | Object observation 458 |
| `schuss-implementation-000027` | `example:component-contract:000002@1#<hash>` | Generated legacy object / `legacy-ksoloti` | Object observation 459 |
| `schuss-implementation-000028` | `example:component-contract:000003@1#<hash>` | Generated legacy object / `legacy-ksoloti` | Object observation 460 |

Each record would include a total port-to-legacy-seam map, dependencies,
target/capability constraints, and named evidence. The observation proves only
that the pinned Java model exported the definition. This example does not
promote the existing `not-evaluated` compatibility entries.

Because the node's exact contract is `...000002`, the legacy backend considers
only `schuss-implementation-000027`. Family siblings `...000026` and
`...000028` are not overload fallbacks. If the exact binding is unavailable or
ineligible for Ksoloti Core, resolution fails rather than choosing a
family-relative alternative.

## Authoritative graph

The example uses these additional abbreviated contract references:

- `example:component-contract:000004@1#<hash>`: sine sound source, referencing
  existing Sine Oscillator family `schuss-family-000003`.
- `example:component-contract:000005@1#<hash>`: noise sound source, referencing
  existing Uniform Noise family `schuss-family-000004`.
- `example:component-contract:000006@1#<hash>`: explicit control-to-audio value
  adapter with runtime parameter `value` and an audio-stream outlet,
  referencing illustrative family `example:catalog-family:000001`.
- `example:component-contract:000007@1#<hash>`: audio output endpoint,
  referencing existing Audio Output family `schuss-family-000002`.

The authoritative graph is conceptually:

```text
example:graph:000001@1#<hash>

nodes:
  source-a      -> example:component-contract:000004@1#<hash>
  source-b      -> example:component-contract:000005@1#<hash>
  blend-value   -> example:component-contract:000006@1#<hash>
  crossfader    -> example:component-contract:000002@1#<hash>
  audio-output  -> example:component-contract:000007@1#<hash>

connections:
  source-a.out       -> crossfader.a
  source-b.out       -> crossfader.b
  blend-value.out    -> crossfader.fade
  crossfader.out     -> audio-output.in

parameter values:
  blend-value.value = 0.5 normalized

exposed compound interface:
  public parameter key blend -> blend-value.value
```

The explicit `blend-value` node owns the control-to-audio behavior, including
update boundary and smoothing. The compiler does not invent that conversion.
The family, legacy paths, implementation identities, backend, target, Gills
controls, and canvas coordinates do not appear as node identity.

### Transparent compound exposure

The same graph can realize an illustrative reusable compound contract:

```text
component contract:
  example:component-contract:000008@1#<hash>
  family: example:catalog-family:000002
  public runtime parameter: blend (normalized 0..1)

transparent implementation binding:
  example:implementation:000001@1#<hash>
  realizes: example:component-contract:000008@1#<hash>
  graph: example:graph:000001@1#<hash>
  mapping key blend -> graph exposure blend -> node blend-value.parameter value
```

The compound contract owns the public `blend` facet and mapping key. The graph
owns the concrete internal target. The binding proves that the mapping is
total and type-compatible. Callers can inspect the sine, noise, adapter,
crossfader, and output nodes; the compound does not become an opaque `.axs`.

## Instrument and Gills mapping

The illustrative instrument remains separate from both graph and device:

```text
instrument:
  ref: example:instrument:000001@1#<hash>
  graph: example:graph:000001@1#<hash>
  device profile: example:device-profile:000001@1#<hash>
  public parameter: blend (normalized 0..1, default 0.5)
  graph mapping: instrument.blend -> graph.exposed_parameter.blend

device profile:
  ref: example:device-profile:000001@1#<hash>
  display label: Gills
  physical slot: knob-1 (absolute rotary, normalized physical range)

device mapping:
  knob-1 absolute position -> instrument.blend
  transform: normalized linear 0..1, explicit soft-pickup policy
```

The device profile contains no graph. The graph contains no `knob-1` or Gills
reference. The compute target contains neither. Changing the knob assignment
creates an instrument/device-mapping revision, not a graph or component
contract revision.

## Legacy build request and resolution

An illustrative build request binds exact inputs:

```text
request: example:build-request:000001@1#<hash>
graph: example:graph:000001@1#<hash>
instrument: example:instrument:000001@1#<hash>
compute target: ksoloti-core@<revision>#<hash>
backend: legacy-ksoloti@<revision>#<hash>
options: <normalized illustrative options>
binding overrides: none
requested stop: ARM link
```

The staged resolution is:

1. Validate graph and contract types without choosing implementations.
2. Validate the explicit Ksoloti Core and legacy-backend pair.
3. Resolve each node's exact contract. For `crossfader`, only the binding
   companion to `schuss-implementation-000027` matches contract `...000002`.
4. Elaborate any transparent compounds and preserve the expansion path.
5. Plan dependencies and resources.
6. Only then may the legacy adapter emit deterministic `.axp` plus a trace
   manifest for the isolated Java bridge.

This walkthrough explains selection; it is not evidence that these future
records or bindings exist or that a build succeeds.

## Separate result and evidence shape

A future result is a separate record. An abbreviated successful shape would
look like this, but no such result was produced by Task 004:

```text
result: example:build-result:000001@1#<hash>
request: example:build-request:000001@1#<hash>
selected bindings:
  crossfader -> schuss-implementation-000027@<revision>#<hash>
  ... every other node selection ...
toolchain: <exact identity>
firmware ABI: <exact identity>
artifacts:
  legacy-axp: sha256:<hash>
  firmware: sha256:<hash>
diagnostics: <structured records with graph/contract/binding/stage trace>
```

Separate evidence records reference the immutable result, stage, or artifact:

```text
evidence claims:
  level 1: <separate structural claim>
  level 2: <separate resolution claim>
  level 3: <separate lowering claim>
  level 4: <separate generation claim>
  level 5: <separate ARM compile/link claim>
  levels 6-8: not-run
```

This result cannot change the Crossfader family, the component contracts, the
binding's compatibility status, or its preferred status. A later reviewed
curation revision may cite the immutable evidence.

## Same graph, future direct frontend

A future request can keep the exact graph and instrument references while
changing only the backend reference to a direct Schuss C++ backend. Resolution
then requires native/direct bindings for the same exact component contracts.
The frontend elaborates the same graph into the normalized DSP representation,
generates C++, lowers to the Ksoloti runtime ABI, and invokes the existing ARM
compiler/linker without Java or `.axp`.

If a native binding is missing, that backend reports an explicit resolution
failure. The graph is not rewritten to another crossfader variant, and the
legacy backend remains an explicit separate request.

## Boundary proof

This slice demonstrates:

- one family is insufficient for three distinct node types;
- graph nodes reference exact component contracts;
- backend selection resolves exact bindings only after graph validation;
- a transparent compound exposes an internal parameter without hiding its
  graph;
- instrument and device mappings remain outside the DSP graph;
- Gills, instrument, graph, Ksoloti Core, and backend stay independent;
- build results/evidence are immutable records outside catalog curation; and
- the direct frontend can consume the same graph without making `.axp` or Java
  authoritative.
