import type {
  ActiveMeaning,
  MachineInspectResult,
  MachinePresentationConfig,
  MachineView,
  PerformanceMode,
  PhysicalRegionView,
  PresentationEdge,
  SourceMapping,
} from "./types";

const forbiddenAffordances = ["build", "deploy", "edit", "play", "promote"] as const;

function invariant(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(`Machine prototype failed closed: ${message}`);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasString(record: Record<string, unknown>, key: string): boolean {
  return typeof record[key] === "string" && record[key].length > 0;
}

export function assertMachineInspectResult(raw: unknown): asserts raw is MachineInspectResult {
  invariant(isRecord(raw), "fixture root must be an object");
  invariant(raw.operation === "machine.inspect", "operation must be machine.inspect");
  invariant(raw.status === "success", "fixture must be a successful result");
  invariant(hasString(raw, "schema_version"), "schema_version is required");
  invariant(isRecord(raw.value), "value is required");

  const value = raw.value;
  invariant(isRecord(value.identity), "identity is required");
  invariant(hasString(value.identity, "display_name"), "identity.display_name is required");
  invariant(isRecord(value.machine_block_diagram), "machine_block_diagram is required");
  invariant(Array.isArray(value.machine_block_diagram.blocks), "machine blocks must be an array");
  invariant(Array.isArray(value.machine_block_diagram.edges), "machine edges must be an array");
  invariant(isRecord(value.panel), "panel is required");
  invariant(Array.isArray(value.panel.semantic_regions), "panel semantic regions must be an array");
  invariant(Array.isArray(value.panel.source_mappings), "panel source mappings must be an array");
  invariant(Array.isArray(value.panel.presentation_links), "panel presentation links must be an array");
  invariant(isRecord(value.source_evidence), "source evidence is required");
  invariant(Array.isArray(value.source_evidence.blocks), "source evidence blocks must be an array");
  invariant(Array.isArray(value.dependencies), "dependencies must be an array");
  invariant(Array.isArray(value.proof_boundary), "proof boundary must be an array");
  invariant(isRecord(value.affordances), "affordances are required");
  invariant(value.affordances.inspect === true, "inspect must be the only enabled affordance");
  for (const action of forbiddenAffordances) {
    invariant(value.affordances[action] === false, `${action} affordance must remain disabled`);
  }
}

function appliesToMode(modes: readonly string[], mode: PerformanceMode): boolean {
  return modes.includes("ALL") || modes.includes(mode);
}

function activeMeaning(mapping: SourceMapping, mode: PerformanceMode): ActiveMeaning | null {
  const meaning = mapping.meanings.find((candidate) => candidate.mode === mode)
    ?? mapping.meanings.find((candidate) => candidate.mode === "ALL");
  if (!meaning) return null;
  return {
    mappingState: mapping.mapping_state,
    meaning: meaning.meaning,
    mode: meaning.mode,
    semanticSlotId: mapping.semantic_slot_id,
  };
}

export function createMachineView(raw: unknown, config: MachinePresentationConfig): MachineView {
  assertMachineInspectResult(raw);
  const value = raw.value;

  const sourceBlocks = new Map(value.source_evidence.blocks.map((block) => [block.source_block_id, block]));
  const blocks = value.machine_block_diagram.blocks.map((block) => {
    const evidence = block.source_block_ids.map((sourceId) => sourceBlocks.get(sourceId));
    invariant(evidence.every(Boolean), `${block.presentation_block_id} has an unresolved source block`);
    const summaries = evidence.map((item) => item?.summary).filter((item): item is string => Boolean(item));
    const parts = config.blockParts[block.presentation_block_id];
    invariant(Array.isArray(parts) && parts.length > 0, `${block.presentation_block_id} has no explanatory parts`);
    return { ...block, parts: [...parts], summary: summaries.join(" ") };
  });

  const blocksById = new Map(blocks.map((block) => [block.presentation_block_id, block]));
  invariant(blocksById.size === blocks.length, "presentation block IDs must be unique");
  const configuredBlockIds = config.rows.flat();
  invariant(new Set(configuredBlockIds).size === configuredBlockIds.length, "layout rows contain duplicate blocks");
  invariant(configuredBlockIds.length === blocks.length, "layout rows must cover every presentation block exactly once");
  for (const blockId of configuredBlockIds) invariant(blocksById.has(blockId), `layout references unknown block ${blockId}`);

  for (const edge of value.machine_block_diagram.edges) {
    invariant(blocksById.has(edge.source_block_id), `${edge.presentation_edge_id} has an unknown source block`);
    invariant(blocksById.has(edge.destination_block_id), `${edge.presentation_edge_id} has an unknown destination block`);
  }

  const mappingsBySlot = new Map(value.panel.source_mappings.map((mapping) => [mapping.semantic_slot_id, mapping]));
  invariant(mappingsBySlot.size === value.panel.source_mappings.length, "semantic slot mappings must be unique");

  const regionGroups = new Map<string, PhysicalRegionView>();
  const regionsBySlot = new Map<string, PhysicalRegionView>();
  for (const region of value.panel.semantic_regions) {
    // The device profile also exposes raw button/encoder/volume slots. They
    // stay visible in the SVG, but are not interactive machine mappings unless
    // this exact inspection supplies a source mapping for them.
    if (!mappingsBySlot.has(region.semantic_slot_id)) continue;
    let group = regionGroups.get(region.svg_element_id);
    if (!group) {
      group = {
        highlightElementIds: [],
        physicalLabel: region.physical_label,
        semanticSlotIds: [],
        slotKind: region.slot_kind,
        svgElementId: region.svg_element_id,
      };
      regionGroups.set(region.svg_element_id, group);
    }
    invariant(group.slotKind === region.slot_kind, `${region.svg_element_id} mixes incompatible slot kinds`);
    group.semanticSlotIds.push(region.semantic_slot_id);
    if (!group.highlightElementIds.includes(region.highlight_element_id)) {
      group.highlightElementIds.push(region.highlight_element_id);
    }
    regionsBySlot.set(region.semantic_slot_id, group);
  }
  for (const slotId of mappingsBySlot.keys()) {
    invariant(regionsBySlot.has(slotId), `${slotId} source mapping has no semantic panel region`);
  }

  for (const link of value.panel.presentation_links) {
    invariant(mappingsBySlot.has(link.semantic_slot_id), `${link.source_mapping_id} links an unknown slot`);
    invariant(blocksById.has(link.presentation_block_id), `${link.source_mapping_id} links an unknown block`);
    invariant(
      mappingsBySlot.get(link.semantic_slot_id)?.mapping_id === link.source_mapping_id,
      `${link.semantic_slot_id} link does not reference its exact mapping`,
    );
  }

  return {
    blocks,
    blocksById,
    config,
    dependencies: value.dependencies,
    edges: value.machine_block_diagram.edges,
    identity: value.identity,
    inspectionState: value.inspection_state,
    links: value.panel.presentation_links,
    mappingsBySlot,
    panelAsset: value.panel.asset,
    proofBoundary: value.proof_boundary,
    raw,
    recordSetReference: value.record_set_reference,
    regions: [...regionGroups.values()],
    regionsByElement: regionGroups,
    regionsBySlot,
    resources: value.resources,
    rows: config.rows.map((row) => [...row]),
  };
}

export function meaningsForSlots(
  view: MachineView,
  slotIds: readonly string[],
  mode: PerformanceMode,
): ActiveMeaning[] {
  return slotIds.flatMap((slotId) => {
    const mapping = view.mappingsBySlot.get(slotId);
    if (!mapping) return [];
    const meaning = activeMeaning(mapping, mode);
    return meaning ? [meaning] : [];
  });
}

export function blockIdsForSlots(
  view: MachineView,
  slotIds: readonly string[],
  mode: PerformanceMode,
): string[] {
  const wanted = new Set(slotIds);
  return [...new Set(view.links
    .filter((link) => wanted.has(link.semantic_slot_id) && appliesToMode(link.modes, mode))
    .map((link) => link.presentation_block_id))];
}

export function slotIdsForBlock(
  view: MachineView,
  blockId: string,
  mode: PerformanceMode,
): string[] {
  return [...new Set(view.links
    .filter((link) => link.presentation_block_id === blockId && appliesToMode(link.modes, mode))
    .map((link) => link.semantic_slot_id))];
}

export function panelLabelForSlot(
  view: MachineView,
  slotId: string,
  mode: PerformanceMode,
): string {
  const configured = view.config.panelLabels[slotId];
  const label = configured?.[mode] ?? configured?.ALL;
  if (label) return label;
  const meaning = meaningsForSlots(view, [slotId], mode)[0];
  if (meaning) return meaning.meaning;
  return view.regionsBySlot.get(slotId)?.physicalLabel ?? slotId;
}

export function downstreamBlockIds(
  edges: readonly PresentationEdge[],
  startingBlockIds: readonly string[],
): string[] {
  const seen = new Set(startingBlockIds);
  const queue = [...startingBlockIds];
  while (queue.length > 0) {
    const current = queue.shift();
    if (!current) continue;
    for (const edge of edges) {
      if (edge.source_block_id !== current || seen.has(edge.destination_block_id)) continue;
      seen.add(edge.destination_block_id);
      queue.push(edge.destination_block_id);
    }
  }
  return [...seen];
}
