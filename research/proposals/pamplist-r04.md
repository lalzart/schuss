# Pamplist 0.4: Seven Voices and Cohesion Bus

> Status: proposed
> Proposal revision: 0.4
> Original idea: Replace the eighth Pamplist voice lane with a true Global/Clear performance page on the regular Launch Control 3; remove misleading global-versus-local model duplication; keep seven independent lane voices; add a shared resonant performance effect that can cohere the whole mix and return immediately to clarity.
> Implementation target: Schuss Instrument Lab v1 portable C++17 Core, deterministic 48 kHz renderer, regular Launch Control 3 adapter, and authenticated JUCE 8.0.15 macOS standalone
> Working artifact and evidence level: built but unlaunched `Pamplist.app`, deterministic revision 0.4 stereo renders, and synthetic controller traces at target-build evidence
> Decision gate: the current-thread request explicitly authorizes uninterrupted proposal-to-implementation work, subject to a ready revision 0.4 bundle before DSP edits.

## 1. Product thesis

### One-sentence thesis

Pamplist becomes seven independent clocked macro voices that can be deliberately
played through one clearable resonant body, with the eighth controller page
reserved for true global performance controls rather than a hidden eighth
voice or a misleading global model.

### Instrument identity

The performer builds seven distinct parts, then uses `COHERE` to let their
combined energy excite one shared six-mode stereo body. The voice engines never
become global: `MODEL` always belongs to one selected lane. The common body is
an explicit post-mix gesture that can be withdrawn by turning `COHERE` to zero
or emptied by pressing `GLOBAL / CLEAR` again.

This remains an instrument because clock, voice, and performance state form one
playable system. It is not a generic effect rack: the first slice has one
bounded shared-body hypothesis and one transparent escape gesture.

### Intended user and musical situation

A single performer improvising with the regular Launch Control 3 or JUCE
standalone, moving between autonomous parts and brief global swells without
menu navigation.

### In scope

- Exactly seven persistent lane schedulers and seven independently controlled,
  RNG-isolated 24-engine voices.
- Exactly eight controller pages: lane pages 1 through 7 and one
  `GLOBAL / CLEAR` page.
- Rename the selected voice control to `MODEL` and the lane destination to
  `MODEL SWEEP`; neither is global.
- True global state: Run, BPM, Master, and one shared performance bus.
- Eight global performance parameters: Drive, Cohere, Root, Spread, Tail,
  Damping, Width, and Duck.
- A newly designed fixed six-mode stereo resonator fed only after the seven
  voice sums, with bounded state, smoothing, non-finite recovery, and an exact
  clear operation.
- Contextual regular Launch Control 3 mapping, accepted-state JUCE projection,
  deterministic renderer, focused/sanitizer tests, retained objective evidence,
  authenticated unlaunched target build, and relocated reproduction.

### Out of scope

- An eighth sound-producing lane, a global Plaits model, or pre-voice summation.
- Cross-lane modulation, sends, pan, mute/solo, presets, scenes, crossfades,
  arbitrary effect routing, reverb, granular processing, freeze, or looping.
- New upstream source bytes, changes to Plaits/stmlib/Ksoloti source, or a claim
  that the new resonator is Rings, Elements, Cinderwheel, or an acoustic model.
- Controller feedback/configuration writes, endpoint access, app launch,
  callback timing, structured listening, Ksoloti/Gills execution, distribution,
  canonical Schuss records, or production integration.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- The inherited revision 0.3 worktree and its passing results are preserved as
  the direct predecessor. Its proposal SHA-256 is
  `ecafd12747c5afb1ad89eb4c073876e8c504c215192c0300c53a7358691e42e0`.
- Revision 0.3 established eight genuinely independent voices; this revision
  intentionally removes voice/lane 8 and does not reopen that independence
  design for lanes 1 through 7.
