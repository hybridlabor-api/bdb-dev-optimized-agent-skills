import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import { extractOptionalBoolean, extractOptionalString, extractString, normalizeArgs } from '../../foundation/arguments/argument-helper.js';
import {
  type AnimationAuthoringResult,
  nonNegativeIntegerOrDefault,
  sendAnimationAuthoringRequest,
  validateRequiredPath,
} from './animation-authoring-utils.js';

export async function handleAnimationSequenceSettingAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<AnimationAuthoringResult | undefined> {
  switch (action) {
    case 'add_sync_marker': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'markerName', required: true },
        { key: 'frame', required: true },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      const markerName = extractString(params, 'markerName');
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'add_sync_marker',
        assetPath: assetPath.sanitized,
        markerName,
        frame: nonNegativeIntegerOrDefault(params['frame'], 0),
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to add sync marker', `Sync marker '${markerName}' added`);
    }

    case 'set_root_motion_settings': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'enableRootMotion', default: true },
        { key: 'rootMotionRootLock', default: 'RefPose' },
        { key: 'forceRootLock', default: false },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'set_root_motion_settings',
        assetPath: assetPath.sanitized,
        enableRootMotion: extractOptionalBoolean(params, 'enableRootMotion') ?? true,
        rootMotionRootLock: extractOptionalString(params, 'rootMotionRootLock') ?? 'RefPose',
        forceRootLock: extractOptionalBoolean(params, 'forceRootLock') ?? false,
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to set root motion settings', 'Root motion settings updated');
    }

    case 'set_additive_settings': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'additiveAnimType', default: 'NoAdditive' },
        { key: 'basePoseType', default: 'RefPose' },
        { key: 'basePoseAnimation' },
        { key: 'basePoseFrame', default: 0 },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'set_additive_settings',
        assetPath: assetPath.sanitized,
        additiveAnimType: extractOptionalString(params, 'additiveAnimType') ?? 'NoAdditive',
        basePoseType: extractOptionalString(params, 'basePoseType') ?? 'RefPose',
        basePoseAnimation: extractOptionalString(params, 'basePoseAnimation'),
        basePoseFrame: nonNegativeIntegerOrDefault(params['basePoseFrame'], 0),
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to set additive settings', 'Additive settings updated');
    }

    default:
      return undefined;
  }
}
