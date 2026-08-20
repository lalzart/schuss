# Instrument Lab v1

Instrument Lab is a repository-owned, non-production support library for
validated DSP prototypes. It shares only bounded host, MIDI-envelope,
descriptor, renderer-artifact, CMake, and evidence mechanics proven by both
Cinderwheel and Tide Pit.

It does not own musical DSP, semantic controls, state meanings, source
equivalence, experiments, comparators, JUCE device lifecycle, or canonical
Schuss identity. Its C++ API contains no Schuss graph/provider/runtime types and
does not make a prototype topology executable.

Consumers link `SchussInstrumentLab::Core` and supply composition adapters.
The lab never chooses a numeric representation, sample rate, internal quantum,
event type, reset behavior, controller mapping, or output conversion.

The CMake helper in `cmake/SchussInstrumentLab.cmake` authenticates the exact
JUCE 8.0.15 source used by the two prototypes, but it never fetches unless the
consumer explicitly enables the exact pinned archive. JUCE remains outside the
portable lab target.

Evidence is limited to deterministic source generation, host structure, host
signal, and authenticated target build. Callback deadlines, restart safety,
physical MIDI, app launch, listening, distribution, and production integration
remain separate gates.
