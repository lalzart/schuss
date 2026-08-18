# AI and MCP boundary

Status: sonic-first project authoring is implemented locally against exact
record set `schuss-record-set-000026@1`. The default server remains safe for
discovery; authoring tools appear only when a human supplies one explicit
absolute project workspace at process startup. Build execution, device access,
USB, upload, firmware/SD mutation, model-provider integration, remote serving,
and publication remain outside this boundary.

## Role in Schuss

MCP is a presentation adapter over the same client-neutral operations used by
the CLI and desktop application:

```text
MCP-capable AI host
        -> bin/schuss-mcp (local stdio)
        -> packages.schuss_core.mcp_server
        -> dispatch_operation()
             -> immutable OperationContext
             -> explicit ProjectService, when configured
             -> process-local SonicAuthoringService, when configured
```

The adapter owns no catalog index, graph model, project database, compiler,
USB implementation, or model orchestration. It derives each tool schema from
the exact canonical operation schema, constructs one Schuss request, dispatches
once, and returns the canonical operation result as both structured content
and canonical JSON text.

## Protocol surface

The primary wire revision is stable MCP `2026-07-28`. The server implements
the revision's stateless per-request metadata, tools, resources, structured
results, cache hints, and optional `server/discover` extension. It also accepts
the immediately preceding `2025-11-25` initialize/initialized stdio flow for
existing hosts. `server/discover` is implemented here but is not a mandatory
method in the stable specification.

Only newline-delimited stdio is implemented. Stdout is protocol-only. There is
no HTTP listener, OAuth surface, prompt, sampling, root, subscription, task
extension, MCP App, or server-initiated request.

## Tool modes

Without `--project`, the deterministic tool surface is read-only:

| MCP tool | Canonical Schuss operation | Effect |
| --- | --- | --- |
| `schuss.application.describe` | `application.describe` v7 | read-only |
| `schuss.catalog.search` | `catalog.search` v2 | read-only |
| `schuss.catalog.inspect` | `catalog.inspect` v2 | read-only |
| `schuss.catalog.implementations.search` | `catalog.implementations.search` v10 | read-only |
| `schuss.component.inspect` | `component.inspect` v11 | read-only |
| `schuss.graph.inspect` | `graph.inspect` v1 | read-only |
| `schuss.sonic.intent.plan` | `sonic.intent.plan` v13 | read-only |

Sonic planning always keeps three lanes open: exact existing objects,
transparent compounds, and bounded native kernels. Validity is a hard gate.
There is no cost objective and an existing partial match cannot suppress a
creation lane. Catalog matching is factual retrieval, not a claim of sonic
fitness. In project mode, the existing-object lane also includes accepted
project-local objects without promoting them into the global catalog.

With `--project /absolute/workspace`, seven project-scoped tools are added:

| MCP tool | Canonical Schuss operation | Effect |
| --- | --- | --- |
| `schuss.authoring.draft.create` | `authoring.draft.create` v13 | process-local draft |
| `schuss.authoring.draft.inspect` | `authoring.draft.inspect` v13 | read-only |
| `schuss.authoring.draft.evaluate` | `authoring.draft.evaluate` v13 | bounded host evaluation and cache write |
| `schuss.authoring.change.preview` | `authoring.change.preview` v13 | proposal only |
| `schuss.authoring.change.accept` | `authoring.change.accept` v13 | explicit atomic project write |
| `schuss.project.objects.list` | `project.objects.list` v13 | read-only |
| `schuss.project.object.inspect` | `project.object.inspect` v13 | read-only |

Tool annotations truthfully distinguish read-only, process-local/cache, and
project-writing effects. An annotation grants no authority. Unknown tools and
malformed MCP requests are protocol errors; valid calls rejected by Schuss
return the canonical diagnostic as a tool execution error.

The sole resource is `schuss://application/capabilities`, backed by the same
`application.describe` operation for the exact selected context and configured
services. It is not a file URI and exposes no semantic-file or host path.

## Object and patch authoring boundary

- Drafts and previews are opaque, process-local, project-scoped, and bounded by
  a one-hour lifetime. They are not semantic IDs or durable authorization.
- Transparent compounds retain an inspectable internal graph and exact public
  facet mappings to existing component contracts.
