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

  it("resolves and adds a patcher object in one action while retaining the complete catalog", async () => {
    const onAdd = vi.fn();
    const user = userEvent.setup();
    render(<ObjectLibrary onAdd={onAdd} />);

    const addSaw = await screen.findByRole("button", { name: "Add Band-limited Saw Oscillator" });
    expect(addSaw).toBeEnabled();
    await user.click(addSaw);
    await waitFor(() => expect(onAdd).toHaveBeenCalledTimes(1));

    expect(screen.queryByText("Mutable Voice")).not.toBeInTheDocument();
    await user.selectOptions(screen.getByRole("combobox", { name: "Object collection" }), "all");
    await user.click(screen.getByRole("button", { name: /Mutable Voice.*Native Object/ }));
    await user.click(screen.getByRole("button", { name: "Add Mutable Voice" }));
    expect(await screen.findByText(/Catalogued only.*no single component contract/)).toBeVisible();
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it("keeps accepted project objects separate and adds their exact component contract", async () => {
    const onAdd = vi.fn();
    const user = userEvent.setup();
    const objectReference = {
      object_definition_id: "schuss-project-object-000123",
      revision: 1,
      content_hash: `sha256:${"d".repeat(64)}`,
    };
    const evidence = {
      structural: "passed",
      host_evaluation: { status: "passed" },
      target_lowering: "not-run",
      arm_build: "not-run",
      connected_device: "not-run",
      real_time_resources: "not-evaluated",
      audible_listening: "not-run",
    };
    dispatchMock.mockImplementation((request: { operation: string }) => {
      if (request.operation === "catalog.implementations.search") {
        return Promise.resolve({ total_matches: 2, results });
      }
      if (request.operation === "project.objects.list") {
        return Promise.resolve({
          project_reference: { project_id: "schuss-project-000123", revision: 3, content_hash: `sha256:${"e".repeat(64)}` },
          object_count: 1,
          objects: [{
            object_reference: objectReference,
            display_name: "Throat Ripper",
            function: "sound-sources",
            form: "native-kernel",
            evidence,
          }],
        });
      }
      if (request.operation === "project.object.inspect") {
        return Promise.resolve({
          project_reference: { project_id: "schuss-project-000123", revision: 3, content_hash: `sha256:${"e".repeat(64)}` },
          object_definition: {
            object_definition_id: objectReference.object_definition_id,
            revision: 1,
            content_hash: objectReference.content_hash,
            family: {
              family_id: "schuss-family-000123",
              revision: 1,
              content_hash: `sha256:${"f".repeat(64)}`,
              display_name: "Throat Ripper",
              aliases: [],
              function: "sound-sources",
              desired_character: ["aggressive"],
              provenance: "ai-authored",
            },
            component_contract: {
              component_contract_id: "schuss-component-contract-000123",
              revision: 1,
              content_hash: `sha256:${"1".repeat(64)}`,
              display_name: "Throat Ripper",
              ports: [],
              parameters: [],
              attributes: [],
            },
            implementation_binding: {},
            realization: { form: "native-kernel" },
            intent: {},
            evidence,
          },
        });
      }
      throw new Error(`Unexpected operation ${request.operation}`);
    });

    render(<ObjectLibrary onAdd={onAdd} projectRevision={3} workspace="/tmp/test-patch" />);

    await user.selectOptions(await screen.findByRole("combobox", { name: "Object source" }), "project");
    expect(await screen.findByText("Throat Ripper")).toBeVisible();
    expect(screen.getAllByText(/Host evaluated · Target not lowered/)).toHaveLength(2);
    const add = await screen.findByRole("button", { name: "Add Throat Ripper" });
    expect(add).toBeEnabled();
    await user.click(add);
    expect(onAdd).toHaveBeenCalledWith(expect.objectContaining({
      component_contract_id: "schuss-component-contract-000123",
    }));
    expect(inspectFamilyMock).not.toHaveBeenCalled();
  });
});
