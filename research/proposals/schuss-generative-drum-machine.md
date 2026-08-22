# Schuss Generative Drum Machine

> Status: approved on 2026-08-21 for the bounded prototype implementation described here; not accepted architecture or production-ready
> Proposal revision: 0.6
> Work type: `new-design`
> Original idea: A Schuss-native, self-contained six-logical-lane generative drum machine with authored progressive complexity, coherent deterministic enthusiasm, semantic `DrumHit` events, and a four-voice dynamically assigned Braids-derived synthesis pool. MIDI remains an optional presentation and integration path.
> Initial target: deterministic offline native-host proof at 48 kHz, with Braids cores rendered at their original 96 kHz core rate and explicitly decimated, a pure regular Launch Control 3 CC-to-semantic mapping adapter, and an optional authenticated-JUCE standalone audition UI
> Working artifact and evidence level: retained stereo WAV plus canonical `DrumHit`/allocator traces, exhaustive simulated LC3 mapping evidence, a fixed-capacity streaming rhythm/synthesis Core, and a built JUCE 8.0.15 standalone target with fifteen selectable authored rhythm studies and per-lane voice shaping; target-build and synthetic callback-kernel measurement ceiling with this revision's app-launch, connected-device, listening-protocol, and production evidence deferred
> Approval reference: user instructions in the current Codex thread on 2026-08-21, including “Okay please implement the proposal,” reuse of the Tide Pit LC3 topology, the UI request, the first selectable-rhythm/voice-shaper amendment, and the subsequent request that buttons one through six select the six drum voices, the bottom six encoders shape the selected voice, changes become realtime, and the bank expand to about fifteen researched patterns across at least five meters. No numbered task or stable schema/record ID is allocated by that approval.
> Decision gate: implementation may proceed only through an implementation-ready Sonic Research Lab bundle and the existing non-production Instrument Lab lane. Promotion into accepted Schuss schemas, runtime providers, records, or governance remains a separate review decision.

## 1. Product thesis

### One-sentence thesis

Six authored rhythmic parts become progressively richer under direct per-lane
control, while one global control develops the groove through coherent,
seed-reproducible bar and phrase choices; four pooled Braids-derived voices turn
the resulting musical events into stereo audio.

### Instrument identity

The performer chooses one of several independently authored rhythm/meter
presets, sets six lane complexities, and controls how freely the machine
develops the groove. A selected lane can enter voice-shaping mode without
becoming a permanent physical oscillator. The instrument responds with its own
audio. A `DrumHit` is the authoritative performance event; MIDI is an adapter
for control or mirroring.

### Intended user and musical situation

A musician who wants a compact playable groove instrument rather than a step
editor or a random-trigger utility. The first proof established the musical
and allocator semantics offline; revision 0.4 added a desktop audition
presentation, revision 0.5 added the first meter bank and per-lane shaper, and
revision 0.6 replaces phrase playback with a streaming Core so accepted
performance changes can affect upcoming audio during the current cycle.

### In scope

- Six logical lanes and fifteen independently authored rhythm studies spanning
  2/4, 3/4, 4/4, 5/4, 5/8, 6/8, 7/8, 9/8, and 10/8, all using meter-aware
  rational event positions and explicit source/context metadata.
- Per-lane thresholded complexity, authored variation bundles, deterministic
  phrase-level enthusiasm, tempo, one swing law, and one queued fill action.
- A four-core fully pooled Braids wrapper with deterministic allocation,
  choking, stealing, stereo mix, and offline evidence.
- The exact regular Launch Control 3 Custom Mode topology reused by Tide Pit:
  slot 1, MIDI channel 16, absolute encoders CC20–35, and momentary buttons
  CC40–47, with an exhaustive pure mapping adapter and no endpoint access.
- A fixed-capacity streaming scheduler and synthesis engine whose audio process
  performs no allocation, locking, I/O, JSON, or UI work; published controls
  become effective at the next supported audio block and voice parameters use
  a bounded fixed-point smoothing law.
- An optional JUCE 8.0.15 standalone audition shell with six lane controls,
  fifteen-way rhythm selection, global enthusiasm/tempo/swing, fill, per-lane
  voice selection/shaping, accepted-state feedback, cycle/lane activity, audio
  output, and selectable MIDI input through the same semantic reducer.
- KICK, SNARE, CYMBAL, SINE_TRIANGLE, FM, and FILTERED_NOISE eligibility for
  initial recipe experiments; the first preset can use a smaller subset.

### Out of scope

- Beat Friend cloning, proprietary analysis, copied Beat Friend patterns,
  copied Grids code or data, a generalized sequencer framework, accepted Schuss
  schema/record allocation, external clock, MIDI output, Ksoloti execution,
  a pattern editor, user preset persistence, live Braids model switching,
  app launch or physical-device exercise during this revision, audio-device
  deadline certification, formal listening claims, packaging, and publication.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- Current Schuss governance has no active task and reserves Task 033 Phase 3 as
  the unactivated next candidate.
- Task 034 supplies structural controller-independent performance semantics but
  intentionally supplies no execution, scheduling, MIDI I/O, sequencer, or
  allocator behavior.
- Current `schuss_rt` accepts only parameter-Q27 and raw MIDI events, has a
  65,536-byte total state ceiling, and consumes MIDI only as a delivered count.
- Upstream Mutable Instruments Eurorack commit
  `08460a69a7e1f7a81c5a2abcc7189c9a6b7208d4` and stmlib commit
  `e3bd7c9cc00e4364166f9905c0509b6ffd0535ec` are the inspected source baselines.

### Deliverables

This proposal, a claim/source ledger, an exact source-closure inventory, and
disposable host benchmark sources/binaries outside the Schuss worktree.

### Acceptance tests

- Product, timing, complexity, enthusiasm, event, synthesis, allocator, and
  ownership semantics are explicit enough to create a bounded task without
  inventing missing musical behavior.
- Source facts, inference, hypothesis, and unresolved questions are separated.
- No repository record, schema, task, or accepted architecture is mutated.

### Decisions this work may make

Recommend an architecture, algorithm, evidence plan, and unnumbered next-task
shape.

### Decisions this work must not make

It may not activate work, allocate stable identities, approve licensing,
promote evidence, select a production distribution model, or claim target
compatibility.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| One canonical event trace, allocator trace, and stereo 48 kHz WAV from one fixed preset/seed/control history | Host-signal/offline | Byte-stable traces and objective audio invariants across repeated fresh processes | Musical quality, JUCE callback safety, physical MIDI, Ksoloti build/execution, listening approval, production integration |
| One authenticated-JUCE standalone app target | Target build | App and host adapters compile/link; focused UI/slot/controller tests pass | App launch, callback deadline, physical MIDI/audio receipt, listening, packaging, or production integration |

