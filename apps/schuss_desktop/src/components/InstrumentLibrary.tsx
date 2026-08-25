import { useCallback, useEffect, useMemo, useState } from "react";
import { dispatchDesktopOperation } from "../core/bridge";
import {
  instrumentLibraryListRequest,
  instrumentSessionInspectRequest,
  instrumentSessionStartRequest,
} from "../core/instrumentRequests";
import type {
  InstrumentAvailability,
  InstrumentLibraryEntry,
  InstrumentLibraryValue,
  InstrumentSessionValue,
} from "../core/types";
import styles from "./InstrumentLibrary.module.css";

const AVAILABILITY_LABELS: Record<InstrumentAvailability, string> = {
  "verified-local-build": "Ready",
  "build-required": "Build required",
  "stale-build": "Build changed",
  "research-only": "Research only",
};

function identity(item: InstrumentLibraryEntry): string {
  return `${item.prototype_id}@${item.revision}`;
}

function identityLabel(item: InstrumentLibraryEntry): "Canonical" | "Prototype" {
  return item.canonical_identity?.status === "canonical" ? "Canonical" : "Prototype";
}

export function InstrumentLibrary() {
  const [library, setLibrary] = useState<InstrumentLibraryValue | null>(null);
  const [selectedIdentity, setSelectedIdentity] = useState("");
  const [sessions, setSessions] = useState<Record<string, InstrumentSessionValue>>({});
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState("");
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const value = await dispatchDesktopOperation<InstrumentLibraryValue>(
        instrumentLibraryListRequest(),
      );
      setLibrary(value);
      setSelectedIdentity((current) => (
        value.instruments.some((item) => identity(item) === current)
          ? current
          : identity(value.instruments[0])
      ));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The instrument library could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selected = useMemo(
    () => library?.instruments.find((item) => identity(item) === selectedIdentity) ?? null,
    [library, selectedIdentity],
  );
  const selectedSession = selected ? sessions[identity(selected)] ?? null : null;

  const open = useCallback(async (item: InstrumentLibraryEntry) => {
    const key = identity(item);
    setOpening(key);
    setError(null);
    try {
      const session = await dispatchDesktopOperation<InstrumentSessionValue>(
        instrumentSessionStartRequest(item.prototype_id, item.revision),
      );
      setSessions((current) => ({ ...current, [key]: session }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The instrument could not be opened.");
    } finally {
      setOpening("");
    }
  }, []);

  const inspectSession = useCallback(async (session: InstrumentSessionValue) => {
    setChecking(true);
    setError(null);
    try {
      const inspected = await dispatchDesktopOperation<InstrumentSessionValue>(
        instrumentSessionInspectRequest(session.instrument_session_id),
      );
      setSessions((current) => ({
        ...current,
        [`${inspected.prototype_id}@${inspected.revision}`]: inspected,
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The instrument session could not be checked.");
    } finally {
      setChecking(false);
    }
  }, []);

  return (
    <section className={styles.library} aria-labelledby="instrument-library-title">
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>INSTRUMENT LAB</span>
          <h1 id="instrument-library-title">Instruments</h1>
          <p>Choose a Schuss instrument and open its verified native performance app.</p>
        </div>
        <div className={styles.libraryMeta}>
          <span>SCHUSS INSTRUMENTS</span>
          <strong>{library ? `${library.instrument_count} instruments` : "Local library"}</strong>
        </div>
      </header>

      {loading && (
        <div className={styles.loading} role="status" aria-live="polite">
          <span />
          <strong>Loading exact instrument library…</strong>
          <p>Checking retained build identity. No instrument is launched.</p>
        </div>
      )}

      {!loading && error && !library && (
        <div className={styles.loading} role="alert">
          <strong>Instrument library unavailable</strong>
          <p>{error}</p>
          <button type="button" onClick={() => void load()}>Retry</button>
        </div>
      )}

      {!loading && library && (
        <div className={styles.content}>
          <div className={styles.listPane}>
            <div className={styles.listHeading}>
              <span>LIBRARY</span>
              <span>{library.instrument_count.toString().padStart(2, "0")}</span>
            </div>
            <div className={styles.instrumentList} aria-label="Schuss instruments">
              {library.instruments.map((item, index) => {
                const key = identity(item);
                return (
                  <button
                    key={key}
                    type="button"
                    aria-pressed={selectedIdentity === key}
                    onClick={() => setSelectedIdentity(key)}
                  >
                    <span className={styles.index}>{String(index + 1).padStart(2, "0")}</span>
                    <span className={styles.rowText}>
                      <strong>{item.display_name}</strong>
                      <span>{identityLabel(item)} · {item.controller_label} · rev {item.revision}</span>
                    </span>
                    <span className={styles.availability} data-availability={item.availability}>
                      {AVAILABILITY_LABELS[item.availability]}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {selected && (
            <article className={styles.detail} aria-labelledby="selected-instrument-title">
              <div className={styles.detailTopline}>
                <span>{selected.lane.replaceAll("-", " ")}</span>
                <code>{selected.prototype_id}@{selected.revision}</code>
              </div>
              <h2 id="selected-instrument-title">{selected.display_name}</h2>
              <p className={styles.summary}>{selected.summary}</p>

              <dl className={styles.facts}>
                <div><dt>Controller</dt><dd>{selected.controller_label}</dd></div>
                <div><dt>Identity</dt><dd>{identityLabel(selected)}</dd></div>
                <div><dt>Local build</dt><dd data-availability={selected.availability}>{AVAILABILITY_LABELS[selected.availability]}</dd></div>
                <div><dt>Application</dt><dd>{selected.evidence.application_launch}</dd></div>
                <div><dt>Controller receipt</dt><dd>{selected.evidence.physical_controller}</dd></div>
                <div><dt>Listening</dt><dd>{selected.evidence.listening}</dd></div>
              </dl>

              <div className={styles.boundaryNote}>
                <strong>Audition boundary</strong>
                <p>{selected.canonical_identity?.status === "canonical"
                  ? "This musical identity is canonical. Opening still uses its exact Instrument Lab build; no canonical provider, device, controller, listening, or production evidence is implied."
                  : "Opening starts the exact verified standalone build. It does not establish device, controller, listening, or production evidence."}</p>
              </div>

              {selectedSession && (
                <div className={styles.session} role="status">
                  <span className={styles.sessionLight} data-status={selectedSession.status} />
                  <div>
                    <strong>{selectedSession.status === "running" ? "Instrument open" : "Instrument closed"}</strong>
                    <code>{selectedSession.instrument_session_id}{selectedSession.exit_code === undefined ? "" : ` · exit ${selectedSession.exit_code}`}</code>
                  </div>
                  <button type="button" disabled={checking} onClick={() => void inspectSession(selectedSession)}>
                    {checking ? "Checking…" : "Check status"}
                  </button>
                </div>
              )}

              {error && <p className={styles.error} role="alert">{error}</p>}

              <footer className={styles.actions}>
                <button
                  className={styles.openButton}
                  type="button"
                  disabled={!selected.launchable || opening === identity(selected) || selectedSession?.status === "running"}
                  onClick={() => void open(selected)}
                >
                  {opening === identity(selected)
                    ? "Opening…"
                    : selectedSession?.status === "running"
                    ? "Already open"
                    : `Open ${selected.display_name}`}
                </button>
                {!selected.launchable && (
                  <span>{selected.availability === "research-only" ? "No native audition target is defined." : "A fresh verified native build is required."}</span>
                )}
              </footer>
            </article>
          )}
        </div>
      )}
    </section>
  );
}
