import { useCallback, useEffect, useMemo, useState } from "react";
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
import {
  graphInspectRequest,
  profileTransactRequest,
  projectHistoryRequest,
  projectInspectRequest,
  projectRevertRequest,
} from "../core/patcherRequests";
import type {
  ComponentContract,
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
} from "../core/types";
import { ObjectLibrary } from "./ObjectLibrary";
import { PatchNode, type PatchFlowNode } from "./PatchNode";
import styles from "./PatchEditor.module.css";

type Props = {
  workspace: string;
  onClose: () => void;
  onDirtyChange: (dirty: boolean) => void;
};
type PositionMap = Record<string, { x: number; y: number }>;
const NODE_TYPES = { patchNode: PatchNode };

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

export function PatchEditor({ workspace, onClose, onDirtyChange }: Props) {
  const [project, setProject] = useState<ProjectManifest | null>(null);
  const [graph, setGraph] = useState<DspGraph | null>(null);
  const [contracts, setContracts] = useState<Record<string, ComponentContract>>({});
  const [positions, setPositions] = useState<PositionMap>({});
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [pending, setPending] = useState<GraphEdit[]>([]);
  const [draftName, setDraftName] = useState("");
  const [loadStage, setLoadStage] = useState<string | null>("Opening accepted project…");
  const [saveStage, setSaveStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showObjects, setShowObjects] = useState(true);
  const [history, setHistory] = useState<ProjectHistoryValue | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [loadToken, setLoadToken] = useState(0);
  const loading = loadStage !== null;
  const saving = saveStage !== null;

  useEffect(() => {
    let active = true;
    setLoadStage("Opening accepted project…");
    setError(null);
    dispatchDesktopOperation<ProjectInspectValue>(projectInspectRequest(), workspace)
      .then(async (projectValue) => {
        if (active) setLoadStage("Loading graph closure…");
        const graphValue = await dispatchDesktopOperation<GraphInspectValue>(graphInspectRequest(projectValue.project.primary_graph_reference), workspace);
        if (!active) return;
        setProject(projectValue.project);
        setGraph(graphValue.graph);
        setDraftName(graphValue.graph.display_name);
        setContracts(Object.fromEntries(graphValue.component_contract_closure.map((contract) => [contract.component_contract_id, contract])));
        setPositions(initialPositions(graphValue.graph.nodes));
        setSelectedNodeId(graphValue.graph.nodes[0]?.node_id ?? null);
        setPending([]);
      })
      .catch((caught: unknown) => active && setError(caught instanceof Error ? caught.message : "Project could not be opened."))
      .finally(() => active && setLoadStage(null));
    return () => { active = false; };
  }, [loadToken, workspace]);

  const flowNodes = useMemo<PatchFlowNode[]>(() => (graph?.nodes ?? []).flatMap((node) => {
    const contract = contracts[node.contract_reference.component_contract_id];
    if (!contract) return [];
    return [{ id: node.node_id, type: "patchNode", position: positions[node.node_id] ?? { x: 0, y: 0 }, data: { contract, nodeId: node.node_id } }];
  }), [contracts, graph, positions]);

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
  const hasNameChange = graph !== null && draftName.trim() !== graph.display_name;
  const dirty = pending.length > 0 || hasNameChange;
  const unsavedCount = pending.length + (hasNameChange ? 1 : 0);

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
    setLoadStage("Reloading accepted project…");
    setLoadToken((value) => value + 1);
  }, [dirty]);

  const openHistory = useCallback(async () => {
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

  if (loading) return <div className={styles.startup} role="status" aria-live="polite">{loadStage}</div>;
  if (!graph || !project) return <div className={styles.startup}><strong>Project unavailable</strong><span role="alert">{error}</span><div className={styles.startupActions}><button type="button" onClick={() => reloadAccepted(false)}>Retry</button><button type="button" onClick={onClose}>Back to patches</button></div></div>;

  return (
    <section className={styles.editor} data-library={showObjects}>
      <header className={styles.toolbar}>
        <button className={styles.back} type="button" onClick={onClose}>‹ Patches</button>
        <input disabled={saving} value={draftName} onChange={(event) => setDraftName(event.currentTarget.value)} aria-label="Patch name" />
        <code>{project.project_id} · r{project.revision}</code>
        <span className={styles.spacer} />
        <button type="button" disabled={saving} onClick={() => setShowObjects((value) => !value)}>{showObjects ? "Hide objects" : "Objects"}</button>
        <button type="button" disabled={saving || historyLoading} onClick={() => void openHistory()}>{historyLoading ? "Loading history…" : "History"}</button>
        <button type="button" disabled={!dirty || saving} onClick={() => reloadAccepted(false)}>Discard</button>
        <button className={styles.save} type="button" disabled={!dirty || saving} onClick={() => void save()}>{saveStage ?? "Save"}</button>
      </header>
      {showObjects && <aside className={styles.objectDrawer}><ObjectLibrary mode="drawer" onAdd={addComponent} /></aside>}
      <div className={styles.canvas}>
        <ReactFlow
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
        {error && <div className={styles.canvasError} role="alert"><span>{error}</span><div>{dirty && <button type="button" disabled={saving} onClick={() => void save()}>Retry save</button>}<button type="button" disabled={saving} onClick={() => reloadAccepted(true)}>Reload accepted</button></div></div>}
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
        <span aria-live="polite">{saveStage ?? (dirty ? `${unsavedCount} unsaved edit${unsavedCount === 1 ? "" : "s"}` : "Saved")}</span>
        <span>{graph.nodes.length} nodes · {graph.connections.length} cables</span>
        <span>Build unavailable in this slice · No device session</span>
      </footer>
      {showHistory && <aside className={styles.history}>
        <header><strong>Project history</strong><button type="button" disabled={saving} onClick={() => setShowHistory(false)} aria-label="Close history">×</button></header>
        <div>{history?.ancestry.slice().reverse().map((entry, index) => <article key={entry.project_reference.content_hash}><strong>Revision {entry.project_reference.revision}</strong><span>{entry.owned_member_count} owned records</span>{index > 0 && <button type="button" disabled={saving} onClick={() => void revert(entry.project_reference)}>Revert</button>}</article>) ?? <p role="status">Loading history…</p>}</div>
      </aside>}
    </section>
  );
}
