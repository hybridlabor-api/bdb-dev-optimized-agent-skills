import type { Rotator, Vector3 } from '../../../../types/handlers/handler-types.js';

type RotationInput = Rotator | [number, number, number] | number[] | null | undefined;

export function normalizeLocation(location: unknown): [number, number, number] | undefined {
  if (!location) {
    return undefined;
  }

  if (Array.isArray(location) && location.length >= 3) {
    return [Number(location[0]) || 0, Number(location[1]) || 0, Number(location[2]) || 0];
  }

  if (typeof location === 'object' && ('x' in location || 'y' in location || 'z' in location)) {
    const loc = location as Vector3;
    return [Number(loc.x) || 0, Number(loc.y) || 0, Number(loc.z) || 0];
  }

  return undefined;
}

export function normalizeRotation(rotation: RotationInput): Rotator | undefined {
  if (!rotation) {
    return undefined;
  }

  if (Array.isArray(rotation) && rotation.length >= 3) {
    return { pitch: Number(rotation[0]) || 0, yaw: Number(rotation[1]) || 0, roll: Number(rotation[2]) || 0 };
  }

  if (typeof rotation === 'object') {
    const rot = rotation as Rotator;
    return {
      pitch: Number(rot.pitch) || 0,
      yaw: Number(rot.yaw) || 0,
      roll: Number(rot.roll) || 0
    };
  }

  return undefined;
}
