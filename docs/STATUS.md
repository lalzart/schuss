# Schuss status

<!-- schuss-governance-routing: active=033-phase-4@review-ready; next=040@not-activated -->

The machine-readable current routing source is
`docs/governance/current-state.json`. This file explains that state in plain
language. Completed implementation detail belongs in `HISTORY.md`, accepted
architectural choices belong in ADRs, and exact semantic truth remains in the
schemas, records, record sets, fixtures, and evidence packets.

## Current work

Task 033 Phase 4 is the only active task and is review-ready from clean
published baseline `d7578e0`. Phase 3 passed its focused, adjacent native, and
copied-root reproduction gates with the accepted seven factory identities and
`runtime_v1.cpp` bytes unchanged. Phase 4 owns only the evidence-ranked next
tranche, the later-UI requirements, documentation integration, and final
cross-layer validation. It does not implement a new DSP algorithm, source
dependency, provider, public operation, UI behavior, device action, package,
or distribution action. Task 040 is the next contracted candidate and remains
not activated.

## Recent completed milestones

- Task 039 completed the five-entry noncanonical desktop audition library at
  `b9a742e`, with three exact verified local builds, one build-required entry,
  and one research-only entry.
- Task 038 completed reusable Mutable source/consumer hardening at `74d87cf`
  without allocating catalog, provider, graph, or runtime identity.
- Tasks 036 and 037 completed the authenticated Mutable/Ksoloti physical source
  package and non-production Instrument Lab at `c6fad1f`.
- Task 035 completed proportional validation and governance consolidation at
  `88788c5`, with all 33 final release checks passing.
- Task 034 completed the structural performance-control layer at `6010f29`.
  It separates controller bindings from instruments and DSP graphs but executes
  no controller graph and opens no physical MIDI/device path.
- Task 033 Phase 1 completed the collection/provider decision and source audits
  at `5dccfd2`.
- Task 033 Phase 2 completed locally at `ccafc1d`. It adds exact source-release,
  object-collection, implementation-provider, availability-policy, catalog,
  and read-only operation contracts in
  `schuss-record-set-000031@1`.

Task 033 Phase 3 was explicitly activated by the user on 2026-08-22 and passed
its completion gate in this worktree. Task 033 Phase 4 is now the serialized
review-ready phase; task numbers never override exact record-set ancestry or
the completion gate. Task 040 remains a proposed canonical Cinderwheel slice,
not an active implementation.

## Current product boundary

Schuss currently has:

- a function-first catalog with provenance and availability facets;
- one authoritative, client-neutral DSP graph model shared by CLI, desktop,
  and AI adapters;
- deterministic project/workspace authoring and build planning;
- the existing Ksoloti legacy backend and direct compiler path;
- a bounded JUCE-independent native desktop runtime for the seven accepted
  Task 031/032 factory types;
- deterministic offline rendering and a headless JUCE audio/MIDI session
  adapter;
- a noncanonical five-entry Instrument Lab audition library with bounded local
  JUCE process launch and an Instruments-first desktop surface;
- device-independent performance-control contracts and Gills/MIDI
  configurations; and
- source-neutral object collections and explicit implementation providers.

The seven native factory types remain a bounded proven runtime cohort, not a
permanent palette ceiling. The complete DSP graph remains accessible, and a
future instrument/controller layer must continue to reference public
instrument facets rather than DSP node IDs.

## Evidence boundary

After automated validation, the user operated the Launch Control and instruments
and reported that they were working fairly well. That closes product acceptance
for Task 039, but it is not a structured connected-device, callback-deadline,
resource, or listening evidence packet. Codex did not open the application,
audio/MIDI endpoints, USB, or hardware during implementation or this closeout.

Current work has not promoted:

- firmware or SD-card mutation;
- general real-time level 7;
- audible level 8;
- packaging, distribution, or publication.

Task 022's retained failed control-panel diagnostic remains historical evidence
and does not become a passing device claim. No structural, host-model, native,
connected-device, real-time, or audible level implies another.

## Validation

ADR 0018 separates validation into `current`, `compatibility`,
`configured-sources`, `native`, `reproduction`, and `release` profiles. The
ordinary current gate must be green without accidentally running compilers,
long renders, copied roots, or configured-source work. Explicit configured
validation still fails closed when `catalog/sources.local.yml` is absent.

Task 035's frozen release profile passed 33 of 33 unique checks in 669.321
seconds. The routine current portion took 17.842 seconds; the 485-test
compatibility sweep ran once in 430.498 seconds. All native, sanitizer, and
applicable reproduction checks passed. Configured historical Tasks 018, 021,
and 027 also passed explicitly using the existing external authenticated
mapping, while this worktree remained correctly unconfigured.

VH-001 remains the historical audit for the five machine-configured source
golden/hash gates. Its retained identities are not rebaselined and an absent
mapping is never reported as passed.

## Deferred and external gates

Tasks 019 and 020 remain deferred. Task 012B remains retired by ADR 0010. Any
further UI, MIDI execution, controller mapping runtime, new DSP palette tranche,
JUCE DSP provider, structured connected-device evidence, packaging, or
distribution work requires a separate explicit contract and activation.

Local completion and publication are separate. The clean baseline through
Task 039 is published at `d7578e0`; current Task 033 Phase 3/4 work is not yet
committed or pushed.
