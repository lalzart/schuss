# Layerwell 0.2: Embedded Tide Pit and Pamplist Sampler

> Status: proposed on 2026-08-24 for the explicitly authorized bounded implementation; not accepted architecture or production-ready
> Proposal revision: 0.2
> Work type: `new-design`
> Original idea: Revise Layerwell so selecting Tide Pit or Pamplist embeds the selected instrument's complete control surface inside the sampler; remove Generative Drums because Pamplist is preferred; retain three synchronized source-only layers and add non-destructive start/end loop trim.
> Implementation target: Portable C++17 Instrument Lab Core, deterministic 48 kHz renderer, regular Launch Control 3 DAW-mode adapter, and authenticated JUCE 8.0.15 macOS standalone
> Working artifact and evidence level: built but unlaunched `Layerwell.app` plus deterministic stereo, accepted-state, embedded-panel, trim, and synthetic controller evidence; authenticated target-build and objective host-signal ceiling
> Approval reference: the user's 2026-08-24 request, “All right, let's try to do it with just the pamplist and TidePit. Generative drums is too similar to Pamplist, which I prefer. Please try to create this.”
> Decision gate: uninterrupted execution is authorized only through the noncanonical Task 044 prototype and its stated evidence ceiling; canonical promotion, app launch, endpoint access, visual approval, listening, and Git publication remain separate decisions.

## 1. Product thesis

### One-sentence thesis

Layerwell 0.2 places the complete Tide Pit or Pamplist performance surface above
a small shared-timeline looper, so the performer can shape a source, capture it,
correct its loop boundaries, and layer up to two more synchronized source takes
without leaving one instrument window.

### Instrument identity

The upper workspace is the selected source instrument rather than a generic row
of unlabeled controls. Tide Pit exposes its sixteen encoders, eight buttons,
four display lines, mode, and bounded scope. Pamplist exposes its eight pages,
Voice/Motion context, sixteen contextual values, Run/Stop, Global/Clear,
dependency help, and bounded seven-lane impact history. The permanent lower
strip owns the sampler: source choice, capture, three aligned layers, trim,
level, pan, mute, monitor, and master output.

This is not a screenshot, plug-in host, or pair of separate applications. One
Layerwell engine owns audio, MIDI, both source Cores, the capture stores, and the
accepted snapshot. The visible panel is a Layerwell-owned presentation of the
selected source's existing public control and UI models.

### Intended user and musical situation

A performer using a Mac and one regular Novation Launch Control 3 wants to
improvise with Tide Pit and Pamplist, see what the selected instrument is doing,
capture a phrase, correct a slightly late start or early stop, and add one or
two aligned layers without creating an Ableton Live routing session.

### In scope

- Exactly two resident sources: Tide Pit Gills 0.1 and accepted Pamplist 0.6.
- One source-faithful replaceable upper panel and one permanent sampler strip.
- Read-only composition of the sources' existing public Cores, reducers, UI
  models, configured-source authority, and notices.
- Three committed stereo layer stores plus one staging store, preallocated for
  at most 32 seconds at exactly 48 kHz.
- Immediate first capture, boundary-quantized later capture, provisional
  replacement/cancel, source-only recording, level, pan, mute, and monitoring.
- A shared non-destructive loop window editable while exactly one layer exists.
- Pure regular Launch Control 3 DAW-mode parsing and accepted-state feedback.
- Deterministic portable tests/renders and an authenticated unlaunched JUCE app
  build.

### Out of scope

Generative Drums inside Layerwell, any change to Generative Drums itself,
arbitrary source discovery, plug-in or process hosting, system-audio capture,
per-layer loop lengths, timestretch, resampling, slicing, reverse, waveform
editing, destructive crop, zero-crossing search, overdub, composite resampling,
sample import/export, persistence, presets, external clock, canonical records,
app launch, endpoint access, physical-controller proof, listening approval,
packaging, publication, staging, commit, or push.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- Task 044 is the active contract. Completed but uncommitted Task 043 Pamplist
  work is inherited read-only and must not be overwritten or staged.
- Layerwell 0.1 supplies the fixed-capacity scheduler, capture transaction,
  three-layer storage, accepted-state publication, controller adapter, renderer,
  and authenticated JUCE seam.
