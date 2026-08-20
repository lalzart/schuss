# Schuss roadmap

<!-- schuss-governance-routing: active=035@review-ready; next=033-phase-3@not-activated -->

Current routing is defined by `docs/governance/current-state.json`; this roadmap
describes sequencing rather than silently activating work.

## Active maintenance

Task 035 is review-ready and consolidates validation and governance under ADR
0018. It makes cumulative record-set loading one-pass, separates routine checks
from native and copied-root reproduction, restores a useful green ordinary
gate, and moves current task/phase state into a small structured source.

Its focused loader/runner negatives, exact adjacent service regression, and
one deduplicated frozen release run are complete. The release passed all 33
unique checks; the routine current portion took 17.842 seconds. Task 035
changes no configured-source semantic input, so the absent authenticated local
mapping remains an explicit not-applicable prerequisite rather than a release
failure or a fabricated pass.

## Next candidate

Task 033 Phase 3 is the next candidate, not an active task. It may replace the
three hand-maintained Python/C++/schema factory tables with one reviewed
generated native registry while preserving the exact seven factories and all
Task 031/032 package/runtime behavior.

Task 033 Phase 4 remains after Phase 3. It owns final cross-layer integration,
follow-up packets, and any full Task 033 integration validation. Neither phase
adds a DSP algorithm, source dependency, JUCE provider, UI, hardware claim, or
audible claim without a separately accepted allocation.

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

Tasks 001-034, with the documented deferrals and failed evidence boundaries,
are indexed in `HISTORY.md`. The important durable choices remain in ADRs:

- ADRs 0005-0007 separate family, contract, binding, build, and evidence;
- ADRs 0010-0015 establish the accepted backend/application/catalog sequence;
- ADR 0016 adopts the portable desktop host runtime;
- ADR 0017 separates collections from providers; and
- ADR 0018 adopts proportional validation profiles.

Tasks 019 and 020 remain deferred. Task 012B remains retired. Completing Task
035 will not automatically activate Task 033 Phase 3 or any later candidate.
