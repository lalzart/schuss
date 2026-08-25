# Tide Pit Local VST3 Host Migration

> Status: approved for uninterrupted private-use implementation by the user's
> 2026-08-25 request, "Let's make Tide Pit a Ableton VST."
> Proposal revision: 0.1
> Work type: source-reimplementation
> Original request: Let's make Tide Pit a Ableton VST.
> Implementation target: macOS arm64 VST3 instrument for Ableton Live 12.4.1
> at exactly 48 kHz using authenticated JUCE 8.0.15.
> Decision gate: source and fidelity readiness are required before plug-in
> implementation edits. Uninterrupted authorization waives only the approval
> pause, never the readiness gate.

## 1. Port thesis and identity

### One-sentence thesis

Preserve Tide Pit Gills 0.1's exact 48 kHz/16-frame portable Core, evolving
four-stage gesture, granular/modal signal path, source gestures, and accepted
state presentation while replacing only the standalone audio/MIDI-device shell
with a bounded private macOS arm64 VST3 host adapter.

### Identity to preserve

- **EVIDENCE:** Tide Pit is a continuously evolving four-stage instrument with
  REED/RND/FOLD sources, a sympathetic lower follower, stereo modal body, six
  grains, diffusion reverb, mutation/Memory/Lock, Freeze capture, four scales,
  four wave targets, and CLEAN/FILT/DRIVE post-reverb modes.
- **EVIDENCE:** The frozen portable Core preserves the original Gills source's
  signal graph, constants, update order, fixed random seed, Q27 boundary,
  48,000 Hz rate, and 16-frame quantum against the retained bit-exact oracle.
- **EVIDENCE:** The existing standalone application is an accepted local
  Instrument Lab artifact, not a canonical Schuss provider, runtime, package,
  or VST implementation authority.
- **INFERENCE:** A prototype-local VST3 can reuse that exact Core and host
  bridge without changing Tide Pit's musical identity, provided plug-in state,
  automation, MIDI timing, and fresh-Core recall are tested separately.

### Working definition and evidence level

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Frozen Tide Pit source set | source | Every listed source and dependency fingerprint authenticates | Plug-in behavior or audible quality |
| Parameter/state/processor tests | host structural | Stable controls, transactional state, lifecycle, failure paths, and allocation probe pass | Loadable VST3 module or callback deadline |
| Direct-Core processor renders | host signal | 48 kHz PCM and event/state comparisons pass across host block partitions | Ableton scan, listening, or real-time fitness |
| Built `Tide Pit.vst3` | target build | One arm64, zero-input/stereo-output instrument scans and instantiates in a separate JUCE VST3 host | Installation, Live behavior, signing identity, distribution, or production |

## 2. Scope and decision rights

### Goal and why

Create one dependable private-use Tide Pit VST3 so it can sit directly on an
Ableton Live MIDI track for automation, recording, freezing, resampling, and
layering without routing audio from the standalone application.

### In scope

- One opt-in JUCE 8.0.15 VST3 instrument target for macOS arm64 with no audio
  input, stereo output, MIDI input, and `COPY_PLUGIN_AFTER_BUILD FALSE`.
- Exact reuse of the current Tide Pit portable Core, Q27 host bridge, controller
  map, UI model, source lock, fixed seed, defaults, and source quirks.
- Sixteen stable prototype-local adapter parameters: eleven continuous controls
  plus desired Source, Lock, FX Mode, Target, and Scale state.
- Mutate and Freeze as non-persistent one-shot actions available from the editor
  and the existing channel-16 CC surface; no state recall replay.
- Versioned transactional state, fresh volatile Core state after recall, and
  bounded reconciliation of persistent discrete modes from source defaults.
- Arbitrary positive host callback lengths through the existing exact
  16-frame `Q27HostBridge`; unsupported rate/layout failure to silence.
- Sample-offset channel-16 CC20-46 handling, with the existing unassigned and
  malformed-message behavior preserved.
