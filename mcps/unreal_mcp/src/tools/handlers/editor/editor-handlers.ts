import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { EditorArgs } from '../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import type { EditorActionResult } from './editor-action-result.js';
import { handleEditorAssetAction } from './editor-asset-actions.js';
import { handleEditorInputAction } from './editor-input-actions.js';
import { handleEditorScreenshotAction } from './editor-screenshot-actions.js';
import { handleEditorSessionAction } from './editor-session-actions.js';
import { prepareEditorAction } from './editor-action-validation.js';
import { handleEditorViewportAction } from './editor-viewport-actions.js';

type EditorActionHandler = (
  action: string,
  args: EditorArgs,
  tools: ITools
) => Promise<EditorActionResult>;

const EDITOR_ACTION_HANDLERS: readonly EditorActionHandler[] = [
  handleEditorSessionAction,
  handleEditorScreenshotAction,
  handleEditorAssetAction,
  handleEditorViewportAction,
  handleEditorInputAction
];

async function dispatchEditorAction(action: string, args: EditorArgs, tools: ITools): Promise<unknown> {
  for (const handler of EDITOR_ACTION_HANDLERS) {
    const result = await handler(action, args, tools);
    if (result.handled) return result.value;
  }

  return await executeAutomationRequest(tools, 'control_editor', args);
}

export async function handleEditorTools(action: string, args: EditorArgs, tools: ITools): Promise<unknown> {
  const prepared = prepareEditorAction(action, args);
  return await dispatchEditorAction(prepared.normalizedAction, prepared.args, tools);
}
