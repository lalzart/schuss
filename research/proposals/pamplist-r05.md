# Pamplist 0.5: Sixteen-Knob Voice, Motion, and Sequencer Surface

> Status: proposed
> Proposal revision: 0.5
> Original idea: Preserve every Pamplist lane feature while replacing the confusing 24-control lane presentation with exactly sixteen visible knobs, clear Voice/Motion/Sequencer grouping, matching regular Launch Control 3 behavior, and an explicit non-bipolar Trigger enable.
> Implementation target: Schuss Instrument Lab v1 portable C++17 Core, deterministic 48 kHz renderer, regular Launch Control 3 adapter, and authenticated JUCE 8.0.15 macOS standalone
> Working artifact and evidence level: built but unlaunched `Pamplist.app`, deterministic revision 0.5 control/audio comparator evidence, and synthetic controller traces at target-build evidence
> Decision gate: the current-thread request explicitly authorizes uninterrupted proposal-to-implementation work, subject to a ready revision 0.5 bundle before source edits.

## 1. Product thesis

### One-sentence thesis

Pamplist presents one lane as eight controls for what the voice is and eight
controls for when and how it moves, while a clearly selected `VOICE` or
`MOTION` view determines whether the top physical row edits stable voice values
or clock-driven modulation amounts.

### Instrument identity

The performer still owns all seven independent lane/voice systems and all 24
existing values per lane. The interface stops showing base values and their
modulation depths as apparent duplicates: `VOICE` means the stable starting
sound, `MOTION` means how the lane shape moves that sound, and `SEQUENCER` means
when and how the lane shape runs. Page eight remains the shared Global/Clear
page from revision 0.4.

This is a presentation and control-semantics correction, not a new synth or
effect. The only audio-facing correction is to admit that Trigger was already
an enable decision rather than a signed modulation depth and present it as
`TRIGGER OFF/ON`.

### Intended user and musical situation

A performer learning and improvising with Pamplist in the JUCE standalone and
on the regular Launch Control 3, without having to translate raw MIDI values or
guess whether two similarly named knobs are duplicates.

### In scope

- Exactly sixteen visible rotary controls: one top row of eight and one bottom
  row of eight.
- Lane contexts `VOICE` and `MOTION`, stored in accepted Controls and projected
  from the accepted Snapshot.
- `VOICE` top row: Model, Pitch, Harmonics, Timbre, Morph, Decay, Colour, Level.
- `MOTION` top row: Trigger Enable, Pitch Motion, Model Sweep, Harmonics Motion,
  Timbre Motion, Morph Motion, Decay Motion, Level Motion.
- Lane bottom row in both contexts: Rate, Phase, Shape, Hits, Rotate, Chance,
  Repeat, Depth.
- Global top row: the eight existing cohesion controls; Global bottom row: BPM,
  Master, and six visibly disabled positions.
- Dynamic group outlines, concise explanatory text, semantic value formatting,
  and per-control tooltips.
- Matching controller semantics: re-press the accepted lane button to toggle
  `VOICE`/`MOTION`; another lane button selects that lane without changing the
  current context.
- A binary Trigger transform: controller values 0-63 mean Off and 64-127 mean
  On; GUI exposes only Off/On; accepted legacy positive trigger values remain
  On after sanitization.
- Focused mapping/state/UI-model tests, an exact revision 0.4 audio comparator,
  deterministic revision 0.5 evidence, an authenticated unlaunched target
  build, prototype freshness, and relocated reproduction.

### Out of scope

- Removing or merging any Model, voice, motion-route, sequencer, cohesion,
  transport, or output feature.
- Changing the seven source voices, model order, scheduler, lane shapes,
  probability/repeat algorithms, modulation scales, dry mixer, or cohesion DSP.
- New effects, routes, mute/solo, pan, presets, external clock, controller
  feedback/configuration, plug-in formats, or Ksoloti/Gills work.
- App launch, endpoint access, physical controller configuration, callback
  timing, structured listening, distribution, or canonical integration.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- Revision 0.4 is the direct predecessor. Its proposal SHA-256 is
  `d5ef3c2d37e4472d34f383eddd4deee148ede4794c6dfcbecf110dbc851ba193`.
