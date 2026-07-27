import type { StandardActionResponse } from '../../types/tools/tool-interfaces.js';
import type { LevelResponse } from '../../types/automation/automation-responses.js';
import { sanitizeCommandArgument } from '../../utils/validation/validation.js';
import { DEFAULT_ASSET_OP_TIMEOUT_MS, DEFAULT_OPERATION_TIMEOUT_MS } from '../../constants.js';
import type { LevelOperationContext } from './level-operation-types.js';

export async function loadLevel(
  context: LevelOperationContext,
  params: { levelPath: string; streaming?: boolean; position?: [number, number, number] }
): Promise<StandardActionResponse> {
  const normalizedPath = context.state.normalizeLevelPath(params.levelPath).path;
  if (params.streaming) return loadStreamingLevel(context, params.levelPath, normalizedPath);

  try {
    const response = await context.sendAutomationRequest<LevelResponse>('manage_level', {
      action: 'load',
      levelPath: params.levelPath
    }, { timeoutMs: DEFAULT_OPERATION_TIMEOUT_MS });
    if (response.success) {
      context.state.setCurrentLevel(normalizedPath);
      context.state.mutateRecord(normalizedPath, { streaming: false, loaded: true, visible: true });
      return { ...response, success: true, message: `Level loaded: ${params.levelPath}`, level: normalizedPath, streaming: false } as StandardActionResponse;
    }
    return { ...response, success: false, error: response.error || 'LOAD_FAILED', message: response.message || `Failed to load level: ${params.levelPath}`, level: normalizedPath } as StandardActionResponse;
  } catch (bridgeError) {
    if (bridgeError instanceof Error) {
      return loadLevelFallback(context, params.levelPath, normalizedPath, bridgeError);
    }
    return loadLevelFallback(context, params.levelPath, normalizedPath, bridgeError);
  }
}

async function loadStreamingLevel(context: LevelOperationContext, originalPath: string, normalizedPath: string): Promise<StandardActionResponse> {
  try {
    const rawSimpleName = (originalPath || '').split('/').filter(Boolean).pop() || originalPath;
    const simpleName = sanitizeCommandArgument(rawSimpleName);
    await context.bridge.executeConsoleCommand(`StreamLevel ${simpleName} Load Show`);
    context.state.mutateRecord(normalizedPath, { streaming: true, loaded: true, visible: true });
    return { success: true, message: `Streaming level loaded: ${originalPath}`, levelPath: normalizedPath, streaming: true } as StandardActionResponse;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.toString() : String(error);
    return { success: false, error: `Failed to load streaming level: ${errorMessage}`, levelPath: normalizedPath };
  }
}

async function loadLevelFallback(
  context: LevelOperationContext,
  originalPath: string,
  normalizedPath: string,
  bridgeError: unknown
): Promise<StandardActionResponse> {
  let isBridgeConnected = false;
  try {
    const automation = context.getAutomationBridge();
    isBridgeConnected = automation && typeof automation.sendAutomationRequest === 'function' && automation.isConnected();
  } catch (error) {
    if (!(error instanceof Error)) throw error;
  }
  if (isBridgeConnected) {
    return { success: false, error: `Bridge error: ${bridgeError instanceof Error ? bridgeError.message : String(bridgeError)}`, level: normalizedPath } as StandardActionResponse;
  }

  try {
    const existsResp = await context.bridge.executeConsoleCommand(`GetLevelPath ${normalizedPath}`);
    if (!existsResp || (typeof existsResp.message === 'string' && existsResp.message.includes('not found'))) {
      return { success: false, error: 'LEVEL_NOT_FOUND', message: `Level not found: ${originalPath}`, level: normalizedPath } as StandardActionResponse;
    }

    await context.bridge.executeConsoleCommand(`Open ${normalizedPath}`);
    context.state.setCurrentLevel(normalizedPath);
    context.state.mutateRecord(normalizedPath, { streaming: false, loaded: true, visible: true });
    return { success: true, message: `Level loaded: ${originalPath}`, level: normalizedPath, streaming: false } as StandardActionResponse;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.toString() : String(error);
    return { success: false, error: `Failed to load level: ${errorMessage}`, level: normalizedPath };
  }
}

