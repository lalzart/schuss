# Unnumbered AI implementation: sonic-first project authoring

Status: implemented and locally validated on 2026-08-18 against exact record
set `schuss-record-set-000026@1`, content hash
`sha256:4ca86d5f870c7c70e39ead9b8793dde68a3f1cec9053f9bd34fb209ed619d67e`.
The implementation follows the explicit user authorization for the bounded
work below. It does not authorize Git publication, package installation,
global catalog promotion, build execution, device access, or hardware
mutation.

## Goal and why it exists

Let Codex and other MCP-capable AI clients design Schuss patches and create
project-local objects through the same client-neutral operation boundary as the
CLI and desktop application. Candidate planning is sonic-first: structural
validity is a hard gate, while fidelity to the stated sonic intent,
distinctiveness, and declared quality goals drive exploration. Reusing an
existing object is never preferred merely because it is cheaper or already
available.

The first writable AI slice must remain useful without claiming that numeric
analysis can hear, that an AI-generated object is target-qualified, or that an
accepted project revision has been built or auditioned on hardware.

## In scope

- Add one additive shared operation version and application-capability
  successor for sonic intent planning and project-local authoring.
- Return parallel candidate lanes for exact existing catalog objects,
  transparent compounds, and new native-kernel objects. Existing-object
  results retain their exact readiness/evidence facts; no cost score or
  cheapest-route ranking exists.
- Add process-local authoring drafts with explicit opaque handles, exact
  project snapshots, bounded lifetimes, deterministic inspection, and no
  ambient workspace selection.
- Support two project-local object forms:
  - transparent compounds assembled from exact existing component contracts;
  - a closed, declarative native DSP kernel language that is interpreted only
    by the bounded host evaluator in this task.
- Validate compact public interfaces, compound graph topology and mappings,
  native-kernel dataflow, instruction limits, value ranges, and exact
  references before a draft can be previewed.
- Produce deterministic host audition WAV bytes and objective signal metrics
  for native-kernel drafts. Store only a content-addressed, non-authoritative
  audition cache entry inside the explicit project workspace.
- Preview the exact project-local object definition and optional primary-graph
  node insertion without durable semantic mutation.
- Accept only the previewed bytes against the same exact project revision and
  one explicit confirmation fingerprint. Acceptance atomically publishes the
  object definition, graph/instrument/build-request successors when insertion
  is requested, the additive project manifest, and finally the workspace head.
- Expose the operations through goal-oriented MCP tools whose schemas derive
  from the canonical operation schema. Writable tools have truthful effect
  annotations and remain unavailable unless the human starts the local MCP
  process with an explicit project workspace.
- Preserve existing v0-v12 operation bytes, project-v0 histories, record sets,
  CLI behavior, desktop behavior, build/device services, and read-only MCP
  compatibility.

## Out of scope

- Model-provider selection, an embedded chat UI, autonomous background agents,
  embeddings, vector storage, remote MCP serving, OAuth, telemetry, or an MCP
  App.
- Arbitrary C/C++/Rust/Python/shell execution, arbitrary filesystem access,
  dependency installation, network access, or source-checkout mutation.
- Automatic target eligibility, direct-backend lowering, ARM compile/link,
  resource closure, connected-device execution, real-time stability, or
  audible-quality claims for a generated native kernel.
- Automatic listening, aesthetic scoring, fabricated sonic-quality numbers,
  or treating RMS/peak/spectrum-style measurements as subjective evidence.
- Global catalog insertion, readiness promotion, family/category policy,
  implementation priority, licensing conclusions, publication, or shared
  identity allocation outside the explicit project.
- Automatic acceptance, hidden graph edits, upload, patch start, USB discovery,
  flash, DFU, reset, SD-card writes, or persistent installation.
- Git staging, commit, push, release, or mutation of unrelated worktree files.

## Inputs and deliverables

