# Task 042: Layerwell desktop meta-instrument

Status: explicitly authorized and completed locally from the user's 2026-08-23
request to implement the agreed standalone desktop meta-instrument. This task
owns a noncanonical Instrument Lab prototype only. It preserves the inherited,
then-uncommitted Task 041 closeout and authorizes no Git, app-launch, audio/MIDI
endpoint, controller-configuration, hardware, listening, or publication action.
A later explicit Git request committed the Task 042 prototype locally at
`7a66949`; it did not authorize a push or change any evidence boundary.

## Goal and why it exists

Build **Layerwell**, a small desktop-only live sampler that embeds the exact
portable Tide Pit Gills 0.1 and Schuss Generative Drums 0.6 Cores, lets a
performer select and control either source from a regular Novation Launch
Control 3, and captures up to three synchronized stereo layers without
requiring Ableton Live or another audio-routing host.

The task exists because the musical operation is distinct from either source
instrument: choose a source, shape it, capture a phrase, then add one or two
aligned layers while continuing to perform. Layerwell owns that capture and
mix interaction; it does not invent a third source synthesizer or change the
two source instruments' musical behavior.

The literal working artifact is a built `Layerwell.app` JUCE 8.0.15 standalone
plus deterministic Core renders and accepted-state/controller traces. The
maximum evidence level in this task is authenticated target build and synthetic
host signal. A built app is not a launched app, real-time callback result,
physical-controller result, listening result, or production integration.

## In scope

- A completed new-design proposal at `research/proposals/layerwell.md`, followed
  by a ready Sonic Research Lab implementation bundle bound to its exact bytes.
- A noncanonical prototype at `research/prototypes/layerwell/` using portable
  C++17, Instrument Lab v1, and the authenticated JUCE 8.0.15 build seam.
- Read-only reuse of Tide Pit Gills 0.1 and Generative Drums 0.6 public Cores,
  instrument-owned descriptors, control reducers, exact source/dependency
  authorities, and retained notices.
- The smallest CMake-only composition guards required to link the two existing
  prototype libraries under one parent without creating duplicate Instrument
  Lab targets or changing either source instrument's standalone build.
- Exactly two selectable source instruments in revision 0.1. Unselected sources
  retain state but do not advance; the selected source advances while selected.
- Exactly three stereo layer slots plus one staging buffer, preallocated for a
  maximum 32-second session loop at 48 kHz.
- Source-only capture. The current layer mix is never recursively resampled.
- The first valid capture starts immediately and its stop establishes the
  session loop length. Later captures begin at the next loop boundary, record
  exactly one session cycle, then atomically replace the selected layer.
- Provisional replacement: cancellation, invalid duration, overflow, or other
  capture failure leaves the previously committed layer unchanged.
- Per-layer level, pan, selection, and mute; session-level source monitor and
  master level; bounded output clipping diagnostics; no callback allocation,
  locks, filesystem access, MIDI output, or UI work in the portable Core.
- A regular Launch Control 3 DAW-mode adapter using the dedicated DAW USB port:
  Page buttons select the source; DAW Control maps the selected source's 16
  encoders and eight buttons; DAW Mixer maps three layers and capture; Track
  buttons select layers; accepted state drives encoder positions, LEDs, and
  fixed-size OLED text messages.
- Explicit DAW-mode enable, relative-row configuration, accepted-state resync,
  endpoint-change cleanup, and DAW-mode disable messages, all covered by
  synthetic protocol tests without opening a MIDI endpoint.
- A restrained JUCE standalone UI for source, layer, capture, audio, and MIDI
  diagnostics. UI projections must come from accepted Core state rather than
  untreated raw MIDI.
- Deterministic Core, capture-boundary, partition, source-composition, mapping,
  protocol, signal-safety, and authenticated target-build evidence.

## Out of scope

