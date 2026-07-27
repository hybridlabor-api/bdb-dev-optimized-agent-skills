import { cleanObject } from '../../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { HandlerArgs, AnimationArgs } from '../../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../../foundation/dispatch/common-handlers.js';
import {
  applyBlendSpaceAxisAliases,
  validateAnimationPathInputs
} from './animation-handler-utils.js';
import { tryHandleSpecialAnimationAction } from './animation-special-handlers.js';
import { tryHandleAnimationCreationAction } from './animation-creation-handlers.js';
import { tryHandleAnimationPhysicsAction } from './animation-physics-actions.js';

export async function handleAnimationTools(action: string, args: HandlerArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsTyped = args as AnimationArgs;
  const animAction = String(action || '').toLowerCase();

  const securityError = validateAnimationPathInputs(args as Record<string, unknown>);
  if (securityError) {
    return securityError;
  }

  const specialResult = await tryHandleSpecialAnimationAction(animAction, args, argsTyped, tools);
  if (specialResult) {
    return specialResult;
  }

  const mutableArgs = { ...argsTyped } as AnimationArgs & Record<string, unknown>;
  if (animAction === 'create_blend_space' || animAction === 'create_blend_tree') {
    applyBlendSpaceAxisAliases(mutableArgs, argsTyped);
  }

  const creationResult = await tryHandleAnimationCreationAction(animAction, args, mutableArgs, tools);
  if (creationResult) {
    return creationResult;
  }

  const physicsResult = await tryHandleAnimationPhysicsAction(animAction, args, mutableArgs, tools);
  if (physicsResult) {
    return physicsResult;
  }

  const res = await executeAutomationRequest(
    tools,
    'animation_physics',
    args,
    'Automation bridge not available for animation/physics operations'
  );
  return cleanObject(res) as Record<string, unknown>;
}
