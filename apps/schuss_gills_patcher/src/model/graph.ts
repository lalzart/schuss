import {
  MarkerType,
  type Edge,
  type Node,
  type XYPosition,
} from "@xyflow/react";

import type {
  CatalogItem,
  MachineDefinition,
  MachineKey,
  PerformanceMode,
} from "./types";
import { SIGNAL_COLORS } from "./types";
import {
  REFERENCE_NODE_IDS,
  type PatchSnapshot,
  type ReferenceNodeId,
} from "./patchLibrary";

export const INPUT_HANDLE_TOP = 104;
export const INPUT_ROW_HEIGHT = 32;
export const COMPOUND_HANDLE_TOP = 142;
export const COMPOUND_ROW_HEIGHT = 32;
export const COMPOUND_OUTPUT_TOP = 147;
export const COMPOUND_OUTPUT_ROW_HEIGHT = 42;
export const OUTPUT_HANDLE_TOP = 86;
export const OUTPUT_ROW_HEIGHT = 44;

export type GillsInputNodeData = Record<string, unknown> & {
  machine: MachineDefinition;
  mode: PerformanceMode;
};

export type InstrumentNodeData = Record<string, unknown> & {
  machine: MachineDefinition;
  mode: PerformanceMode;
  onModeChange: (mode: PerformanceMode) => void;
};

export type GillsOutputNodeData = Record<string, unknown> & {
  machine: MachineDefinition;
};

export type CatalogDraftNodeData = Record<string, unknown> & {
  item: CatalogItem;
  localIndex: number;
};

export type GillsInputFlowNode = Node<GillsInputNodeData, "gillsInput">;
export type InstrumentFlowNode = Node<InstrumentNodeData, "instrument">;
export type GillsOutputFlowNode = Node<GillsOutputNodeData, "gillsOutput">;
export type CatalogDraftFlowNode = Node<CatalogDraftNodeData, "catalogDraft">;

export type PatcherNode =
  | GillsInputFlowNode
  | InstrumentFlowNode
  | GillsOutputFlowNode
  | CatalogDraftFlowNode;

const ignoreModeChange = () => undefined;

export function buildReferenceNodes(
  machine: MachineDefinition,
  mode: PerformanceMode,
  onModeChange: (mode: PerformanceMode) => void = ignoreModeChange,
): PatcherNode[] {
  return [
    {
      data: { machine, mode },
      deletable: false,
      id: "gills-input-rack",
      position: { x: 0, y: 40 },
      type: "gillsInput",
    },
    {
      data: { machine, mode, onModeChange },
      deletable: false,
      id: "instrument-compound",
      position: { x: 360, y: 20 },
      type: "instrument",
    },
    {
      data: { machine },
      deletable: false,
      id: "gills-output-rack",
      position: { x: 940, y: 110 },
      type: "gillsOutput",
    },
  ];
}

export function buildReferenceEdges(machine: MachineDefinition): Edge[] {
  const controlEdges: Edge[] = machine.controls
    .filter((mapping) => mapping.mapped)
    .map((mapping) => ({
      animated: false,
      deletable: false,
      id: `mapping-${mapping.controlId}`,
      markerEnd: {
        color: SIGNAL_COLORS[mapping.kind],
        height: 9,
        type: MarkerType.ArrowClosed,
        width: 9,
      },
      source: "gills-input-rack",
      sourceHandle: mapping.controlId,
      style: {
        stroke: SIGNAL_COLORS[mapping.kind],
        strokeDasharray: mapping.kind === "event" ? "5 5" : undefined,
        strokeWidth: 1.7,
      },
      target: "instrument-compound",
      targetHandle: mapping.targetId,
      type: "smoothstep",
    }));

  const outputEdges: Edge[] = machine.outputs.map((output) => ({
    animated: false,
    deletable: false,
    id: `output-${output.outputId}`,
    markerEnd: {
      color: SIGNAL_COLORS[output.kind],
      height: 9,
      type: MarkerType.ArrowClosed,
      width: 9,
    },
    source: "instrument-compound",
    sourceHandle: output.outputId,
    style: {
      stroke: SIGNAL_COLORS[output.kind],
      strokeWidth: output.kind === "audio" ? 2.2 : 1.7,
    },
    target: "gills-output-rack",
    targetHandle: output.targetId,
    type: "smoothstep",
  }));

  return [...controlEdges, ...outputEdges];
}

export function buildCatalogDraftNode(
  item: CatalogItem,
  position: XYPosition,
  localIndex: number,
): CatalogDraftFlowNode | null {
  if (!item.selectable || item.contractReference === null) return null;
  return {
    data: { item, localIndex },
    deletable: true,
    id: `catalog-draft-${localIndex}`,
    position,
    type: "catalogDraft",
  };
}

export function isCatalogDraftNode(node: PatcherNode): node is CatalogDraftFlowNode {
  return node.type === "catalogDraft";
}

export function createPatchSnapshot(
  machineKey: MachineKey,
  mode: PerformanceMode,
  nodes: readonly PatcherNode[],
): PatchSnapshot {
  const referenceEntries = REFERENCE_NODE_IDS.map((nodeId) => {
    const node = nodes.find((entry) => entry.id === nodeId);
    if (node === undefined) throw new Error(`Missing reference node ${nodeId}.`);
    return [nodeId, { ...node.position }] as const;
  });
  const catalogNodes = nodes
    .filter(isCatalogDraftNode)
    .map((node) => ({
      familyId: node.data.item.familyReference.stableId,
      localIndex: node.data.localIndex,
      position: { ...node.position },
    }))
    .toSorted((left, right) => left.localIndex - right.localIndex);

  return {
    catalogNodes,
    machineKey,
    mode,
    referencePositions: Object.fromEntries(referenceEntries) as Record<
      ReferenceNodeId,
      { x: number; y: number }
    >,
  };
}
