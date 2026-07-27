import { addActionParamsSchema } from './tool-definition-utils.js';
import { allToolDefinitions } from '../definitions/shared/all-tool-definitions.js';
import type { ToolDefinition } from '../definitions/shared/tool-definition.js';

export type { ToolDefinition } from '../definitions/shared/tool-definition.js';
export {
  BEHAVIOR_TREE_ACTIONS,
  GAME_FRAMEWORK_ACTIONS,
  INPUT_ACTIONS,
  LIGHTING_ACTIONS,
  MATERIAL_AUTHORING_ACTIONS,
  NAVIGATION_ACTIONS,
  PCG_ACTIONS,
  PERFORMANCE_ACTIONS,
  ENVIRONMENT_ACTIONS,
  RENDER_ACTIONS,
  SESSION_ACTIONS,
  SKELETON_ACTIONS,
  SPLINE_ACTIONS,
  TEXTURE_ACTIONS,
  VOLUME_ACTIONS,
  WIDGET_AUTHORING_ACTIONS
} from '../definitions/shared/action-sets.js';

export const consolidatedToolDefinitions: ToolDefinition[] = [...allToolDefinitions];

addActionParamsSchema(consolidatedToolDefinitions);
