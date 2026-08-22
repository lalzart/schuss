export const FILTER_NAMES = [
  "function",
  "abstraction",
  "form",
  "signal_domain",
  "signal_rate",
  "signal_role",
  "capability",
  "technique",
  "readiness",
  "provenance",
] as const;

export type CatalogFilterName = (typeof FILTER_NAMES)[number];
export type CatalogFilters = Record<CatalogFilterName, string[]>;

export type ExactFamilyReference = {
  family_id: string;
  revision: number;
  content_hash: string;
};

export type ExactRecordSetReference = {
  record_set_id: string;
  revision: number;
  content_hash: string;
};

export type CatalogSearchItem = {
  family_reference: ExactFamilyReference;
  display_name: string;
  aliases: string[];
  description: string;
  primary_function: string;
  technique_tags: string[];
  abstraction_level: string;
  implementation_forms: string[];
  readiness_states: string[];
  contract_facets_available: boolean;
  provenance_facets: string[];
  score: number;
  curation_treatment?: string;
  drawer_visibility?: string;
};

export type SignalFacet = {
  domain: string;
  rate: string;
  role: string;
  channel_count: number;
};

export type ExactReference = {
  stable_id: string;
  revision: number;
  content_hash: string;
};

export type CatalogImplementation = {
  implementation_id: string;
  exact_reference: ExactReference;
  display_name: string;
  form: string;
  provenance_sources: string[];
  observation_references: string[];
  contract_references: ExactReference[];
  binding_references: ExactReference[];
  eligibility_references: ExactReference[];
  target_references: ExactReference[];
  backend_references: ExactReference[];
  result_references: ExactReference[];
  artifact_references: ExactReference[];
  evidence_references: ExactReference[];
  readiness_states: string[];
  unresolved_facts: string[];
  provenance_tags?: string[];
};

export type CatalogFamilyInspection = {
  family_reference: ExactFamilyReference;
  display_name: string;
  aliases: string[];
  description: string;
  primary_function: string;
  technique_tags: string[];
  abstraction_level: string;
  implementation_forms: string[];
  signal_facets: SignalFacet[];
  contract_facet_names: string[];
  capability_keys: string[];
  provenance_facets: string[];
  readiness_states: string[];
  contract_facets_available: boolean;
  implementations: CatalogImplementation[];
  unresolved_facts: string[];
  curation_treatment?: string;
  drawer_visibility?: string;
};

export type CatalogSearchValue = {
  record_set_reference: ExactRecordSetReference;
  projection_version: string;
  match_algorithm: string;
  query: string;
  filters: CatalogFilters;
  results: CatalogSearchItem[];
  total_matches: number;
};

export type CatalogInspectValue = {
  record_set_reference: ExactRecordSetReference;
  projection_version: string;
  match_algorithm: string;
  family: CatalogFamilyInspection;
};

export type ApplicationCapability = {
  operation: string;
  availability: string;
  effect_class: string;
};

export type ApplicationDescription = {
  description_version: string;
  operations: ApplicationCapability[];
  record_set_reference: ExactRecordSetReference;
};

export type OperationDiagnostic = {
  code: string;
  severity: "error" | "warning" | "info";
  subject: string;
  location: string;
  message: string;
};

export type OperationResult<T, O extends string> = {
  schema_version: string;
  canonical_profile: "schuss-canonical-json-v1";
  operation: O;
  status: "success" | "invalid" | "unresolved" | "unsupported" | "ambiguous" | "conflict" | "unavailable" | "failed" | "cancelled" | "budget-failure";
  value: T | null;
  diagnostics: OperationDiagnostic[];
};

export type ApplicationDescribeRequest = {
  schema_version: "schuss-operation-request-v7";
  canonical_profile: "schuss-canonical-json-v1";
  operation: "application.describe";
  payload: { scope: "selected-context" };
};

export type CatalogSearchRequest = {
  schema_version: "schuss-operation-request-v2";
  canonical_profile: "schuss-canonical-json-v1";
  operation: "catalog.search";
  payload: { query: string; filters: CatalogFilters };
};

export type CatalogInspectRequest = {
  schema_version: "schuss-operation-request-v2";
  canonical_profile: "schuss-canonical-json-v1";
  operation: "catalog.inspect";
  payload: { family_reference: ExactFamilyReference };
};

export type ReadOnlyRequest =
  | ApplicationDescribeRequest
  | CatalogSearchRequest
  | CatalogInspectRequest;

