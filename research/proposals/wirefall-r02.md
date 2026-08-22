# Wirefall revision 0.2: energy and interrupt instrument

> Status: approved for uninterrupted implementation
> Proposal revision: 0.2
> Work type: new-design revision
> Original idea: One highly sensitive, musical ENERGY knob drives an intense high wire-like drone. BREAK introduces rhythmic interruption, PULSE chooses its rate, and TICK moves the interruption from silence toward a short marker.
> Implementation target: Instrument Lab v1 portable C++17 Core and deterministic renderer, followed only after host-signal acceptance by an authenticated JUCE 8.0.15 standalone target built but not launched.
> Working artifacts and evidence ceiling: `wirefall_r02_core_tests` at host-structural, `wirefall_r02_render` at host-signal, and `wirefall-r02-instrument` at target-build.
> Decision gate: the 2026-08-21 request for a full implementation authorizes uninterrupted execution of this bounded revision. Bundle readiness remains mandatory before DSP work.

## 1. Product thesis

### One-sentence thesis

Wirefall is a performative gated drone whose identity is carried by one unusually expressive ENERGY gesture and punctuated by a separately playable interruption.

### Instrument identity

The performer rides ENERGY as the principal musical phrase: a short turn must produce a continuous, predictable rise in pitch, spectral density, brightness, and urgency without crossing an abrupt mode boundary. BREAK then removes that stream rhythmically. PULSE controls how often the interruption arrives, and TICK determines whether the removed moment is empty or marked by a compact, deliberately separate sound. ROOT, COLOR, WIDTH, EDGE, SPACE, OUTPUT, and TEMPO are supporting settings, not competing macros.

This is an instrument rather than a generic effect chain because the sound source, pitch trajectory, timbral trajectory, interrupt scheduler, interrupt shape, and control semantics are one bounded performance system.

### Intended user and musical situation

The prototype is for mouse performance over an existing beat or pulse. It must remain legible without note input: one hand can ride ENERGY while the other introduces and reshapes interruption.

### In scope

- Preserve Wirefall 0.1 as historical source and evidence; create a separate 0.2 prototype.
- Implement a portable, allocation-free C++17 Core, deterministic event renderer, tests, signal report, and retained manifests.
- Implement the ten-pot/four-button/encoder semantic surface defined below.
- Build an authenticated JUCE standalone shell only after all Core and host-signal gates pass.
- Make the standalone mouse-operable and show accepted Core state.

### Out of scope

- Editing, deleting, or reclassifying Wirefall 0.1 evidence.
- A lower `Shadow` voice, the 0.1 error-accumulator pulse grammar, external sync, MIDI/device work, hardware, listening claims, plugin formats, catalog/runtime integration, packaging, publication, or production readiness.
- Launching any application, opening an audio device, listening, staging, committing, pushing, fetching dependencies, or installing packages.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- User feedback on 2026-08-21 establishes the musical center: ENERGY first; a secondary gated/ticked interrupt; another control may set interrupt rhythm.
- Wirefall 0.1 establishes the name, high wire-like drone territory, and evidence gaps, but not an implementation to patch in place.
- The local Instrument Lab workflow is the process authority.
- The existing local JUCE source is authenticated separately; it cannot establish Core or listening evidence.

### Deliverables

- This proposal and a hash-bound ready implementation bundle.
- `research/prototypes/wirefall-r02/` containing Core, renderer, tests, standalone source, CMake, README, and compact retained results.
- WAV audition/render outputs only under ignored build or result paths; no binary audio is proposed as tracked source.

### Acceptance tests

- Contract-ready validation before DSP implementation.
- CMake build and CTest for Core structural behavior.
- The frozen four-condition signal matrix passes at every declared block partition and on repeat.
- Only then, an authenticated JUCE 8.0.15 standalone target compiles and links without being launched.

### Decisions this work may make

- Tune original DSP constants inside the public semantics and frozen objective tolerance envelope before the final implementation freeze.
- Choose internal data structures, layout, and test decomposition while preserving the specified capacities and event convention.

### Decisions this work must not make

