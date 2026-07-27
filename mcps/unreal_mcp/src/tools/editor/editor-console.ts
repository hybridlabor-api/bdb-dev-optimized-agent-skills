import type { UnrealBridge } from '../../unreal-bridge.js';
import type { StandardActionResponse } from '../../types/tools/tool-interfaces.js';

export async function executeSimpleEditorCommand(
  bridge: UnrealBridge,
  command: string,
  successMessage: string,
  errorPrefix: string
): Promise<StandardActionResponse> {
  try {
    await bridge.executeConsoleCommand(command);
    return { success: true, message: successMessage };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: `${errorPrefix}: ${message}` };
  }
}

export async function stepPIEFrames(bridge: UnrealBridge, steps: number = 1): Promise<StandardActionResponse> {
  const clampedSteps = Number.isFinite(steps) ? Math.max(1, Math.floor(steps)) : 1;
  try {
    for (let index = 0; index < clampedSteps; index += 1) {
      await bridge.executeConsoleCommand('Step=1');
    }
    return {
      success: true,
      message: `Advanced PIE by ${clampedSteps} frame(s)`,
      steps: clampedSteps
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: `Failed to step PIE: ${message}` };
  }
}

export async function setViewportResolutionCommand(
  bridge: UnrealBridge,
  width: number,
  height: number
): Promise<StandardActionResponse> {
  try {
    const clampedWidth = Math.max(320, Math.min(7680, width));
    const clampedHeight = Math.max(240, Math.min(4320, height));
    const command = `r.SetRes ${clampedWidth}x${clampedHeight}`;
    await bridge.executeConsoleCommand(command);

    return {
      success: true,
      message: `Viewport resolution set to ${clampedWidth}x${clampedHeight}`,
      width: clampedWidth,
      height: clampedHeight
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: `Failed to set viewport resolution: ${message}` };
  }
}

export async function executeUserConsoleCommand(
  bridge: UnrealBridge,
  command: string
): Promise<StandardActionResponse> {
  try {
    if (!command || typeof command !== 'string') {
      return { success: false, error: 'Invalid command: must be a non-empty string' };
    }

    if (command.length > 1000) {
      return {
        success: false,
        error: `Command too long (${command.length} chars). Maximum is 1000 characters.`
      };
    }

    const res = await bridge.executeConsoleCommand(command);
    return {
      success: true,
      message: `Console command executed: ${command}`,
      output: res
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: `Failed to execute console command: ${message}` };
  }
}
