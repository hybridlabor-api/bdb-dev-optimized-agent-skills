import { EditorResponse } from '../../types/automation/automation-responses.js';
import { toRotObject, toVec3Object, Vec3Obj, Rot3Obj } from '../../utils/validation/normalize.js';
import { isRecord } from '../../utils/validation/type-guards.js';

export type CameraTuple = [number, number, number];
export type CameraLocationInput = Vec3Obj | CameraTuple;
export type CameraRotationInput = Rot3Obj | CameraTuple;

export interface ViewportCameraInfo {
  success: boolean;
  location?: CameraTuple;
  rotation?: CameraTuple;
  error?: string;
  message?: string;
}

type SendEditorAutomation = (
  action: string,
  params: Record<string, unknown>,
  options?: { timeoutMs?: number }
) => Promise<EditorResponse>;

function toCameraTuple(value: unknown): CameraTuple | undefined {
  return Array.isArray(value) && value.length === 3
    ? [Number(value[0]) || 0, Number(value[1]) || 0, Number(value[2]) || 0]
    : undefined;
}

function normalizeAngle(value: number): number {
  return ((value % 360) + 360) % 360;
}

export async function getViewportCameraInfo(sendAutomationRequest: SendEditorAutomation): Promise<ViewportCameraInfo> {
  try {
    const resp = await sendAutomationRequest(
      'control_editor',
      { action: 'get_camera' },
      { timeoutMs: 3000 }
    );
    const result = isRecord(resp.result) ? resp.result : resp;
    const camera = isRecord(result.camera) ? result.camera : {};
    const loc = result.location ?? camera.location;
    const rot = result.rotation ?? camera.rotation;
    const location = toCameraTuple(loc);
    const rotation = toCameraTuple(rot);
    if (resp.success !== false && location && rotation) {
      return { success: true, location, rotation };
    }
    return { success: false, error: 'Failed to get camera information' };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: `Camera query failed: ${message}` };
  }
}

export function normalizeViewportCameraInput(
  location?: CameraLocationInput | null,
  rotation?: CameraRotationInput | null
): { location?: Vec3Obj; rotation?: Rot3Obj } {
  const normalized: { location?: Vec3Obj; rotation?: Rot3Obj } = {};

  if (location === null) {
    throw new Error('Invalid location: null is not allowed');
  }
  if (location !== undefined) {
    const locObj = toVec3Object(location);
    if (!locObj) {
      throw new Error('Invalid location: must be {x,y,z} or [x,y,z]');
    }
    const maxCoord = 1000000;
    normalized.location = {
      x: Math.max(-maxCoord, Math.min(maxCoord, locObj.x)),
      y: Math.max(-maxCoord, Math.min(maxCoord, locObj.y)),
      z: Math.max(-maxCoord, Math.min(maxCoord, locObj.z))
    };
  }

  if (rotation === null) {
    throw new Error('Invalid rotation: null is not allowed');
  }
  if (rotation !== undefined) {
    const rotObj = toRotObject(rotation);
    if (!rotObj) {
      throw new Error('Invalid rotation: must be {pitch,yaw,roll} or [pitch,yaw,roll]');
    }
    normalized.rotation = {
      pitch: normalizeAngle(rotObj.pitch),
      yaw: normalizeAngle(rotObj.yaw),
      roll: normalizeAngle(rotObj.roll)
    };
  }

  return normalized;
}
