# React presentation boundary

This renderer owns only ephemeral query, filter, selection, tab, panel, and
loading state. Product data arrives through `src/core/bridge.ts` as canonical
results from `application.describe`, `catalog.search`, or `catalog.inspect`.

The renderer has no direct catalog, semantic-record, workspace, filesystem,
shell, build, network-plugin, or hardware access. The Vite bridge exists only
for local browser verification and routes through the same read-only Python
allowlist against exact record set `schuss-record-set-000021@1`.
