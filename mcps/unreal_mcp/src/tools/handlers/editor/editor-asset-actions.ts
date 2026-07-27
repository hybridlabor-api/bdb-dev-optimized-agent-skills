import type { EditorArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { cleanObject } from '../../../utils/serialization/safe-json.js';
import { executeAutomationRequest, requireNonEmptyString } from '../foundation/dispatch/common-handlers.js';
import { EDITOR_ACTION_UNHANDLED, editorActionHandled, type EditorActionResult } from './editor-action-result.js';

export async function handleEditorAssetAction(
  action: string,
  args: EditorArgs,
  tools: ITools
): Promise<EditorActionResult> {
  switch (action) {
    case 'console_command': {
      const res = await executeAutomationRequest(tools, 'console_command', { command: args.command ?? '' }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'open_asset': {
      const assetPath = requireNonEmptyString(args.assetPath || args.path, 'assetPath');
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'open_asset', assetPath });
      return editorActionHandled(cleanObject(res));
    }
    case 'close_asset': {
      const assetPath = requireNonEmptyString(args.assetPath || args.path, 'assetPath');
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'close_asset', assetPath });
      return editorActionHandled(cleanObject(res));
    }
    case 'open_level': {
      const levelPath = requireNonEmptyString(args.levelPath || args.path || args.assetPath, 'levelPath');
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'open_level', levelPath });
      return editorActionHandled(cleanObject(res));
    }
    case 'save_all': {
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'save_all' });
      return editorActionHandled(cleanObject(res));
    }
    case 'execute_command': {
      const command = requireNonEmptyString(args.command, 'command');
      const res = await executeAutomationRequest(tools, 'console_command', { command }) as Record<string, unknown>;
      return editorActionHandled({ ...cleanObject(res), action: 'execute_command' });
    }
    case 'set_preferences': {
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'set_preferences', category: args.category ?? '', preferences: args.preferences ?? {} }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    default:
      return EDITOR_ACTION_UNHANDLED;
  }
}
