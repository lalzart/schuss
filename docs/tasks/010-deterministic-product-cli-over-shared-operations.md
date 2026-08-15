# Task 010: Deterministic product CLI over shared operations

Status: complete. The user explicitly authorized Task 010 implementation on
2026-08-15. The complete acceptance suite and preservation gate passed on
2026-08-15; the exact evidence is recorded below.

Work in the Schuss repository. Work only on Task 010.

This is a bounded product-CLI task over the already accepted Task 008 operation
layer. It must make existing validation, inspection, resolution, and in-memory
transaction capabilities pleasant to use without creating a second source of
domain truth or presenting the one-slice Task 009 handler as a general build
system.

Before changing implementation, read completely:

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
- Tasks 005 through 009, including the complete Task 009 prerequisite,
  repair, execution, completion, and preservation evidence;
- `schemas/operation-request-v1.schema.json` and
  `schemas/operation-result-v1.schema.json`;
- `schemas/prerequisite/record-set-v0.schema.json`;
- `packages/schuss_core/control_plane.py` and its public API;
- `bin/schuss`, the existing Task 008 CLI tests, and all operation fixtures;
- accepted record set `schuss-record-set-000001` revision 1; and
- Task 009 successor record set `schuss-record-set-000003` revision 1.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Goal and why it exists

Create the first human-usable Schuss command-line interface as a deterministic,
thin projection over the shared Task 008 operations.

Task 008 already provides one authoritative in-process dispatcher and a
minimal canonical-JSON process adapter. Task 009 proves one exact graph can
reach ARM compile/link through a separately bounded handler. Users now need a
clear front door for the capabilities Schuss actually has, while GUI, CLI, and
future AI clients continue to share exactly the same operation semantics.

The product CLI must improve argument handling, reference lookup, help,
human-readable presentation, and shell completion. It must not add compiler,
graph, selection, persistence, or device behavior.

## Current boundary

The authoritative public operations remain exactly:

- `records.validate`;
- `graph.inspect`;
- `build.resolve`; and
- `graph.transact`.

`bin/schuss op --request <file-or-stdin> --json` is the accepted Task 008
machine boundary. Its request/result bytes, stdout/stderr separation, and exit
behavior are frozen inputs to this task.

The default operation context selects accepted record set
`schuss-record-set-000001` revision 1, content hash
`sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6`.
Its build request remains unresolved by design.

Task 009 successor record set `schuss-record-set-000003` revision 1, content
hash
`sha256:2f3706b7ccf08b59356bbfcadbdb37d0437b01857a9c50ba6e5d84e24a9b95c0`,
contains the promoted exact Blend closure and a successful `build.resolve`
result. It is an explicit opt-in record set, not a new ambient default.

The Task 009 executable handler remains a separate exact-slice adapter. It is
not registered as a general control-plane operation and must not become an
ergonomic `schuss build` command in this task.

## Required command surface

Implement exactly these ergonomic command families over the existing
operations:

```text
schuss validate [--record-set MANIFEST] [--json]
schuss graph inspect GRAPH_ID@REVISION [--record-set MANIFEST] [--json]
schuss graph transact GRAPH_ID@REVISION --edits FILE_OR_STDIN [--record-set MANIFEST] [--json]
schuss build resolve REQUEST_ID@REVISION [--record-set MANIFEST] [--json]
schuss completion {bash|zsh|fish}
```

The existing machine adapter remains supported and byte-compatible:

```text
schuss op --request REQUEST_FILE_OR_STDIN --json
```

No alias may omit `resolve` from `schuss build resolve`. A plain
`schuss build` command would misleadingly imply general executable backend
support and must be rejected with deterministic usage help.

## Command-to-operation mapping

Each ergonomic command constructs and dispatches exactly one existing
operation request:

| Product command | Shared operation |
| --- | --- |
| `schuss validate` | `records.validate` |
| `schuss graph inspect` | `graph.inspect` |
| `schuss graph transact` | `graph.transact` |
| `schuss build resolve` | `build.resolve` |

The product CLI owns parsing and presentation only. It must call the same
public dispatcher used by `schuss op`; it must not call validator internals,
resolver internals, the Task 009 handler, Java, ARM tools, or filesystem record
writers directly.

`schuss completion` is presentation-only. It emits a static completion script
for the fixed product grammar and invokes no domain operation.

## Exact reference shorthand

`GRAPH_ID@REVISION` and `REQUEST_ID@REVISION` are CLI locators, not new stable
Schuss identities and not semantic references stored in records.

The CLI must resolve a locator only inside the selected exact record-set
manifest. Resolution succeeds only when that manifest contains exactly one
member with the requested stable ID and revision. The CLI then constructs the
existing exact ID/revision/content-hash operation reference from that pinned
member.

The CLI must fail closed before dispatch when:

