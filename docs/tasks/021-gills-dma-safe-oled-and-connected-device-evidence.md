# Task 021: DMA-safe Gills OLED and connected-device evidence

Status: completed on 2026-08-16 through deterministic local evidence level 5
and separately retained connected-device evidence level 6 under ADR 0013.
Tasks 019 and 020 remain deferred and are not activated by this correction.

## Goal and why it exists

Preserve the immutable Task 018 result while correcting the mapped Gills OLED
command transport so every DMA source buffer is in DMA-visible SRAM. Retain the
separately authorized connected-device result as an exact level-6 claim without
inflating it into real-time, audible, persistence, safety, or release proof.

This task exists because the Task 018 binary linked successfully but placed a
stack-local two-byte I2C command payload in a ChibiOS thread working area in
CCM. That memory is not usable by the STM32 DMA path. The exact connected probe
failed at OLED initialization even though its local level-5 build evidence was
valid.

## Dependencies

Task 018 is the immutable parent closure and ADR 0012 remains its promotion
authority. ADR 0013 authorizes this versioned corrective successor and the
separate level-6 evidence boundary. Tasks 016 and 017 remain transitive exact
dependencies through Task 018.

The user separately authorized volatile-RAM connected-device execution. That
authorization did not include firmware flash, SD-card writes, persistent
installation, additional hardware experiments, staging, commit, or push.

## In scope

- Preserve every Task 018 record, record-set member, generated artifact, and
  retained evidence byte.
- Add an exact handler revision, runtime-realization revision, build-request
  revision, and the mechanical instrument/coverage successors required to
  keep old and corrected inspection closures independently exact.
- Replace only the unsafe stack-local OLED command payload with a dedicated
  two-byte `.sram2` buffer; retain the independent 129-byte OLED page buffer
  and its `0x40` data-control byte.
- Keep graph, device profile, panel evidence, compute target, backend, DSP
  operations, mappings, transforms, pickup, smoothing, gestures, display text,
  and semantic goldens unchanged.
- Register Task 018 and Task 021 handlers side by side with exact selectors and
  no implicit fallback. No implicit fallback is permitted at any selector.
- Build the Task 021 closure twice in fresh roots and processes, compare every
  portable operation result and artifact byte, and retain local level-5 proof.
- Retain one level-6 claim bound to the exact connected ELF, derived upload
  binary, board identity, volatile-RAM readback/start result, responsiveness
  probes, and user-confirmed upright four-word OLED output.
- Add focused positive, negative, regression, CLI, governance, and evidence
  validation.

## Out of scope

- Rewriting Task 018 in place or reclassifying its failed device probe as a
  successful Task 018 result.
- New DSP behavior, mapping changes, panel-layout claims, catalog work,
  sampling/assets, another target/device, firmware replacement, or UI work.
- Treating the mechanical instrument/coverage successors as new musical
  semantics; they exist only to preserve exact, unambiguous closure selection.
- Control sweeps, audio tests, timing/resource measurement, endurance,
  listening, electrical safety, or release qualification.
- Firmware flash, SD-card write, persistent install, or any additional hardware
  action.
- Staging, committing, tagging, pushing, or publication without separate
  approval.

## Inputs and deliverables

Inputs are ADRs 0011-0013; exact Task 018 record set
`schuss-record-set-000012@1`; the retained Task 018 evidence; the authenticated
Task 016 ARM toolchain/runtime boundary; the pinned Gills panel sources; and the
separately authorized connected-device observations.

Deliverables are this contract; ADR 0013; exact Task 021 records and record set
`schuss-record-set-000013@1`; handler/frontend/runtime successors; focused
tests and validators; deterministic retained build evidence under
`evidence/task021-completion-v1/`; and a separate exact level-6 evidence claim
and connected-device observation.

The retained executable descriptor's `input_closure_hash` binds the canonical
six-reference producer-input closure: request, runtime realization,
instrument, device profile, compute target, and handler. It is intentionally
distinct from the build plan's accepted-record closure hash. That broader
closure contains the retained evidence claim, which itself references the
executable artifact, so using it as the artifact input identity would create a
circular record identity.

## Acceptance tests

