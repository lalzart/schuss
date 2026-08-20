# Tide Pit Gills Portable JUCE Port

> Status: proposed
> Proposal revision: 0.2
> Work type: source-reimplementation
> Approval reference: the user's 2026-08-20 request for uninterrupted workflow improvement and Tide Pit reimplementation
> Implementation target: isolated 48 kHz C++17 reference Core, deterministic renderer, and pinned JUCE 8.0.15 standalone app
> Working artifact and evidence level: a built `Tide Pit Gills.app` plus deterministic host-signal evidence
> Decision gate: source and fidelity readiness are required before DSP edits. The approval pause is waived; readiness is not.

## 1. Port thesis and identity

### One-sentence thesis

Rehost the exact favorite Gills Tide Pit voice as a standalone desktop
instrument while preserving its four-stage gesture, feedback-body character,
granular memory, mutation, tuning, effects, and performance state.

### Identity to preserve

The performer shapes four continuously evolving stages. Tide Pit turns them
into a REED, RND, or FOLD source, sympathetic lower string, stereo eight-mode
body, two-second six-grain memory, diffusion tail, and CLEAN/FILT/DRIVE output.
Memory controls evolution; Lock, Mutate, Freeze, source, scale, wave target,
root, and contextual effect parameters remain musically distinct operations.

This is Tide Pit for Gills, not Cinderwheel, Tidepool, or a new derivative.
No Undertow, Pulse, Wake, Ember, Bloom, Reset, Panic, or Cinderwheel scale is
introduced.

### Working definition and evidence level

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Built `Tide Pit Gills.app`, portable Core library, reference renderer, and retained hashes | host-signal | Core/reference golden and render matrix pass; pinned JUCE app and adapter tests build | launched app, measured real-time safety, controller session, listening equivalence, plugin format, device, or Schuss production integration |

## 2. Scope and decision rights

### Goal and why

Test a repeatable existing-source-to-JUCE workflow on a loved, known instrument
with a real reference oracle, rather than designing another sound from scratch.

### In scope

- Exact Tide Pit and minimal MIT Mutable Instruments source closure.
- A 48 kHz, 16-frame internal reference engine with fixed owned storage.
- A semantic controller adapter and arbitrary JUCE host-buffer partitioning into
  16-frame internal quanta.
- Deterministic reference and objective renderers.
- A standalone JUCE GUI with physical MIDI input selection and authoritative
  Core-state reflection.
- Reuse of the regular Launch Control 3 channel/CC topology.

### Out of scope

- Canonical Schuss catalog, graph, provider, runtime, schema, or record changes.
- VST3/AU, preset/state serialization, resampling, multi-rate redesign, hardware
  flashing, Gills changes, and production distribution.
- Claims of measured real-time fitness, physical-controller feedback, device
  reconnection correctness, or listening equivalence.

### Inputs and deliverables

Inputs are the exact Gills source revision and hashes below, the exact Mutable
closure, the fresh source-bound CLEAN reference, Cinderwheel's proven host/MIDI mechanics,
the reusable controller topology, JUCE 8.0.15, and this approval.

Deliverables are this proposal, a ready implementation bundle, source and
dependency manifests/notices, portable Core, renderer, JUCE adapter/app,
focused tests, objective results, and an explicit gap register.

### Acceptance tests

- The source-bound 12,000-block CLEAN fixture is byte-identical on the canonical
  macOS build, or the port stops and records the first localized divergence.
- The Core remains 48 kHz/16-frame internally and gives invariant output across
  supported outer host partitions.
- Original discrete startup state, tuning/scale arrays, mutation, mode cycles,
  freeze, effect crossfade, and pickup behavior are tested.
- UI controls reflect accepted Core state; raw input remains diagnostic.
- Direct semantic events and adapted MIDI yield equivalent Core state/audio.
- Pinned JUCE standalone and reference renderer build without modifying the
  Gills or Ksoloti checkouts.

### Decisions this work may make

