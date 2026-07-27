import type { ToolDefinition } from '../../shared/tool-definition.js';
import { manageBlueprintInputSchema } from './manage-blueprint-input-schema.js';
import { manageBlueprintOutputSchema } from './manage-blueprint-output-schema.js';

export const manageBlueprintToolDefinition: ToolDefinition = {
  name: 'manage_blueprint',
  category: 'core',
  description: 'Create Blueprints and UMG widgets, add SCS/UI components, set defaults, and manipulate Blueprint graphs, bindings, and widget layouts.',
  inputSchema: manageBlueprintInputSchema,
  outputSchema: manageBlueprintOutputSchema
};