- The configured read-only source remains `patcher` commit
  `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, synthesis tree
  `58917f3e2e46a30337cfb6292a3504845b1d5552`.
- The regular Launch Control 3 authority has 16 endless encoders, eight
  assignable buttons, and no faders; the existing Custom Mode 1 channel-16
  CC20-35/40-47 topology remains physical/protocol authority.
- The user's current message is uninterrupted authorization for the bounded
  design described here, not authority to stage, commit, launch, access
  endpoints, configure hardware, or promote evidence.

### Deliverables

- A ready revision 0.4 implementation bundle under
  `research/prototypes/pamplist/contract-r04/`.
- Portable C++17 Core with seven lane voices and a shared six-mode cohesion bus.
- Contextual page-aware control adapter and JUCE presentation.
- Frozen controller table, state matrix, experiment, objective evidence,
  target-build receipt, results, gaps, prototype index, topology, and handoff.
- Preserved revision 0.2 and revision 0.3 proposals/contracts/evidence.

### Acceptance tests

- Arrays, snapshots, event masks, and source instances contain exactly seven
  voice lanes; button 8 cannot start or edit an eighth voice.
- Each lane page edits only its own lane and voice records.
- Global-page continuous messages edit only true global/effect records; all
  seven lane and voice records remain byte-identical.
- The first `GLOBAL / CLEAR` press selects the page without changing sound or
  clearing state. A later press while already selected increments one clear
  generation and clears only cohesion-bus state at the next quantum.
- `COHERE=0` reaches the inherited dry seven-voice path exactly after its fixed
  smoothing interval. Drive cannot leak into the dry path.
- Nonzero Cohere produces objective output divergence from the dry comparator,
  a measurable tail after voice levels reach zero, and exact zero tail after
  Clear while lane/source/scheduler state continues unchanged.
- Parameter minima, maxima, and rapid changes remain finite; modal poles remain
  below one; nominal conditions have zero final Q27 saturation.
- All 24 source-order engines remain finite/non-silent in the unchanged voice
  adapter, and stochastic interleave isolation remains exact.
- PCM, events, snapshots, and metrics are partition-identical at host blocks
  `1, 16, 64, 128, 257, 512`.
- Release, ASan/UBSan, no-allocation, controller-exhaustion, target-build,
  prototype-freshness, current, and relocated reproduction checks pass.

### Decisions this work may make

- Pamplist-local modal ratios, coefficient ranges, smoothing times, wet gain,
  duck envelope, diagnostics, UI labels/layout, and deterministic fixtures.
- The exact contextual mapping of CC20-35 on the global page, provided no
  hidden lane or replicated model control is introduced.
- Prototype-local state layout and effect-clear generation semantics.

### Decisions this work must not make

- Modify, copy, normalize, or replace authenticated upstream voice source.
- Change revision 0.2 or 0.3 retained contract/evidence bytes.
- Add a generic shared DSP framework or refactor Cinderwheel/other prototypes.
- Allocate canonical IDs or change catalogs, schemas, providers, runtimes,
  device profiles, the audition library, or release records.
- Claim musical cohesion, real-time safety, physical controller behavior, or
  production quality from offline/compile evidence.
- Launch, enumerate/open endpoints, install, stage, commit, push, publish, or
  redistribute.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Built but unlaunched `Pamplist.app`, retained revision 0.4 renders, and synthetic controller traces | target-build | Seven independent voices, contextual Global/Clear mapping, bounded shared-body DSP, deterministic objective conditions, and authenticated compile/link pass | Live callback deadline, endpoint/device behavior, audible cohesion, embedded feasibility, distribution, or production |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Revision 0.3 lane/voice | Eight complete independent lane/voice records | Local Core, tests, and retained results | Keep semantics for lanes 1-7 | High |
| Revision 0.3 top row | BPM/Master are global while Model/Note/Harmonics/Timbre/Morph/Decay/Colour/Level are selected-lane controls in a row named `global_sliders_` | Local JUCE source | Split presentation and rename context | High |
| Revision 0.3 Model route | Signed lane-local offset changes the selected source engine | Local Core and model-local evidence | Keep, rename `MODEL SWEEP` | High |
| Controller selector 8 | CC47 selects lane 8 | Frozen control map and topology | Transform into Global/Clear page | High |
| Shared output | Seven or eight main channels meet only at final L sum; auxiliaries meet at R sum | Local Core | Keep dry mix; add explicit post-mix bus | High |
| Performer request | One gesture should make parts resonate together and another should restore clarity | Current-thread user observation | Central hypothesis | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| Pamplist 0.3 | Local predecessor | Independent clocked macro voices and fixed final mixer | No intentional shared timbral stage; UI context is misleading | local proposal/Core/results | Preserve local ownership, change only post-mix interaction |
| Cinderwheel | Local Instrument Lab prototype | Project-owned damped resonators, smoothing, reset/clear, and bounded diffusion | Resonance generates its own counterpoint/body rather than processing Pamplist tracks | `research/prototypes/cinderwheel/src/core.cpp` and `RESULTS.md` | Reuse stability lessons and objective guards, not code or musical architecture |
| Mutable Instruments Rings | First-party documented instrument | External excitation drives modal modes; structure changes partial ratios; brightness/damping shape higher modes and decay | A dedicated resonator instrument with many more source-specific behaviors | https://pichenettes.github.io/mutable-instruments-documentation/modules/rings/manual/ | Supports excitation-to-common-body interaction; do not copy code or claim equivalence |
| Launch Control 3 | First-party controller | 16 endless encoders, 8 programmable buttons, custom mappings | General control surface, not an instrument page model | https://userguides.novationmusic.com/hc/en-gb/articles/30683940823442-Introduction-to-the-Launch-Control-3 | Seven lane buttons plus one global page fit the actual surface exactly |
| Plug-in/software lane | Bounded search gap | Many resonator and bus-effect products exist | No current plug-in is normative for this correction | not relied on in this search | Make no adjacent-market or novelty claim |

## 5. Synthesis and engineering research

| Paper, patent, standard, or technical source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Mutable Instruments Rings manual | Modal synthesis models modes as resonant band-pass responses; frequency ratios, higher-mode damping, and decay are performer controls | First-party behavior/technical explanation | Supports Root, Spread, Damping, and Tail semantics | Does not authorize copying implementation or establish equivalence |
| Cinderwheel Core and result record | Complex two-state damped resonator; excitation normalized by pole distance; objective render exposed excessive gain/DC before correction | Exact project-owned source and measurements | Direct warning that compile/state tests are insufficient and pole-distance normalization matters | Its voice/body design is not reusable as Pamplist's effect contract |
| Pamplist 0.3 Core | Signed 64-bit voice sums, one final Q27 clamp, fixed 16-frame quantum, exact block invariance | Exact predecessor source/evidence | Normative dry comparator and timing boundary | Does not include float effect state or clear semantics |
| Instrument Lab v1 and ADRs 0016/0018 | Portable Core, JUCE adapter separation, and proportional evidence profiles | Accepted local architecture | Owns host/evidence boundary | Does not prove live callback or listening behavior |

**EVIDENCE:** modal excitation and partial-ratio/damping controls are established.
**INFERENCE:** feeding the combined Pamplist bus to one modal bank creates an
audibly common body. **HYPOTHESIS:** this will feel cohesive rather than merely
muddy; only a later listening protocol can decide that claim.

## 6. Musical-practice research

No named tradition, repertoire, community, or culturally situated structure is
introduced. The revision concerns controller/page ownership and a generic
modal-response principle. It borrows no repertoire, tuning system, identity,
or authenticity claim and requires no cultural translation.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Mode-dependent control surface / finite-state UI | Contextual pages are common on programmable controllers | `selected_page` chooses one of seven lane maps or one global map; accepted Core state remains authoritative | Eight buttons become semantically complete without an eighth sound lane | Stale page writes into lane 7 or global edits mutate voice records | Exhaust all CC values on every page and compare non-target records |
| Monotonic command generation | Sequence/token patterns are common for callback-safe actions | Increment `effect_clear_generation`; callback clears exactly once when generation changes | A repeatable performance action needs no raw GUI/button pulse in DSP | Duplicate, missed, or wrap mishandling | Press/select/repress/duplicate/release traces and block partitions must match |
| Shared latent state | Common-bus processors are established audio practice | One mode bank receives only the aggregate dry bus | All voices can acquire one temporary body without losing local synthesis ownership | Shared bus masks transients or becomes unstable | Dry comparator, bounded tail, clear, saturation, and listening checks |

## 8. Novelty map

### Common elements

Per-track voices, contextual controller pages, bus drive, modal resonators,
wet/dry macros, damping, stereo width, ducking, and clear/reset gestures are
established mechanisms.

### Less-common combinations found

The bounded local search found Pamplist's clock-lane/macro-voice surface and
Cinderwheel's resonance-driven instrument separately. It did not establish a
normative existing design with exactly seven Pamplist lanes plus one
Global/Clear page and one shared modal body.

### Proposed contribution

No universal novelty claim is made. The proposed contribution is interaction:
the eighth physical selector changes category from sound source to explicit
shared-state performance page, while the common resonator sits after rather
than inside the independent voices.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Keep eight voices and add a ninth global mode | Exceeds the physical eight-button mental model | User confusion and controller topology |
| Global Plaits model plus local model offsets | Engine and model are the same source selection axis | Revision 0.3 source semantics |
| Reuse one voice as the effect | Reintroduces hidden ownership and changes dry synthesis | Predecessor defect |
| Full reverb or multi-effect rack | Obscures the first musical hypothesis and expands controls | Scope and validation cost |
| Per-lane resonators | Does not create one shared body and multiplies state/controls | User asked for cohesion across everything |
| Import Rings or Clouds DSP | Unnecessary source/dependency expansion and false identity pressure | Local modal bank can test the hypothesis |
| Extract Cinderwheel DSP into shared infrastructure | Changes another accepted prototype and creates a premature abstraction | Instrument Lab says use it as regression, not superclass |
| Dynamic mix normalization | Changing active lanes would change every other lane's dry level | Violates local ownership |

## 9. Recommended architecture

### Signal flow

```text
seven rational lane schedulers
  -> seven local route rows
  -> seven persistent authenticated macro voices
  -> per-voice Level
  -> signed 64-bit dry L(main) / R(aux) sums
  -> [dry reference branch]
  -> Cohesion branch: Drive -> six shared modal modes -> Damping/Width/Duck
  -> COHERE interpolation between dry and cohesion branch
  -> shared Master
  -> one final Q27 clamp
