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
  let eyebrow = "PRESENTATION NODE";
  let body = "Canvas placement and selection are local presentation state.";
  let references: Array<{ label: string; value: string }> = [];
  let canDelete = false;

  if (node.type === "gillsInput") {
    title = "Gills controls";
    eyebrow = "DEVICE PROFILE INPUT";
    body = `${node.data.machine.controls.length} stable physical slots map through instrument facets. They are not catalog identities.`;
    references = [{ label: "Machine", value: node.data.machine.sourcePatch }];
  } else if (node.type === "instrument") {
    title = node.data.machine.displayName;
    eyebrow = "SOURCE-DEFINED COMPOUND";
    body = node.data.machine.summary;
    references = [
      { label: "Patch", value: node.data.machine.sourcePatch },
      { label: "Object", value: node.data.machine.sourceObject },
    ];
  } else if (node.type === "gillsOutput") {
    title = "Gills outputs";
    eyebrow = "DEVICE PROFILE OUTPUT";
    body = "Stereo audio, stage LEDs, and OLED feedback terminate in device-profile services, not palette nodes.";
    references = [{ label: "Machine", value: node.data.machine.sourcePatch }];
  } else if (node.type === "catalogDraft") {
    const contract = node.data.item.contractReference;
    title = node.data.item.displayName;
    eyebrow = "LOCAL DRAFT · UNWIRED";
    body = "The exact accepted identity is placed, but semantic ports and persistence wait for the governed desktop adapter.";
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
      <p>{body}</p>
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

