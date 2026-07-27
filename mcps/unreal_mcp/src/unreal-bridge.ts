import type { AutomationBridge } from './automation/index.js';
import { UnrealCommandQueue } from './utils/commands/unreal-command-queue.js';
import { Logger } from './utils/logging/logger.js';
import type { StandardActionResponse } from './types/tools/tool-interfaces.js';
import {
  configureAutomationBridge,
  connectAutomationBridge,
  tryConnectWithBackoff,
  type AutomationBridgeListeners
} from './unreal-bridge-connection.js';
import {
  executeBatchConsoleCommands as executeBatchConsoleCommandsViaBridge,
  executeConsoleCommand as executeConsoleCommandViaBridge,
  executeConsoleCommands as executeConsoleCommandsViaBridge
} from './unreal-bridge-console.js';
import {
  executeEditorFunction as executeEditorFunctionViaBridge,
  getEngineVersion as getEngineVersionViaBridge,
  getFeatureFlags as getFeatureFlagsViaBridge
} from './unreal-bridge-system.js';
import {
  getObjectProperty as getObjectPropertyViaBridge,
  setObjectProperty as setObjectPropertyViaBridge
} from './unreal-bridge-properties.js';
import type {
  BatchConsoleCommand,
  BatchConsoleOptions,
  BatchConsoleResult,
  ConsoleCommandContext,
  EngineVersionInfo,
  FeatureFlagsInfo,
  ObjectPropertyReadParams,
  ObjectPropertyWriteParams
} from './unreal-bridge-types.js';

export class UnrealBridge {
  private log = new Logger('UnrealBridge');
  private connected = false;
  private automationBridge?: AutomationBridge;
  private automationBridgeListeners?: AutomationBridgeListeners;
  private connectPromise?: Promise<void>;
  private commandQueue = new UnrealCommandQueue();

  get isConnected() { return this.connected; }

  setAutomationBridge(automationBridge?: AutomationBridge): void {
    const listeners = configureAutomationBridge({
      currentBridge: this.automationBridge,
      listeners: this.automationBridgeListeners,
      nextBridge: automationBridge,
      log: this.log,
      setConnected: connected => {
        this.connected = connected;
      }
    });

    this.automationBridge = automationBridge;
    this.automationBridgeListeners = listeners;
  }

  getAutomationBridge(): AutomationBridge {
    if (!this.automationBridge) {
      throw new Error('Automation bridge is not configured');
    }
    return this.automationBridge;
  }

  async tryConnect(maxAttempts: number = 3, timeoutMs: number = 15000, retryDelayMs: number = 3000): Promise<boolean> {
    return tryConnectWithBackoff({
      log: this.log,
      getConnected: () => this.connected,
      setConnected: connected => {
        this.connected = connected;
      },
      getAutomationBridge: () => this.automationBridge,
      getConnectPromise: () => this.connectPromise,
      setConnectPromise: promise => {
        this.connectPromise = promise;
      },
      connect: timeout => this.connect(timeout)
    }, maxAttempts, timeoutMs, retryDelayMs);
  }

  async connect(timeoutMs: number = 15000): Promise<void> {
    await connectAutomationBridge({
      getAutomationBridge: () => this.automationBridge,
      setConnected: connected => {
        this.connected = connected;
      },
      log: this.log
    }, timeoutMs);
  }

  async getObjectProperty(params: ObjectPropertyReadParams): Promise<StandardActionResponse> {
    return getObjectPropertyViaBridge(this.automationBridge, params);
  }

  async setObjectProperty(params: ObjectPropertyWriteParams): Promise<StandardActionResponse> {
    return setObjectPropertyViaBridge(this.automationBridge, params);
  }

  async executeConsoleCommand(command: string): Promise<StandardActionResponse> {
    return executeConsoleCommandViaBridge(this.createConsoleContext(), command);
  }

  async executeConsoleCommands(
    commands: Iterable<string | BatchConsoleCommand>,
    options: BatchConsoleOptions = {}
  ): Promise<unknown[]> {
    return executeConsoleCommandsViaBridge(this.createConsoleContext(), commands, options);
  }

  async executeBatchConsoleCommands(
    commands: string[],
    options: { timeoutMs?: number } = {}
  ): Promise<BatchConsoleResult> {
    return executeBatchConsoleCommandsViaBridge(this.createConsoleContext(), commands, options);
  }

  async executeEditorFunction(
    functionName: string,
    params?: Record<string, unknown>,
    options?: { timeoutMs?: number }
  ): Promise<StandardActionResponse> {
    return executeEditorFunctionViaBridge(this.automationBridge, functionName, params, options);
  }

  async getEngineVersion(): Promise<EngineVersionInfo> {
    return getEngineVersionViaBridge(this.getAutomationBridge(), this.log);
  }

  async getFeatureFlags(): Promise<FeatureFlagsInfo> {
    return getFeatureFlagsViaBridge(this.getAutomationBridge(), this.log);
  }

  dispose(): void {
    try {
      this.commandQueue.stopProcessor();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.log.debug('Failed to stop command queue processor', message);
    }
  }

  private createConsoleContext(): ConsoleCommandContext {
    return {
      log: this.log,
      getAutomationBridge: () => this.automationBridge,
      runThrottled: (command, priority) => this.commandQueue.execute(command, priority)
    };
  }
}
