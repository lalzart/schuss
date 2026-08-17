import { invoke } from "@tauri-apps/api/core";
import { applicationDescribeRequest, catalogInspectRequest, catalogSearchRequest } from "./requests";
import type {
  ApplicationDescription,
  CatalogFilters,
  CatalogInspectValue,
  CatalogSearchValue,
  ExactFamilyReference,
  OperationResult,
  ReadOnlyRequest,
} from "./types";

const RESULT_SCHEMAS: Record<ReadOnlyRequest["operation"], string> = {
  "application.describe": "schuss-operation-result-v7",
  "catalog.inspect": "schuss-operation-result-v2",
  "catalog.search": "schuss-operation-result-v2",
};

type BridgeErrorShape = {
  error?: { code?: string; message?: string };
  code?: string;
  message?: string;
};

export class CoreOperationError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "CoreOperationError";
    this.code = code;
  }
}

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

function errorFromUnknown(error: unknown): CoreOperationError {
  if (error instanceof CoreOperationError) {
    return error;
  }
  const shaped = error as BridgeErrorShape;
  const code = shaped?.error?.code ?? shaped?.code ?? "BRIDGE_UNAVAILABLE";
  const message =
    shaped?.error?.message ?? shaped?.message ?? "The local Schuss core is unavailable.";
  return new CoreOperationError(code, message);
}

async function transport(request: ReadOnlyRequest): Promise<unknown> {
  if (isTauriRuntime()) {
    return invoke("dispatch_read_only_operation", { request });
  }
  if (import.meta.env.DEV) {
    const response = await fetch("/__schuss/read-only-operation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify(request),
    });
    const body = (await response.json()) as unknown;
    if (!response.ok) {
      throw body;
    }
    return body;
  }
  throw new CoreOperationError(
    "BRIDGE_RUNTIME_REQUIRED",
    "The production catalog renderer requires the Schuss desktop shell.",
  );
}

function assertResult<T, O extends ReadOnlyRequest["operation"]>(
  value: unknown,
  operation: O,
): OperationResult<T, O> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new CoreOperationError("BRIDGE_RESPONSE_INVALID", "Core result must be an object.");
  }
  const result = value as Partial<OperationResult<T, O>>;
  if (
    result.canonical_profile !== "schuss-canonical-json-v1" ||
    result.operation !== operation ||
    result.schema_version !== RESULT_SCHEMAS[operation] ||
    typeof result.status !== "string" ||
    !Array.isArray(result.diagnostics)
  ) {
    throw new CoreOperationError(
      "BRIDGE_RESPONSE_INVALID",
      "Core result metadata does not match the read-only request.",
    );
  }
  return result as OperationResult<T, O>;
}

async function dispatch<T, O extends ReadOnlyRequest["operation"]>(
  request: ReadOnlyRequest & { operation: O },
): Promise<T> {
  try {
    const result = assertResult<T, O>(await transport(request), request.operation);
    if (result.status !== "success" || result.value === null) {
      const diagnostic = result.diagnostics[0];
      throw new CoreOperationError(
        diagnostic?.code ?? "CORE_OPERATION_FAILED",
        diagnostic?.message ?? `Schuss core returned ${result.status}.`,
      );
    }
    return result.value;
  } catch (error) {
    throw errorFromUnknown(error);
  }
}

export function describeApplication(): Promise<ApplicationDescription> {
  return dispatch<ApplicationDescription, "application.describe">(applicationDescribeRequest());
}

export function searchCatalog(
  query: string,
  filters: Partial<CatalogFilters> = {},
): Promise<CatalogSearchValue> {
  return dispatch<CatalogSearchValue, "catalog.search">(catalogSearchRequest(query, filters));
}

export function inspectCatalogFamily(
  reference: ExactFamilyReference,
): Promise<CatalogInspectValue> {
  return dispatch<CatalogInspectValue, "catalog.inspect">(catalogInspectRequest(reference));
}
