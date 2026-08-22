# Schuss Generative Drum Machine prototype

This directory is a noncanonical Instrument Lab implementation of the approved
[research proposal](../../proposals/schuss-generative-drum-machine.md). Revision
0.6 is a portable C++17 streaming drum machine: fifteen selectable,
independently authored rhythm studies and six logical drum lanes drive four
pooled Braids-derived physical voices through semantic `DrumHit` events.

The instrument does not carry its own Mutable source shelf. It consumes the
repository's exact `mutable-eurorack-braids-v1` and `mutable-stmlib-v1`
physical closures through `SchussMutableBraidsV1::Core`. Source identity,
revision, provenance, and licensing remain owned by source releases 000008 and
000009; the adapter has no catalog, graph, provider, or runtime identity.

The ready bundle in `contract/` is the prototype's implementation boundary.
Nothing here allocates an accepted Schuss schema, object, provider, factory,
record set, or numbered task.

## Realtime interaction

The standalone app no longer pre-renders whole phrases. Its callback owns a
persistent fixed-capacity musical scheduler, four synthesis voices, envelope
state, and mixer state. It reads one coherent integer-only public-control
snapshot at block start and performs no locks, allocation, file I/O, JSON, or UI
work.

- Complexity and Enthusiasm affect future un-crossed events at the next block.
- Tune, Timbre, Color, Decay, Punch, and Level affect sounding voices of the
  selected logical lane plus future hits, with a fixed 128-sample slew.
- Tempo changes preserve musical phase.
- Swing retimes future eligible off-eighth events.
- A rhythm change restarts the new study at its downbeat on the next block while
  existing synthesis tails continue.
- Fill starts one normalized one-bar overlay on the next block.

At the largest supported 512-frame block, the declared control observation
bound is 10.667 ms at 48 kHz. This is a software contract; only a later
authorized live-device run can establish xruns and endpoint behavior.

## Rhythm bank

The bank uses rational quarter-note positions rather than a sixteen-step grid.

| # | Study | Meter/grouping |
|---:|---|---|
| 1 | First Light | 4/4 |
| 2 | Three Turn | 3/4 |
| 3 | Rolling Six | 6/8 |
| 4 | Five Across | 5/4 |
| 5 | Samba Enredo Study | 2/4 |
| 6 | Partido Alto Study | 2/4, syncopated 3-3-2 relationship |
| 7 | Samba de Roda Study | 2/4, alternating call-response bars |
| 8 | Samba-Reggae Study | 4/4, layered two-beat cells |
| 9 | Maracatu Pulse Study | 4/4 |
| 10 | Candombe Conversation | 4/4 |
| 11 | Chacarera Cross-Meter | 6/8 surface against 3/4 accents |
| 12 | Aksak Five Study | 5/8 = 2+3 |
| 13 | Aksak Seven Study | 7/8 = 2+2+3 |
| 14 | Aksak Nine Study | 9/8 = 2+2+2+3 |
| 15 | Jhaptal Cycle Study | 10/8 adaptation = 2+3+2+3 |

Culturally named entries are independently authored structural studies with
public research relationships embedded in the fixture. They copy no source
notation, audio, proprietary pattern, or ceremonial toque and make no
authenticity claim.

## Regular Launch Control 3 map

Use the same physical Custom Mode topology as Tide Pit: slot 1, MIDI channel 16,
encoders CC20-35, and momentary buttons CC40-47.

| Selector | Drum-machine control |
|---|---|
| Top encoders CC20-25 | Kick, snare, hat, percussion 1-3 complexity |
| Top encoder CC26 | Enthusiasm |
| Top encoder CC27 | Tempo, 30-240 BPM |
| Bottom encoders CC28-33 | Selected voice: Tune, Timbre, Color, Decay, Punch, Level |
| Bottom encoder CC34 | Swing |
| Bottom encoder CC35 | Direct selection across all fifteen rhythm studies |
| Buttons CC40-45 (1-6) | Select/toggle kick, snare, hat, percussion 1, 2, or 3 |
| Button CC46 (7) | Immediate one-bar Fill |
| Button CC47 (8) | Next Rhythm |

The six bottom shaping encoders are semantic no-ops until one of buttons 1-6 is
active. GUI and controller gestures terminate at the same accepted public
control reducer; raw MIDI is not the musical authority.

## Build and checks

From the repository root:

```sh
python3 research/prototypes/generative-drum-machine/tests/run_structural.py --check
python3 tools/instrument_lab/generate_task038_source_dependencies.py --check
python3 research/prototypes/generative-drum-machine/tests/render_evidence.py \
  --reproduce --output build/generative-drum-machine-evidence
python3 research/prototypes/generative-drum-machine/tests/benchmark_realtime.py \
  --reproduce --output build/generative-drum-machine-realtime-benchmark.json
```

To build the optional authenticated JUCE 8.0.15 app without network fetching:

```sh
cmake -S research/prototypes/generative-drum-machine \
  -B build/generative-drum-machine-juce \
  -DCMAKE_BUILD_TYPE=Release \
  -DGDM_ENABLE_JUCE=ON \
  -DGDM_JUCE_SOURCE_DIR=/absolute/path/to/the-exact-authenticated-JUCE-tree
cmake --build build/generative-drum-machine-juce --parallel
```

The bundle is produced at:

```text
build/generative-drum-machine-juce/
  schuss-generative-drums_artefacts/Release/
  Schuss Generative Drums.app
```

Building does not launch the app, open a MIDI endpoint, or prove a physical
controller, listening, Ksoloti, distribution, or production claim.
