import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
  type DragEvent,
} from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type NodeChange,
  type NodeMouseHandler,
  type XYPosition,
} from "@xyflow/react";

import { catalogItemByFamily, CATALOG_DRAG_MIME } from "../model/catalog";
import {
  buildCatalogDraftNode,
  createPatchSnapshot,
  buildReferenceEdges,
  buildReferenceNodes,
  isCatalogDraftNode,
  type PatcherNode,
} from "../model/graph";
import type { PatchSnapshot } from "../model/patchLibrary";
import type { CatalogItem, MachineDefinition, PerformanceMode } from "../model/types";
import { CatalogDraftNode } from "./CatalogDraftNode";
import { GillsInputRackNode } from "./GillsInputRackNode";
import { GillsOutputRackNode } from "./GillsOutputRackNode";
import { InstrumentCompoundNode } from "./InstrumentCompoundNode";
import { SelectionInspector } from "./SelectionInspector";

const nodeTypes = {
  catalogDraft: CatalogDraftNode,
  gillsInput: GillsInputRackNode,
  gillsOutput: GillsOutputRackNode,
  instrument: InstrumentCompoundNode,
};

export interface PatcherCanvasHandle {
  addCatalogItem: (item: CatalogItem) => void;
  getSnapshot: () => PatchSnapshot;
}

interface PatcherCanvasProps {
  initialSnapshot: PatchSnapshot | null;
  machine: MachineDefinition;
  mode: PerformanceMode;
  onDirty: () => void;
  onModeChange: (mode: PerformanceMode) => void;
}

