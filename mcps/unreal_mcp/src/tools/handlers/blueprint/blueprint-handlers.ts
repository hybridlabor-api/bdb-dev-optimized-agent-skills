import type { HandlerArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { createBlueprintContext } from './blueprint-action-context.js';
import { blueprintCoreHandlers, handleBlueprintDefault } from './blueprint-core-actions.js';
import { blueprintEventHandlers } from './blueprint-event-actions.js';
import { blueprintGraphHandlers } from './blueprint-graph-actions.js';
import { blueprintScsHandlers } from './blueprint-scs-actions.js';
import { blueprintVariableHandlers } from './blueprint-variable-actions.js';
import type { BlueprintActionHandler } from './blueprint-action-context.js';

export { handleBlueprintGet } from './blueprint-query-actions.js';

const BLUEPRINT_ACTION_HANDLERS: Readonly<Record<string, BlueprintActionHandler>> = {
  ...blueprintCoreHandlers,
  ...blueprintVariableHandlers,
  ...blueprintEventHandlers,
  ...blueprintScsHandlers,
  ...blueprintGraphHandlers
};

export async function handleBlueprintTools(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<Record<string, unknown>> {
  const contextResult = createBlueprintContext(args, tools);
  if (contextResult.kind === 'blocked') {
    return contextResult.response;
  }

  const handler = BLUEPRINT_ACTION_HANDLERS[action];
  if (handler) {
    return await handler(contextResult.context);
  }

  return await handleBlueprintDefault(contextResult.context, args);
}
