# Pamplist 0.2

Pamplist is a noncanonical Instrument Lab prototype: eight deterministic
clock/modulation lanes focus on one complete 24-engine macro voice. Main is the
left output and auxiliary is the right output. It is an independently designed
instrument informed by observable clock-modulator behavior; it is not a
Pamela's firmware, panel, menu, or algorithm emulation.

The portable Core owns exact rational phase carry, fixed 16-step Euclidean
masks, addressed probability and repeat windows, eight unipolar shapes, a
signed 8-by-8 voice matrix, coherent accepted snapshots, and a persistent
16-frame source quantum. The macro voice is compiled read-only from the exact
configured `patcher` source only after commit, subtree, cleanliness, and file
hash authentication.

## Controls

Regular Launch Control 3 Custom Mode 1, MIDI channel 16:

- CC20-27: selected lane routes to Trigger, Pitch, Model, Harmonics, Timbre,
  Morph, Decay, and Level.
- CC28-35: selected lane Rate, Phase, Shape, Hits, Rotation, Probability,
  Repeat, and Amplitude.
- CC40-47: select lane 1-8 on the rising edge.

The standalone distinguishes GUI injection from physical receipt. Audio and
MIDI remain off until the user explicitly starts audio, refreshes the MIDI
list, and selects an endpoint.

## Build and validate

```sh
python3 research/prototypes/pamplist/tests/verify_source_authority.py
python3 research/prototypes/pamplist/tests/run_focused.py
python3 research/prototypes/pamplist/tests/render_evidence.py --check
python3 research/prototypes/pamplist/tests/build_juce.py --check
```

Fresh target construction needs an operator-supplied authenticated JUCE 8.0.15
tree:

```sh
python3 research/prototypes/pamplist/tests/build_juce.py \
  --reproduce --juce-source /path/to/authenticated/juce-8.0.15
```

No network fetch or fallback source is enabled. These commands do not launch
the app. The current retained evidence proves source identity, host structure,
objective host signal, and target build only—not real-time deadline, endpoint,
physical device, listening, embedded, distribution, or production behavior.
