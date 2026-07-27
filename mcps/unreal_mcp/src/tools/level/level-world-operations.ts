import type { StandardActionResponse } from '../../types/tools/tool-interfaces.js';
import type { LevelResponse } from '../../types/automation/automation-responses.js';
import { sanitizeCommandArgument } from '../../utils/validation/validation.js';
import type { LevelOperationContext } from './level-operation-types.js';

export async function setupWorldComposition(
  context: LevelOperationContext,
  params: { enableComposition: boolean; tileSize?: number; distanceStreaming?: boolean; streamingDistance?: number }
): Promise<StandardActionResponse> {
  const commands: string[] = [];
  if (params.enableComposition) {
    commands.push('EnableWorldComposition');
    if (params.tileSize) commands.push(`SetWorldTileSize ${params.tileSize}`);
    if (params.distanceStreaming) commands.push(`EnableDistanceStreaming ${params.streamingDistance || 5000}`);
  } else {
    commands.push('DisableWorldComposition');
  }
  await context.bridge.executeConsoleCommands(commands);
  return { success: true, message: 'World composition configured' };
}

export function editLevelBlueprint(
  context: LevelOperationContext,
  params: { eventType: 'BeginPlay' | 'EndPlay' | 'Tick' | 'Custom'; customEventName?: string; nodes?: Array<{ nodeType: string; position: [number, number]; connections?: string[] }> }
): Promise<StandardActionResponse> {
  return context.bridge.executeConsoleCommand(`OpenLevelBlueprint ${sanitizeCommandArgument(params.eventType)}`);
}

export function createSubLevel(
  context: LevelOperationContext,
  params: { name: string; type: 'Persistent' | 'Streaming' | 'Lighting' | 'Gameplay'; parent?: string }
): Promise<StandardActionResponse> {
  const parent = params.parent ? sanitizeCommandArgument(params.parent) : 'None';
  return context.bridge.executeConsoleCommand(`CreateSubLevel ${sanitizeCommandArgument(params.name)} ${sanitizeCommandArgument(params.type)} ${parent}`);
}

export async function setWorldSettings(
  context: LevelOperationContext,
  params: { gravity?: number; worldScale?: number; gameMode?: string; defaultPawn?: string; killZ?: number }
): Promise<StandardActionResponse> {
  const commands: string[] = [];
  if (params.gravity !== undefined) commands.push(`SetWorldGravity ${params.gravity}`);
  if (params.worldScale !== undefined) commands.push(`SetWorldToMeters ${params.worldScale}`);
  if (params.gameMode) commands.push(`SetGameMode ${sanitizeCommandArgument(params.gameMode)}`);
  if (params.defaultPawn) commands.push(`SetDefaultPawn ${sanitizeCommandArgument(params.defaultPawn)}`);
  if (params.killZ !== undefined) commands.push(`SetKillZ ${params.killZ}`);
  await context.bridge.executeConsoleCommands(commands);
  return { success: true, message: 'World settings updated' };
}

export function setLevelBounds(
  context: LevelOperationContext,
  params: { min: [number, number, number]; max: [number, number, number] }
): Promise<StandardActionResponse> {
  return context.bridge.executeConsoleCommand(`SetLevelBounds ${params.min.join(',')} ${params.max.join(',')}`);
}

export async function buildNavMesh(
  context: LevelOperationContext,
  params: { rebuildAll?: boolean; selectedOnly?: boolean }
): Promise<StandardActionResponse> {
  try {
    const response = await context.sendAutomationRequest<LevelResponse>('build_navigation_mesh', {
      rebuildAll: params.rebuildAll ?? false,
      selectedOnly: params.selectedOnly ?? false
    }, { timeoutMs: 120000 });
    if (response.success === false) {
      return { success: false, error: response.error || response.message || 'Failed to build navigation' };
    }
    return {
      success: true,
      message: response.message || (params.rebuildAll ? 'Navigation rebuild started' : 'Navigation update started'),
      rebuildAll: params.rebuildAll,
      selectedOnly: params.selectedOnly,
      selectionCount: response.selectionCount,
      warnings: response.warnings,
      details: response.details
    } as StandardActionResponse;
  } catch (error) {
    return {
      success: false,
      error: `Navigation build not available: ${error instanceof Error ? error.message : String(error)}. Please ensure a NavMeshBoundsVolume exists in the level.`
    };
  }
}

export function setLevelVisibility(
  context: LevelOperationContext,
  params: { levelName: string; visible: boolean }
): Promise<StandardActionResponse> {
  return context.bridge.executeConsoleCommand(`SetLevelVisibility ${sanitizeCommandArgument(params.levelName)} ${params.visible}`);
}
