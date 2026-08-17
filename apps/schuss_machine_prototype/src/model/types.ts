export type MachineKey = "tide-pit" | "palimpsest";
export type PerformanceMode = "CLEAN" | "FILT" | "DRIVE";
export type MappingState = "mapped" | "intentionally-unmapped";
export type SignalKind = "audio" | "control" | "display" | "event";

export interface ExactSourceFile {
  byte_sha256: string;
  portable_path: string;
  role: string;
  source_file_id: string;
}

export interface ExactSourceIdentity {
  commit: string;
  files: ExactSourceFile[];
  project_root: string;
  repository_url: string;
  source_id: string;
}

export interface MachineIdentity {
  display_name: string;
  source_identity: ExactSourceIdentity;
  source_review_reference: {
    content_hash: string;
    machine_source_review_id: string;
    revision: number;
  };
  summary: string;
}

export interface PresentationBlock {
  geometry: { height: number; width: number; x: number; y: number };
  graph_node_references: unknown[];
  kind: string;
  label: string;
  presentation_block_id: string;
  source_block_ids: string[];
}

export interface PresentationEdge {
  destination_block_id: string;
  presentation_edge_id: string;
  signal_kind: SignalKind;
  source_block_id: string;
  source_edge_ids: string[];
}

export interface SemanticRegion {
  anchor: { x: string; y: string };
  highlight_element_id: string;
  physical_label: string;
  semantic_slot_id: string;
  slot_kind: string;
  svg_element_id: string;
}

export interface SourceMeaning {
  meaning: string;
  mode: string;
}

export interface SourceMapping {
  evidence_span_ids: string[];
  mapping_id: string;
  mapping_state: MappingState;
  meanings: SourceMeaning[];
  semantic_slot_id: string;
}

export interface PresentationLink {
  modes: string[];
  presentation_block_id: string;
  semantic_slot_id: string;
  source_mapping_id: string;
}

export interface SourceEvidenceBlock {
  evidence_span_ids: string[];
  label: string;
  source_block_id: string;
  summary: string;
}

export interface DependencyEvidence {
  classification: string;
  dependency_id: string;
  evidence_level: number;
  evidence_status: string;
  first_proof_gap: string;
  label: string;
  reason: string;
  required: boolean;
}

export interface ProofBoundary {
  level: number;
  limitation: string;
  name: string;
  status: string;
}

export interface MachineInspectResult {
  operation: "machine.inspect";
  schema_version: string;
  status: "success";
  value: {
    affordances: Record<string, boolean>;
    dependencies: DependencyEvidence[];
    entry_kind: string;
    identity: MachineIdentity;
    inspection_state: "inspection-only" | "completed-machine";
    machine_block_diagram: {
      blocks: PresentationBlock[];
      edges: PresentationEdge[];
      presentation_state: string;
    };
    panel: {
      asset: {
        byte_sha256: string;
        portable_path: string;
      };
      presentation_links: PresentationLink[];
      semantic_regions: SemanticRegion[];
      source_mappings: SourceMapping[];
    };
    proof_boundary: ProofBoundary[];
    record_set_reference: {
      content_hash: string;
      record_set_id: string;
      revision: number;
    };
    resources: {
      measurement_state: string;
      source_declared_bytes: number | null;
    };
    source_evidence: {
      blocks: SourceEvidenceBlock[];
    };
  };
}

export interface MachinePresentationConfig {
  key: MachineKey;
  blockParts: Record<string, string[]>;
  oledLines: [string, string, string, string];
  panelLabels: Record<string, Partial<Record<PerformanceMode | "ALL", string>>>;
  rows: string[][];
}

export interface MachineBlockView extends PresentationBlock {
  parts: string[];
  summary: string;
}

export interface PhysicalRegionView {
  highlightElementIds: string[];
  physicalLabel: string;
  semanticSlotIds: string[];
  slotKind: string;
  svgElementId: string;
}

export interface ActiveMeaning {
  mappingState: MappingState;
  meaning: string;
  mode: string;
  semanticSlotId: string;
}

export interface MachineView {
  blocks: MachineBlockView[];
  blocksById: Map<string, MachineBlockView>;
  config: MachinePresentationConfig;
  dependencies: DependencyEvidence[];
  edges: PresentationEdge[];
  identity: MachineIdentity;
  inspectionState: "inspection-only" | "completed-machine";
  links: PresentationLink[];
  mappingsBySlot: Map<string, SourceMapping>;
  panelAsset: { byte_sha256: string; portable_path: string };
  proofBoundary: ProofBoundary[];
  raw: MachineInspectResult;
  recordSetReference: MachineInspectResult["value"]["record_set_reference"];
  regions: PhysicalRegionView[];
  regionsByElement: Map<string, PhysicalRegionView>;
  regionsBySlot: Map<string, PhysicalRegionView>;
  resources: MachineInspectResult["value"]["resources"];
  rows: string[][];
}
