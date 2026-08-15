# Task 009 prerequisite: Authenticated environment and isolated probe contract

Status: complete. The user authorized this prerequisite on 2026-08-15. The
accepted completion still does not authorize Task 009, backend proof,
artifact-generation, or hardware execution.

Work in the Schuss repository. Work only on this prerequisite after the user
explicitly approves running it. Do not run Task 009 as part of this task.

This prerequisite exists because the Task 009 preflight correctly stopped
before executable work. The locally observed ARM tools were identifiable, but
the available Java application/classpath and firmware/runtime ABI bytes were
not authenticated to the pinned `patcher` source commit. Two contract problems
also prevent a truthful implementation:

1. the accepted validators and `load_repository_context()` enumerate every
   JSON record in their known contract directories, so placing new revisions
   beside revision 1 would change the frozen Task 005-008 summaries and
   operation bytes; and
2. `build-request-v0`, `build-result-v0`, and `evidence-claim-v0` cannot
   represent an ineligible `candidate-under-test` probe result and cite that
   exact result without pretending it was a selected production build.

This task must close those prerequisites without lowering the Blend graph,
emitting `.axp`, generating patch C++, promoting compatibility, or executing a
linked artifact.

Before changing anything, read completely:

- `AGENTS.md`;
- `README.md`;
- `docs/PROJECT_CONTEXT.md`;
- `docs/ARCHITECTURE.md`;
- `docs/SCHEMA_STRATEGY.md`;
- `docs/COMPILER_STRATEGY.md`;
- `docs/LEGACY_STRATEGY.md`;
- `docs/ROADMAP.md`;
- `docs/OPERATION_CONTRACTS.md`;
- `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`;
- ADRs 0005, 0006, and 0007;
- Tasks 004 through 009, including completion evidence for Tasks 004-008;
- every Task 005-008 schema, production record, validator, fixture, test,
  operation envelope, registry loader, and backend-invocation seam;
- `legacy/ksoloti-bridge/README.md` and its existing source and fixtures;
- `catalog/sources.lock.json` and the exact pinned `patcher` Git object; and
- the exact local Java, legacy application/source, GNU Arm Embedded, and
  firmware/runtime candidates proposed for authentication.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Goal and why it exists

Create the smallest reproducible, fail-closed prerequisite that lets a later
Task 009 run start with:

1. an immutable Java/source/classpath closure derived from exact local bytes;
2. an immutable firmware/runtime ABI closure traceable to the pinned source;
3. an exact GNU Arm Embedded identity manifest for the tools later permitted
   to consume that closure;
4. an explicit accepted-record-set mechanism that preserves the frozen Task
   005-008 view while allowing later revisions through an explicit prospective
   view;
5. a closed non-production conformance-probe input/result contract that can
   name binding revision 1 as `candidate-under-test` without selecting it; and
6. an acyclic evidence-reference path by which a later evidence claim can cite
   the exact probe result, and a later eligibility revision can cite evidence
   that names the strictly earlier binding revision.

This task exists to turn the failed Task 009 preflight into exact approved
inputs and truthful schemas. It is not the backend proof itself.

## In scope

- Reproducing and hashing the complete Task 005-008 baseline before changes.
- Read-only access to pinned Git objects and ignored local source configuration
  solely as locators.
- Creating a clean source capsule from the exact locked `patcher` commit via
  read-only Git object/archive access. Dirty checkout bytes are not inputs.
- Exact hashing of the Java executable, compiler, classpath members, source
  inputs, compiled class outputs, and any locally available dependency JARs
  required for the bounded legacy generation closure.
- Offline compilation of the minimum pinned Java class closure in a fresh
  task-local output root, but only when every source and dependency byte is
  already local, explicitly enumerated, and content-addressed.
- A deterministic Java closure manifest defining the executable, classpath,
  locale, encoding, working-directory contract, controlled source/registry
  inputs, and prohibited preference/GUI/device authority.
- Static and bounded smoke validation that the proposed later bridge entrypoint
  can receive explicit source, registry, target, and firmware inputs without
  treating mutable preferences as authority. It must not load the Task 006
  Blend patch or generate patch source.
- Exact hashing of the existing GNU Arm Embedded tools that a later Task 009
  run would invoke. No generated patch input may be compiled in this task.