- Revision 0.4 source, host, render, target-build, relocated, and routine
  evidence passed; its retained dry audio SHA-256 is
  `a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912`.
- The current lane page displays 26 rotary controls: eight base voice values,
  BPM/Master, eight signed routes, and eight timing values. The user correctly
  perceived the base and route rows as unexplained duplicates.
- Core inspection shows Trigger fires only when its stored route is positive;
  route magnitude and negative modulation are not used to form an alternate
  trigger. Negative/zero values therefore silence new voice triggers by design,
  despite the UI presenting Trigger like a bipolar continuous destination.
- The regular Launch Control 3 authority remains 16 endless encoders and eight
  buttons on channel 16 CC20-35/40-47, with no faders.
- The configured Macro Voice source, controller topology, Instrument Lab seam,
  and authenticated JUCE 8.0.15 tree remain exact revision 0.4 dependencies.
- The current user message authorizes this bounded implementation, but not
  staging, committing, launching, endpoint access, or hardware mutation.

### Deliverables

- `research/proposals/pamplist-r05.md` and a ready implementation bundle under
  `research/prototypes/pamplist/contract-r05/`.
- Accepted lane control-mode state and contextual, exhaustive controller map.
- A portable pure surface model used by the JUCE host to define exactly sixteen
  knob slots, group names, labels, tooltips, ranges, values, and enabled state.
- Refactored JUCE presentation using two rows of eight sliders and explicit
  `VOICE`/`MOTION` selectors.
- Binary Trigger Enable semantics with revision 0.4 trigger-on audio parity.
- Updated tests, renderer/evidence, target-build receipt, README, topology,
  semantic surface, prototype index, handoff, results, and gaps.
- Preserved revision 0.2 through 0.4 proposal/contract/evidence directories.

### Acceptance tests

- The portable surface model always contains exactly sixteen knob slots and the
  JUCE component owns exactly sixteen rotary sliders.
- All eight Voice, eight Motion, and eight Sequencer values remain independently
  reachable; Global retains all eight cohesion values plus BPM/Master.
- Labels and tooltips distinguish base values from modulation amounts; semantic
  values show names, ratios, percentages, steps, Free, Direct, or Off/On rather
  than raw CC values where applicable.
- Accepted context, not raw button or GUI focus, controls labels, values,
  controller transforms, group outlines, and selected view feedback.
- On lane pages, CC20-27 edit only the selected voice in `VOICE` and only the
  selected lane routes in `MOTION`; CC28-35 retain the exact sequencer map in
  both contexts.
- A positive edge on the already-selected lane toggles context once; duplicate
  positive values and release do not repeat. Selecting another lane preserves
  context and changes no musical record.
- Trigger controller values 0 and 63 produce accepted Off; 64 and 127 produce
  accepted On. Off creates no triggers; On produces the exact revision 0.4
  trigger-on output for the frozen comparator.
- All other Voice/Motion/Sequencer transforms meet exact endpoint and
  non-target equality tests.
- The revision 0.4 dry comparator audio remains byte-identical when Trigger is
  On. Global/Clear, seven-lane independence, all-model/source behavior, exact
  dry cohesion bypass, safety, and block determinism do not regress.
- Release/sanitizer/no-allocation, target build, prototype freshness, retained
  evidence, current, and relocated reproduction checks pass.

### Decisions this work may make

- Exact group titles, concise labels, tooltips, semantic value formatting,
  layout dimensions, and view-selector appearance.
- Pamplist-local accepted `LaneControlMode` state and same-lane re-press gesture.
- Exact CC-to-Voice transforms within the existing declared parameter ranges.
- Trigger Off/On representation and the physical midpoint threshold.
- Revision 0.5 deterministic control/render fixtures and diagnostics.

### Decisions this work must not make

- Delete, combine, or silently repurpose an existing musical parameter.
- Change authenticated upstream source, model names/order, source RNG behavior,
  voice DSP, clock math, route scales other than Trigger, or cohesion DSP.
- Modify revision 0.2 through 0.4 retained proposal/contract/evidence bytes.
- Add shared infrastructure or refactor another prototype.
- Allocate canonical IDs or modify catalogs, schemas, providers, runtimes,
  device profiles, source releases, or production records.
