import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import type { ComponentContract } from "../core/types";
import styles from "./PatchNode.module.css";

export type PatchNodeData = { contract: ComponentContract; nodeId: string };
export type PatchFlowNode = Node<PatchNodeData, "patchNode">;

export function PatchNode({ data, selected }: NodeProps<PatchFlowNode>) {
  const inputs = data.contract.ports.filter((port) => port.direction === "inlet");
  const outputs = data.contract.ports.filter((port) => port.direction === "outlet");
  const rows = Math.max(inputs.length, outputs.length, 1);

  return (
    <article className={styles.node} data-selected={selected}>
      <header><strong>{data.contract.display_name}</strong><code>{data.nodeId.slice(-3)}</code></header>
      <div className={styles.ports} style={{ gridTemplateRows: `repeat(${rows}, 22px)` }}>
        {Array.from({ length: rows }, (_, index) => (
          <div className={styles.portRow} key={index}>
            <span className={styles.input}>
              {inputs[index] && <>
                <Handle className={styles.handle} data-rate={inputs[index].port_type.rate} type="target" position={Position.Left} id={inputs[index].facet_id} />
                <small>{inputs[index].display_label}</small>
              </>}
            </span>
            <span className={styles.output}>
              {outputs[index] && <>
                <small>{outputs[index].display_label}</small>
                <Handle className={styles.handle} data-rate={outputs[index].port_type.rate} type="source" position={Position.Right} id={outputs[index].facet_id} />
              </>}
            </span>
          </div>
        ))}
      </div>
    </article>
  );
}
