import { describe, expect, it } from "vitest";

import {
  blockIdsForSlots,
  createMachineView,
  downstreamBlockIds,
  meaningsForSlots,
  panelLabelForSlot,
  slotIdsForBlock,
} from "./machineModel";
import { fixtureForMachine, presentationForMachine } from "./presentation";
import type { MachineKey, PerformanceMode } from "./types";

const machineKeys: MachineKey[] = ["tide-pit", "palimpsest"];

describe("canonical machine inspection adapter", () => {
  it.each(machineKeys)("adapts %s without mutating its canonical fixture", (key) => {
    const fixture = fixtureForMachine(key);
    const before = JSON.stringify(fixture);
    const view = createMachineView(fixture, presentationForMachine(key));

    expect(JSON.stringify(fixture)).toBe(before);
    expect(view.blocks).toHaveLength(9);
    expect(view.regions).toHaveLength(20);
    expect(view.raw.operation).toBe("machine.inspect");
    expect(view.inspectionState).toBe("inspection-only");
    expect(view.identity.source_identity.source_id).toContain(key === "tide-pit" ? "tide-pit" : "palimpsest");
    expect(view.blocks.every((block) => block.source_block_ids.length > 0 && block.parts.length > 0)).toBe(true);
  });

  it("fails closed if an editing affordance becomes enabled", () => {
    const fixture = structuredClone(fixtureForMachine("tide-pit")) as Record<string, unknown>;
    const value = fixture.value as Record<string, unknown>;
    const affordances = value.affordances as Record<string, unknown>;
    affordances.edit = true;
    expect(() => createMachineView(fixture, presentationForMachine("tide-pit"))).toThrow(/edit affordance must remain disabled/);
  });

  it("keeps exact panel links separate from downstream flow", () => {
    const view = createMachineView(fixtureForMachine("tide-pit"), presentationForMachine("tide-pit"));
    const exact = blockIdsForSlots(view, ["device-input-000009"], "CLEAN");
    expect(exact).toEqual(["presentation-block-000001"]);
    expect(downstreamBlockIds(view.edges, exact)).toEqual(view.blocks.map((block) => block.presentation_block_id));
    expect(blockIdsForSlots(view, ["device-display-000001"], "CLEAN")).toEqual(["presentation-block-000009"]);
  });

  it("groups every gesture on one physical S4 button", () => {
    const view = createMachineView(fixtureForMachine("tide-pit"), presentationForMachine("tide-pit"));
    const s4 = view.regionsByElement.get("button-04-region");
    expect(s4?.semanticSlotIds).toEqual([
      "device-gesture-000010",
      "device-gesture-000011",
      "device-gesture-000012",
    ]);
    expect(meaningsForSlots(view, s4?.semanticSlotIds ?? [], "CLEAN").map((item) => item.mappingState)).toEqual([
      "mapped",
      "mapped",
      "mapped",
    ]);
  });

  it("retains intentionally unmapped gestures as visible evidence", () => {
    const view = createMachineView(fixtureForMachine("palimpsest"), presentationForMachine("palimpsest"));
    const encoder = view.regionsByElement.get("encoder-region");
    const meanings = meaningsForSlots(view, encoder?.semanticSlotIds ?? [], "CLEAN");
    expect(meanings.some((item) => item.semanticSlotId === "device-gesture-000016" && item.mappingState === "intentionally-unmapped")).toBe(true);
  });

  it.each([
    ["tide-pit", "CLEAN", "Grain size", "Depth / tail"],
    ["tide-pit", "FILT", "Cutoff", "Resonance"],
    ["tide-pit", "DRIVE", "Drive tone", "Drive amt."],
    ["palimpsest", "CLEAN", "Modal decay", "Activity / mix"],
    ["palimpsest", "FILT", "Cutoff", "Resonance"],
    ["palimpsest", "DRIVE", "Drive tone", "Drive amt."],
  ] as Array<[MachineKey, PerformanceMode, string, string]>)(
    "resolves %s %s mode-aware P9/P10 labels",
    (key, mode, pot9, pot10) => {
      const view = createMachineView(fixtureForMachine(key), presentationForMachine(key));
      expect(panelLabelForSlot(view, "device-input-000009", mode)).toBe(pot9);
      expect(panelLabelForSlot(view, "device-input-000010", mode)).toBe(pot10);
    },
  );

  it("returns only exact linked slots for a selected block", () => {
    const view = createMachineView(fixtureForMachine("palimpsest"), presentationForMachine("palimpsest"));
    expect(slotIdsForBlock(view, "presentation-block-000009", "CLEAN")).toEqual([
      "device-feedback-000001",
      "device-feedback-000002",
      "device-feedback-000003",
      "device-feedback-000005",
      "device-display-000001",
    ]);
  });
});
