import { cleanObject } from '../../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AnimationArgs, HandlerArgs } from '../../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../../foundation/dispatch/common-handlers.js';
import { normalizeArgs } from '../../foundation/arguments/argument-helper.js';
import { TOOL_ACTIONS } from '../../../../utils/commands/action-constants.js';
import { sanitizePath } from '../../../../utils/paths/path-security.js';
import { optionalArray, sanitizeAnimationPath, securityViolation } from './animation-handler-utils.js';

export async function tryHandleAnimationCreationAction(
  animAction: string,
  args: HandlerArgs,
  mutableArgs: AnimationArgs & Record<string, unknown>,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
  switch (animAction) {
    case 'create_blend_space':
      return await handleCreateBlendSpace(mutableArgs, tools);
    case 'create_state_machine':
      return await handleCreateStateMachine(mutableArgs, tools);
    case 'setup_ik':
      return await handleSetupIk(mutableArgs, tools);
    case 'create_pose_library':
      return await handleCreatePoseLibrary(mutableArgs, tools);
    case 'create_procedural_anim':
      return await handleCreateProceduralAnim(args, tools);
    case 'create_blend_tree':
      return await handleCreateBlendTree(mutableArgs, tools);
    default:
      return undefined;
  }
}

async function handleCreateBlendSpace(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  let savePath: string;
  try {
    savePath = sanitizeAnimationPath(mutableArgs.path || mutableArgs.savePath, '/Game/Animations');
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }
  const payload = {
    action: 'create_blend_space',
    name: mutableArgs.name,
    path: savePath,
    savePath,
    skeletonPath: mutableArgs.skeletonPath,
    horizontalAxis: mutableArgs.horizontalAxis,
    verticalAxis: mutableArgs.verticalAxis,
    minX: mutableArgs.minX,
    maxX: mutableArgs.maxX,
    minY: mutableArgs.minY,
    maxY: mutableArgs.maxY
  };
  const res = await executeAutomationRequest(tools, 'animation_physics', payload, 'Automation bridge not available for blend space creation');
  return cleanObject(res) as Record<string, unknown>;
}

async function handleCreateStateMachine(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  let blueprintPath: string | undefined;
  try {
    const rawPath = mutableArgs.blueprintPath || mutableArgs.path || mutableArgs.savePath;
    if (rawPath && typeof rawPath === 'string') {
      blueprintPath = sanitizePath(rawPath);
    }
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }
  return cleanObject(await executeAutomationRequest(tools, TOOL_ACTIONS.ANIMATION_PHYSICS, {
    action: 'create_state_machine',
    machineName: mutableArgs.machineName || mutableArgs.name,
    states: optionalArray(mutableArgs.states),
    transitions: optionalArray(mutableArgs.transitions),
    blueprintPath
  })) as Record<string, unknown>;
}

async function handleSetupIk(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  let savePath: string;
  try {
    savePath = sanitizeAnimationPath(mutableArgs.savePath || mutableArgs.path, '/Game/Animations');
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }
  return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
    action: 'setup_ik',
    name: mutableArgs.name,
    savePath,
    skeletonPath: mutableArgs.skeletonPath,
    actorName: mutableArgs.actorName,
    ikBones: optionalArray(mutableArgs.ikBones),
    enableFootPlacement: mutableArgs.enableFootPlacement
  })) as Record<string, unknown>;
}

async function handleCreatePoseLibrary(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  if (!mutableArgs.name) {
    return cleanObject({ success: false, error: 'INVALID_ARGUMENT', message: 'name is required for create_pose_library' });
  }
  if (!mutableArgs.skeletonPath || typeof mutableArgs.skeletonPath !== 'string') {
    return cleanObject({ success: false, error: 'INVALID_ARGUMENT', message: 'skeletonPath is required for create_pose_library' });
  }

  let savePath: string;
  let skeletonPath: string;
  try {
    savePath = sanitizeAnimationPath(mutableArgs.path || mutableArgs.savePath, '/Game/Animations/PoseLibraries');
    skeletonPath = sanitizePath(mutableArgs.skeletonPath);
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }

  return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
    action: 'create_pose_library',
    name: mutableArgs.name,
    path: savePath,
    savePath,
    skeletonPath,
    save: mutableArgs.save !== false
  })) as Record<string, unknown>;
}

async function handleCreateProceduralAnim(args: HandlerArgs, tools: ITools): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'name', required: true },
    { key: 'path', aliases: ['directory'], default: '/Game/Animations' },
    { key: 'skeletonPath', required: true },
    { key: 'boneTracks', required: true },
    { key: 'numFrames', default: 30 },
    { key: 'frameRate', default: 30 },
    { key: 'save', default: true }
  ]);

  let savePath: string;
  let skeletonPath: string;
  try {
    savePath = sanitizePath(String(params.path || '/Game/Animations'));
    skeletonPath = sanitizePath(String(params.skeletonPath));
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }

  if (!Array.isArray(params.boneTracks)) {
    return cleanObject({
      success: false,
      error: 'MISSING_REQUIRED_PARAM',
      message: 'boneTracks is required and must be an array for create_procedural_anim'
    });
  }

  return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
    action: 'create_procedural_anim',
    subAction: 'create_procedural_anim',
    name: params.name,
    path: savePath,
    savePath,
    skeletonPath,
    boneTracks: params.boneTracks,
    numFrames: params.numFrames,
    frameRate: params.frameRate,
    save: params.save
  })) as Record<string, unknown>;
}

async function handleCreateBlendTree(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  let blueprintPath: string | undefined;
  try {
    const rawPath = mutableArgs.blueprintPath || mutableArgs.path || mutableArgs.savePath;
    if (rawPath && typeof rawPath === 'string') {
      blueprintPath = sanitizePath(rawPath);
    }
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }

  if (!blueprintPath) {
    return cleanObject({ success: false, error: 'INVALID_ARGUMENT', message: 'blueprintPath is required for create_blend_tree' });
  }

  const sanitizedChildren: unknown[] = [];
  if (Array.isArray(mutableArgs.children)) {
    for (const child of mutableArgs.children as Record<string, unknown>[]) {
      if (child && typeof child === 'object' && child.animationPath) {
        try {
          sanitizedChildren.push({ ...child, animationPath: sanitizePath(String(child.animationPath)) });
        } catch {
          return securityViolation('Invalid animationPath in children: path traversal or illegal characters detected');
        }
      } else {
        sanitizedChildren.push(child);
      }
    }
  }

  const payload: Record<string, unknown> = {
    action: 'create_blend_tree',
    blueprintPath,
    treeName: mutableArgs.treeName || mutableArgs.name || 'BlendTree',
    blendParameters: optionalArray(mutableArgs.blendParameters),
    children: sanitizedChildren.length > 0 ? sanitizedChildren : optionalArray(mutableArgs.children),
    save: mutableArgs.save !== false
  };

  return cleanObject(await executeAutomationRequest(tools, TOOL_ACTIONS.ANIMATION_PHYSICS, payload)) as Record<string, unknown>;
}
