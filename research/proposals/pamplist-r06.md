# Pamplist 0.6: Control Response and Impact Trails

> Status: proposed
> Proposal revision: 0.6
> Original idea: Verify Phase, Shape, Rotate, and every Global control from the accepted surface through DSP; preserve correct lane semantics, make the shared cohesion body and Clear musically legible, and add a persistent seven-colour per-lane percussive history rather than an oscilloscope.
> Implementation target: Schuss Instrument Lab v1 portable C++17 Core, deterministic 48 kHz renderer, and authenticated JUCE 8.0.15 macOS standalone
> Working artifact and evidence level: built but unlaunched revision 0.6 `Pamplist.app`, focused control-response evidence, exact revision 0.5 dry comparison, and a bounded seven-lane impact-history model at target-build evidence
> Decision gate: the current-thread request explicitly authorizes uninterrupted proposal-to-implementation work, subject to a ready revision 0.6 bundle before implementation edits.

## 1. Product thesis

### One-sentence thesis

Pamplist keeps its existing seven-lane sequencer grammar, makes the shared
resonant body respond clearly enough to perform, and shows each lane as a
colour-coded impact trail whose brightness records actual recent sound energy
and whose sparks record triggers.

### Instrument identity

The seven independent voices, Voice/Motion contexts, sixteen-knob surface,
Euclidean patterning, and source-order model bank remain Pamplist. `Phase`
still offsets a lane in time, `Shape` still forms the continuous value sent to
nonzero Motion destinations, and `Rotate` still moves a nontrivial Euclidean
pattern without changing its hit count. Revision 0.6 does not silently turn
those three controls into tone controls.

The correction is in two places. First, the existing shared body is presently
so quiet that its retained tail before Clear peaks at roughly -83 dBFS; its
modal controls and Clear are therefore structurally correct but practically
hard to hear. The body output and ducking range become stronger while Cohere
zero remains the exact dry path. Second, the UI gains a persistent percussive
history rather than a waveform scope: seven horizontal colour lanes show
recent pre-cohesion contribution energy, trigger sparks, and a faint shared
body field.

### Intended user and musical situation

A performer shaping a dense generative rhythm in the standalone application,
who needs to see which lane is contributing, understand which sequencer
controls require an interaction partner, and use the Global body as an audible
performance gesture.

### In scope

- Trace `Phase`, `Shape`, `Rotate`, all eight cohesion controls, BPM, Master,
  and Clear from surface/controller acceptance through Core state and output.
- Preserve the existing Phase, Shape, and Rotate equations, but make their
  dependencies explicit in tooltips and objective tests.
- Increase the modal-body output gain from `0.82` to `12.0` and the duck
  sensitivity factor from `6.0` to `24.0`; retain linear Cohere crossfade and
  exact dry output at Cohere zero.
- Add cumulative, normalized per-lane pre-cohesion output energy to the
  accepted Snapshot, computed without allocation or host/UI work.
- Add a portable fixed-state activity reducer and a JUCE `ImpactHistory`
  component with seven existing lane colours, 192 samples at 20 Hz, trigger
  sparks, shared-body haze, and Clear markers.
- Give Clear immediate accepted-state visual feedback while retaining its
  effect-history-only semantics.
- Add focused response, reset, partition, safety, activity-model, UI-source,
  authenticated build, and bounded objective evidence.
- Update the existing Pamplist prototype authorities to revision 0.6 without
  allocating canonical identity or adding it to the desktop audition library.

### Out of scope

- Changing the authenticated macro-voice source, 24-model order, voice DSP,
  random-state virtualization, controller topology, or source dependencies.
- Turning Shape into trigger velocity, changing Euclidean hit placement,
  changing Phase range, or changing Motion-route scales.
- Adding or removing controls, pages, lanes, effects, presets, external clock,
  plug-in formats, Ksoloti/Gills behavior, or shared visualization framework.
