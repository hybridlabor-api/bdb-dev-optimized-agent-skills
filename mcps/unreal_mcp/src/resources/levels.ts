import { UnrealBridge } from '../unreal-bridge.js';
import type { AutomationRequestBridge } from '../types/tools/tool-interfaces.js';
import { coerceString } from '../utils/responses/result-helpers.js';
import { isRecord } from '../utils/validation/type-guards.js';

const LIST_LEVELS_ACTION = 'list_levels';
const BRIDGE_UNAVAILABLE = 'Automation bridge is not available';

export class LevelResources {
  private automationBridge: AutomationRequestBridge | undefined;

  constructor(_bridge: UnrealBridge, automationBridge?: AutomationRequestBridge) {
    this.automationBridge = automationBridge;
  }

  async getCurrentLevel() {
    try {
      const resp = await this.sendAutomationRequest(LIST_LEVELS_ACTION);
      if (!resp) {
        return { success: false, error: BRIDGE_UNAVAILABLE };
      }

      if (resp.success !== false) {
        const result = this.getNestedResult(resp);
        const name = coerceString(resp.currentMap) ?? coerceString(result?.currentMap) ?? 'None';
        const path = coerceString(resp.currentMapPath) ?? coerceString(result?.currentMapPath) ?? 'None';
        return { success: true, name, path };
      }

      return { success: false, error: 'Failed to get current level' };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { error: `Failed to get current level: ${message}`, success: false };
    }
  }

  async getLevelName() {
    try {
      const resp = await this.sendAutomationRequest(LIST_LEVELS_ACTION);
      if (!resp) {
        return { success: false, error: BRIDGE_UNAVAILABLE };
      }

      if (resp.success !== false) {
        const result = this.getNestedResult(resp);
        return {
          success: true,
          path: coerceString(resp.currentMapPath) ?? coerceString(result?.currentMapPath) ?? ''
        };
      }

      return { success: false, error: 'Failed to get level name' };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { error: `Failed to get level name: ${message}`, success: false };
    }
  }

  async saveCurrentLevel() {
    try {
      const resp = await this.sendAutomationRequest('save_level');
      if (!resp) {
        return { success: false, error: BRIDGE_UNAVAILABLE };
      }

      if (resp.success !== false) {
        return { success: true, message: 'Level saved' };
      }

      return { success: false, error: 'Failed to save level' };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { error: `Failed to save level: ${message}`, success: false };
    }
  }

  private async sendAutomationRequest(action: string): Promise<Record<string, unknown> | undefined> {
    if (!this.automationBridge || typeof this.automationBridge.sendAutomationRequest !== 'function') {
      return undefined;
    }

    const response = await this.automationBridge.sendAutomationRequest(action, {});
    return isRecord(response) ? response : {};
  }

  private getNestedResult(response: Record<string, unknown>): Record<string, unknown> | undefined {
    return isRecord(response.result) ? response.result : undefined;
  }

}
