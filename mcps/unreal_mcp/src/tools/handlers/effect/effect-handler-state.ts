import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';

export const DEFAULT_EFFECT_SAVE_PATH = '/Game/MCPTest/ManageEffectDefaults';
export const DEFAULT_NIAGARA_SYSTEM_NAME = `MCP_ManageEffectDefaultSystem_${process.pid}`;
export const DEFAULT_NIAGARA_EMITTER_ASSET_NAME = `MCP_ManageEffectDefaultEmitter_${process.pid}`;
export const DEFAULT_NIAGARA_AUTHORING_SYSTEM_NAME = `MCP_ManageEffectAuthoringSystem_${process.pid}`;
export const DEFAULT_NIAGARA_AUTHORING_EMITTER_ASSET_NAME = `MCP_ManageEffectAuthoringEmitter_${process.pid}`;
export const DEFAULT_NIAGARA_EMITTER_NAME = 'DefaultEmitter';
export const DEFAULT_NIAGARA_ACTOR_NAME = `MCP_ManageEffectDefaultActor_${process.pid}`;

let defaultNiagaraAssetsPromise: Promise<{ systemPath: string; emitterPath: string }> | undefined;
let defaultNiagaraAuthoringAssetsPromise: Promise<{ systemPath: string; emitterPath: string }> | undefined;
let lastCreatedNiagaraSystemPath: string | undefined;
let lastCreatedNiagaraEmitterPath: string | undefined;
let lastAddedNiagaraUserParameterName: string | undefined;

function makeGameAssetPath(savePath: string, assetName: string): string {
  return `${savePath.replace(/\/$/, '')}/${assetName}`;
}

function makeGameObjectPath(savePath: string, assetName: string): string {
  const assetPath = makeGameAssetPath(savePath, assetName);
  return `${assetPath}.${assetName}`;
}

export function rememberLastCreatedNiagaraSystemPath(path: unknown): void {
  if (typeof path === 'string' && path.length > 0) {
    lastCreatedNiagaraSystemPath = path;
  }
}

export function rememberLastCreatedNiagaraEmitterPath(path: unknown): void {
  if (typeof path === 'string' && path.length > 0) {
    lastCreatedNiagaraEmitterPath = path;
  }
}

export function rememberLastAddedNiagaraUserParameterName(parameterName: unknown): void {
  if (typeof parameterName === 'string') {
    lastAddedNiagaraUserParameterName = parameterName;
  }
}

export function getLastAddedNiagaraUserParameterName(): string | undefined {
  return lastAddedNiagaraUserParameterName;
}

export async function ensureDefaultNiagaraAssets(tools: ITools): Promise<{ systemPath: string; emitterPath: string }> {
  if (!defaultNiagaraAssetsPromise) {
    defaultNiagaraAssetsPromise = (async () => {
      const systemResult = await executeAutomationRequest(tools, 'create_niagara_system', {
        name: DEFAULT_NIAGARA_SYSTEM_NAME,
        path: DEFAULT_EFFECT_SAVE_PATH,
        savePath: DEFAULT_EFFECT_SAVE_PATH,
        save: false,
      }) as Record<string, unknown>;
      if (systemResult.success === false) {
        throw new Error(`Failed to create default Niagara system: ${String(systemResult.message || systemResult.error || 'unknown error')}`);
      }

      const emitterResult = await executeAutomationRequest(tools, 'create_niagara_emitter', {
        name: DEFAULT_NIAGARA_EMITTER_ASSET_NAME,
        path: DEFAULT_EFFECT_SAVE_PATH,
        savePath: DEFAULT_EFFECT_SAVE_PATH,
        save: false,
      }) as Record<string, unknown>;
      if (emitterResult.success === false) {
        throw new Error(`Failed to create default Niagara emitter: ${String(emitterResult.message || emitterResult.error || 'unknown error')}`);
      }

      const systemPayload = (systemResult.result ?? systemResult) as Record<string, unknown>;
      const emitterPayload = (emitterResult.result ?? emitterResult) as Record<string, unknown>;
      const systemPath = typeof systemPayload.systemPath === 'string' && systemPayload.systemPath.length > 0
        ? systemPayload.systemPath
        : makeGameObjectPath(DEFAULT_EFFECT_SAVE_PATH, DEFAULT_NIAGARA_SYSTEM_NAME);
      const emitterPath = typeof emitterPayload.emitterPath === 'string' && emitterPayload.emitterPath.length > 0
        ? emitterPayload.emitterPath
        : makeGameObjectPath(DEFAULT_EFFECT_SAVE_PATH, DEFAULT_NIAGARA_EMITTER_ASSET_NAME);

      return {
        systemPath,
        emitterPath,
      };
    })();
  }

  return defaultNiagaraAssetsPromise;
}

