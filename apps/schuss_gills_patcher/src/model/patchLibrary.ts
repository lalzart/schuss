import { catalogItemByFamily } from "./catalog";
import type { MachineKey, PerformanceMode } from "./types";

export const LOCAL_PATCH_LIBRARY_SCHEMA = "schuss-gills-local-patch-library-v1";
export const LOCAL_PATCH_LIBRARY_STORAGE_KEY = "schuss.gillsPatcher.localLibrary.v1";

export const REFERENCE_NODE_IDS = [
  "gills-input-rack",
  "instrument-compound",
  "gills-output-rack",
] as const;

export type ReferenceNodeId = (typeof REFERENCE_NODE_IDS)[number];

export interface PatchPosition {
  x: number;
  y: number;
}

export interface CatalogNodePlacement {
  familyId: string;
  localIndex: number;
  position: PatchPosition;
}

export interface PatchSnapshot {
  machineKey: MachineKey;
  mode: PerformanceMode;
  referencePositions: Record<ReferenceNodeId, PatchPosition>;
  catalogNodes: CatalogNodePlacement[];
}

export interface SavedLocalPatch extends PatchSnapshot {
  patchId: string;
  name: string;
}

export interface LocalPatchLibrary {
  schemaVersion: typeof LOCAL_PATCH_LIBRARY_SCHEMA;
  patches: SavedLocalPatch[];
}

export interface LocalPatchLibraryDecodeResult {
  library: LocalPatchLibrary;
  warnings: string[];
}

const MAX_PATCH_NAME_LENGTH = 80;
const MAX_PATCHES = 64;
const MAX_CATALOG_NODES = 100;
const MAX_POSITION_MAGNITUDE = 100_000;
const FAMILY_ID_PATTERN = /^schuss-family-[0-9]{6}$/;
const LOCAL_PATCH_ID_PATTERN = /^local-patch-[0-9a-z-]{8,}$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isMachineKey(value: unknown): value is MachineKey {
  return value === "tide-pit" || value === "palimpsest";
}

function isMode(value: unknown): value is PerformanceMode {
  return value === "clean" || value === "filter" || value === "drive";
}

function parsePosition(value: unknown): PatchPosition | null {
  if (!isRecord(value)) return null;
  const { x, y } = value;
  if (
    typeof x !== "number"
    || typeof y !== "number"
    || !Number.isFinite(x)
    || !Number.isFinite(y)
    || Math.abs(x) > MAX_POSITION_MAGNITUDE
    || Math.abs(y) > MAX_POSITION_MAGNITUDE
  ) return null;
  return { x, y };
}

export function normalizePatchName(value: string): string {
  return value.replace(/\s+/g, " ").trim().slice(0, MAX_PATCH_NAME_LENGTH);
}

function parseReferencePositions(
  value: unknown,
): Record<ReferenceNodeId, PatchPosition> | null {
  if (!isRecord(value)) return null;
  const entries = REFERENCE_NODE_IDS.map((nodeId) => {
    const position = parsePosition(value[nodeId]);
    return position === null ? null : [nodeId, position] as const;
  });
  if (entries.some((entry) => entry === null)) return null;
  return Object.fromEntries(entries as Array<readonly [ReferenceNodeId, PatchPosition]>) as Record<
    ReferenceNodeId,
    PatchPosition
  >;
}

function parseCatalogNodes(value: unknown): CatalogNodePlacement[] | null {
  if (!Array.isArray(value) || value.length > MAX_CATALOG_NODES) return null;
  const seenIndices = new Set<number>();
  const placements: CatalogNodePlacement[] = [];
  for (const entry of value) {
    if (!isRecord(entry)) return null;
    const { familyId, localIndex } = entry;
    const position = parsePosition(entry.position);
    if (
      typeof familyId !== "string"
      || !FAMILY_ID_PATTERN.test(familyId)
      || catalogItemByFamily(familyId)?.selectable !== true
      || typeof localIndex !== "number"
      || !Number.isSafeInteger(localIndex)
      || localIndex < 1
      || seenIndices.has(localIndex)
      || position === null
    ) return null;
    seenIndices.add(localIndex);
    placements.push({ familyId, localIndex, position });
  }
  return placements.toSorted((left, right) => left.localIndex - right.localIndex);
}

function parseSavedPatch(value: unknown): SavedLocalPatch | null {
  if (!isRecord(value)) return null;
  const { machineKey, mode, name, patchId } = value;
  const referencePositions = parseReferencePositions(value.referencePositions);
  const catalogNodes = parseCatalogNodes(value.catalogNodes);
  if (
    typeof patchId !== "string"
    || !LOCAL_PATCH_ID_PATTERN.test(patchId)
    || typeof name !== "string"
    || normalizePatchName(name) !== name
    || name.length === 0
    || !isMachineKey(machineKey)
    || !isMode(mode)
    || referencePositions === null
    || catalogNodes === null
  ) return null;
  return {
    catalogNodes,
    machineKey,
    mode,
    name,
    patchId,
    referencePositions,
  };
}