- A source-faithful editor that shows accepted Core state and a bounded stereo
  scope, without owning audio devices, MIDI endpoints, or controller discovery.
- Focused model/processor/allocation/module tests, direct-Core signal parity,
  multi-instance checks, authenticated Release target build, and one relocated
  reproduction.

### Out of scope

- Any Tide Pit DSP equation, default, scale, random sequence, gesture duration,
  source dependency, source oracle, retained standalone evidence, or controller
  mapping change.
- Serialization of evolving grain/capture buffers, mutation history, timeline,
  gesture queues, diagnostics, or scope history; Freeze always recalls off.
- Host tempo sync, note-trigger redesign, sidechain/audio input, MIDI output,
  sample recording/export, preset browser, oversampling, or sample-rate conversion.
- AU/AAX/CLAP/VST2, universal/x86_64, Windows/Linux, installer, identity signing,
  notarization, packaging, public distribution, or production promotion.
- Canonical Schuss component/graph/binding/provider/runtime/catalog changes, a
  generic plug-in framework, Pamplist/Layerwell changes, or Gills firmware work.
- Copying/installing the VST3, launching Ableton or another app, opening an
  endpoint, physical controller work, structured listening, callback-deadline
  promotion, Git staging/commit/push, or publication.

### Inputs and deliverables

Inputs are the exact files in section 3, the approved Tide Pit JUCE-port
proposal and ready bundle, the authenticated shared Mutable/Ksoloti package,
the JUCE 8.0.15 source manifest, the local universal Ableton Live 12.4.1 host
identity, accepted ADRs 0016-0018, and Instrument Lab workflow rules.

Deliverables are:

1. This frozen proposal and ready bundle at
   `research/prototypes/tide-pit-gills/contract-vst3-r01/`.
2. A JUCE-independent stable parameter/program model and focused tests.
3. A JUCE VST3 processor, editor, entry point, transactional state seam, and
   separate module-host tests under `research/prototypes/tide-pit-gills/vst3/`.
4. An authenticated opt-in CMake build that never fetches or installs by default.
5. An uninstalled arm64 Release bundle, portable build receipt, results, gap
   register, validation record, and bounded reproduction command.

### Acceptance tests

1. The proposal fingerprint, every declared Tide Pit input, original Gills
   source files, shared Mutable package, and JUCE source authenticate before
   plug-in implementation.
2. Exactly sixteen adapter parameters have unique stable IDs, exact domains,
   defaults, step counts, complete mapping, and a frozen contract fingerprint.
3. State requires the exact schema, fingerprint, complete unique parameter set,
   finite in-range values, and applies only after full validation; malformed
   state cannot partially change the prior program.
4. Recall creates a fresh Core, restores continuous values and persistent
   Source/Lock/FX/Target/Scale targets, and never replays Mutate or Freeze or
   claims to restore captured audio, mutations, tails, timeline, or diagnostics.
5. At 48 kHz, direct Core and processor paths match for continuous controls,
   raw timestamped CCs, actions, reset/recall, and host block partitions
   including 1, 16, 64, 128, 511, 512, 513, 2048, and 4096 frames.
6. Unsupported sample rates/layouts, malformed MIDI/state, event overflow, and
   failed Core preparation produce deterministic silence or bounded drops.
7. Two instances remain independent and deterministic; editor construction and
   destruction open no endpoint and inject no duplicate event.
8. The Release arm64 bundle exposes one VST3 instrument with zero inputs and
   stereo output, scans/instantiates in a separate JUCE VST3 host, round-trips
   state, creates/destroys its editor, and renders the expected nonzero fixture.
9. Existing Tide Pit source/Core/control/UI/adapter/render checks, authenticated
   standalone build, Schuss `current`, and one relocated VST3 reproduction pass.
10. Results keep source, host structural, host signal, target build, real-time,
    Live, physical-controller, listening, distribution, and production claims
    independent.

### Decisions this work may make

- Prototype-local VST3 codes, bundle/target names, parameter IDs, state schema,
  processor/editor classes, fixed adapter capacities, UI dimensions, and
  bounded host error presentation.
