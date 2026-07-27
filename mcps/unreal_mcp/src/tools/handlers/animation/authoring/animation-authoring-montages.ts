import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import { handleMontageAssetAction } from './animation-authoring-montage-assets.js';
import { handleMontageBlendAction } from './animation-authoring-montage-blending.js';

export async function handleAnimationMontageAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
    const assetResult = await handleMontageAssetAction(action, args, tools);
    if (assetResult !== undefined) return assetResult;
    const blendResult = await handleMontageBlendAction(action, args, tools);
    if (blendResult !== undefined) return blendResult;
  return undefined;
}
