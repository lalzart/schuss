import { useCallback, useEffect, useMemo, useState } from "react";
import { dispatchDesktopOperation, inspectCatalogFamily } from "../core/bridge";
import { componentInspectRequest, implementationSearchRequest } from "../core/patcherRequests";
import type { ComponentContract, ImplementationSearchItem, ImplementationSearchValue } from "../core/types";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import styles from "./ObjectLibrary.module.css";

type Props = {
  mode: "page" | "drawer";
  onAdd?: (component: ComponentContract) => void;
};

function label(value: string): string {
  return value.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

export function ObjectLibrary({ mode, onAdd }: Props) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ImplementationSearchValue | null>(null);
  const [selected, setSelected] = useState<ImplementationSearchItem | null>(null);
  const [functionFilter, setFunctionFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);
  const [resolved, setResolved] = useState<Record<string, ComponentContract | null>>({});
  const [message, setMessage] = useState<string | null>(null);
  const debounced = useDebouncedValue(query, 160);

  useEffect(() => {
    let active = true;
    setLoading(true);
    dispatchDesktopOperation<ImplementationSearchValue>(implementationSearchRequest(debounced))
      .then((value) => {
        if (!active) return;
        setResult(value);
        setSelected((current) => value.results.find((item) => item.implementation_id === current?.implementation_id) ?? value.results[0] ?? null);
        setMessage(null);
      })
      .catch((error: unknown) => active && setMessage(error instanceof Error ? error.message : "Catalog unavailable."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [debounced]);

  const functions = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of result?.results ?? []) counts.set(item.primary_function, (counts.get(item.primary_function) ?? 0) + 1);
    return [...counts.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [result]);

  const visible = useMemo(
    () => (result?.results ?? []).filter((item) => functionFilter === "all" || item.primary_function === functionFilter),
    [functionFilter, result],
  );

  const resolve = useCallback(async (item: ImplementationSearchItem) => {
    if (!onAdd) return;
    setResolving(item.implementation_id);
    setMessage(null);
    try {
      const inspection = await inspectCatalogFamily(item.family_reference);
      const implementation = inspection.family.implementations.find((candidate) => candidate.implementation_id === item.implementation_id);
      if (!implementation || implementation.contract_references.length !== 1) {
        throw new Error("Catalogued only — no single component contract is available for the patcher.");
      }
      const value = await dispatchDesktopOperation<{ component_contract: ComponentContract }>(
        componentInspectRequest({
          component_contract_id: implementation.contract_references[0].stable_id,
          revision: implementation.contract_references[0].revision,
          content_hash: implementation.contract_references[0].content_hash,
        }),
      );
      setResolved((current) => ({ ...current, [item.implementation_id]: value.component_contract }));
    } catch (error) {
      setResolved((current) => ({ ...current, [item.implementation_id]: null }));
      setMessage(error instanceof Error ? error.message : "Object could not be resolved.");
    } finally {
      setResolving(null);
    }
  }, [onAdd]);

  useEffect(() => {
    if (
      onAdd &&
      selected &&
      !Object.prototype.hasOwnProperty.call(resolved, selected.implementation_id) &&
      resolving !== selected.implementation_id
    ) {
      void resolve(selected);
    }
  }, [onAdd, resolve, resolved, resolving, selected]);

  return (
    <section className={styles.library} data-mode={mode}>
      <aside className={styles.functions} aria-label="Object functions">
        <header><span>FUNCTION</span><strong>{result?.total_matches ?? 0}</strong></header>
        <button type="button" data-active={functionFilter === "all"} onClick={() => setFunctionFilter("all")}>All objects <code>{result?.results.length ?? 0}</code></button>
        {functions.map(([name, count]) => (
          <button type="button" data-active={functionFilter === name} key={name} onClick={() => setFunctionFilter(name)}>{label(name)} <code>{count}</code></button>
        ))}
      </aside>
      <div className={styles.listPane}>
        <header className={styles.listHeader}>
          <div><span>OBJECTS</span><strong>{mode === "page" ? "Catalog" : "Add object"}</strong></div>
          <input type="search" value={query} onChange={(event) => setQuery(event.currentTarget.value)} placeholder="Search objects" aria-label="Search objects" />
        </header>
        <div className={styles.summary}><span>{visible.length} shown</span><span>{loading ? "Searching…" : "Exact catalog"}</span></div>
        <div className={styles.rows}>
          {visible.map((item) => (
            <div className={styles.row} data-selected={selected?.implementation_id === item.implementation_id} key={item.implementation_id}>
              <button className={styles.select} type="button" onClick={() => setSelected(item)}>
                <span className={styles.route} data-function={item.primary_function} />
                <span className={styles.rowText}><strong>{item.family_display_name}</strong><small>{label(item.form)} · {item.provenance_tags.includes("mutable-instruments-derived") ? "Mutable-derived" : item.provenance_sources[0]}</small></span>
              </button>
              {onAdd && <button
                className={styles.add}
                type="button"
                disabled={!resolved[item.implementation_id]}
                aria-label={resolved[item.implementation_id] ? `Add ${item.family_display_name}` : `${item.family_display_name} unavailable`}
                onClick={() => resolved[item.implementation_id] && onAdd(resolved[item.implementation_id]!)}
              >{resolving === item.implementation_id ? "…" : "+"}</button>}
            </div>
          ))}
        </div>
        {message && <p className={styles.message} role="status">{message}</p>}
      </div>
      {mode === "page" && (
        <aside className={styles.detail}>
          {selected ? <>
            <span className={styles.detailKind}>{label(selected.primary_function)}</span>
            <h2>{selected.family_display_name}</h2>
            <dl>
              <div><dt>Implementation</dt><dd>{selected.display_name}</dd></div>
              <div><dt>Form</dt><dd>{label(selected.form)}</dd></div>
              <div><dt>Level</dt><dd>{label(selected.abstraction_level)}</dd></div>
              <div><dt>Readiness</dt><dd>{selected.readiness_states.map(label).join(" · ")}</dd></div>
              <div><dt>Origin</dt><dd>{selected.provenance_tags.includes("mutable-instruments-derived") ? "Mutable Instruments derived" : selected.provenance_sources.join(" · ")}</dd></div>
            </dl>
            <code>{selected.implementation_id}</code>
          </> : <p>Select an object.</p>}
        </aside>
      )}
    </section>
  );
}
