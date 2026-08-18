import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  type Connection,
  type Edge,
  type Node,
  type OnNodeDrag,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { dispatchDesktopOperation } from "../core/bridge";
import type { DrawerTab } from "../core/desktopPreferences";
import {
  buildSessionInspectRequest,
  buildSessionStartRequest,
  deviceDiscoverRequest,
  deviceUploadInspectRequest,
  deviceUploadStartRequest,
  graphInspectRequest,
  profileTransactRequest,
  projectHistoryRequest,
  projectInspectRequest,
  projectRevertRequest,
} from "../core/patcherRequests";
import type {
  BuildSessionValue,
  ComponentContract,
  DeviceDiscoveryValue,
  DeviceSessionValue,
  DspGraph,
  GraphConnectionRecord,
  GraphEdit,
  GraphInspectValue,
  GraphNodeRecord,
  GraphReference,
  ProjectHistoryValue,
  ProjectInspectValue,
  ProjectManifest,
  ProjectReference,
  UploadSessionValue,
  WorkspaceProject,
} from "../core/types";
import { ObjectLibrary } from "./ObjectLibrary";
import { PatchNode, type PatchFlowNode } from "./PatchNode";
import styles from "./PatchEditor.module.css";

type Props = {
  workspace: string | null;
  projects: WorkspaceProject[];
  projectsRoot: string;
  drawer: { open: boolean; tab: DrawerTab; width: number };
  libraryStage: string | null;
  shellError: string | null;
  onDirtyChange: (dirty: boolean) => void;
  onSelectProject: (workspace: string) => void;
  onCreateProject: () => void;
  onOpenSettings: () => void;
  onChooseDrawer: (tab: DrawerTab) => void;
  onDrawerWidth: (width: number) => void;
};
type PositionMap = Record<string, { x: number; y: number }>;
const NODE_TYPES = { patchNode: PatchNode };
const ACTIVE_SESSION_STATUSES = new Set(["queued", "running"]);
const ACCEPTED_PROJECT_CHECK_MS = 4_000;

function graphReference(graph: DspGraph): GraphReference {
  return { graph_id: graph.graph_id, revision: graph.revision, content_hash: graph.content_hash };
}

function projectReference(project: ProjectManifest): ProjectReference {
  return { project_id: project.project_id, revision: project.revision, content_hash: project.content_hash };
}

function allocatedId(prefix: string, values: string[]): string {
  const used = new Set(values);
  for (let index = 1; index < 1_000_000; index += 1) {
    const candidate = `${prefix}-${String(index).padStart(6, "0")}`;
    if (!used.has(candidate)) return candidate;
  }
  throw new Error(`No ${prefix} identity remains.`);
}

function initialPositions(nodes: GraphNodeRecord[]): PositionMap {
  return Object.fromEntries(nodes.map((node, index) => [node.node_id, { x: 90 + (index % 3) * 300, y: 70 + Math.floor(index / 3) * 210 }]));
}

