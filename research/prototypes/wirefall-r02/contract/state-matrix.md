# Wirefall revision 0.2 state-by-operation matrix

> Status: ready

Events at absolute frame `k` are accepted in stable input order before rendering
frame `k`. Core processing has fixed capacities: 512 host frames and 128 events
per process call. Rejection increments a diagnostic and leaves musical state
unchanged.

| Operation | Current controls | Pending controls | DSP/audio state | Buffers/write heads | Random/scheduler state | Event provenance | Host/controller/UI feedback | Exact timing and failure behavior |
|---|---|---|---|---|---|---|---|---|
| Initialization | Load ENERGY `.32`, BREAK `0`, PULSE `OFF`, TICK `0`, ROOT `0 st`, COLOR `.55`, WIDTH `.35`, EDGE `.34`, SPACE `.10`, OUTPUT `.82`, TEMPO `120`, OPEN false, PANIC false | Smoothers begin at the accepted defaults; no latent raw values | Oscillator phase, SVF integrators, DC state, tick state, and reset/panic envelope start at deterministic zero/running values | Delay arrays are zero; write heads are zero | Pulse phase zero; deterministic seed `0x57465232` is stored but unused | Initial values are tagged `default` | UI reads accepted state after `prepare`; no endpoint/device state exists | Unsupported sample rates or capacities fail `prepare` without partial mutation |
| Reset | Accepted control targets and TEMPO remain unchanged | Smoothers are cleared to their accepted targets at the clear point | Start/restart 240-frame linear fade-down; at zero clear oscillator, SVF, DC, tick, fault window, and pulse state; then 240-frame fade-up | Zero both delay arrays and write heads at the clear point | Pulse phase returns to zero; seed remains unused | Reset request records its accepted absolute frame; a second request replaces the first reset sequence | Feedback reports `fade-down`, `clear`, `fade-up`, then `running` | Request is applied before its frame; second Reset restarts fade-down from the current envelope; no allocation or exception |
| Panic | Accepted continuous controls remain unchanged; panic latch becomes true on press and false on release | Smoothing continues | Press starts 480-frame fade-down and then exact silence while latched; release clears the non-finite window and starts a 240-frame fade-up | Delay buffers and write heads continue deterministically | Pulse phase continues; tick triggers may advance but are inaudible while latched | Press/release frames and automatic non-finite escalation share the same accepted panic operation | Button/status follows accepted latch and fade state, not raw UI input | Press and release apply before their frames; output is multiplied by the safety envelope after synthesis; repeated press restarts fade-down |
| Freeze or capture | N/A — no Freeze or capture control exists | N/A — no pending capture values exist | N/A — the vertical slice has no capture buffer or frozen DSP state | N/A — no capture buffer exists | N/A — no capture scheduler exists | Any such event is rejected as an unknown operation and counted | No feedback or physical mapping is presented | Fail closed with no musical-state mutation |
| Mode change | PULSE selector changes are accepted as direct semantic values; comparator mode is renderer-only and cannot be selected by the standalone UI | The selector uses `.012` normalized detent hysteresis at the adapter; Core receives a resolved index | Wire/filter state continues | Buffers and write heads continue | New PULSE rate preserves normalized phase; OFF holds the current phase and opens the scheduled gate | Accepted value and absolute frame enter the event ledger | UI label shows the accepted literal rate | Invalid selector indices are rejected and counted; a rate change cannot create an extra phase wrap at the current frame |
| State recall | N/A — presets and state serialization are outside this vertical slice | N/A — no recall queue exists | N/A — no recalled audio state exists | N/A — no recalled buffers exist | N/A — no recalled scheduler state exists | Recall requests are not part of the public event enum | No recall feedback is exposed | No claim; an unknown operation fails closed without mutation |
| Disconnect/reconnect | N/A — no MIDI, controller, network, or physical endpoint is opened | N/A — no endpoint queue exists | Core lifetime is independent of endpoint state | N/A — no endpoint-owned audio buffers exist | N/A — no endpoint clock exists | Only mouse/renderer semantic events exist | UI is local accepted state only; endpoint/device evidence remains deferred | No reconnect behavior or evidence is claimed |
| Non-finite recovery | Offending incoming control/event is rejected; last accepted target remains | Valid pending smoothing remains | An invalid intermediate sample becomes zero and increments the rolling fault window; the third fault within 48,000 rendered frames invokes Panic | Buffers retain only finite samples; a non-finite delay read/write is replaced with zero | Pulse phase is sanitized to zero if invalid; seed remains unused | Diagnostic records fault count and escalation frame | Status reports panic escalation; no strings/logging are generated inside process | Three faults in a rolling 48,000-frame window begin the 480-frame panic fade before that frame's final output; release clears the window |

## State equivalence

Reset repeatability is byte equality of future interleaved output and normalized
musical state after the reset fade completes, given identical subsequent events
and process partitions. Normalized state includes accepted controls, smoother
values, oscillator/filter/DC/delay/tick state, delay contents/write heads, pulse
phase, reset/panic envelopes, and seed value. It deliberately excludes the
absolute rendered-frame counter, monotonic ingress/rejection/fault diagnostics,
and retained provenance timestamps. Partition equivalence is byte equality of
24-bit WAV payloads plus canonical accepted-event ledgers for the complete
frozen condition.
