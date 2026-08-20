# Instrument Lab v1 differential audit

> Status: frozen before shared C++ implementation.
> Classification vocabulary: `extract`, `parameterized-adapter`,
> `instrument-owned`, or `defer`.

## Gate and activation baseline

Task 037 was explicitly activated only after the Task 036 completion handoff
validated against its live package and Tide Pit references. The activation
state was:

- Task 037 proposal SHA-256:
  `52344203b3520001f4266c25f226f7181f1a74ef89024e47e109e6a2a5bd50db`;
- Task 037 contract SHA-256:
  `39b4d73bf053bc7104e6605569c72ed61cb32b5d793f75b32e78589fda08f093`;
- Task 036 handoff SHA-256:
  `a083214f7f2d08bb0dd7278bcaa10cb3eec6a7c4e0ad646a1710b0b6d59beb8b`;
- local `main`, fetched `origin/main`, and their merge base:
  `2b0180a47f7ac03011f56e9683c77060c8080f09`, with divergence `0/0`;
- Cinderwheel complete-tree path-and-byte manifest SHA-256:
  `86822abd2c7cea8b1b7a9c497c5fc737a99cf8f5daa31298e4a3eb15eba15c76`;
- post-Task-036 Tide Pit complete-tree path-and-byte manifest SHA-256:
  `5ee602583116adce423f2ac7ca96c1daa2a280bec9f80c9caf544e76a86524c9`;
- Cinderwheel authority proposal SHA-256:
  `cd0c09e0df22f382d74bb380fa9ab91549faf1894199f5d02e4ac5e3795a1549`;
- Tide Pit authority proposal SHA-256:
  `3c2157eaa26ceed61afe87b256a395dccc5fbbd0dab889189926ffb72b5c2157`;
- regular Launch Control 3 topology SHA-256:
  `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`;
  and
- Cinderwheel reuse-audit manifest SHA-256:
  `19425167e2c27a37508a7acf594ed2263f36b06ea0051d177c6b9cf21c2320a9`.

The Tide Pit implementation bundle passed Sonic Research Lab readiness with
the authenticated Gills source root. Cinderwheel predates that bundle format;
its approved proposal, README contract, result/gap records, controller fixture,
and reuse manifest form the repository-native legacy approval bundle. Task 037
will index those exact authorities without rewriting its musical contract.

## Pre-extraction comparator

Before this document and before shared C++ edits, the live baselines passed:

| Consumer | Structural/source | Sanitizer | Authenticated JUCE/render |
|---|---|---|---|
| Cinderwheel | Core and mapping 2/2 | not part of its accepted pre-Task-037 contract | 4/4, including adapter parity and 64/128/512/repeat render matrix |
| Tide Pit | source/Core/control/golden/UI 6/6 | fail-fast ASan/UBSan 6/6 | 8/8, including adapter parity and 16/64/128/512 render matrix |

The JUCE source used by both was the locally authenticated 8.0.15 tree whose
archive SHA-256 is
`04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70`.
No app, audio device, MIDI device, controller configuration, or hardware was
opened.

## Corresponding source fingerprints