const PatcherCanvasInner = forwardRef<PatcherCanvasHandle, PatcherCanvasProps>(
  function PatcherCanvasInner({
    initialSnapshot,
    machine,
    mode,
    onDirty,
    onModeChange,
  }, ref) {
    const referenceNodes = useMemo(
      () => buildReferenceNodes(machine, mode, onModeChange),
      [machine, mode, onModeChange],
    );
    const referenceEdges = useMemo(() => buildReferenceEdges(machine), [machine]);
    const initialNodes = useMemo(() => {
      if (initialSnapshot === null || initialSnapshot.machineKey !== machine.key) {
        return referenceNodes;
      }
      const restoredReferences = referenceNodes.map((node) => ({
        ...node,
        position: initialSnapshot.referencePositions[node.id as keyof typeof initialSnapshot.referencePositions]
          ?? node.position,
      }));
      const restoredCatalogNodes = initialSnapshot.catalogNodes.flatMap((placement) => {
        const item = catalogItemByFamily(placement.familyId);
        if (item === undefined) return [];
        const node = buildCatalogDraftNode(item, placement.position, placement.localIndex);
        return node === null ? [] : [node];
      });
      return [...restoredReferences, ...restoredCatalogNodes];
    }, [initialSnapshot, machine.key, referenceNodes]);
    const [nodes, setNodes, onNodesChange] = useNodesState<PatcherNode>(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(referenceEdges);
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const draftCounter = useRef(
      initialSnapshot?.catalogNodes.reduce(
        (highest, placement) => Math.max(highest, placement.localIndex),
        0,
      ) ?? 0,
    );
    const flow = useReactFlow<PatcherNode>();

    useEffect(() => {
      setNodes((current) => {
        const positions = new Map(
          current
            .filter((node) => !isCatalogDraftNode(node))
            .map((node) => [node.id, node.position]),
        );
        const nextReferences = referenceNodes.map((node) => ({
          ...node,
          position: positions.get(node.id) ?? node.position,
        }));
        return [...nextReferences, ...current.filter(isCatalogDraftNode)];
      });
      setEdges(referenceEdges);
      setSelectedNodeId(null);
    }, [referenceEdges, referenceNodes, setEdges, setNodes]);

    const fitAfterPlacement = useCallback(() => {
      window.requestAnimationFrame(() => {
        void flow.fitView({ duration: 320, maxZoom: 1, padding: 0.08 });
      });
    }, [flow]);

    const addAtPosition = useCallback((item: CatalogItem, position: XYPosition) => {
      draftCounter.current += 1;
      const nextNode = buildCatalogDraftNode(item, position, draftCounter.current);
      if (nextNode === null) return;
      setNodes((current) => [...current, nextNode]);
      setSelectedNodeId(nextNode.id);
      onDirty();
      fitAfterPlacement();
    }, [fitAfterPlacement, onDirty, setNodes]);

    const addAtDefaultPosition = useCallback((item: CatalogItem) => {
      const draftCount = nodes.filter(isCatalogDraftNode).length;
      addAtPosition(item, {
        x: 420 + (draftCount % 3) * 280,
        y: 880 + Math.floor(draftCount / 3) * 230,
      });
    }, [addAtPosition, nodes]);

    useImperativeHandle(ref, () => ({
      addCatalogItem: addAtDefaultPosition,
      getSnapshot: () => createPatchSnapshot(machine.key, mode, nodes),
    }), [addAtDefaultPosition, machine.key, mode, nodes]);

    const handleDrop = useCallback((event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      const familyId = event.dataTransfer.getData(CATALOG_DRAG_MIME);
      const item = catalogItemByFamily(familyId);
      if (item === undefined || !item.selectable) return;
      const position = flow.screenToFlowPosition({ x: event.clientX, y: event.clientY });
      addAtPosition(item, position);
    }, [addAtPosition, flow]);

    const handleDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
    }, []);

    const handleNodeClick: NodeMouseHandler<PatcherNode> = useCallback((_event, node) => {
      setSelectedNodeId(node.id);
    }, []);

    const handleNodesChange = useCallback((changes: NodeChange<PatcherNode>[]) => {
      onNodesChange(changes);
      if (changes.some((change) => (
        change.type === "remove"
        || (change.type === "position" && change.dragging === false)
      ))) onDirty();
    }, [onDirty, onNodesChange]);

    const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? null;

    const deleteSelectedDraft = useCallback(() => {
      if (selectedNode === null || !isCatalogDraftNode(selectedNode)) return;
      setNodes((current) => current.filter((node) => node.id !== selectedNode.id));
      setSelectedNodeId(null);
      onDirty();
    }, [onDirty, selectedNode, setNodes]);

    const minimapColor = useCallback((node: PatcherNode) => {
      if (node.type === "gillsInput" || node.type === "gillsOutput") return "#41a9ff";
      if (node.type === "instrument") return "#ffb15c";
      return "#b78cff";
    }, []);

    return (
      <div className="patcher-canvas" onDragOver={handleDragOver} onDrop={handleDrop}>
        <ReactFlow<PatcherNode>
          aria-label={`${machine.displayName} Gills patch graph`}
          edges={edges}
          edgesFocusable={false}
          fitView
          fitViewOptions={{ maxZoom: 0.92, minZoom: 0.38, padding: 0.06 }}
          maxZoom={1.45}
          minZoom={0.24}
          nodeTypes={nodeTypes}
          nodes={nodes}
          nodesConnectable={false}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onNodesChange={handleNodesChange}
          onPaneClick={() => setSelectedNodeId(null)}
          panOnScroll
          proOptions={{ hideAttribution: true }}
          selectionOnDrag
          snapGrid={[14, 14]}
          snapToGrid
          zoomOnDoubleClick={false}
        >
          <Background color="#3a4150" gap={22} size={1} variant={BackgroundVariant.Dots} />
          <Controls position="top-right" showInteractive={false} />
          <MiniMap
            className="patcher-minimap"
            maskColor="rgba(6, 8, 12, 0.74)"
            nodeColor={minimapColor}
            pannable
            position="bottom-right"
            zoomable
          />
        </ReactFlow>

        <div className="signal-legend" aria-label="Cable legend" role="group">
          <span><i className="legend-control" /> continuous</span>
          <span><i className="legend-event" /> event</span>
          <span><i className="legend-audio" /> audio</span>
          <span><i className="legend-feedback" /> feedback</span>
        </div>

        <div className="canvas-help">
          <strong>Drag to move · scroll to pan</strong>
          <span>Drop accepted catalog objects anywhere</span>
        </div>

        <SelectionInspector
          node={selectedNode}
          onDeleteDraft={deleteSelectedDraft}
          onDismiss={() => setSelectedNodeId(null)}
        />
      </div>
    );
  },
);

export const PatcherCanvas = forwardRef<PatcherCanvasHandle, PatcherCanvasProps>(
  function PatcherCanvas(props, ref) {
    return (
      <ReactFlowProvider>
        <PatcherCanvasInner {...props} ref={ref} />
      </ReactFlowProvider>
    );
  },
);