- Tide Pit supplies a public event-driven Core, semantic control reducer, UI
  model, and scope pattern at 48 kHz with a 16-frame source quantum.
- Pamplist supplies a public Core, contextual control map, surface model,
  activity reducer, and authenticated configured macro-voice source at exact
  patcher commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c` and synthesis tree
  `58917f3e2e46a30337cfb6292a3504845b1d5552`.
- Both standalone JUCE components own their own engines and therefore cannot be
  nested directly without duplicating audio/MIDI lifecycles. Layerwell may
  reproduce their exact public presentation semantics in neutral panels.
- JUCE 8.0.15 must come from the authenticated local seam. No download is
  allowed.
- Official controller topology is protocol authority; synthetic messages are
  not physical receipt evidence.

### Deliverables

The proposal; an implementation-ready Sonic Research Lab bundle; revised
portable Core, source adapters, controller adapter, renderer, focused tests,
retained evidence, source-faithful JUCE panels, authenticated standalone build,
prototype metadata, and truthful handoff/results/gaps.

### Acceptance tests

The literal gates are in Task 044. Central checks are exact combined source
linkage; exhaustive panel projection; valid and invalid trim transitions;
partition-independent capture, playback, and protocol traces; byte preservation
on non-destructive edits and aborts; no process allocation or I/O; affected
source regressions; retained-evidence freshness; authenticated app build; one
relocated reproduction; and explicit evidence-level separation.

### Decisions this work may make

Prototype-local fixed-capacity panel structs, GUI-to-Core mailbox representation,
layout, source-derived colors, bounded scope/history reduction, trim gesture
units, diagnostics, and the smallest parent-only CMake composition needed to
preserve both source authorities.

### Decisions this work must not make

New Tide Pit or Pamplist DSP, musical controls, defaults, equations, source
identity, standalone UI evidence, canonical identity, generic panel ABI,
arbitrary hosting, independent layer timing, controller firmware behavior not
in authority, persistence, distribution, or any visual, physical, audible,
real-time, production, or publication conclusion.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| `Layerwell.app` linked from authenticated JUCE 8.0.15 source | Target build | Configure, compile, and link without launch or endpoint opening | Visual approval, callback deadline, endpoint selection, physical MIDI/audio, listening, packaging, production |
| Deterministic WAV, event/state/panel/controller traces, metrics, and hashes | Objective host signal and synthetic protocol | Frozen conditions agree across 16/64/128/512-frame partitions and invariants pass | Musical quality, physical receipt, product readiness |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Decision | Confidence |
|---|---|---|---|---|
| Embedded source workspace | Selecting a source reveals its labeled controls and visual state | User correction plus source JUCE/public models | Keep; neutral Layerwell presentation of exact public semantics | High |
| Tide Pit panel | Sixteen encoders, eight buttons, four lines, mode, scope | Tide Pit public Core/control/UI and JUCE source | Keep complete bounded surface | High |
| Pamplist panel | Eight pages, two contexts, sixteen controls, actions/help, seven-lane activity | Pamplist 0.6 public models and JUCE source | Keep complete bounded surface | High |
| Source selection | Page buttons switch between exactly two resident sources | User request and controller authority | Keep; retain inactive state | High |
| First capture | One source performance establishes the session cycle | Layerwell 0.1 contract | Keep sample-exact inclusive/exclusive convention | High |
| Boundary correction | Start/end trim choose a subrange without deleting audio | User request | Add only while one layer exists | High |
| Later layering | Additional source takes align to the corrected cycle | Layerwell 0.1 behavior | Keep; record exact current cycle | High |
| Truthful feedback | UI/controller show accepted state | Schuss accepted-state rule | Keep; raw input never presentation authority | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Evidence | Design implication |
|---|---|---|---|---|---|
| Layerwell 0.1 | Local prototype | Two resident Cores, transactional three-layer capture | Generic source shell; Tide Pit plus Generative Drums; no trim | `research/proposals/layerwell.md` and retained contract | Preserve scheduler/storage proof, replace source and presentation |
| Tide Pit Gills 0.1 | Local instrument | Event-driven textured pitched source and compact hardware-style UI | Sixteen controls, eight actions, mode/display/scope | Exact local public source and contract | Reuse unchanged and project every accepted field |
| Pamplist 0.6 | Local instrument | Seven-lane polymetric macro-voice system with modal UI | Eight pages, Voice/Motion, actions/help/activity | Exact local proposal, bundle, and public source | Prefer over similar Generative Drums and reuse unchanged |
| Ableton Live resampling/Looper | DAW/effect | Route and capture audio, loop/overdub/undo | Requires DAW session and broader transport | Research ledger in Layerwell 0.1 proposal | Layerwell stays standalone and source-only |
| Multi-track loopers | Hardware/software | Parallel aligned tracks and replace/cancel | Broad effects, storage, routing, tempo systems | Layerwell 0.1 bounded landscape | Three simple aligned stores are sufficient |
| Sampler trim editors | Hardware/software | Select playback start and end inside retained audio | Often waveform, slicing, undo, resampling | User's requested behavior is narrower | Use integer-frame metadata only; reject workstation breadth |

No exact Tide Pit/Pamplist wrapper is claimed outside this repository. The
landscape is bounded and makes no universal novelty claim.

## 5. Synthesis and engineering research

| Source | Mechanism | Strength | Applicability | Limitation |
|---|---|---|---|---|
| Layerwell 0.1 ready bundle and retained evidence | Fixed storage, sample-exact scheduler, commit/abort, SPSC snapshot | Executed local evidence | Direct baseline for the looper | Proves only prior two-source revision |
| Tide Pit public Core/control/UI model | Exact accepted semantics and source state | Executed local source/tests | Embedded Tide panel and audio | Standalone component is not embeddable as-is |
| Pamplist 0.6 public Core/control/UI/activity models | Exact contextual semantics and bounded history | Executed local source/tests | Embedded Pamplist panel and audio | Depends on configured authenticated source |
| JUCE audio callback and component APIs | One host lifecycle and UI component tree | Official API plus authenticated build seam | Standalone adapter | Build is not real-time or visual proof |
| Regular Launch Control 3 authority | DAW-mode messages, relative encoders, LEDs/OLED | Official manufacturer-derived local authority | Pure mapping and feedback | No endpoint or device receipt proof |

The trim mechanism intentionally uses no interpolation or time-domain DSP. It
changes integer playback metadata and reuses the existing deterministic seam
treatment, which limits the new proof burden to state, indexing, and alignment.

## 6. Musical-practice research

| Practice/community/context | Relationship | Structural principle | Translation | Restriction | Risk |
|---|---|---|---|---|---|
| Live electronic performer-controlled memory, including the documented Expanded Instrument System lineage | Already bounded in Layerwell 0.1 research | Past and present gestures can remain performer-controlled | General motivation for capture/layer interaction only | Do not use EIS naming, routing, repertoire, recordings, pedagogy, or lineage claim without collaboration/permission | False lineage or appropriation |
| Contemporary hardware/software live looping | Product/manual prior art in Layerwell 0.1 ledger | A first phrase can define a repeatable cycle for later layers | Shared session length and boundary-aligned captures | No claim that the common mechanism belongs to one community | Feature imitation if product identity is copied |

Revision 0.2 adds usability and boundary correction, not a culturally derived
musical mechanism. It makes no cultural-authenticity claim.

## 7. Computer-science transfer search

| Concept and field | Audio prior art | Mapping | Benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| View model / projection | Common UI architecture | Exact source snapshot to fixed neutral panel snapshot | Rich UI without a second engine | Raw or stale input becomes display authority | Exhaustively compare every projected field with accepted source state |
| Prepare/commit/abort | Loop replace/undo prior art | Staging store swaps only after a complete valid capture | Failed takes preserve the sounding layer | Partial capture leaks or old owner changes | Hash owners/bytes across cancel, reject, overflow, and source failure |
| Metadata view/slice | Array/span and sampler prior art | Store `recorded_length` and `playback_offset`; shared active length | Correct loop without copying audio | Off-by-one, out-of-bounds, or layer drift | Exact impulse/ramp subrange playback and sentinel-byte preservation |
| Modular phase accumulator | Sequencer/looper prior art | One phase modulo active loop length | Partition-independent alignment | An accepted trim could be ignored while state still appears plausible | Exact 16/64/128/512 comparison; otherwise identical untrimmed comparator must diverge |
| Bounded SPSC publication | Existing Schuss UI pattern | Callback publishes complete accepted snapshot | UI and feedback tell the truth without locks | Torn snapshot | Sequence-tag stress test and whole-snapshot equality |

## 8. Novelty map

### Common elements

Embedded sound engines, labeled source panels, multi-track live capture,
non-destructive start/end points, replace/cancel, relative encoders, and
accepted-state feedback all have established prior art.

### Less-common combinations found

Workstations combine synthesis and sampling, and loopers combine multiple
tracks with MIDI control. The bounded local/external research did not identify
this exact composition of Tide Pit and Pamplist public models, one-source-at-a-
time processing, source-only aligned replacement, and one-layer-only trim lock.

### Proposed contribution

Within this bounded search, the contribution is an auditable repository-local
composition: two existing instruments feel present inside a single small
sampler while one owner retains audio/MIDI authority and integer-frame trim
cannot silently desynchronize later layers. No global novelty, patentability,
or first-in-category claim is made.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Keep Generative Drums | User prefers Pamplist and sees them as too similar | Explicit user decision |
| Embed each whole standalone component | Each owns its own Core/audio/MIDI lifecycle | Duplicate engines and false accepted-state authority |
| Screenshot or remote-window embedding | Not interactive source control and fragile lifecycle | Does not satisfy the requested instrument UI |
| Generic plug-in/process host | Adds discovery, routing, latency, and endpoint ambiguity | Task boundary |
| Independent trim per occupied layer | Can silently change relative phase/period | Musical synchronization risk |
| Copy/crop samples on trim | Adds destructive work and callback cost | Unnecessary for playback-window semantics |
| Automatic zero-crossing/transient snapping | Adds hidden musical policy | Explicitly deferred |

## 9. Recommended architecture

### Signal flow

```text
JUCE source panel or regular Launch Control 3 DAW port
  -> fixed-capacity semantic command adapter
  -> selected public source reducer/Core
       -> Tide Pit Q27 stereo OR Pamplist Q27 main/aux
  -> source monitor ---------------------------------------+
  -> staging capture -> commit/abort -> layer stores ------+-> pan/level/mute
  -> accepted source + sampler snapshot -> SPSC -> panels -+-> master/clamp
