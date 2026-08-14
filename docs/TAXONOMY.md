# Catalog taxonomy

## Policy

Schuss browses by function, filters by form, and exposes provenance for
inspection. Filesystem layout and library ownership are evidence about origin;
they are not musical meaning.

This document fixes the classification rules and the Phase 4A draft functional
tree. The tree is a reviewed starting hypothesis, not an immutable standard.
A later change must record a concrete semantic or drawer-usability reason.

## Classification axes

Each catalog entry may carry independent facets:

- **Function:** what the object does in a musical or signal-processing graph.
- **Abstraction level:** primitive, compound, or instrument.
- **Signal role:** audio, control, event, data, display, or mixed.
- **Form:** generator, native object, legacy subpatch, Schuss compound, asset,
  or target-specific implementation.
- **Provenance:** source repository, author evidence, original path, byte hash,
  and explicit license evidence.
- **Compatibility:** declared or verified target/backend support, with the
  evidence level attached.
- **Status:** raw, resolved, curated, deprecated, unresolved, or unsupported.

Function may be hierarchical, but every family has exactly one canonical
primary category for predictable drawer placement. Secondary functions use
controlled tags. The other axes must not be encoded by pretending they are
function branches.

## Rules

1. Stable IDs never contain category paths, source-library names, or display
   labels that curators may change.
2. `factory`, `community`, `user`, repository names, and author names are
   provenance facets only.
3. `primitive`, `compound`, and `instrument` are abstraction levels only.
4. Help patches, examples, and demos retain those raw roles but are not
   automatically catalog categories.
5. A path or object name may suggest a candidate function, but raw inventory
   may not promote that suggestion to curated truth.
6. Missing, conflicting, or ambiguous classification remains explicit rather
   than being filled by a heuristic.
7. Compounds remain expandable to their complete graph.
8. Preferred/core status is a manual curation decision, separate from source
   priority or load order.

## Curation gate

A functional category becomes canonical only when its definition, inclusion
criteria, exclusions, and representative objects are reviewed together. The
inventory task may collect candidate labels and legacy paths as evidence but
must not establish the final tree.

## Phase 4A functional vocabulary v0

The stable classification values are the slugs shown below. Human-facing
labels and the tree may be revised without changing family or implementation
identity. Representative objects are evidence examples, not automatic rules
for classifying everything with a similar path.

The external-system notes are approximate conceptual crosswalks. They do not
claim identical object granularity, terminology, signal types, or package
boundaries across Ableton Live, Max/MSP, Pure Data, REAKTOR, and VCV Rack.

### 1. Input & Output (`input-output`)

- **Purpose:** move musical audio, control, event, or note information across
  the boundary of a graph or host-facing stream.
- **Include:** audio input/output endpoints, MIDI ingress/egress, and explicit
  graph boundary ports.
- **Exclude/boundary:** physical pin configuration belongs in Interface &
  System; internal fan-out belongs in Mixing & Routing; buffers are Sampling &
  Buffers.
- **Likely subcategories:** audio input, audio output, MIDI input, MIDI output,
  graph ports, external control protocols.
- **Representative legacy objects:** `audio/in stereo`, `audio/out stereo`,
  `midi/in/keyb`, `midi/out/note`, `ksoloti/usbaudio/in stereo`.
- **Approximate crosswalk:** Live Audio/MIDI tracks and External
  Instrument/Audio Effect I/O; Max `adc~`, `dac~`, and MIDI objects; Pd
  `adc~`/`dac~` and MIDI objects; REAKTOR Audio/MIDI Terminal modules; VCV Rack
  Audio and MIDI/CV interface modules.

### 2. Sound Sources (`sound-sources`)

- **Purpose:** create an audio signal whose main use is as sound material.
- **Include:** oscillators, noise, drum voices, physical-model voices, and
  complete sound generators.
- **Exclude/boundary:** sub-audio cyclic modulators go in Modulation & Control;
  playback from stored media goes in Sampling & Buffers; pitch utilities go in
  Pitch & Notes.
- **Likely subcategories:** periodic oscillators, noise, wavetable/vector,
  percussion, physical modeling, voice generators.
- **Representative legacy objects:** `osc/sine`, `noise/uniform`, `edrum/bd1`,
  `sptnk/osc/vosim`, `fx/lmnts/string`.