| Responsibility | Cinderwheel path / SHA-256 | Tide Pit path / SHA-256 |
|---|---|---|
| CMake/JUCE/CTest | `research/prototypes/cinderwheel/CMakeLists.txt` / `d349220c04bf0a6cd9349b7e004ed3e673d67b1fa8c16971c57967a8df786ea9` | `research/prototypes/tide-pit-gills/CMakeLists.txt` / `b122b0ec44f82783371fae8e5f261e7303eb4afc210769027dcc9083f7998942` |
| Core contract | `include/cinderwheel/core.hpp` / `af8a59cda4ab7baff9711b828222d7e0420b2e5747838e49915e2914b41745e6` | `include/tidepit/core.hpp` / `897100d45e4019d6b1f3dabc6f93a3798a85f73b659c26c9ec3fe85a1d4221b5` |
| Control contract | `include/cinderwheel/control_map.hpp` / `6ae5147081123b1fc53146738e85c298b41864c69ed0beff6af156a726703d70` | `include/tidepit/control_map.hpp` / `066a482d85f147e90c7e5e11e7f6fa795fe87c2177d6f61c95ceee3bbcdb7c1d` |
| MIDI adapter API | `include/cinderwheel/juce_midi_adapter.hpp` / `5b107623b154402c3b4fb6e0af943f1c9ff15f920ff5c278c4c21082f4ed7d75` | `include/tidepit/juce_midi_adapter.hpp` / `66048ebd86744b8e897ab8411b29fedac49da64ccb7d59967d6abdf275cfb905` |
| MIDI/host bridge | `src/juce_midi_adapter.cpp` / `5d3212fec8ea60f2c5268e71f6dcf0ccd33030a6de67ea4c5025a232fd7b4e61` | `src/juce_midi_adapter.cpp` / `fa7080776c2a21fd88986277d0c62808ab8cabecc7a8a9868f4eb4ff5c708e64` |
| Standalone shell/UI | `src/juce_main.cpp` / `2d9001f5db02c6c4e1cd356e4d1ebeda787a6ed4df898f4dd5bc66c10fe8e734` | `src/juce_main.cpp` / `931caabbc953f37cd98f3d1c8674a911aa7509be6aeeeeefe1f57d1acf77e0cf` |
| Renderer | `src/render.cpp` / `0a889f6339bc7d3be2c8a07eda442d11b0ca70b4fc42c9de2d4e35b8fa5c6c84` | `src/render.cpp` / `8b60ef7ab2e5f98d661a668c12f99009a2b55359e72430185233f58d1f3f5e67` |
| Adapter tests | `tests/juce_midi_adapter_tests.cpp` / `292e91fe69b81997a05ff6a432fdb04ce3330252c275937725a98f3f30375727` | `tests/juce_midi_adapter_tests.cpp` / `bf62db512d2e2838705b81014abb07ab7d761734fc6ed88994a6b05b9e68efaa` |
| Render matrix | `tests/validate_render_matrix.py` / `4569226c08c8f485fb31f1caf5b65a2950bad4c0759c508b08f4be47bede1021` | `tests/validate_render_matrix.py` / `2ca9a4bf934ca640d120c3767f34e7c132e5043cd4e47515b1f596dee4a1658b` |

Paths in the two columns are relative to their prototype roots when shortened.

## Seam-by-seam classification

