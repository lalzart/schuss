# Repeatable source-to-JUCE instrument workflow

This second instrument turns the Cinderwheel trial into a reusable process.
Cinderwheel began with a sonic proposal and original prototype DSP; Tide Pit
begins with an existing favorite implementation and must preserve it. Those
are different lanes, but they now share the same contract, controller, host,
and evidence shape.

## What changed before this build

The Sonic Research Lab plugin was extended from version 0.2 to 0.3 with a
`source-reimplementation` lane. Its readiness gate now requires an immutable
source authority, per-file and dependency fingerprints, license disposition,
a fidelity matrix, numeric/platform assumptions, explicit random and storage
ownership, an oracle, and a machine-readable implementation bundle. User
authorization may waive the proposal pause; it cannot waive readiness.

The implementation bundle was also generalized:

- `implementation-contract.json` defines scope, decision rights, deliverables,
  acceptance, evidence level, and deferred claims.
- `source-equivalence.json` separates exact preservation, allowed seams,
  exclusions, intentional deviations, and the comparator.
- `experiment.json` owns render conditions, events, seeds, output expectations,
  and tolerances instead of hiding them in renderer code.
- `control-map.json` owns labels, defaults, physical selectors, transforms,
  gestures, invalid-input policy, and application feedback. C++ descriptors are
  generated from it and checked for freshness.
- `state-matrix.md`, `RESULTS.md`, and `GAPS.md` keep state semantics, retained
  evidence, and unresolved claims reviewable.

The regular Launch Control 3 topology is now a separate fingerprinted surface
artifact. An instrument replaces only semantic bindings and labels. This
prevents each build from rediscovering channel, CC, message, and physical-layout
facts while avoiding a false claim that the prototype map is a production
Schuss performance graph.

## Generic execution sequence

1. **Identify the lane and artifact.** Decide whether the job is a new sonic
   design or an existing-source reimplementation, and define whether “working”
   means a Core, renderer, standalone app, plugin, device session, or release.
2. **Freeze authority before porting.** Record source revisions, dirty-state
   scope, normative files, hashes, licenses, minimal dependency closure, and
   forbidden mutations.
3. **Recover a lawful oracle.** Fix initialization, random state, compiler/FP
   profile, buffer layout, and output encoding. An old hash is evidence only if
   those preconditions are reproducible.
4. **Write machine-readable behavior.** Freeze controls, defaults versus audition
   presets, gestures, state transitions, experiment timelines, tolerances, and
   evidence boundaries before DSP changes.
5. **Port through narrow seams.** Keep the musical Core free of JUCE. Adapt only
   allocation, platform I/O, event delivery, state snapshots, and numeric
   conversion. Preserve upstream bytes when an overlay can expose the needed
   state without changing behavior.
6. **Generate repeated glue.** Generate control descriptors from the mapping;
   do not maintain JSON and C++ copies by hand. Keep the MIDI adapter bounded
   and compare adapted input with direct semantic input.
7. **Validate from cheap to expensive.** Run fixture freshness and focused Core
   tests, then sanitizers, golden equality, partition invariance, JUCE adapter
   parity, deterministic render repetition, full native build, and the scoped
   workspace profile once after freeze.
8. **Promote evidence one rung at a time.** Source, host structural, host signal,
   native build, launch, real-time, connected device, listening, packaging, and
   production integration are independent results.
9. **Backfill and compare.** Record exact commands, hashes, metrics, failures,
   corrections, and open gaps. Only extract a shared library after at least two
   implementations show that the seam is genuinely stable.

## Lessons from Tide Pit

The most important improvement is that fidelity now includes runtime context,
not just source text. The earlier historical reference hash could not serve as
an oracle because automatic storage left two Clouds reverb histories
uninitialized. Reconstructing Ksoloti's zero-initialized global-storage
semantics produced a stable reference. The exact RNG stream, five arena
allocations, 48 kHz/16-frame schedule, Q27 layout, and floating-point
contraction profile are equally part of the comparator.

Sanitizer output is evidence, not merely an exit code. The first recovery-mode
run printed an upstream signed-shift error while CTest still reported success.
The frozen workflow now runs UBSan with `halt_on_error=1`. Tide Pit keeps the
authoritative bytes untouched and generates a two-expression defined-C++
overlay whose range, output hash, canonical audio hash, and clean sanitizer run
are all bound together.

The UI also has a clearer authority rule. Cinderwheel initially reflected raw
MIDI for convenience. Tide Pit has contextual soft pickup, so raw input can
differ from the active DSP value. The reusable rule is now: raw MIDI belongs in
diagnostics; interactive controls display the accepted Core snapshot.

## What should remain un-generalized for now

The Core API, gesture synthesizer, source-state overlay, Q27 buffering,
compiled Mutable target, and runtime policy are Tide Pit-specific. The
exact raw 21-file Mutable closure is now a shared physical build input, not a
general provider or catalog entry. Cinderwheel uses native float
DSP and different state semantics. Copying those into a broad framework now
would encode the second example as policy. The stable candidates for later
extraction are narrower: pinned-JUCE configuration, fixed-capacity MIDI intake,
audio-device lifecycle, state-mailbox mechanics, renderer artifact writing,
and descriptor-driven UI layout. A two-prototype differential audit should be
the gate for that extraction.
