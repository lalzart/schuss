# Shared headless operation contracts

Task 008 establishes one deterministic control-plane boundary for every Schuss
client. The public in-process API is `packages.schuss_core.dispatch_operation`;
the minimal executable adapter is `bin/schuss`. Both return the same canonical
`schuss-operation-result-v1` bytes.

## Validator dependency boundary

The validator dependency direction is fixed:

```text
validator_core
    |-- device_instrument_rules
    |-- component_graph_rules
    `-- target_backend_build_rules

aggregate_validator -> composes all three rule modules
```

Domain-rule modules import no sibling rule module. The core contains restricted
JSON loading, canonicalization, hashing, schema traversal, portability,
diagnostic ordering, exact-reference, registry, and domain-neutral graph-cycle
mechanisms. Domain policy remains in its owning rule module. The three historic
`validate_*_contracts.py` commands are compatibility adapters and preserve
their accepted summaries byte-for-byte.

## Explicit record-set boundary

Repository validation no longer treats every JSON file in a known directory as
one ambient registry. `record-set-v0` pins every selected schema and semantic
record by portable path, raw byte hash, semantic content hash, stable ID, and
revision. Missing, extra, duplicate, stale, hash-mismatched, or unlisted members
fail closed.

The default validators and `load_repository_context()` select exactly
`schuss-record-set-000001` revision 1, content hash
`sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6`.
That is the frozen Task 005-008 view. The Task 009 prerequisite view is an
explicit opt-in parent-preserving superset,
`schuss-record-set-000002` revision 1, content hash
`sha256:6f2855c384ef8bab88991a6cabdd8416c7f3c59a010eed0c6cda1ac08651ecaf`.
The in-memory operation context retains the exact selected record-set
reference. It never guesses a newest revision or derives membership from
filesystem order.

## Request and result envelopes

`operation-request-v1.schema.json` defines a closed request for exactly one of:

- `records.validate` over the accepted in-memory record closure;
- `graph.inspect` for one exact graph reference;
- `build.resolve` for one exact Task 007 build-request reference; or
- `graph.transact` for one exact base graph and an ordered edit sequence.

`operation-result-v1.schema.json` defines the closed result envelope. It carries
the operation identity, one stable status, an operation-owned domain value or
`null`, and deterministically ordered structured diagnostics. Domain values
remain governed by their existing record schemas and the operation contract;
the adapter performs no client-specific reshaping.

Requests and results contain no timestamps, random IDs, absolute paths, or
ambient client state. Canonical output uses `schuss-canonical-json-v1`.

## Operation behavior

`records.validate` returns separate device/instrument, component/graph,
target/backend/build, and aggregate summaries. It does not discover or rewrite
records after the operation context has been loaded.

`graph.inspect` returns the exact graph and exact component-contract closure.
Implementation selection remains `not-evaluated`; lowering remains `not-run`.

`build.resolve` revalidates the supplied target/backend/build closure in memory
and returns every candidate with its exclusion and unresolved reasons. Only a
candidate with neither exclusion nor uncertainty can be selected. A completely
selected request produces a `schuss-backend-invocation-input-v1` data value for
Task 009. That seam contains the accepted request, traces, and selected
bindings, then stops at:

```text
completed_stage: implementation-resolution
next_stage: backend-lowering
next_stage_status: not-run
executable_handler_status: absent
```

Task 008 defines no executable backend handler. The
`executable_handler_status: absent` member records that frozen producer-side
boundary; it is not a mutable global handler registry.

Task 009 leaves this value and the dispatcher unchanged. Its bounded external
handler revalidates the exact seam plus the accepted build-request schema,
requires the complete revision-2 request and selected binding, rejects stale or
uncertain input before creating an output root, and then runs only the exact
Blend slice. The retained seam bytes are recorded under
`evidence/task-009-v1/`.

`graph.transact` supports only add/remove node, add/remove connection, set node
parameter, and set node attribute. It rejects a stale base content hash, applies
edits to a private copy, creates a proposed next revision, and runs the complete
Task 006 component/graph plus device/instrument validation closure. Any edit or
validation failure returns no proposed graph. Success reports
`persistence_status: not-written`; the operation never writes production data.

## Minimal process adapter

The Task 008 machine boundary is:

```bash
bin/schuss op --request request.json --json
bin/schuss op --request - --json < request.json
```

Canonical result JSON plus one LF is written to stdout. Usage, file-I/O,
malformed-JSON, and unexpected adapter diagnostics are written only to stderr.
Exit codes are `0` for success, `1` for a dispatched non-success result, `2`
when dispatch could not begin, and `3` for an unexpected adapter failure.

Task 010 owns ergonomic commands, human output, convenient flags, completion,
progress, and final CLI UX. Task 009 has completed only its bounded lowering,
`.axp`, Java/ARM, compile/link, and artifact proof; it adds no product CLI.

## Deterministic product CLI

Task 010 implements the product projection without adding an operation:

```text
schuss validate [--record-set MANIFEST] [--json]
schuss graph inspect GRAPH_ID@REVISION [--record-set MANIFEST] [--json]
schuss graph transact GRAPH_ID@REVISION --edits FILE_OR_STDIN [--record-set MANIFEST] [--json]
schuss build resolve REQUEST_ID@REVISION [--record-set MANIFEST] [--json]
schuss completion {bash|zsh|fish}
```

The original `schuss op --request FILE_OR_STDIN --json` invocation is retained
byte-for-byte for unchanged requests and context. Its optional
`--record-set MANIFEST` form selects the same explicit context used by product
commands; the default remains `schuss-record-set-000001` revision 1.

Graph and request shorthand is resolved only when the selected validated
manifest contains exactly one member of the required kind and exact revision.
The pinned member supplies the existing ID/revision/content-hash reference.
There is no implicit revision, `latest`, display-name lookup, or ambient scan.
Prospective selections must retain a complete parent chain ending at the
frozen accepted default.

Without `--json`, a fixed plain-text renderer identifies the selected record
set, operation status, exact domain references, ordered candidates/reasons,
ordered graph structure, diagnostics, and the `not-written` transaction state.
With `--json`, stdout is exactly the canonical operation result plus one LF.
Usage/input failures remain stderr-only at exit 2; dispatched non-success
results remain stdout at exit 1. Help and static Bash/Zsh/Fish completion use
no live record enumeration, network, shell-profile edit, terminal adaptation,
or client configuration.

No progress UI is exposed. The operations are synchronous and bounded, and
the shared operation contract defines no progress events. A plain
`schuss build` is usage failure; only `schuss build resolve` exists, and it
never invokes the Task 009 exact-slice handler.

## Evidence boundary

Task 008 proves structural validation, exact reference resolution, deterministic
inspection/resolution, atomic in-memory graph mutation, and client-neutral
canonical bytes. It does not prove backend lowering, artifact generation, ARM
compile/link, connected hardware, real-time resource behavior, or audible
behavior.