- Weaken an acceptance threshold to convert a defect into a pass.
- Reintroduce the `Shadow` voice or 0.1 pulse scheduler as character.
- Promote build evidence to launch, real-time, listening, device, production, or canonical Schuss evidence.
- Modify unrelated `generative-drum-machine` work or make git/publication changes.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| `wirefall_r02_core_tests` | host-structural | All deterministic state, event, reset, panic, and capacity tests pass | Musical usefulness or audio quality |
| `wirefall_r02_render` | host-signal | Frozen matrix passes objective tolerances and partition equivalence | Listening, callback safety, or target feasibility |
| `wirefall-r02-instrument` | target-build | Authenticated JUCE standalone compiles and links | Launch, audio-device access, real-time sound, or physical control |

## 3. Reference anatomy

The bounded reference research in Wirefall 0.1 remains the research base; this revision changes the internal recommendation in response to audition uncertainty.

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Energy rise | A control increases pitch and apparent intensity | User description and 0.1 listening response | Keep; concentrate it into one continuous macro | High |
| Rhythmic removal | Sound periodically disappears or is broken | User description | Keep; make it a simple phase-stable pulse | High |
| Optional marker | An interruption may contain a tick rather than silence | User description | Add as a continuous silence-to-tick setting | High |
| Lower contrasting layer | 0.1 `Shadow` placed a lower voice in the gap | 0.1 source/render | Reject; it made the sparse samples harder to judge | Medium |
| Irregular rate grammar | 0.1 used error-accumulator slot decisions | 0.1 source/render | Reject; use direct musical pulse divisions | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| SOMA LYRA-8 | Hardware instrument | Cross-modulated drone performance | Organismic multi-voice interaction | Wirefall 0.1 source ledger | Keep continuous gesture energy, not its topology |
| UVI Drone | Software instrument | Layered evolving drone macros | Broad source/effect architecture | Wirefall 0.1 source ledger | Wirefall should stay narrower and more tactile |
| Soundmachines DS2 | Hardware drone | Direct performance controls | Immediate hands-on sound shaping | Wirefall 0.1 source ledger | Preserve one-control legibility |
| Erica Synths Plasma Drive | Hardware effect | High-energy bright distortion territory | Processes external input | Wirefall 0.1 source ledger | Treat intensity as source identity, not copied circuitry |
| Mutable Instruments Grids | Open-source modular work | Pattern-density control | Probabilistic drum-event topology | Wirefall 0.1 source ledger | Reject density grammar for this revision |
| Wirefall 0.1 | Local prototype | TENSION/CUT with Wire/Shadow alternation | Deterministic but failed host-signal acceptance | Local source and retained report | Preserve identity; simplify the central experiment |
| Plugin-format lane | VST/AU/AAX | — | Not researched for this bounded prototype | Missing by scope | Do not infer plugin readiness |

## 5. Synthesis and engineering research

| Technical source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Esqueda et al., aliasing measurements for nonlinear models | Objective spectral inspection of nonlinear output | Peer-reviewed, cited in 0.1 | Motivates explicit high-frequency artifact measurement | Does not prescribe Wirefall's oscillator |
| Simper, topology-preserving state-variable filter | Stable TPT SVF recurrence | Published technical derivation, cited in 0.1 | Exact state-variable colour stage | Coefficient modulation still needs bounded updates |
| JUCE 8.0.15 local authenticated source | Standalone host framework | Exact local commit/archive authentication | UI and target-build shell only | Does not establish DSP correctness or real-time evidence |

## 6. Musical-practice research

| Named practice, community, place, and period | Source relationship | Structural principle | Possible translation | Context or restriction | Risk |
|---|---|---|---|---|---|
| Jamaican dub mixing, Kingston studio practice, 1970s | Contextual sources recorded in Wirefall 0.1; no practitioner collaboration | Performative removal can be as active as addition | Treat interruption as a playable negative-space gesture | No copied recordings, names, iconography, genre claim, or claim of authenticity | Decontextualizing a situated practice into a generic control trope |

