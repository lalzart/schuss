# Pamplist 0.6 Local VST3 Host Migration

> Status: approved for uninterrupted personal-use implementation by the user's
> 2026-08-24 request, "Let's try to create a Solid personal-use VST3 of
> Pamplist."
> Proposal revision: 0.1
> Work type: source-reimplementation
> Original request: Create a solid personal-use arm64 VST3 of the accepted
> Pamplist 0.6 instrument so it can run, be sampled, and be layered directly
> inside Ableton Live.
> Implementation target: macOS arm64 VST3 instrument for the installed Ableton
> Live 12 Suite 12.4.1 at exactly 48 kHz, built from authenticated JUCE 8.0.15
> and the frozen current-working-tree Pamplist 0.6 Core.
> Decision gate: source and fidelity readiness are required before
> implementation edits. The uninterrupted authorization waives only the pause
> for a second approval, never the readiness gate.

## 1. Port thesis and identity

### One-sentence thesis

Preserve Pamplist 0.6's exact portable Core, musical control laws, seeded
timeline, seven Macro Voices, cohesion body, and accepted-state presentation,
while replacing only the standalone audio/MIDI device shell with a bounded
VST3 host adapter suitable for private sampling and layering in Ableton Live.

### Identity to preserve

- **EVIDENCE:** Pamplist 0.6 is the current accepted prototype revision; its
  Core renders at exactly 48 kHz, accepts blocks no larger than 512 frames, and
  owns seven deterministic lanes, seven Macro Voices, one dry mixer, one shared
  cohesion body, and stereo output.
- **EVIDENCE:** Task 043 gave that musical identity canonical family
  `schuss-family-000109@1`, graph `schuss-graph-000009@1`, and instrument
  `schuss-instrument-000007@1`, but expressly created no canonical
  implementation binding, provider, runtime, package, or distribution claim.
- **INFERENCE:** A prototype-local VST3 adapter may use the canonical labels as
  a completeness cross-check, but its parameter IDs and runtime mapping remain
  adapter authority. This avoids pretending that Task 045 creates the missing
  canonical provider binding.
- **EVIDENCE:** The existing standalone application and its retained build are
  inputs, not outputs to rewrite. The VST3 is an additional host form.

### Working definition and evidence level

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| Frozen Pamplist source set | source | Listed working-tree files match their SHA-256 values and the configured Macro Voice checkout authenticates | Correct VST behavior or audible quality |
| Parameter/state model tests | host-structural | Stable IDs, exact domains, defaults, state rules, and control round-trips pass | Loadable module or target architecture |
| Direct processor renders | host-signal | 48 kHz PCM, MIDI scheduling, state recall, and multi-instance comparators pass | VST3 module loading or Ableton behavior |
| Built `Pamplist.vst3` | target-build | Release bundle is arm64, exposes one zero-input/two-output instrument, scans and instantiates through JUCE's VST3 host, and passes offline module tests | Installation, Live scan, callback deadline, listening, distribution, or production |

## 2. Scope and decision rights

### Goal and why

Create one dependable private-use VST3 so the performer can place multiple
Pamplist instances on Ableton tracks, automate or MIDI-control them, record or
freeze their stereo output, and layer the resulting material without routing a
separate standalone process.

### In scope

- One macOS arm64 VST3 instrument target with zero audio inputs, stereo audio
  output, and MIDI input.
- Exact reuse of the frozen Pamplist 0.6 Core and configured Macro Voice source.
- A stable adapter parameter set covering all 178 accepted musical controls,
  plus one explicit host-only Run parameter.
- Existing physical control domains and displays: BPM 20-300; lane rate,
  phase, shape, hits, rotation, chance, repeat, depth; eight signed/boolean
  motion routes; eight voice controls; eight cohesion controls; and master.
- Run as a persistent automatable value; Clear Cohesion as a non-persistent
  one-shot; page and Voice/Motion context as private recalled editor state.
- Versioned, transactional plug-in state recall; fresh volatile DSP state on
  recall; no replay of Clear.
- Existing channel-16 regular Launch Control 3 CC semantics when CC messages
  arrive inside the host MIDI buffer, with event sample offsets preserved.
