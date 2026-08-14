# Parameter and interaction model

Schuss keeps graph connectivity, public control, structural configuration,
events, and presentation distinct. A legacy format may serialize several of
these together; the Schuss model must not.

## Facets

| Facet | Meaning | Typical lifetime | Graph-connectable |
| --- | --- | --- | --- |
| Port | Typed data, audio, control, or event endpoint on a node | Graph topology | Yes |
| Parameter | Runtime value with a defined domain and update behavior | Performance/state | Through an explicit binding |
| Attribute | Structural or compile-time configuration | Object/graph build | No |
| Action | Discrete command or gesture such as trigger, clear, or save | Event | Through an explicit event binding |
| Display | Read-only presentation value or formatted view | Runtime presentation | No |

### Ports

Ports define direction, value/event type, rate, units when known, and
cardinality. A connection joins compatible ports. A UI control is not a port,
and a parameter becomes graph-connectable only through an explicit binding or
modulation contract.

Future component contracts also keep domain, channel shape, semantic role,
value representation, range, optionality, and buffer/reference ownership
independent. Direct cables require compatible dimensions. Rate conversion,
channel reshaping, unit/range conversion, event latching, and
parameter-to-stream promotion use explicit nodes or bindings; a backend never
inserts them silently. The normative minimum type shape and illegal implicit
conversions are in `docs/SCHEMA_STRATEGY.md`.

### Parameters

Parameters define a stable semantic ID, value type, domain, default, units,
update rate, smoothing/quantization behavior when relevant, and automation or
state rules. Display range and panel mapping are presentation concerns and may
differ from the internal domain.

### Attributes

Attributes choose structure or code-generation behavior: table sizes, modes
that alter ports, compile-time options, resource allocation, and references are
typical examples. A value that must change continuously during performance is
not an attribute.

### Actions

Actions are discrete and may carry a typed payload. Trigger, reset, commit,
load, and clear should not be represented as magic parameter values. Gesture
recognition belongs to a device/instrument mapping; the resulting action is
device-independent.

### Displays

Displays expose state for presentation. They declare value or text shape,
formatting responsibility, update cadence, and ownership. A display is not a
hidden parameter and does not acquire write semantics merely because a legacy
widget allowed editing.

## Identity and mapping

Stable facet IDs are local to a stable object or instrument identity and do not
contain category paths or UI coordinates. Labels, grouping, layout, color, and
control placement may change without changing identity.

Mappings are explicit records between:

- device controls or gestures;
- instrument parameters or actions; and
- graph parameters, ports, or actions.

Mappings carry transforms, range shaping, polarity, response time, and feedback
behavior. They do not rewrite the underlying parameter definition.

The full exposure chain remains explicit:

```text
implementation seam
    -> component-contract facet
    -> compound public facet
    -> instrument public parameter/action/display
    -> device control/gesture/feedback slot
```

An implementation binding owns the first realization map. A component
contract owns stable public facet IDs and compound mapping keys. A transparent
graph owns the concrete internal exposure targets. An instrument owns graph
and device mappings. No layer copies or redefines the target facet.

## Legacy import rule

The Java-resolved inventory exports legacy inlets, outlets, parameters,
attributes, displays, modulators, and instance values as distinct observations.
It must not collapse them into the final Schuss contract. Any later semantic
normalization retains a trace back to the source observation and records
uncertainty.