This prototype borrows no protected musical material and makes no cultural-authenticity claim. Any public framing around dub would require fresh practitioner/context research and attribution; the present control is described neutrally as interruption.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Monotone response curve / interaction design | Macro controls are common | ENERGY maps monotonically across pitch, slope, squeal mix, filter, and gain | A sensitive control remains learnable | One submapping dominates or creates a discontinuity | Step/sweep measurements plus later blinded performance listening |
| Phase-continuous scheduling / real-time systems | Clocked LFO and sequencer practice is common | PULSE division changes preserve normalized phase | Rate can be played without random resets | A change produces a double trigger or missing slot | Partitioned event test at rate boundaries |
| Raised-cosine window / signal processing | Standard gating/windowing prior art | Shape the interrupt pulse without a click unless TICK requests one | Clean silence and a separately controlled marker | Edge becomes too soft at high rates | Boundary discontinuity and full-gate residual checks |

## 8. Novelty map

### Common elements

Additive oscillation, macro mapping, resonant filtering, tremolo/gating, ticks, clock divisions, stereo delay, smoothing, and DC blocking are established techniques.

### Less-common combinations found

The bounded search found many expressive drones and many rhythmic gates, but did not establish a reference with this exact `ENERGY + BREAK + PULSE + TICK` hierarchy.

### Proposed contribution

Within the bounded sources, the contribution is interaction design: one continuous high-energy wire macro remains the entire foreground while a phase-stable negative-space instrument can move continuously from clean removal to a compact marker. This is not a universal novelty claim.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Lower harmonizing `Shadow` during cuts | Competes with the clarified silence-or-tick request | 0.1 audition was hard to assess |
| Stateful processing after the gate | Prevents mathematically complete interruption | 0.1 full-void residual failure |
| Hard nonlinear waveshaping as the normal brightening path | Creates avoidable alias burden at the high end | 0.1 antialiasing failure and Esqueda rationale |
| Error-accumulator pulse grammar | Obscures rate and weakens direct performance causality | Clarified user request |
| Probabilistic ticks | Makes the smallest experiment harder to compare | Determinism and learning risk |

## 9. Recommended architecture

### Signal flow

`ENERGY/ROOT -> harmonic Wire + tracked Squeal -> COLOR TPT SVF -> gain -> DC blocker -> stereo SPACE -> BREAK gate -> optional TICK -> OUTPUT -> finite safety clamp`

All stateful sound processing occurs before the interruption. Consequently `BREAK=1`, `TICK=0`, and the closed center of a pulse can produce exact digital zero.

### Executable DSP contract

At sample rate `Fs=48000`, maximum block size is 512 frames and the fixed event capacity is 128 events per block. Normalized controls are sanitized to `[0,1]`. Control smoothing uses `x[n]=target+(x[n-1]-target)exp(-1/(tau Fs))`.

