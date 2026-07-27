import { BaseTool } from '../catalog/base-tool.js';
import type { StandardActionResponse } from '../../types/tools/tool-interfaces.js';
import type { LevelOperationContext } from './level-operation-types.js';
import { ManagedLevelState } from './level-state.js';
import {
  createLevel as createLevelOperation,
  deleteLevels as deleteLevelsOperation,
  exportLevel as exportLevelOperation,
  getLevelSummary as getLevelSummaryOperation,
  importLevel as importLevelOperation,
  listLevels as listLevelsOperation,
  saveLevel as saveLevelOperation,
  saveLevelAs as saveLevelAsOperation
} from './level-asset-operations.js';
import {
  addSubLevel as addSubLevelOperation,
  loadLevel as loadLevelOperation,
  streamLevel as streamLevelOperation
} from './level-load-operations.js';
import {
  buildNavMesh as buildNavMeshOperation,
  createSubLevel as createSubLevelOperation,
  editLevelBlueprint as editLevelBlueprintOperation,
  setLevelBounds as setLevelBoundsOperation,
  setLevelVisibility as setLevelVisibilityOperation,
  setWorldSettings as setWorldSettingsOperation,
  setupWorldComposition as setupWorldCompositionOperation
} from './level-world-operations.js';

export class LevelTools extends BaseTool {
  private readonly state = new ManagedLevelState();

  async listLevels(): Promise<StandardActionResponse> {
    return listLevelsOperation(this.createOperationContext());
  }

  async getLevelSummary(levelPath?: string): Promise<StandardActionResponse> {
    return getLevelSummaryOperation(this.createOperationContext(), levelPath);
  }

  registerLight(levelPath: string | undefined, info: { name: string; type: string; details?: Record<string, unknown> }): void {
    this.state.registerLight(levelPath, info);
  }

  async exportLevel(params: { levelPath?: string; exportPath: string; note?: string; timeoutMs?: number }): Promise<StandardActionResponse> {
    return exportLevelOperation(this.createOperationContext(), params);
  }

  async importLevel(params: { packagePath: string; destinationPath?: string; streaming?: boolean; timeoutMs?: number }): Promise<StandardActionResponse> {
    return importLevelOperation(this.createOperationContext(), params);
  }

  async saveLevelAs(params: { sourcePath?: string; targetPath: string }): Promise<StandardActionResponse> {
    return saveLevelAsOperation(this.createOperationContext(), params);
  }

  async deleteLevels(params: { levelPaths: string[] }): Promise<StandardActionResponse> {
    return deleteLevelsOperation(this.createOperationContext(), params);
  }

  async loadLevel(params: { levelPath: string; streaming?: boolean; position?: [number, number, number] }): Promise<StandardActionResponse> {
    return loadLevelOperation(this.createOperationContext(), params);
  }

  async saveLevel(params: { levelName?: string; savePath?: string }): Promise<StandardActionResponse> {
    return saveLevelOperation(this.createOperationContext(), params);
  }

  async createLevel(params: { levelName: string; template?: 'Empty' | 'Default' | 'VR' | 'TimeOfDay'; savePath?: string; useWorldPartition?: boolean }): Promise<StandardActionResponse> {
    return createLevelOperation(this.createOperationContext(), params);
  }

  async addSubLevel(params: { parentLevel?: string; subLevelPath: string; streamingMethod?: 'Blueprint' | 'AlwaysLoaded' }): Promise<StandardActionResponse> {
    return addSubLevelOperation(this.createOperationContext(), params);
  }

  async streamLevel(params: { levelPath?: string; levelName?: string; shouldBeLoaded: boolean; shouldBeVisible?: boolean; position?: [number, number, number] }): Promise<StandardActionResponse> {
    return streamLevelOperation(this.createOperationContext(), params);
  }

  async setupWorldComposition(params: { enableComposition: boolean; tileSize?: number; distanceStreaming?: boolean; streamingDistance?: number }): Promise<StandardActionResponse> {
    return setupWorldCompositionOperation(this.createOperationContext(), params);
  }

  async editLevelBlueprint(params: { eventType: 'BeginPlay' | 'EndPlay' | 'Tick' | 'Custom'; customEventName?: string; nodes?: Array<{ nodeType: string; position: [number, number]; connections?: string[] }> }): Promise<StandardActionResponse> {
    return editLevelBlueprintOperation(this.createOperationContext(), params);
  }

  async createSubLevel(params: { name: string; type: 'Persistent' | 'Streaming' | 'Lighting' | 'Gameplay'; parent?: string }): Promise<StandardActionResponse> {
    return createSubLevelOperation(this.createOperationContext(), params);
  }

  async setWorldSettings(params: { gravity?: number; worldScale?: number; gameMode?: string; defaultPawn?: string; killZ?: number }): Promise<StandardActionResponse> {
    return setWorldSettingsOperation(this.createOperationContext(), params);
  }

  async setLevelBounds(params: { min: [number, number, number]; max: [number, number, number] }): Promise<StandardActionResponse> {
    return setLevelBoundsOperation(this.createOperationContext(), params);
  }

  async buildNavMesh(params: { rebuildAll?: boolean; selectedOnly?: boolean }): Promise<StandardActionResponse> {
    return buildNavMeshOperation(this.createOperationContext(), params);
  }

  async setLevelVisibility(params: { levelName: string; visible: boolean }): Promise<StandardActionResponse> {
    return setLevelVisibilityOperation(this.createOperationContext(), params);
  }

  private createOperationContext(): LevelOperationContext {
    return {
      state: this.state,
      bridge: this.bridge,
      getAutomationBridge: () => this.getAutomationBridge(),
      sendAutomationRequest: (action, params, options) => this.sendAutomationRequest(action, params, options)
    };
  }
}