```

The selected page is control state, not an audio node. Pages 0-6 address one
lane/voice. Page 7 addresses global/effect controls. There is no voice index 7.

### Executable DSP contract

Let `Q = 2^27`, `xL = sumMain/Q`, and `xR = sumAux/Q` before Master. Six modal
states each store real/imaginary floats. Harmonic ratios are
`H=[1,2,3,4,5,6]`; inharmonic ratios are
`I=[1,1.41421356,1.932,2.756,3.561,4.781]`.

| Mechanism | Equation or pseudocode | Coefficients/ranges | Gain and stability bound | Update timing | Failure behavior |
|---|---|---|---|---|---|
| Parameter smoothing | `v += (target-v)*a`; snap exactly when within `1e-7` | `a=1-exp(-1/(0.010*48000))` for Cohere/Master; `0.030 s` for modal controls | Convex movement inside sanitized ranges | Per sample; targets accepted at 16-frame boundary | Non-finite target sanitizes to default |
| Drive branch | `g=1+7*drive`; `s=(1-drive)*x + drive*tanh(g*x)/tanh(g)` | Drive `[0,1]` | `|tanh|<=1`; dry branch remains separate | Per sample | Non-finite result clears effect state and substitutes dry |
| Root and ratios | `f0=440*2^((root-69)/12)`; `ratio_i=lerp(H_i,I_i,spread)`; `f_i=min(0.45*fs,f0*ratio_i)` | Root MIDI `[24,84]`; Spread `[0,1]` | Frequencies positive and below Nyquist guard | Recompute coefficients per sample from smoothed controls | Invalid coefficient clears all modes and increments diagnostic |
| Modal tail | `T=0.06*(4/0.06)^tail`; `Ti=T/(1+damp*0.32*i)`; `r_i=exp(-1/(Ti*fs))` | Tail/Damping `[0,1]`; `0<r_i<1` | Strictly stable poles | Per sample from smoothed controls | Clamp to finite declared ranges; otherwise clear |
| Modal excitation/update | `u=mid + side*pan_i`; `re+=u*w_i*(1-r_i)`; rotate `(re,jm)` by `2*pi*f_i/fs`, then multiply by `r_i` | `w_i=exp(-0.34*damp*i)`; base pan `[-1,.55,-.35,.85,-.7,.25]*width` | Pole-distance input normalization; output divides by positive `sum(w_i)` | Per sample | Denormals snap to zero; non-finite mode clears entire bus |
| Stereo wet | `wetL=sum(re_i*w_i*(1-pan_i))/sum(w_i)`; `wetR=sum(re_i*w_i*(1+pan_i))/sum(w_i)` | Width `[0,1]` | Normalized mode-weight sum; final Q27 clamp remains authority | Per sample | Zero/invalid normalizer clears and returns zero wet |
| Duck | Envelope peak follower on `max(|xL|,|xR|)`; `duckGain=1/(1+6*duck*env)` | Attack `5 ms`; release `160 ms`; Duck `[0,1]` | Gain in `(0,1]` | Per sample | Non-finite envelope resets to zero |
| Cohere | `fx=s + 0.82*wet*duckGain`; `y=x + cohere*(fx-x)` | Cohere `[0,1]` | At stable zero, exact dry integer branch is selected; final Master/clamp bounds output | Per sample; exact dry branch after smoothing snap | Clear token zeros modes/envelope without altering dry/source/scheduler state |
| Final conversion | `round(y*Q*master)`, clamp to Q27 | Master `[0,1]` | One declared final saturation point; no dynamic normalization | Per sample | Saturation and non-finite diagnostics increment |

### State and timing model

- Core construction allocates seven source instances and fixed modal state only.
- Controls are accepted at the next 16-frame source quantum.
- Page selection alone changes no audio state.
- A clear-generation change zeros six modes and the duck envelope before the
  next rendered sample; it does not reset lanes, source voices, trigger counts,
  source RNG, transport, or accepted parameters.
- Reset restores all defaults and exact fresh-run bytes.
- Panic stops transport and clears voices, schedulers, and cohesion state.
- Stopped transport is exact silence and clears the cohesion bus on the first
  stopped quantum.
- No Freeze/capture or serialized recall exists in this slice.
- Non-finite effect state clears the entire effect bank and returns the dry
  branch for that sample. Source non-finite behavior remains unchanged.
- Repeatability means byte-identical PCM/events/snapshots for the same controls,
  seed, and host partition, except host partitions must also be identical.

### Control and performance mapping

Regular Launch Control 3 Custom Mode 1, MIDI channel 16:

| Control or gesture | Range or states | DSP mapping | Perceptual role | Safety or pickup behavior |
|---|---|---|---|---|
| CC40-46 press | page 1-7 | Select corresponding lane page | Focus local track | Release accepted no-op; selection changes no sound |
| CC47 first press from lane | Global page | Select page 8 | Enter shared performance controls | Does not clear on entry |
| CC47 press while Global selected | action | Increment clear generation once | Flush resonant history | Holds/duplicate press do not repeat; release no-op |
| Lane CC20-27 | signed route `[-1,1]` | Trigger, Pitch, Model Sweep, Harmonics, Timbre, Morph, Decay, Level | Local clock-shape routing | Center 64 is zero |
| Lane CC28-35 | existing transforms | Rate, Phase, Shape, Hits, Rotation, Probability, Repeat, Amplitude | Local temporal behavior | Existing bounds preserved |
| Global CC20-27 | normalized/quantized | Drive, Cohere, Root, Spread, Tail, Damping, Width, Duck | Shared body performance | Accepted-state UI; Root maps 24-84 semitones |
| Global CC28-29 | bounded | BPM 20-300, Master 0-1 | True global timing/output | Smoothed; Master remains final gain |
| Global CC30-35 | unassigned-global | Count and ignore | Deliberately no replicated lane controls | No state change |
| JUCE MODEL | integer 0-23 on lane page | Selected lane base source model | Stable local identity | Label shows source-order name |
| JUCE MODEL SWEEP | signed route | Selected lane model offset | Local engine movement | Never changes another lane or base model |
| JUCE CLEAR FX | action | Increment clear generation | Immediate tail flush | Available only as explicit action |

The frozen map is exhaustively compared with compiled mapping and synthetic
traces. Physical endpoint/device behavior remains a separate evidence level.

### Parameter interactions and edge cases

- Cohere zero wins over Drive and all modal parameters for the audible path.
- Root/Spread changes glide through coefficient smoothing; no engine or lane
  state is reconstructed.
- Tail maximum cannot produce a pole at or above one.
- Damping shortens and reduces higher modes; it never changes the dry path.
- Duck affects wet modes only, keeping new dry transients intelligible.
- Clear is idempotent for already empty effect state and does not change
  accepted parameter values.
- Page selection does not retarget a pending GUI callback; UI writes use the
  accepted selected page at dispatch and project accepted state afterward.
- Clear-generation wrap is defined by unsigned inequality; a change still
  means one clear at the next quantum.

### Failure behavior

Invalid controls sanitize and count. Unsupported blocks clear requested output
and do not advance transport. Non-finite effect state clears the entire bus and
uses dry audio for the affected sample. No callback allocation, lock, file I/O,
JSON, endpoint, UI work, or unbounded loop is allowed.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Sample rate | Fixed 48 kHz | predecessor Core/JUCE contract | exact only | ready |
| Internal quantum | 16 frames | authenticated source wrapper | fixed | ready |
| Host block | 1-512 frames | predecessor evidence | exact partition invariance | ready |
| Voice count | 7 persistent full source instances | one fewer than passing revision 0.3 | fixed | feasible |
| Effect state | 6 complex modes, smoothers, one envelope; no delay buffers | proposed equations | fixed stack/Core state | feasible |
| Numeric path | source q27 -> signed 64-bit sum -> bounded float bus -> final q27 | predecessor plus new bus | finite and final-clamped | test required |
| Dependencies | exact configured source; Instrument Lab; authenticated JUCE 8.0.15 | existing authorities | no fetch/fallback | ready |
| Real-time CPU | Seven source voices plus six modes | inference only | no live deadline claim | unresolved/deferred |
| License/distribution | private local prototype with preserved provenance | ADR 0016 and source records | no distribution claim | bounded |

## 11. Minimal experiment

### Central hypothesis

**HYPOTHESIS:** replacing the eighth voice with one explicit global page and a
shared post-mix modal body makes control ownership legible and provides a
performative arc from independent clarity to a common resonant sound and back.
Objective evidence can prove ownership, effect activity, tail, clear, safety,
and determinism. Only later listening can judge cohesion or usefulness.

### Smallest vertical slice

Seven voice lanes, one contextual global page, one six-mode bus, one clear
action, one standalone presentation, and no additional effects or routing.

### Test signals and gestures

| Field | Bound value |
|---|---|
| Sample rate and supported block sizes | 48000 Hz; `1,16,64,128,257,512` frames |
| Deterministic seed | decimal `1346456912` (`0x50414d50`) |
| Event/sample timeline convention | controls accepted only when a new 16-frame quantum begins; event frame is first output frame affected |
| Literal condition IDs and count | `PAMP_R04_DRY7`, `PAMP_R04_GLOBAL_ISOLATION`, `PAMP_R04_COHERE`, `PAMP_R04_CLEAR`, `PAMP_R04_SWEEP`, `PAMP_R04_24`, `PAMP_R04_SILENCE`, `PAMP_R04_DRY_CMP` (8) |
| Falsifying comparator condition | `PAMP_R04_DRY_CMP` is the same seven-voice excitation with Cohere fixed at zero; `PAMP_R04_COHERE` must diverge in PCM and effect-state trace |
| Output names and kinds | stereo `audio.wav`; canonical `events.json`, `snapshots.json`, `metrics.json`, `controller-trace.json`, `manifest.json`, and hashes |
| Objective tolerances | 100% finite; Q27 bounded; zero nominal final saturation; exact partition hashes; exact silence/clear subcases; poles `<1`; Cohere output and trace diverge from dry; global edit leaves all seven lane/voice records exact |
| Artifact retention policy and location | checked in under `research/prototypes/pamplist/contract-r04/evidence/`; validator refuses overwrite |

`PAMP_R04_CLEAR` first excites the shared bus, sets all seven voice Levels to
zero while transport continues, proves a nonzero tail, increments Clear, then
requires exact zero tail while source RNG/scheduler snapshots match a no-clear
reference. `PAMP_R04_SWEEP` drives every global parameter through min/max and
rapid changes. `PAMP_R04_24` retains the source-order model sweep.

### Measurements

- Peak/RMS/DC/finite/nonzero/saturated sample counts per channel.
- Per-mode pole maxima, state peaks, effect non-finite clears, effect clear count,
  duck envelope maximum, and dry/effect difference energy.
- Accepted page/global/lane/voice records, trigger counts, source RNG states,
  and event traces.
- Exact hashes at all six block partitions and fresh relocated root.

### Listening protocol

Deferred. Later audition should compare dry seven-voice, low Cohere, high
Cohere, root/spread sweeps, Tail/Damping extremes, Duck off/on, and Clear. Judge
voice separation, masking, perceived common body, transition clicks, and
whether Clear is findable. No host render can answer these.

### Stop or pivot conditions

- Any global edit mutates lane/voice state or Global entry clears accidentally.
- Cohere zero cannot return to exact dry after the declared smoothing interval.
- Clear resets source/scheduler state or leaves nonzero effect output.
- Nominal conditions saturate, produce non-finite state, excessive DC, or a
  resonator pole reaches one.
- The effect is objectively inactive or partition-dependent.
- A required source/JUCE/controller authority drifts.
- Work requires app launch, physical controller access, another dependency,
  canonical records, or a broader effect architecture.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Proposal is implementable | ready bundle validates against exact proposal fingerprint | proposal | pending | `contract-r04/` |
| Seven voices remain independent | focused state/source/RNG/controller tests | host structural | pending | CTest |
| Global page is semantically isolated | exhaustive contextual mapping and snapshot comparison | host structural | pending | control trace/tests |
| Shared bus is active and bounded | Cohere/dry comparator, pole/state/gain metrics | host signal | pending | retained evidence |
| Clear is effect-only | tail/clear/reference condition | host signal | pending | retained evidence |
| Target compiles | authenticated JUCE configure/build/hash without launch | target build | pending | `juce-build.json` |
| Real-time deadline | live callback timing/xruns | real-time | not run | deferred |
| Controller works physically | endpoint/configuration/gesture/feedback session | connected device | not run | deferred |
| The bus sounds cohesive | controlled audition | listening | not run | deferred |
| Production-ready instrument | canonical/runtime/distribution gates | production integration | not run | deferred |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/pamplist/contract-r04/`
- Proposal fingerprint and approval reference: exact revision 0.4 SHA-256 plus
  the current-thread request to remove voice 8, use page 8 for globals, remove
  duplicated/misleading globals, and add a clearable shared resonant effect.
