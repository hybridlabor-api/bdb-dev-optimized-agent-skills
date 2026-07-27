import type { AutomationResponse } from '../../../types/automation/automation-responses.js';
import type { HandlerArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { TOOL_ACTIONS } from '../../../utils/commands/action-constants.js';
import { sanitizePath } from '../../../utils/paths/path-security.js';
import { ResponseFactory } from '../../../utils/responses/response-factory.js';
import { executeAutomationRequest, normalizePathFields } from '../foundation/dispatch/common-handlers.js';

export type MaterialActionContext = {
  readonly action: string;
  readonly args: HandlerArgs;
  readonly tools: ITools;
};

export type MaterialActionHandler = (context: MaterialActionContext) => Promise<Record<string, unknown>>;

type MaterialPathParts = {
  readonly name: string;
  readonly path: string;
};

export function parseMaterialPath(fullPath: string | undefined): MaterialPathParts | null {
  if (!fullPath) return null;
  const lastSlash = fullPath.lastIndexOf('/');
  if (lastSlash < 0) return { name: fullPath, path: '/Game' };
  const name = fullPath.substring(lastSlash + 1);
  const path = fullPath.substring(0, lastSlash);
  return { name, path };
}

export function normalizeAssetPath(path: string): string {
  const normalized = normalizePathFields({ path }, ['path']).path as string;
  return sanitizePath(normalized);
}

export async function executeMaterialAutomation(
  tools: ITools,
  payload: Record<string, unknown>
): Promise<AutomationResponse> {
  return (await executeAutomationRequest(
    tools,
    TOOL_ACTIONS.MANAGE_MATERIAL_AUTHORING,
    payload
  )) as AutomationResponse;
}

export async function completeMaterialAutomation(
  tools: ITools,
  payload: Record<string, unknown>,
  failureMessage: string,
  successMessage: string
): Promise<Record<string, unknown>> {
  const res = await executeMaterialAutomation(tools, payload);
  if (res.success === false) {
    return ResponseFactory.error(res.error ?? failureMessage, res.errorCode);
  }
  return ResponseFactory.success(res, res.message ?? successMessage);
}

export function promoteNodeId(response: Record<string, unknown>, result: unknown): void {
  if (result && typeof result === 'object' && !Array.isArray(result)) {
    const nodeId = (result as Record<string, unknown>).nodeId;
    if (typeof nodeId === 'string') response.nodeId = nodeId;
  }
}

export function validateCustomExpressionEntries(
  value: unknown,
  fieldName: 'inputs' | 'additionalOutputs',
  actionName: 'add_custom_expression' | 'update_custom_expression'
): Record<string, unknown> | null {
  const errorCode = fieldName === 'inputs' ? 'INVALID_INPUTS' : 'INVALID_OUTPUTS';
  if (value != null && !Array.isArray(value)) {
    return ResponseFactory.error(`manage_material_authoring.${actionName}: ${fieldName} must be an array`, errorCode);
  }
  if (value == null) return null;

  for (let i = 0; i < value.length; i++) {
    const item = value[i];
    if (item === null || typeof item !== 'object' || Array.isArray(item)) {
      return ResponseFactory.error(
        `manage_material_authoring.${actionName}: ${fieldName}[${i}] must be an object with a non-empty string "name"`,
        errorCode
      );
    }
    const record = item as Record<string, unknown>;
    if (typeof record.name !== 'string' || !record.name.trim()) {
      return ResponseFactory.error(
        `manage_material_authoring.${actionName}: ${fieldName}[${i}] must be an object with a non-empty string "name"`,
        errorCode
      );
    }
    if (fieldName === 'additionalOutputs' && record.type != null && typeof record.type !== 'string') {
      return ResponseFactory.error(
        `manage_material_authoring.${actionName}: additionalOutputs[${i}].type must be a string if provided`,
        'INVALID_OUTPUTS'
      );
    }
  }

  return null;
}
