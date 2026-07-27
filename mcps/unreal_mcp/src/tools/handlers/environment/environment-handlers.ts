import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { HandlerArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { executeAutomationRequest, validateArgsSecurity } from '../foundation/dispatch/common-handlers.js';
import { normalizeEnvironmentPathArgs, type EnvironmentArgs } from './environment-handler-utils.js';
import { handleEnvironmentLandscapeAction } from './environment-landscape-actions.js';
import { handleEnvironmentFoliageAction } from './environment-foliage-actions.js';
import { handleEnvironmentProceduralAction } from './environment-procedural-actions.js';
import { handleEnvironmentMiscAction } from './environment-misc-actions.js';

export async function handleEnvironmentTools(action: string, args: HandlerArgs, tools: ITools): Promise<Record<string, unknown>> {
  validateArgsSecurity(args);

  const envAction = String(action || '').toLowerCase();
  const argsRecord = normalizeEnvironmentPathArgs(envAction, args as Record<string, unknown>);
  const argsTyped = argsRecord as EnvironmentArgs;

  const landscapeResult = await handleEnvironmentLandscapeAction(envAction, argsRecord, argsTyped, tools);
  if (landscapeResult !== undefined) return landscapeResult;
  const foliageResult = await handleEnvironmentFoliageAction(envAction, argsRecord, argsTyped, tools);
  if (foliageResult !== undefined) return foliageResult;
  const proceduralResult = await handleEnvironmentProceduralAction(envAction, argsRecord, argsTyped, tools);
  if (proceduralResult !== undefined) return proceduralResult;
  const miscResult = await handleEnvironmentMiscAction(envAction, argsRecord, argsTyped, tools);
  if (miscResult !== undefined) return miscResult;

  const res = await executeAutomationRequest(tools, 'build_environment', argsRecord, 'Automation bridge not available for environment building operations');
  return cleanObject(res) as Record<string, unknown>;
}