1. Task 018 generation and retained evidence checks remain byte-exact after
   Task 021 is added.
2. Task 018 request/handler/runtime revisions and Task 021 successors coexist
   under exact selectors with no fallback or implicit latest-revision choice.
3. The Task 021 generated C++ contains one dedicated two-byte
   `SchussOledCommand` buffer in `.sram2` and contains no stack-local OLED
   command payload.
4. OLED command writes use only `SchussOledCommand`; page writes retain the
   separate `SchussOledTx` buffer and set `SchussOledTx[0] = 0x40`.
5. The mechanical instrument and coverage successors differ only in exact
   identity/reference closure; graph, DSP semantics, mappings, and public
   facets remain unchanged.
6. Exact Task 018 and Task 021 instrument inspections each resolve one runtime
   realization, and the Task 021 build plan selects request revision 5,
   handler revision 2, and runtime revision 2.
7. Two fresh roots and processes produce identical portable operation results
   and artifact bytes; generated C++ SHA-256 is `e69155998e91c7c3af6b6e0aaebbac965f4cf822b67382f25de5776453af2928`
   and target ELF SHA-256 is `4f9bd68f5f71fc9d5bf70bd88988e7e20ff980fb46a886beff52f60c968874de`.
8. Authenticated `objcopy -O binary` derives the exact 6,440-byte uploaded
   binary with SHA-256 `b573ea36aaa29b5e213ca0e616b13e7e2131d7cad2a0ab29a5b5fe9eaa8b13e3`.
9. The level-6 claim names the exact instrument, device profile, compute
   target, request, executable artifact, procedure identity, board serial,
   firmware identity, and volatile-RAM-only limitations.
10. Retained observation records exact RAM readback, start acknowledgement,
    three responsiveness probes over six seconds, flags zero, upright
    orientation, and the four words `SCHUSS`, `BLEND`, `PICKUP`, and `TASK018`.
11. Build execution reports levels 1-5 passed and levels 6-8 `not-run`; the
    separate product evidence summary reports level 6 passed and levels 7-8
    `not-run`.
12. Task 021 record, contract, focused, determinism, governance, path/hash,
    CLI, Task 018 regression, and `git diff --check` validation passes. The
    full repository suite is also run; any unrelated inherited failure must be
    reproduced from clean `HEAD` and reported rather than changing its golden
    under this task.

## Decisions Task 021 may make

- Exact successor revisions and stable evidence/artifact IDs needed to keep
  old and corrected closures independently selectable.
- The smallest source transformation and regression anchors that prove the
  dedicated DMA-safe command-buffer correction.
- The deterministic retained evidence shape for distinguishing build-level
  proof from the already-performed connected-device observation.
- Exact diagnostics and validation additions required to allow unique
  versioned runtime closures without permitting ambiguity.

## Decisions Task 021 must not make

- Any rewrite of Task 018 bytes or any claim that its original connected
  binary passed.
- New graph, DSP, device-profile, panel, mapping, transform, gesture, pickup,
  smoothing, or display semantics.
- An implicit newest-revision rule, display-name selection, ambient discovery,
  or fallback between handlers.
- Level 7 or level 8 truth, control/audio behavior, persistence, safety, or
  release readiness without corresponding procedures and evidence.
- Activation of Task 019, Task 020, or UI work.
- Firmware flash, SD-card write, persistent install, further hardware action,
  staging, commit, or push.

## Readiness state

Task 021 is complete for exact record set `schuss-record-set-000013@1`.
Deterministic build execution reaches level 5 in two fresh roots and processes.
The exact corrected ELF and derived binary match the separately authorized
volatile-RAM candidate, which acknowledged start, remained responsive, and was
confirmed upright with all four expected words. The connected-device claim
therefore reaches level 6 only.

Levels 7 and 8 remain `not-run`. No control sweep, real-time/resource
measurement, audible/listening test, firmware flash, SD-card write, persistent
install, stage, commit, or push is claimed.

The repository-wide contract suite retains one unrelated inherited failure:
the Task 011A CLI output golden expects input-closure hash `291b695c...`, while
clean `HEAD` already emits `7aff3534...`. Task 021 does not rewrite that
historical golden.
