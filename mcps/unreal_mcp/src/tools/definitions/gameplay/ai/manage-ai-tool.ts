import type { ToolDefinition } from '../../shared/tool-definition.js';
import { manageAiInputSchema } from './manage-ai-input-schema.js';
import { manageAiOutputSchema } from './manage-ai-output-schema.js';

export const manageAiToolDefinition: ToolDefinition = {
  name: 'manage_ai',
  category: 'gameplay',
  description: 'Build AI systems: AI controllers, Behavior Trees, Blackboards, EQS, perception, State Trees, Smart Objects, NavMesh settings, nav modifiers, links, and pathfinding.',
  inputSchema: manageAiInputSchema,
  outputSchema: manageAiOutputSchema
};
