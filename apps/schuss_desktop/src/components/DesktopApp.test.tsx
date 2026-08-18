import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DesktopApp } from "./DesktopApp";

const dispatchMock = vi.fn();

vi.mock("../core/bridge", () => ({
  dispatchDesktopOperation: (...args: unknown[]) => dispatchMock(...args),
}));

vi.mock("./ObjectLibrary", () => ({ ObjectLibrary: () => <div>Objects</div> }));
vi.mock("./PatchEditor", () => ({ PatchEditor: () => <div>Editor</div> }));

const hash = (value: string) => `sha256:${value.repeat(64)}`;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

describe("DesktopApp patch creation", () => {
  beforeEach(() => {
    dispatchMock.mockReset();
    localStorage.clear();
  });

  it("announces each create stage and prevents duplicate submission", async () => {
    const user = userEvent.setup();
    const initialized = deferred<{ project: Record<string, unknown> }>();
    const forked = deferred<{ project: Record<string, unknown>; graph: Record<string, unknown> }>();
    const renamed = deferred<Record<string, unknown>>();
    dispatchMock
      .mockImplementationOnce(() => initialized.promise)
      .mockImplementationOnce(() => forked.promise)
      .mockImplementationOnce(() => renamed.promise);
    const navigate = vi.fn();
    render(<DesktopApp route={{ view: "patches" }} navigate={navigate} onEditorDirtyChange={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "New patch" }));
    const dialog = screen.getByRole("dialog", { name: "Create patch" });
    await user.clear(within(dialog).getByLabelText("Workspace"));
    await user.type(within(dialog).getByLabelText("Workspace"), "/tmp/new-schuss-patch");
    await user.click(within(dialog).getByRole("button", { name: "Create patch" }));
    expect(within(dialog).getByRole("status")).toHaveTextContent("Preparing workspace");
    expect(within(dialog).getByRole("button", { name: "Preparing workspace…" })).toBeDisabled();

    await act(async () => initialized.resolve({
      project: {
        project_id: "schuss-project-000100",
        revision: 1,
        content_hash: hash("a"),
      },
    }));
    await waitFor(() => expect(within(dialog).getByRole("status")).toHaveTextContent("Copying accepted profile"));

    await act(async () => forked.resolve({
      project: {
        project_id: "schuss-project-000100",
        revision: 2,
        content_hash: hash("b"),
      },
      graph: {
        graph_id: "schuss-graph-900001",
        revision: 1,
        content_hash: hash("c"),
      },
    }));
    await waitFor(() => expect(within(dialog).getByRole("status")).toHaveTextContent("Naming patch"));

    await act(async () => renamed.resolve({}));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith({
      view: "editor",
      workspace: "/tmp/new-schuss-patch",
    }));
    expect(dispatchMock).toHaveBeenCalledTimes(3);
  });
});
