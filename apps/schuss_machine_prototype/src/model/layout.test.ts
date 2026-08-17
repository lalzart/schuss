import { describe, expect, it } from "vitest";

import { layoutMachineRows } from "./layout";
import { createMachineView } from "./machineModel";
import { fixtureForMachine, presentationForMachine } from "./presentation";

describe("machine layout", () => {
  it("is deterministic and preserves the configured two-row grouping", async () => {
    const view = createMachineView(fixtureForMachine("tide-pit"), presentationForMachine("tide-pit"));
    const expanded = new Set(["presentation-block-000001"]);
    const first = await layoutMachineRows(view, expanded);
    const second = await layoutMachineRows(view, expanded);

    expect(second).toEqual(first);
    expect(first.blocks).toHaveLength(9);
    expect(new Set(first.blocks.map((block) => block.rowIndex))).toEqual(new Set([0, 1]));
    const row0Y = first.blocks.filter((block) => block.rowIndex === 0).map((block) => block.y);
    const row1Y = first.blocks.filter((block) => block.rowIndex === 1).map((block) => block.y);
    expect(Math.min(...row1Y)).toBeGreaterThan(Math.max(...row0Y));
  });

  it("gives expanded compounds more vertical space", async () => {
    const view = createMachineView(fixtureForMachine("palimpsest"), presentationForMachine("palimpsest"));
    const collapsed = await layoutMachineRows(view, new Set());
    const expanded = await layoutMachineRows(view, new Set(["presentation-block-000005"]));
    const getBlock = (layout: typeof collapsed) => layout.blocks.find((block) => block.id === "presentation-block-000005");
    expect(getBlock(expanded)?.height).toBeGreaterThan(getBlock(collapsed)?.height ?? 0);
  });
});