- the locator syntax is malformed;
- the requested ID/revision is absent;
- the member kind is wrong for the command;
- more than one member could satisfy the locator;
- the manifest, schema, raw byte, or semantic content hash is stale;
- the manifest is not an accepted parent-preserving record set; or
- any selected member uses an absolute or otherwise non-portable durable path.

There is no `latest`, `newest`, implicit revision, display-name lookup,
filesystem-order preference, or ambient scan. A manifest path is only an
explicit local locator; durable output identifies the selected record set by
stable ID, revision, and content hash, never by an absolute path.

## Record-set selection

Without `--record-set`, all ergonomic commands use the same frozen accepted
default as Task 008: `schuss-record-set-000001` revision 1.

`--record-set MANIFEST` explicitly selects another validated record set, such
as the Task 009 successor. The command must validate the complete manifest and
parent chain before locator resolution or dispatch. It must not search for a
manifest by name or infer the highest record-set revision.

Every human-readable result must identify the exact selected record-set ID,
revision, and content hash. JSON mode remains the authoritative operation
result and must expose the same context only where the existing operation
contract already provides it; Task 010 must not mutate the frozen result
schema merely to add presentation metadata.

## Output modes

### Canonical JSON

`--json` writes the exact canonical `schuss-operation-result-v1` bytes returned
by the shared dispatcher plus one LF. For the same selected context and exact
operation request, output must be byte-identical to the public in-process API
and to `schuss op`.

The CLI must not wrap, annotate, reorder, abbreviate, color, or otherwise
reshape JSON output. Operation diagnostics remain ordered exactly as the
dispatcher returns them.

### Human-readable output

Without `--json`, operation results use a concise deterministic plain-text
renderer. Human output must:

- state the operation and stable result status;
- identify the selected record-set ID, revision, and content hash;
- show exact graph, request, binding, target, and backend identities when they
  are present in the operation result;
- preserve diagnostic severity/code/subject/location order;
- preserve candidate, exclusion, unresolved, node, connection, and stage order
  wherever the domain result defines it;
- distinguish `unresolved`, `invalid`, `conflict`, and `success` rather than
  collapsing them into generic failure;
- describe `graph.transact` success as a proposed non-persisted revision and
  show `persistence_status: not-written`; and
- label structural, compile/link, connected-device, real-time, and audible
  evidence separately whenever evidence is displayed.

Human output must contain no ANSI color, terminal-control sequence, spinner,
clock time, random value, host name, user name, current working directory,
absolute path, temporary-root name, locale-dependent number, or terminal-width
dependent wrapping. Fixed labels, indentation, line endings, and ordering are
part of the tested Task 010 presentation contract.

Human output is presentation, not a new semantic record family. Machine
clients must use `--json`.

## Input, stdout, stderr, and exits

`--edits FILE_OR_STDIN` accepts either one explicit JSON file or `-` for stdin.
Its value must be exactly the existing ordered `graph.transact` edit array; the
CLI may not define a second edit language.

The product CLI retains the Task 008 exit classes:

- `0`: the dispatched operation returned `success`, or static help/completion
  emission succeeded;
- `1`: dispatch occurred and the operation returned any non-success status;
- `2`: product-command usage, locator parsing, record-set loading, edits-file
  I/O, or malformed JSON prevented dispatch; and
- `3`: an unexpected internal CLI failure occurred.

Dispatched operation results go to stdout in the selected output mode,
including domain-level non-success results. Usage, locator, manifest-loading,
file-I/O, malformed-input, and unexpected adapter diagnostics go only to
stderr. Stderr must never contaminate canonical JSON stdout.

Broken-pipe behavior must terminate quietly with a stable non-success process
result and no traceback. Keyboard interruption must not write records or emit
a traceback. Exact reachable behavior and exit values must be tested without
adding artificial domain failure paths.

## Help and completion

Root and subcommand `--help` output must document only the implemented grammar,
record-set behavior, output modes, and exit classes. Help text must not imply
general compilation, persistence, hardware connection, or upload capability.

`schuss completion bash`, `zsh`, and `fish` emit deterministic static scripts
to stdout. Completion must not inspect record sets, enumerate project records,
access the network, or edit shell profiles. It may complete only commands,
fixed options, and shell names; dynamic ID completion is deferred.

No progress UI or progress protocol is required. The four shared operations are
synchronous and bounded. Task 010 must document that progress presentation is
intentionally absent rather than invent progress events unsupported by the
operation layer.

## In scope

- Product command parsing for the exact command surface above.
- Exact ID/revision locator resolution through one validated record set.
- Explicit record-set selection while preserving the Task 008 default.
- One deterministic human renderer over existing operation results.
- Byte-identical canonical JSON passthrough through `--json`.
- Deterministic root/subcommand help and static Bash, Zsh, and Fish completion.
- Stable stdout, stderr, exit, broken-pipe, and interruption behavior.
- Packaging or entry-point changes strictly necessary to keep `bin/schuss` as
  the executable product boundary.