export async function ensureDefaultNiagaraAuthoringAssets(tools: ITools): Promise<{ systemPath: string; emitterPath: string }> {
  if (lastCreatedNiagaraSystemPath && lastCreatedNiagaraEmitterPath) {
    return {
      systemPath: lastCreatedNiagaraSystemPath,
      emitterPath: lastCreatedNiagaraEmitterPath,
    };
  }

  if (!defaultNiagaraAuthoringAssetsPromise) {
    defaultNiagaraAuthoringAssetsPromise = (async () => {
      const systemResult = await executeAutomationRequest(tools, 'create_niagara_system', {
        name: DEFAULT_NIAGARA_AUTHORING_SYSTEM_NAME,
        path: DEFAULT_EFFECT_SAVE_PATH,
        savePath: DEFAULT_EFFECT_SAVE_PATH,
        save: false,
      }) as Record<string, unknown>;
      if (systemResult.success === false) {
        throw new Error(`Failed to create default Niagara authoring system: ${String(systemResult.message || systemResult.error || 'unknown error')}`);
      }

      const emitterResult = await executeAutomationRequest(tools, 'create_niagara_emitter', {
        name: DEFAULT_NIAGARA_AUTHORING_EMITTER_ASSET_NAME,
        path: DEFAULT_EFFECT_SAVE_PATH,
        savePath: DEFAULT_EFFECT_SAVE_PATH,
        save: false,
      }) as Record<string, unknown>;
      if (emitterResult.success === false) {
        throw new Error(`Failed to create default Niagara authoring emitter: ${String(emitterResult.message || emitterResult.error || 'unknown error')}`);
      }

      const systemPayload = (systemResult.result ?? systemResult) as Record<string, unknown>;
      const emitterPayload = (emitterResult.result ?? emitterResult) as Record<string, unknown>;
      const systemPath = typeof systemPayload.systemPath === 'string' && systemPayload.systemPath.length > 0
        ? systemPayload.systemPath
        : makeGameObjectPath(DEFAULT_EFFECT_SAVE_PATH, DEFAULT_NIAGARA_AUTHORING_SYSTEM_NAME);
      const emitterPath = typeof emitterPayload.emitterPath === 'string' && emitterPayload.emitterPath.length > 0
        ? emitterPayload.emitterPath
        : makeGameObjectPath(DEFAULT_EFFECT_SAVE_PATH, DEFAULT_NIAGARA_AUTHORING_EMITTER_ASSET_NAME);

      return {
        systemPath,
        emitterPath,
      };
    })();
  }

  return defaultNiagaraAuthoringAssetsPromise;
}

export async function ensureDefaultNiagaraActor(tools: ITools): Promise<void> {
  const defaultAssets = await ensureDefaultNiagaraAssets(tools);
  await executeAutomationRequest(tools, 'create_effect', {
    action: 'niagara',
    systemPath: defaultAssets.systemPath,
    actorName: DEFAULT_NIAGARA_ACTOR_NAME,
    location: { x: 0, y: 0, z: 100 },
  });
}
