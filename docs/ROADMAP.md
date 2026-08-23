# Schuss roadmap

<!-- schuss-governance-routing: active=040-phase-1@review-ready; next=none -->

Current routing is defined by `docs/governance/current-state.json`; this roadmap
describes sequencing rather than silently activating work.

## Active maintenance

Task 040 Phase 1 is the only active task and is review-ready. The exact parent,
stable-ID, schema, operation, provider, numeric, graph/fusion, experiment, and
validation allocations are frozen. The ready bundle adds no canonical record,
DSP implementation, provider factory, application launch, device action, or
higher evidence.

## Next gate

Task 040 Phase 2 is not activated. It may begin only after user review of the
Phase 1 bundle and exact allocation. The later serialized phases remain bounded
to canonical model, device-independent performance execution, and deterministic
native host-signal evidence; no DSP algorithm, source dependency, provider,
runtime, UI, device, real-time, listening, packaging, or release work starts
from Phase 1 readiness alone.

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

Tasks 019 and 020 remain deferred. Task 012B remains retired. Completion of Task
033 did not automatically activate Task 040 or any later candidate.