- App launch, endpoint access, physical-controller work, live deadline/xrun
  measurement, controlled listening, canonical promotion, catalog/library
  entry, packaging, distribution, or publication.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- Revision 0.5 is the exact predecessor. Proposal SHA-256:
  `8c15dd3c38ca8a585c2603d219daccbba9446dff7a08156e0ba579fac25e1423`.
- Revision 0.5 source, structural, host-signal, target-build, relocated, and
  routine checks passed. Its seven-voice dry audio SHA-256 is
  `a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912`.
- The user has directly auditioned revision 0.5 and reports that Phase, Shape,
  Rotate, most Global fields, and Clear seem ineffective; BPM, Drive, and
  Cohere are at least partly perceptible.
- Source inspection proves every named field is accepted and read. Phase is a
  fractional lane-cycle offset; Rotate changes only patterns with Hits 1-15;
  Shape changes only the continuous lane value routed to Motion destinations.
- At Cohere zero all eight body controls are intentionally bypassed. In the
  retained Clear fixture, effect state clears exactly, but the pre-Clear tail
  peak is only 9,151 Q27, approximately -83.3 dBFS.
- Existing lane colours, accepted Snapshot authority, atomic whole-value
  mailbox, source tree, Instrument Lab seam, and authenticated JUCE dependency
  remain exact predecessor dependencies.
- The request authorizes bounded implementation and build/test work, but not
  staging, commit, app launch, endpoints, hardware, or promotion.

### Deliverables

- This proposal and a ready bundle at
  `research/prototypes/pamplist/contract-r06/`.
- Response tests proving Phase and Rotate change event timing and Shape changes
  routed modulation while documenting their genuine no-effect cases.
- Stronger but bounded six-mode body response with an exact dry comparator and
  individually falsifying Global parameter fixtures.
- Cumulative per-lane energy telemetry, portable activity reduction, and a
  fixed 9.6-second seven-colour impact-history UI.
- Clear acceptance feedback and a visible history marker without changing dry,
  lane, scheduler, or source state.
- Updated Core/UI tests, renderer/evidence, JUCE build receipt, prototype
  metadata, topology, handoff, results, and gaps.

### Acceptance tests

- Phase 0 versus 64 changes eligible trigger times for a frozen 5-of-16 lane
  while preserving rate and hit count; Rotate 0 versus 3 changes the 5-of-16
  trigger positions while preserving count.
- Shape variants produce different modulation trajectories and PCM when a
  nonzero Motion destination is present; trigger-only event timing remains
  exact across Shape variants and the UI explains this dependency.
- With Cohere active, each of Drive, Root, Spread, Tail, Damping, Width, and
  Duck has a nonzero independently measured output difference; all selected
  response comparisons reach at least `5e-4` normalized stereo RMS difference
  or a parameter-specific stronger invariant.
- The frozen silent-input effect tail before Clear peaks at least `5e-4`
  normalized, Clear makes the next effect-only quantum exact zero, increments
  one generation/count, and changes no lane, voice, scheduler, or source state.
- Cohere zero remains byte-identical to revision 0.5 dry PCM even with all
  other cohesion controls at extremes.
- Nominal output remains finite, Q27 bounded, and free of recovery and
  saturation diagnostics in the frozen fixtures; all six host partitions are
  exact within one build.
- Per-lane cumulative energy is finite, monotone while running, exact across
  host partitions, zero for silent/unstarted lanes, and reset by Core reset.
- The portable activity reducer captures energy and trigger deltas between UI
  polls, handles reset/rollback, maps silence to zero, and reports Clear once.
- The audio callback path retains zero post-construction allocation. The JUCE
  history owns fixed 192-sample storage and never reads raw audio pointers.
- The authenticated JUCE target builds and source review proves seven colours,
  seven history rows, trigger sparks, cohesion field, and Clear marker are
  bound to accepted Snapshot telemetry.

### Decisions this work may make

- Exact Pamplist-local history geometry, opacity, labels, colours derived from
  the existing palette, and window dimensions.