```

Only the selected source advances. The inactive Core and its controls retain
state. Layerwell owns exactly one audio device and MIDI lifecycle. Panel classes
contain no source Core and dispatch only bounded semantic commands.

### Executable DSP contract

| Mechanism | Equation or pseudocode | Ranges | Gain/stability bound | Timing | Failure behavior |
|---|---|---|---|---|---|
| Source select | `selected = wrap(selected + direction, 2)` | Tide Pit or Pamplist | inactive source contributes zero | ordered event before addressed sample; blocked during capture | invalid direction ignored/counted |
| Source control | relative mirror or absolute 7-bit value -> existing source reducer | 16 encoders, 8 buttons; values 0..127 | reducer owns semantic bounds | ordered fixed-capacity event; snapshot after acceptance | invalid slot/value ignored/counted |
| Source render | selected public Core -> Q27 -> float | exact source block contracts; 48 kHz | convert and clamp non-finite contribution to zero | 16-frame internal quantum | source failure silences segment and aborts active provisional capture |
| First capture | start inclusive; stop exclusive; `N = stop - start` | `24000 <= N <= 1536000` | copy source only | immediate start; valid stop commits and phase becomes zero | short/invalid capture rejected; old owner preserved |
| Later capture | wait for phase zero; record exactly `loop_length` frames | active loop length | source only; staging isolated | commit before next phase-zero mix | cancel/failure preserves old layer |
| Trim accept | require idle and one occupied layer; `0 <= s < e <= recorded_length`; `e-s >= 24000`; set `offset=s`, `loop_length=e-s`, `phase=0` | integer frames | no sample writes; owner unchanged | control/event boundary outside active capture | reject atomically with diagnostic and no state/storage change |
| Playback | `sample = store[playback_offset + phase]` | `phase < loop_length`; sum index inside recorded extent | existing equal-power pan and final clamp `[-1,1]` | per sample; phase wraps modulo loop length | invalid invariant silences and counts fault |
| Seam | existing Layerwell bounded seam treatment at active window edges | unchanged revision 0.1 coefficients | bounded mix contribution | computed from active playback window | no new interpolation/resampling |
| Later layer after trim | staging records active cycle at offset zero; committed metadata is `{recorded_length=loop_length, offset=0}` | exact active length | same source-only bound | next phase-zero cycle | trim locks when second layer commits |
| Mix | `sum = monitor*source + Σ mute?0:level*pan(layer)` | levels/pan as revision 0.1 | finite final clamp `[-1,1]` | per sample | non-finite contribution becomes zero and is counted |

### State and timing model

Events are stable-sorted by block-relative `sample_offset`, then ingress
sequence, and apply before the addressed sample. Capture start is inclusive and
stop is exclusive. Trim is accepted only in `idle` with exactly one occupied
layer. Acceptance does not rewrite samples, changes the sole layer's offset and
the shared active length, and resets phase before subsequent playback.

Reset returns both sources, layers, offsets, lengths, controls, phase, trim,
panel history, and diagnostics to deterministic defaults. Panic is unsupported.
Capture is the existing provisional transaction. Source/page/context changes
retain both source Cores. Recall/persistence is unsupported. Reconnect affects
only host feedback queues, not Core state. Non-finite controls are rejected or
recovered to declared defaults; non-finite audio is never staged or emitted.
The complete state-by-operation matrix belongs in `contract-r02/state-matrix.md`.

State equivalence for the frozen experiment is byte equality of canonical
event/state/panel/controller JSON and PCM within one build across all supported
partitions; exact equality of integer boundaries, offsets, lengths, owners,
phase, accepted controls, activity/scope reductions, and diagnostics; and
SHA-256 equality of committed stores where preservation is claimed. Object
padding, addresses, GUI component state, host handles, paths, wall time, and
endpoint identity are excluded.

### Control and performance mapping

| Control/gesture | States | Mapping | Role | Safety/feedback |
|---|---|---|---|---|
| Page Up/Down | two-source wrap | select Tide Pit/Pamplist | make source identity primary | blocked during active capture; accepted source shown |
| Control encoders 1-16 | relative around 64 | selected source public slots 1-16 | complete source shaping | accepted 7-bit mirror and contextual label/value |
| Control buttons 1-8 | press/release | selected source public actions 1-8 | modes/pages/actions | exact reducer termination; accepted colors/text |
| Mixer top 1-3 | relative | layer pan | spatial mix | accepted position feedback |
| Mixer top 4 | relative | source monitor | audition level | accepted feedback |
| Mixer top 5/6 | relative | trim start/end | correct loop boundary | enabled only idle + one layer; 48-frame fine step, Shift 480-frame coarse step |
| Mixer top 7/8 | unused | no semantic event | reserved | neutral feedback |
| Mixer bottom 1-3 | relative | layer levels | blend layers | accepted feedback |
| Mixer bottom 4 | relative | master | final level | accepted feedback |
| Mixer buttons | selected layer, mutes, capture/cancel, monitor | sampler actions | performance workflow | Shift + button 8 clears selected layer |
| UI trim handles/reset | integer-frame bounded commands | set start/end or full recorded extent | precise correction | accepted snapshot is authoritative; reset requires same trim availability |

Protocol input, semantic transformation, accepted state, visual feedback, and
endpoint/device evidence remain separate. No controller endpoint is opened by
the frozen implementation checks.

### Parameter interactions and edge cases

- Moving trim start never crosses `end - 24000`; moving end never crosses
  `start + 24000`.
- Trim cannot expand beyond the remaining layer's own recorded extent.
- Once two or three layers exist, start/end are read-only. Clearing back to one
  layer re-enables inward editing against that remaining layer's recorded bytes.
- Replacing the sole layer records the current active cycle and commits with
  offset zero; failed replacement preserves its old extent and offset.
- Clearing the final layer removes the session length and returns full trim to
  unavailable defaults.
- Source switch/page/context edits do not change loop phase or trim metadata.
- A trim event concurrent with capture start is resolved by total event order;
  only the state immediately before that event determines acceptance.

### Failure behavior

Unsupported process shapes silence the call and leave transport unchanged.
Event overflow aborts provisional capture before commit. Invalid source/panel
slots, trim windows, non-finite values, or locked trim increment diagnostics and
change no accepted musical state. Out-of-range playback metadata is treated as
an invariant fault: the affected contribution is zero and the fault is counted.

## 10. Target and resource feasibility

| Constraint | Assumption/value | Evidence | Limit | Status |
|---|---|---|---|---|
| Sample rate | exactly 48 kHz | all three prototype contracts | no resampling | Ready to test |
| Outer block | 16/64/128/512 frames | Layerwell 0.1 matrix | max 512, multiple of 16 | Ready to test |
| Loop storage | four stereo float stores | existing fixed Core | 32 s = 1,536,000 frames/store | Existing baseline |
| New trim state | integer lengths/offsets only | proposed contract | O(1), no audio copy | Feasible |
| Panel state | fixed arrays and bounded history/scope | source public models | no callback allocation | Feasible |
| Source dependencies | Tide private Braids/stmlib plus configured Pamplist macro voice | exact source authorities | read-only, authenticated | Prerequisite verified locally |
| Toolchain | C++17, CMake, authenticated JUCE 8.0.15 | repository build seams | no download | Ready to test |
| CPU/deadline | two resident Cores, one selected advances | structural design | target build only | Real-time performance unproved |
| Licensing | existing source notices plus Pamplist configured closure | source dependency records | retain notices; no distribution approval | Ready for local build only |

The desktop target has no device-memory limit, but the fixed 32-second stores
are retained for deterministic behavior and bounded callback work.

## 11. Minimal experiment

### Central hypothesis

A single-owner host can present the complete accepted Tide Pit and Pamplist
surfaces while preserving sample-exact three-layer capture, and integer metadata
trim can correct the first loop without altering bytes or desynchronizing later
layers.

### Smallest vertical slice

Build both exact source Cores into one portable Layerwell target; project every
source panel field; record one deterministic phrase; trim it; play the exact
subrange; record a second source over the trimmed cycle; prove trim lock and
alignment; then render/build the unlaunched JUCE host.

### Frozen machine-readable experiment

| Field | Bound value |
|---|---|
| Sample rate and blocks | 48,000 Hz; 16, 64, 128, 512 frames |
| Deterministic seed | `1279342930` |
| Timeline | ordered events apply before addressed sample; capture start inclusive/stop exclusive; trim reset phase zero |
| Conditions | `LW02_TIDE_PANEL`, `LW02_PAMPLIST_PANEL`, `LW02_TRIM`, `LW02_LAYER_AFTER_TRIM`, `LW02_REJECT`, `LW02_CMP_UNTRIMMED` |
| Comparator | `LW02_CMP_UNTRIMMED` deliberately ignores accepted trim and must diverge from `LW02_TRIM` |
| Outputs | `layerwell.wav`, event/state trace, panel trace, controller trace, metrics, comparator record, `SHA256SUMS` |
| Tolerances | finite 100%; max abs <= 1; process allocations 0; integer boundaries/owners exact; canonical JSON and PCM byte-identical across partitions; preservation hashes exact |
| Retention | checked in under `research/prototypes/layerwell/contract-r02/evidence/` |

### Measurements

Exact event acceptance; source advance counts; every panel field; recorded
lengths, offsets, active length, phase, owners; byte hashes before/after trim and
rejection; aligned second-layer samples; finite/peak/RMS/limiter/allocation
metrics; synthetic MIDI input and accepted feedback; and comparator divergence.

### Listening protocol

No listening is authorized or required. A later listening pass should audition
late-start and early-stop corrections, seam audibility, layer alignment, source
identity, and controller legibility at matched output level, but that would be a
new evidence step.

### Stop or pivot conditions

Stop if exact public models cannot represent either source panel, one parent
cannot link both source closures without source mutation, trim requires sample
copying in the callback, any later layer can acquire a different period, the
comparator does not diverge, or the implementation needs endpoint/app/device
access. Pivot only through a revised proposal and approval.

## 12. Acceptance and evidence matrix

| Claim | Check | Evidence level | Current result | Artifact |
|---|---|---|---|---|
| Proposal defines bounded revision | proposal/bundle validators | Proposal/source | Pending implementation bundle | this file / `contract-r02/` |
| Both exact source authorities compose | authority verifier and parent build | Source/host structural | Pending | source dependency record/build log |
| Panels expose complete accepted models | exhaustive portable tests | Host structural | Pending | panel trace/tests |
| Trim is non-destructive and exact | hashes plus ramp/impulse tests | Objective host signal | Pending | state trace/hashes |
| Later capture aligns to trimmed cycle | partition matrix | Objective host signal | Pending | WAV/state/metrics |
| LC3 map is internally consistent | pure protocol tests/traces | Synthetic protocol | Pending | control map/controller trace |
| Standalone compiles/links | authenticated no-launch build | Target build | Pending | build receipt |
| App looks/feels correct | launch and human inspection | Visual | Forbidden/deferred | none |
| Real-time callback meets deadline | instrumented runtime | Real-time | Forbidden/deferred | none |
| Physical LC3 controls app | endpoint/device test | Connected device | Forbidden/deferred | none |
| Musical result is approved | controlled audition | Listening | Forbidden/deferred | none |
| Canonical/product-ready | governance/integration/release | Production | Out of scope | none |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/layerwell/contract-r02/`
- Proposal fingerprint and approval reference: recorded after this proposal is frozen
- `validate_implementation_bundle.py --phase ready`: required before Core/source/controller/JUCE edits

