import {
  FILTER_NAMES,
  type ApplicationDescribeRequest,
  type CatalogFilters,
  type CatalogInspectRequest,
  type CatalogSearchRequest,
  type ExactFamilyReference,
} from "./types";

export function emptyCatalogFilters(): CatalogFilters {
  return Object.fromEntries(FILTER_NAMES.map((name) => [name, []])) as unknown as CatalogFilters;
}

export function applicationDescribeRequest(): ApplicationDescribeRequest {
  return {
    schema_version: "schuss-operation-request-v7",
    canonical_profile: "schuss-canonical-json-v1",
    operation: "application.describe",
    payload: { scope: "selected-context" },
  };
}

export function catalogSearchRequest(
  query: string,
  partialFilters: Partial<CatalogFilters> = {},
): CatalogSearchRequest {
  const filters = emptyCatalogFilters();
  for (const name of FILTER_NAMES) {
    filters[name] = [...new Set(partialFilters[name] ?? [])].sort();
  }
  return {
    schema_version: "schuss-operation-request-v2",
    canonical_profile: "schuss-canonical-json-v1",
    operation: "catalog.search",
    payload: { query, filters },
  };
}

export function catalogInspectRequest(
  familyReference: ExactFamilyReference,
): CatalogInspectRequest {
  return {
    schema_version: "schuss-operation-request-v2",
    canonical_profile: "schuss-canonical-json-v1",
    operation: "catalog.inspect",
    payload: { family_reference: familyReference },
  };
}
