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
          </button>
        ))}
      </div>

      <div className="patch-document-status">
        <strong>{currentPatchName ?? `${MACHINES[machineKey].displayName} sketch`}</strong>
        <small>{dirty ? "Unsaved changes" : currentPatchName === null ? "Not saved" : "Saved locally"}</small>
      </div>

      <button
        aria-label="New from template"
        className="reset-button"
        onClick={onReset}
        title="New from template"
        type="button"
      >
        New
      </button>
      <button
        aria-label={currentPatchName === null ? "Save patch" : "Save changes"}
        className="save-patch-button"
        onClick={onSave}
        type="button"
      >
        Save
      </button>
    </nav>
  );
}
