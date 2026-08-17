# Future Tauri shell boundary

This directory is reserved for a later, separately authorized Tauri 2 shell.
It currently contains no Rust source, Cargo metadata, Tauri configuration,
commands, permissions, process bridge, packaging, or updater behavior.

Any later transport must remain a capability-limited adapter over the existing
versioned Schuss operations. Rust may own shell lifecycle, transport, and
security policy, but it may not become a source of catalog, graph, project,
compiler, build, or evidence semantics.

