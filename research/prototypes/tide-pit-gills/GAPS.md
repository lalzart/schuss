# Tide Pit Gills portable JUCE port gap register

> Status: reviewed after host validation on 2026-08-20

## Closed during this trial

| ID | Former gap | Closing evidence |
|---|---|---|
| CLOSED-001 | No permanent source comparator | Apple clang 16 reference test matches 1,536,000-byte Q27 SHA-256 `39d8...ad2b` |
| CLOSED-002 | Source and Mutable closure not authenticated | external and vendored source-lock validation passes; notices retained |
| CLOSED-003 | Global stmlib RNG ownership unsuitable for instances | compatible per-instance save/restore preserves the canonical stream and passes interleaved/concurrent-instance tests |
| CLOSED-004 | Source state not observable to the host | behavior-neutral overlay plus complete snapshots preserve the golden and pass state/display tests |
| CLOSED-005 | Upstream negative signed shift triggered UBSan | exact two-expression defined-C++ generated overlay; output hash locked; fail-fast ASan/UBSan clean; golden unchanged |
| CLOSED-006 | Mapping and startup state could drift between JSON, Core, and UI | generated descriptors, compile-time default checks, runtime snapshot check, and exhaustive map tests pass |
| CLOSED-007 | JUCE MIDI and arbitrary host block sizes could alter behavior | fixed-capacity adapter and Q27 bridge pass raw-byte, ordering, drop, lifecycle, allocation, audio, diagnostic, and snapshot parity tests |
| CLOSED-008 | Offline evidence did not cover partitions and state | exact artifacts and complete final snapshots match at 16/64/128/512 frames and on a fresh repeat |
| CLOSED-009 | Research workflow only handled new sonic ideas | Sonic Research Lab 0.3 adds a validated source-reimplementation lane and machine-readable equivalence bundle |

## Accepted and deferred gaps

| ID | Gap | Severity | Owner/stage | Current decision | Proof required |
|---|---|---|---|---|---|
| GAP-001 | No canonical continuous physical-pot startup preset exists | medium | host UX | Keep the JSON-owned desktop audition preset explicitly labelled noncanonical | future Gills capture or product preset decision |
| GAP-002 | The source is deeply fixed to 48 kHz and 16-frame quanta | high | audio host | Reject any other device rate; do not infer a resampler | separate resampling design plus reference comparison |
| GAP-003 | Fixed-arena exhaustion is fail-closed by contract but not failure-injected | medium | Core safety | Exact source and arena size make the path unreachable in the frozen build; retain the limitation | bounded test seam that forces partial allocation and proves silent prepare failure |
| GAP-004 | Exact byte identity is platform-specific | medium | portability | Apple clang 16 is the bit-exact oracle; other toolchains get structural and signal evidence only | independently frozen compiler/FP profiles and tolerances |
| GAP-005 | Tide Pit has not been exercised with the physical Launch Control 3 | medium | connected device | Reuse the user-confirmed Cinderwheel topology without claiming Tide Pit device proof | authorized session covering every control, pickup, long holds, invalid CCs, and reconnect |
| GAP-006 | Callback deadlines and audio-device lifecycle are unproved | high | real-time | Make no real-time claim | worst-case and p99 timing under load, device stop/start/reconfigure, and drop/underrun evidence |
| GAP-007 | UI mailbox reset can race a live consumer during device restart | high | host lifecycle | App startup is bounded, but restart safety remains part of deferred lifecycle work | generation or handshake design plus restart stress test |
| GAP-008 | JUCE `MidiMessageCollector` may lock or allocate outside the fixed adapter | high | real-time host | Bounded adapter begins after collection; make no whole-callback allocation/lock claim | instrumented collector/callback measurement or a proven bounded intake replacement |
| GAP-009 | HostBridge requires nondecreasing event sample offsets | medium | adapter API | Precondition is documented and JUCE `MidiBuffer` satisfies it; general unordered callers are unsupported | enforce/sort bounded input or add a checked failure contract |
| GAP-010 | Audible equivalence to the favorite Gills instrument is unproved | high | listening | Hand off the app after objective validation without making a listening claim | user A/B against remembered, recorded, or device reference |
| GAP-011 | Exact source has substantial raw DC mean | medium | DSP/product | Preserve and report it for fidelity; do not silently high-pass | separate intentional variant, listening test, and new oracle if DC removal is desired |
| GAP-012 | Generic local-JUCE source mode checks version, not tree bytes | medium | dependency intake | This build was separately authenticated against the retained exact archive | reusable source-tree fingerprint/authentication step |
| GAP-013 | Prototype links JUCE modules beyond the canonical Schuss device lock | medium | dependency/packaging | Permit only for this local renderer/GUI trial | module/license review before distribution or shared-host extraction |
| GAP-014 | JUCE distribution, signing, and plugin formats are not approved | medium | packaging | Local unsigned standalone only | distribution license review, signing/notarization, and explicit AU/VST3 task |
| GAP-015 | The application UI has not been launched or visually exercised | medium | host launch | Compile/link evidence only | authorized launch, audio/MIDI selection, resize/display, and shutdown test |
| GAP-016 | No permanent shared C++/JUCE support library exists | medium | workflow | Reuse fingerprinted topology and patterns; defer code extraction until seams stabilize across both prototypes | two-instrument differential audit and adjacent regressions |
| GAP-017 | Canonical Schuss graph/provider/control-runtime integration is outside this task | high | production | Keep the prototype isolated | accepted successor task, identities, records, runtime, packaging, and release gates |

The legacy `9e47...ab00` stream remains provenance evidence only. It is not an
open comparator: its automatic-storage Clouds reverb history was undefined.
