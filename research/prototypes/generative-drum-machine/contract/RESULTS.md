# Schuss Generative Drum Machine implementation results

> Status: bounded revision 0.6 streaming prototype complete; source, host-structural, host-signal, synthetic callback-kernel, and target-build evidence passed

## Fingerprints

- Proposal SHA-256:
  `e64c62891f34cbe085bace71c4ea4536ec0665340ae566aa24734885da4728f7`
- Implementation contract SHA-256:
  `ee89e2696f14a785283c622a947b5b79984720543e40ca699faa6f12904a239f`
- Source lock SHA-256:
  `b9815983e4fc19e542fbb9fe0da81aecf27b1000c1993c778e8a427a107ecbff`
- Base preset SHA-256:
  `578eb8e134f6c46d9cba945772a474a2189a3683ad3054988a2de3e62d7d1459`
- Retained v1 rhythm extension SHA-256:
  `e063242963481733c62bb9bd926cb6b2a08ac470b73c1d440662c1eb46ae213e`
- Revision 0.6 rhythm extension SHA-256:
  `6b1b1bc4f5b437239f68e614307c0cb07fe17d12fe147f7f907547ec9c502943`
- Generated fifteen-study descriptor SHA-256:
  `081dc0501de6c8b067dca99f8e887d1b476ecb80e6bd713a4d614198189e847c`
- LC3 control map SHA-256:
  `49b01bc54605d89a2a1feaa8b1e9edc071742a9c09c9708e8de3144608c00d0e`
- Generated LC3 descriptor SHA-256:
  `ad8acaec074320826864b9e7b132c71e68ce12aa8f804da98be404a22736a8a5`
- Shared regular Launch Control 3 topology SHA-256:
  `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`
- Frozen/reproduced render manifest SHA-256:
  `c173d54bce78d4d4110a8de7d3adcb891df1fa5ae896ae2dcc5d198730adf5fe`
- Synthetic benchmark artifact SHA-256:
  `3d52db448a63b8a9024e27417d58dc366bde12cae70a5ab58b0c95841d045530`
- Built arm64 standalone executable SHA-256:
  `5078176a25650e545c3e607f777d7e6fc8fb0ac62b25b0411c6cb1c9566790cd`
  (8,266,104 bytes; reproducible-only build artifact)

## Environment

- Apple M1 Pro / arm64, Darwin 24.6.0
- Apple Clang 16.0.0 (`clang-1600.0.26.6`)
- CMake 4.4.2
- Python 3.10.4
- Host audio: 48 kHz signed Q27; four Braids cores each render two 96 kHz
  samples per host frame before a fixed five-tap integer decimator

## Implemented behavior

The prior immutable phrase-preview worker and three-slot exchange were removed.
The optional app now uses `StreamingEngine`, which owns persistent musical
phase, event-crossing state, fill state, four Braids voices, envelopes,
decimator histories, and mixer state. One coherent bounded control snapshot is
read at block start. The snapshot uses a three-slot
single-writer/single-reader exchange whose contention test rejects torn reads.
The callback performs no locking, heap
allocation, file I/O, JSON, UI work, or worker wait.

Continuous semantics are frozen as follows:

- complexity and enthusiasm apply to future un-crossed events on the next block;
- all six voice-shape controls affect sounding matching-lane voices and future
  hits through an exact 128-sample slew;
- tempo preserves Q32 musical phase and carried remainder;
- swing affects future eligible off-eighth events;
- rhythm selection restarts the selected study at downbeat on the next block
  while existing synthesis tails continue; and
- Fill starts one normalized one-bar overlay on the next block.

The fifteen-entry bank spans 2/4, 3/4, 4/4, 5/4, 5/8, 6/8, 7/8, 9/8, and
10/8. The new entries are Samba Enredo, Partido Alto, Samba de Roda,
Samba-Reggae, Maracatu Pulse, Candombe Conversation, Chacarera Cross-Meter,
Aksak Five/Seven/Nine, and Jhaptal Cycle studies. Every cultural entry stores a
public-source relationship and `authenticity_claim: false`; no source notation,
audio, proprietary pattern, or ceremonial toque was copied.

## Launch Control 3 and UI

The exact regular Tide Pit topology remains Custom Mode slot 1, channel 16,
encoders CC20-35, and momentary buttons CC40-47.

- CC20-25: six lane complexities
- CC26: Enthusiasm
- CC27: Tempo
- CC28-33: selected lane Tune, Timbre, Color, Decay, Punch, Level
- CC34: Swing
- CC35: direct fifteen-way rhythm selection
- CC40-45 / buttons 1-6: corresponding voice select/toggle
- CC46 / button 7: Fill
- CC47 / button 8: Next Rhythm

All 7-bit values, invalid values 128-255, wrong channels, unknown selectors,
button press/release transitions, rhythm wrapping/direct selection,
inactive-shaper behavior, and lane isolation pass focused tests. The app UI now
lists all fifteen rhythms, exposes study family/grouping, numbers the six voice
buttons, presents the six selected-voice controls, and reports accepted state,
cycle progress, lane activity, MIDI receipt, callback block size, and observed
callback peak. It was compiled and linked against authenticated JUCE 8.0.15
with fetching disabled and was not launched during this evidence run.

