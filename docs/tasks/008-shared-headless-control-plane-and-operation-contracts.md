# Task 008: Shared headless control plane and operation contracts

Status: complete. Accepted as the shared headless control-plane gate on
2026-08-15; no compiler lowering or CLI-product work was performed.

Work in the Schuss repository. Work only on Task 008.

This is a bounded validator-consolidation and headless-operation implementation
task. It must create the shared control-plane gate consumed by later GUI, CLI,
AI, and backend work without performing compiler lowering or creating build
artifacts.

Before changing implementation, read completely:

- `AGENTS.md`;
- `README.md`;
- `docs/PROJECT_CONTEXT.md`;
- `docs/ARCHITECTURE.md`;
- `docs/SCHEMA_STRATEGY.md`;
- `docs/COMPILER_STRATEGY.md`;
- `docs/LEGACY_STRATEGY.md`;
- `docs/ROADMAP.md`;
- Tasks 004 through 007 and their completion evidence;
- the Task 005, Task 006, and Task 007 schemas, production records,
  validators, fixtures, and tests; and
- all currently accepted operation, graph, target, backend, build-request,
  diagnostic, and canonicalization contracts.

If this task conflicts with an accepted decision, stop and report the conflict
instead of silently changing the architecture.

## Goal and why it exists

Create one language-neutral, deterministic, versioned operation boundary over
the accepted Schuss records, with a pure in-process dispatcher shared by every
client and one minimal executable process adapter.

This gate exists so GUI, CLI, AI, and later backend integration cannot acquire
different graph mutation, validation, inspection, or build-resolution truth.
It also removes the validator dependency cycle left by incremental Tasks
005-007 before Task 009 introduces executable compiler work.

## In scope

- Consolidation of genuinely shared validator mechanisms into one shared
  validator core.
- Three sibling domain-rule modules and one aggregate validator with the exact
  dependency direction fixed below.
- Preservation-compatible entry points for the existing Task 005, Task 006,
  and Task 007 validators.
- One closed, versioned, language-neutral JSON operation request envelope and
  one closed, versioned canonical result envelope.
- One public in-process operation dispatcher implementing exactly:
  `records.validate`, `graph.inspect`, `build.resolve`, and `graph.transact`.
- Pure, deterministic, atomic graph transactions limited to add/remove node,
  add/remove connection, set node parameter, and set node attribute.
- A read-only backend invocation seam that can receive an accepted build
  request after validation and resolution, but has no executable handler.
- One minimal machine-oriented executable process adapter over the same public
  dispatcher, sufficient for `schuss op --request <file-or-stdin> --json`.
- Focused positive and negative fixtures and new Task 008 tests.
- Documentation of the operation contract, transaction conflict rules, exit
  behavior, backend seam, and all work deferred to Tasks 009 and 010.

## Out of scope

- Graph lowering, transparent-compound elaboration as executable compiler
  work, dependency planning as executable compiler work, scheduling,
  optimization, code generation, or source-map production.
- Generation of `.axp`, legacy XML, C++, object files, linked images,
  packages, production build artifacts, or deployment media.
- Java or ARM tool invocation, compilation, linking, firmware interaction,
  hardware access, upload, flash, SD-card writes, device execution, resource
  measurement, or listening tests.
- An executable backend handler or any Task 009 compiler implementation.
- Ergonomic CLI subcommands, human-readable formatting, convenient flags,
  completion, progress presentation, terminal UI, or final CLI UX; Task 010
  owns those concerns.
- GUI implementation, graph canvas, object browser, AI prompting behavior,
  remote transports, queues, streaming, progress events, or cancellation.
- New production component, graph, instrument, device, target, backend,
  eligibility, build-request, build-result, artifact, or evidence records.
- Mutation of the production Blend graph or any accepted Task 005-007 record.
- Changes to existing diagnostic meaning, ordering, canonicalization, record
  hashes, retained semantics, or accepted selection policy.

## Inputs and frozen boundaries

Treat all accepted Task 005, Task 006, and Task 007 schemas and production
records as immutable inputs. In particular, Task 008 must not change the Task
007 build-request bytes or hashes and must not write a proposed graph returned
by `graph.transact` to the production record tree.

Before validator refactoring, preserve the current regression baseline:

- all 42 pre-existing contract tests pass;
- device/instrument validator canonical stdout SHA-256 is
  `254a77c534c911da759a21e438544b4b0e69e16093307e0fc269a0857b6d3af6`;
