# Tide Pit and Pamplist Fixed-Rate VST3 Resampling implementation gap register

> Status: implementation and target-build evidence complete; all higher-level
> gaps below remain open or explicitly accepted

Keep a gap visible when a lower evidence level passes. Do not rewrite deferred
real-time, device, listening, license, or production-integration work as source
success.

| ID | Gap | Severity | Owner/stage | Current decision | Proof required | Disposition |
|---|---|---|---|---|---|---|
| GAP-001 | Ableton Live has not scanned, instantiated, automated, recorded, frozen, or resampled either successor module at a non-48-kHz rate. | medium | Later local Live gate | Do not install or launch in Task 047. | Explicit installation/app-launch authority and a documented Live session at 44.1, 48, and 96 kHz. | deferred |
| GAP-002 | Callback deadlines, xruns, CPU, memory, and useful layered instance counts are unmeasured, especially at 176.4 and 192 kHz. | high | Later real-time gate | Offline allocation and signal tests do not promote real-time safety. | Declared M1 Pro budgets with retained worst-case and p99 Live observations at each intended rate. | deferred |
| GAP-003 | No physical Launch Control 3 route has exercised the resampled event timeline. | medium | Later connected-device gate | Preserve existing maps and test synthetic host MIDI only. | Endpoint identity, message receipt/order, feedback, reconnect, and operator result in Live. | deferred |
| GAP-004 | No structured listening comparison has judged the 129-tap transition band, reset transient, or layered character. | medium | User listening gate | Objective passband/alias metrics are not a listening judgment. | Level-matched 44.1/48/96-kHz audition of both instruments, automation, recall, freeze/resample, and layers. | deferred |
| GAP-005 | JUCE/VST3 and Pamplist GPL/private-use redistribution boundaries, signing, notarization, packaging, and public release remain unreviewed. | high | Distribution gate | Keep both successor bundles private and uninstalled. | Fresh license review, required source/notices, signing/notarization, package, and release evidence. | deferred |
| GAP-006 | Host rates outside 32, 44.1, 48, 88.2, 96, 176.4, and 192 kHz remain unsupported. | low | Requirement-driven later design | Fail closed rather than allocate an unbounded phase bank or accept an untested ratio. | Concrete host requirement, frozen capacity/tolerance update, and new signal/module evidence. | accepted constraint |
| GAP-007 | Non-bypass callbacks above 8,192 frames render silence. | low | Host-bound capacity | Preserve fixed storage and bounded callback work. | Evidence of a real host callback above the cap followed by an approved larger bound and allocation regression. | accepted constraint |
| GAP-008 | State recall/reset clears FIR history and produces the reported-latency initial transient. | low | Intentional fresh-state rule | Prevent pre-reset samples leaking into fresh Core state. | A separately approved tail-preserving state design if the transient proves musically harmful. | accepted behavior |
| GAP-009 | Pamplist's authenticated Macro Voice signed-shift sanitizer findings at `macro_voice_dsp.h:122` and `:123` remain. | medium | Upstream/source authority | Do not rewrite source as part of resampling. | Upstream-authorized correction or separately accepted sanitizer disposition. | retained |
| GAP-010 | The repository-wide compatibility partition is not green because an unchanged desktop bridge test expects five instruments while inherited Task 043 audition-library v2 correctly returns six. | medium | Task 043 compatibility closeout | Do not mutate inherited Task 043 or its tracked historical test under Task 047. | Reconcile the bridge expectation with the accepted six-entry Task 043 authority, run its focused test, then run compatibility under the owning task. | inherited; deferred |