- Focused positive, negative, golden-output, fresh-process, and preservation
  tests.
- CLI documentation and a completion report.

## Out of scope

- New operation request/result schemas or changes to the meaning of the four
  Task 008 operations.
- A general `schuss build` command, backend execution command, or direct call
  into the Task 009 exact-slice handler.
- Graph lowering, compound elaboration, dependency planning, scheduling,
  optimization, `.axp` generation, Java generation, C++ generation, ARM
  compilation/linking, packaging, deployment, or artifact production.
- Graph or record persistence, project files, workspaces, autosave, undo/redo,
  locking, or revision publication. `graph.transact` remains an in-memory
  proposal with `persistence_status: not-written`.
- Catalog search, drawer browsing, Phase 4B/Task 011 family expansion, new
  component contracts, new implementation bindings, or new graph semantics.
- Interactive prompts, REPL, terminal UI, daemon, remote API, queue, streaming,
  cancellation service, or dynamic progress events.
- GUI, AI-specific prompting, MCP, editor integration, telemetry, analytics,
  self-update, package download, or network access.
- Device discovery, USB, firmware, upload, flash, SD-card writes, connected
  execution, real-time measurement, or listening tests.
- Dynamic shell completion from live repository or record-set contents.
- Color, themes, terminal-width adaptation, configuration files, environment
  variable configuration, or user preference storage.
- Mutation of accepted schemas, records, fixtures, evidence, upstream
  checkouts, hardware, or firmware.

## Inputs and deliverables

Inputs are:

- the accepted Task 008 dispatcher, operation envelopes, process adapter,
  fixtures, result bytes, exit behavior, and documentation;
- the accepted explicit record-set loader and manifests;
- the completed Task 009 successor closure and retained preservation hashes;
  and
- all accepted Task 005-009 validators and test baselines.

Deliverables are:

- this approved Task 010 contract;
- the ergonomic product command parser and fixed command grammar;
- exact record-set-based locator resolution;
- deterministic human and canonical-JSON output paths;
- deterministic help and Bash/Zsh/Fish completion output;
- focused CLI fixtures and tests;
- updated CLI/operation documentation; and
- a completion report containing exact preservation, output, test, and scope
  evidence.

## Acceptance tests

Task 010 is accepted only if automated tests prove all of the following:

1. All 96 pre-existing contract tests, all 14 inventory tests, all 6 catalog
   tests, and every existing validator pass before counting Task 010 tests.
2. Every accepted Task 005-009 schema, semantic record, record-set member,
   fixture, evidence file, retained artifact, validator summary, operation
   result, canonical byte stream, content hash, diagnostic code, and diagnostic
   order remains unchanged.
3. `schuss op --request <file-or-stdin> --json` retains its exact Task 008
   behavior and accepted output bytes.
4. Each ergonomic domain command constructs and dispatches exactly one of the
   four existing operations through the public dispatcher.
5. No product command imports or invokes domain-rule internals, the Task 009
   handler, Java, ARM tools, device code, or persistence code.
6. For every command, `--json`, direct public API, and `schuss op` return
   byte-identical canonical result bytes for the same exact request and record
   set.
7. The default command context is exactly accepted record set
   `schuss-record-set-000001` revision 1; no later record is selected merely
   because it exists in the repository.
8. Explicit selection of Task 009 successor record set
   `schuss-record-set-000003` revision 1 produces the same successful
   `build.resolve` value retained by Task 009, while performing no backend
   stage.
9. Locator resolution accepts only one exact ID/revision member of the correct
   kind and constructs its exact pinned content-hash reference.
10. Malformed, absent, wrong-kind, duplicate, stale, hash-mismatched, or
    unlisted locators and record-set members fail closed before dispatch.
11. No command implements an implicit revision, `latest` alias, display-name
    lookup, ambient record discovery, or filesystem-order selection.
12. Human output is byte-identical across at least two fresh processes,
    differently named working directories/output roots, supported test
    locales, terminal-width settings, and TTY/non-TTY capture.
13. Human output contains no ANSI escapes, timestamps, random IDs, absolute
    paths, temporary-root names, host/user values, locale-dependent values, or
    adaptive wrapping.
14. Human output preserves stable status distinctions, exact identities,
    diagnostic order, resolution reasons, and `not-written` transaction state
    without inventing evidence or simplifying uncertainty away.
15. JSON stdout contains only canonical operation-result bytes plus one LF;
    human stdout follows its golden presentation fixture; process diagnostics
    remain exclusively on stderr.
16. Exit classes 0, 1, 2, and 3 are stable at every reachable boundary, and
    broken-pipe and keyboard-interruption tests emit no traceback or partial
    persistent state.
17. `graph.transact` accepts only the existing edit-array language, applies no
    production write, and leaves the Blend graph byte-identical on success and
    failure.
