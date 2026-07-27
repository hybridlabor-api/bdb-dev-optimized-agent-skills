import { commonSchemas } from '../catalog/tool-definition-utils.js';
import type { ToolDefinition } from './core-tool-definition.js';

export const manageToolsToolDefinition: ToolDefinition = {
  name: 'manage_tools',
  description: 'Dynamic MCP tool management. List canonical tools, view category counts, and enable/disable tools or categories at runtime.',
  category: 'core',
  inputSchema: {
    type: 'object',
    properties: {
      action: {
        type: 'string',
        enum: ['list_tools', 'list_categories', 'enable_tools', 'disable_tools', 'enable_category', 'disable_category', 'get_status', 'reset'],
        description: 'list_tools: show canonical tools with status. list_categories: show category counts. enable/disable_tools: toggle specific tools. enable/disable_category: toggle category. get_status: current state. reset: restore defaults.'
      },
      tools: { type: 'array', items: commonSchemas.stringProp, description: 'Tool names to enable/disable' },
      category: { type: 'string', description: 'Category name to enable/disable (core, world, gameplay, utility, all)' }
    },
    required: ['action']
  },
  outputSchema: {
    type: 'object',
    properties: {
      ...commonSchemas.outputBase,
      tools: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, enabled: { type: 'boolean' }, category: { type: 'string' } } } },
      categories: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, enabled: { type: 'boolean' }, toolCount: { type: 'number' } } } },
      enabledCount: { type: 'number' },
      disabledCount: { type: 'number' }
    }
  }
};