- Claim physical usability, real-time safety, audible quality, or production
  readiness from synthetic/compile evidence.
- Launch, enumerate/open endpoints, install, stage, commit, push, publish,
  package, redistribute, upload, or flash.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Built but unlaunched revision 0.5 `Pamplist.app`, retained comparator renders, portable surface-model tests, and synthetic controller trace | target-build | Exactly sixteen visible semantic knobs, complete 24-value lane access through accepted Voice/Motion context, binary Trigger behavior, unchanged trigger-on audio, exhaustive mapping, and authenticated compile/link | Live callback deadline, endpoint/device behavior, physical layout feel, listening approval, embedded feasibility, distribution, or production |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Revision 0.4 lane | Eight base voice, eight motion-route, and eight sequencer values | Exact Controls/Core | Keep every value | High |
| Revision 0.4 JUCE lane page | Eight base knobs plus BPM/Master above sixteen route/timing knobs | Exact JUCE source and user audition | Transform into two rows of eight with context | High |
| Duplicate labels | Harmonics, Timbre, Morph, Decay, and Level appear once as a base and once as an unexplained route | Exact labels and user observation | Rename route variants as Motion | High |
| Trigger route | Positive route enables boundary triggers; zero/negative disables; magnitude/sign do not select a second trigger behavior | Exact Core condition | Transform into binary Enable | High |
| Regular controller | Two rows of eight encoders and eight buttons | Authenticated topology and first-party guide | Make app mirror the actual surface | High |
| Accepted-state UI | Core Snapshot is authoritative; raw input is diagnostic | Instrument Lab workflow and predecessor host | Keep and extend to context | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| Pamplist 0.4 | Local predecessor | Complete voice, route, and sequencer state | Correct ownership but over-complete simultaneous GUI | Exact local source/evidence | Normative sound/state comparator |
| Layerwell | Local Instrument Lab prototype | Regular Launch Control 3 contexts expose different coherent control families | Source and mixer pages are explicitly distinct | Local proposal/Core/results | Context is useful only when visibly named and state-driven |
| Tide Pit UI model | Local Instrument Lab prototype | Accepted Snapshot drives button/control presentation | Raw input never owns visible state | Local source/tests | Use a pure portable surface model rather than JUCE-local truth |
| Launch Control 3 | First-party controller | 16 endless encoders and eight assignable buttons | Fixed two-row physical surface | https://userguides.novationmusic.com/hc/en-gb/articles/30683940823442-Introduction-to-the-Launch-Control-3 | Exactly two rows of eight should be the visual invariant |
| Broad software/product lane | Bounded non-search | Contextual synth pages and modulation views are common | No external product is normative for this correction | Not relied upon | Make no novelty or market-equivalence claim |

## 5. Synthesis and engineering research

| Source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Pamplist 0.4 Core/tests/evidence | Trigger, scheduler, route, source, effect, and exact dry behavior | Exact local source and measurement | Normative audio comparator | Does not prove revised usability |
| Instrument Lab workflow | Accepted Core snapshots drive presentation; controller topology and semantics stay separate | Accepted architecture | Owns context/state boundary | Does not choose labels |
| JUCE 8.0.15 local headers | Group outlines, sliders, buttons, tooltips, and value-format callbacks | Authenticated implementation API | Supports thin host presentation | A successful build is not visual inspection |
| ADR 0018 | Proportional focused/native/reproduction evidence | Accepted decision | Avoids replaying unrelated historical work | Does not lower affected checks |

**EVIDENCE:** the Trigger control's negative half is not an alternate musical
operation. **INFERENCE:** a binary label and state will make its silence
predictable. **HYPOTHESIS:** the Voice/Motion split and two outlined rows will
make the full lane learnable without reducing playability; only the user's next
audition can decide that.

## 6. Musical-practice research

