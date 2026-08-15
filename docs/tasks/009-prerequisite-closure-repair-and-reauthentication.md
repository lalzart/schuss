# Task 009 prerequisite repair: Executable-closure re-authentication

Status: complete. The user authorized this bounded investigation and repair on
2026-08-15. It did not authorize or perform Task 009 lowering, compatibility
promotion, device access, firmware installation, staging, commit, or push.

## Goal and why it exists

Determine whether the five stop reasons recorded in
`evidence/task-009-v0/preflight-stop-report.json` can be closed from exact
already-local bytes, then create the smallest additive authenticated closure
that lets Task 009 restart its preflight without weakening provenance.

The accepted prerequisite claimed more than its retained artifacts prove:
expanded firmware command vectors were not captured, compiled Java and stripped
ELF products were not retained, the Ant runtime closure was not authenticated,
and the no-patch smoke did not exercise the real configuration boundary. This
task repairs those evidence defects or records a terminal blocker.

## In scope

- Preserve and hash the complete accepted Task 005-008 and prerequisite
  revision-1 inputs before work.
- Audit the exact source, Java/Javac, Ant, dependency-JAR, GNU Make, GNU Arm,
  firmware source, linker, library, and installed firmware bytes already local.
- Capture exact expanded compiler, assembler, linker, objcopy, objdump, and
  size argument vectors with portable roots and deterministic ordering.
- Rebuild the pinned Java classes and firmware twice in independent clean roots.
- Retain the exact compiled-class closure and canonical stripped link ELF in an
  ignored content-addressed local store, with durable portable manifests and
  byte identities in task-local evidence.
- Authenticate the complete Ant executable/runtime/library closure actually
  used, without ambient `CLASSPATH`, user library, or network authority.
- Replace the string-only smoke with the smallest bridge-local, no-Schuss-graph
  isolation probe that exercises memory-only preferences, explicit registry
  configuration, and the exact generated mixed-Crossfader definition while
  making GUI, device, upload, and flash entrypoints unreachable.
- Add only additive prerequisite environment/record-set revisions if the
  repaired facts need durable semantic references; retain all revision-1 bytes.
- Correct Task 009's preflight wording only where required to distinguish
  authenticated inputs, retained products, and reproducible derived products.
- Add focused positive, negative, determinism, and preservation tests.

## Out of scope

- Lowering the Schuss Blend graph, emitting its `.axp`, generating its patch
  C++, compiling/linking that patch, or invoking the Task 009 backend handler.
- Selecting or promoting any implementation binding, eligibility, target,
  backend, build request, result, artifact, resource, or evidence record.
- Changing any accepted Task 005-008 schema or semantic record.
- Modifying any prerequisite revision-1 schema, record, manifest, or evidence
  byte in place.
- Generalizing the bridge, compiler, registry, or evidence model beyond this
  exact prerequisite closure.
- Network access, dependency installation, upstream checkout mutation,
  preference writes, GUI presentation, USB/device access, upload, flash,
  firmware installation, SD-card writes, real-time tests, or listening.
- Staging, committing, tagging, pushing, or publishing.

## Inputs

- `docs/tasks/009-minimal-deterministic-legacy-backend-proof.md`;
- `docs/tasks/009-prerequisite-authenticated-environment-and-probe-contract.md`;
- `evidence/task-009-v0/preflight-stop-report.json`;
- record sets `schuss-record-set-000001` r1 and
  `schuss-record-set-000002` r1;
- prerequisite environment `schuss-prerequisite-environment-000001` r1;
- the pinned `patcher` commit and tree in `catalog/sources.lock.json`;
- the exact installed Java, Ant, GNU Make, GNU Arm, and firmware candidates;
- the current capture script and bridge-local prerequisite smoke; and
- accepted architecture, evidence direction, and source-safety rules.

## Deliverables

- A task-local pre-repair preservation manifest.
- A repaired deterministic capture implementation.
- Two clean-root equality evidence for source, Java, Ant, firmware, command
  vectors, compiled classes, stripped ELF, symbols, and retained products.
- An exact content-addressed local-product store plus portable durable manifest.
- A bridge-isolation report covering preferences, registry, GUI, device,
  upload, and flash authority.
- Additive prerequisite environment/record-set revisions only if required.
- Focused tests for every original stop code and relevant failure injection.
- A post-repair preservation/equality report and a clear `ready` or `blocked`
  Task 009 restart verdict.

## Acceptance tests

1. All existing 72 contract, 14 inventory, and 6 catalog tests and every
   validator pass before and after the task.
2. Record sets 000001 r1 and 000002 r1, prerequisite environment r1, all
   revision-1 evidence, and frozen operation/validator bytes are unchanged.
3. Two independent clean captures produce byte-identical canonical manifests,
   compiled classes, stripped ELF, firmware bin, symbols, and command vectors.
