# ADR 0018: Adopt proportional validation profiles

- Status: accepted
- Date: 2026-08-20
- Extends: the evidence separation rules of ADRs 0007, 0013, and 0016
- Task: 035

## Context

Schuss has strong evidence boundaries, but its validation workflow gradually
turned each completed task into another layer of the next task's ordinary test
suite. Cumulative record-set manifests were recursively validated as complete
snapshots, so the same immutable members were reopened for every ancestor.
Focused, adjacent, aggregate, copied-root, compiler, and render commands then
overlapped. The resulting 30- to 40-minute task endings did not provide 30 to
40 minutes of distinct evidence.

Some checks also depend on ignored machine-local source configuration, while
others intentionally preserve historical presentation bytes that differ from
the current successor. Keeping those as known failures in the ordinary
aggregate makes a new regression harder to see.

The evidence itself remains valuable. The problem is ownership and cadence,
not the existence of native, source-authenticated, fresh-process, or historical
checks.

## Decision

Schuss validation is divided into explicit profiles:

- **current**: ordinary semantic, negative, retained-byte, freshness, and
  governance checks for the working tree;
- **compatibility**: historical ordinary contract checks selected when shared
  infrastructure can affect completed behavior;
- **configured-sources**: checks requiring authenticated paths from ignored
  machine-local source configuration;
- **native**: compilation, sanitizer, CTest, and render matrices;
- **reproduction**: copied-root, fresh-process, and explicit retained-evidence
  reproduction; and
- **release**: one deduplicated composition of current, compatibility, native,
  and reproduction; configured sources are added when their source-dependent
  inputs are applicable.

Ordinary test discovery must be useful by itself and green in a correctly
unconfigured checkout. It may skip a named external prerequisite, but the
configured-source profile fails closed if explicitly selected without that
prerequisite. A skip never promotes evidence.

New ordinary test modules belong to `current` by default. Checks with side
effects, external prerequisites, native toolchains, expensive copied-root or
fresh-process matrices, or meaningful runtime cost must be explicitly listed
in the validation plan. Small subprocess or temporary-root fixtures may remain
in compatibility when isolation is the behavior under test. Duplicate,
malformed, or unknown entries fail plan validation.

The runner exposes granular check IDs and read-only plan/list modes. Declared
inputs guide affected-check selection; they do not create an opaque cache or
imply that an unselected evidence boundary passed. Missing selected
prerequisites are preflighted before expensive work, and an unexpected skip in
an explicitly selected check is incomplete rather than passing.

Validation selection follows affected boundaries. Focused and adjacent checks
run while code is changing. Expensive evidence runs once after implementation
freeze when the changed boundary can affect it. A release or an explicitly
full-integration task runs the deduplicated release profile. Intermediate
phases and prose-only changes do not automatically replay the entire history.

The latest cumulative record set remains a complete authenticated snapshot.
Its manifest ancestry and every exact parent/subset edge are checked, while
each selected schema and record member is structurally and cryptographically
validated once per top-level load. Caches are confined to that load; later
calls observe the filesystem again.

Historical artifact identity and current behavior are different assertions.
Accepted historical bytes are protected by their manifest/evidence hashes.
Only the latest applicable generator or successor fixture is a current
freshness/behavior gate. Reproducing an old generator requires its original
commit and prerequisites, not an assumption that successor code must recreate
old output.

## Consequences

Routine validation becomes a meaningful fast regression signal. Native,
configured-source, and copied-root evidence remains explicit and auditable
without executing accidentally several times. Task contracts can ask for a
narrower profile during a phase and reserve full integration for the phase
that owns it.

This decision does not lower any evidence gate, change accepted bytes, allow
missing sources to pass, or infer native/device/audible evidence from structural
tests. It changes how checks are selected and deduplicated, not what a passing
check proves.