18. Root help, every subcommand help page, and Bash/Zsh/Fish completion output
    are deterministic and contain no unsupported capability claim.
19. Completion emits to stdout only and never reads live records, accesses the
    network, or modifies a shell profile.
20. A plain `schuss build` invocation fails as usage rather than invoking the
    Task 009 handler or implying general compilation.
21. Full repository validation passes from a clean process after all Task 010
    tests, and `git diff --check` passes.
22. The completion report explicitly confirms that no new operation, semantic
    schema, compiler/backend behavior, persistent graph write, catalog
    expansion, network action, device action, firmware action, upload, flash,
    staging, commit, or push occurred without separate authorization.

Run the complete repository validation and test suite, not only Task 010 tests.
Fresh-process, fresh-working-directory, locale, TTY/non-TTY, and deterministic
golden-output checks are mandatory.

## Decisions Task 010 may make

- Exact Python module/file layout for the product parser and renderer.
- Exact deterministic wording, labels, indentation, and fixed wrapping width
  for human output and help.
- Stable Task 010-owned product-usage diagnostic codes and messages that occur
  before dispatch, without changing domain diagnostics.
- Exact grammar for `--edits -`, help invocation, and option placement so long
  as the required documented forms remain accepted and unambiguous.
- Static Bash, Zsh, and Fish completion implementation details.
- The smallest packaging/entry-point adjustment needed for `bin/schuss`.
- Test fixture filenames and organization consistent with repository
  conventions.

## Decisions Task 010 must not make

- New graph, component, family, binding, instrument, device, target, backend,
  build, artifact, resource, evidence, or operation semantics.
- Changes to accepted operation request/result shapes, canonicalization,
  status meaning, diagnostic ordering, or dispatcher ownership.
- A new client-specific operation or direct domain-rule code path.
- A general build-execution interface or product exposure of the one-slice
  Task 009 handler.
- Persistence format, project/workspace model, graph publication behavior, or
  production revision-writing policy.
- Implicit newest-revision selection, mutable aliases, preference/load-order
  authority, display-name identity, or ambient discovery.
- Compiler frontend, IR, optimizer, scheduler, code generator, backend
  registration, device protocol, or deployment behavior.
- GUI, AI, remote-service, telemetry, update, configuration, or user-preference
  architecture.
- Mutation of accepted records, record sets, retained evidence, upstream
  checkouts, hardware, or firmware.
- Staging, committing, pushing, publishing, uploading, or flashing without
  separate explicit approval.

## Stop conditions

Stop and report rather than broadening the task if:

- ergonomic commands cannot map one-to-one onto the accepted operations;
- exact locator resolution requires a mutable alias, ambient discovery, or
  operation-schema change;
- JSON byte identity requires changing the public dispatcher or result schema;
- deterministic human output cannot be achieved without machine-local,
  locale, terminal, clock, or random state;
- a useful command requires graph persistence, backend execution, a new domain
  operation, or Task 011 catalog/contract expansion;
- exposing successful Task 009 resolution would require invoking its exact
  handler or relabeling compile/link evidence as runtime evidence;
- completion requires live record enumeration or shell-profile mutation;
- packaging requires an unpinned network dependency or installation side
  effect; or
- any accepted Task 005-009 byte, hash, diagnostic, fixture, artifact, or
  evidence claim changes.

Partial CLI investigation may be documented, but Task 010 remains incomplete
until the complete deterministic product boundary passes.

## Completion report requirements

On completion, update the status to complete and record:

- the final exact command grammar and entry-point identity;
- every direct-API, `schuss op`, and ergonomic `--json` equality hash;
- every deterministic human, help, and completion golden-output hash;
- the complete locator and record-set positive/negative matrix;
- the exact stdout/stderr and exit-code matrix;
- fresh-process, working-directory, locale, TTY/non-TTY, broken-pipe, and
  interruption results;
- pre-existing and final test counts and all validator summaries;
- accepted Task 005-009 preservation hashes and post-task equality checks;
- the explicit default and Task 009 successor record-set outcomes;
- confirmation that `graph.transact` wrote nothing;
- confirmation that no plain `schuss build` execution path exists;
- separate evidence status for structural, compile/link, connected-device,
  real-time, and audible levels; and
- every remaining product, compiler, persistence, catalog, device, real-time,
  and audible proof gap with its earliest owning later task.

## Completion report: 2026-08-15

### Implemented boundary and exact grammar

Task 010 adds one deterministic product projection over the unchanged Task 008
dispatcher. Every ergonomic domain command constructs one existing request and
calls `dispatch_operation()` exactly once. Completion is static and dispatches
no domain operation. The implemented grammar is exactly:

