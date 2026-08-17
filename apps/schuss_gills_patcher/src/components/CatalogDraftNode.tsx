import { memo } from "react";
import { type NodeProps } from "@xyflow/react";

import type { CatalogDraftFlowNode } from "../model/graph";

function CatalogDraftNodeComponent({ data, selected }: NodeProps<CatalogDraftFlowNode>) {
  return (
    <article className={`patch-node catalog-draft-node${selected ? " is-selected" : ""}`}>
      <header>
        <span className="node-eyebrow node-eyebrow--draft">Unwired object</span>
        <span className="draft-number">#{String(data.localIndex).padStart(2, "0")}</span>
      </header>
      <h2>{data.item.displayName}</h2>
      <div className="draft-function">{data.item.primaryFunction.replaceAll("-", " ")}</div>
    </article>
  );
}

export const CatalogDraftNode = memo(CatalogDraftNodeComponent);
