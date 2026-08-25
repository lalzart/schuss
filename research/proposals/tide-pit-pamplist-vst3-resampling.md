# Tide Pit and Pamplist Fixed-Rate VST3 Resampling

> Status: proposed; uninterrupted implementation authorized by the user's
> 2026-08-25 request, "Sounds good. Let's go ahead and implement this."
> Proposal revision: 0.1
> Work type: source-reimplementation
> Original request: Add internal high-quality sample-rate conversion to the
> Tide Pit and Pamplist private VST3 instruments so Ableton can run them at
> common host sample rates while both musical Cores remain exactly 48 kHz.
> Implementation target: one shared JUCE-independent fixed-rate stereo adapter
> used only by the existing macOS arm64 Tide Pit and Pamplist VST3 wrappers.
> Decision gate: this proposal and its implementation bundle must be ready
> before DSP-facing edits. Uninterrupted authorization waives only the approval
> pause, never readiness.

## 1. Port thesis and identity

### One-sentence thesis

Preserve Tide Pit and Pamplist as exact 48 kHz instruments while adding one
bounded causal sample-rate and timeline adapter outside both Cores so their
private VST3s can follow common Ableton host rates without changing musical
speed, pitch, event order, parameters, state, or controller meaning.

### Identity to preserve

- **EVIDENCE:** Tide Pit's accepted Core is Q27, fixed at 48,000 Hz and
  sixteen-frame source quanta, with its own gesture/event quantization.
- **EVIDENCE:** Pamplist's accepted Core is Q27, fixed at 48,000 Hz, accepts
  host chunks no larger than 512 frames, and applies coherent control values at
  its own internal Macro Voice quantum boundary.
- **EVIDENCE:** Tasks 045 and 046 already prove exact 48 kHz VST3-to-Core PCM,
  state, MIDI, allocation, module-host, and uninstalled target-build behavior.
- **EVIDENCE:** Both VST3s are zero-audio-input, stereo-output MIDI instruments,
  so this task requires output conversion only.
- **INFERENCE:** A shared output-only converter can preserve both identities if
  the 48 kHz lane remains a direct bypass and MIDI time conversion is performed
  by the same exact rational clock that advances source audio.

### Working definition and evidence level

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Shared fixed-rate adapter | host structural and host signal | Exact rational timeline, bounded FIR, latency, numeric, partition, and allocation tests pass | Either instrument or Ableton works |
| Tide Pit and Pamplist processor suites | host signal | Existing 48 kHz exact parity remains and declared multi-rate fixtures meet tolerances | Callback deadline or listening quality |
| Built `Tide Pit.vst3` and `Pamplist.vst3` | target build | Each actual arm64 module scans, instantiates, reports latency, recalls state, and renders at 44.1, 48, and 96 kHz | Installation, Live behavior, physical MIDI, or distribution |

## 2. Scope and decision rights

### Goal and why

Remove the practical requirement that an Ableton set use 48 kHz merely to load
either private instrument. Ableton remains host-rate authority; the wrappers
translate to and from the unchanged 48 kHz source timeline.

### In scope

- Common host rates: 32,000; 44,100; 48,000; 88,200; 96,000; 176,400; and
  192,000 Hz.
- Exact direct bypass with zero added latency at 48 kHz.
- Causal, fixed-capacity, phase-normalized 129-tap Kaiser-windowed sinc output
  conversion at the other six rates.
- Exact reduced rational phase and cumulative source-frame accounting.
- Integer host latency reported through the existing JUCE processor.
- Host MIDI offsets mapped monotonically to source frames without applying an
  event earlier than its host timestamp; equal mapped frames retain order.
- A maximum non-bypass callback of 8,192 host frames with deterministic-silence
  failure above the bound.
- Reset/reprepare/state-recall resampler-history rules and updated truthful
  status text.
- Shared converter tests plus both instrument integrations and affected build,
  module-host, sanitizer, regression, and reproduction evidence.

### Out of scope

- Changes to either musical Core, source dependency, seed, equation, default,
  parameter, state schema, gesture, controller map, accepted-state UI rule, or
  retained 48 kHz oracle.
- Audio input, arbitrary or continuously changing ratios, time stretching,
  pitch shifting, host-tempo synchronization, oversampling inside a Core, or
  native multi-rate Cores.