## 3. Reference anatomy

| Function | Observable behavior | Evidence | Keep, transform, or reject | Confidence |
|---|---|---|---|---|
| Six drum sliders | Silent-to-complex per drum | Beat Friend manufacturer page | Keep as six normalized public lane controls | High |
| Enthusiasm | Static loop at zero; more autonomous change upward | Manufacturer page | Transform into explicit seeded phrase decisions | High for behavior, inference for mechanism |
| Preset/meter variants | Individually authored beat/time-signature variants | Manufacturer January 2026 pack notes | Keep preset-oriented authoring; make meter explicit | High |
| A/B-like ranges | Small slider changes reveal alternate material | Manufacturer pack notes | Model as authored, range-eligible variation bundles | Medium-high |
| Swing/fill | Product exposes both; exact algorithms are undocumented publicly | Manufacturer page/UI references | One explicit Schuss swing and one queued authored fill in v0 | High for presence, unresolved for source behavior |
| MIDI | Clock/transport/note I/O and stopped-state slider CC output | Manufacturer MIDI documentation | Defer as adapters around the same event/control semantics | High |

## 4. Adjacent landscape

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Design implication |
|---|---|---|---|---|
| Audio Computer Beat Friend | Hardware instrument | Six authored drum complexity paths plus autonomous variation | Preset- and performance-oriented | Preserve interaction intent, not implementation or patterns |
| Mutable Instruments Grids | Open hardware/software | 3-channel interpolated 8-bit intensity maps, density threshold, one perturbation per channel/pattern | Fixed 32-step 4/4 map and AVR trigger output | Reuse the musical concept only |
| Mutable Instruments Braids | Open hardware/software | Macro-oscillator core, struck models, trigger/excitation and panel AD modulation | One monophonic core at 96 kHz | Embed the MIT DSP closure behind a Schuss-owned drum-voice wrapper |
| Conventional 16-step sequencer | Common product pattern | One binary/probability cell per lane/step | Simple but constrains meter/subdivision | Reject as semantic authority |

## 5. Synthesis and engineering research

| Source | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Grids `pattern_generator.*` and resources at the pinned commit | 5x5 rhythm nodes; bilinear X/Y interpolation; density threshold; held per-pattern perturbation | Exact source | Demonstrates authored-strength thresholding and coherent perturbation | Three lanes, 32 fixed steps, AVR/global state, GPLv3-or-later |
| Braids `macro_oscillator.*`, oscillator files, resources, and stmlib RNG | 48 model dispatch entries; integer core; retained oscillator/model state | Exact source plus native compile/render | Direct MIT-licensed synthesis dependency | Global RNG, large state, original core rate and wrapper behavior need explicit handling |
| Current Schuss runtime v1 | Bounded frame-offset/sequence event queue and fixed-Q27 buffers | Exact local source | Scheduling order and Q27 conversion can be preserved | No semantic event routing, new factories, or sufficient state budget |

## 6. Musical-practice research

Revision 0.6 adds named, situated studies. These are independently authored
translations of documented structural principles, not transcriptions,
repertoire, samples, or claims of authentic performance.

| Practice and context | Source evidence | Structural principle translated | Deliberate context loss and restriction |
|---|---|---|---|
| Rio samba matrices: partido-alto, samba de terreiro, and samba-enredo | IPHAN's bearer-informed *Matrizes do Samba no Rio de Janeiro* dossier describes the Estácio-derived polyrhythmic paradigm, high/mid conduction, counter-beat surdo, collective improvisation, and a documented 3-3-2 relation in some partido-alto practice: https://portal.iphan.gov.br/uploads/ckfinder/arquivos/Dossi-%20Matrizes%20do%20Samba.pdf | A 2/4 low-drum counter-beat, continuous high subdivision, and independently authored syncopated response layers | No lyrics, dance, ensemble identity, named repertoire, or exact timeline is copied. “Study” is mandatory in the display name. |
| Samba performance pedagogy in the University of Michigan Brazil Initiative | Practitioner-led demonstrations identify the surdo pulse, teleco-teco timeline function, four subdivisions per beat, and characteristic non-isochronous phrasing: https://ii.umich.edu/lacs/about-us/brazil-initiative/arts-and-culture-network/samba-residency.html | Separate anchor, conduction, and phrase lanes plus dense high-complexity subdivisions | The v0 scheduler remains quantized except for its existing bounded swing law; it does not claim to reproduce performed samba microtiming. |
| Samba de Roda in the Recôncavo of Bahia | UNESCO describes a living Afro-Brazilian festive practice combining music, dance, poetry, circle participation, improvisation, responsorial song, clapping, and specific instruments: https://ich.unesco.org/en/RL/samba-de-roda-of-the-reconcavo-of-bahia-00101 | Alternating call/answer bundles and clap-like high-lane anchors | The machine cannot represent the roda, movement, social learning, religious context, or practitioner agency. It is only a structural study and requires collaboration before any authenticity claim. |
| Samba-reggae of Salvador, Bahia | Olodum attributes the rhythm to Mestre Neguinho do Samba and situates it in the Afro-Brazilian cultural work of Pelourinho: https://olodum.com.br/banda-olodum/ | A slower 4/4 layered low-drum foundation with answering mid/high percussion | No Olodum composition, branded pattern, recording, visual identity, or pedagogical notation is copied. |
| Maracatu Nação / baque virado in Pernambuco | IPHAN identifies it as a centuries-old Afro-Brazilian processional practice strongly connected to religiosity and extending beyond rhythm and dance: https://www.gov.br/iphan/pt-br/superintendencias/pernambuco/patrimonio-imaterial | Independently authored processional low-drum anchors, bell-like guide, and answer phrases | No sacred or ceremonial toque is represented; the preset is a generic pulse study and must not be described as a Maracatu performance. |
| Candombe llamadas in Sur, Palermo, and Cordón, Montevideo | UNESCO documents the community practice and neighbourhood-specific call/response identity; Montevideo and Universidad de la República sources distinguish piano, chico, and repique roles: https://ich.unesco.org/en/RL/candombe-and-its-socio-cultural-space-a-community-practice-00182 and https://municipioch.montevideo.gub.uy/comunicacion/noticias/percusion | Stable high ostinato, low foundation, and variable answering lane | No neighbourhood toque, encoded call, recording, or claim of candombe authenticity is copied. The community/history embodied by performance is not reducible to a sequencer fixture. |
| Chacarera of Santiago del Estero, Argentina | Argentine institutional and university research describes crossed 6/8 and 3/4 layers, with sharp sounds marking 6/8 and low sounds supporting beats two and three of 3/4: https://www.argentina.gob.ar/cultura/manifestaciones-del-patrimonio-cultural-inmaterial/santiago-del-estero/chacarera and https://sedici.unlp.edu.ar/bitstream/handle/10915/56443/Documento_completo.pdf?sequence=1 | One compound-duple high layer against a three-beat low layer | Dance form, guitar technique, song form, and regional performance timing are omitted; the result is a cross-meter study only. |
| Turkish/Balkan additive-meter practice | Çankırı Karatekin University research summarizes short/long groupings including 5=2+3, 7=2+2+3, and 9=2+2+2+3: https://academicjournals.org/journal/ERR/article-full-text/C20BC0B67144 | Three neutral additive-meter studies with group-boundary anchors and interlocking subdivisions | The generic studies do not claim a named dance, regional style, or authentic *usul*; “aksak” identifies the researched structural family only. |
| Hindustani Jhaptāl | CompMusic/Universitat Pompeu Fabra documents ten mātrās in four unequal vibhāgs, with sam, tālī, and khālī accent roles: https://compmusic.upf.edu/examples-taal-hindustani | A 10/8 cycle grouped 2+3+2+3 with differentiated first, strong, and light divisions | Drum-lane mapping cannot encode bol vocabulary, improvisational grammar, rāga relation, gesture, or gharānā practice. It is a cycle study, not tabla accompaniment. |

