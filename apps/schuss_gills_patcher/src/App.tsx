import { useCallback, useRef, useState } from "react";

import { CatalogSidebar } from "./components/CatalogSidebar";
import { ConfirmDeletePatchDialog } from "./components/ConfirmDeletePatchDialog";
import { PatcherCanvas, type PatcherCanvasHandle } from "./components/PatcherCanvas";
import { PatcherToolbar } from "./components/PatcherToolbar";
import { SavePatchDialog } from "./components/SavePatchDialog";
import { MACHINES } from "./model/machines";
import {
  LOCAL_PATCH_LIBRARY_STORAGE_KEY,
  createLocalPatchId,
  decodePatchLibrary,
  deleteLocalPatch,
  encodePatchLibrary,
  upsertLocalPatch,
  type LocalPatchLibrary,
  type PatchSnapshot,
  type SavedLocalPatch,
} from "./model/patchLibrary";
import type { CatalogItem, MachineKey, PerformanceMode } from "./model/types";

interface InitialLibraryState {
  library: LocalPatchLibrary;
  warning: string | null;
}

function readInitialLibrary(): InitialLibraryState {
  try {
    const result = decodePatchLibrary(window.localStorage.getItem(LOCAL_PATCH_LIBRARY_STORAGE_KEY));
    return {
      library: result.library,
      warning: result.warnings.length === 0 ? null : result.warnings.join(" "),
    };
  } catch {
    return {
      library: decodePatchLibrary(null).library,
      warning: "Browser storage was unavailable; local patches cannot be restored yet.",
    };
  }
}

