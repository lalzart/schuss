interface ConfirmDeletePatchDialogProps {
  name: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDeletePatchDialog({
  name,
  onCancel,
  onConfirm,
}: ConfirmDeletePatchDialogProps) {
  return (
    <div className="dialog-backdrop" role="presentation">
      <section
        aria-labelledby="delete-dialog-title"
        aria-modal="true"
        className="save-dialog delete-patch-dialog"
        role="dialog"
      >
        <header>
          <div>
            <span className="section-kicker">LOCAL PATCH LIBRARY</span>
            <h2 id="delete-dialog-title">Delete “{name}”?</h2>
          </div>
          <button aria-label="Cancel delete" onClick={onCancel} type="button">×</button>
        </header>
        <p>
          This removes the browser-local saved record. If it is open, the canvas
          stays available as a new unsaved draft.
        </p>
        <div className="save-dialog__actions">
          <button className="dialog-secondary-button" onClick={onCancel} type="button">Cancel</button>
          <button className="dialog-delete-button" onClick={onConfirm} type="button">Delete local patch</button>
        </div>
      </section>
    </div>
  );
}

