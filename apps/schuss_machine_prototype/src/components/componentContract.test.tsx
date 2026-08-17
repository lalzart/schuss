import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { createMachineView } from "../model/machineModel";
import { fixtureForMachine, presentationForMachine } from "../model/presentation";
import { ModeSwitch } from "./ModeSwitch";
import { SelectionInspector } from "./SelectionInspector";

describe("read-only component contract", () => {
  it("renders one pressed performance mode without mutation actions", () => {
    const html = renderToStaticMarkup(<ModeSwitch mode="FILT" onChange={vi.fn()} />);
    expect(html.match(/aria-pressed="true"/g)).toHaveLength(1);
    expect(html).toContain("FILT");
    expect(html).not.toMatch(/build|deploy|connect|delete/i);
  });

  it("renders exact mapped and intentionally-unmapped meanings for a physical control", () => {
    const view = createMachineView(fixtureForMachine("palimpsest"), presentationForMachine("palimpsest"));
    const encoder = view.regionsByElement.get("encoder-region");
    const html = renderToStaticMarkup(
      <SelectionInspector
        exactTargetBlockIds={["presentation-block-000001"]}
        mode="CLEAN"
        selectedSlotIds={encoder?.semanticSlotIds ?? []}
        selection={{ elementId: "encoder-region", kind: "panel" }}
        view={view}
      />,
    );
    expect(html).toContain("Set root from C2 through C5");
    expect(html).toContain("No encoder-hold mapping in the inspected source");
    expect(html).toContain("Four-stage mutation engine");
  });
});
