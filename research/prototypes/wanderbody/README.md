# Wanderbody 0.1

Wanderbody is a noncanonical standalone Instrument Lab prototype that keeps an
eight-second recent-memory field, moves fragment decisions through that field,
remembers eight complete decisions, and feeds the fragments into an optional
six-mode physical body. It can listen to stereo input or use its small internal
exciter.

The two motion policies are deliberately distinct:

- **Hover** traverses a pendular path around `Anchor`, bounded by `Field` and
  scaled by `Wander`.
- **Drunk** uses a correlated velocity with reflected field boundaries. At zero
  `Wander` it is exactly still.

`Fresh` continually learns decisions. `Locked` repeats the oldest-to-newest
eight-tuple cycle, `Shuffled` repeats one exact permutation, and `Mutated`
cycles the same identities with bounded position, rate, duration, and pan
changes. Each fragment freezes its source time, duration, direction, gain, pan,
and body pitch at birth.

The portable C++17 Core owns capture, motion, recurrence, voices, body, state,
and diagnostics. The JUCE layer owns only the optional standalone window and
audio/device lifecycle. Its controls are refreshed from accepted Core
snapshots, while the memory display receives only a fixed 256-point decimated
observation. The app does not expose the live capture store to the UI.

## Build and validation

Run the portable checks from the repository root:

```sh
python3 research/prototypes/wanderbody/tests/run_structural.py --check
python3 research/prototypes/wanderbody/tests/render_evidence.py \
  --reproduce --output build/wanderbody-evidence
```

Build the standalone against an authenticated JUCE 8.0.15 tree:

```sh
python3 research/prototypes/wanderbody/tests/build_juce.py \
  --build-dir build/wanderbody-juce-release \
  --juce-source-dir /absolute/path/to/authenticated/JUCE-8.0.15
```

The resulting private development bundle is
`build/wanderbody-juce-release/wanderbody-instrument_artefacts/Release/Wanderbody 0.1.app`.
Building does not launch, install, sign, or distribute it.

## Evidence boundary

The retained matrix covers ten 48 kHz conditions and block partitions 1, 17,
64, 127, 256, 511, and 1024. It establishes structural and offline host-signal
behavior only. It does not establish callback deadlines, endpoint behavior,
physical control, listening quality, distribution readiness, or canonical
Schuss instrument/provider identity. The exact contract and deferred evidence
are in `contract-r01/`.