- Portable activity reducer layout and logarithmic display mapping.
- Revision 0.6 objective fixtures, diagnostics, tooltips, and accepted-state
  feedback copy.
- Pamplist-local tests and generated prototype metadata necessary for freshness.

### Decisions this work must not make

- Repurpose Phase, Shape, Rotate, Trigger, or any Motion route.
- Change source bytes, model bank, source RNG, scheduler rate/hit/probability/
  repeat math, lane cardinality, controller CC mapping, or dry mixing.
- Add a new global effect or let any body control leak through Cohere zero.
- Put painting, allocation, locks, I/O, JSON, or endpoint work on the audio path.
- Refactor other instruments or introduce a shared telemetry/visualization API.
- Modify retained revision 0.2-0.5 proposal, contract, or evidence bytes.
- Allocate canonical records, alter the audition library, or claim live,
  device, listening, production, packaging, or distribution evidence.
- Launch, access endpoints/hardware, install, stage, commit, push, publish,
  upload, or flash.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Built but unlaunched revision 0.6 `Pamplist.app`, response/effect renders, exact dry comparator, and portable activity-history tests | target-build | Every questioned control is either objectively effective under its declared dependency or explicitly documented; body/Clear response meets frozen bounds; seven-lane history transport is bounded; authenticated app compiles and fingerprints | Visual quality, musical approval, live callback deadline, endpoint/controller behavior, production integration, or distribution |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Phase | Adds 0-127/128 of one lane cycle before step and local-phase extraction | Exact Core source | Keep; clarify it is alignment, not tone | High |
| Shape | Produces Gate/Pulse/Triangle/Sine/Ramp/Decay/Hold/Smooth values only on accepted steps | Exact Core source/tests | Keep; expose its Motion-route dependency | High |
| Rotate | Adds a modulo-16 offset inside the Euclidean hit predicate | Exact Core source/tests | Keep; expose Hits 0/16 no-effect cases | High |
| Cohere | Linear dry-to-body crossfade; zero is exact dry | Exact Core and predecessor comparator | Keep | High |
| Modal body | Six stable complex modes, but current output multiplier is 0.82 | Exact Core and retained metrics | Increase output multiplier only | High |
| Duck | `1/(1+6*duck*envelope)`, with retained envelope below 0.08 | Exact source/metrics | Increase sensitivity to 24 | High |
| Clear | Zeros modal and duck history without touching sources or scheduler | Exact source/tests | Keep semantics; strengthen tail and feedback | High |
| Current UI | Sixteen controls and seven existing colours, no history view | Exact JUCE source | Add fixed percussive history | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| Pamplist 0.5 | Local predecessor | Accepted-state surface and six-mode cohesion body | Correct wiring but weak effect tail and no longitudinal activity | Exact source/evidence/user audition | Normative state and dry comparator |
| Tide Pit Gills UI | Local prototype | Fixed accumulator and audio-to-UI bounded publication | Oscilloscope suits continuous texture | `research/prototypes/tide-pit-gills` | Reuse the bounded-threading lesson, not the waveform design |
| Schuss Generative Drums | Local prototype | Lane activity and cycle feedback | Percussive identity is event-oriented | `research/prototypes/generative-drum-machine` | Prefer impact history to raw waveform |
| Hardware/VST/modular product lane | Not searched for this bounded successor | Many products show meters, scopes, or step grids | No external behavior is normative | Explicit gap | Make no novelty or product-equivalence claim |

## 5. Synthesis and engineering research

| Technical source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Pamplist 0.5 Core and retained r04/r05 evidence | Scheduler, routes, complex modes, exact dry, Clear, metrics | Exact local source and measurement | Normative baseline and falsifier | Does not prove audibility or visual quality |
| JUCE 8.0.15 authenticated local headers | Component painting, timer callbacks, colours, fixed rectangles | Exact build dependency | Thin host rendering | Compile success is not visual inspection |
| Instrument Lab workflow | Accepted Snapshot drives presentation; UI work stays off callback | Accepted architecture | Owns telemetry boundary | Does not choose display metaphor |
| ADR 0018 | Changed-boundary proportional validation | Accepted decision | Limits revision checks to affected Core/UI/native boundaries | Does not lower proof thresholds |