- An offline, clean-root reproduction of the exact firmware/runtime artifact
  and ABI closure from pinned sources when the already-local build inputs are
  complete and the reproduction requires no source modification, download, or
  installation.
- Exact manifests for firmware ELF/bin bytes, exported/imported symbol view,
  ABI headers, linker scripts, libraries, compiler/linker flags, and the source
  and tool inputs that produced them.
- A minimal explicit accepted-record-set or equivalent registry-selection
  contract. The accepted Task 005-008 view must remain the default used by
  existing validators and operations.
- A separate prospective Task 009 registry view selected only by an exact
  manifest/reference, never by directory globbing, newest-revision guessing,
  or ambient filesystem order.
- The smallest new versioned conformance-probe input and result schemas needed
  to represent `candidate-under-test`, exact environment/source closure,
  requested stages, ordered outcomes, diagnostics, and artifact hashes.
- The smallest new versioned evidence schema or companion reference contract
  needed to cite an exact conformance-probe result without calling it a normal
  build result.
- Schema, validator, registry, direct-API, CLI, failure-injection,
  determinism, and preservation tests for only these prerequisite mechanisms.
- A correction to the proposed Task 009 prompt so it consumes the accepted
  prerequisite outputs and no longer requires mutually incompatible baseline
  and directory-enumeration behavior.
- Documentation of exact established closure, unresolved facts, and the
  remaining Task 009 execution boundary.

## Out of scope

- Running Task 009 or changing its status to active or complete.
- Lowering any Schuss graph or selecting an implementation binding.
- Emitting `.axp`, a resolution plan, a source map, generated patch C++, ARM
  patch objects, a linked patch executable, or a production build result.
- Calling the revision-1 mixed Crossfader binding eligible, compatible,
  selected, supported, or promoted.
- Creating implementation-binding revision 2, eligibility revision 2, target
  or backend promotion revisions, or a promoted build request.
- Claiming Task 009 evidence levels 3, 4, or 5. Environment reproduction is
  prerequisite identity evidence, not graph lowering, source generation, or
  ARM patch compile/link evidence.
- Modifying pinned legacy source, firmware source, an upstream checkout, or a
  locally installed application/toolchain.
- Downloading dependencies, installing packages, updating source checkouts, or
  using network resolution.
- Treating a dirty application JAR, version string, source directory, or
  successful parse as proof of pinned provenance.
- Making Ksoloti Java, XML, firmware, or toolchain values part of Schuss domain
  semantics or reusable schema constants.
- Connected-device execution, USB, upload, flash, SD-card writes, boot,
  firmware installation, real-time measurement, or listening.
- GUI, graph editor, product CLI, Task 010 UX, direct Schuss-to-C++ frontend,
  generalized compiler IR, or broader object support.
- Rewriting or deleting any accepted Task 005-008 schema or production record.
- Staging, committing, tagging, pushing, publishing, uploading, or flashing.

## Inputs and frozen boundaries

Treat as immutable:

- every accepted Task 005-008 schema and production record;
- all accepted Task 005-008 validator summaries, canonical outputs, operation
  fixtures, diagnostic codes/order, and test expectations;
- the production Blend graph and mixed Crossfader binding revision 1;
- build request `schuss-build-request-000001` revision 1;
- the unresolved Task 007 environment, target, backend, and eligibility facts;
- the Task 008 operation envelopes and data-only backend-invocation seam;
- `catalog/sources.lock.json` and the pinned `patcher` commit; and
- the ownership, reference, evidence-level, and strictly-earlier binding rules
  in the accepted architecture and ADRs.

Before implementation, record SHA-256 baselines for the complete frozen trees
and canonical outputs named by Task 009. Also record the repository status and
preserve the pre-existing untracked Task 009 prompt. Do not normalize, rewrite,
or adopt unrelated user work.

## Execution authorization and safety boundary

Creating this prompt authorizes nothing beyond writing this prompt. A later
explicit instruction to run this prerequisite authorizes only:

- read-only inspection and hashing of exact local source/tool/application
  candidates;
- creating fresh task-local or ignored content-addressed output roots;
- read-only Git object/archive extraction of the pinned source commit;
- executing the exact local Java compiler/runtime only for deterministic
  closure construction and bounded no-patch smoke checks;