export type GraphReference = {
  graph_id: string;
  revision: number;
  content_hash: string;
};

export type ProjectReference = {
  project_id: string;
  revision: number;
  content_hash: string;
};

export type BuildRequestReference = {
  build_request_id: string;
  revision: number;
  content_hash: string;
};

export type ComponentReference = {
  component_contract_id: string;
  revision: number;
  content_hash: string;
};

export type FacetValue = { facet_id: string; value: string };

export type GraphNodeRecord = {
  node_id: string;
  contract_reference: ComponentReference;
  parameter_values: FacetValue[];
  attribute_values: FacetValue[];
};

export type GraphConnectionRecord = {
  connection_id: string;
  source: { node_id: string; facet_id: string };
  destination: { node_id: string; facet_id: string };
};

export type DspGraph = {
  schema_version: string;
  canonical_profile: "schuss-canonical-json-v1";
  graph_id: string;
  revision: number;
  content_hash: string;
  display_name: string;
  nodes: GraphNodeRecord[];
  connections: GraphConnectionRecord[];
  public_parameters: Array<{
    facet_id: string;
    display_label: string;
    default: string;
  }>;
  [key: string]: unknown;
};

export type ComponentPort = {
  facet_id: string;
  semantic_key: string;
  display_label: string;
  direction: "inlet" | "outlet";
  port_type: { domain: string; rate: string; semantic_role: string };
};

export type ComponentParameter = {
  facet_id: string;
  semantic_key: string;
  display_label: string;
  default: string;
  unit?: string;
};

export type ComponentContract = {
  component_contract_id: string;
  revision: number;
  content_hash: string;
  display_name: string;
  ports: ComponentPort[];
  parameters: ComponentParameter[];
  attributes: Array<{
    facet_id: string;
    semantic_key: string;
    display_label: string;
    default: string;
  }>;
};

export type ProjectObjectReference = {
  object_definition_id: string;
  revision: number;
  content_hash: string;
};

export type ProjectObjectEvidence = {
  structural: string;
  host_evaluation: {
    status: string;
    artifact?: {
      content_hash: string;
      sample_rate: number;
      frame_count: number;
      channel_count: number;
      sample_format: string;
      byte_length: number;
      measurements: Record<string, string | number>;
    };
  };
  target_lowering: string;
  arm_build: string;
  connected_device: string;
  real_time_resources: string;
  audible_listening: string;
};

export type ProjectObjectSummary = {
  object_reference: ProjectObjectReference;
  display_name: string;
  function: string;
  form: "transparent-compound" | "native-kernel";
  evidence: ProjectObjectEvidence;
};

export type ProjectObjectsListValue = {
  project_reference: ProjectReference;
  object_count: number;
  objects: ProjectObjectSummary[];
};

export type ProjectObjectDefinition = {
  object_definition_id: string;
  revision: number;
  content_hash: string;
  family: {
    family_id: string;
    revision: number;
    content_hash: string;
    display_name: string;
    aliases: string[];
    function: string;
    desired_character: string[];
    provenance: "ai-authored" | "user-authored";
  };
  component_contract: ComponentContract;
  implementation_binding: Record<string, unknown>;
  realization: { form: "transparent-compound" | "native-kernel" } & Record<string, unknown>;
  intent: Record<string, unknown>;
  evidence: ProjectObjectEvidence;
};

export type ProjectObjectInspectValue = {
  project_reference: ProjectReference;
  object_definition: ProjectObjectDefinition;
};

export type GraphInspectValue = {
  graph: DspGraph;
  component_contract_closure: ComponentContract[];
};

export type ProjectManifest = {
  project_id: string;
  revision: number;
  content_hash: string;
  primary_graph_reference: GraphReference;
  instrument_references: ExactReference[];
  build_request_references: BuildRequestReference[];
};

export type WorkspaceProject = {
  workspace: string;
  project_reference: ProjectReference;
  graph_reference: GraphReference;
  display_name: string;
};

export type WorkspaceProjectsValue = {
  projects_root: string;
  project_count: number;
  rejected_child_count: number;
  truncated: boolean;
  projects: WorkspaceProject[];
};

export type WorkspaceProjectCreateValue = {
  projects_root: string;
  project: WorkspaceProject;
  creation: {
    project_id_allocated: string;
    template_profile_forked: boolean;
    display_name_revision: number;
    publication: string;
  };
};

export type BuildArtifact = {
  artifact_kind: string;
  media_type: string;
  producer_stage: string;
  byte_sha256: string;
  byte_length: number;
  portable_locator: string;
};