N/A — this revision introduces no named tradition, repertoire, tuning system,
community practice, cultural identity, or culturally situated mechanism. It is
an interface-ownership correction derived from the instrument's own state and
the user's direct audition.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Finite-state view model | Contextual controller pages are established and already used locally | Accepted enum selects Voice, Motion, or Global surface model | One physical knob has one visible meaning | Raw UI context diverges from mapping context | Exhaust context/page/CC combinations and compare accepted surface model |
| Mode-dependent input grammar | Re-press/shift gestures are common on bounded controllers | Same-lane positive edge toggles context; other lane selects | No extra physical button or hidden 17th knob | Holds/releases toggle repeatedly | Edge-state trace with duplicate positive and release |
| Information scent / explicit grouping | Common UI practice; no novelty claim | Group title, labels, values, and tooltips describe ownership | Base versus modulation distinction becomes visible | Labels still look duplicated or raw | Exact portable surface table and source/build assertions |

## 8. Novelty map

### Common elements

Two-row controller surfaces, synth parameter pages, modulation pages, group
outlines, tooltips, semantic value labels, and binary enables are established.

### Less-common combinations found

No broad novelty search was required or performed. The local bounded audit
found Pamplist's specific 24-value lane compressed onto the regular controller
only by leaving the eight base voice values off the physical mapping.

### Proposed contribution

No universal novelty claim is made. The contribution is a Pamplist-specific
alignment: exactly sixteen physical/visible positions, an explicit accepted
top-row context, and a stable sequencer bottom row, with all 24 values retained.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Delete the motion routes | They are musically active and the user asked to retain features | Scope and audition |
| Delete base controls as duplicates | They are starting values, not modulation depths | Exact Core ownership |
| Show 24 smaller knobs | Does not solve physical mapping or comprehension | User report and controller topology |
| Put Voice and Motion in two simultaneous top rows | Recreates 24-knob presentation | Central defect |
| Make every route unipolar | Pitch/model/tone negative motion is musically meaningful | Existing DSP and user enjoyment |
| Give negative Trigger a new complement/retrigger algorithm | Adds a sequencer feature while solving a UI defect | Unapproved DSP expansion |
| Keep Trigger bipolar but explain it | Half the range still has no distinct behavior | Exact Core condition |
| Use local JUCE focus as context authority | Can drift from physical mapping and accepted audio state | Instrument Lab architecture |

## 9. Recommended architecture

### Signal flow

The revision 0.4 audio graph is byte-preserved for Trigger On:

```text
accepted page + accepted LaneControlMode
  -> pure sixteen-slot surface model and contextual CC mapping
  -> seven existing lane/voice records
  -> unchanged scheduler, source voices, dry mixer, cohesion body, final output
```

`LaneControlMode` and page selection are control/presentation state, not audio
nodes. Trigger Enable changes whether an accepted sequencer step sends the
existing trigger event; it does not scale audio or add a new trigger algorithm.

### Executable DSP contract

| Mechanism | Equation or pseudocode | Ranges | Bound | Timing | Failure behavior |
|---|---|---|---|---|---|
| Accepted context | `context = page==7 ? Global : lane_mode` | Voice, Motion; Global derived | No audio write | Accepted at 16-frame boundary | Invalid enum sanitizes to Voice |
| Trigger sanitize | `trigger = finite && requested > 1/127 ? 1 : 0` | exact 0 or 1 | Binary | Whole Controls acceptance | Non-finite becomes Off and counts invalid |
| Trigger event | `boundary && accepted_step && amplitude>0 && trigger==1` | Boolean | Same event count/output as revision 0.4 route 1 | Before that lane's source quantum | Off emits no trigger |
| Physical Trigger | `value < 64 ? 0 : 1` | CC 0-127 | 0-63 Off; 64-127 On | Message dispatch then next Core quantum | Invalid message rejected/counts |
| Voice Model | `round(value*23/127)` | 0-23 | exact endpoints | Contextual CC dispatch | Clamp/sanitize |
| Voice Pitch | `24 + value*72/127` | MIDI 24-96 | exact endpoints | Contextual CC dispatch | Clamp/sanitize |
| Unit Voice fields | `value/127` | 0-1 | exact endpoints | Contextual CC dispatch | Clamp/sanitize |
| Motion except Trigger | `clamp((value-64)/63,-1,1)` | -1 to 1 | CC64 exact Direct zero | Contextual CC dispatch | Clamp/sanitize |
| Sequencer row | Exact revision 0.4 CC28-35 transforms | Existing ranges | Existing bounds | Contextual CC dispatch | Existing sanitize/count |
| Audio processing | Exact revision 0.4 equations and capacities | Existing | Existing Q27/pole/gain bounds | Existing per-sample/quantum timing | Existing recovery |

