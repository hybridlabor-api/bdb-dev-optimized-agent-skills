import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AudioArgs } from '../../../../types/handlers/handler-types.js';
import { TOOL_ACTIONS } from '../../../../utils/commands/action-constants.js';
import { toString as toStringValue } from '../../../../utils/validation/type-coercion.js';
import { executeAutomationRequest, requireNonEmptyString } from '../../foundation/dispatch/common-handlers.js';

export async function setSoundMixClassOverride(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const payload = {
    ...args,
    mixName: toStringValue(args.mixName ?? args.mix ?? args.name),
    soundClassName: toStringValue(args.soundClassName ?? args.soundClass)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.SET_SOUND_MIX_CLASS_OVERRIDE, payload)) as Record<string, unknown>;
}

export async function clearSoundMixClassOverride(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const payload = {
    ...args,
    mixName: toStringValue(args.mixName ?? args.mix ?? args.name),
    soundClassName: toStringValue(args.soundClassName ?? args.soundClass)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.CLEAR_SOUND_MIX_CLASS_OVERRIDE, payload)) as Record<string, unknown>;
}

export async function setBaseSoundMix(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  const payload = {
    ...args,
    mixName: toStringValue(args.mixName ?? args.mix ?? args.name)
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.SET_BASE_SOUND_MIX, payload)) as Record<string, unknown>;
}

export async function pushSoundMix(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  requireNonEmptyString(args.mixName ?? args.name, 'mixName', 'Missing required parameter: mixName (or name)');

  const payload = {
    mixName: args.mixName ?? args.name ?? ''
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.PUSH_SOUND_MIX, payload)) as Record<string, unknown>;
}

export async function popSoundMix(tools: ITools, args: AudioArgs): Promise<Record<string, unknown>> {
  requireNonEmptyString(args.mixName ?? args.name, 'mixName', 'Missing required parameter: mixName (or name)');

  const payload = {
    mixName: args.mixName ?? args.name ?? ''
  };

  return (await executeAutomationRequest(tools, TOOL_ACTIONS.POP_SOUND_MIX, payload)) as Record<string, unknown>;
}