- A plug-in editor reproducing the current Pamplist page/context surface and
  accepted impact history without audio-device or physical-endpoint controls.
- Bounded processing for arbitrary positive host block sizes by partitioning
  into at most 512-frame Core calls.
- Focused model/processor tests, Release target build, module scan/instantiate,
  offline host-signal comparators, and multi-instance lifecycle checks.

### Out of scope

- Changes to Pamplist Core equations, defaults, random addressing, smoothing,
  Macro Voice wrapper, controller semantics, canonical records, or retained
  0.6 evidence.
- Host tempo synchronization, note-trigger mode, external clock, sidechain,
  audio input, MIDI output, program banks, sample recording/export, preset
  browser, oversampling, or sample-rate conversion.
- A canonical Schuss provider/runtime/binding, generic plug-in framework, Tide
  Pit VST3, Layerwell integration, or production catalog route.
- Universal/x86_64, AU/AAX/CLAP, Windows/Linux, installer, codesigning identity,
  notarization, packaging, public distribution, or licensing approval.
- Installing the bundle in a system/user VST3 folder, launching Ableton,
  opening audio/MIDI endpoints, physical controller operation, listening
  approval, real-time deadline promotion, Git staging/commit/push, or
  publication.

### Inputs and deliverables

Inputs are the exact files in section 3, accepted ADRs 0016-0018, Task 043,
the current Pamplist 0.6 proposal and ready bundle, the configured locked
Macro Voice source, authenticated JUCE 8.0.15 bytes, and the local arm64-capable
Ableton Live 12.4.1 installation.

Deliverables are:

1. This frozen proposal and `contract-vst3-r01/` implementation-ready bundle.
2. A JUCE-independent stable parameter/control model and tests.
3. A JUCE VST3 processor/editor/entry seam, state schema, and host tests.
4. An opt-in authenticated CMake VST3 target that never copies after build.
5. A Release `Pamplist.vst3` retained in a build directory, plus a portable
   build receipt, results, gaps, notices, and exact validation commands.

### Acceptance tests

1. Every listed Pamplist input and configured source identity authenticates
   before the plug-in target is configured.
2. The adapter exposes exactly 178 source-musical parameters plus Run; every ID
   is unique and stable, every domain/default matches the frozen Core/UI model,
   and the complete mapping round-trips through `Controls` without loss beyond
   declared discrete quantization.
3. Clear is an edge/generation event that is absent from serialized state;
   restoring state cannot clear the cohesion body accidentally.
4. State requires the exact schema and complete unique parameter set, applies
   transactionally, restores Run/page/mode/seed, and requests a fresh Core.
   Voice internals, timeline phase, cohesion tail, diagnostics, and accepted
   impact history reset.
5. At 48 kHz the processor partitions large buffers safely, preserves in-block
   CC offsets, returns finite stereo PCM within `[-1, 1]`, and matches direct
   Core output for the same controls, events, blocks, and seed.
6. Unsupported sample rates, invalid layouts, malformed state, null/empty
   buffers, and failed Core calls produce deterministic silence or retain the
   prior valid state without crashing.
7. Two instances have independent Core/controller/state/history and identical
   instances render identical PCM without cross-instance influence.
8. The arm64 VST3 bundle builds without copying or installing, is discovered
   as one instrument by a separate JUCE VST3 host executable, instantiates at
   48 kHz, creates/destroys an unattached editor, recalls state, and renders the
   expected nonzero test signal.
9. Pamplist's existing focused/adjacent suites, source authentication,
   standalone authenticated target build, Task 043 freshness, and Schuss
   `current` remain valid after freeze; one relocated VST3 reproduction passes.
10. Results state source, host-structural, host-signal, target-build, real-time,
    Live, physical-controller, listening, distribution, and production evidence
    independently.

### Decisions this work may make

- Prototype-local VST3 manufacturer/plugin codes, bundle ID, target names,
  adapter parameter IDs, state schema, editor layout, and bounded host failure
  messages.
- Exact host-only treatment of Run, Clear, page, and Voice/Motion context so
  long-lived automation and state do not reinterpret canonical action facets.
