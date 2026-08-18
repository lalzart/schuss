import { describe, expect, it } from "vitest";
import {
  DESKTOP_RECORD_SET,
  STARTER_GRAPH,
  buildSessionStartRequest,
  deviceUploadStartRequest,
  graphTransactRequest,
  profileTransactRequest,
  projectInitRequest,
  projectObjectInspectRequest,
  projectObjectsListRequest,
  workspaceProjectCreateRequest,
  workspaceProjectsListRequest,
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
          portable_locator: "contracts/record-sets/ui-desktop-workspace-shell-v1.json",
        },
        primary_graph_reference: STARTER_GRAPH,
      },
    });
  });

  it("uses v14 for core-owned workspace browsing and creation", () => {
    expect(workspaceProjectsListRequest()).toEqual({
      schema_version: "schuss-operation-request-v14",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "workspace.projects.list",
      payload: {},
    });
    expect(workspaceProjectCreateRequest("New patch")).toEqual({
      schema_version: "schuss-operation-request-v14",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "workspace.project.create",
      payload: { display_name: "New patch" },
    });
  });

  it("uses explicit v12 session and volatile upload intents", () => {
    const build = buildSessionStartRequest({
      build_request_id: "schuss-build-request-000005",
      revision: 1,
      content_hash: `sha256:${"a".repeat(64)}`,
    });
    expect(build).toMatchObject({
      schema_version: "schuss-operation-request-v12",
      operation: "build.session.start",
      payload: { execution_intent: true },
    });
    expect(deviceUploadStartRequest("device-session-000001", "build-session-000001", "b".repeat(64), true)).toEqual({
      schema_version: "schuss-operation-request-v12",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "device.upload.start",
      payload: {
        device_session_id: "device-session-000001",
        build_session_id: "build-session-000001",
        artifact_sha256: "b".repeat(64),
        upload_intent: "explicit-volatile-ram",
        start_patch: true,
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

  it("uses only the exact v13 read operations for project-local objects", () => {
    const reference = {
      object_definition_id: "schuss-project-object-000123",
      revision: 1,
      content_hash: `sha256:${"f".repeat(64)}`,
    };
    expect(projectObjectsListRequest()).toEqual({
      schema_version: "schuss-operation-request-v13",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "project.objects.list",
      payload: {},
    });
    expect(projectObjectInspectRequest(reference)).toEqual({
      schema_version: "schuss-operation-request-v13",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "project.object.inspect",
      payload: { object_reference: reference },
    });
  });
});
