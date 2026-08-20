# Cinderwheel trial gap register

This register turns the revision 0.2 proposal audit into actions for the
specification-to-portable-Core-to-JUCE workflow. A frozen trial decision closes
only the design ambiguity named in that row. The final column states the proof
that is still required.

Severity uses `B` for a trial blocker, `H` for a high-risk weakness, and `M` for
an improvement that can remain deferred without invalidating the isolated
vertical slice.

## Freeze disposition

The 2026-08-20 freeze closes every blocker needed for the isolated
source-to-host slice. It does not close the production-instrument or musical
hypothesis. “Closed” below always means at the named prototype evidence level.

| Disposition | Gap IDs | Result |
|---|---|---|
| Closed for the isolated trial | `GOV-01`, `SCOPE-01`, `ARCH-01`, `BUILD-01`, `STAGE-01`, `WAKE-01`, `LEDGER-01`, `LEDGER-02`, `RESET-01`, `MIDI-01`, `GEST-01`, `SAFE-01`, `RECORD-01` | The approved bytes and scope are frozen; Core, renderer, mapping, state/safety semantics, CMake targets, hashes, and evidence record exist and pass focused validation. |
| Partially closed | `UND-01`, `BODY-01`, `PICKUP-01`, `DET-01`, `JUCE-01`, `DEVICE-01` | Coefficients, surrogate signal, simulated soft pickup, repeated render matrix, bounded adapter, exact fetch build, and standalone physical-input source path pass. Acoustic pitch/off isolation, external gesture fixture, physical takeover/capture, callback lifecycle, reconnect, and real-time behavior remain open. |
| Deliberately deferred | `GRAPH-01`, `DEP-01`, `BASE-01`, `HYP-01`, `COMP-01`, `RT-01`, `LISTEN-01`, `LIC-01` | These require production identities/execution, dependency/distribution review, exact Tide Pit lineage, comparator/listening work, callback measurement, physical-device evidence, or release decisions outside this trial. |

## Process improvements exposed by the trial

Future sonic proposals should add these before implementation approval:

1. Define “working” as a named artifact and evidence level: library, offline
   renderer, standalone app, plugin, real-time session, or physical device.
2. Provide a machine-readable gesture schedule, condition count, comparator,
   seed, output names, tolerances, and artifact-retention policy. The v0
   renderer's hard-coded schedule is deterministic but too difficult to audit
   independently from its implementation.
3. Specify executable DSP equations and gain normalization, not only signal-flow
   prose. The first render's ceiling/DC failure was invisible to compile and
   scheduler tests.
4. Include a state-by-operation matrix for Reset, Panic, Freeze, mode changes,
   pending controls, buffers, random state, and event provenance, with exact
   sample-boundary conventions.
5. Separate controller surface assignments, semantic transforms, gesture state
   machines, application feedback, and physical endpoint/configuration proof.
   Generate the compiled descriptor from the fixture or exhaustively compare
   them; the current Python and C++ checks validate their respective artifacts
   but do not share one source of truth.
6. Bind dependency commit/archive hash, allowed modules, local-cache
   authentication, download policy, and distribution review. Version macros
   alone do not authenticate a supplied JUCE tree.
7. Register deterministic render repetition and host-adapter parity as tests;
   keep build, host signal, real-time, device, and listening promotion gates
   independent.
8. Decide whether reference WAVs are checked in, stored externally, or
   reproducible-only. This trial retains 198 MiB under ignored `build/` paths
   and records compact cryptographic hashes in `RESULTS.md`.

