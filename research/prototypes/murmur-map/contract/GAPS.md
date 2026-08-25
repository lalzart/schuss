# Murmur Map 0.1 implementation gap register

> Status: revision 0.1 implemented; higher evidence and product integration remain open

Keep a gap visible when a lower evidence level passes. Do not rewrite deferred
real-time, device, listening, license, or production-integration work as source
success.

| ID | Gap | Severity | Owner/stage | Current decision | Proof required | Disposition |
|---|---|---|---|---|---|---|
| GAP-001 | The central route-coherence claim has no listening result. | high | Listening gate | Keep MM10 as the frozen matched comparator. | Six blinded 45-second A/B pairs meet the proposal thresholds for the exact build. | deferred |
| GAP-002 | The Murmur Map Launch Control 3 mapping and endpoint lifecycle have not been exercised physically. | high | Connected-device gate | Build explicit selection, refresh, receipt, and mapping diagnostics; make no device claim. | Named controller/Custom Mode session confirms channel 16 CC20-35 and CC40-47, capture semantics, reconnect, and accepted-state display. | deferred |
| GAP-003 | Target build does not establish callback deadline, allocation, or xrun behavior. | high | Real-time gate | Keep synthetic/offline timing separate and avoid a live claim. | Named audio interface, sample rate, block size, lifecycle, allocation, p99, worst-case, and xrun record. | deferred |
| GAP-004 | The shared Braids adapter owns process-global stmlib random state. | medium | Prototype scope | Support one Murmur Map Core per process in revision 0.1 and seed it deterministically; do not claim concurrent-instance isolation. | Separate adapter/runtime design and contention/determinism tests if multi-instance use is requested. | accepted limitation |
| GAP-005 | Only 48 kHz and host blocks through 512 frames are supported. | medium | Future host adapter | Fail closed at other sample rates or oversized blocks. | Separately frozen resampling contract and multi-rate parity evidence. | deferred |
| GAP-006 | Standalone visual layout and interaction have no launched-app inspection. | medium | App gate | Compile the restrained UI and retain accepted-state model tests without launching. | Fresh built-app visual inspection covers resizing, map drag/capture, labels, diagnostics, and failure states. | deferred |
| GAP-007 | JUCE and selected Mutable closures are private-development dependencies with distribution review still required. | high | Distribution gate | Produce an uninstalled private build with notices; do not package or distribute. | Exact license, notice, branding, binary, and distribution review for the intended release mode. | deferred |
| GAP-008 | Canonical Schuss identity, graph/provider/runtime ownership, and Ksoloti/Gills feasibility are absent. | medium | Production integration | Keep the prototype noncanonical and transparent. | Separate accepted task allocates exact identities and closes target/provider evidence without deriving them from source ancestry. | deferred |
