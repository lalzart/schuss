import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

import {
  INPUT_HANDLE_TOP,
  INPUT_ROW_HEIGHT,
  type GillsInputFlowNode,
} from "../model/graph";
import { labelForMode, SIGNAL_COLORS } from "../model/types";

function GillsInputRackNodeComponent({ data, selected }: NodeProps<GillsInputFlowNode>) {
  return (
    <article className={`patch-node gills-input-node${selected ? " is-selected" : ""}`}>
      <header className="patch-node__header">
        <span className="node-eyebrow node-eyebrow--profile">DEVICE PROFILE</span>
        <h2>Gills controls</h2>
        <p>Stable physical slots. Each cable shows the mapped instrument facet.</p>
      </header>
      <div className="rack-caption">
        <span>PHYSICAL</span>
        <span>MAPPED MEANING</span>
      </div>
      <div className="control-rows">
        {data.machine.controls.map((mapping, index) => (
          <div
            className={`control-row signal-${mapping.kind}${mapping.mapped ? "" : " is-unmapped"}`}
            key={mapping.controlId}
          >
            <strong>{mapping.physicalLabel}</strong>
            <span>
              {labelForMode(mapping, data.mode)}
              {mapping.detail && <small>{mapping.detail}</small>}
            </span>
            <Handle
              className={`signal-handle signal-handle--${mapping.mapped ? mapping.kind : "unmapped"}`}
              id={mapping.controlId}
              isConnectable={false}
              position={Position.Right}
              style={{
                background: mapping.mapped ? SIGNAL_COLORS[mapping.kind] : "#697386",
                top: INPUT_HANDLE_TOP + index * INPUT_ROW_HEIGHT,
              }}
              type="source"
            />
          </div>
        ))}
      </div>
      <footer className="node-boundary-note">Profile slots · not catalog objects</footer>
    </article>
  );
}

export const GillsInputRackNode = memo(GillsInputRackNodeComponent);