```text
bin/schuss validate [--record-set MANIFEST] [--json]
bin/schuss graph inspect GRAPH_ID@REVISION [--record-set MANIFEST] [--json]
bin/schuss graph transact GRAPH_ID@REVISION --edits FILE_OR_STDIN [--record-set MANIFEST] [--json]
bin/schuss build resolve REQUEST_ID@REVISION [--record-set MANIFEST] [--json]
bin/schuss completion {bash|zsh|fish}
bin/schuss op --request REQUEST_FILE_OR_STDIN [--record-set MANIFEST] --json
```

The original Task 008 `op --request ... --json` form remains byte-compatible.
Its optional explicit record-set selector exists only so the same machine
adapter can be compared in the same pinned context; omission retains the
accepted default. There are no abbreviated options, implicit revisions,
aliases, `latest` selection, or plain build-execution form. `--help` is
available at the root and every implemented command node.

The executable identity is `bin/schuss`, 408 bytes, raw SHA-256
`ec7404558714d7577c82a3092c4117cbfdab4bfe86c0d8a70b5a2ac3779e71da`.
It imports `packages.schuss_core.cli.main`. The final parser/adapter module is
18,177 bytes, SHA-256
`5881a94e2f8a143d7cf99096d2a02b47aa9c528b860fe3045d4d7d023b615579`;
the locator/request/presentation module is 19,787 bytes, SHA-256
`2774816c1715283d9cb8201a214c015c8549c15068d38dd52c6b472d3035ed23`.

Task-local changes are limited to:

- `README.md`;
- `bin/schuss`;
- `docs/ARCHITECTURE.md`;
- `docs/OPERATION_CONTRACTS.md`;
- `docs/PROJECT_CONTEXT.md`;
- `docs/ROADMAP.md`;
- `docs/SCHEMA_STRATEGY.md`;
- `docs/TARGET_BACKEND_BUILD_CONTRACTS.md`;
- this Task 010 contract and completion report;
- `packages/schuss_core/cli.py`;
- `packages/schuss_core/product_cli.py`;
- `tools/contracts/README.md`;
- `tools/contracts/tests/fixtures/task010-cli-golden-hashes.json`; and
- `tools/contracts/tests/test_task010_cli.py`.

No operation or semantic schema, domain rule, accepted record, dispatcher,
compiler/backend handler, catalog record, or persistence implementation was
changed.

### Direct API, machine adapter, and product JSON equality

The canonical column excludes the process LF. The stream column is the exact
stdout from both `schuss op` and the ergonomic `--json` command, including its
single final LF. For every row, direct public API bytes plus LF, `schuss op`,
and ergonomic product output are byte-identical.

| Context and operation | Status | Canonical bytes / SHA-256 | Process bytes / SHA-256 | Equality |
| --- | --- | --- | --- | --- |
| accepted `000001@1` `records.validate` | `success` | 4,324 / `cb0735df54a0baade54c8cc16807a94771c1e7cbbc93a6710291084fcb656543` | 4,325 / `3e7f3695759558bdd9d4d625b9708778b5b778008ca5e5f3e1a42c004efa58d2` | API = `op` = product |
| accepted `000001@1` `graph.inspect` | `success` | 7,318 / `88d5a4f52f4d3bfc31ff361ebe3a8835860e7b5890e9c9791be21cd86c179ee1` | 7,319 / `1893cbf0b5fa122a9490b69acff897c792a22753344598c9fa3ef769b4390e0b` | API = `op` = product |
| accepted `000001@1` `graph.transact` no-op fixture | `success` | 3,964 / `6def7986739604e807b3b95e26513fe6a9a41cd1d827ea4e417809b9027c48b8` | 3,965 / `eca4265bca7246a52b770f278d979c122ac72459ae07e44630c4d2c7ce0a7031` | API = `op` = product |
| accepted `000001@1` `build.resolve` request r1 | `unresolved` | 1,367 / `643a063d1553ff000a4776fd2a4eb5b7d300c0ba34ccbb977f3babd78abf7de9` | 1,368 / `98c68e915ffdc5b6c025dad8af5449c93de65bbcb181dc9536d10aa1672ebeed` | API = `op` = product |
| successor `000003@1` `build.resolve` request r2 | `success` | 5,210 / `f19ee9b682983c20c2267a8492dd4b63d8ce5282c120513156f1aef8db75f8ec` | 5,211 / `4e39a787be715a552cecbc33793a7467c019ebf4c3f22c8ab052771978777799` | API = `op` = product |

The four default canonical hashes remain the frozen Task 008 operation hashes.
The successor result reports the existing Task 009 resolution value and
`executable_handler_status: absent`; no backend stage is invoked.

### Deterministic presentation goldens

The golden fixture is 2,483 bytes, SHA-256
`2373c57ed53676470eb077b79156c4f7f44b1e21c4f1f3d6bd98393e8c2fc146`.
Human outputs are:

