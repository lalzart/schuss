import {
  meaningsForSlots,
  panelLabelForSlot,
  slotIdsForBlock,
} from "../model/machineModel";
import type { MachineView, PerformanceMode } from "../model/types";
import type { MachineSelection } from "./uiTypes";

interface SelectionInspectorProps {
  exactTargetBlockIds: readonly string[];
  mode: PerformanceMode;
  selectedSlotIds: readonly string[];
  selection: MachineSelection;
  view: MachineView;
}

export function SelectionInspector({
  exactTargetBlockIds,
  mode,
  selectedSlotIds,
  selection,
  view,
}: SelectionInspectorProps) {
  if (!selection) {
    return (
      <aside className="selection-inspector is-empty" aria-live="polite">
        <span className="selection-inspector__marker" />
        <p><strong>Touch the panel or a block.</strong> The exact entry point turns orange; its downstream path stays lit.</p>
      </aside>
    );
  }

  if (selection.kind === "panel") {
    const region = view.regionsByElement.get(selection.elementId);
    const meanings = meaningsForSlots(view, selectedSlotIds, mode);
    const targetLabels = exactTargetBlockIds.flatMap((id) => {
      const block = view.blocksById.get(id);
      return block ? [block.label] : [];
    });
    return (
      <aside className="selection-inspector" aria-live="polite">
        <div>
          <span className="eyebrow">PHYSICAL CONTROL</span>
          <h3>{region?.physicalLabel ?? selection.elementId}</h3>
        </div>
        <div className="meaning-list">
          {meanings.map((meaning) => (
            <span className={meaning.mappingState === "mapped" ? "is-mapped" : "is-unmapped"} key={meaning.semanticSlotId}>
              {meaning.meaning}
            </span>
          ))}
        </div>
        <p className="selection-route">
          <strong>Exact entry:</strong> {targetLabels.join(", ") || "no linked presentation block"}
        </p>
      </aside>
    );
  }

  const block = view.blocksById.get(selection.blockId);
  const slots = slotIdsForBlock(view, selection.blockId, mode);
  const labels = [...new Set(slots.map((slotId) => panelLabelForSlot(view, slotId, mode)))];
  return (
    <aside className="selection-inspector" aria-live="polite">
      <div>
        <span className="eyebrow">MACHINE COMPOUND</span>
        <h3>{block?.label ?? selection.blockId}</h3>
      </div>
      <p>{block?.summary}</p>
      <div className="meaning-list">
        {labels.length > 0
          ? labels.map((label) => <span className="is-mapped" key={label}>{label}</span>)
          : <span className="is-neutral">No direct panel link in the retained inspection</span>}
      </div>
    </aside>
  );
}
