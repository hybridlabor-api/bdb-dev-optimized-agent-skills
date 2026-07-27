import type { HandlerArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { createSubActionDispatcher, requireNonEmptyString } from '../foundation/dispatch/common-handlers.js';
import type { SubActionDispatcher } from '../foundation/dispatch/common-handlers.js';
import { normalizeGASPayloadForBridge } from './gas-payload-normalization.js';

export type GASActionContext = {
  readonly argsRecord: Record<string, unknown>;
  readonly sendSubAction: SubActionDispatcher['sendRequest'];
};

export function createGASActionContext(args: HandlerArgs, tools: ITools): GASActionContext {
  const { argsRecord, sendRequest } = createSubActionDispatcher(tools, args, {
    toolName: 'manage_gas',
    domainName: 'GAS',
    pathFields: [
      'blueprintPath',
      'attributeSetPath',
      'abilityPath',
      'effectPath',
      'cuePath',
      'assetPath',
      'costEffectPath',
      'cooldownEffectPath',
      'decalPath',
      'path'
    ],
    preparePayload: normalizeGASPayloadForBridge
  });

  return { argsRecord, sendSubAction: sendRequest };
}

export function validateGASRequiredFields(
  argsRecord: Record<string, unknown>,
  fieldNames: readonly string[]
): void {
  for (const fieldName of fieldNames) {
    requireNonEmptyString(argsRecord[fieldName], fieldName, `Missing required parameter: ${fieldName}`);
  }
}

export async function sendGASRequest(
  context: GASActionContext,
  subAction: string,
  blueprintPathParam?: string
): Promise<Record<string, unknown>> {
  const extraPayload = blueprintPathParam && typeof context.argsRecord[blueprintPathParam] === 'string'
    ? { blueprintPath: context.argsRecord[blueprintPathParam] }
    : undefined;
  return await context.sendSubAction(subAction, extraPayload);
}
