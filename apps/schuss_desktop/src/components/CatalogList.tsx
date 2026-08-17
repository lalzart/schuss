import { memo } from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import type { CatalogSearchItem } from "../core/types";
import { StatusBadge } from "./StatusBadge";
import styles from "./CatalogBrowser.module.css";

export function routeTone(primaryFunction: string): string {
  if (["sound-sources", "sampling-buffers"].includes(primaryFunction)) return "yellow";
  if (["filters-resonators", "gain-dynamics"].includes(primaryFunction)) return "cyan";
  if (["modulation-control", "envelopes"].includes(primaryFunction)) return "green";
  if (["delay-reverb", "distortion-waveshaping"].includes(primaryFunction)) return "red";
  if (["sequencing", "timing-logic"].includes(primaryFunction)) return "orange";
  if (primaryFunction === "input-output") return "blue";
  return "violet";
}

function referenceKey(item: CatalogSearchItem): string {
  const reference = item.family_reference;
  return `${reference.family_id}@${reference.revision}`;
}

type CatalogRowProps = {
  item: CatalogSearchItem;
  selected: boolean;
  onSelect: (key: string) => void;
};

const CatalogRow = memo(function CatalogRow({ item, selected, onSelect }: CatalogRowProps) {
  const key = referenceKey(item);
  const mutableDerived = item.provenance_facets.includes("mutable-instruments-derived");
  return (
    <li className={styles.resultItem}>
      <button
        type="button"
        className={styles.resultButton}
        data-selected={selected ? "true" : "false"}
        data-tone={routeTone(item.primary_function)}
        aria-current={selected ? "true" : undefined}
        onClick={() => onSelect(key)}
      >
        <span className={styles.routeStripe} aria-hidden="true" />
        <span className={styles.resultBody}>
          <span className={styles.resultTopline}>
            <strong>{item.display_name}</strong>
            <code>{item.family_reference.family_id.replace("schuss-family-", "F-")}</code>
          </span>
          <span className={styles.resultDescription}>{item.description}</span>
          <span className={styles.resultMeta}>
            <span>{item.abstraction_level}</span>
            <span>{item.implementation_forms.join(" · ")}</span>
            {mutableDerived ? <span className={styles.mutableTag}>MUTABLE-DERIVED</span> : null}
          </span>
          <span className={styles.rowStatuses}>
            {item.readiness_states.slice(0, 3).map((status) => (
              <StatusBadge key={status} status={status} />
            ))}
          </span>
        </span>
      </button>
    </li>
  );
});

type CatalogListProps = {
  items: CatalogSearchItem[];
  selectedKey: string | null;
  loading: boolean;
  onSelect: (key: string) => void;
};

export function CatalogList({ items, selectedKey, loading, onSelect }: CatalogListProps) {
  return (
    <ScrollArea.Root className={styles.listScroll}>
      <ScrollArea.Viewport className={styles.scrollViewport}>
        {items.length === 0 && !loading ? (
          <div className={styles.emptyState}>
            <span className={styles.emptyCode}>NO MATCH</span>
            <p>No exact families match this route and filter combination.</p>
          </div>
        ) : (
          <ul className={styles.resultList} aria-busy={loading}>
            {items.map((item) => (
              <CatalogRow
                key={referenceKey(item)}
                item={item}
                selected={referenceKey(item) === selectedKey}
                onSelect={onSelect}
              />
            ))}
          </ul>
        )}
      </ScrollArea.Viewport>
      <ScrollArea.Scrollbar className={styles.scrollbar} orientation="vertical">
        <ScrollArea.Thumb className={styles.scrollThumb} />
      </ScrollArea.Scrollbar>
    </ScrollArea.Root>
  );
}
