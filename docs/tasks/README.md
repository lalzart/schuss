# Task contracts

<!-- schuss-governance-routing: active=039@review-ready; next=033-phase-3@not-activated -->

Current scheduling authority is `../governance/current-state.json`. Task files
define frozen boundaries; their presence in this directory does not make them
active. Completed detail is indexed in `../HISTORY.md` and remains recoverable
from Git.

## Active

- Task 039, desktop instrument library and bounded JUCE audition launch, is review-ready.
  Its contract is `039-desktop-instrument-library.md`; it owns the
  noncanonical audition manifest, exact list/start/inspect operations, closed
  desktop bridge additions, and Instruments-first presentation only.

## Next candidate, not activated

- Task 033 Phase 3 may begin only after Task 035 completes and the user
  explicitly activates it. Task 033 Phase 2 is complete locally at `ccafc1d`;
  Phases 3 and 4 remain unstarted.

## Documented sequential follow-ups, not activated

- Task 036 specifies an isolated shared authenticated Mutable source-package
  pilot with Tide Pit as its first exact consumer. Its documentation records
  the user's intent to implement it in a new chat, but it does not alter the
  current routing above, activate Task 033, or allocate product/provider
  semantics. Completion must emit the exact Instrument Lab handoff defined by
  the task.
- Task 037 specifies Instrument Lab v1: a two-prototype differential extraction
  of reusable JUCE, MIDI, control, UI, renderer, build, and validation mechanics
  plus a prototype-only DSP-topology artifact. It is hard-blocked on a complete
  Task 036 handoff. It allocates no canonical graph/provider identity and does
  not execute Task 034 performance-control graphs.

The required order is Task 036 followed by Task 037. Neither documentation
entry is an activation or a change to `docs/governance/current-state.json`.

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
