import { emptyCatalogFilters } from "./requests";
import type {
  ComponentReference,
  BuildRequestReference,
  DesktopOperationRequest,
  ExactRecordSetReference,
  GraphEdit,
  GraphReference,
  ProjectObjectReference,
  ProjectReference,
} from "./types";

export const DESKTOP_RECORD_SET: ExactRecordSetReference = {
  record_set_id: "schuss-record-set-000028",
  revision: 1,
  content_hash: "sha256:90bd454c4bf3c66f216496d461acf54d05b816927da8056907bf6fde51032bf9",
};

export const STARTER_GRAPH: GraphReference = {
  graph_id: "schuss-graph-000006",
  revision: 1,
  content_hash: "sha256:1c3e3e66245cf497b507d60d21d3a8ebd8cdc5117f02eab8b793853a4bef5aa2",
};

export const STARTER_INSTRUMENT = {
  instrument_id: "schuss-instrument-000005",
  revision: 1,
  content_hash: "sha256:e4d8d801dba7f8c557295444d3de22ad212601b88d3bd4bf7dfa7f4025aa2679",
};

export const STARTER_BUILD_REQUEST = {
  build_request_id: "schuss-build-request-000005",
  revision: 1,
  content_hash: "sha256:8f40ac2f996f32f10f59b862da566f1d66f145cdf1780f29d786c9b2f42f03c2",
};

function request(
  schema_version: string,
  operation: string,
  payload: Record<string, unknown>,
): DesktopOperationRequest {
  return {
    schema_version,
    canonical_profile: "schuss-canonical-json-v1",
    operation,
    payload,
  };
}

export function workspaceProjectsListRequest(): DesktopOperationRequest {
  return request("schuss-operation-request-v15", "workspace.projects.list", {});
}

export function workspaceProjectCreateRequest(displayName: string): DesktopOperationRequest {
  return request("schuss-operation-request-v15", "workspace.project.create", {
    display_name: displayName,
  });
}

export function implementationSearchRequest(query: string): DesktopOperationRequest {
  return request("schuss-operation-request-v10", "catalog.implementations.search", {
    query,
    filters: emptyCatalogFilters(),
  });
}

export function componentInspectRequest(reference: ComponentReference): DesktopOperationRequest {
  return request("schuss-operation-request-v11", "component.inspect", {
    component_contract_reference: reference,
  });
}

export function graphInspectRequest(reference: GraphReference): DesktopOperationRequest {
  return request("schuss-operation-request-v1", "graph.inspect", {
    graph_reference: reference,
  });
}

export function projectInspectRequest(): DesktopOperationRequest {
  return request("schuss-operation-request-v3", "project.inspect", {
    scope: "accepted-project",
  });
}

export function projectObjectsListRequest(): DesktopOperationRequest {
  return request("schuss-operation-request-v13", "project.objects.list", {});
}

export function projectObjectInspectRequest(reference: ProjectObjectReference): DesktopOperationRequest {
  return request("schuss-operation-request-v13", "project.object.inspect", {
    object_reference: reference,
  });
}

export function projectHistoryRequest(): DesktopOperationRequest {
  return request("schuss-operation-request-v8", "project.history.inspect", {
    scope: "immutable-ancestry",
  });
}

export function projectRevertRequest(
  expected: ProjectReference,
  target: ProjectReference,
): DesktopOperationRequest {
  return request("schuss-operation-request-v8", "project.revert", {
    expected_project_reference: expected,
    target_project_reference: target,
    write_intent: "explicit",
  });
}

export function projectInitRequest(projectId: string): DesktopOperationRequest {
  return request("schuss-operation-request-v3", "project.init", {
    project_id: projectId,
    base_record_set: {
      reference: DESKTOP_RECORD_SET,
      portable_locator: "contracts/record-sets/ui-desktop-workspace-shell-v1.json",
    },
    primary_graph_reference: STARTER_GRAPH,
    instrument_references: [STARTER_INSTRUMENT],
    build_request_references: [STARTER_BUILD_REQUEST],
    asset_references: [],
  });
}

export function buildSessionStartRequest(reference: BuildRequestReference): DesktopOperationRequest {
  return request("schuss-operation-request-v12", "build.session.start", {
    build_request_reference: reference,
    execution_intent: true,
  });
}

export function buildSessionInspectRequest(sessionId: string): DesktopOperationRequest {
  return request("schuss-operation-request-v12", "build.session.inspect", {
    build_session_id: sessionId,
  });
}

export function deviceDiscoverRequest(reference: BuildRequestReference): DesktopOperationRequest {
  return request("schuss-operation-request-v12", "device.session.discover", {
    build_request_reference: reference,
    discovery_intent: true,
  });
}

export function deviceSessionInspectRequest(sessionId: string): DesktopOperationRequest {
  return request("schuss-operation-request-v12", "device.session.inspect", {
    device_session_id: sessionId,
  });
}

export function deviceUploadStartRequest(
  deviceSessionId: string,
  buildSessionId: string,
  artifactSha256: string,
  startPatch: boolean,
): DesktopOperationRequest {
  return request("schuss-operation-request-v12", "device.upload.start", {
    device_session_id: deviceSessionId,
    build_session_id: buildSessionId,
    artifact_sha256: artifactSha256,
    upload_intent: "explicit-volatile-ram",
    start_patch: startPatch,
  });
}

export function deviceUploadInspectRequest(sessionId: string): DesktopOperationRequest {
  return request("schuss-operation-request-v12", "device.upload.inspect", {
    upload_session_id: sessionId,
  });
}

export function projectForkRequest(project: ProjectReference): DesktopOperationRequest {
  return request("schuss-operation-request-v8", "project.profile.fork", {
    expected_project_reference: project,
    template_graph_reference: STARTER_GRAPH,
    template_instrument_reference: STARTER_INSTRUMENT,
    template_build_request_reference: STARTER_BUILD_REQUEST,
    write_intent: "explicit",
  });
}

export function graphTransactRequest(
  graph: GraphReference,
  edits: GraphEdit[],
): DesktopOperationRequest {
  return request("schuss-operation-request-v11", "graph.transact", {
    graph_reference: graph,
    base_content_hash: graph.content_hash,
    edits,
  });
}

export function profileTransactRequest(
  project: ProjectReference,
  graph: GraphReference,
  edits: GraphEdit[],
): DesktopOperationRequest {
  return request("schuss-operation-request-v11", "project.profile.transact", {
    expected_project_reference: project,
    graph_reference: graph,
    base_content_hash: graph.content_hash,
    edits,
    write_intent: "explicit",
  });
}
