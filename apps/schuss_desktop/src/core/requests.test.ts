import { describe, expect, it } from "vitest";
import {
  applicationDescribeRequest,
  catalogInspectRequest,
  catalogSearchRequest,
  emptyCatalogFilters,
} from "./requests";

describe("read-only operation requests", () => {
  it("builds the exact shared application description request", () => {
    expect(applicationDescribeRequest()).toEqual({
      schema_version: "schuss-operation-request-v7",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "application.describe",
      payload: { scope: "selected-context" },
    });
  });

  it("normalizes every catalog search filter without adding private fields", () => {
    const request = catalogSearchRequest("bell", {
      provenance: ["mutable-instruments-derived", "mutable-instruments-derived"],
      function: ["sound-sources"],
    });
    expect(request.payload.filters).toEqual({
      ...emptyCatalogFilters(),
      function: ["sound-sources"],
      provenance: ["mutable-instruments-derived"],
    });
    expect(Object.keys(request).sort()).toEqual([
      "canonical_profile",
      "operation",
      "payload",
      "schema_version",
    ]);
  });

  it("retains the exact family reference for catalog inspection", () => {
    const reference = {
      family_id: "schuss-family-000038",
      revision: 1,
      content_hash: `sha256:${"a".repeat(64)}`,
    };
    expect(catalogInspectRequest(reference).payload.family_reference).toBe(reference);
  });
});