| Candidate seam | Cinderwheel evidence | Tide Pit evidence | Classification | Frozen v1 boundary and reason |
|---|---|---|---|---|
| JUCE authentication | exact commit/archive constants; local tree checks version 8.0.15 | same commit/archive and version check | `extract` | One helper validates caller-supplied source or explicitly enabled exact fetch. It owns no distribution claim and never fetches by default. |
| JUCE module selection | adapter uses `audio_basics`; renderer uses `audio_formats`, `core`; app uses audio/device/event/gui modules | adapter same; renderer additionally needs `cryptography`; app adds instrument UI model | `parameterized-adapter` | Helper registers only caller-declared modules. `juce_dsp` is forbidden. |
| CMake warnings and sanitizers | C++17 and warnings; no accepted sanitizer profile | C++17, warnings, consumer-owned ASan/UBSan and Apple Release `-O2` for source-exact targets | `parameterized-adapter` | Lab provides target-scoped helper functions. Consumers retain flags and numeric policy. No global options. |
| Target/CTest registration | Core, mapping, optional adapter/renderer/app, render test | source, Core, control, golden, UI, optional adapter/renderer/app, render test | `extract` | Narrow helper registers exact caller targets/tests without choosing musical sources. |
| Raw MIDI bytes | all messages enter a 128-event raw `MidiEvent` buffer so Core can diagnose malformed/wrong-channel data | adapter validates 3-byte CC and maps accepted input into at most 128 semantic events | `parameterized-adapter` | Share fixed-capacity storage, timestamp clamping, ingress sequencing, and byte-envelope helpers. Validation/mapping/drop accounting remain supplied policy so malformed-message behavior cannot drift. |
| Ordering | JUCE timestamp order plus monotonic ingress sequence | same; Q27 bridge later carries absolute sample/sequence across callbacks | `extract` | Common helpers preserve `(sample_offset, ingress_sequence)` and never sort or allocate in the proven span. |
| Semantic mapping | raw bytes remain normative input to Cinderwheel Core; button timing and Reset/Panic live there | mapping rejects/diagnoses raw input and emits exact `SemanticAction` values; source gestures remain in Core | `instrument-owned` | No common semantic action, unit conversion, gesture, or reset model. |
| Core numeric/sample profile | float, 48 kHz, maximum 512 frames, direct host-sized processing | Q27, 48 kHz, exact 16-frame internal quantum, host callback may be irregular | `parameterized-adapter` | Composition traits declare representation, conversion owner, maximum host block, internal quantum, process contract, and output-clearing policy. No implicit float/Q27 conversion. |
| Cinderwheel host processing | direct float Core process, fixed 512-frame scratch, Wake event sink | not applicable | `parameterized-adapter` | Float adapter owns Wake sink and direct call. The lab owns only bounded host partition/call sequencing. |
| Tide Pit host processing | not applicable | 512 pending events; absolute carry; Q27 planar quantum buffers; explicit Q27-to-float conversion | `parameterized-adapter` | Tide adapter retains conversion constant, quantum event translation, and overflow semantics while consuming shared bounded bridge primitives. |
| Prepare/reset/unsupported call | exact Core-specific rules and diagnostics | exact source configuration, arena, queue, and no public reset operation | `instrument-owned` | Traits expose capabilities; lab never invents Reset or accepted formats. |
| Snapshot and diagnostics | `StateSnapshot` plus Core diagnostics; current UI has raw accepted-encoder reflection | `Snapshot`, Core/MIDI/bridge diagnostics, and Core-state UI model | `parameterized-adapter` | Each instrument supplies a projection. Shared descriptor/UI mechanics accept immutable projected values only. |
| Control descriptors | compile-time C++ descriptor table plus exhaustively checked JSON fixture | generated C++ descriptor table from authoritative JSON and exhaustive generator check | `extract` | One deterministic generator validates controller topology and emits descriptor structure; the map remains instrument-owned. Cinderwheel's legacy fixture is adapted without changing defaults or semantics. |
| Physical topology | exact regular Launch Control 3 CC/channel layout copied into a Cinderwheel test fixture | control map references the same topology fingerprint | `extract` | Reuse the single existing topology by path/hash. No new controller model or device claim. |
| UI layout | descriptor-driven sliders and buttons; visual identity and raw MIDI diagnostics are local | descriptor-driven layout, snapshot-reflected controls, buttons, displays, scope, and diagnostics are local | `parameterized-adapter` | Shared layout descriptors and snapshot-value plumbing only. Visuals, labels, status text, button state, display lines, and scope remain local. |
| Soft pickup and contextual values | none | accepted value can differ from raw input across mode recall and pickup | `instrument-owned` | UI always consumes projected Core state; the lab never treats raw input as accepted state. |
| UI/scope mailbox | Cinderwheel uses atomics only for diagnostics/raw encoder observations | two local SPSC mailboxes are reset while consumer access can still be live; gap is recorded | `defer` | No shared mailbox in v1. Existing Tide implementation remains local; restart-safe lifecycle is not promoted. |
| Experiment authority | gesture schedule is compiled into renderer; conditions and tolerances are retained in proposal/results | exact `experiment.json` owns conditions, seed, events, comparator, and tolerances | `instrument-owned` | Cinderwheel receives a non-rebaselining index to its legacy authority. Task 037 does not invent a new musical experiment. |
| JSON escaping/finite number formatting | local deterministic implementation | materially identical local implementation | `extract` | Move exact byte-compatible helpers to one library and compare all manifests. |
| Artifact path/overwrite policy | refuses each known artifact target; writes six WAVs, six ledgers, one manifest | refuses a non-empty output directory; writes condition-specific Q27/WAV and one manifest | `parameterized-adapter` | Shared filesystem checks and hashing are policy-parameterized. Artifact names/counts remain instrument-owned. |
| WAV/Q27 encoding | JUCE 24-bit stereo WAV; float metrics/fingerprint | JUCE 24-bit stereo WAV plus canonical planar little-endian Q27 | `parameterized-adapter` | Common mechanics cannot choose encoding. Tide's Q27 writer and comparator stay local. |
| Hashes/measurements | ledger/file sizes, finite/peak/RMS/DC, FNV-style audio fingerprint | SHA-256, Q27 peak/RMS, normalized peak/DC, snapshots | `parameterized-adapter` | Share deterministic SHA-256/file metadata and finite formatting only; measurement definitions stay explicit per experiment. |
| Render partitions/repeat | 64/128/512 and repeated 128; byte/ledger/state comparisons and overwrite negative | 16/64/128/512, repeated render, snapshot, experiment-tamper, overwrite negatives | `extract` | Reproduction driver invokes each instrument's own matrix and compares declared outputs; it does not replace either comparator. |
| Source/dependency fidelity | no copied source dependency; proposal/README/fixture/reuse manifest are authority | Task 036 physical package plus source-equivalence, source lock, overlay generator, exact golden | `instrument-owned` | Prototype index binds authorities; lab never imports or reinterprets source. |
| Golden and sanitizer evidence | Core/render matrix; no accepted sanitizer claim | exact `39d8...ad2b` Q27 golden and fail-fast sanitizer matrix | `instrument-owned` | Lab registers commands and freshness only. It never changes a comparator or promotes missing evidence. |
| Fresh-root evidence | existing prototype builds, but no reusable generator | Task 036 relocated source-package reproduction only | `extract` | Deterministic generator plus two fresh outputs and one relocated-root runner are new Task 037 evidence. |
| Prototype topology | no retained noncanonical graph artifact | no retained noncanonical graph artifact | `extract` | Add lab-local, non-executable topology artifacts and deterministic promotion-needs reports. No stable IDs or canonical records. |
| Compact context handoff | no compact generated handoff | Task 036 predecessor handoff exists, but no per-prototype lab handoff | `extract` | Generate path/hash indexes and concise Markdown handoffs from live authorities. |
| Callback deadline, collector/device restart, physical control, listening, distribution | unproved or separately user-observed only | unproved; unsafe mailbox reset noted | `defer` | Task 037 makes no real-time, lifecycle, device, listening, or release promotion. |

## Frozen shared API direction

The smallest common v1 layer is therefore:

1. JUCE source authentication and target-scoped CMake helpers;
2. fixed-capacity storage, raw three-byte envelopes, timestamp clamping, and
   ingress sequencing with instrument-supplied acceptance policy;
3. a traits/composition host bridge whose adapter explicitly owns float/Q27
   conversion, quantum, event, reset, snapshot, and diagnostic behavior;
4. deterministic JSON/string, SHA-256/file, overwrite, and reproduction
   mechanics driven by instrument-owned experiments;
5. control descriptor generation/validation from instrument maps plus the
   single existing controller topology reference; and
6. lab-local prototype indexes, noncanonical topologies, promotion-needs
   reports, and compact handoffs.

The lab will not extract any DSP Core, source overlay, musical control map,
gesture, reset/state semantics, snapshot schema, UI identity, experiment
timeline, comparator, or mailbox lifecycle. A failure to preserve either
pre-extraction comparator causes that seam to remain local rather than forcing
the abstraction.
