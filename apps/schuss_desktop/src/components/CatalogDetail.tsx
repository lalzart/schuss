import * as ScrollArea from "@radix-ui/react-scroll-area";
import * as Tabs from "@radix-ui/react-tabs";
import type { CatalogFamilyInspection, CatalogInspectValue, ExactReference } from "../core/types";
import { StatusBadge } from "./StatusBadge";
import { routeTone } from "./CatalogList";
import styles from "./CatalogBrowser.module.css";

function compactReference(reference: ExactReference): string {
  return `${reference.stable_id}@${reference.revision}`;
}

function ReferenceList({ title, references }: { title: string; references: ExactReference[] }) {
  if (references.length === 0) return null;
  return (
    <div className={styles.referenceGroup}>
      <dt>{title}</dt>
      <dd>
        {references.map((reference) => (
          <code key={`${reference.stable_id}@${reference.revision}:${reference.content_hash}`}>
            {compactReference(reference)}
          </code>
        ))}
      </dd>
    </div>
  );
}

function Overview({ family }: { family: CatalogFamilyInspection }) {
  return (
    <div className={styles.detailTabBody}>
      <section className={styles.detailSection} aria-labelledby="signal-interface-title">
        <div className={styles.sectionHeading}>
          <h3 id="signal-interface-title">Signal interface</h3>
          <span>{family.signal_facets.length}</span>
        </div>
        {family.signal_facets.length > 0 ? (
          <div className={styles.signalTable} role="table" aria-label="Canonical signal facets">
            <div className={styles.signalHeader} role="row">
              <span role="columnheader">Domain</span>
              <span role="columnheader">Rate</span>
              <span role="columnheader">Role</span>
              <span role="columnheader">Ch</span>
            </div>
            {family.signal_facets.map((facet, index) => (
              <div
                className={styles.signalRow}
                role="row"
                key={`${facet.domain}-${facet.rate}-${facet.role}-${facet.channel_count}-${index}`}
              >
                <span role="cell">{facet.domain}</span>
                <span role="cell">{facet.rate}</span>
                <span role="cell">{facet.role}</span>
                <span role="cell">{facet.channel_count}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className={styles.notAvailable}>No exact signal facets are exposed for this family.</p>
        )}
      </section>

      <section className={styles.detailSection} aria-labelledby="interface-facets-title">
        <div className={styles.sectionHeading}>
          <h3 id="interface-facets-title">Named interface facets</h3>
          <span>{family.contract_facet_names.length}</span>
        </div>
        <p className={styles.sectionNote}>
          Port, parameter, attribute, action, and display names are kept collective because the
          catalog result does not infer their kind.
        </p>
        {family.contract_facet_names.length > 0 ? (
          <div className={styles.facetGrid}>
            {family.contract_facet_names.map((name) => (
              <code key={name}>{name}</code>
            ))}
          </div>
        ) : (
          <p className={styles.notAvailable}>No exact named contract facets are available.</p>
        )}
      </section>

      <section className={styles.detailSection} aria-labelledby="capabilities-title">
        <div className={styles.sectionHeading}>
          <h3 id="capabilities-title">Capabilities</h3>
          <span>{family.capability_keys.length}</span>
        </div>
        <div className={styles.inlineTokens}>
          {family.capability_keys.map((capability) => (
            <code key={capability}>{capability}</code>
          ))}
          {family.capability_keys.length === 0 ? (
            <span className={styles.notAvailable}>None exposed</span>
          ) : null}
        </div>
      </section>

      {family.unresolved_facts.length > 0 ? (
        <section className={styles.detailSection} aria-labelledby="open-facts-title">
          <div className={styles.sectionHeading}>
            <h3 id="open-facts-title">Open facts</h3>
            <span>{family.unresolved_facts.length}</span>
          </div>
          <ul className={styles.factList}>
            {family.unresolved_facts.map((fact) => (
              <li key={fact}>{fact}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function SourcesAndEvidence({ family }: { family: CatalogFamilyInspection }) {
  return (
    <div className={styles.detailTabBody}>
      {family.implementations.map((implementation) => (
        <section className={styles.implementation} key={implementation.implementation_id}>
          <header>
            <div>
              <h3>{implementation.display_name}</h3>
              <code>{implementation.implementation_id}</code>
            </div>
            <span className={styles.formLabel}>{implementation.form}</span>
          </header>
          <div className={styles.inlineTokens}>
            {implementation.provenance_sources.map((source) => (
              <span key={source}>{source}</span>
            ))}
            {(implementation.provenance_tags ?? []).map((tag) => (
              <span className={styles.mutableTag} key={tag}>
                {tag}
              </span>
            ))}
          </div>
          <div className={styles.rowStatuses}>
            {implementation.readiness_states.map((status) => (
              <StatusBadge key={status} status={status} />
            ))}
          </div>
          <dl className={styles.referenceList}>
            <ReferenceList title="Contracts" references={implementation.contract_references} />
            <ReferenceList title="Bindings" references={implementation.binding_references} />
            <ReferenceList title="Eligibility" references={implementation.eligibility_references} />
            <ReferenceList title="Evidence" references={implementation.evidence_references} />
          </dl>
          <div className={styles.sourceObservations}>
            <span>Source observations</span>
            {implementation.observation_references.length > 0 ? (
              implementation.observation_references.map((reference) => (
                <code key={reference}>{reference}</code>
              ))
            ) : (
              <em>None exposed</em>
            )}
          </div>
          {implementation.evidence_references.length === 0 ? (
            <p className={styles.evidenceBoundary}>No exact evidence reference is attached.</p>
          ) : null}
        </section>
      ))}
      {family.implementations.length === 0 ? (
        <p className={styles.notAvailable}>No catalog implementation is exposed.</p>
      ) : null}
    </div>
  );
}

type CatalogDetailProps = {
  inspection: CatalogInspectValue | null;
  loading: boolean;
  error: string | null;
};

export function CatalogDetail({ inspection, loading, error }: CatalogDetailProps) {
  if (loading) {
    return (
      <div className={styles.detailLoading} role="status">
        <span className={styles.pulseLine} />
        <span className={styles.pulseLineShort} />
        <p>Inspecting exact family reference…</p>
      </div>
    );
  }
  if (error !== null) {
    return (
      <div className={styles.detailMessage} role="alert">
        <span>INSPECTION ERROR</span>
        <p>{error}</p>
      </div>
    );
  }
  if (inspection === null) {
    return (
      <div className={styles.detailMessage}>
        <span>NO SELECTION</span>
        <p>Select an exact catalog family to inspect its canonical details.</p>
      </div>
    );
  }

  const family = inspection.family;
  const familyLocator = `${family.family_reference.family_id}@${family.family_reference.revision}`;
  return (
    <article className={styles.detail} data-tone={routeTone(family.primary_function)}>
      <header className={styles.detailHeader}>
        <span className={styles.detailRoute} aria-hidden="true" />
        <div className={styles.detailHeading}>
          <div className={styles.detailKicker}>
            <span>{family.primary_function}</span>
            <code>{familyLocator}</code>
          </div>
          <h2>{family.display_name}</h2>
          <p>{family.description}</p>
          <div className={styles.detailTags}>
            <span>{family.abstraction_level}</span>
            {family.provenance_facets.map((facet) => (
              <span
                key={facet}
                className={
                  facet === "mutable-instruments-derived" ? styles.mutableTag : undefined
                }
              >
                {facet}
              </span>
            ))}
          </div>
          <div className={styles.detailStatuses}>
            {family.readiness_states.map((status) => (
              <StatusBadge key={status} status={status} />
            ))}
          </div>
        </div>
      </header>

      <Tabs.Root className={styles.detailTabs} defaultValue="interface">
        <Tabs.List className={styles.detailTabList} aria-label="Catalog inspection details">
          <Tabs.Trigger className={styles.detailTab} value="interface">
            Interface
          </Tabs.Trigger>
          <Tabs.Trigger className={styles.detailTab} value="sources">
            Sources &amp; evidence
          </Tabs.Trigger>
        </Tabs.List>
        <ScrollArea.Root className={styles.detailScroll}>
          <ScrollArea.Viewport className={styles.scrollViewport}>
            <Tabs.Content className={styles.detailTabContent} value="interface">
              <Overview family={family} />
            </Tabs.Content>
            <Tabs.Content className={styles.detailTabContent} value="sources">
              <SourcesAndEvidence family={family} />
            </Tabs.Content>
          </ScrollArea.Viewport>
          <ScrollArea.Scrollbar className={styles.scrollbar} orientation="vertical">
            <ScrollArea.Thumb className={styles.scrollThumb} />
          </ScrollArea.Scrollbar>
        </ScrollArea.Root>
      </Tabs.Root>
      <footer className={styles.detailFooter}>
        <span>{inspection.projection_version}</span>
        <span>{inspection.record_set_reference.record_set_id}@{inspection.record_set_reference.revision}</span>
      </footer>
    </article>
  );
}