- Ableton Live integration, plug-in formats, ReWire, aggregate/system audio
  capture, virtual loopback devices, wrapping or launching separate binaries,
  or hosting arbitrary executables or plug-ins.
- More than two sources or three layers; overdub into a layer; composite-mix
  resampling; slicing; one-shots; timestretch; pitch-shift; reverse; fades as
  editable effects; quantization to an external clock; MIDI clock; or transport
  synchronization.
- File import, sample export, session save/restore, autosave, crash recovery,
  preset storage, or disk-backed buffers.
- Changes to Tide Pit or Generative Drums DSP equations, source state, timing,
  mappings, defaults, labels, source revisions, source manifests, or retained
  evidence.
- Canonical Schuss families, components, graphs, bindings, providers, factories,
  record sets, instruments, projects, machines, operations, application-library
  entries, schemas, or production runtime integration.
- Ksoloti/Gills target builds, firmware changes, board access, USB access,
  controller programming, physical MIDI/audio endpoint access, app launch,
  listening claims, distribution review, packaging, notarization, publication,
  staging, commit, push, or remote mutation.
- A culturally derived mechanism or identity claim. Revision 0.1 uses no
  repertoire, recording, name, image, or structural mechanism sourced from a
  musical community.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, current governance, ADRs 0016-0018,
   and `docs/workflows/instrument-development.md`.
2. The Sonic Research Lab new-design workflow and the user's uninterrupted
   implementation authorization in this thread.
3. `research/prototypes/tide-pit-gills/` and its exact source-reimplementation
   contract, source-equivalence authority, public Core, mapping, and notices.
4. `research/prototypes/generative-drum-machine/` and its ready new-design
   bundle, public streaming Core, mapping, physical source packages, and notices.
5. Instrument Lab v1 and the authenticated JUCE 8.0.15 source-tree manifest.
6. The repository regular Launch Control 3 topology plus Novation's official
   programmer guide for DAW-mode messages, control indices, display, LEDs,
   Page/Track events, and cleanup requirements.
7. Ableton Looper/resampling and other cited prior art as behavior comparison
   only, not as a runtime dependency or novelty claim.

### Deliverables

1. Completed `research/proposals/layerwell.md` with claim labels, exact state,
   equations, control map, failure behavior, experiment, and proof gaps.
2. A ready implementation bundle under
   `research/prototypes/layerwell/contract/`, bound to the proposal hash and
   explicit approval reference.
3. Portable Layerwell Core, two source adapters, fixed-capacity event and state
   boundaries, deterministic renderer, and focused tests.
4. Instrument-owned semantic control surface, LC3 DAW protocol adapter,
   accepted-state feedback model, and synthetic bidirectional protocol tests.
5. Authenticated JUCE standalone target and restrained state-driven UI, built
   but not launched.
6. Prototype index, complete DSP topology, promotion needs, implementation
   handoff, results, gaps, retained source/dependency fingerprints, and notices.
7. Focused, adjacent, native, fresh-root, and routine-current validation results
   appropriate to the files actually changed.

## Acceptance tests

1. The proposal is complete and the implementation bundle passes Sonic Research
   Lab structure and ready validation before DSP implementation begins.
2. One parent build links both exact public source Cores and one Instrument Lab
   authority. Duplicate target, symbol, source, or notice authority fails closed;
   both source prototypes' existing focused suites remain unchanged and pass.
3. At 48 kHz, supported outer blocks `16`, `64`, `128`, and `512` produce the
   same accepted event trace, layer state, capture boundaries, PCM, and metrics
   for the frozen timeline.
4. The first valid capture length is inclusive of recorded frames before the
   stop event, lies in `[24000, 1536000]`, resets transport to phase zero on
   commit, and establishes the exact later-layer cycle length.
5. A later capture waits for the next session boundary, records exactly one
   cycle from the selected source only, and swaps staging/committed storage in
   bounded time. Cancellation, short first capture, event overflow, and invalid
   process shape do not replace the old layer.
