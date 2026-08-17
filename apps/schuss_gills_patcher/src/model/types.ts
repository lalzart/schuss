export type MachineKey = "tide-pit" | "palimpsest";
export type PerformanceMode = "clean" | "filter" | "drive";
export type SignalKind = "control" | "event" | "audio" | "feedback";

export interface ControlMapping {
  controlId: string;
  physicalLabel: string;
  labels: Record<PerformanceMode, string>;
  detail?: string;
  kind: "control" | "event";
  mapped: boolean;
  targetId: string;
}

export interface MachineOutput {
  outputId: string;
  label: string;
  detail: string;
  kind: "audio" | "feedback";
  targetId: string;
}

export interface SourceOutlineStage {
  label: string;
  detail: string;
}

export interface MachineDefinition {
  key: MachineKey;
  displayName: string;
  subtitle: string;
  sourceObject: string;
  sourcePatch: string;
  sourceRevision: string;
  summary: string;
  performanceModes: readonly PerformanceMode[] | null;
  controls: readonly ControlMapping[];
  outputs: readonly MachineOutput[];
  sourceOutline: readonly SourceOutlineStage[];
}

export interface ExactReference {
  stableId: string;
  revision: number;
  contentHash: string;
}

export interface CatalogItem {
  displayName: string;
  description: string;
  primaryFunction: string;
  familyReference: ExactReference;
  contractReference: ExactReference | null;
  selectable: boolean;
  statusLabel: string;
  disabledReason?: string;
}

export const PERFORMANCE_MODES: readonly PerformanceMode[] = [
  "clean",
  "filter",
  "drive",
];

export const SIGNAL_COLORS: Record<SignalKind, string> = {
  control: "#41a9ff",
  event: "#b78cff",
  audio: "#ff9a4a",
  feedback: "#53d69b",
};

export function labelForMode(
  mapping: ControlMapping,
  mode: PerformanceMode,
): string {
  return mapping.labels[mode];
}
