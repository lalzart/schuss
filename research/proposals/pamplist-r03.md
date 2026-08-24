# Pamplist 0.3: Independent Lane Voices

> Status: proposed
> Proposal revision: 0.3
> Work type: `new-design`
> Original idea: Correct Pamplist 0.2 so each of its eight lanes owns an independent persistent Plaits voice, base engine, synthesis controls, modulation, and random state; expose source-order engine names in the selected-lane UI.
> Implementation target: Schuss Instrument Lab v1 portable C++17 Core, deterministic 48 kHz renderer, regular Launch Control 3 adapter, and authenticated JUCE 8.0.15 macOS standalone
> Working artifact and evidence level: a built but unlaunched `Pamplist.app`, deterministic stereo renders, and accepted-state/control traces at `target-build`
> Decision gate: the user's 2026-08-24 request to fix the committed first iteration authorizes uninterrupted proposal-to-prototype work through the stated target-build ceiling. It does not authorize application launch, endpoint access, listening claims, canonical promotion, staging, commit, or push.

## 1. Product thesis

### One-sentence thesis

Pamplist 0.3 is an eight-track clocked macro-voice instrument in which every
lane owns its timing, engine, synthesis state, modulation, and random state, so
changing one track cannot silently redesign the other seven.

### Instrument identity

The performer selects one of eight lanes and edits a complete voice: rate,
phase, shape, Euclidean pattern, probability, repeat, amplitude, base engine,
pitch, tone, decay, level, and eight local modulation amounts. Each lane drives
one persistent Plaits-derived source voice. The eight independent main signals
mix to the left output and the eight independent auxiliary signals mix to the
right output.

The revision preserves Pamplist's clock-lane workflow while correcting the
0.2 mental model. In 0.2, eight independent lane generators converged on one
shared macro voice; therefore `ENGINE` and routed `MODEL` necessarily changed
the same shared source. In 0.3 the lane selector is also a voice selector.

### Intended user and musical situation

Private desktop improvisation on the current Apple-silicon Mac, with mouse
control and the regular Launch Control 3 for lane timing/routing. This first
correction is meant to make layered percussion, contrasting engines, and
independent evolving parts possible before broader interaction redesign.

### In scope

- Exactly eight persistent source voices, one owned by each existing lane.
- Per-lane base Engine, Note, Harmonics, Timbre, Morph, Decay, and Level.
- Per-lane local routing to Trigger, Pitch, Model Mod, Harmonics, Timbre,
  Morph, Decay, and Level; no pre-voice cross-lane summation.
- Stable per-lane source state, including isolation of the exact source's
  process-global stochastic state.
- A selected-lane JUCE edit surface with source-order base and resolved engine names.
- One fixed, non-normalizing final main/aux mixer with explicit saturation.
- Deterministic renderer, synthetic controller tests, authenticated standalone
  build, retained successor evidence, and relocated reproduction.
- Preservation of the committed Pamplist 0.2 proposal, contract, and evidence.

### Out of scope

- New clock algorithms, cross-lane modulation, sends, voice stealing,
  polyphony within a lane, effects, panning, solo/mute, presets, or automation.
- New physical mappings for the per-lane base voice controls; in 0.3 those are
  edited in the JUCE UI while the existing CC20-47 contract remains unchanged.
- Exact Pamela's behavior, Plaits hardware-panel emulation, or an official
  Mutable Instruments engine-name claim. Labels are descriptive names tied to
  the authenticated source registration order.
- Crossfades for model changes or automatic gain normalization.
- App launch, real-time callback proof, connected controller proof, structured
  listening, Ksoloti/Gills execution, packaging, distribution, or publication.
