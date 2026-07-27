import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import { handleBlendSpaceAssetAction } from './animation-authoring-blend-space-assets.js';
import { handleAimOffsetAction } from './animation-authoring-aim-offsets.js';

export async function handleBlendSpaceAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
    const blendSpaceResult = await handleBlendSpaceAssetAction(action, args, tools);
    if (blendSpaceResult !== undefined) return blendSpaceResult;
    const aimOffsetResult = await handleAimOffsetAction(action, args, tools);
    if (aimOffsetResult !== undefined) return aimOffsetResult;
  return undefined;
}