| Output | Bytes | SHA-256 |
| --- | ---: | --- |
| accepted validation | 5,371 | `bb9171763459ac6c204afa3d1a510f09200b8f35e6003184afdfe31e0c998619` |
| accepted graph inspection | 1,050 | `663ae69bcea29725cae697730ad8012c1a9e771602aceca160d0193b8458153c` |
| accepted non-persisted transaction | 1,109 | `70c292e32dcae9476d0927f13d0bfeb0850ad96568f747c36bb213f18ef57bc3` |
| accepted unresolved build resolution | 1,933 | `36e1d353e7d57cdbbcdb71326a0485a7d9fd6ba586e398fd164111b3cb7c1125` |
| successor successful build resolution | 2,652 | `8f9a7c5352c64dc7b4fbcc5f80458d4af03ef12fcf17476f4ebbe12ff4e047fa` |

Help outputs are fixed at a maximum of 80 bytes per line and do not vary with
the ambient `COLUMNS` value:

| Help page | Bytes | SHA-256 |
| --- | ---: | --- |
| root | 973 | `a4b5842627d24cd5b62682737fa4485b37b6e18d8cec1a1fb77c39298b7ed1bb` |
| `validate` | 642 | `dbe5bc7cacda777a9f13c83413d938c1ed6551fdac2a1c6be49e00282eb74419` |
| `graph` | 425 | `2f4fc0aad233ce821c7768fa2f9a229611cec5da2725a4e4b296c2e378f69739` |
| `graph inspect` | 743 | `7852c9a9c35e22290c4fe870a9184a4a52a846dd4607367878cebf2d5ee666af` |
| `graph transact` | 911 | `645127895ea20e412dc1be9e5f7a0a89203d432b56826c3d2c1349d9868eb7e3` |
| `build` | 398 | `2fbc0ab3be00cc5a142557f48e710db20b4b7b5ec0ec3087a1a09e2246ce8c89` |
| `build resolve` | 744 | `ba3e2657382b84b67047c3f90e06254def35348b8590bc3bfd3ab35309ad2447` |
| `completion` | 353 | `9aff46f98102c24a96dbd2062803859db326a6ce2813f1a3d93a8bd8eca66bd8` |
| `op` | 577 | `7e7939870dc32ed82f05cf4825ec876f0a2bb9a4ec619cbbe48e42ce27dbb138` |

Static completion outputs are:

| Shell | Bytes | SHA-256 |
| --- | ---: | --- |
| Bash | 1,021 | `5ebee4376bea760ad09e2f171b62eb8178c2a9872f5dcc02f6d52294202393e9` |
| Zsh | 1,044 | `4ae2913d2cce69c50d7fc7d77384dc8458e05fc7eba9aa0237aaa26cc4189dcb` |
| Fish | 941 | `ca5610ec9417ae0e07cce6e5103b3d6c407424f162ad87b8ada7418846ec4f8f` |

Bash and Zsh scripts pass their installed shells' syntax checks. Fish was not
installed, so its fixed bytes and grammar are covered by the golden/static
source tests rather than a local Fish parser. Completion calls no context
loader, contains no record IDs or repository paths, performs no network
access, and does not modify a shell profile.

### Locator and record-set matrix

Positive locator cases resolve exactly one pinned member and construct its
existing content-hash reference:

- `schuss-graph-000001@1` in the accepted set resolves and inspects
  successfully;
- `schuss-build-request-000001@1` resolves in the accepted set and truthfully
  returns `unresolved`;
- `schuss-build-request-000001@2` is absent from the default but resolves and
  succeeds only when successor set `000003@1` is explicitly selected; and
- explicit selection of accepted set `000001@1` produces the same validation
  bytes as omission of `--record-set`.

The locator negatives are missing `@revision`, revision zero, leading-zero
revision, `@latest`, display-name syntax, absent stable ID, graph/request
wrong-kind use, and a duplicated exact in-memory member. Every case exits 2,
writes no stdout, emits a `CLI_LOCATOR_*` diagnostic on stderr, and prevents
dispatch. No ambient file ordering or later record can affect selection.

Positive record-set cases are the frozen accepted root and the explicit
parent-preserving Task 009 successor. The negative manifest/member matrix is:

- duplicate record member;
- stale raw record byte hash;
- stale schema byte hash;
- stale semantic record content hash;
- a member omitted from the manifest while still present in an enforced
  directory;
- a missing member path;
- an absolute member path;
- a traversal/non-portable member path;
- wrong parent content hash;
- a prospective set falsely relabeled as an accepted root;
- stale manifest content hash;
- missing manifest file; and
- malformed manifest JSON.

Every negative is rejected before locator resolution/dispatch with exit 2,
empty stdout, and a deterministic record-set/input diagnostic. The selected
manifest and its complete recursive parent chain must resolve exactly once and
end at frozen accepted set `000001@1`; a manifest filename or higher revision
has no authority.