**EVIDENCE:** the controls are wired. **EVIDENCE:** Shape is mathematically
inactive for a trigger-only lane because Trigger is edge-based and all other
routes are Direct. **EVIDENCE:** the retained Clear tail is technically nonzero
but extremely quiet. **INFERENCE:** raising only modal return gain and duck
sensitivity will make the existing body controls legible while preserving
their identities. **HYPOTHESIS:** an energy/event trail will communicate lane
contribution better than an oscilloscope for this percussive instrument.

## 6. Musical-practice research

N/A - this revision borrows no named tradition, repertoire, rhythmic identity,
recording, visual motif, community practice, or cultural label. Its event-trail
display is derived solely from Pamplist's own lane and energy records.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Monotone cumulative counters / telemetry | Common in meters and diagnostics | Core publishes cumulative energy; UI differences consecutive accepted snapshots | No short impact is lost between 20 Hz polls | reset creates negative/huge delta | Rollback/reset fixture must emit zero and rebase |
| Fixed circular history | Common in scopes and timelines | 192 UI-owned samples wrap without allocation | About 9.6 seconds of rhythmic memory | ordering flips at wrap | Fill beyond capacity and compare chronological order |
| Log amplitude display | Standard audio metering practice | Map -80 dBFS to 0 and 0 dBFS to 1 | Quiet tails remain visible without dominating | silence produces log invalidity | Exact silence must map to finite zero |
| Event overlay | Common sequencer visualization | Trigger-count deltas produce one bright spark per affected UI slice | Separates scheduling from residual sound | multiple hits between polls disappear | Preserve trigger presence and count delta, not exact pixel count |

## 8. Novelty map

### Common elements

Per-lane colours, logarithmic activity meters, ring histories, trigger markers,
modal resonators, wet/dry controls, and effect Clear operations are established.

### Less-common combinations found

No broad product search was performed. The bounded local comparison found no
other Schuss prototype combining seven independently coloured pre-effect energy
histories, trigger overlays, and a shared-body difference field.

### Proposed contribution

No universal novelty claim is made. The contribution is a Pamplist-specific
diagnostic/performance view in which what sounded recently, what triggered,
and what the shared body added are visually distinct without presenting a
waveform or fixed step grid as musical authority.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Make Shape alter trigger velocity automatically | Silently repurposes a Motion source and changes predecessor sound | Existing route contract |
| Replace Phase/Rotate with new controls | They are wired and musically distinct | Core audit |
| Add another global effect | User asked to verify/fix current controls, not expand the chain | Scope |
| Conventional oscilloscope | Mixes all lanes and emphasizes waveform polarity over percussive events | User request and instrument identity |
| FFT/spectrogram | More CPU/UI complexity and weaker lane ownership | No need for frequency diagnosis |
| Read output buffers directly from paint/timer thread | Violates host ownership and can tear | ADR/workflow boundary |
| Clear the whole sequence or voice tails | Contradicts effect-only Clear identity | Existing state contract |

## 9. Recommended architecture

### Signal flow

```text
accepted Voice/Motion/Sequencer controls
  -> unchanged seven schedulers and macro voices
  -> per-lane scaled stereo contributions
       -> cumulative fixed telemetry -> accepted Snapshot -> UI activity reducer
       -> unchanged signed dry sum
  -> existing drive and six-mode body
       -> 12x modal return, stronger duck, linear Cohere
       -> cumulative shared-body difference telemetry
  -> Master and Q27 output

accepted Snapshot deltas at 20 Hz
  -> 192-column ImpactHistory ring
  -> seven coloured energy trails + trigger sparks + cohesion haze + Clear mark
```

### Executable DSP contract

