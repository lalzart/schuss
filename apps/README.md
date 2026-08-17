# Applications

Future Schuss user-facing applications live here. Applications are clients of
the shared catalog, graph, project, compiler, build, and diagnostic operations;
they do not own alternate semantics or persistence.

No application is currently implemented. ADR 0014 explicitly authorizes the
unnumbered UI-architecture milestone described in
`docs/APPLICATION_SPINE_PLAN.md`: client boundaries, state ownership,
transport, interaction design, fixtures, and a bounded technical spike. The
bounded `schuss_desktop` structural initialization is complete, but the broader
architecture milestone remains open. UI implementation, including the object
drawer and transparent graph canvas, remains separately gated; see
`docs/STATUS.md` and `docs/DESKTOP_UI_BOUNDARY.md`.
