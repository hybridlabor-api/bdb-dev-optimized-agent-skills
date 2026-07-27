import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { LightingArgs } from '../../../types/handlers/handler-types.js';
import { TOOL_ACTIONS } from '../../../utils/commands/action-constants.js';
import { toBoolean, toColor3, toNumber, toString } from '../../../utils/validation/type-coercion.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import { normalizeLightName } from './lighting-name.js';

export async function createSkyLight(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  const name = normalizeLightName(args.name);
  const sourceType = toString(args.sourceType) || 'CapturedScene';
  const cubemapPath = toString(args.cubemapPath);
  const intensity = toNumber(args.intensity);
  const recapture = toBoolean(args.recapture);
  const realTimeCapture = toBoolean(args.realTimeCapture);
  const castShadows = toBoolean(args.castShadows);
  const color = toColor3(args.color);

  if (sourceType === 'SpecifiedCubemap' && !cubemapPath) {
    return { success: false, isError: true, error: 'cubemapPath is required when sourceType is SpecifiedCubemap' };
  }

  const payload: Record<string, unknown> = {
    name,
    sourceType,
    location: args.location,
    rotation: args.rotation
  };

  if (cubemapPath) payload.cubemapPath = cubemapPath;
  if (intensity !== undefined) payload.intensity = intensity;
  if (recapture !== undefined) payload.recapture = recapture;

  const properties: Record<string, unknown> = {};
  if (intensity !== undefined) properties.Intensity = intensity;
  if (castShadows !== undefined) properties.CastShadows = castShadows;
  if (realTimeCapture !== undefined) properties.RealTimeCapture = realTimeCapture;
  if (color) properties.LightColor = { r: color[0], g: color[1], b: color[2], a: 1.0 };

  if (Object.keys(properties).length > 0) payload.properties = properties;

  return await executeAutomationRequest(
    tools,
    TOOL_ACTIONS.SPAWN_SKY_LIGHT,
    payload,
    'Automation bridge not available for sky light creation'
  ) as Record<string, unknown>;
}

export async function ensureSingleSkyLight(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  const defaultName = 'MCP_Test_Sky';
  const name = normalizeLightName(args.name, defaultName);
  const recapture = args.recapture !== false;

  return await executeAutomationRequest(
    tools,
    TOOL_ACTIONS.ENSURE_SINGLE_SKY_LIGHT,
    { name, recapture },
    'Automation bridge not available for sky light management'
  ) as Record<string, unknown>;
}