- Portable allocation, event queue, snapshot, UI layout, test-fixture, and
  CMake seams that do not change the source behavior.
- A clearly labelled desktop audition preset for otherwise unrecorded physical
  pot positions.
- Direct Launch Control gestures that synthesize the original Gills gestures.

### Decisions this work must not make

- Change source tuning, labels, DSP equations, timing, scale contents, defaults,
  mode memory, or source quirks without a frozen deviation.
- Treat an app build as a launch, listening result, real-time proof, device
  proof, or production integration.
- Modify, clean, stage, commit, or publish either external source checkout.

## 3. Source authority and lineage

| Portable source ID | Revision | Dirty-state scope | Authority | Forbidden mutations |
|---|---|---|---|---|
| `gills-instruments:tide-pit-gills` | target introduced at `53287e49e5bcc5fb0d73b546d88431f82467f969`; observed repository HEAD `33038b5de6315bce9bbe167062f2876823ff1adc` | target folder clean and unchanged; unrelated surrounding work exists | user-owned MIT source | external checkout remains read-only |

| Relative path | SHA-256 | Role | License |
|---|---|---|---|
| `projects/tide-pit-gills/LICENSE.md` | `2701d4f24dfe91723d1d43103daa123e8be61e53ad09f142735c91f58a06baac` | normative | MIT, Lance Ship |
| `projects/tide-pit-gills/README.md` | `be3a5174d13f03fc02faff57b9afa3275faf34b3210850c7f50b219fdad7b52a` | supporting | project documentation |
| `projects/tide-pit-gills/tidepit-gills.axp` | `35b8df83ffc06bacca1890d936525c75758b193bcf7ef7edd69082acdb7e963c` | normative control wiring | MIT project |
| `projects/tide-pit-gills/tidepit.axo` | `8e62fdfd1f6b101cb5b6f876d3d54538af8be9a04a46cddba2711eaabc3b9009` | normative adapter | MIT project |
| `projects/tide-pit-gills/tidepit_dsp.h` | `3f75a3aa337109e7de270cb4a4aa7281f71ba4de443f057b4e37299e3bd7b32e` | normative DSP | MIT, Lance Ship and attributed Mutable DSP |
| `projects/tide-pit-gills/tidepit_voice.h` | `e6cd224160df87afbfda5743c5124a4600c5f3c6fe4c02df272c41916cd6566c` | normative DSP | MIT, Lance Ship and attributed Mutable DSP |

The canonical sorted six-file manifest hash is
`6cbb9842a785c90f54de28e122487194c79868b4b5505f0ab26506836abaaa85`.

## 4. Dependency and license closure

| Dependency | Exact revision/files | License | Authentication | Distribution disposition |
|---|---|---|---|---|
| Ksoloti Mutable Instruments subset | Ksoloti revision `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`; 21-file Braids/Clouds/stmlib closure | MIT, Emilie Gillet | per-file hashes and sorted manifest `0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f` | vendor exact minimal files with notices |
| JUCE | commit `91ad83ae34a81e0833b1a2b0866f54846370ae53`, archive SHA-256 `04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70`, version 8.0.15 | JUCE license boundary retained for local trial | authenticated FetchContent archive or operator-authenticated local tree | local standalone trial only; distribution review deferred |

The GPL Gills display object is not copied. Four 21-character display strings
and stage LEDs are rendered independently from Tide Pit's MIT state.

## 5. Source behavior contract

### Signal flow

```text
root + scale + four-stage mutation
  -> REED / RND / FOLD
  -> sympathetic f/(2..5)
  -> gesture energy and low-pass gate
  -> stereo eight-mode body
  -> dry branch + two-second mono recorder
  -> six high-quality grains
  -> dry/grain mix
  -> Clouds diffusion reverb
  -> CLEAN / FILT / DRIVE
  -> SoftClip(x * 0.72) -> stereo
```

### Parameters, defaults, and curves

