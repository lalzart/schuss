import { memo, useMemo, useState, type DragEvent } from "react";

import {
  CATALOG_CATEGORIES,
  CATALOG_DRAG_MIME,
  DISABLED_CATALOG_ITEMS,
  SELECTABLE_CATALOG_ITEMS,
  filterCatalogItems,
} from "../model/catalog";
import { MACHINE_KEYS, MACHINES } from "../model/machines";
import { searchSavedPatches, type SavedLocalPatch } from "../model/patchLibrary";
import type { CatalogItem, MachineKey } from "../model/types";

type LibraryTab = "objects" | "patches";

interface CatalogCardProps {
  item: CatalogItem;
  onAdd: (item: CatalogItem) => void;
}

function functionLabel(value: string): string {
  return value
    .split("-")
    .map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
    .join(" ");
}

function CatalogCardComponent({ item, onAdd }: CatalogCardProps) {
  const contract = item.contractReference;
  const handleDragStart = (event: DragEvent<HTMLElement>) => {
    if (!item.selectable || contract === null) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData(CATALOG_DRAG_MIME, item.familyReference.stableId);
    event.dataTransfer.setData("text/plain", item.displayName);
  };

  return (
    <article
      aria-disabled={!item.selectable}
      className={`catalog-card${item.selectable ? "" : " is-disabled"}`}
      draggable={item.selectable}
      onDragStart={handleDragStart}
      title={item.selectable ? undefined : item.disabledReason}
    >
      <div className="catalog-card__body">
        <h3>{item.displayName}</h3>
        <span>{functionLabel(item.primaryFunction)}</span>
        {!item.selectable && (
          <small>{item.disabledReason ?? item.statusLabel}</small>
        )}
      </div>
      {item.selectable ? (
        <button
          aria-label={`Add ${item.displayName} to canvas`}
          className="catalog-add-button"
          onClick={() => onAdd(item)}
          title="Add to canvas"
          type="button"
        >
          +
        </button>
      ) : (
        <span aria-hidden="true" className="catalog-lock">—</span>
      )}
    </article>
  );
}

const CatalogCard = memo(CatalogCardComponent);

interface PatchTemplateCardProps {
  machineKey: MachineKey;
  onLoad: (machineKey: MachineKey) => void;
}

function PatchTemplateCardComponent({ machineKey, onLoad }: PatchTemplateCardProps) {
  const machine = MACHINES[machineKey];
  return (
    <article className="patch-library-card is-template">
      <div className="patch-card__body">
        <h3>{machine.displayName}</h3>
        <span>Source template</span>
      </div>
      <button
        aria-label={`Open new ${machine.displayName} draft`}
        onClick={() => onLoad(machineKey)}
        type="button"
      >
        New
      </button>
    </article>
  );
}

const PatchTemplateCard = memo(PatchTemplateCardComponent);

interface SavedPatchCardProps {
  active: boolean;
  patch: SavedLocalPatch;
  onDelete: (patchId: string) => void;
  onLoad: (patch: SavedLocalPatch) => void;
}

function SavedPatchCardComponent({ active, patch, onDelete, onLoad }: SavedPatchCardProps) {
  const machine = MACHINES[patch.machineKey];
  return (
    <article className={`patch-library-card is-saved${active ? " is-active" : ""}`}>
      <div className="patch-card__body">
        <h3>{patch.name}</h3>
        <span>
          {machine.displayName} · {patch.catalogNodes.length} object{patch.catalogNodes.length === 1 ? "" : "s"}
        </span>
      </div>
      <div className="patch-card__actions">
        <button onClick={() => onLoad(patch)} type="button">{active ? "Reload" : "Open"}</button>
        <button
          aria-label={`Delete local patch ${patch.name}`}
          className="delete-patch-button"
          onClick={() => onDelete(patch.patchId)}
          type="button"
        >
          Delete
        </button>
      </div>
    </article>
  );
}

const SavedPatchCard = memo(SavedPatchCardComponent);

interface CatalogSidebarProps {
  activePatchId: string | null;
  libraryWarning: string | null;
  onAdd: (item: CatalogItem) => void;
  onDeletePatch: (patchId: string) => void;
  onLoadPatch: (patch: SavedLocalPatch) => void;
  onLoadTemplate: (machineKey: MachineKey) => void;
  savedPatches: readonly SavedLocalPatch[];
}