- Canonical Schuss component, graph, instrument, provider, source-release,
  runtime-factory, record-set, project, or machine identity.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/STATUS.md`, ADRs 0016 and 0018,
  and `docs/workflows/instrument-development.md`.
- Committed Pamplist 0.2 at `79bca419fccd072d017e12c8f2e6cdb31704e902`.
- The user's direct listening report that lane voice/model changes feel
  globally coupled, plus the explicit request to build a second iteration.
- Exact configured source authority: `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`,
  synthesis tree `58917f3e2e46a30337cfb6292a3504845b1d5552`.
- The authenticated source registers 24 engines in a fixed order and uses
  `plaits_stmlib::Random` as process-global state in several engines.
- Instrument Lab v1, authenticated JUCE 8.0.15, and the regular Launch Control
  3 topology already used by 0.2.
- Fixed 48 kHz processing; host blocks 1-512 partition persistent 16-frame quanta.

The listening report is design input, not retained structured listening
evidence. No real-time, endpoint, or device state is inferred from it.

### Deliverables

- This successor proposal and a ready implementation bundle at
  `research/prototypes/pamplist/contract-r03/`.
- Revised portable Core, source adapter, snapshots, renderer, tests, JUCE UI,
  topology/index authorities, results, gaps, and handoff within the existing
  noncanonical Pamplist prototype.
- Retained objective evidence under `contract-r03/evidence/` and a separate
  authenticated JUCE build receipt.
- No mutation of `research/prototypes/pamplist/contract/` or its evidence.

### Acceptance tests

1. The 0.3 proposal/bundle passes ready validation before DSP edits.
2. The exact configured source commit/tree/hashes authenticate without source checkout mutation.
3. Changing any base voice control for lane A leaves all accepted base voice
   controls for lanes B-H byte-identical.
4. At least two lanes simultaneously resolve to different named engines, and
   Model Mod on lane A changes only lane A's resolved engine.
5. Interleaving stochastic rendering by another lane does not change a
   reference lane's PCM or persistent random state.
6. Engine changes or resets in one lane do not reset another lane's source
   state, phase, trigger history, or accepted controls.
7. All 24 source-order engine indices have deterministic nonempty labels and
   render finite main and auxiliary output in the bounded sweep.
8. Eight active, differently configured lanes render finite mixed output;
   nominal frozen conditions have no final saturation.
9. Supported host partitions produce byte-identical PCM, event traces, and
   final accepted snapshots for every frozen experiment.
10. Stop and specified zero conditions remain exact silence; all output is
    finite and bounded to Q27 `[-1, 1)`.
11. Synthetic Launch Control 3 mapping remains exhaustive and selected-lane
    routing edits cannot alter another lane.
12. Repeated processing allocates nothing and performs no lock, I/O, JSON, or UI work.
13. Authenticated JUCE 8.0.15 configures, compiles, and links without launch.
14. Focused, adjacent, current, affected native, and relocated reproduction
    checks pass at their declared evidence levels.

### Decisions this work may make

- Prototype-local state layout, per-lane seed derivation and RNG context
  switching, mixer law, engine labels, selected-lane UI projection, diagnostics,
  frozen test conditions, and successor evidence paths.
- The smallest adapter change required to make the already authenticated
  source dependency behave as eight isolated prototype-owned instances.

### Decisions this work must not make

- A change to upstream source bytes, algorithms, engine order, licensing,
  catalog preference, component contract, provider eligibility, or production status.
- A new Launch Control model/topology or a claim that the regular model has faders.
- Real-time, connected-device, audible-quality, distribution, or production claims.
- App/device access, installation, source-checkout mutation, staging, commit,
  push, upload, flash, or publication.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Built `Pamplist.app`, deterministic mixed stereo renders, per-lane event/state traces, and synthetic control trace | target-build | Eight-voice Core/source/control/render suites and authenticated standalone compile/link pass; executable hash retained | launch, callback deadline, physical controller receipt, listening quality, Ksoloti, distribution, or production |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Pamplist 0.2 lane | Timing, mask, probability, shape, amplitude, and routes are independently stored | **EVIDENCE:** committed `Controls::lanes[8]` and tests | Keep | High |
| Pamplist 0.2 voice | All routes sum before one `MacroVoice`; Engine is global and Model offsets it | **EVIDENCE:** committed `Core::Impl` and `Controls` | Replace with one source voice and base controls per lane | High |
| Pamplist 0.2 UI | Lane selection changes routing/timing edit focus, not Engine/voice focus | **EVIDENCE:** committed JUCE callbacks | Transform lane selection into complete track focus | High |
| Plaits engine selection | Source selects one of 24 registered engine objects per `Voice` | **EVIDENCE:** authenticated local `voice.cc` | Keep exact order; name descriptively | High |
| Plaits stochastic state | Several registered engines consume one static `plaits_stmlib::Random` state | **EVIDENCE:** authenticated local stmlib/source calls | Context-switch a stored RNG state around each voice render | High |
| Shared output | Main and auxiliary are separate source channels | **EVIDENCE:** exact wrapper/source contract | Sum all mains to left and all auxiliaries to right | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| Pamplist 0.2 | Local predecessor | Eight modulation lanes into one macro voice | Lane timing independent; source identity shared | committed proposal/source/evidence | Preserve timing, replace convergence point |
| Mutable Instruments Plaits | Macro oscillator | One persistent multi-engine voice with main/aux | A single voice, not a multitrack mixer | authenticated dependency/manual | Instantiate and isolate one exact voice per lane |
| Schuss Generative Drums 0.6 | Local prototype | Multiple persistent Mutable-derived voices and fixed mixer | Authored drum lanes rather than general 24-engine tracks | local proposal/source | Reuse bounded ownership/mixing lessons, not musical architecture |
| Pamela's PRO Workout | Hardware modulation source | Eight independently edited clock outputs | No fused eight-voice sound engine | official reference already recorded by 0.2 | Retain lane workflow without emulating firmware/UI |

This correction does not make a novelty claim. Its research scope is bounded
to the committed predecessor, authenticated source behavior, and existing
Schuss multi-voice practice. Research stops when the coupling mechanism,
source-order names, RNG boundary, and falsifying test are specified.

## 5. Synthesis and engineering research

| Technical source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Authenticated Plaits-derived `dsp/voice.cc` | Fixed registration order of 24 engine instances | Exact local source | Normative numeric-to-name mapping | Descriptive UI labels are Pamplist-owned |
| Authenticated `stmlib/utils/random.h/.cc` and engine call sites | Static process-global RNG state | Exact local source | Proves an otherwise hidden inter-instance coupling | Context switching assumes single-threaded Core render order |
| Pamplist 0.2 Core/tests | Persistent 16-frame quantum, rational lane timing, snapshots, renderer | Committed local implementation | Mechanics preserved where semantics remain valid | Shared voice/matrix semantics are superseded |
| Instrument Lab v1 / ADR 0016 | Portable Core and bounded host seam | Accepted local architecture | Keeps DSP independent of JUCE | No real-time/device proof |

The source-order label table is frozen as follows. These are concise Pamplist
descriptions of the exact registered source classes, not a claim of official
panel wording.

| Index | Pamplist label | Exact registered source class/slot |
|---:|---|---|
| 0 | Virtual Analog VCF | `VirtualAnalogVcfEngine` |
| 1 | Phase Distortion | `PhaseDistortionEngine` |
| 2 | 6-Op FM A | `SixOpEngine` slot A |
| 3 | 6-Op FM B | `SixOpEngine` slot B |
| 4 | 6-Op FM C | `SixOpEngine` slot C |
| 5 | Wave Terrain | `WaveTerrainEngine` |
| 6 | String Machine | `StringMachineEngine` |
| 7 | Chiptune | `ChiptuneEngine` |
| 8 | Virtual Analog | `VirtualAnalogEngine` |
| 9 | Waveshaping | `WaveshapingEngine` |
| 10 | 2-Op FM | `FmEngine` |
| 11 | Granular Formant | `GrainEngine` |
| 12 | Harmonic / Additive | `AdditiveEngine` |
| 13 | Wavetable | `WavetableEngine` |
| 14 | Chord | `ChordEngine` |
| 15 | Speech | `SpeechEngine` |
| 16 | Swarm | `SwarmEngine` |
| 17 | Noise | `NoiseEngine` |
| 18 | Particle | `ParticleEngine` |
| 19 | String | `StringEngine` |
| 20 | Modal Resonator | `ModalEngine` |
| 21 | Bass Drum | `BassDrumEngine` |
| 22 | Snare Drum | `SnareDrumEngine` |
| 23 | Hi-Hat | `HiHatEngine` |

## 6. Musical-practice research

No new cultural or musical-practice material is introduced by this corrective
revision. The 0.2 phase-process attribution remains in its frozen proposal,
but 0.3 neither expands it nor uses culturally identified rhythmic material.
The design change is state ownership, not cultural translation; no authenticity
or lineage claim is made.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Context switching / virtualized global state | The exact dependency uses a static RNG; no per-instance interface is exposed | Before each voice operation load its stored RNG state; afterward save the dependency's resulting state | A noisy or stochastic lane cannot advance another lane's random sequence | Missed call site or wrong save point preserves coupling | Compare a reference stochastic voice with the same voice while arbitrary stochastic renders are interleaved; PCM/state must be exact |
| Encapsulated aggregate state | 0.2 already snapshots lanes but stores voice bases globally | Store `VoiceControls[8]` beside `LaneControls[8]`; snapshot both coherently | Lane selection behaves as track selection and edits are locally attributable | UI writes stale selected index or Core reads torn arrays | Exhaust every lane/control and compare all seven non-target records byte-for-byte |

## 8. Novelty map

### Common elements

Multitimbral voices, per-track synthesis controls, source-order model labels,
clock lanes, modulation routing, and final saturating mixers are established.

### Less-common combinations found

Pamplist's particular combination remains an eight-lane programmable clock
surface fused with the exact 24-engine dependency. Revision 0.3 changes the
ownership boundary rather than asserting a new synthesis technique.

### Proposed contribution

**INFERENCE:** making a lane a complete track should align the software with
the user's demonstrated editing model. **HYPOTHESIS:** per-lane source and RNG
state will make simultaneous contrasting engines behave independently and
make base versus modulated model identity legible.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Keep one voice and merely change labels | Would conceal, not fix, the reported coupling | 0.2 source topology |
| Eight voice objects without RNG isolation | Stochastic engines would retain render-order coupling | exact static RNG source |
| Dynamic mix normalization | Activating one lane would change every other lane's amplitude | violates local-edit expectation |
| Cross-lane matrix in this correction | Reintroduces deliberate coupling before local ownership is proven | scope and diagnostic ambiguity |
| Controller remap | Requires a separate performance-design decision | current request is voice independence |

## 9. Recommended architecture

### Signal flow

```text
shared tempo + running + master gain + seed
  -> lane 1 timing/mask/random/shape -> lane 1 local routes -> voice 1 base controls -> Plaits voice 1 --\
  -> lane 2 timing/mask/random/shape -> lane 2 local routes -> voice 2 base controls -> Plaits voice 2 ----+-> fixed main/aux sums -> master -> Q27 clamp
  ...                                                                                                    |
  -> lane 8 timing/mask/random/shape -> lane 8 local routes -> voice 8 base controls -> Plaits voice 8 --/