| Mechanism | Equation or pseudocode | Coefficients/ranges | Gain and stability bound | Update timing | Failure behavior |
|---|---|---|---|---|---|
| Phase | `effective = lane_phase_q32 + (phase_u7 << 25)` | 0-127 gives 0 through 127/128 cycle | Integer Q32; no overflow within supported session assumptions | Each 16-frame quantum | Sanitize to 0-127 |
| Shape | `v=accepted_step ? clamp(shape(local_phase)*depth,0,1) : 0` | Eight existing shapes; depth 0-1 | Existing finite clamp | Each quantum before routes | Invalid shape becomes Pulse |
| Rotate | `hit = euclidean((step + rotation) mod 16,hits)` | hits 0-16; rotation 0-15 | Exact hit cardinality; no allocation | Step boundary | Invalid bounds sanitize |
| Drive | Existing normalized `tanh((1+7d)x)` blend | d 0-1 | Existing finite guard | Per sample, 30 ms smoothing | Recover to dry and clear body on nonfinite |
| Modal modes | Existing six complex stable poles and ratios | Root 24-84, Spread/Tail/Damp/Width 0-1 | Every pole strictly 0-1; final Q27 saturation guard | Per sample, 30 ms smoothing | Existing clear/recovery |
| Modal return | `effect = driven + 12.0 * wet * duck_gain` | fixed gain 12.0 | Frozen nominal fixtures require zero saturation/recovery | Per sample | Nonfinite rejects body sample and recovers |
| Duck | `duck_gain=1/(1+24*duck*envelope)` | duck 0-1, envelope finite/nonnegative | strictly `(0,1]` | Per sample | Existing recovery |
| Cohere | `out=dry + cohere*(effect-dry)` | 0-1 linear | Cohere 0 exact dry bytes | Per sample, 10 ms smoothing | Nonfinite sanitized/recovered |
| Clear | zero six complex mode states and duck envelope; increment accepted generation/count | uint32 generation | No scheduler/source/control mutation | Next accepted quantum | Repeated same generation is no-op |
| Lane energy | `E_i += (scaled_main_i/Q27)^2 + (scaled_aux_i/Q27)^2` | seven doubles, finite nonnegative | Cumulative double; reset to zero on Core reset/transport reset | Each rendered sample | Nonfinite source already replaced; clamp negative UI delta to zero |
| Activity reduction | `rms=sqrt(max(0,dE)/(2*dFrames)); display=clamp((20log10(max(rms,1e-4))+80)/80,0,1)` | floor -80 dBFS; 20 Hz | UI-only fixed arithmetic | Accepted Snapshot poll | reset/rollback rebases and emits zero |
| History | fixed array 192; newest index advances modulo 192 | 9.6 seconds at 20 Hz | No heap work after component construction | UI timer | audio-off/reset records bounded zero |

### State and timing model

- Controls still accept only at a 16-frame Core quantum.
- Energy is calculated from each lane's actual post-level, pre-cohesion stereo
  contribution, so a source tail remains visible after its trigger spark.
- The UI reducer consumes cumulative counters from accepted Snapshots. It does
  not read callback buffers, scheduler internals, or raw MIDI.
- Reset and seed-driven transport reset zero cumulative lane energy; the UI
  detects frame/counter rollback and rebases without drawing a false spike.
- Panic/Running false produces no new energy and preserves the existing
  accepted control semantics.
- Clear zeros effect history and creates one visual marker; it does not erase
  lane history because that history describes prior voice activity truthfully.
- Freeze/capture, recall, serialization, and controller feedback remain absent.

### Control and performance mapping

