import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import { type EnvironmentArgs, getString, normalizeProceduralFoliageBounds, vec3ToObject } from './environment-handler-utils.js';

export async function handleEnvironmentProceduralAction(
  action: string,
  argsRecord: Record<string, unknown>,
  argsTyped: EnvironmentArgs,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
  switch (action) {
    case 'create_procedural_terrain': {
      // Generate default name if not provided (C++ requires non-empty name)
      const defaultName = argsTyped.name || argsTyped.actorName || `ProceduralTerrain_${Date.now()}`;
      return cleanObject(await executeAutomationRequest(tools, 'create_procedural_terrain', {
        name: defaultName,
        actorName: defaultName,
        location: vec3ToObject(argsTyped.location),
        sizeX: argsRecord.sizeX as number | undefined,
        sizeY: argsRecord.sizeY as number | undefined,
        heightScale: argsRecord.heightScale as number | undefined,
        subdivisions: argsRecord.subdivisions as number | undefined,
        rotation: argsRecord.rotation as Record<string, unknown> | undefined,
        material: argsRecord.material as string | undefined
      }) as Record<string, unknown>);
    }
    case 'create_procedural_foliage': {
      // Generate default name if not provided (C++ will auto-generate if empty)
      const volumeName = getString(argsRecord.volumeName);
      const defaultName = argsTyped.name || volumeName || `ProceduralFoliage_${Date.now()}`;
      // Accept both 'foliageTypes' and 'types' parameter names
      const foliageTypes = (argsRecord.foliageTypes || argsRecord.types) as { meshPath: string; density: number }[] | undefined;
      return cleanObject(await executeAutomationRequest(tools, 'create_procedural_foliage', {
        name: defaultName,
        foliageTypes: foliageTypes,
        // Pass 'types' as well for C++ handler that accepts both
        types: foliageTypes,
        volumeName: argsRecord.volumeName as string | undefined,
        bounds: normalizeProceduralFoliageBounds(argsRecord.bounds),
        seed: argsTyped.seed,
        tileSize: argsRecord.tileSize as number | undefined
      }) as Record<string, unknown>);
    }

    default:
      return undefined;
  }
}
