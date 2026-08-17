import { describe, expect, it } from "vitest";

import {
  buildCatalogDraftNode,
  buildReferenceEdges,
  buildReferenceNodes,
  createPatchSnapshot,
} from "./graph";
import { SELECTABLE_CATALOG_ITEMS } from "./catalog";
import { MACHINES } from "./machines";
import { labelForMode } from "./types";

const expectedControlIds = [
  "pot-1",
  "pot-2",
  "pot-3",
  "pot-4",
  "pot-5",
  "pot-6",
  "pot-7",
  "pot-8",
  "pot-9",
  "pot-10",
  "button-1",
  "button-2",
  "button-3",
  "button-4",
  "encoder-turn",
  "encoder-push",
  "encoder-hold",
];

describe("Gills reference machines", () => {
  it.each([MACHINES["tide-pit"], MACHINES.palimpsest])(
    "$displayName exposes the complete physical control and output racks",
    (machine) => {
      expect(machine.controls.map((mapping) => mapping.controlId)).toEqual(expectedControlIds);
      expect(machine.outputs.map((output) => output.outputId)).toEqual([
        "stereo-out",
        "stage-led-1",
        "stage-led-2",
        "stage-led-3",
        "stage-led-4",
        "oled-status",
      ]);
      expect(buildReferenceNodes(machine, "clean").map((node) => node.type)).toEqual([
        "gillsInput",
        "instrument",
        "gillsOutput",
      ]);
    },
  );

  it("retains the intentional encoder-hold difference", () => {
    const tideHold = MACHINES["tide-pit"].controls.find(
      (mapping) => mapping.controlId === "encoder-hold",
    );
    const palimpsestHold = MACHINES.palimpsest.controls.find(
      (mapping) => mapping.controlId === "encoder-hold",
    );

    expect(tideHold).toMatchObject({ mapped: true, targetId: "destination" });
    expect(labelForMode(tideHold!, "clean")).toBe("Destination");
    expect(palimpsestHold).toMatchObject({ mapped: false, targetId: "encoder-hold-unmapped" });
    expect(labelForMode(palimpsestHold!, "drive")).toBe("Unmapped");

    const tideEdges = buildReferenceEdges(MACHINES["tide-pit"]);
    const palimpsestEdges = buildReferenceEdges(MACHINES.palimpsest);
    expect(tideEdges.some((edge) => edge.id === "mapping-encoder-hold")).toBe(true);
    expect(palimpsestEdges.some((edge) => edge.id === "mapping-encoder-hold")).toBe(false);
    expect(tideEdges).toHaveLength(23);
    expect(palimpsestEdges).toHaveLength(22);
  });

  it("uses exact mode-dependent P9 and P10 labels", () => {
    const tideP9 = MACHINES["tide-pit"].controls[8];
    const tideP10 = MACHINES["tide-pit"].controls[9];
    const palimpsestP9 = MACHINES.palimpsest.controls[8];
    const palimpsestP10 = MACHINES.palimpsest.controls[9];

    expect(tideP9 && ["clean", "filter", "drive"].map(
      (mode) => labelForMode(tideP9, mode as "clean" | "filter" | "drive"),
    )).toEqual(["Grain Size", "Cutoff", "Tone"]);
    expect(tideP10 && ["clean", "filter", "drive"].map(
      (mode) => labelForMode(tideP10, mode as "clean" | "filter" | "drive"),
    )).toEqual(["Depth / Tail", "Resonance", "Amount"]);
    expect(palimpsestP9 && labelForMode(palimpsestP9, "clean")).toBe("Modal Decay");
    expect(palimpsestP10 && labelForMode(palimpsestP10, "clean")).toBe("Activity / Mix");
  });

  it("keeps source internals as outline stages rather than flow nodes", () => {
    const nodes = buildReferenceNodes(MACHINES["tide-pit"], "clean");
    expect(nodes).toHaveLength(3);
    expect(MACHINES["tide-pit"].sourceOutline).toHaveLength(5);
    expect(MACHINES.palimpsest.sourceOutline).toHaveLength(5);
  });

  it("captures only presentation placement and exact accepted catalog identity", () => {
    const referenceNodes = buildReferenceNodes(MACHINES["tide-pit"], "drive");
    referenceNodes[0]!.position = { x: 14, y: 56 };
    const draftNode = buildCatalogDraftNode(
      SELECTABLE_CATALOG_ITEMS[0]!,
      { x: 700, y: 900 },
      4,
    );
    const snapshot = createPatchSnapshot(
      "tide-pit",
      "drive",
      draftNode === null ? referenceNodes : [...referenceNodes, draftNode],
    );

    expect(snapshot).toMatchObject({
      catalogNodes: [{
        familyId: SELECTABLE_CATALOG_ITEMS[0]!.familyReference.stableId,
        localIndex: 4,
        position: { x: 700, y: 900 },
      }],
      machineKey: "tide-pit",
      mode: "drive",
      referencePositions: { "gills-input-rack": { x: 14, y: 56 } },
    });
    expect(Object.keys(snapshot)).toEqual([
      "catalogNodes",
      "machineKey",
      "mode",
      "referencePositions",
    ]);
  });
});