- executing the exact local GNU Arm Embedded tools only to reproduce and
  inspect the pinned firmware/runtime closure, never to compile generated
  Schuss patch source; and
- implementing and testing the bounded registry/probe/evidence prerequisite
  contracts in this repository.

It does not authorize network access, package installation, source or installed
application mutation, backend proof execution, device access, firmware action,
staging, commit, or push.

Local absolute paths may appear in a non-canonical execution log, but never in
semantic identities, schemas, canonical manifests, content hashes, portable
locators, or retained evidence records.

## Required work sequence

### 1. Reproduce the frozen baseline and the two contract conflicts

Before introducing a design, prove the current state:

1. Run the complete accepted Task 005-008 tests and validators.
2. Capture all preservation hashes required by Task 009.
3. Reproduce the current `build.resolve` unresolved trace and its four reasons.
4. Demonstrate in a temporary fixture that adding a new revision to a currently
   glob-enumerated production directory changes the loaded registry and frozen
   validator/operation result.
5. Demonstrate that the v0 request/result/evidence schemas cannot truthfully
   express the proposed non-production candidate probe and exact probe-result
   evidence reference.

These are bounded conflict demonstrations. Do not add production revisions to
prove them.

### 2. Establish the pinned source capsule

- Resolve the exact `patcher` commit from the source lock.
- Extract from Git object storage into two independent fresh roots without
  reading tracked bytes from the dirty checkout as source inputs.
- Record commit, tree, archive/capsule byte identity, file manifest, file modes,
  lengths, and hashes for the complete Java and firmware/build subset used.
- Prove both extractions yield identical canonical manifests.
- Never clean, reset, checkout, update, or rewrite the upstream worktree.

### 3. Establish the Java/classpath closure

- Inventory exact Java/Javac executable bytes and version output.
- Enumerate every source, JAR, resource, and generated class required by the
  smallest later headless generation entrypoint.
- Reject a prebuilt application JAR unless its complete relevant class/source
  closure is authenticated to the pinned commit.
- If compiling pinned classes, use only explicitly enumerated local inputs and
  a fresh output root. Disable annotation/network/dependency discovery and
  ambient `CLASSPATH` authority.
- Compile twice in isolated roots and compare normalized class manifests and
  every retained class/JAR byte.
- Record any nondeterministic class bytes or path leakage and fail closed.
- Prove through static dependency inspection plus a bounded no-patch smoke
  entrypoint that target, firmware, source roots, object registry, locale, and
  encoding can be explicit inputs. Mutable preferences, GUI presentation, USB,
  upload, and flash must be absent or unreachable.
- Do not solve preference authority by editing the pinned upstream source. A
  bridge-local isolation mechanism may be specified for Task 009, but this
  prerequisite must not implement patch generation.

### 4. Establish the ARM and firmware/runtime ABI closure

- Hash every exact compiler, assembler, linker, object utility, and size tool
  that would participate in the closure.
- Starting only from the pinned source capsule and exact local tool inputs,
  reproduce the firmware/runtime artifacts in two clean output roots if the
  local dependency closure is complete.
- Record canonical argument vectors with portable locators, target triple,
  architecture/ABI flags, deterministic-build flags, exact headers, linker
  scripts, libraries, produced ELF/bin hashes, ELF identity, and a stable
  exported/imported symbol manifest.
- Prove which ABI files and symbols a later generated patch compile/link would
  consume. Do not infer this from filenames or version prose.
- Distinguish source identity, firmware artifact identity, ABI compatibility,
  and target-build compatibility. None implies device execution.
- If the pinned build cannot be reproduced from already-local exact inputs,
  stop. Do not substitute bundled firmware bytes merely because they run on
  the same board or report a similar version.

### 5. Add explicit accepted and prospective registry views

Implement the smallest versioned mechanism satisfying all of these rules:

- the Task 005-008 accepted view lists or otherwise pins its exact schemas and
  records by portable path and byte/content hash;
- existing validator commands and Task 008 operations continue to use that
  accepted view by default and produce byte-identical outputs;
- a prospective view can explicitly add later revisions and prerequisite
  schemas without changing the accepted view;
