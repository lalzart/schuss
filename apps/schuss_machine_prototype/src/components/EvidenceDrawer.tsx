import { useEffect, useRef } from "react";

import type { MachineView } from "../model/types";

interface EvidenceDrawerProps {
  onClose: () => void;
  open: boolean;
  view: MachineView;
}

function readableClassification(value: string): string {
  return value.replaceAll("-", " ");
}

export function EvidenceDrawer({ onClose, open, view }: EvidenceDrawerProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    closeButtonRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = [...(drawerRef.current?.querySelectorAll<HTMLElement>("button, [href], [tabindex]:not([tabindex='-1'])") ?? [])]
        .filter((element) => !element.hasAttribute("disabled"));
      const first = focusable[0];
      const last = focusable.at(-1);
      if (!first || !last) return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      previousFocus?.focus();
    };
  }, [onClose, open]);

  if (!open) return null;
  const source = view.identity.source_identity;
  return (
    <div className="drawer-layer" role="presentation">
      <button aria-label="Close evidence drawer" className="drawer-scrim" onClick={onClose} tabIndex={-1} type="button" />
      <aside aria-label="Dependency and support evidence" aria-modal="true" className="evidence-drawer" ref={drawerRef} role="dialog">
        <header>
          <div>
            <span className="eyebrow">WHY SHOULD I TRUST THIS?</span>
            <h2>Evidence boundary</h2>
          </div>
          <button aria-label="Close evidence drawer" className="icon-button" onClick={onClose} ref={closeButtonRef} type="button">×</button>
        </header>
        <section className="evidence-identity">
          <span className="state-pill state-pill--warning">{view.inspectionState}</span>
          <p>{source.repository_url}</p>
          <code>{source.commit}</code>
          <code>{source.project_root}</code>
          <small>{view.recordSetReference.record_set_id}@{view.recordSetReference.revision}</small>
        </section>
        <section>
          <h3>Proof, kept separate</h3>
          <div className="proof-grid">
            {view.proofBoundary.map((proof) => (
              <article className={proof.status === "passed" ? "is-passed" : "is-not-run"} key={`${proof.level}-${proof.name}`}>
                <strong>L{proof.level}</strong>
                <span>{proof.name}</span>
                <small>{proof.status}</small>
              </article>
            ))}
          </div>
        </section>
        <section>
          <h3>Dependency/support inventory</h3>
          <div className="dependency-list">
            {view.dependencies.map((dependency) => (
              <article key={dependency.dependency_id}>
                <header>
                  <strong>{dependency.label}</strong>
                  <span>{readableClassification(dependency.classification)}</span>
                </header>
                <p>{dependency.reason}</p>
                <small><b>First proof gap:</b> {dependency.first_proof_gap}</small>
              </article>
            ))}
          </div>
        </section>
        <p className="drawer-limit">
          This web prototype proves presentation behavior only. It does not prove a Schuss graph, compiler lowering, ARM output, device timing, OLED behavior, resources, or audible output.
        </p>
      </aside>
    </div>
  );
}