- Native objects use a closed declarative DSP kernel with bounded instruction
  and frame counts. Arbitrary C/C++/Rust/Python/shell and dependency loading are
  prohibited.
- Native host evaluation emits deterministic content-addressed mono WAV bytes
  and objective peak/RMS/DC/crest/zero-crossing facts in
  `.schuss/cache/ai-authoring/`. The cache is not governed project truth.
- Preview validates the complete base-plus-project semantic closure and returns
  exact proposed records, a write plan, and a confirmation fingerprint without
  changing governed bytes.
- Acceptance requires the same exact project reference, unchanged fingerprint,
  and `write_intent: explicit`. Immutable records are published before one
  atomic workspace-head replacement; stale and replayed previews fail closed.
- Project-local native bindings remain target-ineligible. Structural and host
  evaluation do not imply compiler lowering, ARM build, device execution,
  real-time/resource closure, listening, or sonic quality.

## Local safety boundary

- The default immutable context is `schuss-record-set-000026@1`.
- `--record-set` may select only an exact validated manifest inside this
  installation's `contracts/record-sets/` directory.
- `--project` must be absolute. The workspace pins its immutable base record
  set; an explicitly supplied record set must equal that base exactly.
- No project is inferred from the current directory, prior request, desktop
  selection, model conversation, or newest record set.
- Requests are size-bounded, duplicate JSON members are rejected, tool calls
  are serialized and locally rate-limited, and EOF cleanly ends the process.
- No generic operation, arbitrary file/process/network, build, device, USB,
  upload, reset, flash, SD-card, or persistent-install tool is exposed.
- The wire adapter remains dependency-free; no package installation is needed.

## Running it

Discovery and sonic planning only:

```bash
/absolute/path/to/schuss/bin/schuss-mcp
```

Project-local object and patch authoring:

```bash
/absolute/path/to/schuss/bin/schuss-mcp \
  --project /absolute/path/to/a/schuss-project
```

New projects created by the maintained desktop application pin exact record
set `schuss-record-set-000026@1` and can therefore be selected here directly.
Historical projects keep their immutable earlier base; Schuss never rewrites a
project’s base record set merely to enable AI tools.

The maintained desktop may consume the two accepted project-object read
operations so an MCP-accepted object appears in its owning project and graph.
It does not expose draft, evaluation, preview, or acceptance operations and
does not infer the MCP project from the desktop selection.

Codex CLI can register the same fixed command and project arguments:

```bash
codex mcp add schuss -- \
  /absolute/path/to/schuss/bin/schuss-mcp \
  --project /absolute/path/to/a/schuss-project
codex mcp list
```

Schuss intentionally validates the complete exact base and project closure
before exposing any tools. Codex's documented default startup timeout is ten
seconds, which is too narrow for that cold validation on some hosts. The
equivalent durable configuration should therefore include a larger startup
window and prompt for tools whose annotations are not read-only:

```toml
[mcp_servers.schuss]
command = "/absolute/path/to/schuss/bin/schuss-mcp"
args = ["--project", "/absolute/path/to/a/schuss-project"]
startup_timeout_sec = 30
default_tools_approval_mode = "writes"
```

The ChatGPT desktop app, Codex CLI, and Codex IDE extension share the same
Codex-host MCP configuration. The current setup syntax and optional per-tool
approval controls are documented in the
[official OpenAI MCP guide](https://developers.openai.com/codex/mcp). Keep the
project argument human-owned and fixed; do not let a model substitute an
ambient workspace.

An MCP host configuration can pass the project as a fixed human-owned startup
argument:

```json
{
  "mcpServers": {
    "schuss": {
      "command": "/absolute/path/to/schuss/bin/schuss-mcp",
      "args": ["--project", "/absolute/path/to/a/schuss-project"]
    }
  }
}
```

Do not type prose into the process manually; stdin and stdout are the MCP wire
after serving begins.

## Expansion gates

The next useful additions are target lowering for a separately reviewed kernel
subset and an audition/compare workflow that can attach actual human listening
judgments without fabricating them. Build/device tools, model-provider choice,
desktop chat, remote security, and global catalog promotion each require their
own contract and authority gate.