- component/graph validator canonical stdout SHA-256 is
  `d295106d38cdf9075a85d9e1a803b5df23e3ffbbe934dceb3cec9194b59ce6af`;
- target/backend/build validator canonical stdout SHA-256 is
  `7a898b3409e5ad7ef02eab1246f87756cc2af7cbd512d72f9a5eb43b1573a3a2`;
  and
- all existing summaries, canonical bytes, content hashes, diagnostic codes,
  diagnostic ordering, and retained semantic records remain byte-identical.

Task 008 adds tests; 42 is the pre-existing baseline, not the final count.

## Required validator architecture

The final validator dependency direction is exactly:

```text
shared validator core
    |-- device/instrument rules
    |-- component/graph rules
    `-- target/backend/build rules

aggregate validator -> composes all three rule modules
```

No domain-rule module may import another domain-rule module. Each may import
only the shared validator core plus Python standard-library modules. The
aggregate validator owns cross-domain composition and exact-reference closure.
Compatibility command wrappers may delegate to the public core, domain, and
aggregate APIs, but must not become a second source of rule truth.

Move only genuinely shared mechanisms into the core: restricted JSON loading,
schema mechanics, canonicalization, hashing, portable value checks, common
diagnostic representation/order support, and genuinely domain-neutral registry
or exact-reference primitives. Device, instrument, component, graph, target,
backend, build, eligibility, and evidence policies remain in their respective
domain modules even when moving a policy into the core would shorten code.

## Operation envelope

The request and result envelopes must be closed, versioned JSON records under
`schuss-operation-request-v1` and `schuss-operation-result-v1`. They must use
the accepted `schuss-canonical-json-v1` restricted value space and canonical
serialization. The request identifies exactly one operation and contains only
that operation's input payload. The result repeats the operation identity and
contains a stable status, operation-specific value on success, and ordered
structured diagnostics. It contains no clock time, random identifier,
absolute path, ambient environment value, or client-specific presentation.

Malformed JSON is a process-input failure. A parsed request that violates the
operation schema, names an unsupported operation, conflicts, or fails a domain
rule produces a canonical operation result envelope through the dispatcher.

## Required pure operations

### `records.validate`

Validate an explicitly supplied record closure through the aggregate
validator. Results must be independent of input enumeration order and report
the same ordered structured diagnostics as the accepted domain rules. The
operation does not discover, rewrite, or persist records.

### `graph.inspect`

Resolve and return a deterministic, target-independent inspection of one exact
graph and its exact component-contract closure. Inspection exposes public
graph structure and contract provenance without selecting implementations,
lowering the graph, or mutating any record.

### `build.resolve`

Accept one exact Task 007 build request and resolve it through the accepted
target/backend/build rules. Its result must report the complete deterministic
candidate, exclusion, unresolved, and selection trace. An unresolved required
fact or uncertainty blocks selection; the resolver must never select through
uncertainty.

When resolution accepts a request, the result may construct the input to the
Task 009 backend invocation seam. The seam contains the accepted exact request
and resolution only. It stops before lowering, has no executable backend
handler in Task 008, emits no artifact, and cannot invoke Java, ARM tools, or
hardware.

### `graph.transact`

Apply a finite ordered transaction to an explicitly supplied graph value in
memory. Supported edits are limited to:

- add node;
- remove node;
- add connection;
- remove connection;
- set node parameter; and
- set node attribute.

The request supplies the exact base graph content hash. A stale base hash is a
conflict. The operation applies edits to an isolated copy, recalculates the
candidate record hash, and runs the complete Task 006 graph and
component-contract validation closure. Success returns one deterministic
proposed graph record. Any edit or validation failure rejects the whole
transaction and returns no partial or candidate graph. The operation performs
no filesystem write and tests must use isolated fixtures rather than mutate the
production Blend graph.

## Backend invocation seam

Define one language-neutral, immutable preparation value for later Task 009
backend invocation. It contains the exact accepted build request, selected
binding resolution, target/backend identities, and the complete resolution
trace required by Task 009. It exposes no callable executable backend handler
in Task 008. The only permitted Task 008 outcome is equivalent to
`ready-for-backend-invocation`; all lowering, tools, artifacts, and execution
remain absent.

## Minimal process adapter

Provide one real executable boundary using the same in-process dispatcher:

```text
schuss op --request <file-or-stdin> --json
```

`--request -` reads stdin. `--json` selects the only Task 008 output mode and
is required. The adapter must not reinterpret or reshape a dispatcher result.
It writes the exact canonical result bytes plus one newline to stdout.
Usage, file-I/O, malformed-JSON, and unexpected process diagnostics go only to
stderr and never contaminate canonical stdout.

Stable exit behavior is:

- `0`: the dispatcher returned status `success`;
- `1`: a parsed request was dispatched and returned any non-success operation
  status;
- `2`: command usage, request-file I/O, or malformed JSON prevented dispatch;
  and
- `3`: an unexpected internal process-adapter failure occurred.

Task 010 may build ergonomic commands over this boundary but must not fork its
operation semantics.

## Inputs and deliverables

Inputs are the accepted Task 005-007 record families, production closures,
canonical profile, validators, fixtures, and exact Task 007 resolution policy.

Deliverables are:

- this approved Task 008 contract;
- the shared validator core, three sibling rule modules, aggregate validator,
  and preservation-compatible existing command entry points;
- versioned operation request/result schemas and documentation;
- the public dispatcher and four pure operations;
- the non-executable Task 009 backend invocation seam;
- the minimal `schuss op` executable adapter;
- isolated Task 008 fixtures and tests; and
- a completion report recording regression and acceptance evidence.

## Acceptance tests

Task 008 is accepted only if automated tests prove all of the following:

1. The dependency graph has the required one-way shape and no domain-rule
   module imports another domain-rule module.
2. All 42 pre-existing tests still pass before counting any Task 008 tests.
3. Existing validator stdout bytes and SHA-256 values, record canonical bytes,
   record hashes, diagnostic codes, diagnostic order, summaries, and retained
   semantic records are unchanged.
4. Request/result schemas are closed, versioned, canonical, language-neutral,
   and reject unsupported members and restricted-value violations.
5. Direct API and executable CLI calls return byte-identical canonical result
   envelopes for the same request.
6. Results are independent of filesystem directory order and supplied record,
   contract, and transaction-source enumeration order wherever order is not
   semantic.
7. Every operation leaves the filesystem and all production records unchanged.
8. `records.validate` composes all three rule families through the aggregate
   validator and retains stable ordered diagnostics.
9. `graph.inspect` resolves exact contract closure without implementation or
   backend selection.
10. `build.resolve` returns the complete candidate, exclusion, unresolved, and
    selection trace, and never selects through unresolved uncertainty.
11. Task 007 build-request records remain byte-identical.
12. Successful `build.resolve` results expose an accepted request to the
    defined Task 009 backend invocation seam; the seam stops before lowering
    and has no executable backend handler.
13. `graph.transact` supports only the six approved edit forms, rejects stale
    base hashes, validates the complete Task 006 closure, is atomic, returns no
    partial graph on failure, and is deterministic on success.
14. Transaction tests use non-production copies or fixtures and do not mutate
    the production Blend graph.
15. CLI stdout is canonical dispatcher output only; process diagnostics remain
    on stderr; exit codes 0, 1, 2, and 3 are stable and tested at their reachable
    boundaries without adding an artificial production failure path.
16. No `.axp`, Java/ARM invocation, compile/link, hardware access, production
    build artifact, Task 009 compiler work, or Task 010 CLI-product work occurs.

Run the complete repository validation and test suite, not only the new Task
008 tests. Fresh-process determinism checks are required.

## Decisions Task 008 may make

- Exact module and schema filenames consistent with repository conventions.
- The smallest closed request/result payload shapes for the four fixed
  operations.
- Stable diagnostic codes and non-success status names newly owned by the
  operation layer, provided existing domain diagnostics are not changed.
- The in-memory registry representation and public dispatcher function shape.
- The non-executable backend invocation preparation value.
- Minimal executable location and packaging needed for the required process
  boundary.

## Decisions Task 008 must not make

- New component, graph, device, instrument, target, backend, capability,
  eligibility, or build semantics.
- Compiler IR, lowering order, code-generation behavior, source maps,
  dependency execution, backend handler behavior, artifact formats, or build
  execution policy.
- Ksoloti Java, ARM, firmware, ABI, processor, toolchain, or backend identities
  as constants in a reusable record-family schema; production records may use
  controlled stable values or vocabulary references.
- GUI/AI behavior or the final CLI product design.
- Implicit compatibility, fallback, selection through uncertainty, ambient
  discovery, or filesystem-order precedence.
- Mutation of accepted production records, upstream checkouts, or hardware.
- Staging, committing, pushing, uploading, or flashing without separate
  explicit approval.

## Completion report requirements

On completion, update this status to complete and record:

- validator-module dependency evidence;
- pre-existing and final test counts;
- preservation hashes and immutable production-tree checks;
- operation and CLI determinism evidence;
- graph transaction atomicity and stale-base evidence;
- full build-resolution trace and unresolved-blocking evidence;
- backend-seam stop point and absence of an executable handler;
- explicit confirmation that no lowering, `.axp`, Java/ARM tool, compile/link,
  hardware, production artifact, Task 009, or Task 010 product work occurred;
  and
- all remaining proof gaps.

## Completion evidence

### Validator architecture and preservation

`tools/contracts/validator_core.py` now owns only shared restricted-JSON,
schema, canonicalization, hashing, portability, diagnostic, exact-reference,
registry, and domain-neutral cycle mechanisms. The sibling modules
`device_instrument_rules.py`, `component_graph_rules.py`, and
`target_backend_build_rules.py` each import only that core plus the Python
standard library. `aggregate_validator.py` imports and composes all three.
Static import tests enforce this direction.

All 42 pre-existing contract tests passed after consolidation. Task 008 adds
16 tests, for a final contract-suite count of 58. The three accepted validator
stdout byte lengths and SHA-256 values remain exactly:

- device/instrument: 684 bytes,
  `254a77c534c911da759a21e438544b4b0e69e16093307e0fc269a0857b6d3af6`;
- component/graph: 1069 bytes,
  `d295106d38cdf9075a85d9e1a803b5df23e3ffbbe934dceb3cec9194b59ce6af`;
  and
- target/backend/build: 1964 bytes,
  `7a898b3409e5ad7ef02eab1246f87756cc2af7cbd512d72f9a5eb43b1573a3a2`.

The production Task 007 build-request file remains SHA-256
`43f9b680116f2ac17e2aa2b164e54bd0b9bcc26582ca5272c14ca620836bac6e`
with unchanged record content hash
`sha256:0ba7e74977ac7ebcf50cb73826c349040d998541f688bb32cbedf88140259e95`.
The production Blend graph file remains SHA-256
`c21b9b2d79a5a6e10d8cd2dd5ca4959ff1556949fd1a1c411d0323ab605c4c15`.

### Operation and process evidence

`packages/schuss_core/control_plane.py` implements the one public dispatcher
for `records.validate`, `graph.inspect`, `build.resolve`, and
`graph.transact`. `schemas/operation-request-v1.schema.json` and
`schemas/operation-result-v1.schema.json` define their versioned envelopes.
Tests prove direct API and `bin/schuss op --request ... --json` results are
byte-identical, fresh calls are deterministic, record and filesystem
enumeration order does not affect results, and operations leave both the
in-memory snapshot and production files unchanged.

The minimal process adapter writes only canonical result JSON to stdout. Tests
cover exit 0 for success, exit 1 for a dispatched non-success result, exit 2
for usage and malformed input, and exit 3 for an unexpected adapter failure.

### Resolution, transaction, and backend-seam evidence

Production `build.resolve` returns the complete Task 007 candidate trace as
`unresolved`, including empty exclusion reasons, all unresolved reasons, no
selected binding, and no backend invocation. A coherent non-production
accepted fixture produces a selected trace and the versioned Task 009 data
seam. That seam carries the accepted request and selected bindings, completes
only `implementation-resolution`, reports `backend-lowering` as `not-run`, and
reports its executable handler as `absent`.

Graph transaction tests prove deterministic next-revision results, all six
bounded edit forms, stale-base conflict rejection, full Task 006 validation,
atomic failure, and absence of a partial graph on failure. They use only the
non-production Task 008 fixture context. Successful proposals report
`persistence_status: not-written`; the production Blend graph is unchanged.

### Full gate and remaining proof gaps

The full repository gate passed:

- 14 inventory tests;
- 6 semantic-catalog tests;
- raw, resolved, Phase 3 review, and Phase 4A validators;
- all three contract validators; and
- 58 contract tests.

No lowering, `.axp` generation, Java or ARM tool invocation, compile/link,
hardware access, firmware action, production build artifact, Task 009 compiler
implementation, or Task 010 CLI-product work occurred. Backend execution,
artifact generation, ARM compile/link, connected-device, real-time-resource,
and audible evidence remain unproved and explicitly deferred.
