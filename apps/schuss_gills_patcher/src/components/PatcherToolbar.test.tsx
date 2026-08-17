import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { PatcherToolbar } from "./PatcherToolbar";

describe("PatcherToolbar", () => {
  it("keeps machine-owned effect modes out of the global toolbar", () => {
    const markup = renderToStaticMarkup(
      <PatcherToolbar
        currentPatchName={null}
        dirty={false}
        machineKey="tide-pit"
        onMachineChange={() => undefined}
        onReset={() => undefined}
        onSave={() => undefined}
      />,
    );

    expect(markup).toContain("Save patch");
    expect(markup).toContain("New from template");
    expect(markup).not.toContain("CLEAN");
    expect(markup).not.toContain("FILT");
    expect(markup).not.toContain("DRIVE");
  });
});

