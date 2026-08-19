# ADR 0016: Adopt a portable desktop host runtime with JUCE as the audio and MIDI adapter

- Status: accepted
- Date: 2026-08-19
- Extends: ADRs 0010, 0011, and 0014 without changing their client or evidence boundaries

## Context

Schuss now has a client-neutral semantic model, portable projects, a reusable
compiler front half, exact Ksoloti lowering and ARM builds for a bounded graph,
a maintained React/Tauri desktop client, and a separate AI/MCP authoring lane.
Those pieces make it possible to author and inspect instruments, but the normal
sandbox is still tied either to bounded Python host evaluation or to a
resource-constrained Ksoloti target.

The desired next capability is a substantially less constrained desktop audio
sandbox in which the same authoritative Schuss graph can run directly on a Mac
with normal audio and MIDI devices. This should shorten the edit-listen-debug
loop and allow ideas to be refined before a compatible subset is exported to
Ksoloti. It must not turn a desktop framework, graphical patcher, MIDI
controller, CLI, or AI client into a competing semantic model.

Tauri and its webview are suitable for presentation and explicit application
commands, but they are not the real-time audio and physical-MIDI runtime.
Physical MIDI routed through JavaScript, JSON, Python, and then an audio process
would add unnecessary timing and lifecycle boundaries. Conversely, making
individual Schuss objects inherit a desktop audio framework's object model
would couple the canonical DSP graph to one host implementation and make later
targets harder rather than easier.

Schuss is currently a private, personal, non-distributed application. JUCE
licensing is therefore not a planning gate for this work. The implementation
may use the simplest available private-development route. Any later decision
to distribute, sell, publish a packaged binary, or materially change that use
must review the applicable JUCE and third-party terms before release.

## Decision

Schuss will add a portable native desktop execution path under Task 031.

The authoritative Schuss project, component contracts, DSP graph, instrument,
implementation bindings, and exact references remain unchanged in ownership.
The desktop path is a new backend and runtime realization of those semantics;
it is not a new graph format and does not derive authority from a JUCE graph,
a Tauri view, or generated desktop code.

A JUCE-independent C++ library named `schuss_rt` will own the portable native
runtime. It will consume one validated, content-addressed host-runtime package,
instantiate registered node implementations, allocate graph buffers and state,
apply timestamped events, execute one fixed processing schedule, and produce
audio. Its public runtime ABI may not expose JUCE, Tauri, React, Python,
Core Audio, Core MIDI, Ksoloti Java, or legacy `.axp` types.

A separate headless `schuss-audio-engine` process will use JUCE only as the
host adapter around `schuss_rt`. JUCE will own audio-device and MIDI-device
enumeration, Core Audio and Core MIDI integration, callback lifecycle, sample
rate and buffer-size negotiation, and bounded runtime telemetry. Physical MIDI
will enter that native process directly and will be timestamped and queued for
the audio callback without passing through React, Tauri JSON, or Python.

The existing compiler front half will lower the same canonical graph through
separate target selections:

```text
canonical Schuss project and graph
        |
        +-- desktop host backend
        |      -> host-runtime package
        |      -> schuss_rt
        |      -> JUCE / Core Audio / Core MIDI
        |
        `-- Ksoloti backend
               -> retained Ksoloti lowering and ARM artifact
               -> optional hardware export
```

The Ksoloti backend remains a sibling export target. A desktop session never
becomes the source for Ksoloti generation, and Schuss will not translate JUCE
objects or host-generated C++ back into firmware. Host-only implementations
may be added later, but their presence must produce an exact Ksoloti
compatibility result rather than an implicit fallback or silent omission.

The React/Tauri desktop, CLI, AI semantic layer, and MCP adapter remain clients
of shared Schuss operations. Task 031 does not choose or redesign node-editor
interaction, object browsing, AI musical reasoning, controller-mapping UX,
scene behavior, or any other presentation concern. A later client-integration
task may expose the accepted host-session operations without changing their
semantics.

Task 031 is divided into four parent-owned, serialized children:

1. **031A:** host-runtime contracts, target/backend identity, package and
   operation boundaries, and exact ownership allocation;
2. **031B:** portable JUCE-independent `schuss_rt` runtime and node ABI;
3. **031C:** exact host lowering plus deterministic headless offline rendering
   for the accepted Task 026 seven-node profile; and
4. **031D:** headless JUCE real-time audio/MIDI engine and process-local shared
   audio-session service, with no Tauri, React, AI, or MCP implementation.

Acceptance of this ADR and the Task 031 parent contract does not automatically
activate any child. Each child requires an explicit start decision within the
parent's fixed scope and ownership rules.

## Consequences

Schuss gains a path toward making the desktop host the primary experimental
sandbox while preserving Ksoloti as a deliberate constrained export target.
The same musical graph can eventually be evaluated with more CPU and memory,
then checked separately for Ksoloti implementation coverage and resources.

The native runtime, host package, engine protocol, and process-local session
service become core infrastructure usable by future UI, CLI, AI, testing, and
other host adapters. JUCE remains replaceable because it is outside the
portable runtime ABI and the semantic model.

The architecture introduces a native C++ build, a second process, a private
control protocol, real-time safety obligations, and target-specific host
implementation bindings. Those costs are accepted because they isolate timing
and device work from Python and the webview instead of spreading real-time
requirements through every client.

Offline rendering, native compilation, one local real-time smoke, resource
measurements, connected Ksoloti execution, and subjective listening remain
separate evidence statements. Running through JUCE does not by itself prove
real-time headroom, stable behavior on other machines, audible quality, target
equivalence, release readiness, or distribution compliance.
