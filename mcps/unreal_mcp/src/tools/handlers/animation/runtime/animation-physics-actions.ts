import { cleanObject } from '../../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AnimationArgs, HandlerArgs } from '../../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../../foundation/dispatch/common-handlers.js';
import { normalizeArgs } from '../../foundation/arguments/argument-helper.js';
import { sanitizePath } from '../../../../utils/paths/path-security.js';
import { optionalArray, securityViolation } from './animation-handler-utils.js';

export async function tryHandleAnimationPhysicsAction(
  animAction: string,
  args: HandlerArgs,
  mutableArgs: AnimationArgs & Record<string, unknown>,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
  switch (animAction) {
    case 'cleanup':
      return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
        action: 'cleanup',
        artifacts: optionalArray(mutableArgs.artifacts)
      })) as Record<string, unknown>;
    case 'create_animation_asset':
      return await handleCreateAnimationAsset(mutableArgs, tools);
    case 'add_notify':
      return await handleAddNotify(mutableArgs, tools);
    case 'configure_vehicle':
      return await handleConfigureVehicle(args, tools);
    case 'setup_physics_simulation':
      return await handleSetupPhysicsSimulation(mutableArgs, tools);
    default:
      return undefined;
  }
}

async function handleCreateAnimationAsset(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  let savePath: string;
  try {
    savePath = sanitizePath(String(mutableArgs.path || mutableArgs.savePath || '/Game/Animations'));
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }

  let assetType = mutableArgs.assetType;
  if (!assetType && mutableArgs.name) {
    const lowerName = mutableArgs.name.toLowerCase();
    if (lowerName.endsWith('montage') || lowerName.includes('montage')) {
      assetType = 'montage';
    }
  }

  return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
    action: 'create_animation_asset',
    name: mutableArgs.name,
    savePath,
    skeletonPath: mutableArgs.skeletonPath,
    assetType
  })) as Record<string, unknown>;
}

async function handleAddNotify(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  let assetPath: string | undefined;
  try {
    const rawPath = mutableArgs.animationPath || mutableArgs.assetPath;
    if (rawPath && typeof rawPath === 'string') {
      assetPath = sanitizePath(rawPath);
    }
  } catch (e) {
    return securityViolation(e instanceof Error ? e.message : 'Invalid path: path traversal or illegal characters detected');
  }

  return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
    action: 'add_notify',
    assetPath,
    notifyName: mutableArgs.notifyName || mutableArgs.name,
    time: mutableArgs.time ?? mutableArgs.startTime
  })) as Record<string, unknown>;
}

async function handleConfigureVehicle(args: HandlerArgs, tools: ITools): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'actorName', required: false },
    { key: 'vehicleName', required: false },
    { key: 'vehicleType', default: 'WheeledVehicle4W' },
    { key: 'wheels' },
    { key: 'engine' },
    { key: 'transmission' },
    { key: 'mass', default: 1500 },
    { key: 'dragCoefficient', default: 0.3 }
  ]);

  if (!params.actorName && !params.vehicleName) {
    return cleanObject({
      success: false,
      error: 'MISSING_REQUIRED_PARAM',
      message: 'At least one of actorName or vehicleName is required for configure_vehicle'
    });
  }

  return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
    action: 'configure_vehicle',
    subAction: 'configure_vehicle',
    actorName: params.actorName,
    vehicleName: params.vehicleName,
    vehicleType: params.vehicleType,
    wheels: params.wheels,
    engine: params.engine,
    transmission: params.transmission,
    mass: params.mass,
    dragCoefficient: params.dragCoefficient
  })) as Record<string, unknown>;
}

async function handleSetupPhysicsSimulation(mutableArgs: AnimationArgs & Record<string, unknown>, tools: ITools): Promise<Record<string, unknown>> {
  const payload: Record<string, unknown> = {
    physicsAssetName: mutableArgs.physicsAssetName
  };

  for (const [inputKey, outputKey, message] of [
    ['savePath', 'savePath', 'Invalid savePath: path traversal or illegal characters detected'],
    ['skeletonPath', 'skeletonPath', 'Invalid skeletonPath: path traversal or illegal characters detected'],
    ['skeletalMeshPath', 'skeletalMeshPath', 'Invalid skeletalMeshPath: path traversal or illegal characters detected']
  ] as const) {
    const rawPath = mutableArgs[inputKey];
    if (rawPath && typeof rawPath === 'string') {
      try {
        payload[outputKey] = sanitizePath(rawPath);
      } catch (e) {
        return securityViolation(e instanceof Error ? e.message : message);
      }
    }
  }

  if (mutableArgs.actorName && !payload.skeletonPath && !payload.skeletalMeshPath) {
    payload.actorName = mutableArgs.actorName;
  }

  if (!payload.skeletonPath && !payload.skeletalMeshPath && !payload.actorName) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'setup_physics_simulation requires skeletonPath, skeletalMeshPath, or actorName parameter'
    });
  }

  return cleanObject(await executeAutomationRequest(tools, 'animation_physics', {
    action: 'setup_physics_simulation',
    ...payload
  })) as Record<string, unknown>;
}
