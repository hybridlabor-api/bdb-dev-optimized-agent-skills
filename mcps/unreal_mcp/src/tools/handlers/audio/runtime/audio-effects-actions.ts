import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AudioArgs, HandlerArgs } from '../../../../types/handlers/handler-types.js';
import { TOOL_ACTIONS } from '../../../../utils/commands/action-constants.js';
import { toBoolean, toNumber, toString as toStringValue } from '../../../../utils/validation/type-coercion.js';
import { executeAutomationRequest } from '../../foundation/dispatch/common-handlers.js';
import { normalizeAudioArgs } from './audio-path-normalization.js';

export async function enableAudioAnalysis(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const payload = {
    enable: toBoolean(args.enable ?? args.enabled) ?? true,
    analysisType: toStringValue(args.analysisType) || 'FFT',
    windowSize: toNumber(args.windowSize) ?? 1024
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.ENABLE_AUDIO_ANALYSIS, payload)) as Record<string, unknown>;
}

export async function setDopplerEffect(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  const payload = {
    soundPath: toStringValue(normalizedArgs.soundPath),
    dopplerIntensity: toNumber(normalizedArgs.dopplerIntensity) ?? 1.0,
    velocityScale: toNumber(normalizedArgs.velocityScale) ?? 1.0,
    save: toBoolean(normalizedArgs.save) ?? true
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.SET_DOPPLER_EFFECT, payload)) as Record<string, unknown>;
}

export async function setAudioOcclusion(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const normalizedArgs = normalizeAudioArgs(args);
  const payload = {
    soundPath: toStringValue(normalizedArgs.soundPath),
    enable: toBoolean(normalizedArgs.enable) ?? true,
    occlusionVolumeScale: toNumber(normalizedArgs.occlusionVolumeScale) ?? 0.5,
    occlusionFilterScale: toNumber(normalizedArgs.occlusionFilterScale) ?? 0.5,
    occlusionInterpolationTime: toNumber(normalizedArgs.occlusionInterpolationTime) ?? 0.1,
    save: toBoolean(normalizedArgs.save) ?? true
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.SET_AUDIO_OCCLUSION, payload)) as Record<string, unknown>;
}

export async function addSourceEffect(tools: ITools, args: HandlerArgs): Promise<Record<string, unknown>> {
  const payload: HandlerArgs = { ...args };
  if (!payload.chainPath && payload.assetPath) {
    payload.chainPath = payload.assetPath;
    delete payload.assetPath;
  }

  const chainPath = payload.chainPath;
  if (typeof chainPath === 'string') {
    const lastSegment = chainPath.split('/').pop() ?? '';
    if (!lastSegment.includes('.')) {
      payload.chainPath = `${chainPath}.${lastSegment}`;
    }
  }

  return (await executeAutomationRequest(tools, 'add_source_effect', payload)) as Record<string, unknown>;
}
