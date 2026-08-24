# Layerwell Desktop Meta-Instrument

> Status: proposed on 2026-08-23 for the explicitly authorized bounded implementation; not accepted architecture or production-ready
> Proposal revision: 0.1
> Work type: `new-design`
> Original idea: A clean desktop-only MIDI-controlled wrapper around existing Schuss instruments: browse Tide Pit and Generative Drums from a regular Launch Control 3, capture one source, then add one or two synchronized source-only layers without requiring Ableton Live.
> Implementation target: Portable C++17 Instrument Lab Core, deterministic 48 kHz renderer, regular Launch Control 3 DAW-mode adapter, and authenticated JUCE 8.0.15 macOS standalone
> Working artifact and evidence level: built `Layerwell.app` plus retained deterministic stereo renders, accepted-state traces, and synthetic Launch Control 3 protocol traces; authenticated target-build and host-signal ceiling
> Approval reference: the user's 2026-08-23 request, “Okay, let's go ahead and implement it then,” following the clarification that Layerwell will be its own standalone instrument rather than a direction to record extra Ableton Live tracks
> Decision gate: uninterrupted execution is authorized only through the noncanonical Task 042 prototype and its stated evidence ceiling; canonical promotion, app launch, endpoint access, listening, and Git publication remain separate decisions.

## 1. Product thesis

### One-sentence thesis

Layerwell turns two already playable Schuss instruments into one performance
gesture: choose a source, shape it, capture a phrase, and replace or add up to
two phase-aligned source-only layers from the same controller.

### Instrument identity

The performer hears and shapes one selected source, presses capture, and lets
that performance establish a session loop. The performer can then switch
source, select another layer, and arm a capture which starts exactly at the next
session boundary. Layerwell answers with a synchronized composite whose layers
remain independently mutable, pannable, and replaceable. The capture clock,
provisional replacement, source browser, and coherent controller feedback make
this a small instrument in its own right rather than a generic audio recorder
or a loose effect chain.

### Intended user and musical situation

A performer using one regular Novation Launch Control 3 and a Mac wants to
improvise with Tide Pit Gills 0.1 and Schuss Generative Drums 0.6 without
building a Live set, routing virtual audio, or operating separate applications.
Revision 0.1 is deliberately compact: two resident sources, three synchronized
layers, one loop length, and one direct controller surface.

### In scope

- Exact read-only composition of the public Tide Pit and Generative Drums
  streaming Cores and their existing semantic control reducers.
- One selected source at a time; the inactive source retains state and does not
  advance.
- Three committed stereo layers plus one staging buffer, all preallocated for
  at most 32 seconds at exactly 48 kHz.
- Immediate first capture, boundary-quantized later captures, provisional
  replacement, source monitor, layer level/pan/mute, and master output.
- A regular Launch Control 3 DAW-mode protocol adapter with Page, Track, DAW
  Control, DAW Mixer, Shift, encoder, LED, and OLED behavior.
- A restrained authenticated-JUCE standalone target and deterministic native
  evidence, without launching the application or opening endpoints.

### Out of scope

Ableton integration, plug-ins, arbitrary source discovery, other binaries,
system-audio capture, mix resampling, overdub, external clock, slicing,
timestretch, pitch shift, reverse, sample import/export, persistence, more than
two sources or three layers, Ksoloti/Gills execution, canonical Schuss records,
physical-controller proof, listening claims, packaging, or publication.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- Task 042 is the sole active authority and inherits uncommitted Task 041 work
  without adopting or overwriting it.
- Tide Pit's public Core accepts 48 kHz, block sizes that are nonzero multiples
  of 16 through 512, and at most 128 semantic events per call.
- Generative Drums' streaming Core accepts up to 512 frames at 48 kHz and one
  coherent `Controls` value per call.
- The existing source control maps remain semantic authorities. Layerwell owns
  only 7-bit mirrors and relative-encoder translation into those reducers.
- JUCE 8.0.15 must come from the authenticated local source seam; no download
  is permitted during the task.
- Official Novation DAW-mode documentation is protocol evidence, not physical
  receipt evidence.

### Deliverables

The proposal; an implementation-ready Sonic Research Lab bundle; portable Core,
source adapters, fixed-capacity controller adapter, renderer, and tests; an
authenticated standalone target; prototype metadata; and truthful retained
results/gaps.

### Acceptance tests

The literal tests are specified in Task 042. Central gates are exact combined
source linkage, partition-independent capture/mix output, transaction-like
replacement safety, no process allocation or I/O, source-map termination,
synthetic bidirectional LC3 coverage, authenticated target build, and explicit
separation of all higher evidence levels.

### Decisions this work may make

Prototype-local types, fixed storage ownership, event representation, UI
layout, diagnostics, colors, relative step sizes, safe gains, and the smallest
CMake composition guard needed to retain both source authorities.

### Decisions this work must not make

