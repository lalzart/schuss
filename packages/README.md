# Headless packages

`schuss_core` is the Task 008 shared headless control plane. Its public
`dispatch_operation` API implements `records.validate`, `graph.inspect`,
`build.resolve`, and atomic `graph.transact` over one in-memory operation
context. GUI, CLI, and AI clients must use this same dispatcher.

The package has no executable backend handler and performs no lowering,
artifact generation, Java/ARM invocation, compile/link, or hardware access.
`bin/schuss` is the minimal machine adapter; Task 010 still owns the CLI
product.