- A generic plug-in SDK/runtime/provider/catalog service, new formats or
  platforms, installation, Ableton launch, endpoint/device work, listening or
  real-time promotion, packaging, signing, notarization, or distribution.
- Git, publication, upstream/configured-source mutation, or unrelated inherited
  Task 043-046 changes.

### Inputs and deliverables

Inputs are Task 045 and Task 046's frozen proposals, ready bundles, exact VST3
processor seams, source authorities, direct comparators, authenticated JUCE
8.0.15 manifest, ADRs 0016-0018, and Instrument Lab contracts.

Deliverables are:

1. This proposal and `research/prototypes/vst3-resampling/contract-r01/`.
2. One narrow `FixedRateStereoResampler` in Instrument Lab prototype support.
3. Focused converter tests and instrument-specific multi-rate processor tests.
4. Tide Pit and Pamplist VST3 integration without parameter/state changes.
5. Two authenticated, uninstalled arm64 Release modules and exact results/gaps.

### Acceptance tests

1. Every source and proposal fingerprint in sections 3 and 8 authenticates and
   the Task 047 bundle passes readiness before implementation.
2. Only the seven declared host rates prepare; 48 kHz is direct and reports
   zero latency; every other rate uses the FIR and reports deterministic
   positive integer latency.
3. For absolute host frame `H`, cumulative internal frames equal
   `ceil(H * 48000 / F_host)` independently of callback partitioning.
4. At 48 kHz both complete existing exact VST3 processor suites pass unchanged
   at the PCM/event/state boundary.
5. At every other declared rate, both processors emit finite bounded nonzero
   stereo output, preserve source progress and event order, reset
   deterministically, and remain instance-isolated.
6. Converter DC error is at most `2e-5`; a 1 kHz sine is within `0.05 dB`; an
   18 kHz sine converted to 44.1 kHz is within `0.35 dB`; and a 23 kHz input
   converted to 44.1 kHz is below `-70 dBFS` after transient exclusion.
7. A deliberately unfiltered linear converter fails the 23 kHz alias threshold.
8. Identical timelines partitioned by the declared block matrix produce exact
   source counts, event mappings, and equal output after the latency convention.
9. Processing owns no heap allocation or lock; invalid rates/layouts and
   callbacks above 8,192 host frames clear output and increment bounded failure
   diagnostics.
10. Actual modules pass scan/instantiate/state/editor/render at 44.1, 48, and
    96 kHz; source/host/target/real-time/device/listening/release claims remain
    independent.

### Decisions this work may make

- Converter API, declared rate list, FIR/window/cutoff, rational clock, latency,
  capacities, reset history, failure behavior, tests, and task-local receipts.
- The smallest processor branches and sample-offset translations needed for
  the two existing wrappers.

### Decisions this work must not make

- New musical semantics, Core-native multi-rate support, state migration,
  controller remapping, source correction, canonical identities, provider or
  runtime promotion, or any higher evidence claim.
- Installation, app launch, endpoints, devices, dependency installation, Git,
  distribution, or publication actions.

## 3. Source authority and lineage

The observed repository revision is `982ded194526f2fbe7e392ae070062df701c34f2`
on `main`. The working tree contains the accepted but uncommitted Tasks 043-046
and unrelated inherited changes. Task 047 owns only the files named by its task
contract and must preserve all other bytes.

| Portable source ID | Revision | Dirty-state scope | Authority | Forbidden mutations |
|---|---|---|---|---|
| `schuss-tide-pit-vst3-task046` | Task 046 frozen bundle | Untracked accepted VST3 subtree | Task 046 proposal, bundle, source lock, and exact processor tests | Tide Pit Core, source lock, oracle, controller map, parameter/state meaning |
| `schuss-pamplist-vst3-task045` | Task 045 frozen bundle | Untracked accepted VST3 subtree plus inherited Task 043/044 Pamplist work | Task 045 proposal, bundle, configured source verifier, and exact processor tests | Pamplist Core, configured source, canonical Task 043 records, controller map, parameter/state meaning |
| `schuss-instrument-lab-v1` | current repository revision | Existing shared prototype support | Accepted workflow and `SchussInstrumentLab::Core` boundary | Canonical runtime/provider/catalog semantics or unrelated consumers |

