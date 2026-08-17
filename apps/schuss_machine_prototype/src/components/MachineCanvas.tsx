import { useEffect, useMemo, useState } from "react";
import {
  Background,
  BackgroundVariant,
  MarkerType,
  ReactFlow,
  type Edge,
  useReactFlow,
} from "@xyflow/react";

import { layoutMachineRows, type MachineLayout } from "../model/layout";
import { panelLabelForSlot, slotIdsForBlock } from "../model/machineModel";
import type { MachineView, PerformanceMode, SignalKind } from "../model/types";
import { MachineNode, type MachineFlowNode } from "./MachineNode";

const nodeTypes = { machine: MachineNode };

const edgeColors: Record<SignalKind, string> = {
  audio: "#e67a43",
  control: "#4e8fff",
  display: "#41b88a",
  event: "#4e8fff",
};

interface MachineCanvasProps {
  downstreamBlockIds: readonly string[];
  exactTargetBlockIds: readonly string[];
  expandedBlockIds: ReadonlySet<string>;
  mode: PerformanceMode;
  onSelectBlock: (blockId: string) => void;
  onToggleExpanded: (blockId: string) => void;
  selectedBlockId: string | null;
  view: MachineView;
}

function CanvasControls() {
  const flow = useReactFlow();
  return (
    <div aria-label="Canvas view controls" className="canvas-controls" role="group">
      <button aria-label="Zoom in" onClick={() => void flow.zoomIn()} type="button">+</button>
      <button aria-label="Zoom out" onClick={() => void flow.zoomOut()} type="button">−</button>
      <button aria-label="Fit machine in view" onClick={() => void flow.fitView({ padding: 0.08 })} type="button">⌗</button>
    </div>
  );
}

export function MachineCanvas({
  downstreamBlockIds,
  exactTargetBlockIds,
  expandedBlockIds,
  mode,
  onSelectBlock,
  onToggleExpanded,
  selectedBlockId,
  view,
}: MachineCanvasProps) {
  const [layout, setLayout] = useState<MachineLayout | null>(null);
  const [layoutError, setLayoutError] = useState<string | null>(null);
  const expandedKey = [...expandedBlockIds].sort().join("|");

  useEffect(() => {
    let active = true;
    setLayout(null);
    setLayoutError(null);
    void layoutMachineRows(view, expandedBlockIds)
      .then((nextLayout) => {
        if (active) setLayout(nextLayout);
      })
      .catch((error: unknown) => {
        if (active) setLayoutError(error instanceof Error ? error.message : String(error));
      });
    return () => { active = false; };
  }, [expandedBlockIds, expandedKey, view]);

  const exactTargets = useMemo(() => new Set(exactTargetBlockIds), [exactTargetBlockIds]);
  const downstream = useMemo(() => new Set(downstreamBlockIds), [downstreamBlockIds]);
  const positions = useMemo(
    () => new Map(layout?.blocks.map((block) => [block.id, block])),
    [layout],
  );

  const nodes = useMemo<MachineFlowNode[]>(() => view.blocks.flatMap((block) => {
    const position = positions.get(block.presentation_block_id);
    if (!position) return [];
    const controlLabels = slotIdsForBlock(view, block.presentation_block_id, mode)
      .map((slotId) => panelLabelForSlot(view, slotId, mode));
    return [{
      data: {
        block,
        controlLabels,
        downstream: downstream.has(block.presentation_block_id),
        exactTarget: exactTargets.has(block.presentation_block_id),
        expanded: expandedBlockIds.has(block.presentation_block_id),
        hasSelection: downstream.size > 0,
        onSelect: onSelectBlock,
        onToggleExpanded,
        selected: selectedBlockId === block.presentation_block_id,
      },
      draggable: false,
      focusable: false,
      id: block.presentation_block_id,
      position: { x: position.x, y: position.y },
      style: { height: position.height, width: position.width },
      type: "machine" as const,
    }];
  }), [
    downstream,
    exactTargets,
    expandedBlockIds,
    mode,
    onSelectBlock,
    onToggleExpanded,
    positions,
    selectedBlockId,
    view,
  ]);

  const rowByBlock = useMemo(() => new Map(layout?.blocks.map((block) => [block.id, block.rowIndex])), [layout]);
  const edges = useMemo<Edge[]>(() => view.edges.map((edge) => {
    const sameRow = rowByBlock.get(edge.source_block_id) === rowByBlock.get(edge.destination_block_id);
    const active = downstream.has(edge.source_block_id) && downstream.has(edge.destination_block_id);
    const color = edgeColors[edge.signal_kind];
    return {
      animated: active,
      className: active ? "machine-edge is-active" : "machine-edge",
      deletable: false,
      focusable: false,
      id: edge.presentation_edge_id,
      markerEnd: { color, height: 14, type: MarkerType.ArrowClosed, width: 14 },
      source: edge.source_block_id,
      sourceHandle: sameRow ? "out-right" : "out-bottom",
      style: {
        opacity: downstream.size > 0 && !active ? 0.18 : 0.78,
        stroke: color,
        strokeWidth: active ? 3.2 : 2.2,
      },
      target: edge.destination_block_id,
      targetHandle: sameRow ? "in-left" : "in-top",
      type: "smoothstep",
    };
  }), [downstream, rowByBlock, view.edges]);

  if (layoutError) return <div className="canvas-error" role="alert">{layoutError}</div>;
  if (!layout) return <div className="canvas-loading">Arranging the machine…</div>;

  return (
    <div className="machine-canvas" style={{ minHeight: Math.min(680, Math.max(470, layout.height)) }}>
      <ReactFlow
        aria-label={`${view.identity.display_name} source-evidenced machine flow`}
        deleteKeyCode={null}
        edges={edges}
        edgesFocusable={false}
        fitView
        fitViewOptions={{ maxZoom: 1, minZoom: 0.48, padding: 0.08 }}
        key={`${view.config.key}:${expandedKey}`}
        maxZoom={1.45}
        minZoom={0.3}
        nodeTypes={nodeTypes}
        nodes={nodes}
        nodesConnectable={false}
        nodesDraggable={false}
        nodesFocusable={false}
        panOnScroll
        proOptions={{ hideAttribution: true }}
        selectionOnDrag={false}
        zoomOnDoubleClick={false}
      >
        <Background color="#b9c2cf" gap={22} size={1} variant={BackgroundVariant.Dots} />
        <CanvasControls />
      </ReactFlow>
      <div className="signal-legend" aria-label="Signal path legend" role="group">
        <span><i className="signal-control" /> control / event</span>
        <span><i className="signal-audio" /> audio</span>
        <span><i className="signal-display" /> feedback</span>
      </div>
    </div>
  );
}
