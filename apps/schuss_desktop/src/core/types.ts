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
  status: "success" | "invalid" | "unresolved" | "unsupported" | "ambiguous" | "conflict";
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
