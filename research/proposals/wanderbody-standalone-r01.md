# Wanderbody 0.1 standalone first playable

> Status: proposed
> Proposal revision: 0.1
> Original idea: Implement the attached Wanderbody JUCE handoff as the smallest noncanonical standalone vertical slice that can listen to or internally generate sound, hover locally, wander by correlated motion, recur through remembered decision tuples, and add a source-preserving physical body.
> Implementation target: macOS arm64 standalone JUCE 8.0.15 application with JUCE-independent portable C++17 Core and deterministic offline renderer
> Working artifact and evidence level: a noncanonical portable Wanderbody Core, deterministic renderer, and built-but-unlaunched standalone application; host-signal plus target-build evidence
> Decision gate: uninterrupted implementation was explicitly authorized by the user's 2026-08-25 instruction, "implement it"; the readiness bundle remains mandatory before DSP edits.

## 1. Product thesis

### One-sentence thesis

Wanderbody is a recent-memory instrument that turns one heard gesture into a
bounded family of local examinations, correlated departures, recognizable
returns, and optional resonant afterimages.

### Instrument identity

The performer supplies live input or enables a modest internal exciter, then
controls where the instrument listens, how far it roams, whether its decisions
are fresh or remembered, and how strongly the recalled fragments excite a
body. The instrument answers by revisiting its own recent capture rather than
generating unrelated notes. That closed relationship among source, memory,
motion, recurrence, and resonance is the identity; the implementation is not a
general granular effect, modular graph, CDP wrapper, or Mutable Instruments
port.

**HYPOTHESIS:** A fixed-capacity history of correlated fragment decisions will
make repetition learnable while preserving enough local mutation to feel alive.

### Intended user and musical situation

A performer or sound designer using a private macOS standalone wants a small,
self-playing partner for microphones, line input, or an internal test exciter.
Revision 0.1 supports exploratory desktop use and objective testing. It does
not claim a release-ready workflow or a completed live instrument.

### In scope

- Device-rate mono capture derived from up to stereo input, plus a deterministic
  internal exciter and source blend.
- Eight seconds of provisional recent memory allocated during `prepare()`.
- One Hover and one Drunk decision policy, an eight-tuple recurrence history,
  four fixed fragment voices, linear interpolation, raised-cosine fragment
  windows, and a six-mode original resonant body.
- Fresh, Locked, Shuffled, and Mutated recurrence states.
- Freeze, bounded click-safe Clear, Reset, Panic, and version-1 transactional
  control/decision state.
- Deterministic Core/offline evidence at 44.1, 48, 88.2, and 96 kHz and block
  partitions including non-power-of-two sizes.
- A minimal JUCE standalone with audio/MIDI device settings, semantic controls,
  accepted-state feedback, and a decimated memory display.

### Out of scope

- Imported files, onset landmarks, spectral processing, convolution, true
  pitch-independent time stretching, interaction/Warps processing, CDP source,
  Mutable source, or source-fidelity claims.
- Plug-ins, Ksoloti/Gills, canonical catalog/graph/provider/runtime identity,
  more than four fragment voices, a frozen public parameter API, or a stable
  session/preset file format.
- MIDI learn, physical MIDI mapping, live endpoint access, app launch,
  callback-deadline proof, listening approval, packaging, distribution, and
  production integration.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

1. The user-supplied
   `/Users/lanceship/Downloads/Wanderbody_JUCE_Handoff.md` is product and
   engineering reference; the user's later `implement it` message is the
   execution authority.
2. Schuss ADR 0016 keeps portable DSP outside JUCE while allowing JUCE to own
   desktop audio/MIDI lifecycle.
3. Instrument Lab v1 is the noncanonical mechanical path and limits this work
   to proposal, source, host-structural, host-signal, and target-build evidence.
4. The existing repository-authenticated JUCE 8.0.15 source manifest is the
   only allowed host-framework input; fetching and installation remain off.
5. The design lane is `new-design`. CDP and Mutable materials are observed
   behavior and engineering references, not normative source.

### Deliverables

- This proposal and `research/prototypes/wanderbody/contract-r01/`.
- Portable C++17 Core, state/control seam, tests, and deterministic renderer.
- Minimal standalone JUCE application built but not launched.
- Noncanonical Instrument Lab topology/index/control/dependency/handoff records.
- Exact objective results and a gap ledger.

### Acceptance tests

The exact tests are frozen in Task 048 and the implementation bundle. At a
minimum they prove capture wrap/freeze/clear integrity; Hover locality; Drunk
bounded correlation; recurrence invariants; state rejection/round-trip;
four-voice capacity; body bypass/decay; finite bounded output; zero process-time
allocation; deterministic semantic decisions across block partitions; an
uncorrelated comparator that fails the locality/correlation criterion; an
authenticated unlaunched target build; and proportional repository checks.

### Decisions this work may make

- Revision-0.1 fixed capacities, original equations, provisional defaults,
  semantic controls, test points, objective tolerances, and internal layout.