6. Three committed layers remain phase aligned through source changes, layer
   selection, mute, level, pan, monitor, replacement, and clear. Clearing the
   last committed layer returns the session to no-loop state.
7. Prepare allocates the four fixed stereo buffers; repeated `process()` calls
   allocate nothing, take no lock, perform no I/O, emit only finite samples,
   remain within `[-1, 1]`, and report any limiting or event drops explicitly.
8. Source controls terminate at each source's existing public mapping reducer.
   Source selection preserves accepted state; the inactive Core is not advanced.
9. Synthetic LC3 tests cover DAW enable/disable, mode reports, relative encoder
   rows, Page source selection, Track layer selection, DAW Control and Mixer
   maps, Shift-clear, reconnection/resync, LED/encoder/OLED output, invalid MIDI,
   and endpoint-change cleanup. Raw MIDI never becomes displayed state directly.
10. The authenticated JUCE 8.0.15 `Layerwell.app` target compiles and links
    without launching the app or opening audio/MIDI endpoints.
11. Instrument Lab prototype validation, fresh-root Core reproduction, affected
    source-prototype regressions, and Schuss `current` pass after implementation
    freeze. Full compatibility/release is required only if an accepted shared
    executable, schema, manifest registration, or canonical authority changes.
12. Results and gaps keep target-build, synthetic timing, physical controller,
    real-time, listening, distribution, and production claims independent, and
    no inherited Task 041 or unrelated dirty file is overwritten or staged.

## Validation plan

1. Run proposal/bundle structure and readiness validation.
2. Prove the combined source-link target before writing capture behavior.
3. Iterate with focused Layerwell Core, state, capture, mapping, protocol, and
   render tests; use sanitizers for the portable Core boundary.
4. Run the existing focused Tide Pit and Generative Drums suites as adjacent
   regression, without reproducing unrelated instruments.
5. Freeze behavior, fixtures, and comparators; then run the block-partition
   matrix, allocation/safety checks, authenticated JUCE build, and one relocated
   Instrument Lab reproduction.
6. Run Schuss `current` once after documentation and implementation stabilize.
   Use `--plan` before any additional native or reproduction profile check and
   select each affected expensive check once. Compatibility or release is not
   the default for this isolated noncanonical prototype.

## Decisions

### Task 042 may decide

- Internal class/file names, fixed-buffer ownership, event representation,
  snapshot transport, UI layout, colors, diagnostic wording, and deterministic
  fixture format within the frozen musical and evidence boundaries.
- The exact bounded ramp or click-suppression implementation at capture commit,
  provided it is deterministic, callback-safe, and objectively tested.
- Relative-encoder step sizes, default layer/monitor/master gains, and safe
  headroom inside the proposal's exact declared ranges.
- The smallest CMake guard or parent-composition seam that retains both source
  prototypes' independent builds and exact source authorities.

### Task 042 must not decide

- New source instruments, arbitrary instrument discovery/loading, a plug-in ABI,
  canonical Schuss promotion, catalog/provider identity, or application-library
  integration.
- Changes to either embedded source instrument's musical identity, DSP, mapping,
  source authority, or existing evidence.
- A different controller model, faders, controller firmware behavior not stated
  by Novation, or physical success inferred from synthetic MIDI.
- Persistence, file formats, external synchronization, advanced sample editing,
  distribution terms, hardware behavior, listening quality, or production
  readiness.
- Adoption, deletion, staging, committing, pushing, or publishing of the
  inherited Task 041 closeout or any unrelated worktree content.

## Stop condition

Stop when the proposal and ready bundle are retained, the bounded Layerwell
prototype and authenticated standalone target pass the applicable checks, and
`RESULTS.md`/`GAPS.md` truthfully record the evidence ceiling. Do not launch the
app, open an endpoint, configure the controller, claim listening quality,
integrate the prototype into canonical Schuss/application records, or perform a
Git action without separate explicit authorization.