| Relative path | SHA-256 | Role | License and notice |
|---|---|---|---|
| `research/proposals/tide-pit-vst3-local.md` | `841f77bdf4a0e2cc9b8301178a95ced9f18641629cf58aff560eaa40b4be0fd5` | normative predecessor proposal | Project documentation |
| `research/proposals/pamplist-vst3-local.md` | `125826a47e649bc91d757d62d7b2a1543238769614c9b5f8b843c819291ee650` | normative predecessor proposal | Project documentation |
| `research/prototypes/tide-pit-gills/contract-vst3-r01/implementation-contract.json` | `ce25996044cbc4a236ed42e0b7d3777fe997b9c0f1d20b8a7fc2a93e531816a8` | normative predecessor approval | Project contract |
| `research/prototypes/tide-pit-gills/contract-vst3-r01/source-equivalence.json` | `8d5a846c17ab5cfffaa9d21a70bbc81abf9fff9e5eba19247cc6da51f8dae32f` | normative source authority | Project contract plus referenced notices |
| `research/prototypes/pamplist/contract-vst3-r01/implementation-contract.json` | `c5bf038aec7f9eb1f6d1a683afbeb18b73e9850d61a41d86cba2113d17a31c3c` | normative predecessor approval | Project contract |
| `research/prototypes/pamplist/contract-vst3-r01/source-equivalence.json` | `69c2ca42956f88d46793351c288c061dc77330360bcfefb61f192cd23cdfa54e` | normative source authority | Project contract plus referenced notices |
| `research/prototypes/tide-pit-gills/vst3/include/tidepit/vst3_processor.hpp` | `750ea9a2abf84d53459425c8b4daccac98aac2be2d472588217dae42d48dc129` | normative host boundary | Project source; dependencies in Tide Pit notices |
| `research/prototypes/tide-pit-gills/vst3/src/vst3_processor.cpp` | `b14df5a7e8e217e1a2385db15bd8756967dbdf98e3166c962b2c3660145d3232` | normative host behavior | Project source; dependencies in Tide Pit notices |
| `research/prototypes/pamplist/vst3/include/schuss/pamplist/vst3_processor.hpp` | `1ee992180606dd2f793f7ade73068998551110a30b7e0ff3640860bd601bc232` | normative host boundary | Project source; dependencies in Pamplist notices |
| `research/prototypes/pamplist/vst3/src/vst3_processor.cpp` | `11224b9f74d8b915c1d2d6f2d7e7d0c1f00a1cf6ace173039295f5bd66ae48e2` | normative host behavior | Project source; dependencies in Pamplist notices |
| `research/prototype_support/instrument_lab/include/schuss/instrument_lab/host_bridge.hpp` | `42264a6bb948cc5d08e289ac185949b8439cacc4e2eb7e7829d025c506b56a04` | supporting reuse seam | Project source |
| `research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json` | `db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5` | supporting dependency authority | JUCE commercial/AGPLv3 and bundled VST3 SDK notices |

## 4. Dependency and license closure

| Dependency | Exact revision/files | License | Authentication | Distribution disposition |
|---|---|---|---|---|
| Tide Pit and Mutable closure | Existing Task 046 source-equivalence contract and `SOURCE_LOCK.json` SHA-256 `52a13c11dbd81df05a3590d2aaa5cf1efc95bdddcc874d69cf6961c18de61a02` | Tide Pit MIT; reviewed Mutable notices | Existing source-lock and exact oracle checks | Private uninstalled build; unchanged |
| Pamplist Macro Voice and Plaits closure | Existing Task 045 source-equivalence contract and `source-dependencies.json` SHA-256 `d7b82c51046bf96d68b726eba1ebbfc989e0d03fc4daab47f4e71f6fd71f5c38` | GPL-3.0-or-later wrapper; MIT Plaits/stmlib | Existing configured source verifier | Private uninstalled build; unchanged |
| Instrument Lab | Current repository-owned C++17 support | Project source | Repository path and focused tests | Prototype-only shared utility |
| JUCE 8.0.15 and bundled VST3 SDK | Authenticated 4,425-file manifest | JUCE commercial/AGPLv3 plus bundled notices | Exact local manifest validator | Private uninstalled build; redistribution unresolved |

