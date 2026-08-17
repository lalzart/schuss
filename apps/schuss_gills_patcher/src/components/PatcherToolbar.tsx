import { MACHINE_KEYS, MACHINES } from "../model/machines";
import type { MachineKey } from "../model/types";

interface PatcherToolbarProps {
  currentPatchName: string | null;
  dirty: boolean;
  machineKey: MachineKey;
  onMachineChange: (key: MachineKey) => void;
  onReset: () => void;
  onSave: () => void;
}

export function PatcherToolbar({
  currentPatchName,
  dirty,
  machineKey,
  onMachineChange,
  onReset,
  onSave,
}: PatcherToolbarProps) {
  return (
    <nav aria-label="Patch controls" className="patcher-toolbar">
      <div aria-label="Reference machine" className="machine-switch" role="tablist">
        {MACHINE_KEYS.map((key) => (
          <button
            aria-selected={machineKey === key}
            className={machineKey === key ? "is-active" : ""}
            key={key}
            onClick={() => onMachineChange(key)}
            role="tab"
            type="button"
          >
            <span>{MACHINES[key].displayName}</span>
            <small>{key === "tide-pit" ? "SOURCE 01" : "SOURCE 02"}</small>
          </button>
        ))}
      </div>

      <div className="toolbar-divider" />

      <div className="patch-document-status">
        <span>PATCH DRAFT</span>
        <strong>{currentPatchName ?? `${MACHINES[machineKey].displayName} sketch`}</strong>
        <small>{dirty ? "Unsaved changes" : currentPatchName === null ? "Not saved" : "Saved locally"}</small>
      </div>

      <button className="reset-button" onClick={onReset} type="button">
        New from template
      </button>
      <button className="save-patch-button" onClick={onSave} type="button">
        {currentPatchName === null ? "Save patch" : "Save changes"}
      </button>
    </nav>
  );
}
