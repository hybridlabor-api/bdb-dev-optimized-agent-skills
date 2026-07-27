import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { HandlerArgs, EffectArgs, AutomationResponse } from '../../../types/handlers/handler-types.js';
import { cleanObject } from '../../../utils/serialization/safe-json.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import {
  applyEffectArgumentAliases,
  ensureActionAndSubAction,
  sanitizeEffectPaths
} from './effect-argument-normalization.js';
import { handleEffectAssetAction } from './effect-asset-actions.js';
import { handleEffectAuthoringAction, handleEffectGraphAction } from './effect-niagara-actions.js';
import {
  applyParticlePreset,
  handleEffectCleanupAction,
  handleEffectCreateAction,
  handleEffectDebugShapeAction,
  handleEffectNiagaraSpawnAction,
  handleEffectParameterAction,
  handleEffectSimulationAction,
  prepareDynamicLightAction
} from './effect-routing-actions.js';

interface ResultPayload {
  error?: string;
  message?: string;
}

export async function handleEffectTools(action: string, args: HandlerArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsTyped = args as EffectArgs;
  const mutableArgs = { ...args } as Record<string, unknown>;

  ensureActionAndSubAction(action, mutableArgs);
  sanitizeEffectPaths(mutableArgs);
  applyEffectArgumentAliases(mutableArgs, argsTyped);

  const effectiveSystemPath = mutableArgs.systemPath as string | undefined;

  const assetResult = await handleEffectAssetAction(action, argsTyped, mutableArgs, effectiveSystemPath, tools);
  if (assetResult !== undefined) {
    return assetResult;
  }

  applyParticlePreset(argsTyped, mutableArgs);

  const debugShapeResult = await handleEffectDebugShapeAction(action, argsTyped, mutableArgs, tools);
  if (debugShapeResult !== undefined) {
    return debugShapeResult;
  }

  prepareDynamicLightAction(action, mutableArgs);

  const cleanupResult = await handleEffectCleanupAction(action, mutableArgs, tools);
  if (cleanupResult !== undefined) {
    return cleanupResult;
  }

  const createResult = await handleEffectCreateAction(action, mutableArgs, tools);
  if (createResult !== undefined) {
    return createResult;
  }

  const simulationResult = await handleEffectSimulationAction(action, mutableArgs, tools);
  if (simulationResult !== undefined) {
    return simulationResult;
  }

  const parameterResult = await handleEffectParameterAction(action, mutableArgs, tools);
  if (parameterResult !== undefined) {
    return parameterResult;
  }

  const graphResult = await handleEffectGraphAction(action, mutableArgs, tools);
  if (graphResult !== undefined) {
    return graphResult;
  }

  const authoringResult = await handleEffectAuthoringAction(action, mutableArgs, tools);
  if (authoringResult !== undefined) {
    return authoringResult;
  }

  const niagaraResult = await handleEffectNiagaraSpawnAction(action, mutableArgs, tools);
  if (niagaraResult !== undefined) {
    return niagaraResult;
  }

  const res = await executeAutomationRequest(
    tools,
    'create_effect',
    mutableArgs,
    'Automation bridge not available for effect creation operations'
  ) as AutomationResponse;

  const result = (res?.result ?? res ?? {}) as ResultPayload;

  const topError = typeof res?.error === 'string' ? res.error : '';
  const nestedError = typeof result.error === 'string' ? result.error : '';
  const errorCode = (topError || nestedError).toUpperCase();

  const topMessage = typeof res?.message === 'string' ? res.message : '';
  const nestedMessage = typeof result.message === 'string' ? result.message : '';
  const message = topMessage || nestedMessage || '';

  const combined = `${topError} ${nestedError} ${message}`.toLowerCase();

  if (
    (action === 'niagara' || action === 'spawn_niagara') &&
    (
      errorCode === 'SYSTEM_NOT_FOUND' ||
      combined.includes('niagara system not found') ||
      combined.includes('system asset not found')
    )
  ) {
    return cleanObject({
      success: false,
      error: 'SYSTEM_NOT_FOUND',
      message: message || 'Niagara system not found',
      systemPath: effectiveSystemPath,
      handled: true
    });
  }

  return cleanObject(res) as Record<string, unknown>;
}
