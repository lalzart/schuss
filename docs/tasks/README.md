# Task contracts

<!-- schuss-governance-routing: active=none; next=033-phase-3@not-activated -->

Current scheduling authority is `../governance/current-state.json`. Task files
define frozen boundaries; their presence in this directory does not make them
active. Completed detail is indexed in `../HISTORY.md` and remains recoverable
from Git. A task contract may retain its proposal-time status when exact result
records bind the contract bytes; the index and result file carry later
activation and completion state.

## Active

There is no active task. Task 039 is complete locally and user-accepted. Task
033 Phase 3 remains only the next candidate.

## Next candidate, not activated

- Task 033 Phase 3 may begin only when the user explicitly activates it. Task
  033 Phase 2 is complete locally at `ccafc1d`; Phases 3 and 4 remain unstarted.

## Completed source, lab, and desktop follow-ups

- Task 036 completed the shared authenticated Mutable/Ksoloti physical source
  package and exact Tide Pit migration at `c6fad1f`. Its frozen contract retains
  proposal-time wording; `036-RESULTS.md`, `036-GAPS.md`, and the exact handoff
  record completion.
- Task 037 completed Instrument Lab v1 at `c6fad1f`, after the complete Task 036
  handoff. It extracted reusable non-production JUCE, MIDI, UI, renderer, build,
  and validation mechanics without allocating canonical graph/provider identity.
- Task 038 completed source/consumer reuse hardening at `74d87cf`, adding only
  the source-only record-set successor and reusable physical source/adapter
  closures.
- Task 039 completed the noncanonical desktop audition library and bounded local
  JUCE launch surface at `b9a742e`. The user later accepted it after operating
  the Launch Control and instruments; no formal real-time or listening evidence
  was promoted.

## Recent retained contracts

- Task 035 is complete and owns proportional validation profiles, one-pass
  record-set validation, and structured current-work governance.
- Task 034 is complete and owns the controller-independent performance graph
  contracts and exact Gills/MIDI configurations.
- Task 033 owns the source-neutral collection/provider architecture. Phase 1
  and Phase 2 are complete locally.
- Task 032 is the complete bounded variable-graph desktop-host successor over
  the seven existing native factory types.
- The Task 031 parent contract is retained at
  `../DESKTOP_HOST_RUNTIME_IMPLEMENTATION_CONTRACT.md`.

Older numbered and unnumbered task contracts may remain here while useful for
review. They are historical inputs, not a live queue, and no validator requires
an exact directory filename list. Task 012B is a retirement notice and must not
be reinterpreted as runnable work.

## Evidence and validation maintenance

VH-001 is retained under `../validation/`. It protects five historical
configured-source identities without changing local source configuration or
rebaselining goldens.

ADR 0018 and Task 035 define `current`, `compatibility`,
`configured-sources`, `native`, `reproduction`, and `release` validation
profiles. Expensive evidence belongs to its explicit profile and runs once when
the changed boundary requires it.

## Required contract shape

Every new implementation task must state:

- its goal and why it exists;
- in-scope and out-of-scope work;
- inputs and deliverables;
- acceptance tests;
- decisions it may make; and
- decisions it must not make.

Its validation section must identify focused, adjacent, configured/native or
reproduction work, and whether full compatibility/release validation is
actually required. Completing a task does not authorize the next task, Git
publication, source mutation, hardware action, or evidence promotion.
