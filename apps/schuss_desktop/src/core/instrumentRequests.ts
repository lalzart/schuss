import type { DesktopOperationRequest } from "./types";

function request(
  operation: string,
  payload: Record<string, unknown>,
): DesktopOperationRequest {
  return {
    schema_version: "schuss-operation-request-v19",
    canonical_profile: "schuss-canonical-json-v1",
    operation,
    payload,
  };
}

export function instrumentLibraryListRequest(): DesktopOperationRequest {
  return request("instrument.library.list", {});
}

export function instrumentSessionStartRequest(
  prototypeId: string,
  revision: string,
): DesktopOperationRequest {
  return request("instrument.session.start", {
    prototype_id: prototypeId,
    revision,
    launch_intent: "explicit-native-juce-audition",
  });
}

export function instrumentSessionInspectRequest(
  instrumentSessionId: string,
): DesktopOperationRequest {
  return request("instrument.session.inspect", {
    instrument_session_id: instrumentSessionId,
  });
}