- The exact fresh-Core recall rule and desired-state reconciliation for Source,
  Lock, FX Mode, Target, and Scale, while source gesture timing remains exact.
- Direct processor and module-host fixtures, artifact receipts, and the final
  bounded validation selection.

### Decisions this work must not make

- New musical behavior, source corrections, alternative scales, new defaults,
  canonical Schuss meanings, hidden Core serialization, or a generic plug-in API.
- Live compatibility, real-time safety, physical controller behavior, audible
  approval, licensing/distribution approval, or production readiness from
  offline source/build evidence.
- Mutation of Gills, Ksoloti/Mutable, JUCE, Pamplist, Layerwell, canonical
  records, inherited dirty files, plug-in folders, applications, devices, Git
  index/history/remotes, or publication state.

## 3. Source authority and lineage

| Portable source ID | Revision | Dirty-state scope | Authority | Forbidden mutations |
|---|---|---|---|---|
| `gills-instruments:tide-pit-gills` | Target introduced at `53287e49e5bcc5fb0d73b546d88431f82467f969`; six target files unchanged at observed repository head `9b5e4f9beb911805d32444730803f69ce333890d` | Target file hashes match; unrelated repository history is outside authority | Original Gills instrument source and MIT license | No checkout edit, reset, clean, normalization, generation, build, or hardware action |
| `schuss:tide-pit-gills-port-r01` | Schuss baseline `982ded194526f2fbe7e392ae070062df701c34f2`; exact hashes below | Tide Pit prototype and original JUCE-port proposal are clean; other Schuss changes are inherited | Frozen portable Core, adapters, UI model, and oracle | No rewrite of retained source, oracle, standalone receipt, or original bundle |
| `juce-8.0.15-authenticated-local` | Commit `91ad83ae34a81e0833b1a2b0866f54846370ae53`; source manifest below | Read-only local build input | Instrument Lab authenticated source tree | No fetch by default, source edit, install, or license inference |

| Relative path | SHA-256 | Role | License and notice |
|---|---|---|---|
| `research/prototypes/tide-pit-gills/include/tidepit/core.hpp` | `897100d45e4019d6b1f3dabc6f93a3798a85f73b659c26c9ec3fe85a1d4221b5` | normative Core ABI | Schuss/Tide Pit project source; closure below |
| `research/prototypes/tide-pit-gills/src/core.cpp` | `b3a664f386ad41b5e58968ed9dd3823684a148a25806f0618c4260b9f267d404` | normative DSP/state/timing | Tide Pit MIT plus attributed Mutable MIT closure |
| `research/prototypes/tide-pit-gills/include/tidepit/control_map.hpp` | `066a482d85f147e90c7e5e11e7f6fa795fe87c2177d6f61c95ceee3bbcdb7c1d` | normative semantic controls | Schuss project source |
| `research/prototypes/tide-pit-gills/src/control_map.cpp` | `37f2746cd35c3a29d7c5cd7659dccf36c6712ce33d3fe838d075b7ce706521d2` | normative mapping | Schuss project source |
| `research/prototypes/tide-pit-gills/control-map.json` | `a91f4ee46b3339f455d5d277f4b8f25d378c652eb946d6c017076e44fd356f60` | normative controller contract | Schuss project source |
| `research/prototypes/tide-pit-gills/generated/control_descriptors.hpp` | `f32eae062294c49c5f01c4e571865b8ecd64b5766635746882280b8ca434c51e` | derived normative mapping | Generated Schuss project source |
| `research/prototypes/tide-pit-gills/include/tidepit/juce_midi_adapter.hpp` | `54f1c2e89a7db46d55b33af33fbb74497ebd1a2ef713f6a12aec4c962c41d350` | normative host/event seam | Schuss project source |
| `research/prototypes/tide-pit-gills/src/juce_midi_adapter.cpp` | `b2123248f291990666e377dbf99e8f61c8efe76667a8adea6d0c9fd9ab9757fb` | normative host/event seam | Schuss project source |
| `research/prototypes/tide-pit-gills/include/tidepit/ui_model.hpp` | `c43620444595de670480acc374f75b8c0ae69d5f67e96b8f3da469c6f429163a` | supporting accepted-state UI | Schuss project source |
| `research/prototypes/tide-pit-gills/src/ui_model.cpp` | `d01d5c8135a7e87af54ea948c74e8a04e044533c9eb893fae55f5f309eb717bb` | supporting accepted-state UI | Schuss project source |
| `research/prototypes/tide-pit-gills/third_party/SOURCE_LOCK.json` | `52a13c11dbd81df05a3590d2aaa5cf1efc95bdddcc874d69cf6961c18de61a02` | normative dependency/source lock | Portable lock metadata |
| `research/prototypes/tide-pit-gills/third_party/THIRD_PARTY_NOTICES.md` | `4e198a537ca719925bc407a073350d7708ecb15d0152fe876478e565e23a98aa` | normative notices | Tide Pit MIT and Mutable MIT notices |
| `research/proposals/tide-pit-gills-juce-port.md` | `3c2157eaa26ceed61afe87b256a395dccc5fbbd0dab889189926ffb72b5c2157` | supporting original port authority | Project documentation |