- no view uses newest-revision guessing, recursive ambient discovery, directory
  order, mutable display names, or category/source paths as identity;
- duplicate exact keys, unlisted records, missing members, extra members, hash
  mismatches, cross-view leakage, and unknown schema versions fail closed; and
- the in-memory operation context records which exact view it loaded.

Do not redesign the domain registries or introduce a general database/package
manager. This is an exact record-set selection boundary only.

### 6. Add the isolated conformance-probe contracts

The new closed versioned input/result boundary must:

- use its own schema identity and stable record IDs;
- carry an explicit `candidate-under-test` state;
- reference exactly one binding revision, exact graph/contract closure, exact
  proposed environment closure, requested probe stages, and probe procedure;
- never contain `selected_bindings` or assert production eligibility;
- record the complete ordered stage sequence with first-terminal failure and
  all later stages `not-run`;
- retain deterministic diagnostics and exact artifact references only for
  stages actually run;
- be rejected by normal `build.resolve` and the production backend handler;
- reject a normal build request/result at the probe boundary; and
- permit immutable evidence to cite the exact probe result while retaining the
  rule that a later eligibility revision references a later binding revision
  and cites evidence whose closure names strictly earlier binding revision 1.

Do not modify v0 schemas in place. Add the smallest new schema versions or
companions needed for this truthful reference direction. Results own their
stage outcomes and artifacts; evidence points to immutable results; results do
not point back to evidence.

This task validates the schema and reference mechanics only. Its production
probe fixture must remain `not-run`; no candidate is executed.

### 7. Correct the proposed Task 009 contract

Update the proposed Task 009 prompt, while leaving it `not started`, so that it:

- names this prerequisite and its exact accepted outputs;
- uses the explicit prospective registry view for new revisions;
- preserves the default Task 005-008 accepted view and frozen outputs;
- uses the accepted probe and evidence schema versions instead of asking Task
  009 to decide them again;
- performs preflight against the authenticated environment manifests;
- stops on any missing/mismatched closure member; and
- retains every existing prohibition on hardware, firmware action, staging,
  commit, push, generalized compiler work, and evidence overstatement.

Do not activate or execute Task 009.

## Deliverables

- This approved prerequisite contract, marked active only when execution
  begins and complete only after every acceptance test passes.
- A deterministic pre-task preservation manifest and post-task equality report.
- A pinned source-capsule manifest derived from the locked Git object.
- A deterministic Java/classpath closure manifest and reproduction report.
- A deterministic GNU Arm Embedded identity manifest.
- A deterministic firmware/runtime ABI closure manifest and reproduction
  report, or a truthful terminal unresolved report with no Task 009 promotion.
- The minimal explicit accepted/prospective record-set mechanism and tests.
- Closed conformance-probe input/result schemas, reference validation, fixtures,
  and tests.
- The minimal versioned evidence-reference addition required to cite a probe
  result without an ownership cycle.
- Updated architecture/contract documentation only where the new prerequisite
  boundary requires it.
- A corrected proposed Task 009 prompt that consumes these outputs.
- A completion report naming exact hashes, commands, evidence limits, and any
  remaining blocker.

Generated local tool/application/firmware bytes belong in a fresh ignored or
task-local content-addressed output root. Durable repository artifacts retain
portable locators and hashes, not machine-local absolute paths.

## Acceptance tests

This prerequisite is accepted only if automated tests and recorded evidence
prove all of the following:

1. Every pre-existing Task 005-008 test and validator passes before and after
   the change.
2. Every accepted Task 005-008 schema, production record, validator summary,
   operation fixture/result byte stream, diagnostic code/order, and content
   hash remains byte-identical.
3. The default repository context loads exactly the frozen accepted view and
   ignores neither unexpected files nor errors silently.
4. A prospective view loads only explicitly listed exact members and fails on
   missing, extra, duplicate, unlisted, stale, or hash-mismatched members.
5. Two independent source-capsule extractions from the pinned Git object yield
   identical canonical manifests, with no dirty-checkout byte as an input.
6. The Java closure enumerates and hashes every executable, compiler, source,
   JAR, resource, and retained class byte required by the proposed headless
   generation path.
