# Local-source configuration test hygiene for Tasks 024 and 025

Status: completed as an unnumbered maintenance task. Task 027 remains reserved
for the application-spine sequence accepted by ADR 0014.

## Goal and why it exists

Keep ordinary contract tests runnable in worktrees that correctly omit ignored
`catalog/sources.local.yml`, while preserving the configured Task 024 and Task
025 reproduction checks as explicit validation of pinned Ksoloti source
identity. A missing machine-local source map is a prerequisite gap, not an
ordinary Schuss product failure.

## In scope

- Identify every Task 024/025 unit-test check that reads configured source
  locations directly or through its record generator.
- Mark only those checks with one deterministic prerequisite skip when the
  ignored local mapping is absent.
- Provide a separately named configured-validation command that runs exactly
  those checks and fails explicitly when its prerequisite is absent.
- Preserve the existing pinned commit, Git-tree, source-hash, generated-byte,
  and two-run determinism assertions when configuration exists.

## Out of scope

- Historical golden or hash auditing or changes.
- Creating or discovering a local source mapping, changing source locks,
  weakening source identity checks, or mutating upstream checkouts.
- Product, catalog, compiler, UI, palette, Java, legacy `.axp`, ARM, hardware,
  real-time, audio, Git staging, commit, push, or publication work.

## Inputs and deliverables

Inputs are the accepted Task 024/025 contracts, their existing tests and
generators, `catalog/sources.lock.json`, the optional ignored
`catalog/sources.local.yml`, and the ordinary contract-suite command.

Deliverables are prerequisite guards on the three affected unit tests, the
read-only `validate_task024_025_configured_sources.py` runner, this task
contract, and command documentation.

## Acceptance tests

1. Focused: without `catalog/sources.local.yml`, both Task 024/025 test modules
   pass their ordinary assertions and report exactly three explicit skips.
2. Focused negative: without the mapping, the configured runner exits `2`,
   names the missing prerequisite and the exact rerun command, and creates no
   configuration or generated output.
3. Configured reproduction: when the mapping exists, the separately named
   runner executes exactly the Task 024 generated-output check plus the Task
   025 source audit and generated-record check; their existing commit, hash,
   freshness, and determinism assertions are unchanged.
4. Adjacent regression: Task 024/025 ordinary non-source tests remain passing.
5. Final aggregate: ordinary contract discovery may cover the same three
   methods as skips when configuration is absent; no separate aggregate rerun
   is needed after an unchanged focused result for this isolated test-only
   split.

## Decisions this task may make

- The deterministic skip wording, configured runner name, and exact grouping
  of the already-existing source-dependent checks.

## Decisions this task must not make

- Any source, source-lock, golden, retained artifact, schema, record, product,
  compiler, UI, or evidence claim change.
- Treating absence as a pass, or allowing configured validation to bypass any
  existing provenance, identity, freshness, or determinism assertion.