The original six Gills source hashes remain those already frozen in
`research/prototypes/tide-pit-gills/source-equivalence.json`; the runtime-only
checkout path is never stored in the implementation bundle.

## 4. Dependency and license closure

| Dependency | Exact revision/files | License | Authentication | Distribution disposition |
|---|---|---|---|---|
| Tide Pit original source | Six files and hashes in `SOURCE_LOCK.json`; project revision above | MIT, Lance Ship | Existing source-lock validator plus runtime source-root hashes | Retain complete MIT license; this task remains private-use |
| Mutable/Ksoloti minimal closure | `mutable-ksoloti-v1@1`, package manifest `9f45e860f1fff388cc18dab077232196befbc7cfb6f383effd35331bf102f2a1` | MIT, Emilie Gillet | Shared package manifest and per-file hashes | Retain package notices; distribution is a separate review |
| JUCE and bundled VST3 SDK | JUCE 8.0.15, commit `91ad83ae34a81e0833b1a2b0866f54846370ae53`, manifest SHA-256 `db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5` | JUCE commercial terms or AGPLv3, plus bundled VST3 SDK terms | Instrument Lab helper authenticates 4,425 files and disables fetch | Private local build only; packaging and redistribution require fresh review |

## 5. Source behavior contract

### Signal flow

The plug-in preserves the existing graph unchanged:

`four-stage gesture -> REED/RND/FOLD source + sympathetic follower -> stereo modal body -> six-grain layer/Freeze -> diffusion reverb -> CLEAN/FILT/DRIVE -> Q27 stereo output`.

The VST seam only converts `float = q27 * 2^-27`; it adds no input path,
resampling, mixing, filtering, limiter, oversampling, host tempo, or note voice.

### Parameters, defaults, and curves

The eleven continuous source controls and defaults are Stage 1-4
`0.20/0.50/0.80/0.30`, Rate `0.55`, Memory `0.78`, Material `0.50`, Position
`0.31`, FX-A `0.60`, FX-B `0.35`, and Root `60`. Unit controls are clamped to
`[0,1]`; Root is the integer range `36..72`. MIDI root remains
`round_half_up(36 + 36 * value / 127)`. Rate, Memory, Material, Position, and
FX semantics remain inside the source Core; the VST never substitutes curves.

The five persistent desired-state parameters use exact source enumerations:
Source `{REED,RND,FOLD}`, Lock `{OFF,ON}`, FX `{CLEAN,FILT,DRIVE}`, Target
`{PIT,BODY,GRAIN,ALL}`, and Scale `{MAJ5,MIN5,DOR,HARM}`. For a cyclic state
of size `N`, reconciliation emits exactly `(desired - projected + N) mod N`
existing source actions. Mutate and Freeze remain one-shot actions.