No new third-party dependency is introduced. The FIR and rational clock are
project-authored from the equations frozen below.

## 5. Source behavior contract

### Signal flow

```text
host block N at F_host
  -> existing host parameter snapshot and raw MIDI order
  -> B(H) = ceil(H * 48000 / F_host) source timeline
  -> instrument-owned 48 kHz renderer
       Tide Pit: existing 16-frame Q27HostBridge
       Pamplist: existing at-most-512-frame Core calls
  -> fixed-capacity stereo source history
  -> causal phase-normalized FIR at F_host
  -> exactly N stereo host samples
```

At 48 kHz the FIR/history path is not called; existing processors render
directly to the JUCE output buffer.

### Parameters, defaults, and curves

All existing Tide Pit and Pamplist parameter IDs, order, domains, defaults,
quantization, desired/accepted semantics, one-shots, and JUCE service parameters
are `preserve`. Task 047 adds no parameter and changes no state bytes.

### State, timing, randomness, and buffers

Let `F_s = 48000`, `F_h` be one declared integer host rate,
`g = gcd(F_s, F_h)`, `p = F_s/g`, and `q = F_h/g`.

- Cumulative source boundary at absolute host frame `H`:
  `B(H) = ceil(H*p/q)`.
- A host event at absolute frame `E` applies before source frame `B(E)`, never
  before its host timestamp. Events sharing `B(E)` retain ingress order.
- Non-bypass block source count is `B(H+N)-B(H)`.
- Filter half support is 64 source samples; the declared causal design delay is
  `D=65` source samples.
- Reported latency is `L_h = ceil(D*q/p)` host samples. The resampling center
  for host frame `H` is `x=(H-L_h)*p/q`.
- The 129 source sample indices surrounding `x` are `floor(x)+j` for
  `j=-64..64`.
- Non-bypass buffers are fixed for at most 8,192 host frames and the maximum
  declared source/host ratio of 3/2.

Reset, reprepare, and accepted state recall clear FIR history, restart the
rational phase at zero, and therefore produce the declared initial latency
transient. Randomness remains wholly Core-owned and returns to each existing
fresh-Core rule.

### Gestures, modes, display, and feedback

Tide Pit retains its semantic event queue and sixteen-frame gesture schedule.
Pamplist retains its raw CC adapter and control acceptance schedule. Both UIs
continue to reflect accepted Core state. Status text may report `48 kHz Core`,
active host rate, and resampling/bypass state; it may not imply Live, endpoint,
or real-time evidence.

### Platform and numeric assumptions

- C++17, IEEE-754 binary32 samples and binary64 coefficient construction.
- Integral declared rates; exact reduced rational phase, no floating phase
  accumulator.
- `sinc(z)=sin(pi*z)/(pi*z)` and `sinc(0)=1`.
- Kaiser parameter `beta=8.6`, window radius `65`, 129 taps.
- Cutoff in source cycles/sample:
  `f_c = 0.475 * min(1, F_h/F_s)`.
- For fractional source center `r` and tap offset `j`, define `d=r-j` and
  `w(d)=I0(beta*sqrt(1-(d/65)^2))/I0(beta)` for `|d|<=65`, else zero.
- Raw coefficient:
  `a_j=2*f_c*sinc(2*f_c*d)*w(d)`.
- Each exact rational phase is normalized once in preparation:
  `h_j=a_j/sum(a_k)`, then rounded to binary32.
- Runtime accumulates each stereo convolution in binary64 and rounds once to
  binary32 output.

### Known source quirks

- Tide Pit's gesture/event changes remain quantized by its existing source
  bridge rather than becoming host-sample continuous.
- Pamplist's authenticated Macro Voice signed-shift sanitizer finding remains
  retained; resampling does not rewrite the source.
- Fresh state recall does not serialize either Core's evolving audio/timeline
  state and now also clears wrapper FIR history.

## 6. Fidelity matrix