The bank therefore uses the suffix “Study” for every culturally situated entry,
retains direct source URLs in its fixture metadata, and forbids copied notation,
audio, names of compositions, sacred material, or authenticity marketing. A
future product release using these labels needs practitioner review, credit, and
compensation decisions beyond this desk-research prototype.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Monotone threshold/layer activation | Grids density maps | Complexity admits authored layers in threshold order | Coherent output at every value | Bad authoring creates abrupt or overfull transitions | Sweep every 16-bit control value and check monotonic base-layer inclusion plus density bounds |
| Counter-addressed deterministic randomness | Algorithmic generation practice | Phrase decisions keyed by preset fingerprint, seed, phrase index, and control-history epoch | Repeatability without per-hit coin flips | Control edits or traversal order alter unrelated decisions | Compare traces across block sizes and fresh processes |
| Resource-pool scheduling | Voice allocation/polyphony | Four replaceable physical cores serve six logical roles | Better utilization than fixed lane ownership | Priority starvation or clicky steals | Adversarial same-sample fixtures and click/energy bounds |

## 8. Novelty map

### Common elements

Thresholded rhythm density, authored patterns, seeded variation, percussion
recipes, voice allocation, and oscillator pooling each have established prior
art.

### Less-common combination found

The less-common product combination is six independently traversable authored
complexity paths, coherent phrase-level autonomy, arbitrary rational timing,
semantic hit mirroring, and a dynamically reassigned four-core macro-oscillator
pool inside one authoring/runtime model.

### Proposed contribution

Within the bounded sources inspected, Schuss can contribute an explicit,
deterministic semantic contract that separates controller presentation,
musical event generation, synthesis allocation, and MIDI adaptation. No claim
of universal novelty is made.

### Rejected directions

| Direction | Reason rejected | Evidence or risk |
|---|---|---|
| Direct Grids embedding | Wrong lane/timing/preset model and GPL distribution coupling | Exact source/license |
| Copied Grids tables | Tables are expressive authored data with GPL headers | Copyright/license risk |
| Independent per-hit enthusiasm probability | Breaks coherent phrases and anchor stability | Product intent and Grids comparison |
| Six fixed Braids voices | Contradicts four-core product decision and wastes pool semantics | Product architecture |
| Fixed 16-step authority | Cannot naturally express the required tuplets and odd meters | Product requirements |
| Raw MIDI as rhythm truth | Couples musical semantics to an integration protocol | Schuss layer contract |

## 9. Recommended architecture

### Signal and ownership flow

```text
controller selector / UI
  -> Task-034-style performance-control semantics
  -> public instrument controls
  -> rhythm preset + deterministic generator state
  -> timed DrumHit stream
       -> four-voice Braids pool -> stereo mixer -> audio
       -> future MIDI-note mapping -> output scheduler
```

Recommended product shape: staged hybrid **C**. A machine/presentation owns one
instrument and its public controls; the reusable semantic primitives are rhythm
definition, timed `DrumHit`, lane recipe, and allocator policy. The first proof
may package these behind one noncanonical Instrument Lab implementation while
retaining explicit traces and documented internals. Accepted graph/runtime
promotion waits for a successor event/state/provider contract.

### Rhythm contract

- Meter: numerator, note-value denominator, and phrase bar count.
- Position: reduced rational quarter-note units `(numerator, denominator)`;
  denominator 1..64 in v0. No MIDI PPQ is persisted.
- Pattern: independently authored layers. A layer has one 16-bit complexity
  threshold and a list of lane events. Eligibility is `C_lane >= threshold`.
- Optional variation group: authored alternatives with explicit complexity and
  enthusiasm eligibility; one entire bundle is selected at a phrase boundary.
- Event: lane key, rational position, velocity U15, articulation U8, stable
  definition-local order. Model/pitch are not embedded in the hit.
- Compiled scheduling: exact rational positions are converted to absolute sample
  targets with integer arithmetic and a carried remainder. Equal targets order
  by `(sample, lane_order, local_event_order)`.

Examples in quarter-note units:

```text
4/4: K at 0/1, 2/1; S at 1/1, 3/1; H at 0/1, 1/2, 1/1, ... 7/2
triplets: H at 0/1, 1/3, 2/3 within beat 1, repeated per quarter
quintuplets: H at 0/1, 1/5, 2/5, 3/5, 4/5 within beat 1
7/8: bar length 7/2 quarters; anchors at 0/1, 3/2, 5/2 for a 3+2+2 test grouping
```

### Complexity

```text
eligible_base_events(lane, C) = union(layer.events for layer if C >= layer.threshold)
```

Base layers are monotone and authored as anchor, groove, syncopation, ghost, and
ornament strata. A validation sweep must prove that raising complexity never
removes base events. Range-eligible A/B overlays are explicit variation bundles,
not hidden exceptions to the base rule.

### Enthusiasm

At `H=0`, always choose the preset's base bundle and do not perturb events. At
each phrase boundary for `H>0`, a fixed counter-based selection function keyed
by `(preset_fingerprint, user_seed, phrase_index, control_history_epoch)` chooses
at most one eligible authored variation per group. `H` controls the maximum
variation tier and selection budget. Decisions apply to whole bundles/bars;
there is no independent per-event coin flip. Moderate tiers may add/replace
ghost or syncopation bundles but cannot remove anchor events. Only explicitly
authored high-tier bundles can suppress anchors. The generated trace must be
identical for fixed preset, seed, controls, and control-change sample times.

