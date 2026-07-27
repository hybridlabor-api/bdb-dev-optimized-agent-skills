import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { LightingArgs } from '../../../types/handlers/handler-types.js';
import { TOOL_ACTIONS } from '../../../utils/commands/action-constants.js';
import { toBoolean, toColor3, toLocationObj, toNumber, toRotationObj, toString } from '../../../utils/validation/type-coercion.js';
import { executeAutomationRequest, normalizeLocation } from '../foundation/dispatch/common-handlers.js';
import { createSkyLight } from './lighting-sky-actions.js';
import { normalizeLightName } from './lighting-name.js';

const VALID_LIGHT_TYPES = [
  'point', 'directional', 'spot', 'rect', 'sky',
  'pointlight', 'directionallight', 'spotlight', 'rectlight', 'skylight'
];

async function spawnLight(
  tools: ITools,
  lightClass: string,
  params: {
    name: string;
    location?: unknown;
    rotation?: unknown;
    properties?: Record<string, unknown>;
  }
): Promise<Record<string, unknown>> {
  const payload: Record<string, unknown> = {
    lightClass,
    name: params.name
  };

  if (params.location) {
    const locObj = toLocationObj(params.location);
    if (locObj) payload.location = locObj;
  }

  if (params.rotation) {
    const rotObj = toRotationObj(params.rotation);
    if (rotObj) payload.rotation = rotObj;
  }

  if (params.properties) {
    payload.properties = params.properties;
  }

  return await executeAutomationRequest(
    tools,
    TOOL_ACTIONS.SPAWN_LIGHT,
    payload,
    'Automation bridge not available for light spawning'
  ) as Record<string, unknown>;
}

async function createDirectionalLight(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  const name = normalizeLightName(args.name);
  const intensity = toNumber(args.intensity);
  const color = toColor3(args.color);
  const castShadows = toBoolean(args.castShadows);
  const temperature = toNumber(args.temperature);
  const useAsAtmosphereSunLight = toBoolean(args.useAsAtmosphereSunLight);

  if (intensity !== undefined && intensity < 0) {
    return { success: false, isError: true, error: 'Invalid intensity: must be non-negative' };
  }

  const properties: Record<string, unknown> = {};
  if (intensity !== undefined) properties.intensity = intensity;
  if (color) properties.color = { r: color[0], g: color[1], b: color[2], a: 1.0 };
  if (castShadows !== undefined) properties.castShadows = castShadows;
  if (temperature !== undefined) properties.temperature = temperature;
  if (useAsAtmosphereSunLight !== undefined) properties.useAsAtmosphereSunLight = useAsAtmosphereSunLight;

  const result = await spawnLight(tools, 'DirectionalLight', {
    name,
    location: [0, 0, 500],
    rotation: args.rotation || [0, 0, 0],
    properties
  });

  return cleanObject(result);
}

async function createPointLight(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  const name = normalizeLightName(args.name);
  const location = normalizeLocation(args.location) || [0, 0, 0];
  const intensity = toNumber(args.intensity);
  const radius = toNumber(args.radius);
  const color = toColor3(args.color);
  const castShadows = toBoolean(args.castShadows);
  const falloffExponent = toNumber(args.falloffExponent);

  if (intensity !== undefined && intensity < 0) {
    return { success: false, isError: true, error: 'Invalid intensity: must be non-negative' };
  }
  if (radius !== undefined && radius < 0) {
    return { success: false, isError: true, error: 'Invalid radius: must be non-negative' };
  }

  const properties: Record<string, unknown> = {};
  if (intensity !== undefined) properties.intensity = intensity;
  if (radius !== undefined) properties.attenuationRadius = radius;
  if (color) properties.color = { r: color[0], g: color[1], b: color[2], a: 1.0 };
  if (castShadows !== undefined) properties.castShadows = castShadows;
  if (falloffExponent !== undefined) properties.lightFalloffExponent = falloffExponent;

  const result = await spawnLight(tools, 'PointLight', {
    name,
    location,
    rotation: args.rotation,
    properties
  });

  return cleanObject(result);
}

