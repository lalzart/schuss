# Headless packages

`schuss_core` is the shared headless control plane. Its public
`dispatch_operation` API implements `records.validate`, `graph.inspect`,
`build.resolve`, and atomic `graph.transact` over one in-memory operation
context. GUI, CLI, and AI clients must use this same dispatcher.

Task 012A additively introduces `ProjectService` beneath that dispatcher. It
owns explicit project loading, base-plus-project closure validation, locking,
write planning, atomic workspace-head publication, and recovery for
`project.init`, `project.inspect`, `project.validate`, and
`project.graph.commit`. CLI code owns none of those algorithms. Persistent
commit reuses the existing ordered `graph.transact` operation once.

Task 013 additively introduces the pure `CompilationContext` and `plan_build`
API in `compiler_front_half.py`. The immutable in-memory context carries one
exact build request and semantic/schema closure through validation, accepted
binding resolution, transparent-compound elaboration, and dependency/resource
planning. Operation v4 exposes the same plan as `build.plan` through the shared
dispatcher and canonical process adapter, including explicit Task 012A project
contexts. The module emits only derived planning artifacts and imports no
legacy bridge, executable handler, product CLI, project filesystem service,
UI, or device transport.

Task 014 additively introduces `ExecutionService`, exact
`HandlerRegistration`, `CancellationToken`, and `execute_build` in
`build_execution.py`. The service consumes the Task 013 plan once, has no
backend implementation of its own, and publishes only a successful fresh
staging root. Operation v5 exposes `build.execute`; the exact Ksoloti adapter
remains isolated under `legacy/ksoloti-bridge/`.

Task 015 adds the pure `lower_minimal_direct(...)` and
`evaluate_linear_mix_q27(...)` APIs in `direct_frontend.py`. They accept only
the exact successful one-node Blend plan/graph/contract closure and emit a
normalized Q27 module, standalone deterministic C++17, and source map. The
module imports no legacy bridge, runtime ABI, product CLI, filesystem service,
or device transport, and it does not register a production backend.

Repository contexts load an exact `record-set-v0` manifest. The default is the
frozen Task 005-008 accepted view; a prospective view must be selected by its
exact manifest and the context retains that reference.

The package itself has no built-in executable backend handler. Lowering,
generation, and Java/ARM invocation occur only through an injected registered
adapter; hardware access remains absent.
Task 009's separate bounded handler consumes the exact `build.resolve` seam in
`tools/contracts/task009_backend.py`; it does not alter this pure package or add
a second request model. `bin/schuss` remains the minimal machine adapter; Task
010 still owns the CLI product.
