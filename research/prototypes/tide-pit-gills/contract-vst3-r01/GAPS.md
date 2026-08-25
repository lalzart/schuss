# Tide Pit Local VST3 Host Migration implementation gap register

> Status: target-build complete; Live, real-time, device, listening, licensing,
> and production evidence remains explicitly deferred

| ID | Gap | Severity | Owner/stage | Current decision | Proof required | Disposition |
|---|---|---|---|---|---|---|
| GAP-001 | Ableton Live has not scanned, instantiated, automated, recorded, frozen, or resampled the plug-in. | medium | Later local Live gate | Do not install or launch in Task 046. | Explicit copy/install and app-launch authority plus a documented Live 12.4.1 session. | deferred |
| GAP-002 | Callback deadlines, xruns, CPU, memory, and useful multi-instance count have no real-time host measurements. | high | Later real-time gate | Offline allocation checks may pass but cannot promote real-time safety. | Declared M1 Pro budgets and retained worst-case and p99 Live observations. | deferred |
| GAP-003 | No physical Launch Control 3 or Ableton MIDI-routing session has run for the plug-in. | medium | Later connected-device gate | Preserve raw channel-16 mapping and test only synthetic host buffers. | Endpoint identity, receipt trace, feedback, reconnect behavior, and operator result. | deferred |
| GAP-004 | No structured single-instance or layered listening assessment has been performed. | medium | User listening gate | Objective parity is not a listening judgment. | Audition continuous controls, modes, actions, recall, automation, record, freeze, resample, and layered instances. | deferred |
| GAP-005 | JUCE/VST3 licensing, identity signing, notarization, packaging, and redistribution have not received a release review. | high | Distribution gate | Private uninstalled local build only. | Fresh license review, required source/notices, identity signing, notarization, and package evidence. | deferred |
| GAP-006 | Task 046 intentionally accepted only exactly 48 kHz; other host rates rendered silence. | low | Task 047 successor | Preserve this historical result; use the separately evidenced fixed-rate adapter successor. | Task 047 proposal, signal/timeline, allocation, actual-module, target-build, and relocated evidence. | closed in successor Task 047 |
| GAP-007 | Freeze audio, mutation state, random progress, timeline, tails, and other evolving Core internals are not serialized. | medium | Separate state design | Recall is explicitly fresh-Core and Freeze off. | Exact bounded Core serialization contract, migration policy, and source-equivalence tests. | accepted constraint |
| GAP-008 | Live's presentation of JUCE's standard bypass and VST3 MIDI-controller service parameters is unknown. | medium | Later Live UI gate | Keep the sixteen Tide Pit parameters first and wrapper service parameters non-musical. | Authorized Live scan and parameter-list inspection. | deferred |
| GAP-009 | Persistent desired modes can lag host values while the exact source tap or hold gesture completes. | low | Later Live usability gate | Accepted-state UI shows actual Core state while automation retains the desired value. | Authorized Live automation and usability observation. | accepted behavior |

Task 047 closes only the historical sample-rate constraint in the current
successor adapter. The artifact is otherwise suitable for the next explicit
local Live gate. None of the higher gaps is closed merely by compiling,
scanning, or signal-testing the module in the separate offline host.