| ID | Gap | Severity / owner / stage | Frozen trial decision | Proposal, template, or process improvement | Proof still required |
|---|---|---|---|---|---|
| GOV-01 | The proposal says `proposed` and the repository has no active task. | B / trial owner / activation | Bind only revision 0.2, Git blob `c075035b9c844eedd29f7f172e557cc985ad6d48`, and SHA-256 `d9b3a50cde3c25a4db6324bd8d20f1a65eaefcbd1ac8e9e7a42adc80713b5e84`; record the 2026-08-20 user prompt as approval for this isolated trial. | Proposal template should include approval date, approver/request reference, immutable fingerprint, and exact implementation-task link. Governance process should activate the bounded task before shared changes. | Fingerprint preflight and final diff prove that only the approved revision and scope were used. |
| SCOPE-01 | “Working JUCE instrument” could mean offline library, standalone app, plugin, physical session, or integrated Schuss instrument. | B / trial owner / task contract | Build one portable JUCE-independent Core, deterministic offline renderer, and thin optional JUCE standalone adapter. No plugin format and no physical device run are acceptance requirements. | Proposal template should require one named host artifact and an operational definition of “working.” | Core/tests/render verification and exact pinned-JUCE build; real-time and device remain separate. |
| ARCH-01 | A direct JUCE implementation could be mistaken for a canonical Schuss graph or instrument. | B / architecture owner / integration | The prototype Core is musical authority only inside this experiment; JUCE is an adapter. No canonical graph, instrument, binding, provider, runtime factory, or stable ID is created. | Every prototype proposal should name whether it is standalone evidence or production-model implementation and cite the integration gate. | Boundary/diff review proves no canonical/shared record or runtime change. |
| GRAPH-01 | The proposal contains a control table but no executable Task 034 performance graph; Task 034 currently provides structural records, not an executor. | B for production, M for prototype / performance-control owner / controller integration | Use the explicit local mapping fixture and simulated CC adapter for the trial. Defer formal graph records and execution until the mechanism passes. This is correct because it tests the proposed semantics without allocating false production identity or using a controller-to-DSP shortcut. | Proposal template should distinguish a prototype input map, a canonical performance-control graph, a performance configuration, and runtime execution evidence. | Prototype mapping tests now; later exact instrument facets, reusable control contracts, graph/configuration validation, executor, and runtime evidence. |
| BUILD-01 | The proposal's expected files omitted CMake targets, host entry points, WAV/ledger formats, and test registration. | B / build owner / source | Add a prototype-local CMake build: Core/tests without JUCE; optional adapter only when enabled; no shared engine edits. Use stable fixture and artifact paths. | Implementation plans should list build-system files, target names, dependency gates, output formats, and verification commands. | Fresh configure/build/test plus artifact inventory and hashes. |
| DEP-01 | JUCE dependency identity and allowed modules could drift or expand silently. | H / host owner / dependency | Use Schuss's pinned JUCE 8.0.15 commit/archive for private development. Keep JUCE types out of Core and do not add `juce_dsp`; dependency installation and source-lock changes are out of scope. | Proposal template should bind exact dependency version/hash, modules, use boundary, download/cache policy, and distribution gate. | Source/hash authentication and linked-module review; distribution remains unreviewed. |
| BASE-01 | The live Tide Pit source was referenced only by path/date, not commit/blob hashes, while its repository contains unrelated dirty work. | H / research owner / source lineage | Do not copy or modify Tide Pit in this slice. Treat revision 0.2 text as the Core's source contract; require an exact Tide Pit fingerprint before the later lineage comparison. | Local-source citations should include repository commit, per-file hashes, dirty-state scope, license, and whether the source is normative or observational. | Later exact-source audit and preservation diff; no current Tide Pit implementation claim. |
| HYP-01 | H1 combines scheduler usefulness with preservation of recognizable Tide Pit identity, but the source-neutral surrogate can test only the former. | B for the claim, not the slice / research owner / acceptance | Split evidence: H1a tests causal, learnable Undertow/Wake counterpoint; H1b tests Tide Pit identity later with exact source and listening. | Proposal template should require each hypothesis to map to one falsifying experiment and one attainable evidence level. | H1a objective/render evidence now; H1b exact-source comparison and documented listening later. |
| STAGE-01 | Four-stage interpolation, transition timing, defaults, rate curve, pitch/scale tables, mutation, Memory, Lock, and seed were not fully specified. | B / DSP owner / Core | Freeze deterministic equations, defaults, transition sample convention, seed/state, and mappings in Core plus tests without changing the four-stage continuous-cycle identity. | Parameter/state tables should include normalized transform, unit, default, update timing, reset policy, and deterministic seed ownership. | Unit tests, expected transition trace, reset trace, and block-partition equivalence. |
| UND-01 | Undertow lacked exact parent-frequency derivation, delay/interpolation, damping, mix, ratio-change, and pitch tolerance. | B / DSP owner / Core | Implement one original bounded follower with Off and integer divisors 1-16; freeze interpolation, damping, gain, transition policy, and estimator tolerance in tests. | DSP proposals should include equations or pseudocode, coefficient ranges, sample-rate behavior, and objective tolerance. | Exact-zero Off test plus measured active-ratio tuning across representative roots/divisors. |
| WAKE-01 | Wake resonator topology, modes, tuning, Structure map, retriggering, stereo law, and gain compensation were hypotheses rather than executable detail. | B / DSP owner / Core | Choose one original fixed four-voice resonator design and freeze every coefficient/mapping needed for the central experiment. Do not import Rings source. | Minimal experiments should specify the simplest allowed reference algorithm and identify which musical details remain tunable. | Resonator impulse/decay/tuning tests, voice-allocation trace, numeric-safety tests, and render measurements. |
| LEDGER-01 | The central energy/rotor scheduler lacked exact deposit, decay, threshold, transfer, cap, refractory, tie-break, and operation-order equations. | B / DSP owner / Core | Freeze an event-derived, audio-independent scalar ledger; four fixed nodes; deterministic initial rotors; no same-transition recursion; one afterstrike per node; two globally per transition; coupling no greater than 0.72; exact zero afterstrikes at `Ember=0`. | Proposal template should require scheduler pseudocode with initialization, update order, numeric clamps, tie-breaks, capacity, and counter behavior. | Golden ledgers for primary-only, Ember zero, medium/high Ember, Bloom, cap saturation, Reset, and repeated/block-partition runs. |
| LEDGER-02 | “Energy derived from body transient” conflicted with the requirement that clean and corroded audio produce identical ledgers. | B / DSP owner / Core | Ledger deposits derive from accepted stage/control events, never from post-source audio amplitude. Audio excitation may use the body transient independently. | Proposals should identify every control-state versus audio-state dependency and include a causal-isolation test. | Byte-identical clean/corroded ledger with demonstrably different audio measurements. |
| BODY-01 | The body/grain surrogate and corroded condition lacked equations and exact gestures. | H / DSP and fixture owners / host signal | Implement the smallest deterministic stereo context needed to hear masking and corrosion; freeze all values in fixtures. It is not a Tide Pit reimplementation. | Render plans should provide exact parameter/event traces, seed, duration, conditions, comparator, and artifact count. | Stable gesture fixtures, repeatable renders, and objective clean/corroded difference with ledger equality. |
| RESET-01 | Reset, Wake-zero, and Panic did not enumerate all affected audio, control, random, buffer, and pending-event state or exact ramp boundaries. | B / DSP owner / Core state | Freeze separate state tables: Reset restores the musical/ledger reference while preserving declared controls/captured buffer; Wake zero clears pending Wake energy after its ramp; Panic clears active audio/pending state through exactly 10 ms while retaining parameter values. | Proposal template should include a state-by-operation matrix and exact ramp/sample-boundary semantics. | Snapshot assertions, reference ledger after Reset, no hidden Wake after zero, and Panic silence/no-pending-energy tests. |
| MIDI-01 | CC normalization/quantization, press/release values, malformed input, and same-sample ordering were incomplete. | B / mapping owner / control adapter | Freeze absolute 7-bit CC input, one-based channel 16, exact per-control binning, press/release edges, ignore/count policy, and ordering by `(sample timestamp, ingress sequence)` in the prototype fixture. | Controller-map templates should require raw protocol ranges, transforms, thresholds, edge semantics, timing units, defaults, and invalid-input policy. | Fixture validator plus exhaustive CC-range, channel/message rejection, and same-timestamp tests. |
| GEST-01 | Tap/hold actions could double-fire or behave differently at their thresholds. | B / mapping owner / control adapter | A hold fires once at or after 600 ms or 1,200 ms; release after hold does nothing; a shorter release performs Source-cycle or Reset; Bloom arms one token until the next transition or Reset/Panic. | Gesture specifications should use explicit state machines with inclusive thresholds and lost/duplicate-edge behavior. | Boundary-sample, duplicate-edge, missing-release, reset/panic, and block-partition tests. |
| PICKUP-01 | Absolute versus relative encoder behavior, recall feedback, and contextual FX soft pickup remain physically unresolved. | M / controller owner / device | The standalone reflects raw accepted encoder CCs in its sliders without echoing them. Core-owned FX-A/FX-B soft pickup remains authoritative, so the displayed raw value can lead the active value until crossing. Do not claim full state synchronization. | Separate raw-input reflection, accepted application state, physical takeover, and controller feedback; record pickup hysteresis and feedback ownership before promotion. | Physical capture plus a recall/mode-change crossing session, authoritative state readback, OLED/LED feedback, reconnect, and firmware-version evidence. |
| DET-01 | Numeric fixtures, medium/high Ember, Bloom timing, audio comparison norm, pitch/DC/silence tolerances, and golden outputs were absent. | B / test owner / host structural/signal | Freeze one canonical gesture set, all values/timestamps/seeds, comparison metrics, tolerances, ledger representation, filenames, and artifact count before accepting renders. | Proposal template should embed or link a complete machine-readable experiment manifest rather than qualitative gesture adjectives alone. | Fixture freshness test, repeated/fresh-process comparison, golden ledger hashes, and measured render report. |
| COMP-01 | The rotor falsification requires a fixed round-robin comparator, but the five planned conditions omitted it; clean/corroded renders also made the promised count ambiguous. | H / research and fixture owners / host signal/listening | Add an explicit fixed-round-robin comparison or record its deferral; enumerate every retained render rather than promising “five” generically. | Acceptance matrices should cross-check every stop condition against a generated artifact and expected count. | Comparator render/ledger and randomized author comparison, or an explicit unresolved result. |
| SAFE-01 | Output mix, DC blocker, ceiling, denormal handling, non-finite containment, and allocation instrumentation lacked exact definitions. | B / DSP and test owners / Core/host structural | Freeze mix gains, safety equations, numeric clamps, silence/DC windows, and fixed capacities. Core processing performs no allocation, lock, I/O, parse, or logging. | DSP templates should require gain/DC/denormal/non-finite/allocation policies and their exact measurement points. | Hostile-state tests, allocator/lock instrumentation, peak/DC report, long stress, and sanitizer results. |
| JUCE-01 | JUCE sample-rate negotiation, block limits, channel layout, event timing, and lifecycle were unspecified. | B / host owner / JUCE adapter | For v0 accept exactly 48 kHz, zero input, stereo output, and host blocks no larger than 512; reject unsupported configuration before processing. Prepare all Core state off the callback. | Host-adapter templates should state bus layout, prepare/reset/release, unsupported-format policy, timestamp conversion, queue capacity, overflow, and thread ownership. | Exact pinned-JUCE compile, adapter unit/offline parity tests, lifecycle negatives, and callback guard instrumentation. |
| RT-01 | A JUCE build or fast offline render could be misreported as real-time proof. | H / evidence owner / real-time | Record build and offline timing only. No real-time pass until a named device, sample rate, block size, load, callback budget, observation interval, and margin are fixed. | Evidence templates should prevent host-build/host-signal results from auto-promoting to real-time. | Authorized physical callback run with worst/p99 timing, underrun count, allocation/lock guards, and declared margin. |
| DEVICE-01 | No Launch Control Components write, physical MIDI capture, feedback, or reconnect evidence exists. | M / device owner / controller session | The follow-up standalone may enumerate and open one selected MIDI input, prefer the regular Launch Control 3 non-DAW endpoint, and display receive count plus last CC. It sends no MIDI output and writes no controller state. This is source/build evidence until observed with hardware. | Controller tasks should separate endpoint discovery/open, raw activity, protocol/map match, exported configuration bytes, application behavior, feedback, and lifecycle evidence. | Separately authorized Custom Mode export/install, captured channel-16 CC20-35/40-47 trace, gesture timing, state feedback, disconnect/reconnect, and panic-findability session. |
| LISTEN-01 | Objective renders cannot prove recognizable Tide Pit identity or musical quality. | H / user/research owner / listening | Retain renders and objective measurements without an audible pass claim. Run the proposal's author protocol only after artifacts are frozen; test exact Tide Pit lineage later. | Proposal templates should separate regression renders from listening protocol, listener role, randomization, loudness matching, response capture, and pass threshold. | Documented author comparison for H1a; exact-source Tide Pit comparison for H1b; no general-listener claim. |
| LIC-01 | Original prototype licensing and any future distribution terms were not resolved; Mutable and JUCE terms differ. | H / project owner / release | Use original trial code and pinned private-development JUCE only. Copy no Mutable/VCV code and make no distribution claim. | Every prototype should record source provenance, repository license status, dependency licenses, notices, and the release decision gate. | Source/provenance review now; exact combined-work and distribution review before packaging or publication. |
| RECORD-01 | A passing local test could leave the proposal and gap register stale. | H / trial owner / freeze review | After implementation freeze, record exact commands, exit statuses, artifact hashes, deviations, and remaining claims in the trial record; update proposal Section 16 only if separately in the active write scope. | Make result backfill, fingerprint comparison, gap disposition, and complete-diff review mandatory freeze steps. | Freshness checks and evidence-accurate final report with source, host, JUCE build, real-time, device, and listening rows kept independent. |

