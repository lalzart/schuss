import { useCallback, useState } from "react";
import { DesktopApp } from "./components/DesktopApp";
import styles from "./App.module.css";

export type AppRoute =
  | { view: "patches" }
  | { view: "objects" }
  | { view: "editor"; workspace: string };

export function App() {
  const [route, setRoute] = useState<AppRoute>({ view: "patches" });
  const [editorDirty, setEditorDirty] = useState(false);
  const navigate = useCallback((next: AppRoute) => {
    const leavesCurrentEditor = route.view === "editor" && (
      next.view !== "editor" || next.workspace !== route.workspace
    );
    if (
      leavesCurrentEditor
      && editorDirty
      && !window.confirm("Close this patch and discard its unsaved edits?")
    ) {
      return;
    }
    setRoute(next);
  }, [editorDirty, route]);

  return (
    <main className={styles.shell}>
      <header className={styles.titlebar} data-tauri-drag-region>
        <button className={styles.wordmark} type="button" onClick={() => navigate({ view: "patches" })}>
          <span className={styles.routeMark} aria-hidden="true">S</span>
          <span>SCHUSS</span>
        </button>
        <nav className={styles.appNav} aria-label="Application">
          <button
            type="button"
            data-active={route.view === "patches" || route.view === "editor"}
            onClick={() => navigate({ view: "patches" })}
          >
            Patches
          </button>
          <button
            type="button"
            data-active={route.view === "objects"}
            onClick={() => navigate({ view: "objects" })}
          >
            Objects
          </button>
        </nav>
        <div className={styles.titlebarMeta} data-tauri-drag-region>
          <span>LOCAL</span>
          <span className={styles.statusLight} aria-hidden="true" />
        </div>
      </header>
      <DesktopApp route={route} navigate={navigate} onEditorDirtyChange={setEditorDirty} />
    </main>
  );
}
