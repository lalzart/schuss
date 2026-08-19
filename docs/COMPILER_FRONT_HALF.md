# Compiler front half and deterministic planning artifacts

Task 013 implements one reusable, backend-neutral compiler front half. Its
public Python API is:

```python
CompilationContext.from_values(...)
plan_build(compilation_context)
```

`CompilationContext` is an immutable canonical-JSON snapshot. It contains one
exact build-request reference, one explicit closure source, the exact semantic
records available to the plan, and the exact schemas and policy versions used
to interpret them. Callers cannot request `latest`, depend on enumeration
order, or mutate the input after construction.

`plan_build` is the only public planning entry point. It is pure and in-memory:
it performs no project writes, backend dispatch, legacy lowering, Java access,
source generation, ARM compilation, packaging, device action, or evidence
promotion.

## Ordered stages

The front half runs these stages in order:

1. `schema-identity-validation`
2. `target-independent-graph-validation`
3. `target-backend-validation`
4. `implementation-resolution`
5. `compound-elaboration`
6. `dependency-resource-planning`

A failed stage records every later front-half stage as `not-run`. Stages 7-10
(`backend-lowering`, `artifact-generation`, `target-compile-link`, and
`packaging-evidence-recording`) are always `not-run` in Task 013. Every exit
sets `build_result_status` to `not-created`, `backend_execution_status` to
`not-run`, and `authoritative_records_mutated` to false.

Stages 2 and 4 reuse the accepted shared graph validator and exact
`build.resolve` selection implementation. The compiler does not carry a second
type system or candidate-selection algorithm. Candidate ordering, exclusions,
uncertainty, overrides, priorities, and ambiguity therefore remain the
accepted control-plane semantics.

## Compound elaboration

Transparent compound expansion validates total equality across contract
mapping keys, binding seam maps, and implementation-graph mappings before it
expands anything. Derived node identities use an explicit outer-to-inner
instance path, such as:

```text
derived-node:graph-node-000001/graph-node-000001
```

The elaborated graph retains hierarchy, contract and selected-binding
references, parameter and attribute values, declared state ownership, public
facet declarations, public exposures, parameter bindings, and remapped
derived endpoints. The origin map binds every derived node, facet, connection,
public mapping, dependency, resource, and diagnostic to stable authoritative
subjects. Recursive definition expansion is a separate error from signal-flow
feedback; elaboration never rewrites the authoritative DSP graph.

## Dependency and resource planning

Selected eligibility records supply exact dependency and resource
requirements. An optional `compiler-dependency-facts-v0` compiler-input record
exists for closed planning fixtures and future exact provider closures; it is
not a catalog, target, backend, binding, or eligibility record and Task 013
adds no production instance of it.

Dependency planning uses content-addressed portable locators. It reports
missing providers, ambiguous providers, version/hash disagreement, prohibited
provider cycles, exclusive-service conflicts, unresolved facts, and
nonportable input separately. The resulting order is deterministic and places
required dependencies before consumers when the provider graph is acyclic.

Resource planning keeps these facts distinct:

- target-region declarations;
- hard requirements and their alignment-expanded byte counts;
- unknown required facts;
- estimates;
- measurements; and
- per-region hard-budget decisions.

Task 013 emits no estimates or measurements for the retained Task 011C input.
It never derives them from compile/link artifacts. Under the accepted resolver,
an unresolved eligibility resource fact prevents selection at stage 4, so it
cannot be relabeled as a stage-6 estimate; a known selected hard requirement
can reach stage 6 and a known overrun is `budget-failure`.

## Artifact bundle and identity

The top-level `compiler-plan-result-v0` binds the exact input-closure hash,
ordered stage results, deterministic diagnostics, later-stage markers, and five
derived artifact kinds:

| Artifact kind | Producer stage | Schema |
| --- | --- | --- |
| `resolution-plan` | 4 | `compiler-resolution-plan-v0` |
| `elaborated-graph` | 5 | `compiler-elaborated-graph-v0` |
| `dependency-plan` | 6 | `compiler-dependency-plan-v0` |
| `resource-plan` | 6 | `compiler-resource-plan-v0` |
| `origin-source-map` | 6 | `compiler-origin-map-v0` |

Every artifact has a `compiler-artifact-descriptor-v0` descriptor containing
its kind, stage/version producer, exact input-closure hash, media type,
canonical byte length, SHA-256, and content-addressed portable locator. These
are planning artifacts only. The elaborated graph is marked `derived: true`
and `authoritative: false`; it cannot validate as `dsp-graph-v0` or be admitted
as a project graph revision.

## Shared operation

Operation envelope v4 additively exposes `build.plan`. Its request contains
only one exact `build_request_reference`. The dispatcher builds the immutable
context from either the explicitly selected record set or an explicitly loaded
Task 012A project. Direct and canonical process adapters return identical v4
result bytes.

Use the existing machine-operation boundary:

```bash
bin/schuss op \
  --record-set contracts/record-sets/task013-compiler-front-half-v1.json \
  --request request.json \
  --json
```

Task 013 does not add an ergonomic `schuss build plan` or executable
`schuss build` command. Task 014 now additively supplies those product commands
without changing the Task 013 planning API or v4 bytes.

## Variable desktop-host consumer

Task 032 reuses `CompilationContext.from_values(...)` and `plan_build(...)`
without adding another resolver. Its closure source is one exact accepted
project revision, and its build request is the exact project-owned request
explicitly named by the caller. The host lowerer consumes the successful
resolution artifact, then independently validates the bounded v1 execution
shape and derives a non-authoritative runtime package. The global Task 032
request is a project-template source only; it is never an ambient or
latest-request shortcut.

This consumer does not change the front half's evidence meaning. A successful
plan selects exact bindings and supplies deterministic source-plan identity;
native package preparation and offline execution are separate host evidence,
and neither promotes Ksoloti compatibility, physical-device execution,
general real-time/resource behavior, or listening quality.

## Evidence boundary

A successful plan reaches only structural evidence levels 1 and 2. Levels
3-8 are `not-run`. Success says nothing about backend lowering, generated
source, ARM compilation/linking, connected hardware, real-time behavior, or
sound. Run the read-only focused gate with:

```bash
python3 tools/contracts/generate_task013_record_set.py --check
python3 tools/contracts/validate_task013.py
python3 -m unittest tools.contracts.tests.test_task013_compiler_front_half
```