## Production graph deferral

The production Launch Control 3 route is deliberately deferred:

```text
portable MIDI selectors
  -> performance configuration
  -> reusable performance-control graph
  -> public Cinderwheel instrument facets
  -> instrument-to-DSP mappings
  -> authoritative DSP graph
  -> selected provider/backend/runtime
```

That route requires exact public facets, control-contract semantics, stable
identities, validated records, an execution policy, provider/runtime support,
and evidence that do not exist for Cinderwheel today. Allocating them inside a
musical experiment would confuse design intent with accepted product semantics.

The prototype mapping is therefore the correct first artifact. It is explicit,
portable, deterministic, and testable, but it declares itself non-canonical and
allocates no stable IDs. It can reveal whether CC ranges, detents, tap/hold
gestures, and the Undertow/Wake performance arc work before production graph
decisions become expensive. Its results may inform a later graph task; they do
not become that graph automatically.

## Evidence reporting rule

Always report these claims independently:

1. proposal/design approval;
2. source implementation and provenance;
3. host structural tests;
4. host signal renders and measurements;
5. JUCE/native build;
6. real-time resource behavior;
7. physical controller/device behavior; and
8. listening/audible judgment.

No earlier row implies a later one. A deferred row is expected and must remain
visible rather than being rewritten as passed.