### Files expected to change

- `research/proposals/layerwell-r02.md`
- `docs/tasks/044-layerwell-r02-embedded-source-sampler.md`
- `research/prototypes/layerwell/CMakeLists.txt`
- Layerwell-owned public/source/test/JUCE files under
  `research/prototypes/layerwell/`
- Layerwell prototype metadata, notices, handoff, contract-r02, evidence, and
  validation registration
- Governance/status/history only as required to open and close Task 044

Tide Pit and Pamplist source project bytes are not expected to change.

### Focused tests

Portable Core/source/panel/controller/trim/snapshot/allocation tests, frozen
render matrix, comparator divergence, source-authority authentication, and
prototype validators.

### Adjacent regression tests

Tide Pit applicable focused authority and Pamplist source/focused/retained
authority checks, followed by Schuss `current` once implementation and records
are frozen.

### Expensive or hardware checks

One Release plus sanitizer Layerwell build/test set, one authenticated JUCE
target build without launch, and one relocated reproduction with the exact
configured Pamplist source. No endpoint, hardware, listening, compatibility,
or full release profile is authorized or required.

### Deferred work

Visual QA, physical controller test, real-time measurement, listening, session
persistence, waveform/zero-crossing UI, additional sources, generic embedded
panel ABI, canonical promotion, packaging, and publication.

