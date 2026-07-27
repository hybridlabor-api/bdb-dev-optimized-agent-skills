import { StandardActionResponse } from '../../types/tools/tool-interfaces.js';
import { CameraTuple, ViewportCameraInfo } from './editor-camera.js';

interface CameraBookmark {
  location: CameraTuple;
  rotation: CameraTuple;
  savedAt: number;
}

interface RecordingState {
  name?: string;
  options?: Record<string, unknown>;
  startedAt: number;
}

export interface RecordingOptions {
  filename?: string;
  frameRate?: number;
  durationSeconds?: number;
  metadata?: Record<string, unknown>;
}

type CameraBookmarkLookup =
  | { success: true; name: string; bookmark: CameraBookmark }
  | { success: false; response: StandardActionResponse };

export class EditorStateStore {
  private cameraBookmarks = new Map<string, CameraBookmark>();
  private editorPreferences = new Map<string, Record<string, unknown>>();
  private activeRecording?: RecordingState;

  startRecording(options?: RecordingOptions): StandardActionResponse {
    const startedAt = Date.now();
    this.activeRecording = {
      name: typeof options?.filename === 'string' ? options.filename.trim() : undefined,
      options: options ? { ...options } : undefined,
      startedAt
    };

    return {
      success: true,
      message: 'Recording session started',
      recording: {
        name: this.activeRecording.name,
        startedAt,
        options: this.activeRecording.options
      }
    };
  }

  stopRecording(): StandardActionResponse {
    if (!this.activeRecording) {
      return {
        success: true,
        message: 'No active recording session to stop'
      };
    }

    const stoppedRecording = this.activeRecording;
    this.activeRecording = undefined;

    return {
      success: true,
      message: 'Recording session stopped',
      recording: stoppedRecording
    };
  }

  createCameraBookmark(name: string, cameraInfo: ViewportCameraInfo): StandardActionResponse {
    const trimmedName = name.trim();
    if (!trimmedName) {
      return { success: false, error: 'bookmarkName is required' };
    }

    if (!cameraInfo.success || !cameraInfo.location || !cameraInfo.rotation) {
      return {
        success: false,
        error: cameraInfo.error || 'Failed to capture viewport camera'
      };
    }

    this.cameraBookmarks.set(trimmedName, {
      location: cameraInfo.location,
      rotation: cameraInfo.rotation,
      savedAt: Date.now()
    });

    return {
      success: true,
      message: `Bookmark '${trimmedName}' saved`,
      bookmark: {
        name: trimmedName,
        location: cameraInfo.location,
        rotation: cameraInfo.rotation
      }
    };
  }

  getCameraBookmark(name: string): CameraBookmarkLookup {
    const trimmedName = name.trim();
    if (!trimmedName) {
      return { success: false, response: { success: false, error: 'bookmarkName is required' } };
    }

    const bookmark = this.cameraBookmarks.get(trimmedName);
    if (!bookmark) {
      return {
        success: false,
        response: {
          success: false,
          error: `Bookmark '${trimmedName}' not found`
        }
      };
    }

    return { success: true, name: trimmedName, bookmark };
  }

  createJumpResponse(name: string): StandardActionResponse {
    return {
      success: true,
      message: `Jumped to bookmark '${name}'`
    };
  }

  setEditorPreferences(category: string | undefined, preferences: Record<string, unknown>): StandardActionResponse {
    const resolvedCategory = typeof category === 'string' && category.trim().length > 0 ? category.trim() : 'General';
    const existing = this.editorPreferences.get(resolvedCategory) ?? {};
    this.editorPreferences.set(resolvedCategory, { ...existing, ...preferences });

    return {
      success: true,
      message: `Preferences stored for ${resolvedCategory}`,
      preferences: this.editorPreferences.get(resolvedCategory)
    };
  }
}