### Input, stdout, stderr, and exit matrix

`--edits` file and stdin inputs produce identical operation bytes. A missing
file, non-array JSON, malformed JSON, and restricted-JSON floating value fail
before dispatch with `CLI_EDITS_*`, exit 2, empty stdout, and diagnostics only
on stderr. Empty or unsupported edit arrays are well-formed operation inputs;
they dispatch, return canonical/human `invalid` results on stdout, and exit 1.

| Boundary | Exit | Stdout | Stderr |
| --- | ---: | --- | --- |
| operation `success` | 0 | selected human result or canonical result plus one LF | empty |
| help or static completion success | 0 | exact deterministic help/script | empty |
| dispatched `unresolved`, `invalid`, or `conflict` | 1 | complete selected operation result | empty |
| quiet broken pipe | 1 | consumer-controlled partial/closed stream | empty; no traceback |
| keyboard interruption | 1 | empty in the tested pre-dispatch path | exactly `schuss: interrupted` plus LF; no traceback |
| usage, locator, record-set, edits I/O, or malformed input | 2 | empty | deterministic adapter diagnostic/help |
| injected unexpected `RuntimeError` | 3 | empty | `schuss: internal operation failure: RuntimeError: fixture internal failure` plus LF |

The no-op transaction human result states
`proposal_status: proposed-non-persisted` and
`persistence_status: not-written`. Success, invalid-operation, conflict, and
interruption tests all leave
`contracts/graphs/blend-crossfader-v0.json` byte-identical at SHA-256
`c21b9b2d79a5a6e10d8cd2dd5ca4959ff1556949fd1a1c411d0323ab605c4c15`.
No graph, manifest, or semantic record writer is reachable from the product
modules.

Two fresh subprocesses used differently named working directories and
redirected output roots, locales `C` and `de_DE.UTF-8`, widths 31 and 211, and
different host/user environment values. Their graph-inspection output was
byte-identical. Raw PTY and pipe capture were byte-identical. All five human
goldens contain no ANSI/control output, CR, timestamp, UUID, repository or
temporary absolute path, host/user value, locale-dependent value, or adaptive
wrapping. Help bytes are identical at widths 25 and 240. Broken-output and
injected-interruption paths both return 1 without a traceback or persistent
state.

### Tests and validator summaries

The pre-change gate passed all 96 existing contract tests, 14 inventory tests,
6 catalog tests, and every validator. The final clean-process gate passed:

- 117 contract tests: the preserved 96 plus 21 Task 010 tests;
- 14 inventory tests;
- 6 catalog tests;
- Python byte compilation for the CLI, renderer, and focused tests; and
- `git diff --check`.

Every validator exited 0 with empty stderr. Exact stdout evidence is:

| Validator | Bytes | SHA-256 | Summary |
| --- | ---: | --- | --- |
| raw inventory | 41 | `3a9ba2256592972c3e104b21b821d9befa9ac2c75c8f69af63020b4765271e80` | `ok`; 4,209 files, 2 retained issues |
| resolved inventory | 62 | `bb435d07670ccf4ce7dad5182a75ad9bc2c18dedb5c0b184ce9d6cca3691e738` | `ok`; 3,602 objects, 1,157 graphs, 3,180 issues |
| Phase 3 review | 103 | `faf90cb359effe3b24f2c68ca66086d1acee813acf0ceacb7c3218e7e9ae62f4` | `ok`; 20 issue classes, 157 overload groups, 805 partial graphs, 103 zombie groups |
| Phase 4A semantic catalog | 1,725 | `8d21352c7265a50a93646f93f9696e4b02ebcfbab3443da53a2cc47c8fc34238` | 26 families, 38 implementations; all required pilot cases present |
| device/instrument | 684 | `254a77c534c911da759a21e438544b4b0e69e16093307e0fc269a0857b6d3af6` | `valid-with-deferred-graph` |
| component/graph | 1,069 | `d295106d38cdf9075a85d9e1a803b5df23e3ffbbe934dceb3cec9194b59ce6af` | `valid-with-historical-deferred` |
| target/backend/build | 1,964 | `7a898b3409e5ad7ef02eab1246f87756cc2af7cbd512d72f9a5eb43b1573a3a2` | `valid`; accepted request remains unresolved |
| Task 009 prerequisite | 1,930 | `3f8f3df84fd47ab51441ec6b3d30abc43fcfd18b2a69cffc6a508f5f0fe08a8b` | `valid`; retained prerequisite probe remains not authorized/not run |
| Task 009 retained `--check` | 458 | `fef638fd5bc9e2e9d4cc571ed557f6924d0db21dcb8cf112856f43c64e353771` | `valid`; 55 records, 14 artifacts, levels 1-5 passed and 6-8 not run |

