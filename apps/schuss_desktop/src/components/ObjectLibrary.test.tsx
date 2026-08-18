import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ObjectLibrary } from "./ObjectLibrary";

const dispatchMock = vi.fn();
const inspectFamilyMock = vi.fn();

vi.mock("../core/bridge", () => ({
  dispatchDesktopOperation: (...args: unknown[]) => dispatchMock(...args),
  inspectCatalogFamily: (...args: unknown[]) => inspectFamilyMock(...args),
}));

const contractReference = {
  stable_id: "schuss-component-contract-000012",
  revision: 1,
  content_hash: `sha256:${"a".repeat(64)}`,
};

const results = [
  {
    implementation_id: "schuss-implementation-000001",
    exact_reference: null,
    display_name: "Saw implementation",
    form: "generated-object",
    family_reference: { family_id: "schuss-family-000001", revision: 1, content_hash: `sha256:${"b".repeat(64)}` },
    family_display_name: "Band-limited Saw Oscillator",
    primary_function: "sound-sources",
    abstraction_level: "primitive",
    provenance_sources: ["axoloti-factory"],
    provenance_tags: [],
    readiness_states: ["contracted"],
    score: 100,
  },
  {
    implementation_id: "schuss-implementation-000002",
    exact_reference: null,
    display_name: "Voice implementation",
    form: "native-object",
    family_reference: { family_id: "schuss-family-000002", revision: 1, content_hash: `sha256:${"c".repeat(64)}` },
    family_display_name: "Mutable Voice",
    primary_function: "sound-sources",
    abstraction_level: "primitive",
    provenance_sources: ["axoloti-factory"],
    provenance_tags: ["mutable-instruments-derived"],
    readiness_states: ["catalogued-only"],
    score: 90,
  },
];

describe("ObjectLibrary patch drawer", () => {
  beforeEach(() => {
    dispatchMock.mockReset();
    inspectFamilyMock.mockReset();
    dispatchMock.mockImplementation((request: { operation: string }) => {
      if (request.operation === "catalog.implementations.search") {
        return Promise.resolve({ total_matches: 2, results });
      }
      return Promise.resolve({
        component_contract: {
          component_contract_id: contractReference.stable_id,
          revision: 1,
          content_hash: contractReference.content_hash,
          display_name: "Band-limited Saw Oscillator",
          ports: [],
          parameters: [],
          attributes: [],
        },
      });
    });
    inspectFamilyMock.mockImplementation((reference: { family_id: string }) => Promise.resolve({
      family: {
        implementations: [{
          implementation_id: reference.family_id === "schuss-family-000001" ? "schuss-implementation-000001" : "schuss-implementation-000002",
          contract_references: reference.family_id === "schuss-family-000001" ? [contractReference] : [],
        }],
      },
    }));
  });

  it("enables Add only after exact contract resolution and guards catalogued-only rows", async () => {
    const onAdd = vi.fn();
    const user = userEvent.setup();
    render(<ObjectLibrary mode="drawer" onAdd={onAdd} />);

    const addSaw = await screen.findByRole("button", { name: "Add Band-limited Saw Oscillator" });
    expect(addSaw).toBeEnabled();
    await user.click(addSaw);
    expect(onAdd).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: /Mutable Voice.*Native Object/ }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Mutable Voice unavailable" })).toBeDisabled());
    expect(await screen.findByText(/Catalogued only/)).toBeVisible();
    expect(onAdd).toHaveBeenCalledTimes(1);
  });
});