- Direct-processor and module-host fixtures needed to prove lifecycle,
  state, MIDI, multi-instance, and PCM behavior offline.

### Decisions this work must not make

- New musical laws, source defaults, canonical graph/provider meanings, source
  equivalence beyond the frozen files, or a claim that VST3 parameters are a
  Task 043 canonical implementation binding.
- Live scan success, connected endpoint behavior, real-time safety, audible
  approval, distribution legality, or production readiness from offline tests.
- Mutation of the configured `patcher` checkout, JUCE source tree, Task 043/044
  inherited bytes outside the exact adapter integration, Git index/history, or
  machine plug-in folders.

## 3. Source authority and lineage

| Portable source ID | Revision | Dirty-state scope | Authority | Forbidden mutations |
|---|---|---|---|---|
| `pamplist-prototype-v06-task045-input` | Exact working-tree hashes below, based on Schuss baseline `982ded194526f2fbe7e392ae070062df701c34f2` plus completed uncommitted Tasks 043/044 | Only listed files are normative; unrelated dirty files are inherited and preserved | Current local Pamplist 0.6 source/proposal/evidence and Task 043 accepted identity | No rebaseline, normalization, or incidental rewrite of frozen Core, wrapper, source checkout, retained evidence, or canonical records |
| `patcher-macro-voice-lock` | repository `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`; synthesis tree `58917f3e2e46a30337cfb6292a3504845b1d5552` | Configured external checkout must be clean at the authenticated scope | `tests/verify_source_authority.py` and `source-dependencies.json` | No checkout update, clean, reset, formatting, generated write, or source edit |
| `juce-8.0.15-authenticated-local` | JUCE 8.0.15 exact source accepted by Instrument Lab helper | Read-only external build input | Existing authenticated build closure | No fetch by default, source edits, installation, or license inference |

| Relative path | SHA-256 | Role | License and notice |
|---|---|---|---|
| `research/prototypes/pamplist/src/core.cpp` | `aad40fed6018bcfa70819cb427907fae412e67e694330ec67543d09499f6b9d3` | normative DSP/timing/state | Schuss project source; dependency closure below |
| `research/prototypes/pamplist/include/schuss/pamplist/core.hpp` | `92e728e096ecff0bf716551080543832bf3b211f951971bc15912b4c858df7b6` | normative Core ABI/defaults | Schuss project source |
| `research/prototypes/pamplist/src/macro_voice.cpp` | `7bbadb688a7b39920606004ee4b5051c6a3bd7455f70aeef4fa007c7f980b4a0` | normative source adapter | GPL-3.0-or-later wrapper closure |
| `research/prototypes/pamplist/include/schuss/pamplist/macro_voice.hpp` | `b46e7a6c5356ba86334b8abf90b52a175317962b5fc48af41a3cd4c4f3228df1` | normative adapter ABI | GPL-3.0-or-later wrapper closure |
| `research/prototypes/pamplist/src/control_map.cpp` | `bd86fd914e2dc975528a9fc2ae618108fb2f6ce14ba05bc896e8c2118e63c5ff` | normative MIDI semantics | Schuss project source |
| `research/prototypes/pamplist/include/schuss/pamplist/control_map.hpp` | `3d5e1d0a4bf3a0e006e2ca621ab84946107d024e9657840bf93daabd7263165b` | normative MIDI ABI | Schuss project source |
| `research/prototypes/pamplist/src/ui_model.cpp` | `edf1c99dcc089df24a6d546f1ee78ae084695c446b0efae01b4af46f1fe4f1f8` | normative control domains/presentation | Schuss project source |
| `research/prototypes/pamplist/include/schuss/pamplist/ui_model.hpp` | `70f3ae476bdd5ae0ed3360d27aeb798623b3be0facea96d256ffe2e71bc142a0` | normative presentation ABI | Schuss project source |
| `research/prototypes/pamplist/src/activity_model.cpp` | `adbfe6d306a70d7de3b7f40c6302b90cdfe145285c362c2ad182cc8e6c99197d` | normative accepted-history reduction | Schuss project source |
| `research/prototypes/pamplist/src/juce_main.cpp` | `c14bb7fcbc9af93a8142d40cbee7c059f456dd1ccb23c70349bb2ae7894b63f9` | supporting standalone UI/host reference | Schuss project source plus JUCE |
| `research/prototypes/pamplist/semantic-control-surface.json` | `1944250974303b05e75059a4fa1d58d6c70d661d19ca6d60ca490b72d5b1015a` | normative public control topology | Schuss project data |
| `research/prototypes/pamplist/source-dependencies.json` | `d7b82c51046bf96d68b726eba1ebbfc989e0d03fc4daab47f4e71f6fd71f5c38` | normative dependency closure | Exact upstream declarations |
| `research/proposals/pamplist-r06.md` | `a923b9665a6024d986a5ae8ac094aa9d41cd634de03c45c8ca954630ea43e917` | normative accepted revision | Proposal authority |
| `research/prototypes/pamplist/contract-r06/RESULTS.md` | `a9c29d66f542e7d047b86c502695d7fd981b62930e12e073bb01f77e5327d5eb` | observational retained result | Evidence limits retained |
| `contracts/task043/pamplist-instrument.json` | `06de37792afd4bfd0fed49f3d6748a06fab14b1274d1c8c772dff073f01b7668` | supporting completeness cross-check only | Canonical semantics; not a provider binding |