New source DSP, source-map changes, arbitrary hosting, canonical identity,
catalog/provider integration, controller firmware behavior absent from official
documentation, persistence formats, distribution terms, or any physical,
listening, production, or publication conclusion.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| `Layerwell.app` linked from authenticated JUCE 8.0.15 source | Target build | Standalone target configures, compiles, and links without launching | Real-time deadline, endpoint selection, physical MIDI/audio, listening, packaging, notarization, production |
| Deterministic stereo WAV, state/event trace, metrics, and LC3 protocol trace | Host signal and synthetic protocol | Frozen conditions agree across 16/64/128/512-frame partitions and all invariants pass | Musical quality, device receipt, controller firmware configuration, product readiness |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Source browsing | Page buttons move through resident instruments | User request plus official Page-button protocol | Keep; exactly two sources, wrap at ends | High |
| Source shaping | Controller surface addresses whichever source is selected | Existing source control maps | Keep public semantics; transform absolute Custom values into relative DAW-mode mirrors | High |
| First capture | One performance creates the time base | Common live-looper behavior and user intent | Keep; start now, stop defines length | High |
| Layer capture | Additional phrases align with the established loop | Looper/fixed-length prior art | Keep; arm now, start next boundary, record exactly one cycle | High |
| Replacement | A slot may be rerecorded without losing the old take on failure | Undo/replace prior art | Transform into staging-and-commit with explicit cancel | High |
| Layer mix | Independent level, pan, mute, selection | Common mixer behavior | Keep, limited to three slots | High |
| Source-only sampling | New take excludes existing loop mix | User's source-layering intent | Keep to avoid recursive gain/noise and ambiguous ownership | High |
| Visual feedback | Surface and UI show accepted state | Existing Schuss accepted-state principle and Novation feedback protocol | Keep; raw input never becomes display authority | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| Ableton Live resampling | DAW routing | Records a track or master result into another track | General routing and arrangement environment | [Live 12 routing manual](https://www.ableton.com/en/live-manual/12/routing-and-i-o/) | Layerwell should not require a session, extra tracks, or recursive resampling |
| Ableton Looper | Software audio effect | Record, overdub, undo, tempo relationship | Broad effect with host transport integration | [Live audio-effect reference](https://www.ableton.com/en/live-manual/11/live-audio-effect-reference/) | Keep immediate record/stop legibility; reject host dependence and overdub |
| Ableton Push fixed length | Controller/workstation workflow | Predetermines clip length and captures into that cycle | Clip/session authority and broad workstation state | [Push 2 manual](https://www.ableton.com/en/live-manual/12/using-push-2/) | Later Layerwell takes inherit exactly one established cycle |
| Boss RC-505mkII | Hardware looper | Multiple parallel loop tracks with track controls | Deep routing, effects, storage, synchronization | [RC-505mkII manual](https://static.roland.com/assets/media/pdf/RC-505mk2_eng01_W.pdf) | Three simple aligned tracks are enough; reject product-scale feature breadth |
| Elektron Octatrack | Hardware sampler | Recorder buffers, track recorders, replaceable captures | Sequencer, storage, slicing, extensive machines | [Octatrack MKII manual](https://www.elektron.se/wp-content/uploads/2024/09/Octatrack-MKII-User-Manual_ENG_OS1.40A_210414.pdf) | Separate staging and playback storage, but do not import its machine model |
| SooperLooper | Open-source software looper | Multiple loops, replace, undo, crossfade, MIDI | Rich JACK-oriented looping engine | [source repository](https://github.com/essej/sooperlooper) | Confirms replace/cancel and crossfade are established; Layerwell rejects the breadth |
| Roland SP-404MKII Looper | Hardware sampler/looper | Performance capture with a bounded looper workflow | Sample workstation and storage context | [reference manual](https://static.roland.com/manuals/sp-404mk2_reference_v4/en-US/8584103589852939.html) | Preserve fast capture, not the sampler workstation |
| Tide Pit Gills 0.1 | Existing Schuss source instrument | Event-driven 16-frame source Core and source gestures | Textural pitched instrument | Exact local prototype and contract | Reuse unchanged through its public Core/map only |
| Schuss Generative Drums 0.6 | Existing Schuss source instrument | Streaming authored rhythm and pooled synthesis | Percussive autonomous source | Exact local prototype and bundle | Reuse unchanged through its public Core/map only |

No hardware-sampler lane with an exact two-resident-source wrapper was found in
the bounded search. That absence is a search result, not a universal claim.

## 5. Synthesis and engineering research

| Paper, standard, or technical source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| JUCE `AudioBuffer` documentation | Owned or externally referenced multichannel sample storage | Official API documentation | Host buffer presentation and preallocation comparison | Layerwell Core storage remains standard C++ and JUCE-free |
| JUCE `AudioIODeviceCallback` documentation | Bounded audio callback contract and device start/stop lifecycle | Official API documentation | Host adapter discipline | Does not certify Layerwell's deadline behavior |
| Lamport, “Concurrent Reading and Writing” | Reasoning about bounded single-writer/shared observations | Primary paper | Accepted-state handoff design | Not an audio algorithm or proof of this implementation |
| Gray and Lamport, “Consensus on Transaction Commit” | Prepare/commit/abort state-transition vocabulary | Primary paper | Useful analogy for provisional capture | Layerwell is single-process and is not a distributed transaction system |
| Novation Launch Control 3 programmer's DAW-mode guide | Exact enable, relative rows, mode, LED, encoder, and OLED messages | Official manufacturer guide | Synthetic protocol authority | Does not prove endpoint names or physical receipt |

The API references are [JUCE `AudioBuffer`](https://docs.juce.com/develop/classjuce_1_1AudioBuffer.html),
[JUCE `AudioIODeviceCallback`](https://docs.juce.com/master/classjuce_1_1AudioIODeviceCallback.html),
[Lamport](https://www.microsoft.com/en-us/research/publication/concurrent-reading-writing/),
[Gray/Lamport](https://www.microsoft.com/en-us/research/publication/consensus-on-transaction-commit/),
and the [official Novation DAW-mode guide](https://userguides.novationmusic.com/hc/en-gb/articles/33742551451666-Launch-Control-3-programmer-s-DAW-mode).

## 6. Musical-practice research

| Named practice, community, place, and period | Source and source relationship | Structural principle | Possible translation | Context or restriction | Risk |
|---|---|---|---|---|---|
| Pauline Oliveros and Panaiotis, Expanded Instrument System, United States, documented 1991 onward | Their [1991 ICMC paper](https://quod.lib.umich.edu/i/icmc/bbp2372.1991.098/1/--expanded-instrument-system-eis?page=root%3Bsize%3D150%3Bview%3Dtext) and an [EMPAC workshop](https://empac.rpi.edu/events/research/2023/expandable-instrument-system-workshop) describe performer-controlled delay/feedback layering | Electronic memory can place a performer's past and present gestures in dialogue | General motivation for performer-owned temporal layering only | Do not use the EIS name, routing, repertoire, recordings, pedagogy, or lineage claim; an EMPAC performance notes EIS use [by special permission](https://empac.rpi.edu/events/2024/time-regained) | Appropriation or false lineage if presented as an EIS implementation |

Layerwell uses the common synchronized-loop mechanic documented by multiple
looper sources, not a culturally derived mechanism. It makes no authenticity or
lineage claim. Any future use of EIS-specific material or naming would require
direct collaboration and permission and is outside this proposal.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Prepare/commit/abort, transaction systems | Audio loopers already expose replace/undo/cancel | Record into staging; swap one buffer owner only after a complete valid take | Risk-free experimentation over a sounding layer | Partial take leaks into playback or cancel destroys old layer | Hash the committed layer before every cancel/overflow/invalid case and require identity afterward |
| Bounded single-producer/single-consumer publication | Existing local accepted-state mailboxes | Three-slot SPSC snapshot publication from callback owner to UI/feedback owner | Surface tells the truth without callback locks | Torn, raw, or stale state becomes authoritative | Sequence-tag stress test with no torn snapshot and monotonic accepted sequence |
| Modular phase accumulator, real-time systems | Common sequencer and looper timing prior art | One frame phase modulo session length; events apply before the addressed sample | Partition-independent captures and aligned playback | Callback boundaries become musical boundaries | Render the same absolute timeline at 16/64/128/512 frames and require exact identity |

These are engineering transfers, not novelty claims. The transaction analogy is
especially limited: no consensus, logging, durability, or distributed failure
model is present.

## 8. Novelty map

### Common elements

Live capture, parallel loop tracks, source monitoring, replace/cancel, fixed
length recording, relative encoders, surface LEDs, OLED labels, and embedded
sound engines all have established prior art.

### Less-common combinations found

Workstations combine sampling and sound engines, and software loopers combine
multiple tracks with MIDI control. The bounded search did not find the exact
repository-specific composition of Tide Pit and Schuss Generative Drums,
source-only three-layer aligned replacement, and full regular Launch Control 3
DAW-mode feedback.

### Proposed contribution

Within the sources searched, Layerwell's contribution is a small, explicit
contract joining those exact two owned source Cores to a transactional capture
state machine and a bidirectional controller presentation. No global novelty,
patentability, or first-in-category claim is made.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Tell the user to record extra Ableton tracks | Loses the standalone instrument interaction and direct accepted-state controller surface | User clarification and product thesis |
| Record the composite output | Recursively embeds old layers, changes gain/noise on every take, and obscures source ownership | Signal-model risk |
| Host separate apps or arbitrary plug-ins | Adds endpoint/routing/discovery ambiguity and exceeds the two exact sources | Task boundary |
| Overdub in place | Cannot preserve the old layer on cancel/failure without another full buffer and changes replacement semantics | Transactional invariant |
| Disk-backed or persistent samples | Adds callback I/O, file formats, recovery, and privacy/lifecycle decisions | Scope and real-time risk |
| Editable fades, timestretch, slicing, reverse | Turns a clear phrase looper into a sampler workstation | Product simplicity |
| External/MIDI clock in revision 0.1 | Requires another transport authority and discontinuity policy | Unresolved product decision |

## 9. Recommended architecture

### Signal flow

```text
JUCE UI or regular Launch Control 3 DAW port
  -> protocol/gesture adapter (fixed capacity)
  -> ordered Layerwell semantic events
  -> selected source adapter
       -> Tide Pit public map/Core OR Generative Drums public map/Core
       -> source stereo Q27
  -> source monitor ------------------------------+
  -> staging capture -> commit/abort -> layer 1 --+
                                     -> layer 2 --+-> pan/level/mute sum
                                     -> layer 3 --+-> master/clamp -> stereo
  -> accepted Core snapshot -> SPSC mailbox -> UI and LC3 feedback builder
```

Only the selected source is processed. Source audio, never the composite sum,
enters staging. Four owned stereo float buffers are allocated during prepare:
three committed stores and one staging store. Each layer owns a buffer index;
successful replacement swaps the selected layer's index with the staging index
in constant time.

### Executable DSP contract

| Mechanism | Equation or pseudocode | Coefficients/ranges | Gain and stability bound | Update timing | Failure behavior |
|---|---|---|---|---|---|
| Source selection | `selected = wrap(selected + direction, 2)` | two exact sources; direction -1/+1 | inactive source contributes zero and is not advanced | event applies before `sample_offset` | blocked while waiting/recording; invalid direction ignored/counted |
| Relative source control | `mirror = clamp(mirror + (value - 64), 0, 127)` then invoke existing source reducer as Custom CC `20+slot` or `40+slot` | 16 mirrors/source; encoder input 0..127, pivot 64; buttons 0/127 | exact reducer bounds accepted source state | ordered event; drum snapshot applies at next processed segment, Tide semantic event at exact segment offset | invalid slot/value counted; no raw state publication |
| First capture | press in no-loop -> recording now; later press at offset `s` commits `N = absolute(s)-start` frames | `24000 <= N <= 1536000` | only source samples copied; no feedback path | start-offset sample is included; stop-offset sample is excluded | short stop rejects and preserves empty/old slot; max length auto-commits |
| Later capture | press -> waiting; on phase 0 record exactly `N`; commit before next phase-0 sample is mixed | established `N` only | staging never read by mixer | if already phase 0, start immediately; otherwise next phase 0 | second press cancels; overflow/invalid call aborts; old owner unchanged |
| Session transport | after first commit `phase=0`; per valid frame `phase=(phase+1)%N` | `N` above | integer exact, no drift | event-before-sample convention | no-loop phase remains zero |
| Layer playback | `x_i,c = buffer_i[phase] * seam(phase,N)` when occupied and not muted | three layers | bounded by buffer sample and level | same phase for all layers | invalid buffer state silences layer and diagnoses |
| Seam ramp | edge length `F=min(128, floor(N/2))`; `g(p)=min(1, p/(F-1), (N-1-p)/(F-1))` in edge regions | fixed, noneditable 128-frame maximum; first/last sample zero | `0 <= g <= 1` | read-time only, deterministic | `F<2` silences invalid loop and diagnoses |
| Equal-power pan | `theta=(pan+1)*pi/4`; `gL=cos(theta)`, `gR=sin(theta)` | pan -1..1 | each channel gain 0..1; constant power per layer | accepted event boundary | non-finite pan resets to 0 and counts recovery |
| Mixer | `m_c = monitor*source_c + sum(active_i * level_i * g_i,c * x_i,c)`; `out_c=clamp(master*m_c,-1,1)` | layer level 0..1 default .45; monitor 0..1 default .35; master 0..1 default .55 | final finite hard bound [-1,1]; each limited sample counted | every sample after event application | non-finite contribution/output becomes zero and counts recovery |
| Event ordering | stable order `(sample_offset, ingress_sequence)`; capacity 128/call | offsets `0..frames`; unique or tie-broken sequence | deterministic across input ordering after stable sort | offset event applies before that sample; offset==frames is retained for next call only if valid API permits, otherwise rejected explicitly | overflow cancels active capture before any commit and counts drops |
| Invalid process shape | supported frames are nonzero multiples of 16 through prepared maximum | exact 48 kHz | output must be silence | whole call | source/capture/transport state unchanged; unsupported-call diagnostic increments |

Q27 source samples become float by exact division by `134217728.0f`. Float
capture storage is an implementation choice, not a source-format change.
Process-time code performs no allocation, lock, filesystem, JSON, MIDI output,
or UI work. Preparation allocates exactly `4 * 2 * 1,536,000 * 4 =
49,152,000` sample bytes, excluding container metadata and the two source Cores.

### State and timing model

States are `unprepared`, `idle_no_loop`, `playing`, `waiting_boundary`, and
`recording`. Events at an offset apply before the source and mixer process that
sample. First-capture start therefore includes its addressed sample; stop
excludes its addressed sample. A first successful commit resets phase to zero
at the commit boundary. A later take starts at phase zero and records exactly
`N` frames; its owner swap occurs before the following phase-zero sample.

| Operation | Idle/no loop | Playing | Waiting | Recording |
|---|---|---|---|---|
| Capture press | Start immediate first take | Arm selected layer | Cancel, preserve old | Cancel, preserve old |
| Source/Page change | Accept and turn monitor on | Accept and turn monitor on | Reject/count | Reject/count |
| Layer/Track change | Accept | Accept | Reject/count | Reject/count |
| Clear selected | Clear selected; if last, no-loop | Clear selected; if last, phase and length reset | Reject/count | Reject/count |
| Mute/level/pan/master/monitor | Accept | Accept | Accept | Accept |
| DAW Control/Mixer mode | Presentation change only | Same | Same | Same |
| Reset/prepare | Clear all storage/state | Only while stopped by host | Only while stopped | Only while stopped |
| Panic | Stop capture, mute transient source contribution, preserve committed buffers | Same | Same | Same |
| Recall/session restore | Unsupported | Unsupported | Unsupported | Unsupported |
| Reconnect | No Core mutation; feedback adapter resends accepted snapshot | Same | Same | Same |

Source controls preserve their accepted values across selection. Selecting a
source turns monitor on; a successful commit turns monitor off so the newly
captured phrase is not doubled. Button 8 can override the monitor state. The
last committed layer being cleared returns to no-loop state. There is no Freeze
operation beyond the capture state machine and no persistence/recall operation.

### Control and performance mapping

DAW mode uses the dedicated DAW USB port. On connection, the host emits DAW
enable `F0 00 20 29 02 16 02 7F F7`, enables relative input for both rows with
channel-7 CC69/CC72 value 127, and sends one accepted-state sync. On endpoint
change or shutdown it disables the prior surface with the same SysEx ending in
`00 F7`. Mode report/select uses channel-7 CC30 (`1` Mixer, `2` Control).

| Control or gesture | Range or states | DSP mapping | Perceptual role | Safety or pickup behavior |
|---|---|---|---|---|
| Page Up / Down, channel 1 CC106/107 | press | previous/next source | Browse Tide Pit/Drums | blocked during capture; accepted source drives display |
| Track Left / Right, channel 1 CC103/102 | press | previous/next selected layer | Choose take to edit/replace | blocked during capture |
| DAW Control encoders, channel 16 CC77..92 | relative about 64 | selected source slots 1..16 -> existing CC20..35 reducer | Shape current source | 7-bit accepted mirror; feedback uses absolute CC13..28 |
| DAW Control buttons, channel 1 indices 37..44 | press/release | selected source buttons 1..8 -> existing CC40..47 reducer | Source actions | release remains explicit; unassigned stays dark/no-op |
| DAW Mixer top encoders 1..3 | relative | layer pan -1..1, step 1/64 | Place layers | clamp, accepted-value feedback |
| DAW Mixer top encoder 4 | relative | monitor level, step 1/127 | Hear live source | clamp 0..1 |
| DAW Mixer bottom encoders 1..3 | relative | layer level, step 1/127 | Balance layers | clamp 0..1 |
| DAW Mixer bottom encoder 4 | relative | master level, step 1/127 | Overall output | clamp 0..1; final limiter remains authoritative |
| DAW Mixer buttons 1..3 | press | select layer 1..3 | Target a take | accepted selection LED |
| DAW Mixer buttons 4..6 | press | toggle layer mute 1..3 | Drop layers | accepted mute color |
| DAW Mixer button 7 | press | start/arm/cancel capture | Perform takes | state-dependent color/text; provisional buffer |
| DAW Mixer button 8 | press | toggle source monitor | Compare live/captured source | accepted monitor state |
| Shift + Mixer button 8 | chord | clear selected layer | Remove take | only rising edge; blocked during capture |

All DAW surface buttons except Shift arrive on channel 1; Shift arrives on
channel 7. Encoder inputs are relative. Output encoder positions use channel 16
CC13..28 and accepted 7-bit values. LEDs use channel 1 control indices; RGB
uses `F0 00 20 29 02 16 01 53 index R G B F7`. Stationary OLED target 53 shows
source/layer/capture and temporary target 54 shows accepted parameter name and
value. Strings and SysEx messages have fixed maximum capacity.

### Parameter interactions and edge cases

- Source or layer selection is rejected while a capture is waiting or active
  so the take's ownership cannot change halfway through.
- Muting a target layer does not stop replacement. The old muted layer stays
  muted after commit.
- Level, pan, monitor, and master edits remain legal during capture because
  source-only staging is unaffected.
- Empty layers contribute silence but retain their mix parameters.
- Pressing capture on an occupied layer always means provisional replacement;
  there is no overdub.
- At exactly phase zero, an armed later capture starts immediately. At any
  other phase it waits until the next zero.
- At maximum length, a first capture auto-commits rather than writing beyond
  capacity.
- Clear of the final occupied layer resets the session length and phase, but
  does not reset either source instrument.

### Failure behavior

Fail closed. Invalid prepare or process shapes emit silence and preserve state.
Invalid or non-finite controls are recovered to declared defaults and counted.
Any event-capacity overflow cancels a provisional capture before commit and
preserves the old layer. A failed source process emits silence for that source
segment and cannot enter staging as a successful take. Feedback generation may
drop or coalesce messages and count it, but must never block or mutate Core
state.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Sample rate | exactly 48,000 Hz | both source public contracts | no conversion in v0.1 | Feasible |
| Block size | nonzero multiple of 16, at most 512 | Tide Pit stricter contract | 16/64/128/512 canonical matrix | Feasible |
| Loop storage | four stereo float buffers, 1,536,000 frames each | arithmetic from 32 s x 48 kHz | 49,152,000 bytes samples; Core target under 64 MiB excluding JUCE | Feasible on desktop; intentionally not Gills |
| Event capacity | 128 semantic events/call | source precedents | overflow aborts provisional capture | Feasible |
| Numeric format | source Q27, capture/mix float32 | exact source APIs plus proposal equation | final finite clamp [-1,1] | Requires tests |
| Source CPU | one source advances at a time | exact public Core calls | no deadline claim | Host-build plausible; measurement deferred |
| Callback behavior | no allocation, locks, I/O, JSON, MIDI output, or UI work | code inspection/instrumented tests required | fixed capacities only | To prove structurally/synthetically |
| JUCE | exact 8.0.15 authenticated local tree | repository manifest `db7daa7f...ac5` | no network/download | Available |
| Tide Pit authority | index `8056df4d...16e2`; contract `81071c9c...8c2`; equivalence `2c661c07...747`; notices `4e198a53...8aa` | exact local hashes | read-only public target | Available |
| Drum authority | index `ecfa9c33...d4e`; contract `79c4998f...1d2`; dependencies `d61e5973...a13`; adapter `c0c56698...acd` | exact local hashes | read-only public target | Available |
| LC3 protocol | official guide plus repository topology `d69475e5...10b` | manufacturer docs/local artifact | synthetic only | Sufficient for adapter, not device proof |
| Licensing/notices | source prototypes retain their own pinned Mutable/stmlib notices | exact source manifests | no copied or modified upstream files; distribution review deferred | Compatible for local build; distribution unresolved |

Hash abbreviations in this table are human-readable pointers only. The bundle
and prototype index must retain complete SHA-256 values.

## 11. Minimal experiment

### Central hypothesis

A single integer session phase plus staging-owner swap can produce three exact,
source-only, phase-aligned layers whose output and accepted state are identical
for the same absolute event timeline across all supported callback partitions.

### Smallest vertical slice

Compose both exact source Cores under one parent, render a frozen sequence that
establishes one-second layer 1 and later captures/replaces another layer, then
emit PCM, state/controller traces, metrics, and hashes for every block size. A
test-only callback-edge quantizer supplies the falsifying comparator.

### Test signals and gestures

The event convention is event-before-sample. The canonical first take starts at
absolute frame 0 and stops at 48,000, establishing `N=48,000` and phase zero.
Layer 2 arms at frame 72,000 while phase is 24,000, begins at frame 96,000, and
records frames 96,000 through 143,999 before committing at 144,000. The suite
also cancels a replacement, rejects a short first take, injects overflow, edits
both sources, and exercises extreme but valid mixer settings.

| Field | Bound value |
|---|---|
| Sample rate and supported block sizes | 48,000 Hz; 16, 64, 128, 512 frames |
| Deterministic seed | hexadecimal `0x4C415952`, decimal `1279342930` |
| Event/sample timeline convention | block-relative events stable-sorted by `(sample_offset, ingress_sequence)`; event applies before addressed sample; first start inclusive, stop exclusive |
| Literal condition IDs and count | eight: `first-capture-establishes-loop`, `second-capture-quantized`, `replacement-cancel-preserves`, `short-first-capture-rejected`, `overflow-aborts-replacement`, `partition-matrix`, `source-pause-and-controls`, `mix-safety-extremes`; protocol-only `lc3-protocol` is retained separately |
| Falsifying comparator condition | test-only callback-edge capture quantizer; expected to diverge across partitions and never enters production |
| Output names and kinds | `layerwell.wav`, `event-state-trace.json`, `controller-trace.json`, `metrics.json`, `SHA256SUMS` |
| Objective tolerances | same-build byte identity across blocks; exact capture/state/controller traces; finite 100%; every output in [-1,1]; zero process allocations; unchanged old-layer hash on every abort |
| Artifact retention policy and location | retained under `research/prototypes/layerwell/contract/evidence/`; generated build trees remain ignored or outside source authority |

### Measurements

Frame count; capture start/stop/commit frames; phase and layer-owner history;
source advance counts; event accepted/dropped/rejected counts; output peak, RMS,
DC, finite/limited counts; allocation count around process; hashes of PCM,
committed buffers, accepted-state trace, and protocol messages.

### Listening protocol

Deferred. A later explicitly authorized test should compare source-monitor
balance, seam audibility, replacement timing, and controller legibility through
real audio and physical controls. No build or render result supports a musical
quality claim.

### Stop or pivot conditions

- Stop if exact source targets cannot coexist without changing source DSP or
  creating a second source/notices authority.
- Pivot storage if four preallocated buffers exceed the declared 64 MiB Core
  target or any process allocation remains.
- Pivot timing if any accepted state, capture boundary, or PCM differs by block
  partition after fixing the absolute event schedule.
- Stop the controller lane if official protocol values cannot be reconciled
  with the retained topology; do not guess physical behavior.
- Do not proceed from target build to app launch, endpoint use, or listening
  without separate authorization.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Exact source contracts are reusable together | combined parent compile/link plus existing source regressions | Source/host structural | Not run | build/test logs |
| First capture defines exact loop length | deterministic boundary fixture | Host signal | Not run | state trace/WAV |
| Later capture is boundary-aligned and source-only | absolute timeline and buffer-hash fixture | Host signal | Not run | event-state trace |
| Replacement failure preserves old audio | cancel/short/overflow/invalid hash tests | Host signal | Not run | test output/metrics |
| Output is deterministic across partitions | 16/64/128/512 byte/hash comparison | Host signal | Not run | `SHA256SUMS` |
| Process is callback-bounded | allocation guard, fixed-capacity inspection, sanitizer/focused tests | Host structural/synthetic | Not run | test logs |
| LC3 mapping/protocol is exact | exhaustive synthetic input/output fixtures | Synthetic protocol | Not run | controller trace |
| Standalone target builds | authenticated JUCE configure/compile/link | Target build | Not run | build log and `.app` |
| App runs in real time | launched audio-device observation | Real time | Forbidden/deferred | none |
| Physical LC3 controls Layerwell | selected endpoint and receipt/feedback observation | Connected device | Forbidden/deferred | none |
| Layers sound good | declared listening protocol | Listening | Deferred | none |
| Canonical or production ready | accepted records, release evidence, distribution review | Production | Out of scope | none |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/layerwell/contract/`
- Proposal fingerprint and approval reference: exact SHA-256 to be frozen after
  this revision; user's uninterrupted 2026-08-23 implementation request quoted
  in the bundle
- `validate_implementation_bundle.py --phase ready`: not yet run at proposal
  freeze; must pass before DSP source is added

### Files expected to change

- `research/proposals/layerwell.md`
- `research/prototypes/layerwell/**`
- minimal target-existence guards in the Tide Pit and Generative Drums CMake
  entry points if the combined parent proves they are necessary
- Task 042 governance/status/history/result pointers and, only if required by
  the frozen validation contract, one explicit prototype validation entry

No source DSP, source map, upstream file, canonical schema/record/provider, or
application-library entry may change.

### Focused tests

Core prepare/process shapes; state transitions; event ordering/overflow;
capture start/stop/arm/commit/cancel/clear; staging-owner hashes; session phase;
source pause/control adapters; mixer/pan/seam/finiteness; block partitions;
snapshot mailbox; LC3 input parser and output feedback; renderer evidence.

### Adjacent regression tests

Existing Tide Pit Core/map tests, existing Generative Drums streaming/map tests,
Instrument Lab prototype structure, exact combined-source link, and one routine
Schuss `current` pass after freeze.

### Expensive or hardware checks

One authenticated JUCE 8.0.15 configure/build and one relocated fresh-root Core
reproduction are authorized. App launch, audio/MIDI endpoints, physical LC3,
hardware, listening, packaging, notarization, and release are forbidden here.
Use the validation runner's plan before any registered native or reproduction
check and run each affected expensive check once after implementation freeze.

### Deferred work

Source discovery, more sources/layers, external synchronization, persistence,
sample editing, a plug-in, a richer visual sampler, listening refinement,
physical controller verification, canonical Schuss promotion, distribution,
and release.

### Dependency contract

- Instrument Lab v1 is the shared portable boundary and must appear once in the
  parent target graph.
- Tide Pit is consumed through its existing public target and exact index,
  implementation-contract, source-equivalence, dependency, and notices files;
  no upstream bytes are copied or changed.
- Generative Drums is consumed through its existing public streaming/map
  targets and exact index, implementation contract, source dependency manifest,
  Braids adapter authority, and notices; no upstream bytes are copied or
  changed.
- JUCE 8.0.15 is allowed only for the prototype host and UI modules already
  used by local Instrument Lab apps and only from the source tree authenticated
  by the repository manifest. Network fetching is disabled.
- Official Novation documents and the downloaded official Bitwig extension are
  research evidence only, never compiled or distributed inputs. The extension
  ZIP SHA-256 is `b785f35e0b2f89d21c14a783be278c477a34181e9bc8475653ded79ad76be794`;
  the `.bwextension` SHA-256 is
  `e7e14637799249444a1b36a7e9f8cd1de114fb2290277fa8fba9e4b0af391651`.
- Local builds retain source notices. Product distribution and license review
  remain an explicit gate.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Source type | Notes or proof gap |
|---|---|---|---|---|---|
| LW-01 | EVIDENCE | Tide Pit exposes a prepared 48 kHz Q27 Core and semantic events | exact local `tidepit/core.hpp` and contract | Source | Host behavior is already tested; composition is not yet tested |
| LW-02 | EVIDENCE | Generative Drums exposes a fixed-capacity 48 kHz streaming Core and public control map | exact local headers and bundle | Source | Composition is not yet tested |
| LW-03 | EVIDENCE | Regular LC3 DAW mode exposes dedicated-port enable/disable, relative rows, input controls, LED, encoder, and OLED feedback | official Novation programmer guide | Manufacturer documentation | Physical endpoint and receipt unproved |
| LW-04 | EVIDENCE | Page controls are CC106/107 and Track controls are CC103/102 in the official integration | official Novation Bitwig extension bytecode, hashes above | Manufacturer binary research | Parsed read-only; no runtime observation |
| LW-05 | EVIDENCE | Multi-track loop, replace, undo or cancel, and fixed-length capture have prior art | Ableton, Boss, Elektron, SooperLooper manuals or source | Product/open-source documentation | Does not dictate internal implementation |
| LW-06 | INFERENCE | Source-only staging is clearer and safer than recursive mix resampling for this product | signal model and user intent | Design reasoning | Needs listening comparison only for preference, not correctness |
| LW-07 | HYPOTHESIS | Constant-time staging-owner swap will preserve old audio through all failure paths | proposed Core | Experiment | Must pass old-buffer hash fixtures |
| LW-08 | HYPOTHESIS | One sample phase will make accepted state and PCM partition-independent | proposed Core | Experiment | Must pass all four blocks |
| LW-09 | INFERENCE | Transaction vocabulary usefully clarifies provisional replacement | Gray/Lamport plus looper prior art | Cross-domain reasoning | Not a distributed system or novelty claim |
| LW-10 | EVIDENCE | EIS treats electronic memory as a performer-controlled expansion | Oliveros/Panaiotis and EMPAC | Practitioner/institutional source | Layerwell borrows no EIS-specific mechanism, name, or material |
| LW-11 | HYPOTHESIS | The regular LC3 surface can remain legible with two modes and three layers | proposed mapping | Experiment | Synthetic trace can prove consistency, not physical usability |
| LW-12 | EVIDENCE | Four float stereo buffers consume 49,152,000 sample bytes | exact arithmetic | Calculation | Container and source-Core overhead measured after implementation |

## 15. Open questions and decision gate

### Open questions

No question blocks the bounded revision 0.1 implementation. Physical endpoint
names, useful encoder acceleration, seam audibility, real callback headroom,
and distribution terms are intentionally deferred to later evidence gates.

### Recommendation

Proceed with the Task 042 noncanonical vertical slice exactly as specified:
resident exact source Cores, three aligned source-only layers and one staging
buffer, event-before-sample timing, provisional replacement, two-mode regular
LC3 DAW presentation, and a state-driven JUCE standalone. Stop at authenticated
build and deterministic or synthetic evidence.

### Approval requested and received

The user's 2026-08-23 request to implement authorizes revision 0.1 after its
exact fingerprint is bound into
`research/prototypes/layerwell/contract/`. It authorizes the built
`Layerwell.app`, deterministic stereo render, accepted-state trace, and
synthetic controller trace up to target-build and host-signal evidence. It does
not authorize app launch, audio or MIDI endpoint access, controller
configuration, physical-device evidence, listening claims, canonical
promotion, distribution, staging, commit, push, or publication.

## 16. Implementation record

Complete after the ready bundle passes and implementation evidence exists.

### Proposal revision implemented

Pending.

### Source and test artifacts

Pending.

### Commands and results

Pending.

### Deviations

Pending.

### Remaining proof gaps

App launch, real-time audio-device deadline, endpoint discovery and selection,
physical LC3 receipt and feedback, listening quality, distribution, and
canonical production integration remain explicitly unproved.
