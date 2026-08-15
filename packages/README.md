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

Repository contexts load an exact `record-set-v0` manifest. The default is the
frozen Task 005-008 accepted view; a prospective view must be selected by its
exact manifest and the context retains that reference.

The package itself has no executable backend handler and performs no lowering,
artifact generation, Java/ARM invocation, compile/link, or hardware access.
Task 009's separate bounded handler consumes the exact `build.resolve` seam in
`tools/contracts/task009_backend.py`; it does not alter this pure package or add
a second request model. `bin/schuss` remains the minimal machine adapter; Task
010 still owns the CLI product.
