import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { BlueprintArgs, HandlerArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';

export type BlueprintActionContext = {
  readonly argsTyped: BlueprintArgs;
  readonly argsRecord: Record<string, unknown>;
  readonly tools: ITools;
};

export type BlueprintActionHandler = (context: BlueprintActionContext) => Promise<Record<string, unknown>>;

type BlueprintContextResult =
  | { readonly kind: 'ok'; readonly context: BlueprintActionContext }
  | { readonly kind: 'blocked'; readonly response: Record<string, unknown> };

export function createBlueprintContext(args: HandlerArgs, tools: ITools): BlueprintContextResult {
  const normalizedArgs: HandlerArgs = { ...args };
  const argsTyped: BlueprintArgs = normalizedArgs;
  const argsRecord: Record<string, unknown> = normalizedArgs;

  argsTyped.blueprintPath = normalizeBlueprintPath(argsTyped.blueprintPath);
  argsRecord.path = normalizeOptionalPath(argsRecord.path);
  argsRecord.assetPath = normalizeOptionalPath(argsRecord.assetPath);

  if (isUnsafePath(argsTyped.blueprintPath) || isUnsafePath(argsRecord.path) || isUnsafePath(argsRecord.assetPath)) {
    return {
      kind: 'blocked',
      response: cleanRecord({
        success: false,
        error: 'INVALID_BLUEPRINT_PATH',
        message: 'Blueprint path blocked for security: traversal segments detected'
      })
    };
  }

  return { kind: 'ok', context: { argsTyped, argsRecord, tools } };
}

export async function executeBlueprintRequest(
  context: BlueprintActionContext,
  toolName: string,
  payload: HandlerArgs,
  errorMessage?: string
): Promise<Record<string, unknown>> {
  return cleanRecord(await executeAutomationRequest(context.tools, toolName, payload, errorMessage));
}

export function cleanRecord(value: unknown): Record<string, unknown> {
  const cleaned = cleanObject(value);
  if (cleaned !== null && typeof cleaned === 'object' && !Array.isArray(cleaned)) {
    const record: Record<string, unknown> = {};
    for (const [key, entry] of Object.entries(cleaned)) {
      record[key] = entry;
    }
    return record;
  }
  return {};
}

export function blueprintTarget(context: BlueprintActionContext): string {
  return firstString(context.argsTyped.name, context.argsTyped.blueprintPath, context.argsRecord.path) ?? '';
}

export function blueprintCandidates(context: BlueprintActionContext): readonly string[] {
  return [blueprintTarget(context)];
}

export function optionalString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined;
}

export function optionalNumber(value: unknown): number | undefined {
  return typeof value === 'number' ? value : undefined;
}

export function optionalBoolean(value: unknown): boolean | undefined {
  return typeof value === 'boolean' ? value : undefined;
}

export function optionalObject(value: unknown): object | undefined {
  return value !== null && typeof value === 'object' ? value : undefined;
}

export function firstString(...values: readonly unknown[]): string | undefined {
  for (const value of values) {
    if (typeof value === 'string' && value.length > 0) {
      return value;
    }
  }
  return undefined;
}

export function commonTimingPayload(context: BlueprintActionContext): Record<string, unknown> {
  return {
    timeoutMs: optionalNumber(context.argsRecord.timeoutMs),
    waitForCompletion: optionalBoolean(context.argsRecord.waitForCompletion),
    waitForCompletionTimeoutMs: optionalNumber(context.argsRecord.waitForCompletionTimeoutMs)
  };
}

function normalizeOptionalPath(value: unknown): unknown {
  return typeof value === 'string' ? normalizeBlueprintPath(value) : value;
}

function normalizeBlueprintPath(path: string | undefined): string | undefined {
  if (!path) {
    return path;
  }

  let normalized = path.replace(/\\/g, '/');
  while (normalized.includes('//')) {
    normalized = normalized.replace(/\/\//g, '/');
  }
  return normalized;
}

function isUnsafePath(value: unknown): boolean {
  return typeof value === 'string' && value.split('/').some((segment) => segment === '..');
}
