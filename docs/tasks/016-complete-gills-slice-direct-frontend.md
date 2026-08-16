# Task 016: Complete Task 011C graph direct frontend

Status: complete on 2026-08-16; accepted locally through evidence level 5 for
the exact Task 011C eight-node graph. Evidence levels 6-8 remain not run.

## Goal and why it exists

Expand the Task 015 normalized-DSP/direct-C++ path from the one-node Blend
graph to all eight nodes and nine connections of `schuss-graph-000002@1`, then
compile/link the result without Java or `.axp`. This is the bridge from a
minimal compiler primitive to the first musically meaningful direct graph.

## In scope

- Reuse the Task 013 front half, Task 014 execution boundary, and Task 015 IR,
  arithmetic, source-map, and code-generation rules.
- Exact normalized operations and direct realization specifications for Square
  LFO, Cyclic Counter, four-step Pitch Sequencer, Sine Oscillator, Crossfader,
  State-variable Filter, and stereo Audio Output.
- Explicit control/audio schedules, state initialization/lifecycle, rising-edge
  history, control-to-audio latching, fanout, public parameter smoothing, and
  two-use reuse of one Sine realization.
- Deterministic direct C++, exact direct handler/backend/binding eligibility,
  Task 014 product execution, and authenticated ARM compile/link evidence.
- Golden semantic vectors for every operation and graph-level schedule/state
  transition before any compatibility promotion.

## Required prerequisite specifications

The current accepted contracts do not determine these implementation facts:

1. semitone-to-phase-increment conversion, reference pitch, sample/control
   rate, precision, rounding, and overflow for Square LFO and Sine Oscillator;
2. Square LFO duty/phase convention and reset output timing;
3. Sine waveform algorithm/table, interpolation, phase representation, and
   wrap behavior;
4. SVF topology, coefficient mapping, integration/update order, state width,
   saturation, resonance policy, and reset/initial state;
5. exact audio-block/control-cycle order and whether counter/sequencer changes
   affect the current or next audio block;
6. Ksoloti direct runtime entry points, buffer sizes, audio I/O symbols,
   initialization/disposal ABI, linker boundary, and firmware compatibility;
7. whether direct behavior must be bit-identical to the retained legacy
   implementation or may define a new Schuss-native sound with separate
   compatibility claims; and
8. source/license authority for any reused algorithm or table.

These are musical DSP and runtime-contract decisions, not compiler mechanics.
They must be supplied by a reviewed direct-implementation specification or a
separately authorized clean-room characterization task.

## Evidence audit and accepted decision

The read-only pinned-source audit in
`docs/tasks/016-direct-semantics-decision-brief.md` shows that all eight items
have an authenticated conditional specification if the direct frontend is
required to preserve the exact Task 011C integer behavior and existing Ksoloti
runtime ABI. It does not select that behavior automatically.

The user explicitly selected **legacy-equivalent direct semantics** on
2026-08-16. Task 016 therefore preserves the authenticated Task 011C integer
DSP behavior and runtime ABI. It does not define a Schuss-native alternative
sound.

## Out of scope

- Inferring the missing facts from display names, copying legacy source without
  license/semantic review, silently treating opaque legacy calls as direct IR,
  weakening compatibility, UI, device execution, listening, firmware change,
  commit, or push.

## Inputs and deliverables

Inputs are Tasks 011B-015, the eight-node graph, and the accepted
legacy-equivalent direct implementation/runtime specs. Delivered outputs are
seven versioned operation specs, candidate and promoted direct bindings, one
direct backend, seven exact eligibility records, the expanded IR/frontend,
registered exact handler, deterministic source/ARM artifacts, semantic
goldens, tests, validator, retained evidence, and completion report.

## Acceptance tests

1. All earlier bytes/tests pass and the exact Task 015 Blend output remains
   unchanged.
2. Every node/facet/connection has one explicit supported lowering and source
   origin; missing facts fail `unsupported` before generation.
3. Schedule/state/control-latch rules are explicit and pass operation and
   graph transition vectors.
4. No Java, `.axp`, legacy object call, implicit adapter, or ambient discovery
   occurs in the direct path.
5. Two fresh roots produce byte-identical IR, C++, object, ELF, map, command,
   and portable operation results.
6. Task 014 CLI execution uses one exact direct handler and never falls back to
   the transitional handler.
7. Evidence levels 1-5 are separate; levels 6-8 remain not-run without new
   authorization.
8. Full tests, validators, schema checks, and `git diff --check` pass.

## Decisions Task 016 may make

- IR scheduling/state layout and derived identities after the prerequisite DSP
  and runtime semantics are accepted; direct handler/backend record layout;
  deterministic code structure; and exact diagnostics.

## Decisions Task 016 must not make

- The eight missing musical/runtime/license specifications above, a hidden
  compatibility-mode choice, a hidden legacy fallback, new compatibility truth
  without evidence, firmware/device behavior, UI, commit, or push.

## Completion report

The accepted decision removes the former stop condition. Exact direct request
`schuss-build-request-000002@3` resolves all eight nodes to native bindings;
the two Sine nodes reuse one binding identity with independent state. The
frontend emits nine ordered operations, explicit state/latches, and origins
for every node, contract facet, connection, and public parameter binding.

Two fresh local execution roots produced identical normalized IR, direct C++,
ARM object, ELF, link map, command vector, and portable operation results. The
retained C++ SHA-256 is
`a29078fef3bb46ad34c9a0175dad2312d765490bbd92e2d0fdc8e5b4c77958af`;
the ARM object is
`0d5d63ab75f6e1fda79b9dcc89ee977f22dfe9d96f96824d74e40d99ba3a75bf`;
and the linked ELF is
`60bac66986b21e083fb8372ce229157c8d6a0867aff4efe3c00fa0a0396902cc`.
See `evidence/task016-completion-v1/completion-report.md` and
`validation-summary.json`. No device, real-time, audible, UI, firmware-write,
upload, or flash action occurred.

All Task 016 and affected Task 013-016/governance tests pass. The ordinary
246-test repository discovery gate still reports six inherited failures in
legacy output-golden checks and the absent ignored Task 009 artifact store;
none names Task 016. The completion report records this repository-wide proof
gap rather than changing unrelated historical goldens or user-owned evidence.