```

There is no lane-to-lane signal path before the final mixer. Selection is an
editing/UI concern only and never changes DSP ownership.

### Executable DSP contract

| Mechanism | Equation or pseudocode | Coefficients/ranges | Gain and stability bound | Update timing | Failure behavior |
|---|---|---|---|---|---|
| Accepted controls | sanitize one `Controls { globals, lanes[8], voices[8] }` | selected 0-7; all existing lane bounds; engine 0-23, note 24-96, unit voice fields | finite, fixed capacity | start of persistent 16-frame quantum | invalid field clamps/defaults and counts recovery |
| Local route | `m[l][d]=clamp(shape[l]*route[l][d],-1,1)` | shape `[0,1]`; route `[-1,1]`; 8 destinations | no sum across lanes | once per source quantum | non-finite -> zero |
| Local trigger | `trig[l]=new_accepted_step[l] && route[l][Trigger]>1/127` | Boolean; at most one per voice/quantum | cannot trigger another voice | before that voice renders | invalid route -> no trigger |
| Local engine | `resolved_engine[l]=clamp(base_engine[l]+round(23*m[l][Model]),0,23)` | base/result 0-23 | bounded lookup | each quantum | clamp + diagnostic |
| Local pitch | `resolved_note[l]=clamp(base_note[l]+24*m[l][Pitch],24,96)` | base/result 24-96 | bounded Q21 conversion | each quantum | non-finite -> base |
| Local unit controls | `resolved=clamp(base+m[l][destination],0,1)` | Harmonics, Timbre, Morph, Decay, Level | exact unit clamp | each quantum | non-finite -> base |
| Per-voice RNG | `Random::Seed(saved[l]); voice[l].Process(...); saved[l]=Random::state()` | deterministic nonzero 32-bit state derived from global seed and lane domain | only one Core thread enters dependency at a time | around construction/reset and every render | invalid zero seed replaced by fixed lane-derived state |
| Voice lifetime | construct eight `MacroVoice`; once locally triggered, render each started voice every quantum until Stop/Reset | exactly eight persistent source states | no allocation in process | construction/reset outside render; processing in lane order | source auth/build mismatch fails closed |
| Mixer | `sum_main=sum_l voice_main[l]*level[l]`; same aux; `out=sat_q27(master*sum)` | per-voice resolved level `[0,1]`; master `[0,1]` | 64-bit accumulation; one final Q27 clamp; no dynamic normalization | per sample after all voices render | saturation counted; non-finite source sample -> zero/count |
| Engine display | `engine_name[index]` from frozen 24-entry table; show selected base and current resolved index/name | total function for 0-23 | presentation only | accepted snapshot publication | invalid index displays `Unknown` and cannot enter DSP |

Existing exact rational rates, Q32 phase carry, Euclidean mask, keyed lane
probability, shape equations, host partition carry, and source Q27 conversion
remain as specified by the frozen 0.2 proposal unless this table supersedes
them. The shared 0.2 8-by-8 summing matrix is removed: the same 64 controls
now form eight independent 1-by-8 local route rows.

Final mixing is deliberately not divided by the number of active voices.
Therefore enabling lane B does not alter lane A's contribution. Nominal test
patches must remain below saturation; extreme user combinations saturate only
at the final declared Q27 boundary and increment a diagnostic.

### State and timing model

- Core owns eight lane schedulers, eight voice-control records, eight source
  voices, eight started flags, eight saved source RNG states, one final mixer,
  diagnostics, and one coherent accepted snapshot.
- Host blocks copy from persistent 16-frame output quanta and never realign state.
- Control changes are accepted only at a quantum boundary. UI and controller
  presentation read the resulting snapshot, never raw input.
- Stop silences immediately at the next quantum and reconstructs all lane,
  voice, started, and per-voice RNG state for a phase-zero future Start.
- Reset while stopped restores defaults and clears diagnostics. Reset/start do
  not depend on selected lane.
- A global seed change deterministically reinitializes all eight source RNG
  states using disjoint lane-domain derivations while preserving accepted base
  controls; the bundle matrix freezes the exact transition.
- Changing lane A's engine may alter lane A's internal engine history only.
  It cannot reconstruct or advance lanes B-H.
- Non-finite controls use explicit defaults; non-finite source samples become zero and count.

State equivalence is byte equality of PCM and canonical event/control/snapshot
traces across supported partitions; exact integer equality of frame, phases,
remainders, lane steps/addresses, eight base/resolved voice records, eight
started flags, per-voice RNG states, counts, and accepted controls. Padding,
pointers, paths, wall time, GUI state, endpoints, and unobservable unused
engine internals are excluded.

### Control and performance mapping

Regular Launch Control 3 Custom Mode 1, MIDI channel 16:

| Control or gesture | Range or states | DSP mapping | Perceptual role | Safety or pickup behavior |
|---|---|---|---|---|
| Buttons CC40-47 | press/release | rising press selects complete lane/voice 1-8; release accepted/no dispatch | choose track | accepted snapshot owns selection |
| Top CC20-27 | 0-127, center 64 | selected lane's local Trigger, Pitch, Model Mod, Harmonics, Timbre, Morph, Decay, Level routes | animate only that voice | center exact zero |
| Bottom CC28-35 | existing bounded mappings | selected lane's Rate, Phase, Shape, Hits, Rotation, Probability, Repeat, Amplitude | sequence only that voice | existing exact endpoints |
| JUCE `BASE ENGINE` | 0-23 | selected lane base engine | choose persistent source identity | discrete accepted value; named display |
| JUCE voice controls | existing bounded ranges | selected lane Note, Harmonics, Timbre, Morph, Decay, Level | tune/shape only selected voice | reload from accepted snapshot on selection |
| JUCE BPM/MASTER/Run/Reset | global | shared clock, final gain, transport | whole instrument | explicit global labels |

No physical control is invented for base engine or other base voice fields in
0.3. Endpoint identity, receipt, LED feedback, reconnect, and live pickup are
not exercised.

### Parameter interactions and edge cases

- `BASE ENGINE` is stored per lane. `MODEL MOD` is a signed local offset from
  that base; the display reports both, so the two roles cannot masquerade as
  duplicate global selectors.
- A lane remains unstarted until its own accepted trigger. After starting, its
  source tail/continuous behavior renders even between triggers.
- Hits/probability/amplitude zero suppress lane modulation/trigger according to
  the inherited contract; Stop is the guaranteed whole-instrument silence.
- Simultaneous lane triggers remain separate and are never coalesced across voices.
- Engine changes occur at quantum boundaries and do not crossfade.
- Left is the sum of source mains; right is the sum of auxiliaries.

### Failure behavior

Mismatched source, JUCE, proposal, bundle, topology, or derived hash fails
before evidence promotion. Unsupported sample rate/frame count clears output
and does not advance. Invalid MIDI is ignored/counted. No fallback source,
alternate engine order, network fetch, dynamic voice reduction, controller,
or implicit target exists.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Sample rate | 48 kHz | inherited wrapper/Instrument Lab | no resampling | Ready to test |
| Quantum | 16 frames | source wrapper | persistent carry | Ready to test |
| Host blocks | 1,16,64,128,257,512 | existing bounded lab path | max 512 | Ready to test |
| Voice state | eight instances; source manifest reports 27,448 bytes per instance | exact source metadata | about 220 KiB plus fixed buffers | Desktop feasible; measure/build |
| CPU | eight source renders per active quantum | architectural count | no desktop deadline claim | Offline/JUCE build only |
| Numeric/mixer | Q27 source/output, signed 64-bit accumulator | executable contract | explicit final saturation | Ready to test |
| RNG | eight saved 32-bit contexts around one static dependency state | exact source + adapter | single-threaded Core ownership | Ready to test |
| Source | exact configured commit/tree above | accepted lock/review | clean read-only subtree | Present; reverify |
| JUCE | 8.0.15 local authenticated tree | existing manifest authority | fetch disabled | Reauthenticate |
| Ksoloti | eight full voices exceed the already oversized single-voice fit | inference from retained 0.2 source size | not a target | Deferred |
| Use policy | private, no redistribution | user instruction | provenance retained | Accepted |

## 11. Minimal experiment

### Central hypothesis

**HYPOTHESIS:** with identical shared clock/global gain, independently owned
base controls, routing, source instances, and random contexts allow one lane's
engine and state to change without any observable change to another lane prior
to the final additive mix.

### Smallest vertical slice

- `PAMP_R03_BASE`: one lane, inherited baseline behavior.
- `PAMP_R03_DUAL`: two simultaneous lanes with different base engines,
  pitches, timing, and main/aux behavior.
- `PAMP_R03_EIGHT`: all eight lanes active with distinct engine/control sets.
- `PAMP_R03_MODEL_LOCAL`: two active lanes; only lane 1 has Model Mod and only
  its resolved engine trace may move.
- `PAMP_R03_RNG_ISOLATION`: stochastic reference voice compared byte-for-byte
  with the same voice while another stochastic voice is interleaved.
- `PAMP_R03_24`: bounded sweep through all 24 indexed/named engines.
- `PAMP_R03_SILENCE`: stopped and declared zero subcases.
- `PAMP_R03_SHARED_VOICE_CMP`: falsifier that collapses the dual condition to
  the predecessor's one shared engine/voice interpretation; trace and PCM must
  differ from `PAMP_R03_DUAL`.

### Test signals and gestures

| Field | Bound value |
|---|---|
| Sample rate and supported block sizes | 48,000; 1,16,64,128,257,512 |
| Deterministic seed | `0x50414D50` (`PAMP`) with fixed lane-domain derivation |
| Event/sample timeline convention | controls accepted at next persistent quantum; each local trigger precedes only its voice render; host partitions never realign |
| Literal condition IDs and count | eight IDs above; silence contains explicit subcases |
| Falsifying comparator condition | `PAMP_R03_SHARED_VOICE_CMP` against `PAMP_R03_DUAL` |
| Output names and kinds | `audio.wav`, `events.json`, `snapshots.json`, `metrics.json`, `manifest.json`, `controller-trace.json`, `SHA256SUMS` |
| Objective tolerances | exact partition/hash equality; 100% finite; peak <= `2^27-1`; exact declared silence; no nominal saturation/recovery; exact non-target lane state; exact RNG-interleave equality |
| Artifact retention policy and location | `research/prototypes/pamplist/contract-r03/evidence/`; refuse implicit overwrite; preserve 0.2 evidence |

### Measurements

Frames, per-lane triggers, per-lane base/resolved engine index/name, other
resolved controls, started mask, phase/address, peak, RMS, DC, final saturated
samples, source non-finite samples, recoveries, invalid MIDI, partition hashes,
RNG isolation equality, non-target state equality, and authenticated hashes.

### Listening protocol

Not run. The user's informal 0.2 audition motivated the change but is not
retained as a controlled result. A later audition can judge separation,
balance, clicks, naming clarity, and whether eight voices are musically useful.

### Stop or pivot conditions

- Stop before DSP edits if ready validation fails.
- Stop if exact source authentication requires source-checkout mutation.
- Do not claim independence if stochastic interleave or non-target state tests fail.
- Do not silently normalize, reduce voice count, remap controller hardware, or
  weaken exact partition/state tolerances to obtain a pass.
- Stop target-build claims if JUCE authentication or compile/link fails.
- Preserve failed conditions and revise the contract rather than relabel evidence.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Successor contract ready | structure/readiness validators | proposal | Pending | `contract-r03/` |
| Exact source/order/RNG boundary consumed | Git/tree/file hashes plus source-bound tests | source | Pending | dependency receipt/tests |
| Eight states isolated and bounded | focused Release + ASan/UBSan tests | host-structural | Pending | test receipts |
| Eight-voice process deterministic/nontrivial | render matrix, partition equality, local-model/RNG tests, divergent comparator | host-signal | Pending | retained evidence |
| Standalone compiles/links | authenticated JUCE build | target-build | Pending | receipt/hash |
| Callback deadline | live device timing | real-time | Not run | none |
| Physical controller | endpoint observation | connected-device | Not run | none |
| Musical usefulness | controlled audition | listening | Not run | none |
| Canonical production integration | governance/provider/release work | production | Not run | none |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/pamplist/contract-r03/`
- Proposal fingerprint and approval reference: freeze after this proposal;
  approval is the user's 2026-08-24 request to implement the second iteration
  on top of committed Pamplist 0.2.