- **Approximate crosswalk:** Live Instruments; Max/MSP oscillator/noise objects
  and instrument patches; Pd audio generators; REAKTOR Oscillator and sound
  generator modules; VCV Rack Oscillator, Noise, Drum, and Physical Modeling
  tags.

### 3. Sampling & Buffers (`sampling-buffers`)

- **Purpose:** capture, store, address, play, or transform time-indexed sample
  data and working buffers.
- **Include:** table allocation, record/play heads, sample playback, looping,
  granular buffer processors, and buffer persistence operations.
- **Exclude/boundary:** ordinary delay effects go in Delay & Reverb; generic
  data arrays without sample semantics go in Data, Math & Logic; file/device
  services go in Interface & System.
- **Likely subcategories:** allocation, recording, playback, looping, granular,
  table access, persistence.
- **Representative legacy objects:** `table/record`, `table/play pitch`,
  `table/alloc 16b sdram`, `wave/play stereo`, `fx/clds/clds`.
- **Approximate crosswalk:** Live Simpler/Sampler and audio clips; Max
  `buffer~`, `record~`, `play~`, and `groove~`; Pd arrays plus `tabread~` and
  `tabwrite~`; REAKTOR Sampler/Grain modules; VCV Rack Sampler and Granular
  tags.

### 4. Modulation & Control (`modulation-control`)

- **Purpose:** generate, shape, combine, or map signals primarily used to vary
  other behavior over time.
- **Include:** LFOs, envelopes, ramps, slew/glide, random modulation, control
  sources, and macro mapping helpers.
- **Exclude/boundary:** audio-rate sound generators belong in Sound Sources;
  clocks and ordered event patterns belong in Timing & Sequencing; hardware
  controls belong in Interface & System.
- **Likely subcategories:** LFO, envelope, ramp/slew, random, mapping, macro,
  modulation routing.
- **Representative legacy objects:** `lfo/sine`, `env/adsr`, `dist/slew`,
  `ctrl/dial p`, `ksoloti/env/adsr loop`.
- **Approximate crosswalk:** Live Modulators, envelopes, and MIDI modulation
  devices; Max control-rate generators and `line~`; Pd `line`, `vline~`, and
  control generators; REAKTOR LFO/Envelope/Modulation modules; VCV Rack LFO,
  Envelope Generator, Random, and Slew Limiter tags.

### 5. Filters & Resonators (`filters-resonators`)

- **Purpose:** shape a signal through frequency-selective response or sustained
  resonance.
- **Include:** low/high/band-pass filters, equalizers, combs used as resonators,
  modal/string resonators, and convolution filters.
- **Exclude/boundary:** time-domain echoes belong in Delay & Reverb; static or
  nonlinear waveshaping belongs in Shaping & Dynamics; FFT analysis belongs in
  Spectral & Analysis.
- **Likely subcategories:** low/high/band/notch, multimode, equalization,
  resonators, comb/modal, convolution.
- **Representative legacy objects:** `filter/lp`, `filter/multimode svf m`,
  `filter/eq5hq`, `filter/fdbkcomb`, `fx/lmnts/lmnts`.
- **Approximate crosswalk:** Live Filter/EQ/Resonator audio effects; Max
  `filtergraph~`, `biquad~`, and resonator externals; Pd filter objects and
  resonator patches; REAKTOR Filter/Resonator modules; VCV Rack Filter,
  Equalizer, and Physical Modeling tags.

### 6. Shaping & Dynamics (`shaping-dynamics`)

- **Purpose:** alter amplitude, contour, or waveform nonlinearly or according
  to signal level.
- **Include:** gain/VCA, clipping, saturation, wavefolding, distortion,
  compression, limiting, gates, and envelope-controlled dynamics.
- **Exclude/boundary:** linear mixing belongs in Mixing & Routing; filter-only
  tone shaping belongs in Filters & Resonators; modulation envelope generation
  belongs in Modulation & Control.
- **Likely subcategories:** gain/VCA, clipping/saturation, distortion/folding,
  compression/limiting, gates/expanders.
- **Representative legacy objects:** `gain/vca`, `dist/hardclip`, `dist/soft`,
  `dyn/comp`, `sptnk/effect/noise gate`.
