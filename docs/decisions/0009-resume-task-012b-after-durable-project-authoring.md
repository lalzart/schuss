# ADR 0009: Resume Task 012B after durable project authoring

- Status: superseded by ADR 0010
- Date: 2026-08-15
- Supersedes: ADR 0008's UI-readiness gate

ADR 0010 records that this decision resulted from a task-label
misinterpretation. Task 012B is retired, ADR 0008's backend-first direction is
reaffirmed, and this document has no current scheduling force.

## Context

ADR 0008 split the original Phase 12 because Schuss did not yet have a durable
project, persistent graph editing, or a proven client-neutral save boundary.
It then coupled resuming the UI to the entire later compiler sequence: shared
build execution, a normalized DSP representation, direct frontend coverage,
and reviewed-core expansion.

Task 012A has now completed the dependency that actually matters to the first
editor client. Schuss has a portable exact project, immutable graph/project
revisions, atomic prior-or-successor persistence, recovery, and shared project
operations. Task 011A already supplies shared catalog search and inspection;
Tasks 008 and 012A supply graph inspection, validation, transactions, and
persistent commit behavior.

Compiler planning and build execution remain valuable, but the basic object
drawer and graph canvas neither need to execute a build nor need a direct
frontend. Treating those later capabilities as UI prerequisites delays
validation of the shared client model and recreates a CLI-only product bias.

## Decision

Remove the headless-backbone readiness gate for Task 012B. Task 012B becomes
the immediate task after completed Task 012A and before the planned Task 013
compiler sequence.

Task 012B is the first bounded GUI client slice. It owns:

- an object drawer over accepted `catalog.search` and `catalog.inspect`;
- a transparent graph canvas over accepted graph inspection and transaction
  results;
- explicit opening, validation, editing, saving, and reopening of a Task 012A
  project; and
- presentation-only layout and interaction state that never becomes DSP graph
  identity.

The UI remains a client. It may not define alternate catalog classification,
graph validation, project persistence, binding resolution, build execution,
compiler behavior, or device semantics. Capabilities that do not yet exist in
the shared operation layer must be shown as unavailable or left absent rather
than implemented privately in the GUI.

Tasks 013A-013D and B6 remain planned and retain their compiler, build, direct-
frontend, and reviewed-core scopes. Their absence is no longer a blocker for
the bounded Task 012B editor.

## Consequences

Schuss can test its central product idea earlier: one immediate drawer and a
complete inspectable graph using the same semantics as CLI and future AI
clients. UI work can expose missing shared capabilities, but any such gap must
return to its owning operation or later task rather than being patched into
client state.

ADR 0008 remains in the decision log as the historical reason Task 012A was
split from the original UI work. Its requirement to wait for Tasks 013A-013D
and B6 is superseded and has no current gating force. Historical completed-task
reports that describe Task 012B as deferred are not active scheduling rules.
