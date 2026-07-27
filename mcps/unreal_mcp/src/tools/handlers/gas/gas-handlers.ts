import type { HandlerArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { createGASActionContext, sendGASRequest, validateGASRequiredFields } from './gas-action-context.js';
import { getGASActionRoute } from './gas-action-routes.js';
import { handleAddTagToAsset, handleCreateGameplayEffect } from './gas-special-actions.js';

export async function handleGASTools(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<Record<string, unknown>> {
  const context = createGASActionContext(args, tools);
  const route = getGASActionRoute(action);

  if (!route) {
    return {
      success: false,
      error: 'UNKNOWN_ACTION',
      message: `Unknown GAS action: ${action}`
    };
  }

  validateGASRequiredFields(context.argsRecord, route.requiredFields);

  if (route.kind === 'create_gameplay_effect') {
    return await handleCreateGameplayEffect(context);
  }
  if (route.kind === 'add_tag_to_asset') {
    return await handleAddTagToAsset(context);
  }

  return await sendGASRequest(context, action, route.blueprintPathParam);
}
