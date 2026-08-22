# Schuss status

<!-- schuss-governance-routing: active=none; next=040@not-activated -->

The machine-readable current routing source is
`docs/governance/current-state.json`. This file explains that state in plain
language. Completed implementation detail belongs in `HISTORY.md`, accepted
architectural choices belong in ADRs, and exact semantic truth remains in the
schemas, records, record sets, fixtures, and evidence packets.

## Current work

There is no active task. Task 033 Phases 3 and 4 completed at published commit
`0bf22b6`: the seven-entry native registry has one generated identity authority,
the Task 031/032 runtime bytes remain exact, and the follow-up packets select
one bounded next tranche without implementing it. Task 040 remains the next
contracted candidate and is not activated.

## Recent completed milestones

- Task 033 Phases 3 and 4 completed at published commit `0bf22b6`, preserving
  provider `schuss-implementation-provider-000001@1`, record set
  `schuss-record-set-000031@1`, and the exact seven native factories while
  closing the generated-registry and follow-up handoffs.
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

Task 033 is complete through Phase 4. Task numbers never override exact
record-set ancestry or the completion gate. Task 040 remains a proposed
canonical Cinderwheel slice, not an active implementation.

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

Local completion and publication are separate. Task 033's implementation and
evidence result is published at `0bf22b6`. Task 040 is not activated by that
publication.
