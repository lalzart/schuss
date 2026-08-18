# React presentation boundary

The renderer owns selection, viewport, node positions, one versioned
projects-root/last-workspace preference, panel state, form drafts, and the
ordered unsaved edit draft. Semantic data
arrives only through `src/core/bridge.ts`; exact request construction lives in
`src/core/requests.ts` and `src/core/patcherRequests.ts`.

`DesktopApp` always mounts `PatchEditor`; there is no Patches/Objects
application routing. Its remembered root is passed to
`workspace.projects.list` and `workspace.project.create`, so the renderer never
enumerates project files or allocates semantic identities.

`ObjectLibrary` is the patch drawer's implementation list. It defaults to the
existing contracted readiness projection, preserves an explicit All catalog
view, and expands object detail in place. In an explicit workspace it also presents
`project.objects.list` separately and resolves one local definition through
`project.object.inspect`; the permanent catalog remains unchanged.
`PatchEditor` projects one exact `graph.inspect` result
into React Flow and submits the ordered edit proposal through
`project.profile.transact`, which validates before atomic persistence. It owns
no catalog matcher, component interface, graph persistence format, compiler
logic, or project filesystem access. Failed saves retain the draft; reload is
explicit when it would discard unsaved work.

The editor checks the accepted project reference through `project.inspect`.
Clean external successors reload through the same operation path; dirty drafts
remain untouched until guarded reload confirmation.

Build/device presentation submits only the six v12 session operations. It
polls opaque process-local handles and renders structured state; it never sees
an output root, artifact bytes, USB handle, memory address, or arbitrary
command. Discovery and volatile upload each require an explicit interaction,
and upload adds a confirmation before the core-owned write begins.
