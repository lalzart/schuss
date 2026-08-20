# Tide Pit Gills Portable JUCE Port state-by-operation matrix

> Status: ready

| Operation | Current controls | Pending controls | DSP/audio state | Buffers/write heads | Random/scheduler state | Event provenance | Host/controller/UI feedback | Exact timing and failure behavior |
|---|---|---|---|---|---|---|---|---|
| Initialization | Discrete source state is C4, MAJ5, PIT, REED, CLEAN, EVOLVE, not captured; adapter audition preset supplies continuous controls | Empty | Explicitly zeroed source object then exact `Init`; initial strike pending | Fixed arena allocated in source order; recorder cleared and writable | stmlib LCG `0x21`; mutation xorshift `0x70697421`; phase/stage zero | prepare/reprepare only | Complete initial snapshot and exact display lines | Only 48 kHz accepted; allocation or rate failure produces silence and prepare error |
| Reset | N/A — source instrument exposes no musical Reset | N/A | N/A | N/A | N/A | Invalid Reset action is ignored and counted | UI exposes no Reset control | No Reset or invented state clearing |
| Panic | N/A — source instrument exposes no Panic | N/A | N/A | N/A | N/A | Invalid Panic action is ignored and counted | UI exposes no Panic control | No Panic or invented state clearing |
| Freeze or capture | Controls unchanged | Capture gesture synthesizer may remain active until source hold threshold | Source toggles `captured_`; DSP continues | Recorder write stops while grains read retained audio; resume uses source 256-sample write fade | Grain/random streams continue exactly | Semantic `capture-toggle` becomes source button level at next quantum | Snapshot changes only when source state changes | 75-block debounce plus 1,500 stable held blocks; release must not emit effect tap |
| Mode change | Per-mode effective FX A/B values retained; raw controls may be uncaptured | Effect/scale/target synthetic gesture or next continuous value | Source/effect/scale/target state changes through original handler; effect state resets only as source defines | Recorder/body/reverb persist; effect-specific state reset follows source | Pitch dirty/strike flags follow source | Ordered semantic event at next 16-frame quantum | Snapshot exposes accepted mode/effective values and source lines | Source next/lock/mutate are rising edges; effect and encoder gestures preserve source debounce/hold/crossfade |
| State recall | N/A — plugin preset/state serialization excluded | N/A | Reprepare creates a fresh instance only | Fresh buffers | Seeds reset only on fresh prepare | Host recall unsupported and counted if presented | UI states no preset support | No evolving/frozen state serialization claim |
| Disconnect/reconnect | Core control state remains unchanged | Adapter queue remains bounded; no synthesized stuck press survives adapter reset | Audio Core continues if audio device remains active | Unchanged | Unchanged except ordinary processing | MIDI endpoint lifecycle is host-only | Selector/diagnostics update; no controller feedback claim | Physical reconnect correctness remains connected-device evidence |
| Non-finite recovery | Valid current controls retained | Invalid/non-finite host control is rejected | Q27 output has no non-finite representation; normalized host output is checked for finiteness without claiming source recovery | Source buffers remain untouched | Source random state continues | Invalid-control diagnostic; retained render finite-sample measurement | UI exposes input rejection counts | Reject non-finite controls before source processing; render validation fails closed on any non-finite normalized sample |

## State equivalence

The canonical reference relation is byte equality of the 1,536,000-byte planar
little-endian Q27 stream on the named macOS toolchain. Outer block partitions
must yield the same Q27 stream and exact final snapshot for identical semantic
events quantized to source boundaries. Focused Core and adapter tests compare
the state/display checkpoints named by their operations. Direct semantic and MIDI
adaptation equality ignores host handles, endpoint names, wall-clock time,
absolute ingress counter origins, and UI repaint cadence. Cross-platform
floating-point builds require exact normalized final state/checkpoints and separately
retained signal tolerances; they do not inherit the macOS byte-equality claim.
