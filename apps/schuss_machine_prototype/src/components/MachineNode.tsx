import { memo } from "react";
import {
  Handle,
  Position,
  type Node,
  type NodeProps,
} from "@xyflow/react";

import type { MachineBlockView } from "../model/types";

export type MachineNodeData = Record<string, unknown> & {
  block: MachineBlockView;
  controlLabels: string[];
  downstream: boolean;
  exactTarget: boolean;
  expanded: boolean;
  hasSelection: boolean;
  onSelect: (blockId: string) => void;
  onToggleExpanded: (blockId: string) => void;
  selected: boolean;
};

export type MachineFlowNode = Node<MachineNodeData, "machine">;

const kindNames: Record<string, string> = {
  audio: "BODY",
  control: "GESTURE",
  display: "GILLS",
  effect: "EFFECT",
  event: "EVENT",
  output: "OUTPUT",
  source: "VOICE",
  state: "STATE",
};

function MachineNodeComponent({ data }: NodeProps<MachineFlowNode>) {
  const { block } = data;
  const classes = [
    "machine-node",
    `machine-node--${block.kind}`,
    data.expanded ? "is-expanded" : "",
    data.selected ? "is-selected" : "",
    data.exactTarget ? "is-exact-target" : "",
    data.downstream ? "is-downstream" : "",
    data.hasSelection && !data.downstream ? "is-dimmed" : "",
  ].filter(Boolean).join(" ");

  const select = () => data.onSelect(block.presentation_block_id);
  return (
    <article
      className={classes}
    >
      <Handle id="in-left" position={Position.Left} type="target" />
      <Handle id="in-top" position={Position.Top} type="target" />
      <Handle id="out-right" position={Position.Right} type="source" />
      <Handle id="out-bottom" position={Position.Bottom} type="source" />
      <button
        aria-label={`${block.label}. ${block.summary}`}
        className="machine-node__select nodrag"
        onClick={select}
        type="button"
      >
        <header className="machine-node__header">
          <span className="machine-node__kind">{kindNames[block.kind] ?? block.kind.toUpperCase()}</span>
        </header>
        <h3>{block.label}</h3>
        <p>{block.summary}</p>
        {data.controlLabels.length > 0 && (
          <div className="machine-node__controls" aria-label="Mapped Gills controls" role="group">
            {data.controlLabels.slice(0, 4).map((label) => <span key={label}>{label}</span>)}
            {data.controlLabels.length > 4 && <span>+{data.controlLabels.length - 4}</span>}
          </div>
        )}
        {data.expanded && (
          <div className="machine-node__parts">
            {block.parts.map((part) => <span key={part}>{part}</span>)}
          </div>
        )}
      </button>
      <button
        aria-label={`${data.expanded ? "Collapse" : "Expand"} ${block.label}`}
        aria-pressed={data.expanded}
        className="machine-node__expand nodrag"
        onClick={() => data.onToggleExpanded(block.presentation_block_id)}
        type="button"
      >
        {data.expanded ? "−" : "+"}
      </button>
    </article>
  );
}

export const MachineNode = memo(MachineNodeComponent);