- A mono capture/fragment Core with stereo pan/body presentation.
- A body implemented from standard parallel second-order resonators rather than
  copied source.

### Decisions this work must not make

- A permanent capture duration, voice count, interpolation, channel topology,
  pitch/time model, resonator resolution, public control count, file format,
  supported OS matrix, distribution licence, or product-quality judgment.
- Any canonical Schuss identity or promotion, external-source equivalence,
  global novelty, real-time, physical-device, listening, or production claim.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| `research/prototypes/wanderbody/` portable Core and renderer | host-signal | Frozen conditions meet finite, peak, DC, locality, correlation, recurrence, body, state, allocation, and partition-determinism checks | Callback deadline, audible quality, device behavior, or production readiness |
| `Wanderbody 0.1.app` in an isolated build directory | target-build | Authenticated JUCE 8.0.15 compiles and links one macOS arm64 standalone bundle without fetch, launch, or install | A working audio device session, real-time headroom, listening approval, signing, notarization, or distribution |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| CDP Hover/Hover2 | Reads a local sound region with repeated zig-zag or polarity-related traversal and bounded frequency/location variation | [CDP EXTEND documentation](https://www.composersdesktop.com/docs/PDF/extend.pdf) | Transform into an original bounded pendular decision policy and shared live fragment renderer | Medium; public behavior is documented, exact source behavior is not a target |
| CDP Drunk | Moves through source material by bounded random steps; the documented BLUR variant reflects attempted boundary escapes | [CDP BLUR documentation](https://www.composersdesktop.com/docs/PDF/blur.pdf) | Transform into a device-rate correlated position walk with explicit reflection and deterministic seed | High for behavior, no fidelity claim |
| Marbles Déjà Vu | Recycles earlier random choices, locks a finite loop, or permutes familiar choices | [Marbles manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/manual/) | Keep the perceptual states but store Wanderbody fragment-decision tuples in a new implementation | High |
| Rings modal resonator | Short excitation drives modes whose frequency relation, brightness, damping, and position affect material character | [Rings manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/rings/manual/) | Keep the source-filter interaction; implement a smaller original modal bank | High for public mechanism, no Rings equivalence |
| JUCE device callback | Device restarts may change sample rate/block size; callback must fill available output pointers | [JUCE `AudioIODeviceCallback`](https://docs.juce.com/master/classjuce_1_1AudioIODeviceCallback.html) | Keep as host boundary; prepare Core outside callback and fail closed on invalid layouts | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| CDP EXTEND HOVER/DRUNK | Offline transformation suite | Local zig-zag and random-walk source navigation | Whole-file/offline processes, not bounded live scheduling | [CDP R8 introduction](https://www.composersdesktop.com/docs/IntroducingCDP-R8.pdf) | Reimplement interaction from documented behavior; do not wrap the CLI or copy LGPL source into the Core |
| Mutable Instruments Marbles | Eurorack random sampler | Probability-controlled recent-decision reuse, lock, and shuffle | Operates on rhythms/voltages rather than audio fragment tuples | [First-party manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/manual/) | Store correlated decisions, not raw automation or audio |
| Mutable Instruments Rings | Eurorack resonator | Excitation into modal/string resonators | Dedicated physical-model voice with several models and polyphony | [First-party manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/rings/manual/) | Keep body parallel and bypassable; use six original modes first |
| Schuss Murmur Map | Local noncanonical prototype | Seeded route history and learnable recurrence | Routes among authored sound places and synth lanes; it does not capture/re-read source audio | `research/prototypes/murmur-map/` | Reuse evidence and bounded-state lessons only; Wanderbody owns different audio-memory semantics |
| Schuss Layerwell | Local noncanonical prototype | Bounded capture stores and accepted-state UI | Layer sampler around exact source instruments, not autonomous fragment motion | `research/prototypes/layerwell/` | Reuse mechanical real-time and evidence patterns, not sample-store code or identity |
| General granular delays | Hardware/software class | Circular capture, overlapping read heads, envelopes | Usually expose density, position, size, pitch, and spray as independent parameters | Bounded product-class search on 2026-08-25; no exhaustive market claim | Wanderbody should expose coherent motion/recurrence behavior rather than independent random spray |

No AU/VST comparison is required because revision 0.1 explicitly rejects a
plug-in target. The market search is bounded; it does not support a claim that
the combination is unique.

## 5. Synthesis and engineering research

| Paper, patent, standard, or technical source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Julius O. Smith, *Physical Audio Signal Processing*, “Modal Expansion” | Modal synthesis as a parallel second-order filter bank with per-mode frequency, damping/bandwidth, and gain | Authoritative technical text | Direct basis for the original six-mode body | A generic modal bank is not a calibrated model of a particular object; [source](https://www.dsprelated.com/freebooks/pasp/Modal_Expansion.html) |
| CDP R8 EXTEND and BLUR documentation | Fragment splicing, Hover, and drunken source traversal behavior | First-party process documentation | Observable reference for motion invariants | Offline parameters and exact implementation are not imported |
| Mutable Instruments Marbles manual and pinned source reference | Finite decision memory, loop, and permutation behavior | First-party manual/source | Prior art and behavioral comparator for recurrence | Wanderbody tuple schema and mutation remain original; no source copied |
| Mutable Instruments Rings manual and pinned source reference | Modal source-filter body and excitation-position concept | First-party manual/source | Prior art for source-preserving resonant body | The six-mode body is smaller and not equivalent |
| JUCE 8 `AudioDeviceManager` and `AudioIODeviceCallback` docs | Device selection, restart, sample-rate/block-size negotiation, xrun/CPU observations | Framework documentation | Host lifecycle and UI settings boundary | A build cannot prove callback deadlines or physical endpoint behavior |

## 6. Musical-practice research

No musical culture is used as a feature source in revision 0.1. The handoff's
identity is already grounded in recent-memory behavior, stochastic motion, and
modal response. Adding a named tradition merely to satisfy a novelty narrative
would be decorative and risk stripping context from a living practice.

| Named practice, community, place, and period | Source and source relationship | Structural principle | Possible translation | Context or restriction | Risk |
|---|---|---|---|---|---|
| Not selected | No community material is needed or used | The general relation between repetition and variation is not attributed to a culture | Implement and test recurrence directly | Do not borrow repertoire, recordings, terminology, imagery, tuning, or identity claims | A superficial cultural analogy would add ethical risk without improving the experiment |

There is therefore no authenticity claim, restricted material, attribution
plan, or collaboration dependency. A future culture-specific design would
require its own situated research and practitioner relationship.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Correlated random walk with reflecting boundaries, stochastic processes | CDP DRUNK explicitly documents bounded random traversal and reflection | Position velocity is an AR(1)-like state; reflection preserves bounded memory locality | Motion has inertia and can leave/return without independent jumps | Correlation is inaudible or causes edge sticking | Compare lag-1 step correlation, boundary occupancy, and launch-distance distribution with uniform independent positions |
| Fixed-capacity replay memory, online learning/control systems | Marbles provides strong musical prior art for recycling random choices | Store eight semantic fragment tuples and select fresh, ordered, permuted, or bounded-mutated reads | Repetition becomes a stable performance state rather than a reduction in randomness | Locked output is not recognizable, or mutation destroys identity | Require exact tuple cycling in Locked, set equality in Shuffled, and bounded per-field distance in Mutated |
| Generation counters, concurrent data structures | Common circular-buffer technique; live samplers use equivalent validity concepts | Every fragment carries absolute source time; reads fail if overwritten or cleared | Prevents stale-pointer and half-reconfigured memory behavior | A voice reads an overwritten generation or wrap changes semantics | Force repeated wrap, Freeze, Clear, and re-prepare while asserting every read lies in the valid absolute interval |

The home-field and audio searches show substantial prior art. The value here is
the coherent performance model, not a claim that these algorithms are novel.

## 8. Novelty map

### Common elements

Circular live capture, windowed fragments, random walks, finite random-memory
loops, modal filter banks, internal exciters, dry/wet mix, and deterministic
PRNGs are all established techniques.

### Less-common combinations found

Marbles combines recurrence with random decisions but not recent audio
fragments. CDP combines source motion with fragment transformation but is an
offline suite. Rings provides a body but not recent-memory motion. Granular
delays combine capture and read heads but commonly expose independent spray
parameters rather than explicit Fresh/Locked/Shuffled/Mutated semantic states.

### Proposed contribution

**HYPOTHESIS:** The bounded combination of a coherent local/away motion state,
decision-tuple recurrence, generation-safe recent memory, and a parallel modal
afterimage can form one learnable instrument gesture: hear, hover, wander,
recur, resonate.

Searches covered first-party CDP R8 documentation, Mutable Instruments Marbles
and Rings manuals/source, local Schuss prototypes, JUCE device documentation,
modal-synthesis engineering material, and bounded granular-instrument query
families on 2026-08-25. This supports “distinct vertical-slice hypothesis,” not
“new,” “first,” or “unique.”

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Compile or link CDP8 | Whole-file LGPL program architecture obscures the real-time experiment and creates a different dependency contract | CDP documentation/repository and the handoff's explicit boundary |
| Port Marbles `RandomSequence` | The desired tuple/state model is small and clearer as Wanderbody-owned code | Pinned source is reference only; no equivalence claim is needed |
| Port Rings in revision 0.1 | Source closure and internal block/sample-rate assumptions would delay the central capture/motion proof | The standard modal-bank experiment is independently testable |
| Spectral or pitch-independent processing | It multiplies latency, allocation, and fidelity choices before motion/recurrence are known to work | Explicit handoff non-goal |
| Onset landmarks | Useful later, but continuous absolute source time is enough to falsify the first hypothesis | Avoid detector thresholds becoming product contracts |
| More than four voices | Density can mask recurrence and raises CPU/stealing complexity | Start with fixed capacity and profile/listen later |
| Cultural metaphor/preset | No situated practice is necessary for the design | Avoid extractive or authenticity claims |
| Plug-in target | Host transport/state would distort the standalone-first architecture | Explicit handoff non-goal |

## 9. Recommended architecture

### Signal flow

```text
device input ─┐
              ├─> sanitize + source blend ─> live bus ─> rolling mono capture
internal ping ┘                                      │
                                                    └─> absolute-time reader
performance controls ─> Hover/Drunk ─> recurrence ─> fragment commands
fragment commands ─> four windowed voices ─> memory bus ─┬─> dry/memory mix
                                                         └─> six-mode body ─> mix
live bus ────────────────────────────────────────────────────────────────┘
mix ─> DC block + soft ceiling ─> stereo output + bounded snapshot
```

JUCE owns devices, GUI, and optional MIDI device selection. The Core knows only
plain values, audio buffers, fixed actions, and portable state.

### Executable DSP contract

| Mechanism | Equation or pseudocode | Coefficients/ranges | Gain and stability bound | Update timing | Failure behavior |
|---|---|---|---|---|---|
| Source sanitize/blend | `x = finite(input) ? clamp(input,-2,2) : 0`; `live = g_ext*x + g_int*exciter` | `g_ext,g_int` in `[0,1]`; 20 ms one-pole slew | Blend normalized by `max(1,g_ext+g_int)` | Every sample; targets accepted at block start | Non-finite input becomes zero and increments a counter |
| Internal exciter | Phase-continuous triangle at `f=55*2^(pitch*2)` Hz, multiplied by a deterministic 3 ms attack / 180 ms decay envelope; a bounded noise impulse is added every `0.5+1.5*(1-energy)` seconds | Phase `[0,1)`; envelope `[0,1]`; noise gain `<=0.18`; deterministic PCG stream | Exciter magnitude `<=0.45` before source normalization | Sample accurate; next trigger is absolute-frame based | Invalid sample rate leaves exciter silent |
| Capture store | On an unfrozen frame write `buffer[W mod C]=live`; increment absolute `W`; valid interval is `[W-V,W)`, `V=min(V+1,C)` | `C=ceil(8*fs)` allocated in prepare; `W` uint64; mono float | All indices reduced modulo nonzero `C`; no pointer escapes Core | One write per sample; Freeze changes before addressed sample | Invalid capacity/process clears output; Clear invalidates metadata after a 10 ms wet fade and never bulk-clears in callback |
| Interpolated read | For absolute `t`, require `oldest<=floor(t)` and `ceil(t)<W`; `read=(1-frac)b[i0]+frac*b[i1]` | Linear interpolation; source rate `r` in `[-1.5,-0.5]∪[0.5,1.5]` | Convex interpolation of finite clamped capture samples | Every voice/sample | Invalid or overwritten source enters a 64-sample release and increments invalid-read count |
| Hover policy | `h'=h+s*dir`; reflect `h` into `[0,1]` and flip `dir`; `p=a+field*w*(2h-1)`; playback direction follows `dir` | `a∈[0,1]`; `field∈[0.01,0.48]`; `w∈[0,1]`; `s=0.12+0.20w` per decision | Position is clamped to the valid normalized source interval | Once per new decision | Empty capture yields no command; invalid state resets `h=0.5,dir=+1` |
| Drunk policy | `v'=0.86v+0.14*(2u-1)*(0.002+0.12w)`; if `w=0`, `v'=0`; `p'=reflect(p+v',[a-field,a+field])` | PCG32 uniform `u`; `p` and reflected bounds in `[0,1]` | Reflection loop has fixed maximum four folds, then clamps; `|v|<=0.14` | Once per fresh decision | Non-finite state resets to anchor and zero velocity |
| Recurrence | Fresh generates and appends; Locked reads oldest-to-newest cyclically; Shuffled creates one Fisher-Yates permutation on entry and cycles it; Mutated cycles history and perturbs position/rate/duration/pan by declared bounded deltas | Capacity 8; one fixed permutation array; mutation `[0,1]`; PCG32 | No dynamic storage; mutation position `<=0.08*field`, rate `<=0.08`, duration `<=8%`, pan `<=0.10`; all reclamped | Mode changes at block boundary; tuple selection at fragment launch | Empty history falls back to Fresh; invalid enum rejects whole control transaction |
| Fragment scheduler | `L=fs*(0.08+0.40*fragment)`; `hop=max(32,round(L*(0.72-0.32*energy)))`; allocate first idle else oldest voice; command freezes absolute start, `L`, rate, gain, pan, body pitch | `L` 80–480 ms; four voices; at most one launch per sample and eight decisions per callback | Fixed loop bounds and voice capacity; gain `<=0.42` per voice | Absolute-frame scheduler independent of callback partition | Capacity/invalid source increments diagnostic and drops or steals deterministically |
| Fragment window | `w(n)=0.5-0.5*cos(2πn/(L-1))`; output `capture(t_n)*w(n)*gain`; reverse is negative source-rate, never a discontinuous buffer reversal | `L>=32`; 64-sample invalid-source release | Four-voice sum scaled by `1/sqrt(4)` | Every sample | Non-finite voice state clears that voice only |
| Modal body | For mode `m`: `y_m[n]=g_m*x[n]+2r_m cos(ω_m)y_m[n-1]-r_m²y_m[n-2]`; `f_m=f0(m+1)(1+0.018*structure*m)` below `0.45fs`; `r=exp(-1/(tau*fs))`; `g_m=sin(π(m+1)position)*(0.25+0.75*brightness^(m/2+1))/sqrt(6)` | Six modes/channel; `f0` 55–440 Hz; `tau=0.12*40^damping` seconds; parameters `[0,1]` | `0<r<0.999999`; body input `0.20*memory`; output scaled `0.18`; per-mode non-finite recovery | Coefficient targets computed per block and linearly interpolated across the block | Any non-finite mode clears its two states and increments body-repair count |
| Mix and safety | Normalize nonnegative dry/memory/body gains by `max(1,sum)`; stereo equal-power pan; DC blocker `y=x-x1+0.995*y1`; ceiling `z=0.98*y/(1+abs(y))` | Mix controls `[0,1]`; 20 ms slew | `|z|<0.98`; finite check after every stage | Every sample | Non-finite final sample becomes zero and latches a diagnostic |

The original body is informed by standard modal synthesis and the public Rings
interaction model. It is not a Rings-derived implementation and does not use
Rings coefficients, tables, source layout, model count, or fixed rate.

### State and timing model

- Events and actions apply before the addressed sample. GUI revision 0.1 sends
  block-boundary control snapshots and monotonic action sequence numbers.
- Absolute capture time increases only when capture writes. Freeze therefore
  preserves both contents and source-time validity.
- Reset restores default controls, seed, policy, recurrence, voices, body,
  capture metadata, counters, and absolute frame zero without reallocating.
- Panic preserves accepted controls and capture contents but clears voices,
  body, envelope, scheduler, and output history at the next block boundary.
- Clear fades memory/body down for 10 ms, invalidates capture metadata and
  recurrence, then fades the eligible path back in; it never loops over the
  complete capture store in the callback.
- Mode changes alter future tuple selection only; active voices retain frozen
  commands.
- State recall is versioned, validated, and transactional. Revision 0.1 stores
  controls, seed, policy, recurrence tuples/permutation/cursors, and motion
  state at a reset boundary. It deliberately excludes capture PCM, active voice
  tails, host handles, absolute wall-clock time, and UI repaint state.
- Re-prepare is a stopped-host operation. It allocates a new capacity from the
  new sample rate and starts an empty capture; no cross-rate capture migration
  is claimed.

The complete operation matrix belongs to `contract-r01/state-matrix.md`.

### Control and performance mapping

| Control or gesture | Range or states | DSP mapping | Perceptual role | Safety or pickup behavior |
|---|---|---|---|---|
| External / Internal | each `[0,1]` | Normalized source blend | Choose heard versus self-generated material | 20 ms slew; non-finite rejected |
| Capture | running/frozen | Enable/disable capture writes | Let memory age or hold still | Block-boundary action; no output jump |
| Clear | action | Bounded fade/invalidate/fade state machine | Empty the learned source and recurrence | Idempotent sequence; no bulk clear in callback |
| Anchor | `[0,1]` | Center of valid recent memory | Return to a chosen locality | 20 ms slew; clamped after wrap |
| Field | `[0,1]` | `0.01+0.47*x` normalized span | Define the local search area | 20 ms slew; valid-interval clamp |
| Motion | Hover / Drunk | Select fresh decision policy | Pendular examination or correlated departure | Changes future decisions only |
| Wander | `[0,1]` | Hover extent and Drunk step magnitude | Stillness to broad motion | Exact zero suppresses Drunk velocity |
| Recurrence | Fresh / Locked / Shuffled / Mutated | Select history operation | Novelty, loop, rearrangement, drift | Mode change preserves active voices and fixed history |
| Mutation | `[0,1]` | Bounds tuple perturbation | Amount of retained-identity drift | Per-field hard bounds |
| Fragment | `[0,1]` | 80–480 ms length | Detail versus gesture | New voices only; min 32 samples |
| Energy | `[0,1]` | Exciter period and fragment overlap | Sparse to active | Fixed voice/event capacities remain |
| Body | `[0,1]` | Parallel modal mix | Physical afterimage | Exact zero structural bypass; 20 ms slew |
| Structure / Brightness / Damping / Position | each `[0,1]` | Modal ratios, gains, decay, excitation weights | Body material and response | Stable ranges and block coefficient ramps |
| Dry / Memory | each `[0,1]` | Source and fragment mix | Preserve source identity versus recall | Normalized sum and soft ceiling |
| Reset / Panic | actions | Full deterministic reset / tail safety clear | Reproducibility and emergency silence | Monotonic idempotent action sequences |

The GUI and compiled defaults are exhaustively compared with the frozen control
map. There is no revision-0.1 physical controller assignment. Device settings
allow the user to choose audio/MIDI devices, but selection/build evidence is not
endpoint evidence.

### Parameter interactions and edge cases

- Empty capture produces live/internal monitor only; the fragment scheduler
  waits until at least one maximum fragment plus interpolation guard is valid.
- Anchor and Field are resolved against the current valid interval, so capture
  wrap never changes an absolute active command.
- `Wander=0` makes Hover stay at Anchor and Drunk velocity exactly zero.
- Entering Locked before eight tuples exist locks the available nonempty prefix;
  an empty history generates one Fresh tuple first.
- Shuffled reorders indices only. Mutated never changes source generation or
  crosses the current valid source region.
- Freeze does not stop internal/live monitor, active voices, body decay, or
  absolute output frame time. It stops capture source time.
- `Body=0` bypasses new body output and clears modes after its 20 ms ramp reaches
  zero so hidden energy cannot erupt later.
- Clear, Reset, Panic, and re-prepare have distinct semantics and counters.
- Changing sample rate recreates time constants in seconds and empties memory;
  no 48 kHz constant is encoded in the Core.

### Failure behavior

Invalid controls/state are rejected before mutation. Null outputs, zero or
oversized blocks, unsupported rates, missing channels, or unprepared processing
return bounded silence and a diagnostic. Non-finite input is replaced with
zero. Non-finite voice or body state is cleared locally; non-finite final output
is zeroed and latched. Queue overflow drops the newest UI command and increments
a counter. No failure path allocates, logs, performs I/O, blocks, retries
without a fixed bound, or destroys the capture store on the audio thread.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Sample rate | Device driven; Core accepts finite 8–192 kHz; frozen test points 44.1/48/88.2/96 kHz | JUCE callback restart docs and offline matrix | No fixed-rate DSP constant | Planned |
| Callback size | Variable, non-power-of-two; maximum declared at prepare | Core API/property tests | 1–2048 frames in revision 0.1 evidence | Planned |
| Capture memory | `ceil(8*fs)` mono floats | Direct capacity calculation | ~1.41 MiB at 44.1 kHz; ~6.0 MiB at 192 kHz, plus negligible metadata | Provisional hypothesis |
| Voice/history/body capacity | 4 voices, 8 tuples, 6 modal modes/channel | Fixed arrays and capacity tests | No process-time growth | Provisional hypothesis |
| Numeric format | 32-bit audio storage/output; double control/coefficient state where useful | Portable C++ and sanitizer tests | All final samples finite and `<0.98` | Planned |
| CPU/deadline | No live callback deadline authorized | Offline structural checks only | No real-time promotion | Deferred |
| JUCE | Exact repository-authenticated 8.0.15 source | `research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json` | No fetch; private prototype build | Available prerequisite to authenticate |
| Third-party DSP | None enters Core | Complete diff and notices | Original implementation only | Ready decision |
| JUCE licence | Private local development follows accepted ADR 0016 posture | [JUCE 8 licence](https://juce.com/legal/juce-8-licence/) | Distribution is a separate legal/product gate | Deferred for distribution |
| CDP licence | CDP8 is LGPL-2.1-or-later | [CDP8 repository](https://github.com/ComposersDesktop/CDP8) | No CDP source or binary enters artifact | Not applicable to Core bytes |

## 11. Minimal experiment

### Central hypothesis

A correlated, field-bounded motion policy plus finite tuple recurrence will
produce objectively local and repeating fragment decisions while an optional
modal body adds decaying energy without erasing the source or violating fixed
real-time work bounds.

### Smallest vertical slice

One mono rolling capture, deterministic internal/external source, Hover and
Drunk, an eight-tuple recurrence store, four windowed voices, six original body
modes, stereo safety mix, fixed state/actions, and a thin standalone host.

### Test signals and gestures

- Silence and exact-zero source.
- A deterministic 110/173 Hz two-tone with impulses every 0.5 seconds.
- DC `0.25`, 997 Hz sine at `0.5`, deterministic white noise at `0.2`, and one
  impulse for body decay.
- Capture wrap beyond twice capacity; Freeze for two seconds; Clear during an
  active fragment; rapid Hover/Drunk and recurrence changes; full-range
  Anchor/Field/Wander/Body gestures; Reset and state recall.

| Field | Bound value |
|---|---|
| Sample rate and supported block sizes | 48 kHz canonical artifact; partitions 1, 17, 64, 127, 256, 511, 1024; additional property runs at 44.1, 88.2, and 96 kHz |
| Deterministic seed | `0x57414E4445523031` (`WANDER01`) |
| Event/sample timeline convention | Absolute zero-based frames; controls/actions apply before addressed sample; renderer feeds identical semantic schedule under every partition |
| Literal condition IDs and count | 10: `WB01_HOVER`, `WB02_DRUNK`, `WB03_LOCKED`, `WB04_SHUFFLED`, `WB05_MUTATED`, `WB06_BODY`, `WB07_FREEZE_CLEAR`, `WB08_EXTREMES`, `WB09_SILENCE`, `WB10_UNCORRELATED` |
| Falsifying comparator condition | `WB10_UNCORRELATED`: independent uniform positions over the same field/history size with body bypassed |
| Output names and kinds | Per condition: `audio.wav`, `decisions.json`, `metrics.json`; matrix: `manifest.json` |
| Objective tolerances | finite count `0`; peak `<0.98`; absolute DC mean `<=0.0025` except pre-DC input fixture; Hover launch positions inside field; Drunk delta lag-1 correlation `>=0.30`; comparator `abs(correlation)<=0.15`; Locked exact cycle; Shuffled tuple-set equality; Mutated normalized tuple distance `(0,0.25]`; body tail energy after 250 ms `> bypass` and after 4 s `< first-second energy`; repeat/partition decision JSON byte-identical |
| Artifact retention policy and location | Canonical 48 kHz/127-frame condition artifacts and canonical manifest retained under `research/prototypes/wanderbody/results/`; other matrix outputs reproduced under `build/wanderbody-evidence/` and not retained |

### Measurements

- Decision count, min/max position, field violations, mean/maximum step,
  lag-1 step correlation, unique tuple count, lock-cycle mismatches, shuffled
  set difference, mutated tuple distance, invalid reads, steals/drops.
- Audio peak, RMS, mean/DC, non-finite count, exact-silence bytes, body energy in
  early/mid/late windows, and left/right difference.
- State acceptance/rejection, process allocation count, capacity bytes, and
  semantic hashes across block partitions.

### Listening protocol

Deferred. A later test should randomize paired 30-second renders of correlated
Drunk versus uncorrelated positions and body versus bypass, then ask whether the
gesture stays related to the source, recurrence is recognizable, and the body
adds rather than masks identity. No subjective threshold is used to promote
revision 0.1.

### Stop or pivot conditions

- Stop before DSP if proposal/bundle readiness or governance validation fails.
- Pivot if Drunk cannot exceed the correlation threshold without spending more
  than 20% of decisions at a boundary, or if Hover leaves its declared field.
- Remove the body from the slice if it cannot remain bounded and source
  preserving under the frozen mix; do not hide a core-motion failure with body
  sound.
- Stop at host-signal/target-build if app launch, endpoints, callback timing,
  listening, or distribution would be needed for the next claim.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Design/source boundary is explicit | Proposal and new-design equivalence rationale validate | Proposal | Pending implementation bundle | `contract-r01/` |
| Core state and work are bounded | Unit/property, allocation, state, capacity, failure tests | Host structural | Pending | `wanderbody_core_tests` |
| Motion and recurrence meet declared invariants | Decision traces and comparator metrics | Host signal | Pending | `results/*/decisions.json`, `manifest.json` |
| Audio is finite, bounded, deterministic, and body is source-preserving | Render matrix, block partition comparison, signal metrics | Host signal | Pending | `render_evidence.py` outputs |
| JUCE accepts the app target | Authenticated Release configure/build and executable hash | Target build | Pending | isolated build receipt |
| Callback deadline and lifecycle are safe | Named live configuration with timing/allocation/xrun evidence | Real-time | Deferred | Separate task required |
| Audio/MIDI devices and controls work | Authorized endpoint/device session | Connected device | Deferred | Separate task required |
| Wanderbody is musically convincing | Documented listening protocol | Listening | Deferred | Separate task required |
| It is a Schuss/release product | Canonical/provider/packaging/licence gates | Production integration | Deferred | Separate task required |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/wanderbody/contract-r01/`
- Proposal fingerprint and approval reference: generated from these frozen
  bytes; approval is the user's 2026-08-25 `implement it` message.
- `validate_implementation_bundle.py --phase ready`: must pass before DSP edits.

### Files expected to change

- `docs/tasks/048-wanderbody-standalone-first-playable.md` and current routing
  while active, followed by status/history/result closure.
- `research/proposals/wanderbody-standalone-r01.md` (frozen after bundle
  generation).
- New files only under `research/prototypes/wanderbody/`, plus a narrow
  validation-manifest entry only if repository policy requires one.

### Focused tests

- Ready-bundle validation.
- CMake Core/state/allocation/property tests.
- Objective render matrix and comparator.
- ASan/UBSan run.
- Authenticated JUCE configure/build/test without launch.

### Adjacent regression tests

- Instrument Lab Core tests and `validate_prototype.py` for this consumer.
- No unrelated instrument DSP regression is justified because no shared DSP or
  source package changes.

### Expensive or hardware checks

- One relocated Core-only reproduction after freeze.
- One authenticated JUCE build if the exact local prerequisite exists.
- Schuss `current` once after freeze.
- No compatibility/release replay, endpoint, hardware, or app launch.

### Deferred work

File import, landmarks, richer body/interaction, MIDI learn, controller map,
captured-audio persistence, live deadline profiling, device lifecycle,
listening, packaging, distribution, canonical promotion, plug-ins, and embedded
targets.

### Dependency contract

| Dependency | Exact authority | Allowed use | Download policy | Licence/notice boundary |
|---|---|---|---|---|
| Instrument Lab | Repository-owned bytes at Task 048 baseline plus inherited dirty work preserved | CMake warnings/authenticated-JUCE helper and renderer hash utilities | Local only | Project-owned; does not own musical DSP |
| JUCE | 8.0.15 tree authenticated by `juce-8.0.15-source-tree.json` | `juce_audio_basics`, `juce_audio_devices`, `juce_core`, `juce_events`, `juce_graphics`, `juce_gui_basics`, `juce_audio_utils` for the standalone | Fetch OFF; operator-supplied exact local tree only | Private prototype build under accepted ADR 0016 posture; distribution licence review required |
| CDP/Mutable references | Direct documentation and pinned source URLs only | Research and behavioral comparison | No code download/build required | No bytes enter build; preserve attribution in proposal/notices |

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Source type | Notes or proof gap |
|---|---|---|---|---|---|
| WB-C01 | EVIDENCE | CDP documents Hover as local zig-zag/polarity-style source examination and Drunk as random source traversal | [CDP EXTEND](https://www.composersdesktop.com/docs/PDF/extend.pdf), [CDP BLUR](https://www.composersdesktop.com/docs/PDF/blur.pdf) | First-party documentation | Exact CDP sequence/equivalence is excluded |
| WB-C02 | EVIDENCE | Marbles recycles past random choices, locks a loop, and permutes familiar choices | [Marbles manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/manual/) | First-party manual | Tuple schema/mutation are Wanderbody-owned |
| WB-C03 | EVIDENCE | Modal synthesis can be implemented as a parallel bank of second-order modes | [Smith, Modal Expansion](https://www.dsprelated.com/freebooks/pasp/Modal_Expansion.html) | Authoritative technical text | Does not define a unique physical object |
| WB-C04 | EVIDENCE | Rings exposes modal structure, brightness, damping, position, and excitation behavior | [Rings manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/rings/manual/) | First-party manual | No Rings source/fidelity claim |
| WB-C05 | EVIDENCE | JUCE notifies callbacks before restarts and exposes current sample rate/block size | [JUCE callback docs](https://docs.juce.com/master/classjuce_1_1AudioIODeviceCallback.html) | Framework documentation | Build evidence is not live lifecycle evidence |
| WB-C06 | INFERENCE | Absolute source time plus valid interval prevents stale reads across ring wrap | Capture invariant and planned tests | Engineering inference | Must be falsified by wrap/clear/property tests |
| WB-C07 | HYPOTHESIS | Correlated Drunk motion is more locally coherent than independent uniform positions | Frozen WB02/WB10 comparator | Testable design claim | Objective correlation does not establish musical preference |
| WB-C08 | HYPOTHESIS | Tuple recurrence creates recognizable gesture identity | Frozen Fresh/Locked/Shuffled/Mutated traces | Testable design claim | Listening remains deferred |
| WB-C09 | HYPOTHESIS | Six original modes add a body without concealing source | Frozen body/bypass energy and mix tests | Testable design claim | Subjective material character remains deferred |
| WB-C10 | UNRESOLVED | Eight seconds, four voices, eight tuples, and six modes are good product defaults | Profiling/listening not yet performed | Open product decision | Values are centralized provisional configuration only |

## 15. Open questions and decision gate

### Open questions

- Whether the product is input-first or gives equal prominence to its exciter.
- Whether capture becomes continuous, explicitly armed, or switchable.
- Whether Hover/Drunk remain modes or become a morph after listening.
- Whether pitch remains varispeed-linked, becomes independent, or quantized.
- Whether landmarks, interaction, richer body models, more voices, and
  captured-audio persistence earn their complexity.
- Supported OS/configuration, accessibility, packaging, and licence path.

None is allowed to become a stable public contract in revision 0.1.

### Recommendation

Implement the exact original vertical slice above as a noncanonical Instrument
Lab consumer. Use semantic traces and an uncorrelated comparator to prove the
motion/recurrence mechanism before investing in file workflows or richer UI.
Keep the body parallel, six-mode, and removable.

### Approval requested

Already supplied for uninterrupted execution by the user's 2026-08-25
`implement it` message. That approval binds proposal revision 0.1 and the
generated SHA-256, the macOS arm64 JUCE 8.0.15/portable C++17 target, the named
host-signal and unlaunched target-build artifacts, the
`research/prototypes/wanderbody/contract-r01/` bundle, and the explicit ban on
real-time, endpoint/device, listening, distribution, and production promotion.

## 16. Implementation record

### Proposal revision implemented

Revision 0.1; exact SHA-256 is owned by the generated implementation contract.

### Source and test artifacts

Pending in `research/prototypes/wanderbody/contract-r01/RESULTS.md` and the
prototype index. This proposal remains byte-frozen after bundle generation.

### Commands and results

Pending in the bundle results ledger.

### Deviations

Pending; any implementation correction must be recorded without rewriting the
approved proposal fingerprint.

### Remaining proof gaps

Real-time callback deadline/lifecycle, app launch, physical audio/MIDI devices,
listening, persistence/product defaults, packaging/licensing, distribution,
canonical identity, and production integration are deliberately open.