Inputs are `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, accepted ADRs 0005, 0008,
0009, 0011, and 0014, `docs/SCHEMA_STRATEGY.md`,
`docs/COMPILER_STRATEGY.md`, `docs/PROJECT_WORKSPACE_CONTRACTS.md`,
`docs/APPLICATION_SPINE_PLAN.md`, `docs/OPERATION_CONTRACTS.md`, the existing
v11 project authoring operation, the v12 desktop-session boundary, the current
read-only MCP adapter, and exact record set `schuss-record-set-000025@1`.

Deliverables are:

1. this accepted implementation contract;
2. additive project/object, native-kernel, operation v13/result v13, and
   application-capability v6 schemas plus one exact successor record set;
3. a client-neutral sonic authoring service with intent planning, draft,
   evaluation, preview, and explicit atomic acceptance operations;
4. deterministic native-kernel validation and host audition artifacts;
5. project-v0/v1 history compatibility and project-local object closure
   validation;
6. MCP tools over the shared operations, enabled only by an explicit startup
   project;
7. focused positive, negative, stale-preview, no-write-before-accept, recovery,
   schema, MCP-authority, and determinism tests; and
8. updated architecture, operation, AI-boundary, status, history, and setup
   documentation.

## Sonic-first planning and evidence rules

1. Validity is a gate, not an optimization score. An invalid candidate cannot
   be recommended or accepted.
2. Existing, compound, and native creation lanes are returned in parallel.
   The presence of a partially matching existing object never suppresses a
   creation lane.
3. Planning may rank exact textual/capability matches only from governed
   catalog facts. Sonic fidelity, interest, and quality remain declared goals
   with `not-evaluated` evidence until a separate evaluation supplies evidence.
4. A novelty preference may favor exploration; no operation accepts cost,
   implementation effort, or object-count minimization as a ranking objective.
5. Objective host measurements are named measurements. They do not constitute
   listening, quality, target, real-time, or device evidence.
6. Every result separately reports structural, host-evaluation, target
   lowering, ARM build, device, real-time/resource, and audible-listening
   states. An unperformed level remains `not-run` or `not-evaluated`.

## Draft and acceptance rules

1. A draft handle is process-local and explicitly scoped to one exact project
   reference. It is never a semantic stable ID or authorization token for a
   different project.
2. Draft creation, inspection, evaluation, and preview do not change the
   accepted workspace head or governed semantic files.
3. A preview freezes canonical proposed records, their hashes, ordered graph
   edits, and one confirmation fingerprint. A stale project, changed draft,
   mismatched fingerprint, absent explicit write intent, or already-consumed
   preview fails before publication.
4. Project-local object stable IDs are allocated without display names,
   categories, paths, or model names. Local facet IDs remain stable inside the
   object definition.
5. A transparent compound retains its inspectable internal graph and exact
   mappings. A native kernel is opaque at the component boundary but its
   declarative program remains inspectable inside the project-owned definition.
6. Native-kernel acceptance grants structural and bounded host-evaluation
   status only. Its implementation binding is not target eligible and a build
   containing it must fail closed until a separately reviewed lowering and
   eligibility record exists.
7. Acceptance uses the existing recoverable multi-record write plan and the
   atomic workspace-head replacement as its sole semantic acceptance boundary.
8. MCP annotations describe effects but grant no authority. Writable calls
   require the same project reference, preview fingerprint, and explicit intent
   as direct API or future GUI/CLI clients.

## Validation cadence

- Focused: schemas and generated-record freshness; compact interface,
  compound, and native-kernel validation; deterministic audition; candidate
  lane behavior; draft lifecycle; preview purity; atomic acceptance; stale and
  replay rejection; project-v0/v1 history; and MCP tool/schema/effect gates.
- Adjacent regression: v1-v12 operation dispatch and canonical bytes, v8/v11
  project authoring/recovery, application capability registry, existing MCP
  modern/legacy behavior, desktop bridge, compiler front-half compound
  expansion, and governance routing.
- Expensive reproduction: no compiler, browser, Java, USB, or connected-device
  action is required. Native audition is bounded and local. The final aggregate
  supplies broad discovery once after implementation freeze.
- Aggregate: after generated files, negative cases, complete diff, and this
  acceptance matrix are frozen, run inventory, catalog, and contract discovery
  once. Diagnose inherited historical failures separately.

## Acceptance tests

1. Sonic intent planning always returns existing, transparent-compound, and
   native-kernel lanes, contains no cost objective, and marks unsupported sonic
   judgments as not evaluated.
2. Draft creation rejects unknown fields, stale exact references, unsafe or
   cyclic kernel dataflow, unsupported instructions, over-limit programs,
   invalid compound topology, and incomplete public mappings.
3. Repeating native evaluation with the same draft and audition request
   produces identical WAV bytes, content hash, and measurements; changing a
   governed input changes the artifact hash.
4. Evaluation reports objective measurements separately from audible,
   real-time, device, ARM, and target states.
5. Preview returns exact canonical object/graph proposals and a confirmation
   fingerprint while leaving every accepted governed byte unchanged.
6. Acceptance requires an exact current project reference, exact preview
   fingerprint, and `write_intent: explicit`; it writes the proposed immutable
   closure and accepts only by atomic workspace-head replacement.
7. Stale, altered, expired, foreign-project, and replayed previews dispatch no
   semantic write. Recovery yields either the complete prior or complete
   successor project.
8. Reloading an accepted transparent compound resolves its family reference,
   component contract, binding, internal graph, mappings, and optional primary
   graph instance. Reloading a native kernel preserves its program and reports
   target eligibility as absent.
9. Historical project-v0 workspaces and v1-v12 operations retain their accepted
   behavior and canonical result bytes.
10. MCP without `--project` advertises no writable authoring tools. MCP with an
    explicit valid project advertises the closed v13 tools in deterministic
    order, derives schemas from v13, truthfully annotates effects, and returns
    the canonical operation result unchanged.
11. The focused and adjacent checks, generated-file freshness,
    `git diff --check`, governance checks, and one final aggregate complete with
    inherited failures identified separately.

## Decisions this task may make

- The compact sonic-intent, interface, transparent-compound, native-kernel,
  audition-request, and preview result shapes inside the closed v13 contract.
- A small fixed safe instruction set, deterministic evaluator limits, default
  audition stimulus, artifact duration/sample-rate bounds, process-local draft
  TTL, and cache locator format.
- Stable operation/tool names, descriptions, effect annotations, diagnostic
  wording, and deterministic project-local numeric ID allocation.
- Private module boundaries and dependency-free Python implementation details.

## Decisions this task must not make

- Global catalog taxonomy, family promotion, readiness, implementation
  priority, licensing, or source-provenance truth.
- A claim that an AI plan is sonically best, that numeric metrics are listening,
  or that host evaluation establishes target/device/audible quality.
- A general-purpose programming language or arbitrary-code execution path.
- Silent build eligibility, compiler substitution, adapter insertion, graph
  mutation, project selection, write confirmation, or device authority.
- A model/vendor, remote security, desktop chat, collaboration, hardware, Git,
  package-installation, or publication policy.

## Completion boundary

Completion proves that a local AI client can explore exact catalog and creation
lanes, author and evaluate bounded project-local object drafts, preview an exact
patch/object change, and explicitly accept that change through the shared
recoverable project boundary. It does not prove that the result sounds good,
matches a reference by ear, compiles for Ksoloti, fits real-time resources,
runs on a board, is safe for hardware, belongs in the global catalog, or is
published.
