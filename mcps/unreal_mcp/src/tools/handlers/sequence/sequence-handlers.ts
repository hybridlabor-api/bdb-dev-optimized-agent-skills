import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { executeAutomationRequest, normalizePathFields } from '../foundation/dispatch/common-handlers.js';
import { handleSequenceAssetAction } from './sequence-asset-actions.js';
import { handleSequenceCoreAction } from './sequence-core-actions.js';
import { handleSequencePlaybackAction } from './sequence-playback-actions.js';
import { handleSequenceTrackAction } from './sequence-track-actions.js';

type SequenceActionHandler = (
  action: string,
  args: Record<string, unknown>,
  tools: ITools
) => Promise<unknown | undefined>;

const sequenceActionHandlers: readonly SequenceActionHandler[] = [
  handleSequenceCoreAction,
  handleSequencePlaybackAction,
  handleSequenceAssetAction,
  handleSequenceTrackAction
];

export async function handleSequenceTools(action: string, args: Record<string, unknown>, tools: ITools): Promise<unknown> {
  const seqAction = String(action || '').trim();
  const normalizedArgs = normalizePathFields(args, ['path', 'destinationPath']);

  for (const handler of sequenceActionHandlers) {
    const result = await handler(seqAction, normalizedArgs, tools);
    if (result !== undefined) {
      return result;
    }
  }

  const payload = { ...normalizedArgs };
  if (payload.action && !payload.subAction) {
    payload.subAction = payload.action;
  }
  return await executeAutomationRequest(tools, 'manage_sequence', payload);
}
