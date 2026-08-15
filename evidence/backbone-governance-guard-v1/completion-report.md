# Backbone Governance Guard completion report

Status: complete locally on 2026-08-16. The guard, focused tests, relevant
read-only validators, full contract suite, and whitespace checks pass. Nothing
was staged, committed, pushed, published, uploaded, flashed, or written to
removable media.

## Goal and why it exists

Prevent current Schuss routing from resurrecting Task 012B as UI work,
reintroducing lettered or informal backbone labels, or drifting the accepted
Task 013-017 status/dependency gates away from ADR 0010. The guard exists
because valid superseded ADR text and completion history must remain visible
without regaining authority over current selection.

## Scope

In scope was one read-only fail-closed validator, focused negative fixtures and
tests, tool documentation, a current-authority annotation in the decisions
index, and the smallest README clarification required to name the unnumbered
UI milestone consistently.

Out of scope remained UI implementation, a Task 016 compatibility-mode choice
or implementation, Task 017 implementation, compiler or CLI behavior changes,
task renumbering, semantic/evidence promotion, hardware, and publication.

## Inputs and deliverables

The validator consumes exactly 14 fixed governance documents: the root README,
project context, roadmap, decisions index, ADRs 0008-0010, the Task 012B
retirement notice, Tasks 013-017, and the Task 016 decision brief. It also
checks current filenames under `docs/tasks/` for Task 013-020 aliases.

Delivered governed files are:

- `tools/contracts/validate_backbone_governance.py`;
- `tools/contracts/tests/test_backbone_governance.py`;
- `tools/contracts/tests/fixtures/backbone-governance-negative-fixtures.json`;
- `tools/contracts/README.md` and `README.md` command/discoverability updates;
- `docs/decisions/README.md` current-authority annotations; and
- this completion report.

The exact valid command result is one canonical JSON line with
`schema_version: backbone-governance-summary-v1`, `status: valid`, zero
diagnostics, ADR 0010 as authority, sequence 013-020, Tasks 013-015 complete,
Task 016 awaiting its explicit compatibility-mode decision, Task 017 blocked
by Task 016, and the UI milestone unnumbered and authorization-gated.

## Acceptance evidence

- Focused guard suite: 5 tests passed. Its six mutation fixtures cover UI
  resurrection, `B6`, a lettered Task 016 alias, Task 015 status drift, bad ADR
  0009 supersession, and loss of Task 017's dependency. Additional assertions
  cover missing documents, aliased filenames, valid historical ADR/completion
  text, deterministic one-line output, and unchanged governed bytes/mtimes.
- Relevant existing checks: all 15 component/build and Task 009-017 validators
  or record-set freshness commands passed, followed by the governance guard.
- Full contract suite: 228 tests passed in the isolated worktree.
- `git diff --check` passed after the final report and documentation edits.

The detached worktree initially lacked two ignored machine-local prerequisites
that Git worktrees do not inherit: `catalog/sources.local.yml` and the six-file
Task 009 prerequisite content-addressed store. Their absence reproduced six
preservation-test failures in the untouched source worktree. The exact ignored
files were mirrored from the canonical Schuss checkout; the six failures then
passed unchanged and the full 228-test suite passed. Those ignored files are
test prerequisites only and are not deliverables or governed diff content.

## Decisions this work may and must not make

This work may define stable governance diagnostic codes, the fixed document
set, current-versus-historical scan boundaries, summary fields, and focused
fixture mutations. It may annotate the existing decisions index without
changing any ADR.

It must not select Task 016 semantics, activate Task 017 or UI work, rewrite a
superseded ADR or completion report, change compiler/CLI behavior, update
goldens, renumber future work, promote evidence, or infer runtime/hardware
truth. None of those decisions or actions occurred.

## Precise limitations

- The guard validates declared governance text and task filenames. It does not
  prove compiler behavior, executable acceptance, Git publication state,
  hardware behavior, real-time safety, or audible results.
- Superseded ADR 0009's body and completed Task 013-015 report sections are
  deliberately historical and excluded from current alias scans. ADR status,
  supersession metadata, decisions-index authority, ADR 0010's Decision
  section, and every current routing surface remain enforced.
- The guard intentionally encodes the present gate. Accepting Task 016's mode,
  completing Task 016, or starting Task 017 must update the authoritative
  documents, validator expectations, and fixtures together; otherwise it
  fails closed.
- The command reads fixed repository-relative UTF-8 files and emits no cache or
  report. Missing or unreadable required documents are invalid; it does not
  discover substitute governance files from ambient directories.