### State and timing model

- `LaneControlMode::voice` is the default and one accepted Controls field.
- Selecting another lane preserves mode. Re-pressing the accepted lane toggles
  mode once on the positive edge. Global entry and effect Clear remain exact
  revision 0.4 gestures; returning to a lane reveals the retained mode.
- Mode selection changes no lane, voice, scheduler, source, effect, or audio
  history. It is included in snapshots/events/controller trace and reset state.
- Reset returns lane 1 / Voice. Panic preserves accepted page/mode with other
  revision 0.4 semantics. Freeze/capture and recall remain unsupported.
- UI writes and physical mapping use the same accepted mode definition. The
  portable surface model derives exactly 16 slots from a Snapshot.
- Trigger Off prevents future trigger edges but does not rewind or reconstruct
  an already-started source voice. Trigger On restores the predecessor event
  rule at the next accepted quantum.
- Repeatability is byte equality for PCM and canonical event/snapshot/control
  artifacts within the frozen build and partition set.

### Control and performance mapping

| Gesture/context | Top CC20-27 | Bottom CC28-35 | Buttons/feedback |
|---|---|---|---|
| Lane / Voice | Model, Pitch, Harmonics, Timbre, Morph, Decay, Colour, Level | Rate, Phase, Shape, Hits, Rotate, Chance, Repeat, Depth | Same selected lane re-press toggles Motion; accepted `VOICE` shown |
| Lane / Motion | Trigger On/Off, Pitch Motion, Model Sweep, Harmonics Motion, Timbre Motion, Morph Motion, Decay Motion, Level Motion | Same sequencer row | Same selected lane re-press toggles Voice; accepted `MOTION` shown |
| Global | Drive, Cohere, Root, Spread, Tail, Damping, Width, Duck | BPM, Master, six disabled/no-op positions | Button 8 entry/re-press Clear unchanged |

The JUCE app mirrors these 16 positions exactly. Explicit `VOICE` and `MOTION`
buttons set accepted mode; group outlines and a one-line guide explain the three
families. The compiled map is exhaustively compared to `control-map.json`.
Physical endpoint/configuration behavior remains deferred.

### Parameter interactions and edge cases

- Trigger On/Off is independent of amplitude, hits, chance, and route motion;
  those controls retain their own meanings.
- Motion Direct zero means no offset from the Voice base. Negative values remain
  useful for Pitch, Model, Harmonics, Timbre, Morph, Decay, and Level.
- Voice values do not overwrite Motion values and switching views changes no
  parameter bytes.
- Model names and the resolved `NOW` model remain visible in both lane views.
- BPM/Master are edited on Global rather than duplicated above every lane.
- Disabled Global positions do not dispatch and display an em dash.

### Failure behavior

Invalid page/mode/knob indices fail closed; invalid numeric values sanitize and
count under existing rules. UI formatting and tooltips remain outside the audio
callback. No processing allocation, lock, file I/O, endpoint, JSON, or UI work
enters Core processing.

## 10. Target and resource feasibility

| Constraint | Assumption/evidence | Limit | Status |
|---|---|---|---|
| Audio | Exact revision 0.4 48 kHz, 16-frame Core, blocks 1-512 | No equation change | Ready comparator |
| State | One byte-sized accepted mode plus fixed surface descriptors | No dynamic audio state | Feasible |
| UI | 16 sliders, two group outlines, two view buttons, labels/tooltips | JUCE UI thread only | Feasible from authenticated headers |
| Controller | Existing CC20-35/40-47 topology | No new physical control | Ready synthetically |
| Source | Exact configured patcher revision/tree | Read-only, no fallback | Ready |
| Target | Authenticated JUCE 8.0.15 | Build only, fetch off | Ready |
| Real-time/device/listening | No new evidence authorized | Deferred | Unresolved by design |

## 11. Minimal experiment

### Central hypothesis

**HYPOTHESIS:** one stable eight-knob Sequencer row plus a clearly accepted
Voice/Motion top-row context makes all 24 lane values legible on a 16-encoder
surface without changing the sound or removing expressive negative motion.

### Smallest vertical slice