### Dependency contract

- Tide Pit remains governed by its exact local prototype index, implementation
  contract, source-equivalence record, adapter/source packages, and notices.
- Pamplist remains governed by its exact accepted local prototype plus patcher
  commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, synthesis tree
  `58917f3e2e46a30337cfb6292a3504845b1d5552`, and authenticated file hashes.
- Layerwell reads/compiles those sources in place, does not copy or mutate them,
  and makes no source-release, implementation-provider, Pamela-equivalence, or
  distribution claim.
- JUCE is operator-supplied exact 8.0.15 source authenticated by the repository
  manifest. Network download is forbidden.
- All inherited third-party notices remain in the local artifact closure;
  distribution remains separately gated.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Type | Gap |
|---|---|---|---|---|---|
| LW02-01 | EVIDENCE | User wants exactly Pamplist and Tide Pit with embedded controls | 2026-08-24 request | User authority | None for scope |
| LW02-02 | EVIDENCE | Layerwell 0.1 has fixed-capacity three-layer transactional capture | revision 0.1 source, contract, retained evidence | Local executed evidence | Must regress after changes |
| LW02-03 | EVIDENCE | Tide Pit exposes the required public control/UI/Core state | exact local headers/tests/JUCE source | Local source evidence | New panel projection untested |
| LW02-04 | EVIDENCE | Pamplist 0.6 exposes contextual surface/activity/help and exact configured source authority | Task 043 prototype/source records and tests | Local source evidence | Parent composition untested |
| LW02-05 | EVIDENCE | Whole standalone components own engines and cannot be nested as passive views | both `juce_main.cpp` component ownership graphs | Local source inspection | Neutral panel implementation pending |
| LW02-06 | INFERENCE | One-owner neutral panels preserve semantics without duplicate lifecycle | public-model architecture | Engineering inference | Exhaustive field/action tests required |
| LW02-07 | HYPOTHESIS | Metadata-only trim can correct loop boundaries without audible regressions | proposed integer-window mechanism | Testable hypothesis | Objective exactness and later listening remain |
| LW02-08 | HYPOTHESIS | Later capture over the trimmed period stays aligned at every supported partition | proposed scheduler contract | Testable hypothesis | Frozen matrix pending |
| LW02-09 | EVIDENCE | Regular Launch Control 3 protocol map can be tested without a device | local topology and revision 0.1 pure adapter | Protocol evidence | Physical receipt remains open |
| LW02-10 | UNRESOLVED | Embedded panel layout and trim feel are visually/musically approved | no launched app or audition | Required future human evidence | Explicitly deferred |

