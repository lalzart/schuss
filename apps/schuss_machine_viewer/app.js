import {
  buildViewModel,
  controlsForBlock,
  diagramSvg,
  exactIdentityText,
  highlightElementIdsForSlots,
  mappingForControl,
  sourceEvidenceForBlock,
} from "./viewer.js";

const fixtureRoot = "fixtures/";
const viewerRoot = document.querySelector("#viewer");
const picker = document.querySelector("#machine-select");
const requestedMachine = new URLSearchParams(window.location.search).get("machine");
if (requestedMachine === "tide-pit") picker.value = "tide-pit-machine-inspect.json";
if (requestedMachine === "palimpsest") picker.value = "palimpsest-machine-inspect.json";
let view = null;
let selectedBlockId = null;
let panelDocument = null;

function text(id, value) {
  document.querySelector(id).textContent = value;
}

function clearHighlights() {
  if (!panelDocument) return;
  for (const element of panelDocument.querySelectorAll(".is-highlighted")) element.classList.remove("is-highlighted");
}

function highlightSlots(slotIds) {
  clearHighlights();
  for (const id of highlightElementIdsForSlots(view, slotIds)) panelDocument?.getElementById(id)?.classList.add("is-highlighted");
}

function renderControl(slotId) {
  const detail = mappingForControl(view, slotId);
  const target = document.querySelector("#control-detail");
  if (!detail) {
    target.innerHTML = "<p>No exact mapping is available for this region.</p>";
    return;
  }
  const { mapping, region } = detail;
  target.replaceChildren();
  const heading = document.createElement("h4");
  heading.textContent = region.physical_label;
  const code = document.createElement("code");
  code.textContent = slotId;
  const state = document.createElement("span");
  state.className = `badge ${mapping.mapping_state === "mapped" ? "ok" : "warning"}`;
  state.textContent = mapping.mapping_state;
  const list = document.createElement("ul");
  for (const meaning of mapping.meanings) {
    const item = document.createElement("li");
    const mode = document.createElement("strong");
    mode.textContent = meaning.mode;
    item.append(mode, ` — ${meaning.meaning}`);
    list.append(item);
  }
  target.append(heading, code, state, list);
  highlightSlots([slotId]);
}

function bindPanel() {
  const object = document.querySelector("#panel-object");
  object.addEventListener("load", () => {
    panelDocument = object.contentDocument;
    if (!panelDocument) return;
    const byElement = new Map();
    for (const region of view.value.panel.semantic_regions) {
      const current = byElement.get(region.svg_element_id) ?? [];
      current.push(region.semantic_slot_id);
      byElement.set(region.svg_element_id, current);
    }
    for (const [elementId, slotIds] of byElement) {
      const element = panelDocument.getElementById(elementId);
      if (!element) continue;
      element.addEventListener("click", () => {
        const mapped = slotIds.find((slotId) => view.mappings.get(slotId)?.mapping_state === "mapped") ?? slotIds[0];
        renderControl(mapped);
      });
    }
    if (selectedBlockId) highlightSlots(controlsForBlock(view, selectedBlockId));
  });
}

function selectBlock(blockId) {
  selectedBlockId = blockId;
  const block = view.blocks.get(blockId);
  const slots = controlsForBlock(view, blockId);
  document.querySelector("#diagram").innerHTML = diagramSvg(view, blockId);
  bindBlocks();
  highlightSlots(slots);
  const detail = document.querySelector("#block-detail");
  const evidence = sourceEvidenceForBlock(view, blockId);
  detail.textContent = `${block.label}: ${slots.length} mapped panel slot${slots.length === 1 ? "" : "s"}. Source evidence: ${evidence.join(", ") || "unresolved"}. Authoritative graph traces: ${block.graph_node_references.length ? block.graph_node_references.length : "none (inspection-only)"}.`;
}

function bindBlocks() {
  for (const element of document.querySelectorAll("[data-block-id]")) {
    const activate = () => selectBlock(element.dataset.blockId);
    element.addEventListener("click", activate);
    element.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activate(); }
    });
  }
}

function renderDependencies() {
  const body = document.querySelector("#dependencies");
  body.replaceChildren();
  for (const dependency of view.value.dependencies) {
    const row = document.createElement("tr");
    const label = document.createElement("td");
    const name = document.createElement("strong");
    name.textContent = dependency.label;
    const required = document.createElement("small");
    required.textContent = dependency.required ? "required" : "explicit non-dependency";
    label.append(name, required);
    const classification = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `badge ${["selectable", "accepted-support", "non-object", "private-helper"].includes(dependency.classification) ? "" : "warning"}`;
    badge.textContent = dependency.classification;
    classification.append(badge);
    const evidence = document.createElement("td");
    evidence.textContent = `L${dependency.evidence_level} ${dependency.evidence_status}. ${dependency.reason}`;
    const gap = document.createElement("td");
    gap.textContent = dependency.first_proof_gap;
    row.append(label, classification, evidence, gap);
    body.append(row);
  }
}

function renderTraceIndex() {
  const list = document.querySelector("#trace-index");
  list.replaceChildren();
  for (const edge of view.value.source_evidence.edges) {
    const item = document.createElement("li");
    const spans = edge.evidence_span_ids.map((spanId) => {
      const span = view.sourceSpans.get(spanId);
      const file = span ? view.sourceFiles.get(span.source.source_file_id) : null;
      return span && file ? `${file.portable_path}:${span.source.line_start}-${span.source.line_end}` : "unresolved";
    });
    item.textContent = `${edge.source_edge_id}: ${edge.summary} — ${[...new Set(spans)].sort().join(", ")}`;
    list.append(item);
  }
}

function render(result) {
  view = buildViewModel(result);
  selectedBlockId = null;
  panelDocument = null;
  viewerRoot.replaceChildren(document.querySelector("#viewer-template").content.cloneNode(true));
  text("#machine-name", view.value.identity.display_name);
  text("#machine-summary", view.value.identity.summary);
  text("#inspection-badge", view.value.inspection_state);
  text("#exact-identity", exactIdentityText(view));
  const source = view.value.identity.source_identity;
  text("#source-provenance", `${source.repository_url} @ ${source.commit} / ${source.project_root}`);
  text("#proof-badge", "Level 1 structural / Levels 2–8 not run");
  document.querySelector("#diagram").innerHTML = diagramSvg(view);
  bindBlocks();
  renderTraceIndex();
  const panelObject = document.querySelector("#panel-object");
  panelObject.data = `../../${view.value.panel.asset.portable_path}`;
  bindPanel();
  const bytes = view.value.resources.source_declared_bytes;
  text("#resource-summary", bytes ? `${bytes.toLocaleString()} source-declared bytes; not measured.` : "Fixed source structures; no measured resource claim.");
  renderDependencies();
}

async function loadFixture(name) {
  viewerRoot.innerHTML = '<p class="loading">Loading exact machine inspection…</p>';
  const response = await fetch(fixtureRoot + name, { cache: "no-store" });
  if (!response.ok) throw new Error(`fixture request failed: ${response.status}`);
  render(await response.json());
}

picker.addEventListener("change", () => loadFixture(picker.value).catch(showError));

function showError(error) {
  viewerRoot.textContent = `Machine Viewer failed closed: ${error.message}`;
}

loadFixture(picker.value).catch(showError);