Accepted context state, pure sixteen-slot surface model, contextual CC map,
binary Trigger Enable, two-row JUCE layout, and no other musical change.

### Test signals and gestures

| Field | Bound value |
|---|---|
| Sample rate and block sizes | 48000 Hz; 1, 16, 64, 128, 257, 512 frames |
| Seed | decimal 1346456912 (`0x50414d50`) |
| Timing | Controls/mode accepted only at the next persistent 16-frame quantum; controller edge rules apply before publication |
| Conditions | `PAMP_R05_AUDIO_CMP`, `PAMP_R05_TRIGGER`, `PAMP_R05_SURFACE`, `PAMP_R05_GLOBAL` (4) |
| Falsifying comparator | `PAMP_R05_AUDIO_CMP` must have audio SHA-256 `a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912`, matching revision 0.4 Dry7 exactly |
| Outputs | `audio.wav`, `events.json`, `snapshots.json`, `metrics.json`, `controller-trace.json`, `surface.json`, `manifest.json`, `SHA256SUMS` |
| Tolerances | 16 slots exact; every declared semantic/range exact; non-target records exact; Trigger 0/63 Off and 64/127 On; On comparators exact; PCM finite/Q27 bounded; partition artifacts exact |
| Retention | Checked in under `research/prototypes/pamplist/contract-r05/evidence/`; refuse overwrite |

`PAMP_R05_TRIGGER` resets between CC20 values 0, 63, 64, and 127 in Motion
context. The first two require zero trigger events and exact silence from an
unstarted voice; the latter two require identical events, source state, and PCM.
`PAMP_R05_SURFACE` exhausts both lane modes, all 16 CC values at endpoints and
representative centers, same-lane toggle edges, another-lane selection, every
surface slot, and non-target equality. `PAMP_R05_GLOBAL` retains the revision
0.4 effect/system/no-op/Clear grammar.

### Measurements

- Surface slot count, enabled count, group/context IDs, labels, presentation
  kinds, semantic values, tooltips, and accepted context.
- Controller status/semantic/target and changed-field masks for every context.
- Trigger event count, started mask, PCM hash, source RNG state, and silence.
- Audio comparator hash, finite/peak/saturation metrics, and exact partition
  equality.

### Listening protocol

Deferred to the user's next manual audition. The useful questions are whether
Voice/Motion/Sequencer ownership is immediately understood, same-lane re-press
is discoverable, semantic values help, and Trigger Off/On feels predictable.

### Stop or pivot conditions

- Any lane parameter becomes unreachable or two UI knobs target one field.
- View changes alter audio or musical records.
- Trigger On diverges from the revision 0.4 comparator.
- Trigger Off is not deterministic or controller boundary values disagree.
- Global/Clear or lane isolation regresses.
- UI requires more than sixteen rotary sliders or raw CC values remain the main
  presentation.
- Work requires launch, hardware, a new dependency, or wider DSP changes.

## 12. Acceptance and evidence matrix

| Claim | Check | Level | Initial result | Artifact |
|---|---|---|---|---|
| Proposal/bundle is complete | Structure and ready validators | Proposal | Pending | `contract-r05/` |
| All values fit the surface | Pure surface-model and mapping exhaustion | Host structural | Pending | CTest/surface trace |
| Trigger semantics are truthful | Boundary/event/silence tests | Host structural/signal | Pending | CTest/render |
| Audio is preserved when On | Exact revision 0.4 PCM hash | Host signal | Pending | Retained evidence |
| UI compiles with 16 sliders | Authenticated JUCE configure/build/hash | Target build | Pending | `juce-build.json` |
| Physical controller feels clear | Hardware session | Connected device | Not run | Deferred |
| UI is understandable | User audition | Listening | Not run | Deferred |
| Production ready | Canonical/runtime/distribution gates | Production | Not run | Deferred |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/pamplist/contract-r05/`
- Approval reference: current-thread request to retain every feature, fit the
  lane into sixteen knobs, group Voice versus Sequencer/Motion, and correct the
  Trigger control's silent negative region.
- `validate_implementation_bundle.py --phase ready`: not yet run.

### Files expected to change

- New `ui_model.hpp/.cpp` plus Core/control-map state and mapping updates.
- JUCE two-row presentation, focused tests, renderer/evidence scripts, build
  receipt, CMake version, README, topology, semantic surface, source annotation,
  prototype index, derived handoff/promotion files, results, and gaps.

### Focused tests

- Context sanitize/reset/snapshot equality and zero audio effect.
- Exact sixteen-slot Voice/Motion/Global surface tables and value application.
- All contextual CC transforms, same-lane edge toggle, hold/release, lane/global
  isolation, Trigger midpoint, and UI/MIDI transform parity.
- Trigger Off silence/On predecessor behavior, all-model/source isolation,
  block identity, effect regression, and no allocation.

### Adjacent regression tests

- Exact configured source authentication.
- Revision 0.4 retained evidence authentication and explicit Dry7 comparator.
- Instrument Lab topology/authority freshness.

### Expensive or hardware checks

- Once after freeze: revision 0.5 render reproduction, authenticated JUCE build,
  relocated reproduction, and `current` profile.
- No launch, endpoint, physical device, callback timing, or listening action.

### Deferred work

Physical mapping feel/feedback, app visual inspection by Codex, structured
listening, additional sound features, embedded adaptation, and production.

### Dependency contract

- Macro Voice source remains configured `patcher` commit
  `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, tree
  `58917f3e2e46a30337cfb6292a3504845b1d5552`, read-only with no fallback.
