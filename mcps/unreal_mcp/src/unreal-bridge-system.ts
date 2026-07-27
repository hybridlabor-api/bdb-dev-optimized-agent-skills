import type { AutomationBridge } from './automation/index.js';
import { ENGINE_QUERY_TIMEOUT_MS } from './constants.js';
import type { StandardActionResponse } from './types/tools/tool-interfaces.js';
import { isRecord, responsePayloadRecord } from './unreal-bridge-response.js';
import type {
  AutomationRequestResponse,
  EngineVersionInfo,
  FeatureFlagsInfo,
  StandardEditorOptions,
  UnrealBridgeLogger
} from './unreal-bridge-types.js';

function defaultEngineVersion(): EngineVersionInfo {
  return {
    version: 'unknown',
    major: 0,
    minor: 0,
    patch: 0,
    isUE56OrAbove: false
  };
}

function normalizeEngineVersion(raw: Record<string, unknown>): EngineVersionInfo {
  const major = typeof raw.major === 'number' ? raw.major : 0;
  const minor = typeof raw.minor === 'number' ? raw.minor : 0;
  const patch = typeof raw.patch === 'number' ? raw.patch : 0;
  const isUE56OrAbove =
    typeof raw.isUE56OrAbove === 'boolean'
      ? raw.isUE56OrAbove
      : (major > 5 || (major === 5 && minor >= 6));

  return {
    version: typeof raw.version === 'string' ? raw.version : 'unknown',
    major,
    minor,
    patch,
    isUE56OrAbove
  };
}

export async function executeEditorFunction(
  bridge: AutomationBridge | undefined,
  functionName: string,
  params?: Record<string, unknown>,
  options?: StandardEditorOptions
): Promise<StandardActionResponse> {
  if (process.env.MOCK_UNREAL_CONNECTION === 'true') {
    return { success: true, result: { status: 'mock_success', function: functionName } };
  }

  if (!bridge || typeof bridge.sendAutomationRequest !== 'function') {
    return { success: false, error: 'AUTOMATION_BRIDGE_UNAVAILABLE' };
  }

  const response = await bridge.sendAutomationRequest<StandardActionResponse>('execute_editor_function', {
    functionName,
    params: params ?? {}
  }, options?.timeoutMs ? { timeoutMs: options.timeoutMs } : undefined);

  if (response.success !== false && isRecord(response.result)) {
    const resultSuccess = response.result.success;
    return {
      ...response.result,
      success: typeof resultSuccess === 'boolean' ? resultSuccess : true
    };
  }

  return response;
}

export async function getEngineVersion(
  bridge: AutomationBridge,
  log: UnrealBridgeLogger
): Promise<EngineVersionInfo> {
  if (process.env.MOCK_UNREAL_CONNECTION === 'true') {
    return { version: '5.6.0-Mock', major: 5, minor: 6, patch: 0, isUE56OrAbove: true };
  }

  try {
    const response = await bridge.sendAutomationRequest<AutomationRequestResponse>(
      'system_control',
      { action: 'get_engine_version' },
      { timeoutMs: ENGINE_QUERY_TIMEOUT_MS }
    );
    return normalizeEngineVersion(responsePayloadRecord(response));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    log.warn('getEngineVersion failed', message);
    return defaultEngineVersion();
  }
}

export async function getFeatureFlags(
  bridge: AutomationBridge,
  log: UnrealBridgeLogger
): Promise<FeatureFlagsInfo> {
  if (process.env.MOCK_UNREAL_CONNECTION === 'true') {
    return {
      subsystems: {
        unrealEditor: true,
        levelEditor: true,
        editorActor: true
      }
    };
  }

  try {
    const response = await bridge.sendAutomationRequest<AutomationRequestResponse>(
      'system_control',
      { action: 'get_feature_flags' },
      { timeoutMs: ENGINE_QUERY_TIMEOUT_MS }
    );
    const raw = responsePayloadRecord(response);
    const subsystems = isRecord(raw.subsystems) ? raw.subsystems : {};
    return {
      subsystems: {
        unrealEditor: Boolean(subsystems.unrealEditor),
        levelEditor: Boolean(subsystems.levelEditor),
        editorActor: Boolean(subsystems.editorActor)
      }
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    log.warn('getFeatureFlags failed', message);
    return {
      subsystems: {
        unrealEditor: false,
        levelEditor: false,
        editorActor: false
      }
    };
  }
}