- **Approximate crosswalk:** Live Dynamics and Drive audio effects; Max/MSP
  gain, clipping, and dynamics patches; Pd arithmetic/waveshaping and dynamics
  externals; REAKTOR Amplifier/Shaper/Dynamics modules; VCV Rack VCA,
  Distortion, Wave Shaper, and Compressor tags.

### 7. Delay & Reverb (`delay-reverb`)

- **Purpose:** create audible time displacement, repeats, diffusion, or
  reverberant space.
- **Include:** echoes, feedback delays, tape-style delays, chorus/flange when
  delay is the primary mental model, diffusers, and reverbs.
- **Exclude/boundary:** raw storage/read-write primitives belong in Sampling &
  Buffers; combs presented primarily as resonators belong in Filters &
  Resonators; pitch-only modulation belongs in Pitch & Notes.
- **Likely subcategories:** simple delay, feedback/tempo delay, modulation
  delay, diffusion, algorithmic reverb, convolution reverb.
- **Representative legacy objects:** `delay/echo fdbk mix`, `fx/rngs/reverb`,
  `fx/chorus`, `cpwitz/delay/tape-delay`, `stomps/reverb1`.
- **Approximate crosswalk:** Live Delay/Reverb/Chorus-Flanger effects; Max
  `tapin~`/`tapout~` and reverb abstractions; Pd delay-line and reverb patches;
  REAKTOR Delay/Reverb modules; VCV Rack Delay and Reverb tags.

### 8. Spectral & Analysis (`spectral-analysis`)

- **Purpose:** inspect signals or operate in spectral/frequency-domain
  representations.
- **Include:** FFT transforms, spectrum displays, scopes, meters, pitch/level
  analysis, and vocoders when spectral transformation is primary.
- **Exclude/boundary:** tonal filtering belongs in Filters & Resonators;
  read-only device presentation belongs in Interface & System; pitch
  conversion from note values belongs in Pitch & Notes.
- **Likely subcategories:** FFT/transforms, spectral processors, scopes,
  meters, spectrum, pitch/onset/level detection.
- **Representative legacy objects:** `spectral/rfft 128`,
  `spectral/analyzer 24`, `disp/scope buffer`, `disp/vu`, `fx/wrps/vocoder`.
- **Approximate crosswalk:** Live Spectrum/Tuner and spectral effects; Max
  `fft~` family and scope/meter objects; Pd `rfft~` family and analysis
  externals; REAKTOR Analyzer and FFT modules; VCV Rack Visual, Scope,
  Spectral, and Vocoder tags.

### 9. Mixing & Routing (`mixing-routing`)

- **Purpose:** combine, distribute, select, pan, crossfade, or route signals
  within a graph.
- **Include:** mixers, sums, splitters, multiplexers, demultiplexers,
  crossfaders, panners, switches, and buses.
- **Exclude/boundary:** host/device endpoints belong in Input & Output;
  mathematical addition with no routing presentation belongs in Data, Math &
  Logic; modulation mapping belongs in Modulation & Control.
- **Likely subcategories:** mixing/summing, panning, crossfade, selection,
  split/merge, buses/sends.
- **Representative legacy objects:** `mix/mix 4`, `mix/xfade`, `mux/mux 4`,
  `demux/demux 4`, `jaffa/mix/StMix4`.
- **Approximate crosswalk:** Live mixer, Utility, racks, and sends; Max
  matrix/router/mix objects; Pd `route`, `select`, and signal-mixing patches;
  REAKTOR Mixer/Router modules; VCV Rack Mixer, Switch, Panning, and Utility
  routing tags.

### 10. Pitch & Notes (`pitch-notes`)

- **Purpose:** represent, convert, quantize, transpose, or organize pitch and
  musical-note information.
- **Include:** note/frequency conversion, scales, tuning, quantization,
  transpose, chord/voice allocation, and note formatting where pitch meaning
  is primary.
- **Exclude/boundary:** MIDI transport endpoints belong in Input & Output;
  ordered note patterns belong in Timing & Sequencing; audio pitch shifting is
  a secondary tag when an effect's primary purpose is elsewhere.
- **Likely subcategories:** conversion, scales/tuning, quantization,
  transposition, harmony/chords, voice allocation.
- **Representative legacy objects:** `conv/mtof`, `harmony/note scale`,
  `harmony/note quantizer`, `phi/harmony/microscl`, `disp/note`.
