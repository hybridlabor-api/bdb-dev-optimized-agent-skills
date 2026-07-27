import type { StandardActionResponse } from '../../types/tools/tool-interfaces.js';
import type { LevelResponse } from '../../types/automation/automation-responses.js';
import { sanitizeCommandArgument } from '../../utils/validation/validation.js';
import { DEFAULT_ASSET_OP_TIMEOUT_MS, LONG_RUNNING_OP_TIMEOUT_MS } from '../../constants.js';
import type { LevelOperationContext } from './level-operation-types.js';

export async function listLevels(context: LevelOperationContext): Promise<StandardActionResponse> {
  try {
    const response = await context.sendAutomationRequest<LevelResponse>('list_levels', {}, { timeoutMs: 10000 });
    if (response && response.success !== false) {
      const managed = context.state.listManagedLevels();
      const ueLevels = (response.allMaps || []) as Array<Record<string, unknown>>;
      const ueLevelPaths = new Set(ueLevels.map(level => level.path));
      const managedOnly = managed.levels.filter(level => !ueLevelPaths.has(level.path));
      const levels = [...ueLevels, ...managedOnly];
      return {
        ...response,
        success: true,
        message: 'Levels listed from Unreal Engine',
        levels,
        currentMap: response.currentMap,
        currentMapPath: response.currentMapPath,
        currentWorldLevels: response.currentWorldLevels || [],
        data: { levels, count: levels.length },
        managedLevels: managed.levels,
        managedLevelCount: managed.count
      } as StandardActionResponse;
    }
  } catch (error) {
    if (error instanceof Error) return context.state.listManagedLevels();
    return context.state.listManagedLevels();
  }
  return context.state.listManagedLevels();
}

export function getLevelSummary(context: LevelOperationContext, levelPath?: string): StandardActionResponse {
  const resolved = context.state.resolveLevelPath(levelPath);
  if (!resolved) return { success: false, error: 'No level specified' };
  return context.state.summarizeLevel(resolved) as StandardActionResponse;
}

export async function exportLevel(
  context: LevelOperationContext,
  params: { levelPath?: string; exportPath: string; note?: string; timeoutMs?: number }
): Promise<StandardActionResponse> {
  const resolved = context.state.resolveLevelPath(params.levelPath);
  if (!resolved) return { success: false, error: 'No level specified for export' };

  try {
    const res = await context.sendAutomationRequest<LevelResponse>('manage_level', {
      action: 'export_level',
      levelPath: resolved,
      exportPath: params.exportPath
    }, { timeoutMs: params.timeoutMs ?? LONG_RUNNING_OP_TIMEOUT_MS });
    if (res?.success === false) {
      return { success: false, error: res.error || res.message || 'Export failed', levelPath: resolved, exportPath: params.exportPath, details: res } as StandardActionResponse;
    }
    return { success: true, message: `Level exported to ${params.exportPath}`, levelPath: resolved, exportPath: params.exportPath, details: res } as StandardActionResponse;
  } catch (error) {
    return { success: false, error: `Export failed: ${error instanceof Error ? error.message : String(error)}` };
  }
}

export async function importLevel(
  context: LevelOperationContext,
  params: { packagePath: string; destinationPath?: string; streaming?: boolean; timeoutMs?: number }
): Promise<StandardActionResponse> {
  const destination = params.destinationPath
    ? context.state.normalizeLevelPath(params.destinationPath)
    : context.state.normalizeLevelPath(`/Game/Maps/Imported_${Math.floor(Date.now() / 1000)}`);
  try {
    const res = await context.sendAutomationRequest<LevelResponse>('manage_level', {
      action: 'import_level',
      packagePath: params.packagePath,
      destinationPath: destination.path
    }, { timeoutMs: params.timeoutMs ?? LONG_RUNNING_OP_TIMEOUT_MS });
    if (res?.success === false) {
      return { success: false, error: res.error || res.message || 'Import failed', levelPath: destination.path, details: res } as StandardActionResponse;
    }
    return { success: true, message: `Level imported to ${destination.path}`, levelPath: destination.path, partitioned: true, streaming: Boolean(params.streaming), details: res } as StandardActionResponse;
  } catch (error) {
    return { success: false, error: `Import failed: ${error instanceof Error ? error.message : String(error)}` };
  }
}

