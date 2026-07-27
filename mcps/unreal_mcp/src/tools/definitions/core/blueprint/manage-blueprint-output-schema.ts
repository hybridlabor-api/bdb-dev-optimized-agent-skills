import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageBlueprintOutputSchema = {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        blueprintPath: commonSchemas.blueprintPath,
        blueprint: { oneOf: [{ type: 'object' }, { type: 'string' }], description: 'Blueprint data object or path string.' }
      }
    };