7. Two isolated Java closure builds yield identical canonical manifests and no
   ambient classpath, network, timestamp, temporary-root, or local-path
   authority enters canonical identity.
8. The bounded Java smoke check uses no Task 006 patch and proves explicit
   configuration can replace preference, GUI, device, upload, and flash
   authority at the later bridge boundary.
9. The ARM manifest identifies every exact tool component and version/hash
   needed by the firmware/runtime reproduction and later Task 009 build.
10. Two clean firmware/runtime reproductions yield identical retained ELF/bin,
    symbol, header, linker, library, flag, and closure manifests.
11. The firmware/runtime output is traceable to the pinned source capsule and
    exact tool inputs. A bundled but unauthenticated binary cannot pass.
12. Probe input/result fixtures validate only through their own boundary, carry
    explicit `candidate-under-test`, and cannot validate as build request/result
    or enter `build.resolve` or the production backend handler.
13. Probe result stage order, terminal behavior, diagnostics, and artifacts are
    deterministic, with the production fixture remaining `not-run`.
14. The evidence-reference contract can cite an exact probe result and binding
    revision 1 without a probe/result/evidence cycle.
15. A fixture proves a later eligibility revision can reference binding
    revision 2 and cite evidence whose exact closure names strictly earlier
    binding revision 1.
16. No production target, backend, environment, binding, eligibility, request,
    result, artifact, resource, or evidence revision is promoted by this task.
17. The corrected Task 009 prompt remains proposed/not started and no `.axp`,
    patch C++, patch object, linked patch executable, or production backend
    result exists.
18. No network, upstream mutation, installed-tool mutation, preference write,
    device, USB, upload, flash, SD-card, real-time, audible, staging, commit, or
    push action occurs.
19. All generated canonical bytes are deterministic and contain no timestamps,
    random IDs, process IDs, temporary roots, or machine-local absolute paths.
20. `git diff --check` and the complete repository validation/test suite pass.

## Decisions this prerequisite may make

- The filename, schema identity, and minimal structure of the explicit
  accepted/prospective record-set mechanism.
- The smallest new probe input/result and evidence-reference schema versions
  needed to preserve truthful ownership and reference direction.
- The task-local layout for ignored content-addressed source, Java, toolchain,
  and firmware closure bytes.
- The exact deterministic manifest formats and stable diagnostic codes owned by
  prerequisite identity/registry/probe validation.
- The minimum pinned Java class subset needed for the later bridge, provided it
  is derived from exact local authenticated inputs.
- The bounded no-patch Java smoke interface used to prove explicit
  configuration authority.
- Whether the firmware/runtime closure is authenticated by exact reproducible
  local build or remains unresolved. Failure to authenticate is a truthful
  incomplete outcome, not permission to weaken provenance.

## Decisions this prerequisite must not make

- Any catalog family, component contract, graph, device, or instrument semantic
  change.
- Whether the mixed Crossfader binding is compatible, eligible, preferred, or
  selected for production.
- Any Task 009 lowering, serialization, source-map, diagnostic, generated-code,
  compile/link, artifact, resource, or evidence result.
- A general revision database, package manager, compiler IR, backend framework,
  Java replacement, firmware architecture, or direct C++ frontend.
- A rewrite of accepted v0 schemas or production records.
- Preference, filesystem, load order, dirty application state, or ambient
  environment as authority.
- Claims that source compilation or firmware reproduction establishes graph
  lowering, patch generation, patch link, device, real-time, or audible proof.
- Hardware access, firmware installation/modification, network installation,
  staging, commit, push, upload, or flash behavior.

## Stop conditions

Stop and report rather than broadening the task if:

- an exact required local Java/source/dependency/tool/firmware input is absent
  and closing it would require a download, installation, or upstream mutation;
- the pinned Java subset cannot be compiled reproducibly from exact local
  inputs;
- the later headless generation boundary cannot avoid mutable preference, GUI,
  or device authority without modifying pinned upstream source or implementing
  the Task 009 backend proof;
- the firmware/runtime closure cannot be reproduced or authenticated to the
  pinned source and exact tool inputs;
- fixed build outputs retain nondeterministic timestamps, paths, build IDs, or
  other uncontrolled identity that cannot be removed without source/tool
  changes outside this task;
