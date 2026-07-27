import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import {
  extractOptionalBoolean,
  extractOptionalObject,
  extractOptionalString,
  extractString,
  normalizeArgs,
} from '../../foundation/arguments/argument-helper.js';
import {
  type AnimationAuthoringResult,
  finiteNumberOrDefault,
  nonNegativeIntegerOrDefault,
  optionalPositiveNumber,
  positiveIntegerOrDefault,
  positiveNumberOrDefault,
  sendAnimationAuthoringRequest,
  validateRequiredPath,
} from './animation-authoring-utils.js';

export async function handleAnimationSequenceAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<AnimationAuthoringResult | undefined> {
  switch (action) {
    case 'create_animation_sequence': {
      const params = normalizeArgs(args, [
        { key: 'name', required: true },
        { key: 'path', aliases: ['directory'], default: '/Game/Animations' },
        { key: 'skeletonPath', required: false },
        { key: 'numFrames', default: 30 },
        { key: 'frameRate', default: 30 },
        { key: 'save', default: true },
      ]);
      const name = extractString(params, 'name');
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'create_animation_sequence',
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Animations',
        skeletonPath: extractOptionalString(params, 'skeletonPath'),
        numFrames: positiveIntegerOrDefault(params['numFrames'], 30),
        frameRate: positiveNumberOrDefault(params['frameRate'], 30),
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to create animation sequence', `Animation sequence '${name}' created`);
    }

    case 'set_sequence_length': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'numFrames', required: true },
        { key: 'frameRate' },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'set_sequence_length',
        assetPath: assetPath.sanitized,
        numFrames: positiveIntegerOrDefault(params['numFrames'], 30),
        frameRate: optionalPositiveNumber(params['frameRate']),
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to set sequence length', 'Sequence length updated');
    }

    case 'add_bone_track': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'boneName', required: true },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      const boneName = extractString(params, 'boneName');
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'add_bone_track',
        assetPath: assetPath.sanitized,
        boneName,
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to add bone track', `Bone track '${boneName}' added`);
    }

    case 'set_bone_key': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'boneName', required: true },
        { key: 'frame', required: true },
        { key: 'location' },
        { key: 'rotation' },
        { key: 'scale' },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      const frame = nonNegativeIntegerOrDefault(params['frame'], 0);
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'set_bone_key',
        assetPath: assetPath.sanitized,
        boneName: extractString(params, 'boneName'),
        frame,
        location: extractOptionalObject(params, 'location'),
        rotation: extractOptionalObject(params, 'rotation'),
        scale: extractOptionalObject(params, 'scale'),
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to set bone key', `Bone key set at frame ${frame}`);
    }

    case 'set_curve_key': {
      const params = normalizeArgs(args, [
        { key: 'assetPath', required: true },
        { key: 'curveName', required: true },
        { key: 'frame', required: true },
        { key: 'value', required: true },
        { key: 'createIfMissing', default: true },
        { key: 'save', default: true },
      ]);
      const assetPath = validateRequiredPath(params, 'assetPath');
      if (!assetPath.valid) return assetPath.error;
      const frame = nonNegativeIntegerOrDefault(params['frame'], 0);
      return await sendAnimationAuthoringRequest(tools, {
        subAction: 'set_curve_key',
        assetPath: assetPath.sanitized,
        curveName: extractString(params, 'curveName'),
        frame,
        value: finiteNumberOrDefault(params['value'], 0),
        createIfMissing: extractOptionalBoolean(params, 'createIfMissing') ?? true,
        save: extractOptionalBoolean(params, 'save') ?? true,
      }, 'Failed to set curve key', `Curve key set at frame ${frame}`);
    }

    default:
      return undefined;
  }
}
