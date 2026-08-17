import type { PatcherNode } from "../model/graph";

interface SelectionInspectorProps {
  node: PatcherNode | null;
  onDeleteDraft: () => void;
  onDismiss: () => void;
}

function ReferenceLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="inspector-reference">
      <span>{label}</span>
      <code>{value}</code>
    </div>
  );
}

export function SelectionInspector({
  node,
  onDeleteDraft,
  onDismiss,
}: SelectionInspectorProps) {
  if (node === null) return null;

  let title = "Selected node";
  let eyebrow = "Presentation node";
  let references: Array<{ label: string; value: string }> = [];
  let canDelete = false;

  if (node.type === "gillsInput") {
    title = "Gills controls";
    eyebrow = "Device inputs";
    references = [{ label: "Source", value: node.data.machine.sourcePatch }];
  } else if (node.type === "instrument") {
    title = node.data.machine.displayName;
    eyebrow = "Source compound";
    references = [
      { label: "Patch", value: node.data.machine.sourcePatch },
      { label: "Object", value: node.data.machine.sourceObject },
    ];
  } else if (node.type === "gillsOutput") {
    title = "Gills outputs";
    eyebrow = "Device outputs";
    references = [{ label: "Source", value: node.data.machine.sourcePatch }];
  } else if (node.type === "catalogDraft") {
    const contract = node.data.item.contractReference;
    title = node.data.item.displayName;
    eyebrow = "Unwired object";
    canDelete = true;
    references = [
      {
        label: "Family",
        value: `${node.data.item.familyReference.stableId}@${node.data.item.familyReference.revision}\n${node.data.item.familyReference.contentHash}`,
      },
      {
        label: "Contract",
        value: contract === null
          ? "none"
          : `${contract.stableId}@${contract.revision}\n${contract.contentHash}`,
      },
    ];
  }

  return (
    <aside className="selection-inspector nodrag nopan" aria-live="polite">
      <header>
        <span>{eyebrow}</span>
        <button aria-label="Close inspector" onClick={onDismiss} type="button">×</button>
      </header>
      <h2>{title}</h2>
      {references.map((reference) => (
        <ReferenceLine key={reference.label} label={reference.label} value={reference.value} />
      ))}
      {canDelete && (
        <button className="delete-draft-button" onClick={onDeleteDraft} type="button">
          Remove local card
        </button>
      )}
    </aside>
  );
}