- preserving the default Task 005-008 bytes requires changing their accepted
  semantic behavior rather than adding an explicit view boundary;
- the probe/evidence reference direction still creates an ownership or content-
  hash cycle; or
- any solution would select or promote the revision-1 binding before Task 009
  executes the accepted probe.

If a stop condition occurs, keep Task 009 proposed and incomplete. Retain only
bounded diagnostic evidence that does not make a false compatibility claim.

## Completion report requirements

On completion, update this prerequisite status to complete and report:

- pre-task preservation hashes and post-task equality checks;
- pinned source commit, tree/capsule identities, and exact source manifest hash;
- Java/Javac identities, every classpath member, compiled-class manifest, and
  two-root determinism result;
- explicit Java configuration boundary and proof that preference/GUI/device
  authority was absent from the bounded smoke check;
- every GNU Arm Embedded tool path outside canonical identity, version, and
  byte hash;
- firmware/runtime ELF/bin, ABI header, linker, library, symbol, flag, source,
  tool, and closure hashes plus two-root determinism result;
- accepted and prospective record-set IDs/hashes and all failure cases tested;
- probe/evidence schema IDs/hashes and the acyclic strictly-earlier revision
  fixture result;
- the corrected Task 009 prompt hash and confirmation that it remains not
  started;
- complete pre-existing and final test counts;
- explicit confirmation that no graph lowering, `.axp`, patch generation,
  patch compile/link, compatibility promotion, device, firmware action,
  real-time, audible, network, staging, commit, push, upload, or flash action
  occurred; and
- every remaining blocker that must still stop a later Task 009 run.

## Completion report

The prerequisite is complete. The Task 005-008 accepted view remains the
default, Task 009 remains proposed/not started, and no backend proof ran.

### Preservation and conflict reproduction

`evidence/task-009-prerequisite-v0/pre-task-preservation.json` records the
complete frozen record-set membership, three validator stdout streams, four
operation results, critical input bytes, initial repository state, test counts,
and the unchanged unresolved resolution trace. The accepted set pins 19 schemas
and 18 records.

`evidence/task-009-prerequisite-v0/preflight-conflict-report.json` records both
precondition failures. A temporary glob-enumerated build-request revision
changed `records.validate` from 4,324 bytes / SHA-256
`cb0735df54a0baade54c8cc16807a94771c1e7cbbc93a6710291084fcb656543`
to 5,293 bytes /
`7394396802532cd31cede1febded6fea24446ea6589917141557c2ad7b3ced1a`.
The accepted v0 production schemas reject the probe input as a build request
and the probe result as a build result; `evidence-claim-v0` cannot directly use
a conformance-probe-result input kind.

`evidence/task-009-prerequisite-v0/post-task-equality.json` proves the accepted
member hashes, validator stdout, operation result bytes, frozen production
files, and diagnostic ordering are unchanged. The historic validator SHA-256
values remain `254a77c5...`, `d295106d...`, and `7a898b34...`; the four operation
SHA-256 values remain `cb0735df...`, `88d5a4f5...`, `643a063d...`, and
`6def7986...`.

### Authenticated environment

