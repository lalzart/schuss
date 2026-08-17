import { describe, expect, it } from "vitest";

import {
  LOCAL_PATCH_LIBRARY_SCHEMA,
  decodePatchLibrary,
  deleteLocalPatch,
  emptyPatchLibrary,
  encodePatchLibrary,
  searchSavedPatches,
  upsertLocalPatch,
  type PatchSnapshot,
} from "./patchLibrary";

const snapshot: PatchSnapshot = {
  catalogNodes: [
    {
      familyId: "schuss-family-000031",
      localIndex: 1,
      position: { x: 448, y: 882 },
    },
  ],
  machineKey: "tide-pit",
  mode: "filter",
  referencePositions: {
    "gills-input-rack": { x: 0, y: 40 },
    "gills-output-rack": { x: 1080, y: 110 },
    "instrument-compound": { x: 430, y: 20 },
  },
};

describe("browser-local patch library", () => {
  it("creates and updates one stable local identity independently of its name", () => {
    const created = upsertLocalPatch(
      emptyPatchLibrary(),
      snapshot,
      "  Tide   study  ",
      null,
      () => "local-patch-12345678",
    );
    expect(created.patch).toMatchObject({
      mode: "filter",
      name: "Tide study",
      patchId: "local-patch-12345678",
    });

    const updated = upsertLocalPatch(
      created.library,
      { ...snapshot, mode: "drive" },
      "Renamed study",
      created.patch.patchId,
      () => "local-patch-never-used",
    );
    expect(updated.library.patches).toHaveLength(1);
    expect(updated.patch).toMatchObject({
      mode: "drive",
      name: "Renamed study",
      patchId: "local-patch-12345678",
    });
  });

  it("round-trips deterministic, timestamp-free storage", () => {
    const first = upsertLocalPatch(
      emptyPatchLibrary(),
      snapshot,
      "Zed",
      null,
      () => "local-patch-zzzzzzzz",
    );
    const second = upsertLocalPatch(
      first.library,
      { ...snapshot, machineKey: "palimpsest", mode: "clean" },
      "Alpha",
      null,
      () => "local-patch-aaaaaaaa",
    );
    const encoded = encodePatchLibrary(second.library);
    const decoded = decodePatchLibrary(encoded);

    expect(decoded.warnings).toEqual([]);
    expect(decoded.library.schemaVersion).toBe(LOCAL_PATCH_LIBRARY_SCHEMA);
    expect(decoded.library.patches.map((patch) => patch.name)).toEqual(["Alpha", "Zed"]);
    expect(encodePatchLibrary(decoded.library)).toBe(encoded);
    expect(encoded).not.toContain("timestamp");
  });

  it("fails closed on unknown schemas and malformed records", () => {
    expect(decodePatchLibrary("not-json").warnings).toHaveLength(1);
    expect(decodePatchLibrary(JSON.stringify({ schemaVersion: "future", patches: [] })))
      .toMatchObject({ library: { patches: [] }, warnings: [expect.stringContaining("schema")] });

    const valid = upsertLocalPatch(
      emptyPatchLibrary(),
      snapshot,
      "Valid",
      null,
      () => "local-patch-valid000",
    ).patch;
    const mixed = decodePatchLibrary(JSON.stringify({
      patches: [valid, { ...valid, patchId: "display-name-as-id", referencePositions: {} }],
      schemaVersion: LOCAL_PATCH_LIBRARY_SCHEMA,
    }));
    expect(mixed.library.patches.map((patch) => patch.name)).toEqual(["Valid"]);
    expect(mixed.warnings).toHaveLength(1);
  });

  it("searches local patches separately and deletes only the requested record", () => {
    const tide = upsertLocalPatch(
      emptyPatchLibrary(),
      snapshot,
      "Tidal Bell",
      null,
      () => "local-patch-tidal000",
    );
    const palimpsest = upsertLocalPatch(
      tide.library,
      { ...snapshot, machineKey: "palimpsest", mode: "drive" },
      "Paper Trace",
      null,
      () => "local-patch-paper000",
    );

    expect(searchSavedPatches(palimpsest.library.patches, "palimpsest"))
      .toEqual([palimpsest.patch]);
    expect(deleteLocalPatch(palimpsest.library, tide.patch.patchId).patches)
      .toEqual([palimpsest.patch]);
  });
});