## 4. Dependency and license closure

| Dependency | Exact revision/files | License | Authentication | Distribution disposition |
|---|---|---|---|---|
| Ksoloti Extended Macro Voice wrapper | `patcher@08d3e6e...`, exact synthesis tree | GPL-3.0-or-later | Pamplist configured-source verifier | Private use allowed by current project policy; redistribution requires a fresh complete GPL/source-offer review |
| Mutable Instruments Plaits | `08460a69...` source subset | MIT | `source-dependencies.json` and source verifier | Retain notice; not independent distribution approval |
| stmlib | `e3bd7c...` source subset | MIT | `source-dependencies.json` and source verifier | Retain notice; not independent distribution approval |
| JUCE | 8.0.15 authenticated local tree | JUCE commercial terms or AGPLv3 | Instrument Lab source helper and exact local source | Personal local build only in this task; redistribution/signing decision unresolved |
| Steinberg VST3 SDK embedded by JUCE | Exact SDK subset in JUCE 8.0.15 | VST3 SDK license files in authenticated tree | JUCE target build and module metadata | Preserve notices; public distribution review unresolved |
| Ableton Live | Installed 12 Suite 12.4.1 universal app | Proprietary host | Local Info.plist and Mach-O architecture inspection | Host only; no files copied or modified |

No legal conclusion beyond the bounded private-use build is made. The VST3
must not be distributed from this task.

## 5. Source behavior contract

### Signal flow

Host MIDI/automation and editor gestures reduce to one coherent `Controls`
value. The Core advances a 48 kHz master timeline, seven lane clocks and
decision systems, local motion routing, seven independent Macro Voices, an
exact dry mixer, a six-mode cohesion body, final gain/saturation, and stereo
Q27 output converted to float. No audio input is consumed.

### Parameters, defaults, and curves

The adapter owns stable source-semantic IDs, not canonical provider IDs. It
exposes exactly 178 musical values in this order: Tempo; seven Rate/Phase
pairs; seven groups of Shape/Hits/Rotate/Chance/Repeat/Depth; seven groups of
eight Motion destinations; seven groups of eight Voice controls; eight Global
cohesion controls; Master. Run is parameter 179 and is explicitly host-only.

Physical domains and quantization come from `ui_model.cpp`: rate 16 steps,
phase 128, shape 8, hits 17, rotation 16, repeat 65, model 24, trigger and Run
boolean, root integer semitones, other values continuous. Defaults come from
`defaultControls()`. VST normalized values map linearly to those physical
domains before source sanitization. Task 043's normalized defaults remain a
semantic cross-check and are not silently promoted into a provider mapping.

### State, timing, randomness, and buffers

- Exactly 48 kHz; the host may supply any positive block size, partitioned
  into fixed-capacity calls of at most 512 frames.