### Tempo, swing, and fill v0

- Internal tempo is required for an audio-producing proof.
- One swing transform is included: a preset declares a swingable pair unit; a
  normalized control moves the internal pair boundary from 1/2 toward a bounded
  maximum while keeping the pair endpoint fixed. Nonbinary events are unswung
  unless explicitly tagged into a swing group.
- Fill is one trigger action that queues an authored one-bar overlay at the next
  declared boundary. Cross-bar fills and autonomous fill grammar are deferred.
- External clock and transport are deferred.

### Drum recipe and voice wrapper

Small v0 synthesis recipe:

```text
model, base_pitch_q7, timbre_u15, color_u15,
amp_decay_ms, transient_decay_ms,
pitch_env_amount_q7, timbre_env_amount_s15, color_env_amount_s15,
gain_q15, pan_s15
```

Lane allocation policy adds `choke_group` and `priority`; velocity scales level
linearly in v0. A fixed short attack/de-click is pool policy, not per-recipe.
One exponential transient envelope drives the three signed tone destinations;
one Schuss-owned amplitude envelope bounds lifecycle and makes continuous
models such as CYMBAL usable as drums. Braids' internal model excitation is
still triggered. The original panel AD is optional behavior outside
`MacroOscillator`, so it is not the wrapper's authority.

For assignment to a different lane/recipe, fully zero the core's storage,
reconstruct it, call `Init`, set model/pitch/parameters, issue `Strike`, and set
sync on the first core sample. This is required because `DigitalOscillator::Init`
does not clear its delay-line union. Same-recipe retrigger preserves core state
and issues Strike/sync unless a recipe explicitly requests hard reset.

The core renders at 96 kHz in 24-sample units. A deterministic fixed 2:1
decimator produces the 48 kHz host stream. Int16 core samples are promoted to
Q27, enveloped/mixed with wider accumulators, then saturated once at stereo
output. The exact decimator and gain bounds must be frozen and tested before
implementation acceptance.

### Deterministic fully pooled allocator

Hits sharing a sample are processed as a batch in descending incoming priority,
then lane order, then local event order.

1. Apply same-group choke to active victims; reuse the lowest-slot choked victim.
2. Otherwise take the lowest-index idle voice.
3. Otherwise take the below-tail-threshold voice with lowest envelope level,
   then oldest onset, then lowest slot.
4. Otherwise steal only a voice whose priority is no greater than the incoming
   priority; choose lowest priority, then lowest envelope level, oldest onset,
   lowest slot.
5. If every active voice is more important, drop the incoming hit and count it.

Choke/steal resets use a fixed bounded de-click policy and emit a trace record.
Kick and snare are protected by priority rather than reserved slots. This keeps
all four cores available while making simultaneous overload deterministic.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Host CPU | Four cores, 96 kHz, 24-frame core block; seven runs | Apple M1 Pro / clang 16 tight-loop benchmark | Slowest all-model case CYMBAL median 0.587% of one core; percussion-set median 0.370% | Feasible host primitive; not real-time proof |
| Full-reset switching | Four voices reset/reassigned at 10 Hz each | Seven-run benchmark | Median 0.379% of one core | Feasible in isolation |
| Core state | `sizeof(MacroOscillator)=17,064`; four = 68,256 bytes before wrapper | Compiled arm64 source | Current runtime v1 total state ceiling 65,536 bytes | Does not fit current ABI |
| Host sample/numeric contract | 48 kHz fixed Q27 | Current Schuss runtime | Braids is int16/96 kHz core | Explicit 2x render, decimation, Q27 adapter needed |
| Source closure | Four Braids `.cc` files plus headers/resources and stmlib RNG | Compiler dependency closure | Generated resources dominate source size | Native compile passed |
| Ksoloti | STM32F-derived integer source; current target record exposes 48 kHz/16-frame runtime and several linker regions | Source/record inspection only | Exact code/data placement and deadline unknown | Source portability plausible; build/resource/realtime compatibility unresolved |
| License | Braids files MIT; Grids files/data GPLv3-or-later; used stmlib utility is MIT | Exact headers/repository license | Distribution notice/source obligations differ | Distribution review required |

Benchmark scope excludes decimation, envelopes, allocator, mixer, JUCE callback,
other system load, sustained deadline measurement, and listening.

## 11. Minimal experiment

### Central hypothesis

One independently authored rational-time preset can drive six logical lanes
through a deterministic four-core pooled allocator and produce a repeatable,
bounded stereo groove without MIDI or accepted schema changes.

### Smallest vertical slice

A nonproduction Instrument Lab native-host proof containing the exact Braids
source closure, four authored rhythm definitions, rhythm compiler/generator, allocator, envelopes,
mixer, trace writer, and offline renderer. It does not enter the canonical
catalog/runtime/provider path.

### Frozen experiment inputs

| Field | Bound value |
|---|---|
| Host sample rate / core rate / core block | 48,000 Hz / 96,000 Hz / 24 core samples |
| Deterministic seed | One literal nonzero 32-bit value in fixture |
| Event/sample convention | Rational quarter-note position -> absolute host sample by integer mapping with carried remainder |
| Conditions | Static H=0; moderate H; complexity sweep; simultaneous six-hit overload; hat choke; full-reset reassignment; triplet; quintuplet/7-8 |
| Comparator | Independent per-hit probability generator with matched mean density, used only to falsify coherence assumptions |
| Outputs | Canonical event JSON, allocator JSON, stereo WAV, render metrics, source/license manifest |
| Objective tolerances | Byte identity for traces; exact frame count; finite samples; no overflow; peak and DC bounds; expected allocation decisions |
| Retention | Task-owned nonproduction evidence path chosen only after activation; current research files remain disposable `/tmp` artifacts |

### Listening protocol

Deferred. A later listening round should blind static/moderate/high enthusiasm
renders and compare phrase coherence, anchor retention, steal artifacts, and
usefulness across complexity sweeps. No source or host-signal result promotes a
musical-quality claim.

### Stop or pivot conditions

- Pivot from full pooling if adversarial fixtures or listening reveal frequent
  unacceptable kick/snare loss despite priority policy.
- Pivot the Braids wrapper if exact reset/decimation equivalence cannot be made
  deterministic or source/license closure cannot be distributed acceptably.