- `validate_implementation_bundle.py --phase ready`: not yet run.

### Files expected to change

- `research/prototypes/pamplist/include/schuss/pamplist/{core,control_map}.hpp`
- `research/prototypes/pamplist/src/{core,control_map,juce_main,render}.cpp`
- Pamplist focused tests, renderer/JUCE evidence scripts, CMake version, README,
  topology, semantic surface, source-dependency annotation, prototype index,
  handoff, and promotion needs.
- New proposal and `contract-r04/` only; predecessor contracts stay unchanged.

### Focused tests

- Seven-lane cardinality, local voice independence, model-sweep locality, and
  stochastic interleave regression.
- Contextual CC map exhaustion, Global entry/repress/hold/release action state,
  and global-to-lane noninterference.
- Modal coefficient/pole bounds, Cohere exact bypass, effect activity, tail,
  Clear-only state, rapid automation, non-finite recovery, reset, silence,
  partition identity, and no allocation.
- UI source compile and accepted-state presentation.

### Adjacent regression tests

- Exact configured source authentication and all 24 models.
- Instrument Lab consumer/topology freshness.
- Preserved revision 0.2/0.3 retained artifact authentication where their
  frozen validators remain revision-local.

### Expensive or hardware checks

- Once after freeze: retained render reproduction, authenticated JUCE build,
  relocated Core/evidence reproduction, and Schuss `current`.
