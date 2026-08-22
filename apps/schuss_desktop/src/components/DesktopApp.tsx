import { useCallback, useEffect, useRef, useState } from "react";
import { CoreOperationError, dispatchDesktopOperation } from "../core/bridge";
import {
  loadDesktopPreferences,
  saveDesktopPreferences,
  type DesktopPreferences,
  type DrawerTab,
} from "../core/desktopPreferences";
import {
  workspaceProjectCreateRequest,
  workspaceProjectsListRequest,
} from "../core/patcherRequests";
import type {
  WorkspaceProject,
  WorkspaceProjectCreateValue,
  WorkspaceProjectsValue,
} from "../core/types";
import { InstrumentLibrary } from "./InstrumentLibrary";
import { PatchEditor } from "./PatchEditor";
import styles from "./DesktopApp.module.css";

export function DesktopApp() {
  const [surface, setSurface] = useState<"instruments" | "workshop">("instruments");
  const [preferences, setPreferences] = useState(loadDesktopPreferences);
  const [workspace, setWorkspace] = useState("");
  const [projects, setProjects] = useState<WorkspaceProject[]>([]);
  const [libraryStage, setLibraryStage] = useState<string | null>(
    preferences.projectsRoot ? "Starting Schuss core…" : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [rootDraft, setRootDraft] = useState(preferences.projectsRoot);
  const [patchName, setPatchName] = useState("Untitled patch");
  const [creating, setCreating] = useState(false);
  const automaticCreation = useRef<{ root: string; promise: Promise<WorkspaceProjectCreateValue> } | null>(null);
  const preferredWorkspace = useRef(preferences.lastWorkspace);

  useEffect(() => {
    saveDesktopPreferences(preferences);
  }, [preferences]);

  const selectProject = useCallback((nextWorkspace: string) => {
    if (
      workspace
      && workspace !== nextWorkspace
      && dirty
      && !window.confirm("Open another patch and discard these unsaved edits?")
    ) return;
    setDirty(false);
    setWorkspace(nextWorkspace);
    preferredWorkspace.current = nextWorkspace;
    setPreferences((current) => ({ ...current, lastWorkspace: nextWorkspace }));
  }, [dirty, workspace]);

  useEffect(() => {
    if (surface !== "workshop") return undefined;
    const root = preferences.projectsRoot;
    if (!root) {
      setProjects([]);
      setWorkspace("");
      setLibraryStage(null);
      return undefined;
    }
    let active = true;
    setLibraryStage("Starting Schuss core and browsing projects…");
    setError(null);
    dispatchDesktopOperation<WorkspaceProjectsValue>(workspaceProjectsListRequest(), root)
      .then(async (value) => {
        if (!active) return;
        let nextProjects = value.projects;
        if (nextProjects.length === 0) {
          setLibraryStage("Creating the first Untitled patch…");
          if (automaticCreation.current?.root !== root) {
            automaticCreation.current = {
              root,
              promise: dispatchDesktopOperation<WorkspaceProjectCreateValue>(
                workspaceProjectCreateRequest("Untitled patch"),
                root,
              ),
            };
          }
          const created = await automaticCreation.current.promise;
          if (!active) return;
          nextProjects = [created.project];
        }
        setProjects(nextProjects);
        const preferred = nextProjects.find((item) => item.workspace === preferredWorkspace.current)
          ?? nextProjects[0]
          ?? null;
        if (preferred) {
          setWorkspace(preferred.workspace);
          preferredWorkspace.current = preferred.workspace;
          setPreferences((current) => (
            current.lastWorkspace === preferred.workspace
              ? current
              : { ...current, lastWorkspace: preferred.workspace }
          ));
        }
        if (value.rejected_child_count > 0) {
          setError(`${value.rejected_child_count} folder${value.rejected_child_count === 1 ? " was" : "s were"} skipped because they are not valid accepted Schuss projects.`);
        }
      })
      .catch(async (caught: unknown) => {
        if (!active) return;
        if (caught instanceof CoreOperationError && caught.code === "WORKSPACE_ROOT_NOT_FOUND") {
          try {
            setLibraryStage("Creating the first Untitled patch…");
            if (automaticCreation.current?.root !== root) {
              automaticCreation.current = {
                root,
                promise: dispatchDesktopOperation<WorkspaceProjectCreateValue>(
                  workspaceProjectCreateRequest("Untitled patch"),
                  root,
                ),
              };
            }
            const created = await automaticCreation.current.promise;
            if (!active) return;
            setProjects([created.project]);
            setWorkspace(created.project.workspace);
            preferredWorkspace.current = created.project.workspace;
            setPreferences((current) => ({ ...current, lastWorkspace: created.project.workspace }));
            return;
          } catch (creationError) {
            if (automaticCreation.current?.root === root) automaticCreation.current = null;
            if (!active) return;
            setError(creationError instanceof Error ? creationError.message : "The first patch could not be created.");
            return;
          }
        }
        if (automaticCreation.current?.root === root) automaticCreation.current = null;
        setProjects([]);
        setWorkspace("");
        setError(caught instanceof Error ? caught.message : "Projects could not be browsed.");
      })
      .finally(() => active && setLibraryStage(null));
    return () => { active = false; };
  }, [preferences.projectsRoot, surface]);

  const createProject = useCallback(async () => {
    const displayName = patchName.trim();
    if (!displayName) {
      setError("Patch name cannot be empty.");
      return;
    }
    if (!preferences.projectsRoot) {
      setShowNew(false);
      setShowSettings(true);
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const value = await dispatchDesktopOperation<WorkspaceProjectCreateValue>(
        workspaceProjectCreateRequest(displayName),
        preferences.projectsRoot,
      );
      setProjects((current) => [...current, value.project].sort((a, b) => a.display_name.localeCompare(b.display_name)));
      setShowNew(false);
      setPatchName("Untitled patch");
      selectProject(value.project.workspace);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The patch could not be created.");
    } finally {
      setCreating(false);
    }
  }, [patchName, preferences.projectsRoot, selectProject]);

  const saveSettings = useCallback(() => {
    const root = rootDraft.trim();
    if (!root.startsWith("/")) {
      setError("Projects root must be an absolute path.");
      return;
    }
    if (dirty && root !== preferences.projectsRoot && !window.confirm("Change projects root and discard these unsaved edits?")) return;
    setDirty(false);
    setWorkspace("");
    setProjects([]);
    setError(null);
    setPreferences((current) => ({ ...current, projectsRoot: root, lastWorkspace: "" }));
    setShowSettings(false);
  }, [dirty, preferences.projectsRoot, rootDraft]);

  const updateDrawer = useCallback((next: Partial<DesktopPreferences["drawer"]>) => {
    setPreferences((current) => ({
      ...current,
      drawer: { ...current.drawer, ...next },
    }));
  }, []);

  const chooseDrawer = useCallback((tab: DrawerTab) => {
    updateDrawer({ tab, open: preferences.drawer.open && preferences.drawer.tab === tab ? false : true });
  }, [preferences.drawer.open, preferences.drawer.tab, updateDrawer]);

  return (
    <>
      <div className={styles.desktop}>
        <nav className={styles.navigation} aria-label="Application">
          <button type="button" data-active={surface === "instruments"} aria-current={surface === "instruments" ? "page" : undefined} onClick={() => setSurface("instruments")}>Instruments</button>
          <button type="button" data-active={surface === "workshop"} aria-current={surface === "workshop" ? "page" : undefined} onClick={() => setSurface("workshop")}>Workshop</button>
          <span />
          <small>{surface === "instruments" ? "JUICE LIBRARY" : "PATCH · BUILD · KSOLATI"}</small>
        </nav>
        <div className={styles.surface} hidden={surface !== "instruments"}>
          <InstrumentLibrary />
        </div>
        <div className={styles.surface} hidden={surface !== "workshop"}>
          <PatchEditor
            workspace={workspace || null}
            projects={projects}
            projectsRoot={preferences.projectsRoot}
            drawer={preferences.drawer}
            libraryStage={libraryStage}
            shellError={error}
            onDirtyChange={setDirty}
            onSelectProject={selectProject}
            onCreateProject={() => setShowNew(true)}
            onOpenSettings={() => { setRootDraft(preferences.projectsRoot); setShowSettings(true); }}
            onChooseDrawer={chooseDrawer}
            onDrawerWidth={(width) => updateDrawer({ width })}
          />
        </div>
      </div>
      {showSettings && (
        <div className={styles.scrim} role="presentation" onMouseDown={() => preferences.projectsRoot && setShowSettings(false)}>
          <section className={styles.dialog} role="dialog" aria-modal="true" aria-labelledby="settings-title" onMouseDown={(event) => event.stopPropagation()}>
            <header><div><span className={styles.eyebrow}>WORKSPACE</span><h2 id="settings-title">Desktop settings</h2></div>{preferences.projectsRoot && <button type="button" onClick={() => setShowSettings(false)} aria-label="Close settings">×</button>}</header>
            <label>Projects root<input autoFocus value={rootDraft} onChange={(event) => setRootDraft(event.currentTarget.value)} placeholder="/absolute/path/to/projects" spellCheck={false} /></label>
            <p>Schuss remembers this folder. Valid projects directly inside it appear in the Patches drawer; IDs and project directories are allocated by the core.</p>
            {error && <p className={styles.error} role="alert">{error}</p>}
            <footer><button className={styles.primaryButton} type="button" onClick={saveSettings}>Use projects root</button></footer>
          </section>
        </div>
      )}
      {showNew && (
        <div className={styles.scrim} role="presentation" onMouseDown={() => !creating && setShowNew(false)}>
          <section className={styles.dialog} role="dialog" aria-modal="true" aria-labelledby="new-patch-title" onMouseDown={(event) => event.stopPropagation()}>
            <header><div><span className={styles.eyebrow}>NEW PATCH</span><h2 id="new-patch-title">Create patch</h2></div><button type="button" disabled={creating} onClick={() => setShowNew(false)} aria-label="Close new patch">×</button></header>
            <label>Patch name<input autoFocus disabled={creating} value={patchName} onChange={(event) => setPatchName(event.currentTarget.value)} onKeyDown={(event) => { if (event.key === "Enter") void createProject(); }} /></label>
            <p>The accepted starter profile, stable project ID, and collision-safe directory are handled automatically.</p>
            {error && <p className={styles.error} role="alert">{error}</p>}
            <footer><button type="button" disabled={creating} onClick={() => setShowNew(false)}>Cancel</button><button className={styles.primaryButton} type="button" disabled={creating} onClick={() => void createProject()}>{creating ? "Creating accepted project…" : "Create patch"}</button></footer>
          </section>
        </div>
      )}
    </>
  );
}