| Control or gesture | Range or states | DSP mapping | Perceptual role | Safety or pickup behavior |
|---|---|---|---|---|
| Phase | 0-127 | fractional lane-cycle offset | shifts alignment against other lanes | no tone/hit-count promise |
| Shape | 8 states | continuous Motion source | changes routed pitch/model/tone/level motion | no audible effect when all continuous routes are Direct |
| Rotate | 0-15 | Euclidean offset | moves hits within 16-step pattern | no effect at Hits 0 or 16 |
| Drive | 0-100% | existing nonlinear pressure inside body | saturation/pressure | exact bypass through Cohere 0 |
| Cohere | 0-100% | linear dry/body crossfade | overall body amount | exact dry at zero |
| Root/Spread | note / 0-100% | modal frequencies and ratios | pitch/inharmonic character | bounded below Nyquist guard |
| Tail/Damp | 0-100% | poles and high-mode weights | duration/brightness | strictly stable poles |
| Width | 0-100% | modal pans | mono-to-wide body | dry stereo unchanged at Cohere 0 |
| Duck | 0-100% | stronger wet attenuation on attacks | clears space around impacts | affects wet return only |
| Clear FX | momentary generation | zero effect state | abruptly removes current body tail | accepted once; voice/scheduler untouched |

Controller CCs and page gestures remain byte-for-byte revision 0.5 semantics.
Application feedback remains accepted Snapshot authority. Physical endpoint,
installed mapping, feel, LEDs, and reconnect stay deferred.

### Parameter interactions and edge cases

- Root through Duck require Cohere above zero by design. Their tooltips and the
  Global guide must state this once without hiding the controls.
- Shape requires at least one nonzero signed Motion route other than Trigger.
- Rotate requires Hits 1-15. Phase is most legible against another lane or a
  fixed metronomic reference.
- Clear is most audible when Cohere and Tail are raised and there is a current
  body tail; visual feedback still confirms accepted Clear when the body is dry.
- Strong body gain may reach the existing final Q27 guard under extreme live
  settings; nominal frozen fixtures must not saturate, while target listening
  determines whether the range is musically excessive.

### Failure behavior

Invalid/nonfinite controls retain predecessor sanitization. Any nonfinite mode
or body result increments recovery, clears body history, and uses the dry path.
Telemetry never decides audio behavior. A non-monotone telemetry Snapshot
rebases the UI reducer rather than producing a false full-scale column.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Sample rate | exact 48 kHz | Existing target/Core | fixed | accepted |
| Host blocks | 1-512 frames | Existing Core contract | max 512 | accepted |
| Source quantum | 16 frames | Authenticated source adapter | fixed | accepted |
| Audio telemetry | seven double accumulators and fixed arithmetic | Proposed Core change | no allocation/lock/I/O | planned test |
| UI history | 192 x seven levels plus flags | Proposed JUCE component | fixed under 16 KiB | feasible |
| UI cadence | 20 Hz existing timer | Existing JUCE source | 50 ms samples | accepted |
| Dependencies | same source, Instrument Lab, JUCE 8.0.15 | Existing authorities | no new package/fetch | accepted |
| Real-time CPU | small fixed arithmetic increase | Inference only | not promoted without live measurement | deferred |
| License/distribution | private local prototype | ADR 0016 and existing source closure | no distribution claim | unchanged |

## 11. Minimal experiment

### Central hypothesis

The reported weak controls arise from dependency visibility for Phase/Shape/
Rotate and inadequate modal-return gain for Global/Clear, not disconnected
state. Preserving the sequencer grammar, strengthening the existing body, and
showing accepted per-lane energy/event history will make the controls legible
without adding a new effect or changing source voices.

### Smallest vertical slice

One lane-response condition, one Global sensitivity/Clear condition, one exact
dry predecessor comparator, and one portable telemetry/history condition,
followed by the authenticated standalone build.

### Test signals and gestures

