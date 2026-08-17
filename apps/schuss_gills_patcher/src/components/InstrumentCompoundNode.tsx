import { memo, useState } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

import {
  COMPOUND_HANDLE_TOP,
  COMPOUND_OUTPUT_ROW_HEIGHT,
  COMPOUND_OUTPUT_TOP,
  COMPOUND_ROW_HEIGHT,
  type InstrumentFlowNode,
} from "../model/graph";
import { labelForMode, SIGNAL_COLORS } from "../model/types";

function InstrumentCompoundNodeComponent({ data, selected }: NodeProps<InstrumentFlowNode>) {
  const [outlineOpen, setOutlineOpen] = useState(false);

  return (
    <article className={`patch-node instrument-node${selected ? " is-selected" : ""}`}>
      <header className="patch-node__header instrument-node__header">
        <div>
          <span className="node-eyebrow node-eyebrow--compound">SOURCE COMPOUND</span>
          <h2>{data.machine.displayName}</h2>
          <p>{data.machine.subtitle}</p>
        </div>
        {data.machine.performanceModes !== null && (
          <div aria-label={`${data.machine.displayName} effect mode`} className="node-mode-switch nodrag" role="group">
            <span>MODE</span>
            {data.machine.performanceModes.map((mode) => (
              <button
                aria-pressed={data.mode === mode}
                className={data.mode === mode ? "is-active" : ""}
                key={mode}
                onClick={() => data.onModeChange(mode)}
                type="button"
              >
                {mode === "filter" ? "FILT" : mode.toUpperCase()}
              </button>
            ))}
          </div>
        )}
      </header>

      <div className="compound-boundary">
        <strong>Opaque implementation boundary</strong>
        <span>Complete inspected local object; not an accepted Schuss graph.</span>
      </div>

      <div className="compound-grid">
        <section aria-label="Mapped inputs" className="compound-inputs">
          <h3>Mapped inputs</h3>
          {data.machine.controls.map((mapping, index) => (
            <div
              className={`compound-port-row signal-${mapping.kind}${mapping.mapped ? "" : " is-unmapped"}`}
              key={mapping.controlId}
            >
              {mapping.mapped && (
                <Handle
                  className={`signal-handle signal-handle--${mapping.kind}`}
                  id={mapping.targetId}
                  isConnectable={false}
                  position={Position.Left}
                  style={{
                    background: SIGNAL_COLORS[mapping.kind],
                    top: COMPOUND_HANDLE_TOP + index * COMPOUND_ROW_HEIGHT,
                  }}
                  type="target"
                />
              )}
              <span>{labelForMode(mapping, data.mode)}</span>
              <small>{mapping.physicalLabel}</small>
            </div>
          ))}
        </section>

        <section aria-label="Instrument outputs" className="compound-outputs">
          <h3>Outputs</h3>
          {data.machine.outputs.map((output, index) => (
            <div className={`compound-output-row signal-${output.kind}`} key={output.outputId}>
              <span>{output.label}</span>
              <small>{output.detail}</small>
              <Handle
                className={`signal-handle signal-handle--${output.kind}`}
                id={output.outputId}
                isConnectable={false}
                position={Position.Right}
                style={{
                  background: SIGNAL_COLORS[output.kind],
                  top: COMPOUND_OUTPUT_TOP + index * COMPOUND_OUTPUT_ROW_HEIGHT,
                }}
                type="source"
              />
            </div>
          ))}
        </section>
      </div>

      <button
        aria-expanded={outlineOpen}
        className="outline-toggle nodrag"
        onClick={() => setOutlineOpen((current) => !current)}
        type="button"
      >
        <span>{outlineOpen ? "Hide" : "Open"} source outline</span>
        <span aria-hidden="true">{outlineOpen ? "−" : "+"}</span>
      </button>

      {outlineOpen && (
        <section className="source-outline">
          <div className="source-outline__title">
            <strong>Source outline</strong>
            <span>Review aid · these rows are not editable graph nodes</span>
          </div>
          {data.machine.sourceOutline.map((stage, index) => (
            <div className="source-stage" key={stage.label}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <div>
                <strong>{stage.label}</strong>
                <small>{stage.detail}</small>
              </div>
            </div>
          ))}
        </section>
      )}

      <footer className="node-boundary-note">{data.machine.sourceObject}</footer>
    </article>
  );
}

export const InstrumentCompoundNode = memo(InstrumentCompoundNodeComponent);
