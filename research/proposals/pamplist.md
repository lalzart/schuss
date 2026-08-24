# Pamplist: Eight-Lane Clocked Macro-Voice Instrument

> Status: proposed
> Proposal revision: 0.2
> Work type: `new-design`
> Original idea: A private Schuss instrument combining a Pam-style eight-lane programmable clock and modulation brain with one complete Plaits-derived 24-engine macro voice, main and auxiliary outputs, deterministic routing, and hands-on desktop control.
> Implementation target: Schuss Instrument Lab v1 portable C++17 Core, deterministic 48 kHz renderer, regular Launch Control 3 adapter, and authenticated JUCE 8.0.15 macOS standalone
> Working artifact and evidence level: a built but unlaunched `Pamplist.app`, deterministic stereo render, and accepted-state/control traces at `target-build`
> Decision gate: the user's 2026-08-24 instruction to implement the recommended version authorizes uninterrupted proposal-to-prototype work through the stated target-build ceiling. It does not authorize application launch, endpoint access, listening, canonical promotion, staging, commit, or push.

## 1. Product thesis

### One-sentence thesis

Pamplist is a self-playing macro-voice animated by eight visible, repeatable
clock lanes: the performer selects one lane, reshapes its temporal behavior,
and routes it into the voice until a coherent pattern emerges from pulse,
phase, probability, and timbre.

### Instrument identity

The performer sets one tempo, chooses a 24-engine voice and base tone, then
treats eight clock lanes as musical hands. Each lane owns a rate, phase,
waveform, 16-step Euclidean mask, probability, repeat window, amplitude, and
eight signed routing amounts. The instrument answers with one evolving voice
whose main and auxiliary signals remain separate as stereo output.

This is an instrument rather than a generic rack because the lane model,
routing destinations, defaults, reset behavior, controller gestures, voice
boundary, and visual feedback form one fixed playable system.

### Intended user and musical situation

Private desktop improvisation on the current Apple-silicon Mac, primarily with
the regular Launch Control 3 and optionally with mouse control. It is intended
for pulse music, generative percussion, drones with clocked timbral motion, and
rapid engine audition—not exact hardware-module emulation or distribution.

### In scope

- Exactly eight deterministic clock/modulation lanes at one master tempo.
- Sixteen fixed Euclidean steps per lane with hits 0-16 and rotation 0-15.
- Sixteen exact rational rates from `/16` through `x16`, phase, eight waveform
  shapes, probability, repeat window 0-64, and amplitude.
- One 8-by-8 signed routing matrix targeting Trigger, Pitch, Model,
  Harmonics, Timbre, Morph, Decay, and Level.
- One complete 24-engine macro voice using the authenticated source dependency
  already reviewed by Schuss, with main and auxiliary on distinct outputs.
- Portable fixed-capacity Core, deterministic renderer, synthetic regular
  Launch Control 3 mapping, state-driven JUCE UI, authenticated standalone
  target, and relocated reproduction.

### Out of scope

- Pamela's firmware, menus, display, panel text, visual design, VCV code,
  undocumented algorithms, calibration, CV electronics, expanders, banks, or
  exact hardware equivalence.
- External/MIDI clock, DIN sync, CV inputs, pitch scales, cross-lane logic,
  Flex/humanization, persistence, or arbitrary destinations in revision 0.2.
- Polyphony, samples, effects, plug-ins, Ksoloti/Gills execution, or firmware.
- Canonical Schuss component, graph, instrument, provider, runtime-factory,
  record-set, project, or machine identity.
