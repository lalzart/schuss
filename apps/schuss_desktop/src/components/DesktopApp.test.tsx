import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DESKTOP_PREFERENCES_KEY } from "../core/desktopPreferences";
import { DesktopApp } from "./DesktopApp";

const dispatchMock = vi.fn();

vi.mock("../core/bridge", () => ({
  CoreOperationError: class CoreOperationError extends Error {
    code: string;
    constructor(code: string, message: string) { super(message); this.code = code; }
  },
  dispatchDesktopOperation: (...args: unknown[]) => dispatchMock(...args),
}));

vi.mock("./PatchEditor", () => ({
  PatchEditor: (props: {
    workspace: string | null;
    projectsRoot: string;
    onCreateProject: () => void;
    onOpenSettings: () => void;
  }) => <div>
    <span>Canvas mounted</span>
    <span>{props.workspace ?? "No project"}</span>
    <span>{props.projectsRoot || "No root"}</span>
    <button type="button" onClick={props.onCreateProject}>New patch</button>
    <button type="button" onClick={props.onOpenSettings}>Settings</button>
  </div>,
}));

const hash = (value: string) => `sha256:${value.repeat(64)}`;
const project = {
  workspace: "/tmp/schuss-projects/test-patch",
  project_reference: { project_id: "schuss-project-900001", revision: 3, content_hash: hash("a") },
  graph_reference: { graph_id: "schuss-graph-900001", revision: 2, content_hash: hash("b") },
  display_name: "Test patch",
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => { resolve = resolvePromise; });
  return { promise, resolve };
}

describe("DesktopApp workspace shell", () => {
  beforeEach(() => {
    dispatchMock.mockReset();
    localStorage.clear();
  });

  it("keeps the canvas mounted while a one-time projects root is configured", async () => {
    const user = userEvent.setup();
    dispatchMock.mockResolvedValue({
      projects_root: "/tmp/schuss-projects",
      project_count: 1,
      rejected_child_count: 0,
      truncated: false,
      projects: [project],
    });
    render(<DesktopApp />);

    expect(screen.getByText("Canvas mounted")).toBeVisible();
    const dialog = screen.getByRole("dialog", { name: "Desktop settings" });
    await user.type(within(dialog).getByLabelText("Projects root"), "/tmp/schuss-projects");
    await user.click(within(dialog).getByRole("button", { name: "Use projects root" }));

    expect(await screen.findByText(project.workspace)).toBeVisible();
    expect(dispatchMock).toHaveBeenCalledWith(
      expect.objectContaining({ operation: "workspace.projects.list" }),
      "/tmp/schuss-projects",
    );
    expect(JSON.parse(localStorage.getItem(DESKTOP_PREFERENCES_KEY) ?? "{}")).toMatchObject({
      version: 2,
      projectsRoot: "/tmp/schuss-projects",
      lastWorkspace: project.workspace,
    });
  });

  it("creates a named patch through one core-owned operation", async () => {
    const user = userEvent.setup();
    localStorage.setItem(DESKTOP_PREFERENCES_KEY, JSON.stringify({
      version: 2,
      projectsRoot: "/tmp/schuss-projects",
      lastWorkspace: project.workspace,
      drawer: { open: true, tab: "objects", width: 340 },
    }));
    const created = deferred<{ projects_root: string; project: typeof project; creation: Record<string, unknown> }>();
    dispatchMock
      .mockResolvedValueOnce({ projects_root: "/tmp/schuss-projects", project_count: 1, rejected_child_count: 0, truncated: false, projects: [project] })
      .mockImplementationOnce(() => created.promise);
    render(<DesktopApp />);
    expect(await screen.findByText(project.workspace)).toBeVisible();

    await user.click(screen.getByRole("button", { name: "New patch" }));
    const dialog = screen.getByRole("dialog", { name: "Create patch" });
    const name = within(dialog).getByLabelText("Patch name");
    await user.clear(name);
    await user.type(name, "New texture");
    await user.click(within(dialog).getByRole("button", { name: "Create patch" }));
    expect(within(dialog).getByRole("button", { name: "Creating accepted project…" })).toBeDisabled();

    const next = { ...project, workspace: "/tmp/schuss-projects/new-texture", display_name: "New texture" };
    await act(async () => created.resolve({ projects_root: "/tmp/schuss-projects", project: next, creation: {} }));
    await waitFor(() => expect(screen.getByText(next.workspace)).toBeVisible());
    expect(dispatchMock).toHaveBeenLastCalledWith(
      expect.objectContaining({
        schema_version: "schuss-operation-request-v14",
        operation: "workspace.project.create",
        payload: { display_name: "New texture" },
      }),
      "/tmp/schuss-projects",
    );
  });
});