export function PatchEditor({
  workspace,
  projects,
  projectsRoot,
  drawer,
  libraryStage,
  shellError,
  onDirtyChange,
  onSelectProject,
  onCreateProject,
  onOpenSettings,
  onChooseDrawer,
  onDrawerWidth,
}: Props) {
  const [project, setProject] = useState<ProjectManifest | null>(null);
  const [graph, setGraph] = useState<DspGraph | null>(null);
  const [contracts, setContracts] = useState<Record<string, ComponentContract>>({});
  const [positions, setPositions] = useState<PositionMap>({});
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [pending, setPending] = useState<GraphEdit[]>([]);
  const [draftName, setDraftName] = useState("");
  const [loadStage, setLoadStage] = useState<string | null>(null);
  const [saveStage, setSaveStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ProjectHistoryValue | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [loadToken, setLoadToken] = useState(0);
  const [externalProject, setExternalProject] = useState<ProjectManifest | null>(null);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);
  const externalRefresh = useRef<{ previousNodeIds: string[]; revision: number } | null>(null);
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [buildSession, setBuildSession] = useState<BuildSessionValue | null>(null);
  const [devices, setDevices] = useState<DeviceSessionValue[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [uploadSession, setUploadSession] = useState<UploadSessionValue | null>(null);
  const [uploadStarting, setUploadStarting] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [startAfterVerify, setStartAfterVerify] = useState(true);
  const loading = loadStage !== null;
  const saving = saveStage !== null;
  const hasNameChange = graph !== null && draftName.trim() !== graph.display_name;
  const dirty = pending.length > 0 || hasNameChange;
  const unsavedCount = pending.length + (hasNameChange ? 1 : 0);

  useEffect(() => {
    if (!workspace) {
      setProject(null);
      setGraph(null);
      setContracts({});
      setPending([]);
      setDraftName("");
      setSelectedNodeId(null);
      setLoadStage(null);
      return undefined;
    }
    let active = true;
    setLoadStage("Opening accepted project…");
    setError(null);
    dispatchDesktopOperation<ProjectInspectValue>(projectInspectRequest(), workspace)
      .then(async (projectValue) => {
        if (active) setLoadStage("Loading graph closure…");
        const graphValue = await dispatchDesktopOperation<GraphInspectValue>(graphInspectRequest(projectValue.project.primary_graph_reference), workspace);
        if (!active) return;
        const nextContracts = Object.fromEntries(graphValue.component_contract_closure.map((contract) => [contract.component_contract_id, contract]));
        const refresh = externalRefresh.current;
        const priorNodes = new Set(refresh?.previousNodeIds ?? []);
        const addedNode = refresh
          ? graphValue.graph.nodes.find((node) => !priorNodes.has(node.node_id)) ?? null
          : null;
        setProject(projectValue.project);
        setGraph(graphValue.graph);
        setDraftName(graphValue.graph.display_name);
        setContracts(nextContracts);
        setPositions(initialPositions(graphValue.graph.nodes));
        setSelectedNodeId(addedNode?.node_id ?? graphValue.graph.nodes[0]?.node_id ?? null);
        setPending([]);
        setExternalProject(null);
        if (refresh) {
          const displayName = addedNode
            ? nextContracts[addedNode.contract_reference.component_contract_id]?.display_name
            : null;
          setSyncNotice(displayName
            ? `Accepted revision r${refresh.revision} loaded. ${displayName} is selected and ready to connect.`
            : `Accepted revision r${refresh.revision} loaded.`);
          externalRefresh.current = null;
        }
        setBuildSession(null);
        setUploadSession(null);
        setDevices([]);
        setSelectedDeviceId(null);
      })
      .catch((caught: unknown) => active && setError(caught instanceof Error ? caught.message : "Project could not be opened."))
      .finally(() => active && setLoadStage(null));
    return () => { active = false; };
  }, [loadToken, workspace]);

  useEffect(() => {
    if (!workspace || !project || !graph || loading || saving) return undefined;
    let active = true;
    let checking = false;
    let refreshScheduled = false;
    const checkAcceptedProject = async () => {
      if (!active || checking || refreshScheduled || document.hidden) return;
      checking = true;
      try {
        const value = await dispatchDesktopOperation<ProjectInspectValue>(projectInspectRequest(), workspace);
        if (!active || value.project.content_hash === project.content_hash) return;
        if (dirty) {
          setExternalProject((current) => current?.content_hash === value.project.content_hash ? current : value.project);
          return;
        }
        refreshScheduled = true;
        externalRefresh.current = {
          previousNodeIds: graph.nodes.map((node) => node.node_id),
          revision: value.project.revision,
        };
        setLoadStage("Loading accepted external revision…");
        setLoadToken((current) => current + 1);
      } catch {
        // The active project remains authoritative; a later focus or interval retries.
      } finally {
        checking = false;
      }
    };
    const onFocus = () => { void checkAcceptedProject(); };
    window.addEventListener("focus", onFocus);
    const timer = window.setInterval(() => { void checkAcceptedProject(); }, ACCEPTED_PROJECT_CHECK_MS);
    return () => {
      active = false;
      window.removeEventListener("focus", onFocus);
      window.clearInterval(timer);
    };
  }, [dirty, graph, loading, project, saving, workspace]);

  useEffect(() => {
    if (!buildSession || !ACTIVE_SESSION_STATUSES.has(buildSession.status)) return undefined;
    let active = true;
    const timer = window.setTimeout(() => {
      dispatchDesktopOperation<BuildSessionValue>(buildSessionInspectRequest(buildSession.session_id), workspace)
        .then((value) => active && setBuildSession(value))
        .catch((caught: unknown) => active && setWorkflowError(caught instanceof Error ? caught.message : "Build status is unavailable."));
    }, 350);
    return () => { active = false; window.clearTimeout(timer); };
  }, [buildSession, workspace]);

  useEffect(() => {
    if (!uploadSession || !ACTIVE_SESSION_STATUSES.has(uploadSession.status)) return undefined;
    let active = true;
    const timer = window.setTimeout(() => {
      dispatchDesktopOperation<UploadSessionValue>(deviceUploadInspectRequest(uploadSession.session_id), workspace)
        .then((value) => active && setUploadSession(value))
        .catch((caught: unknown) => active && setWorkflowError(caught instanceof Error ? caught.message : "Upload status is unavailable."));
    }, 250);
    return () => { active = false; window.clearTimeout(timer); };
  }, [uploadSession, workspace]);

  const flowNodes = useMemo<PatchFlowNode[]>(() => (graph?.nodes ?? []).flatMap((node) => {
    const contract = contracts[node.contract_reference.component_contract_id];
    if (!contract) return [];
    return [{ id: node.node_id, type: "patchNode", position: positions[node.node_id] ?? { x: 0, y: 0 }, selected: node.node_id === selectedNodeId, data: { contract, nodeId: node.node_id } }];
  }), [contracts, graph, positions, selectedNodeId]);

  const flowEdges = useMemo<Edge[]>(() => (graph?.connections ?? []).map((connection) => ({
    id: connection.connection_id,
    source: connection.source.node_id,
    sourceHandle: connection.source.facet_id,
    target: connection.destination.node_id,
    targetHandle: connection.destination.facet_id,
    type: "smoothstep",
  })), [graph]);

  const selectedNode = graph?.nodes.find((node) => node.node_id === selectedNodeId) ?? null;
  const selectedContract = selectedNode ? contracts[selectedNode.contract_reference.component_contract_id] : null;
  const buildRequest = project?.build_request_references.length === 1 ? project.build_request_references[0] : null;
  const buildBusy = buildSession !== null && ACTIVE_SESSION_STATUSES.has(buildSession.status);
  const uploadBusy = uploadStarting || (uploadSession !== null && ACTIVE_SESSION_STATUSES.has(uploadSession.status));
  const targetExecutable = buildSession?.status === "success"
    ? buildSession.artifacts.find((artifact) => artifact.artifact_kind === "target-executable") ?? null
    : null;
  const selectedDevice = devices.find((device) => device.session_id === selectedDeviceId) ?? null;

  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);

  useEffect(() => {
    if (!dirty) return undefined;
    const warnBeforeClose = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeClose);
    return () => window.removeEventListener("beforeunload", warnBeforeClose);
  }, [dirty]);

  const connect = useCallback((connection: Connection) => {
    if (!graph || !connection.source || !connection.target || !connection.sourceHandle || !connection.targetHandle) return;
    const record: GraphConnectionRecord = {
      connection_id: allocatedId("graph-connection", graph.connections.map((item) => item.connection_id)),
      source: { node_id: connection.source, facet_id: connection.sourceHandle },
      destination: { node_id: connection.target, facet_id: connection.targetHandle },
    };
    setGraph({ ...graph, connections: [...graph.connections, record] });
    setPending((current) => [...current, { edit: "add-connection", connection: record }]);
  }, [graph]);

  const deleteEdges = useCallback((edges: Edge[]) => {
    if (!graph) return;
    const ids = new Set(edges.map((edge) => edge.id));
    setGraph({ ...graph, connections: graph.connections.filter((connection) => !ids.has(connection.connection_id)) });
    setPending((current) => [...current, ...edges.map((edge): GraphEdit => ({ edit: "remove-connection", connection_id: edge.id }))]);
  }, [graph]);

  const deleteNodes = useCallback((nodes: Node[]) => {
    if (!graph) return;
    const ids = new Set(nodes.map((node) => node.id));
    const attached = graph.connections.filter((connection) => ids.has(connection.source.node_id) || ids.has(connection.destination.node_id));
    setGraph({ ...graph, nodes: graph.nodes.filter((node) => !ids.has(node.node_id)), connections: graph.connections.filter((connection) => !attached.includes(connection)) });
    setPending((current) => [
      ...current,
      ...attached.map((connection): GraphEdit => ({ edit: "remove-connection", connection_id: connection.connection_id })),
      ...nodes.map((node): GraphEdit => ({ edit: "remove-node", node_id: node.id })),
    ]);
    setSelectedNodeId(null);
  }, [graph]);

  const addComponent = useCallback((contract: ComponentContract) => {
    if (!graph) return;
    const node: GraphNodeRecord = {
      node_id: allocatedId("graph-node", graph.nodes.map((item) => item.node_id)),
      contract_reference: {
        component_contract_id: contract.component_contract_id,
        revision: contract.revision,
        content_hash: contract.content_hash,
      },
      parameter_values: [],
      attribute_values: [],
    };
    setContracts((current) => ({ ...current, [contract.component_contract_id]: contract }));
    setGraph({ ...graph, nodes: [...graph.nodes, node] });
    setPositions((current) => ({ ...current, [node.node_id]: { x: 120 + (graph.nodes.length % 3) * 280, y: 100 + Math.floor(graph.nodes.length / 3) * 190 } }));
    setPending((current) => [...current, { edit: "add-node", node }]);
    setSelectedNodeId(node.node_id);
  }, [graph]);

  const setParameter = useCallback((facetId: string, value: string) => {
    if (!graph || !selectedNodeId || !value) return;
    setGraph({
      ...graph,
      nodes: graph.nodes.map((node) => node.node_id !== selectedNodeId ? node : {
        ...node,
        parameter_values: [...node.parameter_values.filter((item) => item.facet_id !== facetId), { facet_id: facetId, value }],
      }),
    });
    setPending((current) => [
      ...current.filter((edit) => !(edit.edit === "set-node-parameter" && edit.node_id === selectedNodeId && edit.facet_id === facetId)),
      { edit: "set-node-parameter", node_id: selectedNodeId, facet_id: facetId, value },
    ]);
  }, [graph, selectedNodeId]);

  const setAttribute = useCallback((facetId: string, value: string) => {
    if (!graph || !selectedNodeId || !value) return;
    setGraph({
      ...graph,
      nodes: graph.nodes.map((node) => node.node_id !== selectedNodeId ? node : {
        ...node,
        attribute_values: [...node.attribute_values.filter((item) => item.facet_id !== facetId), { facet_id: facetId, value }],
      }),
    });
    setPending((current) => [
      ...current.filter((edit) => !(edit.edit === "set-node-attribute" && edit.node_id === selectedNodeId && edit.facet_id === facetId)),
      { edit: "set-node-attribute", node_id: selectedNodeId, facet_id: facetId, value },
    ]);
  }, [graph, selectedNodeId]);

  const save = useCallback(async () => {
    if (!graph || !project || !dirty) return;
    const edits = [...pending];
    if (hasNameChange) edits.unshift({ edit: "set-graph-display-name", display_name: draftName.trim() });
    setSaveStage("Validating and saving revision…");
    setError(null);
    try {
      await dispatchDesktopOperation(profileTransactRequest(projectReference(project), graphReference(graph), edits), workspace);
      setLoadStage("Reloading accepted revision…");
      setLoadToken((value) => value + 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Patch could not be saved.");
    } finally {
      setSaveStage(null);
    }
  }, [dirty, draftName, graph, hasNameChange, pending, project, workspace]);

  const reloadAccepted = useCallback((confirmDiscard: boolean) => {
    if (
      confirmDiscard
      && dirty
      && !window.confirm("Reload the accepted project and discard these unsaved edits?")
    ) {
      return;
    }
    if (graph && externalProject) {
      externalRefresh.current = {
        previousNodeIds: graph.nodes.map((node) => node.node_id),
        revision: externalProject.revision,
      };
    }
    setExternalProject(null);
    setSyncNotice(null);
    setLoadStage("Reloading accepted project…");
    setLoadToken((value) => value + 1);
  }, [dirty, externalProject, graph]);

  const openHistory = useCallback(async () => {
    setShowWorkflow(false);
    setShowHistory(true);
    setHistoryLoading(true);
    setError(null);
    try {
      setHistory(await dispatchDesktopOperation<ProjectHistoryValue>(projectHistoryRequest(), workspace));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "History could not be loaded.");
    } finally {
      setHistoryLoading(false);
    }
  }, [workspace]);

  const startBuild = useCallback(async () => {
    if (!buildRequest || dirty || buildBusy) return;
    setShowHistory(false);
    setShowWorkflow(true);
    setWorkflowError(null);
    setUploadSession(null);
    try {
      setBuildSession(await dispatchDesktopOperation<BuildSessionValue>(buildSessionStartRequest(buildRequest), workspace));
    } catch (caught) {
      setWorkflowError(caught instanceof Error ? caught.message : "Build could not be started.");
    }
  }, [buildBusy, buildRequest, dirty, workspace]);

  const discoverDevices = useCallback(async () => {
    if (!buildRequest || discovering) return;
    setShowHistory(false);
    setShowWorkflow(true);
    setDiscovering(true);
    setWorkflowError(null);
    try {
      const value = await dispatchDesktopOperation<DeviceDiscoveryValue>(deviceDiscoverRequest(buildRequest), workspace);
      setDevices(value.sessions);
      setSelectedDeviceId(null);
    } catch (caught) {
      setDevices([]);
      setSelectedDeviceId(null);
      setWorkflowError(caught instanceof Error ? caught.message : "Device discovery failed.");
    } finally {
      setDiscovering(false);
    }
  }, [buildRequest, discovering, workspace]);

  const startUpload = useCallback(async () => {
    if (!selectedDevice || !targetExecutable || !buildSession || dirty || uploadBusy) return;
    const action = startAfterVerify ? "upload, verify, and start" : "upload and verify";
    if (!window.confirm(`Explicitly ${action} this patch in volatile RAM on ${selectedDevice.board_identity.product ?? "the selected device"} (${selectedDevice.board_identity.cpu_serial ?? "unknown CPU identity"})?`)) return;
    setUploadStarting(true);
    setWorkflowError(null);
    try {
      setUploadSession(await dispatchDesktopOperation<UploadSessionValue>(deviceUploadStartRequest(
        selectedDevice.session_id,
        buildSession.session_id,
        targetExecutable.byte_sha256,
        startAfterVerify,
      ), workspace));
    } catch (caught) {
      setWorkflowError(caught instanceof Error ? caught.message : "Volatile upload could not be started.");
    } finally {
      setUploadStarting(false);
    }
  }, [buildSession, dirty, selectedDevice, startAfterVerify, targetExecutable, uploadBusy, workspace]);

  const revert = useCallback(async (target: ProjectReference) => {
    if (!project || !window.confirm(`Revert to project revision ${target.revision}?`)) return;
    setSaveStage("Reverting project…");
    setError(null);
    try {
      await dispatchDesktopOperation(projectRevertRequest(projectReference(project), target), workspace);
      setShowHistory(false);
      setLoadStage("Reloading accepted revision…");
      setLoadToken((value) => value + 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Project could not be reverted.");
    } finally {
      setSaveStage(null);
    }
  }, [project, workspace]);

  const moved: OnNodeDrag = useCallback((_, node) => {
    setPositions((current) => ({ ...current, [node.id]: node.position }));
  }, []);

  const beginDrawerResize = useCallback((event: ReactPointerEvent<HTMLElement>) => {
    const startX = event.clientX;
    const startWidth = drawer.width;
    const move = (next: PointerEvent) => onDrawerWidth(Math.min(460, Math.max(280, startWidth + next.clientX - startX)));
    const stop = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop, { once: true });
  }, [drawer.width, onDrawerWidth]);

  const resizeDrawerWithKeyboard = useCallback((event: ReactKeyboardEvent<HTMLElement>) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    onDrawerWidth(drawer.width + (event.key === "ArrowRight" ? 16 : -16));
  }, [drawer.width, onDrawerWidth]);

  const editorStyle = { "--drawer-width": `${drawer.width}px` } as CSSProperties;

  return (
    <section className={styles.editor} data-library={drawer.open} style={editorStyle}>
      <header className={styles.toolbar}>
        <div className={styles.drawerTabs} aria-label="Patcher drawers">
          <button type="button" data-active={drawer.open && drawer.tab === "objects"} aria-pressed={drawer.open && drawer.tab === "objects"} onClick={() => onChooseDrawer("objects")}>Objects</button>
          <button type="button" data-active={drawer.open && drawer.tab === "patches"} aria-pressed={drawer.open && drawer.tab === "patches"} onClick={() => onChooseDrawer("patches")}>Patches</button>
        </div>
        <input disabled={saving || !graph} value={draftName} placeholder="No patch open" onChange={(event) => setDraftName(event.currentTarget.value)} aria-label="Patch name" />
        {project && <code>{project.project_id} · r{project.revision}</code>}
        <span className={styles.spacer} />
        <button type="button" disabled={saving || dirty || buildBusy || !buildRequest} onClick={() => void startBuild()}>{buildBusy ? "Building…" : "Build"}</button>
        <button type="button" disabled={saving || discovering || !buildRequest} onClick={() => void discoverDevices()}>{discovering ? "Finding…" : "Device"}</button>
        <button type="button" disabled={saving || historyLoading || !project} onClick={() => void openHistory()}>{historyLoading ? "Loading history…" : "History"}</button>
        <button type="button" disabled={!dirty || saving} onClick={() => reloadAccepted(false)}>Discard</button>
        <button className={styles.save} type="button" disabled={!dirty || saving} onClick={() => void save()}>{saveStage ?? "Save"}</button>
        <button className={styles.settings} type="button" onClick={onOpenSettings} aria-label="Desktop settings">Settings</button>
      </header>
      {drawer.open && <aside className={styles.objectDrawer} aria-label={drawer.tab === "objects" ? "Objects drawer" : "Patches drawer"}>
        {drawer.tab === "objects" ? (
          <ObjectLibrary onAdd={addComponent} projectRevision={project?.revision} workspace={workspace ?? undefined} />
        ) : (
          <div className={styles.patchDrawer}>
            <header><div><span>PATCHES</span><strong>{projects.length}</strong></div><button type="button" onClick={onCreateProject}>New</button></header>
            <div className={styles.projectRoot}><span>PROJECTS ROOT</span><code>{projectsRoot || "Not configured"}</code></div>
            <div className={styles.patchRows}>
              {projects.map((item) => <button
                type="button"
                key={item.project_reference.content_hash}
                data-active={item.workspace === workspace}
                onClick={() => onSelectProject(item.workspace)}
              ><span className={styles.patchRoute} /><span><strong>{item.display_name}</strong><code>{item.project_reference.project_id} · r{item.project_reference.revision}</code></span></button>)}
              {!libraryStage && projects.length === 0 && <p>No accepted projects in this root.</p>}
            </div>
            {libraryStage && <p className={styles.drawerStage} role="status">{libraryStage}</p>}
            {shellError && <p className={styles.drawerError} role="status">{shellError}</p>}
          </div>
        )}
        <div className={styles.drawerResize} role="separator" aria-label="Resize drawer" aria-orientation="vertical" aria-valuemin={280} aria-valuemax={460} aria-valuenow={drawer.width} tabIndex={0} onKeyDown={resizeDrawerWithKeyboard} onPointerDown={beginDrawerResize} />
      </aside>}
      <div className={styles.canvas}>
        <ReactFlow
          key={graph?.content_hash ?? workspace ?? "empty-patcher"}
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={NODE_TYPES}
          onNodeClick={(_, node) => setSelectedNodeId(node.id)}
          onNodeDragStop={moved}
          onConnect={connect}
          onEdgesDelete={deleteEdges}
          onNodesDelete={deleteNodes}
          fitView
          minZoom={0.25}
          maxZoom={1.8}
          deleteKeyCode={["Backspace", "Delete"]}
        >
          <Background color="#252b33" gap={20} size={1} />
          <Controls showInteractive={false} />
        </ReactFlow>
        {(!workspace || loading || !graph || !project) && <div className={styles.startup} role="status" aria-live="polite">
          {!projectsRoot ? <><strong>Choose a projects root</strong><span>Set it once; Schuss will remember it and open directly into the patcher next time.</span><button type="button" onClick={onOpenSettings}>Open settings</button></> : loading || libraryStage ? <><span className={styles.startupPulse} /><strong>{loadStage ?? libraryStage}</strong><span>The canvas is ready while the accepted project closure loads.</span></> : <><strong>Project unavailable</strong><span role="alert">{error ?? shellError ?? "No accepted project could be opened."}</span><div className={styles.startupActions}><button type="button" onClick={() => reloadAccepted(false)}>Retry</button><button type="button" onClick={() => onChooseDrawer("patches")}>Browse patches</button></div></>}
        </div>}
        {externalProject && <div className={styles.externalUpdate} role="status">
          <span>Accepted revision r{externalProject.revision} is available. Your unsaved edits are preserved.</span>
          <button type="button" disabled={saving} onClick={() => reloadAccepted(true)}>Review and reload</button>
        </div>}
        {!externalProject && syncNotice && <div className={styles.syncNotice} role="status">
          <span>{syncNotice}</span>
          <button type="button" onClick={() => setSyncNotice(null)} aria-label="Dismiss project update">×</button>
        </div>}
        {workspace && graph && error && <div className={styles.canvasError} role="alert"><span>{error}</span><div>{dirty && <button type="button" disabled={saving} onClick={() => void save()}>Retry save</button>}<button type="button" disabled={saving} onClick={() => reloadAccepted(true)}>Reload accepted</button></div></div>}
      </div>
      <aside className={styles.inspector}>
        {selectedNode && selectedContract ? <>
          <header><span>NODE</span><code>{selectedNode.node_id}</code></header>
          <h2>{selectedContract.display_name}</h2>
          <section>
            <h3>Parameters</h3>
            {selectedContract.parameters.length === 0 ? <p>None</p> : selectedContract.parameters.map((parameter) => {
              const value = selectedNode.parameter_values.find((item) => item.facet_id === parameter.facet_id)?.value ?? parameter.default;
              return <label key={parameter.facet_id}><span>{parameter.display_label}</span><input value={value} onChange={(event) => setParameter(parameter.facet_id, event.currentTarget.value)} /></label>;
            })}
          </section>
          {selectedContract.attributes.length > 0 && <section>
            <h3>Attributes</h3>
            {selectedContract.attributes.map((attribute) => {
              const value = selectedNode.attribute_values.find((item) => item.facet_id === attribute.facet_id)?.value ?? attribute.default;
              return <label key={attribute.facet_id}><span>{attribute.display_label}</span><input value={value} onChange={(event) => setAttribute(attribute.facet_id, event.currentTarget.value)} /></label>;
            })}
          </section>}
          <section><h3>Ports</h3>{selectedContract.ports.map((port) => <div className={styles.port} key={port.facet_id}><span>{port.display_label}</span><code>{port.direction} · {port.port_type.rate}</code></div>)}</section>
          <footer><code>{selectedContract.component_contract_id}@{selectedContract.revision}</code></footer>
        </> : <div className={styles.noSelection}>Select a node to inspect it.</div>}
      </aside>
      <footer className={styles.statusbar}>
        <span aria-live="polite">{libraryStage ?? saveStage ?? (graph ? dirty ? `${unsavedCount} unsaved edit${unsavedCount === 1 ? "" : "s"}` : "Saved" : "Patcher ready")}</span>
        <span>{graph?.nodes.length ?? 0} nodes · {graph?.connections.length ?? 0} cables</span>
        <span aria-live="polite">Build {buildSession?.status ?? "not run"} · Device {selectedDevice?.compatibility ?? "not checked"}</span>
      </footer>
      {showWorkflow && <aside className={styles.workflow} aria-label="Build and device">
        <header><strong>Build &amp; device</strong><button type="button" onClick={() => setShowWorkflow(false)} aria-label="Close build and device">×</button></header>
        <div>
          <section>
            <div className={styles.workflowHeading}><h3>Build</h3><span data-status={buildSession?.status}>{buildSession?.status ?? "not run"}</span></div>
            {buildSession ? <>
              <code>{buildSession.phase}</code>
              {targetExecutable && <p>{Math.ceil(targetExecutable.byte_length / 1024)} KB target executable</p>}
              {buildSession.diagnostics[0] && <p className={styles.workflowDiagnostic}>{buildSession.diagnostics[0].message}</p>}
            </> : <p>Builds the accepted revision. Save edits first.</p>}
            <button type="button" disabled={dirty || buildBusy || !buildRequest} onClick={() => void startBuild()}>{buildBusy ? "Building…" : buildSession ? "Build again" : "Build patch"}</button>
          </section>
          <section>
            <div className={styles.workflowHeading}><h3>Device</h3><span>{devices.length === 0 ? "not checked" : `${devices.length} found`}</span></div>
            <button type="button" disabled={discovering || !buildRequest} onClick={() => void discoverDevices()}>{discovering ? "Discovering…" : "Discover USB"}</button>
            {devices.map((device) => <button
              className={styles.deviceChoice}
              data-selected={device.session_id === selectedDeviceId}
              aria-pressed={device.session_id === selectedDeviceId}
              type="button"
              key={device.session_id}
              onClick={() => setSelectedDeviceId(device.session_id)}
            >
              <span>{device.board_identity.product ?? "Ksoloti"}</span>
              <code>{device.compatibility} · {device.board_identity.firmware?.version ?? "identity incomplete"}</code>
              <code>CPU {device.board_identity.cpu_serial ?? "unknown"} · CRC {device.board_identity.firmware?.crc ?? "unknown"}</code>
            </button>)}
          </section>
          <section>
            <div className={styles.workflowHeading}><h3>Volatile upload</h3><span data-status={uploadSession?.status}>{uploadSession?.status ?? "not run"}</span></div>
            {uploadSession && <>
              <code>{uploadSession.phase}</code>
              {uploadSession.status === "success" && <p>Read-back verified{uploadSession.start_patch_requested ? " · patch started" : ""}</p>}
              {uploadSession.diagnostics[0] && <p className={styles.workflowDiagnostic}>{uploadSession.diagnostics[0].message}</p>}
            </>}
            <label className={styles.startOption}><input type="checkbox" checked={startAfterVerify} onChange={(event) => setStartAfterVerify(event.currentTarget.checked)} />Start after verification</label>
            <button
              className={styles.upload}
              type="button"
              disabled={dirty || uploadBusy || selectedDevice?.compatibility !== "compatible" || !targetExecutable}
              onClick={() => void startUpload()}
            >{uploadBusy ? "Uploading…" : "Upload to volatile RAM"}</button>
          </section>
          {workflowError && <p className={styles.workflowError} role="alert">{workflowError}</p>}
        </div>
      </aside>}
      {showHistory && <aside className={styles.history}>
        <header><strong>Project history</strong><button type="button" disabled={saving} onClick={() => setShowHistory(false)} aria-label="Close history">×</button></header>
        <div>{history?.ancestry.slice().reverse().map((entry, index) => <article key={entry.project_reference.content_hash}><strong>Revision {entry.project_reference.revision}</strong><span>{entry.owned_member_count} owned records</span>{index > 0 && <button type="button" disabled={saving} onClick={() => void revert(entry.project_reference)}>Revert</button>}</article>) ?? <p role="status">Loading history…</p>}</div>
      </aside>}
    </section>
  );
}
