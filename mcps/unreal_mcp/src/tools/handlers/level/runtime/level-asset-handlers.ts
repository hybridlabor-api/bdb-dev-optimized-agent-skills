import { cleanObject } from '../../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AutomationResponse, LevelArgs } from '../../../../types/handlers/handler-types.js';
import { executeAutomationRequest, requireNonEmptyString } from '../../foundation/dispatch/common-handlers.js';
import { ResultPayload } from './level-handler-utils.js';

export async function handleCreateLevel(argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const levelPathStr = typeof argsTyped.levelPath === 'string' ? argsTyped.levelPath : '';
  const levelName = requireNonEmptyString(argsTyped.levelName || levelPathStr.split('/').pop() || '', 'levelName', 'Missing required parameter: levelName');
  const levelParentPath = argsTyped.savePath || argsTyped.levelPath || '/Game/Maps';
  const createRes = await executeAutomationRequest(tools, 'manage_level_structure', {
    subAction: 'create_level',
    levelPath: levelParentPath,
    levelName,
    bCreateWorldPartition: argsTyped.useWorldPartition ?? false,
    save: true
  }) as Record<string, unknown>;
  if (createRes.success !== true) {
    return cleanObject(createRes);
  }

  const result = createRes.result && typeof createRes.result === 'object' && !Array.isArray(createRes.result)
    ? createRes.result as Record<string, unknown>
    : {};
  const createdLevelPath = typeof result.levelPath === 'string'
    ? result.levelPath
    : `${String(levelParentPath).replace(/\/+$/, '')}/${levelName}`;

  const loadRes = await executeAutomationRequest(tools, 'manage_level', {
    action: 'load',
    levelPath: createdLevelPath,
    saveDirtyPackages: argsTyped.saveDirtyPackages === true
  }) as Record<string, unknown>;
  if (loadRes.success !== true) {
    return cleanObject(loadRes);
  }

  return cleanObject({
    ...createRes,
    result: {
      ...result,
      loaded: true
    }
  });
}

export async function handleExportLevel(argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const res = await executeAutomationRequest(tools, 'manage_level', {
    action: 'export_level',
    levelPath: argsTyped.levelPath,
    exportPath: argsTyped.exportPath ?? argsTyped.destinationPath ?? '',
    timeoutMs: typeof argsTyped.timeoutMs === 'number' ? argsTyped.timeoutMs : undefined
  }) as Record<string, unknown>;
  return cleanObject(res);
}

export async function handleImportLevel(argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const res = await executeAutomationRequest(tools, 'manage_level', {
    action: 'import_level',
    packagePath: argsTyped.packagePath ?? argsTyped.sourcePath ?? '',
    destinationPath: argsTyped.destinationPath,
    overwrite: argsTyped.overwrite === true,
    timeoutMs: typeof argsTyped.timeoutMs === 'number' ? argsTyped.timeoutMs : undefined
  }) as Record<string, unknown>;
  return cleanObject(res);
}

export async function handleDeleteLevel(action: string, argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const levelPaths = Array.isArray(argsTyped.levelPaths)
    ? argsTyped.levelPaths.filter((path): path is string => typeof path === 'string')
    : (argsTyped.levelPath ? [argsTyped.levelPath] : []);

  if (levelPaths.length === 0) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'levelPath or levelPaths is required for delete',
      action
    });
  }

  if (levelPaths.length === 1) {
    const res = await executeAutomationRequest(tools, 'manage_level', {
      action: 'delete_level',
      levelPath: levelPaths[0]
    }) as Record<string, unknown>;
    return cleanObject(res);
  }

  const results: Record<string, unknown>[] = [];
  for (const levelPath of levelPaths) {
    const result = await executeAutomationRequest(tools, 'manage_level', {
      action: 'delete_level',
      levelPath
    }) as Record<string, unknown>;
    results.push(cleanObject(result));
  }

  const failed = results.find(result => result.success === false || result.isError === true);
  return cleanObject({
    success: !failed,
    deletedCount: results.filter(result => result.success !== false && result.isError !== true).length,
    results,
    error: failed ? 'DELETE_FAILED' : undefined,
    message: failed ? 'One or more level deletes failed' : 'Levels deleted'
  });
}

export async function handleRenameLevel(action: string, argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const sourcePath = argsTyped.levelPath || argsTyped.sourcePath;
  if (!sourcePath) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'levelPath or sourcePath is required for rename_level',
      action
    });
  }
  if (!argsTyped.newName) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'newName is required for rename_level',
      action
    });
  }

  const lastSlash = sourcePath.lastIndexOf('/');
  const parentDir = lastSlash > 0 ? sourcePath.substring(0, lastSlash) : '/Game';
  const destinationPath = `${parentDir}/${argsTyped.newName}`;
  const res = await executeAutomationRequest(tools, 'manage_level', {
    action: 'rename',
    levelPath: sourcePath,
    destinationPath,
    overwrite: argsTyped.overwrite === true
  });
  return cleanObject(res) as Record<string, unknown>;
}

export async function handleDuplicateLevel(action: string, argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const sourcePath = argsTyped.sourcePath || argsTyped.levelPath;
  if (!sourcePath) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'sourcePath or levelPath is required for duplicate_level',
      action
    });
  }
  if (!argsTyped.destinationPath) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'destinationPath is required for duplicate_level',
      action
    });
  }
  const res = await executeAutomationRequest(tools, 'manage_level', {
    action: 'duplicate',
    sourcePath,
    destinationPath: argsTyped.destinationPath,
    overwrite: argsTyped.overwrite === true
  });
  return cleanObject(res) as Record<string, unknown>;
}

export async function handleValidateLevel(argsTyped: LevelArgs, tools: ITools): Promise<Record<string, unknown>> {
  const levelPath = requireNonEmptyString(argsTyped.levelPath, 'levelPath', 'Missing required parameter: levelPath');
  const automationBridge = tools.automationBridge;
  if (!automationBridge || typeof automationBridge.sendAutomationRequest !== 'function' || !automationBridge.isConnected()) {
    return cleanObject({
      success: false,
      error: 'BRIDGE_UNAVAILABLE',
      message: 'Automation bridge not available; cannot validate level asset',
      levelPath
    });
  }

  try {
    const resp = await automationBridge.sendAutomationRequest('execute_editor_function', {
      functionName: 'ASSET_EXISTS_SIMPLE',
      path: levelPath
    }) as AutomationResponse;
    const respState = resp as { success?: boolean; isError?: boolean };
    if (respState.success === false || respState.isError === true) {
      return cleanObject(resp as Record<string, unknown>);
    }

    const result = (resp?.result ?? {}) as ResultPayload;
    const exists = Boolean(result.exists);
    return cleanObject({
      success: true,
      exists,
      levelPath: result.path ?? levelPath,
      classPath: result.class,
      error: exists ? undefined : 'NOT_FOUND',
      message: exists ? 'Level asset exists' : 'Level asset not found'
    });
  } catch (err) {
    return cleanObject({
      success: false,
      error: 'VALIDATION_FAILED',
      message: `Level validation failed: ${err instanceof Error ? err.message : String(err)}`,
      levelPath
    });
  }
}