- Pivot timing if rational-to-sample mapping differs across block sizes.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Current result |
|---|---|---|---|
| Grids concept is useful | Exact algorithm/source comparison | Research/source | Supported |
| Grids code/data should be reused | Architecture/license comparison | Proposal | Rejected for v0 |
| Braids core compiles natively | Exact pinned closure compile | Host-structural | Passed in disposable clone |
| Four cores are CPU-practical on current Mac | Repeated tight-loop benchmark | Host measurement | Supported, bounded |
| Four cores fit current `schuss_rt` v1 | Size versus exact ceiling | Host-structural | Rejected |
| Recommended groove model is deterministic | Fresh-process trace and block-size equivalence | Host-signal | Not run; implementation required |
| Pool sounds acceptable | Blind listening protocol | Listening | Not run |
| Ksoloti compatible | ARM build/link, target render/deadline evidence | Target | Not run/unresolved |
| Production ready | Integrated release evidence | Production | Not run |

## 13. Implementation plan

### Files expected to change

Only the existing nonproduction proposal/prototype/evidence subtree and its
prototype-local CMake/UI/host files may change. Accepted records, schemas,
factory registries, runtime providers, task state, and governance remain out of
scope.

### Focused tests

- Exact upstream provenance/license and dependency closure.
- Core model reset/trigger/render fixtures.
- Rational validation and sample mapping across block sizes.
- Complexity monotonicity and H=0 stability.
- Seed/control-history determinism across fresh processes.
- Allocation/choke/drop/steal trace matrix.
- WAV frame/peak/DC/finiteness and deterministic hashes where portable.

### Adjacent regression tests

No accepted runtime boundary changes are proposed in the first proof. Run the
routine Schuss `current` profile only if the activated task adds repository
code/docs that the manifest classifies as current inputs.

### Expensive or hardware checks

Native build/render is explicitly gated. The pure LC3 selector adapter is
host-structural and the optional authenticated JUCE executable is target-build
evidence. App launch, callback timing, physical MIDI/audio receipt, Ksoloti,
listening, and release checks remain excluded.

### Deferred work

Accepted rhythm/recipe/event schemas, runtime event routing and expanded state
budget, provider binding, a true streaming real-time Core, MIDI note/output/
clock, Ksoloti feasibility, pattern/preset authoring UI, AI authoring, and
publication.

### Dependency contract

Candidate pin: Eurorack
`08460a69a7e1f7a81c5a2abcc7189c9a6b7208d4`, stmlib
`e3bd7c9cc00e4364166f9905c0509b6ffd0535ec`. Allowed modules are the exact
compiler-derived Braids/stmlib closure listed in the research report. Braids
and used stmlib files retain MIT notices. Grids code/data are forbidden inputs.
Network/download policy, local-cache authentication, source archive hashes, and
distribution review must be frozen by the activated task.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Notes or proof gap |
|---|---|---|---|---|
| BF-01 | EVIDENCE | Beat Friend exposes six complexity sliders and Enthusiasm | Manufacturer product page | Public behavior only |
| BF-02 | EVIDENCE | Pack notes include individual meters, A/B-like ranges, triplets, quintuplets, and polyrhythm | Manufacturer January 2026 pack page | Does not reveal firmware model |
| BF-03 | INFERENCE | Smallest plausible source model is authored layers plus phrase variants | BF-01/02 | Not a reverse-engineering claim |
| GR-01 | EVIDENCE | Grids uses 25 3x32-byte nodes, bilinear interpolation, density threshold, and held perturbation | Pinned source | Exact source |
| GR-02 | EVIDENCE | Grids timing is 32 fixed steps at 8 steps/quarter | Pinned source | Exact source |
| GR-03 | EVIDENCE | Grids code and rhythm resources are GPLv3-or-later | Exact file headers | Distribution implications need counsel |
| BR-01 | EVIDENCE | Minimal tested native closure excludes UI/hardware firmware | Compiler dependency closure | Host compile only |
| BR-02 | EVIDENCE | KICK/SNARE consume Strike; CYMBAL is continuous raw material | Pinned source | External amp envelope required for voice lifecycle |
| BR-03 | EVIDENCE | Four cores exceed runtime v1 total state ceiling | Compiled sizes plus local contract | Wrapper increases the excess |
| BR-04 | EVIDENCE | Four cores are inexpensive in a tight-loop M1 Pro benchmark | Disposable benchmark | Not real-time proof |
| SC-01 | EVIDENCE | Task 034 separates controller semantics but executes none | Current task/records | Reusable unchanged at structural level |
| SC-02 | EVIDENCE | Runtime v1 orders raw MIDI but does not route it to synthesis | Current source | Needs successor/adaptation |
| AR-01 | HYPOTHESIS | Fully pooled priority allocation will sound better/use resources better than fixed slots | Proposed experiment | Needs render/listening evidence |
| MP-01 | EVIDENCE | Rio samba sources distinguish foundation, conduction, and syncopated phrase roles in a primarily 2/4 interlocking texture | IPHAN dossier; University of Michigan practitioner residency | Supports independently authored role translation, not a copied pattern |
| MP-02 | EVIDENCE | Samba de Roda, samba-reggae, Maracatu Nação, and candombe are living situated practices with social meanings beyond their drum patterns | UNESCO, Olodum, IPHAN, Montevideo sources | Requires “Study” labels and explicit non-authenticity boundary |
| MP-03 | EVIDENCE | Chacarera supports simultaneous 6/8 and 3/4 organization | Argentina cultural page; Universidad Nacional de La Plata research | Supports one cross-meter fixture only |
| MP-04 | EVIDENCE | Additive meters can be organized as 2+3, 2+2+3, and 2+2+2+3 | Çankırı Karatekin University research | Supports neutral 5/8, 7/8, and 9/8 studies |
| MP-05 | EVIDENCE | Jhaptāl is a ten-mātrā cycle with four unequal divisions and differentiated accent roles | CompMusic/UPF | Supports a 2+3+2+3 cycle study, not a thekā transcription |
| RT-01 | HYPOTHESIS | A fixed-capacity streaming Core can apply controls within one supported callback block while preserving deterministic authored-event and four-voice-pool behavior | Revision 0.6 experiment | Requires block-partition parity, control-latency fixtures, no-allocation inspection, and measured callback-kernel timing |

## 15. Open questions and decision gate

### Decisions requiring the user

1. Approve or reject the staged-hybrid product shape and fully pooled v0 policy.
2. Choose whether v0 complexity may include range-based A/B replacements or
   must remain strictly additive/monotone.
3. Choose whether the first preset should expose one manual fill and one binary
   swing law, or defer both until after the first deterministic groove.
4. Choose whether direct MIT Braids source reuse is acceptable in the eventual
   distribution model, subject to formal review.

### Recommendation

Approve the design direction only, then activate one unnumbered-at-draft
Instrument Lab task for the deterministic offline vertical proof. Do not yet
approve accepted schemas/runtime ABI changes or Ksoloti work.

### Approval record

