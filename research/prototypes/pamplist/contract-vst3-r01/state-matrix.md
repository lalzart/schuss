# Pamplist 0.6 Local VST3 Host Migration state-by-operation matrix

> Status: ready

`Current controls` means the coherent value used for the next Core segment.
Stable host parameter values are atomic adapter state. The audio thread alone
owns `Core`, `ControllerAdapter`, Q27 scratch arrays, process counters, and
accepted-snapshot publication.

| Operation | Current controls | Pending controls | DSP/audio state | Buffers/write heads | Random/scheduler state | Event provenance | Host/controller/UI feedback | Exact timing and failure behavior |
|---|---|---|---|---|---|---|---|---|
| Initialization | Build from 178 source defaults, Run On, default seed, page 0, Voice mode, Clear generation 0 | No pending one-shot; parameter atomics already contain the program | Fresh Core and source Macro Voices; processor not prepared until host calls prepare | Two fixed 512-frame Q27 scratch arrays; host buffer external | Default addressed seed; timeline frame zero | Construction only | Editor may show program but reports not prepared until a valid 48 kHz stereo prepare | No endpoint opens and no audio renders during construction; allocation is permitted outside processing |
| Reset | Re-read complete parameter atomics plus seed/page/mode; Clear generation set to the audio-thread applied generation | Consume the latest reset generation exactly once | Call Core reset and ControllerAdapter reset; replace accepted snapshot with the fresh Core snapshot | Scratch contents are irrelevant and are overwritten before conversion | Timeline, lane phase/remainders, addresses, and voice random state return to source defaults | Host prepare or a validated state transaction generation | Accepted history reducer rebases; prior Clear feedback ends | Reset occurs on the audio thread before the next rendered sample; multiple pending requests coalesce to the newest generation |
| Panic | Persistent program remains unchanged | Clear any pending one-shot and mark processor unprepared | Call Core panic then reset before later valid prepare; output silence | Clear all host output channels; no write head exists | Volatile source scheduler is discarded | Host releaseResources or processor destruction | Editor status becomes not prepared; no fabricated accepted activity | No Core processing after release until a valid prepare; destruction closes no endpoint |
| Freeze or capture | Unchanged | Unchanged | N/A - the plug-in has no capture or freeze subsystem | N/A - Ableton owns recording, freeze, and sample storage | Unchanged | Host operation is outside the plug-in contract | No plug-in feedback beyond ordinary processing | Pamplist continues only when the host invokes process; no capture state is serialized |
| Mode change | Selected page or lane mode changes private presentation state; musical parameters remain unchanged | One atomic private value update | Core receives the page/mode in the next Controls snapshot; DSP sound is unchanged unless the same MIDI gesture is defined as Clear | Audio scratch unchanged | Timeline and randomness unchanged | Editor click or existing channel-16 page/mode CC at a declared sample position | Page buttons, group labels, slots, and tooltips change only after accepted snapshot projection | Editor private changes apply at the next Core segment boundary; MIDI changes apply before their exact host sample; repeated Global press may issue one Clear through existing edge semantics |
| State recall | Candidate contains all 179 normalized values, seed, page, and mode; complete validated candidate replaces current atomics transactionally | Increment reset generation; Clear generation and pending Clear are absent | Fresh Core is requested; voice internals, tails, timeline, diagnostics, controller edge memory, and impact history are not restored | Scratch remains fixed and is overwritten; no serialized audio buffer exists | Restored seed starts a fresh addressed timeline at frame zero | Host state bytes with exact schema version and unique complete IDs | Editor eventually projects the new accepted fresh snapshot and rebases history | Parse and validate off the audio path; malformed, truncated, wrong-version, duplicate, missing, non-finite, or out-of-range state leaves every prior value and reset generation unchanged |
| Disconnect/reconnect | Parameter program and private recalled state remain in processor memory while the instance exists | Pending Clear is discarded on release; a later prepare requests reset | releaseResources panics; valid prepare creates fresh volatile Core state | Host output is silent while unprepared; fixed scratch remains instance-owned | Restart at frame zero using retained seed | Host lifecycle only | Prepared status changes; no physical endpoint identity exists | Only exactly 48 kHz and mono-disabled stereo output becomes ready; reconnect at unsupported rate remains silent |
| Non-finite recovery | Custom parameters accept only bounded normalized finite values; Core sanitizer remains final authority | Invalid state candidate is discarded wholly | A failed Core call increments adapter failure diagnostics and the affected segment remains silent; next valid segment may continue | Clear the full host buffer before rendering, then overwrite only successful segments | Prior valid seed/scheduler retained unless a valid reset was committed | Malformed host state, invalid parameter conversion, or Core failure is recorded separately | Status reports invalid state, unsupported host, or process failure without displaying rejected values as accepted | No exception, partial state, NaN, infinity, out-of-bounds write, endpoint action, allocation, or lock is permitted in repeated processing |

## State equivalence

For an uninterrupted 48 kHz run with identical initial program, seed, block
partition, and sample-positioned CC events, equivalence is exact Q27 output,
exact deterministic float conversion, and equality of accepted musical state,
absolute frame, event, trigger, Clear, and diagnostic traces.

For state recall, equivalence is deliberately **fresh-program equivalence**:
after a valid state transaction, the restored instance must equal a newly
constructed Core started at frame zero with the same 179 parameter values,
seed, page, and mode. Hidden voice state, timeline phase, cohesion tail,
diagnostic counters, controller button-edge memory, accepted sequence number,
editor impact history, host handles, and absolute ingress counters are excluded.
Clear is excluded from serialized state and therefore must not occur until a
new accepted action is delivered.
