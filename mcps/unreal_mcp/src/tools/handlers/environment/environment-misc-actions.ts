import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import { LONG_RUNNING_OP_TIMEOUT_MS } from '../../../constants.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import { type EnvironmentArgs, getNumber } from './environment-handler-utils.js';

export async function handleEnvironmentMiscAction(
  action: string,
  argsRecord: Record<string, unknown>,
  argsTyped: EnvironmentArgs,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
  switch (action) {

    case 'bake_lightmap':
      return cleanObject(await executeAutomationRequest(tools, 'bake_lightmap', {
        quality: (argsRecord.quality as string) || 'Preview',
        buildOnlySelected: false,
        buildReflectionCaptures: false,
        timeoutMs: typeof argsRecord.timeoutMs === 'number'
          ? argsRecord.timeoutMs
          : LONG_RUNNING_OP_TIMEOUT_MS
      }) as Record<string, unknown>);
    case 'create_landscape_grass_type':
      return cleanObject(await executeAutomationRequest(tools, 'create_landscape_grass_type', {
        name: argsTyped.name || '',
        meshPath: argsTyped.meshPath || (argsRecord.staticMesh as string) || '',
        path: argsRecord.path as string | undefined,
        staticMesh: argsRecord.staticMesh as string | undefined
      }) as Record<string, unknown>);
    case 'export_snapshot':
      return cleanObject(await executeAutomationRequest(tools, 'build_environment', {
        ...argsRecord,
        action: 'export_snapshot'
      }, 'Automation bridge not available for environment snapshot operations')) as Record<string, unknown>;
    case 'import_snapshot':
      return cleanObject(await executeAutomationRequest(tools, 'build_environment', {
        ...argsRecord,
        action: 'import_snapshot'
      }, 'Automation bridge not available for environment snapshot operations')) as Record<string, unknown>;
    case 'set_landscape_material':
      return cleanObject(await executeAutomationRequest(tools, 'set_landscape_material', {
        landscapeName: argsTyped.landscapeName || argsTyped.name || '',
        materialPath: argsTyped.materialPath ?? ''
      }) as Record<string, unknown>);
    case 'configure_landscape_material':
      return cleanObject(await executeAutomationRequest(tools, 'build_environment', {
        ...argsRecord,
        action: 'configure_landscape_material'
      }, 'Automation bridge not available for environment building operations')) as Record<string, unknown>;
    case 'set_time_of_day': {
      const time = getNumber(argsRecord.time) ?? getNumber(argsRecord.hour) ?? getNumber(argsRecord.propertyValue) ?? 12;
      return cleanObject(await executeAutomationRequest(tools, 'build_environment', {
        action: 'set_time_of_day',
        time,
        hour: argsRecord.hour as number | undefined
      }) as Record<string, unknown>);
    }
    case 'generate_lods':
      return cleanObject(await executeAutomationRequest(tools, 'build_environment', {
        action: 'generate_lods',
        assetPaths: (argsRecord.assetPaths as string[]) || (argsRecord.assets as string[]) || (argsRecord.path ? [argsRecord.path as string] : []),
        numLODs: argsRecord.numLODs as number | undefined
      }, 'Automation bridge not available for environment building operations')) as Record<string, unknown>;
    case 'delete': {
      const names: string[] = Array.isArray(argsRecord.names)
        ? argsRecord.names as string[]
        : (Array.isArray(argsRecord.actors) ? argsRecord.actors as string[] : []);
      if (argsTyped.name) {
        names.push(argsTyped.name);
      }
      const res = await executeAutomationRequest(tools, 'build_environment', {
        action: 'delete',
        names,
        actorPath: argsRecord.actorPath as string | undefined,
        actorName: argsRecord.actorName as string | undefined,
        targetActor: argsRecord.targetActor as string | undefined
      }) as Record<string, unknown>;
      return cleanObject(res);
    }
    default:
      return undefined;
  }
}
