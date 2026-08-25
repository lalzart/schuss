# Pamplist 0.6: Control Response and Impact Trails state-by-operation matrix

> Status: ready

| Operation | Current controls | Pending controls | DSP/audio state | Buffers/write heads | Random/scheduler state | Event provenance | Host/controller/UI feedback | Exact timing and failure behavior |
|---|---|---|---|---|---|---|---|---|
| Initialization | Exact revision 0.5 defaults: Running, 120 BPM, Master 0.65, lane 1 Voice, Trigger On for lane 1, Cohere zero | Host owns one coherent default Controls value | Seven fresh source voices; empty stable body; cumulative lane/body energy zero | Source/output quanta zero; fixed UI history empty | Existing seed, phase, address, and source contexts | Existing diagnostics/counters zero | Accepted Voice surface plus empty seven-colour history | First supported process accepts at the first 16-frame quantum; construction-only allocation remains allowed |
| Reset | Restore exact revision 0.5 defaults and clear cumulative telemetry | Discard unaccepted host Controls | Reconstruct source/effect/transport state; energy zero | Zero quanta/carry; UI detects rollback and rebases on next poll | Reset phases, addresses, deterministic source contexts | Clear diagnostics, triggers, Clear count, and accepted sequence | Activity reducer emits one exact-zero sample; fixed history may remain as truthful prior UI memory until overwritten | Host-only lifecycle call; next audio is fresh-instance exact; no false telemetry spike |
| Panic | Preserve accepted musical/global values while forcing Running false as revision 0.5 | Discard unaccepted host Controls | Reset source/effect transport and zero energy through existing transport reset | Clear quanta/carry | Existing panic semantics reset scheduler/source state | Increment panic count | Subsequent polls append zero; controls remain projected from accepted Snapshot | Host-only; no UI/allocation work on callback |
| Freeze or capture | N/A - Pamplist has no freeze, capture, recording, or sampled-surface state | N/A | N/A | N/A | N/A | Unsupported operation absent | UI exposes none | Future behavior requires a new contract |
| Mode change | Voice/Motion/page and every existing field retain revision 0.5 ownership; Phase/Shape/Rotate and Global values accept coherently | One whole Controls value may await the next source quantum | Phase/Shape/Rotate retain equations; body targets smooth; telemetry observes resulting sound only | Already rendered carry is never rewritten | Existing future-boundary behavior; source state persists | Accepted sequence changes; activity uses existing trigger counts | Surface and dependency tooltips follow accepted state; history remains always visible | Apply at the next 16-frame acceptance; invalid fields sanitize; parameter change alone never fabricates a trigger/history event |
| Clear FX | Preserve all controls except incremented effect-clear generation | One coherent generation change may await acceptance | Zero six complex modes and duck envelope only; cumulative lane energy and history remain | No voice/output history rewrite; next effect-only sample has no prior body tail | Scheduler, address, probability, and source RNG exact | Increment one Clear count and retain one Clear event | Button briefly reports CLEARED; activity reducer emits one marker; lane history is not erased | Apply once at next accepted quantum; duplicate generation is no-op; silent body still reports accepted Clear without claiming audible change |
| State recall | N/A - no presets, serialization, scenes, or recall | N/A | N/A | N/A | N/A | Unsupported operation absent | UI identifies volatile session | Future recall must version cumulative telemetry or explicitly rebase it |
| Disconnect/reconnect | Accepted Controls, telemetry, and Core continue independently of controller presence | Raw endpoint input may be discarded outside Core | No DSP change | No change | No change | Endpoint identity never enters musical provenance | History continues from accepted audio; no physical feedback claim | Synthetic mapping only; no endpoint enumeration/open/reconnect evidence |
| Non-finite recovery | Existing sanitization replaces invalid controls; telemetry fields derive only from bounded integer source samples | Invalid pending fields replaced within one coherent value | Nonfinite body state clears effect history and returns dry; telemetry never controls recovery | No invalid value enters UI history | Preserve valid scheduler/source state | Existing invalid/clamp/recovery counters increment | Activity reducer clamps negative/nonfinite delta to zero and rebases on rollback | Sanitize before processing; body failure uses dry path; readiness requires finite Snapshot/activity output |

## State equivalence

Within one frozen revision 0.6 build, repeatability means byte equality of
stereo PCM, canonical events, accepted snapshots including cumulative lane and
body telemetry, activity outputs, controller/surface outputs, and metrics across
host partitions 1, 16, 64, 128, 257, and 512. The revision 0.5 dry comparator
requires exact audio SHA-256 equality when Cohere is zero.

Reset equivalence is fresh-instance equality for Controls, audio, scheduler,
source state, effect state, diagnostics, and cumulative telemetry. The
UI-owned visual ring is deliberately not DSP state; on counter/frame rollback
its reducer rebases with one zero sample and retains or overwrites previous
screen history without feeding Core.

Mode-only and page-only equivalence retain revision 0.5 exclusions: accepted
mode/page, accepted sequence, and presentation/provenance may differ while PCM,
musical records, scheduler, source, effect, and telemetry remain exact. Clear
equivalence excludes only generation/count/event and effect state; lane/voice,
scheduler/source, dry PCM, and cumulative lane energy remain exact.

Host pointers, object padding, build paths, UI pixels, timer wall time, endpoint
identity, raw MIDI, window geometry, and paint order are excluded. Visual
quality, live timing, device behavior, listening, and production remain
independent claims.
