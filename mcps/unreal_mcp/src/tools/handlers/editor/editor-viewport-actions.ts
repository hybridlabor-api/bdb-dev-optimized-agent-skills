import type { EditorArgs } from '../../../types/handlers/handler-types.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { cleanObject } from '../../../utils/serialization/safe-json.js';
import { sanitizeCommandArgument } from '../../../utils/validation/validation.js';
import { executeAutomationRequest, requireNonEmptyString } from '../foundation/dispatch/common-handlers.js';
import { EDITOR_ACTION_UNHANDLED, editorActionHandled, type EditorActionResult } from './editor-action-result.js';

function getBookmarkIndex(args: EditorArgs): number {
  return typeof args.id === 'number' ? Math.trunc(args.id) : (parseInt(args.bookmarkName ?? '0') || 0);
}

export async function handleEditorViewportAction(
  action: string,
  args: EditorArgs,
  tools: ITools
): Promise<EditorActionResult> {
  switch (action) {
    case 'set_view_target': {
      const actorName = requireNonEmptyString(args.actorName ?? args.name ?? args.objectPath, 'actorName');
      const res = await executeAutomationRequest(tools, 'control_editor', {
        action: 'set_view_target',
        actorName,
        objectPath: args.objectPath,
        location: args.location,
        rotation: args.rotation,
        blendTime: typeof args.blendTime === 'number' ? args.blendTime : undefined
      }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'set_camera': {
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'set_camera', location: args.location, rotation: args.rotation }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'set_camera_fov': {
      const safeFov = sanitizeCommandArgument(String(args.fov));
      if (!safeFov) return editorActionHandled({ success: false, error: 'FOV is required after sanitization', action: 'set_camera_fov' });
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'set_camera_fov', fov: Number(safeFov) }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'set_view_mode': {
      const viewMode = requireNonEmptyString(args.viewMode, 'viewMode');
      const validModes = [
        'Lit', 'Unlit', 'Wireframe', 'DetailLighting', 'LightingOnly', 'Reflections',
        'OptimizationViewmodes', 'ShaderComplexity', 'LightmapDensity', 'StationaryLightOverlap', 'LightComplexity',
        'PathTracing', 'Visualizer', 'LODColoration', 'CollisionPawn', 'CollisionVisibility'
      ];
      if (!validModes.includes(viewMode)) {
        throw new Error(`unknown_viewmode: ${viewMode}. Must be one of: ${validModes.join(', ')}`);
      }
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'set_view_mode', viewMode }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'set_viewport_resolution': {
      const width = Number(args.width);
      const height = Number(args.height);
      if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
        return editorActionHandled({
          success: false,
          error: 'VALIDATION_ERROR',
          message: 'Width and height must be positive numbers',
          action: 'set_viewport_resolution'
        });
      }
      const res = await executeAutomationRequest(tools, 'console_command', { command: `r.SetRes ${width}x${height}` }) as Record<string, unknown>;
      return editorActionHandled(cleanObject({ ...res, action: 'set_viewport_resolution', width, height }));
    }
    case 'set_viewport_realtime': {
      const enabled = args.enabled !== undefined ? args.enabled : (args.realtime !== false);
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'set_viewport_realtime', enabled, realtime: enabled }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'create_bookmark': {
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'create_bookmark', index: getBookmarkIndex(args) }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'jump_to_bookmark': {
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'jump_to_bookmark', index: getBookmarkIndex(args) }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'undo':
    case 'redo': {
      const res = await executeAutomationRequest(tools, 'control_editor', { action }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'set_editor_mode': {
      const mode = requireNonEmptyString(args.mode, 'mode');
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'set_editor_mode', mode });
      return editorActionHandled(cleanObject(res));
    }
    case 'show_stats':
    case 'hide_stats': {
      const res = await executeAutomationRequest(tools, 'control_editor', { action, stat: args.stat }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'set_game_view':
    case 'set_immersive_mode': {
      const enabled = args.enabled !== false;
      const res = await executeAutomationRequest(tools, 'control_editor', { action, enabled }) as Record<string, unknown>;
      return editorActionHandled(cleanObject(res));
    }
    case 'focus':
    case 'focus_actor': {
      const actorName = requireNonEmptyString(args.actorName || args.name, 'actorName');
      const res = await executeAutomationRequest(tools, 'control_editor', { action: 'focus_actor', actorName });
      return editorActionHandled(cleanObject(res));
    }
    default:
      return EDITOR_ACTION_UNHANDLED;
  }
}
