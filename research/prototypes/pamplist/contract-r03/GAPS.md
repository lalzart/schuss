# Pamplist 0.3 independent-voice gap register

> Status: implementation and bounded host/target-build validation complete; real-time, device, listening, distribution, and production work remain outside this iteration

Passing a lower evidence level never closes a higher one. The committed
revision 0.2 contract and evidence remain historical authority for that design;
they do not prove revision 0.3.

| ID | Gap | Severity | Current decision | Proof required | Disposition |
|---|---|---|---|---|---|
| GAP-001 | Eight per-lane base voice records, persistent sources, local routes, and fixed final mixer | blocker before host evidence | Implemented as eight lane-owned source instances and one fixed additive final mixer | Focused state/isolation tests, source-bound build, no-allocation check, and complete diff review | closed |
| GAP-002 | Process-global source RNG can couple otherwise separate stochastic voices | blocker before independence claim | Save/restore one deterministic RNG context around every voice construction/reset/render | Byte-exact standalone versus interleaved stochastic voice output and final RNG state | closed for one single-threaded Core |
| GAP-003 | Source-order engine labels and base versus resolved UI presentation | blocker before requested UI claim | Frozen 24 descriptive labels; selected accepted base and resolved engine are projected by index and name | Exact table test, snapshot test, and authenticated JUCE compile | closed at build level; hands-on clarity remains GAP-009 |
| GAP-004 | Objective eight-voice behavior, local Model Mod, partition invariance, mix bounds, and comparator divergence | blocker before host-signal evidence | Retained eight frozen successor conditions after implementation freeze | Exact PCM/event/snapshot/metric hashes across six partitions | closed |
| GAP-005 | Authenticated standalone target | blocker before target-build | Built and hashed without launch | JUCE authentication, configure, compile, link, executable identity/hash receipt | closed |
| GAP-006 | Live audio-device callback deadline, lifecycle, CPU headroom, and xruns with eight voices | high for real-time promotion | Deferred; no launch or endpoint access authorized | 48 kHz device run with declared blocks/load, lifecycle, xruns, worst-case, and p99 callback measurements | open |
| GAP-007 | Concurrent processing of more than one Pamplist Core | high if a future host requires it | Not claimed; one Core owns the single audio-thread source boundary because dependency RNG is static | Thread-safe upstream boundary or external serialization plus race/concurrency tests | deferred |
| GAP-008 | Physical regular Launch Control 3 identity, receipt, gesture scale, feedback, and reconnect | high for connected-device claim | Synthetic protocol only; no new base-voice hardware page | Exact endpoint and observed CC20-47 receipt, control feel, accepted-state behavior, disconnect/reconnect | open |
| GAP-009 | Voice separation, balance, engine-change clicks, label clarity, and musical usefulness | medium | User's 0.2 report is input, not controlled 0.3 listening evidence | Documented audition of dual/eight/model-local/comparator conditions | open |
| GAP-010 | Manual drone/start, mute, solo, pan, cross-lane sends, controller page for base voice controls, effects, presets, and crossfades | enhancement | Excluded from this correction | New approved design and experiment | deferred |
| GAP-011 | Ksoloti or Gills memory, CPU, controls, display, and device behavior | high for embedded work | Excluded; eight full voices are desktop-only here | Separate target proposal, resource measurement, compile/link, device, and listening evidence | deferred |
| GAP-012 | Distribution, assembled notices, dependency review, packaging, signing, and notarization | high for redistribution | Private local use only; provenance retained | Formal distribution review and distributable package evidence | open |
| GAP-013 | Canonical Schuss component, graph, instrument, provider, application runtime, shared library entry, and production status | high for production | Explicitly excluded; preserve frozen shared record-set authority | Accepted successor task/record allocation plus compatibility, native, reproduction, and release gates | open |
