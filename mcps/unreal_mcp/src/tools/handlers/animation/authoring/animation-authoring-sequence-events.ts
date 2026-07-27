import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import { extractOptionalBoolean, extractOptionalString, normalizeArgs } from '../../foundation/arguments/argument-helper.js';
import {
  type AnimationAuthoringResult,
  nonNegativeIntegerOrDefault,
  sendAnimationAuthoringRequest,
  validateRequiredPath,
} from './animation-authoring-utils.js';

export async function handleAnimationSequenceEventAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<AnimationAuthoringResult | undefined> {
  switch (action) {
    case 'add_notify': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'notifyClass', required: false },
        { key: 'frame', required: true },
        { key: 'trackIndex', default: 0 },
        { key: 'notifyName' },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'add_notify',
        assetPath: assetPath.sanitized,
        notifyClass: extractOptionalString(params, 'notifyClass'),
        frame: nonNegativeIntegerOrDefault(params['frame'], 0),
        trackIndex: nonNegativeIntegerOrDefault(params['trackIndex'], 0),
        notifyName: extractOptionalString(params, 'notifyName'),
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to add notify', 'Notify added');
    }

    case 'add_notify_state': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'notifyClass', required: false },
        { key: 'startFrame', required: true },
        { key: 'endFrame', required: true },
        { key: 'trackIndex', default: 0 },
        { key: 'notifyName' },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'add_notify_state',
        assetPath: assetPath.sanitized,
        notifyClass: extractOptionalString(params, 'notifyClass'),
        startFrame: nonNegativeIntegerOrDefault(params['startFrame'], 0),
        endFrame: nonNegativeIntegerOrDefault(params['endFrame'], 10),
        trackIndex: nonNegativeIntegerOrDefault(params['trackIndex'], 0),
        notifyName: extractOptionalString(params, 'notifyName'),
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to add notify state', 'Notify state added');
    }

    default:
      return undefined;
  }
}