- Stage 1-4: normalized physical pots.
- Rate: `0.08 + 5.92*x^2` full cycles per second.
- Memory: automatic mutation on wrap when random `> memory^2`.
- Material, position, and contextual FX A/B follow the source equations.
- Root is MIDI 36-72 and initializes to 60.
- Discrete startup is C4, MAJ5, PIT, REED, CLEAN, EVOLVE, not frozen,
  stage 1, initial strike.
- The source has no canonical continuous-pot startup preset. The desktop
  audition preset is explicitly adapter-owned: stages .20/.50/.80/.30, rate
  .55, memory .78, material .50, position .31, CLEAN size .60, depth .35.

### State, timing, randomness, and buffers

- Exactly 48 kHz and 16 samples per source call.
- Effect debounce 75 blocks/25 ms; effect and encoder hold 1,500 blocks/500 ms;
  encoder debounce 8 blocks/2.667 ms.
- Effect crossfade is 1,024 samples; record-resume fade is 256 samples.
- Recorder is 96,000 plus eight tail samples, mono int16; six HQ grains.
- Requested external memory is 251,408 bytes before allocator alignment.
- stmlib's shared LCG begins at `0x21`; Tide Pit's mutation xorshift begins at
  `0x70697421`. The port saves/restores a compatible per-instance LCG stream.

### Gestures, modes, display, and feedback

Source next, manual mutate, and lock are rising edges. Effect tap advances
CLEAN/FILT/DRIVE; effect hold toggles capture. Encoder tap advances scales;
encoder hold advances PIT/BODY/GRAIN/ALL. Contextual FX controls remember values
and use a 0.015 crossing pickup threshold. The UI shows accepted values, four
source display lines, active stage, lock, capture, source, scale, and target.

### Platform and numeric assumptions

Q27 positive controls and int32 planar output form the reference boundary.
JUCE float output is normalized by `2^27`; source output already includes its
`126000000 / 2^27` level. Outer host blocks are buffered into exact internal
quanta. Unsupported sample rates fail closed.

### Known source quirks

- `RND` is a sine/triangle blend, not random noise.
- The scale labelled `HARM` is exactly `{0,3,5,7,10,12}`; the label/interval
  mismatch is preserved.
- There is no authoritative physical-pot startup state.
- Cross-platform floating-point byte identity is not assumed.

## 6. Fidelity matrix

| Behavior or subsystem | Disposition | Equivalence rule | Evidence |
|---|---|---|---|
| DSP algorithms, lookup tables, 48k/16 timing, Q27 boundary | preserve | canonical macOS source-bound byte equality | fresh zero-BSS reference plus focused tests |
| Controls, scales, modes, pickup, mutation, freeze, display strings | preserve | exact state/event trace | Core tests and snapshots |
| Ksoloti `sdram_malloc` | allowed change | same allocation order/capacity and successful initialized state | fixed-arena tests |
| Global stmlib RNG ownership | allowed change | identical single-instance sequence; independent instances | golden and interleaving tests |
| Gills button/encoder hardware glue | allowed change | same semantic operation and source timing through synthetic gestures | adapter parity tests |
| Physical ADC jitter, headphone gain, OLED driver | exclude | not modelled | explicit gap |
| Non-48-kHz behavior and preset serialization | exclude | fail closed | negative tests |

## 7. Port seams and architecture

| Source seam | Portable adaptation | Fixed capacity/timing | Failure behavior | Test |
|---|---|---|---|---|
| `BUFSIZE=16` | immutable reference quantum behind outer block adapter | 16 samples | unsupported partial state retained until next quantum | partition matrix |
| `sdram_malloc` | prepare-time monotonic owned arena | bounded above audited allocation | prepare fails closed and outputs silence | allocation exhaustion |
| global BSS instance | explicitly zeroed owned storage and placement construction before `Init` | one owned instance | deterministic reset/reprepare | source-bound reference/reprepare |
| stmlib global LCG | thread-local save/restore around one instance | one uint32 state per Core | independent instances; no lock | interleaving parity |
| raw Gills controls | timestamped semantic events plus gesture synthesizer | fixed queue | ignore/count overflow or invalid event | adapter tests |
| display pointers | immutable state snapshot/mailbox | fixed strings | last complete snapshot retained | UI/state tests |