The user approved revision 0.2's deterministic offline vertical slice on
2026-08-21 and then explicitly amended the mapping scope on the same date to
reuse Tide Pit's regular Launch Control 3 mapping topology. Revision 0.3 binds
that mapping amendment. The user then requested an instrument UI; revision 0.4
adds a bounded standalone audition shell without promoting app-launch,
real-time, connected-device, listening, or production evidence.
After testing that app and reporting it “pretty cool,” the user requested
selectable rhythm types/time signatures and selected-lane voice shaping;
revision 0.5 freezes that advancement without promoting the revised app's
launch, device, real-time, formal listening, or production evidence.
After testing revision 0.5 and reporting it “pretty good,” the user requested
the literal physical layout of buttons one through six as lane selectors, the
bottom six encoders as the selected lane's shaper, realtime audible editing,
and a substantially researched bank of about fifteen rhythms and at least five
meters. Revision 0.6 freezes that uninterrupted prototype advancement.

## 16. Implementation and LC3 mapping record

Revision 0.2 was implemented as the noncanonical Instrument Lab prototype at
`research/prototypes/generative-drum-machine/`. Its frozen host-signal results
and evidence limits are recorded in `contract/RESULTS.md` and
`contract/GAPS.md`.

Revision 0.3 reuses the exact fingerprinted physical topology already used by
Tide Pit:

- regular Novation Launch Control 3, not an XL model;
- Custom Mode slot 1, MIDI channel 16;
- 16 absolute 7-bit encoders on CC20–35;
- eight momentary buttons on CC40–47, press 127 and release 0;
- Merge off, MIDI Thru off, main USB MIDI output;
- wrong-channel, unknown-CC, unassigned-control, invalid-value, press, and
  release outcomes remain distinct and counted by a later host adapter.

The instrument-specific bindings are:

| LC3 control | Semantic control |
|---|---|
| Top encoders CC20–25 | Kick, snare, hat, percussion 1, percussion 2, percussion 3 complexity |
| Top encoder CC26 | Enthusiasm |
| Top encoder CC27 | Tempo, round-half-up from 30,000 to 240,000 milli-BPM |
| Bottom encoder CC28 | Swing U15 |
| Bottom encoders CC29–35 | Selected-lane Tune, Timbre, Color, Decay, Pitch Env, Timbre Env, and Level |
| Button CC40 | Fill on press 127; release 0 is accepted but does not dispatch twice |
| Button CC41 | Advance to the next authored rhythm preset on press 127 |
| Buttons CC42–47 | Select kick, snare, hat, percussion 1, percussion 2, or percussion 3 and enter shaping; pressing the selected lane again exits shaping |

All continuous values translate through explicit integer round-half-up laws.
The adapter terminates at public drum-machine controls; it never sends raw MIDI
to the rhythm or Braids layers. Revision 0.5 consumes the previously unassigned
selectors through one explicit performance-state reducer. A shaping encoder is
a no-op unless one lane is selected. This amendment authorizes compiled
descriptors, a pure CC mapping function, semantic-application tests, and
controller-topology fingerprints only. It does not authorize rewriting the
Custom Mode or promoting endpoint receipt into accepted runtime evidence.

## 17. Desktop UI amendment

Revision 0.4 authorizes one prototype-local JUCE 8.0.15 standalone target. The
UI is an instrument presentation, not a new semantic authority. Both on-screen
gestures and MIDI CC messages pass through the generated LC3 mapping and end at
the same public `Controls`/fill semantics.

### Presentation surface

- Six lane cards show kick, snare, hat, percussion 1, percussion 2, and
  percussion 3 complexity plus accepted-state activity.
- A global strip exposes Enthusiasm, Tempo, Swing, and one momentary Fill
  action.
- A compact phrase-progress display and render-generation status show what the
  audition engine is actually playing.
- MIDI input enumeration/selection and receive/last-CC diagnostics are host
  presentation facts only; no endpoint identifier enters the instrument,
  rhythm definition, `DrumHit`, allocator, or DSP state.
- The visual language is Schuss-owned and deliberately does not copy Beat
  Friend branding, panel artwork, typography, or trade dress.

### Audition-host boundary

The existing Core is an offline deterministic renderer, not a prepared
deadline-proven streaming sequencer. Therefore the first UI uses a bounded
audition architecture:

```text
UI or LC3 CC
  -> generated selector map
  -> accepted public controls / fill token
  -> non-audio render worker prepares the next deterministic phrase
  -> immutable phrase slot
  -> audio callback performs bounded playback and slot exchange only
  -> stereo device output
```

Three phrase slots separate rendering from playback. The worker may allocate
and invoke the existing offline renderer only while a slot is free. The audio
callback never invokes Braids rendering, JSON, filesystem I/O, UI work, MIDI
enumeration, or an unbounded scheduler; it reads one immutable slot and swaps
only at a phrase boundary. If a fresh slot is unavailable it repeats the
current non-fill phrase instead of blocking or emitting partial evidence. A
completed fill slot is never repeated: if it is the underrun victim, playback
releases it and emits zero until a new slot is ready. Control changes apply to
a subsequently prepared phrase. If a ready fill slot becomes stale before
activation, its bounded fill token returns to the queue; otherwise Fill is
consumed exactly once by the next activated prepared phrase.

This architecture is an intentional prototype limitation: a built standalone
target proves compilation and host-boundary structure, not callback headroom,
continuous voice tails across phrase swaps, physical controller receipt,
audible quality, or production readiness. A later true streaming Core should
replace the preview slots without changing the public control or `DrumHit`
semantics.

### UI acceptance

- A pure UI projection model formats accepted public state and has focused
  tests independent of JUCE.
- GUI changes and MIDI CCs traverse the same generated selector mapping.
- UI feedback follows accepted state, never uncaptured raw input.
- The worker/audio slot protocol has deterministic unit coverage for free,
  rendering, ready, active, stale, and repeat-on-underrun transitions.
- Stale fill retirement restores its token, and a fill slot is never selected
  as the repeat-on-underrun loop.
- The authenticated JUCE 8.0.15 standalone target builds from an
  operator-supplied source tree with fetching disabled by default.
- The frozen offline render manifest remains byte-identical.
- No app is launched and no audio or MIDI endpoint is accessed as part of the
  build evidence unless separately authorized.

## 18. Selectable rhythm bank and per-lane voice shaping amendment

Revision 0.5 responds to the user's first listening/device trial. The user
reported that the built instrument was “pretty cool” and requested two bounded
advancements: several selectable rhythm types in different time signatures,
and a voice-shaping mode that edits the selected logical drum through the
remaining controller encoders. This is informal user feedback, not a completed
listening protocol or real-time/device promotion for the revised build.

