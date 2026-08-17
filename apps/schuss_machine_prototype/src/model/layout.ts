import type { ElkNode } from "elkjs/lib/elk-api";

import type { MachineView } from "./types";

let elkPromise: Promise<import("elkjs/lib/elk-api").ELK> | null = null;

function getElk(): Promise<import("elkjs/lib/elk-api").ELK> {
  elkPromise ??= import("elkjs/lib/elk.bundled.js").then(({ default: ELK }) => new ELK());
  return elkPromise;
}

export const collapsedNodeSize = { height: 132, width: 236 } as const;
export const expandedNodeSize = { height: 220, width: 252 } as const;

export interface LayoutedBlock {
  height: number;
  id: string;
  rowIndex: number;
  width: number;
  x: number;
  y: number;
}

export interface MachineLayout {
  blocks: LayoutedBlock[];
  height: number;
  width: number;
}

interface LayoutedRow {
  children: Array<{ height: number; id: string; width: number; x: number; y: number }>;
  height: number;
  width: number;
}

async function layoutRow(
  view: MachineView,
  row: readonly string[],
  rowIndex: number,
  expandedBlockIds: ReadonlySet<string>,
): Promise<LayoutedRow> {
  const elk = await getElk();
  const rowIds = new Set(row);
  const graphInput: ElkNode = {
    id: `machine-row-${rowIndex}`,
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.edgeRouting": "ORTHOGONAL",
      "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
      "elk.padding": "[top=16,left=16,bottom=16,right=16]",
      "elk.spacing.nodeNode": "34",
      "elk.layered.spacing.nodeNodeBetweenLayers": "46",
    },
    children: row.map((id) => {
      const size = expandedBlockIds.has(id) ? expandedNodeSize : collapsedNodeSize;
      return { id, ...size };
    }),
    edges: view.edges
      .filter((edge) => rowIds.has(edge.source_block_id) && rowIds.has(edge.destination_block_id))
      .map((edge) => ({
        id: edge.presentation_edge_id,
        sources: [edge.source_block_id],
        targets: [edge.destination_block_id],
      })),
  };
  const graph = await elk.layout(graphInput);

  const children = (graph.children ?? []).map((child) => {
    if (
      typeof child.x !== "number"
      || typeof child.y !== "number"
      || typeof child.width !== "number"
      || typeof child.height !== "number"
    ) {
      throw new Error(`Machine prototype failed closed: ELK did not position ${child.id}`);
    }
    return { id: child.id, x: child.x, y: child.y, width: child.width, height: child.height };
  });
  return {
    children,
    height: graph.height ?? Math.max(...children.map((child) => child.y + child.height), 0),
    width: graph.width ?? Math.max(...children.map((child) => child.x + child.width), 0),
  };
}

export async function layoutMachineRows(
  view: MachineView,
  expandedBlockIds: ReadonlySet<string>,
): Promise<MachineLayout> {
  const rows = await Promise.all(view.rows.map((row, index) => layoutRow(view, row, index, expandedBlockIds)));
  const width = Math.max(...rows.map((row) => row.width), 0);
  const blocks: LayoutedBlock[] = [];
  let y = 20;

  rows.forEach((row, rowIndex) => {
    const centeredOffset = (width - row.width) / 2;
    for (const child of row.children) {
      blocks.push({
        ...child,
        rowIndex,
        x: child.x + centeredOffset,
        y: child.y + y,
      });
    }
    y += row.height + 88;
  });

  return {
    blocks,
    height: Math.max(320, y - 68),
    width: Math.max(640, width),
  };
}
