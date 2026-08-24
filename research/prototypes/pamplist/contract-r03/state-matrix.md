# Pamplist 0.3: Independent Lane Voices state-by-operation matrix

> Status: ready

The Core is the sole musical-state writer. The UI and synthetic controller
trace are projections of coherent accepted snapshots, never raw-input mirrors.
Lane selection changes edit focus only; it never copies or aliases state.

| Operation | Current controls | Pending controls | DSP/audio state | Buffers/write heads | Random/scheduler state | Event provenance | Host/controller/UI feedback | Exact timing and failure behavior |
|---|---|---|---|---|---|---|---|---|
| Initialization | Running true; tempo 120 BPM; seed `0x50414D50`; master gain 0.65; selected lane 1; all eight voices Engine 0, note 48, Harmonics/Timbre/Morph/Decay/LPG Colour 0.5, Level 0.8; lane 1 x1 pulse 4-of-16 amplitude 1 Trigger route 1; lanes 2-8 zero amplitude/routes | Constructor controls await first 16-frame acceptance | Eight exact source instances are constructed once from eight deterministic lane-derived seeds; every voice is unstarted and silent | Eight main and eight auxiliary 16-frame voice quanta plus final main/aux quantum are zero; final read cursor equals 16 so first supported process renders | Master/lane phases, remainders, steps, free addresses, keyed decisions, and started mask are zero; each adapter captures its post-initialization source RNG state | Absolute frame, quantum, accepted sequence, per-lane trigger counts, and diagnostics start at zero | Initial snapshot reports all eight default records, selected lane 1, base/resolved Engine 0 `Virtual Analog VCF`, and no physical endpoint | Construction may allocate fixed objects only; first supported process accepts defaults before frame 0; unsupported sample rate/frame request emits silence and does not advance |
| Reset | Restore every declared default, including all eight distinct records and selected lane 1 | Discard any not-yet-accepted host control value | Reconstruct all eight source voices from their default lane-derived seeds; clear started mask and silence transport/output | Clear all voice/final quanta and set final read cursor to 16 | Zero phases, remainders, steps, addresses, held/smoothed lane random values; restore global seed and eight captured source RNG contexts | Clear accepted sequence, event trace cursor, and every diagnostic | Publish one default accepted snapshot on the next supported process call | Host invokes reset outside concurrent processing; the next quantum is equivalent to a fresh instance and starts at absolute frame zero |
| Panic | Preserve accepted timing and voice values but force accepted running false | Discard unaccepted host control value | Silence immediately for the remainder of the bounded process request; reconstruct all eight voices before a later start | Zero all unconsumed final/voice carry and set cursor to 16 | Zero scheduler state and started mask; preserve accepted global seed and recreate its eight lane-derived source RNG contexts | Increment panic count and retain the absolute frame at request | Snapshot reports stopped state and panic count; UI derives from it | Public panic is host-only and applies before the next output sample; no allocation, lock, or endpoint work occurs |
| Freeze or capture | N/A - revision 0.3 has no freeze, capture, recording, or held-global-state operation | N/A - no freeze or capture command is accepted | Continuous independent lane/voice processing only | No capture storage or write head exists | Addressed repeat windows are musical loop state, not capture | Unsupported operations are absent from the public event type | UI exposes no freeze/capture control | A future capture feature requires a new approved contract and state model |
| Mode change | Lane-select changes only `selected_lane`; Base Engine and other base voice fields change only `voices[selected_lane]`; Model Mod changes only the selected lane route; global seed is an explicitly shared control | One coherent full Controls value may await the next quantum | Selection alone is inaudible; a local base/model change affects only its voice before its next render and has no crossfade; global seed change reconstructs all eight voices and clears started mask by explicit global semantics | Already-rendered final carry is never rewritten; the next quantum uses accepted values | Lane phase/keyed addresses continue across selection and local engine change; a global seed change reinitializes lane decisions and all eight source RNG contexts | Accepted trace records target lane, base/resolved engine indices/names, changed-field mask, and quantum frame | Selected lane reloads all JUCE voice/timing/routing controls from accepted state; engine banner shows its base and resolved names | Valid changes apply at the next persistent 16-frame quantum; invalid indices clamp/count; changing lane A cannot reset or advance B-H unless the changed control is explicitly global seed/transport |
| State recall | N/A - session save, presets, serialization, and recall are unsupported | N/A - no recall queue exists | No recall operation exists | No disk or preset buffer exists | No serialized scheduler, source, or RNG state exists | Unsupported calls are absent from the public API | UI identifies the session as volatile | Future recall must define all eight source-state equivalence and migrations in a new contract |
| Disconnect/reconnect | Preserve every accepted Core global, lane, voice, route, and selected-lane value | A host-only raw MIDI input not yet transformed may be discarded; Core has no endpoint queue | Audio continues independently of controller presence | No voice/final quantum change | No scheduler, keyed lane random, or source RNG change | Endpoint identity and wall-clock disconnect time never enter musical provenance | A future host repopulates controls only from latest accepted snapshot; revision 0.3 sends no physical feedback | Validation constructs messages in memory only; it does not enumerate/open endpoints and proves no reconnect behavior |
| Non-finite recovery | Tempo becomes 120 BPM; Note 48; unit voice fields 0.5 except Level 0.8; master 0.65; non-finite local route becomes zero; integer/enum fields clamp to declared bounds independently per lane | Invalid fields are replaced inside one sanitized coherent Controls value; other lane/voice bytes remain unchanged | A non-finite source sample becomes exact zero for that lane/channel/sample before mixing; finite voices continue | No non-finite value enters voice or final persistent carry | Preserve valid phase/address/source RNG state; invalid scheduler input uses declared default; count recovery | Increment invalid-control, clamp, source-non-finite, or final-saturation counter at the quantum frame and affected lane when applicable | Snapshot shows recovered accepted value and counters; raw NaN/infinity is never formatted or mirrored | Recovery occurs before scheduler math, Q conversion, local source gain, 64-bit sum, and final Q27 saturation; every output remains bounded |

## State equivalence

Within one frozen build and experiment, repeatability means byte equality of
signed 24-bit stereo PCM and canonical per-lane event, accepted-snapshot,
controller, and metrics JSON across host partitions 1, 16, 64, 128, 257, and
512. It also means exact integer equality of absolute frame and quantum,
master/lane phases and remainders, step/loop addresses, keyed decisions, all
eight base and resolved voice records, trigger/started masks, stored source RNG
states, final saturation/recovery counters, and accepted controls.

Lane independence additionally means that a local control, engine, trigger, or
source operation addressed to lane A changes no observable accepted, scheduler,
source-output, or stored RNG state for lanes B-H. A final mixed output is
deliberately excluded from that per-lane equality because additive audio from
lane A is expected to change it. The dedicated adapter test observes each
voice before mixing.

Freshly reset instances are equivalent when every public accepted record and
snapshot, scheduler integer, eight source initializations/RNG contexts, started
mask, persistent samples/cursor, seed, held lane random values, and diagnostics
agree. C++ padding, pointer/allocator addresses, local source/build paths, Git
worktree location, host handles, endpoint identities, wall time, GUI component
state, and unaccepted raw input are excluded. Concurrent processing by multiple
Core instances and cross-toolchain floating-bit identity are not claimed.