### State, timing, randomness, and buffers

- Sample rate is exactly 48,000 Hz. Every source event is quantized to
  `ceil(sample / 16) * 16` and applied before that source quantum.
- The host bridge retains at most one 16-frame rendered quantum, supports any
  positive host callback length, and never resamples.
- Source RNG starts at `0x21` per Core and remains per-instance. Recall creates
  a fresh Core with that seed; random state is not serialized.
- Fixed capacities remain: 251,408-byte source arena, five source allocations,
  128 Core semantic events, 512 bridge-pending host events, and a 1,024-sample
  display-only stereo scope.
- VST state is bounded to 1 MiB and stores only the complete sixteen-parameter
  program. It excludes evolving capture audio, mutations, timeline, tails,
  gesture queues, diagnostics, MIDI edges, and scope data.

### Gestures, modes, display, and feedback

The source gesture synthesizers remain exact: Source/Mutate/Lock are pulse
actions; FX tap and Freeze hold share the source effect-button lane; Scale tap
and Target hold share the encoder-switch lane. Channel 16 CC20-30 and CC40-46
retain their existing sample-offset semantics. The editor derives mode/button
labels, latch state, display lines, accepted continuous values, and scope from
accepted Core snapshots. Requested host values and MIDI counters are diagnostic
state and cannot masquerade as accepted DSP state.

### Platform and numeric assumptions

The first target is Apple silicon, C++17, JUCE 8.0.15, Release `-O2` on the
existing Tide Pit source targets, stereo float host buffers, and exact Q27
conversion. Output must be finite and bounded to `[-1,1]`; unsupported rates or
layouts clear the host buffer and consume MIDI without attempting Core work.

### Known source quirks

- The `HARM` label intentionally retains the existing interval mismatch.
- FX-A/FX-B use source soft pickup after FX-mode changes; accepted effective
  values may intentionally lag raw input.
- Freeze/capture owns evolving audio and is intentionally not preset state.
- The generated voice overlay changes only two undefined signed left shifts to
  multiplication by two and must retain the bit-exact oracle.
- A host build, scanner result, or render is not real-time, Live, device,
  listening, licensing, distribution, or production evidence.

## 6. Fidelity matrix

| Behavior or subsystem | Classification | Equivalence rule | Evidence |
|---|---|---|---|
| DSP graph, tables, constants, update order, RNG, Q27 | preserve | Existing exact source oracle remains unchanged | Tide Pit golden/source suites |
| Eleven continuous controls | preserve | Same defaults/domains and semantic events; direct PCM exact | Model and processor comparators |
| Source/Lock/FX/Target/Scale | preserve through allowed host target representation | VST target resolves only through existing cycle/toggle gestures | State/action trace tests |
| Mutate and Freeze | preserve; exclude from serialized state | One action per editor/MIDI edge; never replay on recall | Action and recall tests |
| Host callback shape | allowed change | Existing `Q27HostBridge` output/event trace equals direct Core across partitions | Processor matrix |
| Audio/MIDI endpoint lifecycle | exclude | Plug-in owns no device or endpoint | Lifecycle/module tests |
| Capture audio, mutation/tail/timeline recall | exclude | Fresh Core with explicit volatile reset | State twin test and gap register |
| Other rates/platforms/formats | exclude | Exact silence/rejection, no implied support | Negative tests |

## 7. Port seams and architecture

| Source seam | Portable adaptation | Fixed capacity/timing | Failure behavior | Test |
|---|---|---|---|---|
| Q27 output | Multiply by `2^-27` into stereo host buffer | One 16-frame bridge quantum | Clear output and count failure | Direct PCM parity |
| Host parameters | Atomic complete sixteen-value program | Six bounded coherent-read attempts | Retain last valid program | Model/state stress |
| MIDI | Existing `JuceMidiAdapter`, merged with host events | 128 events/block, 512 bridge pending | Deterministic drop counters | Timestamp/overflow tests |
| Discrete targets | Projected cyclic target plus source actions | At most 2 Source/FX, 1 Lock, 3 Target/Scale events per target update | Retain requested state; accepted UI exposes lag | Mode reconciliation tests |
| State | Bounded XML, exact schema/fingerprint/cardinality | 1 MiB maximum | Reject transaction completely | Malformed-state matrix |
| Snapshot/scope | Fixed whole-value mailbox and 1,024-sample accumulator | No paint/string work in callback | Retain last complete UI frame | Lifecycle/UI tests |

