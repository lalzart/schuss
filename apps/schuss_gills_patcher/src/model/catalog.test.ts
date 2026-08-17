import { describe, expect, it } from "vitest";

import task025PwmBinding from "../../../../contracts/task025/implementation-binding-pwm.json";
import task025SawBinding from "../../../../contracts/task025/implementation-binding-saw.json";
import task025SmoothBinding from "../../../../contracts/task025/implementation-binding-smooth.json";
import task025SoftClipBinding from "../../../../contracts/task025/implementation-binding-soft-clip.json";
import task025VcaBinding from "../../../../contracts/task025/implementation-binding-vca.json";
import task025Selection from "../../../../contracts/task024/task025-selection-packet.json";
import task028Selection from "../../../../contracts/task028/selection-packet.json";
import {
  ALL_CATALOG_ITEMS,
  DISABLED_CATALOG_ITEMS,
  SELECTABLE_CATALOG_ITEMS,
  catalogItemByFamily,
  filterCatalogItems,
} from "./catalog";
import { buildCatalogDraftNode } from "./graph";

describe("prototype catalog fixture", () => {
  it("contains exactly the accepted twenty-item direct palette", () => {
    expect(SELECTABLE_CATALOG_ITEMS).toHaveLength(20);
    expect(new Set(SELECTABLE_CATALOG_ITEMS.map(
      (item) => item.familyReference.stableId,
    )).size).toBe(20);
    expect(SELECTABLE_CATALOG_ITEMS.every(
      (item) => item.selectable && item.contractReference !== null,
    )).toBe(true);
  });

  it("pins every selectable family and contract to revision and content hash", () => {
    for (const item of SELECTABLE_CATALOG_ITEMS) {
      expect(item.familyReference.revision).toBe(1);
      expect(item.familyReference.contentHash).toMatch(/^sha256:[0-9a-f]{64}$/);
      expect(item.contractReference?.revision).toBe(1);
      expect(item.contractReference?.contentHash).toMatch(/^sha256:[0-9a-f]{64}$/);
    }
  });

  it("matches the exact Task 025 baseline and Task 028 addition references", () => {
    const baselineBindings = [
      task025SawBinding,
      task025PwmBinding,
      task025SmoothBinding,
      task025SoftClipBinding,
      task025VcaBinding,
    ];
    const baselineContractIds = new Set(
      baselineBindings.map((binding) => binding.contract_reference.component_contract_id),
    );
    expect(task028Selection.baseline.map(
      (entry) => entry.native_binding_reference.implementation_id,
    ).sort()).toEqual(baselineBindings.map((binding) => binding.implementation_id).sort());

    const expectedBaseline = task025Selection.subjects
      .filter((subject) => baselineContractIds.has(subject.contract_reference.stable_id))
      .map((subject) => ({
        contractHash: subject.contract_reference.content_hash,
        contractId: subject.contract_reference.stable_id,
        contractRevision: subject.contract_reference.revision,
        familyHash: subject.family_reference.content_hash,
        familyId: subject.family_reference.stable_id,
        familyRevision: subject.family_reference.revision,
      }));
    const expectedAdditions = task028Selection.additions.map((addition) => ({
      contractHash: addition.contract_reference.content_hash,
      contractId: addition.contract_reference.component_contract_id,
      contractRevision: addition.contract_reference.revision,
      familyHash: addition.family_reference.content_hash,
      familyId: addition.family_reference.family_id,
      familyRevision: addition.family_reference.revision,
    }));
    const actual = SELECTABLE_CATALOG_ITEMS.map((item) => ({
      contractHash: item.contractReference?.contentHash,
      contractId: item.contractReference?.stableId,
      contractRevision: item.contractReference?.revision,
      familyHash: item.familyReference.contentHash,
      familyId: item.familyReference.stableId,
      familyRevision: item.familyReference.revision,
    }));
    const byFamily = (left: { familyId: string }, right: { familyId: string }) => (
      left.familyId.localeCompare(right.familyId)
    );

    expect(actual.sort(byFamily)).toEqual([...expectedBaseline, ...expectedAdditions].sort(byFamily));
  });

  it("keeps unsupported reference items visible and fail-closed", () => {
    expect(DISABLED_CATALOG_ITEMS.map((item) => item.displayName)).toEqual([
      "Granular Buffer Processor",
      "Rings-derived Stereo Reverb",
      "Gills Text Display",
    ]);
    expect(DISABLED_CATALOG_ITEMS.every((item) => !item.selectable)).toBe(true);
    for (const item of DISABLED_CATALOG_ITEMS) {
      expect(buildCatalogDraftNode(item, { x: 0, y: 0 }, 1)).toBeNull();
    }
  });

  it("creates only exact, accepted local draft cards", () => {
    const item = catalogItemByFamily("schuss-family-000031");
    expect(item).toBeDefined();
    expect(buildCatalogDraftNode(item!, { x: 28, y: 42 }, 3)).toMatchObject({
      id: "catalog-draft-3",
      position: { x: 28, y: 42 },
      type: "catalogDraft",
    });
  });

  it("filters by function and search text without changing the source fixture", () => {
    expect(filterCatalogItems(ALL_CATALOG_ITEMS, "envelope", "all")).toHaveLength(2);
    expect(filterCatalogItems(ALL_CATALOG_ITEMS, "", "timing-sequencing")).toHaveLength(2);
    expect(ALL_CATALOG_ITEMS).toHaveLength(23);
  });
});
