import * as Tooltip from "@radix-ui/react-tooltip";
import styles from "./CatalogBrowser.module.css";

const STATUS_EXPLANATIONS: Record<string, string> = {
  "catalogued-only": "Catalog membership exists; no matching exact contract is reached.",
  contracted: "An exact component contract is available.",
  bound: "At least one exact implementation binding is available.",
  eligible: "An exact target/backend eligibility record is supported.",
  "compile-proven": "Exact level-5 compile/link evidence is attached.",
  "device-tested": "Exact level-6 connected-device evidence is attached.",
  "real-time-tested": "Exact level-7 real-time/resource evidence is attached.",
  "audible-tested": "Exact level-8 listening evidence is attached.",
  unresolved: "The exact source records retain unresolved or not-evaluated facts.",
};

function statusTone(status: string): string {
  if (["audible-tested", "real-time-tested", "device-tested"].includes(status)) return "green";
  if (["compile-proven", "eligible"].includes(status)) return "cyan";
  if (["bound", "contracted"].includes(status)) return "blue";
  if (status === "unresolved") return "orange";
  return "neutral";
}

export function StatusBadge({ status }: { status: string }) {
  const explanation = STATUS_EXPLANATIONS[status] ?? "Exact catalog readiness state.";
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <span className={styles.statusBadge} data-tone={statusTone(status)} tabIndex={0}>
          {status}
        </span>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content className={styles.tooltip} sideOffset={6}>
          {explanation}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
