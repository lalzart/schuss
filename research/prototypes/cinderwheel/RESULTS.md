# Cinderwheel trial results

Freeze date: 2026-08-20

This record reports the isolated prototype only. It is bound to proposal
revision 0.2, Git blob
`c075035b9c844eedd29f7f172e557cc985ad6d48`, and original proposal SHA-256
`d9b3a50cde3c25a4db6324bd8d20f1a65eaefcbd1ac8e9e7a42adc80713b5e84`.
The proposal was approved for this bounded trial by the user's 2026-08-20
request. No Schuss identity, production graph, provider, target, or device
claim is created.

## Built result

The source-to-host slice is working under this deliberately narrow definition:

- a JUCE-independent C++17 Core accepts the prototype MIDI/control contract and
  renders stereo audio at exactly 48 kHz with blocks no larger than 512 frames;
- a fixed-capacity JUCE MIDI adapter converts host events and was compared
  bit-for-bit with the direct Core path;
- a deterministic renderer writes six 40-second, 24-bit stereo WAV files, six
  event ledgers, and one observation manifest; and
- the pinned JUCE build creates
  `build/cinderwheel-juce-trial/cinderwheel-instrument_artefacts/Release/Cinderwheel.app`.

The app bundle was built but not launched. No audio or MIDI device was opened.

## Commands and results

JUCE-free source and mapping closure:

```sh
cmake -S research/prototypes/cinderwheel -B build/cinderwheel-core-trial \
  -DCMAKE_BUILD_TYPE=Release \
  -DCINDERWHEEL_ENABLE_JUCE=OFF
cmake --build build/cinderwheel-core-trial --parallel
ctest --test-dir build/cinderwheel-core-trial --output-on-failure
```

Result: configure/build passed and CTest passed `2/2`:
`cinderwheel_core_tests` and `cinderwheel_mapping_fixture`.

Authenticated JUCE 8.0.15 closure:

```sh
cmake -S research/prototypes/cinderwheel -B build/cinderwheel-juce-trial \
  -DCMAKE_BUILD_TYPE=Release \
  -DCINDERWHEEL_ENABLE_JUCE=ON \
  -DCINDERWHEEL_ALLOW_JUCE_FETCH=ON
cmake --build build/cinderwheel-juce-trial --parallel
ctest --test-dir build/cinderwheel-juce-trial --output-on-failure
```

The fetch route authenticated JUCE commit
`91ad83ae34a81e0833b1a2b0866f54846370ae53` with archive SHA-256
`04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70`.
Configure/build passed, including the renderer and standalone app. CTest passed
`4/4`: Core, mapping, JUCE adapter, and render matrix.

The adapter test exercised exact raw three-byte preservation, malformed input,
timestamp clamping and deterministic ingress order, a 128-event cap with drop
accounting, lifecycle reset, allocation-free adaptation in the tested path, and
bit-exact audio/Wake-event parity against direct Core processing.

Focused sanitizer closure compiled the Core and tests with AppleClang 16,
`-fsanitize=address,undefined`, and `-fno-omit-frame-pointer`. It passed with
`ASAN_OPTIONS=detect_leaks=0`; leak detection is disabled because the macOS leak
sanitizer path is unsupported in this environment.

Workspace closure:

```sh
python3 tools/validation/run.py --profile current
```

Result: `4/4` checks passed (`inventory.discovery`, `catalog.discovery`,
`contracts.current-closure`, and `contracts.current-tests`). The current
contract suite reported its normal configured-source/native prerequisites as
out of scope; the profile itself had zero failed or incomplete checks.

## Render matrix

The registered matrix invoked the renderer in four fresh processes: block sizes
64, 128, and 512 plus a repeated block-128 run. Each run processed 1,920,000
frames, or 32 cycles / 40 seconds, per condition. It established:

- all 12 WAV/ledger artifacts are byte-identical across 64, 128, and 512;
- all 13 outputs, including the manifest, are byte-identical on the fresh
  block-128 repeat;
- clean and corroded rotor ledgers are byte-identical while their audio differs;
- all outputs are finite, below the -1 dBFS ceiling, and below the absolute
  `1e-4` DC-mean limit;
- `Ember=0` produces zero afterstrikes; and
- the high-Ember Bloom condition reaches the bounded event cap once.

The block-128 outputs are retained locally under
`build/cinderwheel-final-v0-128/`. The three retained render directories are
ignored build evidence, not repository artifacts or a release package.

| Condition | Peak | RMS | DC mean L | DC mean R | Primary | Afterstrikes | Cap hits |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.2642559707 | 0.1163331656 | 3.9604e-7 | 2.5848e-8 | 0 | 0 | 0 |
| Undertow f/3 | 0.2725040913 | 0.1165729686 | -1.2813e-6 | -1.2860e-6 | 0 | 0 | 0 |
| Primary Wake, Ember zero | 0.2648517787 | 0.1062793775 | 3.6411e-7 | 2.0912e-8 | 127 | 0 | 0 |
| Rotor medium, clean | 0.2810001671 | 0.1069240556 | 3.2476e-7 | 8.5630e-8 | 42 | 7 | 0 |
| Rotor high plus Bloom | 0.2997882664 | 0.1099877615 | 4.4918e-7 | 5.5876e-7 | 42 | 74 | 1 |
| Rotor medium, corroded | 0.8778860569 | 0.2954826522 | 7.6119e-7 | -2.1402e-6 | 42 | 7 | 0 |

Manifest SHA-256:
`5141fe881bb3012fb654d9c52b62d59fcacbbbdad45141596452d7097ee466aa`.

