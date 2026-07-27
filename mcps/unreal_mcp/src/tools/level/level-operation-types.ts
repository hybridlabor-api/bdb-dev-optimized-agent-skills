import type { AutomationBridge } from '../../automation/index.js';
import type { LevelResponse } from '../../types/automation/automation-responses.js';
import type { UnrealBridge } from '../../unreal-bridge.js';
import type { ManagedLevelState } from './level-state.js';

export interface LevelOperationContext {
  readonly state: ManagedLevelState;
  readonly bridge: UnrealBridge;
  readonly getAutomationBridge: () => AutomationBridge;
  readonly sendAutomationRequest: <T = LevelResponse>(
    action: string,
    params?: Record<string, unknown>,
    options?: { timeoutMs?: number; waitForEvent?: boolean; waitForEventTimeoutMs?: number }
  ) => Promise<T>;
}
