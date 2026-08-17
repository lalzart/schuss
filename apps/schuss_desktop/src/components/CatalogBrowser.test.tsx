import * as Tooltip from "@radix-ui/react-tooltip";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  CatalogFamilyInspection,
  CatalogSearchItem,
  ExactFamilyReference,
  ReadOnlyRequest,
} from "../core/types";
import { CatalogBrowser } from "./CatalogBrowser";

const recordSet = {
  record_set_id: "schuss-record-set-000021",
  revision: 1,
  content_hash: `sha256:${"1".repeat(64)}`,
};

const audioReference: ExactFamilyReference = {
  family_id: "schuss-family-000001",
  revision: 1,
  content_hash: `sha256:${"2".repeat(64)}`,
};

const bellReference: ExactFamilyReference = {
  family_id: "schuss-family-000038",
  revision: 1,
  content_hash: `sha256:${"3".repeat(64)}`,
};

const audio: CatalogSearchItem = {
  family_reference: audioReference,
  display_name: "Audio Input",
  aliases: ["Audio In"],
  description: "Receives a stereo audio stream.",
  primary_function: "input-output",
  technique_tags: ["audio-input"],
  abstraction_level: "primitive",
  implementation_forms: ["native-object"],
  readiness_states: ["catalogued-only", "unresolved"],
  contract_facets_available: false,
  provenance_facets: ["ksoloti-objects"],
  score: 0,
};

const bell: CatalogSearchItem = {
  family_reference: bellReference,
  display_name: "Struck Bell Voice",
  aliases: ["Braids Struck Bell"],
  description: "Generates a struck-bell voice.",
  primary_function: "sound-sources",
  technique_tags: ["percussion"],
  abstraction_level: "primitive",
  implementation_forms: ["native-object"],
  readiness_states: ["contracted", "bound", "unresolved"],
  contract_facets_available: true,
  provenance_facets: ["axoloti-factory", "mutable-instruments-derived"],
  score: 0,
};

function familyInspection(item: CatalogSearchItem): CatalogFamilyInspection {
  return {
    ...item,
    signal_facets:
      item === bell
        ? [{ domain: "stream", rate: "audio", role: "audio", channel_count: 1 }]
        : [],
    contract_facet_names: item === bell ? ["Pitch", "Strike", "audio"] : [],
    capability_keys: item === bell ? ["audio-stream-fixed-q27"] : [],
    implementations: [],
    unresolved_facts: item.readiness_states.includes("unresolved")
      ? ["Exact runtime behavior is not established by catalog membership."]
      : [],
  };
}

function success(operation: string, value: unknown) {
  return {
    schema_version:
      operation === "application.describe"
        ? "schuss-operation-result-v7"
        : "schuss-operation-result-v2",
    canonical_profile: "schuss-canonical-json-v1",
    operation,
    status: "success",
    value,
    diagnostics: [],
  };
}

function response(body: unknown): Response {
  return { ok: true, json: async () => body } as Response;
}

describe("CatalogBrowser", () => {
  const requests: ReadOnlyRequest[] = [];

  beforeEach(() => {
    requests.length = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, init?: RequestInit) => {
        const request = JSON.parse(String(init?.body)) as ReadOnlyRequest;
        requests.push(request);
        if (request.operation === "application.describe") {
          return response(
            success("application.describe", {
              description_version: "schuss-application-capability-description-v1",
              record_set_reference: recordSet,
              operations: [
                { operation: "application.describe", availability: "available", effect_class: "read-only" },
                { operation: "catalog.search", availability: "available", effect_class: "read-only" },
                { operation: "catalog.inspect", availability: "available", effect_class: "read-only" },
              ],
            }),
          );
        }
        if (request.operation === "catalog.search") {
          const filters = request.payload.filters;
          const selected =
            filters.function.includes("sound-sources") ||
            filters.provenance.includes("mutable-instruments-derived")
              ? [bell]
              : [audio, bell];
          return response(
            success("catalog.search", {
              record_set_reference: recordSet,
              projection_version: "schuss-catalog-projection-v4",
              match_algorithm: "schuss-catalog-match-v1",
              query: request.payload.query,
              filters,
              results: selected,
              total_matches: selected.length,
            }),
          );
        }
        return response(
          success("catalog.inspect", {
            record_set_reference: recordSet,
            projection_version: "schuss-catalog-projection-v4",
            match_algorithm: "schuss-catalog-match-v1",
            family: familyInspection(
              request.payload.family_reference.family_id === bellReference.family_id ? bell : audio,
            ),
          }),
        );
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  function renderBrowser() {
    return render(
      <Tooltip.Provider>
        <CatalogBrowser />
      </Tooltip.Provider>,
    );
  }

  it("renders operation-backed families and inspects the exact selected reference", async () => {
    const user = userEvent.setup();
    renderBrowser();

    expect(await screen.findByText("Audio Input")).toBeVisible();
    expect(screen.getByText("Struck Bell Voice")).toBeVisible();
    expect(screen.getAllByText("schuss-record-set-000021@1")[0]).toBeVisible();

    screen.getByRole("button", { name: /Struck Bell Voice/ }).focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("heading", { name: "Struck Bell Voice" })).toBeVisible();
    expect(screen.getByText("Pitch")).toBeVisible();
    expect(screen.getByText("audio-stream-fixed-q27")).toBeVisible();

    await waitFor(() => {
      expect(
        requests.some(
          (request) =>
            request.operation === "catalog.inspect" &&
            request.payload.family_reference.family_id === bellReference.family_id &&
            request.payload.family_reference.content_hash === bellReference.content_hash,
        ),
      ).toBe(true);
    });
  });

  it("routes search and every drawer filter through catalog.search", async () => {
    const user = userEvent.setup();
    renderBrowser();
    await screen.findAllByText("Audio Input");

    await user.click(screen.getByPlaceholderText("Search exact catalog…"));
    await user.type(screen.getByPlaceholderText("Search exact catalog…"), "bell");
    await waitFor(() => {
      expect(
        requests.some(
          (request) => request.operation === "catalog.search" && request.payload.query === "bell",
        ),
      ).toBe(true);
    });

    await user.click(screen.getByRole("button", { name: /Sound Sources/ }));
    await waitFor(() => {
      expect(
        requests.some(
          (request) =>
            request.operation === "catalog.search" &&
            request.payload.filters.function.includes("sound-sources"),
        ),
      ).toBe(true);
    });

    await user.click(screen.getByRole("tab", { name: "Mutable-derived" }));
    await waitFor(() => {
      expect(
        requests.some(
          (request) =>
            request.operation === "catalog.search" &&
            request.payload.filters.provenance.includes("mutable-instruments-derived"),
        ),
      ).toBe(true);
    });

    await user.selectOptions(screen.getByRole("combobox"), "catalogued-only");
    await waitFor(() => {
      expect(
        requests.some(
          (request) =>
            request.operation === "catalog.search" &&
            request.payload.filters.readiness.includes("catalogued-only"),
        ),
      ).toBe(true);
    });
  });

  it("focuses exact search with the documented Command-K shortcut", async () => {
    const user = userEvent.setup();
    renderBrowser();
    await screen.findAllByText("Audio Input");

    await user.keyboard("{Meta>}k{/Meta}");
    expect(screen.getByPlaceholderText("Search exact catalog…")).toHaveFocus();
  });
});