| Block-128 artifact | SHA-256 |
|---|---|
| `01-baseline.wav` | `5b111fe1a1afaaa47f6be75a157fa0887693dfd782bd2f8386d9253790297873` |
| `02-undertow-f3.wav` | `4b97566fd20c2656c15f25904cae985bac017f3f226f66e54189b818e1640e0e` |
| `03-primary-wake-ember-zero.wav` | `129369e98c4ced86733a6fedf9cc586739dc79fa02200b340980bbb060fe6077` |
| `04-rotor-medium-clean.wav` | `1411c0f118194f726ab0099de4fd6be708026a633af5d7be9eede8ae15ed2d93` |
| `05-rotor-high-bloom.wav` | `1a66717da83479086d9483bfdc8d0df64c6a4d553e575b1869426433bd6fed7b` |
| `06-rotor-medium-corroded.wav` | `93fd00b67a9eab442f16fd9a87a561d8825773327312ad3982a884d138a2dfd7` |
| `01-baseline.ledger.csv` | `ec8efbf8eb6ce74f9da3059112845533d9f8bf8583efc5dc74c37f129a3cc9df` |
| `02-undertow-f3.ledger.csv` | `ec8efbf8eb6ce74f9da3059112845533d9f8bf8583efc5dc74c37f129a3cc9df` |
| `03-primary-wake-ember-zero.ledger.csv` | `a0f7da6a204c08d44a9a37f1cfe029af51cbe2ceed88017697c17db21e816c07` |
| `04-rotor-medium-clean.ledger.csv` | `d2b8c34624401edded1d0215fcfe1c5313a526d89ed195a9b5f5910e171915fa` |
| `05-rotor-high-bloom.ledger.csv` | `920b58972fdaf167b44bf4572dc9364e8adc8ae8b353b7062a53105653c94f26` |
| `06-rotor-medium-corroded.ledger.csv` | `d2b8c34624401edded1d0215fcfe1c5313a526d89ed195a9b5f5910e171915fa` |

## What the trial caught

The first complete render exposed a real specification-to-signal failure: clean
conditions sat close to the -1 dBFS ceiling, around `0.748` RMS, and baseline
left-channel DC was about `1.54e-4`. Source review traced this to resonator drive
that was not normalized for pole distance. After normalizing excitation,
retuning bounded gains, and rerunning every affected check, final peaks, RMS,
and DC are the values above. The trial therefore demonstrated why a compilable
instrument and passing state tests are not enough; objective reference renders
must be part of the acceptance loop.

Review also found and corrected semantic defects before freeze: low-frequency
Undertow clamping, Bloom timing, ignored-input provenance mutation, Reset/Panic
state handling, contextual FX leakage, rapid pending gesture collapse,
same-detent Undertow resets, clean/corroded mutation-trace drift, JUCE MIDI
overflow accounting, and controller-default drift.

The Reset assertion uses normalized musical-ledger equality: transition index,
voice, event kind, and energy repeat after removing absolute timeline position.
It does not claim byte equality for absolute `sample_index` or
`ingress_sequence`; proposals should define that equivalence explicitly.

## Evidence boundary

This result proves an isolated source implementation, deterministic host
processing, bounded host-signal observations, exact pinned-JUCE compilation,
and tested MIDI-adapter parity. It does not prove:

- acoustic Undertow pitch tolerance from output estimation;
- that Undertow Off has no contribution in a separately isolated audio
  difference experiment;
- a fixed-round-robin comparator or the listening hypothesis;
- callback timing, lock freedom, or real-time headroom;
- standalone application lifecycle or channel-layout behavior after launch;
- authoritative standalone UI feedback for Source, Scale, Lock, Freeze, FX
  mode, Target, pickup, Bloom, Reset, or Panic state;
- exhaustive fixture-to-compiled-control-map equivalence from one generated
  source of truth;
- a physical Launch Control 3 Custom Mode, capture, takeover, feedback, or
  reconnect path;
- exact Tide Pit source lineage, musical identity, or audible quality;
- serialized state restoration, plugin packaging, distribution licensing,
  target lowering, hardware execution, or Schuss production integration.

See [`TRIAL_GAPS.md`](TRIAL_GAPS.md) for dispositions and workflow changes.

## Follow-up physical MIDI-input source path

After launching the original standalone, the user reported that its GUI worked
but physical MIDI did not. Source inspection confirmed that the app populated a
`MidiMessageCollector` from GUI controls only and registered no physical MIDI
input callback.

The follow-up host-only change adds an input selector, refresh control,
Launch-Control-3 preference, explicit endpoint open/close, collector forwarding,
and a receive counter with last channel/CC/value. It changes neither the
portable Core nor the frozen mapping. The rebuilt standalone and focused tests
passed:

```sh
cmake --build build/cinderwheel-juce-trial \
  --target cinderwheel-instrument cinderwheel_juce_adapter_tests --parallel
ctest --test-dir build/cinderwheel-juce-trial --output-on-failure \
  -R 'cinderwheel_(juce_adapter_tests|mapping_fixture)'
```

Result: both targets built and focused CTest passed `2/2`. No application or
physical endpoint was opened by this validation. Connected-device behavior,
the controller's installed Custom Mode, feedback, reconnect, callback timing,
and listening remain unproved until the user runs the rebuilt app with the
controller.

A second follow-up adds encoder-input reflection after the user confirmed the
physical map works. The MIDI callback publishes only accepted channel-16
CC20-35 values through fixed atomics; the JUCE message thread updates sliders
at approximately 30 Hz with notifications suppressed. The standalone rebuilt
and the focused mapping/adapter CTest again passed `2/2`. This proves the source
and build path, not the visual behavior on the connected controller. The UI
shows raw controller values; it is not yet authoritative state feedback for
FX-A/FX-B while soft pickup is armed.