| Mechanism | Equation or pseudocode | Coefficients/ranges | Gain and stability bound | Update timing | Failure behavior |
|---|---|---|---|---|---|
| ENERGY pitch | `s=36 E^1.15`; `f=clamp(82.4069*2^((ROOT+s)/12),55,1800)` | `E` in `[0,1]`, `ROOT` in `[-12,12]` semitones; 12 ms smoothing | Fundamental cannot exceed 1.8 kHz | Per sample | Non-finite target rejected and counted |
| Harmonic Wire | `H=min(24,floor(20000/f))`; `p=clamp(2.40-1.50E-0.45COLOR,.55,2.40)`; `w=sum(h^-p sin(h phi+.17(h mod 4)))/sqrt(.5 sum(h^-2p))` | Harmonics `1...H`, fixed loop bound 24 | Analytic RMS normalization; emitted partials remain below 20 kHz | Per sample | Invalid normalizer mutes the source and counts a fault |
| Tracked Squeal | `m=2+7E`; equal-power crossfade between `floor(m)` and `ceil(m)` harmonics that are `<=H`; `mix=clamp(.08+.32E+.25COLOR,0,.65)` | No inharmonic or above-band oscillator | Added source bounded by explicit mix | Per sample | Out-of-range harmonic contributes zero |
| COLOR filter | TPT SVF: `g=tan(pi fc/Fs)`, `k=1/Q`, `a1=1/(1+g(g+k))`, `v1=a1*ic1eq+a1*g*(input-ic2eq)`, `v2=ic2eq+g*v1`, state updates `ic1eq=2v1-ic1eq`, `ic2eq=2v2-ic2eq`; output `.82 input+.18 v1/sqrt(Q)` | `fc=min(18000,f(2+5E+2COLOR))`; `Q=1.1+5.5E^2(.3+.7COLOR)` | `Q<=6.6`; TPT recurrence | Coefficients every 16 samples; state per sample | Invalid coefficient keeps last valid coefficient and counts a fault |
| ENERGY gain | `A=.16*10^((3E)/20)` | About 3 dB electrical range before spectral contribution | Normal path must not reach safety clamp | Per sample | Sanitized E |
| DC/SPACE | DC blocker `R=exp(-2 pi 12/Fs)`; cross-delay 23/31 ms, wet `.18 SPACE`, feedback `.20 SPACE` | Fixed delay capacities for 48 kHz | Feedback `<=.20` | Per sample, before gate | Reset clears filter/delay state |
| PULSE scheduler | Rates `{OFF,.5,1,2,3,4,6,8}` per beat; `Hz=rate*tempo/60`; rate changes preserve normalized phase | Selector hysteresis `.012`; tempo 40–240 BPM | Phase wrapped to `[0,1)` | Per sample | OFF leaves gate open and phase stable |
| BREAK window | Closed-pulse duty `d=.08+.34 WIDTH`; edge `min((1.5+10.5 EDGE^2)ms,.45 d/Hz)`; raised-cosine 0→1, hold, 1→0 pulse `p`; `gMain=1-BREAK*p` | Duty `.08...42`; BREAK `[0,1]` | `gMain` in `[0,1]` | Per sample | Invalid phase opens gate |
| TICK marker | For 384 frames, `u=n/(L-1)` and `t=.24 TICK sqrt(BREAK) sin(8 pi u) sin(pi u)^2` | 8 ms, four cycles, exact zero endpoints and zero mean by construction | Peak before output `<=.24` | Restarted at each pulse onset | OFF/BREAK=0 gives exact zero |
| Output safety | `y=OUTPUT*(gMain*spaceWire+t)` | OUTPUT `[0,1]`; finite clamp only to `±.8912` | Normal frozen experiment must never clamp | Per sample | Non-finite becomes zero; 3 faults in 48,000 samples escalates to Panic |

### State and timing model

Events at frame `k` are accepted before rendering frame `k`; stable input order resolves same-frame events. Events beyond the fixed per-block capacity are rejected without mutating state and increment a diagnostic. Absolute rendered-sample and monotonic diagnostic counters are excluded from reset equivalence; all other state must be identical.

| Operation | Envelope/state behavior | Timing | Equivalence/diagnostics |
|---|---|---|---|
| Reset | 240-frame fade down, clear oscillator/filter/delay/pulse/tick/control-smoothing state, then 240-frame fade up | Sample-exact | A second reset restarts the fade-down; normalized post-reset state and future output are identical |
| Panic press | 480-frame fade down, then latch silence | Sample-exact | DSP state may continue but output is zero while latched |
| Panic release | Clear non-finite window and fade up over 240 frames | Sample-exact | Does not claim reset equivalence |
| Downbeat | Set pulse phase to zero and allow the pulse-onset event | Before current frame | Deterministic at every partition |
| Tick preview | Start one marker with current TICK/BREAK scaling, without altering pulse phase | Before current frame | Deterministic |
| Open momentary | Force `gMain=1` while held; pulse phase continues | Per sample | Release resumes current phase |
| Freeze/capture | Not implemented | — | No hidden state |
| Recall/reconnect/external clock | Not implemented | — | No claim |

### Control and performance mapping

The target surface follows the Gills-sized ten-pot/four-button/encoder vocabulary but is mouse-only in this revision. No physical protocol mapping is claimed.

