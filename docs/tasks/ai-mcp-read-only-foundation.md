# Unnumbered AI implementation: read-only MCP foundation

Status: accepted by explicit user authorization, implemented, and locally
validated on 2026-08-18. Git publication and every project, build, device, and
hardware mutation remain separate.

Successor note: the later sonic-first project-authoring slice adds the v13
planning and explicitly project-scoped authoring tools. This document retains
the exact historical six-tool `schuss-record-set-000025@1` boundary.

This is the first bounded AI-client implementation. It exposes a small,
read-only projection of the existing client-neutral Schuss control plane over
Model Context Protocol (MCP); it does not introduce a second semantic model or
an embedded language model.

## Goal and why it exists

Let an MCP-capable AI host discover Schuss, search the exact catalog, inspect
families and component contracts, and inspect exact DSP graphs through the
same canonical operations already used by the CLI and desktop application.
The first slice should be directly usable by local clients while keeping
mutation, model-provider, project, build, and hardware authority out of the AI
adapter.

## Protocol basis

The implementation is based on the stable MCP `2026-07-28` specification
reviewed on 2026-08-18, especially:

- <https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning>
- <https://modelcontextprotocol.io/specification/2026-07-28/server/discover>
- <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
- <https://modelcontextprotocol.io/specification/2026-07-28/server/resources>
- <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio>

The modern protocol is stateless and requires version and client capabilities
on every request. The optional `server/discover` extension is implemented by
this adapter; ordinary results carry `resultType`; list/read results carry
cache hints; and stdio is newline-delimited JSON-RPC with protocol-only stdout.
The local server also accepts the immediately preceding `2025-11-25`
initialization-based era so existing hosts can migrate without changing Schuss
operation semantics.

## In scope

- Add one dedicated local stdio MCP process entry point.
- Implement MCP `2026-07-28` discovery, metadata validation, tools, one static
  resource, cache hints, structured tool results, and standard JSON-RPC errors.
- Implement the `2025-11-25` stdio initialize/initialized path for the same
  tools and resource, plus its retained `ping` utility.
- Expose exactly these read-only shared operations as deterministically ordered
  MCP tools:
  - `application.describe`;
  - `catalog.search`;
  - `catalog.inspect`;
  - `catalog.implementations.search`;
  - `component.inspect`; and
  - `graph.inspect`.
- Derive every tool input and output schema from the selected exact Schuss
  operation schemas instead of copying a client-owned schema.
- Return the unchanged canonical Schuss operation result both as MCP structured
  content and as canonical JSON text. A non-success Schuss result is an MCP tool
  execution error, not a protocol error.
- Expose `schuss://application/capabilities` as a JSON resource backed by the
  same `application.describe` operation.
- Default to exact record set `schuss-record-set-000025@1`; permit a human-owned
  startup argument to select another exact validated in-installation manifest.
- Use deterministic, dependency-free Python so this slice requires no package
  installation. Keep protocol adaptation isolated so a later official-SDK
  transport can replace it without changing tool-to-operation mappings.

## Out of scope

- An embedded chat UI, prompt orchestration, model-provider API, credentials,
  embeddings, vector search, retrieval database, memory, or autonomous agent.
- MCP prompts, sampling, roots, elicitation, tasks, subscriptions, Apps, HTTP,
  SSE, remote deployment, OAuth, telemetry, or network listening.
- Project loading or persistence, graph proposals or writes, build execution or
  sessions, filesystem tools, device discovery, USB, upload, patch start, flash,
  DFU, reset, SD-card writes, or persistent installation.
- Generic operation passthrough, arbitrary schema/file reads, ambient workspace
  discovery, implicit newest record set, or tool-list changes caused by prior
  calls on one connection.
- A new semantic record, record-set successor, catalog projection, compiler
  capability, evidence promotion, desktop feature, or hardware claim.
- Package installation, upstream-checkout mutation, Git staging, commit, push,
  or publication.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADR 0008,
`docs/ARCHITECTURE.md`, `docs/APPLICATION_SPINE_PLAN.md`,
`docs/OPERATION_CONTRACTS.md`, the exact shared operation schemas and
dispatcher, exact record set `schuss-record-set-000025@1`, and MCP
specification revision `2026-07-28` with the `2025-11-25` compatibility era.

Deliverables are:

1. this accepted implementation contract;
2. one isolated MCP adapter and dedicated executable entry point;
3. one closed, deterministic tool registry over six shared read-only operations;
4. one capability resource backed by `application.describe`;
5. focused modern/legacy protocol, schema, error, and authority-boundary tests;
6. adjacent shared-operation and governance regression evidence; and
7. concise setup, architecture, status, and limitation documentation.

## Wire and safety rules

1. MCP is only an adapter. It constructs a versioned Schuss request, calls
   `dispatch_operation()` once, and returns the canonical result unchanged.
2. MCP tool names are stable presentation identifiers; Schuss operation names
   remain the semantic operation identities.
3. Tool schemas are extracted from the exact selected operation schema branch.
   Missing, ambiguous, stale, or unsupported schemas fail startup closed.
4. The modern server validates required per-request protocol version and client
   capability metadata independently on every request. It infers no identity,
   capability, project, or conversation from the stdio process.
5. The legacy server performs one exact initialization negotiation before
   accepting ordinary calls. Modern and legacy result shapes never bleed into
   one another.
6. `stdout` contains only one compact JSON-RPC message per line. Human and
   adapter diagnostics use `stderr`; malformed or oversized input is bounded
   and cannot become a tool call.
7. Tool results contain no host path, raw semantic file, artifact bytes,
   process handle, USB handle, or implicit authority. The selected immutable
   operation context is loaded once and is read-only for the process lifetime.