- `validate_implementation_bundle.py --phase ready`: not yet run.

### Files expected to change

- `research/proposals/pamplist-r03.md`
- Existing Pamplist Core/adapter/UI/renderer/tests and prototype-local derived authorities.
- New `research/prototypes/pamplist/contract-r03/**` successor contract/evidence.
- Exact current/native/reproduction registration only if freshness checks require it.

The frozen 0.2 proposal, contract, evidence, source dependency bytes, upstream
checkout, canonical schema/catalog/graph/provider/runtime/device/backend,
shared audition-library record set, and unrelated work must not change.

### Focused tests

Per-lane accepted control isolation; base/resolved engine naming; local model
route; eight source ownership; RNG interleave; engine-change/reset isolation;
all 24 engines; lane timing/routes; exact silence; final mix saturation;
partition equality; snapshot/UI projection; MIDI selection/mapping; invalid
input; callback allocation.

### Adjacent regression tests

Unchanged lane timing/rate/shape/Euclidean/keyed-random behavior, exact source
authentication, prototype index/hash freshness, Instrument Lab validation, and
the repository `current` profile.

### Expensive or hardware checks

One stable Release/ASan pass, render evidence matrix, authenticated JUCE build,
and relocated configured-source reproduction after implementation freeze. No
launch, live callback, physical device, listening, Ksoloti, network fetch, or release.

