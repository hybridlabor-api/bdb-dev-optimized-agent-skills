import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { SystemArgs } from '../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import type { OperationResponse } from './system-handler-types.js';

const FALLBACK_SOUND_PATH = '/Engine/EditorSounds/Notifications/CompileSuccess_Cue';

function isMissingAssetError(value: unknown): boolean {
  const lowered = String(value || '').toLowerCase();
  return lowered.includes('asset_not_found') || lowered.includes('asset not found');
}

export async function handlePlaySound(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsRecord = args as Record<string, unknown>;
  const soundPath = typeof argsRecord.soundPath === 'string' ? argsRecord.soundPath.trim() : '';
  const volume = typeof argsRecord.volume === 'number' ? argsRecord.volume : undefined;
  const pitch = typeof argsRecord.pitch === 'number' ? argsRecord.pitch : undefined;

  if (typeof volume === 'number' && volume <= 0) {
    return {
      success: true,
      message: 'Sound request handled (volume is 0 - silent)',
      action: 'play_sound',
      soundPath,
      volume,
      pitch,
      handled: true
    };
  }

  try {
    const response = await executeAutomationRequest(tools, 'play_sound_2d', {
      soundPath,
      volume: volume ?? 1.0,
      pitch: pitch ?? 1.0
    }) as OperationResponse;

    if (!response || response.success === false) {
      if (isMissingAssetError(response?.error) || !soundPath) {
        if (soundPath !== FALLBACK_SOUND_PATH) {
          const fallbackResponse = await executeAutomationRequest(tools, 'play_sound_2d', {
            soundPath: FALLBACK_SOUND_PATH,
            volume: volume ?? 1.0,
            pitch: pitch ?? 1.0
          }) as OperationResponse;
          if (fallbackResponse.success) {
            return {
              success: true,
              message: `Sound asset not found, played fallback sound: ${FALLBACK_SOUND_PATH}`,
              action: 'play_sound',
              soundPath: FALLBACK_SOUND_PATH,
              originalPath: soundPath,
              volume,
              pitch
            };
          }
        }

        return {
          success: false,
          error: 'ASSET_NOT_FOUND',
          message: 'Sound asset not found (and fallback failed)',
          action: 'play_sound',
          soundPath,
          volume,
          pitch
        };
      }

      return cleanObject({
        success: false,
        error: response?.error || 'Failed to play 2D sound',
        action: 'play_sound',
        soundPath,
        volume,
        pitch
      });
    }

    return cleanObject({
      ...response,
      action: 'play_sound',
      soundPath,
      volume,
      pitch
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);

    if (isMissingAssetError(message) || !soundPath) {
      return {
        success: false,
        error: 'ASSET_NOT_FOUND',
        message: 'Sound asset not found',
        action: 'play_sound',
        soundPath,
        volume,
        pitch
      };
    }

    return {
      success: false,
      error: `Failed to play 2D sound: ${message}`,
      action: 'play_sound',
      soundPath,
      volume,
      pitch
    };
  }
}