### Authored rhythm bank

The first rhythm bank contains exactly four independently authored definitions:

| Index | Name | Meter | Phrase | Timing character |
|---:|---|---|---:|---|
| 0 | First Light | 4/4 | four bars | Existing straight/syncopated reference with triplet and quintuplet ornaments |
| 1 | Three Turn | 3/4 | four bars | Three-beat anchors, rotating percussion answers, and triplet detail |
| 2 | Rolling Six | 6/8 | four bars | Compound-duple eighth-note flow with dotted-quarter anchors |
| 3 | Five Across | 5/4 | two bars | 3+2 anchors plus authored quintuplet ornament material |

Each definition owns its meter, phrase-bar count, event slice, variation
eligibility, fill material, denominator LCM, name, and fingerprint. Rhythm
selection is a public semantic integer in `[0, 3]`. CC41 press advances modulo
four; release is accepted without a second advance. The desktop selector may
choose a literal index through the same public-state reducer. Selection changes
become audible only at a prepared phrase boundary. The current phrase is never
rescaled, truncated, or reinterpreted in place.

The rational position law becomes meter-dependent. For meter `N/D`, one bar is
`N * 4 / D` quarter-note units and one phrase is `phrase_bars` times that
length. Every authored event must satisfy `0 <= position < bar_length`; reduced
denominators remain bounded by 64. Absolute host frames are computed with
checked integer rational arithmetic. No MIDI PPQ or shared pulse grid becomes
authoritative.

### Voice-shaping state and parameter laws

Logical lanes retain one shape bank each. Selection state is presentation and
performance state; it does not change rhythm events or allocate a physical
Braids core. Pressing CC42–47 selects the named lane and enters shaping mode.
Pressing the already-selected lane exits shaping. Selecting another lane moves
the edit focus directly. Shape values persist independently for all six lanes
during the process lifetime.

Every shape encoder stores one 7-bit public value. `64` is neutral and must
render byte-identically to the authored recipe. Values are resolved only when a
phrase render snapshot is prepared:

| CC | Parameter | Resolution from U7 value `v` |
|---:|---|---|
| 29 | Tune | Piecewise linear offset around `v=64`, bounded to -24..+24 semitones, then clamped to Braids pitch range |
| 30 | Timbre | Piecewise signed offset around the authored Timbre, bounded to the U15 model domain |
| 31 | Color | Piecewise signed offset around the authored Color, bounded to the U15 model domain |
| 32 | Decay | Piecewise interpolation from one-quarter authored decay at `0`, exact authored decay at `64`, to four-times authored decay at `127`; generated Q31 multipliers avoid callback-time transcendental work |
| 33 | Pitch Env | Piecewise signed offset of up to 16 semitones around the authored transient pitch amount |
| 34 | Timbre Env | Piecewise signed offset around the authored timbre-envelope amount |
| 35 | Level | Piecewise linear gain scale: zero at `0`, unity at `64`, and two-times at `127`, followed by the existing output saturation/counting boundary |

Model, pan, choke group, priority, Color envelope, and transient-decay time are
not editable in this slice. This keeps model-switch/reset behavior, spatial
identity, and allocation policy stable while exposing a musically useful
shaper. Shaping an inactive lane changes no audio until that lane's next hit.
Changing a shape invalidates only not-yet-active preview slots; active audio
remains immutable until the phrase boundary.

### UI and controller presentation

The desktop UI adds a rhythm selector, one shaping button per lane card, and a
seven-knob shaping panel. The panel is disabled when no lane is selected. It
shows the selected lane and its accepted stored U7 values, not raw MIDI input.
Changing lane focus updates the panel without scheduling a new audio render;
changing an actual shape value schedules a later phrase generation. The
physical Custom Mode remains the exact Tide Pit topology and requires no
controller rewrite beyond the already documented CC20–35/CC40–47 setup.

### Revision 0.5 acceptance

- The generator rejects events outside each meter-specific bar and emits four
  stable descriptors with exact slices/fingerprints.
- All four rhythms produce deterministic events; ordinary 4/4, 3/4, compound
  6/8, and 5/4/quintuplet positions have exact frame fixtures.
- Neutral shape banks preserve the prior recipe path exactly; each non-neutral
  parameter changes only the selected lane recipe and stays in declared bounds.
- CC41 and CC42–47 press/release state machines are exhaustive, and CC29–35
  cannot mutate a lane without active selection.
- Rhythm or sound changes invalidate prepared generations, while focus-only
  changes do not rerender audio.
- The app target, structural suite, objective render matrix, ready bundle,
  Instrument Lab validation, and Schuss `current` profile pass after evidence
  fingerprints are refreshed.

The revision deliberately does not prove the subjective quality of all four
rhythms or parameter ranges. The next user-run audition is the appropriate
listening/device gate; any requested range or authoring changes remain
prototype-local until separately accepted.

## 19. Realtime surface and fifteen-study bank amendment

Revision 0.6 supersedes revision 0.5's phrase-preview host mechanics while
preserving its public controls, rational authored-event representation,
semantic `DrumHit`, fully pooled allocator, source closure, and accepted-state
UI rule.

### Goal and bounded implementation contract

The goal is to make the instrument directly editable while it sounds and to
expand its authored vocabulary enough for meaningful audition. In scope are a
prototype-local fixed-capacity streaming Core, the corrected regular LC3
physical layout, exactly fifteen researched rhythm studies, accepted-state UI
updates, deterministic realtime-control fixtures, an offline callback-kernel
benchmark, and a rebuilt unlaunched JUCE target. Out of scope remain accepted
Schuss records/schemas/providers, task activation, controller rewriting,
external clock, MIDI output, app launch, hardware access, a user pattern
editor, persisted presets, cultural authenticity claims, Ksoloti, publication,
and production promotion.

Inputs are revision 0.5's validated Core and source lock, the exact regular LC3
topology, the cited public/institutional research, and the user's current
listening/layout feedback. Deliverables are revised proposal/bundle artifacts,
one fifteen-study fixture and generated descriptor, one streaming C++ Core, the
JUCE presentation, focused tests, deterministic renders, and bounded timing
evidence. The task may choose independent event details, smoothing constants,
UI layout, and test conditions inside the laws below. It must not copy a
published pattern, change source lineage, invent a hardware claim, or mutate
accepted Schuss authority.

### Literal LC3 layout

The physical surface is regular Launch Control 3 Custom Mode 1, channel 16,
with the existing CC20–35 encoders and CC40–47 momentary buttons. The revised
instrument bindings are:

