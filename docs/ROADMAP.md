# Schuss roadmap

<!-- schuss-governance-routing: active=039@review-ready; next=033-phase-3@not-activated -->

Current routing is defined by `docs/governance/current-state.json`; this roadmap
describes sequencing rather than silently activating work.

## Active maintenance

- Task 039, the desktop instrument library and bounded JUCE audition-launch
  slice, is review-ready. It changes the desktop entry surface and adds only
  manifest-bound fake-tested launch sessions; validation launched no app and
  promoted no prototype, device, listening, or production evidence.

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

Tasks 001-035, with the documented deferrals and failed evidence boundaries,
are indexed in `HISTORY.md`. The important durable choices remain in ADRs:

- ADRs 0005-0007 separate family, contract, binding, build, and evidence;
- ADRs 0010-0015 establish the accepted backend/application/catalog sequence;
- ADR 0016 adopts the portable desktop host runtime;
- ADR 0017 separates collections from providers; and
- ADR 0018 adopts proportional validation profiles.

Tasks 019 and 020 remain deferred. Task 012B remains retired. Completing Task
035 will not automatically activate Task 033 Phase 3 or any later candidate.