export function CatalogSidebar({
  activePatchId,
  libraryWarning,
  onAdd,
  onDeletePatch,
  onLoadPatch,
  onLoadTemplate,
  savedPatches,
}: CatalogSidebarProps) {
  const [activeTab, setActiveTab] = useState<LibraryTab>("objects");
  const [category, setCategory] = useState("all");
  const [objectQuery, setObjectQuery] = useState("");
  const [patchQuery, setPatchQuery] = useState("");

  const available = useMemo(
    () => filterCatalogItems(SELECTABLE_CATALOG_ITEMS, objectQuery, category),
    [category, objectQuery],
  );
  const unavailable = useMemo(
    () => filterCatalogItems(DISABLED_CATALOG_ITEMS, objectQuery, category),
    [category, objectQuery],
  );
  const matchingSavedPatches = useMemo(
    () => searchSavedPatches(savedPatches, patchQuery),
    [patchQuery, savedPatches],
  );
  const matchingTemplates = useMemo(() => {
    const normalizedQuery = patchQuery.trim().toLocaleLowerCase();
    if (normalizedQuery.length === 0) return MACHINE_KEYS;
    return MACHINE_KEYS.filter((machineKey) => {
      const machine = MACHINES[machineKey];
      return `${machine.displayName} ${machine.subtitle ?? ""} ${machineKey}`
        .toLocaleLowerCase()
        .includes(normalizedQuery);
    });
  }, [patchQuery]);

  const patchCount = savedPatches.length + MACHINE_KEYS.length;

  return (
    <aside className="catalog-sidebar" aria-label="Patcher library">
      <header className="catalog-header">
        <h2>Library</h2>
        <span title={activeTab === "objects" ? "Accepted direct-palette selections" : "Templates and local patches"}>
          {activeTab === "objects" ? "Objects" : "Patches"}
        </span>
      </header>

      <div aria-label="Library type" className="library-tabs" role="tablist">
        <button
          aria-selected={activeTab === "objects"}
          className={activeTab === "objects" ? "is-active" : ""}
          onClick={() => setActiveTab("objects")}
          role="tab"
          type="button"
        >
          Objects <span>20</span>
        </button>
        <button
          aria-selected={activeTab === "patches"}
          className={activeTab === "patches" ? "is-active" : ""}
          onClick={() => setActiveTab("patches")}
          role="tab"
          type="button"
        >
          Patches <span>{patchCount}</span>
        </button>
      </div>

      {activeTab === "objects" ? (
        <>
          <div className="catalog-filters">
            <label>
              <span className="visually-hidden">Search objects</span>
              <input
                onChange={(event) => setObjectQuery(event.target.value)}
                placeholder="Search objects…"
                type="search"
                value={objectQuery}
              />
            </label>
            <label>
              <span className="visually-hidden">Filter by function</span>
              <select onChange={(event) => setCategory(event.target.value)} value={category}>
                <option value="all">All functions</option>
                {CATALOG_CATEGORIES.map((entry) => (
                  <option key={entry} value={entry}>{functionLabel(entry)}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="catalog-scroll">
            <section aria-labelledby="available-catalog-heading">
              <div className="catalog-section-heading">
                <h3 id="available-catalog-heading">Available</h3>
                <span>{available.length}</span>
              </div>
              <div className="catalog-list">
                {available.map((item) => (
                  <CatalogCard item={item} key={item.familyReference.stableId} onAdd={onAdd} />
                ))}
                {available.length === 0 && <p className="catalog-empty">No accepted objects match.</p>}
              </div>
            </section>

            <section aria-labelledby="unavailable-catalog-heading" className="unavailable-section">
              <div className="catalog-section-heading">
                <h3 id="unavailable-catalog-heading">Reference only</h3>
                <span>{unavailable.length}</span>
              </div>
              <div className="catalog-list">
                {unavailable.map((item) => (
                  <CatalogCard item={item} key={item.familyReference.stableId} onAdd={onAdd} />
                ))}
              </div>
            </section>
          </div>
        </>
      ) : (
        <>
          <div className="patch-filters">
            <label>
              <span className="visually-hidden">Search patches</span>
              <input
                onChange={(event) => setPatchQuery(event.target.value)}
                placeholder="Search patches…"
                type="search"
                value={patchQuery}
              />
            </label>
          </div>

          <div className="catalog-scroll patch-scroll">
            {libraryWarning !== null && <p className="library-warning" role="alert">{libraryWarning}</p>}
            <section aria-labelledby="patch-templates-heading">
              <div className="catalog-section-heading">
                <h3 id="patch-templates-heading">Source templates</h3>
                <span>{matchingTemplates.length}</span>
              </div>
              <div className="catalog-list">
                {matchingTemplates.map((machineKey) => (
                  <PatchTemplateCard key={machineKey} machineKey={machineKey} onLoad={onLoadTemplate} />
                ))}
                {matchingTemplates.length === 0 && <p className="catalog-empty">No source templates match.</p>}
              </div>
            </section>

            <section aria-labelledby="saved-patches-heading" className="saved-patches-section">
              <div className="catalog-section-heading">
                <h3 id="saved-patches-heading">My local patches</h3>
                <span>{matchingSavedPatches.length}</span>
              </div>
              <div className="catalog-list">
                {matchingSavedPatches.map((patch) => (
                  <SavedPatchCard
                    active={activePatchId === patch.patchId}
                    key={patch.patchId}
                    onDelete={onDeletePatch}
                    onLoad={onLoadPatch}
                    patch={patch}
                  />
                ))}
                {matchingSavedPatches.length === 0 && (
                  <p className="catalog-empty">
                    {savedPatches.length === 0 ? "No local patches yet. Build one, then save it." : "No local patches match."}
                  </p>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </aside>
  );
}