8. The tool registry and resource list are deterministic and advertise no
   change notifications. Cache scope is private because the selected local
   record-set context is process configuration.
9. Every exposed tool is annotated read-only, non-destructive, idempotent, and
   closed-world. An annotation never grants authority beyond the allowlist.
10. Unknown methods/tools and malformed protocol requests use protocol errors;
    valid calls that Schuss rejects return structured actionable tool errors.
11. Tool invocations are serialized and rate-limited within the local process;
    exhausting that budget dispatches no Schuss operation and returns a bounded
    application-defined protocol error outside the JSON-RPC/MCP reserved range.

## Validation cadence

- Focused: tool-registry/schema extraction; modern discovery and per-request
  metadata; deterministic tools/list; structured success and operation-error
  calls; local rate limiting; resource list/read; legacy initialize/initialized/ping; unknown
  method/tool; malformed/duplicate/oversized input; stdout purity; explicit EOF
  shutdown; and entry-point argument behavior.
- Adjacent regression: exact canonical results through direct dispatch versus
  MCP, existing operation v1-v12 compatibility, application capability
  description, CLI process adapter, and governance/task routing checks.
- Expensive reproduction: no compiler, browser, desktop, network, Java, USB, or
  connected-device reproduction is required. The final aggregate already
  covers broad contract discovery and must not be duplicated separately.
- Aggregate: after the implementation, generated-file review, negative cases,
  complete diff, and acceptance matrix are frozen, run the full inventory,
  catalog, and contracts discovery once. Diagnose any inherited failures
  separately from this task.

## Acceptance tests

1. A modern `server/discover` request returns only the supported versions,
   tools/resources capabilities, stable server identity, instructions, and
   required private cache hints, with no session identifier or handshake.
2. Every modern request independently requires exact `2026-07-28` metadata;
   unsupported or missing versions/capabilities fail with the specified
   protocol error and do not dispatch a Schuss operation.
3. `tools/list` is deterministic and exposes exactly six stable tools whose
   payload/output schemas derive from the selected canonical operation schemas
   and whose annotations truthfully declare read-only behavior.
4. Each tool constructs the exact versioned Schuss request, dispatches once,
   returns byte-equivalent canonical structured/text results, and sets MCP
   `isError` only when the canonical Schuss status is not `success`.
5. Invalid tool arguments are retained as canonical Schuss diagnostics where a
   valid MCP call reached the operation boundary; unknown tools and malformed
   MCP calls remain JSON-RPC protocol errors.
6. `resources/list` and `resources/read` expose only the one capability URI,
   with exact canonical `application.describe` bytes and no file URI/path.
7. A legacy client can initialize exactly `2025-11-25`, send initialized, list
   and call the same tools, read the same resource, and ping without modern-only
   result/cache members.
8. Prompts, sampling, roots, generic operations, mutation, project, build,
   device, network, filesystem, and hardware calls are absent and rejected.
9. The stdio loop rejects malformed, duplicate-key, non-object, and oversized
   messages safely, writes no non-protocol text to stdout, and exits cleanly on
   EOF.
10. Focused and adjacent checks, `git diff --check`, task/governance checks, and
    the final aggregate complete with inherited failures reported separately.

## Decisions this task may make

- Stable MCP tool names/titles/descriptions for the six fixed operations.
- Private module structure, request-size limit, cache TTL, deterministic JSON
  encoding, error-message wording, and the one custom resource URI.
- Exact modern/legacy response shaping required by the two protocol revisions.
- Whether protocol conformance helpers are functions or small immutable data
  classes, provided the Schuss operation boundary remains unchanged.

## Decisions this task must not make

- New Schuss operation semantics, a generic operation tool, a client-specific
  graph/catalog database, implicit workspace or record-set selection, or any AI
  mutation authority.
- A model/vendor choice, prompt policy, autonomous planning loop, memory store,
  remote MCP deployment, authentication policy, or desktop chat experience.
- Permission to build, discover a real device, upload, run, flash, reset, write
  SD, access arbitrary files/processes/network, install packages, mutate an
  upstream checkout, stage, commit, push, or publish.
- Promotion of catalog visibility or structural inspection to compiler,
  connected-device, real-time/resource, stable-runtime, or audible evidence.

## Local validation evidence

- The focused MCP and governance run passed 15/15 tests. It covers all six
  tools, both protocol eras, exact canonical result equivalence, the sole
  resource, protocol errors, rate limiting, malformed/oversized input, EOF,
  startup configuration, and task routing.
- A real `bin/schuss-mcp` subprocess accepted one modern discovery request,
  emitted exactly one JSON-RPC response and no stderr bytes, then exited zero
  when stdin closed.
- Generated modern discovery/tool/resource request and response shapes and the
  legacy initialize/list/call/resource/ping shapes produced zero errors against
  the official `2026-07-28` and `2025-11-25` JSON schemas during the one-time
  specification check. This is wire-shape evidence, not every-host proof.
- The final aggregate passed inventory 14/14 and catalog 6/6. Contracts ran 423
  tests in 986.850 seconds and retained exactly the three previously audited
  Task 011A/Task 023 golden and Task 027 freshness failures. No MCP,
  build/device, shared-operation, governance, or current Task 030 test failed.
- `git diff --check`, Python compilation, protocol-only stdout, and executable
  entry-point checks passed. No package was installed and no model, network
  listener, browser, desktop, compiler, USB, or connected-hardware action ran
  for this AI slice.

## Completion boundary

Completion proves that local MCP hosts can use a small read-only Schuss surface
through the latest stable protocol and its immediately preceding compatibility
era. It does not prove compatibility with every MCP host, remote security,
model quality, project authoring, build execution, device behavior, real-time
safety, or sound.