- Controller topology SHA-256 remains
  `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`.
- JUCE 8.0.15 must authenticate against the existing exact tree manifest;
  fetching remains disabled.
- No new library, external DSP, copied UI asset, or source byte enters.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Type | Gap |
|---|---|---|---|---|---|
| CL-001 | EVIDENCE | The lane owns 24 existing values in three functional families | Revision 0.4 Controls/Core | Exact source | None structurally |
| CL-002 | EVIDENCE | Current JUCE presents 26 lane-page rotary sliders and duplicated-looking names | Revision 0.4 JUCE source plus user report | Exact source/direct observation | User count was approximate; defect remains real |
| CL-003 | EVIDENCE | Negative/zero Trigger route cannot fire new accepted triggers | Revision 0.4 Core condition | Exact source | No physical feel claim |
| CL-004 | EVIDENCE | Regular Launch Control 3 provides 16 encoders and eight buttons | Controller authority and first-party guide | Authenticated/first-party | Installed mapping unverified |
| CL-005 | INFERENCE | Accepted Voice/Motion context aligns all values with the surface | State/control reasoning | Design inference | Requires exhaustive tests |
| CL-006 | HYPOTHESIS | Grouping and semantic values make the instrument easier to learn | User feedback plus design | Musical/usability hypothesis | Requires next audition |
| CL-007 | UNRESOLVED | Same-lane re-press is discoverable and pleasant on hardware | No device session | Gap | Deferred |

## 15. Open questions and decision gate

### Open questions

- Whether same-lane re-press is discoverable enough on the physical controller.
- Whether `MOTION` or `MOD` is the clearer short label after audition.
- Whether semantic text boxes provide enough explanation without a longer help
  panel.
- Whether future controller feedback should indicate Voice/Motion context.

These do not block the bounded synthetic/target-build slice; they block
connected-device and listening acceptance.

### Recommendation

Proceed with exactly sixteen rotary controls, accepted Voice/Motion context for
the top row, a stable Sequencer bottom row, explicit grouping/tooltips/semantic
values, and binary Trigger Enable. Preserve every other revision 0.4 musical
field and its audio behavior.

### Approval requested

The current-thread request already authorizes uninterrupted implementation of
this exact revision 0.5 architecture after its SHA-256 is bound into a ready
bundle at `research/prototypes/pamplist/contract-r05/`. Authorization reaches
source, host structural, host signal, and authenticated target-build evidence
only. It does not authorize app launch, endpoints, hardware, real-time or
listening claims, embedded work, distribution, canonical records, staging,
commit, push, or publication.

## 16. Implementation record

### Proposal revision implemented

Pending readiness gate.

### Source and test artifacts

Pending.

### Commands and results

Pending.

### Deviations

None yet.

### Remaining proof gaps

Physical controller behavior, app visual inspection, real-time deadline,
listening usefulness, embedded feasibility, distribution, and production remain
deferred regardless of host/target-build success.
