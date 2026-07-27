import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import { handleControlRigAction } from './animation-authoring-control-rig.js';
import { handleIkRetargetingAction } from './animation-authoring-ik-retargeting.js';

export async function handleRigRetargetingAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
    const controlRigResult = await handleControlRigAction(action, args, tools);
    if (controlRigResult !== undefined) return controlRigResult;
    const retargetingResult = await handleIkRetargetingAction(action, args, tools);
    if (retargetingResult !== undefined) return retargetingResult;
  return undefined;
}