| Field | Bound value |
|---|---|
| Sample rate and supported block sizes | 48 kHz; 1, 16, 64, 128, 257, 512 |
| Deterministic seed | `0x50414d50` |
| Event/sample timeline convention | Controls accepted at 16-frame boundaries; half-open host intervals; cumulative telemetry covers every rendered source sample |
| Literal condition IDs and count | `PAMP_R06_DRY_CMP`, `PAMP_R06_SEQUENCE`, `PAMP_R06_GLOBAL`, `PAMP_R06_ACTIVITY` (4) |
| Falsifying comparator condition | `PAMP_R06_DRY_CMP` must retain r05 audio SHA-256 `a07ed1...7912` |
| Output names and kinds | stereo WAV, events JSON, snapshots JSON, metrics JSON, activity JSON, surface JSON, manifest, SHA256SUMS |
| Objective tolerances | exact dry bytes; exact partition artifacts; finite/Q27; zero nominal saturation/recovery; active control delta >= `5e-4` RMS or stronger invariant; pre-Clear tail peak >= `5e-4`; post-Clear effect-only zero |
| Artifact retention policy and location | checked in under `contract-r06/evidence` after freeze |

### Measurements

- Trigger frame/count differences for Phase and Rotate; routed modulation/PCM
  differences and trigger-time equality for Shape.
- Stereo RMS/peak/difference, side energy, mode frequency/pole/state, tail
  energy, duck reduction, Clear state/count, saturation/recovery.
- Per-lane cumulative energy, poll-delta activity, trigger/Clear flags, reset
  behavior, partition identity, fixed history ordering.
- Exact dry predecessor SHA-256 and authenticated app executable SHA-256.

### Listening protocol

Deferred to the user's next audition. Suggested checks: compare Phase against a
second lane; try Shape after moving Pitch or Level Motion away from Direct; try
Rotate at Hits 5; set Cohere around 50%, then sweep each body control; raise
Tail and press Clear during a ringing passage; observe lane trails and trigger
sparks. This remains informal product feedback, not a controlled listening
evidence packet.

### Stop or pivot conditions

- Stop if source identity or ready-bundle fingerprints drift.
- Preserve current sequencer behavior if Phase/Shape/Rotate wiring tests pass;
  do not invent replacement semantics to force audible difference.
- Reduce or redesign body gain only through a recorded proposal deviation if
  nominal fixtures saturate or become unstable.
- Stop target-build promotion if telemetry allocates or crosses UI/audio
  ownership, history is unbounded, or exact dry comparison fails.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Questioned controls are wired | focused response matrix and surface application | host structural | planned | Core/UI tests |
