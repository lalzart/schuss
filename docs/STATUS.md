# Schuss status

<!-- schuss-governance-routing: active=035@review-ready; next=033-phase-3@not-activated -->

The machine-readable current routing source is
`docs/governance/current-state.json`. This file explains that state in plain
language. Completed implementation detail belongs in `HISTORY.md`, accepted
architectural choices belong in ADRs, and exact semantic truth remains in the
schemas, records, record sets, fixtures, and evidence packets.

## Current work

Task 035 is the only active task and is review-ready. It is a maintenance task
consolidating validation and governance; it allocates no product schema,
record, stable ID, operation, DSP behavior, compiler behavior, runtime ABI, UI
behavior, or evidence promotion.

Its baseline is local commit
`ccafc1d403513c822d9294b6c257906820ff88eb`. Work is occurring in the isolated
`codex/task035-validation-consolidation` worktree. No Task 035 staging, commit,
push, publication, package installation, hardware action, or audio/MIDI device
action is implied by this status.

## Recent completed milestones

- Task 034 completed the structural performance-control layer at `6010f29`.
  It separates controller bindings from instruments and DSP graphs but executes
  no controller graph and opens no physical MIDI/device path.
- Task 033 Phase 1 completed the collection/provider decision and source audits
  at `5dccfd2`.
- Task 033 Phase 2 completed locally at `ccafc1d`. It adds exact source-release,
  object-collection, implementation-provider, availability-policy, catalog,
  and read-only operation contracts in
  `schuss-record-set-000031@1`.

Task 033 Phases 3 and 4 have not started. Task 033 Phase 3 is the next candidate
after Task 035, but it is not activated. Task numbers never override exact
record-set ancestry or explicit user activation.

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
- device-independent performance-control contracts and Gills/MIDI
  configurations; and
- source-neutral object collections and explicit implementation providers.

The seven native factory types remain a bounded proven runtime cohort, not a
permanent palette ceiling. The complete DSP graph remains accessible, and a
future instrument/controller layer must continue to reference public
instrument facets rather than DSP node IDs.

## Evidence boundary

Current work has not promoted:

- physical hardware execution for Task 035;
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

Tasks 019 and 020 remain deferred. Task 012B remains retired by ADR 0010. A UI,
MIDI execution, controller mapping runtime, new DSP palette tranche, JUCE DSP
provider, connected-device action, packaging, or distribution task requires a
separate explicit contract and activation.

Local completion and publication are separate. Consult Git directly before
claiming that any local commit is present on `origin/main`.
