const forbiddenAffordances = ["build", "deploy", "edit", "play", "promote"];

export function assertInspectionResult(result) {
  if (!result || result.operation !== "machine.inspect" || result.status !== "success") {
    throw new Error("Machine Viewer requires one successful machine.inspect result");
  }
  const value = result.value;
  if (!value || !["inspection-only", "completed-machine"].includes(value.inspection_state)) {
    throw new Error("machine.inspect result has no recognized inspection state");
  }
  for (const action of forbiddenAffordances) {
    if (value.affordances?.[action] !== false) {
      throw new Error(`machine.inspect must disable ${action}`);
    }
  }
  return value;
}

export function buildViewModel(result) {
  const value = assertInspectionResult(result);
  const blocks = new Map(value.machine_block_diagram.blocks.map((block) => [block.presentation_block_id, block]));
  const sourceBlocks = new Map(value.source_evidence.blocks.map((block) => [block.source_block_id, block]));
  const sourceSpans = new Map(value.source_evidence.spans.map((span) => [span.evidence_span_id, span]));
  const sourceFiles = new Map(value.identity.source_identity.files.map((file) => [file.source_file_id, file]));
  const regions = new Map(value.panel.semantic_regions.map((region) => [region.semantic_slot_id, region]));
  const mappings = new Map(value.panel.source_mappings.map((mapping) => [mapping.semantic_slot_id, mapping]));
  const linksByBlock = new Map();
  for (const link of value.panel.presentation_links) {
    const current = linksByBlock.get(link.presentation_block_id) ?? [];
    current.push(link);
    linksByBlock.set(link.presentation_block_id, current);
  }
  return { value, blocks, sourceBlocks, sourceSpans, sourceFiles, regions, mappings, linksByBlock };
}

export function exactIdentityText(view) {
  const machine = view.value.identity.machine;
  if (machine) return `${machine.machine_id}@${machine.revision} / ${machine.content_hash}`;
  const review = view.value.identity.source_review_reference;
  return `${review.machine_source_review_id}@${review.revision} / ${review.content_hash}`;
}

export function sourceEvidenceForBlock(view, blockId) {
  const block = view.blocks.get(blockId);
  if (!block) return [];
  const labels = [];
  for (const sourceBlockId of block.source_block_ids) {
    const sourceBlock = view.sourceBlocks.get(sourceBlockId);
    for (const spanId of sourceBlock?.evidence_span_ids ?? []) {
      const span = view.sourceSpans.get(spanId);
      const file = span ? view.sourceFiles.get(span.source.source_file_id) : null;
      if (span && file) labels.push(`${file.portable_path}:${span.source.line_start}-${span.source.line_end}`);
    }
  }
  return [...new Set(labels)].sort();
}

export function controlsForBlock(view, blockId) {
  return [...new Set((view.linksByBlock.get(blockId) ?? []).map((link) => link.semantic_slot_id))].sort();
}

export function mappingForControl(view, slotId) {
  const mapping = view.mappings.get(slotId);
  const region = view.regions.get(slotId);
  if (!mapping || !region) return null;
  return { mapping, region };
}

export function highlightElementIdsForSlots(view, slotIds) {
  return [...new Set(slotIds.map((slotId) => view.regions.get(slotId)?.highlight_element_id).filter(Boolean))].sort();
}

export function disabledAffordances(view) {
  return forbiddenAffordances.filter((name) => view.value.affordances[name] === false);
}

function escapeXml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" })[character]);
}

function labelLines(label, limit = 22) {
  const words = String(label).split(/\s+/);
  const lines = [];
  for (const word of words) {
    const candidate = lines.length ? `${lines.at(-1)} ${word}` : word;
    if (!lines.length || candidate.length > limit) lines.push(word);
    else lines[lines.length - 1] = candidate;
  }
  return lines;
}

export function diagramSvg(view, selectedBlockId = null) {
  const blocks = view.value.machine_block_diagram.blocks;
  const edges = view.value.machine_block_diagram.edges;
  const width = Math.max(...blocks.map((block) => block.geometry.x + block.geometry.width)) + 20;
  const height = Math.max(...blocks.map((block) => block.geometry.y + block.geometry.height)) + 28;
  const centers = new Map(blocks.map((block) => [block.presentation_block_id, {
    left: block.geometry.x,
    right: block.geometry.x + block.geometry.width,
    y: block.geometry.y + block.geometry.height / 2,
  }]));
  const edgeMarkup = edges.map((edge) => {
    const source = centers.get(edge.source_block_id);
    const destination = centers.get(edge.destination_block_id);
    return `<path class="diagram-edge ${escapeXml(edge.signal_kind)}" d="M ${source.right} ${source.y} L ${destination.left} ${destination.y}" marker-end="url(#arrow)"/>`;
  }).join("");
  const blockMarkup = blocks.map((block) => {
    const selected = block.presentation_block_id === selectedBlockId ? " selected" : "";
    const centerX = block.geometry.x + block.geometry.width / 2;
    const centerY = block.geometry.y + block.geometry.height / 2;
    const lines = labelLines(block.label);
    const startY = centerY - 13 - ((lines.length - 1) * 7);
    const label = lines.map((line, index) => `<tspan x="${centerX}" y="${startY + index * 14}">${escapeXml(line)}</tspan>`).join("");
    return `<g class="diagram-block${selected}" data-block-id="${escapeXml(block.presentation_block_id)}" role="button" tabindex="0"><rect x="${block.geometry.x}" y="${block.geometry.y}" width="${block.geometry.width}" height="${block.geometry.height}" rx="10"/><text>${label}</text><text class="block-kind" x="${centerX}" y="${centerY + 27}">${escapeXml(block.kind.toUpperCase())}</text></g>`;
  }).join("");
  return `<svg class="machine-diagram" viewBox="0 0 ${width} ${height}" role="img" aria-label="Source-evidenced machine block diagram"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>${edgeMarkup}${blockMarkup}</svg>`;
}
