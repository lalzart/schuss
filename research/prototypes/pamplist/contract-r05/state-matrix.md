# Pamplist 0.5: Sixteen-Knob Voice, Motion, and Sequencer Surface state-by-operation matrix

> Status: ready

The Core remains the sole accepted musical/control-state writer. The portable
surface model and JUCE host derive context, sixteen slots, labels, values, and
feedback from the accepted Snapshot. Raw GUI focus and MIDI input remain
diagnostic only. `LaneControlMode` is control presentation state and never an
audio node.

| Operation | Current controls | Pending controls | DSP/audio state | Buffers/write heads | Random/scheduler state | Event provenance | Host/controller/UI feedback | Exact timing and failure behavior |
|---|---|---|---|---|---|---|---|---|
| Initialization | Revision 0.4 defaults plus selected lane 1 and `LaneControlMode::voice`; Trigger Enable On for lane 1 and Off for lanes 2-7 through existing route defaults | Constructor Controls await first 16-frame acceptance | Exact revision 0.4 seven-source/cohesion construction; no context audio state | Exact revision 0.4 fixed source/final quanta and cursor | Exact revision 0.4 phases, addresses, source contexts, and zero started mask | Existing counters zero; accepted mode is Voice in first snapshot | Surface reports Voice top group, Sequencer bottom group, exactly 16 enabled lane slots, accepted Model name, and no endpoint | First supported process accepts defaults before frame zero; invalid enum sanitizes to Voice; construction-only allocation unchanged |
| Reset | Restore every revision 0.4 default plus lane 1 / Voice and binary trigger routes | Discard unaccepted host Controls | Reconstruct exact revision 0.4 source/effect/transport state | Clear exact existing quanta/carry | Restore exact revision 0.4 scheduler/source contexts | Clear accepted sequence, controller edge latches, mode events, and diagnostics | Next accepted snapshot projects default Voice surface | Host invokes reset outside concurrent processing; next quantum is byte-equivalent to fresh revision 0.5 instance |
| Panic | Preserve accepted page, mode, BPM, seed, Voice/Motion/Sequencer/Global values, Master, and clear generation while forcing Running false | Discard unaccepted host Controls | Exact revision 0.4 panic behavior; mode has no DSP state | Exact revision 0.4 carry clearing | Exact revision 0.4 scheduler/source reset | Increment panic count; retain accepted mode | Stopped status retains page/mode and corresponding surface | Host-only before next output sample; no UI/formatting/controller work enters processing |
| Freeze or capture | N/A - revision 0.5 has no freeze, capture, recording, or sampled surface state | N/A | N/A | N/A | N/A | Unsupported operation absent | UI exposes none | Future behavior requires a new approved contract |
| Mode change | Explicit Voice/Motion UI action sets mode; positive edge on already-selected lane toggles; another lane selects and preserves mode; Global selection and Clear remain revision 0.4 | One coherent full Controls value plus controller button-down latches may await next quantum | Mode/page selection alone changes no audio/source/effect state; Voice edits change selected base record; Motion edits change selected route; Sequencer edits selected lane; Trigger Off/On changes only future trigger eligibility | Already-rendered carry is never rewritten | Mode/page changes preserve every scheduler/address/source RNG field | Trace records prior/next page and mode, semantic target, edge status, changed-field mask, and accepted quantum | Accepted mode selects Voice or Motion title/labels/values/tooltips; Global derives its own surface; same-lane re-press is visibly reflected only after acceptance | Valid changes apply at next 16-frame acceptance; duplicate positive and release never toggle; invalid mode becomes Voice; non-target records remain exact |
| Trigger Off or On | Trigger route sanitizes to exact 0 for non-finite/non-positive and exact 1 for positive; physical 0-63 writes Off and 64-127 On | Coherent Controls awaits next quantum | Off prevents a new boundary trigger; On uses exact revision 0.4 trigger rule; already-started voice state is not killed or reconstructed | No buffer is rewritten by the control change | Scheduler, accepted steps, address, probability, and source RNG continue | Trigger event count changes only when an eligible boundary occurs with On | Motion slot displays exact OFF or ON; no signed percentage or Direct label is used for Trigger | Applies at next accepted quantum; Off from fresh reset yields silence, On comparator yields exact revision 0.4 PCM |
| State recall | N/A - no session save, presets, serialization, scenes, or recall | N/A | No recall operation | No preset buffer | No serialized source/scheduler/mode state | Unsupported operation absent | UI identifies volatile session | Future recall must version page/mode plus every existing musical state field |
| Disconnect/reconnect | Preserve accepted page, mode, Trigger state, and every revision 0.4 musical/global field | Untransformed raw endpoint input may be discarded outside Core | Audio/tail continue independently of controller presence | No change | No change | Endpoint identity never enters musical provenance | A future host repopulates from accepted surface Snapshot; no feedback is sent in revision 0.5 | Synthetic mapping only; no endpoint enumeration/open/reconnect claim |
| Non-finite recovery | Revision 0.4 field defaults apply; invalid mode becomes Voice; non-finite Trigger becomes Off; other routes retain signed sanitize | Invalid fields replaced inside one coherent Controls value; unrelated bytes unchanged | Exact revision 0.4 source/effect recovery; context has no signal path | No non-finite value enters carry | Preserve valid scheduler/source state | Existing invalid/clamp/recovery counters increment at affected quantum | Surface formats sanitized accepted values only; raw NaN/infinity is never presented | Sanitize before control mapping, scheduler math, source/effect processing, and UI-model derivation; invalid slot/index fails closed |

## State equivalence

Within one frozen revision 0.5 build, repeatability means byte equality of
stereo PCM and canonical events, accepted snapshots, controller traces, surface
descriptors, and metrics across host partitions 1, 16, 64, 128, 257, and 512.
It includes exact page, `LaneControlMode`, all seven lane/voice records, binary
Trigger values, scheduler integers, started/trigger masks, source RNG contexts,
effect state/diagnostics, and every surface slot's context, group, semantic,
label, tooltip, presentation kind, enabled state, bounds, and accepted value.

Mode-only equivalence compares before/after snapshots excluding only accepted
mode, accepted sequence, and mode provenance; PCM, lane/voice/global records,
scheduler/source/effect state, and diagnostics remain exact. Lane selection
excludes page and accepted sequence only. Trigger-On predecessor equivalence is
exact audio SHA-256 equality with revision 0.4 Dry7 plus exact trigger/source
behavior for the frozen comparator; control snapshots differ only by the new
mode field and revision metadata. Trigger Off from a fresh unstarted reference
requires exact-zero PCM and zero trigger/started masks.

Reset equivalence includes mode Voice and exact binary trigger defaults. C++
padding, pointer addresses, build paths, host handles, raw input, tooltip hover,
window geometry, endpoint identity, and wall time are excluded. Cross-toolchain
floating-bit identity, live deadlines, physical gestures, visual/audible
quality, and production behavior remain unclaimed.
