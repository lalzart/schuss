# Phase 4A semantic catalog pilot

## Result

The pilot contains 26 user-facing families and 38 implementation records. It
covers all 13 top-level categories with exactly two families per category. The
overlay references 38 distinct object observations and two complete `.axs`
graph observations from the frozen Phase 3 snapshot; it copies no legacy graph
or object record.

This is structural and curation evidence only. All Ksoloti Core/legacy-backend
compatibility entries are `not-evaluated`. No code generation, ARM compile or
link, connected-device check, or listening test occurred.

## Selection by primary category

| Category | Families |
| --- | --- |
| Input & Output | Audio Input; Audio Output |
| Sound Sources | Sine Oscillator; Uniform Noise |
| Sampling & Buffers | Table Recorder; Granular Buffer Processor |
| Modulation & Control | ADSR Envelope; Sine LFO |
| Filters & Resonators | State-variable Filter; Physical-model Resonator |
| Shaping & Dynamics | Compressor Gain Computer; Hard Clip |
| Delay & Reverb | Feedback Echo; Tape Delay |
| Spectral & Analysis | 24-band Spectrum Analyzer; 128-point Real FFT Display |
| Mixing & Routing | Four-input Mixer; Crossfader |
| Pitch & Notes | MIDI Note to Frequency; Scale Quantizer |
| Timing & Sequencing | Internal MIDI Clock; 16-step Pitch Sequencer |
| Data, Math & Logic | Addition; Boolean AND |
| Interface & System | Gills Text Display; Smoothed Analog GPIO Input |

Selection favored semantic contrast and model stress over graph-reference
frequency. The set mixes simple primitives with dense objects and compounds,
and includes `axoloti-factory`, `axoloti-contrib`, `ksoloti-objects`, and
provider-only `patcher` provenance without using any of those names as a
functional category.

## Difficult cases exercised

- Audio Input and Audio Output each group built-in, USB, and external-I2S
  implementations under one family while leaving transport and target
  requirements below family identity.
- ADSR Envelope and Sine LFO group related factory and Ksoloti implementations
  without treating repository ownership as function.
- Four-input Mixer, Crossfader, and Addition group two or three same-name
  control/audio/integer overloads. Frozen graph selection includes ambiguity
  for Crossfader and Addition; the family grouping does not erase it.
- Hard Clip references object observation 99 and complete graph 1047 (13
  instances, 12 nets). Tape Delay references object 752 and complete graph 5
  (16 instances, 14 nets). Their authoritative future form remains an
  inspectable Schuss compound, not an opaque `.axs` or emitted `.axp`.
- The granular processor has 18 inlets, two outlets, and 14 parameters; the
  physical-model resonator has 24 inlets, two outlets, and 21 parameters. The
  pitch sequencer contributes 16 parameters. These exercise port- and
  parameter-heavy curation without copying facet payloads into the overlay.
- Generated objects are represented explicitly, and the provider-only RFFT
  observation remains a separate implementation rather than being silently
  merged with the file-backed RFFT definition.

## Resolved and deferred cases

- `schuss-family-000006` is confirmed under Sampling & Buffers. Granular
  buffer capture and manipulation define its primary drawer role; delay,
  pitch, feedback, and reverb remain secondary functions.
- `schuss-implementation-000023` remains explicitly deferred under
  `PROVIDER_FILE_IDENTITY_UNPROVEN`. Its provider
  class, name, and facets match the file-backed RFFT family, but Phase 3 could
  not prove whether it is a duplicate observation or a distinct emitted
  component.
- Preferred implementation selection and most core promotion remain
  `not-evaluated`; target/backend selection cannot be inferred from resolver
  presence or source order.
- External-system crosswalks remain approximate navigation guidance. They do
  not establish one-to-one object equivalence.

## Recommended next scope

First validate the pilot with drawer/query exercises and retain the flagged
provider-membership question until stronger identity evidence exists. Then Phase 4B may expand the same model
toward roughly 150-250 manually reviewed families, while preserving explicit
unresolved membership. In parallel roadmap order, define only the minimal
Gills device-profile/instrument reference contract needed before the Schuss
graph/backend and shared-operation contracts harden.