| Behavior or subsystem | Classification | Equivalence rule | Evidence |
|---|---|---|---|
| Tide Pit and Pamplist Cores | preserve | No Core source or numeric constants change | Source hashes and adjacent suites |
| 48 kHz VST3 audio/events | preserve | Existing exact PCM and accepted-state comparisons remain exact | Existing processor suites rerun |
| Non-48-kHz host support | allowed change | Declared rates render the same 48 kHz source timeline through the frozen FIR | Multi-rate signal/timeline tests |
| Unsupported host rates | preserve/focused change | Still exact silence; declared supported set expands only to seven rates | Negative processor tests |
| MIDI timing | preserve in time | Never early; exact rational mapping; equal-frame order retained | Mapping and boundary tests |
| Parameter/state schema | preserve | Exact descriptor/state fingerprints unchanged | Existing state/model tests |
| Reset/recall output transient | intentional deviation | FIR history clears and output restarts with reported latency | Fresh-twin and impulse tests |
| UI scope time base | allowed host presentation change | Scope consumes final host samples; musical accepted state remains Core authority | Editor/status tests |
| Real-time and listening | exclude | No claim | Deferred Live gates |

## 7. Port seams and architecture

| Source seam | Portable adaptation | Capacity or timing | Failure behavior | Test |
|---|---|---|---|---|
| Host/source clock | Exact `p/q` boundary helper | 64-bit counters; seven rates | Invalid rate or overflow fails prepare/process | Long-count and partition tests |
| Stereo conversion | 129-tap phase bank plus ring history | At most 147 phases and 8,192 host frames | Invalid plan/history clears output | DC, sine, impulse, alias tests |
| Tide Pit renderer | Existing `ParameterizedQ27HostBridge` into source scratch | Existing 16-frame quanta | Existing bounded event drops plus processor failure | Direct and multi-rate MIDI tests |
| Pamplist renderer | Existing Core into source scratch in chunks <=512 | Existing fixed Q27 scratch | Existing process failure plus silence | Direct and multi-rate MIDI tests |
| JUCE lifecycle | `prepareToPlay`, reset, latency report | Coefficients built only outside callback | Unsupported layout/rate stays unprepared | Lifecycle/module tests |

### Portable Core boundary

Neither Core receives `F_h`. Both continue to see an uninterrupted 48 kHz
sample sequence and existing control structures. The converter is a host
adapter, not a DSP graph node or implementation provider.

### Renderer and reference boundary

The strongest 48 kHz oracle remains exact direct-Core comparison. At other
rates the independent comparators are closed-form DC/sine/impulse expectations,
exact rational sample/event accounting, and a deliberately unfiltered linear
converter that must fail the high-frequency alias gate.

### Host, MIDI, controller, and UI boundary

Raw MIDI remains JUCE-host input. Each processor owns musical mapping and uses
the shared clock only to translate host offsets. The shared adapter knows no
instrument parameters, gestures, state, MIDI bytes, UI, or endpoint.

## 8. Controller and UI reuse

| Reused artifact | Fingerprint | Reused mechanism | Instrument-specific replacement |
|---|---|---|---|
| Tide Pit Task 046 adapter | Processor header/source hashes in section 3 | Parameter, state, semantic MIDI, accepted UI | Only output/timeline seam gains resampled branch |
| Pamplist Task 045 adapter | Processor header/source hashes in section 3 | 179-state surface, controller adapter, accepted UI | Only output/timeline seam gains resampled branch |
| Instrument Lab HostBridge | `42264a6bb948cc5d08e289ac185949b8439cacc4e2eb7e7829d025c506b56a04` | JUCE-independent host support convention | Add sibling fixed-rate utility; do not alter HostBridge semantics |

The application UI continues to reflect authoritative accepted Core state.
Raw input remains diagnostic and never feeds duplicate events back.

## 9. Reference oracle

| Field | Bound value |
|---|---|
| Oracle kind | Exact 48 kHz direct-Core oracle plus analytic multi-rate signal/timeline invariants |
| Source fixtures and commands | Existing Tide Pit/Pamplist VST3 processor suites; new Instrument Lab converter suite; actual module suites |
| Sample rates and block sizes | Seven declared rates; 1, 16, 64, 127, 128, 511, 512, 513, 2,048, and 4,096 frames; negative 8,193 |
| Seed and event convention | Existing instrument seeds; event maps to `B(E)` and equal mapped events retain input order |
| Metrics and tolerances | Exact 48 PCM; exact counts/order; DC `2e-5`; 1 kHz `0.05 dB`; 18 kHz `0.35 dB`; 23 kHz at 44.1 below `-70 dBFS`; finite bounded PCM |
| Retained outputs and hashes | Small deterministic test vectors and build receipts; long signal fixtures reproducible-only |
| Explicit proof limits | No Live callback, device, listening, packaging, or production proof |