- MIDI CCs are consumed in JUCE sample-position order. Audio before an event is
  rendered with the preceding state; the event applies before the sample at
  its position. Equal-position events preserve buffer iteration order.
- Randomness remains addressed and seeded by `kDefaultSeed`; seed is serialized
  as private state for schema completeness but has no new public control.
- Persistent: 179 parameter values, seed, selected page, and lane mode.
- Volatile on prepare/recall: timeline phase/remainders, voice internals,
  cohesion history, diagnostics, controller edge memory, and impact history.
- Excluded from state: Clear generation and any pending one-shot.
- State application is transactional. Wrong schema, duplicate/missing IDs,
  non-finite values, out-of-domain private values, or malformed bytes retain
  the prior valid program and request no reset.

### Gestures, modes, display, and feedback

The editor keeps eight pages, Voice/Motion context, sixteen contextual rotary
slots, Run, Global Clear, dependency guidance, seven lane colours, and accepted
impact trails. Page and mode choose presentation only. All values and activity
come from an accepted Core snapshot; requested host/MIDI input may appear only
as separate diagnostics. The plug-in has no endpoint selector or Start Audio
button because the host owns lifecycle and endpoints.

### Platform and numeric assumptions

The first artifact is macOS arm64, VST3, float32 host buffers, stereo output,
and JUCE 8.0.15. The DSP remains integer Q27 at its public output seam and uses
the existing Core numeric contract. Unsupported sample rate/layout fails to
silence while the module remains loadable and reports the condition in-editor.

### Known source quirks

- Default lane Depth and Motion routes are zero, so the faithful default may be
  silent until configured.
- Pamplist is internally timed; Live transport and tempo do not drive it.
- Core state is intentionally not serializable; recall restarts the musical
  program from frame zero rather than resuming tails or phase.
- The configured Macro Voice source retains a known signed-shift UBSan finding
  in upstream byte-authentic code; ordinary Release behavior and the evidence
  ceiling remain distinct from sanitizer limitations.

## 6. Fidelity matrix

| Behavior or subsystem | Disposition | Equivalence rule | Evidence |
|---|---|---|---|
| Core DSP and random timeline | preserve | Same source files, Controls timeline, frame partition, Q27 outputs, and snapshots | Existing tests plus direct Core/plugin comparator |
| 178 musical controls | preserve | Every source field is reachable once with exact domain/default/quantization | Descriptor and exhaustive round-trip tests |
| Run | allowed host adaptation | Boolean adapter parameter maps only to `Controls::running` | Parameter/state/process tests |
| Clear Cohesion | preserve as action | Each accepted edge increments generation exactly once and is never serialized | Action/MIDI/state tests |
| Page and Voice/Motion mode | preserve privately | Same page/mode topology; recalled but not automatable musical facets | UI/model/state tests |
| Channel-16 controller map | preserve | Existing `ControllerAdapter`; JUCE buffer timestamp defines boundary | Timestamped MIDI comparator |
| Standalone endpoint shell | exclude from plug-in | Host owns audio/MIDI devices | Structural inspection |
| Core volatile state across recall | allowed reset | Fresh Core with restored program, not bit-resumed hidden state | State twin-render comparator |
| Host blocks over 512 | allowed adaptation | Consecutive bounded Core calls equal explicit direct partition | Block matrix |
| Other sample rates | exclude/fail closed | Deterministic silence and visible status | 44.1/96 kHz negative tests |
| Live transport/tempo sync | exclude | No playhead query changes Core controls | Structural test |

## 7. Port seams and architecture