async function createSpotLight(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  const name = normalizeLightName(args.name);
  const location = normalizeLocation(args.location);
  const intensity = toNumber(args.intensity);
  const innerCone = toNumber(args.innerCone);
  const outerCone = toNumber(args.outerCone);
  const radius = toNumber(args.radius);
  const color = toColor3(args.color);
  const castShadows = toBoolean(args.castShadows);

  if (!location) {
    return { success: false, isError: true, error: 'Location is required for spot light' };
  }
  if (intensity !== undefined && intensity < 0) {
    return { success: false, isError: true, error: 'Invalid intensity: must be non-negative' };
  }
  if (innerCone !== undefined && (innerCone < 0 || innerCone > 180)) {
    return { success: false, isError: true, error: 'Invalid innerCone: must be between 0 and 180 degrees' };
  }
  if (outerCone !== undefined && (outerCone < 0 || outerCone > 180)) {
    return { success: false, isError: true, error: 'Invalid outerCone: must be between 0 and 180 degrees' };
  }
  if (radius !== undefined && radius < 0) {
    return { success: false, isError: true, error: 'Invalid radius: must be non-negative' };
  }

  const properties: Record<string, unknown> = {};
  if (intensity !== undefined) properties.intensity = intensity;
  if (innerCone !== undefined) properties.innerConeAngle = innerCone;
  if (outerCone !== undefined) properties.outerConeAngle = outerCone;
  if (radius !== undefined) properties.attenuationRadius = radius;
  if (color) properties.color = { r: color[0], g: color[1], b: color[2], a: 1.0 };
  if (castShadows !== undefined) properties.castShadows = castShadows;

  const result = await spawnLight(tools, 'SpotLight', {
    name,
    location,
    rotation: args.rotation || [0, 0, 0],
    properties
  });

  return cleanObject(result);
}

async function createRectLight(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  const name = normalizeLightName(args.name);
  const location = normalizeLocation(args.location);
  const intensity = toNumber(args.intensity);
  const width = toNumber(args.width);
  const height = toNumber(args.height);
  const color = toColor3(args.color);

  if (!location) {
    return { success: false, isError: true, error: 'Location is required for rect light' };
  }
  if (intensity !== undefined && intensity < 0) {
    return { success: false, isError: true, error: 'Invalid intensity: must be non-negative' };
  }
  if (width !== undefined && width <= 0) {
    return { success: false, isError: true, error: 'Invalid width: must be positive' };
  }
  if (height !== undefined && height <= 0) {
    return { success: false, isError: true, error: 'Invalid height: must be positive' };
  }

  const properties: Record<string, unknown> = {};
  if (intensity !== undefined) properties.intensity = intensity;
  if (color) properties.color = { r: color[0], g: color[1], b: color[2], a: 1.0 };
  if (width !== undefined) properties.sourceWidth = width;
  if (height !== undefined) properties.sourceHeight = height;

  const result = await spawnLight(tools, 'RectLight', {
    name,
    location,
    rotation: args.rotation || [0, 0, 0],
    properties
  });

  return cleanObject(result);
}

export async function createDynamicLight(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  const name = normalizeLightName(args.name);
  const lightTypeRaw = toString(args.lightType) || 'Point';
  const intensity = toNumber(args.intensity);
  const color = toColor3(args.color);
  const typeNorm = lightTypeRaw.toLowerCase();

  switch (typeNorm) {
    case 'directional':
    case 'directionallight':
      return await createDirectionalLight(tools, { ...args, name, intensity, color });
    case 'spot':
    case 'spotlight':
      return await createSpotLight(tools, { ...args, name, intensity, color });
    case 'rect':
    case 'rectlight':
      return await createRectLight(tools, { ...args, name, intensity, color });
    case 'point':
    case 'pointlight':
    default:
      return await createPointLight(tools, { ...args, name, intensity, color });
  }
}

export async function handleSpawnLightAction(tools: ITools, args: LightingArgs): Promise<Record<string, unknown>> {
  let lightType = args.lightType ? String(args.lightType).toLowerCase() : 'point';

  if (lightType.endsWith('light') && lightType !== 'light') {
    lightType = lightType.replace(/light$/, '');
  }

  if (!VALID_LIGHT_TYPES.includes(lightType) && !VALID_LIGHT_TYPES.includes(`${lightType}light`)) {
    return {
      success: false,
      isError: true,
      error: 'INVALID_LIGHT_TYPE',
      message: `Invalid lightType: '${args.lightType}'. Must be one of: point, directional, spot, rect, sky`
    };
  }

  switch (lightType) {
    case 'directional':
      return await createDirectionalLight(tools, args);
    case 'spot':
      return await createSpotLight(tools, args);
    case 'rect':
      return await createRectLight(tools, args);
    case 'sky':
      return await createSkyLight(tools, args);
    default:
      return await createPointLight(tools, args);
  }
}