| Phase/Shape/Rotate semantics remain exact | event/modulation/audio comparators | host signal | planned | r06 sequence evidence |
| Global body/Clear are materially active | independent sensitivity and tail/Clear bounds | host signal | planned | r06 global evidence |
| Cohere zero preserves r05 sound | exact audio SHA-256 | host signal | planned | r06 dry comparator |
| Telemetry is bounded and truthful | energy/history/reset/partition/allocation tests | host structural/signal | planned | activity tests/evidence |
| Standalone contains the impact history | authenticated configure/compile/link and source assertions | target build | planned | JUCE receipt |
| Visual design is useful | user operates rebuilt app | listening/product feedback | deferred | user report |
| Live deadline and controller behavior | live instrument session | real-time/device | deferred | none |
| Canonical/library integration | separate promotion work | production integration | out of scope | none |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/pamplist/contract-r06/`
- Proposal fingerprint and approval reference: generated after this file is
  frozen; current-thread user request authorizes uninterrupted execution.
- `validate_implementation_bundle.py --phase ready`: not yet run.

### Files expected to change

- `research/prototypes/pamplist/include/schuss/pamplist/core.hpp`
- new portable activity-model header/source under the same include/src tree
- `research/prototypes/pamplist/src/core.cpp`
- `research/prototypes/pamplist/src/ui_model.cpp`
- `research/prototypes/pamplist/src/juce_main.cpp`
- `research/prototypes/pamplist/src/render.cpp`
- Pamplist CMake/tests/build/evidence scripts and revision 0.6 authorities
- Pamplist README, semantic surface, topology, prototype index, promotion
  needs, and implementation handoff

### Focused tests

- Existing five Release and sanitizer CTests plus one activity-model CTest.
- Sequencer dependency/response, individual Global sensitivity, Clear, energy
  accumulation/reset, history wrap/reset, snapshot coherence, and allocation.
- Exact control-map and surface transforms remain revision 0.5 compatible.

### Adjacent regression tests

- Exact r05 dry audio comparator and all-model/source isolation.
- Existing Global mapping/Clear edge, context, Trigger, and sixteen-slot UI.
- Instrument Lab prototype freshness and affected current profile.

### Expensive or hardware checks

- Reproduce the four r06 conditions once after freeze across six partitions.
- Build and fingerprint the authenticated JUCE app without launch.
- Relocated Core-only reproduction once after freeze if declared inputs changed.
- No hardware, endpoint, app launch, release, or distribution check.

### Deferred work

User visual/listening judgment, live callback timing, physical controller,
audition-library entry, canonical promotion, packaging, and distribution.

### Dependency contract

No dependency enters this revision. Preserve patcher commit
`08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, synthesis tree
`58917f3e2e46a30337cfb6292a3504845b1d5552`, the exact declared source files,
Instrument Lab v1, controller topology SHA-256
`d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`,
and authenticated JUCE 8.0.15. Fetching remains disabled. Distribution and
assembled-notice review remain separate gates.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Source type | Notes or proof gap |
|---|---|---|---|---|---|
| R06-001 | EVIDENCE | Phase, Shape, and Rotate are accepted and read by Core | `control_map.cpp`, `ui_model.cpp`, `core.cpp` | exact local source | Does not prove perceptibility |
| R06-002 | EVIDENCE | Shape changes only continuous Motion destinations; Trigger is boundary enable | `core.cpp:998-1017` | exact local source | Trigger-only Shape is intentionally silent |
| R06-003 | EVIDENCE | Global controls are bypassed at Cohere zero | Core/tests/r05 results | exact source and comparator | UI must communicate dependency |
| R06-004 | EVIDENCE | Clear zeros effect history but retained pre-Clear peak is about -83 dBFS | r04 metrics/tests | retained measurement | Explains user report without a wiring fault |
| R06-005 | INFERENCE | 12x modal return and 24x duck sensitivity make the existing controls legible | Current equations and metrics | engineering inference | Frozen response experiment may falsify |
| R06-006 | HYPOTHESIS | Seven-lane impact history is clearer than an oscilloscope for Pamplist | User request and instrument structure | design hypothesis | Requires user visual audition |
| R06-007 | EVIDENCE | Accepted Snapshot/mailbox is the authoritative cross-thread UI seam | workflow and predecessor implementation | accepted architecture | Live deadline remains unmeasured |

## 15. Open questions and decision gate

### Open questions

- Whether a 12x body return is musically strong enough or too strong across all
  personal presets can only be settled by audition; the frozen fixture guards
  safety, not taste.
- Whether 9.6 seconds is the best visual memory length remains a UI judgment.
- Whether Phase should later be displayed in degrees or fractions is cosmetic
  and deferred; its accepted value remains 0-127.

### Recommendation

Implement the bounded response/telemetry revision exactly as specified. Keep
Phase, Shape, and Rotate behavior; strengthen only the existing modal-return
and duck ranges; add objective dependency explanations and a fixed accepted-
Snapshot impact trail. Do not add another effect or promotion step.

### Approval requested

The current-thread request already authorizes uninterrupted implementation of
this revision 0.6 architecture after the exact proposal fingerprint and ready
bundle pass. That authorization covers Pamplist-local source, tests, retained
host evidence, and an authenticated unlaunched app build. It does not authorize
app launch, endpoints/hardware, staging/commit/push, library/canonical changes,
packaging, distribution, or promotion of listening/live/device/production
evidence.

## 16. Implementation record

### Proposal revision implemented

Pending.

### Source and test artifacts

Pending.

### Commands and results

Pending.

### Deviations

Pending.

### Remaining proof gaps

Pending.
