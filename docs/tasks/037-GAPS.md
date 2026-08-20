# Task 037 gaps and evidence limits

## Deliberately instrument-owned

- Cinderwheel and Tide Pit keep separate Cores, sample representations,
  processing APIs, state, reset and gesture semantics, numeric conversion,
  control maps, experiments, comparators, presentation identity, and DSP/source
  files.
- Tide Pit keeps its source overlay, Task 036 physical-package intake, exact
  Q27 oracle, 16-frame buffering policy, and semantic mapping.
- Cinderwheel keeps its float processing, raw-MIDI-as-Core-input contract,
  Wake ledger, render timeline, and musical state.
- Experiment signals, timelines, seeds, tolerances, interpretation, artifact
  counts, and final-state expectations remain consumer-owned.

## Deferred seams

- No shared snapshot mailbox was delivered. Tide Pit's existing instrument-local
  mailbox reset/restart seam remains unproved and explicitly deferred.
  Cinderwheel uses instrument-local atomic presentation values derived from the
  accepted Core snapshot; this is not generalized as a lab transport contract.
- JUCE message collectors, callbacks, audio-device restart, and GUI/audio-thread
  lifecycle have target-build evidence only. There is no measured deadline,
  allocation-free collector claim, or restart stress result.
- Physical Launch Control 3 behavior remains untested. The reused topology and
  simulated MIDI mappings do not prove Custom Mode state, feedback, cabling,
  merge/thru behavior, or hardware timing.
- No application was launched. No audio/MIDI device was opened. No listening,
  callback real-time, connected-device, distribution, signing, notarization,
  publication, or production evidence exists.

## Architecture limits

- Prototype topologies are noncanonical and nonexecutable. Promotion reports
  only list missing component contracts; they allocate no records.
- No Task 033/034 graph, performance-control, implementation/provider,
  runtime-factory, target/backend, catalog, operation, project, machine, or
  stable-ID work is implemented.
- A fused Core is not yet a graph-preserving production compound. Successor
  architecture must decide how inspectable internal roles bind to accepted
  component contracts and provider implementations.
- The lab is a repository-internal C++17 source surface, not a stable ABI,
  plugin SDK, dynamic loader, `juce_dsp` layer, or distribution package.
- Float and Q27/16-frame profiles still require explicit instrument adapters.
  Task 037 deliberately does not infer sample rates, block sizes, conversion,
  state, or event semantics.

## Context-reduction evidence

Three consumers link one CMake target and reuse the same bounded-event,
composition-profile, UI projection, renderer JSON/hash, JUCE authentication,
warning/sanitizer, generator, validator, topology, and handoff mechanics. The
two fresh-root and relocated-root test proves the scaffold removes copied shared
source from generated consumers. This is code and process reuse evidence only;
no token, model-cost, development-time, or future-instrument quality total is
claimed.

## Successor work

1. Propose and prove a restart-safe immutable latest-snapshot transport before
   sharing lifecycle code.
2. Run callback allocation/deadline and repeated device-restart evidence under
   an explicitly authorized host task.
3. Use promotion reports in a separately activated graph/component/provider
   architecture task; do not allocate from Task 037.
4. Review the bounded plugin follow-up packet before any external Sonic
   Research Lab update.
5. Validate the next separately approved musical instrument end to end before
   broadening the lab interface.
