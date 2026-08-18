import { useCallback, useState } from "react";
import type { AppRoute } from "../App";
import { dispatchDesktopOperation } from "../core/bridge";
import { projectForkRequest, projectInitRequest, profileTransactRequest } from "../core/patcherRequests";
import type { DspGraph, ProjectManifest, ProjectReference } from "../core/types";
import { ObjectLibrary } from "./ObjectLibrary";
import { PatchEditor } from "./PatchEditor";
import styles from "./DesktopApp.module.css";

const RECENTS_KEY = "schuss.desktop.recent-projects.v1";

type Props = {
  route: AppRoute;
  navigate: (route: AppRoute) => void;
  onEditorDirtyChange: (dirty: boolean) => void;
};
type ForkValue = { project: ProjectManifest; graph: DspGraph };

function projectReference(project: ProjectManifest): ProjectReference {
  return { project_id: project.project_id, revision: project.revision, content_hash: project.content_hash };
}

function loadRecents(): string[] {
  try {
    const value = JSON.parse(localStorage.getItem(RECENTS_KEY) ?? "[]") as unknown;
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

export function DesktopApp({ route, navigate, onEditorDirtyChange }: Props) {
  const [recents, setRecents] = useState(loadRecents);
  const [workspace, setWorkspace] = useState(recents[0] ?? "");
  const [showNew, setShowNew] = useState(false);
  const [projectId, setProjectId] = useState("schuss-project-000100");
  const [patchName, setPatchName] = useState("Untitled patch");
  const [createStage, setCreateStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const creating = createStage !== null;

  const remember = useCallback((path: string) => {
    setRecents((current) => {
      const next = [path, ...current.filter((item) => item !== path)].slice(0, 8);
      localStorage.setItem(RECENTS_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const open = useCallback((path: string) => {
    const normalized = path.trim();
    if (!normalized.startsWith("/")) {
      setError("Enter an absolute project workspace path.");
      return;
    }
    setError(null);
    remember(normalized);
    navigate({ view: "editor", workspace: normalized });
  }, [navigate, remember]);

  const create = useCallback(async () => {
    const path = workspace.trim();
    if (!path.startsWith("/")) {
      setError("Enter an absolute workspace path for the new patch.");
      return;
    }
    if (!/^schuss-project-[0-9]{6}$/.test(projectId)) {
      setError("Project ID must use the form schuss-project-000000.");
      return;
    }
    if (!patchName.trim()) {
      setError("Patch name cannot be empty.");
      return;
    }
    setCreateStage("Preparing workspace…");
    setError(null);
    try {
      const initialized = await dispatchDesktopOperation<{ project: ProjectManifest }>(projectInitRequest(projectId), path);
      setCreateStage("Copying accepted profile…");
      const forked = await dispatchDesktopOperation<ForkValue>(projectForkRequest(projectReference(initialized.project)), path);
      setCreateStage("Naming patch…");
      await dispatchDesktopOperation(
        profileTransactRequest(
          projectReference(forked.project),
          { graph_id: forked.graph.graph_id, revision: forked.graph.revision, content_hash: forked.graph.content_hash },
          [{ edit: "set-graph-display-name", display_name: patchName.trim() }],
        ),
        path,
      );
      remember(path);
      setShowNew(false);
      navigate({ view: "editor", workspace: path });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The patch could not be created.");
    } finally {
      setCreateStage(null);
    }
  }, [navigate, patchName, projectId, remember, workspace]);

  if (route.view === "editor") {
    return (
      <PatchEditor
        workspace={route.workspace}
        onClose={() => navigate({ view: "patches" })}
        onDirtyChange={onEditorDirtyChange}
      />
    );
  }
  if (route.view === "objects") return <ObjectLibrary mode="page" />;

  return (
    <section className={styles.patches}>
      <header className={styles.pageHeader}>
        <div><span className={styles.eyebrow}>PROJECTS</span><h1>Patches</h1></div>
        <button className={styles.primaryButton} type="button" onClick={() => setShowNew(true)}>New patch</button>
      </header>
      <div className={styles.openBar}>
        <label htmlFor="workspace">Project workspace</label>
        <input id="workspace" value={workspace} onChange={(event) => setWorkspace(event.currentTarget.value)} placeholder="/absolute/path/to/patch" spellCheck={false} />
        <button type="button" onClick={() => open(workspace)}>Open</button>
      </div>
      {error && <p className={styles.error} role="alert">{error}</p>}
      <div className={styles.recentHeader}><span>RECENT</span><span>{recents.length}</span></div>
      <div className={styles.recentList}>
        {recents.length === 0 ? (
          <div className={styles.empty}><strong>No recent patches</strong><span>Create a patch or open an existing Schuss workspace.</span></div>
        ) : recents.map((path) => (
          <button className={styles.recentRow} type="button" key={path} onClick={() => open(path)}>
            <span className={styles.patchIcon} aria-hidden="true" />
            <strong>{path.split("/").filter(Boolean).at(-1)}</strong><code>{path}</code><span>Open</span>
          </button>
        ))}
      </div>
      {showNew && (
        <div className={styles.scrim} role="presentation" onMouseDown={() => !creating && setShowNew(false)}>
          <section className={styles.dialog} role="dialog" aria-modal="true" aria-labelledby="new-patch-title" onMouseDown={(event) => event.stopPropagation()}>
            <header><div><span className={styles.eyebrow}>NEW PROJECT</span><h2 id="new-patch-title">Create patch</h2></div><button type="button" disabled={creating} onClick={() => setShowNew(false)} aria-label="Close">×</button></header>
            <label>Patch name<input disabled={creating} value={patchName} onChange={(event) => setPatchName(event.currentTarget.value)} /></label>
            <label>Workspace<input disabled={creating} value={workspace} onChange={(event) => setWorkspace(event.currentTarget.value)} placeholder="/absolute/path/to/patch" /></label>
            <label>Project ID<input disabled={creating} value={projectId} onChange={(event) => setProjectId(event.currentTarget.value)} /></label>
            <p>Starts from the accepted seven-object profile. The ID is explicit until a shared allocator exists.</p>
            {error && <p className={styles.error} role="alert">{error}</p>}
            {createStage && <p className={styles.progress} role="status" aria-live="polite">{createStage}</p>}
            <footer><button type="button" disabled={creating} onClick={() => setShowNew(false)}>Cancel</button><button className={styles.primaryButton} type="button" disabled={creating} onClick={create}>{creating ? createStage : "Create patch"}</button></footer>
          </section>
        </div>
      )}
    </section>
  );
}