| Source seam | Portable adaptation | Fixed capacity or timing | Failure behavior | Test |
|---|---|---|---|---|
| VST parameter API to `Controls` | JUCE-independent descriptor table and converters | 179 atomics; O(parameter count) per control snapshot | Clamp/quantize; non-finite rejected | Exhaustive defaults/extremes/round-trip |
| Host block to Core | Processor partitions around MIDI positions and 512-frame maximum | Two 512-frame Q27 scratch arrays; no callback allocation | Clear output, count failure, continue safely | 1/16/64/128/512/513/2048 matrix |
| Host MIDI to source map | Existing `ControllerAdapter` per instance | Bounded iteration over host-provided MIDI; sample offsets | Ignore non-CC/wrong-channel/invalid mappings | Trace comparator |
| Core snapshot to editor | Existing fixed-capacity accepted snapshot mailbox | Audio publish; 20 Hz UI read | UI rebases history after reset/rollback | Threaded snapshot and activity tests |
| Host state bytes to program | Versioned ValueTree with complete child set | 179 values plus four bounded private fields | Transactional reject; prior state retained | Corrupt/missing/duplicate/version tests |
| VST3 module boundary | JUCE wrapper around one processor factory | One instrument class, 0-in/2-out | Scanner/instantiation failure is target-build failure | Separate-process module host |

### Portable Core boundary

Pamplist `Core`, control map, UI model, activity reducer, snapshot mailboxes,
and source adapter remain JUCE-independent. A new JUCE-independent VST model
owns parameter descriptors and `Controls` conversion but does not become a
Schuss implementation provider.

### Renderer and reference boundary

The direct Pamplist Core is the numeric oracle. The comparator feeds identical
initial Controls, MIDI-equivalent edits, sample offsets, and block partitions
to direct and plug-in processors and compares PCM/snapshots exactly where the
float conversion is deterministic. Retained 0.6 renders remain regression
evidence, not regenerated historical authority.

### Host, MIDI, controller, and UI boundary

JUCE owns VST3 ABI, float buffers, parameter gesture notification, state byte
transport, editor component lifetime, and host MIDI delivery. It never opens
an audio or MIDI endpoint. Editor code reuses the current topology and palette
mechanics but speaks only to the processor adapter.

## 8. Controller and UI reuse

| Reused artifact | Fingerprint | Reused topology or mechanism | Instrument-specific replacement |
|---|---|---|---|
| Pamplist standalone JUCE UI | `c14bb7f...` | palette, eight pages, two contextual rows, Run/Clear, labels/tooltips | Endpoint lifecycle row removed; processor status replaces device status |
| UI model | `edf1c99d...` / `70f3ae47...` | accepted-state slot projection and physical domains | No replacement |
| Activity model | `adbfe6d3...` | fixed 192-sample, seven-lane history and Clear marker | Editor-local history rebases on editor/recalled-Core reset |
| Control map | `bd86fd91...` / `3d5e1d0a...` | channel-16 CC topology and edge behavior | Host MIDI buffer replaces physical callback |

The plug-in editor must reflect authoritative accepted Core state. Raw host or
MIDI input may be shown separately as diagnostics and must not feed duplicate
events back.

## 9. Reference oracle

| Field | Bound value |
|---|---|
| Oracle kind | Frozen direct Pamplist 0.6 Core plus source parameter/UI model |
| Source fixtures and commands | Existing Core/control/UI/snapshot tests; new direct-vs-processor and VST3 module-host fixtures |
| Sample rate and block sizes | 48,000 Hz; 1, 16, 64, 128, 512, 513, and 2048 frames; timestamped event splits |
| Seed and event/sample convention | `0x50414d50`; CC applies before its declared sample; state recall begins at frame zero |
| Metrics and tolerances | Exact Q27 and deterministic float conversion when paths are identical; finite/bounded PCM; nonzero energy for enabled fixture; zero for invalid-rate fixture |
| Retained outputs and hashes | New receipt binds bundle executable, moduleinfo, fixture outputs, proposal, source set, JUCE, and configured source |
| Explicit proof limits | No Live scan, callback-deadline, physical MIDI, audible, distribution, or production proof |

## 10. Minimal experiment

### Primary bounded equivalence claim

At exactly 48 kHz, one Pamplist VST processor instance with a fixed program and
timestamped CC trace produces the same stereo samples and accepted state as the
frozen direct Core driven by the equivalent `Controls` transitions and frame
partition.

### Conditions and comparator

Use default seed; enable one lane with Trigger, Depth, Hits, Model, Pitch, and
Level; render at each block size; insert page/mode and Clear messages at
non-boundary offsets; serialize, restore into a fresh instance, and compare to
a fresh direct Core with the restored program.

