import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { LightingArgs } from '../../../types/handlers/handler-types.js';
import { ResponseFactory } from '../../../utils/responses/response-factory.js';
import { createDynamicLight, handleSpawnLightAction } from './lighting-light-actions.js';
import { configureShadows, setAmbientOcclusion, setExposure, setupGlobalIllumination } from './lighting-render-settings.js';
import { createSkyLight, ensureSingleSkyLight } from './lighting-sky-actions.js';
import {
  buildLighting,
  createLightingEnabledLevel,
  createLightmassVolume,
  listLightTypes,
  setupVolumetricFog
} from './lighting-world-actions.js';

export async function handleLightingTools(action: string, args: LightingArgs, tools: ITools): Promise<Record<string, unknown>> {
  switch (action) {
    case 'spawn_light':
    case 'create_light':
      return await handleSpawnLightAction(tools, args);

    case 'create_dynamic_light':
      return await createDynamicLight(tools, args);

    case 'spawn_sky_light':
    case 'create_sky_light':
      return cleanObject(await createSkyLight(tools, args));

    case 'ensure_single_sky_light':
      return cleanObject(await ensureSingleSkyLight(tools, args));

    case 'create_lightmass_volume':
      return cleanObject(await createLightmassVolume(tools, args));

    case 'setup_volumetric_fog':
      return cleanObject(await setupVolumetricFog(tools, args));

    case 'setup_global_illumination':
      return cleanObject(await setupGlobalIllumination(tools, args));

    case 'configure_shadows':
      return cleanObject(await configureShadows(tools, args));

    case 'set_exposure':
      return cleanObject(await setExposure(tools, args));

    case 'set_ambient_occlusion':
      return cleanObject(await setAmbientOcclusion(tools, args));

    case 'build_lighting':
      return cleanObject(await buildLighting(tools, args));

    case 'create_lighting_enabled_level':
      return cleanObject(await createLightingEnabledLevel(tools, args));

    case 'list_light_types':
      return cleanObject(await listLightTypes(tools));

    default:
      return ResponseFactory.error(`Unknown lighting action: ${action}`);
  }
}
