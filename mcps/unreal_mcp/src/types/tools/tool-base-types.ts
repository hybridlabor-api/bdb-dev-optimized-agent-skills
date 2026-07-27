export interface BaseToolResponse {
  success: boolean;
  message?: string;
  error?: string;
  warning?: string;
  retriable?: boolean;
  scope?: string;
}

export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

export interface Rotation3D {
  pitch: number;
  yaw: number;
  roll: number;
}

export type ScreenshotMode = 'editor_viewport' | 'game_viewport' | 'full_editor_window';
