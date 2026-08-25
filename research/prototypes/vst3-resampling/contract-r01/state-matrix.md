# Tide Pit and Pamplist Fixed-Rate VST3 Resampling state-by-operation matrix

> Status: ready

| Operation | Current controls | Pending controls | DSP/audio state | Buffers/write heads | Random/scheduler state | Event provenance | Host/controller/UI feedback | Exact timing and failure behavior |
|---|---|---|---|---|---|---|---|---|
| Initialization | Existing default or already requested complete VST3 program | Existing processor generation barriers remain authoritative | Existing fresh 48 kHz Core; converter is bypassed at 48 kHz or prepared for one declared fixed host rate | Source scratch, history, host/source counters, and phase start at zero; FIR phases are prepared outside the callback | Existing instrument seed/scheduler reset exactly as Task 045/046 | No prior raw MIDI or musical event survives | Status shows fixed 48 kHz Core, active host rate, and bypass/resampling truth; accepted UI begins from existing fresh snapshot | Unsupported/nonintegral rate or layout leaves processor unprepared and output silence; supported rate sets latency before first block |
| Reset | Complete requested program is retained under each existing state rule | Pre-reset Clear/Mutate/Freeze generation barriers remain instrument-owned | Fresh existing Core; no musical equation changes | FIR history, scratch, rational phase, host/source counters, scope/history presentation reset to zero | Existing seed and scheduler fresh-state behavior | Pre-reset pending wrapper history and pre-barrier one-shots do not cross reset | UI may briefly show fresh default accepted state until the first post-reset accepted snapshot | First valid post-reset block begins a new timeline and non-bypass output includes the full reported latency transient |
| Panic | Pamplist Run and Tide Pit requested values follow existing release/panic rules | No new pending state is introduced | Existing Core panic/release behavior; converter becomes non-observable while unprepared | History is retained only as inaccessible object memory until next prepare/reset clears it | Existing Core-owned random/scheduler behavior only | Incoming MIDI is cleared by existing processor behavior | Processor reports unprepared; no endpoint is owned | `releaseResources` sets zero or non-observable latency state and later prepare follows Initialization |
| Freeze or capture | Tide Pit Freeze and Pamplist Clear retain existing non-persistent action semantics | Existing one-shot generation counters only | Existing instrument action at mapped source frame; converter has no capture state | FIR history continues normally and is not serialized | Existing Core scheduler/random changes only | Host offset maps to `B(E)`; equal mapped actions retain ingress order | Accepted Core state remains UI authority | Action cannot occur before `B(E)`; Tide Pit may further quantize through its existing 16-frame bridge |
| Mode change | Existing desired persistent modes/controls | Existing parameter snapshot or raw-MIDI dispatch | Existing Core acceptance and smoothing | Converter history and phase continue without reset | Existing instrument scheduler/randomness | Host offset maps through the exact shared timeline, then instrument-owned rules apply | Requested host value and accepted Core value remain distinct where already designed | At 48 kHz existing exact timing; elsewhere never-early source mapping plus reported output delay |
| State recall | Complete validated existing program replaces requested state transactionally | Existing reset barrier supersedes older pending one-shots | Fresh Core under Task 045/046; evolving audio, tail, mutation/capture, and timeline remain excluded | FIR history and all converter counters clear; no pre-recall sample leaks | Existing fresh seed/scheduler behavior | Raw MIDI edge state and wrapper history do not restore | Existing state schema/fingerprint and accepted-state presentation are unchanged | Invalid state retains prior program and running history; valid recall applies once at next valid block and restarts latency transient |
| Disconnect/reconnect | N/A — VST3 owns no physical endpoint | N/A — Ableton owns routing | Host reprepare is Initialization; no device state exists here | Reprepare clears converter state | Existing Core reprepare behavior | No endpoint receipt claim | Status reflects host callback state only | No connected-device evidence is inferred |
| Non-finite recovery | Existing parameter/state validators reject non-finite input | No non-finite coefficient or ratio is queued | Invalid rate fails prepare; existing Core diagnostics own non-finite source handling | Invalid plan or non-finite runtime output clears the current output block and increments bounded failure diagnostics | Existing Core recovery only | Malformed MIDI retains existing ignored/counting behavior | Status may report process failure count; accepted state is not fabricated | No allocation, retry loop, ratio fallback, or silent substitution of another host rate |

## State equivalence

At 48 kHz, repeatability remains exact float PCM and the predecessor normalized
accepted-state/event equality. At the other declared rates, fresh-state twins
must have exact rational source counts, mapped event sequence, reported
latency, and equal float PCM when processed with the same host partition; the
analytic signal fixtures use the proposal's numeric tolerances. Repartitioned
timelines must have exact source/event accounting and equal PCM after aligning
the same reported latency relation.

Deliberately excluded are pre-reset FIR history, absolute pre-reset host/source
counters, raw ingress diagnostic counts where predecessor contracts already
normalize them, GUI repaint timing, host handles, endpoint/device identity,
callback wall time, and any listening judgment.
