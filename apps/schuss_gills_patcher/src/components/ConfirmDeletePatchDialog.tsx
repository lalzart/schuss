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
          <h2 id="delete-dialog-title">Delete “{name}”?</h2>
          <button aria-label="Cancel delete" onClick={onCancel} type="button">×</button>
        </header>
        <p>The saved draft is removed. The open canvas stays available.</p>
        <div className="save-dialog__actions">
          <button className="dialog-secondary-button" onClick={onCancel} type="button">Cancel</button>
          <button className="dialog-delete-button" onClick={onConfirm} type="button">Delete patch</button>
        </div>
      </section>
    </div>
  );
}
