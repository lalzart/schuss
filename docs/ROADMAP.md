# Schuss roadmap

<!-- schuss-governance-routing: active=none; next=none -->

Current routing is defined by `docs/governance/current-state.json`; this roadmap
describes sequencing rather than silently activating work.

## Active maintenance

There is no active task.

Task 048 is complete but uncommitted. Its noncanonical Wanderbody 0.1
standalone passed portable Core/state/allocation and sanitizer checks, the
frozen ten-condition/seven-partition objective matrix, Instrument Lab and
relocated reproduction, and an authenticated unlaunched JUCE arm64 target
build. App launch, endpoints, real-time, physical devices, listening,
distribution, canonical promotion, and production remain separate future
work.

Task 047 is complete but uncommitted. Its narrow shared fixed-internal-rate
converter lets the private Tide Pit and Pamplist arm64 VST3 adapters accept
32, 44.1, 48, 88.2, 96, 176.4, and 192 kHz while preserving exact 48 kHz
bypass. Focused signal/timeline, allocation, module-host, authenticated
target-build, and relocated reproduction gates passed. Installation, Ableton
launch, endpoints, real-time, listening, distribution, canonical
provider/runtime work, and production remain separate future work. Schuss
`current` passed; the one compatibility run retained an unrelated inherited
Task 043 stale five-versus-six library-count assertion.

Task 046 is complete but uncommitted. Its bounded local Tide Pit arm64 VST3
adapter passed stable parameter/state, exact direct signal, module-host,
authenticated target-build, and relocated reproduction gates. Installation,
Ableton launch, endpoints, real-time, listening, distribution, canonical
provider/runtime work, and production remain separate future work.

Task 045 is complete but uncommitted. Its bounded local Pamplist 0.6 arm64 VST3
adapter passed stable parameter/state, direct signal, module-host, authenticated
target-build, and relocated reproduction gates. Installation, Ableton launch,
endpoints, real-time, listening, distribution, canonical provider/runtime work,
and production remain separate future work.

Task 044 is complete but uncommitted. Layerwell now uses exactly Tide Pit and
Pamplist, embeds the selected source's complete accepted-state control
presentation inside one host, retains three synchronized source-only layers,
and adds non-destructive shared loop start/end trim. Higher app-launch, visual,
real-time, device, listening, distribution, publication, and production gates
remain separate future work.

## Next gate

There is no next candidate. Task 041 stopped after its bounded dependency
hardening and evidence report. Task 040 may return only through a fresh
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
canonical backbone. Completed source, lab, desktop, selective-reuse,
meta-instrument, private VST3, and standalone prototype work in Tasks 036-048 is also indexed in
`HISTORY.md`, with its evidence limits retained. The important durable choices
remain in ADRs:

- ADRs 0005-0007 separate family, contract, binding, build, and evidence;
- ADRs 0010-0015 establish the accepted backend/application/catalog sequence;
- ADR 0016 adopts the portable desktop host runtime;
- ADR 0017 separates collections from providers; and
- ADR 0018 adopts proportional validation profiles.

Tasks 019, 020, and 040 remain deferred. Task 012B remains retired. Completion
of one task does not automatically activate any later candidate.
