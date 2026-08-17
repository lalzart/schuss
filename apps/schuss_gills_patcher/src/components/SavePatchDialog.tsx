import { useState, type FormEvent } from "react";

import { normalizePatchName } from "../model/patchLibrary";

interface SavePatchDialogProps {
  defaultName: string;
  isUpdate: boolean;
  onCancel: () => void;
  onSave: (name: string) => void;
}

export function SavePatchDialog({
  defaultName,
  isUpdate,
  onCancel,
  onSave,
}: SavePatchDialogProps) {
  const [name, setName] = useState(() => defaultName);
  const normalizedName = normalizePatchName(name);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (normalizedName.length === 0) return;
    onSave(normalizedName);
  };

  return (
    <div className="dialog-backdrop" role="presentation">
      <form
        aria-labelledby="save-dialog-title"
        aria-modal="true"
        className="save-dialog"
        onSubmit={handleSubmit}
        role="dialog"
      >
        <header>
          <h2 id="save-dialog-title">{isUpdate ? "Save changes" : "Name this patch"}</h2>
          <button aria-label="Cancel save" onClick={onCancel} type="button">×</button>
        </header>
        <p>Saved only in this browser.</p>
        <label>
          <span>Patch name</span>
          <input
            autoFocus
            maxLength={80}
            onChange={(event) => setName(event.target.value)}
            placeholder="My Gills patch"
            type="text"
            value={name}
          />
        </label>
        <div className="save-dialog__actions">
          <button className="dialog-secondary-button" onClick={onCancel} type="button">Cancel</button>
          <button className="dialog-primary-button" disabled={normalizedName.length === 0} type="submit">
            {isUpdate ? "Save changes" : "Save patch"}
          </button>
        </div>
      </form>
    </div>
  );
}
