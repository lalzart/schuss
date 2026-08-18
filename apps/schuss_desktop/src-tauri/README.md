# Tauri shell boundary

The native shell exposes one command: `dispatch_desktop_operation`. Rust
validates the exact operation/version allowlist, canonical envelope, size
limits, explicit absolute workspace path, and expected result metadata. One
persistent Python child loads the exact base context and caches project
services by explicit workspace.

Only `core:default` is granted. There is no renderer filesystem, shell, HTTP,
build-process, device, raw USB, or hardware permission. The allowlisted session
requests reach core-owned services inside the persistent Python process;
bundling and release packaging remain disabled.
