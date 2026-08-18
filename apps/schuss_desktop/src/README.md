# React presentation boundary

The renderer owns selection, viewport, node positions, recent workspace paths,
panel state, form drafts, and the ordered unsaved edit draft. Semantic data
arrives only through `src/core/bridge.ts`; exact request construction lives in
`src/core/requests.ts` and `src/core/patcherRequests.ts`.

`ObjectLibrary` is the shared implementation list used by both the Objects
page and patch drawer. `PatchEditor` projects one exact `graph.inspect` result
into React Flow and submits the ordered edit proposal through
`project.profile.transact`, which validates before atomic persistence. It owns
no catalog matcher, component interface, graph persistence format, compiler
logic, or project filesystem access. Failed saves retain the draft; reload is
explicit when it would discard unsaved work.