## 8. Controller and UI reuse

| Reused artifact | Fingerprint | Reused part | Instrument-specific replacement |
|---|---|---|---|
| `research/prototype_support/controllers/novation-launch-control-3-regular-v1.json` | bound in implementation bundle | channel 16, CC20-35 encoders, CC40-47 buttons, topology | Tide Pit labels, mappings, gestures, defaults, pickup |
| Cinderwheel JUCE host/MIDI patterns | exact source hashes bound in bundle | pinned JUCE, input selector, bounded adapter, layout mechanics | Tide Pit Core, semantic events, state snapshot, copy, colors |

Tide Pit mapping:

- CC20-23 stages, CC24 Rate, CC25 Memory, CC26 Material, CC27 Position.
- CC28 FX-A, CC29 FX-B, CC30 Root; CC31-35 are visibly unassigned.
- CC40 Source, CC41 Mutate, CC42 Lock, CC43 Freeze, CC44 FX Mode,
  CC45 Target, CC46 Scale; CC47 is unassigned.

Buttons synthesize the source gesture duration needed by the reference engine;
they do not add Reset, Panic, or another musical state.

## 9. Reference oracle

| Field | Bound value |
|---|---|
| Oracle kind | canonical macOS bit-exact Q27 stream from exact source under Ksoloti-equivalent zeroed-BSS semantics |
| Fixture | RNG `0x21`; 12,000 blocks; stages .18/.52/.83/.34; rate .55; memory .78; timbre .47; position .31; size .42; texture .58; root 60 |
| Timeline | source `Process` called once per 16-sample block, no gesture events |
| Output | planar little-endian int32: left 16 then right 16 per block |
| Expected | 1,536,000 bytes; SHA-256 `39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b`; peak 39,182,832 Q27; RMS 14,011,444.589680206 |
| Canonical toolchain profile | Apple Clang 16, C++17, `-O2`, default floating-point contraction |
| Legacy result | `9e47bed8...ab00` came from an automatic-storage harness with uninitialized Clouds reverb histories and is retained only as provenance evidence |
| Cross-platform rule | objective tolerance and state invariants; no byte-identity promotion |
| Limits | no physical ADC, output hardware, listening, or non-48k equivalence |

## 10. Minimal experiment

### Primary bounded equivalence claim

At 48 kHz, the portable reference Core preserves the exact canonical CLEAN
source stream and remains semantically invariant when the same event timeline
is delivered through supported JUCE outer block partitions.

### Conditions and comparator

The fresh source-bound zero-BSS reference is the primary comparator. Additional deterministic
conditions cover REED/RND/FOLD, CLEAN/FILT/DRIVE, capture/resume, mutation/lock,
root/scales/targets, soft pickup, and parameter extremes. A bypassed-grain or
altered-quantum condition must differ where expected and cannot satisfy the
golden comparator accidentally.

### Objective measurements

SHA-256/byte count, peak, RMS, DC, finite samples, state/display trace,
allocation count, queue/drop counters, host partition equality, direct versus
MIDI-adapted parity, and sanitizer results.

### Listening protocol

Deferred to the user after the built app is handed off. A/B against the remembered
Gills experience is useful feedback but not promoted to source equivalence.

### Stop or pivot conditions

Stop on source/hash/license drift, golden mismatch not localized to an approved
port seam, non-finite output, unbounded callback work, or UI feedback that
misrepresents pickup state.

## 11. State-operation summary