export default function App() {
  const [initialLibrary] = useState(readInitialLibrary);
  const [library, setLibrary] = useState(initialLibrary.library);
  const [libraryWarning, setLibraryWarning] = useState<string | null>(initialLibrary.warning);
  const [machineKey, setMachineKey] = useState<MachineKey>("tide-pit");
  const [mode, setMode] = useState<PerformanceMode>("clean");
  const [initialSnapshot, setInitialSnapshot] = useState<PatchSnapshot | null>(null);
  const [activePatchId, setActivePatchId] = useState<string | null>(null);
  const [activePatchName, setActivePatchName] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [deleteCandidateId, setDeleteCandidateId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [resetRevision, setResetRevision] = useState(0);
  const canvasRef = useRef<PatcherCanvasHandle>(null);
  const machine = MACHINES[machineKey];

  const persistLibrary = useCallback((nextLibrary: LocalPatchLibrary): boolean => {
    try {
      window.localStorage.setItem(
        LOCAL_PATCH_LIBRARY_STORAGE_KEY,
        encodePatchLibrary(nextLibrary),
      );
      setLibrary(nextLibrary);
      setLibraryWarning(null);
      return true;
    } catch {
      setLibraryWarning("Browser storage rejected the local patch write. Nothing was replaced.");
      return false;
    }
  }, []);

  const startTemplate = useCallback((nextMachine: MachineKey) => {
    setMachineKey(nextMachine);
    setMode("clean");
    setInitialSnapshot(null);
    setActivePatchId(null);
    setActivePatchName(null);
    setDirty(false);
    setNotice(`Started a new ${MACHINES[nextMachine].displayName} draft.`);
    setResetRevision((current) => current + 1);
  }, []);

  const handleAddCatalogItem = useCallback((item: CatalogItem) => {
    canvasRef.current?.addCatalogItem(item);
  }, []);

  const handleModeChange = useCallback((nextMode: PerformanceMode) => {
    setMode(nextMode);
    setDirty(true);
    setNotice(null);
  }, []);

  const handleLoadPatch = useCallback((patch: SavedLocalPatch) => {
    setMachineKey(patch.machineKey);
    setMode(patch.mode);
    setInitialSnapshot(patch);
    setActivePatchId(patch.patchId);
    setActivePatchName(patch.name);
    setDirty(false);
    setNotice(`Loaded ${patch.name} from this browser.`);
    setResetRevision((current) => current + 1);
  }, []);

  const handleConfirmDeletePatch = useCallback(() => {
    if (deleteCandidateId === null) return;
    const patchId = deleteCandidateId;
    const patch = library.patches.find((entry) => entry.patchId === patchId);
    if (patch === undefined) {
      setDeleteCandidateId(null);
      return;
    }
    const nextLibrary = deleteLocalPatch(library, patchId);
    if (!persistLibrary(nextLibrary)) return;
    if (activePatchId === patchId) {
      setActivePatchId(null);
      setActivePatchName(null);
      setDirty(true);
      setNotice(`Deleted ${patch.name} from the local library; the open canvas is now unsaved.`);
    } else {
      setNotice(`Deleted ${patch.name} from the local library.`);
    }
    setDeleteCandidateId(null);
  }, [activePatchId, deleteCandidateId, library, persistLibrary]);

  const handleSave = useCallback((name: string) => {
    const snapshot = canvasRef.current?.getSnapshot();
    if (snapshot === undefined) {
      setLibraryWarning("The canvas was not ready, so the patch was not saved.");
      return;
    }
    try {
      const result = upsertLocalPatch(
        library,
        snapshot,
        name,
        activePatchId,
        createLocalPatchId,
      );
      if (!persistLibrary(result.library)) return;
      setActivePatchId(result.patch.patchId);
      setActivePatchName(result.patch.name);
      setInitialSnapshot(result.patch);
      setDirty(false);
      setSaveDialogOpen(false);
      setNotice(`${result.patch.name} saved in this browser.`);
    } catch (error) {
      setLibraryWarning(error instanceof Error ? error.message : "The local patch could not be saved.");
    }
  }, [activePatchId, library, persistLibrary]);

  const handleCanvasDirty = useCallback(() => {
    setDirty(true);
    setNotice(null);
  }, []);

  const handleReset = useCallback(() => {
    startTemplate(machineKey);
  }, [machineKey, startTemplate]);

  const openSaveDialog = useCallback(() => setSaveDialogOpen(true), []);
  const closeSaveDialog = useCallback(() => setSaveDialogOpen(false), []);
  const closeDeleteDialog = useCallback(() => setDeleteCandidateId(null), []);

  const canvasTitle = activePatchName ?? machine.displayName;

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">S</div>
          <div>
            <span>SCHUSS</span>
            <strong>Gills graph patcher</strong>
          </div>
        </div>
        <div className="evidence-status" role="status">
          <span className="status-dot" />
          <div>
            <strong>BROWSER-LOCAL PATCH DRAFT</strong>
            <small>Saved presentation state · not a wired or buildable Schuss graph</small>
          </div>
        </div>
        <div className="header-machine-id">
          <span>REFERENCE</span>
          <strong>{machine.displayName}</strong>
        </div>
      </header>

      <PatcherToolbar
        currentPatchName={activePatchName}
        dirty={dirty}
        machineKey={machineKey}
        onMachineChange={startTemplate}
        onReset={handleReset}
        onSave={openSaveDialog}
      />

      <main className="workspace">
        <CatalogSidebar
          activePatchId={activePatchId}
          libraryWarning={libraryWarning}
          onAdd={handleAddCatalogItem}
          onDeletePatch={setDeleteCandidateId}
          onLoadPatch={handleLoadPatch}
          onLoadTemplate={startTemplate}
          savedPatches={library.patches}
        />
        <section className="canvas-region" aria-labelledby="canvas-title">
          <div className="canvas-titlebar">
            <div>
              <span className="section-kicker">
                {activePatchName === null ? "REFERENCE MACHINE" : "LOCAL PATCH DRAFT"}
              </span>
              <h1 id="canvas-title">{canvasTitle}</h1>
              <p>{activePatchName === null ? machine.subtitle : `Based on ${machine.displayName} · ${dirty ? "unsaved changes" : "saved locally"}`}</p>
            </div>
            <div className="source-reference">
              <span>INSPECTED SOURCE</span>
              <code>{machine.sourcePatch}</code>
              {notice !== null && <span className="canvas-notice" role="status">{notice}</span>}
            </div>
          </div>
          <PatcherCanvas
            initialSnapshot={initialSnapshot}
            key={`${machineKey}:${resetRevision}`}
            machine={machine}
            mode={mode}
            onDirty={handleCanvasDirty}
            onModeChange={handleModeChange}
            ref={canvasRef}
          />
        </section>
      </main>

      {saveDialogOpen && (
        <SavePatchDialog
          defaultName={activePatchName ?? `${machine.displayName} patch`}
          isUpdate={activePatchId !== null}
          onCancel={closeSaveDialog}
          onSave={handleSave}
        />
      )}

      {deleteCandidateId !== null && (
        <ConfirmDeletePatchDialog
          name={library.patches.find((patch) => patch.patchId === deleteCandidateId)?.name ?? "local patch"}
          onCancel={closeDeleteDialog}
          onConfirm={handleConfirmDeletePatch}
        />
      )}
    </div>
  );
}