## 15. Open questions and decision gate

### Open questions

- Whether a later visual pass should add a waveform or zero-crossing preview.
- Whether physical controller testing prefers the proposed 1 ms/10 ms trim
  increments after actual use.
- Whether future sessions need persistence or independent loop treatment.
- Whether this source-panel pattern merits a generic ABI after a second distinct
  consumer proves reuse value.

None blocks the bounded revision 0.2 implementation.

### Recommendation

Implement the smallest one-owner composition now: replace Generative Drums with
Pamplist, add exact fixed-capacity source panel projections and actions, add the
one-layer-only integer trim window, preserve Layerwell 0.1 capture semantics,
then build but do not launch the JUCE target.

### Approval requested

The quoted user request authorizes proposal revision 0.2 at its recorded SHA-256,
the architecture above, the target-build/objective-host-signal working artifact,
and the implementation-ready bundle at
`research/prototypes/layerwell/contract-r02/`. It does not authorize app launch,
endpoint/device access, visual or listening promotion, canonical integration,
distribution, staging, commit, push, or publication.

## 16. Implementation record

Complete after the ready bundle passes and implementation is frozen.

### Proposal revision implemented

Revision 0.2 was implemented inside the approved two-source boundary. The
pre-implementation ready proposal fingerprint was
`6374480a5b07ca2cfe56008c29a775e693a80f2d0b863a99e46f330c4a0fa6b6`.