### Portable Core boundary

The existing `tidepit::Core`, `Controls`, `SemanticEvent`, source lock, generated
voice overlay, and shared Mutable package remain untouched. The plug-in Core is
per-instance and prepared only for 48 kHz with a 16-frame maximum Core call.

### Renderer and reference boundary

The retained source golden remains the strongest source oracle. New direct
processor comparators use the same Core/bridge/event timeline and require exact
float PCM equality because both paths share the same Q27 conversion.

### Host, MIDI, controller, and UI boundary

`vst3_model` is JUCE-independent. `vst3_processor` owns atomic parameters,
state validation, fixed event merging, Core/bridge lifecycle, and UI mailboxes.
The editor owns only presentation and host notifications. The VST wrapper owns
module registration. No layer opens an endpoint or application.

## 8. Controller and UI reuse

| Reused artifact | Fingerprint | Reused mechanism | Instrument-specific replacement |
|---|---|---|---|
| Regular Launch Control 3 topology | `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b` | Channel 16, CC20-35, CC40-47, no faders | Tide Pit's existing assigned/unassigned surface |
| Tide Pit control map | `a91f4ee46b3339f455d5d277f4b8f25d378c652eb946d6c017076e44fd356f60` | Curves, edge rules, gesture identities | No replacement |
| Tide Pit UI model | `c4362044...` header, `d01d5c81...` implementation | Accepted-state button labels and fixed scope | VST omits standalone endpoint controls |
| Task 045 VST host seam | Inherited dirty files remain read-only | CMake isolation, atomic parameter/state/module-test mechanics | Tide Pit-specific model, actions, editor, oracle, IDs, and tolerances |

The application UI must reflect authoritative accepted Core state. Raw input
may be shown separately as diagnostics and must not feed duplicate events back.

## 9. Reference oracle

| Field | Bound value |
|---|---|
| Oracle kind | Existing bit-exact Q27 source golden plus exact direct-Core/VST float comparator |
| Source fixtures and commands | `tide_pit_reference_golden`; existing control/adapter/render suites; new model/processor/module suites |
| Sample rate and block sizes | Exactly 48 kHz; source quantum 16; host blocks 1, 16, 64, 128, 511, 512, 513, 2048, 4096 |
| Seed and event convention | Per-instance `0x21`; block-relative offsets, ceil-to-16 quantization, stable equal-offset ordering |
| Metrics and tolerances | Source hash byte-exact; direct VST PCM exact; all samples finite in `[-1,1]`; state/accepted trace exact after declared settling |
| Retained outputs and hashes | Existing Q27 golden SHA-256 `39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b`; new build receipt and reproducible test outputs |
| Explicit proof limits | No Live scan, callback deadline, xrun/CPU, endpoint, physical control, listening, redistribution, or production proof |

## 10. Minimal experiment

### Primary bounded equivalence claim

At exactly 48 kHz, an uninstalled arm64 Tide Pit VST3 instantiated by a
separate JUCE host preserves the frozen Core's continuous-control, timestamped
MIDI, persistent-mode, fresh-recall, and stereo signal behavior under arbitrary
positive host block partitions.

### Conditions and comparator

Use the adapter defaults and one deterministic enabled fixture that changes all
eleven continuous controls, cycles every persistent mode, invokes Mutate and
Freeze once, and recalls state into a fresh twin. Compare the processor against
the direct `Core + Q27HostBridge` path. Negative comparators use 44.1/96 kHz,
mono output, malformed/incomplete/duplicate/nonfinite state, wrong-channel and
unassigned CCs, and a deliberately changed control/event timeline that must
diverge.

