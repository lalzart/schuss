# Pamplist 0.6 Local VST3 Host Migration gap register

> Status: target-build complete; higher host, device, listening, licensing, and
> production evidence remains explicitly deferred

| ID | Gap | Severity | Proof required | Disposition |
|---|---|---|---|---|
| GAP-001 | Ableton Live has not scanned, instantiated, automated, recorded, frozen, or resampled the plug-in. | medium | Explicit install/copy and app-launch permission followed by a documented local Live 12.4.1 session. | deferred |
| GAP-002 | Callback deadlines, xruns, CPU, memory, and multi-instance stress have no real-time host measurements. | high | Declared budgets and retained worst-case/p99 observations in an authorized host session. | deferred |
| GAP-003 | No physical Launch Control 3 or Live MIDI-routing session has been run. | medium | Endpoint identity, message receipts, feedback trace, reconnect behavior, and operator result. | deferred |
| GAP-004 | No structured single-instance or layered listening assessment has been performed. | medium | Audition sound, automation, recall, recording, freeze, and resampling in the intended workflow. | deferred |
| GAP-005 | JUCE/VST3 licensing, identity signing, notarization, packaging, and redistribution have not received a release review. | high | Fresh distribution review plus required source, notices, package, and signing evidence. | deferred |
| GAP-006 | The authenticated upstream Macro Voice source retains its known signed-shift UBSan finding. | medium | Upstream-authorized correction or a separately accepted sanitizer disposition without silent source mutation. | retained |
| GAP-007 | Task 045 intentionally accepted only exactly 48 kHz; other rates rendered silence. | low | Task 047 proposal, signal/timeline, allocation, actual-module, target-build, and relocated evidence. | closed in successor Task 047 |
| GAP-008 | Live's presentation of JUCE's 2,080 non-automatable MIDI CC service parameters has not been observed. | medium | Authorized Live scan and parameter-list inspection; revise wrapper policy only if it harms the local workflow. | deferred |
| GAP-009 | Host tempo synchronization and MIDI-note triggering are not implemented. | low | A separate musical requirement and contract. | out of scope |

Task 047 closes only the historical sample-rate constraint in the current
successor adapter. The artifact is otherwise suitable for the next explicit
local Live gate, not yet evidence of Live compatibility, real-time safety,
listening quality, redistribution readiness, or production integration.
