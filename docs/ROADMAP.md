# Schuss roadmap

<!-- schuss-governance-routing: active=none; next=none -->

Current routing is defined by `docs/governance/current-state.json`; this roadmap
describes sequencing rather than silently activating work.

## Active maintenance

There is no active task. Task 040 Phase 1 completed as a planning-only
Cinderwheel readiness bundle at published commit `955084e`. Phase 2 was never
activated, and no canonical semantic, runtime, DSP, UI, device, or listening
implementation began.

## Next gate

There is no next candidate. Task 040 may return only through a fresh
live-parent, version, provider-route, and stable-ID allocation audit; its Phase
1 planning snapshot does not reserve identities or silently reactivate Phase 2.

## Likely later work

Later contracts may address these independent needs:

- execute the device-independent performance-control graph and define event,
  smoothing, conflict, takeover, and timing policies;
- present instrument and controller mappings in the desktop client through the
  same core operations used by CLI and AI clients;
- expand the native DSP palette through explicit component/binding/provider
  evidence rather than collection membership;
- investigate a separate desktop-float/JUCE provider only if its numeric,
  licensing, lifecycle, allocation, and real-time boundaries are accepted; and
- perform packaging, connected-device, listening, or distribution work only
  under their own evidence gates.

These are candidates, not promises or active tasks.

## Completed backbone

Tasks 001-035, including all four phases of Task 033, form the completed
canonical backbone. Completed noncanonical
source/lab work in Tasks 036-038 and the Task 039 desktop audition product slice
are also indexed in `HISTORY.md`, with their evidence limits retained. The
important durable choices remain in ADRs:

- ADRs 0005-0007 separate family, contract, binding, build, and evidence;
- ADRs 0010-0015 establish the accepted backend/application/catalog sequence;
- ADR 0016 adopts the portable desktop host runtime;
- ADR 0017 separates collections from providers; and
- ADR 0018 adopts proportional validation profiles.

Tasks 019, 020, and 040 remain deferred. Task 012B remains retired. Completion
of one task does not automatically activate any later candidate.