### Signals, gestures, and extremes

Cover silent default, nonzero single lane, seven-lane dense program, minimum
and maximum discrete controls, signed motion routes, cohesion extremes, Run
off/on, Clear, malformed state, wrong MIDI channel, 44.1/96 kHz, and two
simultaneous instances.

### Objective measurements

Compare sample hashes, maximum absolute delta, finite/bounded counts, event and
clear counts, absolute frames, parameter/control round-trips, state bytes after
canonical reserialization, scanner description, bus layout, architecture, and
module metadata.

### Listening protocol

Deferred. After explicit permission to install and launch Ableton, a separate
gate should audition single and layered instances, state recall, automation,
record/freeze/resample, CPU stability, and controller feel. No listening claim
is made during implementation.

### Stop or pivot conditions

Stop and report rather than weaken fidelity if source authentication fails,
the plug-in requires Core DSP edits, parameter/state mapping cannot be made
stable, VST3 module loading fails after focused diagnosis, or licensing no
longer supports the bounded private-use build.

## 11. State-operation summary

- Initialization/prepare: retain parameter program, reset Core/controller and
  accepted mailboxes, clear editor history, accept processing only at 48 kHz.
- Reset/recall: validate complete state transactionally, apply atomics/private
  state, then reset Core on the audio thread before the next rendered sample.
- Panic/release: silence output and reset volatile Core/controller state.
- Freeze/capture: not owned by the plug-in; Ableton performs recording/freeze.
- Mode/page change: private presentation state, applied at the next event/audio
  boundary and serialized.
- Disconnect/reconnect: host lifecycle reset with persistent program retained.
- Non-finite recovery: state transaction rejects; parameter converter clamps a
  host-provided finite normalized value; Core sanitizer remains final authority.

The implementation bundle owns the complete state-by-operation matrix.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Result | Artifact |
|---|---|---|---|---|
| Exact source migrated | SHA/source verifier and no frozen-byte diff | source | pending | source-equivalence and receipt |
| Stable complete controls/state | Exhaustive model tests | host-structural | pending | test log |
| Deterministic correct PCM | Direct/processor matrix | host-signal | pending | fixture hashes/results |
| Loadable arm64 VST3 | Release build plus separate module host | target-build | pending | `Pamplist.vst3` and receipt |
| Callback deadlines | Not run | real-time | excluded | GAP |
| Ableton compatibility | Not run | host-specific connected application | excluded | future gate |
| Physical controller | Not run | connected-device | excluded | future gate |
| Sound/creative usefulness | Not run | listening | excluded | future gate |
| Redistribution/production | Not reviewed | distribution/production | excluded | GAP |

## 13. Implementation plan

### Implementation-ready bundle

- Bundle path: `research/prototypes/pamplist/contract-vst3-r01/`
- Proposal fingerprint and approval reference: generated after this proposal is
  frozen; user request in the active 2026-08-24 task.
- Source root is runtime-only and not stored in durable artifacts.
- `validate_implementation_bundle.py --phase ready --source-root ...`: pending.

### Expected files and stages

1. Freeze Task 045 routing, proposal, source-equivalence, state matrix, control
   map, experiment, and validation plan.
2. Add a JUCE-independent `vst3_model` descriptor/conversion library and tests.
3. Add processor, editor, entry point, direct processor tests, and VST3 module
   host tests behind `PAMPLIST_ENABLE_VST3`.
4. Extend CMake and notices without enabling copy-after-build or installation.
5. Run focused/adjacent checks, freeze, then one Release target build, module
   host matrix, configured source check, `current`, and relocated reproduction.
6. Write exact results/gaps/build receipt and close Task 045 locally.

### Focused and adjacent tests

Focused checks own parameter identity/domain/defaults, Controls conversion,
state transaction/recall, Run/Clear/private state, process partition/MIDI
offsets, invalid-rate silence, multi-instance independence, editor lifetime,
module scan, and architecture. Adjacent checks own existing Pamplist Core,
control/UI/activity/snapshot/allocation suites, retained evidence, prototype
freshness, Task 043 canonical freshness, and standalone target build.