export async function saveLevelAs(
  context: LevelOperationContext,
  params: { sourcePath?: string; targetPath: string }
): Promise<StandardActionResponse> {
  const source = context.state.resolveLevelPath(params.sourcePath);
  const target = context.state.normalizeLevelPath(params.targetPath);
  try {
    const response = await context.sendAutomationRequest<LevelResponse>('manage_level', { action: 'save_level_as', savePath: target.path }, { timeoutMs: DEFAULT_ASSET_OP_TIMEOUT_MS });
    if (response.success === false) return { success: false, error: response.error || response.message || 'Failed to save level as' };
    const sourceRecord = source ? context.state.getRecord(source) : undefined;
    const now = Date.now();
    context.state.ensureRecord(target.path, {
      name: target.name,
      partitioned: sourceRecord?.partitioned ?? true,
      streaming: sourceRecord?.streaming ?? false,
      loaded: true,
      visible: true,
      metadata: { ...(sourceRecord?.metadata ?? {}), ...(source ? { savedFrom: source } : {}) },
      exports: sourceRecord?.exports ?? [],
      lights: sourceRecord?.lights ?? [],
      createdAt: sourceRecord?.createdAt ?? now,
      lastSavedAt: now
    });
    context.state.setCurrentLevel(target.path);
    return { success: true, message: response.message || `Level saved as ${target.path}`, levelPath: target.path } as StandardActionResponse;
  } catch (error) {
    return { success: false, error: `Failed to save level as: ${error instanceof Error ? error.message : String(error)}` };
  }
}

export function deleteLevels(context: LevelOperationContext, params: { levelPaths: string[] }): StandardActionResponse {
  const removed: string[] = [];
  for (const path of params.levelPaths) {
    const normalized = context.state.normalizeLevelPath(path).path;
    if (context.state.getRecord(normalized)) {
      context.state.removeRecord(normalized);
      removed.push(normalized);
    }
  }
  return { success: true, message: removed.length ? `Deleted ${removed.length} managed level(s)` : 'No managed levels removed', removed } as StandardActionResponse;
}

export async function saveLevel(context: LevelOperationContext, params: { levelName?: string; savePath?: string }): Promise<StandardActionResponse> {
  try {
    if (params.savePath && !params.savePath.startsWith('/Game/')) throw new Error(`Invalid save path: ${params.savePath}`);
    const payload: Record<string, unknown> = { action: params.savePath ? 'save_level_as' : 'save' };
    if (params.savePath) payload.savePath = params.savePath;
    const response = await context.sendAutomationRequest<LevelResponse>('manage_level', payload, { timeoutMs: DEFAULT_ASSET_OP_TIMEOUT_MS });
    if (response.success === false) return { success: false, error: response.error || response.message || 'Failed to save level' };
    return { ...response, success: true, message: response.message || 'Level saved' } as StandardActionResponse;
  } catch (error) {
    return { success: false, error: `Failed to save level: ${error instanceof Error ? error.message : String(error)}` };
  }
}

export async function createLevel(
  context: LevelOperationContext,
  params: { levelName: string; template?: 'Empty' | 'Default' | 'VR' | 'TimeOfDay'; savePath?: string; useWorldPartition?: boolean }
): Promise<StandardActionResponse> {
  const sanitizedName = sanitizeCommandArgument(params.levelName);
  const isPartitioned = params.useWorldPartition ?? false;
  const normalizedPath = params.savePath ? context.state.normalizeLevelPath(params.savePath).path : '/Game/Maps';
  const pathSegments = normalizedPath.split('/').filter(segment => segment.length > 0);
  const lastSegment = pathSegments[pathSegments.length - 1];
  const fullPath = params.savePath && lastSegment?.toLowerCase() === sanitizedName.toLowerCase()
    ? normalizedPath
    : `${normalizedPath}/${sanitizedName}`;
  try {
    const response = await context.sendAutomationRequest<LevelResponse>('create_new_level', { levelPath: fullPath, useWorldPartition: isPartitioned }, { timeoutMs: DEFAULT_ASSET_OP_TIMEOUT_MS });
    if (response.success === false) return { success: false, error: response.error || response.message || 'Failed to create level', path: fullPath, partitioned: isPartitioned } as StandardActionResponse;
    context.state.ensureRecord(fullPath, { name: params.levelName, partitioned: isPartitioned, loaded: true, visible: true, createdAt: Date.now() });
    return { ...response, success: true, message: response.message || 'Level created', path: response.levelPath || fullPath, packagePath: response.packagePath ?? fullPath, objectPath: response.objectPath, partitioned: isPartitioned } as StandardActionResponse;
  } catch (error) {
    return { success: false, error: `Failed to create level: ${error instanceof Error ? error.message : String(error)}`, path: fullPath, partitioned: isPartitioned } as StandardActionResponse;
  }
}