### Deferred work

Cross-lane operations, voice sends, mute/solo/pan, dynamic mix policy,
controller mapping for base voice parameters, engine crossfades, presets,
external clock, effects, live/device/listening evidence, embedded target,
canonical integration, and distribution.

### Dependency contract

| Dependency | Authority | Allowed modules | Local authentication/download | License/distribution boundary |
|---|---|---|---|---|
| Macro Voice / Plaits-derived source | `patcher@08d3e6e1e2b61230308c20a15ded58ffdaf4656c`; synthesis tree `58917f3e2e46a30337cfb6292a3504845b1d5552`; existing locked file hashes | existing exact wrapper/vendor subtree plus adapter calls to `Random::Seed/state` | configured local checkout only; clean-tree/hash verification; no fetch | existing notices retained; private build; distribution review deferred |
| Instrument Lab | repository shared target | Core/JUCE/render/build mechanics | repository-local | noncanonical prototype |
| JUCE 8.0.15 | existing authenticated commit/tree | standalone modules already declared | local path, fetch disabled | private development |
| Regular Launch Control 3 topology | existing frozen topology hash | MIDI channel/CC facts | repository-local | synthetic only |

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Source type | Notes or proof gap |
|---|---|---|---|---|---|
| P03-001 | EVIDENCE | Pamplist 0.2 stores one global voice-control set and one `MacroVoice` | committed 0.2 Core/headers | exact local source | explains reported global behavior |
| P03-002 | EVIDENCE | 0.2 lanes independently store only timing/routing data | committed 0.2 headers/tests | exact local source | independence stops before voice |
| P03-003 | EVIDENCE | The authenticated dependency registers the frozen 24-engine order | exact `voice.cc` | configured source | labels are local descriptions |
| P03-004 | EVIDENCE | Multiple dependency engines consume static `plaits_stmlib::Random` state | exact random/source files | configured source | requires adapter isolation |
| P03-005 | EVIDENCE | Main and auxiliary are distinct exact source outputs | wrapper/source contract | configured/local source | final mixer retains separation |
| P03-006 | INFERENCE | Lane selection should select a complete editable track | user report plus 0.2 topology | design interpretation | requires user retest |
| P03-007 | HYPOTHESIS | RNG context switching makes stochastic voice output independent of interleaved lanes | executable design | testable | exact interleave test required |
| P03-008 | HYPOTHESIS | Eight independent voices remain deterministic and nominally unsaturated offline | experiment | testable | no real-time CPU claim |
| P03-009 | HYPOTHESIS | Base/resolved engine names make Engine versus Model Mod legible | UI design | testable | listening/usability remains open |
| P03-010 | UNRESOLVED | Eight-voice balance, model-change clicks, CPU deadline, and controller feel | none | gap | controlled listening/live/device work required |

