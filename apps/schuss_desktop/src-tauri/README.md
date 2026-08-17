# Tauri shell boundary

The native shell exposes one command: `dispatch_read_only_operation`. Rust
validates the exact envelope, operation-specific request shape, size limit,
allowlist, and expected result metadata before returning a canonical Schuss
result. A persistent Python child loads the exact core context once.

Only `core:default` is granted to the main window. No general process API,
filesystem, shell, HTTP plugin, project-write, build, device, or hardware
permission is exposed to the renderer. Bundling and release packaging remain
disabled.
