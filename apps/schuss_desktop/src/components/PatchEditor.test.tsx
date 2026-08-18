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
    build_request_references: [{
      build_request_id: "schuss-build-request-000005",
      revision: 1,
      content_hash: hash("d"),
    }],
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

const externalProjectValue = {
  project: {
    ...projectValue.project,
    revision: 3,
    content_hash: hash("e"),
    primary_graph_reference: {
      ...graphReference,
      revision: 2,
      content_hash: hash("f"),
    },
  },
  validation: {},
};

const externalGraphValue = {
  graph: {
    ...graphValue.graph,
    ...externalProjectValue.project.primary_graph_reference,
    nodes: [
      ...graphValue.graph.nodes,
      {
        node_id: "graph-node-000002",
        contract_reference: {
          component_contract_id: "schuss-component-contract-000002",
          revision: 1,
          content_hash: hash("2"),
        },
        parameter_values: [],
        attribute_values: [],
      },
    ],
  },
  component_contract_closure: [
    ...graphValue.component_contract_closure,
    {
      component_contract_id: "schuss-component-contract-000002",
      revision: 1,
      content_hash: hash("2"),
      display_name: "New project voice",
      ports: [],
      parameters: [],
      attributes: [],
    },
  ],
};

const shellProps = {
  projects: [{
    workspace: "/tmp/test-patch",
    project_reference: {
      project_id: projectValue.project.project_id,
      revision: projectValue.project.revision,
      content_hash: projectValue.project.content_hash,
    },
    graph_reference: graphReference,
    display_name: "Test patch",
  }],
  projectsRoot: "/tmp",
  drawer: { open: true, tab: "objects" as const, width: 340 },
  libraryStage: null,
  shellError: null,
  onDirtyChange: vi.fn(),
  onSelectProject: vi.fn(),
  onCreateProject: vi.fn(),
  onOpenSettings: vi.fn(),
  onChooseDrawer: vi.fn(),
  onDrawerWidth: vi.fn(),
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

    render(<PatchEditor {...shellProps} workspace="/tmp/test-patch" />);
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
    render(<PatchEditor {...shellProps} workspace="/tmp/test-patch" onDirtyChange={onDirtyChange} />);

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

  it("keeps build and USB authority behind explicit session operations", async () => {
    const user = userEvent.setup();
    const target = {
      artifact_kind: "target-executable",
      media_type: "application/x-elf",
      producer_stage: "target-compile-link",
      byte_sha256: "e".repeat(64),
      byte_length: 4096,
      portable_locator: `sha256/${"e".repeat(64)}`,
    };
    dispatchMock.mockImplementation((request: { operation: string }) => {
      if (request.operation === "project.inspect") return Promise.resolve(projectValue);
      if (request.operation === "graph.inspect") return Promise.resolve(graphValue);
      if (request.operation === "build.session.start") return Promise.resolve({
        session_id: "build-session-000001",
        status: "success",
        phase: "completed",
        build_request_reference: projectValue.project.build_request_references[0],
        progress: [],
        stage_outcomes: [],
        artifacts: [target],
        evidence_levels: [],
        diagnostics: [],
      });
      if (request.operation === "device.session.discover") return Promise.resolve({
        status: "complete",
        device_count: 1,
        discovery_was_explicit: true,
        background_monitoring: false,
        sessions: [{
          session_id: "device-session-000001",
          status: "available",
          transport: "usb-bulk-libusb",
          transport_location: "usb:bus-001/ports-2",
          usb_identity: { vendor_id: "0x16C0", product_id: "0x0444", usb_serial: "core" },
          board_identity: { product: "Ksoloti Core", cpu_serial: "cpu", firmware: { version: "1.1.0.0", crc: "5021D42A", patch_entrypoint: "0x20011000" } },
          identity_status: "complete",
          compatibility: "compatible",
          diagnostics: [],
        }],
      });
      if (request.operation === "device.upload.start") return Promise.resolve({
        session_id: "upload-session-000001",
        status: "success",
        phase: "completed",
        device_session_id: "device-session-000001",
        build_session_id: "build-session-000001",
        artifact: target,
        device_binary: { byte_sha256: "f".repeat(64), byte_length: 512, load_address: "0x20011000" },
        start_patch_requested: true,
        progress: [],
        verification: "byte-for-byte-match",
        outcome: {},
        diagnostics: [],
      });
      throw new Error(`Unexpected operation ${request.operation}`);
    });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<PatchEditor {...shellProps} workspace="/tmp/test-patch" />);

    await user.click(await screen.findByRole("button", { name: "Build" }));
    expect(await screen.findByText("4 KB target executable")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Device" }));
    expect(await screen.findByText("compatible · 1.1.0.0")).toBeInTheDocument();
    expect(screen.getByText("CPU cpu · CRC 5021D42A")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Upload to volatile RAM" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: /Ksoloti Core/ }));
    await user.click(screen.getByRole("button", { name: "Upload to volatile RAM" }));

    expect(confirm).toHaveBeenCalledWith(expect.stringContaining("volatile RAM"));
    expect(confirm).toHaveBeenCalledWith(expect.stringContaining("cpu"));
    const upload = dispatchMock.mock.calls.find(([request]) => (request as { operation: string }).operation === "device.upload.start")?.[0] as { payload: Record<string, unknown> };
    expect(upload.payload).toMatchObject({
      device_session_id: "device-session-000001",
      build_session_id: "build-session-000001",
      artifact_sha256: "e".repeat(64),
      upload_intent: "explicit-volatile-ram",
      start_patch: true,
    });
  });

  it("reloads a clean external successor and selects its newly inserted node", async () => {
    let projectInspections = 0;
    dispatchMock.mockImplementation((request: { operation: string; payload: Record<string, unknown> }) => {
      if (request.operation === "project.inspect") {
        projectInspections += 1;
        return Promise.resolve(projectInspections === 1 ? projectValue : externalProjectValue);
      }
      if (request.operation === "graph.inspect") {
        const reference = request.payload.graph_reference as { revision: number };
        return Promise.resolve(reference.revision === 1 ? graphValue : externalGraphValue);
      }
      throw new Error(`Unexpected operation ${request.operation}`);
    });
    render(<PatchEditor {...shellProps} workspace="/tmp/test-patch" />);
    expect(await screen.findByRole("textbox", { name: "Patch name" })).toHaveValue("Test patch");
    await waitFor(() => expect(projectInspections).toBe(1));

    await act(async () => { window.dispatchEvent(new Event("focus")); });
    await waitFor(() => expect(projectInspections).toBeGreaterThanOrEqual(2));

    expect(await screen.findByText(/Accepted revision r3 loaded.*New project voice is selected and ready to connect/)).toBeVisible();
    expect(screen.getByText("schuss-project-900001 · r3")).toBeVisible();
  });

  it("preserves a dirty draft when an external accepted revision appears", async () => {
    const user = userEvent.setup();
    let projectInspections = 0;
    dispatchMock.mockImplementation((request: { operation: string }) => {
      if (request.operation === "project.inspect") {
        projectInspections += 1;
        return Promise.resolve(projectInspections === 1 ? projectValue : externalProjectValue);
      }
      if (request.operation === "graph.inspect") return Promise.resolve(graphValue);
      throw new Error(`Unexpected operation ${request.operation}`);
    });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<PatchEditor {...shellProps} workspace="/tmp/test-patch" />);
    const name = await screen.findByRole("textbox", { name: "Patch name" });
    await user.clear(name);
    await user.type(name, "Keep this draft");

    await act(async () => { window.dispatchEvent(new Event("focus")); });

    expect(await screen.findByText(/Accepted revision r3 is available.*unsaved edits are preserved/)).toBeVisible();
    expect(name).toHaveValue("Keep this draft");
    await user.click(screen.getByRole("button", { name: "Review and reload" }));
    expect(confirm).toHaveBeenCalledOnce();
    expect(name).toHaveValue("Keep this draft");
  });
});