### Source and test artifacts

- Layerwell now composes the unchanged Tide Pit Core/UI model and Pamplist
  Core/contextual surface/activity model under one Instrument Lab authority.
- The public Layerwell snapshot carries exact accepted source panels, bounded
  Tide scope and Pamplist impact history, layer recorded extents/offsets, and
  trim availability/state.
- The JUCE target contains passive Tide Pit and Pamplist panels above one
  permanent sampler strip and sends GUI commands through a fixed-capacity SPSC
  queue to the sole audio/MIDI engine.
- Focused Core, exhaustive panel, controller, snapshot, allocation, source-link,
  deterministic render, target-build, source-regression, and relocation
  evidence is retained under `research/prototypes/layerwell/contract-r02/`.

### Commands and results

The exact commands and hashes are recorded in `contract-r02/RESULTS.md`.
Release and bounded sanitizer tests, both standalone source suites, the exact
16/64/128/512 render matrix, the untrimmed falsifying comparator, authenticated
unlaunched JUCE target, prototype freshness, relocated build, and routine
`current` profile passed at the declared evidence levels.

### Deviations

The authenticated Macro Voice wrapper uses a signed negative left shift for its
established Q15-to-Q27 conversion. Clang shift-base UBSan reports that exact
source operation. Layerwell preserves the configured bytes and disables only
`shift-base` instrumentation on the parent-owned `pamplist_macro_voice` target;
ASan and all other UBSan instrumentation remain enabled. This inherited source
issue is retained as GAP-008 and prevents a broader production-safety claim.

The renderer's falsifying condition was implemented as the more direct
`LW02_CMP_UNTRIMMED` case described by the frozen experiment: it replays the
same schedule while ignoring `[4800, 43200)`, rather than quantizing unrelated
event timing to callback edges.

### Remaining proof gaps

Visual approval, real-time deadline, endpoint and physical controller receipt,
listening, packaging, distribution, canonical identity, and production
integration remain explicitly unproved.