4. The command manifest contains exact expanded executable argument vectors,
   target/ABI flags, include/library/linker inputs, and exit statuses; quiet
   progress text is not represented as a command vector.
5. Every Java class and dependency JAR in the authenticated classpath is
   retained or reproducibly resolved from an authenticated retained input, with
   exact hashes and no ambient classpath authority.
6. The exact Ant launcher, executable scripts/JARs, and runtime library closure
   actually used are enumerated and hashed.
7. The canonical stripped link ELF and firmware bin are retained by content
   hash and match both clean reproductions.
8. The bridge isolation probe uses the actual memory-only preference and
   explicit registry/generated-object path, and fails if preference, GUI,
   device, upload, flash, ambient registry, or filesystem discovery is enabled.
9. No canonical artifact contains a timestamp, random/process ID, temporary
   root, or absolute machine path.
10. No Task 009 graph/probe/backend/promotion stage and no hardware or firmware
    action occurs.
11. `git diff --check` and the complete repository validation suite pass.
12. The final report maps every original stop code to `closed` or `open` with
    exact evidence and states whether Task 009 may restart.

## Decisions this task may make

- The exact task-local evidence and ignored content-addressed store layout.
- The deterministic command-vector capture mechanism.
- Whether compiled classes and firmware products are retained directly or
  reconstructed from a separately authenticated retained input closure, as
  long as Task 009 can verify the chosen path before its backend invocation.
- The smallest bridge-local no-graph isolation probe implementation.
- Stable IDs/revisions and file layout for additive repaired prerequisite
  records when necessary.
- Narrow preflight wording corrections that remove an impossible circular
  requirement without weakening exact-byte authentication.

## Decisions this task must not make

- Component, graph, instrument, device, target, backend, binding, eligibility,
  or capability semantics.
- A new prerequisite schema unless the accepted schema cannot truthfully carry
  an additive revision; in that case stop and report the schema conflict.
- Whether the mixed Crossfader is production-compatible or selectable.
- Any Task 009 lowering, generation, ARM patch compile/link, result, or evidence
  claim.
- Any substitution, network resolution, implicit discovery, preference/load
  order authority, or weakening of a validator.

## Stop conditions

Stop and report if an exact required input is unavailable without network,
installation, or upstream mutation; if deterministic reconstruction cannot be
made independent of local paths and parallel output ordering; if real bridge
isolation cannot be established without executing the Schuss graph/backend; if
an additive repair requires changing an accepted revision-1 byte or schema; or
if any repair would imply compatibility, device, real-time, or audible proof.

## Completion report

The repair completed without adding or revising any semantic schema or record.
The 63-member accepted/revision-1 preservation fingerprint is
`a1ff7e05f6da1cdb30d45f24cd4a41b03e4b25c780126bcf7522e957375be017`;
the post-repair comparison passed.

Two independent clean roots reproduced byte-identically:

- the pinned patcher and factory source archives;
- all 896 compiled Java classes and the complete classpath fingerprint
  `5ebd2f2b7f2aa6dc1d3d10a04edb5f2bbedd97cfb4372dab56dc22c778b17710`;
- the 57-member direct Java/Ant launcher-library closure;
- 194 expanded ARM compiler, assembler-driver, linker-driver, binary-tool, and
  inspection command vectors with per-command exit status;
- the firmware binary
  `fd61a6a109a234d1c72e445a0542ab59c407a6896b9aafe2bfcbcadaf775e258`;
- the stripped link ELF
  `df65f2153eb999386cc1bc30b382cafeac63aea8495bf8cb4cdad1c01fca944b`;
- the 1,950-line symbol manifest; and
- the real generated-Mixer isolation-probe output.

Six exact products are retained under the ignored content-addressed store and
named portably by `evidence/task-009-prerequisite-repair-v1/retained-products.json`.
The 12 other durable repair-evidence files are byte-indexed by
`repair-evidence-manifest.json`.
The bridge probe installed a memory-only preference singleton, configured only
the pinned factory root, intercepted `generatedobjects.Mixer`, and observed the
exact mixed `objects/mix/xfade.axo` definition. It left the factory tree and
isolated user/preference/work roots unchanged; missing headless authority and
an added GUI-authority argument both failed closed.

All five stop codes in the original preflight report are closed. The verdict is
`ready-for-task009-preflight-restart`, not proof that Task 009 itself ran or
that the binding is compatible. Structural/reproduction evidence passed;
generated-patch, connected-device, real-time, and audible levels remain
`not-run`.

Final validation passed: 80 contract tests (the original 72 plus eight repair
tests), 14 inventory tests, 6 catalog tests, all four contract validators, all
three inventory validators, the semantic-catalog validator, and
`git diff --check`.
