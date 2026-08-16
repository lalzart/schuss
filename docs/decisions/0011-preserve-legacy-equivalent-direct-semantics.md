# ADR 0011: Preserve legacy-equivalent direct semantics

- Status: accepted
- Date: 2026-08-16
- Promotes: the accepted Task 016 direct-semantics decision

## Context

The complete eight-node Gills slice required explicit scheduling, state,
control, and native-operation behavior before the direct frontend could replace
the legacy Java/`.axp` path. Two legitimate choices existed: reproduce the
reviewed legacy behavior or define new Schuss-native musical semantics.

The user selected the legacy-equivalent route. Task 016 then authenticated the
retained source and runtime closure, specified the seven required operations,
lowered the exact graph without Java or `.axp`, and produced deterministic ARM
compile/link evidence through level 5.

## Decision

The accepted direct implementation of the Task 016 graph uses
legacy-equivalent semantics. Later work may reuse that exact behavior and its
evidence but may not silently substitute Schuss-native behavior.

A Schuss-native alternative requires a separate musical specification,
versioned semantic successors, explicit compatibility treatment, and its own
evidence. Direct lowering may never fall back invisibly to the Java bridge or
to a generated `.axp`.

Compile/link evidence remains level 5. Connected-device, real-time, and audible
levels 6-8 are independent and remain `not-run` until separately authorized and
performed.

## Consequences

Task 018 may reuse the accepted Task 016 graph as its executable mapped Gills
reference without reopening DSP semantics. New reference instruments that rely
on unsupported operations must continue to fail closed rather than borrowing
compatibility from this decision.
