import { cleanObject } from '../../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { HandlerArgs, LevelArgs } from '../../../../types/handlers/handler-types.js';
import { LONG_RUNNING_OP_TIMEOUT_MS } from '../../../../constants.js';
import { executeAutomationRequest } from '../../foundation/dispatch/common-handlers.js';
import { CREATE_LIGHT_TYPES, LIGHT_TYPE_CLASS_PATHS, normalizeLightType } from './level-handler-utils.js';

export async function handleCreateLight(action: string, argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const lightType = argsTyped.type || argsTyped.lightType;
  if (!lightType || typeof lightType !== 'string' || lightType.trim() === '') {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'Missing required parameter: type (or lightType). Valid types: Point, Directional, Spot, Sky, Rect, PointLight, DirectionalLight, SpotLight, SkyLight, RectLight',
      action
    });
  }

  const normalizedLightType = normalizeLightType(lightType);
  if (!normalizedLightType || !CREATE_LIGHT_TYPES.has(normalizedLightType)) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: `Invalid light type: ${lightType}. Valid types: Point, Directional, Spot, Sky, Rect, PointLight, DirectionalLight, SpotLight, SkyLight, RectLight`,
      action
    });
  }

  const properties: Record<string, unknown> = {};
  if (typeof argsTyped.intensity === 'number') {
    properties.intensity = argsTyped.intensity;
  }
  const color = (argsTyped as Record<string, unknown>).color;
  if (Array.isArray(color) && color.length >= 3) {
    properties.color = {
      r: Number(color[0]),
      g: Number(color[1]),
      b: Number(color[2]),
      a: color.length > 3 ? Number(color[3]) : 1
    };
  } else if (color && typeof color === 'object') {
    properties.color = color;
  }

  const res = await executeAutomationRequest(tools, 'manage_lighting', {
    action: 'create_light',
    lightType,
    name: argsTyped.name,
    location: argsTyped.location,
    rotation: argsTyped.rotation,
    properties: Object.keys(properties).length > 0 ? properties : undefined
  });
  return cleanObject(res) as Record<string, unknown>;
}

export async function handleSpawnLight(args: HandlerArgs, argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const lightType = normalizeLightType(argsTyped.lightType) ?? normalizeLightType((argsTyped as Record<string, unknown>).type) ?? 'point';
  const classPath = LIGHT_TYPE_CLASS_PATHS.get(lightType) || '/Script/Engine.PointLight';

  try {
    const res = await executeAutomationRequest(tools, 'control_actor', {
      action: 'spawn',
      classPath,
      actorName: argsTyped.name,
      location: argsTyped.location,
      rotation: argsTyped.rotation,
      scale: argsTyped.scale
    }) as Record<string, unknown>;
    return { ...cleanObject(res), action: 'spawn_light' };
  } catch (error) {
    if (!(error instanceof Error)) {
      throw error;
    }
    return await executeAutomationRequest(tools, 'manage_level', args) as Record<string, unknown>;
  }
}

export async function handleBuildLighting(args: HandlerArgs, argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsRecord = args as Record<string, unknown>;
  const res = await executeAutomationRequest(tools, 'manage_lighting', {
    action: 'build_lighting',
    quality: (argsTyped.quality as string) || 'Preview',
    buildOnlySelected: typeof argsRecord.buildOnlySelected === 'boolean' ? argsRecord.buildOnlySelected : false,
    buildReflectionCaptures: typeof argsRecord.buildReflectionCaptures === 'boolean' ? argsRecord.buildReflectionCaptures : false,
    timeoutMs: typeof argsTyped.timeoutMs === 'number'
      ? argsTyped.timeoutMs
      : LONG_RUNNING_OP_TIMEOUT_MS
  }) as Record<string, unknown>;
  return cleanObject(res);
}
