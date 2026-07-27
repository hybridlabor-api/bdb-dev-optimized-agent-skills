import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AudioArgs } from '../../../../types/handlers/handler-types.js';
import { TOOL_ACTIONS } from '../../../../utils/commands/action-constants.js';
import { toBoolean, toNumber, toString as toStringValue, toVec3Array, validateAudioParams } from '../../../../utils/validation/type-coercion.js';
import { executeAutomationRequest, requireNonEmptyString } from '../../foundation/dispatch/common-handlers.js';
import { normalizeAudioArgs } from './audio-path-normalization.js';

export async function createSoundCue(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.name, 'name', 'Missing required parameter: name');

  const explicitVolume = toNumber(normalizedArgs.settings?.volume);
  const explicitPitch = toNumber(normalizedArgs.settings?.pitch);
  const validatedAudio = validateAudioParams(explicitVolume, explicitPitch);
  const payload = {
    name: normalizedArgs.name ?? '',
    packagePath: toStringValue(normalizedArgs.savePath ?? normalizedArgs.path) || '/Game/Audio/Cues',
    wavePath: normalizedArgs.wavePath ?? normalizedArgs.soundPath ?? '',
    attenuationPath: toStringValue(normalizedArgs.settings?.attenuationSettings),
    volume: explicitVolume === undefined ? undefined : validatedAudio.volume,
    pitch: explicitPitch === undefined ? undefined : validatedAudio.pitch,
    looping: toBoolean(normalizedArgs.looping ?? normalizedArgs.settings?.looping)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.CREATE_SOUND_CUE, payload)) as Record<string, unknown>;
}

export async function setSoundAttenuation(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.name, 'name', 'Missing required parameter: name');

  const payload = {
    name: normalizedArgs.name ?? '',
    path: toStringValue(normalizedArgs.path ?? normalizedArgs.savePath),
    save: toBoolean(normalizedArgs.save),
    innerRadius: toNumber(normalizedArgs.innerRadius),
    falloffDistance: toNumber(normalizedArgs.falloffDistance),
    attenuationShape: toStringValue(normalizedArgs.attenuationShape),
    falloffMode: toStringValue(normalizedArgs.falloffMode)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.SET_SOUND_ATTENUATION, payload)) as Record<string, unknown>;
}

export async function createSoundClass(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.name, 'name', 'Missing required parameter: name');

  const payload = {
    name: normalizedArgs.name ?? '',
    path: toStringValue(normalizedArgs.path) || '/Game/Audio/Classes',
    parentClass: toStringValue(normalizedArgs.parentClass),
    properties: normalizedArgs.properties
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.CREATE_SOUND_CLASS, payload)) as Record<string, unknown>;
}

export async function createSoundMix(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.name, 'name', 'Missing required parameter: name');

  const payload = {
    name: normalizedArgs.name ?? '',
    path: toStringValue(normalizedArgs.path) || '/Game/Audio/Mixes',
    classAdjusters: normalizedArgs.classAdjusters
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.CREATE_SOUND_MIX, payload)) as Record<string, unknown>;
}

export async function createReverbZone(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.name, 'name', 'Missing required parameter: name');

  const payload = {
    name: normalizedArgs.name ?? '',
    location: toVec3Array(normalizedArgs.location) ?? [0, 0, 0],
    size: toVec3Array(normalizedArgs.size) ?? [0, 0, 0],
    reverbEffect: toStringValue(normalizedArgs.reverbEffect),
    volume: toNumber(normalizedArgs.volume),
    fadeTime: toNumber(normalizedArgs.fadeTime)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.CREATE_REVERB_ZONE, payload)) as Record<string, unknown>;
}