## 15. Open questions and decision gate

### Open questions

- Whether the fixed additive mixer needs per-lane mute/solo/pan or a later gain policy.
- Whether engine changes need per-lane crossfades.
- Whether base voice parameters deserve a second physical controller page.
- Whether lanes should later modulate one another intentionally through explicit sends.
- Whether all eight voices should have a manual drone/start gesture.

### Recommendation

Implement revision 0.3 as a noncanonical successor in place, retain all 0.2
authorities, and put the new contract/evidence in `contract-r03/`. Preserve the
clock/lane mechanics and controller layout, but replace the shared voice and
matrix accumulation with eight locally modulated persistent voices and one
final explicit mixer.

### Approval requested and recorded

The user's 2026-08-24 request authorizes this revision 0.3 architecture,
portable Core/source adapter changes, eight frozen voice-isolation conditions,
selected-lane UI/name display, synthetic controller mapping, deterministic
evidence, and authenticated but unlaunched `Pamplist.app` through
`target-build`, subject to a ready `contract-r03` bundle. It does not authorize
canonical promotion, application/device access, real-time or listening claims,
installation, upstream mutation, staging, commit, push, upload, or publication.

## 16. Implementation record

### Proposal revision implemented

Pending ready-bundle validation.

### Source and test artifacts

Pending.

### Commands and results

Pending.

### Deviations

Pending.

### Remaining proof gaps

Real-time deadline, launch, physical controller, controlled listening,
embedded target, distribution, and canonical production integration remain open.
