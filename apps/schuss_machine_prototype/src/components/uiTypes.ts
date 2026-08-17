export type MachineSelection =
  | { blockId: string; kind: "block" }
  | { elementId: string; kind: "panel" }
  | null;