- App launch, live endpoints, callback-deadline proof, connected-device proof,
  listening claims, packaging, distribution, or publication.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/STATUS.md`, ADRs 0016-0018,
  and `docs/workflows/instrument-development.md`.
- The user's current-thread private-use clarification and explicit 2026-08-24
  authorization to implement the recommended version.
- Official Pamela's PRO Workout page/manual as observable-behavior references:
  <https://busycircuits.com/pages/alm034> and
  <https://assets.busycircuits.com/docs/alm034-manual.pdf>.
- Official Plaits documentation/source and the exact local
  `patcher@08d3e6e...` source review.
- Instrument Lab v1, authenticated JUCE 8.0.15, and exact regular Launch
  Control 3 topology.
- Fixed 48 kHz processing; host blocks 1-512 partition a persistent 16-frame
  source/control quantum.

### Deliverables

- This proposal and a ready Sonic Research Lab implementation bundle.
- `research/prototypes/pamplist/`: portable Core, source adapter, controls,
  snapshot transport, renderer, tests, state-driven JUCE standalone, prototype
  index, topology, evidence, results, gaps, and handoff.
- An additive noncanonical audition-library entry after the standalone
  executable is built and its hash frozen.

### Acceptance tests

1. Proposal and bundle readiness pass before Pamplist DSP source is written.
2. The configured `patcher` checkout matches the lock; the synthesis subtree
   has its expected Git tree and no tracked or untracked drift.
3. All 24 voice engines render finite main and auxiliary output in a bounded sweep.
4. Every rate, shape, Euclidean extreme, probability extreme, loop, route,
   amplitude, and voice parameter is bounded and deterministic.
5. Probability is keyed by seed/lane/loop position, not host partition or lane
   evaluation order.
6. Supported host partitions produce byte-identical PCM, event traces, and
   final accepted state for the frozen experiment.
7. Stop, zero hits, zero amplitude, and zero route produce exact silence where
   specified; all output is finite and bounded to Q27 `[-1, 1)`.
8. Synthetic Launch Control 3 tests exhaust channel, CC, mapping, lane
   selection, signed routing, invalid input, and accepted-state reflection.
9. Repeated processing allocates nothing and performs no lock, I/O, JSON, or UI work.
10. Authenticated JUCE 8.0.15 configures, compiles, and links without launch.
11. Instrument Lab, current, affected native, and relocated reproduction pass.

### Decisions this work may make

- Prototype-local names, exact rate table, waveform math, Euclidean rotation,
  keyed musical hash, quantum carry, state/snapshot representation, UI layout,
  labels, defaults, and diagnostics.
- The smallest source-authentication adapter needed to consume the already
  reviewed exact source without canonical allocation.

### Decisions this work must not make

- Pamela's source/algorithm equivalence, undocumented behavior, or branding.
- A changed Plaits algorithm/revision, catalog preference, component contract,
  provider, Ksoloti eligibility, or production status.
- A different Launch Control model or an assumption that the regular model has faders.
- Real-time, connected-device, audible, distribution, or production claims.
- App/device access, installation, source-checkout mutation, staging, commit,
  push, upload, flash, or publication.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Built `Pamplist.app`, deterministic stereo render, event/state trace, and synthetic control trace | target-build | Core/source/control/render suites and authenticated standalone build pass; executable hash retained | launch, callback deadline, controller receipt, listening, Ksoloti, distribution, or production |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Master clock | BPM-based start/stop | **EVIDENCE:** ALM manual 3.2-3.3 | Keep internal 20-300 BPM timeline; stop resets phase | High |
| Eight outputs | Eight independently edited outputs share the clock | **EVIDENCE:** ALM feature list | Transform into eight internal modulation lanes | High |
| Rates | Per-output divisions/multiplications include non-integer choices | **EVIDENCE:** ALM manual | Keep bounded exact rational table | High |
| Shapes | Pulse, ratchet, triangle, sine, envelope, and random shapes occupy a step | **EVIDENCE:** ALM manual 4.1 | Keep eight independently specified shapes; reject equivalence | High |
| Euclidean filtering | Steps, hits, padding, and rotation mask steps | **EVIDENCE:** ALM manual 4.7 | Keep fixed 16 steps, hits, rotation; defer padding/length | High |
| Probability/loops | Probabilistic skipping plus loop reset structures randomness | **EVIDENCE:** ALM manual 4.6/4.8 | Keep probability and addressable repeat window | High |
| Cross operations | Another output can mix, mask, hold, sample, or reset a lane | **EVIDENCE:** ALM manual 4.9 | Transform into lane-to-voice matrix; defer cross-lane operators | High |
| Flex | Swing, human error, ramps, humps, delays alter timing | **EVIDENCE:** ALM manual 4.10 | Reject from 0.2 so phase and loops stay legible | High |
| Macro voice | Model, pitch, tone controls, trigger/dynamics, main/aux | **EVIDENCE:** official Plaits manual/source | Keep through exact dependency and local adapter | High |
| Hardware/UI | Display, program encoder, voltage I/O, panel | **EVIDENCE:** manuals | Reject; Pamplist owns distinct presentation | High |

## 4. Adjacent landscape

| Product/project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| Pamela's PRO Workout | Eurorack modulator | Eight synced lanes, shapes, ratios, probability, Euclidean filters, loops, cross ops | General CV source with deep compact menus | [ALM](https://busycircuits.com/pages/alm034) | Behavior reference only; no UI/firmware emulation |
| Official Pam for VCV | Software module | Officially described as hardware-feature equivalent | Virtual Eurorack, not fused voice | ALM page above | Confirms software feasibility, no source authority |
| Mutable Instruments Marbles | Random sampler | Clock ratios, random timing/voltage, history reuse, loops | Controls novelty versus repetition | [Manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/manual/) | Make repeatable randomness a primary gesture |
| Ornament & Crime v1.2 | Open multi-function module | Euclidean trigger lengths/filtering | App utility rather than fixed instrument | [Manual](https://ornament-and-cri.me/user-manual.pdf) | Fixed sixteen-step lanes are a bounded established choice |
| Mutable Instruments Plaits | Macro oscillator | Model-selected voice with main/aux and internal dynamics | No integrated multichannel clock brain | [Manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/plaits/manual/) | Preserve exact voice boundary; lane interaction is Pamplist's identity |
| Schuss Generative Drums 0.6 | Local prototype | Seeded scheduling, whole snapshots, Mutable adapter, LC3 | Six authored drum lanes and voice pool | `research/proposals/schuss-generative-drum-machine.md` | Reuse mechanics only, not rhythms/allocation/identity |

The bounded search covered official manuals/pages, Mutable's archive/repository,
the Ornament & Crime manual, algorithmic-rhythm papers, and existing Schuss
prototypes. No inspected item combined one complete macro voice with eight
addressably random clock lanes and this selected-lane voice matrix. This is not
a global novelty claim.

## 5. Synthesis and engineering research

| Source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Godfried Toussaint, “The Euclidean Algorithm Generates Traditional Musical Rhythms,” Bridges 2005 | Even distribution of `k` onsets over `n` slots | Primary paper | Mask family and rotation-class expectation | Cultural identifications are not product identity or permission; only abstract distribution is used |
| Salmon, Moraes, Dror, Shaw, “Parallel Random Numbers: As Easy as 1, 2, 3,” SC11 | Keyed counter-to-random mapping without sequential dependence | Primary paper/project | Block/order-independent decisions | Pamplist uses a smaller musical hash and claims no Random123 statistics |
| Mutable Instruments Plaits firmware/manual | 24 engines, modulation, envelope/LPG, main/aux | Exact source/documentation | Normative voice dependency | Whole instrument remains new-design |
| Schuss Instrument Lab v1 | Persistent numeric profile, bounded host seam, evidence separation | Local accepted prototype contract | Mechanical implementation route | Does not decide music, controls, or promotion |

## 6. Musical-practice research

| Named practice, place, period | Source relationship | Structural principle | Translation | Context/restriction | Risk |
|---|---|---|---|---|---|
| Steve Reich's early live phase-shifting, New York, 1966-67, especially *Piano Phase* | [Composer's program note](https://stevereich.com/composition/piano-phase/) | Repeated material creates changing composites when phase relationships move | Stable per-lane phase offsets expose emergent composite figures | No score, motif, recording, title, or identity is copied; revision 0.2 does not claim gradual Reich phasing | Low with attribution |

Only the idea that phase relationships can be audible process is translated.
The human performance challenge, gradual drift, specific pattern, tape context,
and composition form are lost. Autonomous gradual phasing is therefore
rejected from revision 0.2; the performer chooses stable offsets directly.

## 7. Computer-science transfer search

| Concept/home field | Audio prior art found | Mapping | Benefit | Failure mode | Falsifier |
|---|---|---|---|---|---|
| Counter-based random access in parallel simulation | Seeded sequencers and Marbles-like loop memory are common; no primary audio source inspected required this exact address tuple | Hash `(seed,lane,loop-position,domain)` rather than advance shared RNG | Block, evaluation order, or unrelated routes cannot move another pattern | Bias, collision, or bad loop address | Exact decisions/PCM across partitions and reversed lane evaluation; bounded mean test |
| Rational phase accumulators | Modular clock division/multiplication and phase are common | Integer quotient/remainder phase carry | Partition-independent phase without float drift | Overflow or discontinuity | Exact trace/PCM at 1,16,64,128,257,512 frames |

## 8. Novelty map

### Common elements

Clocks, rational ratios, Euclidean masks, probability, random loops,
modulation matrices, macro oscillators, and controller-selected editing are
individually established.

### Less-common combinations found

Pam combines lanes and cross processing but no fused voice. Marbles makes
randomness replayable through a different three-clock/voltage interaction.
Plaits supplies the voice but no clock brain. Generative Drums joins rhythms
and Mutable voices but not an arbitrary lane-to-one-voice matrix.

### Proposed contribution

**HYPOTHESIS:** one selected-lane workflow with eight visible destinations
makes a deep clock modulator behave like a coherent standalone instrument. The
contribution is the interaction contract: temporally complete lanes,
addressable random decisions, and one gesture that moves a lane across the
whole macro voice.

### Rejected directions

| Direction | Reason | Evidence/risk |
|---|---|---|
| Literal Pam emulation | Large menu/proprietary surface, not needed | Obscures instrument thesis |
| Full cross-lane operators | Cycles/order/controller paging before primary test | Official space is large |
| Gradual drift | Weakens master lock/direct control | Retained as future option |
| Variable Euclidean length/padding | Extra states before usability evidence | Fixed 16 keeps controls legible |
| Full Ksoloti target | Retained source reports 188,048 bytes versus 45,056 | Desktop first; H7/reduced bank separate |
| Canonical Macro Voice promotion | Audit requires source-failure repair, contracts, bindings, eligibility | Prototype use must not promote it |

## 9. Recommended architecture

### Signal flow

```text
tempo + running + seed
  -> 8 persistent rational phase lanes
  -> 16-step Euclidean masks
  -> keyed probability/repeat decisions
  -> eight unipolar shapes + amplitude
  -> 8 x 8 signed routing matrix
  -> Trigger/Pitch/Model/Harmonics/Timbre/Morph/Decay/Level
  -> exact 24-engine macro voice
  -> main Q27 (left) + auxiliary Q27 (right)