- No launch, endpoint, physical controller, real-time, or listening work.

### Deferred work

Physical mapping feel/feedback, additional effects, presets/scenes, external
clock, mute/solo/pan, Ksoloti/Gills feasibility, production integration, and
distribution.

### Dependency contract

- Authenticated macro voices: configured `patcher` commit
  `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, tree
  `58917f3e2e46a30337cfb6292a3504845b1d5552`; read-only, no fallback/copy.
- Source RNG context remains owned by one single-threaded Pamplist Core; no
  concurrent multi-Core claim.
- Instrument Lab is the shared host seam only; musical DSP remains Pamplist-owned.
- JUCE 8.0.15 must match the authenticated extracted-tree manifest; fetch off.
- Controller topology SHA-256 remains
  `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`.
- The modal effect is newly designed from published principles and local
  lessons; no external resonator source enters the artifact.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Source type | Notes or proof gap |
|---|---|---|---|---|---|
| CL-001 | EVIDENCE | Revision 0.3 voice controls are lane-local despite misleading top-row naming | Pamplist 0.3 Core/JUCE/tests | exact local source | Current user confusion is presentation-grounded |
| CL-002 | EVIDENCE | Regular Launch Control 3 has 16 endless encoders and 8 programmable buttons | Novation guide plus local topology | first-party and authenticated local artifact | Physical installed Custom Mode remains unverified in this turn |
| CL-003 | EVIDENCE | Modal structures can be described as modes with controllable frequency ratios, higher-mode damping, and decay | Mutable Instruments Rings manual | first-party technical behavior | No implementation equivalence claimed |
| CL-004 | EVIDENCE | Pole-distance excitation normalization prevented severe gain failure in a prior local resonator trial | Cinderwheel Core/RESULTS | exact local source and measurement | Different musical topology |
| CL-005 | INFERENCE | One post-mix modal bank gives all seven voices one causal shared state | signal-flow reasoning | design inference | Objective state trace can prove shared excitation, not perceived cohesion |
| CL-006 | HYPOTHESIS | Cohere/clear creates a useful performance arc without destroying lane separation | user request plus proposed experiment | musical hypothesis | Requires listening |
| CL-007 | UNRESOLVED | Seven full voices plus the bus meet live callback deadlines | no live measurement | proof gap | Deferred real-time gate |

## 15. Open questions and decision gate

### Open questions

- Whether six modes are rich enough without becoming metallic or muddy.
- Whether the proposed Root/Spread/Tail ranges feel useful.
- Whether Duck should default above zero after audition; objective default stays zero.
- Whether pressing Global again is sufficiently discoverable as Clear.
- Whether future versions need mute/solo or per-lane effect sends.

These questions do not block the bounded host experiment; they block listening
acceptance or a wider performance design.

### Recommendation

Proceed with exactly seven independent voices and one Global/Clear page. Use a
single six-mode post-mix resonator plus Drive, controlled by Cohere and seven
supporting parameters. Keep Cohere zero as the exact dry escape and repeated
Global press as effect-only Clear.

### Approval requested

The current-thread request already authorizes uninterrupted implementation of
this revision 0.4 architecture after its exact SHA-256 is bound into a ready
bundle at `research/prototypes/pamplist/contract-r04/`. Authorization reaches
only source, host structural, host signal, and authenticated target-build
evidence. It does not authorize launch, endpoints, physical-device work,
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

Real-time, connected-device, listening, embedded, distribution, and production
evidence remain deferred regardless of host/target-build success.
