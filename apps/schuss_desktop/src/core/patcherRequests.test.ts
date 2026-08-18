import { describe, expect, it } from "vitest";
import {
  DESKTOP_RECORD_SET,
  STARTER_GRAPH,
  graphTransactRequest,
  profileTransactRequest,
  projectInitRequest,
} from "./patcherRequests";

describe("desktop patcher operation requests", () => {
  it("initializes from the exact accepted starter closure", () => {
    const operation = projectInitRequest("schuss-project-000123");
    expect(operation).toMatchObject({
      schema_version: "schuss-operation-request-v3",
      operation: "project.init",
      payload: {
        project_id: "schuss-project-000123",
        base_record_set: {
          reference: DESKTOP_RECORD_SET,
          portable_locator: "contracts/record-sets/ui-desktop-patcher-authoring-v1.json",
        },
        primary_graph_reference: STARTER_GRAPH,
      },
    });
  });

  it("uses v11 for graph proposals and durable profile edits", () => {
    const edits = [{ edit: "set-graph-display-name" as const, display_name: "A patch" }];
    expect(graphTransactRequest(STARTER_GRAPH, edits)).toEqual({
      schema_version: "schuss-operation-request-v11",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "graph.transact",
      payload: {
        graph_reference: STARTER_GRAPH,
        base_content_hash: STARTER_GRAPH.content_hash,
        edits,
      },
    });
    const project = { project_id: "schuss-project-000123", revision: 2, content_hash: `sha256:${"a".repeat(64)}` };
    expect(profileTransactRequest(project, STARTER_GRAPH, edits).payload).toMatchObject({
      expected_project_reference: project,
      graph_reference: STARTER_GRAPH,
      write_intent: "explicit",
    });
  });
});