```

The topology exposes all lane, mask, random-address, matrix, adapter, voice,
and output roles even when fused in C++.

### Executable DSP contract

| Mechanism | Equation/pseudocode | Range | Bound | Timing | Failure |
|---|---|---|---|---|---|
| Master phase | per sample, `advance=floor((tempo_milli_bpm*2^32*4+rem)/(60000*48000))`; carry `rem`; apply sixteen iterations before each source quantum | 20-300 BPM, Q32 sixteenth-note steps | integer carry below denominator | each persistent 16-frame quantum | invalid tempo -> 120 BPM + recovery |
| Lane phase | add master advance times exact ratio with per-lane remainder | 16 positive ratios; phase `[0,1)` | wraps modulo `2^32` | each quantum | invalid ratio -> x1 |
| Euclidean mask | `hit=((rotated_step*hits)%16)<hits` | hits 0-16, rotation 0-15 | Boolean | new step | 0 exact off; 16 exact on |
| Addressed random | `u=mix64(seed,lane,address,domain)>>11 / 2^53`; loop 0 uses free step, otherwise `step%loop` | probability `[0,1]`, loop 0-64 | `u` in `[0,1)` | new step | invalid probability clamps |
| Shape | gate, pulse, triangle, sine, ramp, exp decay, sample-hold, or smooth random at local step phase | eight shapes, amplitude `[0,1]` | lane clamps `[0,1]` | sampled once per quantum | non-finite -> zero |
| Matrix | `m[d]=clamp(sum lane[l]*route[l][d],-1,1)` | 64 weights `[-1,1]` | explicit clamp | each quantum | invalid route -> zero |
| Trigger | rising accepted lane step with positive Trigger weight; simultaneous triggers OR | threshold `>1/127` | at most one source trigger/quantum | before source render | coalesced count retained |
| Pitch/Model | base plus `24*m[pitch]` semitones; engine plus `round(23*m[model])` | note 24-96; engine 0-23 | explicit clamp | before render | clamp + count |
| Unit modulation | base plus matrix value | `[0,1]` | clamp before Q27 | before render | non-finite -> default |
| Macro voice | authenticated wrapper renders one 16-frame main/aux block | 24 engines, 48 kHz | final Q27 saturation; gain 0.65 | exactly 16 frames | auth failure stops build; invalid sample -> zero |

The rate table, in controller-index order, is `/16`, `/12`, `/8`, `/6`,
`/4`, `/3`, `/2`, `x3/4`, `x1`, `x4/3`, `x3/2`, `x2`, `x3`, `x4`,
`x8`, and `x16`. Each entry is stored as an exact positive numerator and
denominator. A tempo or rate change preserves accumulated Q32 phase and clears
only the affected fractional division remainder before future advance.

For local step phase `x = phase_q32 / 2^32`, an accepted mask/probability step
evaluates the eight shapes as follows; a rejected step is exactly zero before
amplitude. Gate is `1`. Pulse is `1` for `x < 0.5`, otherwise `0`. Triangle is
`1 - abs(2x - 1)`. Sine is `0.5 - 0.5*cos(2*pi*x)`. Ramp is `x`.
Exponential decay is `exp(-6x)`. Sample-hold is the address-keyed unit random
value `a`. Smooth random is `a + (b-a)*(3x^2-2x^3)`, where `a` and `b` use
the current and next address with a separate shape-random domain. Phase control
is an observation offset of `phase_u7/128`; changing it never rewrites the
underlying accumulated phase.

### State and timing model

- Core owns scheduler, source, diagnostics, and accepted snapshots.
- Host blocks copy from a persistent 16-frame output quantum and never realign state.
- One coherent `Controls` value is sanitized/accepted at a new quantum. UI and
  controller presentation use the resulting `Snapshot`, never raw input.
- Stop silences and resets master/lane/voice at the next quantum; Start begins phase zero.
- Reset while stopped reconstructs all state, clears diagnostics, and publishes defaults.
- Seed changes preserve phase; the next step uses the new key. Persistence is unsupported.
- Non-finite controls use explicit defaults; non-finite source samples become zero and count.

State equivalence is byte equality of PCM and canonical event/control/snapshot
traces across supported partitions; exact integer equality of frame, phase and
remainders, lane steps/addresses, resolved engine, counts, and accepted
controls. Padding, pointers, paths, wall time, GUI state, and endpoints are excluded.

### Control and performance mapping

Regular Launch Control 3 Custom Mode 1, MIDI channel 16:

| Control | Range | Mapping | Role | Safety |
|---|---|---|---|---|
| Buttons CC40-47 | press/release | rising press selects lane 1-8; release accepted/no dispatch | choose lane | snapshot owns selection |
| Top CC20-27 | 0-127, center 64 | selected lane routes to Trigger, Pitch, Model, Harmonics, Timbre, Morph, Decay, Level | move lane across voice | center exact zero |
| Bottom CC28 | 0-127 | 16-entry rate | speed | discrete index |
| Bottom CC29 | 0-127 | phase `[0,1)` | placement | accepted value |
| Bottom CC30 | 0-127 | eight shapes | contour | discrete index |
| Bottom CC31 | 0-127 | hits 0-16 | density | exact endpoints |
| Bottom CC32 | 0-127 | rotation 0-15 | start point | discrete index |
| Bottom CC33 | 0-127 | probability 0-1 | certainty | exact endpoints |
| Bottom CC34 | 0-127 | repeat 0 then 1-64 | free/repeating | zero means free |
| Bottom CC35 | 0-127 | amplitude 0-1 | route depth | exact zero |
| JUCE controls | bounded fields | running, tempo, seed, engine, pitch, base tone/dynamics, gain | source/global behavior | whole snapshots; accepted display |

Endpoint identity, receipt, LED/OLED feedback, encoder feel, and reconnect are
not exercised. Controller topology is protocol authority only.

### Parameter interactions and edge cases

- Hits/probability/amplitude zero suppress before routing; probability one accepts every mask hit.
- Loop zero uses monotonic addresses; loop one repeats one decision; other lengths repeat exactly.
- Phase/rate changes preserve stored phase; only future observation/advance changes.
- Multiple triggers coalesce; continuous routes sum then clamp.
- Model changes occur only at quantum boundaries and do not crossfade in 0.2.
- Left is source main and right is auxiliary; they are not summed.

### Failure behavior

Mismatched source, JUCE, proposal, controller, bundle, topology, or derived
hash fails before build/evidence promotion. Unsupported sample rate/frame count
clears output and does not advance. Invalid MIDI is ignored/counted. No fallback
engine, source revision, network fetch, alternate controller, or implicit target exists.

## 10. Target and resource feasibility

| Constraint | Assumption/value | Evidence | Limit | Status |
|---|---|---|---|---|
| Sample rate | 48 kHz | wrapper/Instrument Lab | no resampling | Ready to test |
| Quantum | 16 frames | wrapper/existing source practice | persistent carry | Ready to test |
| Host blocks | 1,16,64,128,257,512 | bounded lab path | max 512 | Ready to test |
| Voice | one 24-engine instance; source reports 27,448 state bytes | exact manifest | one resident | Authenticate/build |
| Lane/matrix | 8 lanes, 64 routes, fixed arrays | equations | no callback allocation | Ready |
| Numeric | declared float/double scheduler; Q27 source/output | wrapper | saturated Q27 | Ready |
| Source | `patcher@08d3e6e...`, tree `58917f...` | accepted lock/review | exact clean subtree | Present; verify |
| JUCE | 8.0.15 local authenticated tree | manifest SHA-256 `db7daa7f...ac5` | no fetch | Reauthenticate |
| Ksoloti | 188,048 bytes versus 45,056 region | retained manifest | 417.37% | Deferred |
| Use policy | private, no redistribution | user instruction and private JUCE lock | provenance only now | Accepted |

## 11. Minimal experiment

### Central hypothesis

**HYPOTHESIS:** with one macro voice held constant, independently phased and
loopable lanes routed across eight voice facets produce a stable, repeatable,
and differentiable process understandable one selected lane at a time.

### Smallest vertical slice and conditions

- `PAMP_BASE`: lane 1 triggers four evenly spaced hits; other routes zero.
- `PAMP_EUCLID`: 5-of-16 trigger plus phased pitch and timbre lanes.
- `PAMP_LOOP`: probability 0.5, seven-step repeat; repeated decisions must match.
- `PAMP_MATRIX`: eight shapes/rates each route to one destination.
- `PAMP_24`: bounded 24-engine finite main/aux sweep.
- `PAMP_SILENCE`: stopped, zero-hit, zero-amplitude, zero-route subcases.
- `PAMP_CMP_PHASELESS`: same rates/hits/probability/base voice as matrix but
  phases and non-trigger routes zero; trace and PCM must differ from matrix.

| Field | Bound value |
|---|---|
| Sample rate/block sizes | 48,000; 1,16,64,128,257,512 |
| Seed | `0x50414D50` (`PAMP`) |
| Timeline | controls accepted at next persistent quantum; trigger before quantum; partitions never realign |
| Conditions | seven IDs above; silence has four subcases |
| Falsifier | `PAMP_CMP_PHASELESS` |
| Outputs | `audio.wav`, `events.json`, `snapshots.json`, `metrics.json`, `manifest.json`, `SHA256SUMS` |
| Tolerances | exact partition/hash equality in one build; 100% finite; peak <= `2^27-1`; exact silence; no nominal drops/recoveries; exact loop decisions |
| Retention | `research/prototypes/pamplist/contract/evidence/`; refuse implicit overwrite |

### Measurements

Frames, peak, RMS, DC, saturated samples, triggers/coalescing, lane steps,
source non-finite, recoveries, invalid MIDI, accepted controls, matrix clamps,
partition equality, loop equality, and source/build/executable hashes.

### Listening protocol

Not run. A later audition should compare authored/phaseless results and judge
route legibility, model-change clicks, main/aux value, and controller scale.

### Stop or pivot conditions

- Stop before DSP edits if readiness fails.
- Stop if exact source cannot be authenticated without mutating its dirty parent checkout.
- Do not silently reduce the 24 engines if desktop build/process fails.
- Stop target-build claims if JUCE authentication or compile/link fails.
- Preserve failed objective conditions; revise contracts rather than weaken tolerances.

## 12. Acceptance and evidence matrix

| Claim | Check | Level | Result | Artifact |
|---|---|---|---|---|
| Proposal ready | structure/readiness validators | proposal | Pending | bundle |
| Exact source consumed | Git commit/tree/clean-subtree hashes | source | Pending | dependency/trace |
| Core/mapping bounded | Release + ASan/UBSan | host-structural | Pending | test receipts |
| Process deterministic/nontrivial | render matrix, loop/partition equality, divergent comparator | host-signal | Pending | retained evidence |
| Standalone builds | authenticated JUCE build | target-build | Pending | receipt/hash |
| Callback deadline | live device timing | real-time | Not run | none |
| Physical controller | endpoint observation | connected-device | Not run | none |
| Musical usefulness | audition | listening | Not run | none |
| Production machine | canonical/provider/release work | production | Not run | none |

## 13. Implementation plan

### Implementation-ready bundle

- Path: `research/prototypes/pamplist/contract/`
- Fingerprint/approval: freeze after this text; approval is the user's
  2026-08-24 uninterrupted implementation request.
- Ready validation: not yet run.

### Files expected to change

- `research/proposals/pamplist.md`
- `research/prototypes/pamplist/**`
- Exact Instrument Lab/current/native/reproduction registration only if required.
- Audition library and exact adjacent fixtures only after target-build succeeds.

No canonical schema, catalog, graph, provider, source release, runtime, device,
backend, project, or governance bytes are expected to change.

### Focused tests

Source authority, rate/phase/remainder, shape, Euclidean, addressed random,
loop, matrix, clamp, silence, reset, 24-engine sweep, snapshot, mapping, invalid
MIDI, allocation, partition, and prototype freshness.

### Adjacent regression tests

Instrument Lab repository validation/current profile; audition-library
operations/tests if added; exact Macro Voice audit bytes unchanged.

### Expensive or hardware checks

One Release/ASan pass, render matrix, JUCE build, and relocated configured-source
reproduction after freeze. No launch, device, listening, Ksoloti, fetch, or release.

### Deferred work

External clock, cross-lane ops, Flex, variable Euclidean length, presets,
polyphony, effects, launch/device/listening, embedded target, canonical
integration, and distribution.

### Dependency contract

| Dependency | Authority | Allowed surface | Download | Boundary |
|---|---|---|---|---|
| Macro Voice/Plaits | `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`; tree `58917f3e2e46a30337cfb6292a3504845b1d5552`; wrapper `d975dd...e4a6`; upstream Plaits `08460a...08d4`; stmlib `e3bd7c...35ec` | exact wrapper/vendor subtree via local adapter | no fetch; exact clean checkout | attribution retained; distribution review deferred |
| Instrument Lab | repository shared target | host mechanics/render/JUCE helper | repository | noncanonical |
| JUCE 8.0.15 | commit `91ad83...e53`, authenticated tree | required standalone modules | local, fetch off | private development |
| Regular LC3 topology | SHA-256 `d69475...510b` | CC/channel facts | repository | synthetic only |

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Type | Gap |
|---|---|---|---|---|---|
| PP-001 | EVIDENCE | Pam exposes eight BPM-related outputs | ALM page/manual | first-party | behavior only |
| PP-002 | EVIDENCE | Ratios, shapes, Euclidean masks, probability, loops, cross ops, Flex are documented | ALM manual | first-party | exact algorithms mostly undocumented |
| PP-003 | EVIDENCE | Plaits exposes model, pitch/tone, trigger/dynamics, level, main/aux | Plaits manual | first-party | wrapper separately authenticated |
| PP-004 | EVIDENCE | STM32F code is MIT and upstream advises distinct derivative names | Mutable repository README | upstream | private codename; no release decision |
| PP-005 | EVIDENCE | Schuss Macro Voice is catalogued-only with no eligibility and retained build failure | Task 033 audit | accepted local | prototype does not promote |
| PP-006 | EVIDENCE | Source metadata reports 24 portable engines finite and Ksoloti overflow | locked manifest | pinned source metadata | reproduce host/source; not Schuss build proof |
| PP-007 | EVIDENCE | Marbles controls replay versus fresh randomness | official manual | first-party | different mechanism |
| PP-008 | EVIDENCE | Euclidean strings evenly distribute hits up to rotation | Toussaint 2005 | primary paper | fixed 16/own rotation |
| PP-009 | EVIDENCE | Counter PRNGs map key/counter without sequential dependence | Salmon et al./Random123 | primary | idea only, no statistical equivalence |
| PP-010 | EVIDENCE | Reich described live performance against a loop and gradual phase shifting | official composer note | practitioner | no material reused |
| PP-011 | INFERENCE | Selected lane plus eight destinations can make the system learnable | comparison/topology | design | needs device/listening |
| PP-012 | HYPOTHESIS | Addressed decisions/rational carry are block/order invariant | equations | testable | partition/order tests |
| PP-013 | HYPOTHESIS | Phased matrix differs from phaseless trigger comparator | experiment | testable | objective difference is not quality |
| PP-014 | UNRESOLVED | Callback headroom and model-click acceptability | none | gap | live/listening required |

## 15. Open questions and decision gate

### Open questions

- Whether model modulation clicks need a later boundary/crossfade design.
- Whether fixed 16-step masks suffice in practice.
- Whether route/lane scales feel legible on physical hardware.
- Whether main-left/aux-right should later become a stereo mix.
- Whether a reduced bank or H7 port merits an embedded task.

### Recommendation and approval recorded

Proceed with revision 0.2 as the noncanonical desktop slice. Use `new-design`
because the complete instrument/clock engine are independently specified; the
exact Plaits-derived source is a bounded dependency, not whole-instrument
source equivalence.

The user's 2026-08-24 request authorizes portable Core, exact source dependency,
seven frozen conditions, synthetic LC3 mapping, authenticated but unlaunched
`Pamplist.app`, additive noncanonical library entry, and evidence through
target-build. It excludes canonical promotion, app/device access, listening,
installation, source mutation, staging, commit, push, upload, and publication.

## 16. Implementation record

### Proposal revision implemented

Pending readiness validation.

### Source and test artifacts

Pending.

### Commands and results

Pending.

### Deviations

Pending.

### Remaining proof gaps

Real-time, launch, physical controller, listening, embedded target,
distribution, and canonical production integration remain open.