export type SessionDiagnostic = {
  code: string;
  severity: "error" | "warning" | "info";
  stage: string;
  subject: string;
  message: string;
};

export type BuildSessionValue = {
  session_id: string;
  status: string;
  phase: string;
  build_request_reference: BuildRequestReference;
  progress: Array<{ ordinal: number; event: string; subject: string }>;
  stage_outcomes: Array<{ stage: string; status: string }>;
  artifacts: BuildArtifact[];
  evidence_levels: Array<{ level: number; status: string }>;
  diagnostics: SessionDiagnostic[];
};

export type DeviceSessionValue = {
  session_id: string;
  status: string;
  transport: string;
  transport_location: string;
  usb_identity: { vendor_id: string; product_id: string; usb_serial: string | null };
  board_identity: {
    product: string | null;
    cpu_serial: string | null;
    firmware: { version: string; crc: string; patch_entrypoint: string } | null;
  };
  identity_status: string;
  compatibility: string;
  diagnostics: SessionDiagnostic[];
};

export type DeviceDiscoveryValue = {
  status: string;
  sessions: DeviceSessionValue[];
  device_count: number;
  discovery_was_explicit: boolean;
  background_monitoring: boolean;
};

export type UploadSessionValue = {
  session_id: string;
  status: string;
  phase: string;
  device_session_id: string;
  build_session_id: string;
  artifact: BuildArtifact;
  device_binary: { byte_sha256: string; byte_length: number; load_address: string };
  start_patch_requested: boolean;
  progress: Array<{
    ordinal: number;
    event: string;
    completed_bytes: number;
    total_bytes: number;
  }>;
  verification: string;
  outcome: Record<string, unknown> | null;
  diagnostics: SessionDiagnostic[];
};

export type ProjectInspectValue = {
  project: ProjectManifest;
  validation: Record<string, unknown>;
};

export type ProjectHistoryValue = {
  head_project_reference: ProjectReference;
  revision_count: number;
  ancestry: Array<{
    project_reference: ProjectReference;
    primary_graph_reference: GraphReference;
    owned_member_count: number;
  }>;
};

export type ImplementationSearchItem = {
  implementation_id: string;
  exact_reference: ExactReference | null;
  display_name: string;
  form: string;
  family_reference: ExactFamilyReference;
  family_display_name: string;
  primary_function: string;
  abstraction_level: string;
  provenance_sources: string[];
  provenance_tags: string[];
  readiness_states: string[];
  score: number;
};

export type ImplementationSearchValue = {
  record_set_reference: ExactRecordSetReference;
  results: ImplementationSearchItem[];
  total_matches: number;
};

export type GraphEdit =
  | { edit: "add-node"; node: GraphNodeRecord }
  | { edit: "remove-node"; node_id: string }
  | { edit: "add-connection"; connection: GraphConnectionRecord }
  | { edit: "remove-connection"; connection_id: string }
  | {
      edit: "set-node-parameter";
      node_id: string;
      facet_id: string;
      value: string;
    }
  | {
      edit: "set-node-attribute";
      node_id: string;
      facet_id: string;
      value: string;
    }
  | { edit: "set-graph-display-name"; display_name: string };

export type DesktopOperationRequest = {
  schema_version: string;
  canonical_profile: "schuss-canonical-json-v1";
  operation: string;
  payload: Record<string, unknown>;
};

export type InstrumentAvailability =
  | "verified-local-build"
  | "build-required"
  | "stale-build"
  | "research-only";

export type InstrumentEvidenceBoundary = {
  application_launch: "not-evaluated";
  listening: "not-evaluated";
  physical_controller: "not-evaluated";
};

export type InstrumentLibraryEntry = {
  prototype_id: string;
  revision: string;
  display_name: string;
  summary: string;
  controller_label: string;
  lane: string;
  availability: InstrumentAvailability;
  launchable: boolean;
  evidence: InstrumentEvidenceBoundary;
  executable_sha256?: string;
};

export type InstrumentLibraryValue = {
  library_id: "instrument-lab-audition-library";
  library_revision: 1;
  claims: {
    canonical_schuss_records: false;
    production_ready: false;
  };
  instrument_count: number;
  instruments: InstrumentLibraryEntry[];
};

export type InstrumentSessionValue = {
  instrument_session_id: string;
  prototype_id: string;
  revision: string;
  display_name: string;
  status: "running" | "exited";
  executable_sha256: string;
  exit_code?: number;
};
