import { BaseTool } from '../catalog/base-tool.js';
import { StandardActionResponse } from '../../types/tools/tool-interfaces.js';
import { EditorResponse } from '../../types/automation/automation-responses.js';
import {
  executeSimpleEditorCommand,
  executeUserConsoleCommand,
  setViewportResolutionCommand,
  stepPIEFrames
} from './editor-console.js';
import {
  CameraLocationInput,
  CameraRotationInput,
  getViewportCameraInfo,
  normalizeViewportCameraInput
} from './editor-camera.js';
import { buildScreenshotCommand } from './editor-screenshot.js';
import { EditorStateStore, RecordingOptions } from './editor-state.js';

export class EditorTools extends BaseTool {
  private editorState = new EditorStateStore();

  async isInPIE(): Promise<boolean> {
    try {
      const response = await this.sendAutomationRequest<EditorResponse>(
        'check_pie_state',
        {},
        { timeoutMs: 5000 }
      );

      if (response && response.success !== false) {
        return response.isInPIE === true || (response.result as Record<string, unknown> | undefined)?.isInPIE === true;
      }

      return false;
    } catch (error) {
      if (!(error instanceof Error)) {
        throw error;
      }
      return false;
    }
  }

  async ensureNotInPIE(): Promise<void> {
    if (await this.isInPIE()) {
      await this.stopPlayInEditor();
      // Wait a bit for PIE to fully stop
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }

  async playInEditor(timeoutMs: number = 30000): Promise<StandardActionResponse> {
    try {
      try {
        const response = await this.sendAutomationRequest<EditorResponse>(
          'control_editor',
          { action: 'play' },
          { timeoutMs }
        );
        if (response && response.success === true) {
          return { success: true, message: response.message || 'PIE started' };
        }
        return { success: false, error: response?.error || response?.message || 'Failed to start PIE' };
      } catch (err: unknown) {
        // If it's a timeout, return error instead of falling back
        const errMsg = err instanceof Error ? err.message : String(err);
        if (errMsg && /time.*out/i.test(errMsg)) {
          return { success: false, error: `Timeout waiting for PIE to start: ${errMsg}` };
        }

        // Fallback to console commands if automation bridge is unavailable or fails (non-timeout)
        await this.bridge.executeConsoleCommand('t.MaxFPS 60');
        await this.bridge.executeConsoleCommand('PlayInViewport');
        return { success: true, message: 'PIE start command sent' };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { success: false, error: `Failed to start PIE: ${message}` };
    }
  }

  async stopPlayInEditor(): Promise<StandardActionResponse> {
    try {
      try {
        const response = await this.sendAutomationRequest<EditorResponse>(
          'control_editor',
          { action: 'stop' },
          { timeoutMs: 30000 }
        );

        if (response.success !== false) {
          return {
            success: true,
            message: response.message || 'PIE stopped successfully'
          };
        }

        return {
          success: false,
          error: response.error || response.message || 'Failed to stop PIE'
        };
      } catch (_pluginErr) {
        if (!(_pluginErr instanceof Error)) {
          throw _pluginErr;
        }
        await this.bridge.executeConsoleCommand('stop');
        return { success: true, message: 'PIE stopped via console command' };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { success: false, error: `Failed to stop PIE: ${message}` };
    }
  }

  async pausePlayInEditor(): Promise<StandardActionResponse> {
    return executeSimpleEditorCommand(this.bridge, 'pause', 'PIE paused/resumed', 'Failed to pause PIE');
  }

  // Alias for consistency with naming convention
  async pauseInEditor(): Promise<StandardActionResponse> {
    return this.pausePlayInEditor();
  }

  async buildLighting(): Promise<StandardActionResponse> {
    return executeSimpleEditorCommand(this.bridge, 'BuildLighting', 'Lighting build started', 'Failed to build lighting');
  }

  private async getViewportCameraInfo(): Promise<{
    success: boolean;
    location?: [number, number, number];
    rotation?: [number, number, number];
    error?: string;
    message?: string;
  }> {
    return getViewportCameraInfo((action, params, options) =>
      this.sendAutomationRequest<EditorResponse>(action, params, options)
    );
  }

  async setViewportCamera(location?: CameraLocationInput | null | undefined, rotation?: CameraRotationInput | null | undefined): Promise<StandardActionResponse> {
    const normalizedCamera = normalizeViewportCameraInput(location, rotation);

    // Use native control_editor.set_camera when available
    try {
      const resp = await this.sendAutomationRequest<EditorResponse>('control_editor', {
        action: 'set_camera',
        location: normalizedCamera.location,
        rotation: normalizedCamera.rotation
      }, { timeoutMs: 10000 });
      if (resp && resp.success === true) {
        return {
          success: true,
          message: resp.message || 'Camera set',
          location: normalizedCamera.location,
          rotation: normalizedCamera.rotation
        };
      }
      return { success: false, error: resp?.error || resp?.message || 'Failed to set camera' };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { success: false, error: `Camera control failed: ${message}` };
    }
  }

  async setCameraSpeed(speed: number): Promise<StandardActionResponse> {
    return executeSimpleEditorCommand(this.bridge, `camspeed ${speed}`, `Camera speed set to ${speed}`, 'Failed to set camera speed');
  }

  async setFOV(fov: number): Promise<StandardActionResponse> {
    return executeSimpleEditorCommand(this.bridge, `fov ${fov}`, `FOV set to ${fov}`, 'Failed to set FOV');
  }

  async takeScreenshot(filename?: string, resolution?: string): Promise<StandardActionResponse> {
    try {
      const screenshot = buildScreenshotCommand(filename, resolution);
      if (!screenshot.valid) return { success: false, error: screenshot.error };

      await this.bridge.executeConsoleCommand(screenshot.command);

      return {
        success: true,
        message: `Screenshot captured: ${screenshot.filename}`,
        filename: screenshot.filename,
        command: screenshot.command
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { success: false, error: `Failed to take screenshot: ${message}` };
    }
  }

  async resumePlayInEditor(): Promise<StandardActionResponse> {
    return executeSimpleEditorCommand(this.bridge, 'pause', 'PIE resume toggled via pause command', 'Failed to resume PIE');
  }

  async stepPIEFrame(steps: number = 1): Promise<StandardActionResponse> {
    return stepPIEFrames(this.bridge, steps);
  }

  async startRecording(options?: RecordingOptions): Promise<StandardActionResponse> {
    return this.editorState.startRecording(options);
  }

  async stopRecording(): Promise<StandardActionResponse> {
    return this.editorState.stopRecording();
  }

  async createCameraBookmark(name: string): Promise<StandardActionResponse> {
    return this.editorState.createCameraBookmark(name, await this.getViewportCameraInfo());
  }

  async jumpToCameraBookmark(name: string): Promise<StandardActionResponse> {
    const lookup = this.editorState.getCameraBookmark(name);
    if (!lookup.success) return lookup.response;

    await this.setViewportCamera(
      { x: lookup.bookmark.location[0], y: lookup.bookmark.location[1], z: lookup.bookmark.location[2] },
      { pitch: lookup.bookmark.rotation[0], yaw: lookup.bookmark.rotation[1], roll: lookup.bookmark.rotation[2] }
    );

    return this.editorState.createJumpResponse(lookup.name);
  }

  async setEditorPreferences(category: string | undefined, preferences: Record<string, unknown>): Promise<StandardActionResponse> {
    return this.editorState.setEditorPreferences(category, preferences);
  }

  async setViewportResolution(width: number, height: number): Promise<StandardActionResponse> {
    return setViewportResolutionCommand(this.bridge, width, height);
  }

  async executeConsoleCommand(command: string): Promise<StandardActionResponse> {
    return executeUserConsoleCommand(this.bridge, command);
  }
}