### Signals, gestures, and extremes

Exercise silence/startup, minimum/maximum/default and rapid controls, root
36/60/72, all enumerated modes, repeated actions, capture toggle, soft pickup,
multi-instance independence, reset, recall, blocks at/between/above source
boundaries, event-at-end behavior, and bounded overflow.

### Objective measurements

Exact PCM equality, nonzero energy for the enabled fixture, finite/bounded
samples, snapshot state, absolute sample, accepted/dropped event counts,
parameter fingerprint, state rejection counters, heap-allocation probe across
repeated 4,096-frame calls, bundle architecture/kind, module metadata, and
source-tree non-mutation.

### Listening protocol

Deferred. A later authorized Ableton session should audition a single instance,
automation, recall, recording/freeze/resampling, and multiple layered instances.
No remembered or informal sound impression can promote this implementation.

### Stop or pivot conditions

Stop on source/hash/license drift, readiness failure, golden mismatch, direct
PCM divergence, non-finite/runaway output, partial state application, endpoint
ownership, source-tree mutation, unavailable authenticated JUCE, or inability
to preserve exact 48 kHz behavior without an unapproved resampler.

## 11. State-operation summary

Initialization and `prepareToPlay(48000)` create/reset one Core, bridge, MIDI
adapter, projected mode state, diagnostics, and scope. Release and unsupported
host shape produce silence. State recall validates all bytes transactionally,
then requests a fresh Core on the audio thread and reconciles persistent modes
using source gestures. Mutate, Freeze/captured audio, mutation state, timeline,
tails, queued gestures, MIDI edge state, diagnostics, and scope reset. Panic is
N/A: the source has no note/voice panic contract. Disconnect/reconnect is host
lifecycle and starts fresh. Non-finite parameter/state input is rejected or
sanitized to the prior valid value. The implementation bundle owns the complete
operation matrix and exact state-equivalence rule.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Source bytes remain authoritative | Hash/source/package/JUCE authentication | source | pending | readiness and existing source checks |
| Adapter model is stable | Sixteen IDs/domains/defaults/fingerprint | host structural | pending | model tests |
| Host event/state lifecycle is bounded | Processor negative/action/recall/allocation tests | host structural | pending | processor tests |
| VST signal equals direct Core | Partition/MIDI/state twin exact PCM | host signal | pending | processor/module tests |
| Intended target accepts the module | arm64 Release bundle scans/instantiates | target build | pending | build receipt |
| Ableton works | Installed Live session | connected host | not authorized | deferred gap |
| Callback margin is safe | Retained Live timing/xrun budget | real-time | not authorized | deferred gap |
| It sounds right | Structured listening protocol | listening | not authorized | deferred gap |
| It is distributable/production-ready | License/signing/package/provider review | production | not authorized | deferred gap |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/tide-pit-gills/contract-vst3-r01/`
- Proposal fingerprint and approval reference: computed after this proposal
  freezes; user request of 2026-08-25 authorizes uninterrupted implementation.
- Source root is runtime-only and not stored in durable artifacts.
- `validate_implementation_bundle.py --phase ready --source-root ...`: pending.

### Expected files and stages

1. Freeze the Task 046 contract and complete the source-reimplementation bundle.
2. Add JUCE-independent `vst3_model` with sixteen stable parameters.
3. Add processor/event/state/mailbox code and exact direct-Core tests.
4. Add accepted-state editor and VST entry point without endpoint controls.
5. Add authenticated CMake module target, module-host tests, build receipt, and
   relocated reproduction runner.
6. Freeze, run focused and adjacent checks, run `current`, then backfill results
   and gaps without rewriting the original Tide Pit authority.

### Focused and adjacent tests

Focused checks are bundle readiness, model, processor, allocation, module scan,
state, action, MIDI, partition, lifecycle, and build receipt. Adjacent checks
are all existing Tide Pit source/Core/control/UI/adapter/render suites and its
authenticated standalone build. `current` runs once after implementation freeze.

### Expensive, device, and listening gates

One arm64 Release VST3 build and one relocated reproduction are authorized
implementation checks. Ableton launch/install, physical controller, endpoints,
real-time profiling, and listening remain separate explicit gates.

### Deferred production work

Universal/other platforms and formats, installer, identity signing,
notarization, release licensing, public package, canonical provider/runtime,
preset compatibility policy, non-48-kHz support, and captured-buffer state.

## 14. Intentional deviations

| Deviation | Why required | Effect | Approval | Test |
|---|---|---|---|---|
| Standalone device shell becomes zero-input stereo VST3 | Direct Ableton use | Host owns audio/MIDI lifecycle; DSP unchanged | This request | Module/layout/direct parity |
| Five cyclic/toggle actions gain desired-state VST parameters | Stable automation and recall need addressable values | Source gestures still mediate accepted state | This proposal | Model/reconciliation/trace tests |
| Mutate and Freeze are editor/MIDI one-shots, not serialized parameters | Replaying destructive/evolving actions on recall is unsafe and false | Recall never mutates or claims captured audio | This proposal | State/action exclusion tests |
| Recall resets volatile DSP history | Core exposes no exact evolving-state serialization | Deterministic fresh identity, not seamless tail/capture restoration | This proposal | Fresh-twin comparator |
| Non-48-kHz hosts render silence | Source equivalence is fixed at 48 kHz | No hidden resampling or pitch/timing change | Existing Tide Pit contract | Negative rate tests |

## 15. Claim-to-source ledger

| ID | State | Claim | Source | Proof gap |
|---|---|---|---|---|
| TPV-001 | EVIDENCE | Original Tide Pit target files still match frozen hashes | Runtime source audit and `SOURCE_LOCK.json` | Does not prove plug-in behavior |
| TPV-002 | EVIDENCE | Portable Core is exact at 48 kHz/16 frames | Existing proposal, source equivalence, golden | Does not prove host lifecycle |
| TPV-003 | EVIDENCE | Existing bridge preserves arbitrary host partitions and MIDI offsets | Current adapter code/tests | Must be revalidated inside processor/module |
| TPV-004 | EVIDENCE | JUCE 8.0.15 local source and Ableton 12.4.1 arm64 host identity exist | Authenticated manifest and read-only app metadata | Ableton has not loaded the module |
| TPV-005 | INFERENCE | Sixteen persistent adapter parameters plus two one-shots are the smallest honest host surface | Source state/action audit | Usability and Live presentation need later session |
| TPV-006 | HYPOTHESIS | Direct-Core parity plus module-host tests will make the bundle ready for the first Live gate | This experiment | Real-time and listening remain open |

## 16. Open questions and decision gate

### Open questions

- Whether Live's presentation of JUCE's VST3 MIDI-controller service parameters
  is acceptable is deferred until an authorized scan.
- Whether captured-buffer persistence or non-48-kHz operation is musically
  necessary is deferred; both require a separate source-aware design.
- Callback CPU/xrun margin and useful multi-instance count require a later Live
  measurement on the user's M1 Pro.

### Recommended architecture

Use an isolated `vst3/` child project that imports only the frozen Tide Pit
Core targets, authenticates the same JUCE source, adds a JUCE-independent
sixteen-parameter model, and keeps processor/editor/wrapper code outside the
retained standalone source files. Build one uninstalled arm64 VST3 and validate
it through a separate JUCE module host.

### Approval reference

The user's 2026-08-25 request explicitly asks to make Tide Pit an Ableton VST,
which authorizes uninterrupted proposal-to-implementation work within this
private local VST3 scope. It does not authorize installation, application
launch, endpoint/device access, listening, Git, or publication actions.

## 17. Implementation record

Complete only after readiness.

### Source and proposal fingerprints implemented

Pending.

### Commands and results

Pending.

### Deviations

None beyond section 14 at proposal freeze.

### Remaining proof gaps

Ableton, real-time, endpoint/controller, listening, distribution, and production
evidence remain open by contract.