The source capsule is derived from pinned commit
`08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, tree
`75b75dba0c3734a8a53464ac93cdc20ec7203bb6`. Two independent Git archives and
3,052-member manifests matched. Archive SHA-256 is
`2f2d6c9e985e5b8609c847a0b21ad7611e614e7dd2a0cb3c51d9b50a77a36f32`;
the retained source-member manifest SHA-256 is
`ce29a6ba66c38b31e13530b20a652a199987c7913afb7849ee2ad5c8875cf5ed`.
No tracked byte from the dirty upstream checkout was a source input, and the
checkout was not mutated.

The exact local Java runtime is OpenJDK 21.0.7. Portable execution paths are
`java-runtime/bin/java` and `java-runtime/bin/javac`; their byte SHA-256 values
are `b56748e35a76328d8a33e52d298930806484e39fa4a68a10d7a54debf51a9151`
and `7937caa17b49a97957cb0d2cc9ff18d148f4a20f98e49c8278cdc45b43a67ba4`.
Two clean Java builds produced 896 identical classes and 69 dependency JARs.
The classpath fingerprint is
`5ebd2f2b7f2aa6dc1d3d10a04edb5f2bbedd97cfb4372dab56dc22c778b17710`;
the classpath and runtime manifest SHA-256 values are `febc2ff3...` and
`775062e3...`. `build/built-jar.properties` was excluded because its temporary
root is nonsemantic.

The bridge-local `ExplicitCompileEnvironmentSmoke` compiled class SHA-256 is
`8947dfad1a3d689c5bf7700fdec9dfdd6f77753a5fea8bf41244fcfb6db56a47`;
its byte-identical output SHA-256 is
`efec1f13603756f312b5c5b7fe0035890bf51e602d39fa7c6451b08acbcaef01`.
It accepted explicit source, registry, target, firmware, locale, and encoding
identities while preference, GUI, device, upload, and flash authority remained
disabled. It loaded no Blend patch and generated no patch source.

The GNU Arm Embedded identity is 9-2020-q2-update, target triple
`arm-none-eabi`. Portable execution paths and byte SHA-256 values are:

| Tool | Byte SHA-256 |
| --- | --- |
| `arm-toolchain/bin/arm-none-eabi-gcc` | `475b81bfcec7787a411e3cb200150c1afb0ccd6d05ab0b1929bd933f2261328f` |
| `arm-toolchain/bin/arm-none-eabi-g++` | `69fe197c81592ae356650437e315966cd592b1015ecbda53edddcde494dcc296` |
| `arm-toolchain/bin/arm-none-eabi-as` | `58acc8c96d8fb361c4feb1e04ef73f496b33c788edb39d518a268821c591dfb0` |
| `arm-toolchain/bin/arm-none-eabi-ld` | `eaccfd337f8b955665168c8344d301e6441577a72739fc5a4116b9fdb072e67a` |
| `arm-toolchain/bin/arm-none-eabi-objcopy` | `744e6a4c7b65059f0f4497a01304e7ad1d1edda1defc2af75f28a6574fb77d29` |
| `arm-toolchain/bin/arm-none-eabi-objdump` | `d4d9369294ae583393fd9fdaa5ce039acf319c1e78623351f4864e04382b13c6` |
| `arm-toolchain/bin/arm-none-eabi-size` | `377e2d38ba57ab5ee5a8e2b6933debeea5cda4249fd1ebc5355deb77c6d365b8` |

The 1,741-member toolchain manifest SHA-256 is
`43e187053d3bd1a616c471991459e62832a8be9d0c455803438b5dd729ad393c`.
The final capture retains 227 canonicalized compiler/linker command lines,
exact GNU Make 3.81 identity, flags, linker inputs, and portable roots in
`firmware-build-commands.json`, SHA-256
`bb81bd052948220444830dcfcee7a77140386e8e33599b9a4eb95287a99a7742`.

Two clean firmware builds, repeated by two complete capture runs, produced
byte-identical retained results. Firmware bin SHA-256 is
`fd61a6a109a234d1c72e445a0542ab59c407a6896b9aafe2bfcbcadaf775e258`
(597,884 bytes) and exactly matches the installed bundles. Stripped link-ELF
SHA-256 is
`df65f2153eb999386cc1bc30b382cafeac63aea8495bf8cb4cdad1c01fca944b`
(823,980 bytes). The 1,474-member firmware input manifest SHA-256 is
`5383ff90ba44bc5540f48f3fffed38438f58ea81173feaea05608c94721d02aa`;
the stable 1,950-line symbol manifest SHA-256 is
`323589fbae0aa6600a417b14c3c764ff6c23c0eb41698e09172ced5419772366`.
Raw debug ELFs retained temporary DWARF paths and are explicitly excluded from
canonical identity. The two final complete capture directories were otherwise
byte-identical; the canonical capture summary SHA-256 is
`b47866a3d450dc4afbf8909bda3184a3f614d824d78220a497c48ef57ddc61d8`.

### Record sets and probe contracts

The default accepted record set is `schuss-record-set-000001` revision 1,
content hash
`sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6`.
The opt-in prerequisite set is `schuss-record-set-000002` revision 1, content
hash
`sha256:6f2855c384ef8bab88991a6cabdd8416c7f3c59a010eed0c6cda1ac08651ecaf`.
It is an exact parent-preserving superset with 25 schemas and 23 records.
Missing, extra, duplicate, unlisted, stale, hash-mismatched, and cross-view
membership cases fail closed. Existing validator commands and Task 008
operations use the accepted set by default and emit their original bytes.

The accepted new schema byte SHA-256 values are:

| Schema | Byte SHA-256 |
| --- | --- |
| `record-set-v0` | `34b625e8051f80e8adc4d14169db8c8f6bd2bdb2e0747d2bb7695f636c8b065d` |
| `prerequisite-environment-v0` | `580432cdd3da15e67e91688eff223f3d0900b063bbd865522978b5864eed0ed9` |
| `conformance-probe-procedure-v0` | `121e3b6704307ca417b96ea24370e39ff9f2606c6f69c610362f74d29cf6d91d` |
| `conformance-probe-input-v0` | `b1c0d0c8bb4c9de782a6d65118728c7ce46241daeb175cf720eb42e32fd3a070` |
| `conformance-probe-result-v0` | `5b26b39d54ae392d06c06decad3ce59441cbdfa68f556fc3401bf9847a03820f` |
| `conformance-probe-evidence-v0` | `81824b59c0395654de0c3acabc31c4a41300ff7fdd74d72aba1ffc4db69cc596` |

The environment, procedure, input, result, and evidence companion content
hashes are respectively
`sha256:8c2021ba5cbbcc1cbb63ca5957baeba71cdedf6a987d5f7091f609858539b3e7`,
`sha256:ca1fca9f18bedb533d192aa0e04f56a1b87ccd45188720f413e375025366cc73`,
`sha256:6b03c1504b5735ba82a307b69b712b761af9ba31dd262b4c0b013ae70dd47e13`,
`sha256:6c86cfbac58f4f9de0d3c7c2ee6b635eeae6aeac4120155fffaa122709f2773b`,
and
`sha256:c8e9b5f09d6891875fb0418602134dcf57bc57346f139e41c8217d535b248772`.
The input and result carry `candidate-under-test`, the fixture remains
`not-authorized`/`not-run`, all three ordered stages are `not-run`, and no
record grants production selection authority. Normal build request/result
schemas and `build.resolve` reject the probe. No executable production handler
exists.

The evidence companion points to the immutable result, binding revision 1, and
the procedure; the result has no evidence back-reference. The strictly-earlier
fixture passes with a prospective eligibility/binding revision 2 reference and
evidence closure naming the same implementation at revision 1. The fixture is
not a production record and performs no promotion.

### Commands, tests, and remaining boundary

The environment command was
`python3 tools/contracts/capture_task009_prerequisite_environment.py` with five
explicit local execution locators and a fresh output root. It uses only Git
archive, local Ant/Java, local GNU Make, and the exact local ARM tools. The final
gate ran the inventory and catalog unit tests and validators, all four contract
validators, `python3 -m unittest discover -s tools/contracts/tests`, and
`git diff --check`.

The final counts are 14 inventory tests, 6 catalog tests, and 72 contract tests
(58 frozen Task 005-008 tests plus 14 prerequisite tests). All passed. The
prerequisite validator stdout is 1,930 bytes with SHA-256
`3f8f3df84fd47ab51441ec6b3d30abc43fcfd18b2a69cffc6a508f5f0fe08a8b`.

The corrected Task 009 prompt remains `proposed; not started`; its SHA-256 is
`9cbfb7a01c5b83c64fbdebff653176147826dd9d66dc5f86c85d476324f39692`.
It now consumes the exact prerequisite set and requires a successor
prospective record set rather than ambient files in accepted directories.

No Schuss graph was lowered; no `.axp`, patch C++, patch object, linked patch
executable, production build result, compatibility promotion, device action,
firmware action, real-time procedure, audible procedure, network resolution,
installation, preference write, staging, commit, push, upload, or flash
occurred.

A later Task 009 run must still stop unless its preflight reproduces every
authenticated closure byte. The production resolver intentionally retains its
four unresolved reasons, no selected binding, and no backend invocation. Task
009 must execute the authorized probe and separately prove lowering, generated
source, and patch compile/link before any promotion; levels 3-8 remain
`not-run` here.