### Expensive, device, and listening gates

Build Release and the separate VST3 module host once after implementation
freeze. Run configured-source/native and relocated reproduction once. Do not
install, launch Ableton, open endpoints, run a physical controller, or conduct
listening without a new explicit gate.

### Deferred production work

Universal builds, installer/codesigning/notarization, public preset/state
migration policy, host matrix beyond the local Live version, real-time resource
measurement, distribution license review, canonical provider binding, and
publication remain separate work.

## 14. Intentional deviations

| Deviation | Why required | Musical/technical effect | Approval | Test |
|---|---|---|---|---|
| Run becomes host parameter 179 | VST automation/state need a stable value; canonical Run remains an action | Same `Controls::running`; host can automate it | Allowed adapter decision in this proposal | Run automation/state test |
| Clear remains editor/MIDI one-shot, not a parameter | Persistent/automated trigger values can replay on recall | Same generation edge; no accidental recall clear | Required fidelity rule | Clear/state tests |
| State recall resets hidden Core state | Core intentionally exposes no hidden-state serializer | Program resumes from frame zero with fresh tails/history | Explicit proposal rule | twin fresh-render test |
| Blocks over 512 are partitioned | VST hosts may choose larger buffers | Continuous source timeline with bounded calls | Allowed host seam | block equivalence matrix |
| Plug-in UI mechanics are isolated from frozen standalone shell | Avoid risking endpoint application while reusing source UI model | Same musical surface; no device controls | Allowed host adaptation | UI structure and standalone regression |

## 15. Claim-to-source ledger

| ID | State | Claim | Source | Proof gap |
|---|---|---|---|---|
| P45-001 | EVIDENCE | Core is fixed 48 kHz, max 512 frames, fixed-capacity callback-owned | `core.hpp`, Core tests | VST seam not yet tested |
| P45-002 | EVIDENCE | Pamplist has 178 accepted musical parameters and two actions | Task 043 instrument record/validator | No canonical provider mapping exists |
| P45-003 | EVIDENCE | Existing controller map is channel 16 and UI presents eight pages/two contexts | control/UI model and semantic surface | Host MIDI timestamp seam not yet tested |
| P45-004 | EVIDENCE | Local Ableton Live 12.4.1 binary includes arm64 | local Info.plist and `file` inspection | VST3 has not been installed/scanned |
| P45-005 | EVIDENCE | Authenticated local JUCE 8.0.15 contains VST3 client and host support | local JUCE source tree and prior build authentication | New module not yet built |
| P45-006 | INFERENCE | Custom atomic parameters avoid unsafe audio-thread host notifications for MIDI-originated changes | JUCE parameter API shape and bounded design | Must be tested under module host; real-time host proof deferred |
| P45-007 | HYPOTHESIS | Exact UI/domain mapping plus direct comparator will make the VST musically equivalent for sampling | Frozen source contracts | Needs implemented host-signal matrix and later listening |
| P45-008 | UNRESOLVED | Public redistribution terms and packaging are acceptable | Dependency licenses/notices | Fresh legal/license and release review required |

## 16. Open questions and decision gate

### Open questions

No implementation-blocking question remains. Live tempo sync, broader formats,
installation, Live audition, and distribution are deliberately future choices.

### Recommended architecture

Use one prototype-local JUCE VST3 wrapper around unchanged Pamplist Core, a
JUCE-independent stable parameter/control model, custom atomic parameters,
versioned transactional state, per-instance controller/Core state, exact
sample-offset CC segmentation, and an accepted-state editor copied only at the
host presentation seam. Do not route it through the canonical provider system.

### Approval reference

The user's 2026-08-24 request explicitly authorizes uninterrupted creation of
a solid personal-use Pamplist VST3. It does not authorize install, application
launch, endpoint/device access, distribution, Git publication, or production
promotion.

## 17. Implementation record

Complete only after readiness.

### Source and proposal fingerprints implemented

Pending.

### Commands and results

Pending.

### Deviations

None yet.

### Remaining proof gaps

Live scan/operation, callback deadlines, connected physical controller,
listening, distribution, and production remain unproved by design.