## 10. Minimal experiment

### Primary bounded equivalence claim

For each declared host rate and host partition, the wrapper advances the exact
same 48 kHz Core timeline, maps events without early application, and emits a
band-limited delayed representation while leaving the exact 48 kHz path
unchanged.

### Conditions and comparator

- Render deterministic stereo constant, impulse, 1 kHz, 18 kHz, and 23 kHz
  source signals through the shared adapter.
- Render deterministic Tide Pit and Pamplist programs through 44.1, 48, 96,
  and the remaining declared processor rates.
- Compare cumulative source counts and mapped events under one-block and
  repartitioned timelines.
- Compare 23 kHz downsampling against an intentionally unfiltered linear
  converter; the latter must fail the alias threshold.

### Signals, gestures, and extremes

Initial silence, impulse, DC, low and high sine, unsupported rate, zero and
8,193-frame blocks, reset, state recall, equal-frame MIDI, event at first/last
host frame, repeated blocks, and two independent instances.

### Objective measurements

Latency peak location, steady DC gain, sine RMS gain, stopband alias RMS,
finite/bounded output, exact source/event counts, exact 48 parity, allocation
count, module metadata, and build authentication.

### Listening protocol

Deferred. A later authorized Live session should compare 44.1, 48, and 96 kHz
for pitch, transient, high-frequency character, automation, recall, layering,
CPU, and xruns. No offline comparator substitutes for that judgment.

### Stop or pivot conditions

Stop before integration if readiness fails. During implementation, stop or
revise the frozen design if 48 kHz exact parity drifts, the FIR misses the
signal thresholds, event mapping depends on callback partition, process
allocates/locks, or the declared capacities are insufficient for the actual
module-host fixtures.

## 11. State-operation summary

- Initialization/reprepare: authenticate supported rate, compute the phase
  bank outside processing, clear history/counters, set latency, then request
  the existing fresh Core transition.
- Reset/state recall: retain existing requested parameter state, create/reset
  the existing fresh Core, clear converter history and timeline, and restart
  the declared latency transient.
- Panic/release: preserve each existing Core rule and mark the wrapper
  unprepared; history becomes non-observable until prepare.
- Freeze/capture and Clear: instrument-owned one-shots remain unchanged and are
  never serialized by the converter.
- Mode change: existing desired/accepted rules; only timestamp translation is
  new outside the 48 kHz bypass.
- Disconnect/reconnect: N/A for the plug-in, because Ableton owns endpoints;
  reprepare follows initialization.
- Non-finite recovery: coefficient preparation rejects invalid rates; runtime
  non-finite samples are counted by existing Core paths and adapter output must
  remain finite or fail the block to silence.

