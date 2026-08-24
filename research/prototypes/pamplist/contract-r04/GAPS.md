# Pamplist 0.4 seven-voice cohesion-bus gap register

> Status: source, host structural, host signal, authenticated standalone,
> relocated, and routine workspace evidence passed; live and subjective levels
> remain explicitly deferred

Passing a lower evidence level never closes a higher one. Revision 0.2 and
revision 0.3 contracts/evidence remain historical authority only for their own
designs; neither proves revision 0.4.

| ID | Gap | Severity | Current decision | Proof required | Disposition |
|---|---|---|---|---|---|
| GAP-001 | Exact proposal fingerprint and complete revision 0.4 approval bundle | blocker before source edit | Bound the current-thread approval and all frozen artifacts before DSP changes | Sonic Research Lab structure and ready validation | closed |
| GAP-002 | Seven-record/source cardinality with no hidden eighth voice or event bit | blocker before host evidence | Removed voice/lane 8 and reserved page index 7 only for Global/Clear | Compile-time cardinality assertions, snapshots, focused state/source tests, and complete diff review | closed |
| GAP-003 | Contextual lane-versus-Global mapping and CC47 edge behavior | blocker before controller claim | Preserved lane transforms on pages 0-6; mapped Global controls only on page 7; first Global edge selects and later edge clears once | Exhaustive CC/page/value comparison plus duplicate-positive/release traces and non-target equality | closed for synthetic protocol; physical evidence remains GAP-011 |
| GAP-004 | Shared six-mode modal bus remains finite and bounded at parameter extremes | blocker before host-signal evidence | Implemented pole guards, pole-distance excitation, weight normalization, smoothing, recovery, and final clamp | Coefficient/unit tests, sanitizer run, automation sweep, pole/state/final metrics | closed for retained host signal |
| GAP-005 | Cohere zero is an exact dry escape and Drive cannot leak | blocker before transparent-bypass claim | Selected the inherited signed-64-bit dry conversion exactly after Cohere snaps to zero | Byte-exact dry-reference test and retained dry condition with Drive at maximum | closed |
| GAP-006 | Clear removes only effect history | blocker before performance-control claim | One accepted generation change zeros modes/envelope before the next quantum sample | Tail-before-clear, exact-zero-after-clear, no-clear reference equality for all lane/source/scheduler state | closed for synthetic host behavior |
| GAP-007 | Deterministic objective revision 0.4 behavior and relocated reproduction | blocker before host-signal promotion | Froze eight conditions and retained canonical evidence after source/tests stabilized | Exact six-partition hashes, comparator divergence, exact silence, all-model regression, fresh-root replay | closed |
| GAP-008 | Authenticated standalone target and accepted-state presentation | blocker before target-build | Built and hashed Pamplist.app against authenticated JUCE 8.0.15 without launch | JUCE authentication, configure, compile, link, executable identity/hash receipt, and source-level UI assertions | closed for authenticated build; launch remains GAP-009 |
| GAP-009 | Live callback deadline, lifecycle, CPU headroom, and xruns with seven voices plus effect | high for real-time promotion | Deferred; no app/audio-device launch is authorized | 48 kHz live run with declared blocks/load, lifecycle, xruns, worst-case, and p99 measurements | open |
| GAP-010 | Concurrent processing of more than one Pamplist Core | high if a future host requires it | Not claimed; one Core owns the single audio-thread source boundary because dependency RNG is static | Thread-safe upstream boundary or external serialization plus race/concurrency tests | deferred |
| GAP-011 | Physical regular Launch Control 3 endpoint, installed Custom Mode, receipt, gesture feel, feedback, and reconnect | high for connected-device claim | Synthetic protocol only; button 8 concept remains untried on hardware | Exact endpoint observation, CC20-47 receipt, edge/encoder feel, accepted-state behavior, disconnect/reconnect | open |
| GAP-012 | Voice clarity, common-body cohesion, masking, control ranges, transitions, Duck, and Clear discoverability | medium | Objective activity is not musical usefulness | Documented dry/low/high Cohere, sweep, Duck, tail, and Clear audition | open |
| GAP-013 | Additional effects, per-lane sends, pan, mute/solo, presets/scenes, external clock, reverb, and freeze | enhancement | Excluded to keep one causal shared-body hypothesis | New approved design, state model, and experiment | deferred |
| GAP-014 | Ksoloti/Gills memory, CPU, control/display, and device behavior | high for embedded work | Excluded; this is a desktop Instrument Lab slice | Separate target proposal, resource measurement, compile/link, device, and listening evidence | deferred |
| GAP-015 | Distribution, assembled notices, packaging, signing, notarization, canonical Schuss identities/graphs/providers/runtime, and production status | high outside private prototype | Explicitly excluded; preserve source provenance and frozen platform authority | Separate distribution review and accepted production-integration task with compatibility/native/reproduction/release gates | open |
