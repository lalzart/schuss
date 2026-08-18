import { DesktopApp } from "./components/DesktopApp";
import styles from "./App.module.css";

export function App() {
  return (
    <main className={styles.shell}>
      <header className={styles.titlebar} data-tauri-drag-region>
        <div className={styles.wordmark}>
          <span className={styles.routeMark} aria-hidden="true">S</span>
          <span>SCHUSS</span>
        </div>
        <span className={styles.appTitle}>PATCHER</span>
        <div className={styles.titlebarMeta} data-tauri-drag-region>
          <span>LOCAL</span>
          <span className={styles.statusLight} aria-hidden="true" />
        </div>
      </header>
      <DesktopApp />
    </main>
  );
}
