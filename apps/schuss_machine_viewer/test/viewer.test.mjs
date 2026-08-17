import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import {
  assertInspectionResult,
  buildViewModel,
  controlsForBlock,
  disabledAffordances,
  exactIdentityText,
  highlightElementIdsForSlots,
  mappingForControl,
  sourceEvidenceForBlock,
} from "../viewer.js";

async function fixture(name) {
  return JSON.parse(await readFile(new URL(`../fixtures/${name}`, import.meta.url), "utf8"));
}

test("both exact reference machines expose all Viewer sections and no unsafe affordances", async () => {
  for (const name of ["palimpsest-machine-inspect.json", "tide-pit-machine-inspect.json"]) {
    const view = buildViewModel(await fixture(name));
    assert.equal(view.value.inspection_state, "inspection-only");
    assert.ok(view.value.identity.display_name);
    assert.ok(view.value.machine_block_diagram.blocks.length >= 8);
    assert.equal(view.value.panel.semantic_regions.length, 42);
    assert.ok(view.value.source_evidence.spans.length >= 6);
    assert.ok(view.value.dependencies.length >= 15);
    assert.deepEqual(disabledAffordances(view), ["build", "deploy", "edit", "play", "promote"]);
  }
});

test("block to panel highlighting and panel to mode meanings are total", async () => {
  const view = buildViewModel(await fixture("palimpsest-machine-inspect.json"));
  const controlBlock = view.value.machine_block_diagram.blocks[0].presentation_block_id;
  const slots = controlsForBlock(view, controlBlock);
  assert.ok(sourceEvidenceForBlock(view, controlBlock)[0].startsWith("projects/palimpsest-gills/"));
  assert.ok(slots.includes("device-input-000009"));
  assert.ok(slots.includes("device-gesture-000001"));
  assert.equal(new Set(highlightElementIdsForSlots(view, slots)).size < slots.length, true, "shared physical regions retain separate semantic IDs");
  const potNine = mappingForControl(view, "device-input-000009");
  assert.deepEqual(potNine.mapping.meanings.map((item) => item.mode), ["CLEAN", "FILT", "DRIVE"]);
  assert.equal(mappingForControl(view, "device-gesture-000016").mapping.mapping_state, "intentionally-unmapped");
});

test("identity rendering uses a completed machine ID when one is present", async () => {
  const result = await fixture("palimpsest-machine-inspect.json");
  result.value.inspection_state = "completed-machine";
  result.value.identity.machine = {
    machine_id: "schuss-machine-000001",
    revision: 2,
    content_hash: `sha256:${"a".repeat(64)}`,
  };
  const view = buildViewModel(result);
  assert.match(exactIdentityText(view), /^schuss-machine-000001@2/);
});

test("Tide Pit retains its exact resource and Rings boundaries", async () => {
  const view = buildViewModel(await fixture("tide-pit-machine-inspect.json"));
  assert.equal(view.value.identity.display_name, "Tide Pit");
  assert.equal(view.value.resources.source_declared_bytes, 251408);
  const rings = view.value.dependencies.find((item) => item.dependency_id === "rings-reverb-non-dependency");
  assert.equal(rings.required, false);
  assert.equal(rings.classification, "unsupported");
  assert.equal(mappingForControl(view, "device-gesture-000016").mapping.mapping_state, "mapped");
});

test("Viewer fails closed on a non-operation payload or enabled unsafe action", async () => {
  const result = await fixture("palimpsest-machine-inspect.json");
  assert.throws(() => assertInspectionResult({}), /requires one successful/);
  result.value.affordances.build = true;
  assert.throws(() => assertInspectionResult(result), /must disable build/);
});