## Validation

The following completed with exit status 0:

```sh
python3 tools/instrument_lab/validate_task038_reuse.py
python3 research/prototypes/generative-drum-machine/tests/run_structural.py --check
python3 research/prototypes/generative-drum-machine/tests/render_evidence.py --reproduce --output build/generative-drum-machine-evidence
python3 research/prototypes/generative-drum-machine/tests/benchmark_realtime.py --reproduce --output build/generative-drum-machine-realtime-benchmark.json
cmake --build build/generative-drum-machine-juce --parallel
ctest --test-dir build/generative-drum-machine-juce --output-on-failure
```

The source-release-bound shared packages authenticated 17 exact physical source
files. Eight focused CTests cover
all fifteen descriptors and metadata, nine meter identities, rational bounds,
monotone complexity, coherent seeded variation, allocator order, active/future
voice shaping, streaming block partition equality, next-block rhythm restart,
fill execution, generated LC3 mapping, concurrent atomic snapshot coherence,
accepted-state UI projection, and source freshness.

The objective matrix reproduced event, allocator, metrics, manifest, and stereo
WAV artifacts byte-for-byte for eight conditions across outer block sizes 1,
16, 64, 128, 511, and 512.

| Condition | Frames | Events | Peak Q27 | Absolute DC Q27 | Chokes | Steals | Drops | Clips/overflows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Authored static | 1,200,000 | 162 | 90,045,497 | 33,375 | 0 | 0 | 0 | 0 / 0 |
| Authored variation + fill | 1,200,000 | 313 | 90,164,095 | 41,975 | 196 | 0 | 0 | 0 / 0 |
| Independent probability comparator | 1,200,000 | 150 | 86,367,503 | 19,585 | 51 | 0 | 0 | 0 / 0 |
| Allocator stress | 48,000 | 8 | 96,054,938 | 24,744 | 2 | 0 | 2 | 0 / 0 |
| Three Turn static | 912,000 | 126 | 87,727,234 | 35,924 | 0 | 0 | 0 | 0 / 0 |
| Rolling Six static | 912,000 | 120 | 90,523,879 | 35,824 | 0 | 0 | 0 | 0 / 0 |
| Five Across shaped + fill | 768,000 | 92 | 94,306,620 | 32,094 | 1 | 0 | 0 | 0 / 0 |
| Samba Enredo Study | 712,615 | 126 | 98,187,782 | 56,151 | 0 | 0 | 0 | 0 / 0 |

## Synthetic callback-kernel measurement

The fixed-capacity Core was stressed for 2,000 measured calls at each block size
with maximum complexity/enthusiasm, 240 BPM, periodic fills, and a changing
lane-shape target every block.

| Frames | Median | p99 | Maximum | Deadline | Maximum/deadline | Allocations | Failures |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | 0.017 ms | 0.021 ms | 0.064 ms | 1.333 ms | 4.80% | 0 | 0 |
| 128 | 0.032 ms | 0.041 ms | 0.130 ms | 2.667 ms | 4.87% | 0 | 0 |
| 512 | 0.121 ms | 0.162 ms | 0.209 ms | 10.667 ms | 1.96% | 0 | 0 |

These measurements demonstrate bounded native-host feasibility and zero
observed heap allocation in the measured `process()` calls. They do not prove
live audio-device scheduling, xruns, endpoint lifecycle, another machine,
Ksoloti, or production headroom.

## Evidence ladder

| Level | Result | Remaining limitation |
|---|---|---|
| Research | passed | Public/source research and cultural context do not prove musical authenticity or preference |
| Proposal | passed | Approval is limited to this prototype revision |
| Source | passed | Exact MIT dependency closure; no production distribution review |
| Host structural | passed | Noncanonical Instrument Lab implementation |
| Host signal | passed | Objective offline renders are not listening evidence |
| Synthetic callback kernel | passed | Not a live audio-device deadline/xrun test |
| Target build | passed | Built only; no launch, visual QA, signing, packaging, or endpoint proof |
| Live real-time | deferred | Requires authorized live run |
| Connected device | deferred | Revised LC3 map has not been physically exercised in this evidence run |
| Listening | partial/informal | User liked the preceding build; revision 0.6 awaits audition |
| Production integration | deferred | No accepted schema, record, provider, factory, task, package, or release |

## Task 038 reuse migration

Task 038 moved the exact 12-file Braids and 5-file stmlib closures into shared
physical packages, introduced the narrow `SchussMutableBraidsV1::Core`
non-provider adapter, and removed the instrument-local source shelf only after
all focused tests and the frozen six-block-size render matrix passed unchanged.
Source releases 000008 and 000009 remain authoritative for upstream identity,
revision, hashes, provenance, and licensing. The accepted JUCE source release
000007 now also authenticates the complete 4,425-file extracted tree before
CMake accepts a local JUCE source directory.
