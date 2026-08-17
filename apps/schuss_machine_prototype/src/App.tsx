import { useCallback, useMemo, useState } from "react";

import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { GillsPanel } from "./components/GillsPanel";
import { MachineCanvas } from "./components/MachineCanvas";
import { ModeSwitch } from "./components/ModeSwitch";
import { SelectionInspector } from "./components/SelectionInspector";
import type { MachineSelection } from "./components/uiTypes";
import {
  blockIdsForSlots,
  createMachineView,
  downstreamBlockIds,
  slotIdsForBlock,
} from "./model/machineModel";
import {
  fixtureForMachine,
  machineChoices,
  presentationForMachine,
} from "./model/presentation";
import type { MachineKey, PerformanceMode } from "./model/types";

const firstBlockId = "presentation-block-000001";

export default function App() {
  const [machineKey, setMachineKey] = useState<MachineKey>("tide-pit");
  const [mode, setMode] = useState<PerformanceMode>("CLEAN");
  const [selection, setSelection] = useState<MachineSelection>(null);
  const [expandedBlockIds, setExpandedBlockIds] = useState<ReadonlySet<string>>(() => new Set([firstBlockId]));
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  const view = useMemo(
    () => createMachineView(fixtureForMachine(machineKey), presentationForMachine(machineKey)),
    [machineKey],
  );

  const selectedSlotIds = useMemo(() => {
    if (!selection) return [];
    if (selection.kind === "panel") return view.regionsByElement.get(selection.elementId)?.semanticSlotIds ?? [];
    return slotIdsForBlock(view, selection.blockId, mode);
  }, [mode, selection, view]);

  const exactTargetBlockIds = useMemo(() => {
    if (!selection) return [];
    if (selection.kind === "block") return [selection.blockId];
    return blockIdsForSlots(view, selectedSlotIds, mode);
  }, [mode, selectedSlotIds, selection, view]);

  const downstream = useMemo(
    () => downstreamBlockIds(view.edges, exactTargetBlockIds),
    [exactTargetBlockIds, view.edges],
  );

  const selectRegion = useCallback((elementId: string) => {
    setSelection({ elementId, kind: "panel" });
  }, []);
  const selectBlock = useCallback((blockId: string) => {
    setSelection({ blockId, kind: "block" });
  }, []);
  const toggleExpanded = useCallback((blockId: string) => {
    setExpandedBlockIds((current) => {
      const next = new Set(current);
      if (next.has(blockId)) next.delete(blockId);
      else next.add(blockId);
      return next;
    });
  }, []);
  const closeEvidence = useCallback(() => setEvidenceOpen(false), []);

  const changeMachine = (nextMachine: MachineKey) => {
    setMachineKey(nextMachine);
    setMode("CLEAN");
    setSelection(null);
    setExpandedBlockIds(new Set([firstBlockId]));
  };

  const selectedElementId = selection?.kind === "panel" ? selection.elementId : null;
  const selectedBlockId = selection?.kind === "block" ? selection.blockId : null;

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <div>
            <span className="eyebrow">SCHUSS / GILLS LAB</span>
            <h1>Machine view</h1>
          </div>
        </div>
        <nav aria-label="Reference machine" className="machine-picker">
          {machineChoices.map((choice) => (
            <button
              aria-current={machineKey === choice.key ? "page" : undefined}
              className={machineKey === choice.key ? "is-active" : undefined}
              key={choice.key}
              onClick={() => changeMachine(choice.key)}
              type="button"
            >
              {choice.label}
            </button>
          ))}
        </nav>
        <div className="header-actions">
          <span className="state-pill state-pill--warning">inspection only</span>
          <button className="evidence-button" onClick={() => setEvidenceOpen(true)} type="button">
            Evidence <span>L1</span>
          </button>
        </div>
      </header>

      <main>
        <section className="machine-intro">
          <div>
            <span className="eyebrow">REFERENCE MACHINE</span>
            <h2>{view.identity.display_name}</h2>
            <p>{view.identity.summary}</p>
          </div>
          <div className="performance-state">
            <label>Effect path</label>
            <ModeSwitch mode={mode} onChange={setMode} />
          </div>
        </section>

        <div className="prototype-workspace">
          <GillsPanel
            mode={mode}
            onSelectRegion={selectRegion}
            selectedElementId={selectedElementId}
            selectedSlotIds={selectedSlotIds}
            view={view}
          />
          <section className="flow-section" aria-labelledby="machine-flow-heading">
            <div className="section-title-row">
              <div>
                <span className="eyebrow">WHAT HAPPENS INSIDE?</span>
                <h2 id="machine-flow-heading">Musical signal path</h2>
              </div>
              {selection && (
                <button className="clear-button" onClick={() => setSelection(null)} type="button">Clear focus</button>
              )}
            </div>
            <MachineCanvas
              downstreamBlockIds={downstream}
              exactTargetBlockIds={exactTargetBlockIds}
              expandedBlockIds={expandedBlockIds}
              mode={mode}
              onSelectBlock={selectBlock}
              onToggleExpanded={toggleExpanded}
              selectedBlockId={selectedBlockId}
              view={view}
            />
          </section>
        </div>

        <SelectionInspector
          exactTargetBlockIds={exactTargetBlockIds}
          mode={mode}
          selectedSlotIds={selectedSlotIds}
          selection={selection}
          view={view}
        />
      </main>

      <footer>
        <span>Panel mapping → exact presentation block → downstream source-evidenced flow</span>
        <span>Viewer prototype · no graph editing or device actions</span>
      </footer>
      <EvidenceDrawer onClose={closeEvidence} open={evidenceOpen} view={view} />
    </div>
  );
}
