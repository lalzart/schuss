import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CatalogSidebar } from "./CatalogSidebar";

describe("CatalogSidebar", () => {
  it("renders compact object rows, drag affordances, and disabled evidence", () => {
    const markup = renderToStaticMarkup(
      <CatalogSidebar
        activePatchId={null}
        libraryWarning={null}
        onAdd={() => undefined}
        onDeletePatch={() => undefined}
        onLoadPatch={() => undefined}
        onLoadTemplate={() => undefined}
        savedPatches={[]}
      />,
    );

    expect(markup).toContain("Patcher library");
    expect(markup).toContain("Accepted direct-palette selections");
    expect(markup).toContain("Objects");
    expect(markup).toContain("Patches");
    expect(markup).toContain("Search objects");
    expect(markup).toContain("draggable=\"true\"");
    expect(markup).toContain("Reference only");
    expect(markup).toContain("Granular Buffer Processor");
    expect(markup).toContain("aria-disabled=\"true\"");
    expect(markup).not.toContain("Generates a band-limited sawtooth audio stream from pitch control.");
    expect(markup).not.toContain("schuss-family-000031");
  });
});
