import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { SystemArgs } from '../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';

const PROFILE_COMMANDS: Record<string, string> = {
  cpu: 'stat unit',
  gamethread: 'stat game',
  renderthread: 'stat scenerendering',
  gpu: 'stat gpu',
  memory: 'stat memory',
  fps: 'stat fps',
  all: 'stat unit'
};

export async function handleShowFps(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const enabled = args.enabled !== false;
  await executeAutomationRequest(tools, 'console_command', { command: enabled ? 'stat fps' : 'stat fps 0' });
  return { success: true, message: `FPS display ${enabled ? 'enabled' : 'disabled'}`, action: 'show_fps' };
}

export async function handleProfile(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const rawType = typeof args.profileType === 'string' ? args.profileType.trim() : '';
  const profileKey = rawType ? rawType.toLowerCase() : 'cpu';
  const enabled = args.enabled !== false;
  const command = PROFILE_COMMANDS[profileKey];

  if (!command) {
    return {
      success: false,
      error: 'INVALID_PROFILE_TYPE',
      message: `Unsupported profileType: ${rawType || String(args.profileType ?? '')}`,
      action: 'profile',
      profileType: args.profileType
    };
  }

  await executeAutomationRequest(tools, 'console_command', { command });
  return {
    success: true,
    message: `Profiling ${enabled ? 'enabled' : 'disabled'} (${rawType || 'CPU'})`,
    action: 'profile',
    profileType: rawType || 'CPU'
  };
}

export async function handleShowStats(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const category = typeof args.category === 'string' ? args.category.trim() : 'Unit';
  const enabled = args.enabled !== false;
  await executeAutomationRequest(tools, 'console_command', { command: `stat ${category}` });
  return {
    success: true,
    message: `Stats display ${enabled ? 'enabled' : 'disabled'} for category: ${category}`,
    action: 'show_stats',
    category,
    enabled
  };
}

function toQualityValue(quality: unknown): number {
  if (typeof quality === 'number') {
    return quality;
  }

  const qualityName = String(quality).toLowerCase();
  if (qualityName === 'high' || qualityName === 'epic') return 3;
  if (qualityName === 'low') return 0;
  if (qualityName === 'cinematic') return 4;
  return 1;
}

function qualityCvarForCategory(category: string): string {
  if (category.includes('shadow')) return 'sg.ShadowQuality';
  if (category.includes('texture')) return 'sg.TextureQuality';
  if (category.includes('effect')) return 'sg.EffectsQuality';
  if (category.includes('postprocess')) return 'sg.PostProcessQuality';
  if (category.includes('foliage')) return 'sg.FoliageQuality';
  if (category.includes('shading')) return 'sg.ShadingQuality';
  if (category.includes('globalillumination') || category.includes('gi')) return 'sg.GlobalIlluminationQuality';
  if (category.includes('reflection')) return 'sg.ReflectionQuality';
  return 'sg.ViewDistanceQuality';
}

export async function handleSetQuality(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsRecord = args as Record<string, unknown>;
  const quality = argsRecord.level ?? 'medium';
  const qualityValue = Math.max(0, Math.min(4, toQualityValue(quality)));
  const category = String(args.category || 'ViewDistance').toLowerCase();
  const cvar = qualityCvarForCategory(category);

  await executeAutomationRequest(tools, 'console_command', { command: `${cvar} ${qualityValue}` });
  return {
    success: true,
    message: `${category} quality derived from '${quality}' set to ${qualityValue} via ${cvar}`,
    action: 'set_quality'
  };
}

export async function handleExecuteCommand(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const result = await executeAutomationRequest(tools, 'console_command', { command: args.command ?? '' });
  return cleanObject(result) as Record<string, unknown>;
}

export async function handleSetCvar(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsRecord = args as Record<string, unknown>;
  const nameVal = typeof args.name === 'string' && args.name.trim().length > 0 ? args.name.trim() : '';
  const cvarVal = typeof argsRecord.cvar === 'string' ? argsRecord.cvar.trim() : '';
  const keyVal = typeof args.key === 'string' ? args.key.trim() : '';
  const cmdVal = typeof args.command === 'string' ? args.command.trim() : '';
  const rawInput = nameVal || cvarVal || keyVal || cmdVal;
  const tokens = rawInput.split(/\s+/).filter(Boolean);
  const rawName = tokens[0] ?? '';

  if (!rawName) {
    return {
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'CVar name is required',
      action: 'set_cvar'
    };
  }

  const value = argsRecord.value !== undefined && argsRecord.value !== null
    ? argsRecord.value
    : (tokens.length > 1 ? tokens.slice(1).join(' ') : '');
  await executeAutomationRequest(tools, 'console_command', { command: `${rawName} ${value}` });
  return {
    success: true,
    message: `CVar ${rawName} set to ${value}`,
    action: 'set_cvar',
    cvar: rawName,
    value
  };
}
