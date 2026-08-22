import { describe, expect, it } from "vitest";
import {
  instrumentLibraryListRequest,
  instrumentSessionInspectRequest,
  instrumentSessionStartRequest,
} from "./instrumentRequests";

describe("instrument library requests", () => {
  it("lists through the exact v19 read operation", () => {
    expect(instrumentLibraryListRequest()).toEqual({
      schema_version: "schuss-operation-request-v19",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "instrument.library.list",
      payload: {},
    });
  });

  it("starts only with the explicit native audition intent", () => {
    expect(instrumentSessionStartRequest("wirefall-r02", "0.2")).toEqual({
      schema_version: "schuss-operation-request-v19",
      canonical_profile: "schuss-canonical-json-v1",
      operation: "instrument.session.start",
      payload: {
        prototype_id: "wirefall-r02",
        revision: "0.2",
        launch_intent: "explicit-native-juce-audition",
      },
    });
  });

  it("inspects one exact process-local session", () => {
    expect(instrumentSessionInspectRequest("instrument-session-000123")).toMatchObject({
      operation: "instrument.session.inspect",
      payload: { instrument_session_id: "instrument-session-000123" },
    });
  });
});
