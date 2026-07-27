import type { EditorArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { cleanObject } from '../../../utils/serialization/safe-json.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import { EDITOR_ACTION_UNHANDLED, editorActionHandled, type EditorActionResult } from './editor-action-result.js';

const SUPPORTED_SCREENSHOT_MODES = new Set(['editor_viewport', 'game_viewport', 'full_editor_window']);

function getScreenshotMode(args: EditorArgs): { mode?: string; error?: string } {
  if (typeof args.mode !== 'string' || args.mode.trim() === '') {
    return {};
  }

  const mode = args.mode.trim().toLowerCase();
  if (!SUPPORTED_SCREENSHOT_MODES.has(mode)) {
    return { error: `Unknown screenshot mode: ${args.mode}. Supported: editor_viewport, game_viewport, full_editor_window` };
  }

  return { mode };
}

export async function handleEditorScreenshotAction(
  action: string,
  args: EditorArgs,
  tools: ITools
): Promise<EditorActionResult> {
  if (action !== 'screenshot') {
    return EDITOR_ACTION_UNHANDLED;
  }

  const filename = args.filename ?? args.path;
  const modeResult = getScreenshotMode(args);
  if (modeResult.error) {
    return editorActionHandled({
      success: false,
      type: 'INVALID_ARGUMENT',
      error: 'INVALID_ARGUMENT',
      message: modeResult.error,
      action: 'screenshot'
    });
  }

  const mode = modeResult.mode;
  const payload: Record<string, unknown> = { action: 'screenshot', filename, resolution: args.resolution };
  if (mode !== undefined) {
    payload.mode = mode;
  }
  if (typeof args.returnBase64 === 'boolean') {
    payload.returnBase64 = args.returnBase64;
  } else if (mode === 'full_editor_window' || mode === 'game_viewport') {
    payload.returnBase64 = true;
  }
  if (args.includeMetadata === true) {
    payload.includeMetadata = true;
  }
  if (args.includeMetadata === true && args.metadata !== undefined) {
    payload.metadata = args.metadata;
  }

  const targetAction = mode === 'game_viewport' ? 'system_control' : 'control_editor';
  const res = await executeAutomationRequest(tools, targetAction, payload) as Record<string, unknown>;
  return editorActionHandled(cleanObject(res));
}
