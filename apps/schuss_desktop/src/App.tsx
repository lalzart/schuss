import { CatalogBrowser } from "./components/CatalogBrowser";
import styles from "./App.module.css";

export function App() {
  return (
    <main className={styles.shell}>
      <header className={styles.titlebar} data-tauri-drag-region>
        <div className={styles.wordmark} data-tauri-drag-region>
          <span className={styles.routeMark} aria-hidden="true">
            S
          </span>
          <span>SCHUSS</span>
          <span className={styles.sectionName}>CATALOG</span>
        </div>
        <div className={styles.titlebarMeta} data-tauri-drag-region>
          <span>LOCAL CORE</span>
          <span className={styles.readOnlyStatus}>
            <span className={styles.statusLight} aria-hidden="true" />
            READ ONLY
          </span>
        </div>
      </header>
      <CatalogBrowser />
    </main>
  );
}
