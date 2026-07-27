import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AudioArgs } from '../../../../types/handlers/handler-types.js';
import { TOOL_ACTIONS } from '../../../../utils/commands/action-constants.js';
import { toBoolean, toNumber, toString as toStringValue, toRotArray, toVec3Array, validateAudioParams } from '../../../../utils/validation/type-coercion.js';
import { executeAutomationRequest, requireNonEmptyString } from '../../foundation/dispatch/common-handlers.js';
import { normalizeAudioArgs } from './audio-path-normalization.js';

export async function playSoundAtLocation(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.soundPath, 'soundPath', 'Missing required parameter: soundPath');

  const { volume, pitch } = validateAudioParams(toNumber(normalizedArgs.volume), toNumber(normalizedArgs.pitch));
  const payload = {
    soundPath: normalizedArgs.soundPath ?? '',
    location: toVec3Array(normalizedArgs.location) ?? [0, 0, 0],
    rotation: toRotArray(normalizedArgs.rotation) ?? [0, 0, 0],
    volume,
    pitch,
    startTime: toNumber(normalizedArgs.startTime) ?? 0.0,
    attenuationPath: toStringValue(normalizedArgs.attenuationPath),
    concurrencyPath: toStringValue(normalizedArgs.concurrencyPath)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.PLAY_SOUND_AT_LOCATION, payload)) as Record<string, unknown>;
}

export async function playSound2D(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.soundPath, 'soundPath', 'Missing required parameter: soundPath');

  const { volume, pitch } = validateAudioParams(toNumber(normalizedArgs.volume), toNumber(normalizedArgs.pitch));
  const payload = {
    soundPath: normalizedArgs.soundPath ?? '',
    volume,
    pitch,
    startTime: toNumber(normalizedArgs.startTime) ?? 0.0
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.PLAY_SOUND_2D, payload)) as Record<string, unknown>;
}

export async function createAudioComponent(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.soundPath, 'soundPath', 'Missing required parameter: soundPath');

  const payload = {
    actorName: normalizedArgs.actorName ?? '',
    componentName: normalizedArgs.componentName ?? '',
    soundPath: normalizedArgs.soundPath ?? '',
    autoPlay: toBoolean(normalizedArgs.autoPlay) ?? false,
    is3D: toBoolean(normalizedArgs.is3D) ?? true
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.CREATE_AUDIO_COMPONENT, payload)) as Record<string, unknown>;
}

export async function createAmbientSound(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  requireNonEmptyString(normalizedArgs.soundPath, 'soundPath', 'Missing required parameter: soundPath');

  const { volume, pitch } = validateAudioParams(toNumber(normalizedArgs.volume), toNumber(normalizedArgs.pitch));
  const payload = {
    soundPath: normalizedArgs.soundPath ?? '',
    location: toVec3Array(normalizedArgs.location) ?? [0, 0, 0],
    volume,
    pitch,
    startTime: toNumber(normalizedArgs.startTime) ?? 0.0,
    attenuationPath: toStringValue(normalizedArgs.attenuationPath),
    concurrencyPath: toStringValue(normalizedArgs.concurrencyPath)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.CREATE_AMBIENT_SOUND, payload)) as Record<string, unknown>;
}

export async function fadeSound(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  requireNonEmptyString(args.soundName, 'soundName', 'Missing required parameter: soundName');

  const payload = {
    soundName: args.soundName ?? '',
    targetVolume: toNumber(args.targetVolume),
    fadeTime: toNumber(args.fadeTime),
    fadeType: toStringValue(args.fadeType) || 'FadeTo'
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.FADE_SOUND, payload)) as Record<string, unknown>;
}
