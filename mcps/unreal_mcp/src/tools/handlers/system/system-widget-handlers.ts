import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { SystemArgs } from '../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import type { OperationResponse } from './system-handler-types.js';

function stringField(args: Record<string, unknown>, key: string): string | undefined {
  const value = args[key];
  return typeof value === 'string' ? value.trim() : undefined;
}

export async function handleCreateWidget(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsRecord = args as Record<string, unknown>;
  const name = stringField(argsRecord, 'name') ?? '';
  const widgetPathRaw = stringField(argsRecord, 'widgetPath') ?? '';
  const widgetType = stringField(argsRecord, 'widgetType');
  let effectiveName = name || `NewWidget_${Date.now()}`;
  let effectivePath = stringField(argsRecord, 'savePath') ?? '';

  if (!name && widgetPathRaw) {
    const parts = widgetPathRaw.split('/').filter((part) => part.length > 0);
    if (parts.length > 0) {
      effectiveName = parts[parts.length - 1];
      if (!effectivePath) {
        effectivePath = '/' + parts.slice(0, parts.length - 1).join('/');
      }
    }
  }

  if (!effectiveName) {
    return {
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'Widget name is required for creation',
      action: 'create_widget'
    };
  }

  try {
    const response = await executeAutomationRequest(tools, 'manage_widget_authoring', {
      action: 'create_widget',
      name: effectiveName,
      type: widgetType,
      savePath: effectivePath,
      folder: effectivePath
    }) as Record<string, unknown>;

    return cleanObject({
      ...response,
      action: 'create_widget'
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      success: false,
      error: `Failed to create widget: ${message}`,
      message,
      action: 'create_widget'
    };
  }
}

export async function handleShowWidget(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsRecord = args as Record<string, unknown>;
  const widgetId = stringField(argsRecord, 'widgetId') ?? '';

  if (widgetId.toLowerCase() === 'notification') {
    const message = stringField(argsRecord, 'message') ?? '';
    const text = message.length > 0 ? message : 'Notification';
    const duration = typeof argsRecord.duration === 'number' ? argsRecord.duration : undefined;

    try {
      const response = await executeAutomationRequest(tools, 'manage_widget_authoring', {
        action: 'show_widget',
        widgetId: 'notification',
        message: text,
        duration
      }) as OperationResponse;

      if (response && response.success !== false) {
        return {
          success: true,
          message: response.message || 'Notification shown',
          action: 'show_widget',
          widgetId,
          handled: true
        };
      }

      return cleanObject({
        success: false,
        error: response?.error || 'NOTIFICATION_FAILED',
        message: response?.message || 'Failed to show notification',
        action: 'show_widget',
        widgetId
      });
    } catch (error) {
      return {
        success: false,
        error: 'NOTIFICATION_FAILED',
        message: error instanceof Error ? error.message : String(error),
        action: 'show_widget',
        widgetId
      };
    }
  }

  const widgetPath = stringField(argsRecord, 'widgetPath') || stringField(argsRecord, 'name') || '';
  if (!widgetPath) {
    return {
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'widgetPath (or name) is required to show a widget',
      action: 'show_widget',
      widgetId
    };
  }

  const response = await executeAutomationRequest(tools, 'manage_widget_authoring', {
    action: 'show_widget',
    widgetPath
  });
  return cleanObject(response) as Record<string, unknown>;
}

export async function handleAddWidgetChild(args: SystemArgs, tools: ITools): Promise<Record<string, unknown>> {
  const argsRecord = args as Record<string, unknown>;
  const widgetPath = stringField(argsRecord, 'widgetPath') ?? '';
  const childClass = stringField(argsRecord, 'childClass') ?? '';
  const parentName = stringField(argsRecord, 'parentName');

  if (!widgetPath || !childClass) {
    return {
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'widgetPath and childClass are required',
      action: 'add_widget_child'
    };
  }

  try {
    const componentName = stringField(argsRecord, 'name');
    const response = await executeAutomationRequest(tools, 'manage_widget_authoring', {
      action: 'add_widget_component',
      subAction: 'add_widget_component',
      widgetPath,
      componentType: childClass,
      componentName,
      parentName,
      text: typeof argsRecord.text === 'string' ? argsRecord.text : undefined
    }) as Record<string, unknown>;
    return cleanObject({
      ...response,
      action: 'add_widget_child'
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      success: false,
      error: `Failed to add widget child: ${message}`,
      message,
      action: 'add_widget_child'
    };
  }
}