| Control or gesture | Range/default | DSP mapping | Perceptual role | Safety or pickup behavior |
|---|---|---|---|---|
| 1 ENERGY, visually primary | 0–1 / `.32` | Pitch, harmonic slope, squeal, filter, gain | Main phrase and intensity | 12 ms smoothing |
| 2 BREAK | 0–1 / `0` | Interruption depth | Add negative-space rhythm | Smoothed; full depth tested |
| 3 PULSE | OFF, x1/2, x1, x2, x3, x4, x6, x8 / OFF | Phase-continuous rate selector | Rhythm density | Detent hysteresis |
| 4 TICK | 0–1 / `0` | Marker amplitude | Silence-to-marker character | Windowed exact endpoints |
| 5 ROOT | -12 to +12 semitones / `0` | Base pitch exponent | Register setting | Smoothed |
| 6 COLOR | 0–1 / `.55` | Harmonic slope/squeal/filter | Spectral bias | Bounded Q and cutoff |
| 7 WIDTH | 0–1 / `.35` | Closed-pulse duty | Interruption length | Bounded by slot |
| 8 EDGE | 0–1 / `.34` | Gate edge time | Soft removal to sharper break | Minimum 1.5 ms |
| 9 SPACE | 0–1 / `.10` | Pre-gate cross-delay | Stereo breadth | Feedback `<=.20` |
| 10 OUTPUT | 0–1 / `.82` | Final gain | Level setting | Finite safety clamp |
| Button 1 OPEN | momentary | Force main gate open | Escape from rhythm | Accepted-state feedback |
| Button 2 TICK PREVIEW | momentary | Trigger marker | Audition marker | Windowed |
| Button 3 DOWNBEAT | trigger | Reset pulse phase | Align gesture | Sample-exact |
| Button 4 PANIC | press/release | Latched fade-down / fade-up | Safety | Sample-exact |
| Encoder turn TEMPO | 40–240 / 120 BPM | Pulse clock | Beat relation | Clamped |
| Encoder tap / hold | tap tempo / RESET | Tempo estimator / reset sequence | Performance clock / recovery | Tap gaps outside 250–1500 ms ignored; hold threshold belongs to UI |

### Parameter interactions and edge cases

- PULSE=OFF makes BREAK inert in the scheduled path; TICK PREVIEW still functions.
- TICK does not leak into the silent condition and never changes the Wire source or schedule.
- At PULSE=x8 the edge is shortened before it can consume more than 90% of the closed interval.
- ROOT and ENERGY are jointly clamped by the 1.8 kHz fundamental ceiling; monotonicity is therefore evaluated on the frozen default ROOT path.
- SPACE tails are cut by the interruption because the delay precedes the gate.

### Failure behavior

Invalid controls are rejected and counted, event overflow is fail-closed, invalid intermediate samples become zero, and three non-finite observations in any rolling 48,000-sample window enter Panic. No exception, allocation, file write, log formatting, or lock is permitted from Core processing.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Sample rate | 48 kHz frozen experiment; Core accepts 44.1–96 kHz | Contract and tests | Reject unsupported rates | Proposed |
| Block size | Arbitrary positive partitions tested; host callback max 512 | Contract | Fixed arrays, no process allocation | Proposed |
| Oscillator work | At most 24 partial iterations plus one squeal pair per sample | Analytic bound | No dynamic harmonic allocation | Proposed |
| Delay memory | Two fixed arrays sized for 31 ms at 96 kHz plus guard | Analytic bound | Under 32 KiB stereo float storage | Proposed |
| Events | 128 per block | Contract | Explicit overflow diagnostic | Proposed |
| Numeric format | `double` phase/coefficient/state in Core; float host buffers allowed at adapter | Contract | Finite checks | Proposed |
| Dependency | JUCE 8.0.15, commit `91ad83ae34a81e0833b1a2b0866f54846370ae53`, archive SHA-256 `04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70` | Existing authenticated local source | Shell only | Available, not yet consumed |
| Device/real-time | No app launch or audio-device access authorized | User boundary | Build evidence only | Out of scope |

## 11. Minimal experiment

### Central hypothesis

A continuous ENERGY sweep can produce a large, monotone, musically graduated rise in pitch and brightness, while BREAK/PULSE create a complete rhythmic interruption whose silence and tick variants share exactly the same schedule.

### Smallest vertical slice

