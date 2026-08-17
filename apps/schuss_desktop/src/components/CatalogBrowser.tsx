import { startTransition, useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import * as Tooltip from "@radix-ui/react-tooltip";
import {
  describeApplication,
  inspectCatalogFamily,
  searchCatalog,
} from "../core/bridge";
import type {
  ApplicationDescription,
  CatalogInspectValue,
  CatalogSearchItem,
  CatalogSearchValue,
} from "../core/types";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { CatalogDetail } from "./CatalogDetail";
import { CatalogList, routeTone } from "./CatalogList";
import styles from "./CatalogBrowser.module.css";

const DESKTOP_OPERATIONS = new Set([
  "application.describe",
  "catalog.search",
  "catalog.inspect",
]);

function referenceKey(item: CatalogSearchItem): string {
  return `${item.family_reference.family_id}@${item.family_reference.revision}`;
}

function displayLabel(value: string): string {
  return value
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "The local Schuss core is unavailable.";
}

export function CatalogBrowser() {
  const [application, setApplication] = useState<ApplicationDescription | null>(null);
  const [baseline, setBaseline] = useState<CatalogSearchValue | null>(null);
  const [results, setResults] = useState<CatalogSearchItem[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [inspection, setInspection] = useState<CatalogInspectValue | null>(null);
  const [query, setQuery] = useState("");
  const [functionFilter, setFunctionFilter] = useState("all");
  const [provenanceFilter, setProvenanceFilter] = useState("all");
  const [readinessFilter, setReadinessFilter] = useState("all");
  const [initialLoading, setInitialLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [initialError, setInitialError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [refreshToken, setRefreshToken] = useState(0);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const debouncedQuery = useDebouncedValue(query, 180);

  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      if (event.metaKey && event.key.toLowerCase() === "k") {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", focusSearch);
    return () => window.removeEventListener("keydown", focusSearch);
  }, []);

  useEffect(() => {
    let active = true;
    setInitialLoading(true);
    setInitialError(null);
    Promise.all([describeApplication(), searchCatalog("")])
      .then(([description, catalog]) => {
        if (!active) return;
        const routes = description.operations.filter(
          (operation) =>
            DESKTOP_OPERATIONS.has(operation.operation) &&
            operation.availability === "available" &&
            operation.effect_class === "read-only",
        );
        if (routes.length !== DESKTOP_OPERATIONS.size) {
          throw new Error("The selected Schuss context does not expose all desktop read routes.");
        }
        setApplication(description);
        setBaseline(catalog);
        setResults(catalog.results);
        setSelectedKey((current) =>
          current ?? (catalog.results[0] ? referenceKey(catalog.results[0]) : null),
        );
      })
      .catch((error: unknown) => {
        if (active) setInitialError(messageFrom(error));
      })
      .finally(() => {
        if (active) setInitialLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadToken]);

  useEffect(() => {
    if (baseline === null) return;
    const usesBaseline =
      debouncedQuery.trim() === "" &&
      functionFilter === "all" &&
      provenanceFilter === "all" &&
      readinessFilter === "all" &&
      refreshToken === 0;
    if (usesBaseline) {
      setResults(baseline.results);
      setSearchError(null);
      return;
    }

    let active = true;
    setSearchLoading(true);
    setSearchError(null);
    searchCatalog(debouncedQuery, {
      function: functionFilter === "all" ? [] : [functionFilter],
      provenance: provenanceFilter === "all" ? [] : [provenanceFilter],
      readiness: readinessFilter === "all" ? [] : [readinessFilter],
    })
      .then((catalog) => {
        if (!active) return;
        startTransition(() => setResults(catalog.results));
      })
      .catch((error: unknown) => {
        if (active) setSearchError(messageFrom(error));
      })
      .finally(() => {
        if (active) setSearchLoading(false);
      });
    return () => {
      active = false;
    };
  }, [baseline, debouncedQuery, functionFilter, provenanceFilter, readinessFilter, refreshToken]);

  useEffect(() => {
    if (results.length === 0) {
      setSelectedKey(null);
      return;
    }
    if (selectedKey === null || !results.some((item) => referenceKey(item) === selectedKey)) {
      setSelectedKey(referenceKey(results[0]));
    }
  }, [results, selectedKey]);

  useEffect(() => {
    if (selectedKey === null || baseline === null) {
      setInspection(null);
      return;
    }
    const item = baseline.results.find((candidate) => referenceKey(candidate) === selectedKey);
    if (item === undefined) return;
    let active = true;
    setDetailLoading(true);
    setDetailError(null);
    inspectCatalogFamily(item.family_reference)
      .then((value) => {
        if (active) setInspection(value);
      })
      .catch((error: unknown) => {
        if (active) {
          setInspection(null);
          setDetailError(messageFrom(error));
        }
      })
      .finally(() => {
        if (active) setDetailLoading(false);
      });
    return () => {
      active = false;
    };
  }, [baseline, selectedKey]);

  const categories = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of baseline?.results ?? []) {
      counts.set(item.primary_function, (counts.get(item.primary_function) ?? 0) + 1);
    }
    return [...counts];
  }, [baseline]);

  const readinessOptions = useMemo(() => {
    const states = new Set((baseline?.results ?? []).flatMap((item) => item.readiness_states));
    return [...states].sort();
  }, [baseline]);

  const selectFamily = useCallback((key: string) => setSelectedKey(key), []);
  const exactRecordSet = baseline?.record_set_reference;
  const availableRouteCount =
    application?.operations.filter((operation) => DESKTOP_OPERATIONS.has(operation.operation)).length ?? 0;

  if (initialLoading) {
    return (
      <div className={styles.startup} role="status">
        <div className={styles.startupRoute} aria-hidden="true" />
        <p>Opening exact catalog context</p>
        <code>schuss-record-set-000021@1</code>
        <span>Validating canonical operation routes…</span>
      </div>
    );
  }

  if (initialError !== null || baseline === null) {
    return (
      <div className={styles.startupError} role="alert">
        <span>CORE ROUTE UNAVAILABLE</span>
        <h1>The catalog could not open.</h1>
        <p>{initialError}</p>
        <button type="button" onClick={() => setReloadToken((value) => value + 1)}>
          Retry local core
        </button>
      </div>
    );
  }

  return (
    <div className={styles.browser}>
      <aside className={styles.categoryRail} aria-label="Catalog functions">
        <div className={styles.railHeading}>
          <span>FUNCTION</span>
          <strong>{baseline.results.length}</strong>
        </div>
        <nav className={styles.categoryNav}>
          <button
            type="button"
            className={styles.categoryButton}
            data-selected={functionFilter === "all" ? "true" : "false"}
            data-tone="neutral"
            onClick={() => setFunctionFilter("all")}
          >
            <span className={styles.categoryRoute} aria-hidden="true" />
            <span>All functions</span>
            <code>{baseline.results.length}</code>
          </button>
          {categories.map(([category, count]) => (
            <button
              type="button"
              className={styles.categoryButton}
              data-selected={functionFilter === category ? "true" : "false"}
              data-tone={routeTone(category)}
              key={category}
              onClick={() => setFunctionFilter(category)}
            >
              <span className={styles.categoryRoute} aria-hidden="true" />
              <span>{displayLabel(category)}</span>
              <code>{count}</code>
            </button>
          ))}
        </nav>
        <div className={styles.railFooter}>
          <span>{exactRecordSet?.record_set_id}@{exactRecordSet?.revision}</span>
          <span>{availableRouteCount} read routes</span>
        </div>
      </aside>

      <section className={styles.drawer} aria-label="Catalog browser">
        <header className={styles.drawerHeader}>
          <div>
            <span className={styles.eyebrow}>OBJECT LIBRARY</span>
            <h1>Browse catalog</h1>
          </div>
          <Tooltip.Root>
            <Tooltip.Trigger asChild>
              <button
                type="button"
                className={styles.refreshButton}
                aria-label="Refresh catalog operation"
                onClick={() => setRefreshToken((value) => value + 1)}
              >
                ↻
              </button>
            </Tooltip.Trigger>
            <Tooltip.Portal>
              <Tooltip.Content className={styles.tooltip} sideOffset={6}>
                Repeat the exact catalog.search operation
              </Tooltip.Content>
            </Tooltip.Portal>
          </Tooltip.Root>
        </header>

        <div className={styles.searchBlock}>
          <label htmlFor="catalog-search">Search names, aliases, tags, signals, or exact IDs</label>
          <div className={styles.searchInputWrap}>
            <span aria-hidden="true">⌕</span>
            <input
              ref={searchInputRef}
              id="catalog-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.currentTarget.value)}
              placeholder="Search exact catalog…"
              autoComplete="off"
              spellCheck={false}
            />
            <kbd>⌘ K</kbd>
          </div>
        </div>

        <div className={styles.filterBar}>
          <Tabs.Root value={provenanceFilter} onValueChange={setProvenanceFilter}>
            <Tabs.List className={styles.provenanceTabs} aria-label="Provenance lens">
              <Tabs.Trigger className={styles.provenanceTab} value="all">
                All origins
              </Tabs.Trigger>
              <Tabs.Trigger
                className={styles.provenanceTab}
                value="mutable-instruments-derived"
              >
                Mutable-derived
              </Tabs.Trigger>
            </Tabs.List>
          </Tabs.Root>
          <label className={styles.readinessSelect}>
            <span className={styles.visuallyHidden}>Readiness</span>
            <select
              value={readinessFilter}
              onChange={(event) => setReadinessFilter(event.currentTarget.value)}
            >
              <option value="all">Any support status</option>
              {readinessOptions.map((status) => (
                <option key={status} value={status}>
                  {displayLabel(status)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className={styles.resultSummary} aria-live="polite">
          <span>
            {results.length} {results.length === 1 ? "family" : "families"}
          </span>
          <span>{searchLoading ? "ROUTING…" : "CANONICAL RESULT"}</span>
        </div>
        {searchError !== null ? (
          <div className={styles.searchError} role="alert">
            {searchError}
          </div>
        ) : null}
        <CatalogList
          items={results}
          selectedKey={selectedKey}
          loading={searchLoading}
          onSelect={selectFamily}
        />
      </section>

      <section className={styles.inspector} aria-label="Object detail">
        <CatalogDetail inspection={inspection} loading={detailLoading} error={detailError} />
      </section>
    </div>
  );
}
