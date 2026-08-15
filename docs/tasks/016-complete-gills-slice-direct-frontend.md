# Task 016: Complete Task 011C graph direct frontend

Status: contract and prerequisite evidence audit complete on 2026-08-16;
implementation not started because one explicit compatibility-mode decision
is still required.

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

## Evidence audit and exact decision needed

The read-only pinned-source audit in
`docs/tasks/016-direct-semantics-decision-brief.md` shows that all eight items
have an authenticated conditional specification if the direct frontend is
required to preserve the exact Task 011C integer behavior and existing Ksoloti
runtime ABI. It does not select that behavior automatically.

One product decision remains: choose **legacy-equivalent direct semantics**
(recommended for the accepted incremental migration strategy) or require a
separate **Schuss-native musical-DSP specification**. No direct implementation,
binding, or evidence may begin until that choice is explicit.

## Out of scope

- Inferring the missing facts from display names, copying legacy source without
  license/semantic review, silently treating opaque legacy calls as direct IR,
  weakening compatibility, UI, device execution, listening, firmware change,
  commit, or push.

## Inputs and deliverables

Inputs are Tasks 011B-015, the eight-node graph, and the prerequisite direct
implementation/runtime specs. The completed prerequisite decision brief is an
input, not an implementation artifact. Deliverables, once the compatibility
mode is selected, are versioned operation specs, direct bindings/backend/
eligibility, expanded IR and frontend, registered direct handler,
deterministic source/ARM artifacts, goldens, tests, validator, evidence, and
completion report.

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

## Stop condition reached

Implementation is stopped before code or semantic-record changes. The pinned
evidence now supplies a complete conditional legacy-equivalent specification,
but selecting legacy-equivalent versus Schuss-native behavior remains a
material product decision. Task 015 proves the compiler mechanics are ready;
proceeding without that choice would manufacture compatibility truth outside
the task's authority. No Task 016 implementation or evidence level is claimed.
