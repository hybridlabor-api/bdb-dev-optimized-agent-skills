import type { AudioArgs } from '../../../../types/handlers/handler-types.js';
import { normalizePathFields } from '../../foundation/dispatch/common-handlers.js';

const AUDIO_PATH_FIELDS = [
  'wavePath',
  'savePath',
  'path',
  'attenuationPath',
  'concurrencyPath',
  'reverbEffect'
] as const;

export function normalizeAudioArgs(args: AudioArgs): AudioArgs {
  return normalizePathFields(args, AUDIO_PATH_FIELDS) as AudioArgs;
}
