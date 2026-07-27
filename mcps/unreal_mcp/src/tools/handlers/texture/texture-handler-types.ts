import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { HandlerArgs } from '../../../types/handlers/handler-types.js';
import type { AutomationResponse } from '../../../types/automation/automation-responses.js';
import type { ArgConfig } from '../foundation/arguments/argument-helper.js';
import { normalizeArgs } from '../foundation/arguments/argument-helper.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import { ResponseFactory } from '../../../utils/responses/response-factory.js';
import { TOOL_ACTIONS } from '../../../utils/commands/action-constants.js';

export interface TextureHandlerContext {
  readonly args: HandlerArgs;
  readonly tools: ITools;
}

export interface BuiltTextureAction {
  readonly payload: Record<string, unknown>;
  readonly successMessage: string;
}

export interface TextureActionConfig {
  readonly subAction: string;
  readonly params: ArgConfig[];
  readonly failureMessage: string;
  readonly build: (params: Record<string, unknown>) => BuiltTextureAction;
}

export interface TextureAssetNameAndPath {
  readonly name: string;
  readonly path: string;
}

export function createTextureContext(args: HandlerArgs, tools: ITools): TextureHandlerContext {
  return { args, tools };
}

export function splitTextureAssetPath(assetPath: string, fallbackPath: string): TextureAssetNameAndPath {
  const lastSlash = assetPath.lastIndexOf('/');
  if (lastSlash >= 0) {
    return {
      name: assetPath.substring(lastSlash + 1),
      path: assetPath.substring(0, lastSlash)
    };
  }
  return { name: assetPath, path: fallbackPath };
}

export async function sendTextureRequest(
  context: TextureHandlerContext,
  payload: Record<string, unknown>,
  failureMessage: string,
  successMessage: string
): Promise<Record<string, unknown>> {
  const res = await executeAutomationRequest(
    context.tools,
    TOOL_ACTIONS.MANAGE_TEXTURE,
    payload
  ) as AutomationResponse;

  if (res.success === false) {
    return ResponseFactory.error(res.error ?? failureMessage, res.errorCode);
  }
  return ResponseFactory.success(res, res.message ?? successMessage);
}

export async function runTextureAction(
  context: TextureHandlerContext,
  config: TextureActionConfig
): Promise<Record<string, unknown>> {
  const params = normalizeArgs(context.args, config.params);
  const built = config.build(params);
  return await sendTextureRequest(
    context,
    { subAction: config.subAction, ...built.payload },
    config.failureMessage,
    built.successMessage
  );
}
