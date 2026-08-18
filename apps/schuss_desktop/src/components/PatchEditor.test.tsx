import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { PatchEditor } from "./PatchEditor";

const dispatchMock = vi.fn();

vi.mock("../core/bridge", () => ({
  dispatchDesktopOperation: (...args: unknown[]) => dispatchMock(...args),
}));

vi.mock("./ObjectLibrary", () => ({
  ObjectLibrary: () => <div>Object library</div>,
}));

vi.mock("@xyflow/react", () => ({
  Background: () => null,
  Controls: () => null,
  Handle: () => null,
  Position: { Left: "left", Right: "right" },
  ReactFlow: ({ children }: { children: React.ReactNode }) => <div data-testid="graph-canvas">{children}</div>,
}));

const hash = (value: string) => `sha256:${value.repeat(64)}`;
const graphReference = {
  graph_id: "schuss-graph-900001",
  revision: 1,
  content_hash: hash("a"),
};
const projectValue = {
  project: {
    project_id: "schuss-project-900001",
    revision: 2,
    content_hash: hash("b"),
    primary_graph_reference: graphReference,
    instrument_references: [],
    build_request_references: [],
  },
  validation: {},
};
const graphValue = {
  graph: {
    schema_version: "dsp-graph-v0",
    canonical_profile: "schuss-canonical-json-v1" as const,
    ...graphReference,
    display_name: "Test patch",
    nodes: [{
      node_id: "graph-node-000001",
      contract_reference: {
        component_contract_id: "schuss-component-contract-000001",
        revision: 1,
        content_hash: hash("c"),
      },
      parameter_values: [],
      attribute_values: [],
    }],
    connections: [],
    public_parameters: [],
  },
  component_contract_closure: [{
    component_contract_id: "schuss-component-contract-000001",
    revision: 1,
    content_hash: hash("c"),
    display_name: "Test object",
    ports: [],
    parameters: [],
    attributes: [],
  }],
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, reject, resolve };
}

describe("PatchEditor reliability states", () => {
  beforeEach(() => {
    dispatchMock.mockReset();
    vi.restoreAllMocks();
  });

  it("announces the dependent project and graph loading stages", async () => {
    const project = deferred<typeof projectValue>();
    const graph = deferred<typeof graphValue>();
    dispatchMock
      .mockImplementationOnce(() => project.promise)
      .mockImplementationOnce(() => graph.promise);

    render(<PatchEditor workspace="/tmp/test-patch" onClose={vi.fn()} onDirtyChange={vi.fn()} />);
    expect(screen.getByRole("status")).toHaveTextContent("Opening accepted project");

    await act(async () => project.resolve(projectValue));
    expect(screen.getByRole("status")).toHaveTextContent("Loading graph closure");

    await act(async () => graph.resolve(graphValue));
    expect(await screen.findByRole("textbox", { name: "Patch name" })).toHaveValue("Test patch");
  });

  it("keeps a failed draft, offers retry and guarded reload, and avoids a duplicate proposal call", async () => {
    const user = userEvent.setup();
    const save = deferred<never>();
    dispatchMock.mockImplementation((request: { operation: string }) => {
      if (request.operation === "project.inspect") return Promise.resolve(projectValue);
      if (request.operation === "graph.inspect") return Promise.resolve(graphValue);
      if (request.operation === "project.profile.transact") return save.promise;
      throw new Error(`Unexpected operation ${request.operation}`);
    });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const onDirtyChange = vi.fn();
    render(<PatchEditor workspace="/tmp/test-patch" onClose={vi.fn()} onDirtyChange={onDirtyChange} />);

    const name = await screen.findByRole("textbox", { name: "Patch name" });
    await user.clear(name);
    await user.type(name, "Unsaved draft");
    await waitFor(() => expect(onDirtyChange).toHaveBeenLastCalledWith(true));
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(screen.getByRole("button", { name: "Validating and saving revision…" })).toBeDisabled();

    await act(async () => save.reject(new Error("Accepted project changed.")));
    expect(await screen.findByRole("alert")).toHaveTextContent("Accepted project changed.");
    expect(name).toHaveValue("Unsaved draft");
    expect(screen.getByRole("button", { name: "Retry save" })).toBeEnabled();

    const opensBeforeReload = dispatchMock.mock.calls.filter(
      ([request]) => (request as { operation: string }).operation === "project.inspect",
    ).length;
    await user.click(screen.getByRole("button", { name: "Reload accepted" }));
    expect(confirm).toHaveBeenCalledOnce();
    expect(dispatchMock.mock.calls.filter(
      ([request]) => (request as { operation: string }).operation === "project.inspect",
    )).toHaveLength(opensBeforeReload);
    expect(dispatchMock.mock.calls.some(
      ([request]) => (request as { operation: string }).operation === "graph.transact",
    )).toBe(false);
  });
});