Render four 24-second stereo conditions at 48 kHz and 120 BPM from one portable Core, using the same event ledger under partitions `1,16,64,257,512`, then repeat the reference partition. No host UI is involved.

### Test signals and gestures

| ID | Gesture |
|---|---|
| `R02_ENERGY` | PULSE OFF. Hold ENERGY `.10,.30,.50,.70,.90` for 2 s each; sweep `.05→.95` for 10 s; hold `.95` for 4 s. |
| `R02_SILENCE` | ENERGY `.68`, TICK `0`; exercise BREAK `0→.5→1` while PULSE visits x1, x2, x4, x8 in 4-second spans. |
| `R02_TICK` | Exactly the `R02_SILENCE` main-control event ledger, with TICK `.85`. |
| `R02_CMP_TREMOLO` | Same rate/depth schedule as silence, but use sinusoidal amplitude modulation and no tick as the explicit comparator. |

| Field | Bound value |
|---|---|
| Sample rate and supported block sizes | 48,000 Hz; partitions `1,16,64,257,512` |
| Deterministic seed | `0x57465232` reserved and intentionally unused |
| Event/sample timeline convention | Event at frame `k` is applied before frame `k`; stable input order |
| Literal condition IDs and count | Four IDs listed above |
| Falsifying comparator condition | `R02_CMP_TREMOLO` |
| Output names and kinds | Per-condition 24-bit stereo WAV, event CSV, metric JSON; suite manifest JSON |
| Artifact retention policy and location | Compact JSON/CSV/manifests in `research/prototypes/wirefall-r02/results`; WAV and builds ignored |

### Measurements and objective tolerances

- No NaN/Inf, processing allocation, event overrun, normal-path safety clamp, sample peak above `0.8912`, absolute DC above `1e-4`, or adjacent-sample boundary discontinuity above `0.032`.
- WAV bytes and event ledgers are exact across every partition and the repeat.
- Measured fundamental is within 15 cents of the specified ENERGY pitch.
- Every `.20` ENERGY step raises the fundamental by 500–900 cents; four successive spectral-centroid comparisons are positive; final/first centroid ratio is at least 2.5.
- Final/first ENERGY-segment RMS gain is 0.5–4.0 dB.
- Highest non-harmonic component below 20 kHz is at most -60 dBFS after excluding eight FFT bins around emitted harmonics.
- At BREAK=1 and TICK=0, the interior closed-pulse peak is at most one 24-bit integer LSB (`1/8388607`).
- In TICK, interruption-region RMS is at least -36 dBFS, tick peak is at most -9 dBFS, and the main Wire band is suppressed by at least 24 dB.
- SILENCE and TICK have identical pulse-onset and closed-window schedules.

### Listening protocol

No new listening is required to pass this implementation. If later authorized, render level-matched, blinded short gestures centered on ENERGY sensitivity and silence-versus-tick preference, then record the user's response separately from objective evidence.

### Stop or pivot conditions