| Physical control | CC | Public semantic |
|---|---:|---|
| Top encoders 1–6 | 20–25 | Kick, snare, hat, percussion 1–3 complexity |
| Top encoder 7 | 26 | Enthusiasm |
| Top encoder 8 | 27 | Tempo |
| Bottom encoder 1 | 28 | Selected lane Tune |
| Bottom encoder 2 | 29 | Selected lane Timbre |
| Bottom encoder 3 | 30 | Selected lane Color |
| Bottom encoder 4 | 31 | Selected lane Decay |
| Bottom encoder 5 | 32 | Selected lane Pitch Env / Punch |
| Bottom encoder 6 | 33 | Selected lane Level |
| Bottom encoder 7 | 34 | Swing |
| Bottom encoder 8 | 35 | Direct rhythm index, round-half-up into `[0, 14]` |
| Buttons 1–6 | 40–45 | Select/toggle Kick, Snare, Hat, Perc 1, Perc 2, Perc 3 shaping |
| Button 7 | 46 | Immediate one-bar fill overlay on press |
| Button 8 | 47 | Advance rhythm modulo fifteen on press |

The earlier Timbre Env shape field is removed from the live shape bank rather
than hidden on a non-corresponding control. Its authored recipe value remains
fixed. Pressing a lane button again exits shaping; pressing another changes
focus. Bottom encoders 1–6 are semantic no-ops while shaping is inactive.

### Realtime control law

The standalone no longer plays pre-rendered phrase audio. A persistent
streaming Core owns musical phase, event cursor, four Braids cores, envelopes,
allocator metadata, fill state, and output-rate conversion. The host publishes
bounded integer control fields through a race-free atomic snapshot; the audio
callback takes at most one coherent snapshot at block start and performs no
locks, allocation, I/O, JSON, endpoint enumeration, or UI work.

Control timing is exact:

- Continuous controls published before a supported audio callback starts are
  effective in that callback, so host-side semantic latency is at most one
  block (`512 / 48000 = 10.667 ms` at the declared maximum).
- Tune, Timbre, Color, Decay, Pitch Env, and Level target the selected logical
  lane and slew through a fixed 128-sample integer smoothing law. They affect
  that lane's currently active physical voices as well as later hits.
- Complexity and Enthusiasm change eligibility only for authored events whose
  event time has not yet been crossed; no newly eligible past event is fired
  retroactively. A changed Enthusiasm value recomputes the current phrase's
  deterministic whole-bundle selection for future events.
- Tempo changes the phase increment without resetting phase. Swing recomputes
  only not-yet-crossed eligible off-eighth targets.
- A rhythm change restarts the selected study at its downbeat in the next audio
  block. Existing synthesis tails continue until decay, choke, or steal; the
  selector never rewrites a physical oscillator directly.
- Fill starts one independently authored, one-bar overlay at the next audio
  block, normalized from that preset's fill bar. It does not wait for a phrase
  boundary and never replaces semantic base hits.
- Selecting/toggling edit focus has no DSP effect and does not reset phase.

Musical phase uses unsigned Q32 quarter-note units. Each rational source event
is converted once to Q32 with round-half-up; the source rational remains the
authoritative definition. Per-sample phase advance uses a carried 64-bit
remainder from `tempo_milli_bpm * 2^32 / (48000 * 60000)`. A due event fires on
the first sample whose phase reaches or crosses its target. Equal-target events
retain descending priority, lane, and source-ordinal ordering. This introduces
at most one-sample placement difference from the offline absolute-frame
rounding law and is tested explicitly rather than hidden.

### Fifteen-study bank

The bank preserves the first four neutral studies and adds eleven sourced,
independently authored studies:

| Index | Display name | Meter/grouping | Phrase | Relationship |
|---:|---|---|---:|---|
| 0 | First Light | 4/4 | 4 bars | Original neutral reference |
| 1 | Three Turn | 3/4 | 4 bars | Original neutral triple study |
| 2 | Rolling Six | 6/8, 3+3 eighths | 4 bars | Original compound-duple study |
| 3 | Five Across | 5/4, 3+2 quarters | 2 bars | Original quintuplet/odd-meter study |
| 4 | Samba Enredo Study | 2/4 | 4 bars | Independent foundation/conduction/phrase translation |
| 5 | Partido Alto Study | 2/4 | 4 bars | Independent compact call/response and 3-3-2-derived layering |
| 6 | Samba de Roda Study | 2/4 | 4 bars | Independent clap and responsorial-bundle translation |
| 7 | Samba-Reggae Study | 4/4 | 4 bars | Independent slow layered low/mid/high percussion translation |
| 8 | Maracatu Pulse Study | 4/4 | 4 bars | Generic processional pulse study; no ceremonial toque |
| 9 | Candombe Conversation | 4/4 | 2 bars | Stable high/low roles plus variable answer, not a neighbourhood toque |
| 10 | Chacarera Cross-Meter | 6/8 over 3/4 | 4 bars | Independent sharp-compound/low-triple cross-meter study |
| 11 | Aksak Five Study | 5/8 = 2+3 | 4 bars | Neutral additive-meter study |
| 12 | Aksak Seven Study | 7/8 = 2+2+3 | 4 bars | Neutral additive-meter study |
| 13 | Aksak Nine Study | 9/8 = 2+2+2+3 | 4 bars | Neutral additive-meter study |
| 14 | Jhaptal Cycle Study | 10/8 = 2+3+2+3 | 2 bars | Abstracted division/accent study, not tabla thekā |

Every entry owns two coherent variation groups and a one-bar fill overlay,
passes monotone base-layer validation, carries meter grouping and source-
relationship metadata, and uses reduced rational positions bounded by 64.

### Acceptance evidence and non-claims

- Exhaustive mapping tests prove buttons 1–6 and bottom encoders 1–6 have the
  literal relationships above; all press/release, inactive, range, and direct
  rhythm-index values are covered.
- All fifteen definitions validate, generate deterministic events, contain all
  six logical lanes across their full complexity range, retain anchors at
  moderate settings, and cover at least five distinct meter signatures.
- Streaming output is block-partition identical for a fixed timestamped control
  history; control-latency fixtures prove next-block shaping, complexity,
  tempo/swing, rhythm restart, and fill behavior without phrase waiting.
- Source inspection and a focused allocation guard establish that the process
  function contains no dynamic allocation, lock, I/O, or unbounded event scan.
- A synthetic worst-case callback-kernel benchmark records median, p99, and
  maximum duration against 64-, 128-, and 512-frame 48 kHz deadlines on the
  named Mac. This supports only bounded host compute feasibility; it does not
  prove live device scheduling under system load.
- The offline render matrix, source lock, authenticated JUCE build/tests,
  Instrument Lab validation, and Schuss `current` profile must pass after final
  freeze. No automated test launches the app or opens audio/MIDI endpoints.