export function emptyPatchLibrary(): LocalPatchLibrary {
  return { patches: [], schemaVersion: LOCAL_PATCH_LIBRARY_SCHEMA };
}

export function decodePatchLibrary(raw: string | null): LocalPatchLibraryDecodeResult {
  if (raw === null || raw.trim().length === 0) {
    return { library: emptyPatchLibrary(), warnings: [] };
  }

  let decoded: unknown;
  try {
    decoded = JSON.parse(raw) as unknown;
  } catch {
    return {
      library: emptyPatchLibrary(),
      warnings: ["The local patch library was not valid JSON and was ignored."],
    };
  }

  if (
    !isRecord(decoded)
    || decoded.schemaVersion !== LOCAL_PATCH_LIBRARY_SCHEMA
    || !Array.isArray(decoded.patches)
  ) {
    return {
      library: emptyPatchLibrary(),
      warnings: ["The local patch library schema was unsupported and was ignored."],
    };
  }

  const warnings: string[] = [];
  const patches: SavedLocalPatch[] = [];
  const seenPatchIds = new Set<string>();
  for (const [index, value] of decoded.patches.slice(0, MAX_PATCHES).entries()) {
    const patch = parseSavedPatch(value);
    if (patch === null || seenPatchIds.has(patch.patchId)) {
      warnings.push(`Local patch record ${index + 1} was malformed or duplicated and was ignored.`);
      continue;
    }
    seenPatchIds.add(patch.patchId);
    patches.push(patch);
  }
  if (decoded.patches.length > MAX_PATCHES) {
    warnings.push(`Only the first ${MAX_PATCHES} local patch records were inspected.`);
  }

  return {
    library: {
      patches: sortSavedPatches(patches),
      schemaVersion: LOCAL_PATCH_LIBRARY_SCHEMA,
    },
    warnings,
  };
}

export function sortSavedPatches(patches: readonly SavedLocalPatch[]): SavedLocalPatch[] {
  return patches.toSorted((left, right) => (
    left.name.localeCompare(right.name, undefined, { sensitivity: "base" })
    || left.patchId.localeCompare(right.patchId)
  ));
}

function normalizeSnapshot(snapshot: PatchSnapshot): PatchSnapshot {
  return {
    catalogNodes: snapshot.catalogNodes
      .map((entry) => ({
        familyId: entry.familyId,
        localIndex: entry.localIndex,
        position: { ...entry.position },
      }))
      .toSorted((left, right) => left.localIndex - right.localIndex),
    machineKey: snapshot.machineKey,
    mode: snapshot.mode,
    referencePositions: Object.fromEntries(
      REFERENCE_NODE_IDS.map((nodeId) => [nodeId, { ...snapshot.referencePositions[nodeId] }]),
    ) as Record<ReferenceNodeId, PatchPosition>,
  };
}

export function upsertLocalPatch(
  library: LocalPatchLibrary,
  snapshot: PatchSnapshot,
  requestedName: string,
  existingPatchId: string | null,
  createId: () => string,
): { library: LocalPatchLibrary; patch: SavedLocalPatch } {
  const name = normalizePatchName(requestedName);
  if (name.length === 0) throw new Error("Patch name is required.");
  const existing = existingPatchId === null
    ? undefined
    : library.patches.find((patch) => patch.patchId === existingPatchId);
  const patchId = existing?.patchId ?? createId();
  if (!LOCAL_PATCH_ID_PATTERN.test(patchId)) throw new Error("Generated local patch ID was invalid.");

  const patch: SavedLocalPatch = {
    ...normalizeSnapshot(snapshot),
    name,
    patchId,
  };
  const patches = existing === undefined
    ? [...library.patches, patch]
    : library.patches.map((entry) => entry.patchId === patchId ? patch : entry);
  return {
    library: { patches: sortSavedPatches(patches), schemaVersion: LOCAL_PATCH_LIBRARY_SCHEMA },
    patch,
  };
}

export function deleteLocalPatch(
  library: LocalPatchLibrary,
  patchId: string,
): LocalPatchLibrary {
  return {
    patches: library.patches.filter((patch) => patch.patchId !== patchId),
    schemaVersion: LOCAL_PATCH_LIBRARY_SCHEMA,
  };
}

export function encodePatchLibrary(library: LocalPatchLibrary): string {
  const normalized: LocalPatchLibrary = {
    patches: sortSavedPatches(library.patches).map((patch) => ({
      ...normalizeSnapshot(patch),
      name: patch.name,
      patchId: patch.patchId,
    })),
    schemaVersion: LOCAL_PATCH_LIBRARY_SCHEMA,
  };
  return JSON.stringify(normalized);
}

export function searchSavedPatches(
  patches: readonly SavedLocalPatch[],
  query: string,
): SavedLocalPatch[] {
  const normalizedQuery = query.trim().toLocaleLowerCase();
  if (normalizedQuery.length === 0) return [...patches];
  return patches.filter((patch) => (
    `${patch.name} ${patch.machineKey} ${patch.mode}`
      .toLocaleLowerCase()
      .includes(normalizedQuery)
  ));
}

export function createLocalPatchId(): string {
  return `local-patch-${crypto.randomUUID()}`;
}
