import { useEffect, useMemo, useRef, useState } from "react";

import panelAssetUrl from "../../../../assets/gills/gills-panel-v06.svg?url";
import { meaningsForSlots, panelLabelForSlot } from "../model/machineModel";
import type { MachineView, PerformanceMode, PhysicalRegionView } from "../model/types";

const potElements = Array.from({ length: 10 }, (_, index) => `pot-${String(index + 1).padStart(2, "0")}-region`);
const utilityElements = [
  "button-01-region",
  "button-02-region",
  "button-03-region",
  "button-04-region",
  "encoder-region",
  "oled-region",
];

function shortPhysicalName(elementId: string): string {
  const pot = elementId.match(/^pot-(\d+)-region$/);
  if (pot) return `P${Number(pot[1])}`;
  const button = elementId.match(/^button-(\d+)-region$/);
  if (button) return `S${Number(button[1])}`;
  if (elementId === "encoder-region") return "ENC";
  if (elementId === "oled-region") return "OLED";
  const led = elementId.match(/^led-(\d+)-region$/);
  if (led) return `L${Number(led[1])}`;
  return elementId;
}

function conciseLabels(view: MachineView, region: PhysicalRegionView, mode: PerformanceMode): string[] {
  return [...new Set(region.semanticSlotIds.flatMap((slotId) => {
    const meaning = meaningsForSlots(view, [slotId], mode)[0];
    if (!meaning || meaning.mappingState !== "mapped") return [];
    return [panelLabelForSlot(view, slotId, mode)];
  }))];
}

interface RegionButtonProps {
  mode: PerformanceMode;
  onSelect: (elementId: string) => void;
  region: PhysicalRegionView;
  selected: boolean;
  view: MachineView;
}

function RegionButton({ mode, onSelect, region, selected, view }: RegionButtonProps) {
  const labels = conciseLabels(view, region, mode);
  return (
    <button
      aria-pressed={selected}
      className={`panel-map-button ${selected ? "is-selected" : ""}`}
      onClick={() => onSelect(region.svgElementId)}
      type="button"
    >
      <strong>{shortPhysicalName(region.svgElementId)}</strong>
      <span>{labels.join(" · ") || "Unmapped"}</span>
    </button>
  );
}

interface GillsPanelProps {
  mode: PerformanceMode;
  onSelectRegion: (elementId: string) => void;
  selectedElementId: string | null;
  selectedSlotIds: readonly string[];
  view: MachineView;
}

export function GillsPanel({
  mode,
  onSelectRegion,
  selectedElementId,
  selectedSlotIds,
  view,
}: GillsPanelProps) {
  const objectRef = useRef<HTMLObjectElement>(null);
  const [panelDocument, setPanelDocument] = useState<Document | null>(null);
  const selectedSlots = useMemo(() => new Set(selectedSlotIds), [selectedSlotIds]);

  useEffect(() => {
    if (!panelDocument) return;
    const cleanups: Array<() => void> = [];
    for (const region of view.regions) {
      const element = panelDocument.getElementById(region.svgElementId);
      if (!element) throw new Error(`Machine prototype failed closed: panel asset lacks ${region.svgElementId}`);
      const activate = () => onSelectRegion(region.svgElementId);
      const keydown = (event: Event) => {
        const keyboardEvent = event as KeyboardEvent;
        if (keyboardEvent.key !== "Enter" && keyboardEvent.key !== " ") return;
        keyboardEvent.preventDefault();
        activate();
      };
      element.setAttribute("role", "button");
      element.setAttribute("tabindex", "0");
      element.setAttribute("aria-label", `${shortPhysicalName(region.svgElementId)}: ${conciseLabels(view, region, mode).join(", ") || "unmapped"}`);
      element.addEventListener("click", activate);
      element.addEventListener("keydown", keydown);
      cleanups.push(() => {
        element.removeEventListener("click", activate);
        element.removeEventListener("keydown", keydown);
      });
    }
    return () => cleanups.forEach((cleanup) => cleanup());
  }, [mode, onSelectRegion, panelDocument, view]);

  useEffect(() => {
    if (!panelDocument) return;
    for (const highlighted of panelDocument.querySelectorAll(".is-highlighted")) {
      highlighted.classList.remove("is-highlighted");
    }
    const highlightIds = new Set(view.regions
      .filter((region) => region.semanticSlotIds.some((slotId) => selectedSlots.has(slotId)))
      .flatMap((region) => region.highlightElementIds));
    for (const highlightId of highlightIds) panelDocument.getElementById(highlightId)?.classList.add("is-highlighted");
  }, [panelDocument, selectedSlots, view]);

  const potRegions = potElements.flatMap((id) => {
    const region = view.regionsByElement.get(id);
    return region ? [region] : [];
  });
  const utilityRegions = utilityElements.flatMap((id) => {
    const region = view.regionsByElement.get(id);
    return region ? [region] : [];
  });

  return (
    <section className="panel-section" aria-labelledby="gills-panel-heading">
      <div className="section-title-row">
        <div>
          <span className="eyebrow">WHAT CAN I TOUCH?</span>
          <h2 id="gills-panel-heading">Gills performance panel</h2>
        </div>
        <span className="asset-badge">v0.6 silhouette</span>
      </div>
      <div className="panel-svg-stage">
        <object
          aria-label="Interactive Ksoloti Gills panel silhouette"
          data={panelAssetUrl}
          onLoad={() => setPanelDocument(objectRef.current?.contentDocument ?? null)}
          ref={objectRef}
          type="image/svg+xml"
        />
        <div className="oled-preview" aria-hidden="true">
          {view.config.oledLines.map((line) => <span key={line}>{line}</span>)}
        </div>
      </div>
      <div className="pot-map-grid" aria-label="Ten performance pots" role="group">
        {potRegions.map((region) => (
          <RegionButton
            key={region.svgElementId}
            mode={mode}
            onSelect={onSelectRegion}
            region={region}
            selected={selectedElementId === region.svgElementId}
            view={view}
          />
        ))}
      </div>
      <div className="utility-map-grid" aria-label="Gills gestures and display" role="group">
        {utilityRegions.map((region) => (
          <RegionButton
            key={region.svgElementId}
            mode={mode}
            onSelect={onSelectRegion}
            region={region}
            selected={selectedElementId === region.svgElementId}
            view={view}
          />
        ))}
      </div>
    </section>
  );
}