The implementation bundle owns the complete state matrix and defines reset
equality as fresh-Core plus zeroed converter history/counters and equal output
under the same host-rate timeline.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Frozen authorities are exact | Ready validator and existing source verifiers | source | planned | Task 047 bundle |
| Shared clock/FIR is bounded and correct | Focused converter suite | host structural/signal | planned | Instrument Lab tests |
| 48 kHz behavior is unchanged | Existing exact processor suites | host signal | planned | Both VST3 tests |
| Declared rates work offline | Multi-rate processor suites | host signal | planned | Both VST3 tests |
| Actual modules expose behavior | Module scan/state/editor/render | target build | planned | Two Release bundles |
| Callback deadline is safe | Authorized Live timing session | real-time | deferred | Later evidence |
| Physical controller route works | Authorized Live/device session | connected device | deferred | Later evidence |
| Conversion sounds acceptable | Structured audition | listening | deferred | Later evidence |
| Redistribution is ready | License/sign/package review | production integration | deferred | Later contract |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/vst3-resampling/contract-r01/`
- Proposal fingerprint and approval reference: filled after this proposal is
  frozen; approval is the user's 2026-08-25 uninterrupted implementation request.
- Source root is runtime-only and not stored in durable artifacts.
- `validate_implementation_bundle.py --phase ready --source-root ...`: not run.

### Expected files and stages

1. Freeze proposal fingerprint and ready bundle.
2. Add shared header/source tests without changing consumers.
3. Pass converter signal/timeline tests.
4. Integrate Tide Pit while retaining the 48 kHz direct branch.
5. Integrate Pamplist through the same converter API and its own renderer.
6. Add multi-rate allocation/module checks and update status text.
7. Freeze, run proportional validation, update results/gaps, and inspect diff.

### Focused and adjacent tests

Instrument Lab core tests; both VST3 model/processor/allocation/module suites;
both existing Core/control/UI/MIDI/render suites; source/JUCE authentication;
applicable sanitizers; `current`; selected compatibility; two reproductions.

### Expensive, device, and listening gates

Run each affected Release target and relocated reproduction once after freeze.
Do not install or launch Live, open endpoints/devices, or claim real-time or
listening evidence.

### Deferred production work

Canonical provider/runtime integration, broader host/plugin matrices,
distribution licensing, signing/notarization/package work, Live resource
budgets, physical MIDI, listening, and public release.

## 14. Intentional deviations

| Deviation | Why required | Musical/technical effect | Approval | Test |
|---|---|---|---|---|
| Replace non-48-kHz silence at six declared rates | User should not change Ableton rate | Delayed band-limited representation of exact 48 kHz Core | 2026-08-25 request | Multi-rate processor/module tests |
| Add nonzero latency outside 48 kHz | Causal FIR cannot use unknown future events | Host-compensable delay near 1.35 ms; 48 kHz remains zero | Same | Impulse and reported-latency tests |
| Clear FIR history on recall/reset | Fresh state must not leak pre-reset samples | Initial latency transient after reset | Same | Fresh-twin/reset tests |
| Non-bypass callback cap 8,192 | Fixed real-time storage and bounded work | Oversized callback is silence/failure | Same | Negative test |

## 15. Claim-to-source ledger

| ID | State | Claim | Source | Proof gap |
|---|---|---|---|---|
| SRC-001 | EVIDENCE | Both VST3s are exact 48 kHz output-only synth wrappers | Task 045/046 contracts and processors | No multi-rate behavior yet |
| SRC-002 | EVIDENCE | Existing 48 kHz PCM/event/state paths have exact offline comparators | Task 045/046 results | Not Live or listening proof |
| SRC-003 | EVIDENCE | JUCE's generic resampling source owns locks and may resize its buffer | Authenticated JUCE 8.0.15 local source inspection | Does not itself select this FIR |
| SRC-004 | INFERENCE | A project-owned fixed-capacity adapter is the smallest provable callback seam | Source boundaries and task constraints | Must pass allocation/signal tests |
| SRC-005 | HYPOTHESIS | The frozen 129-tap Kaiser design meets the declared passband/alias limits with acceptable offline cost | Executable equations and known FIR behavior | Must be falsified or confirmed by tests |
| SRC-006 | UNRESOLVED | Useful multi-instance count in Live | No real-time host measurements | Later Live gate |

## 16. Open questions and decision gate

### Open questions

- Real-time CPU and useful layered instance counts at 176.4/192 kHz remain
  unknown until an authorized Live measurement.
- Listening preference for the chosen transition band remains unknown.
- Host rates outside the seven common integral values remain deliberately
  unsupported until there is a concrete need.

### Recommended architecture

One narrow JUCE-independent `FixedRateStereoResampler` owns rational timing,
phase coefficients, source scratch, history, and output conversion. Tide Pit
and Pamplist keep separate musical render/event code. The 48 kHz processor lane
is left direct and exact.

### Approval reference

The user approved uninterrupted implementation on 2026-08-25 with, "Sounds
good. Let's go ahead and implement this." This authorizes proposal-to-source
continuation only after readiness; it does not authorize installation, app
launch, endpoint/device access, Git, publication, or distribution.

## 17. Implementation record

Complete only after readiness.

### Source and proposal fingerprints implemented

Pending.

### Commands and results

Pending.

### Deviations

Pending.

### Remaining proof gaps

Live, real-time, connected-device, listening, packaging, distribution, and
production integration remain deferred.