The focused Task 010 test file is 36,964 bytes, SHA-256
`f08d6a51b8f378f3c27506dcf765bb1d4ccd184775cbdc3536082eb3ae065de2`.
It covers request mapping, dispatcher-call count, all equality streams,
human/help/completion goldens, locator/record-set/input negatives, output and
exit separation, deterministic environments, non-persistence, forbidden
imports, and Task 005-009 preservation.

### Accepted preservation and explicit outcomes

The accepted/prerequisite/successor manifest raw hashes remain, respectively:

- `389b82834f41e4c8b1c2058cb7a9eccba348f7922f5de6abaeadb42bfd00e7a8`;
- `1ba2baf4affe2d0e1c08ec34f54659c89e4989d184df7421cd94c8bc72507553`;
  and
- `0ca4ac25d76605c595ac56b68b4cd78b949467c057d9b97b56bdc96c3be6cf8a`.

Their semantic identities remain `schuss-record-set-000001@1`
`sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6`,
`000002@1`
`sha256:6f2855c384ef8bab88991a6cabdd8416c7f3c59a010eed0c6cda1ac08651ecaf`,
and `000003@1`
`sha256:2f3706b7ccf08b59356bbfcadbdb37d0437b01857a9c50ba6e5d84e24a9b95c0`.
The frozen Task 008 request fixture raw hash remains
`cb21063005fdb18abd4362f3537b7286eb94db23d2c1d2963eac247616fac99a`.
The retained Task 009 post-task equality record remains SHA-256
`9a4f470f9570bbcec72b25d6d7e47de985621f76c4ae64c5ed71b6c56ab0ff11`.

A sorted portable-path/raw-SHA-256 fingerprint over all successor schema and
record members, all three Task 009 evidence trees, all three record-set
manifests, and the Task 008 operation fixture covers 130 files and 3,042,060
bytes. Current bytes and `HEAD` both produce
`a28e45ac19efb79816eb1d5c364661345e89e45037590aacc1c9a10be001a7b9`.
`git diff --quiet HEAD` over the same protected set succeeds. The three
accepted contract-validator hashes and four accepted Task 008 canonical
operation hashes shown above also remain unchanged, including diagnostic order.

The ambient default is still only accepted set `000001@1`: request r1 returns
`unresolved`, and request r2 is a pre-dispatch locator failure. Explicit
successor set `000003@1` identifies itself by stable reference and content
hash, resolves request r2 successfully, and reports that the executable
handler is absent. Neither path executes Task 009. The product modules do not
import domain-rule internals, Java/ARM/process tools, `task009_backend`, or
`run_task009`. A plain `schuss build` is a deterministic exit-2 usage failure;
only `schuss build resolve` exists.

### Evidence levels and remaining proof gaps

Task 010 creates no build-evidence claim. Structural/schema and exact graph
resolution evidence remain independently reported by the accepted validators.
Task 009's retained successor evidence, not this CLI task, establishes levels
1-5 only for the exact Blend slice. Task 010 did not lower, generate, compile,
link, connect, execute, measure, or listen. Levels 6 connected-device, 7
real-time/resource, and 8 audible/listening remain explicitly `not-run`; a
level-5 retained ELF does not imply any of them.

| Remaining gap | Earliest later roadmap owner |
| --- | --- |
| Complete reviewed-core catalog expansion, real family contracts/bindings, catalog search data, and dynamic ID discovery | Task 011 / Phase 4B |
| Object drawer, transparent graph canvas, user-facing graph editing, and GUI use of the shared operations | Task 012 |
| Durable project/workspace format, save/publication, locking, undo/redo, and persistent graph transactions | Task 012 is the earliest product dependency, but it requires its own explicit persistence contract before any write |
| General graph/backend execution, direct lowering, scheduling, source generation, and product progress/execution semantics | Task 013 for the direct Schuss frontend; any general legacy-execution product surface remains a separately authorized follow-on |
| Complete Gills parameter/control mapping, connected-device execution, and device-specific runtime integration | Task 014 |
| Real-time timing, CPU, memory, I/O, load, and stability measurements at evidence level 7 | Task 014 is the earliest Gills validation owner and must define an explicit procedure |
| Audible correctness, stability, and musical/listening claims at evidence level 8 | Task 014 is the earliest Gills validation owner and must define an explicit listening procedure |
| Sampling and durable asset-management behavior | Task 015 |
| Additional compute targets and physical devices | Task 016 |
| Package distribution, configuration/preferences, dynamic completion, AI/remote clients, and any generalized deployment/upload interface | No accepted task yet; each requires a new bounded contract after its dependencies |

No network action, package installation, upstream mutation, device access,
firmware action, SD-card write, upload, flash, stage, commit, push, or publish
occurred. No operation, semantic schema, compiler/backend behavior, persistent
write, or catalog expansion was added. Task 010 stops at deterministic parsing,
exact lookup, one shared dispatch, and presentation as authorized.
