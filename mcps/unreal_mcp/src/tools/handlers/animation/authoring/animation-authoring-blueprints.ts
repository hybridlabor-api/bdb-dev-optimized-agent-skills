import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import { handleAnimationBlueprintStateAction } from './animation-authoring-blueprint-states.js';
import { handleAnimationBlueprintGraphAction } from './animation-authoring-blueprint-graphs.js';

export async function handleAnimationBlueprintAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
    const stateResult = await handleAnimationBlueprintStateAction(action, args, tools);
    if (stateResult !== undefined) return stateResult;
    const graphResult = await handleAnimationBlueprintGraphAction(action, args, tools);
    if (graphResult !== undefined) return graphResult;
  return undefined;
}