async function addSubLevelWithConsole(context: LevelOperationContext, sub: string): Promise<StandardActionResponse> {
  const consoleResponse = await context.sendAutomationRequest<LevelResponse>('console_command', { command: `LevelEditor.AddLevel ${sub}` });
  if (consoleResponse.success) {
    context.state.ensureRecord(sub, { loaded: true, visible: true, streaming: true });
    return { success: true, message: `Sublevel added via console: ${sub}`, data: { method: 'console' } } as StandardActionResponse;
  }

  return {
    success: false,
    error: 'Fallbacks failed',
    message: 'Failed to add sublevel via automation or console.',
    details: { consoleError: consoleResponse }
  } as StandardActionResponse;
}

export async function addSubLevel(
  context: LevelOperationContext,
  params: { parentLevel?: string; subLevelPath: string; streamingMethod?: 'Blueprint' | 'AlwaysLoaded' }
): Promise<StandardActionResponse> {
  const parent = params.parentLevel ? context.state.resolveLevelPath(params.parentLevel) : context.state.currentLevelPath;
  const sub = context.state.normalizeLevelPath(params.subLevelPath).path;
  try {
    const response = await context.sendAutomationRequest<LevelResponse>('manage_level', {
      action: 'add_sublevel',
      levelPath: sub,
      subLevelPath: sub,
      parentPath: parent,
      streamingMethod: params.streamingMethod
    }, { timeoutMs: DEFAULT_OPERATION_TIMEOUT_MS });
    if (response.success) {
      context.state.ensureRecord(sub, { loaded: true, visible: true, streaming: true });
      return response as StandardActionResponse;
    }
    return response.error === 'UNKNOWN_ACTION' ? addSubLevelWithConsole(context, sub) : response as StandardActionResponse;
  } catch (error) {
    if (error instanceof Error) return addSubLevelWithConsole(context, sub);
    return addSubLevelWithConsole(context, sub);
  }
}

export async function streamLevel(
  context: LevelOperationContext,
  params: { levelPath?: string; levelName?: string; shouldBeLoaded: boolean; shouldBeVisible?: boolean; position?: [number, number, number] }
): Promise<StandardActionResponse> {
  const rawPath = typeof params.levelPath === 'string' ? params.levelPath.trim() : '';
  const levelPath = rawPath.length > 0 ? rawPath : undefined;
  const providedName = typeof params.levelName === 'string' ? params.levelName.trim() : '';
  const levelName = providedName.length > 0 ? providedName : (levelPath ? levelPath.split('/').filter(Boolean).pop() ?? '' : '');
  const shouldBeVisible = params.shouldBeVisible ?? params.shouldBeLoaded;

  try {
    const response = await context.sendAutomationRequest<LevelResponse>('stream_level', {
      levelPath: levelPath || '',
      levelName: levelName || '',
      shouldBeLoaded: params.shouldBeLoaded,
      shouldBeVisible
    }, { timeoutMs: DEFAULT_ASSET_OP_TIMEOUT_MS });
    if (response.success === false) {
      return { success: false, error: response.error || response.message || 'Streaming level update failed', message: response.message, level: levelName || '', levelPath, loaded: params.shouldBeLoaded, visible: shouldBeVisible } as StandardActionResponse;
    }
    return { success: true, message: response.message || 'Streaming level updated', level: levelName || '', levelPath, loaded: params.shouldBeLoaded, visible: shouldBeVisible, warnings: response.warnings, details: response.details } as StandardActionResponse;
  } catch (error) {
    if (!(error instanceof Error)) throw error;
    const levelIdentifier = levelName || levelPath || '';
    const simpleName = sanitizeCommandArgument(levelIdentifier.split('/').filter(Boolean).pop() || levelIdentifier);
    return context.bridge.executeConsoleCommand(`StreamLevel ${simpleName} ${params.shouldBeLoaded ? 'Load' : 'Unload'} ${shouldBeVisible ? 'Show' : 'Hide'}`);
  }
}
