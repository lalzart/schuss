import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { dispatchDesktopOperation, inspectCatalogFamily } from "../core/bridge";
import {
  componentInspectRequest,
  implementationSearchRequest,
  projectObjectInspectRequest,
  projectObjectsListRequest,
} from "../core/patcherRequests";
import type {
  ComponentContract,
  ImplementationSearchItem,
  ImplementationSearchValue,
  ProjectObjectDefinition,
  ProjectObjectInspectValue,
  ProjectObjectSummary,
  ProjectObjectsListValue,
} from "../core/types";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import styles from "./ObjectLibrary.module.css";

type Props = {
  onAdd?: (component: ComponentContract) => void;
  projectRevision?: number;
  workspace?: string;
};

type ObjectSource = "catalog" | "project";

function label(value: string): string {
  return value.split("-").map((part) => part === "ai" ? "AI" : part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function evidenceLabel(item: ProjectObjectSummary): string {
  const host = item.evidence.host_evaluation.status === "passed"
    ? "Host evaluated"
    : `Host ${label(item.evidence.host_evaluation.status)}`;
  const target = item.evidence.target_lowering === "not-run"
    ? "Target not lowered"
    : `Target ${label(item.evidence.target_lowering)}`;
  return `${host} · ${target}`;
}

function sameProjectObject(a: ProjectObjectSummary | null, b: ProjectObjectSummary): boolean {
  return a?.object_reference.object_definition_id === b.object_reference.object_definition_id
    && a.object_reference.revision === b.object_reference.revision
    && a.object_reference.content_hash === b.object_reference.content_hash;
}

export function ObjectLibrary({ onAdd, projectRevision, workspace }: Props) {
  const [source, setSource] = useState<ObjectSource>("catalog");
  const [collection, setCollection] = useState<"patcher" | "all">("patcher");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ImplementationSearchValue | null>(null);
  const [selected, setSelected] = useState<ImplementationSearchItem | null>(null);
  const [functionFilter, setFunctionFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);
  const [resolved, setResolved] = useState<Record<string, ComponentContract | null>>({});
  const [catalogMessage, setCatalogMessage] = useState<string | null>(null);
  const [projectResult, setProjectResult] = useState<ProjectObjectsListValue | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectObjectSummary | null>(null);
  const [projectDefinitions, setProjectDefinitions] = useState<Record<string, ProjectObjectDefinition | null>>({});
  const [projectLoading, setProjectLoading] = useState(Boolean(workspace));
  const [projectMessage, setProjectMessage] = useState<string | null>(null);
  const debounced = useDebouncedValue(query, 160);

  useEffect(() => {
    setSource("catalog");
  }, [workspace]);

  useEffect(() => {
    if (workspace && source === "project") {
      setLoading(false);
      return undefined;
    }
    let active = true;
    setLoading(true);
    dispatchDesktopOperation<ImplementationSearchValue>(implementationSearchRequest(debounced))
      .then((value) => {
        if (!active) return;
        setResult(value);
        setSelected((current) => value.results.find((item) => item.implementation_id === current?.implementation_id) ?? value.results[0] ?? null);
        setCatalogMessage(null);
      })
      .catch((error: unknown) => active && setCatalogMessage(error instanceof Error ? error.message : "Catalog unavailable."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [debounced, source, workspace]);

  useEffect(() => {
    if (!workspace) {
      setProjectResult(null);
      setSelectedProject(null);
      setProjectDefinitions({});
      setProjectLoading(false);
      setProjectMessage(null);
      return undefined;
    }
    let active = true;
    setProjectLoading(true);
    dispatchDesktopOperation<ProjectObjectsListValue>(projectObjectsListRequest(), workspace)
      .then((value) => {
        if (!active) return;
        setProjectResult(value);
        setSelectedProject((current) => value.objects.find((item) => sameProjectObject(current, item)) ?? value.objects[0] ?? null);
        setProjectDefinitions({});
        setProjectMessage(null);
      })
      .catch((error: unknown) => {
        if (!active) return;
        setProjectResult(null);
        setSelectedProject(null);
        setProjectDefinitions({});
        setProjectMessage(error instanceof Error ? error.message : "Project objects are unavailable.");
        setSource("catalog");
      })
      .finally(() => active && setProjectLoading(false));
    return () => { active = false; };
  }, [projectRevision, workspace]);

  const functions = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of result?.results ?? []) counts.set(item.primary_function, (counts.get(item.primary_function) ?? 0) + 1);
    return [...counts.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [result]);

  const visible = useMemo(
    () => (result?.results ?? []).filter((item) => (
      (collection === "all" || item.readiness_states.includes("contracted"))
      && (functionFilter === "all" || item.primary_function === functionFilter)
    )),
    [collection, functionFilter, result],
  );

  const visibleProject = useMemo(() => {
    const needle = debounced.trim().toLowerCase();
    return (projectResult?.objects ?? []).filter((item) => !needle || [item.display_name, item.function, item.form].some((value) => value.toLowerCase().includes(needle)));
  }, [debounced, projectResult]);

  const resolve = useCallback(async (item: ImplementationSearchItem) => {
    if (!onAdd) return;
    setResolving(item.implementation_id);
    setCatalogMessage(null);
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
      onAdd(value.component_contract);
    } catch (error) {
      setResolved((current) => ({ ...current, [item.implementation_id]: null }));
      setCatalogMessage(error instanceof Error ? error.message : "Object could not be resolved.");
    } finally {
      setResolving(null);
    }
  }, [onAdd]);

  const resolveProject = useCallback(async (item: ProjectObjectSummary) => {
    if (!onAdd || !workspace) return;
    const identity = item.object_reference.object_definition_id;
    setResolving(identity);
    setProjectMessage(null);
    try {
      const value = await dispatchDesktopOperation<ProjectObjectInspectValue>(
        projectObjectInspectRequest(item.object_reference),
        workspace,
      );
      setProjectDefinitions((current) => ({ ...current, [identity]: value.object_definition }));
      onAdd(value.object_definition.component_contract);
    } catch (error) {
      setProjectDefinitions((current) => ({ ...current, [identity]: null }));
      setProjectMessage(error instanceof Error ? error.message : "Project object could not be resolved.");
    } finally {
      setResolving(null);
    }
  }, [onAdd, workspace]);

  const projectAvailable = projectResult !== null || projectLoading;
  const activeLoading = source === "project" ? projectLoading : loading;
  const shownCount = source === "project" ? visibleProject.length : visible.length;
  const activeMessage = source === "project" ? projectMessage : catalogMessage;

  return (
    <section className={styles.library}>
      <div className={styles.listPane}>
        <header className={styles.listHeader}>
          <div><span>OBJECTS</span><strong>{source === "project" ? "Project objects" : "Add object"}</strong></div>
          <div className={styles.filters}>
            {workspace && <select aria-label="Object source" value={source} onChange={(event) => setSource(event.currentTarget.value as ObjectSource)}><option value="catalog">Catalog</option><option value="project" disabled={!projectAvailable}>Project ({projectResult?.object_count ?? 0})</option></select>}
            {source === "catalog" && <><select aria-label="Object collection" value={collection} onChange={(event) => setCollection(event.currentTarget.value as "patcher" | "all")}><option value="patcher">Patcher</option><option value="all">All catalog</option></select><select aria-label="Object function" value={functionFilter} onChange={(event) => setFunctionFilter(event.currentTarget.value)}><option value="all">All functions</option>{functions.map(([name, count]) => <option value={name} key={name}>{label(name)} ({count})</option>)}</select></>}
          </div>
          <input type="search" value={query} onChange={(event) => setQuery(event.currentTarget.value)} placeholder={source === "project" ? "Search project objects" : "Search objects"} aria-label={source === "project" ? "Search project objects" : "Search objects"} />
        </header>
        <div className={styles.summary}><span>{shownCount} shown</span><span>{activeLoading ? "Loading…" : source === "project" ? "Accepted project" : collection === "patcher" ? "Contracted" : "Complete catalog"}</span></div>
        <div className={styles.rows}>
          {source === "catalog" && visible.map((item) => (
            <Fragment key={item.implementation_id}><div className={styles.row} data-selected={selected?.implementation_id === item.implementation_id}>
              <button className={styles.select} type="button" aria-expanded={selected?.implementation_id === item.implementation_id} onClick={() => setSelected((current) => current?.implementation_id === item.implementation_id ? null : item)}>
                <span className={styles.route} data-function={item.primary_function} />
                <span className={styles.rowText}><strong>{item.family_display_name}</strong><small>{label(item.form)} · {item.provenance_tags.includes("mutable-instruments-derived") ? "Mutable-derived" : item.provenance_sources[0]}</small></span>
              </button>
              {onAdd && <button className={styles.add} type="button" disabled={resolving !== null} aria-label={`Add ${item.family_display_name}`} onClick={() => void resolve(item)}>{resolving === item.implementation_id ? "…" : "+"}</button>}
            </div>{selected?.implementation_id === item.implementation_id && <div className={styles.inlineDetail}><dl><div><dt>Implementation</dt><dd>{item.display_name}</dd></div><div><dt>Form</dt><dd>{label(item.form)}</dd></div><div><dt>Readiness</dt><dd>{item.readiness_states.map(label).join(" · ")}</dd></div><div><dt>Origin</dt><dd>{item.provenance_sources.join(" · ")}</dd></div></dl><code>{item.implementation_id}</code>{resolved[item.implementation_id] && <span>{resolved[item.implementation_id]?.ports.length} ports · {resolved[item.implementation_id]?.parameters.length} parameters</span>}</div>}</Fragment>
          ))}
          {source === "project" && visibleProject.map((item) => {
            const identity = item.object_reference.object_definition_id;
            const definition = projectDefinitions[identity];
            return <Fragment key={`${identity}@${item.object_reference.revision}`}><div className={styles.row} data-selected={sameProjectObject(selectedProject, item)}>
              <button className={styles.select} type="button" aria-expanded={sameProjectObject(selectedProject, item)} onClick={() => setSelectedProject((current) => sameProjectObject(current, item) ? null : item)}>
                <span className={styles.route} data-function={item.function} />
                <span className={styles.rowText}><strong>{item.display_name}</strong><small>{label(item.form)} · {definition ? label(definition.family.provenance) : "Project-local"}<br />{evidenceLabel(item)}</small></span>
              </button>
              {onAdd && <button className={styles.add} type="button" disabled={resolving !== null} aria-label={`Add ${item.display_name}`} onClick={() => void resolveProject(item)}>{resolving === identity ? "…" : "+"}</button>}
            </div>{sameProjectObject(selectedProject, item) && <div className={styles.inlineDetail}><dl><div><dt>Form</dt><dd>{label(item.form)}</dd></div><div><dt>Evidence</dt><dd>{evidenceLabel(item)}</dd></div><div><dt>Origin</dt><dd>{definition ? label(definition.family.provenance) : "Accepted project-local"}</dd></div></dl><code>{identity}@{item.object_reference.revision}</code></div>}</Fragment>;
          })}
          {!activeLoading && shownCount === 0 && <p className={styles.empty}>{source === "project" ? "No accepted project-local objects. MCP-created objects stay here instead of entering the permanent catalog." : "No catalog objects match."}</p>}
        </div>
        {activeMessage && <p className={styles.message} role="status">{activeMessage}</p>}
      </div>
    </section>
  );
}
