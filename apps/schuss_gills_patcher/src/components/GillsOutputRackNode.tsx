import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

import {
  OUTPUT_HANDLE_TOP,
  OUTPUT_ROW_HEIGHT,
  type GillsOutputFlowNode,
} from "../model/graph";
import { SIGNAL_COLORS } from "../model/types";

function GillsOutputRackNodeComponent({ data, selected }: NodeProps<GillsOutputFlowNode>) {
  return (
    <article className={`patch-node gills-output-node${selected ? " is-selected" : ""}`}>
      <header className="patch-node__header">
        <span className="node-eyebrow node-eyebrow--profile">DEVICE PROFILE</span>
        <h2>Gills outputs</h2>
        <p>Audio and visible feedback owned by the device profile.</p>
      </header>
      <div className="output-rows">
        {data.machine.outputs.map((output, index) => (
          <div className={`output-row signal-${output.kind}`} key={output.outputId}>
            <Handle
              className={`signal-handle signal-handle--${output.kind}`}
              id={output.targetId}
              isConnectable={false}
              position={Position.Left}
              style={{
                background: SIGNAL_COLORS[output.kind],
                top: OUTPUT_HANDLE_TOP + index * OUTPUT_ROW_HEIGHT,
              }}
              type="target"
            />
            <span className="output-row__icon" aria-hidden="true">
              {output.kind === "audio" ? "◒" : output.outputId.startsWith("stage") ? "●" : "▰"}
            </span>
            <span>
              <strong>{output.label}</strong>
              <small>{output.detail}</small>
            </span>
          </div>
        ))}
      </div>
      <footer className="node-boundary-note">Profile services · not palette nodes</footer>
    </article>
  );
}

export const GillsOutputRackNode = memo(GillsOutputRackNodeComponent);