- Do not create or build the JUCE target if any Core structural or host-signal tolerance fails.
- Do not weaken a metric after observing a failure. Revise the proposal/bundle and retain the failed result instead.
- Stop at target-build even if successful; no application launch or audio-device access follows.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Proposal is implementation-ready | Ready-bundle validator | proposal/source boundary | Pending | `contract/` |
| Core state/event model is deterministic | CTest unit/partition/reset tests | host-structural | Pending | Test executable/report |
| ENERGY has the specified monotone range | Frozen signal analyzer | host-signal | Pending | Metrics JSON |
| Interrupt can be silence or tick | Residual/parity/suppression checks | host-signal | Pending | Metrics JSON |
| Standalone source is dependency-authenticated | Instrument Lab CMake authentication | source/target configuration | Pending | Configure log |
| Standalone compiles/links | Native build | target-build | Pending | Build log/product |
| Standalone launches and sounds correct | Prohibited in this task | real-time/listening | Not claimed | None |
| Physical controls work | Prohibited in this task | connected-device | Not claimed | None |
| Canonical Schuss runtime integration | Prohibited in this task | production-integration | Not claimed | None |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/wirefall-r02/contract`
- Proposal fingerprint and approval reference: generated after this text is frozen
- `validate_implementation_bundle.py --phase ready`: required before DSP source

### Files expected to change

- New `research/prototypes/wirefall-r02/**` source, tests, contract, docs, and retained compact results.
- This proposal's implementation-record section after validation.
- No existing instrument, catalog, architecture, task, or governance file.

### Focused tests

- Core controls/defaults, event timing, capacity/overflow, reset equivalence, panic, pulse phase, exact full interruption, tick endpoints, and allocation guard.
- Renderer partition/repeat byte equivalence and frozen condition metrics.

### Adjacent regression tests

- Instrument Lab bundle validators.
- Existing Instrument Lab native configuration path only as required to authenticate JUCE; no broad compatibility or release profile is justified by a prototype-local addition.

### Expensive or hardware checks

- One native configure/build after implementation freeze and signal acceptance.
- No reproduction profile, hardware, network, launch, or listening operation.

### Deferred work

Fresh listening, UI visual inspection, audio callback/device evidence, MIDI/controller mapping, plugin formats, packaging, ARM/Gills target work, catalog registration, and production integration.

### Dependency contract

The only external dependency is JUCE 8.0.15 at commit `91ad83ae34a81e0833b1a2b0866f54846370ae53`, authenticated by archive SHA-256 `04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70`. Allowed modules are `juce_core`, `juce_events`, `juce_graphics`, `juce_gui_basics`, `juce_audio_basics`, and `juce_audio_devices`; `juce_dsp` is not allowed. The source must already exist locally and match the contract. Fetch/download/install is forbidden. JUCE notices remain required for any later distribution, which is outside this task.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Source type | Notes or proof gap |
|---|---|---|---|---|---|
| WF02-R01 | EVIDENCE | The user wants one sensitive musical main knob and a separate rhythmic interrupt that can be silence or a tick | User feedback, 2026-08-21 | Primary design input | Exact preferred curve still needs listening |
| WF02-R02 | EVIDENCE | Wirefall 0.1 passed deterministic Core work but retained DC, void, antialiasing, ENERGY/TENSION, and Shadow acceptance gaps | 0.1 retained report/source | Local primary artifact | Does not predict 0.2 success |
| WF02-R03 | INFERENCE | Removing Shadow and stateful post-gate DSP will make silence/tick identity easier to assess | R01 plus 0.1 failure anatomy | Design inference | Falsified if later listening remains ambiguous |
| WF02-R04 | EVIDENCE | TPT SVF and alias-measurement sources support the selected implementation/measurement tools | Simper; Esqueda et al., cited in 0.1 | Technical sources | They do not establish musical merit |
| WF02-R05 | HYPOTHESIS | The proposed ENERGY map feels sensitive yet musical | Architecture and curve | Testable hypothesis | Objective monotonicity is necessary, not sufficient |
| WF02-R06 | HYPOTHESIS | Silence and tick variants share one readable rhythmic gesture | Frozen schedule parity design | Testable hypothesis | Later listening required for usefulness |
| WF02-R07 | EVIDENCE | The specified JUCE source is locally authenticated | Existing Instrument Lab evidence | Local dependency evidence | Must be rechecked by configure; no launch claim |

## 15. Open questions and decision gate

### Open questions

- Whether the final ENERGY sensitivity should be concentrated lower, centered, or higher on the knob remains a listening question.
- Whether the tick should later gain pitch or material controls remains deliberately deferred.
- Whether PULSE should ultimately remain a separate large control or become a clocked performance gesture remains a UI/listening question.

### Recommendation

Implement the frozen four-control center first, retain objective failures honestly, and only expose the standalone build after Core acceptance. Subsequent revision should be driven by hands-on audition rather than by adding more synthesis modes.

### Approval recorded

The user's 2026-08-21 request to “go ahead and give it a full implementation” authorizes proposal revision 0.2, the `new-design` lane, the three named working artifacts, and evidence only through target-build. It does not authorize app launch, audio devices, listening, physical devices, staging, commit, push, publishing, or evidence promotion.

## 16. Implementation record

Complete after the frozen contract is validated and implementation work finishes.

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