- **Approximate crosswalk:** Live MIDI Pitch/Scale/Chord devices and tuning;
  Max `mtof`/`ftom` plus note-processing objects; Pd `mtof`/`ftom` and scale
  patches; REAKTOR Note Pitch/Quantizer modules; VCV Rack Quantizer and MIDI
  tags.

### 11. Timing & Sequencing (`timing-sequencing`)

- **Purpose:** generate and organize clocks, triggers, durations, ordered
  steps, and event sequences.
- **Include:** clocks, dividers/multipliers, pulse timing, counters used as
  sequence position, step sequencers, arpeggiators, and rhythmic generators.
- **Exclude/boundary:** free-running modulation belongs in Modulation &
  Control; generic Boolean/state operations belong in Data, Math & Logic;
  external MIDI clock ports belong in Input & Output while clock generation
  belongs here.
- **Likely subcategories:** clocks/tempo, pulse timing, division/multiplication,
  counters, step sequencing, algorithmic rhythm, arpeggiation.
- **Representative legacy objects:** `midi/intern/clock`, `timer/pulselength`,
  `logic/counter`, `seq/lfsrseq`, `drj/seq/stepseq_16_pitch`.
- **Approximate crosswalk:** Live MIDI sequencers, Arpeggiator, and clocked
  devices; Max `metro`, `counter`, `transport`, and sequencing patches; Pd
  `metro`, counters, and sequencers; REAKTOR Clock/Sequencer modules; VCV Rack
  Clock, Clock Modulator, Sequencer, and Arpeggiator tags.

### 12. Data, Math & Logic (`data-math-logic`)

- **Purpose:** transform values, types, conditions, and state with explicit
  data or mathematical semantics.
- **Include:** arithmetic, comparison, Boolean logic, conversion, bitwise
  operations, constants, latches, and structured data manipulation.
- **Exclude/boundary:** do not place an item here merely because it is small or
  hard to classify. Audio-presented mixing belongs in Mixing & Routing; timing
  state belongs in Timing & Sequencing; device services belong in Interface &
  System.
- **Likely subcategories:** arithmetic, comparison, Boolean, conversion,
  constants, state/memory, bitwise, strings/data structures.
- **Representative legacy objects:** `math/+`, `logic/and 2`,
  `conv/bipolar2unipolar`, `logic/latch`, `ksoloti/string/frac2string`.
- **Approximate crosswalk:** Live expression/utility functions mainly through
  Max for Live; Max arithmetic, logic, message, and data objects; Pd arithmetic,
  logic, messages, and lists; REAKTOR Math/Logic/Event Processing modules; VCV
  Rack Logic, Utility, and Function Generator tags, narrowed by Schuss
  subcategory.

### 13. Interface & System (`interface-system`)

- **Purpose:** connect a graph to physical controls, displays, hardware buses,
  runtime services, diagnostics, and explicit system configuration.
- **Include:** GPIO/ADC/PWM, Gills controls and displays, I2C/SPI/serial setup,
  patch lifecycle services, diagnostics, and device-specific presentation.
- **Exclude/boundary:** do not place any otherwise-unclassified object here.
  Audio/MIDI stream endpoints belong in Input & Output; signal analysis belongs
  in Spectral & Analysis; generic data transformations belong in Data, Math &
  Logic. New entries require a narrower subcategory or a controlled function
  tag.
- **Likely subcategories:** hardware controls, hardware outputs, displays,
  buses/protocols, runtime/patch services, diagnostics, configuration.
- **Representative legacy objects:** `gpio/in/analog`, `gpio/out/digital`,
  `gpio/i2c/config`, `ksoloti/gills/display`, `patch/cyclecounter`.
- **Approximate crosswalk:** Live control-surface, Max for Live UI, and device
  services; Max UI, scheduler, serial, and hardware objects; Pd GUI/system and
  hardware externals; REAKTOR Panel, Terminal, and System Info modules; VCV
  Rack Hardware, Visual, Controller, and Utility modules, narrowed by Schuss
  subcategory.

## Landfill prevention

`data-math-logic` and `interface-system` are not fallback buckets. A curator
must name a listed or newly reviewed subcategory and at least one concrete
function tag. If neither fits, the record remains unresolved until the
taxonomy changes for a documented semantic or usability reason. The same rule
applies to any future category called Utility, Other, Miscellaneous, or System.