Initialization recreates zeroed global-BSS semantics and the exact source
discrete state. The source has no Reset or Panic operations; those remain N/A.
Capture stops recorder writes but continues granular playback. Mode changes
preserve per-mode FX values and reset only source-defined effect state.
Reprepare reconstructs a fresh instance. Non-finite host output fails closed
without claiming source recovery behavior.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result |
|---|---|---|---|
| Exact source bytes and licenses frozen | drift validator and manifests | source | planned |
| Portable reference translation | canonical golden | host signal | planned |
| Numeric and state safety | focused/sanitizer tests | host structural | planned |
| JUCE boundary correctness | direct/adapted parity and lifecycle | host structural | planned |
| Objective sound output | render matrix | host signal | planned |
| Standalone compiles | pinned JUCE build | target build | planned |
| App runs in deadline | callback measurement | real-time | deferred |
| Launch Control performs correctly | user/controller session | connected device | deferred |
| Favorite sound is preserved | user A/B | listening | deferred |
| Schuss instrument integration | canonical task/records | production integration | out of scope |

## 13. Implementation plan

1. Validate the implementation bundle and source root.
2. Vendor exact normative DSP and minimal Mutable closure with notices/manifests.
3. Prove the source-bound zero-BSS reference through the untouched source seam.
4. Wrap fixed storage, semantic controls, arbitrary outer blocks, snapshots,
   renderer, and tests.
5. Add the pinned JUCE adapter/app using the reusable controller topology.
6. Freeze source/host evidence, run proportional checks, and hand off the app.

No shared `schuss_rt`, catalog, graph, provider, or record artifact changes.
General C++/JUCE extraction waits until both Cinderwheel and Tide Pit reveal a
stable common denominator.

## 14. Intentional deviations

| Deviation | Why | Effect | Approval/test |
|---|---|---|---|
| Desktop audition preset for continuous controls | physical pots have no stored source default | startup is immediately audible but not called canonical | current uninterrupted approval; preset labelled and tested |
| Separate Launch Control buttons for overloaded Gills gestures | regular controller has eight buttons and no encoder push contract | operations are easier to reach; source state/timing preserved by synthesis | current approval; semantic/source parity |
| Per-instance compatible stmlib LCG | desktop instances must not share mutable global state | exact single-instance sequence, independent interleaving | golden plus two-instance test |
| Unsupported sample rates rejected | source is deeply fixed to 48 kHz | no silent retuning/redesign | negative prepare test |

## 15. Claim-to-source ledger

| ID | State | Claim | Source | Proof gap |
|---|---|---|---|---|
| TP-001 | EVIDENCE | exact source revision/file hashes and target-clean observation | read-only Gills Git/file audit | surrounding repo remains dirty and untouched |
| TP-002 | EVIDENCE | 48k/16 timing, signal graph, scales, gestures, buffers, effects | normative Tide Pit headers/patch | portable build pending |
| TP-003 | EVIDENCE | minimal dependency closure is MIT | per-file include/license audit | retained notices pending |
| TP-004 | EVIDENCE | fresh exact source with zero-BSS semantics produces `39d8...ad2b` twice | isolated Apple Clang 16 probe | permanent repository harness pending |
| TP-005 | EVIDENCE | legacy `9e47...ab00` is not a lawful oracle because its automatic-storage Reverb histories were uninitialized | recovered harness plus controlled initialization and FP probes | retained only as legacy provenance |
| TP-006 | HYPOTHESIS | portable owned-storage reference can reproduce `39d8...ad2b` | exact code and bounded seams | implementation test pending |
| TP-007 | HYPOTHESIS | familiar LC3 topology can control Tide Pit effectively | Cinderwheel user-confirmed map | Tide Pit session pending |

## 16. Open questions and decision gate

No new scale is needed: preserving the original four exact scale arrays is part
of the fidelity baseline. A later scale change would be a separately accepted
instrument variation.

The selected architecture is an isolated exact-source reference engine, then a
portable semantic/host wrapper, renderer, and JUCE standalone app. The current
user request authorizes uninterrupted implementation of proposal revision 0.2
after the readiness validator passes, but does not authorize commits, pushes,
publication, hardware writes, or production Schuss integration.

## 17. Implementation record

To be completed after validation with exact source/contract fingerprints,
commands, results, corrections, deviations, and remaining proof gaps.
