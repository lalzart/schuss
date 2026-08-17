import { memo } from "react";
import { type NodeProps } from "@xyflow/react";

import type { CatalogDraftFlowNode } from "../model/graph";

function CatalogDraftNodeComponent({ data, selected }: NodeProps<CatalogDraftFlowNode>) {
  const contract = data.item.contractReference;
  return (
    <article className={`patch-node catalog-draft-node${selected ? " is-selected" : ""}`}>
      <header>
        <span className="node-eyebrow node-eyebrow--draft">LOCAL DRAFT · UNWIRED</span>
        <span className="draft-number">#{String(data.localIndex).padStart(2, "0")}</span>
      </header>
      <h2>{data.item.displayName}</h2>
      <p>{data.item.description}</p>
      <div className="draft-function">{data.item.primaryFunction}</div>
      <dl>
        <div>
          <dt>Family</dt>
          <dd>{data.item.familyReference.stableId}@{data.item.familyReference.revision}</dd>
        </div>
        <div>
          <dt>Contract</dt>
          <dd>{contract?.stableId}@{contract?.revision}</dd>
        </div>
      </dl>
      <footer>Ports wait for the governed contract adapter</footer>
    </article>
  );
}

export const CatalogDraftNode = memo(CatalogDraftNodeComponent);

